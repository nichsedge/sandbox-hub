select
    account_id,
    customer_id,
    product_type,
    akad_type,
    transaction_date,
    daily_net_change,
    ending_balance
from {{ ref('int_daily_account_balances') }}
