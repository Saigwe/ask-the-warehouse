"""Copy the real spend lines from project 10 (procurement-spend-cube) into `bronze.spend_lines`.

Project 10 loads the USAspending FY2025 Department of the Interior contract archive (41,980 contract
actions) and categorises every line. This project puts a semantic layer and an agent on top of that data,
so it takes the line-level fact as its raw input, not project 10's reports.

Usage (after `make all` in ../procurement-spend-cube)
    python ingestion/load_spend_lines.py --source ../procurement-spend-cube/warehouse/spend.duckdb --db warehouse/atw.duckdb
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import duckdb

COLUMNS = [
    "line_id", "award_id", "action_date", "fiscal_year", "fiscal_quarter", "org_unit", "supplier_id",
    "supplier_name", "parent_supplier_id", "parent_supplier_name", "amount_usd", "psc_code", "category",
    "extent_competed", "business_size",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, default=Path("../procurement-spend-cube/warehouse/spend.duckdb"))
    ap.add_argument("--db", default="warehouse/atw.duckdb")
    args = ap.parse_args()
    if not args.source.exists():
        raise SystemExit(f"{args.source} not found: run `make download all` in procurement-spend-cube first")

    start = time.time()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute(f"attach '{args.source.as_posix()}' as src (read_only)")
    con.execute("create schema if not exists bronze")
    con.execute(f"create or replace table bronze.spend_lines as select {', '.join(COLUMNS)} from src.gold.fct_spend_line")
    n, net = con.execute("select count(*), sum(amount_usd) from bronze.spend_lines").fetchone()
    print(f"bronze.spend_lines {n:,} lines, ${float(net) / 1e9:.2f}B net ({time.time() - start:.1f}s)")


if __name__ == "__main__":
    main()
