with source as (
    select * from {{ ref('raw_bank_income_pool') }}
),

renamed as (
    select
        cast(period_month as varchar) as period_month,
        cast(income_source as varchar) as income_source,
        cast(gross_amount as double) as gross_amount,
        cast(description as varchar) as description
    from source
)

select * from renamed
