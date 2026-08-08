with accounts as (
    select account_id, customer_id, product_type, akad_type
    from {{ ref('stg_accounts') }}
),

daily_tx as (
    select
        account_id,
        transaction_date,
        sum(signed_amount) as daily_net_change
    from {{ ref('stg_daily_transactions') }}
    group by 1, 2
),

account_running_balance as (
    select
        a.account_id,
        a.customer_id,
        a.product_type,
        a.akad_type,
        t.transaction_date,
        t.daily_net_change,
        sum(t.daily_net_change) over (
            partition by a.account_id 
            order by t.transaction_date
            rows between unbounded preceding and current row
        ) as ending_balance
    from accounts a
    inner join daily_tx t on a.account_id = t.account_id
)

select * from account_running_balance
