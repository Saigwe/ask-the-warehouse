-- What the BI dashboard shows on its category page. Hand-written, as dashboard SQL usually is;
-- eval/check_dashboards.py proves every number equals the semantic layer's.
select
    category,
    fiscal_quarter,
    sum(amount_usd)                                                         as net_spend_usd,
    sum(obligation_usd)                                                     as gross_obligations_usd,
    count(*)                                                                as contract_actions,
    count(distinct supplier_id)                                             as active_suppliers,
    sum(obligation_usd) filter (where competition_status = 'Not competed')
        / nullif(sum(obligation_usd) filter (where competition_status <> 'Unknown'), 0) as not_competed_share
from {{ ref('fct_spend_lines') }}
group by 1, 2
