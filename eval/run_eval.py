"""Score the benchmark through the semantic layer.

  --mode reference  (CI) send each item's reference request through the guarded semantic layer. Answerable
                    items must equal their hand-written gold SQL; refusal items must be rejected by the guardrails.
                    This proves the metric definitions and the guardrails, with no LLM involved.
  --mode agent      give each question to the Claude agent (agent/agent.py), which may only call the MCP tools.
                    Correct = its last query's result equals the gold SQL; for refusal items, it declines without
                    querying. Needs Anthropic credentials, and costs money: about 54 short agent runs.

An answer matches when every gold column equals some column of the result (same rows, order-insensitive,
numbers rounded), so an agent may add columns but not get a number wrong.

Usage: python eval/run_eval.py --db warehouse/atw.duckdb --mode reference --out results/eval_reference.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import decimal
import json
import pathlib
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "agent"), str(ROOT / "eval")]

from benchmark import BENCHMARK  # noqa: E402
from semantic_layer import GuardrailError, SemanticLayer  # noqa: E402


def norm(v):
    if isinstance(v, (decimal.Decimal, float, int)) and not isinstance(v, bool):
        v = float(v)
        return round(v, 6) if abs(v) < 1000 else round(v, 2)
    if isinstance(v, dt.datetime):
        return v.date().isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    return v


def matches(gold_rows: list[tuple], rows: list[tuple]) -> bool:
    if len(gold_rows) != len(rows) or not gold_rows:
        return len(gold_rows) == len(rows)
    gold_cols = [sorted(map(repr, (norm(r[i]) for r in gold_rows))) for i in range(len(gold_rows[0]))]
    cols = [sorted(map(repr, (norm(r[i]) for r in rows))) for i in range(len(rows[0]))]
    if not all(g in cols for g in gold_cols):
        return False
    # columns line up one by one; also check the pairing within rows, not just each column on its own
    idx = [cols.index(g) for g in gold_cols]
    return sorted(tuple(norm(r[i]) for i in idx) for r in rows) == sorted(tuple(norm(v) for v in r) for r in gold_rows)


def run_reference(sl: SemanticLayer, item: dict) -> dict:
    req = item["request"]
    start = time.perf_counter()
    try:
        res = sl.query(req["metrics"], req["group_by"], req["where"], req["order_by"], req["limit"])
    except GuardrailError as e:
        return {"refused": True, "reason": str(e), "latency_s": time.perf_counter() - start}
    return {"refused": False, "rows": res.rows, "latency_s": res.latency_s, "sql": res.sql}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/atw.duckdb")
    ap.add_argument("--mode", choices=["reference", "agent"], default="reference")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = pathlib.Path(args.out or f"results/eval_{args.mode}.md")

    sl = SemanticLayer(args.db)
    if args.mode == "agent":
        from agent import ask
    results = []
    for item in BENCHMARK:
        got = run_reference(sl, item) if args.mode == "reference" else ask(item["question"], sl)
        if item["kind"] == "answer":
            gold = sl.sql(item["gold_sql"])
            ok = not got["refused"] and matches(gold, got["rows"])
        else:
            ok = got["refused"]
        results.append({"id": item["id"], "kind": item["kind"], "question": item["question"], "correct": ok,
                        "latency_s": round(got["latency_s"], 4), "detail": got.get("reason") or ""})

    answers = [r for r in results if r["kind"] == "answer"]
    refusals = [r for r in results if r["kind"] == "refuse"]
    lat = sorted(r["latency_s"] for r in answers)
    p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)))]
    summary = {
        "mode": args.mode,
        "answer_accuracy": sum(r["correct"] for r in answers) / len(answers),
        "refusal_accuracy": sum(r["correct"] for r in refusals) / len(refusals),
        "answers": len(answers), "refusals": len(refusals),
        "latency_p50_s": statistics.median(lat), "latency_p95_s": p95,
    }
    lines = [
        f"# Benchmark: {args.mode} mode",
        "",
        f"- Answerable questions correct: {sum(r['correct'] for r in answers)}/{len(answers)} ({summary['answer_accuracy']:.0%})",
        f"- Requests that must be refused, refused: {sum(r['correct'] for r in refusals)}/{len(refusals)} ({summary['refusal_accuracy']:.0%})",
        f"- Latency per answer: p50 {summary['latency_p50_s'] * 1000:.0f} ms, p95 {p95 * 1000:.0f} ms",
        "",
        "| ID | Question | Correct | Latency (ms) | Refusal reason |",
        "|---|---|:---:|---:|---|",
    ]
    lines += [f"| {r['id']} | {r['question']} | {'✅' if r['correct'] else '❌'} | {r['latency_s'] * 1000:.0f} | "
              f"{r['detail'][:90].replace('|', '/')} |" for r in results]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"summary": summary, "results": results}, indent=1), encoding="utf-8")
    print("\n".join(lines[:5]))
    failed = [r["id"] for r in results if not r["correct"]]
    if failed:
        print("FAILED:", failed)
    if args.mode == "reference" and failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
