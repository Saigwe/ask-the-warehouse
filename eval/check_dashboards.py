"""Every number a dashboard shows must equal the semantic layer's number for the same metric and slice.

This is the Power BI data-validation idea, in code: each dashboard table is listed with its grain and which
metric each column claims to show. The check queries the semantic layer at that grain and compares cell by
cell (to the cent, ratios to 1e-9). `rpt_dashboard_legacy_spend` is deliberately wrong and must be caught:
the check fails if it ever passes, so the test can't quietly stop testing anything.

Usage: python eval/check_dashboards.py --db warehouse/atw.duckdb --out results/dashboard_check.md
"""
from __future__ import annotations

import argparse
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
from semantic_layer import SemanticLayer  # noqa: E402

DASHBOARDS = [
    {"table": "gold.rpt_dashboard_category_quarter", "grain": {"category": "spend_line__category",
                                                              "fiscal_quarter": "spend_line__fiscal_quarter"},
     "columns": {"net_spend_usd": "net_spend", "gross_obligations_usd": "gross_obligations",
                 "contract_actions": "contract_actions", "active_suppliers": "active_suppliers",
                 "not_competed_share": "not_competed_share"}},
    {"table": "gold.rpt_dashboard_org_unit", "grain": {"org_unit": "spend_line__org_unit"},
     "columns": {"net_spend_usd": "net_spend", "deobligations_usd": "deobligations",
                 "small_business_share": "small_business_share"}},
    {"table": "gold.rpt_dashboard_legacy_spend", "grain": {"org_unit": "spend_line__org_unit"},
     "columns": {"net_spend_usd": "net_spend", "small_business_share": "small_business_share"},
     "expect_mismatch": True},
]


def same(a, b) -> bool:
    if a is None or b is None or (isinstance(a, float) and math.isnan(a)):
        return (a is None or (isinstance(a, float) and math.isnan(a))) and (b is None or (isinstance(b, float) and math.isnan(b)))
    a, b = float(a), float(b)
    return abs(a - b) <= (1e-9 if abs(b) < 1 else 0.01)


def check(sl: SemanticLayer, dash: dict) -> list[dict]:
    keys, dims = list(dash["grain"]), list(dash["grain"].values())
    cols, metrics = list(dash["columns"]), list(dash["columns"].values())
    shown = {tuple(r[:len(keys)]): r[len(keys):]
             for r in sl.sql(f"select {', '.join(keys + cols)} from {dash['table']}")}
    res = sl.query(metrics, dims, limit=500)
    order = [res.columns.index(c) for c in dims + metrics]
    governed = {tuple(r[i] for i in order[:len(dims)]): [r[i] for i in order[len(dims):]] for r in res.rows}
    out = []
    for c, col in enumerate(cols):
        bad = [k for k in set(shown) | set(governed)
               if k not in shown or k not in governed or not same(shown[k][c], governed[k][c])]
        example = ""
        if bad:
            k = sorted(bad, key=str)[0]
            example = f"{' / '.join(map(str, k))}: dashboard {shown.get(k, [None] * len(cols))[c]}, semantic layer {governed.get(k, [None] * len(cols))[c]}"
        out.append({"column": col, "metric": metrics[c], "cells": len(shown), "mismatched": len(bad), "example": example})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/atw.duckdb")
    ap.add_argument("--out", default="results/dashboard_check.md")
    args = ap.parse_args()
    sl = SemanticLayer(args.db)

    lines = ["# Dashboard numbers vs the semantic layer", "",
             "| Dashboard | Column | Metric | Cells | Mismatched | Example |", "|---|---|---|---:|---:|---|"]
    problems = []
    for dash in DASHBOARDS:
        rows = check(sl, dash)
        mismatched = any(r["mismatched"] for r in rows)
        if mismatched != dash.get("expect_mismatch", False):
            problems.append(dash["table"])
        for r in rows:
            lines.append(f"| `{dash['table']}`{' (planted bug)' if dash.get('expect_mismatch') else ''} | {r['column']} | "
                         f"{r['metric']} | {r['cells']} | {r['mismatched']} | {r['example']} |")
    lines += ["", "Result: " + ("PASS. Real dashboards match to the cent; the planted legacy dashboard is caught."
                                if not problems else f"FAIL: {problems}")]
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
