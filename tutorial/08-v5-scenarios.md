# 8 · v5: Rail and tram projects, and when they arrive

**Goal:** `nuernberg-mobility-planning-v5`: v4 with the planned rail and tram projects as scenarios you can switch on and off, to see where they add capacity, whether they keep up with growth, and whether they arrive before or after the new residents. You need v4 from [chapter 7](07-v4-growth.md).

## The idea

The city, VAG and the region are building or planning 10 rail and tram projects that touch Nürnberg. The dataset holds each project's stations, opening year, status and funding, curated from official sources ([research/pt-projects-notes.md](../research/pt-projects-notes.md)):

| Group | Projects |
|---|---|
| Funded | U3 extension to Gebersdorf (2028), tram 7 to Stadtpark (13 Dec 2026), tram 7 back on Allersberger Straße (2027), tram 4 through Minervastraße (2027), new tram stop Melanchthonplatz (2028) |
| Planned, with a date | tram 7 to Lichtenreuth and the new university (2030, risk 2031), Stadt-Umland-Bahn (StUB) from Am Wegfeld to Reutles (2031, risk 2032) |
| Discussed, no date | tram on to Klinikum Süd, two S-Bahn study items (S9 on the Nordring, the Gräfenberg line with a halt at Buchenbühl) |

A project adds capacity at its stations from its opening year on; projects without a published year are placed at 2040. Two modeling decisions:
- **How much service does a new line get?** Where a frequency is published, use it. Where none is, borrow the weekday service of a comparable existing line.
- **Where does it count?** At its stations, for every area within walking distance, like the existing stops.

Opening years slip. A "pessimistic dates" option uses the published risk years instead. Only the Lichtenreuth tram and the StUB have one, so the option only changes 2030–2032.

**When does rail reach the new homes?** v4 showed where people move in and when. The other half is when the train or tram gets there. Measure from each new-build project (the centre of its site on the city's map, `centroid_lat`/`centroid_lon` in `NEWBUILD_PROJECTS`) to the nearest U-Bahn, tram or S-Bahn stop, with the same walking distances as the map. Two large projects show why the timing matters:
- **Tiefes Feld** (1,500 homes, first occupied 2027): the U3 to Gebersdorf, with a stop at Kleinreuth, opens in 2028. Does rail arrive with the residents?
- **Brunecker Straße II in Lichtenreuth** (1,300 homes, first occupied 2025): the Lichtenreuth tram, with a stop at Ingolstädter Straße, opens in 2030 (risk 2031). How far is the nearest stop until then, and how long do the residents wait?

## The prompt

```text
Build v5 as nuernberg-mobility-planning-v5, starting from v4.

I want to switch the planned rail and tram projects on and off, in groups: none, the funded ones, the funded ones plus those with a published opening date, and everything that has been discussed. A project should count from its opening year, with an option to use the later risk years instead. Show the stations of the projects on the map, marking which are open in the selected year, and tell me in one line how many projects are open and how much capacity they add.

Also show, for each new-build project from v4, whether it has a rail stop within walking distance in the selected year, and the gap in years between its first occupancy and the year rail reaches it in the selected scenario. Measure from the project's site, not from the area's boundary.

Before you build the page, show me for 2033 how the city and the areas come out with no projects, with the funded projects and with all of them.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-mobility-planning-v5

- Set 2028 and switch on the funded projects. How much does the city gain? Go to 2033: does the gain grow or shrink, and why?
- Which area gains most from the funded projects, and from which project? Which growth areas get nothing from them?
- Switch on the dated projects and look at the Lichtenreuth group. Its tram arrives: does the group get back to its 2024 level? If not, what would it take?
- Switch on everything and go to 2040. Which area jumps, which project is behind it, and how solid is that project?
- Switch on pessimistic dates. Which years change, and which don't?
- Look at the new-build projects. Which large ones still have no rail within walking distance in 2027, and when does that change? Compare Tiefes Feld (U3, 2028) with Brunecker Straße II (tram, 2030).
- Which new-build projects have no dated rail project at all, and which of them is the largest?

Ask for changes in your own words, for example:
```text
I want to see each project's funding status and whether its data is verified, next to its name.
```

## Understand it

```text
For the StUB and the Lichtenreuth tram, break down where their added capacity comes from: which stations, which areas they reach, and whether the frequency is published or borrowed from another line. Which of these numbers are the most uncertain?
```

## What the data can't tell you

- Opening years, frequencies and comparable lines are assumptions from public sources. Projects without a published year are placed at 2040.
- Some stop locations are approximate (the StUB stops and the S9 halts); the S9 items are study recommendations without money or a date.
- The distance from new homes to rail is measured from the centre of each project's site on the city's map. Large sites such as Lichtenreuth stretch several hundred metres, so some homes are closer and some farther.
- The model adds capacity where the stations are. It doesn't know whether people would use it, how travel times change, or whether a project is built on time or at all. Money is tight: see [research/plans-research.md](../research/plans-research.md).

Next: [9 · v6: the savings package](09-v6-savings-package.md)
