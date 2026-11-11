#!/usr/bin/env python3
"""Fetch per-area tables from the city's statistics office into data/source/ (curated, committed).

    pip install pymupdf          # only for the car counts, read from the district PDF sheets
    python3 scripts/fetch_nuernberg_statistik.py
    python3 scripts/build_nuernberg_dataset.py

Sources, all from the Amt für Stadtforschung und Statistik für Nürnberg und Fürth:
- "Nürnberg in Zahlen" (https://online-service2.nuernberg.de/Informationsportal11_nbg/). Each table is served by the
  DUVA table viewer (aswn.dll) as HTML; tables with a year filter are fetched one year at a time.
    WASU_SvBs_AO_zbez                               employees subject to social insurance at place of work, 2019-2024
    WASU_Niederlassungen_Wirtschaftssektoren_zbez   establishments by sector, 2019-2024
    SMOS_mindessicherung_zbez                       minimum-income benefit rate, 2012-2025
    WPG_GBGG_03_zbez, WPG_GBGF_03_zbez              homes permitted and completed per year, 2012-2025
- Bezirksdatenblätter 2025 (https://www.nuernberg.de/internet/statistik/bezirksdatenblaetter_nbg_2025.html): one PDF per
  Bezirk with the cars registered there (31 Dec 2025).

All tables use the statistics office's 79 "zusammengefasste Statistische Bezirke", the same areas as DISTRICTS.
District numbers are the lowest member Bezirk ("41 - Rangierbahnhof/..." = 41/42/43); 0 = not assigned to an area.
No open licence is stated (see data/README.md).
"""
from __future__ import annotations

import argparse
import csv
import html
import http.cookiejar
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ASW = "https://online-service2.nuernberg.de/aswn/aswn.dll"
SHEETS = "https://www.nuernberg.de/internet/statistik/bezirksdatenblaetter_nbg_2025.html"
UA = {"User-Agent": "nuernberg-mobility-planning-agents (data prep)"}
YEARS = range(2012, 2026)


# --------------------------------------------------------------------------- DUVA table viewer
def _opener():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = list(UA.items())
    return op


def asw_page(name: str, year: int | None = None) -> str:
    """One table as HTML; with `year`, the table's (single) filter list set to that year."""
    op = _opener()
    page = op.open(f"{ASW}?aw=/Internet/{name}", timeout=90).read().decode("utf-8", "ignore")
    if year is None:
        return page
    form = {"Locale": "de_DE", "ActionCode": "30",
            "Session": re.search(r'name="Session" value="(\w+)"', page).group(1),
            "SessionCode": re.search(r'name="SessionCode" value="(\w+)"', page).group(1),
            re.search(r'<div id="(FD_\w+)" class="cssOptionList', page).group(1): str(year)}
    page = op.open(ASW + "/report", urllib.parse.urlencode(form).encode(), timeout=90).read().decode("utf-8", "ignore")
    assert f'= "{year}"' in html.unescape(page), f"{name}: filter {year} not applied"
    return page


def tables(page: str) -> list[list[list[str]]]:
    out = []
    for tab in re.findall(r"(?s)<table[^>]*>.*?</table>", page):
        rows = []
        for tr in re.findall(r"(?s)<tr.*?</tr>", tab):
            cells = [" ".join(html.unescape(re.sub("<[^>]+>", "", c)).split())
                     for c in re.findall(r"(?s)<t[dh][^>]*>(.*?)</t[dh]>", tr)]
            if cells:
                rows.append(cells)
        out.append(rows)
    return out


def num(s: str) -> int | float | str:
    s = re.sub(r"\s", "", s).replace(".", "").replace(",", ".")
    if s in ("-", ""):
        return 0
    return float(s) if "." in s else int(s)


def area_rows(rows):
    """Rows that start with an area label "NN - Name"."""
    for r in rows:
        m = re.match(r"(\d\d) - (.+)", r[0])
        if m:
            yield int(m.group(1)), m.group(2), r[1:]


# --------------------------------------------------------------------------- the tables
def jobs_and_establishments():
    page = asw_page("WASU_SvBs_AO_zbez")
    rows = [r for t in tables(page) for r in t]
    years = next(r for r in rows if r[0] == "Jahr")[1:]
    names, out = {}, {}
    for no, name, vals in area_rows(rows):
        names[no] = name
        for y, v in zip(years, vals):
            out[(no, int(y))] = {"sv_jobs": num(v)}
    # establishments: one tab per year ("Jahr: 2019" -> div report-1); per area secondary, tertiary, total
    page = asw_page("WASU_Niederlassungen_Wirtschaftssektoren_zbez")
    tabs = dict(re.findall(r'<a href="#(report-\d+)">Jahr: (\d{4})</a>', page))
    parts = re.split(r'<div id="(report-\d+)">', page)
    for tab_id, body in zip(parts[1::2], parts[2::2]):
        y = int(tabs[tab_id])
        for no, name, vals in area_rows([r for t in tables(body) for r in t]):
            assert len(vals) == 3, (no, vals)
            sec, ter, tot = (num(v) for v in vals)
            out.setdefault((no, y), {}).update(establishments_secondary=sec, establishments_tertiary=ter,
                                               establishments_total=tot)
    return names, out


def min_income(names):
    page = asw_page("SMOS_mindessicherung_zbez")
    rows = [r for t in tables(page) for r in t]
    years = [int(y) for y in next(r for r in rows if r[0] == "Jahr")[1:]]
    by_name = {v: k for k, v in names.items()}
    out = {}
    for r in rows:
        if r[0] in by_name and len(r) == len(years) + 1:
            for y, v in zip(years, r[1:]):
                out[(by_name[r[0]], y)] = num(v)
    assert len({k[0] for k in out}) == len([n for n in names if n]), "benefit rate: not every area matched"
    return out


def housing():
    out = {}
    for name, key in (("WPG_GBGG_03_zbez", "homes_permitted"), ("WPG_GBGF_03_zbez", "homes_completed")):
        for y in YEARS:
            page = asw_page(name, y)
            total = [t for t in tables(page) if any(r and r[0] == "Gesamt" for r in t)][-1]  # last block: all kinds
            for no, _, vals in area_rows(total):
                d = out.setdefault((no, y), {})
                d[key] = num(vals[-2])
                d[key.replace("homes", "floor_area_m2")] = num(vals[-1])
            city = next(r for r in total if r[0] == "Gesamt")
            assert sum(v.get(key, 0) for (n, yy), v in out.items() if yy == y) == num(city[-2]), (name, y)
            time.sleep(0.5)
    return out


def cars(names):
    import pymupdf  # noqa: PLC0415  (only needed here)
    links = re.findall(r'href="(/imperia/md/statistik/dokumente/bezirksdatenblatt/nbg/\d\d-[^"]+\.pdf)"',
                       urllib.request.urlopen(urllib.request.Request(SHEETS, headers=UA), timeout=60)
                       .read().decode("utf-8", "ignore"))
    out = []
    for link in sorted(set(links)):
        pdf = urllib.request.urlopen(urllib.request.Request("https://www.nuernberg.de" + link, headers=UA),
                                     timeout=60).read()
        lines = [x.strip() for x in pymupdf.open(stream=pdf, filetype="pdf")[0].get_text().splitlines()]
        head = next(x for x in lines if x.startswith("Datenblatt "))
        m = re.search(r"Datenblatt (\d{4}) für den Statistischen Bezirk (\d\d)-(.+)", head)
        i = lines.index("Pkw / Kombi")
        pop = next(x for x in lines if x.startswith("Bevölkerung1):"))
        ev = lines.index("mit Elektroantrieb8)")
        out.append({"bezirk_no": int(m.group(2)), "bezirk_name": m.group(3).strip(), "year": int(m.group(1)),
                    "residents": num(pop.split(":")[1].replace(" ", "")),
                    "cars": num(lines[i + 1].replace(" ", "")), "cars_ev": num(lines[ev + 1].replace(" ", "")),
                    "source": "https://www.nuernberg.de" + link})
        time.sleep(0.5)
    return out


def write(path: Path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(rows)
    print(f"  {path.relative_to(REPO)}: {len(rows)} rows")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=REPO / "data" / "source")
    ap.add_argument("--skip-cars", action="store_true", help="skip the PDF sheets (no PyMuPDF needed)")
    a = ap.parse_args()
    src = "Amt fuer Stadtforschung und Statistik fuer Nuernberg und Fuerth, Nuernberg in Zahlen, table "

    names, jobs = jobs_and_establishments()
    names[0] = "nicht zugeordnet"
    write(a.out / "district_jobs_2019_2024.csv",
          ["district_no", "district_name", "year", "sv_jobs", "establishments_secondary", "establishments_tertiary",
           "establishments_total", "source"],
          [{"district_no": no, "district_name": names[no], "year": y, **v,
            "source": src + "WASU_SvBs_AO_zbez, WASU_Niederlassungen_Wirtschaftssektoren_zbez (Unternehmensregister)"}
           for (no, y), v in sorted(jobs.items())])

    rate = min_income(names)
    write(a.out / "district_min_income_rate.csv", ["district_no", "district_name", "year", "min_income_rate_pct",
                                                   "source"],
          [{"district_no": no, "district_name": names[no], "year": y, "min_income_rate_pct": v,
            "source": src + "SMOS_mindessicherung_zbez"} for (no, y), v in sorted(rate.items())])

    homes = housing()
    write(a.out / "district_housing_2012_2025.csv",
          ["district_no", "district_name", "year", "homes_permitted", "floor_area_m2_permitted", "homes_completed",
           "floor_area_m2_completed", "source"],
          [{"district_no": no, "district_name": names[no], "year": y, "homes_permitted": v.get("homes_permitted", 0),
            "floor_area_m2_permitted": v.get("floor_area_m2_permitted", 0),
            "homes_completed": v.get("homes_completed", 0),
            "floor_area_m2_completed": v.get("floor_area_m2_completed", 0),
            "source": src + "WPG_GBGG_03_zbez, WPG_GBGF_03_zbez (Bautaetigkeitsstatistik)"}
           for no in sorted({n for n, _ in homes} | set(names)) for y in YEARS
           for v in [homes.get((no, y), {})]])

    if not a.skip_cars:
        write(a.out / "bezirk_cars_2025.csv", ["bezirk_no", "bezirk_name", "year", "residents", "cars", "cars_ev",
                                               "source"], cars(names))


if __name__ == "__main__":
    main()
