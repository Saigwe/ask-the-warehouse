select
    order_id,
    customer_id,
    cast(order_date as date)            as order_date,
    status,
    amount_usd
from {{ source('bronze', 'orders') }}
