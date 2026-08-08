with source as (
    select * from {{ ref('raw_customers') }}
),

renamed as (
    select
        cast(customer_id as varchar) as customer_id,
        cast(nik as varchar) as nik,
        cast(full_name as varchar) as full_name,
        cast(customer_segment as varchar) as customer_segment,
        cast(branch_code as varchar) as branch_code,
        cast(branch_name as varchar) as branch_name,
        cast(city as varchar) as city,
        cast(birth_date as date) as birth_date,
        cast(is_sharia_compliant_flag as boolean) as is_sharia_compliant_flag,
        cast(created_at as date) as created_at
    from source
)

select * from renamed
