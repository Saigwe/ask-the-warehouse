"""README charts from the dashboard tables that eval/check_dashboards.py validates against the semantic layer.
Usage: python charts/make_charts.py [--db warehouse/atw.duckdb] [--out docs/charts]"""
import argparse
from pathlib import Path

import duckdb

import style as st

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--db", default=str(ROOT / "warehouse" / "atw.duckdb"))
ap.add_argument("--out", default=str(ROOT / "docs" / "charts"))
a = ap.parse_args()
OUT = Path(a.out)
con = duckdb.connect(a.db, read_only=True)

SHORT = {"Bureau of Indian Affairs and Bureau of Indian Education": "Indian Affairs and Indian Education",
         "Bureau of Safety and Environmental Enforcement": "Safety and Environmental Enforcement",
         "Office of Surface Mining, Reclamation and Enforcement": "Surface Mining Reclamation",
         "Bureau of Ocean Energy Management": "Ocean Energy Management"}

# 1. Governed dashboard vs the planted legacy dashboard, by bureau
rows = con.execute("""select o.org_unit, o.net_spend_usd::double, l.net_spend_usd::double
                      from gold.rpt_dashboard_org_unit o join gold.rpt_dashboard_legacy_spend l using (org_unit)
                      order by 2 desc limit 8""").fetchall()
f, ax = st.fig(8, 4.0)
y = list(range(len(rows)))
ax.barh([i - 0.19 for i in y], [r[1] / 1e6 for r in rows], 0.36, color=st.S[0], label="Governed dashboard (matches the semantic layer)")
ax.barh([i + 0.19 for i in y], [r[2] / 1e6 for r in rows], 0.36, color=st.S[1], label="Legacy dashboard (planted bug: ignores de-obligations)")
for i, r in enumerate(rows):
    ax.text(r[2] / 1e6 + 20, i + 0.19, f"+{r[2] / r[1] - 1:.0%}", va="center", fontsize=8, color=st.TEXT2)
ax.set_yticks(y, [SHORT.get(r[0], r[0]) for r in rows])
ax.invert_yaxis()
ax.set_xlim(0, max(r[2] for r in rows) / 1e6 * 1.12)
ax.xaxis.set_major_formatter(st.FuncFormatter(lambda v, _: f"${v:,.0f}M"))
ax.grid(axis="y", visible=False)
ax.grid(axis="x", visible=True)
st.head(ax, "The dashboard check catches a legacy dashboard that overstates spend",
        "Net spend by bureau, largest 8; every legacy cell is flagged, every governed cell matches to the cent",
        legend=True, ncol=1, flush=True)
st.save(f, OUT / "dashboard_check.png")

# 2. The governed category x quarter dashboard
q = con.execute("""select category, fiscal_quarter, net_spend_usd::double from gold.rpt_dashboard_category_quarter""").fetchall()
tot = {}
for c, _, v in q:
    tot[c] = tot.get(c, 0) + v
top = sorted(tot, key=tot.get, reverse=True)[:4]
quarters = sorted({r[1] for r in q})
f, ax = st.fig(8, 3.4)
bottom = [0.0] * len(quarters)
for i, cat in enumerate(top + ["All other categories"]):
    vals = [sum(v for c, qq, v in q if qq == qu and (c == cat or (cat == "All other categories" and c not in top))) / 1e6
            for qu in quarters]
    ax.bar(quarters, vals, 0.6, bottom=bottom, color=(st.S + [st.MUTED])[i], label=cat, edgecolor=st.SURFACE, linewidth=1)
    bottom = [b + v for b, v in zip(bottom, vals)]
ax.yaxis.set_major_formatter(st.FuncFormatter(lambda v, _: f"${v:,.0f}M"))
share = bottom[-1] / sum(bottom)
st.head(ax, f"Spend builds to year-end: {quarters[-1][-2:]} is {share:.0%} of the year's net spend", "The governed category-by-quarter dashboard table, every cell checked against the semantic layer",
        legend=True, ncol=3)
st.save(f, OUT / "spend_by_quarter.png")
print(f"wrote charts to {OUT}")
