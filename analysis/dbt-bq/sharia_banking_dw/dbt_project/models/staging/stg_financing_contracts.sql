with source as (
    select * from {{ ref('raw_financing_contracts') }}
),

renamed as (
    select
        cast(contract_id as varchar) as contract_id,
        cast(customer_id as varchar) as customer_id,
        cast(contract_number as varchar) as contract_number,
        cast(akad_type as varchar) as akad_type,
        cast(financing_sector as varchar) as financing_sector,
        cast(principal_amount as double) as principal_amount,
        cast(margin_amount as double) as margin_amount,
        cast(total_financing_amount as double) as total_financing_amount,
        cast(monthly_installment as double) as monthly_installment,
        cast(tenor_months as integer) as tenor_months,
        cast(start_date as date) as start_date,
        cast(end_date as date) as end_date,
        cast(ojk_kolektibilitas as integer) as ojk_kolektibilitas,
        case 
            when cast(ojk_kolektibilitas as integer) = 1 then 'LANCAR'
            when cast(ojk_kolektibilitas as integer) = 2 then 'DALAM_PERHATIAN_KHUSUS'
            when cast(ojk_kolektibilitas as integer) = 3 then 'KURANG_LANCAR'
            when cast(ojk_kolektibilitas as integer) = 4 then 'DIRAGUKAN'
            when cast(ojk_kolektibilitas as integer) = 5 then 'MACET'
        end as kolektibilitas_label,
        case 
            when cast(ojk_kolektibilitas as integer) >= 3 then true 
            else false 
        end as is_npf_non_performing_flag,
        cast(outstanding_principal as double) as outstanding_principal
    from source
)

select * from renamed
