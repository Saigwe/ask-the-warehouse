"""The only door an AI agent gets into the warehouse: governed metrics via MetricFlow, never raw SQL.

Guardrails, all checked before MetricFlow compiles anything:
  - metrics must be defined in dbt/models/marts/_semantic.yml (no ad-hoc formulas)
  - group_by and filters may only use dimensions MetricFlow lists for those metrics
  - filters are a small grammar: {{ Dimension('x') }} <op> <literal>, joined by and/or; no SQL keywords
  - at most 5 metrics, 3 group-bys and 500 rows per request
A rejected request raises GuardrailError with a reason the agent can read and act on.
"""
from __future__ import annotations

import os
import pathlib
import re
import time
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[1]
TIME_GRAINS = ("day", "week", "month", "quarter", "year")
MAX_METRICS, MAX_GROUP_BY, MAX_ROWS = 5, 3, 500

_LITERAL = r"(?:'[^';\\]*'|-?\d+(?:\.\d+)?)"
_DIM = r"\{\{\s*(?:Dimension|TimeDimension)\(\s*'([a-z_]+)'(?:\s*,\s*'([a-z]+)')?\s*\)\s*\}\}"
_CONDITION = re.compile(
    rf"^\s*{_DIM}\s*(?:(=|!=|<>|>=|<=|>|<)\s*{_LITERAL}|(?:not\s+)?in\s*\(\s*{_LITERAL}(?:\s*,\s*{_LITERAL})*\s*\))\s*$",
    re.IGNORECASE,
)
_FORBIDDEN = re.compile(r";|--|/\*|\b(select|insert|update|delete|drop|alter|create|attach|copy|union|from|pragma)\b", re.I)


class GuardrailError(ValueError):
    """The request was refused before reaching the warehouse."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple]
    sql: str
    latency_s: float
    request: dict = field(default_factory=dict)


class SemanticLayer:
    def __init__(self, db_path: str | None = None):
        from dbt_metricflow.cli.cli_configuration import CLIConfiguration

        if db_path:
            os.environ["DUCKDB_PATH"] = str(pathlib.Path(db_path).resolve())
        project = ROOT / "dbt"
        self._cfg = CLIConfiguration()
        self._cfg.setup(dbt_profiles_path=project, dbt_project_path=project, configure_file_logging=False)
        self._mf = self._cfg.mf
        self._metrics = {m.name: m for m in self._mf.list_metrics()}
        self._dims: dict[str, set[str]] = {}

    # ---- catalogue (what the agent is allowed to know) -------------------------------------------------
    def list_metrics(self) -> list[dict]:
        return [{"name": m.name, "label": m.label, "description": m.description, "type": m.type.value}
                for m in sorted(self._metrics.values(), key=lambda m: m.name)]

    def list_dimensions(self, metrics: list[str]) -> list[str]:
        self._check_metrics(metrics)
        key = ",".join(sorted(metrics))
        if key not in self._dims:
            names = {d.dunder_name for d in self._mf.list_dimensions(sorted(metrics))}
            names.discard("metric_time__day")
            names |= {f"metric_time__{g}" for g in TIME_GRAINS}
            self._dims[key] = names
        return sorted(self._dims[key])

    # ---- query --------------------------------------------------------------------------------------
    def query(self, metrics: list[str], group_by: list[str] | None = None, where: list[str] | None = None,
              order_by: list[str] | None = None, limit: int | None = None) -> QueryResult:
        from metricflow.engine.metricflow_engine import MetricFlowQueryRequest

        group_by, where, order_by = list(group_by or []), list(where or []), list(order_by or [])
        self.validate(metrics, group_by, where, order_by, limit)
        start = time.perf_counter()
        result = self._mf.query(MetricFlowQueryRequest.create(
            metric_names=metrics, group_by_names=group_by or None, where_constraints=where or None,
            order_by_names=order_by or None, limit=min(limit or MAX_ROWS, MAX_ROWS)))
        table = result.result_df
        return QueryResult(list(table.column_names), [tuple(r) for r in table.rows], result.sql,
                           time.perf_counter() - start,
                           {"metrics": metrics, "group_by": group_by, "where": where, "order_by": order_by, "limit": limit})

    def validate(self, metrics, group_by, where, order_by, limit) -> None:
        self._check_metrics(metrics)
        if len(metrics) > MAX_METRICS or len(group_by) > MAX_GROUP_BY:
            raise GuardrailError(f"at most {MAX_METRICS} metrics and {MAX_GROUP_BY} group-bys per request")
        if limit is not None and not (isinstance(limit, int) and 0 < limit <= MAX_ROWS):
            raise GuardrailError(f"limit must be between 1 and {MAX_ROWS}: this API answers questions, it does not export data")
        allowed = set(self.list_dimensions(metrics))
        bad = [g for g in group_by if g not in allowed]
        if bad:
            raise GuardrailError(f"unknown dimension(s) {bad}; available: {sorted(allowed)}")
        for o in order_by:
            name = o.lstrip("-")
            if name not in metrics and name not in group_by:
                raise GuardrailError(f"order_by {o!r} must be a requested metric or group-by")
        for clause in where:
            if _FORBIDDEN.search(clause):
                raise GuardrailError(f"filter {clause!r} contains SQL; use {{{{ Dimension('name') }}}} = 'value'")
            for cond in re.split(r"\s+(?:and|or)\s+", clause.strip(), flags=re.I):
                match = _CONDITION.match(cond)
                if not match:
                    raise GuardrailError(f"filter {cond!r} must look like {{{{ Dimension('name') }}}} = 'value'")
                dim = match.group(1) + (f"__{match.group(2)}" if match.group(2) else "")
                if match.group(1) not in allowed and dim not in allowed:
                    raise GuardrailError(f"filter dimension {match.group(1)!r} is not available for {metrics}")

    def _check_metrics(self, metrics: list[str]) -> None:
        if not metrics:
            raise GuardrailError("ask for at least one metric")
        unknown = [m for m in metrics if m not in self._metrics]
        if unknown:
            raise GuardrailError(f"metric(s) {unknown} are not defined in the semantic layer; "
                                 f"defined: {sorted(self._metrics)}")

    def sql(self, statement: str) -> list[tuple]:
        """Read-only SQL for the eval's independent gold queries. Never exposed to the agent."""
        return [tuple(r) for r in self._cfg.sql_client.query(statement).rows]
