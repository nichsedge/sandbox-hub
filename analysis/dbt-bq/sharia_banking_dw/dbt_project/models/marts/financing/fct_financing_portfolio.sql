select
    contract_id,
    customer_id,
    branch_code,
    branch_name,
    customer_segment,
    contract_number,
    akad_type,
    financing_sector,
    principal_amount,
    margin_amount,
    total_financing_amount,
    outstanding_principal,
    ojk_kolektibilitas,
    kolektibilitas_label,
    is_npf_non_performing_flag
from {{ ref('int_financing_performance') }}
