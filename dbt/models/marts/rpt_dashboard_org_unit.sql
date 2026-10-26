-- The dashboard's bureau page.
select
    org_unit,
    sum(amount_usd)                                                         as net_spend_usd,
    sum(deobligation_usd)                                                   as deobligations_usd,
    sum(obligation_usd) filter (where business_size = 'Small')
        / nullif(sum(obligation_usd) filter (where business_size <> 'Unknown'), 0) as small_business_share
from {{ ref('fct_spend_lines') }}
group by 1
