# Dashboard numbers vs the semantic layer

| Dashboard | Column | Metric | Cells | Mismatched | Example |
|---|---|---|---:|---:|---|
| `gold.rpt_dashboard_category_quarter` | net_spend_usd | net_spend | 45 | 0 |  |
| `gold.rpt_dashboard_category_quarter` | gross_obligations_usd | gross_obligations | 45 | 0 |  |
| `gold.rpt_dashboard_category_quarter` | contract_actions | contract_actions | 45 | 0 |  |
| `gold.rpt_dashboard_category_quarter` | active_suppliers | active_suppliers | 45 | 0 |  |
| `gold.rpt_dashboard_category_quarter` | not_competed_share | not_competed_share | 45 | 0 |  |
| `gold.rpt_dashboard_org_unit` | net_spend_usd | net_spend | 11 | 0 |  |
| `gold.rpt_dashboard_org_unit` | deobligations_usd | deobligations | 11 | 0 |  |
| `gold.rpt_dashboard_org_unit` | small_business_share | small_business_share | 11 | 0 |  |
| `gold.rpt_dashboard_legacy_spend` (planted bug) | net_spend_usd | net_spend | 11 | 11 | Bureau of Indian Affairs and Bureau of Indian Education: dashboard 408684907.08, semantic layer 365693674.66 |
| `gold.rpt_dashboard_legacy_spend` (planted bug) | small_business_share | small_business_share | 11 | 11 | Bureau of Indian Affairs and Bureau of Indian Education: dashboard 0.7310607968501524, semantic layer 0.7275386858898534 |

Result: PASS. Real dashboards match to the cent; the planted legacy dashboard is caught.
