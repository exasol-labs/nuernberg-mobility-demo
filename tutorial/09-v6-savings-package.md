# 9 · v6: The savings package

**Goal:** `nuernberg-mobility-planning-v6`, a simpler page that answers one question: **what would each of the city's savings packages do to public transport in Nürnberg as planned for 2027?** The base is fixed: the new homes and the funded tram projects of 2027. You pick a package, P1 to P5, and see how capacity per person changes and which areas lose the most. You need the model from v3 to v5 (chapters 6 to 8).

## The idea

v1 to v5 built the measure and then added the forces acting on the network: who lives there, who works there, how the city grows and what gets built. Each added controls too. v6 adds the money, and drops controls instead of adding them.

Nürnberg must improve its 2027 budget by at least €122 m, and VAG's losses are part of the gap. In early November 2026 the city published the savings package for the VAG service. It has five packages, P1 to P5, each building on the one before, from €1.3 m to €10.0 m a year. The council decides by **30 November 2026**. The cuts start in March 2027, so v6 shows one year, 2027, set up as planned:
- **Residents** as modeled for 2027, so the new homes of v4 are in.
- **Jobs** from 2024, weight 1, as in v2.
- **Service** from the reference day's timetable, plus the funded projects that open by 2027 (v5): tram 7 to Stadtpark, tram 7 back on Allersberger Straße, and tram 4 to Minervastraße.

On top of that base comes the package. There's no year slider and no project or date choice: those questions belong to v4 and v5.

Two tables hold the packages:
- `PT_SAVINGS_PACKAGES`: the five packages with their main measures and VAG's own estimates of passengers lost and euros saved. VAG strongly recommends deciding on P4 and P5 later.
- `PT_SERVICE_CUTS`: the packages as rules the timetable can be cut with. Each rule is a line dropped, trips dropped in a time window, a thinner headway, or one trip of the day dropped.
  - Only **P3** is published line by line. Its rules are tagged with the first package whose description matches them, P1, P2 or P3. The document doesn't mark that, so the tagging is an interpretation.
  - **P4** adds its three concrete measures: service ends at 23:30, trams 10 and 11 are gone at weekends, and a 30/60-minute headway runs from 22:00.
  - **P5** names no lines or times, so it shows the same cuts as P4.

  [data/data-model.md](../data/data-model.md) says which rows make up each package; [research/vag-cuts-2027-notes.md](../research/vag-cuts-2027-notes.md) says why.

Much of P3 falls on the weekend: before 8:00 on Saturdays and Sundays, only the Nightliner network runs, as on a strike day. So the page has a day switch: the reference weekday (Wednesday 21 Oct 2026) or the reference Saturday (Saturday 24 Oct 2026).

Choices you'll make with the agent:
- **Compared with what?** Capacity per person against the 2027 city average without cuts says where an area ends up. The share of its capacity a package takes away says what the package takes. The map shows one or the other, and the hover shows both.
- **Most affected by what?** A share is fair to small and large areas alike, but an area with almost no service can lose a large share of very little. Ask the agent to rank by share lost and show residents and capacity per person next to it.
- **Projects on a Saturday.** The projects publish weekday frequencies only. Counting them at their off-peak frequency all day is a simple choice for Saturday.

## The prompt

```text
Build v6 as nuernberg-mobility-planning-v6. Reuse the model and look of v5, but make the page simpler: it answers one question, what each savings package would do to public transport in Nürnberg as planned for 2027.

Fix the base, with no controls for it: residents as modeled for 2027, jobs 2024 with weight 1, the reference day's timetable plus the funded projects that open by 2027. Drop the year slider and the project and date controls.

Give the page three controls:
- Package: none, P1, P2, P3, P4, P5. Take the rules from PT_SERVICE_CUTS as the data model describes.
- Day: the reference weekday or the reference Saturday.
- View: "capacity per person" colors each area against the 2027 city average without cuts; "most affected" colors each area by the share of its capacity the package takes away and lists the ten areas that lose the largest share.

In the hover and in the list, show each area's residents, capacity per person without cuts and with the package, and the lines that lose trips there. Below the map, add a bar chart of the city's capacity per person for each package on the selected day, and a table of the five packages with VAG's figures next to the share of capacity each one takes away in the model.

Say on the page that the cuts are a proposal the council decides by 30 November 2026, that only P3 is published line by line, and that P1, P2, P4 and P5 are modeled from their descriptions. List in a foldout the measures that couldn't be modeled for the selected package.

Before you build it, show me for each package how much capacity it removes on the weekday and on the Saturday, by mode.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-mobility-planning-v6

- Step from P1 to P5 on the weekday, then on the Saturday. Where does the big jump come, and which measures cause it?
- Pick P3 and "most affected". Which areas lose the largest share on each day? Are they the same areas? How many people live there, and were they already below the city average?
- Bus lines 81, 82 and 84 are withdrawn in P3. Which areas did they serve, and how much do those areas lose? If the loss is smaller than you'd expect, what else runs within walking distance?
- P4 removes trams 10 and 11 on weekends entirely. Which areas depend on them on a Saturday?
- Look at Lichtenreuth and the western new-build areas. With the new homes in, how far below the city average do they fall under each package?
- Open the package table. VAG expects P3 to cost about 2.8 million passengers a year and to save €5.3 m. Does the share of capacity each package removes rise the way VAG's figures do? Why can't the dashboard check the passenger number?
- Open the foldout for P4 and for P5. What does the map leave out, and does that make it look better or worse than the plan?

## Understand it

```text
Explain how one package becomes cut trips: which rows of PT_SERVICE_CUTS make up P2 and which make up P4, why P1 and P2 come from the March stage and P3 and P4 from the end state, and how the cuts are applied to bus 34 on the weekday under P3. Why does the headway rule keep the first trip in each slot instead of every other trip?
```

## What the data can't tell you

- **The decision.** The cuts are a proposal. The council may adopt any package, or postpone. Until 30 November 2026, every package on the page is a scenario.
- **Which measure belongs to which package.** Only P3 is published line by line. Sorting its rules into P1, P2 and P3 follows the package descriptions; the document doesn't mark it. P4 is modeled through its three concrete measures, the 30/60-minute split by mode is an assumption, and P5 adds nothing that can be modeled.
- **Everything the rules can't express.** Shortened routes, dropped short runs, named reinforcement trips and on-demand replacements are listed but not modeled. On weekend mornings the Nightliner network replaces day service; its extra trips aren't in the feed, so the loss before 8:00 is a little overstated.
- **The 2027 timetable.** The rules are applied to the 2026 reference days, with the 2027 projects added. Other changes by then, such as construction diversions, aren't in it.
- **Passengers and time of day.** The model counts capacity offered over the whole day. It can't say how many people are affected, and a line that loses all its evening trips loses only a small share of its daily capacity.

Next: [10 · v7: an assistant that drives the view](10-v7-assistant.md)
