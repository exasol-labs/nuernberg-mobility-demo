# 7 · v4: Homes before trams

**Goal:** `nuernberg-mobility-planning-v4`: v3 with a year slider and a chart of how each area changes as Nürnberg grows, assuming the timetable stays as it is today. You need v3 from [chapter 6](06-v3-can-we-trust-it.md).

## The idea

The city's forecast (report M558) runs to 2033. Growth doesn't come evenly: new homes are built in a few places, and some of them are already occupied. In [chapter 3](03-first-questions.md#33-growth-that-has-already-started) you looked at how fast the Lichtenreuth group grew in 2025. The city's new-homes map (`NEWBUILD_PROJECTS`) lists the major projects with their homes and the year each is first occupied. Most of them lie in three corridors:

| Corridor | Areas | First occupied |
|---|---|---|
| **South-east:** Lichtenreuth, on the former Südbahnhof next to the new Technische Universität | 41/42/43, Hasenbuck | 2024–2025 |
| **West:** Tiefes Feld, the former Quelle site on Fürther Straße, Muggenhof | Großreuth b. Schweinau, Höfen, Eberhardshof, Muggenhof | 2026–2030 |
| **North-west:** Wetzendorf, Nordwestring | Wetzendorf, Westfriedhof | 2024–2028 |

If no service is added, every new resident shares the existing capacity. This version shows where that matters and how soon.

Three choices make the years comparable:
- Every year is compared with the **2024** city average.
- The city's forecast (report M558) gives **2033 per Stadtteil** (10 parts of the city), not per area. The per-area 2033 figure in `DISTRICT_POPULATION.pop_2033_model` is a **model**: each Stadtteil's new-build movers go to its areas by their share of the new homes on the city's map, at most two people per listed home; the rest of the Stadtteil's change goes by today's residents. The Stadtteil totals match the forecast.
- The years in between are interpolated; after 2033 residents are held. Jobs stay at the 2024 count.

**The counts are a check on the model.** The model starts from the 2024 count and draws a straight line to 2033. The 2025 count is already in the data, so you can see whether real growth runs ahead of the line or behind it.

**So are the building statistics, with care.** `DISTRICT_HOUSING` has the homes permitted and completed per area and year, 2012–2025, from the city's building statistics. They don't always agree with the residents count: completions are recorded when the builder reports them, which can lag by years. Compare permits, completions and residents for the Lichtenreuth group and for Eberhardshof. Use the three signals together: permits say what is coming, completions what the statistics have caught up with, residents what has happened.

M558's new-build movers are a **gross** figure: many of them move from elsewhere in Nürnberg. So areas without new homes can shrink in the forecast. [research/district-growth.md](../research/district-growth.md) has the forecast, the new-build projects and the method.

## The prompt

```text
Build v4 as nuernberg-mobility-planning-v4, starting from v3.

I want to see what happens as Nürnberg grows if public transport stays exactly as it is today. Add a year slider from 2024 to 2040. Residents should follow the modelled 2033 figures in the data, interpolated in between and held after 2033; jobs stay as they are. The map should always compare with today's city average, so I can see areas falling behind as the city grows. Show the city's new-build projects on the map, sized by homes and marked by the year they are first occupied, so I can see which ones are occupied by the selected year.

Next to the map, add a chart "Change since 2024": how much each area gains or loses compared with 2024, with Nürnberg overall at the top and then the areas from best to worst. When I click an area, show its residents over time: the counts for 2023 to 2025 next to the modelled path, and below it the homes permitted and completed per year since 2012.

Tell me how the 2033 residents per area are built and which part of that is a model, and show me the result for 2033 first.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-mobility-planning-v4

- Move the slider to 2033. How does the city as a whole change? Which areas lose far more, and are they the areas where the new-build projects sit?
- Click the Lichtenreuth group. Compare the model's straight line for 2025 with the count. Is growth running ahead of the model or behind it, and what would that mean for the years before 2030?
- Click Eberhardshof. Compare the homes completed since 2020 with its residents count. The Quelle site's homes are first occupied from 2026. When does its line start to bend?
- Click the Lichtenreuth group again and look at the homes chart. Do permits and completions tell the same story? Which source would you trust for 2025, and why?
- Which areas gain, and why, when nothing is added?
- Move past 2033. Why does nothing change any more?

## Understand it

```text
For the Lichtenreuth group (41/42/43), walk me through the numbers in 2024, 2025 and 2033: residents counted and modelled, new homes and when they are first occupied, capacity and the ratio. How much of the 2033 figure comes from the city's forecast and how much from the model? If growth runs ahead of or behind the straight line, how would you change the model?
```

## What the data can't tell you

- The per-area 2033 figure is a model built on a Stadtteil forecast, not a published number. Where the city's new-homes map is incomplete, the model spreads growth by today's residents.
- The years in between are a straight line, and nothing is forecast after 2033. Real moving-in follows the building sites; compare the counts with the line.
- Holding today's timetable is a thought experiment. The timetable changes every year; the next change is on 13 Dec 2026 (see [research/plans-facts.md](../research/plans-facts.md)).
- Fewer capacity per person doesn't mean fuller trains. There is no passenger or crowding data.
- Completions in the building statistics can lag years behind the move-ins, and they count net changes (conversions and demolitions can make a year negative).

Next: [8 · v5: rail and tram projects, and when they arrive](08-v5-scenarios.md)
