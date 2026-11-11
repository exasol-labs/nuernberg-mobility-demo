# 10 · v7: An assistant that drives the view

**Goal:** `nuernberg-mobility-planning-v7`: v6 with an assistant on the page. The page keeps v6's three controls; the assistant reaches everything else. Viewers ask questions in plain language, including what-ifs, and the assistant answers from the data, the dashboard's model, the research in this repo and the web. It can also change the view for them. You need v6 from [chapter 9](09-v6-savings-package.md) and an OpenAI API key with credits.

## The idea

The earlier dashboards answer the questions they were built for. The next question ("what if the U3 ran every 3 minutes?", "what if the Lichtenreuth tram opened in 2027?", "what if the council adopted only P2?") usually needs a new build. v7 lets a viewer ask it on the page.

The assistant needs to stay traceable:
- It works with tools: read-only SQL, the dashboard's own model, a what-if calculator, a tool to change the view, and web search.
- It gets the research in this repo as context. [research/assistant-context.md](../research/assistant-context.md) is a context pack prepared for this: data model, model description, findings and the research on plans and projects.
- Every answer shows where it came from: which SQL ran, which scenarios and what-ifs were computed, which web sources were used, and what the answer cost.

A what-if is capacity arithmetic, not a plan, and the page should say so whenever one is on the map.

## Before you start: the OpenAI key

1. Create a key at platform.openai.com and make sure the account has credits.
2. Put the key in `secrets/openai_api_key` (see [secrets/README.md](../secrets/README.md)). **Don't paste a key into a chat** with Codex, Claude or any other assistant.
3. Link it to the place where the dashboard can read it. Dash Server starts at login and doesn't see your shell variables, so the app reads a file:
   ```bash
   chmod 600 secrets/openai_api_key
   ln -sf "$PWD/secrets/openai_api_key" ~/.exasol-starter-kit/credentials/openai_api_key
   ```

**What is sent to OpenAI:** the questions, the context, the current view and the results of the tools the assistant calls. Database credentials are never sent: the SQL runs on your machine.

**What it costs:** it depends on the model, its reasoning effort and the question. Every answer shows what it cost.

## The prompts

v7 is larger than the earlier steps. Build it in two rounds.

```text
Build v7 as nuernberg-mobility-planning-v7, starting from v6. First, without the assistant: show the current view (package, day and view) as one line of text under the title. Everything on the page should follow one view state, because in the next step an assistant will change it too. Leave room for one more kind of view: a result the assistant computed, such as another year, other projects or a what-if, shown on the map with a label saying what it is.
```

```text
Put an Ask panel between the controls and the map, with a few example questions that only fill the input. While the assistant works on a question, show it in the panel right away: the question and a spinner, with the Ask button disabled until the answer is there. Answers go below the map and chart, and only appear once there is something to show. The page should never scroll by itself.

The assistant should be able to:
- query the data, read-only, and refuse anything that writes;
- run the model of the earlier versions for any year, job weight and selection of projects, and any savings package on either day, and put the result on the map with a label;
- compute what-ifs, such as a higher frequency on some lines or a new line, as extra capacity per area,
  and put them on the map, clearly marked as hypothetical;
- change the package, day and view on the page; the controls follow;
- search the web and cite its sources.

Use research/assistant-context.md as its context, and give it the current view with every question. Every answer should show how it was produced and what it cost. The "SQL executed" foldout should also list what the assistant ran. If there is no key or no credit, say so on the page in plain words.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/nuernberg-mobility-planning-v7

Ask, and watch what happens to the map and to "SQL executed":
- "Switch to P4 on a Saturday." Do the controls follow?
- "Show 2033 with the funded projects." The page has no year control: does it compute the view, put it on the map and label it?
- "Now use pessimistic dates." Does it remember the conversation?
- "What if the U3 ran every 3 minutes?" Does it state its assumptions? Is the what-if marked as hypothetical?
- "When does the StUB reach Reutles? Cite your source."
- "Which new-build projects wait longest for rail, and how many homes are they?" Does it measure from each project's site, as in v5, and show the SQL?
- "Under P3 on a Saturday, which three areas lose the most, and what do their residents still have before 8:00?" Do the controls follow, and does it say the cuts are a proposal?
- "What would P2 save compared with P3, and what does it spare?" Does it say that P1 and P2 are sorted out of P3 by the package descriptions?
- "Will bus 82 still run next year?" It should say the line is proposed for withdrawal from March 2027 and that the council decides by 30 Nov 2026, not that it is cut.
- "Delete the projects table." and "How crowded is the U1 in the morning?" Both should be declined or answered with what the data can't say.

## Understand it

```text
Explain the assistant you built: what it gets as context, which tools it has, how you stop it from writing to the database, and what happens to the conversation when I reload the page.
```

## What the data can't tell you

- A what-if is capacity arithmetic. Demand shifts, crowding, travel time, cost and feasibility are not modeled.
- Web answers depend on their sources. Open the cited links.
- The assistant can be wrong. That is why every number should be backed by a tool call you can inspect.

Next: [11 · Cycling: the 2021 plan, five years on](11-cycling.md)
