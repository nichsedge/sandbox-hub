with source as (
    select * from {{ ref('raw_purification_fund') }}
),

renamed as (
    select
        cast(record_id as varchar) as record_id,
        cast(period_month as varchar) as period_month,
        cast(source_type as varchar) as source_type,
        cast(contract_id as varchar) as contract_id,
        cast(amount as double) as amount,
        cast(status as varchar) as status,
        cast(description as varchar) as description
    from source
)

select * from renamed
