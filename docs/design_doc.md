# Design doc: "Ask the Warehouse": Semantic Layer + AI Agent

| | |
|---|---|
| **Author** | Stanley Igwe |
| **Status** | Core build complete; agent evaluation pending an API key |
| **Last updated** | 2026-10-26 |

## 1. Problem and users
- **Users:** procurement analysts, finance leads reading dashboards, and anyone asking an AI assistant about spend.
- **Questions they need answered:** how much was spent, by whom, on what, how competitively, and with which suppliers.
- **Current pain (scenario):** the bureau dashboard shows $408.7M for the Bureau of Indian Affairs, the finance pack shows $365.7M, and a chatbot over raw tables gives a third number. All three are "spend".

## 2. Requirements
| Type | Requirement |
|---|---|
| Functional | Each metric is defined once; dashboards, analysts and agents read it through the same layer. |
| Data quality | Dashboard cells equal governed metrics to the cent; the fact reconciles to the raw load. |
| Safety | The agent cannot run SQL, read raw tables, write, or pull bulk rows; refusals are explained. |
| Latency | A metric query answers in well under a second (p95 26 ms on 42k lines). |
| Scale | 42k lines today; MetricFlow compiles the same requests to Snowflake/BigQuery/Databricks at 10x and beyond. |

## 3. Design
- **Layers:** bronze (project 10's spend lines) → silver (typed, governed labels) → gold (fact, supplier dimension, time spine, dashboard tables) → MetricFlow semantic layer.
- **Key choices:** obligations and de-obligations are split in the fact, so "net" vs "gross" is a metric choice, never a dashboard formula. The guardrails sit in front of MetricFlow, so a request is validated before any SQL exists. The benchmark's answers are hand-written SQL, so a wrong metric definition fails the eval instead of agreeing with itself.

## 4. Options considered
| Decision | Options | Chosen | Why |
|---|---|---|---|
| Semantic layer | MetricFlow; Cube; hand-rolled SQL views | MetricFlow | Lives in the dbt project, compiles per warehouse, and is what dbt Cloud's Semantic Layer serves. |
| Agent interface | Text-to-SQL; metrics API via MCP | Metrics via MCP | No SQL means no injection, no raw-table reads and one definition per number; any MCP client can use it. |
| Eval answers | Compare to the semantic layer; independent SQL | Independent SQL | Otherwise a wrong definition scores 100%. |
| Dashboard test | Manual spot checks; cell-by-cell check in CI | CI check + planted bug | Proves the check works on every run. |

## 5. Risks and what I'd change at 10x scale
- The reference benchmark proves the layer, not the LLM. The agent run (`make agent-eval`) should be tracked per model and per prompt change, with cost per question.
- Questions needing a metric filter ("categories over $1B") aren't supported by the filter grammar yet; add `Metric()` filters with the same validation.
- At 10x: run MetricFlow against the cloud warehouse, cache frequent queries, and add per-user row-level permissions in the MCP server.
