# Nürnberg Cycling Coverage: how well is each area served for cycling?

The data and method behind the dashboard `nuernberg-cycling-coverage` on `NUERNBERG_DATASET`. The network is OpenStreetMap (© OpenStreetMap contributors, ODbL), retrieved 28 Oct 2026; the counters are the city's 12 permanent bicycle counters (Eco-Counter pages, Jan 2025–Oct 2026); weather is DWD station 03668 Nürnberg. No results are stored here: every value comes from the dashboard, computed live.

## The data

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

## What the dashboard looks at

- **Per person** (residents + jobs, w = 1, 2024 jobs): weighted km per 1,000 people, per area against the city value. Which areas are thinnest, and whether any have no mapped cycle infrastructure.
- **Per km²**, for comparison: dense areas can look average per km² and thin per person; outer areas with a lot of open land the other way round.
- **The 2021 plan:** km of planned and decided routes per area (both directions), against the areas thinnest per person. Quiet-street routes are a separate category, which the OSM-based view doesn't count.
- **Use:** bikes per weekday per counter, and the change on days with ≥5 mm rain.

## Caveats

- **Supply only:** mapped length and path type. Nothing on width, surface, gaps, junction safety or motor traffic.
- **Twelve counting points** can't stand for whole areas, and some of them have gaps.
- **The weights are assumptions,** not an official quality scale.
- **Planned cycling projects** are in `ROADWORKS` (`is_cycling = 1`, works with dates and polygons, e.g. Radvorrangroute RVR 10 cycle streets in 2026, the Radschnellverbindung Nürnberg–Erlangen 2028–2029). [plans-facts.md](plans-facts.md) has the programme: 135 km of Radvorrangrouten planned, about 1.3 km built by the end of 2025.
- **Closures:** `ROADWORK_DIVERSIONS` has current or planned cycle-path closures with diversions.
