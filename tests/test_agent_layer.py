"""Tests for the guardrails, the MCP server and the agent loop. Run against whichever warehouse
ATW_DB points at (the CI fixture, or the real build). No LLM calls: the agent test scripts Claude's replies.
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys
from types import SimpleNamespace

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "agent"), str(ROOT / "eval")]

from run_eval import matches  # noqa: E402
from semantic_layer import GuardrailError, SemanticLayer  # noqa: E402

NPS = "{{ Dimension('spend_line__org_unit') }} = 'National Park Service'"


@pytest.fixture(scope="session")
def sl():
    return SemanticLayer(os.environ.get("ATW_DB", str(ROOT / "warehouse" / "atw.duckdb")))


def test_metric_equals_hand_written_sql(sl):
    res = sl.query(["net_spend", "contract_actions"], where=[NPS])
    gold = sl.sql("select sum(amount_usd), count(*) from gold.fct_spend_lines where org_unit = 'National Park Service'")
    assert matches(gold, res.rows)


@pytest.mark.parametrize("request_", [
    {"metrics": ["revenue"]},
    {"metrics": []},
    {"metrics": ["net_spend"], "group_by": ["spend_line__description"]},
    {"metrics": ["net_spend"], "where": ["amount_usd > 0"]},
    {"metrics": ["net_spend"], "where": [NPS + "; drop table gold.fct_spend_lines"]},
    {"metrics": ["net_spend"], "where": [NPS + " union select * from bronze.spend_lines"]},
    {"metrics": ["net_spend"], "where": [NPS + " or 1 = 1"]},
    {"metrics": ["net_spend"], "where": ["{{ Dimension('supplier__tax_id') }} = '1'"]},
    {"metrics": ["net_spend"], "limit": 10_000},
    {"metrics": ["net_spend"], "order_by": ["-gross_obligations"]},
])
def test_guardrails_refuse(sl, request_):
    with pytest.raises(GuardrailError):
        sl.query(request_["metrics"], request_.get("group_by"), request_.get("where"),
                 request_.get("order_by"), request_.get("limit"))


def test_matches_is_strict_about_numbers_and_pairing():
    gold = [("A", 1.0), ("B", 2.0)]
    assert matches(gold, [("B", 2.0, 9), ("A", 1.0, 9)])      # extra column, other order: fine
    assert not matches(gold, [("A", 2.0), ("B", 1.0)])         # same columns, wrong pairing
    assert not matches(gold, [("A", 1.0), ("B", 2.5)])         # wrong number


def test_mcp_server_serves_governed_tools_only(sl):
    from mcp import Client
    from mcp_server import build_server

    async def run():
        async with Client(build_server(sl)) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            ok = await client.call_tool("query_metrics", {"metrics": ["net_spend"], "where": [NPS]})
            bad = await client.call_tool("query_metrics", {"metrics": ["net_spend"], "where": ["1=1; drop table x"]})
            return names, ok, bad

    names, ok, bad = asyncio.run(run())
    assert names == {"list_metrics", "list_dimensions", "query_metrics"}
    assert not ok.is_error and bad.is_error
    assert "guardrail" in bad.content[0].text


def _reply(stop_reason, *blocks):
    return SimpleNamespace(stop_reason=stop_reason, content=list(blocks),
                           usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def _tool_use(id_, name, input_):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=input_)


class ScriptedClaude:
    """Stands in for anthropic.Anthropic: returns scripted replies and records what the agent sent back."""

    def __init__(self, replies):
        self.replies, self.sent = list(replies), []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.sent.append(kwargs["messages"][-1])
        return self.replies.pop(0)


def test_agent_loop_runs_tools_and_recovers_from_a_refusal(sl):
    from agent import ask

    claude = ScriptedClaude([
        _reply("tool_use", _tool_use("t1", "query_metrics", {"metrics": ["profit"]})),
        _reply("tool_use", _tool_use("t2", "query_metrics", {"metrics": ["net_spend"], "where": [NPS]})),
        _reply("end_turn", SimpleNamespace(type="text", text="The National Park Service spent ...")),
    ])
    out = ask("How much did the National Park Service spend?", sl, client=claude)
    first_result = claude.sent[1]["content"][0]
    assert first_result["is_error"] and "not defined" in json.loads(first_result["content"])["error"]
    assert [c["error"] for c in out["calls"]] == [True, False]
    gold = sl.sql("select sum(amount_usd) from gold.fct_spend_lines where org_unit = 'National Park Service'")
    assert matches(gold, out["rows"]) and not out["refused"]


def test_agent_decline_counts_as_refusal(sl):
    from agent import ask

    claude = ScriptedClaude([
        _reply("tool_use", _tool_use("t1", "decline", {"reason": "writes are not allowed"})),
        _reply("end_turn", SimpleNamespace(type="text", text="I can't change data.")),
    ])
    assert ask("Delete the de-obligations", sl, client=claude)["refused"]
