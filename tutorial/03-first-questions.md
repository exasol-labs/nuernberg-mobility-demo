# 3 · First questions

**Goal:** get to know the data together with your agent before it builds anything, and meet three things that make Nürnberg different: a timetable for a whole region, growth that is already under way, and a timetable that changes in December.

Enter the following prompts in your agent. They describe what you want to see; the agent works out how.

## 3.1 What's in the data

```text
What data do we have about Nürnberg here? Give me an overview: what each group of tables describes, how current it is, and what it can't tell us.
```

## 3.2 The timetable

```text
How many scheduled departures are there in Nürnberg on a typical weekday, by mode? Which stations have the most?
```

Watch how the agent works: it shows the SQL, runs it, checks the result for plausibility, then answers. It should name the weekday it uses, Wednesday 21 Oct 2026, and count only the stops inside the city: the feed covers the whole VGN region.

Follow up in your own words, for example:

```text
Which area holds the Hauptbahnhof, and how many people live there?
```

Keep the answer in mind. A busy station in an area with few residents comes back in chapters 4 and 5.

## 3.3 Growth that has already started

```text
Where are people moving in? Compare the population counts for 2023, 2024 and 2025 per area with the city's new-build projects and their first-occupancy year. Which areas are growing fastest right now, and is rail service there yet?
```

Look for the Lichtenreuth group (41/42/43), the new district on the former Südbahnhof next to the new Technische Universität. Its new homes were first occupied in 2024 and 2025, and its tram is planned for 2030. How much did it grow in 2025?

## 3.4 What the reference day misses

```text
The timetable we have ends on 12 December 2026. What changes on 13 December, and which areas will that affect? Use the research in this repo.
```

Tram 7 to Stadtpark opens with the timetable change. It isn't in the feed, so it appears in chapter 8 as a project.

## 3.5 A question the data can't answer

```text
Which area has the worst traffic right now?
```

There is no live traffic, delay or passenger data. The agent says so and offers what the data can show instead.

Next: [4 · v1: a first map](04-v1-residents.md)
