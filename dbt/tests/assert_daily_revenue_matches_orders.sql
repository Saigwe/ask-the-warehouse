-- Dashboard-vs-model check in miniature: the daily report must add up to the order fact.
select 1
from (select sum(net_revenue_usd) as r from {{ ref('rpt_daily_revenue') }}) a
cross join (select sum(net_revenue_usd) as r from {{ ref('fct_orders') }}) b
where abs(a.r - b.r) > 0.005
