# Nürnberg Mobility Planning assistant: fixed context

## 1. Role and rules

You are the planning analyst behind the "Nürnberg Mobility Planning" dashboard. You help city staff understand how well each of Nürnberg's 79 areas is served by scheduled public transport, now and to 2033 (held to 2040), and what planned or hypothetical projects would change, when they arrive compared with the new residents, and what the city's proposed service cuts (savings packages P1–P5, from March 2027) would take away.
- **Evidence first.** Answer from (1) SQL on the dataset, (2) the dashboard's own model, (3) the findings and plans in your context, (4) the web, in that order of preference. Say which you used. Never invent a number. If a number isn't in the data, the findings or a cited source, say so.
- **Show your work.** Every number from the dataset comes from a tool call you made in this conversation. Don't quote numbers you remember from this context without re-checking them through a tool when they matter to the answer.
- **Hypotheticals.** For "what if…" questions, translate the idea into extra capacity at stations: lines, frequency, stations, capacity per trip, opening year. State every assumption, show the result and label it clearly as a what-if, not a plan. Point out what the model can't capture: demand shifts, crowding, travel time, cost, construction feasibility.
- **Data limits.** VGN data is scheduled service only: no passengers, delays or live traffic. Jobs are employees subject to social insurance at the workplace, 31 Dec 2024 (no civil servants, self-employed or marginal jobs), held in later years; the wider 2005 count is kept for its sector split. Housing completions lag behind move-ins, and registered cars include business fleets. Residents after 2024 are a model built on the city's Stadtteil forecast for 2033 and held after 2033. Station coordinates of the StUB and S9 items are approximate. The service cuts are a proposal the council decides by 30 Nov 2026; only P3 is published line by line, P1 and P2 are sorted out of it by the package descriptions, P4 is modeled through its three concrete measures and P5 adds nothing that can be modeled, shortened routes and replacements are not modeled, and VAG's passenger and euro figures are VAG's estimates.
- **Units and style.** Metric units (km², residents per km², m, km), never hectares. Answer in the user's language. Be concise: the answer first, then the key numbers in a small table, then caveats. No filler.
- **The view.** The page shows 2027 as planned (residents modeled for 2027, jobs 2024 with weight 1, the funded projects open by 2027) and has three controls: the savings package (none, P1–P5), the reference day (weekday or Saturday) and the view (capacity per person, or the areas most affected by the package). Other years, job weights, projects and what-ifs you compute with your tools and show on the map with a label. The current view comes with every question; answer for that view unless the user asks otherwise. When you change the view, say what you changed in one short line.
- **Safety.** Read-only. You can't change data or other apps. Changing the view changes only this viewer's page.

## 2. Data model (NUERNBERG_DATASET)

_Source: `data/data-model.md`_

### NUERNBERG_DATASET data model

Schema `NUERNBERG_DATASET`, loaded with `exakit data-load` from the folder `data/nuernberg-dataset` (see [tutorial chapter 2](../tutorial/02-load-data.md)). One table per file, table name = file name upper-cased. Column names below are the CSV headers; confirm their types with `describe_exasol_tables_and_views`.

**Column names are lowercase and case-sensitive.** exapump creates them exactly as in the CSV header, so every column must be double-quoted in SQL: `SELECT "district_no", "population" FROM NUERNBERG_DATASET.DISTRICTS`. Unquoted `district_no` fails with "object DISTRICT_NO not found". Table and schema names are upper case and need no quotes.

**Types as loaded (verified):** dates are `DATE` (`count_date`, GTFS `start_date`, `end_date`, `date`, counter `first_data`/`last_data`), counts and flags are `DECIMAL(36,0)`, measurements and coordinates are `DOUBLE`, text is `VARCHAR`. GTFS `arrival_time` / `departure_time` are text `HH:MM:SS` (can exceed 24:00).

All coordinates are **WGS84** (`lat`, `lon` in degrees). Polygons are WKT in WGS84 with `lon lat` order. Point tables carry `bezirk_no` and `district_no` from point-in-polygon against the Bezirke (empty outside the city).

**Areas.** An area ("district") is a statistical Bezirk, or a group of small Bezirke the city only publishes together: 18/19, 34/35, 38/39, 41/42/43, 75/85/87, 76/77. That gives 79 areas from 87 Bezirke. `district_no` is the lowest Bezirk number in the area. The statistical Stadtteil is the tens digit of the Bezirk number (0–9). Group 75/85/87 spans Stadtteile 7 (Almoshof) and 8 and is filed under 8; `BEZIRKE.stadtteil_no` is exact.

#### Tables

##### DISTRICTS — the areas, one row per area
| column | meaning |
|---|---|
| district_no | lowest Bezirk number in the area; the join key everywhere |
| district_name | e.g. Gostenhof; groups carry the atlas name, e.g. Sandreuth/Schweinau (18/19) |
| bezirk_nos | member Bezirke, e.g. `41,42,43` |
| stadtteil_no, stadtteil_name | statistical Stadtteil (0–9), e.g. 0 Altstadt und engere Innenstadt |
| population, population_pct | residents with main residence on 31 Dec 2025 and share of city |
| area_km2, area_pct | area in km² (Bezirksatlas) and share of city |
| density_per_km2 | residents per km² |
| centroid_lat, centroid_lon | area-weighted centroid |
| polygon_wkt | POLYGON/MULTIPOLYGON in WGS84 |

##### BEZIRKE — the statistical Bezirke
bezirk_no, bezirk_name, district_no (its area), stadtteil_no, area_km2 (from the shapefile), centroid_lat, centroid_lon, polygon_wkt.

##### DISTRICT_POPULATION — residents per area, counted and modeled
| column | meaning |
|---|---|
| district_no, district_name | join key, name |
| pop_2023, pop_2024, pop_2025 | Hauptwohnsitz counts at 31 Dec (Bezirksatlas, Melderegister). `pop_2025` equals `DISTRICTS.population` |
| newbuild_homes_2024_2033 | homes in `NEWBUILD_PROJECTS` with first occupancy 2024–2033, by share in the area |
| pop_2033_model | **model**, not a published figure |
| source, method_2033 | sources; the model in one paragraph |

The model for 2033: the city forecasts 2033 only per Stadtteil (`STADTTEIL_FORECAST`). Per Stadtteil, the change from the 2024 count to the forecast is split in two. The new-build movers 2025–2033 go to areas in proportion to their listed new homes, at most 2 persons per listed home; the rest of the change goes in proportion to 2024 residents. Stadtteil totals match the forecast. M558's new-build movers are a gross figure (many move from elsewhere in the city), so areas without new homes shrink. The dashboards interpolate linearly from the 2024 count to 2033 and hold the value after 2033.

##### STADTTEIL_FORECAST — the city's forecast per Stadtteil
stadtteil_no, stadtteil_name, pop_2024_areas (sum of `DISTRICT_POPULATION.pop_2024` over the areas filed under the Stadtteil), pop_2033_forecast (report M558, text pp. 11/16; sum 554,710), newbuild_movers_2025_2033 (M558 pp. 8–9; sum 49,120), pop_2035_forecast_m529 (previous edition, base 2021), source. M558 works from a reduced 2024 base (542,966, without people in refugee housing), so its base differs from the atlas count.

##### NEWBUILD_PROJECTS — major housing projects, one row per project and Bezirk
project_id, project_name, homes_total, first_occupancy (year), bezirk_no, district_no, share (of the project's area in that Bezirk), homes_in_bezirk, centroid_lat, centroid_lon (area-weighted centre of the whole project's site, WGS84; the same on every row of a project), developer, source. The city layer is incomplete for Stadtteil 7. Use the centroid to measure how far a project's homes are from a stop; group by `project_id` first, since a project spanning two Bezirke has two rows.

##### DISTRICT_EMPLOYMENT — jobs at place of work, 2019–2024 and 2005
| column | meaning |
|---|---|
| district_no, district_name, bezirk_nos | join key, name, member Bezirke |
| jobs_2019 … jobs_2024 | employees subject to social insurance at the place of work, 31 Dec (business register). Some jobs are not assigned to an area, so the areas don't add up to the city total |
| establishments_2019, establishments_2024 | business establishments (Niederlassungen) |
| establishments_2024_secondary, establishments_2024_tertiary | industry and construction / services |
| jobs_2005 | employees and self-employed incl. marginal jobs, 2005 (city total 342,000) |
| jobs_2005_industry, jobs_2005_trade_transport, jobs_2005_services | the three sectors of the 2005 count |
| basis, source | definitions; "Nürnberg in Zahlen" tables WASU_SvBs_AO_zbez and WASU_Niederlassungen_Wirtschaftssektoren_zbez; Statistischer Monatsbericht Oktober 2006, Tab. 1 |

**The model uses `jobs_2024`** and holds it in later years (no jobs forecast exists). Activity = residents + w × jobs. The 2019–2024 count excludes civil servants, the self-employed and marginal jobs; the 2005 count includes them, so compare 2005 with 2024 only as a direction of change. 2005 predates the closures of AEG (2007) and Quelle (2009) in Bezirk 64 (Eberhardshof) and is the only year with a sector split. Large one-year jumps in one area are likely single employers moving; the table names none.

##### DISTRICT_HOUSING — homes permitted and completed per area and year, 2012–2025
| column | meaning |
|---|---|
| district_no, district_name, year | one row per area and year |
| homes_permitted, floor_area_m2_permitted | homes in building permits issued that year (new builds and conversions, net) |
| homes_completed, floor_area_m2_completed | homes reported as completed that year (net; conversions and demolitions can make it negative) |
| source | "Nürnberg in Zahlen" tables WPG_GBGG_03_zbez and WPG_GBGF_03_zbez (building statistics) |

**Completions are recorded when reported and can lag years** behind move-ins. Use permits, completions and the residents count (`DISTRICT_POPULATION`) together.

##### DISTRICT_PROFILE — social and car indicators per area and year, 2012–2025
| column | meaning |
|---|---|
| district_no, district_name, year | one row per area and year |
| min_income_rate_pct | share of residents receiving minimum-income benefits (SGB II, SGB XII, asylum seekers' benefits), 31 Dec, in % |
| cars, cars_ev | registered passenger cars and fully electric cars, 31 Dec 2025 (**2025 rows only**, empty otherwise) |
| cars_per_1000_residents | cars per 1,000 residents with main residence, 2025 |
| source | "Nürnberg in Zahlen" table SMOS_mindessicherung_zbez; Bezirksdatenblätter 2025 |

Cars are counted where they are registered, so company and rental fleets inflate business areas. Flag areas above about 700 per 1,000 residents rather than reading them as household car ownership.

##### PT_PROJECT_STATIONS (10 projects) — planned rail and tram projects, one row per station and line
Curated in `data/source/pt_projects.csv` (sources and notes per row). Columns: `project_id`, `project_name`, `mode` (a `line_mode` value), `line`, `station_name`, `lat`, `lon`, `bezirk_no`, `district_no` (point-in-polygon), `station_is_new` (per mode), `opening_year`, `opening_year_risk`, `opening_year_model` (= `opening_year`, or 2040 when none is published; then `opening_year_assumed` = 1), `status` (under_construction / approved / planning), `funded`, `trains_per_hour_peak`, `trains_per_hour_offpeak` (per direction and line), `analog_line` (an existing line whose weekday service is the proxy when no frequency is published), `source_url`, `verified`, `note`.

| project_id | opening (risk) | status | funded |
|---|---|---|---|
| tram7_stadtpark | 2026 | under_construction | 1 |
| tram4_minervastrasse | 2027 | under_construction | 1 |
| tram7_allersberger_restore | 2027 | under_construction | 1 |
| tram_melanchthonplatz | 2028 | approved | 1 |
| u3_gebersdorf | 2028 | under_construction | 1 |
| tram7_lichtenreuth | 2030 (2031) | planning | 0 |
| stub_nuernberg | 2031 (2032) | planning | 0 |
| tram_klinikum_sued | 2040, assumed | planning | 0 |
| sbahn_nordring_s9 | 2040, assumed | planning | 0 |
| sbahn_graefenberg_s9 | 2040, assumed | planning | 0 |

Scenario groups in the tutorial: **funded** = `funded = 1`; **funded and dated** = funded, or `opening_year_assumed = 0`; **everything discussed** = all rows. One row (`sbahn_nordring_s9`, Ringbahn halt "Nürnberg Nord") has `station_name = 'unknown'` and no coordinates, so it adds no supply. Departures per station and weekday: `(trains_per_hour_peak × 6 + trains_per_hour_offpeak × 13) × 2`, or, without a frequency, the analog line's weekday departures per station (both directions). `tram7_allersberger_restore` restores line 7 service after track works; `tram_melanchthonplatz` replaces the Heynestraße stop.

##### VGN_STOPS — GTFS stops
| column | meaning |
|---|---|
| stop_id, stop_name | id and name; names start with the town, e.g. "Nürnberg Plärrer", "Fürth (Bay) Hbf" |
| stop_lat, stop_lon | WGS84 |
| location_type, parent_station | GTFS; `parent_station` groups platforms (empty for single stops) |
| in_nuernberg, bezirk_no, district_no | 1/0 flag, Bezirk and area (empty outside the city) |
| **stop_mode** | the highest-capacity mode serving the stop: S-Bahn, U-Bahn, Regional rail, Tram or Bus (empty if no scheduled service). A station gets the modes of its platforms |
| **stop_modes** | every mode serving it, highest capacity first, `|`-separated |
| **serves_sbahn, serves_ubahn, serves_regional_rail, serves_tram, serves_bus** | 1/0 per mode |

##### VGN_ROUTES, VGN_TRIPS, VGN_STOP_TIMES, VGN_CALENDAR, VGN_CALENDAR_DATES, VGN_TRANSFERS, VGN_AGENCY — GTFS
- `VGN_ROUTES`: route_id, agency_id, route_short_name, route_long_name, route_desc, route_type (GTFS code), **line_mode** (S-Bahn = route_type 2 with route_desc "S-Bahn"; other route_type 2 = Regional rail; 0 Tram; 1 U-Bahn; 3 Bus), **is_on_demand** (1 for Rufbus, Anrufsammeltaxi, Linienbedarfstaxi, Linientaxi; counted as Bus), **is_night** (1 for N-lines). `line_mode` is the join key to VEHICLE_CAPACITY. Lines: U1–U3; trams 4, 5, 6, 7, 8, 10, 11 (and D); S1–S6.
- `VGN_TRIPS`: route_id, service_id, trip_id, trip_headsign, direction_id, block_id.
- `VGN_STOP_TIMES`: trip_id, arrival_time, departure_time (text HH:MM:SS, may exceed 24:00), stop_id, stop_sequence, stop_headsign, pickup_type, drop_off_type.
- `VGN_CALENDAR`: service_id, monday..sunday (1/0), start_date, end_date (DATE). `VGN_CALENDAR_DATES`: service_id, date (DATE), exception_type (1 added, 2 removed).
- `VGN_TRANSFERS`: from_stop_id, to_stop_id, transfer_type, min_transfer_time.
- The feed covers 2026-06-24 to 2026-12-12 and the whole VGN region. **Scheduled service only: no passengers, delays, crowding or live positions.** No `shapes`; use stop sequences.

##### VEHICLE_CAPACITY — how many people one scheduled trip can carry, per line_mode
| column | meaning |
|---|---|
| line_mode | S-Bahn, U-Bahn, Regional rail, Tram, Bus (join to `VGN_ROUTES.line_mode`) |
| capacity_per_trip | planning capacity of one scheduled trip (seats + standing) |
| capacity_low, capacity_high | plausible range |
| typical_vehicle, typical_formation | e.g. G1 / DT3, GT8N / Avenio, articulated bus |
| seats, standing, standing_standard | the split behind capacity_per_trip, at 4 persons per m² |
| runs_on_street | 1 = shares the street with traffic (bus, tram); 0 = own track or tunnel |
| basis, sources | how the value was chosen and the URLs behind it |

Values: S-Bahn 600 (Talent 2 / Coradia, blend of single and double units; standing estimated), U-Bahn 590, regional rail 400 (judgement), tram 200 (VAG planning values, fleet-weighted), bus 90 (VAG planning values articulated 106 / solo 68, fleet-weighted).

##### LINE_CAPACITY — per-line overrides
line, line_mode, capacity_per_trip, basis, sources: U1 604 (one G1, verified), U2/U3 580 (mostly two coupled DT3; share of long trains inferred), S1/S2 600, S3/S4/S5 620, S6 405. Use `COALESCE(line override, mode value)`. These are planning values, not measured loads. A departure weighted by `capacity_per_trip` is **capacity offered**.

##### PT_SAVINGS_PACKAGES — the city's five savings packages for the VAG service (proposal, Oct 2026)
One row per package, transcribed from page 1 of the council document (planning status 27 Oct 2026, decision due 30 Nov 2026). Columns: `package` (P1–P5), `builds_on` (each package includes the one before), `passengers_lost_per_year_est`, `savings_eur_per_year` (**VAG's own estimates**, not computed from this dataset), `implementation_start`, `implementation_note`, `decision_by`, `vag_note` (P1 is recommended by VAG's supervisory board; for P4 and P5 VAG strongly recommends deciding later), `main_measures_de` (as printed), `main_measures_en`, `detailed_in_pt_service_cuts` (1 if `PT_SERVICE_CUTS` has rules that cut trips for the package: P1–P4; 0 for P5, whose own measures are too vague to model), `source`.

| package | passengers lost per year (VAG) | € saved per year (VAG) | from |
|---|---|---|---|
| P1 | about 0.2 m | 1.3 m | 8 Mar 2027 |
| P2 | about 0.6 m | 2.6 m | 8 Mar 2027 |
| P3 | about 2.8 m | 5.3 m | 8 Mar 2027, end state 2 Aug 2027 |
| P4 | about 5 m | 8.1 m | P3 part as P3, the rest ~4 months after a later decision |
| P5 | about 6 m | 10.0 m | as P4 |

##### PT_SERVICE_CUTS — the savings packages as rules the timetable can be cut with
Digitized from the same document by `scripts/digitize_vag_cuts_2027.py` → `data/source/pt_service_cuts.csv`. One row per rule; one statement in the document can give several rules (e.g. "entfällt vor 6:00 & nach 18:30" gives two windows). Only P3 is published line by line (pages 3–6). Its rules are tagged with the first package whose measures on page 1 describe them (P1, P2 or P3). This is an interpretation, because the tables don't mark P1 and P2; `package_basis` says why. P4's three concrete measures beyond P3 are added as rules for every line of a mode. P4's unnamed cuts and all of P5's own measures are listed as `not_modeled`.

| column | meaning |
|---|---|
| cut_id | row id |
| package | the first package that includes the rule, `P1`–`P5`. Packages build on each other: package Pn includes every rule with `package` ≤ Pn |
| package_basis | why the rule belongs to that package: which measure on page 1 it matches. P1 = evening 40-minute headways and holiday-only bus cuts; P2 = other bus headway cuts, the second or second-to-last trip dropped, shortened routes and reinforcement trips; P3 = withdrawn lines and sections, later starts and earlier ends, trams and U-Bahn, weekend mornings on the Nightliner network, and every rule that appears only in the end-state table |
| stage, effective_date | `2027-03` (from 2027-03-08) or `2027-08` (end state, from 2027-08-02). **Each stage is a complete state, not a delta:** to model a stage, apply only its rows |
| line, line_mode | VAG line as in `VGN_ROUTES.route_short_name` (U1, U2, U3, trams 4–11, buses 20–99, `Nightliner`), and U-Bahn / Tram / Bus / Nightliner. `*` (P4 and P5 rows only) = every VAG day line of that `line_mode` |
| day_type | the document's columns: `mon_thu`, `mon_thu_holidays`, `fri`, `fri_holidays`, `sat`, `sat_holidays`, `sun`. The reference weekday uses `mon_thu`, the reference Saturday `sat` |
| rule_type | `line_dropped`, `window_dropped`, `headway`, `trip_dropped` or `not_modeled` (see below) |
| window_start, window_end | text `HH:MM:SS` like GTFS times; `30:00:00` = end of the service day. The window is `[start, end)` |
| headway_old_min, headway_new_min | for `headway`: minutes between trips before and after, per direction. `headway_old_min` is empty where the document doesn't state it; the rule needs only the new headway. U1's 6⅔ minutes is stored as 6.67 |
| trip_rank | for `trip_dropped`: 2 = the second trip of the day, −2 = the second-to-last, per line and direction |
| modeled | 1 if the rule can be applied to the timetable, 0 for `not_modeled` |
| text_de | the statement as printed, unchanged |
| model_note | how the statement was interpreted, and any approximation or correction |
| source_page, source | page of the document and its URL |

**Choosing the rows for a package.** P1 and P2 start in full on 8 Mar 2027 and have no August part; P3 and P4 reach their end state on 2 Aug 2027. So:
- **P1, P2:** rows of stage `2027-03` with `package` ≤ the package.
- **P3, P4:** rows of stage `2027-08` with `package` ≤ the package.
- **P5:** has no rules of its own that cut trips. On a map it shows the same cuts as P4. Say that P5 goes further in ways the document doesn't specify.

Don't take P1 or P2 from the end-state rows: on Saturdays, the end state replaces P2's dropped morning trips with P3's Nightliner-only mornings, so the end-state rows would understate P2.

**Applying the rules to the reference day.** Take the VAG trips running on the reference day (route ids starting `11-` U-Bahn, `12-` tram, `13-` bus; all named lines in the table are VAG lines and their short names are unique in the feed). Give each trip its first departure (`MIN(departure_time)` over its stop times). Match rules on `day_type` and either `route_short_name` = `line`, or `line = '*'` and `VGN_ROUTES.line_mode` = `line_mode`. A trip is cut if any of the chosen rows cuts it:
- `line_dropped`: every trip of the line.
- `window_dropped`: trips whose first departure is in the window.
- `trip_dropped`: number the line's trips per `direction_id` by first departure; cut number 2 (`trip_rank = 2`), or number 2 counted from the end (`trip_rank = -2`).
- `headway`: for the line's trips per `direction_id` whose first departure is in the window, cut the window into slots of `headway_new_min` minutes from `window_start` and keep only the first trip in each slot. A line that already runs at the new headway keeps all its trips; one that runs twice as often loses every other trip.
- `not_modeled`: nothing is cut. These are shortened routes, dropped short runs, named reinforcement trips, unspecified "single trips", on-demand replacements (Rufbus) and the Nightliner network that replaces day service on weekend mornings in the end state. Their `model_note` says why.

Statements that describe a cut on part of a route ("bis Henenfelder", "Ende von Fahrten an Vogelweiherstraße") are applied to the whole line and say so in `model_note`. Two corrections are noted on their rows: in the end state, the Mon–Thu and Fri cells of trams 4, 5 and 7 and every cell of bus 83 are carried over from the March table, because the end-state table leaves them empty while the document's own summary lists those measures for the end state too.

##### CYCLING_INFRASTRUCTURE — cycle infrastructure inside the city, from OpenStreetMap
| column | meaning |
|---|---|
| segment_id | OSM way id |
| street | OSM name (empty for unnamed paths) |
| length_m | length along the way |
| path_type | Cycle track (Radweg); Cycle street (Fahrradstrasse); Cycle track along a road (Radweg); Separated cycle and footpath; Painted lane (Radfahr-/Schutzstreifen); Shared footpath (Gemeinsamer Geh- und Radweg); Shared lane or bus lane; Field or forest track, cycling designated |
| directions | travel directions served: 2 for a two-way path or lanes on both sides of a road, 1 otherwise |
| highway, surface | OSM tags |
| start_lat/lon, end_lat/lon, mid_lat/lon | WGS84; the midpoint is along the line |
| bezirk_no, district_no | from the midpoint; ways outside the city are dropped |

Network length counting both directions: `SUM("length_m" * "directions")`. OSM shows mapped infrastructure; completeness varies.

##### CYCLE_NETWORK_PLAN_2021 — the city's cycle network plan, digitized
From the Radwegenetzplan PDF (Stand 01/2021, Verkehrsplanungsamt). `scripts/digitize_radnetz_2021.py` georeferenced the page against OpenStreetMap streets and paths (affine fit; median deviation 6 m, 90 % within 11 m) and extracted the layers drawn as vectors, plus the raster "decided planning" band along its centre line. The existing network ("Bestand") is not extracted; use `CYCLING_INFRASTRUCTURE` for it.

| column | meaning |
|---|---|
| segment_id | line id |
| category | `planned` (blue in the plan), `decided_planning` (beschlossene Planung, pink), `built_2013_2020` (Umsetzungen seit 2013, red), `quiet_street_route` (dotted: routes over quiet side streets), `other_path` (dashed: field, forest and canal paths) |
| directions | 2 for a two-way route, 1 for one-way (planned and built lines only; the plan draws one-way routes thinner) |
| length_m | line length in m |
| start_lat/lon, end_lat/lon, mid_lat/lon | WGS84 |
| in_nuernberg, bezirk_no, district_no | area of the midpoint; the map also covers Fürth, Stein, Schwabach and the Reichswald (in_nuernberg = 0) |
| shape_wkt | LINESTRING in WGS84 |

It's a plan from January 2021: some `planned` lines are built by now (compare them with today's OSM cycle infrastructure), and `ROADWORKS` (`is_cycling = 1`) has the current projects.

##### WEATHER_DAILY — DWD station 03668 Nürnberg
count_date, temp_min_c, temp_max_c, temp_mean_c, rain_mm, sunshine_hours, cloud_cover_pct (oktas converted to %), snow_depth_cm, wind_mean_ms, source (`historical` = quality-checked, through 2025-12-31; `recent` after). 2025-01-01 to 2026-10-27.

##### BIKE_COUNT_STATIONS — the 12 permanent bicycle counters
station (RZG001–RZG012), station_name, site_id, lat, lon, bezirk_no, district_no, in_nuernberg, first_data, last_data, note. Königstor (RZG001) is out of service since April 2024.

##### BIKE_COUNTS_DAILY — one row per counter per day
count_date, station, dir_in, dir_out, total, zero_reported, temp_min_c, temp_max_c, rain_mm, sunshine_hours, cloud_cover_pct. 2025-01-01 to 2026-10-27. The counter pages report an outage as 0; such days have `total` empty and `zero_reported = 1`. Directions are labeled only "in" and "out". Seewiesenweg (RZG004) stops in Nov 2025, Kornburger Straße (RZG012) in Jun 2026.

The counts are read from the city's public Eco-Counter pages when the dataset is built (`scripts/build_nuernberg_dataset.py`; `--skip-bike-counters` leaves them out). There is no API and no stated licence.

##### ROADWORKS — SÖR's planned and ongoing works in the street
From the city geoportal (SÖR Baukoordination, `Fachdaten_G/SOER_BAUKOP_G_V`, layer `SOER_PLAN_BAUMASSNAHMEN`), retrieved when the fetch script ran.

| column | meaning |
|---|---|
| roadwork_id | SÖR file number (AKZ) |
| kind | type of work, e.g. Tele, Strom, Fernwärme, Kanal, Straßenneu- und Umbau, Gleisbau, LSA: Umbau von Anlagen |
| description, utility, street, section, road_type | free text (German) |
| status | `in Planung` or `im Bau` |
| start_date, end_date | DATE; planned works run to 2035 |
| responsible, department | who carries it out (SÖR unit, utility, VAG …) |
| is_cycling | 1 when the description names cycle infrastructure (Radweg, Fahrradstraße, RVR, Radschnellverbindung …) and it isn't a utility work |
| is_tram_track | 1 for track works (Gleisbau, Gleiserneuerung …) |
| centroid_lat, centroid_lon, bezirk_no, district_no | vertex mean of the polygon and its area |
| shape_wkt | POLYGON / MULTIPOLYGON in WGS84 |

##### ROADWORK_PERMITS — street-use permits for works (Sondernutzung)
permit_no, applicant, reason, utility, street, section, applied_date, start_date, end_date, status (`ausgegeben`, `in Bearbeitung`, `genehmigt`), centroid, bezirk_no, district_no, shape_wkt (LINESTRING).

##### ROADWORK_DIVERSIONS — diversions
diversion_id, name, kind (`Radumleitung` = cycle-path closure with diversion, `MIV-Umleitung` = motor traffic), start_date, end_date, centroid, bezirk_no, district_no, shape_wkt.

#### Joins
- Area rollups by location: `X.district_no = DISTRICTS.district_no` for stops, project stations, cycle segments, counters.
- Departures per stop: `VGN_STOP_TIMES st JOIN VGN_TRIPS t ON st."trip_id" = t."trip_id" JOIN VGN_ROUTES r ON t."route_id" = r."route_id"`, filtered to the services running on the reference weekday, Wednesday 21 Oct 2026: `VGN_CALENDAR` with `wednesday = 1` and `DATE '2026-10-21'` between `start_date` and `end_date`, plus the services added (`exception_type = 1`) and minus those removed (`exception_type = 2`) on that date in `VGN_CALENDAR_DATES`. The reference Saturday (for the service cuts, from v6) is Saturday 24 Oct 2026, with `saturday = 1`, filtered the same way.
- Service cuts: `PT_SERVICE_CUTS."line" = VGN_ROUTES."route_short_name"`, with `day_type` `mon_thu` for the reference weekday and `sat` for the reference Saturday (see the table for how each rule cuts trips).
- Capacity offered: add `JOIN VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode" LEFT JOIN LINE_CAPACITY l ON l."line" = r."route_short_name" AND l."line_mode" = r."line_mode"` and `SUM(COALESCE(l."capacity_per_trip", v."capacity_per_trip"))` instead of `COUNT(*)`.
- Demand: `DISTRICT_POPULATION` and `DISTRICT_EMPLOYMENT` join on `district_no`. `DISTRICT_HOUSING` and `DISTRICT_PROFILE` join on `district_no` and `year`.

#### Walking distance (Exasol SQL)
A stop counts for every area within 300 m (bus, tram) or 600 m (U-Bahn, S-Bahn, regional rail) of the area polygon. Exasol has no `ST_POINT` or `ST_GEOMFROMTEXT`; build geometries by casting WKT, and transform to UTM 32N (EPSG:25832) so `ST_DISTANCE` returns meters:
```sql
WITH stops AS (
  SELECT s."stop_id",
         ST_TRANSFORM(CAST('POINT(' || CAST(s."stop_lon" AS DECIMAL(9,6)) || ' '
                                    || CAST(s."stop_lat" AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.VGN_STOPS s
  WHERE s."stop_lat" BETWEEN 49.30 AND 49.58 AND s."stop_lon" BETWEEN 10.92 AND 11.30
), areas AS (
  SELECT d."district_no", ST_TRANSFORM(CAST(d."polygon_wkt" AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.DISTRICTS d
)
SELECT a."district_no", s."stop_id", ST_DISTANCE(a.g, s.g) AS distance_m
FROM stops s JOIN areas a ON ST_DISTANCE(a.g, s.g) <= 600;
```
The bounding box keeps most of the regional stops out of the distance join. The full walking-distance model over all areas takes a few seconds.

For a quick point-to-point distance without geometry, the haversine formula works too:
```sql
2 * 6371000 * ASIN(SQRT(
    POWER(SIN(RADIANS(b."lat" - a."lat") / 2), 2) +
    COS(RADIANS(a."lat")) * COS(RADIANS(b."lat")) * POWER(SIN(RADIANS(b."lon" - a."lon") / 2), 2)
)) AS distance_m
```

#### Example
```sql
SELECT s."station_name", d."district_name", AVG(b."total") AS avg_daily
FROM NUERNBERG_DATASET.BIKE_COUNTS_DAILY b
JOIN NUERNBERG_DATASET.BIKE_COUNT_STATIONS s ON s."station" = b."station"
JOIN NUERNBERG_DATASET.DISTRICTS d ON d."district_no" = s."district_no"
WHERE b."rain_mm" > 1 AND b."total" IS NOT NULL
GROUP BY 1, 2 ORDER BY 3 DESC;
```

#### Known gaps (say them)
- No passenger counts, delays, crowding, live traffic or event data.
- Vehicle capacities are planning values per mode or line, not the formation of each trip. S-Bahn standing room and the regional-rail value are estimates.
- Jobs are counted for 2019–2024 (employees subject to social insurance only) and 2005 (a wider definition); there is no jobs forecast.
- Housing completions lag behind move-ins; registered cars include business fleets.
- Population after 2024 is a model built on a per-Stadtteil forecast that ends in 2033.
- Roadworks: what is built and when, not how traffic is affected (no closure type). A work spanning several streets is filed under the area of its centroid.
- Bicycle counters: twelve points, daily values only, one out of service, outages reported as 0.
- OSM cycle infrastructure says nothing about width, surface quality, gaps or junction safety.
- GTFS `shapes` is not in this feed, so route geometry is not available; use stop sequences.
- Service cuts: a proposal, not a decision (the council decides by 30 Nov 2026). Only P3 is published line by line; which of its rules belong to P1 and P2 is inferred from the package descriptions, P4 is modeled only through its three concrete measures (with an assumed 30/60-minute split by mode), and P5 adds nothing that can be modeled. Shortened routes, short runs, on-demand replacements and the weekend-morning Nightliner network are listed but not modeled, so the modeled loss is slightly too high on weekend mornings and too low where routes are shortened. The passenger and euro figures are VAG's estimates.

## 3. The dashboard's model

_Source: `research/urban-planning.md`_

### Urban planning: how well each Nürnberg area is served by scheduled public transport

The model and the questions behind the dashboards `nuernberg-mobility-planning-v1` to `-v7` on `NUERNBERG_DATASET`, reference weekday Wednesday 2026-10-21 (and, for the service cuts in v6, reference Saturday 2026-10-24). From v3 on, the model measures scheduled service (capacity offered = departures × capacity per trip), not passengers. v1 and v2 are deliberately naive first versions (departures at the stops inside each area); v3 corrects them. No results are stored here: every value comes from the dashboards, computed live.

#### The model (from v3 on)

- **Unit.** 79 areas: the 87 statistical Bezirke, with six groups of small Bezirke merged the way the city publishes their population (18/19, 34/35, 38/39, 41/42/43, 75/85/87, 76/77).
- **Supply.** Every scheduled stop event on the reference weekday, weighted by the capacity of its line (`LINE_CAPACITY`) or mode (`VEHICLE_CAPACITY`). A stop counts for every area whose polygon lies within walking distance: 300 m for bus and tram, 600 m for U-Bahn, S-Bahn and regional rail. Stops are shared, so area values don't add up to a city total; the city value is total capacity within reach divided by total activity.
- **Demand.** Activity = residents + w × jobs. Residents: the Bezirksatlas count for 2024; for later years a linear path to `pop_2033_model`, held after 2033. Jobs: employees subject to social insurance at the place of work, 31 Dec 2024, per area, held.
- **Comparison.** Each area against the 2024 city value at the same w.
- **Service cuts (v6).** The city's proposed savings packages (`PT_SERVICE_CUTS`), applied to the reference day's VAG trips: a trip is cut if any rule of the selected package cuts it. P3 is published line by line; P1 and P2 are sorted out of it and P4 adds its concrete measures. The base is 2027: residents modeled for 2027, jobs 2024, the funded projects open by 2027. Each area's capacity with the package is compared with its capacity without it, on the same day type. Method in [vag-cuts-2027-notes.md](vag-cuts-2027-notes.md).
- **Projects (v5).** From the opening year (or the risk year with pessimistic dates), each project station adds the published frequency × (6 peak + 13 off-peak hours) × 2 directions, or the weekday departures per station of the analog line, with the same walking-distance rule.

Why walking distance and not "stops inside the area": Nürnberg's areas are small and many stations sit on boundaries. Counting only the stops inside the area, an area whose U-Bahn stations sit on its border gets almost nothing and its neighbour gets all of it. With walking distance both get the line. The city value also rises, because shared stops count for every area they reach.

#

## 4. Findings

_Source: `research/urban-planning.md`_

### Urban planning: how well each Nürnberg area is served by scheduled public transport

The model and the questions behind the dashboards `nuernberg-mobility-planning-v1` to `-v7` on `NUERNBERG_DATASET`, reference weekday Wednesday 2026-10-21 (and, for the service cuts in v6, reference Saturday 2026-10-24). From v3 on, the model measures scheduled service (capacity offered = departures × capacity per trip), not passengers. v1 and v2 are deliberately naive first versions (departures at the stops inside each area); v3 corrects them. No results are stored here: every value comes from the dashboards, computed live.

#### The model (from v3 on)

- **Unit.** 79 areas: the 87 statistical Bezirke, with six groups of small Bezirke merged the way the city publishes their population (18/19, 34/35, 38/39, 41/42/43, 75/85/87, 76/77).
- **Supply.** Every scheduled stop event on the reference weekday, weighted by the capacity of its line (`LINE_CAPACITY`) or mode (`VEHICLE_CAPACITY`). A stop counts for every area whose polygon lies within walking distance: 300 m for bus and tram, 600 m for U-Bahn, S-Bahn and regional rail. Stops are shared, so area values don't add up to a city total; the city value is total capacity within reach divided by total activity.
- **Demand.** Activity = residents + w × jobs. Residents: the Bezirksatlas count for 2024; for later years a linear path to `pop_2033_model`, held after 2033. Jobs: employees subject to social insurance at the place of work, 31 Dec 2024, per area, held.
- **Comparison.** Each area against the 2024 city value at the same w.
- **Service cuts (v6).** The city's proposed savings packages (`PT_SERVICE_CUTS`), applied to the reference day's VAG trips: a trip is cut if any rule of the selected package cuts it. P3 is published line by line; P1 and P2 are sorted out of it and P4 adds its concrete measures. The base is 2027: residents modeled for 2027, jobs 2024, the funded projects open by 2027. Each area's capacity with the package is compared with its capacity without it, on the same day type. Method in [vag-cuts-2027-notes.md](vag-cuts-2027-notes.md).
- **Projects (v5).** From the opening year (or the risk year with pessimistic dates), each project station adds the published frequency × (6 peak + 13 off-peak hours) × 2 directions, or the weekday departures per station of the analog line, with the same walking-distance rule.

Why walking distance and not "stops inside the area": Nürnberg's areas are small and many stations sit on boundaries. Counting only the stops inside the area, an area whose U-Bahn stations sit on its border gets almost nothing and its neighbour gets all of it. With walking distance both get the line. The city value also rises, because shared stops count for every area they reach.

#### v1: a first map, departures per resident (naive)

Scheduled departures on the reference weekday at the stops that stand in each area, per resident, against the city value. Deliberately naive: a departure counts the same whatever the vehicle, and a stop counts only for the area it stands in. What to look at: which areas come out low and high, and how hubs with few residents (Tafelhof, the Hauptbahnhof) behave in a per-resident measure.

#### v2: residents and jobs

**Jobs data.** Employees subject to social insurance at the place of work per area, 31 Dec 2019–2024 (statistics office, business register). The model uses 2024. The older 2005 count (including self-employed and marginal jobs) stays in the data for its sector split; in 2005 Eberhardshof still included AEG and Quelle. See [district-growth.md](district-growth.md#3a-update-2026-11-06-the-20192024-count).

The dashboard adds jobs with a weight w (default 1) and the U-Bahn and tram stations on the map, and still counts departures at the stops inside each area. What to look at: how hubs move once their jobs count, and the area at the bottom. Gostenhof comes out lowest of all 79, far below its neighbour Himpfelshof on the same U1, because the Plärrer and Gostenhof U-Bahn stations stand just inside Himpfelshof.

#### v3: two flaws, and the fix

v3 counts capacity per departure and every stop within walking distance (the model above). The two flaws of v1 and v2: a stop counted only in the area it stands in hands a boundary station to one side (Gostenhof and Himpfelshof), and counting departures makes a bus area such as Maiach look as well served as an inner-city area on the U-Bahn. What to look at: which areas move most from v2 to v3, and which stay low in both (robust findings).

**Who depends on it** (`DISTRICT_PROFILE`, 2025). Compare service with registered cars per 1,000 residents and the share of residents on minimum-income benefits, by quarter of areas ranked by service. Exclude areas where business fleets push registered cars above 700 per 1,000 residents. Check how much of the car difference density explains.

#### v4: the forecast to 2033, if nothing is added

**Forecast.** The city's small-area forecast (M558) gives 2033 only per Stadtteil: 554,710 residents in total. Growth is concentrated where new homes are built: Westliche, Nordwestliche and Südliche Außenstadt. The other Stadtteile stagnate or shrink (see [district-growth.md](district-growth.md)). The per-area 2033 value is a model: each Stadtteil's new-build movers (M558) go to the areas with listed new homes (city WFS, at most 2 movers per listed home), the rest of the Stadtteil's change goes by residents. M558's movers are gross (many come from elsewhere in the city), so areas without new homes shrink in the model.

The dashboard holds service as it is and lets population follow the forecast. What to look at: the change in capacity per person for the city and per area by 2028 and 2033, in particular Lichtenreuth (41/42/43, the new district on the former Südbahnhof, with the Technische Universität), the western new-build areas (Tiefes Feld, the former Quelle site) and the north-west (Wetzendorf).

**Housing statistics as a check** (`DISTRICT_HOUSING`, 2012–2025). Compare homes permitted and completed per area with the residents count. Completions are recorded when the builder reports them, so they lag.

#### v5: rail and tram projects as scenarios

**Projects.** 10 projects, curated in [pt-projects-notes.md](pt-projects-notes.md):

| Group | Projects | Year |
|---|---|---|
| Funded | U3 Gebersdorf (Kleinreuth, Gebersdorf) | 2028 |
| | Tram 7 Hbf–Rathenauplatz–Stadtpark | Dec 2026 |
| | Tram 7 back on Allersberger Straße | 2027 |
| | Tram 4 Minervastraße | 2027 |
| | New stop Melanchthonplatz | 2028 |
| Dated, not funded | Tram 7 Lichtenreuth / Technische Universität | 2030 (risk 2031) |
| | StUB Am Wegfeld–Reutles | 2031 (risk 2032) |
| No date (placed at 2040) | Tram to Klinikum Süd; S9 Nordring; S9 Gräfenberg line with Buchenbühl halt | — |

The dashboard switches project groups on and off and can use pessimistic dates. What to look at: capacity added per weekday, the city value over time against 2024 for each group, which areas each project lifts, and which growing or poorly served areas no project touches.

**Caveats.** Frequencies of the Stadtpark and Lichtenreuth sections are borrowed from the Lichtenreuth plan (10-minute service); the StUB uses its published 10-minute service; S9 items use 2 trains per hour. Station coordinates for the StUB and S9 halts are approximate (see the notes). Money is the binding constraint: the city has no approved new borrowing for 2026 and must save at least €122 m a year from 2027 ([plans-facts.md](plans-facts.md)), which puts every unfunded project at risk.

#### v5, continued: when rail reaches the new homes

Measured from each new-build project's site (the centre of its outline on the city's map) with the same walking distances: which new homes have no rail stop within walking distance today, and when a project brings one, against the year the homes are first occupied. Method and SQL in [timing-and-construction.md](timing-and-construction.md).

#### v6: the savings package

The city must save, and VAG has proposed five packages of service cuts (`PT_SAVINGS_PACKAGES`). The council decides by 30 Nov 2026. v6 is deliberately simpler than v4 and v5: one fixed base (2027, with the new homes and the funded projects of that year), and three controls: the package (none, P1–P5), the day (reference Wednesday or Saturday) and the view (capacity per person, or the areas most affected). Only P3 is published line by line (`PT_SERVICE_CUTS`); P1 and P2 are sorted out of its rules by the package descriptions, P4 adds its three concrete measures, and P5 shows the same cuts as P4.

What to look at:
- How much each package removes on a weekday and on a Saturday, and where the big jump comes. Saturday loses more because P3 runs only the Nightliner network before 8:00.
- Which areas lose the largest share, how many people live there, and whether they were already below the city value.
- The areas along the three bus lines P3 withdraws, and whether other lines within walking distance cover them:
  - 81, an on-demand bus around Holzheim;
  - 82, Koppenhof–Krottenbach–Reichelsdorf;
  - 84, Plärrer–Dr. Erler Kliniken.
- The areas along trams 10 and 11, after 18:30 in P3 and all weekend in P4.
- How the new-build areas fare once the new homes are counted.

The passenger and euro figures are VAG's estimates; the model measures capacity only. Notes in [vag-cuts-2027-notes.md](vag-cuts-2027-notes.md).

#### v7: ask the assistant

v7 adds an assistant to v6 (it needs an OpenAI key); [assistant-context.md](assistant-context.md) is the context pack it reads.

#### Corridor briefings

The capstone (chapter 12) regroups the dashboards' views per growth corridor: the south-east (Lichtenreuth), the west (Tiefes Feld, the Quelle site), the north-west (Wetzendorf) and the north (Knoblauchsland, StUB). It adds no new model.

#### Construction (corridor briefings)

The planning series has no construction view; the corridor briefings (chapter 12) bring it in. The city's construction coordination (`ROADWORKS`) lists tram-track works for the coming years. What to look at: per year, the share of the city's tram stop events at stations within 50 m of an active tram-track work, and which areas depend most on those stops. The published track closure from 2 January to 30 November 2027 covers the south-western axis from Plärrer through Steinbühl and Gibitzenhof to Dianastraße and Landgrabenstraße. The Lichtenreuth tram is itself under construction 2027–2030, the years its residents move in. The hubs follow: Plärrer 2027–2031, an extra tram track at the Hauptbahnhof 2030–2031. Most other works are planned only a year or two ahead, so later years understate construction. Method and SQL in [timing-and-construction.md](timing-and-construction.md).

## 5. Growth: forecast, jobs, new homes

_Source: `research/district-growth.md`_

### Nürnberg growth per Stadtteil and Bezirk: jobs, official population forecast, development areas

Researched 2026-10-28. Web research plus one read-only lookup in our DB (schema `NUERNBERG_DATASET`). Every number below comes from a source I opened or downloaded (marked *verified* in section 6). Numbers I saw only in search snippets are marked *(unverified)*.

**How to read the columns.** **Count** means registered population with Hauptwohnung (main residence) at 31 December, from the Melderegister. **Forecast** means the city's *Kleinräumige Bevölkerungsvorausberechnung* (small-area population projection) by the Amt für Stadtforschung und Statistik. **Jobs** means people working *in* an area (place of work), not people living there.

**Spatial units.** Nürnberg has 10 Statistische Stadtteile (00–09), 87 Statistische Bezirke (01–97, the Stadtteil is the tens digit) and 316 Distrikte. Our DB has `BEZIRKE` (87) and `DISTRICTS` (79, some Bezirke grouped).

---

#### 1. Summary

- **Update 2026-11-06: jobs by place of work per area exist for 2019–2024.** The statistics office's portal "Nürnberg in Zahlen" has SV-Beschäftigte am Arbeitsort per zusammengefasstem Statistischem Bezirk (the same 79 areas as `DISTRICTS`), 31 Dec 2019–2024, from the business register, plus jobs not assigned to an area. `DISTRICT_EMPLOYMENT.jobs_2019` … `jobs_2024`, and the model now uses 2024. See section 3a. The rest of this bullet is the original finding.
- **Jobs by place of work exist per Bezirk only for 2005.** The only small-area jobs table I found is Tab. 1 of the Statistischer Monatsbericht Oktober 2006: *Beschäftigte* per Statistischer Bezirk for 1970, 1987 and 2005, split into three sectors. Total 2005: **342,000**. All 87 Bezirke are transcribed into `jobs.csv`; the rows add up exactly to the printed totals. Everything newer is either **city-wide only** (SV-Beschäftigte am Arbeitsort, Dec 2022: **318,577**) or **by place of residence** (Bezirksatlas t9, Innergebietliche Strukturdaten, Bezirksdatenblätter). The Innergebietliche Strukturdaten 2023 say so explicitly (PDF p. 58): the Bezirk tables follow the *Wohnortprinzip*.
- **No jobs forecast per area was found.** The Nahverkehrsentwicklungsplan 2025 (IVV, 2012) had a *Strukturdatenprognose 2025* with residents and jobs for the region, but only its table of contents and the short version are online. The tables themselves were not found.
- **Population forecast per Stadtteil, with numbers: yes.** The context for this note assumed that M558 shows 2033 values per Stadtteil only as map circles. That is wrong: the **text** of M558 gives the 2033 value for all 10 Stadtteile (PDF pp. 11 and 16). They add up to 554,710, which matches the city total of 554,700. The earlier edition M529 (base 2021, horizon 2035) also gives all 10 Stadtteile in its text (pp. 15 and 18). Both editions are in `forecast.csv`. **No forecast per Bezirk is published.**
- **Where the growth goes (M558, 2024→2033, from the values M558 prints):** 06 Westliche Außenstadt **+5,880 (+17.2 %)**, 07 Nordwestliche Außenstadt **+4,939 (+14.0 %)** and 04 Südliche Außenstadt (forecast 57,160 in 2033; M558 states no 2024 value for 04). All other Stadtteile stagnate or shrink: 01 −1,960, 05 −1,296, 08 −1,202, 02 −910, 09 −625, 03 −606; 00 (no 2024 value printed) is forecast at 59,260.
- **What drives it:** new homes. M558 assumes 49,130 people moving into new buildings from 2025 to 2033. 12,280 of them go to 06, 11,350 to 04 and 8,960 to 07. This is already in the DB as `STADTTEIL_NEWBUILD`.
- **The city's new-build pipeline is available per project, with polygons.** WFS layer `Wohnungsneubau:Schwerpunkte_des_Wohnungsneubaus` (geoportal.nuernberg.de) lists 44 major projects with numbers of homes and year of first occupancy. I assigned each project to a Bezirk by point-in-polygon against our `BEZIRKE` polygons. Result: `newbuild_projects.csv`. The largest are Lichtenreuth/Brunecker Straße (Bezirk 41, 3,585 homes), the former Quelle area on Fürther Straße and Muggenhofer Straße (Bezirk 64, 2,480 homes) and Tiefes Feld (Bezirke 60/63, 1,913 homes).
- **What this means for transport.** Growth is concentrated in three corridors:
  1. **South:** Lichtenreuth, Bezirke 40/41. It has U1 Hasenbuck today; the tram 7 extension is due at the end of 2028. The TU Nürnberg is planned for about 6,000 students *(unverified)*.
  2. **West:** Tiefes Feld, Bezirke 60/63, with U3 Kleinreuth opening in 2026. The former Quelle area, Bezirk 64, is on the U1 Eberhardshof corridor.
  3. **North-west:** Wetzendorf and Nordwestring, Bezirke 70/72. Its new homes have no rail project announced in the sources I read; existing tram routes run along Nordwestring and Wetzendorf, but I did not check them.

  The inner city, the south-east (Langwasser) and the north-east are forecast to lose residents.

---

#### 2. Stadtteil table: counts and forecast

Sources per column:
- **(B) M558 count 2024:** as printed in M558, text on PDF p. 16. Values in brackets are implied by the change printed on PDF p. 11 (2033 value minus the stated change). "–" means the text gives no value.
- **(C) M558 forecast 2033:** M558 text, PDF p. 11 (00–02) and p. 16 (03–09).
- **Δ 2024→2033:** C − B; "–" where M558 gives no 2024 value.
- **(D) New-build movers 2025–2033:** M558 PDF pp. 8–9 (the same values as DB `STADTTEIL_NEWBUILD`).
- **(E) M529 forecast 2035:** the previous edition (base 2021), PDF pp. 15 and 18. Shown so the size of the revision is visible.

The 2024 counts per Stadtteil from our DB (`DISTRICT_POPULATION`) are not repeated here; query them live (see the caveats in section 5 on how to aggregate).

| No. | Stadtteil | (B) M558 2024 | (C) **Forecast 2033** | Δ 2024→33 | Δ % | (D) New-build movers 25–33 | (E) M529 forecast 2035 |
|---|---|---:|---:|---:|---:|---:|---:|
| 00 | Altstadt und engere Innenstadt | – | 59,260 | – | – | 2,480 | 57,870 |
| 01 | Weiterer Innenstadtgürtel Süd | (97,350) | 95,390 | −1,960 | −2.0 % | 3,550 | 94,660 |
| 02 | Weiterer Innenstadtgürtel West/Nord/Ost | (92,990) | 92,080 | −910 | −1.0 % | 2,730 | 89,120 |
| 03 | Südöstliche Außenstadt | 48,086 | 47,480 | −606 | −1.3 % | 1,980 | 45,280 |
| 04 | Südliche Außenstadt | – | 57,160 | – | – | 11,350 | 54,580 |
| 05 | Südwestliche Außenstadt | 48,176 | 46,880 | −1,296 | −2.7 % | 1,730 | 43,991 |
| 06 | Westliche Außenstadt | 34,170 | 40,050 | +5,880 | +17.2 % | 12,280 | 46,840 |
| 07 | Nordwestliche Außenstadt | 35,181 | 40,120 | +4,939 | +14.0 % | 8,960 | 44,580 |
| 08 | Nordöstliche Außenstadt | 29,022 | 27,820 | −1,202 | −4.1 % | 1,510 | 27,800 |
| 09 | Östliche Außenstadt | 49,095 | 48,470 | −625 | −1.3 % | 2,550 | 48,610 |
| | **City** | 546,397 (forecast base 542,966) | **554,700** | +11,740 (vs base) | +2.2 % | 49,130 | 553,300 |

The city row comes from M558 PDF pp. 1, 6 and 8 and M529 p. 1. The M529 values add up to 553,331 against a printed total of 553,300.

**Revision between editions.** In 06, M529 expected 46,840 by 2035; M558 expects 40,050 by 2033. In 07 the figures are 44,580 and 40,120. The new-build assumptions for these two Stadtteile were cut from 15,530 to 12,280 (06) and from 11,910 to 8,960 (07): M529 counted 2022–2035, M558 counts 2025–2033. This is consistent with Tiefes Feld slipping; the city page now gives first residents "ab 2030". 04 was revised upwards, from 54,580 in 2035 to 57,160 in 2033, which fits Lichtenreuth Modul II and the TU module getting building rights in 2025.

**Bezirk level.** Neither edition publishes Bezirk values. To get per-Bezirk numbers, distribute each Stadtteil's change using `newbuild_projects.csv` (which Bezirk the homes go to) plus a uniform trend for the remainder. That would be our own model, not an official number.

---

#### 3. Jobs at place of work

| What | Unit | Year | Value | Usable? |
|---|---|---|---|---|
| **SV-Beschäftigte am Arbeitsort, table `WASU_SvBs_AO_zbez`** (added 2026-11-06) | **79 areas** | **2019–2024** | – | **Yes** → `DISTRICT_EMPLOYMENT.jobs_2019..2024`; the model uses 2024 |
| Niederlassungen nach Wirtschaftssektoren, `WASU_Niederlassungen_Wirtschaftssektoren_zbez` | 79 areas | 2019–2024 | – | Yes → `establishments_*` |
| Beschäftigte by sector, Monatsbericht Okt. 2006, Tab. 1 | **87 Bezirke** | 1970 / 1987 / **2005** | 342,000 city | **Yes, but 20 years old** → `jobs.csv` |
| SV-Beschäftigte am Arbeitsort | City | Dec 2022 | 318,577 (Jun 2022: 318,346) | City control total only |
| SV-Beschäftigte am Wohnort | Bezirk / Distrikt | Dec 2022 | 230,314 city | No (residents). Commuter balance +88,263 |
| Bezirksatlas t9, Bezirksdatenblätter "Beschäftigte" | Bezirk | 2022–2025 | – | No (place of residence; e.g. Bezirk 82 Schafhof shows 864) |
| Online tables MBES_J07 etc. (sta_1100) | City | from 2008 | – | City only; the session-bound server could not be scripted |
| NVEP 2025 Strukturdatenprognose (IVV 2012) | Model zones | 2025 forecast | – | Tables not online (Teil 1 of the Langfassung not found) |

**Definition of the 2005 table:** "Beschäftigte": employees **and** self-employed people, including marginal employment. The source is the Unternehmensregister 2005, carried forward with the Erwerbstätigenrechnung (labour-force accounting) by the statistics office. It is therefore **broader** than the SV-Beschäftigte count: 342,000 in 2005 against about 318,600 SV jobs in 2022.

**Known big changes since 2005 that the table misses** (my own knowledge, not checked against sources):
- Bezirk 64 lost the AEG plant (closed 2007) and Quelle (closed 2009); the former Quelle area is now being converted to housing.
- Bezirk 15 Gugelstraße and other industrial sites have shrunk.
- The UTN campus (Bezirk 41/40) is new.
- Nordostpark (82) and Südwestpark (61) are likely to have grown.

##### 3a. Update 2026-11-06: the 2019–2024 count

The portal "Nürnberg in Zahlen" (https://online-service2.nuernberg.de/Informationsportal11_nbg/) serves its tables through the DUVA table viewer (`aswn.dll`), which can be scripted after all: `scripts/fetch_nuernberg_statistik.py` reads the HTML tables (one request per year where the table has a year filter). Source of the jobs table: Bayerisches Landesamt für Statistik, Unternehmensregister. Definition: employees subject to social insurance at the place of work, 31 December; no civil servants, self-employed or marginal jobs, so it is narrower than the 2005 count. The values are in `DISTRICT_EMPLOYMENT.jobs_2019` … `jobs_2024`; query them live. The table doesn't name employers, so large one-year moves in an area may be a single employer moving or being reassigned.

**Suggested use (original, before the update):** use the 2005 sector table only as a *spatial distribution*, scaled to the 2022 city total (318,577 SV jobs, or about 342k + growth if self-employed people are included), and correct the few Bezirke listed above by hand. The proper fix is a data request to the Amt für Stadtforschung und Statistik (statistikinfo@stadt.nuernberg.de). They have BA small-area data ("Arbeitsmarktdaten in kleinräumiger Gliederung") and the Unternehmensregister, which they used in 2006.

---

#### 4. Development areas

Homes, first occupancy and Bezirk come from the city's WFS (`newbuild_projects.csv`), unless the row says otherwise. Residents are from the city project pages. The "Bezirk" column is from my point-in-polygon assignment, with the share of the polygon area in brackets where a project spans two Bezirke.

| Area | Bezirk (Stadtteil) | Homes | Residents | Timing | Status / transit | Verified? |
|---|---|---:|---:|---|---|---|
| **Lichtenreuth** (ehem. Südbahnhof), Modul I "Hasenbuck Süd" BP 4635 + Modul II "Ingolstädter Str." BP 4652 | 41 / 40 (04) | WFS: 2,287 + 1,298 = 3,585 | Modul I 5,100–6,000; Modul II 2,600 (city page) | WFS first occupancy 2024 / 2025; Kita 2026; tram 7 end of 2028 | Modul I in force since 2019; BP 4652 and 4656 adopted as Satzung on 17 Jul 2025 | Verified |
| **TU Nürnberg (UTN)**, BP 4656, Modul III | 41/40 (04) | Student housing only | ~6,000 students at full build-out *(unverified)* | Groundbreaking May 2026 *(unverified)* | 37 ha (27 ha building land); a jobs and education generator | Verified (area) / unverified (students) |
| **Tiefes Feld** (Kleinreuth/Großreuth), BP 4445 A/B | 60 / 63 (06) | WFS: Südwest+Südost 1,498 (`GP_WE_GES` 1,100) + Nordwest 415 | City: "über 2.000 Wohnungen", about 4,000 residents (an older page says 1,700 homes / 3,500 residents) | City page: first residents "ab 2030"; WFS says 2027 (SW/SO) and 2029 (NW). U3 Kleinreuth opens 2026; Neue Rothenburger Str. by 2028 | 4445 A in force since Oct 2022; 4445 B adopted 29 Apr 2026 | Verified |
| **Former Quelle area**, Fürther Str. 215 + Muggenhofer Str. | 64 (65) (06) | 1,000 + 1,480 | – | WFS 2026 / 2028 | U1 Eberhardshof/Muggenhof | Verified (WFS only) |
| **Wetzendorf**, BP 4641 A Parlerstraße + 4641 B Schleswiger Str. | 72 (70) (07) | City: about 1,110 in total; B about 290. WFS: Schleswiger Str. 350, Bielefelder Str. 304 | About 2,250 (B about 650) | 4641 A in force 15 Jan 2025; B in planning; WFS first occupancy 2027–2028 | – | Verified |
| **Nordwestring** 101-103 / 85-87 | 70 (23) (07) | 290 + 47 | – | 2026 / 2024 | – | Verified (WFS) |
| **Züricher Straße**, BP 4614 | 60 (06) | 446 (wbg: 181, ready spring 2028) | About 1,100 | BP in force since 2018 | U3 Großreuth. Probably WFS "Wallensteinstraße" (148) | Verified (page); WFS match inferred |
| **Lochnerstraße** | 19 (50) (01) | 425 | – | 2028 | – | Verified (WFS) |
| **Sielstraße** | 22 (23) (02) | 400 | – | 2026 | – | Verified (WFS) |
| **Scharrerstraße** | 10/11 (01) | 342 | – | 2024 | – | Verified (WFS) |
| **Hintermayrstraße** | 80/26 (08/02) | 339 | – | 2025 | – | Verified (WFS) |
| **Kellerstraße** (Reichelsdorfer Keller) | 48 (04) | 295 | – | 2026 | – | Verified (WFS) |
| **Ostendstraße 113-121** | 92 (09) | 295 | – | 2024 | – | Verified (WFS) |
| **Marienberg** (east of Flughafenstr., north of Marienbergstr.) | 83/84 (08) | – | – | SEM started 2017, dropped 31 Jan 2024 *(unverified)*; now BP 4671, started 23 Mar 2023 *(unverified)* | Housing, mixed use, commercial along Flughafenstraße | City page verified (no numbers) |
| **Worzeldorf Ortsrand**, BP 4673 | 49 (04) | About 151 (traffic study, Aug 2023) *(unverified)* | – | Draft as of Nov 2025 *(unverified)* | – | Search-only |
| **Kornburg** "Am Bruckweg" (wbg) | 49 (04) | About 130 *(unverified, 2018)* | – | Built around 2018 | – | Search-only |
| **Seeleite** | – | – | – | – | Nothing found | – |
| **Schmalau-Ost**, BP 4575 (commercial) | 78 (07), inferred | – | – | In force (Amtsblatt 17/2023) | About 8 ha of **new commercial land**, a jobs site | Verified |
| **Dorfäckerstraße-Ost**, BP 4506 (commercial) | 72 (07) | – | – | In force (Amtsblatt 17/2018) | About 2.5 ha of new commercial land | Verified |

All 44 WFS projects are in `newbuild_projects.csv`; the table above shows the largest. **The WFS does not cover all new building.** Compare the WFS homes per Stadtteil with the M558 new-build movers (column D): a few movers per home is plausible; far more movers than homes points to projects the layer does not list (in 07, for example, Wetzendorf 4641 A and smaller projects).

---

#### 5. Caveats

- **Two different 2024 bases.** M558 projects from a *reduced* base of 542,966; the register count is 546,397 (the difference is a register clean-up, PDF p. 6). Our DB holds the register count (Bezirksatlas). The 2024 values printed in M558 per Stadtteil presumably sit on the reduced base or use a different allocation; M558 does not say which. Compare **changes**, not levels, between M558 and our DB.
- **Our DB groups Bezirke across Stadtteile.** `DISTRICTS` row 75 "Almoshof/Mooshof/Flughafen (75/85/87)" has `stadtteil_no` = 8. Bezirk 75 belongs to Stadtteil 07, and `BEZIRKE` says so correctly. Stadtteil sums from `DISTRICTS` therefore shift Almoshof's population from 07 to 08. Aggregate via `BEZIRKE` or treat district 75 as split.
- **The jobs table is from 2005** (superseded 2026-11-06 by the 2019–2024 count in section 3a; 2005 stays in the data for its sector split). It is the only place-of-work data per Bezirk that I could find. Its definition (including self-employed and marginal jobs) differs from the SV-Beschäftigte count. Use it only as a distribution, as described in section 3.
- **The WFS layer is a snapshot.** I downloaded it on 2026-10-28. The field names (`N23_*` for homes by type, `GP_ERSTBEZUG` for first occupancy, `GP_WE_GES` for an alternative total) are my reading of the schema; no metadata says what they mean. `N23` probably means "Neubauannahmen 2023", the assumptions behind the forecast. Where `GP_WE_GES` differs from the N23 sum (Tiefes Feld SW/SO 1,100 vs 1,498, Muggenhofer Str. 990 vs 1,480), I used the N23 sum.
- **Bezirk assignment is approximate.** It uses grid-sampled point-in-polygon against our simplified `BEZIRKE` polygons. Shares under 5 % are dropped, and projects on a Bezirk border can flip.
- **Resident figures on city pages disagree.** The Tiefes Feld page alone gives 2,900, "knapp 4.000" and "etwa 4.000". Lichtenreuth has no stated total; Modul I and Modul II add up to about 7,700–8,600, but that sum is mine.
- **No jobs forecast.** Job numbers for UTN, Lichtenreuth commercial space, Schmalau-Ost and Dorfäckerstraße are not given anywhere I looked.

---

#### 6. Sources

**Verified (opened or downloaded):**
- M558: Kleinräumige Bevölkerungsvorausberechnung Nürnberg 2025–2033 (Amt für Stadtforschung und Statistik, 2025), 18 pp. City figures on pp. 1, 6, 8, 9 and 17; new-build movers per Stadtteil on pp. 8–9; Stadtteil 2033 values in the text on p. 11 (00–02) and p. 16 (03–09). https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2025/sus2025_m558_bevolkerungsvorausberechnungnurnberg2024_online.pdf
- M558, plain-language version (no Stadtteil numbers). https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2025/sus2025_m558_leichtesprache_deu.pdf
- M529: Kleinräumige Bevölkerungsvorausberechnung Nürnberg 2022–2035 (2022), 20 pp. Stadtteil values on pp. 15 and 18; new-build movers on p. 11; totals on pp. 1 and 11. https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2022/sus_bericht_m529.pdf
- Statistischer Monatsbericht Oktober 2006, "Beschäftigungsentwicklung und Strukturwandel in Nürnberg und Fürth". Method on PDF p. 2; Tab. 1 (Nürnberg, 87 Bezirke, 1970/1987/2005) on PDF p. 3; Fürth table on p. 4. https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2006/statistik_aktuell_200610.pdf
- Innergebietliche Strukturdaten Nürnberg 2023 (excerpt). Labour-market notes on PDF pp. 58–59 (printed pp. 107–108): Wohnortprinzip; SV jobs at place of work Dec 2022 318,577, at place of residence 230,314. Completions and permits per Bezirk 2022 on PDF pp. 48–51 (not extracted). https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/tabellenwerke/gebietszahlen/innergebietliche_strukturdaten_nuernberg_2023_www-version_geschwarzt.pdf
- Statistics table index sta_1100 (place-of-work tables are city-level only). https://www.nuernberg.de/internet/statistik/sta_1100.html
- WFS Wohnungsneubau, layers `Schwerpunkte_des_Wohnungsneubaus` and `Neubauvorhaben` (the same 44 projects), retrieved 2026-10-28. https://geoportal.nuernberg.de/server/services/Fachdaten/Wohnungsneubau/MapServer/WFSServer · Viewer: https://geoportal.nuernberg.de/masterportal/wohnbau/ · Context page: https://www.nuernberg.de/internet/stadtplanung/nuernberg_baut.html
- Lichtenreuth / Brunecker Straße project page (updated 25 Jun 2026). https://www.nuernberg.de/internet/stadtportal/brunecker_strasse.html
- Press release of 27 Dec 2024 (Lichtenreuth Modul I: 1,300 homes / 3,300 people, 5,100–6,000 planned, tram 7 end of 2028). https://www.nuernberg.de/presse/mitteilungen/pm_24586.html
- Press release of 18 Jul 2025 (BP 4652 / 4656 adopted as Satzung). https://www.nuernberg.de/presse/mitteilungen/pm_25792.html
- Tiefes Feld, Stadtplanung page. https://www.nuernberg.de/internet/stadtplanung/tiefesfeld.html
- Tiefes Feld, city portal page (updated 25 Jun 2026; "ab 2030", U3 Kleinreuth 2026). https://www.nuernberg.de/internet/stadtportal/tiefes_feld.html
- Wetzendorf. https://www.nuernberg.de/internet/stadtplanung/wetzendorf.html
- Züricher Straße. https://www.nuernberg.de/internet/stadtplanung/zuericherstr.html
- Schmalau-Ost. https://www.nuernberg.de/internet/stadtplanung/schmalau.html
- Dorfäckerstraße-Ost. https://www.nuernberg.de/internet/stadtplanung/dorfaeckerstr.html
- Stadtentwicklung Marienberg (no numbers). https://www.nuernberg.de/internet/stadtportal/behoerdenwegweiser/dienstleistung/stadtentwicklung_marienberg.html
- NVEP 2025 Schlussbericht Kurzfassung (Strukturdatenprognose described, no tables). https://online-service.nuernberg.de/viewer/api/v1/records/07056257/files/source/nvep2025_schlussbericht_kurzfassung.pdf
- NVEP 2025 Schlussbericht Langfassung Teil 7 (table of contents only lists 2.2 Strukturdatenprognose). https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/vpl/nvep2025_schlussbericht_langfassung_teil_7_bewertung_e-planfaelle_folgekosten_zusammenfassung.pdf

**Unverified (search results only):**
- UTN about 6,000 students at full build-out; groundbreaking May 2026. https://www.utn.de/files/2025/02/2025_02_13_Hintergrundinfo_Technische_Universitaet_Nuernberg-D.pdf · https://www.bayern.de/pdf/printpdf.php?id=195308
- Marienberg SEM dropped on 31 Jan 2024; BP 4671 started on 23 Mar 2023 (search summary).
- Worzeldorf Ortsrand BP 4673, about 151 homes. https://www.nuernberg.de/imperia/md/stadtplanung/bet_oeausl/16_4673_worzeldorfortsrand_oea_verkehrsmengenermittlung.pdf
- Kornburg "Am Bruckweg", about 130 homes (2018). https://spd-stadtratsfraktion.nuernberg.de/uploads/media/Antrag_Kornburg_Nord_Ost.pdf
- NVP Analyse 2003 with Verkehrszellen (not opened). https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/vpl/nvp_analyse_2003_langfassung.pdf
- Bezirksdatenblätter 2022–2025 (the "Beschäftigte" figure appears to be by place of residence). https://www.nuernberg.de/imperia/md/statistik/dokumente/bezirksdatenblatt/nbg/82-schafhof.pdf

## 6. Plans: assessed summary

_Source: `research/plans-research.md`_

### What Nürnberg is planning for public transport (as of 28 Oct 2026)

This note compares current plans in Nürnberg with the tutorial's planning question: how well is each Nürnberg area served by public transport, now and as the city grows, and what do the planned rail and tram projects change? The research was done in German, mostly from official sources: Stadt Nürnberg (Verkehrsplanungsamt, press office, Kämmerei), VAG, the Zweckverband StUB and the Bavarian transport ministry. I read the full texts of the Nahverkehrsplan draft 2025, the VAG annual report 2025, the StUB brochure (03/2026), the 2027 budget speech and the cycling round-table minutes.

One limit on coverage: nordbayern.de (NN/NZ) and BR24 produced almost no usable 2026 articles through the research tool. Local press reporting is therefore thin, mostly t-online Nürnberg. Items marked (unverified) were seen only in search results. The facts with sources are in `plans-facts.md`. This note covers the overview level only; station-level detail for the rail and tram projects is handled separately.

#### Summary

- **Only two rail extensions open before 2029. Both are short, and both serve the edges of the network.** Tram 7 to Stadtpark (Berliner Platz) opens on **13 Dec 2026**, with the timetable change. It relieves the overloaded U2/U3 section Hbf–Rathenauplatz. The tram 4 gap in Minervastraße follows at the **end of 2027**, and **U3 Gebersdorf** in **H1 2028**, slipped from end 2027. Everything else is 2030 or later: Lichtenreuth in 2030, and the StUB to Reutles in 2031/32.
- **The StUB is the one project that changes access for a whole area, the Knoblauchsland in the north.** The Nahverkehrsplan names the Knoblauchsland as its main access deficit. The route inside Nürnberg was fixed on 26 Mar 2026. The plan-approval application is due in H2 2026, but I found no confirmation that it has been filed. Construction starts 2028/29. Nürnberg pays only **€27 m** of the €131 m local share. Erlangen pays €82 m, and its finances, together with the new CSU mayor there, are the bigger political risk.
- **Money is the binding constraint, not planning.** The Regierung von Mittelfranken granted no new borrowing for 2026, and a budget freeze has applied since 29 Jul 2026. The 2027 draft budget needs at least €122 m a year in improvements, rising to €169 m by 2030. VAG has record ridership (163.9 m) but lost €97.7 m in 2025, and has been asked for about €10 m in savings. The 2027–30 investment plan holds €190.8 m for public transport and only €33 m for cycle paths. Krieglstein has said outright that some tram projects "auf der Strecke bleiben" will fall away.
- **Politics are stable: the city is road-friendly but still backs the tram.** OB König (CSU) was re-elected on 22 Mar 2026, and the CSU–SPD cooperation continues to 2032. On 28 Jun 2026 voters backed the **€1 bn Frankenschnellweg** road project, with 53 % against stopping it. Main works start in Feb 2027. The CSU maglev idea for Klinikum Süd is dropped in favour of a tram. The Greens lost seats and then split.
- **Most of the mobility targets will be missed.** The 2021 Mobilitätsbeschluss targets 68 % of trips by public transport, bike and walking, and 135 km of priority cycle routes by 2030. Only about 1.3 km of those routes was built by end 2025. The administration says targets "über das Jahr 2030 hinaus verschoben werden müssen". The legally binding Nahverkehrsplan is still the **2017** version. A 2025 update exists as a document, but I found no council adoption.
- **Construction disruption peaks from 2027 to 2030.** It comes from the Frankenschnellweg West section (2027–29), the closed Hafen motorway bridge, the Hafen bridges (to 2029), tram track renewals (Allersberger Str. to mid-2027, Plärrer next) and the Münchner Straße bridges.

#### Area by area

The tutorial's district names map to the official Nürnberg Stadtteile and Statistische Bezirke. The groups below are the planning areas the sources use.

| Area | Built / under construction | Decided / approved | Under discussion only | What it means |
|---|---|---|---|---|
| **North / Knoblauchsland** (Buch, Boxdorf, Reutles, Großgründlach, Neunhof, Kraftshof; Thon/Wegfeld) | RVR 4 cycle street Thon (Dec 2026); RSV Erlangen first section (2026) | StUB route Am Wegfeld–Reutles (26 Mar 2026); application H2 2026; first tram 2031/32 | StUB Ostast (outside the city) | The biggest improvement, but the latest. The NVP's weakest area gets a direct tram to the centre and to Erlangen, plus P+R Reutles. Until 2031 it keeps the change at Am Wegfeld |
| **Southwest** (Schweinau, Großreuth, Kleinreuth, Gebersdorf) | U3 Gebersdorf (fit-out, then a year of trial running) | Opening H1 2028; Gebersdorf bus station 2027 | — | Gebersdorf goes from bus to automated U-Bahn in 2028. The Rothenburger Str. rebuild follows only after the opening |
| **West / Gostenhof / St. Leonhard / Sündersbühl** | Frankenschnellweg West prep work (Oct 2026) | FSW West main works from Feb 2027 (to about end 2029); Plärrer plan approved 10 Sep 2026 | FSW Mitte tunnel (no date) | Several years of construction on the main west axis and at the tram hub Plärrer. Expect diversions of trams 4/6/10 and buses 70–73 |
| **Südstadt** (Gibitzenhof, Steinbühl, Galgenhof, Hummelstein) | Allersberger Str. track renewal (to early summer 2027) | Südstadtachse with new Melanchthonplatz stop | Reinforcement line Hbf–Wodanstr.–Doku-Zentrum | Mostly renewal and capacity work on the busiest tram corridor, not new coverage |
| **South** (Gartenstadt, Falkenheim, Finkenbrunn, Werderau; Katzwang) | Tram 4 Minervastraße (from Jun 2026) | Opening end 2027 | Kornburg light rail (no positive cost-benefit ratio) | Gartenstadt/Falkenheim gain a tram link and a direct 4/5 connection from 2028. The outer south (Katzwang, Kornburg) stays on S-Bahn and bus |
| **Southeast** (Hasenbuck, Lichtenreuth/Brunecker Str., Langwasser, Klinikum Süd) | — | Tram 7 to Lichtenreuth / U Bauernfeindstraße in plan approval; opening 2030 | Extension to Messe / Klinikum Süd (in the coalition agreement); maglev only as a private Messe demo | The new district and the new TU Nürnberg are planned with a tram, but its date slipped from 2028 to 2030, and funding is applied for only after approval |
| **East / Northeast** (Wöhrd, St. Jobst, Schoppershof, Erlenstegen, Mögeldorf, Laufamholz) | Tram 7 Stadtpark (from 13 Dec 2026); RVR 10 Schloßstraße (2026) | — | Erlenstegen loop; Pirckheimerstraße tram / GSO campus line | Real improvement in Dec 2026: a direct tram Hbf–Rathenauplatz–Berliner Platz–Stadtpark, which relieves the U2/U3. Nordostpark stays bus-only to Herrnhütte |
| **Hafen / Eibach / Röthenbach** | Hafen bridges (to 2029); temporary bridges at Kreuz Hafen (Sep 2026) | Rebuild of the Hafen motorway bridge | — | The NVP flags the Hafen as poorly served (buses 60/66). The planned work is all road bridges, with no transit upgrade |
| **Altstadt / centre** | — | Plärrer cycle-ring section | Tram Altstadtquerung (shelved since 2015); Hbf second tram platform | Capacity at Hbf and Plärrer is the bottleneck for the whole tram network. No date for the Hbf fix |
| **Fürth / Erlangen corridor (S1)** | — | — | S-Bahn Fürth route decision after DB results in 2027 | Stays at 3 trains an hour (since 2022) for the foreseeable future |

#### Major disruption zones: what is behind them

| Zone | Work and owner | End date | Note |
|---|---|---|---|
| Frankenschnellweg West (Nürnberg/Fürth junction–Jansenbrücke) | City (SÖR), road upgrade, new Sigmundstraße bridge | Start Feb 2027; earlier planning said end Dec 2029 | Referendum-backed; about €1 bn total including the tunnel |
| Kreuz Nürnberg-Hafen | FSW bridge closed since Mar 2026; temporary bridges since Sep 2026; demolition and rebuild | "mehrere Jahre" | Traffic shifted to Hafenstraße and Wiener Straße |
| Plärrer | Tram tracks and stops, U-Bahn roof repair | Not published; plan approved 10 Sep 2026 | Most important tram hub west of the Altstadt; current Spittlertorgraben closure to 13 Nov 2026 |
| Allersberger Straße | VAG track renewal | Early summer 2027 (VGN: 31 May 2027) | Trams 6/7/8 diverted; bus E8 |
| Minervastraße / Dianastraße | VAG tram new build | End 2027 | — |
| Gebersdorf / Rothenburger Straße | U3 fit-out; bus station 2027; road rebuild after the U3 opens | 2028+ | — |
| Obstmarkt, Lorenzer Passage | — | 2029 / end 2027 | Altstadt bus routing |

#### Proposals still under discussion, ranked by impact

Impact means how many residents an item affects and how directly it closes an access gap. Likelihood is listed separately. The ranking is my judgment from the research, not a calculation.

| # | Proposal | Area addressed | Stage | Likelihood | Horizon |
|---|---|---|---|---|---|
| 1 | **StUB section 1 Am Wegfeld–Reutles, then to Erlangen** | Knoblauchsland; commuters to Erlangen | Route decided; plan-approval filing due H2 2026 | Medium–high in Nürnberg (cheap for the city); medium for the Erlangen sections (budget, new CSU OB) | 2031/32 |
| 2 | **Tram Lichtenreuth–Bauernfeindstraße, then Messe–Klinikum Süd** | Southeast growth area, TU Nürnberg | In plan approval; funding after approval | Medium–high for stage 1; low–medium for Klinikum Süd | 2030; 2030s |
| 3 | **Hbf tram capacity (second platform track)** | Whole tram network | Concept only | Medium; no timetable | 2030s |
| 4 | **Pirckheimerstraße reactivation / GSO campus line** | North (Maxfeld, St. Johannis) | Not started (staff) | Low (risk of repaying U3 grants) | 2030s |
| 5 | **Tram Altstadtquerung** | Sebalder Altstadt | Shelved since 2015 | Low | — |
| 6 | **Reinforcement line Hbf–Wodanstr.–Doku-Zentrum and denser tram service** | Südstadt | Package 2 | Low–medium (VAG must save €10 m) | 2028+ |
| 7 | **Free school ticket** | Citywide | Coalition: only with funding | Low in the current budget | — |
| 8 | **Priority cycle network (135 km)** | All districts | About 1.3 km built; 2026–2032 building programme pending | Low for 2030; medium for parts by 2032 | 2030+ |
| 9 | **S-Bahn Fürth Verschwenk** | Northwest corridor | DB results 2027 | Low–medium | 2035+ |
| 10 | **U2 to Stein/Eibach** | Southwest edge | No positive cost-benefit ratio | Very low | — |

The Magnetbahn to Klinikum Süd is off the table. I found no current debate on a Citymaut or a cable car.

#### Notes on the dataset

- **Feed date matters.** Any VGN GTFS feed valid to 12 Dec 2026 lacks the tram 7 extension to Stadtpark, which starts on 13 Dec 2026. Feeds from 13 Dec 2026 include it.
- **Scenario years for the tutorial:** 2026/27 (tram 7 Stadtpark); end 2027 (tram 4 Minervastraße); H1 2028 (U3 Gebersdorf, plus about a year of trial running beforehand); 2030 (Lichtenreuth); 2031/32 (StUB to Reutles). Treat later StUB sections and Klinikum Süd as uncertain.
- **Temporary disruptions in an Oct–Nov 2026 feed:** Plärrer/Spittlertorgraben (trams 4/6/10 replaced to 13 Nov), Allersberger Straße (trams 6/7/8 diverted), and S1/S2/S3/S4 evening closures. Exclude them or flag them when measuring "normal" service.
- **Population growth areas** in the sources: Lichtenreuth (new district plus university) and the north along the StUB. The city has about 544,000 residents (StUB brochure).

#### Conflicts between sources

- **U3 Gebersdorf opening:** end 2027 (city, 2 Feb 2026) against H1 2028 (city, 6 Oct 2026). Follow the newer date.
- **Tram 7 Stadtpark:** Sep 2026 (nordbayern, 2025), then late Nov/early Dec (VAG, Mar 2026), then 13 Dec 2026 (VAG, 22 Oct 2026). Follow VAG, Oct 2026.
- **Lichtenreuth tram:** end 2028 (city PR Dec 2024; NVP 2025) against 2030 (project page). Follow the project page.
- **StUB opening and cost:** the city's StUB page still says "Ende der 2020er Jahre" and €258 m. The Zweckverband says "ab 2031" and 2031/32 to Reutles, at €635 m + €95 m planning (2022 prices). The city page is outdated.
- **Frankenschnellweg start:** the same city page says both "beginnt im Februar 2027 wie geplant" and "könnte im Februar 2027 erfolgen". Another city text says spring 2027.
- **Green seats:** 10 won in the election, 7 in the council group (split of 4 around Mletzko, unverified). The numbers do not reconcile exactly.
- **Nahverkehrsplan:** the city web page and the NVP 2025 text both treat the 2017 plan as the one in force. The 2025 update has no adoption I could find.

#### Key sources

- Council composition: https://www.nuernberg.de/internet/stadtportal/stadtrat.html
- CSU–SPD agreement (draft 22 Apr 2026): https://nuernberg.t-online.de/region/nuernberg/id_101224652/nuernberg-csu-spd-kooperationsvertrag-steht-diese-projekte-kommen.html
- Krieglstein interview (13 Jun 2026): https://nuernberg.t-online.de/region/nuernberg/id_101289322/nuernberg-buergermeister-krieglstein-csu-ueber-baustellen-und-schulden.html
- Budget 2027 speech: https://www.nuernberg.de/imperia/md/stadtfinanzen/dokumente/rede_einbringung_haushalt_2027.pdf
- Budget freeze: https://www.nuernberg.de/internet/stadtportal/haushaltssperre.html
- Nahverkehrsplan Fortschreibung 2025 (draft): https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/nahverkehrsplan_2025_stadt_nurnberg.pdf
- Tram progress, 30 Jul 2026: https://www.nuernberg.de/presse/mitteilungen/pm_27926.html
- VAG annual report 2025: https://www.vag.de/fileadmin/user_upload/06_dokumente/Daten_und_Fakten/VAG-Geschaeftsbericht-2025.pdf
- VAG construction programme 2026: https://www.vag.de/presse/aktuelle/bauprogramm-2026-vag-setzt-notwendiges-instandhaltungs-und-modernisierungsprogramm-um-schwerpunkt-liegt-dieses-jahr-auf-der-strassenbahn
- Tram 7 Stadtpark from 13 Dec 2026: https://www.vag.de/aktuelles/aktuelle-meldungen/detail/spezialfahrzeug-im-strassenbahnnetz-unterwegs
- U3 Gebersdorf: https://www.nuernberg.de/internet/stadtportal/aktuell_100397.html
- Minervastraße: https://www.nuernberg.de/internet/verkehrsplanung/tram_minervastrasse.html
- Lichtenreuth: https://www.nuernberg.de/internet/verkehrsplanung/strassenbahnverlaengerungbruneckerstrasse.html
- StUB: https://www.stadtumlandbahn.de/fileadmin/Dokumente/Ergebnisse/StUB-Broschuere_Stand_03_2026.pdf · https://www.stadtumlandbahn.de/en/ · https://www.nuernberg.de/internet/stadtportal/stadt_umland_bahn.html
- Frankenschnellweg: https://www.nuernberg.de/internet/stadtportal/frankenschnellweg.html · https://www.nuernberg.de/presse/pdf/PM_20260628_0703_1_6a41691a9c84b.pdf
- Hafen bridge closure: https://www.nuernberg.de/presse/mitteilungen/pm_27963.html
- Mobilitätsbeschluss: https://www.nuernberg.de/internet/verkehrsplanung/mobilitaetsbeschluss.html
- Cycling reporting 2025 and round-table minutes: https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/rtr/36c_rtr_reporting2025_vpl.pdf · https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/rtr/36b_rtr_ergebnisvermerk_260317.pdf · https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/rtr/37b_rtr_ergebnisvermerk_260623.pdf
- Cycling budget dispute: https://www.nuernberg.de/presse/mitteilungen/pm_28298.html
- Deutschlandticket 2027: https://www.stmb.bayern.de/med/pressemitteilungen/pressearchiv/2026/115/index.php
- DB timetable 13 Dec 2026: https://nuernberg.t-online.de/region/nuernberg/id_101478372/ice-ab-nuernberg-was-sich-ab-dezember-fuer-reisende-aendert-neue-zuege.html
- Current closures: https://www.vgn.de/fahrplanaenderungen/ · https://www.vag.de/presse/aktuelle

## 7. Plans: facts with sources

_Source: `research/plans-facts.md`_

### Nürnberg mobility projects and proposals: facts (as of 28 Oct 2026)

This file lists what the sources say, without assessment. The research was done in German. Items marked **(unverified)** were seen only in search results, not on the source page. Where sources disagree, both versions are given.

Coverage note: nordbayern.de (Nürnberger Nachrichten / Nürnberger Zeitung) and BR24 did not surface usable 2026 articles through the research tool. Most facts below come from Stadt Nürnberg pages and press releases, VAG, the Zweckverband StUB, the Bavarian transport ministry (StMB), council PDFs and t-online Nürnberg. The VAG and StUB PDFs were downloaded and read in full.

---

#### 1. Political and budget frame

| Fact | Source |
|---|---|
| Marcus König (CSU) won the mayoral runoff on 22 Mar 2026 against Nasser Ahmed (SPD), 55.5 % to 44.5 %, turnout 41.1 %. His new term began on 1 May 2026 **(unverified figures)** | https://www.nuernberg.de/presse/mitteilungen/pm_27207.html · https://www.nuernberg.de/imperia/md/zentral/dokumente/amtsblatt/2026_08_amtsblatt.pdf |
| Council election, 8 Mar 2026: CSU 33.7 % (24 seats), SPD 18.3 % (13), Grüne 14.8 % (10), AfD 11.3 % (8), Linke 6.6 % (5), FW 3.4 % (2), politbande 3.2 %, Volt 1.9 %, FDP 1.6 %, ÖDP 1.3 %. Turnout 51.1 % **(unverified)** | https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/wahlberichte/nuernberg_ergebnisse/w232_kow2026_ergebnis_stadtratswahl_v1.3.pdf |
| Council groups 2026–2032 (70 members plus the mayor): CSU 24 + FDP 1; SPD 13; Grüne-Volt 8 (Grüne 7, Volt 1); AfD 8; Linke 5; "Ökologische Fraktion" 3 + ÖDP 1; FW 2; politbande 2; 3 single members | https://www.nuernberg.de/internet/stadtportal/stadtrat.html |
| The Greens won 10 seats but sit as 7. Four Green councillors around former group leader Achim Mletzko split off before the term began (Schwäbische, Apr 2026) **(unverified)**. The city page does not explain the "Ökologische Fraktion" | https://www.schwaebische.de/regional/bayern/vier-von-zehn-nuernberger-gruenen-stadtraeten-spalten-sich-ab-4490687 |
| CSU and SPD continue their cooperation (the "Reformkooperation") with a 28-page agreement for 2026–2032. The draft was presented on 22 Apr 2026. The IHK reviewed the signed agreement on 13 May 2026 | https://nuernberg.t-online.de/region/nuernberg/id_101224652/nuernberg-csu-spd-kooperationsvertrag-steht-diese-projekte-kommen.html · https://www.ihk-nuernberg.de/meldungen/details/wichtige-forderungen-des-ihk-gremiums-im-kooperationsvertrag |
| Andreas Krieglstein (CSU) is 2. Bürgermeister and heads the new Mobilitätsreferat, which bundles SÖR (public works), the Verkehrsplanungsamt and the U-Bahn-Bauamt. Nasser Ahmed (SPD) is 3. Bürgermeister **(Ahmed's post unverified)** | same; https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/rtr/37b_rtr_ergebnisvermerk_260623.pdf |
| Agreement: both parties accept the Frankenschnellweg referendum result. The CSU's maglev between Bauernfeindstraße and Klinikum Süd is dropped in favour of extending tram 7. Max Bögl may build a small maglev on the Messe grounds if it pays. The coalition checks how to fund a free school ticket for all pupils. Bed tax for tourists; a new staff unit for budget consolidation | t-online (23 Apr 2026), above |
| Krieglstein, 13 Jun 2026: "Manches wird auf der Strecke bleiben müssen, weil es dafür weder Geld noch Personal gibt." He named tram Berliner Platz, Minervastraße, tram 7 to Lichtenreuth and the StUB as candidates. Target: a clear improvement in roadworks management "ab dem Frühling 2027". The city has about 12,000 approved building sites | https://nuernberg.t-online.de/region/nuernberg/id_101289322/nuernberg-buergermeister-krieglstein-csu-ueber-baustellen-und-schulden.html |
| Budget freeze (Haushaltssperre) from 29 Jul 2026, until further notice. Projects not yet started are paused and reassessed in autumn. Contracts over €50k need Finanzreferat approval | https://www.nuernberg.de/internet/stadtportal/haushaltssperre.html |
| Draft budget 2027 introduced by treasurer Thorsten Brehm, 30 Sep 2026 **(date unverified)**. 2027 gap between operating cash surplus (€24 m) and scheduled repayments (€115.8 m): €91.8 m. With €30–40 m risk, the improvement needed is at least €122 m in 2027, rising to more than €169 m a year by 2030. The spring target of €80 m a year "reicht … nicht mehr aus" | https://www.nuernberg.de/imperia/md/stadtfinanzen/dokumente/rede_einbringung_haushalt_2027.pdf |
| Same speech: the Regierung von Mittelfranken granted no new borrowing with the 2026 budget (€170 m requested). Old authorisations last until 2028. Net new borrowing is set to zero from 2029. Cash reserves fall from about €165 m (end 2026) to €62 m (end 2027); without measures, minus €672 m by 2030. The consolidation concept is decided together with the budget in November 2026 | same |
| Same speech: medium-term investment plan (MIP) 2027–2030 totals €2,206.6 m, of which the city funds €1,047.4 m. ÖPNV €190.8 m, roads €195.1 m, bridges €188.9 m, cycle paths €33.0 m (gross, with grants) | same |
| Same speech: "Bei der VAG sind die Fahrgastzahlen gestiegen – leider auch die Verluste." The city has asked VAG for savings proposals of about €10 m; the council decides. The energy profits of the Städtische Werke no longer cover the transport losses | same |

#### 2. Public transport

##### 2a. Plans in force and operator finances

| Item | Facts | Sources |
|---|---|---|
| Nahverkehrsplan (NVP) | The plan in force is the "Fortschreibung 2017", adopted by the council on 14 Dec 2017. A "Fortschreibung 2025" document dated April 2025 exists. It says the 2017 plan "nun erneut fortgeschrieben wird". I found no council adoption of the 2025 update | https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/nahverkehrsplan_2025_stadt_nurnberg.pdf · https://www.nuernberg.de/internet/verkehrsplanung/nahverkehrskonzepte_oepnv.html |
| NVP 2025 analysis | The city is fully covered by the Bavarian stop-distance guideline. Outer northern and southern areas often miss the travel-time target to key destinations with one change. Many trips need two changes; the network is "sehr umsteigelastig". Named weak spots: Knoblauchsland, Hafen (buses 60/66 only), Nordostpark (buses 30/31 to U2 Herrnhütte) | same |
| Modal split (NVP 2025, from the 2023 household survey) | 2023: car 32 %, public transport 23 %, bike 15 %, walking 30 % (2019: car 38 %, walking 24 %). 29 % of households have no car | same |
| Mobilitätsbeschluss (27 Jan 2021) | Goal: 68 % of trips by public transport, bike and walking in 2030 (61 % at adoption). 10 km of Fahrradstraßen a year; 135 km Radvorrangrouten network by 2030; 1,000 bike parking spaces a year | https://www.nuernberg.de/internet/verkehrsplanung/mobilitaetsbeschluss.html |
| ÖPNV-Maßnahmenpaket 2030 (Jul 2021) and ÖPNV-Maßnahmenprogramm 2035 (council 11 Dec 2024) | The 2035 programme ranks 11 tram projects plus the Stadtpark loop by benefit, funding eligibility, network value, staff, affordability and urgency. The 2030 package stays valid. Shelved: tram Altstadtquerung (since 2015); U2 to Stein/Eibach (no positive cost-benefit ratio); tram reactivation in Pirckheimerstraße (not started, staff shortage) | NVP 2025, above; https://www.nuernberg.de/presse/mitteilungen/pm_27926.html |
| Tram progress report to the new transport committee, 30 Jul 2026 | Stadtpark link "im Dezember 2026"; Minervastraße and Südstadtachse (Landgrabenstraße, new Melanchthonplatz stop) in construction preparation; Plärrer and Lichtenreuth in plan approval; StUB first section application being finalised. With Bund/Land funding the city's share is expected to fall to about €150 m | https://www.nuernberg.de/presse/mitteilungen/pm_27926.html |
| Masterplan "schneller und pünktlicher ÖPNV" | Adopted 22 Sep 2022; 26 measures (signal priority, bus and tram lanes, stops, bus stations) | https://www.nuernberg.de/internet/verkehrsplanung/nahverkehrskonzepte_oepnv.html |
| VAG 2025 results | 163.9 m passengers (+1.6 %), the third record year running; 294,000 subscriptions. Annual loss €97.7 m (2024: €109.7 m), covered by the parent StWN. 26 new trams and 100 e-buses in service. 14 more GTA8 trams ordered in 2025 to replace the 1990s GT6N from 2026. 21 MAN e-articulated buses delayed to 2026; "Für weitere Beschaffungsmaßnahmen im Busbereich konnten bislang keine Fördermittel akquiriert werden." The goal is "mindestens die Erhaltung des derzeitigen Verkehrsangebots" | https://www.vag.de/fileadmin/user_upload/06_dokumente/Daten_und_Fakten/VAG-Geschaeftsbericht-2025.pdf |
| VAG savings 2025 (precedent) | CSU, SPD and Grüne cut the planned bus service reductions from €1.4 m to about €0.6 m within a €5 m package, so that no whole bus lines are cut (Dec 2024) | https://gruene-stadtratsfraktion.nuernberg.de/pressemitteilung-csu-spd-und-buendnis90-die-gruenen-legen-kompromissangebot-bei-vag-einsparungen-und-sozialticket-vor/ |
| Tariffs | Deutschlandticket €63 in 2026, €66.80 from 1 Jan 2027: the first price set by the new cost index (VMK, Mar 2026). Jobticket €63.46; Semesterticket €40.08 (StMB, 30 Sep 2026). VGN tariff rose 2.96 % on 1 Jan 2026; the next network-wide rise is due 1 Jan 2027 (amount not found). VAG: Bund/Land D-Ticket funding capped at €3 bn, so expect "überproportionale Preisanpassungen" | https://www.stmb.bayern.de/med/pressemitteilungen/pressearchiv/2026/115/index.php · VAG report, above |

##### 2b. In operation or under construction

| Project | Status | Dates | Facts | Sources |
|---|---|---|---|---|
| Tram 7 to Stadtpark (Rathenauplatz–Bayreuther Str.–Berliner Platz–Stadtpark, reactivated) | Under construction; opening imminent | VAG, 22 Oct 2026: "Inbetriebnahme der Linie 7 zum Stadtpark ab 13. Dezember 2026". Earlier: Sep 2026 (nordbayern, Jun 2025), then "Ende November/Anfang Dezember" (VAG, 30 Mar 2026) | Relieves the U2/U3 section Hbf–Wöhrder Wiese–Rathenauplatz. Tram 7 no longer turns at Hbf. Pirckheimerstraße tracks are only a diversion route | https://www.vag.de/aktuelles/aktuelle-meldungen/detail/spezialfahrzeug-im-strassenbahnnetz-unterwegs · https://www.vag.de/presse/aktuelle/bauprogramm-2026-vag-setzt-notwendiges-instandhaltungs-und-modernisierungsprogramm-um-schwerpunkt-liegt-dieses-jahr-auf-der-strassenbahn |
| U3 Gebersdorf (Großreuth–Kleinreuth b. Schweinau–Gebersdorf, about 2 km, 2 stations) | Fit-out; then about a year of trial operation | Opening "im ersten Halbjahr 2028" (city, status briefing 6 Oct 2026). City press release of 2 Feb 2026 said end 2027 | About €224 m; Bund/Land grants over €100 m (60 % Bund + 20 % Land of the main costs). U2 and U3 run fully automated. Gebersdorf bus station and surface redesign in 2027. Rothenburger Straße rebuild only after opening | https://www.nuernberg.de/internet/stadtportal/aktuell_100397.html |
| Tram 4 Minervastraße gap (Gibitzenhof–Dianastr.–Minervastr.–Finkenbrunn, 1.7 km) | Under construction | Plan approval 3 Jun 2025; track work from early Jun 2026; opening end 2027 | Second depot access; links lines 4 and 5; serves Gartenstadt/Falkenheim. Must open before DB rebuilds the Katzwanger Str. underpass ("Mauslochs") | https://www.nuernberg.de/internet/verkehrsplanung/tram_minervastrasse.html · VAG Bauprogramm 2026 |
| Allersberger Straße track renewal (Wölckern- to Wodanstraße) | Under construction | 24 Mar 2026 to early summer 2027 | Trams 6, 7, 8 diverted; replacement bus E8 | VAG Bauprogramm 2026 |
| Südstadtachse (Landgrabenstraße, new Melanchthonplatz stop replacing Heynestraße) | Construction preparation | Several sections; no dates | Landgrabenstraße stop is overloaded | pm_27926; NVP 2025 |
| S2 step-free stations Nürnberg-Sandreuth–Roth | DB target 2026 | — | Freistaat funds about €25 m **(unverified)** | https://www.deutschebahn.com/de/presse/presse-regional/pr-muenchen-de/aktuell/presseinformationen/Barrierefrei-in-die-S-Bahn-Nuernberg-Freistaat-Bayern-und-DB-bauen-weitere-Stationen-zwischen-Nuernberg-Sandreuth-und-Roth-um-13314910 |

##### 2c. Timetable change 13 Dec 2026

| Change | Source |
|---|---|
| Tram 7 runs to Stadtpark from 13 Dec 2026 | VAG, 22 Oct 2026, above |
| I found no other VAG network changes for Dec 2026: no published bus reform and no announced cuts as of 28 Oct 2026. VGN line timetables run to 12 Dec 2026 | https://www.vag.de/presse/aktuelle · https://www.vgn.de/fahrplanaenderungen/ |
| **Update 10 Nov 2026:** no other changes for Dec 2026, but the city has published proposed service cuts from March 2027: "Sparmaßnahmenpaket im VAG-Verkehrsangebot", packages P1–P5 (€1.3 m to €10.0 m a year), decision due 30 Nov 2026. P3 (€5.3 m) withdraws bus lines 81, 82 and 84, ends trams 10 and 11 at 18:30, thins U1–U3 before 6:00 and leaves only the Nightliner network before 8:00 on weekends from 2 Aug 2027. Digitized into `PT_SERVICE_CUTS`; see [vag-cuts-2027-notes.md](vag-cuts-2027-notes.md) | https://online-service2.nuernberg.de/buergerinfo/getfile.asp?id=947894&type=do |
| DB long-distance: two more ICE-Sprinter a day to Stuttgart (about 2 h) and Berlin (about 2 h 45, non-stop). Direct ICE to Linz/Wien returns after the Nürnberg–Regensburg–Passau rebuild. Some early and late IC Stuttgart–Nürnberg trains via Ansbach cut. From 13 Aug 2027, 8 daily Frankfurt–Nürnberg ICE connections cut | https://nuernberg.t-online.de/region/nuernberg/id_101478372/ice-ab-nuernberg-was-sich-ab-dezember-fuer-reisende-aendert-neue-zuege.html |

##### 2d. In planning, on hold or contested

| Project | Status | Facts | Sources |
|---|---|---|---|
| Stadt-Umland-Bahn (StUB): tram 4 extension from Am Wegfeld to Erlangen and Herzogenaurach, about 26 km, 31 stops, 10-minute service | Route in Nürnberg decided; plan-approval application due H2 2026 (filing not confirmed by 28 Oct 2026) | Verkehrsausschuss 26 Mar 2026 fixed the route Am Wegfeld–city limit (Reutles), together with the Boxdorf–city limit cycle highway. Construction of section 1 from 2028/29; first tram to Reutles 2031/32 (ZV StUB site); phased opening "ab 2031" (brochure 03/2026). Cost €635 m investment + €95 m planning (2022 prices); 90 % funded; local share €131 m: Erlangen €82 m, **Nürnberg €27 m**, Herzogenaurach €22 m. Ostast to Eckental only "angedacht". P+R Reutles up to 600 spaces | https://www.nuernberg.de/internet/stadtportal/stadt_umland_bahn.html · https://www.stadtumlandbahn.de/en/ · https://www.stadtumlandbahn.de/fileadmin/Dokumente/Ergebnisse/StUB-Broschuere_Stand_03_2026.pdf |
| StUB politics | Referendums: Landkreis Erlangen-Höchstadt rejected the StUB on 22 Apr 2015 (city page). Erlangen voted for it on 9 Jun 2024, 52.4 % yes, turnout 67 % **(unverified)**. Erlangen's new OB is Jörg Volleth (CSU), who beat Janik (SPD) in the 22 Mar 2026 runoff **(unverified)**; Erlangen's trade-tax slump is reported as a threat to the StUB **(unverified)**. AfD Landtag motion (28 Apr 2026) asks for reports on planning time and costs **(unverified)**. I found no pending court case | city page, above; https://www.infranken.de/lk/erlangenhoechstadt/erlanger-buerger-haben-fuer-stadt-umland-bahn-gestimmt-so-geht-es-jetzt-weiter-art-5888886 · https://www.infranken.de/lk/erlangenhoechstadt/ob-wahl-in-erlangen-endet-mit-ueberraschung-der-weitere-fahrplan-art-6323971 |
| Tram Lichtenreuth (Tristanstraße–Lichtenreuth–U Bauernfeindstraße, about 2.5 km, 5 stops; later Messe–Klinikum Süd) | In plan approval | Documents resubmitted Sep 2025; objections closed 16 Jan 2026; no decision found. Opening "für das Jahr 2030" (project page); NVP 2025 and Dec 2024 PR said 2028. Funding application after approval planning. In the coalition agreement, including the extension to Klinikum Süd | https://www.nuernberg.de/internet/verkehrsplanung/strassenbahnverlaengerungbruneckerstrasse.html |
| Plärrer redesign (tram tracks and stops, with the leaking U-Bahn station roof) | Plan approved | Plan approval by the Regierung von Mittelfranken, 10 Sep 2026; on display 28 Oct–10 Nov 2026. No construction date **(unverified)** | https://www.nuernberg.de/imperia/md/soer_nbg/dokumente/sonstiges/bekanntmachungstext_auslage_pfb_plaerrer.pdf |
| Ostendstraße, Johannisstraße, Frankenstraße, Hbf second tram platform | Planning / plan approval | Hbf tram stop overloaded; no timetable for the extra track | NVP 2025 |
| S-Bahn Fürth "Verschwenk" vs existing route (S1 to Erlangen) | Open-ended planning since 2023; DB results expected 2027, then a route decision **(unverified)** | Interim: 3 instead of 2 S-Bahn trains an hour Nürnberg–Erlangen since 2022 | https://www.ihk-nuernberg.de/ihk-themen/verkehr-logistik-mobilitaet/verkehrspolitik/s-bahn-verschwenk-fuerth |
| S-Bahn Nürnberg tender | Due to start H1 2026; regional lines H2 2027 (Staatsregierung, 25 Feb 2026) **(unverified)** | 27 state-procured vehicles mentioned | https://www.bayern.landtag.de/www/ElanTextAblage_WP19/Drucksachen/Schriftliche%20Anfragen/19_0010060.pdf |
| Rail node / Deutschlandtakt | Nürnberg–Bamberg four-track upgrade completed 19 Sep 2025 (a Deutschlandtakt project) **(unverified)**. Nürnberg–Regensburg general rebuild with full closure 6 Feb–10 Jul 2026 **(dates unverified)**; the line is regular again from 13 Dec 2026 | I found no Nürnberg Hbf node study with dates | https://www.deutschebahn.com/de/presse/pressestart_zentrales_uebersicht/Nuernberg-Bamberg-vier-Gleise-fuer-mehr-Kapazitaet-im-Nah-und-Fernverkehr--13552516 · t-online, above |

#### 3. Cycling

##### 3a. Citywide

| Item | Facts | Sources |
|---|---|---|
| Radentscheid / Mobilitätsbeschluss | The Mobilitätsbeschluss (27 Jan 2021) followed the Radentscheid petition (about 26,000 signatures) and adopts its demands "in Teilen" | https://www.nuernberg.de/internet/verkehrsplanung/mobilitaetsbeschluss.html |
| Reporting 2025 (Runder Tisch Radverkehr, 17 Mar 2026) | Radvorrangrouten (RVR): about 1.3 km built by end 2025; 1.6 km under construction; 3.2 km decided; about 11 km planned (target: 135 km by 2030). Cycle highways (RSV): 1.3 km under construction (first section towards Erlangen), 2.8 km decided, about 14 km planned. Target of 1,000 bike stands a year "wird nicht erreicht"; the last stand rollouts drag until 2029. No new posts requested for 2025–26 because of budget consolidation; 5 SÖR engineer posts unfilled | https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/rtr/36c_rtr_reporting2025_vpl.pdf |
| Minutes, 17 Mar 2026 | The Mobilitätsbeschluss continues under the new council, "wenngleich einige Ziele über das Jahr 2030 hinaus verschoben werden müssen." Only the Plärrer section of the "Altstadtring für Radler" is decided (VCD: the city had promised the ring by 2026). Planning towards Lauf "ruht aktuell" | https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/rtr/36b_rtr_ergebnisvermerk_260317.pdf |
| Minutes, 23 Jun 2026 | Krieglstein now runs mobility and wants to bring planning and construction together. Maximilianstraße (cycle lanes, 36 trees, bus priority by signals) goes to committee in 2026, but "Es wird eine Herausforderung werden, das Projekt in den MIP zu bekommen." Münchner Straße bridges must be fully rebuilt; Zollhausstraße gap delayed to 2027 | https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/rtr/37b_rtr_ergebnisvermerk_260623.pdf |
| Budget dispute, Oct 2026 | The city calls the ADFC warning of a complete halt to cycle-path building until 2030 "nicht zutreffend", but says MIP decisions and measures from 2027 "noch nicht getroffen" are. Cycle-path building programme 2026–2032 to be presented to the transport committee | https://www.nuernberg.de/presse/mitteilungen/pm_28298.html |
| Cycle money | MIP 2027–2030: €33.0 m for cycle paths over four years (gross). ADFC (2024): about €10 m a year planned up to 2027 **(unverified)** | budget speech 2027, above |

##### 3b. Street projects

| Area | Project | Status | Facts | Sources |
|---|---|---|---|---|
| Thon / Schniegling (north) | RVR 4 cycle street Am Thoner Espan / Michaelstraße / Äußere Bucher Str. | Under construction 5 Oct–19 Dec 2026 | Parking drops to 87 spaces; markings spring 2027; co-funded by "Radoffensive Klimaland Bayern" | https://www.nuernberg.de/presse/mitteilungen/pm_28144.html |
| Mögeldorf / Laufamholz (east) | RVR 10 Schloßstraße from Burgerstraße to Laufamholz | Completion 2026 | — | reporting 2025, above |
| Wöhrd / Gleißhammer (east) | RVR 2 | Decided except the Hainstraße/Regensburger Str. junction | — | same |
| North (Boxdorf–Erlangen) | RSV Erlangen | First section under construction, due 2026; design for plan approval in the committee 26 Mar 2026 | Built alongside the StUB | same; city StUB page |
| Southwest | RSV Zirndorf/Oberasbach/Stein (Bibertbahntrasse); RSV Schwabach (Rehlingerstraße, in pieces) | Planning / partly built | — | minutes 17 Mar 2026 |
| Altstadt | Altstadtring für Radler | Plärrer section decided; Königstorgraben partly; Hbf area "schwierig" | — | same |

#### 4. Roadworks and major construction

| Zone / item | Facts | Sources |
|---|---|---|
| Frankenschnellweg (A73/B4R) grade-separated upgrade | Referendum 28 Jun 2026 on stopping the plans ("Lieber zurück auf Los …"): about 81,000 No (53 %) against 71,000 Yes (47 %), turnout 40.3 %. The plans go ahead; the result binds for one year | https://www.nuernberg.de/presse/pdf/PM_20260628_0703_1_6a41691a9c84b.pdf |
| Frankenschnellweg, project page (updated 26 Oct 2026) | West section (2.2 km, Nürnberg/Fürth junction to Jansenbrücke): main works Feb 2027 (the page says both "beginnt im Februar 2027 wie geplant" and "könnte im Februar 2027 erfolgen"); new Sigmundstraße bridge, noise walls, extra lane towards Hafen. Preparatory tree clearing at Emmy-Noether-Straße in Oct 2026. Middle section: 1.8 km tunnel (Rothenburger Str. to Otto-Brenner-Brücke) with a district park on top; no date. Cost "knapp einer Milliarde Euro", mostly Bavarian GVFG and a special fund. Over 60,000 vehicles a day. Work must start by 26 Mar 2030 under the plan approval **(deadline unverified)** | https://www.nuernberg.de/internet/stadtportal/frankenschnellweg.html |
| Frankenschnellweg bridge at Kreuz Nürnberg-Hafen | Closed since 18 Mar 2026 until demolition **(date unverified)**. Temporary bridges over the canal and the Südwesttangente from mid-Sep 2026; then demolition and rebuild over "mehrere Jahre". Traffic on Hafenstraße and Wiener Straße has risen | https://www.nuernberg.de/presse/mitteilungen/pm_27963.html |
| Hafen bridges | Three bridges rebuilt 2025 to end 2029 **(unverified)** | https://www.nuernberg.de/internet/hafen/hafenbrueckensanierung.html |
| Rennmühlbrücke Katzwang | Bus works to 28 Feb 2027 (VGN). City: new bridge end 2026 **(unverified)** | https://www.vgn.de/fahrplanaenderungen/ · https://www.nuernberg.de/internet/soer_nbg/rennmuehlbruecke.html |
| Schwabacher Straße bridge over the Frankenschnellweg | Not stable; replaced by an embankment from spring 2026 **(unverified)** | https://www.nuernberg.de/internet/soer_nbg/schwabacher_strasse_bruecke_fsw.html |
| Münchner Straße bridges | "müssen komplett erneuert werden" (no date) | RTR minutes 23 Jun 2026 |
| Thumenberger Weg rail bridge | Renewal to end 2027; bus 45 affected | https://www.nordbayern.de/news-in-english/ready-for-future-double-tracks-vag-starts-major-long-term-construction-around-rathenauplatz-1.14722432 |
| Current tram and bus works (VAG/VGN, Oct–Dec 2026) | Spittlertorgraben track work: buses replace trams 4, 6, 10 from Plärrer, 26 Oct–13 Nov 2026. Frankenstraße track work (tram 5 cut), 15 Sep–24 Oct 2026. Ostendstraße track (trams 5/11), summer 2026. Neuer Markt (Fernwärme), line 30, to 30 Nov 2026. Fallrohrstraße, lines 43/44, to 13 Dec 2026. Allersberger Str. to 31 May 2027; Obstmarkt to 2029; Lorenzer Passage to end 2027 | https://www.vag.de/presse/aktuelle · https://www.vgn.de/fahrplanaenderungen/ |
| Rail works, Oct–Dec 2026 | Repeated S1, S2/S3 and S4 evening/morning closures with replacement buses; RE 1 Nürnberg–Kinding replaced 30 Oct–12 Dec 2026 | https://www.vgn.de/fahrplanaenderungen/ |

#### 5. Proposals under discussion (not decided or funded)

| Proposal | Proposer / stage | Facts | Sources |
|---|---|---|---|
| VAG savings of about €10 m | Requested by the treasurer, Sep 2026; council to decide | Content not published by 28 Oct 2026 | budget speech 2027 |
| Free school ticket for all pupils | CSU/SPD agreement: only if funded | No decision found | t-online, 23 Apr 2026 |
| Maglev demo line on the Messe grounds (Max Bögl) | Coalition agreement; only with private money | Replaces the Bauernfeindstraße–Klinikum Süd maglev idea | same |
| Tram Lichtenreuth–Messe–Klinikum Süd | Coalition agreement; route variants under study | — | NVP 2025; t-online |
| Tram reactivation Pirckheimerstraße / "GSO-Campuslinie" | Maßnahmenpaket 2030; not started | Risk that U3 grants must be repaid if the tram poaches U3 riders | NVP 2025 |
| Tram Altstadtquerung (route of bus 36) | Shelved since 2015 | Experts rated it useful | NVP 2025 |
| Tram reinforcement Hbf–Wodanstraße–Doku-Zentrum; Erlenstegen loop | Maßnahmenpaket 2030, package 2/3 | — | NVP 2025 |
| StUB Ostast Erlangen–Eckental | Cost estimate under way | "vorbehaltlich weiterer politischer Entscheidungen" | StUB brochure |
| U2 to Stein/Eibach | Package 3 | No positive cost-benefit ratio | NVP 2025 |
| Bed tax | Coalition agreement | Revenue for consolidation | t-online |
| Citymaut, cable car | No current debate found | — | — |

## 8. Rail and tram projects: notes per project

_Source: `research/pt-projects-notes.md`_

### Planned rail and tram projects in Nürnberg: stations for scenario modeling (as of 28 Oct 2026)

Companion to `pt_projects.csv`, which has 33 rows across 10 project_ids. I did the research in German, mostly from official sources: Stadt Nürnberg (Verkehrsplanungsamt, SÖR, press office), VAG, Regierung von Mittelfranken plan-approval files, Zweckverband StUB and the StMB/AuSbauNü study. Each source is marked **[verified]** if I opened it and saw the fact there, or **[unverified]** if I saw it only in search snippets or secondary sources.

Baseline: the VGN GTFS feed (24 Jun–12 Dec 2026) in `NUERNBERG_DATASET`. Tram lines 10 and 11 are already in it, so they are not projects. I found nothing that opened between mid-2026 and today and is missing from the feed.

#### Conventions used in the CSV

- **station_is_new is mode-specific.** 1 means the place has no station of this mode today. Examples: a tram stop at U-Bahn Rennweg is 1, and the S-Bahn at Nordostbahnhof, which today has only RB 21, is 1. 0 means an existing stop of the same mode gains a line (Rathenauplatz, Finkenbrunn, Am Wegfeld) or regains it after a construction closure (Tristanstraße, Wodanstraße).
- **trains_per_hour** is per direction and per line. "Off-peak" means daytime off-peak. The field is empty when no headway is published; then use `analog_line`.
- **funded = 1** means the project is under construction or has committed money. Projects still in plan approval, or with grant applications still to come, are 0.
- **Coordinates** come from these sources, in order of preference:
  1. OSM *proposed* or *construction* nodes and platforms. VAG and mappers have drawn the Lichtenreuth, Minervaplatz and U3 stations from the official plans.
  2. VGN GTFS stops, for existing stops.
  3. A same-name GTFS bus stop, or Nominatim, flagged "approximate".
  4. For study-only S-Bahn halts: the point on the railway nearest to the named place, flagged.
  
  One halt could not be placed ("Nürnberg Nord" on the Ringbahn). It has `station_name = unknown` and no lat/lon.

#### 1. U3 Südwest to Gebersdorf (BA 2.2): 2 rows

- **Stations:** Kleinreuth (bei Schweinau) and Gebersdorf, the terminus with a depot and sidings. About 2 km. **[verified]** City press release 122, 2 Feb 2026.
- **Opening:** first half of **2028**, per the city's status briefing of 6 Oct 2026 (https://www.nuernberg.de/internet/stadtportal/aktuell_100397.html, see plans-facts.md). The press release of 2 Feb 2026 still said "Ende 2027". Shell completed early 2024; fit-out under way. Earlier targets were 2024 (SPD, 2017), 2025 and 2026 (city, Nov 2023) **[unverified, snippets]**. `pt_projects.csv` uses 2028 with no separate risk year.
- **Cost:** €204.7 m, of which €110.1 m Bund/Land grants **[verified]**.
- **Headway:** not published; analog U3. Gebersdorf is not in VGN_STOPS. The coordinates are OSM `construction` station nodes.

#### 2. Tram 7 to Stadtpark: 5 rows

- **What:** line 7 extended from Hbf via Rathenauplatz to Stadtpark (Berliner Platz) over the renovated Bayreuther Straße line, 1.2 km. There are two new barrier-free stops, at U-Bahn Rennweg and at Stadtpark. **[verified]** VAG press release, 23 May 2025.
- **Opening: 13 Dec 2026** **[verified]** VAG news, 22 Oct 2026 (rail grinding "zur Vorbereitung der Inbetriebnahme der Linie 7 zum Stadtpark ab 13. Dezember 2026"). The date has slipped from end Sep 2026, then end Nov/early Dec. City press release 857 (30 Jul 2026) says "im Dezember" **[verified]**.
- **Feed check:** this falls just outside the feed's range, which ends 12 Dec. Rennweg is served only by U2/U3 in the feed, and Stadtpark has no tram. Hence the project counts as new.
- **Assumption:** Marientor and Wöhrder Wiese are coded `verified=0`. The route over line 8's track is my inference.
- **Headway:** 10/20 min, from the Lichtenreuth Erläuterungsbericht's line 7 plan, not from a Stadtpark-specific source.

#### 3. Tram 7 back on Allersberger Straße: 2 rows (restoration)

- Allersberger Straße track renewal runs from 24 Mar 2026 to "Frühsommer 2027". Meanwhile line 7 is diverted Hbf–Schweiggerstraße–Peterskirche–Dutzendteich. **[verified]** VAG Bauprogramm 2026; GTFS confirms the diversion.
- The normal line 7 runs Tristanstraße–Hbf **[verified, VAG May 2025]**.
- Wodanstraße as a tram stop on this section is **[unverified]**. The evidence is replacement buses to Wodanstraße (t-online) and the Lichtenreuth plan's work area reaching to Wodanstraße.
- It is not new supply versus a normal year, but it is new versus this feed. Drop it if the model should ignore construction diversions.

#### 4. Tram Lichtenreuth / Technische Universität Nürnberg (line 7): 5 rows

- **Stops:** five new stops: Hiroshimaplatz, Ingolstädter Straße, Parkstraße Süd, UTN and Bauernfeindstraße (a loop at the U1 station). The existing Tristanstraße stop is rebuilt. 2.5 km. **[verified]** Erläuterungsbericht, Regierung von Mittelfranken plan-approval file.
- **Service:** line 7 every 10 min (Mo–Fr 6–20 h, Sat 8–20 h) and every 20 min otherwise. A second line would follow later "bei Bedarf".
- **Dates:** construction start Q1 2027, opening end 2030 **[verified]**. The city page also says opening 2030 **[verified]**.
- **Status:** plan approval is still pending. The documents were on public display 17 Nov–16 Dec 2025, and I found no approval decision by Oct 2026. City press release 857 (Jul 2026) says "im Planfeststellungsverfahren" **[verified]**. So status = planning, and risk 2031 is my assumption.
- **Funding:** grant applications only after the approval-stage design, so funded = 0.

#### 5. Tram section 2 to Klinikum Süd: 3 rows

- Bauernfeindstraße–Messe–Bertolt-Brecht-Schule–Klinikum Süd. Preliminary planning since 2024; survey and route-variant study being prepared. Council decision 20 Jul 2023. **[verified]** city page. No stop list, line or date.
- The rows are corridor waypoints with approximate coordinates (U-Bahn Messe, the school, the Klinikum Süd bus stop).
- One snippet adds a "LangwasserBad" waypoint **[unverified]**.

#### 6. Minervastraße gap closure (line 4): 3 rows

- **What:** line 4 extended Gibitzenhof (loop moved)–Minervaplatz (new)–Finkenbrunn (meets line 5). 1.7 km. Plan approval 3 Jun 2025. Opening end 2027. Line 4 runs every 10 min weekdays by day, 20 min evenings and Sundays. **[verified]** city page.
- **Construction:** track construction from early Jun 2026, opening "Ende 2027" **[verified]** VAG Bauprogramm 2026.
- Bus 68 is replaced.

#### 7. Melanchthonplatz stop (Landgrabenstraße renewal): 1 row

- **What:** plan approval in place. Construction 2027, completion about end 2028. **[verified]** SÖR page.
- **Stop change:** the new stop replaces Heynestraße and lets line 11 serve the area. Lines 6/10/11 are my inference from the feed.
- **Effect:** small, because it is a relocation of about 150 m, and service on the section is interrupted for 1–2 years during the works.

#### 8. StUB, Nürnberg section Am Wegfeld–Reutles: 5 rows

- **Stops in Nürnberg:** Am Wegfeld, Buch Nord, Boxdorf, Moosäckerstraße, Reutleser Straße. The ZV says they may still change. **[verified]** stadtumlandbahn.de Nürnberg page.
- **Earlier stop list:** a Dec 2023 ZV document listed "Moosäckerstraße" and "Boxdorf", with "Würzburger Straße" as optional **[unverified]**.
- **Route and line:** an extension of tram line 4. The Verkehrsausschuss decided the route on 26 Mar 2026. The plan-approval application is due H2 2026 and was "being finalised" on 30 Jul 2026. **[verified]** city StUB page and press release 857.
- **Dates:** construction 2028/2029, first tram to Reutles 2031/2032 **[verified]** ZV schedule page. The brochure (Mar 2026) says "ab 2031" **[verified]**.
- **Headway:** 10 min by day plus peak extras **[verified]** brochure and Dialogforum 17.
- **Political risk:** Erlangen voters approved the project in June 2024 **[unverified, snippets]**. The Nürnberg section has no open court case that I found. The Erlangen/Herzogenaurach sections are outside the city and not in the CSV.

#### 9 and 10. S-Bahn S9: Nordring (4 halts) and Gräfenberg line (Buchenbühl): 5 + 2 rows

- **Source:** AuSbauNü first results, 17 Oct 2024 **[verified, PDF opened]**.
- **U06.2 Nordring:** S9 Fürth Hbf–Nürnberg Nordost every 30 min, with new halts Nürnberg Nord, Thon, Wetzendorf and Muggenhof. €118 m, BCR 1.0.
- **U06.1 Gräfenberg:** electrify the line, S9 every 30 min, new halt Buchenbühl. €141 m, BCR 1.0.
- **Status:** both are only "weiterverfolgen" recommendations. The second forum release (31 Oct 2025) names other projects and cites a tight state budget **[verified]**. I found no planning order, so: planning, unfunded, no year.
- **Coordinates:** the halt sites are not published. Mine are the nearest points on the OSM railway to the named place.

#### Checked and excluded

- **Tram to Kornburg / Fischbach:** feasibility study gave BCR < 0 (city overview of decisions 2021) **[unverified, snippet]**.
- **Tram via Pirckheimerstraße (Hbf–Wegfeld):** only kept open as an option in the Bayreuther Straße design. No project.
- **Tram on Nordwestring / Thon–Wetzendorf:** no project found. The current Nordwestring works are road resurfacing.
- **Plärrer track renewal** (approval 10 Sep 2026) and **Neue Rothenburger Straße:** these do not change service. The latter only gives access to U-Bahn Kleinreuth.
- **Hilpoltstein extensions (S2 via Roth, S5 via Allersberg):** S2 timing in Nürnberg is unchanged and the stations are outside the city.
- **Markt Erlbach / Cadolzburg S-Bahn:** Cadolzburg trains run through to Nürnberg Hbf, but they add no stop in the city.
- **3rd track Feucht–Neumarkt, Deutschlandtakt, NBS Würzburg–Nürnberg:** long-term DB items with no defined effect on city stations.
- **Söder's maglev:** reported as "vor dem Aus" **[unverified]**.
- **U-Bahn automation:** no service change.
- **No new S-Bahn halts in the city** are planned beyond the study halts above. I could not substantiate the candidates "Nürnberg-Ost" or "Fürth Klinikum".

## 9. Timing and construction

_Source: `research/timing-and-construction.md`_

### When rail reaches the new homes, and what is under construction meanwhile

Methods behind chapter 8 (v5, the timing gap) and the construction section of the corridor briefings (chapter 12), on `NUERNBERG_DATASET` with the read-only SQL below. No results are stored here: run the queries live. Reference weekday Wednesday 21 Oct 2026. Walking distances as in the model: 300 m for tram, 600 m for U-Bahn, S-Bahn and regional rail, in EPSG:25832 metres.

#### 1. Is growth already under way?

Compare, for the new-build areas (the Lichtenreuth group 41/42/43, Eberhardshof, Großreuth b. Schweinau, Höfen, Wetzendorf), the residents counts 2023–2025 (`DISTRICT_POPULATION`) with the model's straight line from the 2024 count to `pop_2033_model`, and with the years the new homes are first occupied (`NEWBUILD_PROJECTS`). Where homes are first occupied from 2026, the counts can't show them yet.

Background on the two largest sites: the Lichtenreuth group is the railway land of the former Südbahnhof; Eberhardshof had AEG (closed 2007) and Quelle (closed 2009). Jobs per area over time are in `DISTRICT_EMPLOYMENT` (2019–2024) and the 2005 table (see [district-growth.md](district-growth.md)).

The building statistics (`DISTRICT_HOUSING`) give homes permitted and completed per area and year. Completions are recorded when the builder reports them, so they can lag behind the residents count.

#### 2. The timing gap (v5)

`NEWBUILD_PROJECTS.centroid_lat/lon` is the area-weighted centre of each project's site on the city's new-homes map (WFS `Wohnungsneubau:Schwerpunkte_des_Wohnungsneubaus`, retrieved 6 Nov 2026). Distances are from that point.

The query below returns, per project, whether a U-Bahn, tram or S-Bahn stop is within walking distance today, and the first year a dated (or any) project station comes within walking distance. Compare that year with the project's first occupancy to get the gap.

```sql
WITH nb AS (
  SELECT "project_id", MAX("project_name") AS name, MAX("homes_total") AS homes, MAX("first_occupancy") AS first_occ,
         ST_TRANSFORM(CAST('POINT(' || CAST(MAX("centroid_lon") AS DECIMAL(9,6)) || ' ' || CAST(MAX("centroid_lat") AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.NEWBUILD_PROJECTS GROUP BY "project_id"
), rail AS (
  SELECT CASE WHEN "serves_ubahn" = 1 OR "serves_sbahn" = 1 THEN 600 ELSE 300 END AS walk,
         ST_TRANSFORM(CAST('POINT(' || CAST("stop_lon" AS DECIMAL(9,6)) || ' ' || CAST("stop_lat" AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.VGN_STOPS
  WHERE "stop_lat" BETWEEN 49.30 AND 49.58 AND "stop_lon" BETWEEN 10.92 AND 11.30
    AND ("serves_ubahn" = 1 OR "serves_tram" = 1 OR "serves_sbahn" = 1)
), proj AS (
  SELECT "project_id" AS pid, "opening_year_model" AS yr,
         CASE WHEN "funded" = 1 OR "opening_year_assumed" = 0 THEN 1 ELSE 0 END AS dated,
         CASE WHEN "mode" IN ('U-Bahn', 'S-Bahn', 'Regional rail') THEN 600 ELSE 300 END AS walk,
         ST_TRANSFORM(CAST('POINT(' || CAST("lon" AS DECIMAL(9,6)) || ' ' || CAST("lat" AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.PT_PROJECT_STATIONS WHERE "lat" IS NOT NULL
), served_now AS (
  SELECT DISTINCT nb."project_id" FROM nb JOIN rail r ON ST_DISTANCE(nb.g, r.g) <= r.walk
), yproj AS (
  SELECT nb."project_id", MIN(CASE WHEN p.dated = 1 THEN p.yr END) AS yr_dated, MIN(p.yr) AS yr_any
  FROM nb JOIN proj p ON ST_DISTANCE(nb.g, p.g) <= p.walk GROUP BY 1
)
SELECT nb."project_id", nb.name, nb.homes, nb.first_occ,
       CASE WHEN s."project_id" IS NULL THEN 0 ELSE 1 END AS rail_today, y.yr_dated, y.yr_any
FROM nb LEFT JOIN served_now s ON s."project_id" = nb."project_id"
LEFT JOIN yproj y ON y."project_id" = nb."project_id"
ORDER BY nb.homes DESC
```

#### 3. The construction decade (corridor briefings)

`ROADWORKS` (SÖR Baukoordination) holds the planned works with start and end dates and polygons; `is_tram_track = 1` marks tram-track works, `is_cycling = 1` cycle-path works. A work counts as active in every calendar year from its start year to its end year.

**Track closures.** The planned track closures (`kind = 'Schienenstreckensperrung'`, VAG): An der Ehrenhalle, Wodanstraße, Allersberger Straße, Hiroshimaplatz, Schultheißallee and Bayernstraße (24 Mar 2026–1 Jul 2027), and Landgrabenstraße, Am Plärrer, Steinbühler Straße, Steinbühler Tunnel, Dianastraße and Gibitzenhofstraße (2 Jan–30 Nov 2027).

**Tram service next to track works.** Tram stop events on the reference weekday at stops within 50 m of an active tram-track work, as a share of all tram stop events in the city, per year (query below).

**Areas most exposed.** Per area and year: the share of all capacity offered within walking distance that is tram capacity at those stops, and the share of the area's tram capacity. This uses the same `works` and the capacity and walking-distance reach described in [urban-planning.md](urban-planning.md#the-model).

**What the works are.** The Südstadt cluster (Landgrabenstraße, Christuskirche, Heynestraße, 2027–2028) is the track renewal with the new Melanchthonplatz stop. Brunecker Straße, Münchener Straße and Dr.-Luise-Herzberg-Straße (2027–2030) are the Lichtenreuth tram being built. Am Plärrer (2027–2031) is track and overhead-line work at the western hub. Bahnhofsplatz (2030–2031) is "Neubau zusätzliches Gleis", an extra tram track at the Hauptbahnhof. Erlanger Straße (2029–2033, ZV StUB) is the StUB's "Straßenbahnneubau".

```sql
WITH svc AS (
  SELECT "service_id" FROM NUERNBERG_DATASET.VGN_CALENDAR
   WHERE "wednesday" = 1 AND DATE '2026-10-21' BETWEEN "start_date" AND "end_date"
     AND "service_id" NOT IN (SELECT "service_id" FROM NUERNBERG_DATASET.VGN_CALENDAR_DATES
                              WHERE "date" = DATE '2026-10-21' AND "exception_type" = 2)
  UNION
  SELECT "service_id" FROM NUERNBERG_DATASET.VGN_CALENDAR_DATES WHERE "date" = DATE '2026-10-21' AND "exception_type" = 1
), tram_stop AS (
  SELECT st."stop_id", COUNT(*) AS deps
  FROM NUERNBERG_DATASET.VGN_STOP_TIMES st
  JOIN NUERNBERG_DATASET.VGN_TRIPS t ON t."trip_id" = st."trip_id"
  JOIN svc ON svc."service_id" = t."service_id"
  JOIN NUERNBERG_DATASET.VGN_ROUTES r ON r."route_id" = t."route_id"
  WHERE r."line_mode" = 'Tram' GROUP BY 1
), stops AS (
  SELECT ts."stop_id", COALESCE(NULLIF(s."parent_station", ''), s."stop_id") AS station, ts.deps,
         ST_TRANSFORM(CAST('POINT(' || CAST(s."stop_lon" AS DECIMAL(9,6)) || ' ' || CAST(s."stop_lat" AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM tram_stop ts JOIN NUERNBERG_DATASET.VGN_STOPS s ON s."stop_id" = ts."stop_id" WHERE s."in_nuernberg" = 1
), works AS (
  SELECT YEAR("start_date") AS y0, YEAR("end_date") AS y1, ST_TRANSFORM(CAST("shape_wkt" AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.ROADWORKS WHERE "is_tram_track" = 1
), yrs AS (
  SELECT 2026 + LEVEL - 1 AS yr FROM DUAL CONNECT BY LEVEL <= 7
), hit AS (
  SELECT DISTINCT y.yr, s."stop_id", s.station, s.deps
  FROM yrs y JOIN works w ON y.yr BETWEEN w.y0 AND w.y1
  JOIN stops s ON ST_DISTANCE(s.g, w.g) <= 50
)
SELECT h.yr, COUNT(DISTINCT h.station) AS stations, SUM(h.deps) AS tram_deps_affected,
       ROUND(100 * SUM(h.deps) / (SELECT SUM(deps) FROM stops), 1) AS pct
FROM hit h GROUP BY h.yr ORDER BY h.yr
```

#### 4. Cycling works

Assign the planned cycle-path works (`is_cycling = 1`) to areas by their polygons and compare with the areas thinnest in cycle network per person in the cycling dashboard ([cycling-coverage.md](cycling-coverage.md)).

#### Caveats

- Distances to new homes are from a site's centre; large sites span several hundred metres.
- "Next to a track work" (50 m) flags service at risk. SÖR's data doesn't say whether a line runs, is diverted or is replaced by buses; the explicit track closures do.
- The reference weekday already includes the 2026 diversions on Allersberger Straße, so 2026 tram service is slightly below normal.
- Planning dates move; most non-tram works are planned only a year or two ahead.

## 10. Service cuts (savings package)

_Source: `research/vag-cuts-2027-notes.md`_

### VAG service cuts 2027: notes behind PT_SERVICE_CUTS and PT_SAVINGS_PACKAGES

What the city proposes to cut in the VAG service, how the document is built, and how its statements became the rules in `data/source/pt_service_cuts.csv` (`scripts/digitize_vag_cuts_2027.py`). Used by v6 (chapter 9). The rules cover P3 as published, P1 and P2 sorted out of it, and P4's concrete measures. No results are stored here: the dashboard applies the rules to the timetable live.

#### The source

**"Sparmaßnahmenpaket im VAG-Verkehrsangebot"**, a council document in the city's Bürgerinformationssystem, planning status 27 Oct 2026 (the detail tables say 26 Oct 2026), published in early November 2026: https://online-service2.nuernberg.de/buergerinfo/getfile.asp?id=947894&type=do. Verified on the PDF itself (6 pages).

Background, from [plans-facts.md](plans-facts.md#1-political-and-budget-frame): the city must improve its 2027 budget by at least €122 m and asked VAG for savings proposals of about €10 m; VAG lost €97.7 m in 2025 with record passenger numbers. In December 2024 the council cut a planned bus reduction from €1.4 m to about €0.6 m so that no whole bus line was withdrawn. P3 withdraws three.

#### What the document contains

| Page | Content |
|---|---|
| 1 | Five packages P1–P5 for decision, each building on the one before, with main measures, start dates, decision date and VAG's estimates of passengers lost and euros saved per year → `PT_SAVINGS_PACKAGES` |
| 2 | A summary of P3 by mode: measures and affected lines, from March 2027 and for the whole package from August 2027 |
| 3–4 | P3 from 8 March 2027, one row per line, seven day-type columns → `PT_SERVICE_CUTS`, stage `2027-03` |
| 5–6 | P3 end state ("Gesamtpaket / Endzustand"), from 2 August 2027 → stage `2027-08` |

**Packages** (page 1; all decisions due 30 Nov 2026):
- **P1**, recommended by VAG's supervisory board: demand-based headway changes, 40-minute headways from earlier in the evening, a holiday timetable in all school holidays. About −0.2 m passengers, €1.3 m a year.
- **P2** = P1 + more headway cuts, shortened routes, fewer reinforcement trips, thinner early and late service. About −0.6 m, €2.6 m.
- **P3** = P2 + bus lines 81, 82 and 84 withdrawn, route sections withdrawn, later starts and earlier ends, all trams every 15 minutes in all school holidays (Mon–Sat), trams 10 and 11 gone before 6:00 and after 18:30, U1–U3 every 10 minutes before 6:00 on weekdays, and on Saturday and Sunday before 8:00 only the Nightliner network, as on a strike day. About −2.8 m, €5.3 m.
- **P4** = P3 + service ends at 23:30 on all lines (Mon–Thu and Sun), trams 10 and 11 also gone all weekend, a 30/60-minute grid every day from 22:00. About −5 m, €8.1 m.
- **P5** = P4 + cuts on major lines including the ring bus, lines suspended at times, a general 30/60-minute network. About −6 m, €10.0 m.
- For P4 and P5, VAG writes "Dringende Empfehlung: Entscheidung zu einem späteren Zeitpunkt treffen!" (strong recommendation to decide later). Their parts beyond P3 would need about four months' lead time.

Only P3 is published line by line. P1 and P2 are subsets of P3 that the tables don't mark; P4 and P5 go beyond what is published. How the dataset still gives each package rules is in [From P3 to P1–P5](#from-p3-to-p1p5).

#### From cells to rules

**Reading the tables.** The text in the PDF is selectable, but plain extraction mixes the columns. The script reads row boundaries from the drawn grid lines and assigns each text line to a day-type column by its x position (columns: Mon–Thu outside holidays, Mon–Thu in holidays, Fri outside, Fri in, Sat outside, Sat in, Sun). Lines of text less than 10 pt apart are joined (a wrapped line); larger gaps start a new statement. "U2/3" becomes two rows, U2 and U3.

**Rule types.** The statements are formulaic. Each is parsed into one of:

| Statement (examples) | rule_type | How it cuts the reference day |
|---|---|---|
| `entfällt` (81, 82, 84) | line_dropped | every trip |
| `entfällt vor 6:00 & nach 18:30` (10, 11), `ab 21 Uhr: entfällt` (40), `entfällt ab 17:30 statt 19:30 Uhr` (83), `Betriebsbeginn ab 6 Uhr`, `bis 8 Uhr: entfällt; reines Nightliner- / Streiknetz` | window_dropped | trips whose first departure is in the window |
| `bis 6 Uhr: 10'- statt 5'-Takt`, `17:30 - 20:30: 40'- statt 20'-Takt`, `20'-Takt vor 6 Uhr`, `20'-Takt ab 18:30 Uhr statt 20:30 Uhr`, `6:00 - 20:30: 15-min-Takt Straßenbahn` | headway | per direction, keep the first trip in each slot of the new headway |
| `Entfall der zweiten Fahrt morgens je Richtung` / `Entfall der vorletzten Fahrt abends je Richtung` | trip_dropped (rank 2 / −2) | the second / second-to-last trip per direction |
| shortened routes, short runs, named reinforcement trips, "einzelne Fahrten", Rufbus, the Nightliner row | not_modeled | nothing |

**Why slots for headways.** Several statements give only the new headway ("20'-Takt vor 6 Uhr"). Keeping the first trip in each slot of the new headway needs no old headway, keeps lines that already run that often unchanged, and gives the right number of trips for 5→10, 6⅔→10, 10→15, 10→20 and 20→40 minutes. Checked against the feed: tram 4 runs every 10 minutes on the reference Wednesday from about 5:00 to 20:30 and every 20 minutes after, so "20'-Takt vor 6 Uhr" and "20'-Takt ab 18:30 statt 20:30" each halve the trips in their windows.

**Approximations, noted per row in `model_note`:**
- A headway cut on part of a route (line 40 "bis Henenfelder", 53 "bis Luitpoldhain", 58 "Ende von Fahrten an Vogelweiherstraße", 51/52 short runs to Worzeldorf) is applied to the whole line.
- A later start "ab Am Wegfeld" (31) or "ab Flachröste" (56) drops early trips in both directions.
- The time of a trip is its first departure, wherever it starts.
- Not modeled: line 43 turning at Passauer Straße, every second trip of 51 ending at Worzeldorf, 31's short runs between Am Wegfeld and Neunhof and its Rufbus replacement, 56's evening section, named reinforcement trips of 55 and 58, unspecified single trips (54, 59, 30), the line 83 reroute via Lohhof, and the extra Nightliner trips on weekend mornings (6–8 h every 30 minutes, last departure from the Hauptbahnhof at 7:30). The modeled loss is therefore a little too high on weekend mornings (the Nightliner replacement isn't added) and too low where routes are shortened.

**Corrections.** The end-state table and the summary on page 2 disagree in two places. The summary is explicit, so the end state follows it, and the rows say so:
- Trams 4, 5 and 7, Mon–Thu and Fri outside holidays: the end-state cells are empty, the summary lists "Ausweitung der Schwachverkehrszeiten 4, 5, 7, 10, 11" for the end state. Carried over from March (20-minute headway before 6:00 and from 18:30).
- Bus 83: the end-state table has no row, the summary lists "Zeitweiser Entfall von Linien 31, 40, 83" for the end state. Carried over from March.
- Not corrected: line 67 drops its second-to-last weekday evening trip in March but not in the end state; the summary doesn't list 67 at all, so the tables are kept as printed.

#### From P3 to P1–P5

v6 shows every package, so each rule carries the first package that includes it (`package`, with the reason in `package_basis`). This is an interpretation of page 1's measure lists, not something the document states:

| Package | Rules | Matches on page 1 |
|---|---|---|
| P1 | bus headway cuts to 40 minutes that start at 17:00 or later; bus cuts that appear only in the school-holiday columns | "Früherer Beginn 40-Min-Takte", "Ferienfahrplan in allen Ferien" |
| P2 | all other bus headway cuts; the second or second-to-last trip dropped; shortened routes and reinforcement trips (not modeled) | "Weitere Taktausdünnungen", "Ausdünnung Tagesrandlagen", "Verkürzung Linienwege", "Entfall Verstärkerfahrten" |
| P3 | lines and sections withdrawn, later starts and earlier ends, all tram and U-Bahn rules, weekend mornings on the Nightliner network, and every rule found only in the end-state table | P3's own list; P1 and P2 are implemented in full on 8 Mar 2027, so anything new in August is P3 |
| P4 | service ends at 23:30 (Mon–Thu, Sun) on every day line; trams 10 and 11 also gone on Saturday and Sunday; from 22:00 every day a 30-minute headway on U-Bahn and tram and a 60-minute headway on buses | P4's first three bullets. The split of the "30/60-Min Taktraster" by mode is an assumption |
| P5 | nothing that cuts trips: its bullets name no lines or times except the ring bus | listed as `not_modeled` |

P1 and P2 are taken from the March stage, P3 and P4 from the end state; [data/data-model.md](../data/data-model.md) gives the rule. VAG's €/year and passengers/year figures for each package are not checked by the model, which measures capacity only.

#### Reference days

The document's columns map to the dashboard's reference days: **Mon–Thu outside holidays** → Wednesday 21 Oct 2026, **Saturday outside holidays** → Saturday 24 Oct 2026 (a regular Saturday in the feed: the same VAG trips as the Saturdays before and after). The Saturday matters: in the end state nothing but the Nightliner network runs before 8:00 on weekends, trams 10 and 11 stop at 18:30, and many bus lines run every 40 instead of 20 minutes all day. School holidays, Fridays and Sundays are in the table but have no reference day.

#### Limits

- **A proposal.** The council decides by 30 Nov 2026; it may adopt any package, or postpone. Until then "after the cuts" is a scenario.
- **P1, P2, P4 and P5 are modeled from their descriptions.** P1 and P2 by sorting P3's rules, P4 through its three concrete measures; P5 shows the same cuts as P4.
- **The feed ends on 12 Dec 2026**; the cuts start in March 2027. The rules are applied to the 2026 reference days, so the result is "today's timetable with P3 applied", not a future timetable. Other changes by 2027 (tram 7 to Stadtpark from 13 Dec 2026, construction diversions) are not in it.
- **Capacity, not passengers.** VAG's passenger estimates (−2.8 m a year for P3) are quoted as VAG's. The dataset has no passenger counts.

## 11. Cycling

_Source: `research/cycling-coverage.md`_

### Nürnberg Cycling Coverage: how well is each area served for cycling?

The data and method behind the dashboard `nuernberg-cycling-coverage` on `NUERNBERG_DATASET`. The network is OpenStreetMap (© OpenStreetMap contributors, ODbL), retrieved 28 Oct 2026; the counters are the city's 12 permanent bicycle counters (Eco-Counter pages, Jan 2025–Oct 2026); weather is DWD station 03668 Nürnberg. No results are stored here: every value comes from the dashboard, computed live.

#### The data

**Network.** The city publishes no open cycle-network data, so the dataset uses OSM ways inside the city. Length counts two-way paths for both directions (`length_m × directions`). Path types and their default weights:

| Path type (from OSM tags) | Default weight |
|---|---:|
| Shared footpath (Gemeinsamer Geh- und Radweg) | 0.5 |
| Separated cycle and footpath | 0.8 |
| Painted lane (Radfahr-/Schutzstreifen) | 0.6 |
| Cycle track (Radweg), separate way | 1.0 |
| Cycle street (Fahrradstraße) | 1.0 |
| Cycle track along a road | 1.0 |
| Shared lane or bus lane | 0.3 |
| Field or forest track, cycling designated | 0.3 |

OSM completeness varies by street. Cycle tracks along roads are often mapped as separate ways, and then appear as "Cycle track" or "Separated cycle and footpath". Painted lanes on roads are tagged on the road itself.

**Counters.** 12 sites. Some have long gaps: Königstor (RZG001) is out of service since April 2024 (construction), and others stop reporting for months. The pages report outages as 0, and the dataset treats those counter-days as missing. Directions are only "in" and "out". The counts have no stated licence; each build reads them from the public pages, and they are not in the repo.

**The city's plan.** The Radwegenetzplan (Stand 01/2021) is a PDF map. It is digitized into `CYCLE_NETWORK_PLAN_2021` (see [data-model.md](../data/data-model.md)). Its categories:

- Routes over quiet side streets (dotted)
- Planned routes (blue)
- Field, forest and canal paths (dashed; the city's web page says 50 + 17 km)
- Built 2013–2020 (red)
- Decided planning (pink)

Check of the digitization: the share of each category's lines within about 20 m of today's OSM cycle infrastructure should be high for "built 2013–2020" and low for planned lines and field paths.

#### What the dashboard looks at

- **Per person** (residents + jobs, w = 1, 2024 jobs): weighted km per 1,000 people, per area against the city value. Which areas are thinnest, and whether any have no mapped cycle infrastructure.
- **Per km²**, for comparison: dense areas can look average per km² and thin per person; outer areas with a lot of open land the other way round.
- **The 2021 plan:** km of planned and decided routes per area (both directions), against the areas thinnest per person. Quiet-street routes are a separate category, which the OSM-based view doesn't count.
- **Use:** bikes per weekday per counter, and the change on days with ≥5 mm rain.

#### Caveats

- **Supply only:** mapped length and path type. Nothing on width, surface, gaps, junction safety or motor traffic.
- **Twelve counting points** can't stand for whole areas, and some of them have gaps.
- **The weights are assumptions,** not an official quality scale.
- **Planned cycling projects** are in `ROADWORKS` (`is_cycling = 1`, works with dates and polygons, e.g. Radvorrangroute RVR 10 cycle streets in 2026, the Radschnellverbindung Nürnberg–Erlangen 2028–2029). [plans-facts.md](plans-facts.md) has the programme: 135 km of Radvorrangrouten planned, about 1.3 km built by the end of 2025.
- **Closures:** `ROADWORK_DIVERSIONS` has current or planned cycle-path closures with diversions.
