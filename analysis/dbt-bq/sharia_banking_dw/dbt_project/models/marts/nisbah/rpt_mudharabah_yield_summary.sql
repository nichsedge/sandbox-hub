with payouts as (
    select * from {{ ref('fct_monthly_nisbah_payout') }}
),

customers as (
    select customer_id, branch_code, branch_name
    from {{ ref('stg_customers') }}
)

select
    c.branch_code,
    c.branch_name,
    p.period_month,
    count(distinct p.account_id) as total_mudharabah_accounts,
    sum(p.average_daily_balance) as total_branch_mudharabah_adb,
    sum(p.account_gross_income_share) as total_gross_income_allocated,
    sum(p.customer_profit_payout_amount) as total_customer_nisbah_payout,
    sum(p.bank_profit_retained_amount) as total_bank_nisbah_retained,
    -- Effective monthly yield % = (Customer payout / ADB) * 100
    round(
        (sum(p.customer_profit_payout_amount) / nullif(sum(p.average_daily_balance), 0)) * 100.0, 
        4
    ) as effective_monthly_yield_pct,
    -- Annualized equivalent yield % = Effective monthly yield * 12
    round(
        (sum(p.customer_profit_payout_amount) / nullif(sum(p.average_daily_balance), 0)) * 100.0 * 12.0, 
        4
    ) as annualized_equivalent_yield_pct
from payouts p
left join customers c on p.customer_id = c.customer_id
group by 1, 2, 3
order by total_branch_mudharabah_adb desc
