PY ?= python
DB ?= warehouse/ask_the_warehouse.duckdb
DBT = cd dbt && DUCKDB_PATH=../$(DB) dbt

.PHONY: fixture-all bronze-fixture dbt eval-self-check clean

fixture-all: bronze-fixture dbt eval-self-check   ## synthetic fixture, no download (CI)

bronze-fixture:
	$(PY) tests/fixtures/make_fixture.py --db $(DB)

dbt:
	$(DBT) build --profiles-dir .

eval-self-check:
	$(PY) eval/run_eval.py --db $(DB) --self-check

clean:
	rm -rf warehouse dbt/target dbt/logs
