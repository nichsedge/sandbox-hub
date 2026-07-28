{{
    config(
        materialized='incremental',
        incremental_strategy='insert_overwrite',
        partition_by={
            "field": "order_date",
            "data_type": "date",
            "granularity": "day"
        },
        partitions=[var('start_date')]
    )
}}

SELECT *
FROM {{ source('dev', 'stg_orders') }}

{% if is_incremental() %}
  WHERE order_date = {{ var("start_date") }}
{% endif %}
