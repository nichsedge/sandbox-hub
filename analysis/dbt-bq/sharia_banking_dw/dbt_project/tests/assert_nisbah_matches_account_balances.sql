-- Singular Cross-Model Data Quality Test
-- Compares two models with different operational granularities:
-- 1. fct_monthly_nisbah_payout (Monthly granularity)
-- 2. fct_account_balances (Daily granularity)
-- Asserts that total Average Daily Balance (ADB) in Nisbah payout report matches the actual average ending balance in account balances fact table.

with monthly_payout_adb as (
    select
        account_id,
        average_daily_balance as payout_adb
    from {{ ref('fct_monthly_nisbah_payout') }}
),

daily_balance_adb as (
    select
        account_id,
        avg(ending_balance) as actual_adb
    from {{ ref('fct_account_balances') }}
    group by 1
),

discrepancies as (
    select
        m.account_id,
        m.payout_adb,
        d.actual_adb,
        abs(m.payout_adb - d.actual_adb) as variance
    from monthly_payout_adb m
    inner join daily_balance_adb d on m.account_id = d.account_id
    where abs(m.payout_adb - d.actual_adb) > 0.01 -- Allow small floating point threshold
)

-- Test fails if any rows are returned
select * from discrepancies
