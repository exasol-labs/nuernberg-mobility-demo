<h1 align="center">Nürnberg Mobility Demo</h1>

<h3 align="center">A hands-on tutorial for AI-assisted analytics on Exasol Personal</h3>

You load open data about Nürnberg into a local [Exasol](https://www.exasol.com) database on your laptop. Then you work with an AI coding agent, Codex or Claude Code, to build a series of live dashboards that answer one planning question, step by step:

> **How well is each area in Nürnberg covered by the current public transport offering, and how do planned activities change that?**

The first maps look convincing: clear colors, plausible numbers, the SQL right there on the page. But how far can you trust what a dashboard shows you? Somewhere in the first answers is a mistake that looks perfectly reasonable. Spotting it takes a bit of local knowledge and a careful look at the SQL, and finding it before you build on it is part of the tutorial. Then comes the twist: the growth is already under way, and the rail that should serve it is still being built. Lichtenreuth is growing fast now, and its tram is planned for 2030. And the city now has to save money on the service too. The chapters follow that thread from today's map to the growth, the projects and when they arrive, the proposed service cuts, cycling, and finally a briefing per growth corridor.

You describe what you want to see and why; the agent writes the SQL and the dashboards. The only prerequisite is the **[Exasol Personal Local Starter Kit](https://github.com/exasol-labs/exasol-personal-local-starterkit)**. The data comes from public sources (VGN, the City of Nürnberg, DWD, OpenStreetMap); one script in this repo downloads it and builds the tables.

## Get the repo

```bash
git clone https://github.com/exasol-labs/nuernberg-mobility-demo.git
cd nuernberg-mobility-demo
```

Then follow the path below, starting with the starter kit in chapter 1.

## The path

1. [Set up the Exasol Personal Local Starter Kit](tutorial/01-setup-starter-kit.md): database, Dash Server, your agent connected over MCP
2. [Load the Nürnberg data](tutorial/02-load-data.md): download the public sources and build the tables
3. [First questions](tutorial/03-first-questions.md): get to know the data with your agent
4. [v1: a first map](tutorial/04-v1-residents.md): how well is each area served today?
5. [v2: residents and jobs](tutorial/05-v2-jobs.md): who is served best, and who worst?
6. [v3: can we trust this map?](tutorial/06-v3-can-we-trust-it.md): look again before you build on it
7. [v4: homes before trams](tutorial/07-v4-growth.md): growth to 2033 and where it has already started
8. [v5: rail and tram projects, and when they arrive](tutorial/08-v5-scenarios.md)
9. [v6: the savings package](tutorial/09-v6-savings-package.md): the city's savings packages P1–P5 on the city as planned for 2027, and the areas that lose the most
10. [v7: an assistant on the page](tutorial/10-v7-assistant.md) (needs an OpenAI API key)
11. [Cycling: the 2021 plan, five years on](tutorial/11-cycling.md)
12. [Corridor briefings](tutorial/12-corridor-briefings.md): the whole story, one growth corridor at a time, with the tram-track works
13. [Troubleshooting](tutorial/13-troubleshooting.md)

## Repo map

| Path | What it is |
|---|---|
| [tutorial/](tutorial/) | The chapters above |
| [AGENTS.md](AGENTS.md) | Standing instructions for the agent: ground rules, the data, building on Dash Server |
| [data/](data/README.md) | The table reference, the data model, sources and licences, and the curated tables in `data/source/` |
| [research/](research/README.md) | The research behind the forecast, the scenarios and the service cuts, and the context pack for the v7 assistant |
| [secrets/](secrets/README.md) | Where your OpenAI key goes (gitignored) |
| [scripts/](scripts/) | `build_nuernberg_dataset.py` downloads the sources and builds the dataset (its steps `fetch_nuernberg_sources.py` and `prepare_nuernberg_dataset.py` also run on their own); `fetch_nuernberg_statistik.py` refreshes the curated statistics tables (jobs, housing, benefits, cars) in `data/source/`; `digitize_radnetz_2021.py` and `digitize_vag_cuts_2027.py` turn the city's PDFs (the 2021 cycle plan, the proposed service cuts) into the curated tables (maintainer scripts, need PyMuPDF; their output is committed); `build_assistant_context.py` regenerates the v7 assistant's context pack |

## About the data

The VGN data is the **scheduled** timetable. It has no passenger counts, delays or crowding, so "well served" means *capacity offered*, not use. Jobs per area are employees subject to social insurance at their workplace (2024), with no forecast. Residents after 2024 are a model built on the city's Stadtteil forecast for 2033.

## Sources and links

- **Data:**
  - VGN GTFS timetable, CC BY 3.0 DE
  - City of Nürnberg, Amt für Stadtforschung und Statistik: statistical Bezirke, Bezirksatlas, forecast reports M558 and M529, Statistischer Monatsbericht 10/2006
  - City of Nürnberg geoportal: new-build projects; SÖR construction coordination (planned works, permits, diversions)
  - City of Nürnberg, Verkehrsplanungsamt: Radwegenetzplan 2021 (PDF map, digitized in this repo)
  - VAG open data: vehicle capacities
  - Deutscher Wetterdienst: daily climate data
  - OpenStreetMap, © OpenStreetMap contributors, ODbL

  Details and licences are in [data/README.md](data/README.md).
- **Tools:** [Exasol Personal](https://www.exasol.com/personal/) · [Starter Kit](https://github.com/exasol-labs/exasol-personal-local-starterkit) · [Dash Server](https://github.com/exasol-labs/dash-server) · [Exasol MCP server](https://github.com/exasol/mcp-server)
