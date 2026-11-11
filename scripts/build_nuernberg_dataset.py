#!/usr/bin/env python3
"""Download the public sources and build data/nuernberg-dataset/: one command for chapter 2.

    python3 scripts/build_nuernberg_dataset.py

1. Downloads the VGN timetable, the city's Bezirke and Bezirksatlas, DWD weather, SÖR's roadworks and the daily
   bicycle counts into data/nuernberg-raw/ (about 35 MB; files already there are kept).
2. Builds data/nuernberg-dataset/, one load-ready CSV per table in schema NUERNBERG_DATASET, then
   `exakit data-load` loads that folder.

Pure standard library, Python 3.9 or newer. The OpenStreetMap cycle network and the curated tables come from
data/source/ in the repo. The steps are scripts/fetch_nuernberg_sources.py and scripts/prepare_nuernberg_dataset.py,
which also run on their own.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_nuernberg_sources  # noqa: E402
import prepare_nuernberg_dataset  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="download everything again, even files already there")
    ap.add_argument("--skip-bike-counters", action="store_true",
                    help="leave out the bicycle counters (their site can take up to 15 minutes)")
    ap.add_argument("--refresh-osm", action="store_true",
                    help="replace the OpenStreetMap snapshot in data/source/ from the Overpass API first")
    ap.add_argument("--skip-stop-times", action="store_true", help="leave out the large GTFS stop_times table")
    args = ap.parse_args()
    t0 = time.time()

    print("Step 1 of 2: download the sources -> data/nuernberg-raw/")
    fetch_nuernberg_sources.main([f for f, on in (("--force", args.force),
                                                  ("--skip-bike-counters", args.skip_bike_counters),
                                                  ("--refresh-osm", args.refresh_osm)) if on])

    print("\nStep 2 of 2: build the tables -> data/nuernberg-dataset/")
    prepare_nuernberg_dataset.main(["--skip-stop-times"] if args.skip_stop_times else [])

    out = prepare_nuernberg_dataset.REPO / "data" / "nuernberg-dataset"
    n = len(list(out.glob("*.csv")))
    print(f"\nDone in {(time.time() - t0) / 60:.1f} min: {n} tables in {out}")
    print("Next: exakit data-load, with that folder and target schema NUERNBERG_DATASET (tutorial chapter 2).")


if __name__ == "__main__":
    main()
