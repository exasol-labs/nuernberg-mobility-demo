# When rail reaches the new homes, and what is under construction meanwhile

Methods behind chapter 8 (v5, the timing gap) and the construction section of the corridor briefings (chapter 12), on `NUERNBERG_DATASET` with the read-only SQL below. No results are stored here: run the queries live. Reference weekday Wednesday 21 Oct 2026. Walking distances as in the model: 300 m for tram, 600 m for U-Bahn, S-Bahn and regional rail, in EPSG:25832 metres.

## 1. Is growth already under way?

Compare, for the new-build areas (the Lichtenreuth group 41/42/43, Eberhardshof, Großreuth b. Schweinau, Höfen, Wetzendorf), the residents counts 2023–2025 (`DISTRICT_POPULATION`) with the model's straight line from the 2024 count to `pop_2033_model`, and with the years the new homes are first occupied (`NEWBUILD_PROJECTS`). Where homes are first occupied from 2026, the counts can't show them yet.

Background on the two largest sites: the Lichtenreuth group is the railway land of the former Südbahnhof; Eberhardshof had AEG (closed 2007) and Quelle (closed 2009). Jobs per area over time are in `DISTRICT_EMPLOYMENT` (2019–2024) and the 2005 table (see [district-growth.md](district-growth.md)).

The building statistics (`DISTRICT_HOUSING`) give homes permitted and completed per area and year. Completions are recorded when the builder reports them, so they can lag behind the residents count.

## 2. The timing gap (v5)

`NEWBUILD_PROJECTS.centroid_lat/lon` is the area-weighted centre of each project's site on the city's new-homes map (WFS `Wohnungsneubau:Schwerpunkte_des_Wohnungsneubaus`, retrieved 6 Nov 2026). Distances are from that point.

The query below returns, per project, whether a U-Bahn, tram or S-Bahn stop is within walking distance today, and the first year a dated (or any) project station comes within walking distance. Compare that year with the project's first occupancy to get the gap.

```sql
WITH nb AS (
  SELECT "project_id", MAX("project_name") AS name, MAX("homes_total") AS homes, MAX("first_occupancy") AS first_occ,
         ST_TRANSFORM(CAST('POINT(' || CAST(MAX("centroid_lon") AS DECIMAL(9,6)) || ' ' || CAST(MAX("centroid_lat") AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.NEWBUILD_PROJECTS GROUP BY "project_id"
), rail AS (
  SELECT CASE WHEN "serves_ubahn" = 1 OR "serves_sbahn" = 1 THEN 600 ELSE 300 END AS walk,
         ST_TRANSFORM(CAST('POINT(' || CAST("stop_lon" AS DECIMAL(9,6)) || ' ' || CAST("stop_lat" AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.VGN_STOPS
  WHERE "stop_lat" BETWEEN 49.30 AND 49.58 AND "stop_lon" BETWEEN 10.92 AND 11.30
    AND ("serves_ubahn" = 1 OR "serves_tram" = 1 OR "serves_sbahn" = 1)
), proj AS (
  SELECT "project_id" AS pid, "opening_year_model" AS yr,
         CASE WHEN "funded" = 1 OR "opening_year_assumed" = 0 THEN 1 ELSE 0 END AS dated,
         CASE WHEN "mode" IN ('U-Bahn', 'S-Bahn', 'Regional rail') THEN 600 ELSE 300 END AS walk,
         ST_TRANSFORM(CAST('POINT(' || CAST("lon" AS DECIMAL(9,6)) || ' ' || CAST("lat" AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.PT_PROJECT_STATIONS WHERE "lat" IS NOT NULL
), served_now AS (
  SELECT DISTINCT nb."project_id" FROM nb JOIN rail r ON ST_DISTANCE(nb.g, r.g) <= r.walk
), yproj AS (
  SELECT nb."project_id", MIN(CASE WHEN p.dated = 1 THEN p.yr END) AS yr_dated, MIN(p.yr) AS yr_any
  FROM nb JOIN proj p ON ST_DISTANCE(nb.g, p.g) <= p.walk GROUP BY 1
)
SELECT nb."project_id", nb.name, nb.homes, nb.first_occ,
       CASE WHEN s."project_id" IS NULL THEN 0 ELSE 1 END AS rail_today, y.yr_dated, y.yr_any
FROM nb LEFT JOIN served_now s ON s."project_id" = nb."project_id"
LEFT JOIN yproj y ON y."project_id" = nb."project_id"
ORDER BY nb.homes DESC
```

## 3. The construction decade (corridor briefings)

`ROADWORKS` (SÖR Baukoordination) holds the planned works with start and end dates and polygons; `is_tram_track = 1` marks tram-track works, `is_cycling = 1` cycle-path works. A work counts as active in every calendar year from its start year to its end year.

**Track closures.** The planned track closures (`kind = 'Schienenstreckensperrung'`, VAG): An der Ehrenhalle, Wodanstraße, Allersberger Straße, Hiroshimaplatz, Schultheißallee and Bayernstraße (24 Mar 2026–1 Jul 2027), and Landgrabenstraße, Am Plärrer, Steinbühler Straße, Steinbühler Tunnel, Dianastraße and Gibitzenhofstraße (2 Jan–30 Nov 2027).

**Tram service next to track works.** Tram stop events on the reference weekday at stops within 50 m of an active tram-track work, as a share of all tram stop events in the city, per year (query below).

**Areas most exposed.** Per area and year: the share of all capacity offered within walking distance that is tram capacity at those stops, and the share of the area's tram capacity. This uses the same `works` and the capacity and walking-distance reach described in [urban-planning.md](urban-planning.md#the-model).

**What the works are.** The Südstadt cluster (Landgrabenstraße, Christuskirche, Heynestraße, 2027–2028) is the track renewal with the new Melanchthonplatz stop. Brunecker Straße, Münchener Straße and Dr.-Luise-Herzberg-Straße (2027–2030) are the Lichtenreuth tram being built. Am Plärrer (2027–2031) is track and overhead-line work at the western hub. Bahnhofsplatz (2030–2031) is "Neubau zusätzliches Gleis", an extra tram track at the Hauptbahnhof. Erlanger Straße (2029–2033, ZV StUB) is the StUB's "Straßenbahnneubau".

```sql
WITH svc AS (
  SELECT "service_id" FROM NUERNBERG_DATASET.VGN_CALENDAR
   WHERE "wednesday" = 1 AND DATE '2026-10-21' BETWEEN "start_date" AND "end_date"
     AND "service_id" NOT IN (SELECT "service_id" FROM NUERNBERG_DATASET.VGN_CALENDAR_DATES
                              WHERE "date" = DATE '2026-10-21' AND "exception_type" = 2)
  UNION
  SELECT "service_id" FROM NUERNBERG_DATASET.VGN_CALENDAR_DATES WHERE "date" = DATE '2026-10-21' AND "exception_type" = 1
), tram_stop AS (
  SELECT st."stop_id", COUNT(*) AS deps
  FROM NUERNBERG_DATASET.VGN_STOP_TIMES st
  JOIN NUERNBERG_DATASET.VGN_TRIPS t ON t."trip_id" = st."trip_id"
  JOIN svc ON svc."service_id" = t."service_id"
  JOIN NUERNBERG_DATASET.VGN_ROUTES r ON r."route_id" = t."route_id"
  WHERE r."line_mode" = 'Tram' GROUP BY 1
), stops AS (
  SELECT ts."stop_id", COALESCE(NULLIF(s."parent_station", ''), s."stop_id") AS station, ts.deps,
         ST_TRANSFORM(CAST('POINT(' || CAST(s."stop_lon" AS DECIMAL(9,6)) || ' ' || CAST(s."stop_lat" AS DECIMAL(9,6)) || ')' AS GEOMETRY(4326)), 25832) AS g
  FROM tram_stop ts JOIN NUERNBERG_DATASET.VGN_STOPS s ON s."stop_id" = ts."stop_id" WHERE s."in_nuernberg" = 1
), works AS (
  SELECT YEAR("start_date") AS y0, YEAR("end_date") AS y1, ST_TRANSFORM(CAST("shape_wkt" AS GEOMETRY(4326)), 25832) AS g
  FROM NUERNBERG_DATASET.ROADWORKS WHERE "is_tram_track" = 1
), yrs AS (
  SELECT 2026 + LEVEL - 1 AS yr FROM DUAL CONNECT BY LEVEL <= 7
), hit AS (
  SELECT DISTINCT y.yr, s."stop_id", s.station, s.deps
  FROM yrs y JOIN works w ON y.yr BETWEEN w.y0 AND w.y1
  JOIN stops s ON ST_DISTANCE(s.g, w.g) <= 50
)
SELECT h.yr, COUNT(DISTINCT h.station) AS stations, SUM(h.deps) AS tram_deps_affected,
       ROUND(100 * SUM(h.deps) / (SELECT SUM(deps) FROM stops), 1) AS pct
FROM hit h GROUP BY h.yr ORDER BY h.yr
```

## 4. Cycling works

Assign the planned cycle-path works (`is_cycling = 1`) to areas by their polygons and compare with the areas thinnest in cycle network per person in the cycling dashboard ([cycling-coverage.md](cycling-coverage.md)).

## Caveats

- Distances to new homes are from a site's centre; large sites span several hundred metres.
- "Next to a track work" (50 m) flags service at risk. SÖR's data doesn't say whether a line runs, is diverted or is replaced by buses; the explicit track closures do.
- The reference weekday already includes the 2026 diversions on Allersberger Straße, so 2026 tram service is slightly below normal.
- Planning dates move; most non-tram works are planned only a year or two ahead.
