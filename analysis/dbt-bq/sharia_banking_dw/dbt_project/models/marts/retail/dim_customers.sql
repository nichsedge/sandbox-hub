select
    customer_id,
    nik,
    full_name,
    customer_segment,
    branch_code,
    branch_name,
    city,
    birth_date,
    is_sharia_compliant_flag,
    created_at
from {{ ref('stg_customers') }}
