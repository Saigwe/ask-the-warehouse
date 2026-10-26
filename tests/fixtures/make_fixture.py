"""Synthetic `bronze.spend_lines` for CI: same columns and vocabulary (bureaus, categories, quarters,
competition and size codes) as project 10's real USAspending lines, so the benchmark runs unchanged.

Usage: python tests/fixtures/make_fixture.py --db warehouse/fixture.duckdb
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

N = 3_000
UNITS = ["Departmental Offices", "National Park Service", "Bureau of Reclamation", "Bureau of Land Management",
         "U.S. Geological Survey", "U.S. Fish and Wildlife Service"]
CATEGORIES = ["Construction & engineering", "IT & telecom", "Facilities & maintenance", "Professional services",
              "Equipment & supplies", "Logistics & travel"]
COMPETITION = ["FULL AND OPEN COMPETITION", "NOT COMPETED", "COMPETED UNDER SAP", "NOT AVAILABLE FOR COMPETITION"]
PARENTS = ["GENERAL DYNAMICS CORP", "NW CONSTRUCTION, INC", "JACOBS SOLUTIONS, INC"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/fixture.duckdb")
    args = ap.parse_args()
    rng = np.random.default_rng(12)
    sup = rng.zipf(1.5, N) % 250
    date = pd.Timestamp("2024-10-01") + pd.to_timedelta(rng.integers(0, 365, N), unit="D")
    q = ((date.month + 2) % 12) // 3 + 1
    amount = np.round(rng.lognormal(9, 1.5, N), 2)
    amount[rng.random(N) < 0.15] *= -0.4
    parent = [PARENTS[s % 3] if s < 9 else f"SUPPLIER {s:03d} INC" for s in sup]
    df = pd.DataFrame({
        "line_id": [f"T{i:06d}" for i in range(N)], "award_id": [f"A{a:04d}" for a in rng.integers(0, 900, N)],
        "action_date": date.date, "fiscal_year": 2025, "fiscal_quarter": [f"FY2025 Q{x}" for x in q],
        "org_unit": rng.choice(UNITS, N), "supplier_id": [f"UEI{s:09d}" for s in sup],
        "supplier_name": [f"SUPPLIER {s:03d} INC" for s in sup],
        "parent_supplier_id": [f"P{s % 3}" if s < 9 else f"UEI{s:09d}" for s in sup], "parent_supplier_name": parent,
        "amount_usd": amount, "psc_code": "R499", "category": rng.choice(CATEGORIES, N),
        "extent_competed": rng.choice(COMPETITION, N, p=[0.6, 0.15, 0.2, 0.05]),
        "business_size": rng.choice(["SMALL BUSINESS", "OTHER THAN SMALL BUSINESS"], N),
    })
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")
    con.execute("create or replace table bronze.spend_lines as select * replace (cast(amount_usd as decimal(18, 2)) as amount_usd) from df")
    print(f"wrote {N:,} synthetic spend lines to {args.db}")


if __name__ == "__main__":
    main()
