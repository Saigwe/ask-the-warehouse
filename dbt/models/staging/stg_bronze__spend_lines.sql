-- Typed spend lines with the two governed labels every report must share:
--   competition_status: Not competed when the contracting officer recorded a non-competitive basis.
--   business_size: Small / Other than small, Unknown when not recorded.
select
    line_id,
    award_id,
    cast(action_date as date)                                           as action_date,
    fiscal_quarter,
    org_unit,
    supplier_id,
    supplier_name,
    parent_supplier_id,
    parent_supplier_name,
    cast(amount_usd as decimal(18, 2))                                  as amount_usd,
    coalesce(category, 'Unclassified')                                  as category,
    case
        when extent_competed is null then 'Unknown'
        when extent_competed like '%NOT %' or extent_competed like 'NON-COMPETITIVE%' then 'Not competed'
        else 'Competed'
    end                                                                 as competition_status,
    case business_size
        when 'SMALL BUSINESS' then 'Small'
        when 'OTHER THAN SMALL BUSINESS' then 'Other than small'
        else 'Unknown'
    end                                                                 as business_size
from {{ source('bronze', 'spend_lines') }}
