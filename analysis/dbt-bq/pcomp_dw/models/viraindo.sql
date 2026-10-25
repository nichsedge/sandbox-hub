with
    cte_0 as (
        select
            name as product_name,
            category,
            replace(price, '.', '') as price,
            date(date_trunc(inserted_at, week)) as inserted_at,
            'viraindo' as source
        from {{ source("dezoomcamp", "viraindo_raw") }}
    )
select product_name, category, safe_cast(price as integer) as price, inserted_at, source
from cte_0
