#!/usr/bin/env python3
"""Digitize VAG's proposed service cuts (Sparmaßnahmenpaket im VAG-Verkehrsangebot, packages P1-P5) into rules.

The city published the savings package for the public-transport service as a council document (Stadtrat Nürnberg,
planning status 27 Oct 2026, decision due 30 Nov 2026):
https://online-service2.nuernberg.de/buergerinfo/getfile.asp?id=947894&type=do

Page 1 lists five packages P1-P5 with VAG's own estimates (passengers lost, euros saved). Only P3 is detailed line by
line: pages 3-4 give the state from 8 March 2027, pages 5-6 the end state from 2 August 2027 ("Gesamtpaket /
Endzustand"). Each of those tables has one row per line and seven day-type columns (Mon-Thu, Fri, Sat, each outside
and in school holidays, and Sunday); a cell holds one or more short German statements.

This script
  1. reads the four table pages: rows from the drawn grid lines, columns from the header positions;
  2. splits each cell into statements and parses each statement into a rule the timetable can be cut with
     (line dropped, trips dropped in a time window, thinner headway in a time window, one trip of the day dropped)
     or marks it `not_modeled` (shortened routes, short runs, on-demand replacements, unnamed single trips);
  3. tags each rule with the first package whose measures on page 1 describe it (P1, P2 or P3; an interpretation,
     the tables don't mark it), and adds P4's three concrete measures as rules and P4's and P5's other measures as
     not modeled;
  4. writes data/source/pt_service_cuts.csv (-> table PT_SERVICE_CUTS), one row per rule, with the original text.

Each stage is a complete state, not a delta: to model "from August 2027", apply only the rows of stage 2027-08.
Two corrections are applied and noted on the rows, both where the end-state table disagrees with the summary on
page 2: the end-state table leaves the Mon-Thu and Fri cells of trams 4, 5 and 7 empty, but the summary lists
"Ausweitung der Schwachverkehrszeiten 4, 5, 7, 10, 11" for the end state too; and it has no row for bus 83, but the
summary lists "Zeitweiser Entfall von Linien 31, 40, 83" for the end state too. Those cells are carried over from
the March table. Line 67 (second-to-last evening trip, Mon-Thu, March only) is not in the summary at all and is left
as printed.

Needs PyMuPDF (not the standard library), so it is run once by a maintainer; the CSV is committed:

    pip install pymupdf
    python3 scripts/digitize_vag_cuts_2027.py
"""
from __future__ import annotations

import argparse
import csv
import re
import urllib.request
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parent.parent
PDF_URL = "https://online-service2.nuernberg.de/buergerinfo/getfile.asp?id=947894&type=do"
SOURCE = "Stadt Nürnberg, Sparmaßnahmenpaket im VAG-Verkehrsangebot (Planungsstand 27.10.2026), " + PDF_URL

STAGES = {  # page index (0-based) -> stage, effective date
    2: ("2027-03", "2027-03-08"), 3: ("2027-03", "2027-03-08"),
    4: ("2027-08", "2027-08-02"), 5: ("2027-08", "2027-08-02"),
}
# Day-type columns: left edge of the text in each column (page points) and the key used in the table.
COLUMNS = [(76, "mon_thu"), (184, "mon_thu_holidays"), (289, "fri"), (394, "fri_holidays"),
           (499, "sat"), (604, "sat_holidays"), (709, "sun")]
LABEL_X = (45, 76)        # the "Linie" column
END_OF_DAY = "30:00:00"   # open-ended windows; GTFS times run past 24:00
CARRY_OVER = {  # (line, day_type) -> why the March cell also holds for the end state
    **{(t, d): ("Carried over from the March table: the end-state table leaves this cell empty, but the summary on "
                "page 2 lists the longer off-peak periods for trams 4, 5, 7, 10 and 11 in the end state too.")
       for t in ("4", "5", "7") for d in ("mon_thu", "fri")},
    **{("83", d): ("Carried over from the March table: the end-state table has no row for line 83, but the summary "
                   "on page 2 lists its partial withdrawal in the end state too.")
       for d in ("mon_thu", "mon_thu_holidays", "fri", "fri_holidays", "sat", "sat_holidays", "sun")},
}

HEADER = ["cut_id", "package", "package_basis", "stage", "effective_date", "line", "line_mode", "day_type", "rule_type",
          "window_start", "window_end", "headway_old_min", "headway_new_min", "trip_rank", "modeled",
          "text_de", "model_note", "source_page", "source"]


def fetch(url: str, target: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "nuernberg-mobility-planning-agents"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        target.write_bytes(resp.read())


# --------------------------------------------------------------------------- table geometry
def row_bounds(page) -> list[float]:
    """y of every horizontal rule that crosses the line-label column."""
    ys = set()
    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] == "l" and abs(it[1].y - it[2].y) < 0.5:
                x0, x1, y = min(it[1].x, it[2].x), max(it[1].x, it[2].x), it[1].y
            elif it[0] == "re" and it[1].height < 1.5:
                x0, x1, y = it[1].x0, it[1].x1, it[1].y0
            else:
                continue
            if x0 <= LABEL_X[0] + 1 and x1 >= LABEL_X[1] - 1:
                ys.add(round(y, 1))
    return sorted(ys)


def text_lines(page):
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            if ln["dir"][0] < 0.9:  # rotated branch labels ("Straßenbahn", "Bus")
                continue
            t = " ".join("".join(s["text"] for s in ln["spans"]).split())
            if t:
                yield ln["bbox"], t


def column_of(x0: float) -> str | None:
    key = None
    for left, name in COLUMNS:
        if x0 >= left:
            key = name
    return key


def read_cells(page):
    """{line_label: {day_type: [statement, ...]}} for one table page."""
    bounds = row_bounds(page)
    rows: dict[int, dict] = {}
    for (x0, y0, x1, y1), t in text_lines(page):
        ym = (y0 + y1) / 2
        band = next((i for i in range(len(bounds) - 1) if bounds[i] <= ym < bounds[i + 1]), None)
        if band is None:
            continue
        r = rows.setdefault(band, {"label": None, "cells": {}})
        if LABEL_X[0] <= x0 < LABEL_X[1]:
            r["label"] = t
        else:
            col = column_of(x0)
            if col:
                r["cells"].setdefault(col, []).append((y0, t))
    out = {}
    for r in rows.values():
        if not r["label"] or r["label"].startswith(("Linie", "Betriebs")):
            continue
        cells = {}
        for col, parts in r["cells"].items():
            parts.sort()
            statements, last_y = [], None
            for y, t in parts:  # a wrapped line sits ~7 pt below, the next statement ~14 pt
                if statements and y - last_y < 10:
                    statements[-1] += " " + t
                else:
                    statements.append(t)
                last_y = y
            cells[col] = statements
        out[r["label"]] = cells
    return out


# --------------------------------------------------------------------------- statement parser
def hhmm(h: str, m: str | None = None) -> str:
    return f"{int(h):02d}:{int(m or 0):02d}:00"


T = r"(\d{1,2})(?:[:.](\d{2}))?"  # a time of day: 6, 6:00, 8.30


def headway_rule(text: str, start: str, end: str, new: float, old: float | None, note: str = "") -> dict:
    partial = re.search(r"\bbis [A-ZÄÖÜ]|zwischen|Teilen der Linie|Ende von Fahrten|gekürzt|Kurzfahrten", text)
    if partial and not note:
        note = ("Applied to every trip of the line in the window; the document describes the change for part of "
                "the route or for its short runs.")
    return {"rule_type": "headway", "window_start": start, "window_end": end,
            "headway_new_min": new, "headway_old_min": old, "model_note": note}


def parse(text: str) -> list[dict]:
    """One statement -> one or more rules."""
    s = re.sub(r"\s*Uhr\b", "", text).strip().rstrip(".")
    s = re.sub(r"(\d)'- Takt", r"\1'-Takt", s)
    s = re.sub(r"(\d)'-? ?[Ss]tatt", r"\1'- statt", s)
    s = re.sub(r"\s+", " ", s)

    def nm(note: str) -> list[dict]:
        return [{"rule_type": "not_modeled", "model_note": note}]

    # whole line dropped
    if re.fullmatch(r"entfällt", s):
        return [{"rule_type": "line_dropped"}]
    if s.startswith("entfällt; Linienwegänderung"):
        return [{"rule_type": "line_dropped", "model_note": "Line 83 is rerouted via Lohhof instead; the new "
                 "route is not modeled."}]
    if s.startswith("entfällt, Rufbus"):
        return [{"rule_type": "line_dropped", "model_note": "An on-demand bus (Rufbus) is offered instead; it has "
                 "no timetable and adds no capacity here."}]
    if s.startswith("reines Nightliner") or text.startswith("5:00 - 8:00: reines Nightliner"):
        return nm("Nightliner network instead of day service on weekend mornings; extra Nightliner trips are not "
                  "in the feed and are not added.")
    # trips dropped in a time window
    if m := re.fullmatch(rf"entfällt ?vor {T} & nach {T}", s) or re.fullmatch(rf"entfällt {T} & nach {T}", s):
        return [{"rule_type": "window_dropped", "window_start": "00:00:00", "window_end": hhmm(m[1], m[2])},
                {"rule_type": "window_dropped", "window_start": hhmm(m[3], m[4]), "window_end": END_OF_DAY}]
    if m := re.fullmatch(rf"entfällt nach {T}", s):
        return [{"rule_type": "window_dropped", "window_start": hhmm(m[1], m[2]), "window_end": END_OF_DAY}]
    if m := re.fullmatch(rf"entfällt ab {T} statt {T}", s):
        return [{"rule_type": "window_dropped", "window_start": hhmm(m[1], m[2]), "window_end": END_OF_DAY,
                 "model_note": f"Service ends at {hhmm(m[1], m[2])[:5]} instead of {hhmm(m[3], m[4])[:5]}."}]
    if m := re.fullmatch(rf"bis {T}, ab {T}: entfällt", s):
        return [{"rule_type": "window_dropped", "window_start": "00:00:00", "window_end": hhmm(m[1], m[2])},
                {"rule_type": "window_dropped", "window_start": hhmm(m[3], m[4]), "window_end": END_OF_DAY}]
    if m := re.match(rf"bis {T}: entfällt(; reines Nightliner)?", s):
        note = ("Nightliner network instead (as on a strike day); its extra trips are not in the feed and are "
                "not added.") if m[3] else ""
        return [{"rule_type": "window_dropped", "window_start": "00:00:00", "window_end": hhmm(m[1], m[2]),
                 "model_note": note}]
    if m := re.match(rf"ab (?:ca\. )?{T}:? entfällt", s):
        return [{"rule_type": "window_dropped", "window_start": hhmm(m[1], m[2]), "window_end": END_OF_DAY}]
    start = where = None
    if m := re.search(rf"[Bb]etriebsbeginn (?:ab |ca\. )?{T}(?: ab (.+))?$", s):
        start, where = hhmm(m[1], m[2]), m[3]
    elif m := re.search(rf"[Bb]etriebsbeginn ab (\D+?) \(ca\. {T}\)", s):
        start, where = hhmm(m[2], m[3]), m[1]
    if start:
        note = (f"The document names the terminus {where}; trips of both directions that start before "
                f"{start[:5]} are dropped.") if where else ""
        return [{"rule_type": "window_dropped", "window_start": "00:00:00", "window_end": start, "model_note": note}]
    # thinner headway in a time window
    hw = r"(\d+(?: \d/\d)?)'- statt (\d+(?: \d/\d)?)'-Takt"
    if m := re.match(rf"(?:bis|vor) {T}:? (?:im )?{hw}", s):
        return [headway_rule(s, "00:00:00", hhmm(m[1], m[2]), minutes(m[3]), minutes(m[4]))]
    if m := re.match(rf"ab (?:ca\. )?{T}:? {hw}", s):
        return [headway_rule(s, hhmm(m[1], m[2]), END_OF_DAY, minutes(m[3]), minutes(m[4]))]
    if m := re.match(rf"{T} ?- ?{T} ?: {hw}", s):
        return [headway_rule(s, hhmm(m[1], m[2]), hhmm(m[3], m[4]), minutes(m[5]), minutes(m[6]))]
    if m := re.match(rf"ab {T}: Kurzfahrten .*entfallen; dadurch 40'-(?: statt 20'-)?Takt", s):
        return [headway_rule(s, hhmm(m[1], m[2]), END_OF_DAY, 40, 20)]
    if m := re.fullmatch(rf"(\d+)'-Takt vor {T}", s):
        return [headway_rule(s, "00:00:00", hhmm(m[2], m[3]), int(m[1]), None)]
    if m := re.fullmatch(rf"(\d+)'-Takt ab {T} statt {T}", s):
        return [headway_rule(s, hhmm(m[2], m[3]), hhmm(m[4], m[5]), int(m[1]), None,
                             f"The {m[1]}-minute evening headway starts at {hhmm(m[2], m[3])[:5]} instead of "
                             f"{hhmm(m[4], m[5])[:5]}.")]
    if m := re.fullmatch(rf"(\d+)'-Takt bis {T} statt {T}", s):
        return [headway_rule(s, hhmm(m[4], m[5]), hhmm(m[2], m[3]), int(m[1]), None,
                             f"The {m[1]}-minute morning headway lasts until {hhmm(m[2], m[3])[:5]} instead of "
                             f"{hhmm(m[4], m[5])[:5]}.")]
    if m := re.fullmatch(rf"(\d+)'-Takt bis {T}", s):
        return [headway_rule(s, "00:00:00", hhmm(m[2], m[3]), int(m[1]), None)]
    if m := re.fullmatch(rf"{T} - {T}: (\d+)-min-Takt Straßenbahn", s):
        return [headway_rule(s, hhmm(m[1], m[2]), hhmm(m[3], m[4]), int(m[5]), None)]
    # one trip of the day dropped, per direction
    if re.fullmatch(r"Entfall der zweiten Fahrt morgens je Richtung", s):
        return [{"rule_type": "trip_dropped", "trip_rank": 2}]
    if re.fullmatch(r"Entfall der vorlet?zt?en Fahrt abends je Richtung", s):
        return [{"rule_type": "trip_dropped", "trip_rank": -2}]
    # everything else is described, not modeled
    if re.search(r"Verstärker|Schulverstärker", s):
        return nm("Named reinforcement trips; they can't be identified in the feed by time alone.")
    if re.search(r"[Ee]inzelne Fahrten entfallen", s):
        return nm("The document doesn't say which trips.")
    if re.search(r"Rufbus", s):
        return nm("On-demand replacement (Rufbus); no timetable, no capacity added.")
    if re.search(r"endet|Wende|nur bis|Kurzläufer|Kurzfahrten|zwischen|Zusätzliche Fahrten", s):
        return nm("Shortened route or dropped short runs; would need cuts at stop level.")
    return nm("Not parsed.")


def minutes(v: str) -> float:
    if " " in v:  # "6 2/3"
        whole, frac = v.split(" ")
        a, b = frac.split("/")
        return round(int(whole) + int(a) / int(b), 2)
    return float(v)


def line_mode(label: str) -> str:
    if label.startswith("U"):
        return "U-Bahn"
    if label.isdigit() and int(label) < 20:
        return "Tram"
    return "Bus"


# --------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", type=Path, default=REPO / "data" / "nuernberg-raw" / "vag" / "sparpaket_vag_2027.pdf")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "source" / "pt_service_cuts.csv")
    args = ap.parse_args(argv)
    if not args.pdf.exists():
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        print(f"download {PDF_URL}")
        fetch(PDF_URL, args.pdf)

    doc = pymupdf.open(args.pdf)
    cells: dict[tuple, list[tuple[str, int]]] = {}  # (stage, line, day_type) -> [(statement, page)]
    for pno, (stage, _) in STAGES.items():
        for label, by_col in read_cells(doc[pno]).items():
            for col, statements in by_col.items():
                label = "Nightliner" if label.startswith("Nightl") else label  # "Nightlilner" on page 6
                for line in (["U2", "U3"] if label == "U2/3" else [label]):
                    cells.setdefault((stage, line, col), []).extend((t, pno + 1) for t in statements)
    missing = sorted({(l, d) for st, l, d in cells if st == "2027-03"} - {(l, d) for st, l, d in cells if st == "2027-08"})
    print("in the March table but empty in the end-state table:", missing)
    for (line, day), why in sorted(CARRY_OVER.items()):
        key = ("2027-08", line, day)
        if key not in cells and ("2027-03", line, day) in cells:
            cells[key] = [(t, p, why) for t, p in cells[("2027-03", line, day)]]

    eff = dict(STAGES.values())
    day_order = [c[1] for c in COLUMNS]

    def sort_key(k):
        stage, line, day = k
        return (stage, line_mode(line) != "U-Bahn", line_mode(line) != "Tram",
                int(re.sub(r"\D", "", line) or 999), line, day_order.index(day))

    rows, n = [], 0
    for key in sorted(cells, key=sort_key):
        stage, line, day = key
        for item in cells[key]:
            text, page, extra = (item + ("",))[:3]
            for rule in parse(text):
                n += 1
                note = " ".join(x for x in (rule.get("model_note", ""), extra) if x)
                rows.append({
                    "cut_id": n, "package": "", "package_basis": "", "stage": stage, "effective_date": eff[stage], "line": line,
                    "line_mode": "Nightliner" if line.startswith("Night") else line_mode(line), "day_type": day,
                    "rule_type": rule["rule_type"], "window_start": rule.get("window_start", ""),
                    "window_end": rule.get("window_end", ""),
                    "headway_old_min": fmt(rule.get("headway_old_min")),
                    "headway_new_min": fmt(rule.get("headway_new_min")),
                    "trip_rank": rule.get("trip_rank", ""),
                    "modeled": 0 if rule["rule_type"] == "not_modeled" else 1,
                    "text_de": text, "model_note": note, "source_page": page, "source": SOURCE})
    march = {(r["line"], r["day_type"], r["text_de"]) for r in rows if r["stage"] == "2027-03"}
    non_holiday = {(r["stage"], r["line"], r["day_type"], r["text_de"]) for r in rows}
    for r in rows:
        r["package"], r["package_basis"] = assign_package(r, march, non_holiday)
    for pkg, line, mode, days, rule, text, note in P4_P5:
        for day in days:
            n += 1
            rows.append({
                "cut_id": n, "package": pkg, "package_basis": f"{pkg}: listed on page 1 beyond P3.",
                "stage": "2027-08", "effective_date": eff["2027-08"], "line": line, "line_mode": mode,
                "day_type": day, "rule_type": rule["rule_type"], "window_start": rule.get("window_start", ""),
                "window_end": rule.get("window_end", ""), "headway_old_min": "",
                "headway_new_min": fmt(rule.get("headway_new_min")), "trip_rank": "",
                "modeled": 0 if rule["rule_type"] == "not_modeled" else 1,
                "text_de": text, "model_note": note, "source_page": 1, "source": SOURCE})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, lineterminator="\n")  # LF only: exapump passes CRLF through
        w.writeheader()
        w.writerows(rows)
    by_type: dict[str, int] = {}
    for r in rows:
        by_type[r["rule_type"]] = by_type.get(r["rule_type"], 0) + 1
    print(f"{len(rows)} rules -> {args.out}  {by_type}")
    by_pkg: dict[tuple, int] = {}
    for r in rows:
        if r["day_type"] in ("mon_thu", "sat"):
            k = (r["stage"], r["day_type"], r["package"])
            by_pkg[k] = by_pkg.get(k, 0) + 1
    print("rules per stage, day and first package:", dict(sorted(by_pkg.items())))


# --------------------------------------------------------------------------- packages
# Page 1 lists the main measures of each package, each package building on the one before; the line tables detail
# only P3 and don't mark which statement belongs to P1 or P2. Each P3 rule gets the first package whose measures
# describe it. This is an interpretation of the measure lists, not a published assignment; package_basis says why.
P1_EVENING = "17:00:00"
BASIS = {
    "P1_evening": "P1: 40-minute headways start earlier in the evening (Früherer Beginn 40-Min-Takte).",
    "P1_holidays": "P1: holiday timetable in all school holidays (Ferienfahrplan in allen Ferien).",
    "P2_headway": "P2: further headway cuts (Weitere Taktausdünnungen).",
    "P2_edge": "P2: thinner early and late service on some lines (Ausdünnung Tagesrandlagen linienspezifisch).",
    "P2_route": "P2: shortened routes and dropped reinforcement trips (Verkürzung Linienwege, Entfall Verstärkerfahrten).",
    "P3_aug": "P3: in the end-state table only; P1 and P2 start in full on 8 Mar 2027, only P3 has parts from 2 Aug 2027.",
    "P3_listed": "P3: a measure page 1 lists for P3 (withdrawn lines and sections, later start or earlier end, trams 10 "
                 "and 11, U-Bahn before 6:00, weekend mornings on the Nightliner network, trams in holidays).",
    "P3_rail": "P3: tram and U-Bahn headway cuts; page 1 names rail measures only from P3 on (Weitere "
               "Taktreduzierungen einz. Linien, U-Bahn U1-U3 vor 6 Uhr 10-min-Takt, Alle Tram 15-Min-Takt in Ferien).",
}


def assign_package(row: dict, march: set, non_holiday: set) -> tuple[str, str]:
    """First package (P1-P3) whose page-1 measures describe this P3 rule."""
    rt, mode, day, text = row["rule_type"], row["line_mode"], row["day_type"], row["text_de"]
    if row["stage"] == "2027-08" and (row["line"], day, text) not in march:
        return "P3", BASIS["P3_aug"]
    if rt in ("line_dropped", "window_dropped") or mode == "Nightliner" or re.search(r"Rufbus|Teilstrecke", text):
        return "P3", BASIS["P3_listed"]
    if mode in ("Tram", "U-Bahn"):
        return "P3", BASIS["P3_rail"]
    if day.endswith("_holidays") and (row["stage"], row["line"], day.removesuffix("_holidays"), text) not in non_holiday:
        return "P1", BASIS["P1_holidays"]
    if rt == "headway" and row["headway_new_min"] == "40" and row["window_start"] >= P1_EVENING:
        return "P1", BASIS["P1_evening"]
    if rt == "trip_dropped":
        return "P2", BASIS["P2_edge"]
    if rt == "not_modeled":
        return "P2", BASIS["P2_route"]
    return "P2", BASIS["P2_headway"]


# P4 and P5 beyond P3 (page 1). Only P4's first three measures are concrete enough to be rules; they apply to every
# VAG day line of a mode (line "*": route ids 11-, 12-, 13-, not the Nightliner) or to named lines. P4's remaining
# parts need about four months' lead time after a later decision, so they are given only in the end state.
ALL_DAYS = [c[1] for c in COLUMNS]
P4_P5 = [
    # (package, line, line_mode, day_types, rule, text_de, model_note)
    ("P4", "*", m, ["mon_thu", "mon_thu_holidays", "sun"],
     {"rule_type": "window_dropped", "window_start": "23:30:00", "window_end": END_OF_DAY},
     "Betriebsschluss 23:30 alle Linien (Mo-Do + So)",
     "Every day line of the mode: trips whose first departure is at or after 23:30 are dropped.")
    for m in ("U-Bahn", "Tram", "Bus")
] + [
    ("P4", t, "Tram", ["sat", "sat_holidays", "sun"], {"rule_type": "line_dropped"},
     "Linie 10 + 11 zusätzlich Entfall Sa + So kpl.", "")
    for t in ("10", "11")
] + [
    ("P4", "*", m, ALL_DAYS,
     {"rule_type": "headway", "window_start": "22:00:00", "window_end": END_OF_DAY, "headway_new_min": hw},
     "30/60-Min Taktraster in SVZ täglich ab 22:00",
     f"Assumption: the document gives a 30/60-minute grid without saying which lines run which; U-Bahn and tram "
     f"every 30, bus every 60 minutes. Here: every {hw} minutes.")
    for m, hw in (("U-Bahn", 30), ("Tram", 30), ("Bus", 60))
] + [
    (pkg, "*", "Bus", ALL_DAYS, {"rule_type": "not_modeled"}, text, note)
    for pkg, text, note in (
        ("P4", "Weitere starke Taktreduzierungen einz. Linien", "The document doesn't name the lines."),
        ("P5", "Weitere Taktreduzierungen bedeutender Linien (u.a. Ringbus)",
         "Only the ring bus is named; neither the other lines nor the headways are given."),
        ("P5", "Zeitweises Einstellen ganzer Linien", "The document doesn't name the lines or the times."),
        ("P5", "Einstellen von Teilstrecken", "The document doesn't name the sections."),
        ("P5", "Weitere strukturelle Anpassungen des Netz-Konzeptes (bspw. grundsätzlicher 30/60-min-Takt)",
         "A network redesign, described only by example."),
    )
]


def fmt(v) -> str:
    if v is None or v == "":
        return ""
    return str(int(v)) if float(v).is_integer() else str(v)


if __name__ == "__main__":
    main()
