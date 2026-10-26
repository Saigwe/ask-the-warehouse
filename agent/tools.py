"""The four tools an agent gets. One definition, served two ways: over MCP (mcp_server.py) and in-process
for the Claude agent loop (agent.py). There is no tool that runs SQL.
"""
from __future__ import annotations

import datetime as dt
import decimal
import json

from semantic_layer import MAX_ROWS, GuardrailError, SemanticLayer

STRING_LIST = {"type": "array", "items": {"type": "string"}}

TOOL_SPECS = [
    {"name": "list_metrics",
     "description": "List every governed metric with its definition. Call this first; only these metrics exist.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "list_dimensions",
     "description": "List the dimensions you can group or filter the given metrics by, e.g. spend_line__org_unit, "
                    "supplier__parent_supplier_name, metric_time__month.",
     "input_schema": {"type": "object", "properties": {"metrics": STRING_LIST}, "required": ["metrics"],
                      "additionalProperties": False}},
    {"name": "query_metrics",
     "description": "Query governed metrics. group_by and order_by use dimension names from list_dimensions "
                    "(prefix '-' in order_by for descending). Each where filter looks like "
                    "{{ Dimension('spend_line__org_unit') }} = 'National Park Service' or "
                    "{{ TimeDimension('metric_time', 'day') }} >= '2025-01-01'. No SQL. "
                    f"Returns at most {MAX_ROWS} rows.",
     "input_schema": {"type": "object", "properties": {
         "metrics": STRING_LIST, "group_by": STRING_LIST, "where": STRING_LIST, "order_by": STRING_LIST,
         "limit": {"type": "integer"}}, "required": ["metrics"], "additionalProperties": False}},
    {"name": "decline",
     "description": "Decline a request the governed metrics cannot answer, or should not (writes, raw data dumps, "
                    "undefined metrics, personal data). Give the reason.",
     "input_schema": {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"],
                      "additionalProperties": False}},
]


def _json_value(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


def call_tool(sl: SemanticLayer, name: str, args: dict) -> tuple[dict, bool]:
    """Run one tool. Returns (result, is_error). A guardrail refusal is a readable error, not an exception."""
    try:
        if name == "list_metrics":
            return {"metrics": sl.list_metrics()}, False
        if name == "list_dimensions":
            return {"dimensions": sl.list_dimensions(args["metrics"])}, False
        if name == "query_metrics":
            res = sl.query(args["metrics"], args.get("group_by"), args.get("where"), args.get("order_by"), args.get("limit"))
            return {"columns": res.columns, "rows": [[_json_value(v) for v in r] for r in res.rows]}, False
        if name == "decline":
            return {"declined": args.get("reason", "")}, False
        return {"error": f"unknown tool {name!r}"}, True
    except GuardrailError as e:
        return {"error": f"refused by guardrail: {e}"}, True
    except Exception as e:  # MetricFlow could not compile the request
        return {"error": f"{type(e).__name__}: {str(e)[:400]}"}, True


def dumps(result: dict) -> str:
    return json.dumps(result, default=str)
