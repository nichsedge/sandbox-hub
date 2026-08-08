with contracts as (
    select * from {{ ref('stg_financing_contracts') }}
),

customers as (
    select customer_id, branch_code, branch_name, customer_segment
    from {{ ref('stg_customers') }}
)

select
    c.contract_id,
    c.customer_id,
    cust.branch_code,
    cust.branch_name,
    cust.customer_segment,
    c.contract_number,
    c.akad_type,
    c.financing_sector,
    c.principal_amount,
    c.margin_amount,
    c.total_financing_amount,
    c.outstanding_principal,
    c.ojk_kolektibilitas,
    c.kolektibilitas_label,
    c.is_npf_non_performing_flag,
    c.start_date,
    c.end_date
from contracts c
left join customers cust on c.customer_id = cust.customer_id
