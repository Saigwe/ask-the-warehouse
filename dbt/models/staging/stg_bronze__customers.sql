select
    customer_id,
    region
from {{ source('bronze', 'customers') }}
