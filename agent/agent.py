"""A Claude agent that answers questions only through the governed tools (the same ones the MCP server serves).

    python agent/agent.py --db warehouse/atw.duckdb "Which bureau spent the most on IT?"

Needs Anthropic credentials (ANTHROPIC_API_KEY or an `ant auth login` profile). Uses claude-opus-5-5 with
adaptive thinking and server-side refusal fallbacks. eval/run_eval.py --mode agent scores it on the benchmark.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import anthropic  # noqa: E402

from semantic_layer import SemanticLayer  # noqa: E402
from tools import TOOL_SPECS, call_tool, dumps  # noqa: E402

MODEL = "claude-opus-5-5"
MAX_TURNS = 8
SYSTEM = (
    "You answer questions about U.S. Department of the Interior contract spending (USAspending.gov, federal "
    "fiscal year 2025: October 2024 to September 2025) for procurement analysts. You can only see the data "
    "through the governed metrics tools. Look up metric definitions with list_metrics and dimensions with "
    "list_dimensions before querying. Answer with one query_metrics call that returns exactly the numbers asked "
    "for. 'Spend' means the net_spend metric unless the user says gross or obligated. If the metrics cannot "
    "answer the question, or it asks to change data, export raw rows, or compute an undefined measure, call "
    "decline instead of approximating. Finish with a one-sentence answer that quotes the numbers."
)


def ask(question: str, sl: SemanticLayer, client: anthropic.Anthropic | None = None) -> dict:
    """Run the agent on one question. Returns the last successful query's rows, whether it declined, and cost data."""
    client = client or anthropic.Anthropic()
    messages = [{"role": "user", "content": question}]
    rows, declined, calls, usage = None, False, [], {"input_tokens": 0, "output_tokens": 0}
    start = time.perf_counter()
    for _ in range(MAX_TURNS):
        response = client.beta.messages.create(
            model=MODEL, max_tokens=16000, system=SYSTEM, tools=TOOL_SPECS, messages=messages,
            thinking={"type": "adaptive"}, output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        )
        usage["input_tokens"] += response.usage.input_tokens
        usage["output_tokens"] += response.usage.output_tokens
        if response.stop_reason in ("end_turn", "refusal", "max_tokens"):
            break
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result, is_error = call_tool(sl, block.name, block.input)
            calls.append({"tool": block.name, "input": block.input, "error": is_error})
            if block.name == "query_metrics" and not is_error:
                rows = [tuple(r) for r in result["rows"]]
            if block.name == "decline":
                declined = True
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": dumps(result), "is_error": is_error})
        messages.append({"role": "user", "content": results})
    answer = next((b.text for b in response.content if b.type == "text"), "")
    return {"refused": declined and rows is None, "rows": rows or [], "answer": answer, "calls": calls,
            "latency_s": time.perf_counter() - start, "usage": usage, "stop_reason": response.stop_reason}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/atw.duckdb")
    ap.add_argument("question")
    args = ap.parse_args()
    out = ask(args.question, SemanticLayer(args.db))
    print(out["answer"])
    print(json.dumps({k: out[k] for k in ("calls", "usage", "latency_s")}, default=str, indent=1))


if __name__ == "__main__":
    main()
