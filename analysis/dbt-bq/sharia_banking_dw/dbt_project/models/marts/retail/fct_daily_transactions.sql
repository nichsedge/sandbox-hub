select
    transaction_id,
    account_id,
    transaction_date,
    transaction_type,
    db_cr_flag,
    amount,
    signed_amount,
    channel,
    description
from {{ ref('stg_daily_transactions') }}
