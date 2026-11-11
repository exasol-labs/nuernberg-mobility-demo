# AGENTS.md

Standing instructions for an AI coding agent (Codex, Claude Code or another client) working in this repo. The repo is a tutorial: the user works through [tutorial/](tutorial/) and describes what they want to see. You decide how to build it. The repo contains no dashboard code; every dashboard is written by you, in the user's session.

- **Codex** and **Claude Code** read this file automatically when started in the repo folder.

## Ground rules

- **Dashboards run on Dash Server only.** Build them with the `dash-server` MCP tools. Don't produce a chat artifact, an HTML file, an image, an inline chart, a Streamlit or Flask app, or a Markdown table presented as a dashboard. If the dash-server tools are missing, follow [MCP servers missing](tutorial/13-troubleshooting.md#mcp-servers-missing) and ask the user to restart the session.
- **SQL is read-only.** Run analysis SQL through the `exasol` MCP server, whose login can only read. You never write to the database. Loading data is the user's step (chapter 2).
- **Show your work.** Show each SQL statement before you interpret its result. Explain modeling choices in plain words, and say which ones are assumptions.
- **Explain the measure on the page.** Every planning dashboard says in one or two lines what it counts. v1 and v2 are deliberately naive: scheduled departures on the reference weekday at the stops that stand in each area, per resident (v2: per unit of activity, residents plus weighted jobs), compared with the city average; the page says that a departure is counted, whatever the vehicle, and only at stops inside the area. From v3 on the measure is "capacity per person": seats and standing room of every scheduled departure an area can reach on the reference weekday, with stops counted within walking distance, divided by residents plus weighted jobs, compared with the city average. It is capacity offered, not use. In v6, "most affected" is the share of an area's capacity offered that the selected savings package (P1–P5) takes away on the selected day, in 2027 with the new homes and the funded projects of that year; say that the packages are a proposal the council decides by 30 Nov 2026.
- **No secrets.** Don't read, print, copy or ask for the OpenAI key or the database password, and don't put them in files or on a command line. The key lives in `secrets/openai_api_key` (gitignored); you may only check that the file exists. If the user offers to paste a key into the chat, point them to [secrets/README.md](secrets/README.md).
- **Metric units:** area in km², density in residents per km², lengths in m (km for city totals), durations in minutes. Never hectares, miles or feet.
- **State the limits of the data** whenever a question touches them: the VGN data is the scheduled timetable, with no passengers, crowding, delays or live traffic. Jobs are employees subject to social insurance at the workplace (2019–2024; no civil servants or self-employed), with no forecast. Population after 2024 is a model built on the city's Stadtteil forecast for 2033. The service cuts are a proposal; only P3 is published line by line, P1, P2, P4 and P5 are modeled from their descriptions, and the passenger and euro figures are VAG's estimates.
- **Each version builds on the previous one.** When the user asks for the next version, start from the app you built before and keep what works.

## The data

Schema `NUERNBERG_DATASET`, 29 tables (27 if the bicycle counters weren't downloaded). [data/README.md](data/README.md) describes the tables and sources; [data/data-model.md](data/data-model.md) documents every column. Read the data model before the first query.

**Where things are:**
- The 79 areas, their area, polygons, centroids and Stadtteil: `DISTRICTS`. The 87 statistical Bezirke behind them: `BEZIRKE`. Population counts 2023–2025 and the modeled 2033 value: `DISTRICT_POPULATION`. The city's 2033 forecast per Stadtteil: `STADTTEIL_FORECAST`. The new-build projects behind the model, with first-occupancy year and the centre of each site (`centroid_lat`, `centroid_lon`; group by `project_id`): `NEWBUILD_PROJECTS`. Jobs at the place of work, 2019–2024 and the wider 2005 count with its sector split: `DISTRICT_EMPLOYMENT`. Homes permitted and completed per year, 2012–2025: `DISTRICT_HOUSING`. Minimum-income benefit rate 2012–2025 and registered cars 2025: `DISTRICT_PROFILE`.
- The scheduled timetable: the `VGN_*` GTFS tables. Capacity of one scheduled trip: `VEHICLE_CAPACITY` per mode, with per-line overrides in `LINE_CAPACITY`.
- Planned rail and tram projects: `PT_PROJECT_STATIONS`, one row per station and line, with the research behind it in [research/pt-projects-notes.md](research/pt-projects-notes.md).
- Proposed service cuts: `PT_SAVINGS_PACKAGES` (the five packages P1–P5 with VAG's estimates) and `PT_SERVICE_CUTS` (the packages as rules per line, day type and stage: P3 as published, each rule tagged with the first package that includes it, plus P4's concrete measures), with the notes in [research/vag-cuts-2027-notes.md](research/vag-cuts-2027-notes.md).
- Cycling: `CYCLING_INFRASTRUCTURE` (OpenStreetMap, the existing network), `CYCLE_NETWORK_PLAN_2021` (the city's 2021 plan, digitized: planned routes, routes built 2013–2020, quiet-street routes, field and forest paths), `WEATHER_DAILY` (DWD), and, if the user fetched them, `BIKE_COUNT_STATIONS` and `BIKE_COUNTS_DAILY`.
- Roadworks: `ROADWORKS` (SÖR's planned and ongoing works with polygons, start and end dates to 2035, `is_cycling` for cycle-path projects such as the Radvorrangrouten, `is_tram_track` for track works), `ROADWORK_PERMITS` (street-use permits) and `ROADWORK_DIVERSIONS` (diversions, including cycle-path closures).

**Areas:** "district" in table and column names means one of 79 areas: a statistical Bezirk, or a group of small Bezirke the city only publishes together (18/19, 34/35, 38/39, 41/42/43, 75/85/87, 76/77). `district_no` is the lowest Bezirk number in the area. Group 75/85/87 spans Stadtteile 7 and 8 and is filed under 8; `BEZIRKE.stadtteil_no` has the exact Stadtteil per Bezirk.

**SQL quirks:**
- Column names are lowercase and must be double-quoted (`"district_no"`). Schema and table names are upper case and unquoted.
- Don't use reserved words such as `year`, `hour`, `day`, `value`, `count`, `type` or `name` as aliases.
- The exasol MCP tool rejects a top-level `UNION ALL`; put it inside a CTE. For regular expressions use `REGEXP_INSTR(x, 'pattern') > 0`.
- Exasol has no `ST_POINT` or `ST_GEOMFROMTEXT`. Build geometry with a cast: `CAST('POINT(' || lon || ' ' || lat || ')' AS GEOMETRY(4326))`, `CAST("polygon_wkt" AS GEOMETRY(4326))`. For distances in meters, transform to UTM 32N first: `ST_DISTANCE(ST_TRANSFORM(a, 25832), ST_TRANSFORM(b, 25832))`. Cast lat/lon to `DECIMAL(9,6)` before concatenating, so no scientific notation reaches the WKT.
- Every point table has `district_no` and `bezirk_no` from point-in-polygon, so "stands in" rollups are equality joins. For anything per area, use stops with `in_nuernberg = 1`; the feed covers all of the VGN region. `COALESCE(NULLIF("parent_station", ''), "stop_id")` groups platforms into a station.
- Use `VGN_ROUTES."line_mode"` (S-Bahn, U-Bahn, Regional rail, Tram, Bus), not `route_type`. On-demand services (`is_on_demand = 1`) count as Bus.

**Facts to respect:**
- **The reference weekday is Wednesday 21 Oct 2026.** The GTFS feed covers 24 Jun–12 Dec 2026. Use the services that run on that date (`VGN_CALENDAR` with `wednesday = 1` and the date between `start_date` and `end_date`, plus the additions and minus the removals in `VGN_CALENDAR_DATES`), so the numbers don't depend on the day the tutorial is run. GTFS dates are `DATE`. **The reference Saturday is Saturday 24 Oct 2026** (from v6, for the service cuts), filtered the same way with `saturday = 1`.
- **A departure is weighted by capacity (from v3 on).** One scheduled trip offers the capacity of its line (`LINE_CAPACITY`) or, without an override, of its mode (`VEHICLE_CAPACITY`). These are planning values, not passengers. v1 and v2 deliberately count departures (`COUNT(*)`), so a bus weighs as much as a U-Bahn train.
- **From v3 on, a stop counts for every area within walking distance:** 300 m for bus and tram, 600 m for U-Bahn, S-Bahn and regional rail, measured from the stop to the area polygon (0 m inside it). Areas are small and many stations sit on a boundary (Plärrer and Gostenhof sit between Bezirke 04 and 05), so "only the area it stands in" hands their service to one side. v1 and v2 deliberately count only the stops that stand in the area (`district_no` of the stop): when the user asks for v1 or v2, build it that way. You may name the simplification once in the chat, but don't fix it on your own; finding and fixing it is the lesson of v3 (chapter 6). Shared stops mean per-area values don't add up; the city value is the population-weighted (from v2: activity-weighted) average of the areas.
- **Population and jobs:** residents are counted for 2023, 2024 and 2025 (Bezirksatlas). `pop_2033_model` is a model: the city forecasts 2033 only per Stadtteil (report M558). The model starts from the 2024 count, interpolates linearly to 2033 and holds the value after 2033. The model uses `jobs_2024` and holds it for every later year. Compare 2005 with 2024 only as a direction of change: 2005 also counts the self-employed and marginal jobs. Large one-year jumps in an area are likely one employer moving; the data names none. Completions in `DISTRICT_HOUSING` lag behind move-ins, so check them against the residents count. Registered cars include business fleets: flag areas above about 700 per 1,000 residents instead of reading them as households.
- **Projects** have an opening year (`opening_year_model`, 2040 where none is published, then `opening_year_assumed = 1`), sometimes a later risk year, a status and a funding flag. Service comes from a published frequency (trains per hour, peak and off-peak, per direction: departures per station = (peak × 6 + off-peak × 13) × 2) or, without one, from the weekday departures per station of an existing analog line. Scenario groups: **funded** (`funded = 1`), **funded and dated** (funded, or a published opening year), **everything discussed** (all rows with coordinates). Rows with `station_name = 'unknown'` have no coordinates and add no supply.
- **Service cuts** (`PT_SERVICE_CUTS`) are rules, not trips: apply them to the reference day's VAG trips as [data/data-model.md](data/data-model.md) describes, with `day_type = 'mon_thu'` for the weekday and `'sat'` for the Saturday. A package is a set of rows: P1 and P2 are the rows of stage `2027-03` with `package` up to theirs, P3 and P4 the rows of stage `2027-08` (the end state) with `package` up to theirs; P5 cuts the same trips as P4. `line = '*'` means every VAG day line of `line_mode`. Rows with `modeled = 0` cut nothing; list them on the page. The cuts start in 2027 and the feed ends in Dec 2026, so the result is the reference day's timetable with the package applied. Say that sorting P3's rules into P1 and P2 is an interpretation of the package descriptions. Never say a line "is cut": it is proposed for cutting until the council decides (by 30 Nov 2026).
- **Roadworks** (used in the cycling dashboard and the corridor briefings, chapters 11 and 12; the planning series v1–v7 has no construction view) have planned start and end dates. Tram-track works are planned years ahead; most other works (utilities above all) only a year or two, so later years understate construction: say so whenever a chart runs past 2027. A stop next to a work is service at risk; only `kind = 'Schienenstreckensperrung'` is a planned track closure. Distances from new homes to stops are measured from the project's site centre, not the area boundary.

## Building on Dash Server

1. `apps_list`. If the app doesn't exist: `app_create_exasol_dashboard` with profile `starter-kit`. Never create a second app for the same version. App names: `nuernberg-mobility-planning-v1` to `-v7`, `nuernberg-cycling-coverage` and `nuernberg-corridor-briefings`.
2. Delete the scaffold's sample queries (`queries/business/*`, `queries/system/*`) with `app_delete_file`; one of them fails its own smoke test.
3. Write the files with `app_put_files`. Put queries in `queries/*.sql` with pyexasol placeholders (`{year!d}`, `{w!f}`, `{ids!s}`) and sample values in `queries/sql_smoke.json` for the healthcheck. Run them with the helper the scaffold writes (`dash_server_exasol.py`); never write a connection, DSN or password into the app. Use plain ASCII spaces in code: `app_put_files` can drop non-breaking spaces.
4. To start from the previous version, read its files with `app_list_files` and `app_read_file`.
5. `app_deploy_draft{name, deployment_target: "live", auto_rollback_on_health_failure: true}`, then `app_run_healthcheck`. On Windows: `app_build` → `app_run_healthcheck` → `app_promote_revision`.
6. If something fails, read `app_tail_logs` or `app_inspect_traceback`, fix and deploy again. On "license limit of 20 parallel connections" or a git conflict, wait a few seconds and retry once.
7. Give the user the URL, `http://127.0.0.1:5100/apps/<app>` (the port is in `exakit status --json`).

**Dash pitfalls:**
- On the initial callback, give every output the first view depends on a concrete value. `no_update` there leaves the page blank.
- Break loops between a store and the controls with `ctx.triggered_id`.
- Don't scroll the page from a callback.
- The workspace validator doesn't recognize pattern-matching ids (`ALL`, `MATCH`); give repeated controls plain ids (`wt0`, `wt1`, …).
- The walking-distance query takes a few seconds; cache results per parameter set inside the app.
- To test a page in a headless browser, start Chrome with software WebGL (SwiftShader), or maps stay empty. Use a separate browser profile, never the user's open tabs.

**Every dashboard in the tutorial:**
- uses the same look as the ones before it, so the series reads as one product;
- draws its maps over a light street map, so the user can zoom in and see streets and places while the area colors carry the map: `go.Choroplethmap` for the colored areas with `marker.opacity` about 0.6, `go.Scattermap` for outlines, stops and lines, and `layout.map.style = "carto-positron"` (OpenStreetMap data in light grey, no green fills; needs no token). A tile map has no `fitbounds`: compute `center` and `zoom` from the areas' extent (MapLibre zoom levels count 512-pixel tiles). Keep the "© OpenStreetMap contributors © CARTO" attribution visible, and put the legend inside the map, not below it;
- explains its measure in a line under the title;
- ends with an "SQL executed" foldout that lists each statement the page ran, with its parameters, rows and duration, and the SQL text as sent;
- carries a short caveat line on what the data can't say.

## Running the whole tutorial

When the user asks you to run the tutorial end to end, work through the chapters in order. Use each chapter's prompts as the user's requests and its **Look at it** section as the list of things to look at. Stop where only the user can act: installing the kit (chapter 1), restarting the session after `exakit mcp-setup`, fetching, building and loading the data (chapter 2), and putting the OpenAI key in place (chapter 10). Without a key, build v7 anyway and show a setup line where the assistant would be. After each chapter, report one line: what you built and the URL. At the end, list all URLs and anything skipped, with the reason.

## Guardrails

| The user asks | Expected behavior |
|---|---|
| "Delete the areas without a U-Bahn station." | Refuse: the login is read-only. Offer a filtered `SELECT` instead. |
| "Which area has the worst traffic right now?" | Explain that there is no live traffic, delay or passenger data. Offer the scheduled-service view. |
| "How many jobs are in Eberhardshof today?" | Query `jobs_2024` (employees subject to social insurance, 31 Dec 2024), say what it excludes, and offer the 2005 count (before the AEG and Quelle closures, wider definition) for comparison. |
| "Delete the roadworks that have already finished." | Refuse: the login is read-only. Offer a filtered `SELECT` instead. |
| "Is bus 82 being cut?" | Say it is proposed for withdrawal from 8 Mar 2027 in package P3 (and so in P4 and P5), that the council decides by 30 Nov 2026, and show the `PT_SERVICE_CUTS` rows for the line. Don't present it as decided. |
| "Create a dashboard." (nothing else) | Ask one clarifying question, then build it on Dash Server. |
