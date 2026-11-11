# 5 · v2: Residents and jobs

**Goal:** `nuernberg-mobility-planning-v2`: the v1 map, counting the people who work in an area as well as those who live there, with the U-Bahn and tram stations on the map. It still counts departures at the stops inside each area, like v1. You need v1 from [chapter 4](04-v1-residents.md).

## The idea

In v1, look at Tafelhof (Hauptbahnhof) and the other central areas. About 1,400 people live in Tafelhof, so its departures per resident are many times the city average. A station like the Hauptbahnhof serves the people who work around it as well as those who live there, and v1 counts only residents. A fairer picture counts both:

> activity = residents + w × jobs

How much a job weighs against a resident is a judgment, so w becomes a control. At w = 0 the map is v1; at w = 1 a job counts as much as a resident.

**Two job counts.** `DISTRICT_EMPLOYMENT` has jobs at the place of work per area from two sources:
- **2019 to 2024** (`jobs_2019` … `jobs_2024`): employees subject to social insurance at their workplace on 31 December, from the business register, published by the city's statistics office in its "Nürnberg in Zahlen" portal. Some jobs aren't assigned to any area. Civil servants, the self-employed and marginal jobs aren't counted. The model uses **2024**.
- **2005** (`jobs_2005` and its split into industry, trade and transport, and services): a wider count that includes the self-employed and marginal jobs, from a 2006 statistics report. It is the only year with a sector split, and the only one from before the AEG (2007) and Quelle (2009) closures.

Because the definitions differ, 2005 against 2024 shows the direction of change, not its exact size. 2019 against 2024 uses the same definition. The table also counts business establishments in 2019 and 2024, split into industry and construction (secondary) and services (tertiary). [research/district-growth.md](../research/district-growth.md#3a-update-2026-11-06-the-20192024-count) has the details.

**From factories to homes, and where the jobs went.** The 2005 split tells a Nürnberg story. Two areas with industrial jobs in 2005 are where the new homes go now:
- **The Lichtenreuth group** (41/42/43) was largely industrial railway land of the former Südbahnhof in 2005. It is now the city's largest new district. What happened to its jobs?
- **Eberhardshof** had the AEG and Quelle sites in 2005. The Quelle site now gets new homes. How do its jobs in 2019 and 2024 compare with 2005?

And where are the city's large job areas outside the centre? How are they served once jobs count?

## The prompt

```text
Now build v2 as nuernberg-mobility-planning-v2, starting from v1.

Residents aren't the whole demand: people also travel to the areas where they work. Count today's jobs too (2024), with a weight I can set, from 0 (residents only, as in v1) to 1.5, default 1. The comparison with the city average should use the same weight. "Dense" should then mean dense in residents and jobs. In the hover, show the jobs in 2024 and how they changed since 2019, and flag areas that are both dense and among the least served.

Keep the U-Bahn and tram stations on the map with their show/hide switch (add them if v1 doesn't have them yet), and keep counting departures at the stops inside each area, as in v1.

Add a "Jobs" panel next to the map: the areas with the most jobs, their change 2019 to 2024, and for comparison the 2005 count with its share of industry. Mark the areas where a large industrial workforce in 2005 has since given way to housing projects. Say on the page that 2005 and 2024 count jobs differently.

Before you build it, show me how the ranking changes between weight 0 and weight 1.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-mobility-planning-v2

- What happens to Tafelhof, Marienvorstadt and the old town at w = 1? Which area moves to the top, and why?
- Which areas drop furthest once jobs count? Look at Maiach in the industrial south: about 1,700 residents and 14,600 jobs.
- Set w to 0. Is it exactly v1 again?
- Look at the Lichtenreuth group in the Jobs panel: industrial railway land in 2005, now the city's largest new district. How did its jobs change, and what does that mean for v4?

**Now find the area at the bottom.** At any weight, one area comes out lowest of all 79: **Gostenhof**, the inner-city neighbourhood west of the Altstadt, at about 0.04 departures per resident (0.03 per person at w = 1). Its neighbour **Himpfelshof** gets about 0.66 per resident, 16 times as much. Does that match what you know about the city?

- Gostenhof and Himpfelshof lie side by side along Fürther Straße. The U1 runs under it. Turn on the stations: where do the U-Bahn stations Plärrer and Gostenhof stand?
- Hover over both areas. How many departures does each get, and from which stops?
- Open "SQL executed". What does the query count, and where does a stop have to be to count for an area?
- Maiach looks about as well served as many inner-city areas. What runs there: buses, trams or trains? Does a bus offer as much as a U-Bahn train?

Write down what you think is wrong. [Chapter 6](06-v3-can-we-trust-it.md) names the two flaws and fixes them.

## Understand it

```text
Which areas move most when I change the job weight, and why? Where did jobs grow or shrink most between 2019 and 2024, and which of those changes look like a single employer moving rather than a trend? What can the 2005 count still tell us that the 2024 count can't?
```

## What the data can't tell you

- Jobs are employees subject to social insurance at the workplace. Civil servants, the self-employed and marginal jobs are missing, which undercounts areas with public offices and small businesses.
- There is no jobs forecast: the model holds jobs at the 2024 count in every later year.
- Large changes in one area can be a single employer moving within the city, for example a loss in one area matched by a gain next door. The data doesn't name employers.
- Nothing here says how many residents or workers use public transport, or when they travel.
- w = 1 doesn't mean "a worker makes as many trips as a resident". It is a weighting you choose.

Next: [6 · v3: can we trust this map?](06-v3-can-we-trust-it.md)
