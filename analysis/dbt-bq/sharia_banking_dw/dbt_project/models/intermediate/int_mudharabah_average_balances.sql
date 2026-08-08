with mudharabah_accounts as (
    select 
        account_id,
        customer_id,
        nisbah_customer_pct,
        nisbah_bank_pct
    from {{ ref('stg_accounts') }}
    where akad_type = 'MUDHARABAH_MUTLAQAH'
),

daily_balances as (
    select * from {{ ref('int_daily_account_balances') }}
),

monthly_adb as (
    select
        m.account_id,
        m.customer_id,
        '2026-01' as period_month,
        m.nisbah_customer_pct,
        m.nisbah_bank_pct,
        count(distinct d.transaction_date) as active_days_count,
        avg(d.ending_balance) as average_daily_balance,
        min(d.ending_balance) as min_daily_balance,
        max(d.ending_balance) as max_daily_balance
    from mudharabah_accounts m
    inner join daily_balances d on m.account_id = d.account_id
    group by 1, 2, 3, 4, 5
)

select * from monthly_adb
