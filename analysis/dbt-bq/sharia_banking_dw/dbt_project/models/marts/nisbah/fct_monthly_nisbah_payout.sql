select
    account_id,
    customer_id,
    period_month,
    average_daily_balance,
    nisbah_customer_pct,
    nisbah_bank_pct,
    total_distributable_gross_income,
    grand_total_mudharabah_adb,
    pool_share_weight_pct,
    account_gross_income_share,
    customer_profit_payout_amount,
    bank_profit_retained_amount
from {{ ref('int_nisbah_profit_distribution') }}
