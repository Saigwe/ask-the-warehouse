-- One row per contract action. Obligations (positive) and de-obligations (negative) are split here, once,
-- so no consumer has to decide again whether "spend" means gross or net.
select
    line_id,
    award_id,
    action_date,
    fiscal_quarter,
    org_unit,
    category,
    competition_status,
    business_size,
    supplier_id,
    amount_usd,
    case when amount_usd > 0 then amount_usd else 0 end    as obligation_usd,
    case when amount_usd < 0 then amount_usd else 0 end    as deobligation_usd,
    case when amount_usd > 0 then 1 else 0 end             as is_obligation
from {{ ref('stg_bronze__spend_lines') }}
