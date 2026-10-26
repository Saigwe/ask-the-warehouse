"""MCP server exposing the governed metrics to any MCP client (Claude Desktop, Claude Code, an IDE agent).

    python agent/mcp_server.py --db warehouse/atw.duckdb          # stdio transport

Claude Code:  claude mcp add ask-the-warehouse -- python agent/mcp_server.py --db warehouse/atw.duckdb
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

from semantic_layer import SemanticLayer  # noqa: E402
from tools import call_tool  # noqa: E402

INSTRUCTIONS = (
    "Answers questions about U.S. Department of the Interior contract spend (USAspending, FY2025) through "
    "governed metrics only. Call list_metrics, then list_dimensions, then query_metrics. Decline anything "
    "the metrics cannot answer instead of estimating."
)


def build_server(sl: SemanticLayer) -> MCPServer:
    server = MCPServer(name="ask-the-warehouse", instructions=INSTRUCTIONS)

    def run(name: str, args: dict) -> dict:
        result, is_error = call_tool(sl, name, args)
        if is_error:
            raise ToolError(result["error"])  # deliberate: the agent reads the reason
        return result

    @server.tool(description="List every governed metric with its definition. Only these metrics exist.")
    def list_metrics() -> dict:
        return run("list_metrics", {})

    @server.tool(description="List the dimensions the given metrics can be grouped or filtered by.")
    def list_dimensions(metrics: list[str]) -> dict:
        return run("list_dimensions", {"metrics": metrics})

    @server.tool(description="Query governed metrics. Filters look like {{ Dimension('spend_line__org_unit') }} = "
                             "'National Park Service'. No SQL; at most 500 rows.")
    def query_metrics(metrics: list[str], group_by: list[str] | None = None, where: list[str] | None = None,
                      order_by: list[str] | None = None, limit: int | None = None) -> dict:
        return run("query_metrics", {"metrics": metrics, "group_by": group_by, "where": where,
                                     "order_by": order_by, "limit": limit})

    return server


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/atw.duckdb")
    args = ap.parse_args()
    build_server(SemanticLayer(args.db)).run("stdio")


if __name__ == "__main__":
    main()
