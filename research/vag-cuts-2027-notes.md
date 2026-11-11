# VAG service cuts 2027: notes behind PT_SERVICE_CUTS and PT_SAVINGS_PACKAGES

What the city proposes to cut in the VAG service, how the document is built, and how its statements became the rules in `data/source/pt_service_cuts.csv` (`scripts/digitize_vag_cuts_2027.py`). Used by v6 (chapter 9). The rules cover P3 as published, P1 and P2 sorted out of it, and P4's concrete measures. No results are stored here: the dashboard applies the rules to the timetable live.

## The source

**"Sparmaßnahmenpaket im VAG-Verkehrsangebot"**, a council document in the city's Bürgerinformationssystem, planning status 27 Oct 2026 (the detail tables say 26 Oct 2026), published in early November 2026: https://online-service2.nuernberg.de/buergerinfo/getfile.asp?id=947894&type=do. Verified on the PDF itself (6 pages).

Background, from [plans-facts.md](plans-facts.md#1-political-and-budget-frame): the city must improve its 2027 budget by at least €122 m and asked VAG for savings proposals of about €10 m; VAG lost €97.7 m in 2025 with record passenger numbers. In December 2024 the council cut a planned bus reduction from €1.4 m to about €0.6 m so that no whole bus line was withdrawn. P3 withdraws three.

## What the document contains

| Page | Content |
|---|---|
| 1 | Five packages P1–P5 for decision, each building on the one before, with main measures, start dates, decision date and VAG's estimates of passengers lost and euros saved per year → `PT_SAVINGS_PACKAGES` |
| 2 | A summary of P3 by mode: measures and affected lines, from March 2027 and for the whole package from August 2027 |
| 3–4 | P3 from 8 March 2027, one row per line, seven day-type columns → `PT_SERVICE_CUTS`, stage `2027-03` |
| 5–6 | P3 end state ("Gesamtpaket / Endzustand"), from 2 August 2027 → stage `2027-08` |

**Packages** (page 1; all decisions due 30 Nov 2026):
- **P1**, recommended by VAG's supervisory board: demand-based headway changes, 40-minute headways from earlier in the evening, a holiday timetable in all school holidays. About −0.2 m passengers, €1.3 m a year.
- **P2** = P1 + more headway cuts, shortened routes, fewer reinforcement trips, thinner early and late service. About −0.6 m, €2.6 m.
- **P3** = P2 + bus lines 81, 82 and 84 withdrawn, route sections withdrawn, later starts and earlier ends, all trams every 15 minutes in all school holidays (Mon–Sat), trams 10 and 11 gone before 6:00 and after 18:30, U1–U3 every 10 minutes before 6:00 on weekdays, and on Saturday and Sunday before 8:00 only the Nightliner network, as on a strike day. About −2.8 m, €5.3 m.
- **P4** = P3 + service ends at 23:30 on all lines (Mon–Thu and Sun), trams 10 and 11 also gone all weekend, a 30/60-minute grid every day from 22:00. About −5 m, €8.1 m.
- **P5** = P4 + cuts on major lines including the ring bus, lines suspended at times, a general 30/60-minute network. About −6 m, €10.0 m.
- For P4 and P5, VAG writes "Dringende Empfehlung: Entscheidung zu einem späteren Zeitpunkt treffen!" (strong recommendation to decide later). Their parts beyond P3 would need about four months' lead time.

Only P3 is published line by line. P1 and P2 are subsets of P3 that the tables don't mark; P4 and P5 go beyond what is published. How the dataset still gives each package rules is in [From P3 to P1–P5](#from-p3-to-p1p5).

## From cells to rules

**Reading the tables.** The text in the PDF is selectable, but plain extraction mixes the columns. The script reads row boundaries from the drawn grid lines and assigns each text line to a day-type column by its x position (columns: Mon–Thu outside holidays, Mon–Thu in holidays, Fri outside, Fri in, Sat outside, Sat in, Sun). Lines of text less than 10 pt apart are joined (a wrapped line); larger gaps start a new statement. "U2/3" becomes two rows, U2 and U3.

**Rule types.** The statements are formulaic. Each is parsed into one of:

| Statement (examples) | rule_type | How it cuts the reference day |
|---|---|---|
| `entfällt` (81, 82, 84) | line_dropped | every trip |
| `entfällt vor 6:00 & nach 18:30` (10, 11), `ab 21 Uhr: entfällt` (40), `entfällt ab 17:30 statt 19:30 Uhr` (83), `Betriebsbeginn ab 6 Uhr`, `bis 8 Uhr: entfällt; reines Nightliner- / Streiknetz` | window_dropped | trips whose first departure is in the window |
| `bis 6 Uhr: 10'- statt 5'-Takt`, `17:30 - 20:30: 40'- statt 20'-Takt`, `20'-Takt vor 6 Uhr`, `20'-Takt ab 18:30 Uhr statt 20:30 Uhr`, `6:00 - 20:30: 15-min-Takt Straßenbahn` | headway | per direction, keep the first trip in each slot of the new headway |
| `Entfall der zweiten Fahrt morgens je Richtung` / `Entfall der vorletzten Fahrt abends je Richtung` | trip_dropped (rank 2 / −2) | the second / second-to-last trip per direction |
| shortened routes, short runs, named reinforcement trips, "einzelne Fahrten", Rufbus, the Nightliner row | not_modeled | nothing |

**Why slots for headways.** Several statements give only the new headway ("20'-Takt vor 6 Uhr"). Keeping the first trip in each slot of the new headway needs no old headway, keeps lines that already run that often unchanged, and gives the right number of trips for 5→10, 6⅔→10, 10→15, 10→20 and 20→40 minutes. Checked against the feed: tram 4 runs every 10 minutes on the reference Wednesday from about 5:00 to 20:30 and every 20 minutes after, so "20'-Takt vor 6 Uhr" and "20'-Takt ab 18:30 statt 20:30" each halve the trips in their windows.

**Approximations, noted per row in `model_note`:**
- A headway cut on part of a route (line 40 "bis Henenfelder", 53 "bis Luitpoldhain", 58 "Ende von Fahrten an Vogelweiherstraße", 51/52 short runs to Worzeldorf) is applied to the whole line.
- A later start "ab Am Wegfeld" (31) or "ab Flachröste" (56) drops early trips in both directions.
- The time of a trip is its first departure, wherever it starts.
- Not modeled: line 43 turning at Passauer Straße, every second trip of 51 ending at Worzeldorf, 31's short runs between Am Wegfeld and Neunhof and its Rufbus replacement, 56's evening section, named reinforcement trips of 55 and 58, unspecified single trips (54, 59, 30), the line 83 reroute via Lohhof, and the extra Nightliner trips on weekend mornings (6–8 h every 30 minutes, last departure from the Hauptbahnhof at 7:30). The modeled loss is therefore a little too high on weekend mornings (the Nightliner replacement isn't added) and too low where routes are shortened.

**Corrections.** The end-state table and the summary on page 2 disagree in two places. The summary is explicit, so the end state follows it, and the rows say so:
- Trams 4, 5 and 7, Mon–Thu and Fri outside holidays: the end-state cells are empty, the summary lists "Ausweitung der Schwachverkehrszeiten 4, 5, 7, 10, 11" for the end state. Carried over from March (20-minute headway before 6:00 and from 18:30).
- Bus 83: the end-state table has no row, the summary lists "Zeitweiser Entfall von Linien 31, 40, 83" for the end state. Carried over from March.
- Not corrected: line 67 drops its second-to-last weekday evening trip in March but not in the end state; the summary doesn't list 67 at all, so the tables are kept as printed.

## From P3 to P1–P5

v6 shows every package, so each rule carries the first package that includes it (`package`, with the reason in `package_basis`). This is an interpretation of page 1's measure lists, not something the document states:

| Package | Rules | Matches on page 1 |
|---|---|---|
| P1 | bus headway cuts to 40 minutes that start at 17:00 or later; bus cuts that appear only in the school-holiday columns | "Früherer Beginn 40-Min-Takte", "Ferienfahrplan in allen Ferien" |
| P2 | all other bus headway cuts; the second or second-to-last trip dropped; shortened routes and reinforcement trips (not modeled) | "Weitere Taktausdünnungen", "Ausdünnung Tagesrandlagen", "Verkürzung Linienwege", "Entfall Verstärkerfahrten" |
| P3 | lines and sections withdrawn, later starts and earlier ends, all tram and U-Bahn rules, weekend mornings on the Nightliner network, and every rule found only in the end-state table | P3's own list; P1 and P2 are implemented in full on 8 Mar 2027, so anything new in August is P3 |
| P4 | service ends at 23:30 (Mon–Thu, Sun) on every day line; trams 10 and 11 also gone on Saturday and Sunday; from 22:00 every day a 30-minute headway on U-Bahn and tram and a 60-minute headway on buses | P4's first three bullets. The split of the "30/60-Min Taktraster" by mode is an assumption |
| P5 | nothing that cuts trips: its bullets name no lines or times except the ring bus | listed as `not_modeled` |

P1 and P2 are taken from the March stage, P3 and P4 from the end state; [data/data-model.md](../data/data-model.md) gives the rule. VAG's €/year and passengers/year figures for each package are not checked by the model, which measures capacity only.

## Reference days

The document's columns map to the dashboard's reference days: **Mon–Thu outside holidays** → Wednesday 21 Oct 2026, **Saturday outside holidays** → Saturday 24 Oct 2026 (a regular Saturday in the feed: the same VAG trips as the Saturdays before and after). The Saturday matters: in the end state nothing but the Nightliner network runs before 8:00 on weekends, trams 10 and 11 stop at 18:30, and many bus lines run every 40 instead of 20 minutes all day. School holidays, Fridays and Sundays are in the table but have no reference day.

## Limits

- **A proposal.** The council decides by 30 Nov 2026; it may adopt any package, or postpone. Until then "after the cuts" is a scenario.
- **P1, P2, P4 and P5 are modeled from their descriptions.** P1 and P2 by sorting P3's rules, P4 through its three concrete measures; P5 shows the same cuts as P4.
- **The feed ends on 12 Dec 2026**; the cuts start in March 2027. The rules are applied to the 2026 reference days, so the result is "today's timetable with P3 applied", not a future timetable. Other changes by 2027 (tram 7 to Stadtpark from 13 Dec 2026, construction diversions) are not in it.
- **Capacity, not passengers.** VAG's passenger estimates (−2.8 m a year for P3) are quoted as VAG's. The dataset has no passenger counts.
