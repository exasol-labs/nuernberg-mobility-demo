# NUERNBERG_DATASET data model

Schema `NUERNBERG_DATASET`, loaded with `exakit data-load` from the folder `data/nuernberg-dataset` (see [tutorial chapter 2](../tutorial/02-load-data.md)). One table per file, table name = file name upper-cased. Column names below are the CSV headers; confirm their types with `describe_exasol_tables_and_views`.

**Column names are lowercase and case-sensitive.** exapump creates them exactly as in the CSV header, so every column must be double-quoted in SQL: `SELECT "district_no", "population" FROM NUERNBERG_DATASET.DISTRICTS`. Unquoted `district_no` fails with "object DISTRICT_NO not found". Table and schema names are upper case and need no quotes.

**Types as loaded (verified):** dates are `DATE` (`count_date`, GTFS `start_date`, `end_date`, `date`, counter `first_data`/`last_data`), counts and flags are `DECIMAL(36,0)`, measurements and coordinates are `DOUBLE`, text is `VARCHAR`. GTFS `arrival_time` / `departure_time` are text `HH:MM:SS` (can exceed 24:00).

All coordinates are **WGS84** (`lat`, `lon` in degrees). Polygons are WKT in WGS84 with `lon lat` order. Point tables carry `bezirk_no` and `district_no` from point-in-polygon against the Bezirke (empty outside the city).

**Areas.** An area ("district") is a statistical Bezirk, or a group of small Bezirke the city only publishes together: 18/19, 34/35, 38/39, 41/42/43, 75/85/87, 76/77. That gives 79 areas from 87 Bezirke. `district_no` is the lowest Bezirk number in the area. The statistical Stadtteil is the tens digit of the Bezirk number (0–9). Group 75/85/87 spans Stadtteile 7 (Almoshof) and 8 and is filed under 8; `BEZIRKE.stadtteil_no` is exact.

## Tables

### DISTRICTS — the areas, one row per area
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

### BEZIRKE — the statistical Bezirke
bezirk_no, bezirk_name, district_no (its area), stadtteil_no, area_km2 (from the shapefile), centroid_lat, centroid_lon, polygon_wkt.

### DISTRICT_POPULATION — residents per area, counted and modeled
| column | meaning |
|---|---|
| district_no, district_name | join key, name |
| pop_2023, pop_2024, pop_2025 | Hauptwohnsitz counts at 31 Dec (Bezirksatlas, Melderegister). `pop_2025` equals `DISTRICTS.population` |
| newbuild_homes_2024_2033 | homes in `NEWBUILD_PROJECTS` with first occupancy 2024–2033, by share in the area |
| pop_2033_model | **model**, not a published figure |
| source, method_2033 | sources; the model in one paragraph |

The model for 2033: the city forecasts 2033 only per Stadtteil (`STADTTEIL_FORECAST`). Per Stadtteil, the change from the 2024 count to the forecast is split in two. The new-build movers 2025–2033 go to areas in proportion to their listed new homes, at most 2 persons per listed home; the rest of the change goes in proportion to 2024 residents. Stadtteil totals match the forecast. M558's new-build movers are a gross figure (many move from elsewhere in the city), so areas without new homes shrink. The dashboards interpolate linearly from the 2024 count to 2033 and hold the value after 2033.

### STADTTEIL_FORECAST — the city's forecast per Stadtteil
stadtteil_no, stadtteil_name, pop_2024_areas (sum of `DISTRICT_POPULATION.pop_2024` over the areas filed under the Stadtteil), pop_2033_forecast (report M558, text pp. 11/16; sum 554,710), newbuild_movers_2025_2033 (M558 pp. 8–9; sum 49,120), pop_2035_forecast_m529 (previous edition, base 2021), source. M558 works from a reduced 2024 base (542,966, without people in refugee housing), so its base differs from the atlas count.

### NEWBUILD_PROJECTS — major housing projects, one row per project and Bezirk
project_id, project_name, homes_total, first_occupancy (year), bezirk_no, district_no, share (of the project's area in that Bezirk), homes_in_bezirk, centroid_lat, centroid_lon (area-weighted centre of the whole project's site, WGS84; the same on every row of a project), developer, source. The city layer is incomplete for Stadtteil 7. Use the centroid to measure how far a project's homes are from a stop; group by `project_id` first, since a project spanning two Bezirke has two rows.

### DISTRICT_EMPLOYMENT — jobs at place of work, 2019–2024 and 2005
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

### DISTRICT_HOUSING — homes permitted and completed per area and year, 2012–2025
| column | meaning |
|---|---|
| district_no, district_name, year | one row per area and year |
| homes_permitted, floor_area_m2_permitted | homes in building permits issued that year (new builds and conversions, net) |
| homes_completed, floor_area_m2_completed | homes reported as completed that year (net; conversions and demolitions can make it negative) |
| source | "Nürnberg in Zahlen" tables WPG_GBGG_03_zbez and WPG_GBGF_03_zbez (building statistics) |

**Completions are recorded when reported and can lag years** behind move-ins. Use permits, completions and the residents count (`DISTRICT_POPULATION`) together.

### DISTRICT_PROFILE — social and car indicators per area and year, 2012–2025
| column | meaning |
|---|---|
| district_no, district_name, year | one row per area and year |
| min_income_rate_pct | share of residents receiving minimum-income benefits (SGB II, SGB XII, asylum seekers' benefits), 31 Dec, in % |
| cars, cars_ev | registered passenger cars and fully electric cars, 31 Dec 2025 (**2025 rows only**, empty otherwise) |
| cars_per_1000_residents | cars per 1,000 residents with main residence, 2025 |
| source | "Nürnberg in Zahlen" table SMOS_mindessicherung_zbez; Bezirksdatenblätter 2025 |

Cars are counted where they are registered, so company and rental fleets inflate business areas. Flag areas above about 700 per 1,000 residents rather than reading them as household car ownership.

### PT_PROJECT_STATIONS (10 projects) — planned rail and tram projects, one row per station and line
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

### VGN_STOPS — GTFS stops
| column | meaning |
|---|---|
| stop_id, stop_name | id and name; names start with the town, e.g. "Nürnberg Plärrer", "Fürth (Bay) Hbf" |
| stop_lat, stop_lon | WGS84 |
| location_type, parent_station | GTFS; `parent_station` groups platforms (empty for single stops) |
| in_nuernberg, bezirk_no, district_no | 1/0 flag, Bezirk and area (empty outside the city) |
| **stop_mode** | the highest-capacity mode serving the stop: S-Bahn, U-Bahn, Regional rail, Tram or Bus (empty if no scheduled service). A station gets the modes of its platforms |
| **stop_modes** | every mode serving it, highest capacity first, `|`-separated |
| **serves_sbahn, serves_ubahn, serves_regional_rail, serves_tram, serves_bus** | 1/0 per mode |

### VGN_ROUTES, VGN_TRIPS, VGN_STOP_TIMES, VGN_CALENDAR, VGN_CALENDAR_DATES, VGN_TRANSFERS, VGN_AGENCY — GTFS
- `VGN_ROUTES`: route_id, agency_id, route_short_name, route_long_name, route_desc, route_type (GTFS code), **line_mode** (S-Bahn = route_type 2 with route_desc "S-Bahn"; other route_type 2 = Regional rail; 0 Tram; 1 U-Bahn; 3 Bus), **is_on_demand** (1 for Rufbus, Anrufsammeltaxi, Linienbedarfstaxi, Linientaxi; counted as Bus), **is_night** (1 for N-lines). `line_mode` is the join key to VEHICLE_CAPACITY. Lines: U1–U3; trams 4, 5, 6, 7, 8, 10, 11 (and D); S1–S6.
- `VGN_TRIPS`: route_id, service_id, trip_id, trip_headsign, direction_id, block_id.
- `VGN_STOP_TIMES`: trip_id, arrival_time, departure_time (text HH:MM:SS, may exceed 24:00), stop_id, stop_sequence, stop_headsign, pickup_type, drop_off_type.
- `VGN_CALENDAR`: service_id, monday..sunday (1/0), start_date, end_date (DATE). `VGN_CALENDAR_DATES`: service_id, date (DATE), exception_type (1 added, 2 removed).
- `VGN_TRANSFERS`: from_stop_id, to_stop_id, transfer_type, min_transfer_time.
- The feed covers 2026-06-24 to 2026-12-12 and the whole VGN region. **Scheduled service only: no passengers, delays, crowding or live positions.** No `shapes`; use stop sequences.

### VEHICLE_CAPACITY — how many people one scheduled trip can carry, per line_mode
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

### LINE_CAPACITY — per-line overrides
line, line_mode, capacity_per_trip, basis, sources: U1 604 (one G1, verified), U2/U3 580 (mostly two coupled DT3; share of long trains inferred), S1/S2 600, S3/S4/S5 620, S6 405. Use `COALESCE(line override, mode value)`. These are planning values, not measured loads. A departure weighted by `capacity_per_trip` is **capacity offered**.

### PT_SAVINGS_PACKAGES — the city's five savings packages for the VAG service (proposal, Oct 2026)
One row per package, transcribed from page 1 of the council document (planning status 27 Oct 2026, decision due 30 Nov 2026). Columns: `package` (P1–P5), `builds_on` (each package includes the one before), `passengers_lost_per_year_est`, `savings_eur_per_year` (**VAG's own estimates**, not computed from this dataset), `implementation_start`, `implementation_note`, `decision_by`, `vag_note` (P1 is recommended by VAG's supervisory board; for P4 and P5 VAG strongly recommends deciding later), `main_measures_de` (as printed), `main_measures_en`, `detailed_in_pt_service_cuts` (1 if `PT_SERVICE_CUTS` has rules that cut trips for the package: P1–P4; 0 for P5, whose own measures are too vague to model), `source`.

| package | passengers lost per year (VAG) | € saved per year (VAG) | from |
|---|---|---|---|
| P1 | about 0.2 m | 1.3 m | 8 Mar 2027 |
| P2 | about 0.6 m | 2.6 m | 8 Mar 2027 |
| P3 | about 2.8 m | 5.3 m | 8 Mar 2027, end state 2 Aug 2027 |
| P4 | about 5 m | 8.1 m | P3 part as P3, the rest ~4 months after a later decision |
| P5 | about 6 m | 10.0 m | as P4 |

### PT_SERVICE_CUTS — the savings packages as rules the timetable can be cut with
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

### CYCLING_INFRASTRUCTURE — cycle infrastructure inside the city, from OpenStreetMap
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

### CYCLE_NETWORK_PLAN_2021 — the city's cycle network plan, digitized
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

### WEATHER_DAILY — DWD station 03668 Nürnberg
count_date, temp_min_c, temp_max_c, temp_mean_c, rain_mm, sunshine_hours, cloud_cover_pct (oktas converted to %), snow_depth_cm, wind_mean_ms, source (`historical` = quality-checked, through 2025-12-31; `recent` after). 2025-01-01 to 2026-10-27.

### BIKE_COUNT_STATIONS — the 12 permanent bicycle counters
station (RZG001–RZG012), station_name, site_id, lat, lon, bezirk_no, district_no, in_nuernberg, first_data, last_data, note. Königstor (RZG001) is out of service since April 2024.

### BIKE_COUNTS_DAILY — one row per counter per day
count_date, station, dir_in, dir_out, total, zero_reported, temp_min_c, temp_max_c, rain_mm, sunshine_hours, cloud_cover_pct. 2025-01-01 to 2026-10-27. The counter pages report an outage as 0; such days have `total` empty and `zero_reported = 1`. Directions are labeled only "in" and "out". Seewiesenweg (RZG004) stops in Nov 2025, Kornburger Straße (RZG012) in Jun 2026.

The counts are read from the city's public Eco-Counter pages when the dataset is built (`scripts/build_nuernberg_dataset.py`; `--skip-bike-counters` leaves them out). There is no API and no stated licence.

### ROADWORKS — SÖR's planned and ongoing works in the street
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

### ROADWORK_PERMITS — street-use permits for works (Sondernutzung)
permit_no, applicant, reason, utility, street, section, applied_date, start_date, end_date, status (`ausgegeben`, `in Bearbeitung`, `genehmigt`), centroid, bezirk_no, district_no, shape_wkt (LINESTRING).

### ROADWORK_DIVERSIONS — diversions
diversion_id, name, kind (`Radumleitung` = cycle-path closure with diversion, `MIV-Umleitung` = motor traffic), start_date, end_date, centroid, bezirk_no, district_no, shape_wkt.

## Joins
- Area rollups by location: `X.district_no = DISTRICTS.district_no` for stops, project stations, cycle segments, counters.
- Departures per stop: `VGN_STOP_TIMES st JOIN VGN_TRIPS t ON st."trip_id" = t."trip_id" JOIN VGN_ROUTES r ON t."route_id" = r."route_id"`, filtered to the services running on the reference weekday, Wednesday 21 Oct 2026: `VGN_CALENDAR` with `wednesday = 1` and `DATE '2026-10-21'` between `start_date` and `end_date`, plus the services added (`exception_type = 1`) and minus those removed (`exception_type = 2`) on that date in `VGN_CALENDAR_DATES`. The reference Saturday (for the service cuts, from v6) is Saturday 24 Oct 2026, with `saturday = 1`, filtered the same way.
- Service cuts: `PT_SERVICE_CUTS."line" = VGN_ROUTES."route_short_name"`, with `day_type` `mon_thu` for the reference weekday and `sat` for the reference Saturday (see the table for how each rule cuts trips).
- Capacity offered: add `JOIN VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode" LEFT JOIN LINE_CAPACITY l ON l."line" = r."route_short_name" AND l."line_mode" = r."line_mode"` and `SUM(COALESCE(l."capacity_per_trip", v."capacity_per_trip"))` instead of `COUNT(*)`.
- Demand: `DISTRICT_POPULATION` and `DISTRICT_EMPLOYMENT` join on `district_no`. `DISTRICT_HOUSING` and `DISTRICT_PROFILE` join on `district_no` and `year`.

## Walking distance (Exasol SQL)
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

## Example
```sql
SELECT s."station_name", d."district_name", AVG(b."total") AS avg_daily
FROM NUERNBERG_DATASET.BIKE_COUNTS_DAILY b
JOIN NUERNBERG_DATASET.BIKE_COUNT_STATIONS s ON s."station" = b."station"
JOIN NUERNBERG_DATASET.DISTRICTS d ON d."district_no" = s."district_no"
WHERE b."rain_mm" > 1 AND b."total" IS NOT NULL
GROUP BY 1, 2 ORDER BY 3 DESC;
```

## Known gaps (say them)
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
