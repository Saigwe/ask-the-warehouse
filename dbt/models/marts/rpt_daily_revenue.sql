select
    order_date,
    count(*)                as orders,
    sum(net_revenue_usd)    as net_revenue_usd
from {{ ref('fct_orders') }}
group by 1
