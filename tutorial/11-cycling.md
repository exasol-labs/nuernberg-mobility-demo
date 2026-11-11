# 11 · Cycling: the 2021 plan, five years on

**Goal:** `nuernberg-cycling-coverage`: the planning question asked for bikes. How much cycle network does each area have today, what did the city plan in 2021, and what is actually being built? This dashboard starts a second series in the same look; the exercises at the end are yours to build.

## The idea

Nürnberg has a cycle network plan, a building programme and a target, and this dataset has all three, which is rare:

- **Today's network** comes from **OpenStreetMap** (`CYCLING_INFRASTRUCTURE`, the ways inside the city). The city publishes no open network data. Count a two-way path for both directions.
- **The city's plan** is the Radwegenetzplan of January 2021, a PDF map that this repo has digitized (`CYCLE_NETWORK_PLAN_2021`): planned routes, decided planning, routes built 2013–2020, and recommended routes over quiet side streets.
- **What is being built** is in the city's roadworks (`ROADWORKS` with `is_cycling = 1`): cycle-path works with dates and outlines, among them the Radvorrangroute RVR 10 cycle streets in Laufamholz (2026) and the Radschnellverbindung, a fast cycle route from Nürnberg to Erlangen, in Thon.
- **The target:** in 2021 the city decided on 135 km of Radvorrangrouten (priority cycle routes) by 2030. About 1.3 km were built by the end of 2025 ([research/plans-facts.md](../research/plans-facts.md)).

Not every meter is worth the same: a separated cycle track serves cyclists better than a painted lane or a shared footpath. So the network is weighted by quality. The weights are an assumption, and the viewer should be able to change them. A starting point:

| Path type (`path_type`) | Weight |
|---|---|
| Cycle track (Radweg), cycle track along a road, cycle street (Fahrradstrasse) | 1.0 |
| Separated cycle and footpath | 0.8 |
| Painted lane (Radfahr-/Schutzstreifen) | 0.6 |
| Shared footpath (Gemeinsamer Geh- und Radweg) | 0.5 |
| Shared lane or bus lane; field or forest track | 0.3 |

There are two ways to compare areas, and they tell different stories:
- **Per person:** network per resident and job, so growth without new paths lowers an area's value over time.
- **Per km²:** network density by area, which doesn't change with the year.

The city also runs 12 permanent bicycle counters. They measure use, but only at 12 points. Their daily counts come from the city's Eco-Counter pages, which have no API and no stated licence; the build in chapter 2 reads them. If they couldn't be downloaded, the dashboard works without the counter layer.

## The prompt

```text
Start a new series with a dashboard nuernberg-cycling-coverage, titled "Nürnberg Cycling Coverage", in the same look as the planning dashboards.

I want to see how well each area is served for cycling: how much cycle network it has today, weighted by path quality, compared with the city average. Let me switch between per person (residents and jobs, with the year slider and job weight as before) and per km². Let me change the quality weights per path type, with a way to reset them. Count two-way paths for both directions.

Then show me the city's plan against it. Add the 2021 network plan as a layer: planned and decided routes, routes built 2013-2020, and the quiet-street routes as a separate, lighter layer. For each area, show how many km the plan adds and how many km of cycle-path works are planned from the selected year on. Highlight the areas that are thin today and get neither.

Show the bicycle counters on the map with their average bikes per weekday and how much heavy rain reduces them. Days a counter reports 0 are outages: leave them out.

Show me the per-person ranking next to the plan's km per area before you build the page.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-cycling-coverage

- Per person, which areas are thin? Now switch to per km². What happens to the same areas?
- Turn on the 2021 plan. Where does it add most? What does it add in the thinnest inner-city areas, and what does it rely on there instead?
- Look at the planned cycle-path works. Which areas get them? Do any of the thinnest inner-city areas get one, and as part of which project?
- Laufamholz gets RVR 10 works in 2026. Where did it stand in the public transport series (v3)? Is cycling filling a gap there?
- Hover over the counters. Which one counts the most bikes per weekday? How much does rain of 5 mm or more reduce the counts, and how much does that differ between counters?

## Understand it

```text
How did you match the 2021 plan against today's OpenStreetMap network? How much of the planned routes already lies on mapped cycle infrastructure, how do you tell which planned km are still missing, and how sure can we be, given that the plan was digitized from a PDF map?
```

## What the data can't tell you

- **Supply only:** where OpenStreetMap shows cycle infrastructure, and its type. Nothing on width, surface quality, continuity, gaps or junction safety, and mapping completeness varies by area.
- **The plan is a digitized picture:** positions are about ±10 m, the plan is from January 2021, and some planned routes are built by now.
- **Works are planned dates,** and like all roadworks they are planned only a year or two ahead.
- **Measured use at 12 points,** January 2025 to October 2026, with outages: some counters are out of service or stop part-way. Check each counter's dates before comparing. One counter can't stand for a whole area.
- **The weights are assumptions,** not an official quality scale.

## Exercises: continue the series

Each exercise is a new version. Describe what you want to see, as in the earlier chapters, and let your agent build it.

1. **The quiet-street routes.** The plan routes cyclists over quiet side streets, which OpenStreetMap doesn't count as cycle infrastructure. Should they count, and with what weight? Which inner-city areas change most if they do?
2. **Change since 2024.** As in v4 of the planning series: how much does each area's cycle network per person change as the city grows, with and without the planned works?
3. **Priority routes against the target.** Of the 135 km of Radvorrangrouten, about 1.3 km were built by the end of 2025. Which areas would the routes connect, which works in `ROADWORKS` belong to them, and how far is the programme from its target year by year?
4. **Roadworks on cycle paths.** Which cycle paths lie next to current and planned works (`ROADWORKS`, `ROADWORK_DIVERSIONS` with `kind = 'Radumleitung'`), and how much high-quality network does each area lose while they last?
5. **Weather sensitivity.** Using `WEATHER_DAILY`, compare the counters: which ones lose most on rainy or cold days, and is that a commuter or a leisure pattern?
6. **An assistant,** as in v7, with a context pack built from [research/cycling-coverage.md](../research/cycling-coverage.md) and the data model.

Next: [12 · Corridor briefings](12-corridor-briefings.md)
