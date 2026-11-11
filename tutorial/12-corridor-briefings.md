# 12 · Corridor briefings: the whole story in one page

**Goal:** `nuernberg-corridor-briefings`: one page per growth corridor that brings the series together. For each corridor it shows who moves in and when, what public transport they get and when it arrives, what is under construction in between (the only place in the tutorial where the tram-track works come in), what the proposed service cuts take away, and what cycling adds. You need v6 from [chapter 9](09-v6-savings-package.md) and the cycling dashboard from [chapter 11](11-cycling.md); v7 is optional.

## The idea

Each chapter answered one part of the planning question for the whole city. A planner, a council committee or a district meeting usually asks about one place: "what happens in our part of town?" The corridors from [chapter 7](07-v4-growth.md) are where the series' findings meet:

| Corridor | Areas | Known from the sources | What to look for |
|---|---|---|---|
| **South-east: Lichtenreuth** | 41/42/43, Hasenbuck | Lichtenreuth tram from 2030 (risk 2031), track works from 2027 | How fast do residents and jobs grow? Does the tram bring capacity per person back to the 2024 level? |
| **West: Tiefes Feld and the Quelle site** | Großreuth b. Schweinau, Höfen, Eberhardshof, Muggenhof | Tiefes Feld first occupied 2027, U3 to Gebersdorf from 2028. The former Quelle site in Eberhardshof gets 2,300 homes; S9 on the Nordring is a study item with no date | Does rail arrive with the residents? Which area is left out? |
| **North-west: Wetzendorf** | Wetzendorf, Westfriedhof | New-build projects from v4 | Which rail project reaches them, and when? |
| **North: the Knoblauchsland** | Kraftshof/Neunhof, Boxdorf, Großgründlach | StUB to Erlangen from 2031 (risk 2032), not funded | How much do these areas gain once the StUB runs, and how certain is that? |

**What's in the way: the tram-track works.** The planning series leaves construction out; the briefings bring it in. The city's construction coordination (SÖR Baukoordination) publishes every planned and ongoing work in the street with its dates and outline (`ROADWORKS`). Tram-track works are flagged with `is_tram_track = 1`: track renewals, the new lines themselves, and the rebuilding of the two hubs, Plärrer and the Hauptbahnhof forecourt. A tram stop within 50 m of an active track work is likely to see diversions, replacement buses or closures while the work lasts, so its capacity is **at risk**, not lost. Only the planned track closures (`kind = 'Schienenstreckensperrung'`) say outright that trams stop; one runs from 2 January to 30 November 2027 from Plärrer through Steinbühl and Gibitzenhof to Landgrabenstraße. Tram-track works are planned years ahead, most other works only a year or two, so later years look quieter than they will be. The method and SQL are in [research/timing-and-construction.md](../research/timing-and-construction.md).

A briefing is only useful if every number on it can be traced. So the page reuses the model of the earlier dashboards rather than restating their results, and the "SQL executed" foldout lists every statement as before.

## The prompt

```text
Build a final dashboard, nuernberg-corridor-briefings, titled "Nürnberg Growth Corridors", in the same look as the series.

I want one briefing per growth corridor: the south-east (Lichtenreuth group and Hasenbuck), the west (Großreuth b. Schweinau, Höfen, Eberhardshof, Muggenhof), the north-west (Wetzendorf, Westfriedhof) and the north (Kraftshof/Neunhof, Boxdorf, Großgründlach). Let me pick a corridor; show a small map of its areas and these sections:

1. Who moves in, and who works there: residents counted 2023-2025 and modelled to 2033, the new-build projects with homes and first-occupancy year, homes permitted and completed since 2020, and jobs 2019 to 2024.
2. What they get: capacity per person against the 2024 city average, for 2024 and 2033, with no projects, the funded projects and the funded and dated projects, using the v5 model.
3. When it arrives: for each large new-build project, the year rail reaches it and the gap to its first occupancy, as in v5.
4. What's in the way: the tram-track works in the corridor per year, 2026 to 2035, and the share of the corridor's capacity offered at tram stops within 50 m of an active track work. Call that service at risk, not a closure, and say how far ahead the city plans its works.
5. What the cuts take away: capacity per person today and under each proposed savings package, on the weekday and on the Saturday, as in v6, and the lines in the corridor that the cuts touch.
6. What cycling adds: the corridor's cycle network today, the km the 2021 plan adds, and the cycle-path works planned.

End each briefing with three lines in plain words: the main finding, the main risk, and what the data can't say. Write them from the numbers on the page, not from memory, and keep the caveat line and the "SQL executed" foldout as in every dashboard.

Show me the briefing for the south-east first, with the SQL behind each section.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-corridor-briefings

- **South-east.** Does the briefing tell the timing story in order: homes first occupied, residents counted, track works from 2027, tram in 2030? Where does the Lichtenreuth group end in 2033 against its 2024 level with no projects, with the funded ones and with its own tram? How much of the gap does the tram close?
- **West.** How does Großreuth b. Schweinau change between no projects and the funded ones, and which project makes the difference? Where does Eberhardshof end up? Is the Quelle site called out?
- **North-west.** How much do Wetzendorf and Westfriedhof lose by 2033 against the 2024 city average? Is any dated project planned for them, and does the briefing say so plainly?
- **North.** How much does Kraftshof/Neunhof gain once the StUB runs? Does the briefing make clear that this depends on an unfunded project, with construction from 2029 and a first tram in 2031 or later?
- Pick any number on a briefing. Can you find the statement that produced it in "SQL executed"?

## Understand it

```text
For the corridor briefings, which sections rest on counted data, which on the city's plans and which on our own model? If a council member quotes one number from the south-east briefing, which one is the most solid and which one needs the most explanation?
```

## Your turn

- **Add a corridor.** The inner south (Gibitzenhof, Steinbühl, Galgenhof) isn't a growth corridor, but it lies on the tram axis of the planned track closure of 2027, from Plärrer to Landgrabenstraße. Ask for a briefing that fits it.
- **Ask the assistant.** With v7, ask: "Write me a half-page briefing for the west corridor for a district meeting, and cite every number." Compare its text with the page.
- **Keep it current.** When the next VGN timetable, Bezirksatlas or SÖR update comes out, reload the data and see which lines of the briefings change.

## What the data can't tell you

Everything from the earlier chapters still holds: scheduled service, not passengers; jobs held at the 2024 count; residents after 2024 modelled from a Stadtteil forecast; project dates and frequencies from public sources; roadworks planned only a few years ahead; service cuts that are a proposal until the council decides; a cycle network from OpenStreetMap and a digitized 2021 plan. A briefing makes the numbers easier to quote. Keep the caveats on the page.

Next: [13 · Troubleshooting](13-troubleshooting.md)
