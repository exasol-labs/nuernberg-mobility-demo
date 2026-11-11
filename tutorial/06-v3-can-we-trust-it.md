# 6 · v3: Can we trust this map?

**Goal:** `nuernberg-mobility-planning-v3`: v2 with a measure you can defend. It counts capacity instead of departures, and every stop within walking distance instead of only the stops inside an area. This is where "capacity per person", the measure of the rest of the series, begins. You need v2 from [chapter 5](05-v2-jobs.md).

## The idea

v1 and v2 produce numbers that look reasonable, and the page explains them. But in v2, Gostenhof, an inner-city neighbourhood on the U1, comes out as the worst served of all 79 areas, and its neighbour Himpfelshof, on the same U-Bahn line, gets 16 times as much per resident. Two neighbours on one U-Bahn line can't be that far apart. Two flaws are behind it, and every first analysis of this data makes them.

**Flaw 1: a stop counts only in the area it stands in.** Nürnberg's 79 areas are small, and many stations sit on a boundary. The U-Bahn stations Plärrer and Gostenhof stand on Fürther Straße, the border between Gostenhof and Himpfelshof, and their platforms lie just inside Himpfelshof. People in Gostenhof walk to them, but the SQL hands the whole station to one side. You can see it on the map: the station points sit on the boundary.

**Flaw 2: departures, not capacity.** `COUNT(*)` counts a bus like a U-Bahn train, though a bus carries about 90 people and a U-Bahn train about 590. You can see it in the SQL: it says `COUNT(*)`, not a sum of capacity.

**The fix:**
- **Capacity offered.** Each scheduled trip counts with the number of people it can carry (seats plus standing room): about 580 for a U2 train, 200 for a tram and 90 for a bus. `LINE_CAPACITY` has values per line, `VEHICLE_CAPACITY` per mode.
- **Walking distance.** A stop counts for every area within walking distance of it: 300 m for bus and tram, 600 m for U-Bahn, S-Bahn and regional rail, measured from the stop to the area's boundary. Areas then share stops, and the per-area values no longer add up to a city total. The city average is therefore the activity-weighted average of the areas.

**What each fix does** (reference Wednesday, 2025 residents, per resident):

| Area | Stops inside: departures | Stops inside: capacity | Walking distance: departures | Walking distance: capacity |
|---|---|---|---|---|
| Gostenhof | 0.04 | 18 | 0.84 | **371** |
| Himpfelshof | 0.66 | 222 | 1.47 | **537** |
| Maiach | 1.09 | 98 | **1.38** | 160 |

- Walking distance brings Gostenhof and Himpfelshof from 12 times apart (counting capacity) to 1.4 times.
- Counting departures, Maiach in the industrial south looks about 65 % better served than Gostenhof. Counting capacity, Gostenhof offers 2.3 times as much: Maiach's service is almost all buses (about 116 people per departure, against about 440 in Gostenhof).

Once jobs count (w = 1), the change is just as clear. Relative to the city average, Gostenhof goes from about 0.14× in v2 to about 1.7× in v3, and Maiach, with about 14,600 jobs and mostly buses, from about 0.6× to about 0.13×, the lowest of all 79. Eberhardshof stays low in both: a robust finding.

The numbers were measured in November 2026. A newer timetable changes them a little.

**The lesson.** The numbers looked fine. What caught the flaw was knowing the city (two neighbours on one U-Bahn line can't be 16 times apart) and reading the SQL the dashboard shows. That's why every page lists the SQL it ran, and why [AGENTS.md](../AGENTS.md) holds the rules a planner would apply.

## The prompt

```text
Build v3 as nuernberg-mobility-planning-v3, starting from v2, and fix both flaws.

Count capacity instead of departures: each departure with the seats and standing room of its line, or of its mode where the line has no value of its own. And count a stop for every area within walking distance of it, not only the area it stands in: 300 m for bus and tram, 600 m for U-Bahn, S-Bahn and regional rail. Keep the jobs weight, the Jobs panel and the stations. Call the measure "capacity per person" and explain it in one line under the title. No switch back to the old count: v2 is still there for comparison.

Before you build it, show me the new SQL next to the old one, and for Gostenhof, Himpfelshof, Maiach and Eberhardshof the value before and after each fix.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-mobility-planning-v3

- Where do Gostenhof and Himpfelshof come out now? Put v2 and v3 side by side in two browser tabs.
- Which areas fall furthest from v2 to v3? What runs there?
- Which areas stay low in both versions? Those are robust findings.
- Hover over Tafelhof. Is it still far above every other area, and why?
- Open "SQL executed". Find the capacity per trip and the walking distance in the SQL. Can you follow how the number for one area is computed?

## Who depends on it

Service matters most to people with no alternative. `DISTRICT_PROFILE` has two indicators per area from the city's statistics office: the share of residents on minimum-income benefits (`min_income_rate_pct`, 2012–2025) and registered cars per 1,000 residents (`cars_per_1000_residents`, 2025). Cars are counted where they are registered, so company and rental fleets make business areas look car-rich.

```text
Add two context layers I can switch on: the share of residents on minimum-income benefits and registered cars per 1,000 residents, both for 2025. Flag the areas where cars registered by businesses distort the count rather than coloring them. Show both values in the hover, and tell me whether the least served areas own more cars and whether poorer areas are better or worse served.
```

- Which areas does the agent flag for business-registered cars? What do they have in common?
- Do people in thinly served areas own more cars? How much of that could be density rather than service?
- Are poorer areas worse served? Look for areas with many residents on benefits, few cars and little service. Keep them in mind for the savings packages in [chapter 9](09-v6-savings-package.md).

## Understand it

```text
Explain in plain words how the color of an area is computed now, step by step. Which of these steps are assumptions? What would change with 200 m or 400 m for bus and tram instead of 300 m?
```

## What the data can't tell you

- The data is the **scheduled** timetable: no passengers, crowding, delays or live traffic.
- Capacities are planning values per mode or line, not measured loads.
- A train that stops at several stations in one area counts at each of them, so areas with many stations on one line look better served than a single stop would suggest.
- Walking distance is measured to the area's boundary, not from where people live inside it.
- Cars per resident count registrations, not cars in use, and benefit rates say nothing about who actually rides.

Next: [7 · v4: homes before trams](07-v4-growth.md)
