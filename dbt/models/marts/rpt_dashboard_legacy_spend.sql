-- A deliberately WRONG legacy dashboard, kept to prove the check catches drift: it calls gross obligations
-- "spend" (ignores de-obligations) and computes small-business share on net amounts instead of obligations.
-- eval/check_dashboards.py expects both columns to mismatch the semantic layer.
select
    org_unit,
    sum(obligation_usd)                                                     as net_spend_usd,
    sum(amount_usd) filter (where business_size = 'Small') / sum(amount_usd) as small_business_share
from {{ ref('fct_spend_lines') }}
group by 1
