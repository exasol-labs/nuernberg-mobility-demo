# Urban planning: how well each Nürnberg area is served by scheduled public transport

The model and the questions behind the dashboards `nuernberg-mobility-planning-v1` to `-v7` on `NUERNBERG_DATASET`, reference weekday Wednesday 2026-10-21 (and, for the service cuts in v6, reference Saturday 2026-10-24). From v3 on, the model measures scheduled service (capacity offered = departures × capacity per trip), not passengers. v1 and v2 are deliberately naive first versions (departures at the stops inside each area); v3 corrects them. No results are stored here: every value comes from the dashboards, computed live.

## The model (from v3 on)

- **Unit.** 79 areas: the 87 statistical Bezirke, with six groups of small Bezirke merged the way the city publishes their population (18/19, 34/35, 38/39, 41/42/43, 75/85/87, 76/77).
- **Supply.** Every scheduled stop event on the reference weekday, weighted by the capacity of its line (`LINE_CAPACITY`) or mode (`VEHICLE_CAPACITY`). A stop counts for every area whose polygon lies within walking distance: 300 m for bus and tram, 600 m for U-Bahn, S-Bahn and regional rail. Stops are shared, so area values don't add up to a city total; the city value is total capacity within reach divided by total activity.
- **Demand.** Activity = residents + w × jobs. Residents: the Bezirksatlas count for 2024; for later years a linear path to `pop_2033_model`, held after 2033. Jobs: employees subject to social insurance at the place of work, 31 Dec 2024, per area, held.
- **Comparison.** Each area against the 2024 city value at the same w.
- **Service cuts (v6).** The city's proposed savings packages (`PT_SERVICE_CUTS`), applied to the reference day's VAG trips: a trip is cut if any rule of the selected package cuts it. P3 is published line by line; P1 and P2 are sorted out of it and P4 adds its concrete measures. The base is 2027: residents modeled for 2027, jobs 2024, the funded projects open by 2027. Each area's capacity with the package is compared with its capacity without it, on the same day type. Method in [vag-cuts-2027-notes.md](vag-cuts-2027-notes.md).
- **Projects (v5).** From the opening year (or the risk year with pessimistic dates), each project station adds the published frequency × (6 peak + 13 off-peak hours) × 2 directions, or the weekday departures per station of the analog line, with the same walking-distance rule.

Why walking distance and not "stops inside the area": Nürnberg's areas are small and many stations sit on boundaries. Counting only the stops inside the area, an area whose U-Bahn stations sit on its border gets almost nothing and its neighbour gets all of it. With walking distance both get the line. The city value also rises, because shared stops count for every area they reach.

## v1: a first map, departures per resident (naive)

Scheduled departures on the reference weekday at the stops that stand in each area, per resident, against the city value. Deliberately naive: a departure counts the same whatever the vehicle, and a stop counts only for the area it stands in. What to look at: which areas come out low and high, and how hubs with few residents (Tafelhof, the Hauptbahnhof) behave in a per-resident measure.

## v2: residents and jobs

**Jobs data.** Employees subject to social insurance at the place of work per area, 31 Dec 2019–2024 (statistics office, business register). The model uses 2024. The older 2005 count (including self-employed and marginal jobs) stays in the data for its sector split; in 2005 Eberhardshof still included AEG and Quelle. See [district-growth.md](district-growth.md#3a-update-2026-11-06-the-20192024-count).

The dashboard adds jobs with a weight w (default 1) and the U-Bahn and tram stations on the map, and still counts departures at the stops inside each area. What to look at: how hubs move once their jobs count, and the area at the bottom. Gostenhof comes out lowest of all 79, far below its neighbour Himpfelshof on the same U1, because the Plärrer and Gostenhof U-Bahn stations stand just inside Himpfelshof.

## v3: two flaws, and the fix

v3 counts capacity per departure and every stop within walking distance (the model above). The two flaws of v1 and v2: a stop counted only in the area it stands in hands a boundary station to one side (Gostenhof and Himpfelshof), and counting departures makes a bus area such as Maiach look as well served as an inner-city area on the U-Bahn. What to look at: which areas move most from v2 to v3, and which stay low in both (robust findings).

**Who depends on it** (`DISTRICT_PROFILE`, 2025). Compare service with registered cars per 1,000 residents and the share of residents on minimum-income benefits, by quarter of areas ranked by service. Exclude areas where business fleets push registered cars above 700 per 1,000 residents. Check how much of the car difference density explains.

## v4: the forecast to 2033, if nothing is added

**Forecast.** The city's small-area forecast (M558) gives 2033 only per Stadtteil: 554,710 residents in total. Growth is concentrated where new homes are built: Westliche, Nordwestliche and Südliche Außenstadt. The other Stadtteile stagnate or shrink (see [district-growth.md](district-growth.md)). The per-area 2033 value is a model: each Stadtteil's new-build movers (M558) go to the areas with listed new homes (city WFS, at most 2 movers per listed home), the rest of the Stadtteil's change goes by residents. M558's movers are gross (many come from elsewhere in the city), so areas without new homes shrink in the model.

The dashboard holds service as it is and lets population follow the forecast. What to look at: the change in capacity per person for the city and per area by 2028 and 2033, in particular Lichtenreuth (41/42/43, the new district on the former Südbahnhof, with the Technische Universität), the western new-build areas (Tiefes Feld, the former Quelle site) and the north-west (Wetzendorf).

**Housing statistics as a check** (`DISTRICT_HOUSING`, 2012–2025). Compare homes permitted and completed per area with the residents count. Completions are recorded when the builder reports them, so they lag.

## v5: rail and tram projects as scenarios

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

## v5, continued: when rail reaches the new homes

Measured from each new-build project's site (the centre of its outline on the city's map) with the same walking distances: which new homes have no rail stop within walking distance today, and when a project brings one, against the year the homes are first occupied. Method and SQL in [timing-and-construction.md](timing-and-construction.md).

## v6: the savings package

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

## v7: ask the assistant

v7 adds an assistant to v6 (it needs an OpenAI key); [assistant-context.md](assistant-context.md) is the context pack it reads.

## Corridor briefings

The capstone (chapter 12) regroups the dashboards' views per growth corridor: the south-east (Lichtenreuth), the west (Tiefes Feld, the Quelle site), the north-west (Wetzendorf) and the north (Knoblauchsland, StUB). It adds no new model.

## Construction (corridor briefings)

The planning series has no construction view; the corridor briefings (chapter 12) bring it in. The city's construction coordination (`ROADWORKS`) lists tram-track works for the coming years. What to look at: per year, the share of the city's tram stop events at stations within 50 m of an active tram-track work, and which areas depend most on those stops. The published track closure from 2 January to 30 November 2027 covers the south-western axis from Plärrer through Steinbühl and Gibitzenhof to Dianastraße and Landgrabenstraße. The Lichtenreuth tram is itself under construction 2027–2030, the years its residents move in. The hubs follow: Plärrer 2027–2031, an extra tram track at the Hauptbahnhof 2030–2031. Most other works are planned only a year or two ahead, so later years understate construction. Method and SQL in [timing-and-construction.md](timing-and-construction.md).
