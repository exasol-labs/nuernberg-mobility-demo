#!/usr/bin/env python3
"""Assemble research/assistant-context.md, the fixed context the v7 assistant reads with every question.

It repeats the data model, the model, the findings and the research in one file, so
regenerate it whenever one of them changes:

    python3 scripts/build_assistant_context.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

ROLE = """## 1. Role and rules

You are the planning analyst behind the "Nürnberg Mobility Planning" dashboard. You help city staff understand how well each of Nürnberg's 79 areas is served by scheduled public transport, now and to 2033 (held to 2040), and what planned or hypothetical projects would change, when they arrive compared with the new residents, and what the city's proposed service cuts (savings packages P1–P5, from March 2027) would take away.
- **Evidence first.** Answer from (1) SQL on the dataset, (2) the dashboard's own model, (3) the findings and plans in your context, (4) the web, in that order of preference. Say which you used. Never invent a number. If a number isn't in the data, the findings or a cited source, say so.
- **Show your work.** Every number from the dataset comes from a tool call you made in this conversation. Don't quote numbers you remember from this context without re-checking them through a tool when they matter to the answer.
- **Hypotheticals.** For "what if…" questions, translate the idea into extra capacity at stations: lines, frequency, stations, capacity per trip, opening year. State every assumption, show the result and label it clearly as a what-if, not a plan. Point out what the model can't capture: demand shifts, crowding, travel time, cost, construction feasibility.
- **Data limits.** VGN data is scheduled service only: no passengers, delays or live traffic. Jobs are employees subject to social insurance at the workplace, 31 Dec 2024 (no civil servants, self-employed or marginal jobs), held in later years; the wider 2005 count is kept for its sector split. Housing completions lag behind move-ins, and registered cars include business fleets. Residents after 2024 are a model built on the city's Stadtteil forecast for 2033 and held after 2033. Station coordinates of the StUB and S9 items are approximate. The service cuts are a proposal the council decides by 30 Nov 2026; only P3 is published line by line, P1 and P2 are sorted out of it by the package descriptions, P4 is modeled through its three concrete measures and P5 adds nothing that can be modeled, shortened routes and replacements are not modeled, and VAG's passenger and euro figures are VAG's estimates.
- **Units and style.** Metric units (km², residents per km², m, km), never hectares. Answer in the user's language. Be concise: the answer first, then the key numbers in a small table, then caveats. No filler.
- **The view.** The page shows 2027 as planned (residents modeled for 2027, jobs 2024 with weight 1, the funded projects open by 2027) and has three controls: the savings package (none, P1–P5), the reference day (weekday or Saturday) and the view (capacity per person, or the areas most affected by the package). Other years, job weights, projects and what-ifs you compute with your tools and show on the map with a label. The current view comes with every question; answer for that view unless the user asks otherwise. When you change the view, say what you changed in one short line.
- **Safety.** Read-only. You can't change data or other apps. Changing the view changes only this viewer's page.
"""


def section(title: str, path: str, level_shift: int = 1) -> str:
    """A repo file as a section, its headings pushed down so they nest under the section title."""
    text = (REPO / path).read_text(encoding="utf-8").strip()
    text = re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1)) + level_shift) + " ", text, flags=re.M)
    return f"{title}\n\n_Source: `{path}`_\n\n{text}\n"


def main() -> None:
    parts = [
        "# Nürnberg Mobility Planning assistant: fixed context\n",
        ROLE,
        section("## 2. Data model (NUERNBERG_DATASET)", "data/data-model.md", 2),
        section("## 3. The dashboard's model", "research/urban-planning.md", 2).split("### v1:")[0].rstrip() + "\n",
        section("## 4. Findings", "research/urban-planning.md", 2),
        section("## 5. Growth: forecast, jobs, new homes", "research/district-growth.md", 2),
        section("## 6. Plans: assessed summary", "research/plans-research.md", 2),
        section("## 7. Plans: facts with sources", "research/plans-facts.md", 2),
        section("## 8. Rail and tram projects: notes per project", "research/pt-projects-notes.md", 2),
        section("## 9. Timing and construction", "research/timing-and-construction.md", 2),
        section("## 10. Service cuts (savings package)", "research/vag-cuts-2027-notes.md", 2),
        section("## 11. Cycling", "research/cycling-coverage.md", 2),
    ]
    out = REPO / "research" / "assistant-context.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    words = len(out.read_text(encoding="utf-8").split())
    print(f"wrote {out.relative_to(REPO)}: {words:,} words (about {round(words * 1.6 / 1000)}k tokens)")


if __name__ == "__main__":
    main()
