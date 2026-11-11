# Data

The dataset is built on your machine from public sources: `python3 scripts/build_nuernberg_dataset.py` downloads them into `data/nuernberg-raw/` and writes `data/nuernberg-dataset/`, one load-ready CSV per table in schema `NUERNBERG_DATASET` (about 120 MB). Both folders are gitignored. Coordinates are converted to WGS84 and every point is tagged with its `bezirk_no` and area (`district_no`) by point-in-polygon, so "stands in" rollups are plain equality joins. Loading is described in [tutorial chapter 2](../tutorial/02-load-data.md). Column-level documentation is in [data-model.md](data-model.md).

**Areas.** Nürnberg has 10 statistical Stadtteile, 87 statistical Bezirke and 316 Distrikte. The tutorial works on **79 areas**: the Bezirke, with six groups of small Bezirke that the city only publishes together (18/19, 34/35, 38/39, 41/42/43, 75/85/87, 76/77). In table and column names an area is called a "district".

| Table | Content | Source |
|---|---|---|
| DISTRICTS | The areas: population (31 Dec 2025), `area_km2`, `density_per_km2`, centroid, polygon (WKT), Stadtteil | Bezirke shapefile and Bezirksatlas, Amt für Stadtforschung und Statistik für Nürnberg und Fürth |
| BEZIRKE | The statistical Bezirke with their area and Stadtteil, polygon (WKT) | Bezirke shapefile (DHDN / Gauss-Krüger 4, converted with a 7-parameter datum shift) |
| DISTRICT_POPULATION | Residents counted 2023 / 2024 / 2025, and `pop_2033_model` (a **model** built on the Stadtteil forecast) | Counts: Bezirksatlas (Melderegister). Model: see [data-model.md](data-model.md) |
| STADTTEIL_FORECAST | The city's forecast for 2033 per Stadtteil, new-build movers 2025–2033, and the previous edition's 2035 forecast | Reports M558 (2025) and M529 (2022), Amt für Stadtforschung und Statistik |
| NEWBUILD_PROJECTS | Major housing projects, one row per project and Bezirk: homes, first occupancy, centre of the site | City WFS `Wohnungsneubau:Schwerpunkte_des_Wohnungsneubaus` (geoportal.nuernberg.de) |
| DISTRICT_EMPLOYMENT | Jobs at place of work: employees subject to social insurance, 31 Dec **2019–2024**; business establishments 2019 and 2024 by sector; and the wider **2005** count with its three sectors | 2019–2024: "Nürnberg in Zahlen", Amt für Stadtforschung und Statistik (business register), via `scripts/fetch_nuernberg_statistik.py` → `data/source/district_jobs_2019_2024.csv`. 2005: Statistischer Monatsbericht Oktober 2006, Tab. 1 |
| DISTRICT_HOUSING | Homes permitted and completed per area and year, 2012–2025, with floor area | Building statistics, "Nürnberg in Zahlen"; `data/source/district_housing_2012_2025.csv` |
| DISTRICT_PROFILE | Per area and year 2012–2025: share of residents on minimum-income benefits; for 2025 also registered cars, electric cars and cars per 1,000 residents | "Nürnberg in Zahlen" (benefit rate) and the Bezirksdatenblätter 2025 (cars); `data/source/district_min_income_rate.csv`, `bezirk_cars_2025.csv` |
| VGN_STOPS, VGN_ROUTES, VGN_TRIPS, VGN_STOP_TIMES, VGN_CALENDAR, VGN_CALENDAR_DATES, VGN_TRANSFERS, VGN_AGENCY | The VGN **scheduled** timetable (GTFS, 24 Jun–12 Dec 2026) for the whole VGN region, enriched with `line_mode`, `is_on_demand`, `stop_mode`, `in_nuernberg`, `bezirk_no` and `district_no` | VGN open data, CC BY 3.0 DE |
| VEHICLE_CAPACITY | Planning capacity of one scheduled trip per mode (S-Bahn 600, U-Bahn 590, regional 400, tram 200, bus 90), with sources | VAG "Gefäßgrößen" and fleet data (opendata.vag.de), Wikipedia; curated in `data/source/vehicle_capacity.csv` |
| LINE_CAPACITY | Per-line overrides (U1 604, U2/U3 580, S1–S6) | Same; `data/source/line_capacity.csv` |
| PT_PROJECT_STATIONS | 10 planned rail and tram projects, one row per station and line: opening year, status, funding, frequency or analog line, area | Curated from official sources in [`data/source/pt_projects.csv`](source/pt_projects.csv); every row has a source URL and a verified flag |
| PT_SAVINGS_PACKAGES | The city's five savings packages P1–P5 for the VAG service (proposal, planning status 27 Oct 2026, decision due 30 Nov 2026): main measures, start dates and **VAG's own estimates** of passengers lost and euros saved per year | Council document "Sparmaßnahmenpaket im VAG-Verkehrsangebot", page 1; `data/source/pt_savings_packages.csv` |
| PT_SERVICE_CUTS | The packages as rules: P3 line by line, one rule per line, day type and stage (from 8 Mar 2027, end state from 2 Aug 2027) — line dropped, trips dropped in a time window, thinner headway, a single trip dropped, or described but not modeled — with the statement as printed. Each rule is tagged with the first package that includes it (P1–P3, inferred from the package descriptions); P4's concrete measures are added, P5's are listed as not modeled. **Digitized** from the PDF | Same document, pages 1 and 3–6; `scripts/digitize_vag_cuts_2027.py` → `data/source/pt_service_cuts.csv`; notes in [research/vag-cuts-2027-notes.md](../research/vag-cuts-2027-notes.md) |
| CYCLING_INFRASTRUCTURE | Cycle infrastructure inside the city (OSM ways): path type, directions served, length, midpoint, area | OpenStreetMap via Overpass, ODbL. Snapshot in `data/source/osm_cycling_ways.json.gz` (OSM data as of 24 Jul 2026) |
| CYCLE_NETWORK_PLAN_2021 | The city's cycle network plan (Radwegenetzplan, Stand 01/2021) as lines: planned routes, decided planning, routes built 2013–2020, routes over quiet side streets, field, forest and canal paths. **Digitized and georeferenced** from the PDF map; positions about ±10 m | Radwegenetzplan PDF, Verkehrsplanungsamt; `scripts/digitize_radnetz_2021.py` → `data/source/cycle_network_plan_2021.csv` |
| WEATHER_DAILY | Daily weather 2025-01-01 to 2026-10-27: temperature, rain, sunshine, cloud | Deutscher Wetterdienst, station 03668 Nürnberg |
| ROADWORKS | SÖR's planned and ongoing works in the street: kind, description, status (`in Planung` / `im Bau`), start and end (to 2035), polygon, area; `is_cycling` (cycle-path projects, e.g. Radvorrangroute RVR 10, Radschnellverbindung N–ER) and `is_tram_track` (track works) | City geoportal, SÖR Baukoordination (`Fachdaten_G/SOER_BAUKOP_G_V`, layer 1) |
| ROADWORK_PERMITS | Street-use permits (Sondernutzung) for works: applicant, reason, dates, status, line geometry | Same, layer 0 |
| ROADWORK_DIVERSIONS | Diversions with dates: cycle-path closures (`Radumleitung`) and diversions for motor traffic | Same, layer 2 |
| BIKE_COUNT_STATIONS, BIKE_COUNTS_DAILY | The 12 permanent bicycle counters, daily counts (in, out, total) 2025-01-01 to 2026-10-27, with that day's weather | The city's Eco-Counter pages; see below |

**What the data can't answer:** passenger numbers, crowding, delays or live traffic. VGN GTFS is the schedule only. The service cuts are a proposal; which package the council adopts isn't known before 30 Nov 2026, and only P3 is published line by line. Jobs per area are counted for 2005 and 2019–2024 (different definitions), and no jobs forecast is published. Registered cars include company and rental fleets, which inflates business areas. The city forecasts population per Stadtteil, not per Bezirk. Cycle traffic is measured at twelve counters, daily only.

**Not available:** 15-minute counter data (the public pages offer daily values only), and an impact field for roadworks (full closure, one lane …): SÖR's layers say what is built and when, not how traffic is affected; the diversions cover the larger closures.

## Licences and attribution

| Source | Terms |
|---|---|
| VGN GTFS | CC BY 3.0 DE, attribution "VGN – Verkehrsverbund Großraum Nürnberg GmbH" |
| Bezirke shapefile, Bezirksatlas, reports M558/M529/Monatsbericht 2006, housing WFS, SÖR construction layers | Published by the City of Nürnberg; no licence stated. Usage terms: nuernberg.de/internet/statistik |
| VAG vehicle data | opendata.vag.de |
| DWD climate data | Open data, attribution "Deutscher Wetterdienst" |
| OpenStreetMap | ODbL, "© OpenStreetMap contributors" (openstreetmap.org/copyright). The snapshot `data/source/osm_cycling_ways.json.gz` and the table built from it are available under the ODbL 1.0 |
| Sparmaßnahmenpaket im VAG-Verkehrsangebot (digitized) | A council document published by the City of Nürnberg in its Bürgerinformationssystem; no licence stated. The rule table is derived data and keeps every statement as printed |
| Radwegenetzplan 2021 (digitized) | Published by the City of Nürnberg as a PDF map; no licence stated. The line geometry is derived data |
| Eco-Counter pages | No API and no stated licence. Each user's build reads them; they are not in the repo |

## Building the dataset

```bash
python3 scripts/build_nuernberg_dataset.py                       # download (~35 MB) and build -> data/nuernberg-dataset/
python3 scripts/build_nuernberg_dataset.py --skip-bike-counters  # without the counters
python3 scripts/build_nuernberg_dataset.py --refresh-osm         # also replace the OpenStreetMap snapshot first
```
It runs `fetch_nuernberg_sources.py` (download) and `prepare_nuernberg_dataset.py` (build), which also work on their own, and needs only the Python standard library. If the roadworks or the counters can't be downloaded, it reports them and carries on, and the build leaves those tables out (`--skip-bike-counters` leaves the counters out on purpose). The OpenStreetMap cycle network comes from the snapshot in `data/source/`; `--refresh-osm` replaces it from the Overpass API. The curated tables come from `data/source/`: capacities, projects, the proposed service cuts, jobs (2005, and 2019–2024 with housing, benefits and cars from `scripts/fetch_nuernberg_statistik.py`), the Stadtteil forecast transcriptions and the new-build projects.

The VGN feed is refreshed about every quarter. A newer feed changes row counts and may need a new reference weekday inside its date range (see [AGENTS.md](../AGENTS.md)).
