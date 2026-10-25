-- One row per order. Net revenue is defined here, once: refunded orders count as zero.
select
    o.order_id,
    o.customer_id,
    c.region,
    o.order_date,
    o.status,
    o.amount_usd                                                    as gross_usd,
    case when o.status = 'refunded' then 0 else o.amount_usd end    as net_revenue_usd
from {{ ref('stg_bronze__orders') }} o
join {{ ref('stg_bronze__customers') }} c on c.customer_id = o.customer_id
