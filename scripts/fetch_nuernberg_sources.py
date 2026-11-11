#!/usr/bin/env python3
"""Download the public sources behind NUERNBERG_DATASET into data/nuernberg-raw/.

    python3 scripts/build_nuernberg_dataset.py        # this download, then the build -> data/nuernberg-dataset/
    python3 scripts/fetch_nuernberg_sources.py        # the download step alone

Every source is public and needs no account. Sources and licences are listed in data/README.md.
Pure standard library. Files already downloaded are kept (--force downloads again).

The OpenStreetMap cycle network is not downloaded by default: the repo ships a snapshot in
data/source/osm_cycling_ways.json.gz (ODbL). --refresh-osm replaces it from the Overpass API.
The VGN timetable, Bezirke and Bezirksatlas are required; if the roadworks (SÖR) or the bicycle
counters fail, the script warns, carries on, and the build leaves those tables out.
"""
from __future__ import annotations

import argparse
import gzip
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ATLAS = "https://online-service2.nuernberg.de/geoinf/ia_bezirksatlas/"
DWD = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/"
SOURCES = [
    # (folder, file name, url)
    ("vgn", "GTFS.zip", "https://www.vgn.de/opendata/GTFS.zip"),
    ("bezirke", "geometrie_nue_stat_bezirke.zip",
     "https://www.nuernberg.de/imperia/md/statistik/dokumente/karten/geometrie_nue_stat_bezirke.zip"),
    ("atlas", "data.js", ATLAS + "data.js"),
    ("atlas", "Statistische_Bezirke-t0.js", ATLAS + "Statistische_Bezirke-t0.js"),
    # DWD daily climate, station 03668 Nuernberg (open data, attribution "Deutscher Wetterdienst")
    ("weather", "tageswerte_KL_03668_hist.zip", DWD + "historical/tageswerte_KL_03668_18790101_20251231_hist.zip"),
    ("weather", "tageswerte_KL_03668_akt.zip", DWD + "recent/tageswerte_KL_03668_akt.zip"),
]
# Cycle network from OpenStreetMap (ODbL, "© OpenStreetMap contributors"): one Overpass query over the city's bbox
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
OVERPASS_QUERY = """[out:json][timeout:180];
(
  way["highway"="cycleway"]({bbox});
  way["cycleway"~"^(lane|track|shared_lane|share_busway|opposite_lane|opposite_track)$"]({bbox});
  way["cycleway:left"~"^(lane|track|shared_lane|share_busway)$"]({bbox});
  way["cycleway:right"~"^(lane|track|shared_lane|share_busway)$"]({bbox});
  way["cycleway:both"~"^(lane|track|shared_lane|share_busway)$"]({bbox});
  way["bicycle_road"="yes"]({bbox});
  way["cyclestreet"="yes"]({bbox});
  way["highway"~"^(path|footway|track)$"]["bicycle"="designated"]({bbox});
);
out tags geom qt;""".replace("{bbox}", "49.33,10.98,49.54,11.21")
# SÖR (Servicebetrieb Öffentlicher Raum) construction coordination on the city geoportal: planned and ongoing works,
# street-use permits and diversions, as GeoJSON in WGS84. "© Stadt Nürnberg", no open licence stated.
SOER = "https://geoportal.nuernberg.de/server/rest/services/Fachdaten_G/SOER_BAUKOP_G_V/MapServer/"
SOER_LAYERS = {"planned_works.geojson": 1, "permits.geojson": 0, "diversions.geojson": 2}
# Bicycle counters: the city's Eco-Counter page. No API and no stated licence: the counts are read from the public
# web pages (one request per counter and year, 2 s apart). Fetched by default; --skip-bike-counters leaves them out.
ECO = "https://nuernberg.eco-counter.com"
COUNTER_YEARS = (2025, 2026)


def fetch(url: str, target: Path, data: bytes | None = None) -> None:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "nuernberg-mobility-planning-agents"})
    tmp = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(req, timeout=300) as resp, tmp.open("wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
    tmp.replace(target)


def fetch_osm(target: Path) -> bool:
    """Query Overpass and write the result, gzipped, to `target` (the snapshot in data/source/)."""
    body = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode()
    raw = target.with_name("osm_cycling_ways.download.json")
    for attempt, url in enumerate(OVERPASS * 2):
        try:
            fetch(url, raw, data=body)
            json.loads(raw.read_text(encoding="utf-8"))["elements"]  # a busy server can answer with an error page
        except (OSError, ValueError, KeyError) as exc:  # the public instances are often at capacity
            print(f"    {url}: {exc}; retrying")
            time.sleep(10 * (attempt + 1))
            continue
        with raw.open("rb") as fh, gzip.GzipFile(target, "wb", compresslevel=9, mtime=0) as gz:
            gz.write(fh.read())
        raw.unlink()
        return True
    raw.unlink(missing_ok=True)
    return False


def fetch_arcgis_layer(layer_url: str, target: Path, page: int = 2000) -> int:
    """Every feature of an ArcGIS MapServer layer as one GeoJSON FeatureCollection, paged by OBJECTID."""
    features, offset = [], 0
    while True:
        params = urllib.parse.urlencode({"where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": 4326,
                                         "orderByFields": "OBJECTID", "resultOffset": offset,
                                         "resultRecordCount": page, "f": "geojson"})
        batch = json.loads(_get(f"{layer_url}/query?{params}"))["features"]
        features += batch
        if len(batch) < page:
            break
        offset += page
    target.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False), encoding="utf-8")
    return len(features)


def _rsc_text(html: str) -> str:
    """The React Server Component payload a Next.js page embeds in self.__next_f.push([1, "..."]) calls."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, flags=re.S)
    return "".join(json.loads('"' + c + '"') for c in chunks)


def _json_after(text: str, key: str):
    i = text.find(f'"{key}":')
    if i < 0:
        return None
    return json.JSONDecoder().raw_decode(text, i + len(key) + 3)[0]


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "nuernberg-mobility-planning-agents"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8")


def fetch_counters(folder: Path) -> None:
    """Counter list and daily counts (total, in, out) per counter and year -> counters.json, counts.csv."""
    folder.mkdir(parents=True, exist_ok=True)
    sites = _json_after(_rsc_text(_get(ECO + "/")), "sites")
    (folder / "counters.json").write_text(json.dumps(sites, ensure_ascii=False, indent=1), encoding="utf-8")
    rows = []
    for site in sites:
        for year in COUNTER_YEARS:
            time.sleep(2)
            text = _rsc_text(_get(f"{ECO}/site/{site['id']}?granularity=P1D&year={year}"))
            days: dict[str, dict] = {}
            for series in _json_after(text, "chartData") or []:
                for p in series["data"]:
                    days.setdefault(p["timestamp"][:10], {})["total"] = p["traffic"]["counts"]
            for series in _json_after(text, "directionGraphData") or []:
                for p in series["data"]:
                    days.setdefault(p["timestamp"][:10], {})[series["direction"]] = p["traffic"]["counts"]
            rows += [{"count_date": d, "site_id": site["id"], **v} for d, v in sorted(days.items())]
            print(f"    {site['name']} {year}: {len(days)} days")
    with (folder / "counts.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["count_date", "site_id", "total", "in", "out"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=REPO / "data" / "nuernberg-raw")
    ap.add_argument("--force", action="store_true", help="download again even when a file is already there")
    ap.add_argument("--skip-bike-counters", action="store_true",
                    help="don't read the daily bicycle counts from the city's Eco-Counter pages (~25 requests, 2 s apart)")
    ap.add_argument("--with-bike-counters", action="store_true", help=argparse.SUPPRESS)  # the default now; kept for old commands
    ap.add_argument("--refresh-osm", action="store_true",
                    help="replace the OpenStreetMap snapshot in data/source/ with a fresh Overpass download")
    args = ap.parse_args(argv)
    problems = []
    for folder, name, url in SOURCES:
        target = args.out / folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not args.force:
            print(f"  have  {target.relative_to(args.out)}")
            continue
        print(f"  fetch {target.relative_to(args.out)}  <- {url}")
        try:
            fetch(url, target)
        except OSError as exc:
            sys.exit(f"download failed for {url}: {exc}\nThis source is required. Check your connection and run the script again.")
    snapshot = REPO / "data" / "source" / "osm_cycling_ways.json.gz"
    if args.refresh_osm:
        print(f"  fetch {snapshot.relative_to(REPO)}  <- Overpass API (OpenStreetMap)")
        if not fetch_osm(snapshot):
            problems.append("OpenStreetMap: Overpass is busy; the existing snapshot is kept. Try --refresh-osm later.")
    else:
        print(f"  have  {snapshot.relative_to(REPO)} (OpenStreetMap snapshot; --refresh-osm to update)")
    for name, layer in SOER_LAYERS.items():
        target = args.out / "soer" / name
        if target.exists() and not args.force:
            print(f"  have  {target.relative_to(args.out)}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            n = fetch_arcgis_layer(SOER + str(layer), target)
        except (OSError, ValueError, KeyError) as exc:
            problems.append(f"roadworks (SÖR layer {layer}): {exc}")
            continue
        print(f"  fetch soer/{name}  <- city geoportal, SÖR layer {layer}: {n:,} features")
    if not args.skip_bike_counters:
        counts = args.out / "counters" / "counts.csv"
        if counts.exists() and not args.force:
            print(f"  have  {counts.relative_to(args.out)}")
        else:
            print(f"  fetch counters/  <- {ECO} (24 pages: usually 1-2 minutes, up to 15 when the site is slow;"
                  " --skip-bike-counters leaves them out)")
            try:
                fetch_counters(counts.parent)
            except (OSError, ValueError, KeyError) as exc:
                problems.append(f"bicycle counters: {exc}")
    print(f"done: {args.out}")
    if problems:
        print("\nNot downloaded (the build leaves these tables out; run the script again later to add them):")
        for p in problems:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
