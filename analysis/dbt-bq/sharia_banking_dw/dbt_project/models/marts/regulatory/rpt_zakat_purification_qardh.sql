with purification as (
    select
        period_month,
        source_type,
        count(record_id) as item_count,
        sum(amount) as total_purified_amount
    from {{ ref('stg_purification_fund') }}
    group by 1, 2
),

bank_profit as (
    select
        period_month,
        sum(bank_profit_retained_amount) as total_bank_nisbah_profit
    from {{ ref('fct_monthly_nisbah_payout') }}
    group by 1
)

select
    p.period_month,
    p.source_type,
    p.item_count,
    p.total_purified_amount as qardh_hasan_fund_addition,
    b.total_bank_nisbah_profit,
    -- Corporate Zakat 2.5% calculated on Bank retained Sharia profit
    round(b.total_bank_nisbah_profit * 0.025, 2) as corporate_zakat_payable_amount,
    'QARDH_HASAN_CHARITY_POOL' as target_fund_destination
from purification p
left join bank_profit b on p.period_month = b.period_month
order by p.total_purified_amount desc
