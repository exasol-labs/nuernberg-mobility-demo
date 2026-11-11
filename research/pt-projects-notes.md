# Planned rail and tram projects in Nürnberg: stations for scenario modeling (as of 28 Oct 2026)

Companion to `pt_projects.csv`, which has 33 rows across 10 project_ids. I did the research in German, mostly from official sources: Stadt Nürnberg (Verkehrsplanungsamt, SÖR, press office), VAG, Regierung von Mittelfranken plan-approval files, Zweckverband StUB and the StMB/AuSbauNü study. Each source is marked **[verified]** if I opened it and saw the fact there, or **[unverified]** if I saw it only in search snippets or secondary sources.

Baseline: the VGN GTFS feed (24 Jun–12 Dec 2026) in `NUERNBERG_DATASET`. Tram lines 10 and 11 are already in it, so they are not projects. I found nothing that opened between mid-2026 and today and is missing from the feed.

## Conventions used in the CSV

- **station_is_new is mode-specific.** 1 means the place has no station of this mode today. Examples: a tram stop at U-Bahn Rennweg is 1, and the S-Bahn at Nordostbahnhof, which today has only RB 21, is 1. 0 means an existing stop of the same mode gains a line (Rathenauplatz, Finkenbrunn, Am Wegfeld) or regains it after a construction closure (Tristanstraße, Wodanstraße).
- **trains_per_hour** is per direction and per line. "Off-peak" means daytime off-peak. The field is empty when no headway is published; then use `analog_line`.
- **funded = 1** means the project is under construction or has committed money. Projects still in plan approval, or with grant applications still to come, are 0.
- **Coordinates** come from these sources, in order of preference:
  1. OSM *proposed* or *construction* nodes and platforms. VAG and mappers have drawn the Lichtenreuth, Minervaplatz and U3 stations from the official plans.
  2. VGN GTFS stops, for existing stops.
  3. A same-name GTFS bus stop, or Nominatim, flagged "approximate".
  4. For study-only S-Bahn halts: the point on the railway nearest to the named place, flagged.
  
  One halt could not be placed ("Nürnberg Nord" on the Ringbahn). It has `station_name = unknown` and no lat/lon.

## 1. U3 Südwest to Gebersdorf (BA 2.2): 2 rows

- **Stations:** Kleinreuth (bei Schweinau) and Gebersdorf, the terminus with a depot and sidings. About 2 km. **[verified]** City press release 122, 2 Feb 2026.
- **Opening:** first half of **2028**, per the city's status briefing of 6 Oct 2026 (https://www.nuernberg.de/internet/stadtportal/aktuell_100397.html, see plans-facts.md). The press release of 2 Feb 2026 still said "Ende 2027". Shell completed early 2024; fit-out under way. Earlier targets were 2024 (SPD, 2017), 2025 and 2026 (city, Nov 2023) **[unverified, snippets]**. `pt_projects.csv` uses 2028 with no separate risk year.
- **Cost:** €204.7 m, of which €110.1 m Bund/Land grants **[verified]**.
- **Headway:** not published; analog U3. Gebersdorf is not in VGN_STOPS. The coordinates are OSM `construction` station nodes.

## 2. Tram 7 to Stadtpark: 5 rows

- **What:** line 7 extended from Hbf via Rathenauplatz to Stadtpark (Berliner Platz) over the renovated Bayreuther Straße line, 1.2 km. There are two new barrier-free stops, at U-Bahn Rennweg and at Stadtpark. **[verified]** VAG press release, 23 May 2025.
- **Opening: 13 Dec 2026** **[verified]** VAG news, 22 Oct 2026 (rail grinding "zur Vorbereitung der Inbetriebnahme der Linie 7 zum Stadtpark ab 13. Dezember 2026"). The date has slipped from end Sep 2026, then end Nov/early Dec. City press release 857 (30 Jul 2026) says "im Dezember" **[verified]**.
- **Feed check:** this falls just outside the feed's range, which ends 12 Dec. Rennweg is served only by U2/U3 in the feed, and Stadtpark has no tram. Hence the project counts as new.
- **Assumption:** Marientor and Wöhrder Wiese are coded `verified=0`. The route over line 8's track is my inference.
- **Headway:** 10/20 min, from the Lichtenreuth Erläuterungsbericht's line 7 plan, not from a Stadtpark-specific source.

## 3. Tram 7 back on Allersberger Straße: 2 rows (restoration)

- Allersberger Straße track renewal runs from 24 Mar 2026 to "Frühsommer 2027". Meanwhile line 7 is diverted Hbf–Schweiggerstraße–Peterskirche–Dutzendteich. **[verified]** VAG Bauprogramm 2026; GTFS confirms the diversion.
- The normal line 7 runs Tristanstraße–Hbf **[verified, VAG May 2025]**.
- Wodanstraße as a tram stop on this section is **[unverified]**. The evidence is replacement buses to Wodanstraße (t-online) and the Lichtenreuth plan's work area reaching to Wodanstraße.
- It is not new supply versus a normal year, but it is new versus this feed. Drop it if the model should ignore construction diversions.

## 4. Tram Lichtenreuth / Technische Universität Nürnberg (line 7): 5 rows

- **Stops:** five new stops: Hiroshimaplatz, Ingolstädter Straße, Parkstraße Süd, UTN and Bauernfeindstraße (a loop at the U1 station). The existing Tristanstraße stop is rebuilt. 2.5 km. **[verified]** Erläuterungsbericht, Regierung von Mittelfranken plan-approval file.
- **Service:** line 7 every 10 min (Mo–Fr 6–20 h, Sat 8–20 h) and every 20 min otherwise. A second line would follow later "bei Bedarf".
- **Dates:** construction start Q1 2027, opening end 2030 **[verified]**. The city page also says opening 2030 **[verified]**.
- **Status:** plan approval is still pending. The documents were on public display 17 Nov–16 Dec 2025, and I found no approval decision by Oct 2026. City press release 857 (Jul 2026) says "im Planfeststellungsverfahren" **[verified]**. So status = planning, and risk 2031 is my assumption.
- **Funding:** grant applications only after the approval-stage design, so funded = 0.

## 5. Tram section 2 to Klinikum Süd: 3 rows

- Bauernfeindstraße–Messe–Bertolt-Brecht-Schule–Klinikum Süd. Preliminary planning since 2024; survey and route-variant study being prepared. Council decision 20 Jul 2023. **[verified]** city page. No stop list, line or date.
- The rows are corridor waypoints with approximate coordinates (U-Bahn Messe, the school, the Klinikum Süd bus stop).
- One snippet adds a "LangwasserBad" waypoint **[unverified]**.

## 6. Minervastraße gap closure (line 4): 3 rows

- **What:** line 4 extended Gibitzenhof (loop moved)–Minervaplatz (new)–Finkenbrunn (meets line 5). 1.7 km. Plan approval 3 Jun 2025. Opening end 2027. Line 4 runs every 10 min weekdays by day, 20 min evenings and Sundays. **[verified]** city page.
- **Construction:** track construction from early Jun 2026, opening "Ende 2027" **[verified]** VAG Bauprogramm 2026.
- Bus 68 is replaced.

## 7. Melanchthonplatz stop (Landgrabenstraße renewal): 1 row

- **What:** plan approval in place. Construction 2027, completion about end 2028. **[verified]** SÖR page.
- **Stop change:** the new stop replaces Heynestraße and lets line 11 serve the area. Lines 6/10/11 are my inference from the feed.
- **Effect:** small, because it is a relocation of about 150 m, and service on the section is interrupted for 1–2 years during the works.

## 8. StUB, Nürnberg section Am Wegfeld–Reutles: 5 rows

- **Stops in Nürnberg:** Am Wegfeld, Buch Nord, Boxdorf, Moosäckerstraße, Reutleser Straße. The ZV says they may still change. **[verified]** stadtumlandbahn.de Nürnberg page.
- **Earlier stop list:** a Dec 2023 ZV document listed "Moosäckerstraße" and "Boxdorf", with "Würzburger Straße" as optional **[unverified]**.
- **Route and line:** an extension of tram line 4. The Verkehrsausschuss decided the route on 26 Mar 2026. The plan-approval application is due H2 2026 and was "being finalised" on 30 Jul 2026. **[verified]** city StUB page and press release 857.
- **Dates:** construction 2028/2029, first tram to Reutles 2031/2032 **[verified]** ZV schedule page. The brochure (Mar 2026) says "ab 2031" **[verified]**.
- **Headway:** 10 min by day plus peak extras **[verified]** brochure and Dialogforum 17.
- **Political risk:** Erlangen voters approved the project in June 2024 **[unverified, snippets]**. The Nürnberg section has no open court case that I found. The Erlangen/Herzogenaurach sections are outside the city and not in the CSV.

## 9 and 10. S-Bahn S9: Nordring (4 halts) and Gräfenberg line (Buchenbühl): 5 + 2 rows

- **Source:** AuSbauNü first results, 17 Oct 2024 **[verified, PDF opened]**.
- **U06.2 Nordring:** S9 Fürth Hbf–Nürnberg Nordost every 30 min, with new halts Nürnberg Nord, Thon, Wetzendorf and Muggenhof. €118 m, BCR 1.0.
- **U06.1 Gräfenberg:** electrify the line, S9 every 30 min, new halt Buchenbühl. €141 m, BCR 1.0.
- **Status:** both are only "weiterverfolgen" recommendations. The second forum release (31 Oct 2025) names other projects and cites a tight state budget **[verified]**. I found no planning order, so: planning, unfunded, no year.
- **Coordinates:** the halt sites are not published. Mine are the nearest points on the OSM railway to the named place.

## Checked and excluded

- **Tram to Kornburg / Fischbach:** feasibility study gave BCR < 0 (city overview of decisions 2021) **[unverified, snippet]**.
- **Tram via Pirckheimerstraße (Hbf–Wegfeld):** only kept open as an option in the Bayreuther Straße design. No project.
- **Tram on Nordwestring / Thon–Wetzendorf:** no project found. The current Nordwestring works are road resurfacing.
- **Plärrer track renewal** (approval 10 Sep 2026) and **Neue Rothenburger Straße:** these do not change service. The latter only gives access to U-Bahn Kleinreuth.
- **Hilpoltstein extensions (S2 via Roth, S5 via Allersberg):** S2 timing in Nürnberg is unchanged and the stations are outside the city.
- **Markt Erlbach / Cadolzburg S-Bahn:** Cadolzburg trains run through to Nürnberg Hbf, but they add no stop in the city.
- **3rd track Feucht–Neumarkt, Deutschlandtakt, NBS Würzburg–Nürnberg:** long-term DB items with no defined effect on city stations.
- **Söder's maglev:** reported as "vor dem Aus" **[unverified]**.
- **U-Bahn automation:** no service change.
- **No new S-Bahn halts in the city** are planned beyond the study halts above. I could not substantiate the candidates "Nürnberg-Ost" or "Fürth Klinikum".
