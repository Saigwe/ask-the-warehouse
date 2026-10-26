# Ingestion

`load_spend_lines.py` copies the line-level fact from [project 10](https://github.com/Saigwe/procurement-spend-cube)
(`gold.fct_spend_line`: 41,980 USAspending contract actions, Department of the Interior, FY2025, already categorised)
into `bronze.spend_lines`, keeping the 15 columns this project uses.

```bash
cd ../procurement-spend-cube && make download all && cd -
python ingestion/load_spend_lines.py --source ../procurement-spend-cube/warehouse/spend.duckdb --db warehouse/atw.duckdb
```

CI uses `tests/fixtures/make_fixture.py`, which writes the same table and vocabulary from a fixed seed.
