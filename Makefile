PY ?= python
DB ?= warehouse/atw.duckdb
SPEND_CUBE ?= ../procurement-spend-cube/warehouse/spend.duckdb
DBT = cd dbt && DUCKDB_PATH=../$(DB) dbt

.PHONY: all load dbt check fixture-all fixture agent-eval mcp clean

all: load dbt check   ## real USAspending spend lines from project 10 (build that first)

load:
	$(PY) ingestion/load_spend_lines.py --source $(SPEND_CUBE) --db $(DB)

dbt:
	$(DBT) build --profiles-dir .

check:   ## semantic layer vs gold SQL, guardrails, dashboards, MCP server and agent loop
	$(PY) eval/run_eval.py --db $(DB) --mode reference
	$(PY) eval/check_dashboards.py --db $(DB)
	ATW_DB=$(DB) $(PY) -m pytest -q tests

fixture-all:   ## synthetic fixture, no download (CI)
	$(MAKE) fixture dbt check DB=warehouse/fixture.duckdb

fixture:
	$(PY) tests/fixtures/make_fixture.py --db $(DB)

agent-eval:   ## the Claude agent on the benchmark; needs Anthropic credentials and costs money
	$(PY) eval/run_eval.py --db $(DB) --mode agent

mcp:
	$(PY) agent/mcp_server.py --db $(DB)

clean:
	rm -rf warehouse dbt/target dbt/logs
