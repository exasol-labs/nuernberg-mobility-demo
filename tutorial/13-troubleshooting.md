# 13 · Troubleshooting

Start with:
```bash
exakit status
```
Then describe the problem to your agent with the facts: "`exakit status` says …, the dashboard shows …". It can run the healthcheck and read the app's logs on Dash Server, and it changes nothing in the database.

## The database hangs, or `exakit status` says "conflict"

**Symptom:** queries hang or fail with "SSL: UNEXPECTED_EOF_WHILE_READING" or "Connection reset by peer". Dashboards show an error, and `exakit status` reports the runtime as `conflict` or not running.

**Fix:** restart the kit.
```bash
exakit stop && exakit start
exakit status
```

## Too many connections

**Symptom:** queries fail with "license limit of 20 parallel connections" after several deploys. Dash Server keeps idle sessions for each deployed app.

**Fix:** wait a few seconds and retry. If that doesn't help, restart the kit (`exakit stop && exakit start`).

## MCP servers missing

**Symptom:** your agent has no `dash-server` tools, or no `exasol` server, so it can't build dashboards or run SQL. Check with `/mcp` in Codex or Claude Code.

**Fix:**
```bash
exakit mcp-doctor        # what is wrong with the MCP setup
exakit mcp-setup         # register or repair the exasol and dash-server servers for your AI clients
```
Then quit your agent and start it again (`codex` or `claude`) so the tools load. If the dash-server add-on isn't installed:
```bash
exakit marketplace dash-server
exakit mcp-setup
exakit start
```
If the `exasol` server is registered but times out, the database is usually down: see [the section above](#the-database-hangs-or-exakit-status-says-conflict).

**Codex** may ask for approval before it calls an MCP tool. Approve the `exasol` and `dash-server` tools for the session.

## The agent builds an artifact or an HTML page instead of a dashboard

Every dashboard in this tutorial runs on Dash Server. Say "Build it on Dash Server with the dash-server tools", and check that the tools are loaded (see [MCP servers missing](#mcp-servers-missing)).

## Building or reloading the data

- **`python3: command not found`:** use the starter kit's own Python, `~/.exasol-starter-kit/pyexasol-venv/bin/python3` (on Windows `pyexasol-venv\Scripts\python.exe` in the same folder). The scripts need only the standard library.

`scripts/build_nuernberg_dataset.py` is safe to rerun: files already downloaded are kept (`--force` downloads again), and the tables are built again.

- **The cycle network:** it isn't downloaded; the build reads the OpenStreetMap snapshot in `data/source/osm_cycling_ways.json.gz`. Only `--refresh-osm` asks the public Overpass servers for a new one. If they answer 502, 504 or time out, they are at capacity: the snapshot is kept, try again later.
- **The bicycle counters fail:** the script reads the city's Eco-Counter pages, which can change without notice. It reports the failure at the end and carries on; the build then skips `BIKE_COUNT_STATIONS` and `BIKE_COUNTS_DAILY`, and everything else works. `--skip-bike-counters` leaves them out on purpose.
- **A newer VGN timetable:** the feed is refreshed about every quarter. If your download no longer covers Wednesday 21 Oct 2026, pick a Wednesday inside its date range and tell your agent (see [AGENTS.md](../AGENTS.md)).

`exakit data-load` skips tables that are already loaded. To reload one table, for example after you rebuilt the CSVs or a load was interrupted, drop it first and load its file again. The `starter-kit` profile of `exapump` has write rights; the agent's MCP login doesn't, so you run this yourself:
```bash
python3 scripts/build_nuernberg_dataset.py
exapump sql -p starter-kit "DROP TABLE NUERNBERG_DATASET.DISTRICTS"
exakit data-load "$PWD/data/nuernberg-dataset"
```
Tables that are still loaded are left alone; the dropped one is loaded again.

If `exakit data-load` waits without loading anything (for example when run from a script, where it can't ask its questions), load the files one by one with exapump instead:
```bash
exapump sql -p starter-kit "CREATE SCHEMA IF NOT EXISTS NUERNBERG_DATASET"
for f in data/nuernberg-dataset/*.csv; do
  t=$(basename "$f" .csv | tr a-z A-Z)
  exapump upload -p starter-kit -t "NUERNBERG_DATASET.$t" "$f"
done
```
This creates each table from its file; drop a table first if it already exists. Don't load a file on top of an existing table: rows are appended by column position, which can duplicate rows or put values in the wrong columns.

## The SÖR roadworks fail

The roadworks come from the city geoportal, which is sometimes slow or busy. The build script lists what it couldn't download at the end. Rerun `python3 scripts/build_nuernberg_dataset.py`: files already downloaded are kept, only the missing ones are fetched. Without the SÖR files the build skips the three `ROADWORK*` tables.

## The digitized cycle network plan

`CYCLE_NETWORK_PLAN_2021` is built from `data/source/cycle_network_plan_2021.csv`, which is in the repo. You don't need to run `scripts/digitize_radnetz_2021.py`: it is the maintainer's tool that made the CSV from the city's PDF map, and it needs PyMuPDF and numpy.

## SQL fails with "object … not found"

Column names in `NUERNBERG_DATASET` are lowercase and must be double-quoted: `SELECT "district_no" FROM NUERNBERG_DATASET.DISTRICTS`. Unquoted `district_no` fails with "object DISTRICT_NO not found". AGENTS.md tells the agent this; if it happens anyway, point it there.

## v6: `PT_SERVICE_CUTS` is missing

You loaded the data before the service cuts were added to the repo. Pull the latest version, run `python3 scripts/build_nuernberg_dataset.py` again (it keeps the files it already downloaded) and load `data/nuernberg-dataset` again as in [chapter 2](02-load-data.md). You should then see `PT_SERVICE_CUTS` and `PT_SAVINGS_PACKAGES`. The rules come from `data/source/pt_service_cuts.csv`; you don't need PyMuPDF or the PDF to build them.

## Blank page after a deploy

**Hard-reload** the page (Cmd+Shift+R on macOS, Ctrl+Shift+R on Windows and Linux). If it stays blank, ask your agent to run the healthcheck and read the app's logs. A common cause is a callback that returns no value on the first load.

## v7: the assistant fails

| On the page | Fix |
|---|---|
| A setup line instead of the input | Put the key in `secrets/openai_api_key` and create the link (see [chapter 10](10-v7-assistant.md#before-you-start-the-openai-key)), then reload. |
| The key is rejected | The key is wrong or revoked. Replace it in `secrets/openai_api_key` and reload. |
| No credits | Add credits to the account that owns the key, at platform.openai.com → Billing. |
| Rate limit | Wait a minute, then ask again. |
| An answer ends with a database error | The database is down: see [the first section](#the-database-hangs-or-exakit-status-says-conflict). |

Don't paste the key into a chat to help the agent fix it. The key only belongs in `secrets/openai_api_key`.

## Maps stay empty in a headless browser

If you or your agent test dashboards in a headless browser, the maps need WebGL. Without a GPU, start Chrome with software WebGL (SwiftShader). Use a separate browser profile for tests.
