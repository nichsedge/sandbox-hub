with source as (
    select * from {{ ref('raw_daily_transactions') }}
),

renamed as (
    select
        cast(transaction_id as varchar) as transaction_id,
        cast(account_id as varchar) as account_id,
        cast(transaction_date as date) as transaction_date,
        cast(transaction_type as varchar) as transaction_type,
        cast(db_cr_flag as varchar) as db_cr_flag,
        cast(amount as double) as amount,
        case 
            when db_cr_flag = 'CR' then cast(amount as double)
            else -1.0 * cast(amount as double)
        end as signed_amount,
        cast(channel as varchar) as channel,
        cast(description as varchar) as description
    from source
)

select * from renamed
