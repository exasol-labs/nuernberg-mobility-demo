#!/usr/bin/env python3
"""Digitize the city's cycle network plan (Radwegenetzplan, Stand 01/2021) into line geometry.

The plan is a PDF map without coordinates (Stadt Nürnberg / Verkehrsplanungsamt, published on
https://www.nuernberg.de/internet/verkehrsplanung/radverkehrsnetz.html). This script
  1. georeferences the page: the map is north-up with one scale, so an affine transform from page points to
     metres is fitted by matching the map's dashed and dotted paths to the OpenStreetMap street and path network
     (FFT cross-correlation for scale and offset, then iterative nearest-point matching);
  2. extracts the layers the city draws as vectors: planned routes (blue), routes built 2013-2020 (red), routes
     over quiet side streets (dotted) and field, forest and canal paths (dashed);
  3. traces the "decided planning" layer, which is drawn as a raster band, along its green centre line;
  4. writes data/source/cycle_network_plan_2021.csv (WGS84 LINESTRINGs) and the fitted transform.

The existing network ("Bestand") is drawn into raster patches and is not extracted; OpenStreetMap covers it.
Derived data: positions are accurate to roughly 10 m (see the fit report), categories as in the plan's legend.

Needs PyMuPDF and numpy (not the standard library), so it is run once by a maintainer; the CSV is committed:

    pip install pymupdf numpy
    python3 scripts/digitize_radnetz_2021.py
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pymupdf

REPO = Path(__file__).resolve().parent.parent
PDF_URL = "https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/stz_2005_radwegenetzplan_stand_01_2021_neu.pdf"
OVERPASS = "https://overpass-api.de/api/interpreter"
OSM_QUERY = ('[out:json][timeout:240];way["highway"~"^(primary|secondary|tertiary|unclassified|residential|living_street|'
             'service|track|path|footway|cycleway|bridleway|pedestrian)$"](49.30,10.95,49.56,11.30);out skel geom qt;')
LAT0, LON0 = 49.45, 11.08  # local metric frame for the fit (equirectangular; distortion < 0.1 % over the map)
KX, KY = math.cos(math.radians(LAT0)) * 111320, 110574
BLACK, BLUE, RED = (0.14, 0.12, 0.13), (0.0, 0.68, 0.94), (0.93, 0.11, 0.14)
EXCLUDE = [(465, 740, 595, 842), (350, 0, 595, 80), (0, 805, 200, 842)]  # legend, title, imprint (page points)
SOURCE = ("Radwegenetzplan Stadt Nürnberg, Stand 01/2021 (Verkehrsplanungsamt), digitized and georeferenced against "
          "OpenStreetMap by scripts/digitize_radnetz_2021.py; " + PDF_URL)


def excluded(x, y):
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in EXCLUDE)


def fetch(url, target, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "nuernberg-mobility-planning-agents"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        target.write_bytes(resp.read())


# --------------------------------------------------------------------------- vector shapes
def subpaths(drawing):
    """A PyMuPDF drawing as a list of point lists (one per subpath)."""
    subs, cur = [], []
    for it in drawing["items"]:
        if it[0] in ("l", "c"):
            a, b = it[1], it[-1]
            if cur and (abs(cur[-1][0] - a.x) > 1e-3 or abs(cur[-1][1] - a.y) > 1e-3):
                subs.append(cur)
                cur = []
            if not cur:
                cur = [(a.x, a.y)]
            cur.append((b.x, b.y))
        elif it[0] == "re":
            r = it[1]
            subs.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
    if cur:
        subs.append(cur)
    return [s for s in subs if len(s) >= 3]


def shape_stats(pts):
    a = np.asarray(pts)
    x, y = a[:, 0], a[:, 1]
    area = abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) / 2
    per = float(np.sum(np.hypot(np.diff(np.r_[x, x[:1]]), np.diff(np.r_[y, y[:1]]))))
    return area, per, max(x.max() - x.min(), y.max() - y.min())


def centerline(pts, n=24):
    """Centre line of a thin filled outline: split the ring at its two farthest points, resample both sides, average."""
    a = np.asarray(pts)
    if np.allclose(a[0], a[-1]):
        a = a[:-1]
    d = np.hypot(*(a[:, None, :] - a[None, :, :]).transpose(2, 0, 1))
    i, j = np.unravel_index(np.argmax(d), d.shape)
    i, j = min(i, j), max(i, j)
    side1 = a[i:j + 1]
    side2 = np.r_[a[j:], a[:i + 1]][::-1]

    def resample(s):
        seg = np.hypot(*np.diff(s, axis=0).T)
        t = np.r_[0, np.cumsum(seg)]
        u = np.linspace(0, t[-1], n) if t[-1] > 0 else np.zeros(n)
        return np.c_[np.interp(u, t, s[:, 0]), np.interp(u, t, s[:, 1])]

    return (resample(side1) + resample(side2)) / 2


def chain(points, max_gap, min_nodes=4):
    """Join dots or dashes into polylines: minimum spanning forest with edges up to max_gap, split at branches."""
    pts = np.asarray(points)
    cell = max_gap
    grid = {}
    for k, (x, y) in enumerate(pts):
        grid.setdefault((int(x // cell), int(y // cell)), []).append(k)
    edges = []
    for k, (x, y) in enumerate(pts):
        cx, cy = int(x // cell), int(y // cell)
        for i in (cx - 1, cx, cx + 1):
            for j in (cy - 1, cy, cy + 1):
                for m in grid.get((i, j), ()):
                    if m > k:
                        dd = math.hypot(pts[m][0] - x, pts[m][1] - y)
                        if dd <= max_gap:
                            edges.append((dd, k, m))
    parent = list(range(len(pts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    adj: dict[int, list[int]] = {}
    for dd, k, m in sorted(edges):
        rk, rm = find(k), find(m)
        if rk != rm:
            parent[rk] = rm
            adj.setdefault(k, []).append(m)
            adj.setdefault(m, []).append(k)
    seen_edges, lines = set(), []
    for start in adj:
        if len(adj[start]) == 2:
            continue
        for nxt in adj[start]:
            if (start, nxt) in seen_edges:
                continue
            line, prev, cur = [start], start, nxt
            seen_edges.add((start, nxt)); seen_edges.add((nxt, start))
            while True:
                line.append(cur)
                if len(adj[cur]) != 2:
                    break
                a, b = adj[cur]
                nn = b if a == prev else a
                seen_edges.add((cur, nn)); seen_edges.add((nn, cur))
                prev, cur = cur, nn
            lines.append(line)
    comp_size: dict[int, int] = {}
    for k in adj:
        comp_size[find(k)] = comp_size.get(find(k), 0) + 1
    return [pts[line] for line in lines if comp_size[find(line[0])] >= min_nodes]


# --------------------------------------------------------------------------- georeference
def osm_points(osm_json: Path):
    xs, ys = [], []
    for w in json.loads(osm_json.read_text())["elements"]:
        g = w.get("geometry") or []
        for a, b in zip(g, g[1:]):
            x0, y0 = (a["lon"] - LON0) * KX, (a["lat"] - LAT0) * KY
            x1, y1 = (b["lon"] - LON0) * KX, (b["lat"] - LAT0) * KY
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 8))
            t = np.linspace(0, 1, n + 1)
            xs.append(x0 + (x1 - x0) * t); ys.append(y0 + (y1 - y0) * t)
    return np.concatenate(xs), np.concatenate(ys)


def fit_affine(src_page, tx, ty, log):
    """Page points (x, y down) -> local metres. FFT search for scale and offset, then iterative closest points."""
    px, py = src_page[:, 0], -src_page[:, 1]

    def raster(xs, ys, cell, n):
        g = np.zeros((n, n), np.float32)
        ix = (xs / cell + n / 2).astype(int); iy = (ys / cell + n / 2).astype(int)
        m = (ix >= 0) & (ix < n) & (iy >= 0) & (iy < n)
        g[iy[m], ix[m]] = 1
        return g

    cx, cy = px.mean(), py.mean()
    best = None
    for cell, n, scales in ((80.0, 1024, np.arange(20, 45, 0.25)), (20.0, 2048, None)):
        tf = np.fft.rfft2(raster(tx, ty, cell, n))
        if scales is None:
            scales = np.arange(best[1] - 0.4, best[1] + 0.41, 0.05)
        for s in scales:
            g = raster((px - cx) * s, (py - cy) * s, cell, n)
            corr = np.fft.irfft2(tf * np.conj(np.fft.rfft2(g)), s=(n, n))
            iy, ix = np.unravel_index(np.argmax(corr), corr.shape)
            ix = ix - n if ix > n / 2 else ix
            iy = iy - n if iy > n / 2 else iy
            if best is None or corr.max() > best[0]:
                best = (corr.max(), s, ix * cell, iy * cell)
        log(f"  correlation at {cell:.0f} m cells: scale {best[1]:.2f} m/pt")
    _, s, ox, oy = best
    A = np.array([[s, 0, ox - s * cx], [0, s, oy - s * cy]])

    cell = 10.0
    keys = (np.floor(tx / cell).astype(np.int64) << 32) + (np.floor(ty / cell).astype(np.int64) & 0xffffffff)
    order = np.argsort(keys)
    ks, txs, tys = keys[order], tx[order], ty[order]
    uk, starts = np.unique(ks, return_index=True)
    lookup = dict(zip(uk.tolist(), zip(starts.tolist(), np.append(starts[1:], len(ks)).tolist())))

    def nearest(x, y, r):
        best_d, best_p = r, None
        c0, c1, k = int(math.floor(x / cell)), int(math.floor(y / cell)), int(math.ceil(r / cell))
        for i in range(c0 - k, c0 + k + 1):
            for j in range(c1 - k, c1 + k + 1):
                se = lookup.get((i << 32) + (j & 0xffffffff))
                if se:
                    d = np.hypot(txs[se[0]:se[1]] - x, tys[se[0]:se[1]] - y)
                    m = int(d.argmin())
                    if d[m] < best_d:
                        best_d, best_p = float(d[m]), (txs[se[0] + m], tys[se[0] + m])
        return best_d, best_p

    rng = np.random.default_rng(0)
    idx = rng.choice(len(px), size=min(8000, len(px)), replace=False)
    P = np.c_[px[idx], py[idx], np.ones(len(idx))]
    for thr in (60, 40, 30, 20, 15, 12, 12):
        pairs = [(i, nearest(x, y, thr)) for i, (x, y) in enumerate(P @ A.T)]
        m = [(i, p) for i, (d, p) in pairs if p is not None]
        src, dst = P[[i for i, _ in m]], np.array([p for _, p in m])
        A = np.linalg.lstsq(src, dst, rcond=None)[0].T
        res = np.hypot(*(src @ A.T - dst).T)
        log(f"  matching within {thr:>2} m: {len(m):5d}/{len(P)} points, median {np.median(res):4.1f} m, p90 {np.percentile(res, 90):4.1f} m")
    return A, {"matched_share_within_12m": len(m) / len(P), "median_m": float(np.median(res)), "p90_m": float(np.percentile(res, 90))}


def to_lonlat(A, pts_page):
    p = np.c_[pts_page[:, 0], -pts_page[:, 1], np.ones(len(pts_page))] @ A.T
    return np.c_[p[:, 0] / KX + LON0, p[:, 1] / KY + LAT0]


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    raw = REPO / "data" / "nuernberg-raw" / "radnetz"
    ap.add_argument("--pdf", type=Path, default=raw / "radwegenetzplan_2021.pdf")
    ap.add_argument("--osm", type=Path, default=raw / "osm_streets_paths.json")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "source" / "cycle_network_plan_2021.csv")
    args = ap.parse_args()
    log = print
    raw.mkdir(parents=True, exist_ok=True)
    if not args.pdf.exists():
        log(f"fetch {PDF_URL}")
        fetch(PDF_URL, args.pdf)
    if not args.osm.exists():
        log("fetch OSM streets and paths (Overpass)")
        for attempt in range(4):
            try:
                fetch(OVERPASS, args.osm, urllib.parse.urlencode({"data": OSM_QUERY}).encode())
                break
            except OSError as exc:
                log(f"  {exc}; retrying")
                time.sleep(20 * (attempt + 1))

    page = pymupdf.open(args.pdf)[0]
    dots, dashes, outlines = [], [], {"planned": [], "built_2013_2020": []}
    seen = set()  # the PDF draws some shapes twice, on top of each other
    for d in page.get_drawings():
        fill = tuple(round(v, 2) for v in (d.get("fill") or ()))
        for s in subpaths(d):
            key = (fill, tuple((round(x, 2), round(y, 2)) for x, y in s))
            if key in seen:
                continue
            seen.add(key)
            area, per, ext = shape_stats(s)
            cx, cy = float(np.mean([q[0] for q in s])), float(np.mean([q[1] for q in s]))
            if excluded(cx, cy):
                continue
            if fill == BLACK:
                if 0.4 <= ext < 0.8:
                    dots.append((cx, cy))
                elif 1.4 <= ext < 2.6:
                    dashes.append((cx, cy))
            elif fill in (BLUE, RED):
                width = 2 * area / per if per else 0
                outlines["planned" if fill == BLUE else "built_2013_2020"].append((s, 2 if width > 0.4 else 1))
    log(f"vector layers: {len(dots)} dots, {len(dashes)} dashes, {len(outlines['planned'])} planned and "
        f"{len(outlines['built_2013_2020'])} built pieces")

    log("georeferencing against OSM")
    tx, ty = osm_points(args.osm)
    A, fit = fit_affine(np.array(dots + dashes), tx, ty, log)

    def nn_spacing(pts):
        a = np.asarray(pts)
        sample = a[np.random.default_rng(1).choice(len(a), size=min(2000, len(a)), replace=False)]
        d = np.hypot(*(sample[:, None, :] - a[None, :, :]).transpose(2, 0, 1))
        d[d == 0] = np.inf
        return float(np.median(d.min(axis=1)))

    lines = []  # (category, directions, page points)
    for cat, pts in (("quiet_street_route", dots), ("other_path", dashes)):
        gap = 1.8 * nn_spacing(pts)
        for ln in chain(pts, gap):
            lines.append((cat, 2, ln))
    for cat, items in outlines.items():
        for s, dirs in items:
            lines.append((cat, dirs, centerline(s)))

    # decided planning: raster band with a green centre line -> green pixels, joined like dots
    zoom = 600 / 72
    pix = page.get_pixmap(dpi=600)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(int)
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    green = (g > r + 40) & (g > b + 15) & (r < 150)
    pink = (r > 215) & (g > 140) & (g < 205) & (b > 175) & (b < 230)
    block = 8  # px, about 1 pt
    hb, wb = green.shape[0] // block, green.shape[1] // block
    gb = green[:hb * block, :wb * block].reshape(hb, block, wb, block).any(axis=(1, 3))
    pb = pink[:hb * block, :wb * block].reshape(hb, block, wb, block).any(axis=(1, 3))
    near_pink = pb.copy()
    for di in (-2, -1, 1, 2):
        near_pink |= np.roll(pb, di, axis=0) | np.roll(pb, di, axis=1)
    iy, ix = np.nonzero(gb & near_pink)
    centres = [((x + 0.5) * block / zoom, (y + 0.5) * block / zoom) for y, x in zip(iy, ix)]
    centres = [c for c in centres if not excluded(*c)]
    for ln in chain(centres, 1.6 * block / zoom, min_nodes=6):
        lines.append(("decided_planning", 2, ln))
    log(f"decided planning: {len(centres)} centre-line cells")

    rows = []
    for n, (cat, dirs, ln) in enumerate(lines, 1):
        ll = to_lonlat(A, np.asarray(ln))
        xy = np.c_[(ll[:, 0] - LON0) * KX, (ll[:, 1] - LAT0) * KY]
        length = float(np.sum(np.hypot(*np.diff(xy, axis=0).T)))
        if length < 15:
            continue
        mid = ll[len(ll) // 2]
        rows.append({"segment_id": n, "category": cat, "directions": dirs, "length_m": round(length, 1),
                     "start_lat": round(ll[0, 1], 6), "start_lon": round(ll[0, 0], 6),
                     "end_lat": round(ll[-1, 1], 6), "end_lon": round(ll[-1, 0], 6),
                     "mid_lat": round(mid[1], 6), "mid_lon": round(mid[0], 6),
                     "shape_wkt": "LINESTRING(" + ", ".join(f"{x:.6f} {y:.6f}" for x, y in ll) + ")",
                     "source": SOURCE})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    fit["affine_page_to_local_m"] = A.tolist()
    fit["local_frame"] = {"lat0": LAT0, "lon0": LON0, "m_per_deg_lon": KX, "m_per_deg_lat": KY}
    args.out.with_suffix(".fit.json").write_text(json.dumps(fit, indent=1))
    km = {}
    for r_ in rows:
        km[r_["category"]] = km.get(r_["category"], 0) + r_["length_m"] / 1000
    log(f"wrote {args.out.relative_to(REPO)}: {len(rows)} lines; km by category: "
        + ", ".join(f"{k} {v:.0f}" for k, v in sorted(km.items())))


if __name__ == "__main__":
    main()
