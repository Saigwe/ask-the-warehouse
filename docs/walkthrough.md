# 3-minute walkthrough: Ask the Warehouse: Semantic Layer + AI Agent

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, dbt/ (semantic models), agent/, results/eval_reference.md, GitHub Actions.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | 'Spend' means three numbers on three dashboards, and a chatbot over raw tables invents a fourth. Here, 14 metrics are defined once in a dbt semantic layer, and an AI agent gets those metrics and no SQL. |
| 0:20–0:45 | README intro and the Data section | At a global management consultancy I built governed metrics and Power BI validation models, so every client saw the same numbers. This rebuilds that on $6.57 billion of public federal spend. No client data is used. |
| 0:45–1:10 | The MetricFlow definitions in `dbt/` | Each metric is defined once: gross, net and net of credits are separate, named and documented. |
| 1:10–1:35 | The MCP server tools in `agent/` | The agent has three tools: list metrics, list dimensions and query metrics. Guardrails reject undefined metrics, raw columns, SQL in filters and bulk exports. |
| 1:35–2:00 | `results/dashboard_check.md` | A check compares 258 dashboard cells to the semantic layer. It catches a planted legacy dashboard reporting gross as spend: $408.7M against $365.7M net. |
| 2:00–2:30 | `results/eval_reference.md` | The benchmark has 54 questions with answers hand-written in SQL. 44 of 44 are answered correctly through the governed layer, and 10 of 10 bad requests are refused, in 17 ms at the median. |
| 2:30–2:45 | `docs/design_doc.md`, the options table | The decision I'd defend in an interview: Give the AI governed metrics instead of tables, so it can't produce a number the business never defined. |
| 2:45–3:00 | Back to the README top | For a data team adopting AI, that means analysts, dashboards and assistants get the same answer, and a wrong dashboard fails CI. The repo, numbers and design doc are linked under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `make fixture-all` once before recording, so CI-style output is fresh if you show it.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "synthetic" out loud wherever the README labels data as synthetic.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the roadmap line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
