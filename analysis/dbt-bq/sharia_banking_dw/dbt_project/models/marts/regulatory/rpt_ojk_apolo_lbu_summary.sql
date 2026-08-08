with financing as (
    select * from {{ ref('fct_financing_portfolio') }}
),

kolek_summary as (
    select
        branch_code,
        branch_name,
        financing_sector,
        akad_type,
        count(contract_id) as total_contract_count,
        sum(outstanding_principal) as total_outstanding_principal,
        sum(case when ojk_kolektibilitas = 1 then outstanding_principal else 0 end) as kolek_1_lancar,
        sum(case when ojk_kolektibilitas = 2 then outstanding_principal else 0 end) as kolek_2_dpk,
        sum(case when ojk_kolektibilitas = 3 then outstanding_principal else 0 end) as kolek_3_kurang_lancar,
        sum(case when ojk_kolektibilitas = 4 then outstanding_principal else 0 end) as kolek_4_diragukan,
        sum(case when ojk_kolektibilitas = 5 then outstanding_principal else 0 end) as kolek_5_macet,
        sum(case when is_npf_non_performing_flag = true then outstanding_principal else 0 end) as total_npf_amount
    from financing
    group by 1, 2, 3, 4
)

select
    branch_code,
    branch_name,
    financing_sector,
    akad_type,
    total_contract_count,
    total_outstanding_principal,
    kolek_1_lancar,
    kolek_2_dpk,
    kolek_3_kurang_lancar,
    kolek_4_diragukan,
    kolek_5_macet,
    total_npf_amount,
    -- NPF Gross % = (Total NPF Amount / Total Outstanding) * 100
    round(
        (total_npf_amount / nullif(total_outstanding_principal, 0)) * 100.0, 
        2
    ) as gross_npf_pct,
    case 
        when (total_npf_amount / nullif(total_outstanding_principal, 0)) * 100.0 > 5.0 then 'WARNING_EXCEEDS_OJK_LIMIT'
        else 'COMPLIANT_WITHIN_OJK_LIMIT'
    end as ojk_regulatory_status
from kolek_summary
order by total_outstanding_principal desc
