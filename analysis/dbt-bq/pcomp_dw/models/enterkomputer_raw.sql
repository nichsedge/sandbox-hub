{{ config(materialized="table") }}

select *
from {{ source("dezoomcamp", "enterkomputer_raw") }}
qualify
    row_number() over (
        partition by pname, kname, pprcz order by inserted_at asc nulls last
    )
    = 1  -- dedup
