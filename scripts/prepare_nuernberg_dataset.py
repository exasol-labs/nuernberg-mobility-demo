#!/usr/bin/env python3
"""Build the flat NUERNBERG_DATASET folder from three public downloads.

`exakit data-load <folder>` reads a folder at its TOP LEVEL only and makes one table per file, named after
the file. This script turns the raw downloads into load-ready CSVs with WGS84 coordinates and an area tag on
every stop, so district rollups are plain equality joins.

Inputs (download them first, see data/README.md):
  --gtfs   GTFS.zip                          https://www.vgn.de/opendata/GTFS.zip (CC BY 3.0 DE, VGN GmbH)
  --bezirke geometrie_nue_stat_bezirke.zip   https://www.nuernberg.de/imperia/md/statistik/dokumente/karten/geometrie_nue_stat_bezirke.zip
  --atlas  folder with data.js, Statistische_Bezirke-t0.js
           from https://online-service2.nuernberg.de/geoinf/ia_bezirksatlas/ (Bezirksatlas, Amt fuer Stadtforschung
           und Statistik fuer Nuernberg und Fuerth)

    python3 scripts/prepare_nuernberg_dataset.py --gtfs GTFS.zip --bezirke geometrie_nue_stat_bezirke.zip \
        --atlas atlas/ --out data/nuernberg-dataset
    EXAKIT_SCHEMA=NUERNBERG_DATASET exakit data-load data/nuernberg-dataset

The unit of analysis is the AREA ("district" in the tables and columns): one of
the 87 statistical Bezirke, or a group of small Bezirke that the city only publishes together (e.g. 18/19,
41/42/43, 75/85/87). That gives 78 areas. `district_no` is the lowest Bezirk number in the area.

Output files (-> table names after load, schema NUERNBERG_DATASET):
  districts.csv            DISTRICTS            78 areas: population 2025, area_km2, density, centroid, polygon, Stadtteil
  bezirke.csv              BEZIRKE              87 statistical Bezirke with their area (district_no) and polygon
  district_population.csv  DISTRICT_POPULATION  residents with main residence 2023/2024/2025 per area
  district_employment.csv  DISTRICT_EMPLOYMENT  jobs at place of work 2019-2024 and 2005, establishments
  district_housing.csv     DISTRICT_HOUSING     homes permitted and completed per area and year, 2012-2025
  district_profile.csv     DISTRICT_PROFILE     minimum-income benefit rate 2012-2025, registered cars 2025
  stadtteil_newbuild.csv   STADTTEIL_NEWBUILD   expected new-build movers 2025-2033 per Stadtteil (report M558)
  vgn_*.csv                VGN_*                the VGN GTFS feed; routes with line_mode / is_on_demand / is_night,
                                                stops with in_nuernberg, district_no, bezirk_no and the modes serving them
  vehicle_capacity.csv,    VEHICLE_CAPACITY,    copied from data/source/ when present (curated, with sources)
  line_capacity.csv        LINE_CAPACITY
  pt_service_cuts.csv,     PT_SERVICE_CUTS,     VAG's proposed service cuts (packages P1-P5) as rules per line and day type,
  pt_savings_packages.csv  PT_SAVINGS_PACKAGES  and the five savings packages P1-P5 with VAG's estimates; copied from
                                                data/source/ (digitized by scripts/digitize_vag_cuts_2027.py)

Pure standard library.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import math
import re
import struct
import sys
import zipfile
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
REPO = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------- geo
# The Bezirke shapefile is DHDN / Gauss-Krueger zone 4 (EPSG:31468, Bessel ellipsoid). Converting it needs a
# datum shift, not just a projection: Bessel/DHDN and WGS84 differ by ~100 m around Nuernberg.
BESSEL_A, BESSEL_F = 6377397.155, 1 / 299.1528128
WGS_A, WGS_F = 6378137.0, 1 / 298.257223563
# DHDN -> WGS84, 7-parameter Helmert (position vector), the PROJ +towgs84 values for EPSG:31468. ~1-3 m accuracy.
HELMERT = (598.1, 73.7, 418.2, 0.202, 0.045, -2.455, 6.7)


def gk_to_bessel(easting: float, northing: float, lon0_deg: float = 12.0, false_e: float = 4_500_000.0):
    """Inverse transverse Mercator on the Bessel ellipsoid (scale 1.0). Returns (lat, lon) in radians."""
    a, f = BESSEL_A, BESSEL_F
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    x, y = easting - false_e, northing
    mu = y / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu)
            + (1097 * e1**4 / 512) * math.sin(8 * mu))
    n1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2)
    t1 = math.tan(phi1) ** 2
    c1 = ep2 * math.cos(phi1) ** 2
    r1 = a * (1 - e2) / (1 - e2 * math.sin(phi1) ** 2) ** 1.5
    d = x / n1
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720)
    lon = math.radians(lon0_deg) + (d - (1 + 2 * t1 + c1) * d**3 / 6
                                    + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120) / math.cos(phi1)
    return lat, lon


def _to_ecef(lat, lon, a, f):
    e2 = f * (2 - f)
    n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    return (n * math.cos(lat) * math.cos(lon), n * math.cos(lat) * math.sin(lon), n * (1 - e2) * math.sin(lat))


def _from_ecef(x, y, z, a, f):
    e2 = f * (2 - f)
    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - e2))
    for _ in range(6):
        n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        lat = math.atan2(z + e2 * n * math.sin(lat), p)
    return lat, lon


def gk4_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    """EPSG:31468 -> WGS84 (lat, lon) in degrees."""
    lat, lon = gk_to_bessel(easting, northing)
    x, y, z = _to_ecef(lat, lon, BESSEL_A, BESSEL_F)
    tx, ty, tz, rx, ry, rz, s = HELMERT
    rx, ry, rz = (math.radians(v / 3600) for v in (rx, ry, rz))
    k = 1 + s * 1e-6
    x2 = tx + k * (x - rz * y + ry * z)
    y2 = ty + k * (rz * x + y - rx * z)
    z2 = tz + k * (-ry * x + rx * y + z)
    lat, lon = _from_ecef(x2, y2, z2, WGS_A, WGS_F)
    return round(math.degrees(lat), 6), round(math.degrees(lon), 6)


def read_shapefile(zip_path: Path):
    """Polygon shapefile + dbf from a zip -> list of (attributes, [ring of (x, y)])."""
    with zipfile.ZipFile(zip_path) as z:
        shp_name = next(n for n in z.namelist() if n.lower().endswith(".shp"))
        shp = z.read(shp_name)
        dbf = z.read(shp_name[:-4] + ".dbf")
    # dbf
    n, header_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields, i = [], 32
    while dbf[i] != 0x0D:
        fields.append((dbf[i:i + 11].split(b"\0")[0].decode(), dbf[i + 16]))
        i += 32
    records, off = [], header_len
    for _ in range(n):
        rec, o, attrs = dbf[off + 1:off + rec_len], 0, {}
        for name, length in fields:
            attrs[name] = rec[o:o + length].decode("latin1").strip()
            o += length
        records.append(attrs)
        off += rec_len
    # shp: 100-byte header, then records (big-endian header, little-endian content)
    shapes, pos = [], 100
    while pos < len(shp):
        _, length = struct.unpack(">ii", shp[pos:pos + 8])
        content = shp[pos + 8:pos + 8 + 2 * length]
        pos += 8 + 2 * length
        if struct.unpack("<i", content[:4])[0] != 5:
            raise ValueError("expected polygon shapes (type 5)")
        nparts, npoints = struct.unpack("<ii", content[36:44])
        parts = list(struct.unpack(f"<{nparts}i", content[44:44 + 4 * nparts])) + [npoints]
        pts_off = 44 + 4 * nparts
        pts = [struct.unpack("<dd", content[pts_off + 16 * k:pts_off + 16 * (k + 1)]) for k in range(npoints)]
        shapes.append([pts[parts[k]:parts[k + 1]] for k in range(nparts)])
    return list(zip(records, shapes))


def ring_area_xy(ring):
    return sum(ring[k][0] * ring[k + 1][1] - ring[k + 1][0] * ring[k][1] for k in range(len(ring) - 1)) / 2


def point_in_ring(lat, lon, ring):
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        yi, xi = ring[i]
        yj, xj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-18) + xi:
            inside = not inside
        j = i
    return inside


def polygons_wkt(polys):
    """polys: list of (outer ring, [hole rings]) with (lat, lon) points -> POLYGON / MULTIPOLYGON WKT (lon lat)."""
    def ring_txt(r):
        r = r if r[0] == r[-1] else r + [r[0]]
        return "(" + ", ".join(f"{lon} {lat}" for lat, lon in r) + ")"
    parts = ["(" + ", ".join(ring_txt(r) for r in [outer] + holes) + ")" for outer, holes in polys]
    return "POLYGON" + parts[0] if len(parts) == 1 else "MULTIPOLYGON(" + ", ".join(parts) + ")"


def group_rings(rings_xy):
    """Shapefile rings -> [(outer, [holes])]. Outer rings run clockwise (negative signed area), holes counter-clockwise."""
    outers = [r for r in rings_xy if ring_area_xy(r) < 0]
    holes = [r for r in rings_xy if ring_area_xy(r) >= 0]
    polys = [(o, []) for o in outers]
    for h in holes:
        hx, hy = h[0]
        for o, hs in polys:
            if point_in_ring(hy, hx, [(y, x) for x, y in o]):
                hs.append(h)
                break
    return polys


class AreaIndex:
    """Even-odd point-in-polygon over every ring of a feature, so holes are respected."""

    def __init__(self):
        self.items = []  # (key, rings_ll, bbox)

    def add(self, key, rings_ll):
        lats = [p[0] for r in rings_ll for p in r]
        lons = [p[1] for r in rings_ll for p in r]
        self.items.append((key, rings_ll, (min(lats), max(lats), min(lons), max(lons))))

    def lookup(self, lat, lon):
        for key, rings, (la0, la1, lo0, lo1) in self.items:
            if la0 <= lat <= la1 and lo0 <= lon <= lo1:
                if sum(point_in_ring(lat, lon, r) for r in rings) % 2 == 1:
                    return key
        return None


# --------------------------------------------------------------------------- csv helpers
def write_csv(path: Path, header: list[str], rows) -> int:
    n = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")  # LF only: exapump passes CRLF through
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(h, "") for h in header])
            n += 1
    print(f"  wrote {path.name:<30} {n:>10,} rows")
    return n


def gtfs_rows(z: zipfile.ZipFile, name: str):
    with z.open(name) as fh:
        yield from csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig", newline=""))


# --------------------------------------------------------------------------- areas
STADTTEILE = {  # statistical Stadtteil = tens digit of the Bezirk number (Amt fuer Stadtforschung und Statistik)
    0: "Altstadt und engere Innenstadt", 1: "Weiterer Innenstadtguertel Sued",
    2: "Weiterer Innenstadtguertel West/Nord/Ost", 3: "Suedoestliche Aussenstadt", 4: "Suedliche Aussenstadt",
    5: "Suedwestliche Aussenstadt", 6: "Westliche Aussenstadt", 7: "Nordwestliche Aussenstadt",
    8: "Nordoestliche Aussenstadt", 9: "Oestliche Aussenstadt",
}
# Expected new-build movers 2025-2033 per Stadtteil, from the text of report M558 (p. 8-9). The city publishes
# the 2033 population per Stadtteil only as map circles, and nothing per Bezirk.
NEWBUILD_2025_2033 = {0: 2480, 1: 3550, 2: 2730, 3: 1980, 4: 11350, 5: 1730, 6: 12280, 7: 8960, 8: 1510, 9: 2550}
_M558 = ("Amt fuer Stadtforschung und Statistik fuer Nuernberg und Fuerth, Bericht M558: Kleinraeumige "
         "Bevoelkerungsvorausberechnung Nuernberg 2025-2033 (Stand Neubau: Stadtplanungsamt 05/2024) "
         "https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2025/"
         "sus2025_m558_bevolkerungsvorausberechnungnurnberg2024_online.pdf")
_ATLAS = ("Bezirksatlas Nuernberg, Amt fuer Stadtforschung und Statistik fuer Nuernberg und Fuerth, Melderegister "
          "31 Dec https://online-service2.nuernberg.de/geoinf/ia_bezirksatlas/atlas.html")


def load_atlas(folder: Path):
    """Bezirk -> atlas area name, plus per-area indicators. Small Bezirke share a feature name and the same values."""
    meta = json.loads((folder / "data.js").read_text(encoding="utf-8-sig"))
    feats = meta["geographies"][0]["features"]
    t0 = json.loads((folder / "Statistische_Bezirke-t0.js").read_text(encoding="utf-8-sig"))

    def values(name, date):
        for ind in t0["indicators"]:
            if ind["name"] == name and ind["date"] == date:
                return ind["values"]
        raise KeyError(f"atlas indicator {name} {date} not found")

    pop = {y: values("Bevölkerung mit Hauptwohnung", y) for y in ("2023", "2024", "2025")}
    ha = values("Fläche in ha", "2025")
    out = {}
    for k, f in enumerate(feats):
        out[int(f["id"])] = {"area_name": f["name"], "pop": {y: int(pop[y][k]) for y in pop}, "ha": ha[k]}
    return out


def build_areas(bezirke_zip: Path, atlas_dir: Path, out: Path):
    atlas = load_atlas(atlas_dir)
    by_bezirk: dict[int, dict] = {}
    for attrs, rings in read_shapefile(bezirke_zip):
        no = int(attrs["KRG_DISS"])
        b = by_bezirk.setdefault(no, {"bezirk_no": no, "bezirk_name": attrs["KRG_BEZ"], "rings_xy": [], "area_sqm": 0.0})
        b["rings_xy"].extend(rings)
        b["area_sqm"] += float(attrs["Shape_Area"])
    assert len(by_bezirk) == 87, f"expected 87 Bezirke, got {len(by_bezirk)}"
    assert set(by_bezirk) == set(atlas), "shapefile and Bezirksatlas disagree on the Bezirk numbers"

    # areas: Bezirke that share an atlas feature name form one area, numbered by their lowest Bezirk
    members: dict[str, list[int]] = {}
    for no in sorted(by_bezirk):
        members.setdefault(atlas[no]["area_name"], []).append(no)
    area_of = {no: min(ms) for ms in members.values() for no in ms}

    index = AreaIndex()
    bezirk_rows, polys_by_area = [], {}
    for no, b in sorted(by_bezirk.items()):
        polys_xy = group_rings(b["rings_xy"])
        polys_ll = [([gk4_to_wgs84(x, y) for x, y in o], [[gk4_to_wgs84(x, y) for x, y in h] for h in hs])
                    for o, hs in polys_xy]
        rings_ll = [r for o, hs in polys_ll for r in [o] + hs]
        index.add(no, rings_ll)
        polys_by_area.setdefault(area_of[no], []).extend(polys_ll)
        lat, lon = centroid_xy(b["rings_xy"])
        bezirk_rows.append({"bezirk_no": no, "bezirk_name": b["bezirk_name"], "district_no": area_of[no],
                            "stadtteil_no": no // 10, "area_km2": round(b["area_sqm"] / 1e6, 3),
                            "centroid_lat": lat, "centroid_lon": lon, "polygon_wkt": polygons_wkt(polys_ll)})
    write_csv(out / "bezirke.csv", ["bezirk_no", "bezirk_name", "district_no", "stadtteil_no", "area_km2",
                                    "centroid_lat", "centroid_lon", "polygon_wkt"], bezirk_rows)

    total_pop = sum(atlas[min(ms)]["pop"]["2025"] for ms in members.values())
    total_km2 = sum(atlas[min(ms)]["ha"] for ms in members.values()) / 100
    district_rows, pop_rows = [], []
    for name, ms in sorted(members.items(), key=lambda kv: min(kv[1])):
        a = atlas[ms[0]]
        km2 = a["ha"] / 100
        lat, lon = centroid_xy([r for m in ms for r in by_bezirk[m]["rings_xy"]])
        # one group (75/85/87) spans Stadtteile 7 and 8: the area takes the Stadtteil of most of its Bezirke
        st = max(sorted({m // 10 for m in ms}), key=lambda s: sum(m // 10 == s for m in ms))
        district_rows.append({
            "district_no": min(ms), "district_name": name, "bezirk_nos": ",".join(f"{m:02d}" for m in ms),
            "stadtteil_no": st, "stadtteil_name": STADTTEILE[st],
            "population": a["pop"]["2025"], "population_pct": round(100 * a["pop"]["2025"] / total_pop, 2),
            "area_km2": round(km2, 3), "area_pct": round(100 * km2 / total_km2, 2),
            "density_per_km2": round(a["pop"]["2025"] / km2) if km2 else "",
            "centroid_lat": lat, "centroid_lon": lon, "polygon_wkt": polygons_wkt(polys_by_area[min(ms)])})
        pop_rows.append({"district_no": min(ms), "district_name": name, "pop_2023": a["pop"]["2023"],
                         "pop_2024": a["pop"]["2024"], "pop_2025": a["pop"]["2025"], "source": _ATLAS})
    write_csv(out / "districts.csv", ["district_no", "district_name", "bezirk_nos", "stadtteil_no", "stadtteil_name",
                                      "population", "population_pct", "area_km2", "area_pct", "density_per_km2",
                                      "centroid_lat", "centroid_lon", "polygon_wkt"], district_rows)
    st_of_area = {r["district_no"]: r["stadtteil_no"] for r in district_rows}
    homes = newbuild_homes(area_of)
    model_2033(pop_rows, st_of_area, homes)
    write_csv(out / "district_population.csv",
              ["district_no", "district_name", "pop_2023", "pop_2024", "pop_2025", "newbuild_homes_2024_2033",
               "pop_2033_model", "source", "method_2033"], pop_rows)
    write_csv(out / "stadtteil_forecast.csv",
              ["stadtteil_no", "stadtteil_name", "pop_2024_areas", "pop_2033_forecast", "newbuild_movers_2025_2033",
               "pop_2035_forecast_m529", "source"], stadtteil_rows(pop_rows, st_of_area))
    write_csv(out / "district_employment.csv", EMPLOYMENT_HEADER, district_jobs(district_rows))
    write_csv(out / "district_housing.csv", HOUSING_HEADER, district_housing(district_rows))
    write_csv(out / "district_profile.csv", PROFILE_HEADER, district_profile(district_rows))
    write_csv(out / "newbuild_projects.csv", NEWBUILD_HEADER, newbuild_rows(area_of))
    print(f"  {len(district_rows)} areas from {len(by_bezirk)} Bezirke, population 2025 {total_pop:,}, "
          f"2033 model {sum(r['pop_2033_model'] for r in pop_rows):,}")
    return index, area_of


# --------------------------------------------------------------------------- growth and jobs (curated, data/source/)
SOURCE = REPO / "data" / "source"
# M558 forecast 2033 per Stadtteil (text, PDF p. 11 for 00-02, p. 16 for 03-09; sums to 554,710) and the previous
# edition M529 for 2035 (pp. 15/18). Transcribed in data/source/stadtteil_forecast_sources.csv.
_M529 = ("Amt fuer Stadtforschung und Statistik, Bericht M529 (base 2021, horizon 2035) "
         "https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2022/sus_bericht_m529.pdf")
_WFS = ("Stadt Nuernberg, Schwerpunkte des Wohnungsneubaus (WFS Wohnungsneubau:Schwerpunkte_des_Wohnungsneubaus, "
        "https://geoportal.nuernberg.de/masterportal/wohnbau/), retrieved 2026-10-28")
METHOD_2033 = ("Model, not a published figure. The city forecasts 2033 only per Stadtteil (M558). Per area: the "
               "Stadtteil's new-build movers 2025-2033 (M558) are split by the area's share of the Stadtteil's new homes "
               "first occupied 2024-2033 (city WFS), at most 2 persons per listed home; the rest of the Stadtteil's change by the "
               "area's share of 2024 "
               "residents. Stadtteil totals match M558; the base is the Bezirksatlas count, so 2024 totals differ from "
               "M558's reduced base by a few thousand.")
PERSONS_PER_HOME = 2.0  # assumption: about Nuernberg's average household size (~1.9) plus families in new builds
NEWBUILD_HEADER = ["project_id", "project_name", "homes_total", "first_occupancy", "bezirk_no", "district_no",
                   "share", "homes_in_bezirk", "centroid_lat", "centroid_lon", "developer", "source"]


def _forecast(edition: str, year: str) -> dict[int, int]:
    out = {}
    for r in csv.DictReader((SOURCE / "stadtteil_forecast_sources.csv").open(encoding="utf-8")):
        if r["edition"] == edition and r["year"] == year and r["kind"] == "forecast" and r["unit"] == "stadtteil":
            out[int(r["unit_no"])] = int(r["population"])
    assert len(out) == 10, f"{edition} {year}: expected 10 Stadtteile, got {len(out)}"
    return out


def _project_shares():
    """data/source/newbuild_projects.csv -> (project row, bezirk_no, share). Shares outside the city are dropped."""
    for r in csv.DictReader((SOURCE / "newbuild_projects.csv").open(encoding="utf-8")):
        for part in r["bezirk_shares_approx"].split(";"):
            bez, pct = part.split(":")
            if bez.strip().isdigit():
                yield r, int(bez), float(pct.rstrip("%")) / 100


def newbuild_rows(area_of):
    return [{"project_id": r["project_id_sta"], "project_name": r["project_name"], "homes_total": r["homes_total"],
             "first_occupancy": r["first_occupancy"], "bezirk_no": bez, "district_no": area_of[bez], "share": share,
             "homes_in_bezirk": round(int(r["homes_total"]) * share),
             "centroid_lat": r["centroid_lat"], "centroid_lon": r["centroid_lon"],  # of the whole project polygon
             "developer": r["developer"], "source": _WFS}
            for r, bez, share in _project_shares()]


def newbuild_homes(area_of) -> dict[int, float]:
    homes: dict[int, float] = {}
    for r, bez, share in _project_shares():
        if 2024 <= int(r["first_occupancy"]) <= 2033:
            homes[area_of[bez]] = homes.get(area_of[bez], 0) + int(r["homes_total"]) * share
    return homes


def model_2033(pop_rows, st_of_area, homes) -> None:
    f2033, movers = _forecast("M558", "2033"), NEWBUILD_2025_2033
    for st in STADTTEILE:
        rows = [r for r in pop_rows if st_of_area[r["district_no"]] == st]
        base = sum(r["pop_2024"] for r in rows)
        st_homes = sum(homes.get(r["district_no"], 0) for r in rows)
        # where the city's project list is incomplete, it can't carry all movers: at most PERSONS_PER_HOME per listed home
        via_projects = min(movers[st], PERSONS_PER_HOME * st_homes)
        rest = f2033[st] - base - via_projects
        for r in rows:
            pop_share = r["pop_2024"] / base
            home_share = homes.get(r["district_no"], 0) / st_homes if st_homes else 0
            r["newbuild_homes_2024_2033"] = round(homes.get(r["district_no"], 0))
            r["pop_2033_model"] = round(r["pop_2024"] + via_projects * home_share + rest * pop_share)
            r["method_2033"] = METHOD_2033


def stadtteil_rows(pop_rows, st_of_area):
    f2033, f2035 = _forecast("M558", "2033"), _forecast("M529", "2035")
    return [{"stadtteil_no": st, "stadtteil_name": name,
             "pop_2024_areas": sum(r["pop_2024"] for r in pop_rows if st_of_area[r["district_no"]] == st),
             "pop_2033_forecast": f2033[st], "newbuild_movers_2025_2033": NEWBUILD_2025_2033[st],
             "pop_2035_forecast_m529": f2035[st], "source": _M558 + " | " + _M529} for st, name in STADTTEILE.items()]


EMPLOYMENT_HEADER = ["district_no", "district_name", "bezirk_nos",
                     "jobs_2019", "jobs_2020", "jobs_2021", "jobs_2022", "jobs_2023", "jobs_2024",
                     "establishments_2019", "establishments_2024", "establishments_2024_secondary",
                     "establishments_2024_tertiary",
                     "jobs_2005", "jobs_2005_industry", "jobs_2005_trade_transport", "jobs_2005_services",
                     "basis", "source"]
_STATISTIK = ("Amt fuer Stadtforschung und Statistik fuer Nuernberg und Fuerth, Nuernberg in Zahlen "
              "https://online-service2.nuernberg.de/Informationsportal11_nbg/")


def _by_area_year(name):
    """data/source/<name>.csv (from scripts/fetch_nuernberg_statistik.py) keyed by (district_no, year)."""
    return {(int(r["district_no"]), int(r["year"])): r
            for r in csv.DictReader((SOURCE / name).open(encoding="utf-8"))}


def district_jobs(district_rows):
    jobs = {int(r["bezirk_no"]): r for r in csv.DictReader((SOURCE / "bezirk_jobs_2005.csv").open(encoding="utf-8"))}
    new = _by_area_year("district_jobs_2019_2024.csv")
    out = []
    for d in district_rows:
        ms = [int(b) for b in d["bezirk_nos"].split(",")]
        src = jobs[ms[0]]
        no = d["district_no"]
        row = {"district_no": no, "district_name": d["district_name"], "bezirk_nos": d["bezirk_nos"]}
        for y in range(2019, 2025):
            row[f"jobs_{y}"] = int(new[(no, y)]["sv_jobs"])
        row.update({
            "establishments_2019": int(new[(no, 2019)]["establishments_total"]),
            "establishments_2024": int(new[(no, 2024)]["establishments_total"]),
            "establishments_2024_secondary": int(new[(no, 2024)]["establishments_secondary"]),
            "establishments_2024_tertiary": int(new[(no, 2024)]["establishments_tertiary"]),
            "jobs_2005": sum(int(jobs[m]["value"]) for m in ms),
            "jobs_2005_industry": sum(int(jobs[m]["value_produzierendes_gewerbe"]) for m in ms),
            "jobs_2005_trade_transport": sum(int(jobs[m]["value_handel_verkehr_nachrichten"]) for m in ms),
            "jobs_2005_services": sum(int(jobs[m]["value_dienstleistungen"]) for m in ms),
            "basis": ("jobs_2019..jobs_2024: employees subject to social insurance at place of work, 31 Dec, from the "
                      "business register (no civil servants, self-employed or marginal jobs); 6,851 jobs in 2024 "
                      "are not assigned to an area. establishments_*: business register, secondary = industry and "
                      "construction, tertiary = services. jobs_2005*: workers at place of work 2005 (employees and "
                      "self-employed incl. marginal jobs, city total 342,000), before the AEG (2007) and Quelle "
                      "(2009) closures in Bezirk 64; a wider definition, so 2005 and 2024 are not directly "
                      "comparable"),
            "source": (f"{_STATISTIK} tables WASU_SvBs_AO_zbez, WASU_Niederlassungen_Wirtschaftssektoren_zbez | "
                       f"2005: {src['source_url']} ({src['source_page']})")})
        out.append(row)
    assert sum(r["jobs_2005"] for r in out) == 342_000, "area jobs do not add up to the 2005 city total"
    assert sum(r["jobs_2024"] for r in out) + int(new[(0, 2024)]["sv_jobs"]) == 308_224, "2024 jobs do not add up"
    return out


HOUSING_HEADER = ["district_no", "district_name", "year", "homes_permitted", "homes_completed",
                  "floor_area_m2_permitted", "floor_area_m2_completed", "source"]


def district_housing(district_rows):
    """Homes permitted and completed per area and year, 2012-2025 (building statistics, net of conversions)."""
    src = _by_area_year("district_housing_2012_2025.csv")
    out = []
    for d in district_rows:
        for y in range(2012, 2026):
            r = src[(d["district_no"], y)]
            out.append({"district_no": d["district_no"], "district_name": d["district_name"], "year": y,
                        "homes_permitted": int(r["homes_permitted"]), "homes_completed": int(r["homes_completed"]),
                        "floor_area_m2_permitted": int(r["floor_area_m2_permitted"]),
                        "floor_area_m2_completed": int(r["floor_area_m2_completed"]),
                        "source": f"{_STATISTIK} tables WPG_GBGG_03_zbez, WPG_GBGF_03_zbez (Bautaetigkeitsstatistik)"})
    return out


PROFILE_HEADER = ["district_no", "district_name", "year", "min_income_rate_pct", "cars", "cars_ev",
                  "cars_per_1000_residents", "source"]


def district_profile(district_rows):
    """Minimum-income benefit rate per area and year 2012-2025; registered cars for 2025 (district PDF sheets)."""
    rate = _by_area_year("district_min_income_rate.csv")
    cars = {int(r["bezirk_no"]): r for r in csv.DictReader((SOURCE / "bezirk_cars_2025.csv").open(encoding="utf-8"))}
    out = []
    for d in district_rows:
        ms = [int(b) for b in d["bezirk_nos"].split(",")]
        for y in range(2012, 2026):
            row = {"district_no": d["district_no"], "district_name": d["district_name"], "year": y,
                   "min_income_rate_pct": rate[(d["district_no"], y)]["min_income_rate_pct"],
                   "cars": "", "cars_ev": "", "cars_per_1000_residents": "",
                   "source": f"{_STATISTIK} table SMOS_mindessicherung_zbez"}
            if y == 2025:
                n = sum(int(cars[m]["cars"]) for m in ms)
                pop = sum(int(cars[m]["residents"]) for m in ms)
                assert pop == d["population"], (d["district_name"], pop, d["population"])
                row.update(cars=n, cars_ev=sum(int(cars[m]["cars_ev"]) for m in ms),
                           cars_per_1000_residents=round(1000 * n / pop) if pop else "",
                           source=row["source"] + " | cars: Bezirksdatenblaetter 2025 "
                                  "https://www.nuernberg.de/internet/statistik/bezirksdatenblaetter_nbg_2025.html")
            out.append(row)
    return out


def centroid_xy(rings_xy):
    """Area-weighted centroid of the outer rings (GK coordinates), converted to WGS84."""
    cx = cy = at = 0.0
    for r in rings_xy:
        a = ring_area_xy(r)
        if a >= 0:  # holes
            continue
        for k in range(len(r) - 1):
            cross = r[k][0] * r[k + 1][1] - r[k + 1][0] * r[k][1]
            cx += (r[k][0] + r[k + 1][0]) * cross
            cy += (r[k][1] + r[k + 1][1]) * cross
        at += a
    return gk4_to_wgs84(cx / (6 * at), cy / (6 * at))


# --------------------------------------------------------------------------- transit
LINE_MODES = ["S-Bahn", "U-Bahn", "Regional rail", "Tram", "Bus"]  # highest capacity first
MODE_FLAGS = {"S-Bahn": "serves_sbahn", "U-Bahn": "serves_ubahn", "Regional rail": "serves_regional_rail",
              "Tram": "serves_tram", "Bus": "serves_bus"}
ON_DEMAND = {"Rufbus", "Anrufsammeltaxi", "Linienbedarfstaxi", "Linientaxi"}


def line_mode(route: dict) -> str:
    """VGN uses plain GTFS route types; S-Bahn is route_type 2 with route_desc 'S-Bahn'."""
    t, desc, name = route["route_type"], route.get("route_desc", ""), route.get("route_short_name", "")
    if t == "2":
        return "S-Bahn" if desc == "S-Bahn" or re.match(r"^S\d+$", name) else "Regional rail"
    return {"0": "Tram", "1": "U-Bahn", "3": "Bus"}.get(t, "Other")


def build_transit(gtfs_zip: Path, index: AreaIndex, area_of: dict, out: Path, skip_stop_times: bool) -> None:
    with zipfile.ZipFile(gtfs_zip) as z:
        names = set(z.namelist())
        routes = list(gtfs_rows(z, "routes.txt"))
        for r in routes:
            r["line_mode"] = line_mode(r)
            r["is_on_demand"] = "1" if r.get("route_desc") in ON_DEMAND else "0"
            r["is_night"] = "1" if re.match(r"^N\d+", r.get("route_short_name", "")) else "0"
        write_csv(out / "vgn_routes.csv", list(routes[0].keys()), routes)
        route_mode = {r["route_id"]: r["line_mode"] for r in routes}

        trips = list(gtfs_rows(z, "trips.txt"))
        write_csv(out / "vgn_trips.csv", list(trips[0].keys()), trips)
        trip_mode = {t["trip_id"]: route_mode.get(t["route_id"], "Other") for t in trips}
        del trips

        stop_modes: dict[str, set[str]] = {}
        if not skip_stop_times:
            print("  copying stop_times and collecting the modes serving each stop ...")
            with z.open("stop_times.txt") as src, (out / "vgn_stop_times.csv").open("w", newline="", encoding="utf-8") as dst:
                rdr = csv.reader(io.TextIOWrapper(src, encoding="utf-8-sig", newline=""))
                w = csv.writer(dst, lineterminator="\n")
                header = next(rdr)
                w.writerow(header)
                i_trip, i_stop, n = header.index("trip_id"), header.index("stop_id"), 0
                for row in rdr:
                    w.writerow(row)
                    stop_modes.setdefault(row[i_stop], set()).add(trip_mode.get(row[i_trip], "Other"))
                    n += 1
            print(f"  wrote {'vgn_stop_times.csv':<30} {n:>10,} rows")

        stops = list(gtfs_rows(z, "stops.txt"))
        for s in stops:
            parent = s.get("parent_station", "")
            if parent and s["stop_id"] in stop_modes:
                stop_modes.setdefault(parent, set()).update(stop_modes[s["stop_id"]])
        inside = 0
        for s in stops:
            try:
                bez = index.lookup(float(s["stop_lat"]), float(s["stop_lon"]))
            except ValueError:
                bez = None
            s["in_nuernberg"] = "1" if bez is not None else "0"
            s["bezirk_no"] = "" if bez is None else bez
            s["district_no"] = "" if bez is None else area_of[bez]
            inside += bez is not None
            modes = stop_modes.get(s["stop_id"], set())
            ordered = [m for m in LINE_MODES if m in modes]
            s["stop_mode"] = ordered[0] if ordered else ""
            s["stop_modes"] = "|".join(ordered)
            for m, col in MODE_FLAGS.items():
                s[col] = "1" if m in modes else "0"
        write_csv(out / "vgn_stops.csv", list(stops[0].keys()), stops)
        print(f"  {inside:,} of {len(stops):,} stops inside Nuernberg")

        for name in sorted(names - {"routes.txt", "trips.txt", "stops.txt", "stop_times.txt"}):
            if name.endswith(".txt"):
                rows = list(gtfs_rows(z, name))
                for r in rows:  # GTFS YYYYMMDD -> YYYY-MM-DD, so the loader types them as DATE
                    for col in ("start_date", "end_date", "date"):
                        if re.fullmatch(r"\d{8}", r.get(col, "")):
                            r[col] = f"{r[col][:4]}-{r[col][4:6]}-{r[col][6:]}"
                if rows:
                    write_csv(out / f"vgn_{name[:-4]}.csv", list(rows[0].keys()), rows)


# --------------------------------------------------------------------------- cycling
def path_type(t: dict) -> str:
    """OSM tags -> the path types used for the cycling quality weights."""
    hw = t.get("highway", "")
    if t.get("bicycle_road") == "yes" or t.get("cyclestreet") == "yes":
        return "Cycle street (Fahrradstrasse)"
    if hw == "cycleway":
        return "Cycle track (Radweg)"
    if hw in ("path", "footway", "track"):
        if t.get("foot") == "designated" and t.get("segregated") == "yes":
            return "Separated cycle and footpath"
        if t.get("foot") == "designated" or hw == "footway":
            return "Shared footpath (Gemeinsamer Geh- und Radweg)"
        return "Cycle track (Radweg)" if hw == "path" else "Field or forest track, cycling designated"
    sides = [t.get(k, "") for k in ("cycleway", "cycleway:both", "cycleway:left", "cycleway:right")]
    if "track" in sides or "opposite_track" in sides:
        return "Cycle track along a road (Radweg)"
    if "lane" in sides or "opposite_lane" in sides:
        return "Painted lane (Radfahr-/Schutzstreifen)"
    return "Shared lane or bus lane"


def directions(t: dict) -> int:
    """How many travel directions a way serves for cycling: 2 for a two-way path or lanes on both sides."""
    hw = t.get("highway", "")
    if hw in ("cycleway", "path", "footway", "track") or t.get("bicycle_road") == "yes" or t.get("cyclestreet") == "yes":
        return 1 if t.get("oneway") == "yes" and t.get("oneway:bicycle") != "no" else 2
    if t.get("cycleway") or t.get("cycleway:both"):
        return 2
    return sum(1 for k in ("cycleway:left", "cycleway:right") if t.get(k) not in (None, "", "no", "separate"))


def haversine_m(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def cycling_rows(osm_json: Path, index: AreaIndex, area_of: dict):
    rows = []
    with gzip.open(osm_json, "rt", encoding="utf-8") as fh:
        elements = json.load(fh)["elements"]
    for e in elements:
        pts = [(p["lat"], p["lon"]) for p in e.get("geometry", [])]
        if e.get("type") != "way" or len(pts) < 2:
            continue
        length = sum(haversine_m(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
        acc, mid = 0.0, pts[0]
        for k in range(len(pts) - 1):  # midpoint along the line, for the area tag
            step = haversine_m(pts[k], pts[k + 1])
            if acc + step >= length / 2:
                f = (length / 2 - acc) / step if step else 0
                mid = (pts[k][0] + f * (pts[k + 1][0] - pts[k][0]), pts[k][1] + f * (pts[k + 1][1] - pts[k][1]))
                break
            acc += step
        bez = index.lookup(*mid)
        if bez is None:  # the Overpass query covers a bbox; keep the ways inside the city
            continue
        t = e.get("tags", {})
        rows.append({"segment_id": e["id"], "street": t.get("name", ""), "length_m": round(length, 1),
                     "path_type": path_type(t), "directions": directions(t), "highway": t.get("highway", ""),
                     "surface": t.get("surface", ""),
                     "start_lat": round(pts[0][0], 6), "start_lon": round(pts[0][1], 6),
                     "end_lat": round(pts[-1][0], 6), "end_lon": round(pts[-1][1], 6),
                     "mid_lat": round(mid[0], 6), "mid_lon": round(mid[1], 6),
                     "bezirk_no": bez, "district_no": area_of[bez]})
    return rows


WEATHER_COLS = {"TNK": "temp_min_c", "TXK": "temp_max_c", "TMK": "temp_mean_c", "RSK": "rain_mm",
                "SDK": "sunshine_hours", "NM": "cloud_cover_pct", "SHK_TAG": "snow_depth_cm", "FM": "wind_mean_ms"}


def weather_rows(folder: Path, since: str = "2025-01-01"):
    """DWD daily climate (kl) for station 03668; the 'recent' file fills in after the quality-checked history."""
    days: dict[str, dict] = {}
    for name, label in (("tageswerte_KL_03668_akt.zip", "recent"), ("tageswerte_KL_03668_hist.zip", "historical")):
        with zipfile.ZipFile(folder / name) as z:
            prod = next(n for n in z.namelist() if n.startswith("produkt_klima_tag"))
            rdr = csv.DictReader(io.TextIOWrapper(z.open(prod), encoding="latin1"), delimiter=";")
            for r in rdr:
                r = {k.strip(): (v or "").strip() for k, v in r.items()}
                d = f"{r['MESS_DATUM'][:4]}-{r['MESS_DATUM'][4:6]}-{r['MESS_DATUM'][6:8]}"
                if d < since:
                    continue
                row = {"count_date": d, "source": label}
                for col, out_col in WEATHER_COLS.items():
                    v = r.get(col, "")
                    if v in ("", "-999"):
                        row[out_col] = ""
                    elif col == "NM":
                        row[out_col] = round(float(v) / 8 * 100, 1)  # oktas -> percent
                    else:
                        row[out_col] = float(v)
                days[d] = row  # historical (read second) wins where both have the day
    return [days[d] for d in sorted(days)]


def counter_rows(folder: Path, index: AreaIndex, area_of: dict, weather: list[dict]):
    sites = json.loads((folder / "counters.json").read_text(encoding="utf-8"))
    stations = []
    for s in sites:
        m = re.search(r"\((RZG\d+)\)", s["name"])
        loc = s.get("location") or {"lat": s.get("latitude"), "lon": s.get("longitude")}  # both page formats
        lat, lon = loc["lat"], loc["lon"]
        bez = index.lookup(lat, lon)
        note = re.sub(r"<[^>]+>", "", s.get("description") or "").strip()
        stations.append({"station": m.group(1) if m else str(s["id"]), "station_name": s["name"].split(" (")[0],
                         "site_id": s["id"], "lat": lat, "lon": lon, "bezirk_no": "" if bez is None else bez,
                         "district_no": "" if bez is None else area_of[bez], "in_nuernberg": 0 if bez is None else 1,
                         "first_data": s.get("firstData", "")[:10], "last_data": s.get("lastData", "")[:10], "note": note})
    by_site = {s["site_id"]: s["station"] for s in stations}
    wx = {w["count_date"]: w for w in weather}
    counts = []
    for r in csv.DictReader((folder / "counts.csv").open(encoding="utf-8")):
        total = int(r["total"]) if r["total"] else None
        w = wx.get(r["count_date"], {})
        counts.append({"count_date": r["count_date"], "station": by_site[int(r["site_id"])],
                       # the counter pages report an outage as 0: a day with no bikes at all is treated as missing
                       "dir_in": r["in"] if total else "", "dir_out": r["out"] if total else "",
                       "total": total if total else "", "zero_reported": 1 if total == 0 else 0,
                       **{k: w.get(k, "") for k in ("temp_min_c", "temp_max_c", "rain_mm", "sunshine_hours", "cloud_cover_pct")}})
    return stations, counts


# --------------------------------------------------------------------------- roadworks (SÖR construction coordination)
_SOER_SRC = ("Stadt Nuernberg, SOER Baukoordination (geoportal.nuernberg.de, Fachdaten_G/SOER_BAUKOP_G_V), "
             "(c) Stadt Nuernberg, no open licence stated")
UTILITY_KINDS = {"Tele", "Strom", "Gas", "Wasser", "Fernwärme", "Kanal"}
CYCLING_WORK = re.compile(r"Radweg|Radverkehr|Fahrradstr|RVR|Radschnell|Radvorrang|Radfahr|Schutzstreifen|Radabstell|Radstreifen",
                          re.I)
TRAM_TRACK_WORK = re.compile(r"Gleis|Schiene|Straßenbahn|Tram", re.I)


def geojson_wkt(g: dict) -> str:
    def ring(r):
        return "(" + ", ".join(f"{round(x, 6)} {round(y, 6)}" for x, y, *_ in r) + ")"
    t, c = g["type"], g["coordinates"]
    if t == "Polygon":
        return "POLYGON(" + ", ".join(ring(r) for r in c) + ")"
    if t == "MultiPolygon":
        return "MULTIPOLYGON(" + ", ".join("(" + ", ".join(ring(r) for r in p) + ")" for p in c) + ")"
    if t == "LineString":
        return "LINESTRING" + ring(c)
    if t == "MultiLineString":
        return "MULTILINESTRING(" + ", ".join(ring(r) for r in c) + ")"
    if t == "Point":
        return f"POINT({c[0]} {c[1]})"
    raise ValueError(f"unexpected geometry {t}")


def _vertices(g: dict):
    def walk(c):
        if isinstance(c[0], (int, float)):
            yield c
        else:
            for x in c:
                yield from walk(x)
    return list(walk(g["coordinates"]))


def _ms_date(v) -> str:
    """ArcGIS epoch milliseconds or 'YYYYMMDD' text -> 'YYYY-MM-DD'."""
    if v in (None, ""):
        return ""
    if isinstance(v, str):
        return f"{v[:4]}-{v[4:6]}-{v[6:8]}" if re.fullmatch(r"\d{8}", v) else ""
    import datetime
    return (datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=v)).date().isoformat()


def _located(g, index: AreaIndex, area_of: dict) -> dict:
    """Vertex-mean centroid and the area it falls in (works spanning several areas are filed under one)."""
    if not g:
        return {"centroid_lat": "", "centroid_lon": "", "bezirk_no": "", "district_no": "", "shape_wkt": ""}
    pts = _vertices(g)
    lon, lat = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    bez = index.lookup(lat, lon)
    return {"centroid_lat": round(lat, 6), "centroid_lon": round(lon, 6), "bezirk_no": "" if bez is None else bez,
            "district_no": "" if bez is None else area_of[bez], "shape_wkt": geojson_wkt(g)}


def soer_tables(folder: Path, index: AreaIndex, area_of: dict, out: Path) -> None:
    def feats(name):
        return json.loads((folder / name).read_text(encoding="utf-8"))["features"]

    works = []
    for f in feats("planned_works.geojson"):
        a, kind = f["properties"], f["properties"].get("MASSNAHMENART") or ""
        text = f"{a.get('BESCHREIBUNG') or ''} {kind}"
        works.append({"roadwork_id": a.get("AKZ"), "kind": kind, "description": (a.get("BESCHREIBUNG") or "").replace("\n", " "),
                      "utility": a.get("SPARTE") or "", "street": a.get("STRASSE") or "", "section": a.get("BEREICH") or "",
                      "road_type": a.get("STRASSENART") or "", "status": a.get("STATUS") or "",
                      "start_date": _ms_date(a.get("BEGINN")), "end_date": _ms_date(a.get("ENDE")),
                      "responsible": a.get("ZUSTAENDIGER") or "", "department": a.get("ABTEILUNG") or "",
                      "is_cycling": 1 if CYCLING_WORK.search(text) and kind not in UTILITY_KINDS else 0,
                      "is_tram_track": 1 if TRAM_TRACK_WORK.search(text) and kind not in UTILITY_KINDS else 0,
                      **_located(f.get("geometry"), index, area_of), "source": _SOER_SRC})
    write_csv(out / "roadworks.csv", list(works[0].keys()), works)
    permits = []
    for f in feats("permits.geojson"):
        a = f["properties"]
        permits.append({"permit_no": a.get("NUMMER"), "applicant": a.get("VERANLASSER") or "", "reason": a.get("ANLASS") or "",
                        "utility": a.get("SPARTE") or "", "street": a.get("STRASSE") or "", "section": a.get("BEREICH") or "",
                        "applied_date": _ms_date(a.get("ANTRAGSDATUM")), "start_date": _ms_date(a.get("BEGINN")),
                        "end_date": _ms_date(a.get("ENDE")), "status": a.get("STATUS") or "",
                        **_located(f.get("geometry"), index, area_of), "source": _SOER_SRC})
    write_csv(out / "roadwork_permits.csv", list(permits[0].keys()), permits)
    diversions = []
    for f in feats("diversions.geojson"):
        a = f["properties"]
        diversions.append({"diversion_id": a.get("VMS_ID"), "name": a.get("BEZEICHNUNG") or "", "kind": a.get("ART") or "",
                           "start_date": _ms_date(a.get("BEGINN")), "end_date": _ms_date(a.get("ENDE")),
                           **_located(f.get("geometry"), index, area_of), "source": _SOER_SRC})
    write_csv(out / "roadwork_diversions.csv", list(diversions[0].keys()), diversions)


# Planned rail and tram projects, one row per station and line -> PT_PROJECT_STATIONS. Curated with sources in
# data/source/pt_projects.csv; research notes in research/pt-projects-notes.md.
PT_HEADER = ["project_id", "project_name", "mode", "line", "station_name", "lat", "lon", "bezirk_no", "district_no",
             "station_is_new", "opening_year", "opening_year_risk", "opening_year_model", "opening_year_assumed",
             "status", "funded", "trains_per_hour_peak", "trains_per_hour_offpeak", "analog_line", "source_url",
             "verified", "note"]
DEFAULT_OPENING = 2040  # projects with no published year


def pt_project_rows(index: AreaIndex, area_of: dict):
    rows = []
    for r in csv.DictReader((SOURCE / "pt_projects.csv").open(encoding="utf-8")):
        bez = index.lookup(float(r["lat"]), float(r["lon"])) if r["lat"] and r["lon"] else None
        r["bezirk_no"] = "" if bez is None else bez
        r["district_no"] = "" if bez is None else area_of[bez]
        r["opening_year_model"] = r["opening_year"] or DEFAULT_OPENING
        r["opening_year_assumed"] = "0" if r["opening_year"] else "1"
        rows.append(r)
    return rows


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    raw = REPO / "data" / "nuernberg-raw"  # where scripts/fetch_nuernberg_sources.py puts them
    ap.add_argument("--gtfs", type=Path, default=raw / "vgn" / "GTFS.zip")
    ap.add_argument("--bezirke", type=Path, default=raw / "bezirke" / "geometrie_nue_stat_bezirke.zip")
    ap.add_argument("--atlas", type=Path, default=raw / "atlas")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "nuernberg-dataset")
    ap.add_argument("--skip-stop-times", action="store_true", help="leave out the ~150 MB GTFS stop_times file")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    print("areas")
    index, area_of = build_areas(args.bezirke, args.atlas, args.out)
    print("VGN GTFS")
    build_transit(args.gtfs, index, area_of, args.out, args.skip_stop_times)
    print("cycling")
    raw = args.gtfs.parent.parent
    osm = SOURCE / "osm_cycling_ways.json.gz"  # OSM snapshot (ODbL); scripts/fetch_nuernberg_sources.py --refresh-osm
    rows = cycling_rows(osm, index, area_of)
    write_csv(args.out / "cycling_infrastructure.csv", list(rows[0].keys()), rows)
    plan = SOURCE / "cycle_network_plan_2021.csv"  # digitized by scripts/digitize_radnetz_2021.py
    if plan.exists():
        rows = []
        for r in csv.DictReader(plan.open(encoding="utf-8")):
            bez = index.lookup(float(r["mid_lat"]), float(r["mid_lon"]))
            r["in_nuernberg"] = 0 if bez is None else 1
            r["bezirk_no"] = "" if bez is None else bez
            r["district_no"] = "" if bez is None else area_of[bez]
            rows.append(r)
        write_csv(args.out / "cycle_network_plan_2021.csv", list(rows[0].keys()), rows)
    weather = weather_rows(raw / "weather") if (raw / "weather").exists() else []
    if weather:
        write_csv(args.out / "weather_daily.csv", ["count_date", *WEATHER_COLS.values(), "source"], weather)
    counters = raw / "counters"
    if (counters / "counts.csv").exists():
        stations, counts = counter_rows(counters, index, area_of, weather)
        write_csv(args.out / "bike_count_stations.csv", list(stations[0].keys()), stations)
        if counts:
            write_csv(args.out / "bike_counts_daily.csv", list(counts[0].keys()), counts)
        else:
            print("  skip bike_counts_daily.csv: the counter pages returned no counts")
    else:
        print("  skip bike counters: not downloaded (run scripts/build_nuernberg_dataset.py again to add them)")
    print("roadworks (SÖR)")
    if (raw / "soer" / "planned_works.geojson").exists():
        soer_tables(raw / "soer", index, area_of, args.out)
    else:
        print("  skip roadworks: SÖR layers not downloaded (run scripts/build_nuernberg_dataset.py again to add them)")
    print("curated tables")
    write_csv(args.out / "pt_project_stations.csv", PT_HEADER, pt_project_rows(index, area_of))
    for name in ("vehicle_capacity.csv", "line_capacity.csv", "pt_service_cuts.csv", "pt_savings_packages.csv"):
        src = REPO / "data" / "source" / name
        if src.exists():
            # Rewrite with LF line endings: exapump passes CRLF through and the load fails.
            (args.out / name).write_bytes(src.read_bytes().replace(b"\r\n", b"\n"))
            print(f"  copied {name}")
        else:
            print(f"  skip {name}: not in data/source/ yet")


if __name__ == "__main__":
    main()
