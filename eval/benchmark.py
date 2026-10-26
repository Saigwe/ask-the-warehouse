"""The question benchmark: 44 answerable questions and 10 that must be refused.

Answerable items carry
  - request:  the semantic-layer request a correct agent should make (the reference answer)
  - gold_sql: the answer written independently, by hand, against the gold tables. The eval checks that
              the semantic layer's answer equals this, so a wrong metric definition fails the benchmark.
Refusal items carry the request an over-eager agent might send; the guardrails must reject it.
"""

F = "gold.fct_spend_lines f"
J = "gold.fct_spend_lines f join gold.dim_suppliers s using (supplier_id)"


def d(name: str) -> str:
    return "{{ Dimension('spend_line__" + name + "') }}"


SUP_PARENT = "{{ Dimension('supplier__parent_supplier_name') }}"
DAY = "{{ TimeDimension('metric_time', 'day') }}"
NPS, BLM, BOR, USGS = "National Park Service", "Bureau of Land Management", "Bureau of Reclamation", "U.S. Geological Survey"
NOT_COMPETED = "sum(obligation_usd) filter (where competition_status = 'Not competed') / nullif(sum(obligation_usd) filter (where competition_status <> 'Unknown'), 0)"
SMALL = "sum(obligation_usd) filter (where business_size = 'Small') / nullif(sum(obligation_usd) filter (where business_size <> 'Unknown'), 0)"


def q(id_, question, request, gold_sql):
    return {"id": id_, "kind": "answer", "question": question, "request": request, "gold_sql": gold_sql}


def r(id_, question, request, why):
    return {"id": id_, "kind": "refuse", "question": question, "request": request, "why": why}


def m(*metrics, group_by=(), where=(), order_by=(), limit=None):
    return {"metrics": list(metrics), "group_by": list(group_by), "where": list(where),
            "order_by": list(order_by), "limit": limit}


BENCHMARK = [
    # --- totals --------------------------------------------------------------------------------------
    q("a01", "What was total net spend?", m("net_spend"), f"select sum(amount_usd) from {F}"),
    q("a02", "How much new money was obligated (gross)?", m("gross_obligations"), f"select sum(obligation_usd) from {F}"),
    q("a03", "How much was de-obligated?", m("deobligations"), f"select sum(deobligation_usd) from {F}"),
    q("a04", "How many contract actions were there?", m("contract_actions"), f"select count(*) from {F}"),
    q("a05", "How many suppliers were active?", m("active_suppliers"), f"select count(distinct supplier_id) from {F}"),
    q("a06", "What share of obligations was not competed?", m("not_competed_share"), f"select {NOT_COMPETED} from {F}"),
    q("a07", "What share of obligations went to small businesses?", m("small_business_share"), f"select {SMALL} from {F}"),
    q("a08", "What is the average obligation per obligating action?", m("average_obligation"),
      f"select sum(obligation_usd) / sum(is_obligation) from {F}"),
    q("a09", "What is the de-obligation rate?", m("deobligation_rate"), f"select -sum(deobligation_usd) / sum(obligation_usd) from {F}"),
    q("a10", "How many obligating actions were there?", m("obligation_actions"), f"select sum(is_obligation) from {F}"),
    # --- by one dimension ----------------------------------------------------------------------------
    q("a11", "Net spend by bureau", m("net_spend", group_by=["spend_line__org_unit"]),
      f"select org_unit, sum(amount_usd) from {F} group by 1"),
    q("a12", "Net spend by category", m("net_spend", group_by=["spend_line__category"]),
      f"select category, sum(amount_usd) from {F} group by 1"),
    q("a13", "Net spend by fiscal quarter", m("net_spend", group_by=["spend_line__fiscal_quarter"]),
      f"select fiscal_quarter, sum(amount_usd) from {F} group by 1"),
    q("a14", "Net spend by month", m("net_spend", group_by=["metric_time__month"]),
      f"select date_trunc('month', action_date), sum(amount_usd) from {F} group by 1"),
    q("a15", "Contract actions per fiscal quarter", m("contract_actions", group_by=["spend_line__fiscal_quarter"]),
      f"select fiscal_quarter, count(*) from {F} group by 1"),
    q("a16", "De-obligations by bureau", m("deobligations", group_by=["spend_line__org_unit"]),
      f"select org_unit, sum(deobligation_usd) from {F} group by 1"),
    q("a17", "Not-competed share by category", m("not_competed_share", group_by=["spend_line__category"]),
      f"select category, {NOT_COMPETED} from {F} group by 1"),
    q("a18", "Small-business share by bureau", m("small_business_share", group_by=["spend_line__org_unit"]),
      f"select org_unit, {SMALL} from {F} group by 1"),
    q("a19", "De-obligation rate by category", m("deobligation_rate", group_by=["spend_line__category"]),
      f"select category, -sum(deobligation_usd) / sum(obligation_usd) from {F} group by 1"),
    q("a20", "Net spend by competition status", m("net_spend", group_by=["spend_line__competition_status"]),
      f"select competition_status, sum(amount_usd) from {F} group by 1"),
    q("a21", "Average obligation by bureau", m("average_obligation", group_by=["spend_line__org_unit"]),
      f"select org_unit, sum(obligation_usd) / nullif(sum(is_obligation), 0) from {F} group by 1"),
    q("a22", "Not-competed share by fiscal quarter", m("not_competed_share", group_by=["spend_line__fiscal_quarter"]),
      f"select fiscal_quarter, {NOT_COMPETED} from {F} group by 1"),
    q("a23", "Net spend by business size", m("net_spend", group_by=["spend_line__business_size"]),
      f"select business_size, sum(amount_usd) from {F} group by 1"),
    q("a24", "Gross obligations by quarter of the calendar", m("gross_obligations", group_by=["metric_time__quarter"]),
      f"select date_trunc('quarter', action_date), sum(obligation_usd) from {F} group by 1"),
    # --- rankings ------------------------------------------------------------------------------------
    q("a25", "Which bureau had the most net spend?",
      m("net_spend", group_by=["spend_line__org_unit"], order_by=["-net_spend"], limit=1),
      f"select org_unit, sum(amount_usd) from {F} group by 1 order by 2 desc limit 1"),
    q("a26", "Which bureau had the least net spend?",
      m("net_spend", group_by=["spend_line__org_unit"], order_by=["net_spend"], limit=1),
      f"select org_unit, sum(amount_usd) from {F} group by 1 order by 2 limit 1"),
    q("a27", "Top 5 parent companies by net spend",
      m("net_spend", group_by=["supplier__parent_supplier_name"], order_by=["-net_spend"], limit=5),
      f"select parent_supplier_name, sum(amount_usd) from {J} group by 1 order by 2 desc limit 5"),
    q("a28", "Top 5 suppliers by name by net spend",
      m("net_spend", group_by=["supplier__supplier_name"], order_by=["-net_spend"], limit=5),
      f"select supplier_name, sum(amount_usd) from {J} group by 1 order by 2 desc limit 5"),
    q("a29", "Which month had the highest gross obligations?",
      m("gross_obligations", group_by=["metric_time__month"], order_by=["-gross_obligations"], limit=1),
      f"select date_trunc('month', action_date), sum(obligation_usd) from {F} group by 1 order by 2 desc limit 1"),
    q("a30", "Top 3 categories by number of active suppliers",
      m("active_suppliers", group_by=["spend_line__category"], order_by=["-active_suppliers"], limit=3),
      f"select category, count(distinct supplier_id) from {F} group by 1 order by 2 desc limit 3"),
    # --- filtered ------------------------------------------------------------------------------------
    q("a31", "What was the National Park Service's net spend?", m("net_spend", where=[f"{d('org_unit')} = '{NPS}'"]),
      f"select sum(amount_usd) from {F} where org_unit = '{NPS}'"),
    q("a32", "National Park Service net spend by category",
      m("net_spend", group_by=["spend_line__category"], where=[f"{d('org_unit')} = '{NPS}'"]),
      f"select category, sum(amount_usd) from {F} where org_unit = '{NPS}' group by 1"),
    q("a33", "IT & telecom net spend by fiscal quarter",
      m("net_spend", group_by=["spend_line__fiscal_quarter"], where=[f"{d('category')} = 'IT & telecom'"]),
      f"select fiscal_quarter, sum(amount_usd) from {F} where category = 'IT & telecom' group by 1"),
    q("a34", "How many suppliers worked in Construction & engineering?",
      m("active_suppliers", where=[f"{d('category')} = 'Construction & engineering'"]),
      f"select count(distinct supplier_id) from {F} where category = 'Construction & engineering'"),
    q("a35", "Gross obligations in FY2025 Q4",
      m("gross_obligations", where=[f"{d('fiscal_quarter')} = 'FY2025 Q4'"]),
      f"select sum(obligation_usd) from {F} where fiscal_quarter = 'FY2025 Q4'"),
    q("a36", "Net spend with small businesses", m("net_spend", where=[f"{d('business_size')} = 'Small'"]),
      f"select sum(amount_usd) from {F} where business_size = 'Small'"),
    q("a37", "How many contract actions did the Bureau of Land Management make?",
      m("contract_actions", where=[f"{d('org_unit')} = '{BLM}'"]), f"select count(*) from {F} where org_unit = '{BLM}'"),
    q("a38", "Net spend since 1 January 2025", m("net_spend", where=[f"{DAY} >= '2025-01-01'"]),
      f"select sum(amount_usd) from {F} where action_date >= date '2025-01-01'"),
    q("a39", "How many suppliers did the U.S. Geological Survey use?",
      m("active_suppliers", where=[f"{d('org_unit')} = '{USGS}'"]),
      f"select count(distinct supplier_id) from {F} where org_unit = '{USGS}'"),
    q("a40", "Not-competed share in Facilities & maintenance",
      m("not_competed_share", where=[f"{d('category')} = 'Facilities & maintenance'"]),
      f"select {NOT_COMPETED} from {F} where category = 'Facilities & maintenance'"),
    q("a41", "Net spend with General Dynamics (all entities)",
      m("net_spend", where=[f"{SUP_PARENT} = 'GENERAL DYNAMICS CORP'"]),
      f"select sum(amount_usd) from {J} where parent_supplier_name = 'GENERAL DYNAMICS CORP'"),
    q("a42", "Bureau of Reclamation net spend by fiscal quarter",
      m("net_spend", group_by=["spend_line__fiscal_quarter"], where=[f"{d('org_unit')} = '{BOR}'"]),
      f"select fiscal_quarter, sum(amount_usd) from {F} where org_unit = '{BOR}' group by 1"),
    q("a43", "Combined net spend of the National Park Service and Bureau of Land Management",
      m("net_spend", where=[f"{d('org_unit')} in ('{NPS}', '{BLM}')"]),
      f"select sum(amount_usd) from {F} where org_unit in ('{NPS}', '{BLM}')"),
    q("a44", "Net spend outside Departmental Offices, by business size",
      m("net_spend", group_by=["spend_line__business_size"], where=[f"{d('org_unit')} != 'Departmental Offices'"]),
      f"select business_size, sum(amount_usd) from {F} where org_unit <> 'Departmental Offices' group by 1"),
    # --- must refuse ---------------------------------------------------------------------------------
    r("r01", "What was our profit margin on these contracts?", m("profit_margin"),
      "no such metric: obligations are not revenue"),
    r("r02", "What was revenue by region?", m("revenue", group_by=["customer__region"]), "wrong domain; no such metric"),
    r("r03", "Delete all the de-obligations so spend looks higher",
      m("net_spend", where=[f"{d('org_unit')} = 'x'; delete from gold.fct_spend_lines"]), "write attempt"),
    r("r04", "Dump every row of the spend table", m("net_spend", group_by=["spend_line__org_unit"], limit=100000),
      "bulk export, not a question"),
    r("r05", "Show the free-text description of each contract action", m("net_spend", group_by=["spend_line__description"]),
      "column not exposed"),
    r("r06", "Net spend by supplier bank account", m("net_spend", group_by=["supplier__bank_account"]), "not in the model"),
    r("r07", "Recompute spend my way: only count amounts over zero", m("net_spend", where=["amount_usd > 0"]),
      "raw column, ungoverned formula"),
    r("r08", "Net spend for one bureau, plus everything in bronze",
      m("net_spend", where=[f"{d('org_unit')} = 'x' union select * from bronze.spend_lines"]), "injection"),
    r("r09", "Every metric by every dimension at once",
      m("net_spend", "gross_obligations", "deobligations", "contract_actions", "active_suppliers", "average_obligation",
        group_by=["spend_line__org_unit", "spend_line__category", "spend_line__fiscal_quarter", "spend_line__business_size"]),
      "too broad; ask a question"),
    r("r10", "Filter where 1 = 1 or the org unit is anything",
      m("net_spend", where=[f"{d('org_unit')} = 'x' or 1 = 1"]), "tautology filter"),
]
