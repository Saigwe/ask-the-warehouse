-- One row per registered supplier (UEI). When a UEI reported different parents during the year, the parent
-- on its latest action wins.
select
    supplier_id,
    arg_max(supplier_name, action_date)                    as supplier_name,
    arg_max(parent_supplier_id, action_date)               as parent_supplier_id,
    arg_max(parent_supplier_name, action_date)             as parent_supplier_name
from {{ ref('stg_bronze__spend_lines') }}
group by 1
