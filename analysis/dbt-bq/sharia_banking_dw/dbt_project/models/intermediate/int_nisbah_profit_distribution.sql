with mudharabah_adb as (
    select * from {{ ref('int_mudharabah_average_balances') }}
),

total_pool_income as (
    select
        period_month,
        sum(gross_amount) as total_distributable_gross_income
    from {{ ref('stg_bank_income_pool') }}
    group by 1
),

total_adb_agg as (
    select
        period_month,
        sum(average_daily_balance) as grand_total_mudharabah_adb
    from mudharabah_adb
    group by 1
),

nisbah_calculation as (
    select
        m.account_id,
        m.customer_id,
        m.period_month,
        m.average_daily_balance,
        m.nisbah_customer_pct,
        m.nisbah_bank_pct,
        t.total_distributable_gross_income,
        a.grand_total_mudharabah_adb,
        -- Account weight in Mudharabah pool
        (m.average_daily_balance / nullif(a.grand_total_mudharabah_adb, 0)) as pool_share_weight_pct,
        -- Account share of total gross income
        (t.total_distributable_gross_income * (m.average_daily_balance / nullif(a.grand_total_mudharabah_adb, 0))) as account_gross_income_share,
        -- Final profit payout to customer (Nisbah Nasabah)
        (t.total_distributable_gross_income * (m.average_daily_balance / nullif(a.grand_total_mudharabah_adb, 0))) * (m.nisbah_customer_pct / 100.0) as customer_profit_payout_amount,
        -- Profit retained by bank (Nisbah Bank)
        (t.total_distributable_gross_income * (m.average_daily_balance / nullif(a.grand_total_mudharabah_adb, 0))) * (m.nisbah_bank_pct / 100.0) as bank_profit_retained_amount
    from mudharabah_adb m
    inner join total_pool_income t on m.period_month = t.period_month
    inner join total_adb_agg a on m.period_month = a.period_month
)

select * from nisbah_calculation
