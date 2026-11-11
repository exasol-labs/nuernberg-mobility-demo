# Nürnberg growth per Stadtteil and Bezirk: jobs, official population forecast, development areas

Researched 2026-10-28. Web research plus one read-only lookup in our DB (schema `NUERNBERG_DATASET`). Every number below comes from a source I opened or downloaded (marked *verified* in section 6). Numbers I saw only in search snippets are marked *(unverified)*.

**How to read the columns.** **Count** means registered population with Hauptwohnung (main residence) at 31 December, from the Melderegister. **Forecast** means the city's *Kleinräumige Bevölkerungsvorausberechnung* (small-area population projection) by the Amt für Stadtforschung und Statistik. **Jobs** means people working *in* an area (place of work), not people living there.

**Spatial units.** Nürnberg has 10 Statistische Stadtteile (00–09), 87 Statistische Bezirke (01–97, the Stadtteil is the tens digit) and 316 Distrikte. Our DB has `BEZIRKE` (87) and `DISTRICTS` (79, some Bezirke grouped).

---

## 1. Summary

- **Update 2026-11-06: jobs by place of work per area exist for 2019–2024.** The statistics office's portal "Nürnberg in Zahlen" has SV-Beschäftigte am Arbeitsort per zusammengefasstem Statistischem Bezirk (the same 79 areas as `DISTRICTS`), 31 Dec 2019–2024, from the business register, plus jobs not assigned to an area. `DISTRICT_EMPLOYMENT.jobs_2019` … `jobs_2024`, and the model now uses 2024. See section 3a. The rest of this bullet is the original finding.
- **Jobs by place of work exist per Bezirk only for 2005.** The only small-area jobs table I found is Tab. 1 of the Statistischer Monatsbericht Oktober 2006: *Beschäftigte* per Statistischer Bezirk for 1970, 1987 and 2005, split into three sectors. Total 2005: **342,000**. All 87 Bezirke are transcribed into `jobs.csv`; the rows add up exactly to the printed totals. Everything newer is either **city-wide only** (SV-Beschäftigte am Arbeitsort, Dec 2022: **318,577**) or **by place of residence** (Bezirksatlas t9, Innergebietliche Strukturdaten, Bezirksdatenblätter). The Innergebietliche Strukturdaten 2023 say so explicitly (PDF p. 58): the Bezirk tables follow the *Wohnortprinzip*.
- **No jobs forecast per area was found.** The Nahverkehrsentwicklungsplan 2025 (IVV, 2012) had a *Strukturdatenprognose 2025* with residents and jobs for the region, but only its table of contents and the short version are online. The tables themselves were not found.
- **Population forecast per Stadtteil, with numbers: yes.** The context for this note assumed that M558 shows 2033 values per Stadtteil only as map circles. That is wrong: the **text** of M558 gives the 2033 value for all 10 Stadtteile (PDF pp. 11 and 16). They add up to 554,710, which matches the city total of 554,700. The earlier edition M529 (base 2021, horizon 2035) also gives all 10 Stadtteile in its text (pp. 15 and 18). Both editions are in `forecast.csv`. **No forecast per Bezirk is published.**
- **Where the growth goes (M558, 2024→2033, from the values M558 prints):** 06 Westliche Außenstadt **+5,880 (+17.2 %)**, 07 Nordwestliche Außenstadt **+4,939 (+14.0 %)** and 04 Südliche Außenstadt (forecast 57,160 in 2033; M558 states no 2024 value for 04). All other Stadtteile stagnate or shrink: 01 −1,960, 05 −1,296, 08 −1,202, 02 −910, 09 −625, 03 −606; 00 (no 2024 value printed) is forecast at 59,260.
- **What drives it:** new homes. M558 assumes 49,130 people moving into new buildings from 2025 to 2033. 12,280 of them go to 06, 11,350 to 04 and 8,960 to 07. This is already in the DB as `STADTTEIL_NEWBUILD`.
- **The city's new-build pipeline is available per project, with polygons.** WFS layer `Wohnungsneubau:Schwerpunkte_des_Wohnungsneubaus` (geoportal.nuernberg.de) lists 44 major projects with numbers of homes and year of first occupancy. I assigned each project to a Bezirk by point-in-polygon against our `BEZIRKE` polygons. Result: `newbuild_projects.csv`. The largest are Lichtenreuth/Brunecker Straße (Bezirk 41, 3,585 homes), the former Quelle area on Fürther Straße and Muggenhofer Straße (Bezirk 64, 2,480 homes) and Tiefes Feld (Bezirke 60/63, 1,913 homes).
- **What this means for transport.** Growth is concentrated in three corridors:
  1. **South:** Lichtenreuth, Bezirke 40/41. It has U1 Hasenbuck today; the tram 7 extension is due at the end of 2028. The TU Nürnberg is planned for about 6,000 students *(unverified)*.
  2. **West:** Tiefes Feld, Bezirke 60/63, with U3 Kleinreuth opening in 2026. The former Quelle area, Bezirk 64, is on the U1 Eberhardshof corridor.
  3. **North-west:** Wetzendorf and Nordwestring, Bezirke 70/72. Its new homes have no rail project announced in the sources I read; existing tram routes run along Nordwestring and Wetzendorf, but I did not check them.

  The inner city, the south-east (Langwasser) and the north-east are forecast to lose residents.

---

## 2. Stadtteil table: counts and forecast

Sources per column:
- **(B) M558 count 2024:** as printed in M558, text on PDF p. 16. Values in brackets are implied by the change printed on PDF p. 11 (2033 value minus the stated change). "–" means the text gives no value.
- **(C) M558 forecast 2033:** M558 text, PDF p. 11 (00–02) and p. 16 (03–09).
- **Δ 2024→2033:** C − B; "–" where M558 gives no 2024 value.
- **(D) New-build movers 2025–2033:** M558 PDF pp. 8–9 (the same values as DB `STADTTEIL_NEWBUILD`).
- **(E) M529 forecast 2035:** the previous edition (base 2021), PDF pp. 15 and 18. Shown so the size of the revision is visible.

The 2024 counts per Stadtteil from our DB (`DISTRICT_POPULATION`) are not repeated here; query them live (see the caveats in section 5 on how to aggregate).

| No. | Stadtteil | (B) M558 2024 | (C) **Forecast 2033** | Δ 2024→33 | Δ % | (D) New-build movers 25–33 | (E) M529 forecast 2035 |
|---|---|---:|---:|---:|---:|---:|---:|
| 00 | Altstadt und engere Innenstadt | – | 59,260 | – | – | 2,480 | 57,870 |
| 01 | Weiterer Innenstadtgürtel Süd | (97,350) | 95,390 | −1,960 | −2.0 % | 3,550 | 94,660 |
| 02 | Weiterer Innenstadtgürtel West/Nord/Ost | (92,990) | 92,080 | −910 | −1.0 % | 2,730 | 89,120 |
| 03 | Südöstliche Außenstadt | 48,086 | 47,480 | −606 | −1.3 % | 1,980 | 45,280 |
| 04 | Südliche Außenstadt | – | 57,160 | – | – | 11,350 | 54,580 |
| 05 | Südwestliche Außenstadt | 48,176 | 46,880 | −1,296 | −2.7 % | 1,730 | 43,991 |
| 06 | Westliche Außenstadt | 34,170 | 40,050 | +5,880 | +17.2 % | 12,280 | 46,840 |
| 07 | Nordwestliche Außenstadt | 35,181 | 40,120 | +4,939 | +14.0 % | 8,960 | 44,580 |
| 08 | Nordöstliche Außenstadt | 29,022 | 27,820 | −1,202 | −4.1 % | 1,510 | 27,800 |
| 09 | Östliche Außenstadt | 49,095 | 48,470 | −625 | −1.3 % | 2,550 | 48,610 |
| | **City** | 546,397 (forecast base 542,966) | **554,700** | +11,740 (vs base) | +2.2 % | 49,130 | 553,300 |

The city row comes from M558 PDF pp. 1, 6 and 8 and M529 p. 1. The M529 values add up to 553,331 against a printed total of 553,300.

**Revision between editions.** In 06, M529 expected 46,840 by 2035; M558 expects 40,050 by 2033. In 07 the figures are 44,580 and 40,120. The new-build assumptions for these two Stadtteile were cut from 15,530 to 12,280 (06) and from 11,910 to 8,960 (07): M529 counted 2022–2035, M558 counts 2025–2033. This is consistent with Tiefes Feld slipping; the city page now gives first residents "ab 2030". 04 was revised upwards, from 54,580 in 2035 to 57,160 in 2033, which fits Lichtenreuth Modul II and the TU module getting building rights in 2025.

**Bezirk level.** Neither edition publishes Bezirk values. To get per-Bezirk numbers, distribute each Stadtteil's change using `newbuild_projects.csv` (which Bezirk the homes go to) plus a uniform trend for the remainder. That would be our own model, not an official number.

---

## 3. Jobs at place of work

| What | Unit | Year | Value | Usable? |
|---|---|---|---|---|
| **SV-Beschäftigte am Arbeitsort, table `WASU_SvBs_AO_zbez`** (added 2026-11-06) | **79 areas** | **2019–2024** | – | **Yes** → `DISTRICT_EMPLOYMENT.jobs_2019..2024`; the model uses 2024 |
| Niederlassungen nach Wirtschaftssektoren, `WASU_Niederlassungen_Wirtschaftssektoren_zbez` | 79 areas | 2019–2024 | – | Yes → `establishments_*` |
| Beschäftigte by sector, Monatsbericht Okt. 2006, Tab. 1 | **87 Bezirke** | 1970 / 1987 / **2005** | 342,000 city | **Yes, but 20 years old** → `jobs.csv` |
| SV-Beschäftigte am Arbeitsort | City | Dec 2022 | 318,577 (Jun 2022: 318,346) | City control total only |
| SV-Beschäftigte am Wohnort | Bezirk / Distrikt | Dec 2022 | 230,314 city | No (residents). Commuter balance +88,263 |
| Bezirksatlas t9, Bezirksdatenblätter "Beschäftigte" | Bezirk | 2022–2025 | – | No (place of residence; e.g. Bezirk 82 Schafhof shows 864) |
| Online tables MBES_J07 etc. (sta_1100) | City | from 2008 | – | City only; the session-bound server could not be scripted |
| NVEP 2025 Strukturdatenprognose (IVV 2012) | Model zones | 2025 forecast | – | Tables not online (Teil 1 of the Langfassung not found) |

**Definition of the 2005 table:** "Beschäftigte": employees **and** self-employed people, including marginal employment. The source is the Unternehmensregister 2005, carried forward with the Erwerbstätigenrechnung (labour-force accounting) by the statistics office. It is therefore **broader** than the SV-Beschäftigte count: 342,000 in 2005 against about 318,600 SV jobs in 2022.

**Known big changes since 2005 that the table misses** (my own knowledge, not checked against sources):
- Bezirk 64 lost the AEG plant (closed 2007) and Quelle (closed 2009); the former Quelle area is now being converted to housing.
- Bezirk 15 Gugelstraße and other industrial sites have shrunk.
- The UTN campus (Bezirk 41/40) is new.
- Nordostpark (82) and Südwestpark (61) are likely to have grown.

### 3a. Update 2026-11-06: the 2019–2024 count

The portal "Nürnberg in Zahlen" (https://online-service2.nuernberg.de/Informationsportal11_nbg/) serves its tables through the DUVA table viewer (`aswn.dll`), which can be scripted after all: `scripts/fetch_nuernberg_statistik.py` reads the HTML tables (one request per year where the table has a year filter). Source of the jobs table: Bayerisches Landesamt für Statistik, Unternehmensregister. Definition: employees subject to social insurance at the place of work, 31 December; no civil servants, self-employed or marginal jobs, so it is narrower than the 2005 count. The values are in `DISTRICT_EMPLOYMENT.jobs_2019` … `jobs_2024`; query them live. The table doesn't name employers, so large one-year moves in an area may be a single employer moving or being reassigned.

**Suggested use (original, before the update):** use the 2005 sector table only as a *spatial distribution*, scaled to the 2022 city total (318,577 SV jobs, or about 342k + growth if self-employed people are included), and correct the few Bezirke listed above by hand. The proper fix is a data request to the Amt für Stadtforschung und Statistik (statistikinfo@stadt.nuernberg.de). They have BA small-area data ("Arbeitsmarktdaten in kleinräumiger Gliederung") and the Unternehmensregister, which they used in 2006.

---

## 4. Development areas

Homes, first occupancy and Bezirk come from the city's WFS (`newbuild_projects.csv`), unless the row says otherwise. Residents are from the city project pages. The "Bezirk" column is from my point-in-polygon assignment, with the share of the polygon area in brackets where a project spans two Bezirke.

| Area | Bezirk (Stadtteil) | Homes | Residents | Timing | Status / transit | Verified? |
|---|---|---:|---:|---|---|---|
| **Lichtenreuth** (ehem. Südbahnhof), Modul I "Hasenbuck Süd" BP 4635 + Modul II "Ingolstädter Str." BP 4652 | 41 / 40 (04) | WFS: 2,287 + 1,298 = 3,585 | Modul I 5,100–6,000; Modul II 2,600 (city page) | WFS first occupancy 2024 / 2025; Kita 2026; tram 7 end of 2028 | Modul I in force since 2019; BP 4652 and 4656 adopted as Satzung on 17 Jul 2025 | Verified |
| **TU Nürnberg (UTN)**, BP 4656, Modul III | 41/40 (04) | Student housing only | ~6,000 students at full build-out *(unverified)* | Groundbreaking May 2026 *(unverified)* | 37 ha (27 ha building land); a jobs and education generator | Verified (area) / unverified (students) |
| **Tiefes Feld** (Kleinreuth/Großreuth), BP 4445 A/B | 60 / 63 (06) | WFS: Südwest+Südost 1,498 (`GP_WE_GES` 1,100) + Nordwest 415 | City: "über 2.000 Wohnungen", about 4,000 residents (an older page says 1,700 homes / 3,500 residents) | City page: first residents "ab 2030"; WFS says 2027 (SW/SO) and 2029 (NW). U3 Kleinreuth opens 2026; Neue Rothenburger Str. by 2028 | 4445 A in force since Oct 2022; 4445 B adopted 29 Apr 2026 | Verified |
| **Former Quelle area**, Fürther Str. 215 + Muggenhofer Str. | 64 (65) (06) | 1,000 + 1,480 | – | WFS 2026 / 2028 | U1 Eberhardshof/Muggenhof | Verified (WFS only) |
| **Wetzendorf**, BP 4641 A Parlerstraße + 4641 B Schleswiger Str. | 72 (70) (07) | City: about 1,110 in total; B about 290. WFS: Schleswiger Str. 350, Bielefelder Str. 304 | About 2,250 (B about 650) | 4641 A in force 15 Jan 2025; B in planning; WFS first occupancy 2027–2028 | – | Verified |
| **Nordwestring** 101-103 / 85-87 | 70 (23) (07) | 290 + 47 | – | 2026 / 2024 | – | Verified (WFS) |
| **Züricher Straße**, BP 4614 | 60 (06) | 446 (wbg: 181, ready spring 2028) | About 1,100 | BP in force since 2018 | U3 Großreuth. Probably WFS "Wallensteinstraße" (148) | Verified (page); WFS match inferred |
| **Lochnerstraße** | 19 (50) (01) | 425 | – | 2028 | – | Verified (WFS) |
| **Sielstraße** | 22 (23) (02) | 400 | – | 2026 | – | Verified (WFS) |
| **Scharrerstraße** | 10/11 (01) | 342 | – | 2024 | – | Verified (WFS) |
| **Hintermayrstraße** | 80/26 (08/02) | 339 | – | 2025 | – | Verified (WFS) |
| **Kellerstraße** (Reichelsdorfer Keller) | 48 (04) | 295 | – | 2026 | – | Verified (WFS) |
| **Ostendstraße 113-121** | 92 (09) | 295 | – | 2024 | – | Verified (WFS) |
| **Marienberg** (east of Flughafenstr., north of Marienbergstr.) | 83/84 (08) | – | – | SEM started 2017, dropped 31 Jan 2024 *(unverified)*; now BP 4671, started 23 Mar 2023 *(unverified)* | Housing, mixed use, commercial along Flughafenstraße | City page verified (no numbers) |
| **Worzeldorf Ortsrand**, BP 4673 | 49 (04) | About 151 (traffic study, Aug 2023) *(unverified)* | – | Draft as of Nov 2025 *(unverified)* | – | Search-only |
| **Kornburg** "Am Bruckweg" (wbg) | 49 (04) | About 130 *(unverified, 2018)* | – | Built around 2018 | – | Search-only |
| **Seeleite** | – | – | – | – | Nothing found | – |
| **Schmalau-Ost**, BP 4575 (commercial) | 78 (07), inferred | – | – | In force (Amtsblatt 17/2023) | About 8 ha of **new commercial land**, a jobs site | Verified |
| **Dorfäckerstraße-Ost**, BP 4506 (commercial) | 72 (07) | – | – | In force (Amtsblatt 17/2018) | About 2.5 ha of new commercial land | Verified |

All 44 WFS projects are in `newbuild_projects.csv`; the table above shows the largest. **The WFS does not cover all new building.** Compare the WFS homes per Stadtteil with the M558 new-build movers (column D): a few movers per home is plausible; far more movers than homes points to projects the layer does not list (in 07, for example, Wetzendorf 4641 A and smaller projects).

---

## 5. Caveats

- **Two different 2024 bases.** M558 projects from a *reduced* base of 542,966; the register count is 546,397 (the difference is a register clean-up, PDF p. 6). Our DB holds the register count (Bezirksatlas). The 2024 values printed in M558 per Stadtteil presumably sit on the reduced base or use a different allocation; M558 does not say which. Compare **changes**, not levels, between M558 and our DB.
- **Our DB groups Bezirke across Stadtteile.** `DISTRICTS` row 75 "Almoshof/Mooshof/Flughafen (75/85/87)" has `stadtteil_no` = 8. Bezirk 75 belongs to Stadtteil 07, and `BEZIRKE` says so correctly. Stadtteil sums from `DISTRICTS` therefore shift Almoshof's population from 07 to 08. Aggregate via `BEZIRKE` or treat district 75 as split.
- **The jobs table is from 2005** (superseded 2026-11-06 by the 2019–2024 count in section 3a; 2005 stays in the data for its sector split). It is the only place-of-work data per Bezirk that I could find. Its definition (including self-employed and marginal jobs) differs from the SV-Beschäftigte count. Use it only as a distribution, as described in section 3.
- **The WFS layer is a snapshot.** I downloaded it on 2026-10-28. The field names (`N23_*` for homes by type, `GP_ERSTBEZUG` for first occupancy, `GP_WE_GES` for an alternative total) are my reading of the schema; no metadata says what they mean. `N23` probably means "Neubauannahmen 2023", the assumptions behind the forecast. Where `GP_WE_GES` differs from the N23 sum (Tiefes Feld SW/SO 1,100 vs 1,498, Muggenhofer Str. 990 vs 1,480), I used the N23 sum.
- **Bezirk assignment is approximate.** It uses grid-sampled point-in-polygon against our simplified `BEZIRKE` polygons. Shares under 5 % are dropped, and projects on a Bezirk border can flip.
- **Resident figures on city pages disagree.** The Tiefes Feld page alone gives 2,900, "knapp 4.000" and "etwa 4.000". Lichtenreuth has no stated total; Modul I and Modul II add up to about 7,700–8,600, but that sum is mine.
- **No jobs forecast.** Job numbers for UTN, Lichtenreuth commercial space, Schmalau-Ost and Dorfäckerstraße are not given anywhere I looked.

---

## 6. Sources

**Verified (opened or downloaded):**
- M558: Kleinräumige Bevölkerungsvorausberechnung Nürnberg 2025–2033 (Amt für Stadtforschung und Statistik, 2025), 18 pp. City figures on pp. 1, 6, 8, 9 and 17; new-build movers per Stadtteil on pp. 8–9; Stadtteil 2033 values in the text on p. 11 (00–02) and p. 16 (03–09). https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2025/sus2025_m558_bevolkerungsvorausberechnungnurnberg2024_online.pdf
- M558, plain-language version (no Stadtteil numbers). https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2025/sus2025_m558_leichtesprache_deu.pdf
- M529: Kleinräumige Bevölkerungsvorausberechnung Nürnberg 2022–2035 (2022), 20 pp. Stadtteil values on pp. 15 and 18; new-build movers on p. 11; totals on pp. 1 and 11. https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2022/sus_bericht_m529.pdf
- Statistischer Monatsbericht Oktober 2006, "Beschäftigungsentwicklung und Strukturwandel in Nürnberg und Fürth". Method on PDF p. 2; Tab. 1 (Nürnberg, 87 Bezirke, 1970/1987/2005) on PDF p. 3; Fürth table on p. 4. https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/berichte/monatsberichte/2006/statistik_aktuell_200610.pdf
- Innergebietliche Strukturdaten Nürnberg 2023 (excerpt). Labour-market notes on PDF pp. 58–59 (printed pp. 107–108): Wohnortprinzip; SV jobs at place of work Dec 2022 318,577, at place of residence 230,314. Completions and permits per Bezirk 2022 on PDF pp. 48–51 (not extracted). https://www.nuernberg.de/imperia/md/statistik/dokumente/veroeffentlichungen/tabellenwerke/gebietszahlen/innergebietliche_strukturdaten_nuernberg_2023_www-version_geschwarzt.pdf
- Statistics table index sta_1100 (place-of-work tables are city-level only). https://www.nuernberg.de/internet/statistik/sta_1100.html
- WFS Wohnungsneubau, layers `Schwerpunkte_des_Wohnungsneubaus` and `Neubauvorhaben` (the same 44 projects), retrieved 2026-10-28. https://geoportal.nuernberg.de/server/services/Fachdaten/Wohnungsneubau/MapServer/WFSServer · Viewer: https://geoportal.nuernberg.de/masterportal/wohnbau/ · Context page: https://www.nuernberg.de/internet/stadtplanung/nuernberg_baut.html
- Lichtenreuth / Brunecker Straße project page (updated 25 Jun 2026). https://www.nuernberg.de/internet/stadtportal/brunecker_strasse.html
- Press release of 27 Dec 2024 (Lichtenreuth Modul I: 1,300 homes / 3,300 people, 5,100–6,000 planned, tram 7 end of 2028). https://www.nuernberg.de/presse/mitteilungen/pm_24586.html
- Press release of 18 Jul 2025 (BP 4652 / 4656 adopted as Satzung). https://www.nuernberg.de/presse/mitteilungen/pm_25792.html
- Tiefes Feld, Stadtplanung page. https://www.nuernberg.de/internet/stadtplanung/tiefesfeld.html
- Tiefes Feld, city portal page (updated 25 Jun 2026; "ab 2030", U3 Kleinreuth 2026). https://www.nuernberg.de/internet/stadtportal/tiefes_feld.html
- Wetzendorf. https://www.nuernberg.de/internet/stadtplanung/wetzendorf.html
- Züricher Straße. https://www.nuernberg.de/internet/stadtplanung/zuericherstr.html
- Schmalau-Ost. https://www.nuernberg.de/internet/stadtplanung/schmalau.html
- Dorfäckerstraße-Ost. https://www.nuernberg.de/internet/stadtplanung/dorfaeckerstr.html
- Stadtentwicklung Marienberg (no numbers). https://www.nuernberg.de/internet/stadtportal/behoerdenwegweiser/dienstleistung/stadtentwicklung_marienberg.html
- NVEP 2025 Schlussbericht Kurzfassung (Strukturdatenprognose described, no tables). https://online-service.nuernberg.de/viewer/api/v1/records/07056257/files/source/nvep2025_schlussbericht_kurzfassung.pdf
- NVEP 2025 Schlussbericht Langfassung Teil 7 (table of contents only lists 2.2 Strukturdatenprognose). https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/vpl/nvep2025_schlussbericht_langfassung_teil_7_bewertung_e-planfaelle_folgekosten_zusammenfassung.pdf

**Unverified (search results only):**
- UTN about 6,000 students at full build-out; groundbreaking May 2026. https://www.utn.de/files/2025/02/2025_02_13_Hintergrundinfo_Technische_Universitaet_Nuernberg-D.pdf · https://www.bayern.de/pdf/printpdf.php?id=195308
- Marienberg SEM dropped on 31 Jan 2024; BP 4671 started on 23 Mar 2023 (search summary).
- Worzeldorf Ortsrand BP 4673, about 151 homes. https://www.nuernberg.de/imperia/md/stadtplanung/bet_oeausl/16_4673_worzeldorfortsrand_oea_verkehrsmengenermittlung.pdf
- Kornburg "Am Bruckweg", about 130 homes (2018). https://spd-stadtratsfraktion.nuernberg.de/uploads/media/Antrag_Kornburg_Nord_Ost.pdf
- NVP Analyse 2003 with Verkehrszellen (not opened). https://www.nuernberg.de/imperia/md/verkehrsplanung/dokumente/vpl/nvp_analyse_2003_langfassung.pdf
- Bezirksdatenblätter 2022–2025 (the "Beschäftigte" figure appears to be by place of residence). https://www.nuernberg.de/imperia/md/statistik/dokumente/bezirksdatenblatt/nbg/82-schafhof.pdf
