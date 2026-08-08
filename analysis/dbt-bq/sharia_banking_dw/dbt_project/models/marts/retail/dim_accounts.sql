select
    account_id,
    customer_id,
    account_number,
    product_type,
    akad_type,
    currency,
    nisbah_customer_pct,
    nisbah_bank_pct,
    status,
    opened_date
from {{ ref('stg_accounts') }}
