select
    contract_id,
    customer_id,
    contract_number,
    akad_type,
    financing_sector,
    principal_amount,
    margin_amount,
    total_financing_amount,
    monthly_installment,
    tenor_months,
    start_date,
    end_date
from {{ ref('stg_financing_contracts') }}
