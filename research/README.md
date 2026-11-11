# Research

The background behind the growth (v4), the scenarios and their timing (v5), the savings package (v6), the assistant (v7) and the construction years in the corridor briefings. The research was done in German and English across official sources: the City of Nürnberg (Amt für Stadtforschung und Statistik, Verkehrsplanungsamt, Stadtrat documents), VAG, VGN, the Zweckverband StUB, DB and the Bavarian state. Each file marks what was verified on the source page and what was seen only in search results.

| File | What's in it | Used by |
|---|---|---|
| [urban-planning.md](urban-planning.md) | The model (method and definitions) and, per dashboard version, the question it answers and what to look at. No results: the dashboards compute them live | v1–v7 |
| [district-growth.md](district-growth.md) | Sources for growth: the M558 forecast for 2033 and the previous M529 forecast per Stadtteil, which jobs data exist per area (2005, and 2019–2024 since the update of 6 Nov 2026), the city's new-build projects and where they are | v2, v4, v5 |
| [plans-facts.md](plans-facts.md) | Nürnberg's current mobility projects and proposals, as facts with sources: transit, cycling, major construction, politics and budget | v5, v6, corridors |
| [plans-research.md](plans-research.md) | The same research as an assessed summary: what is funded, what is stalled, what it means per area | v5, corridors |
| [timing-and-construction.md](timing-and-construction.md) | How to measure when rail reaches each new-build project and how much tram service sits next to track works, with the SQL; the published track closures and what the major works are. No results | v5, corridors |
| [vag-cuts-2027-notes.md](vag-cuts-2027-notes.md) | The city's proposed VAG service cuts (packages P1–P5, P3 line by line): how the council document is built, how its statements became the rules in `data/source/pt_service_cuts.csv`, the approximations and corrections. No results | v6, v7 |
| [pt-projects-notes.md](pt-projects-notes.md) | Per project: stations, opening years, frequencies, behind `data/source/pt_projects.csv` | v5 |
| [cycling-coverage.md](cycling-coverage.md) | The cycling data (OSM network, counters, the 2021 plan), the path-type weights and what the cycling dashboard looks at. No results | cycling |
| [assistant-context.md](assistant-context.md) | The context pack the v7 assistant reads with every question: role and rules, data model, the model and the research above. Regenerate with `python3 scripts/build_assistant_context.py` | v7 |

The context pack repeats the other files in one document. When you change the research, regenerate it.
