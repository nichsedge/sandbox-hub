with source as (
    select * from {{ ref('raw_accounts') }}
),

renamed as (
    select
        cast(account_id as varchar) as account_id,
        cast(customer_id as varchar) as customer_id,
        cast(account_number as varchar) as account_number,
        cast(product_type as varchar) as product_type,
        cast(akad_type as varchar) as akad_type,
        cast(currency as varchar) as currency,
        cast(indicative_nisbah_customer_pct as double) as nisbah_customer_pct,
        (100.0 - cast(indicative_nisbah_customer_pct as double)) as nisbah_bank_pct,
        cast(status as varchar) as status,
        cast(opened_date as date) as opened_date
    from source
)

select * from renamed
