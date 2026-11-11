# 2 · Load the Nürnberg data

**Goal:** the tables of schema `NUERNBERG_DATASET` built from the public sources, loaded and checked.

Every table comes from a public download that needs no account: the VGN timetable, the city's statistical Bezirke and its Bezirksatlas, plus a few curated tables in this repo. [data/README.md](../data/README.md) describes every table and its source.

## 2.1 Download and build
```bash
python3 scripts/build_nuernberg_dataset.py
```
The script needs Python 3.9 or newer and nothing else: no packages to install. If `python3` isn't found, use the Python the starter kit installed for itself: replace `python3` with `~/.exasol-starter-kit/pyexasol-venv/bin/python3` (on Windows, `pyexasol-venv\Scripts\python.exe` in the same folder).

It works in two steps and says which one it's on:
1. **Download** the sources (about 35 MB) into `data/nuernberg-raw/`: the VGN timetable, the city's Bezirke and statistics, SÖR's construction layers from the city geoportal, DWD weather and the daily counts of the city's 12 bicycle counters. Most of it takes seconds. The counters are read from the city's Eco-Counter pages, one page per counter and year: usually a minute or two, but up to 15 minutes when that site is slow; the script shows each page as it arrives. The OpenStreetMap cycle network isn't downloaded: the repo ships a snapshot in `data/source/`.
2. **Build** the folder `data/nuernberg-dataset/`, one CSV per table (about 137 MB), in about a minute. It converts the city's coordinates to GPS (WGS84), tags every stop, roadwork and path with the area it lies in and adds the curated tables from `data/source/`, among them the city's 2021 cycle network plan, digitized from its PDF map, and the service cuts the city proposed in November 2026, digitized from the council document.

At the end it prints how many tables it built: 29. If the roadworks or the bicycle counters couldn't be downloaded, it lists them, builds the rest and leaves those tables out; run it again later to add them. Files it already has are kept. Both folders are gitignored.

## 2.2 Load
```bash
exakit data-load
```
1. Choose **A local CSV / Parquet / JSON file, or a folder of them**.
2. Enter the **full path** of `data/nuernberg-dataset`.
3. Target schema: `NUERNBERG_DATASET`.

Each file becomes one table named after it, e.g. `districts.csv` → `NUERNBERG_DATASET.DISTRICTS`.

## 2.3 Check with your agent
Ask:
```text
What tables are in the NUERNBERG_DATASET schema and how many rows does each have? Show the SQL.
```
The agent shows one query on the system tables and the row count per table. You should see 29 tables:

`BEZIRKE`, `BIKE_COUNTS_DAILY`, `BIKE_COUNT_STATIONS`, `CYCLE_NETWORK_PLAN_2021`, `CYCLING_INFRASTRUCTURE`, `DISTRICTS`, `DISTRICT_EMPLOYMENT`, `DISTRICT_HOUSING`, `DISTRICT_POPULATION`, `DISTRICT_PROFILE`, `LINE_CAPACITY`, `NEWBUILD_PROJECTS`, `PT_PROJECT_STATIONS`, `PT_SAVINGS_PACKAGES`, `PT_SERVICE_CUTS`, `ROADWORKS`, `ROADWORK_DIVERSIONS`, `ROADWORK_PERMITS`, `STADTTEIL_FORECAST`, `VEHICLE_CAPACITY`, `VGN_AGENCY`, `VGN_CALENDAR`, `VGN_CALENDAR_DATES`, `VGN_ROUTES`, `VGN_STOPS`, `VGN_STOP_TIMES`, `VGN_TRANSFERS`, `VGN_TRIPS`, `WEATHER_DAILY`.

Does every table have rows? Do the counts look plausible for what [data/README.md](../data/README.md) says each table holds?

The VGN timetable is refreshed about every quarter. If you download a newer feed, the row counts change and the reference weekday in [AGENTS.md](../AGENTS.md) may need moving into the new feed's date range.

Next: [3 · First questions](03-first-questions.md)
