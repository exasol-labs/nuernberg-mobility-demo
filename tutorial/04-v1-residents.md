# 4 · v1: A first map

**Goal:** the first dashboard, `nuernberg-mobility-planning-v1`: a map of Nürnberg's 79 areas that shows which ones get less public transport per resident than the city average. This first version is deliberately simple. It has two flaws, and chapter 6 finds and fixes them. Build it as described and keep your eyes open.

## The idea

The simplest measure you can think of: for each area, count the scheduled departures on the reference weekday (Wednesday 21 Oct 2026) at the stops that stand in the area, divide by its residents, and compare with the city as a whole:

- 1.0× means the area gets as many departures per resident as Nürnberg on average.
- 0.5× means half as many, 2× twice as many.

A departure is one stop event: a bus or train stopping at a stop. A line with ten stops in an area counts ten times there. This is **service offered**, not use: it says nothing about how full the vehicles are.

A planner looks at the areas well below 1.0×, where residents get less service than elsewhere.

## The prompt

```text
Build my first dashboard, nuernberg-mobility-planning-v1, titled "Nürnberg Mobility Planning".

Keep it simple for this first version: for each of the 79 areas, count the scheduled departures on the reference weekday at the stops that stand in the area, and divide by its residents. Show that on a map of the areas, over a light, almost white street map so I can zoom in and see what is where, relative to the Nürnberg average. It should be obvious at a glance which areas are below and which are above average, and very high or very low values shouldn't wash out the rest of the map. When I hover over an area, show me the numbers behind its color. Say on the page in one line what is counted.

Before you build anything, show me the SQL and the result per area, and tell me which areas come out lowest and highest.
```

The agent shows the query and the ranking first. That is the moment to ask questions, for example "why is this area so low?", or to change the approach before the page exists. The agent may say that this is a simplification. It is: build it anyway.

When the page is live, add one layer:

```text
Add the U-Bahn and tram stations to the map, with a switch to show or hide them.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-mobility-planning-v1

- Which areas are clearly below average? Where do they lie: in the centre, at the edge?
- Hover over Tafelhof, which holds the Hauptbahnhof. How many residents live there, and what does that do to a per-resident value?
- Which other areas come out far above average? What do they have in common?
- Look at the stations. Do the areas with U-Bahn stations always come out well?
- Open "SQL executed" at the bottom. What exactly does the query count, and where does a stop have to be to count? Write down anything you'd question. Chapter 6 comes back to it.

Change what you don't like, in your own words, for example:
```text
Make the stations smaller and show the line names when I hover over one.
```

## Understand it

```text
Explain in plain words how the color of an area is computed, step by step. Which of these steps are assumptions, and how would the map change if we made them differently?
```

## What the data can't tell you

- The data is the **scheduled** timetable: no passengers, crowding, delays or live traffic.
- A departure is a departure here, whatever the vehicle: a bus and a U-Bahn train count the same.
- A train that stops at several stations in one area counts at each of them.
- Residents are counted where they are registered, not where they travel.

Next: [5 · v2: residents and jobs](05-v2-jobs.md)
