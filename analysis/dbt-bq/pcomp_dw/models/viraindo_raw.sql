{{ config(materialized="table") }}

select *
from {{ source("dezoomcamp", "viraindo_raw") }}
qualify
    row_number() over (
        partition by name, category, price order by inserted_at asc nulls last
    )
    = 1  -- dedup
