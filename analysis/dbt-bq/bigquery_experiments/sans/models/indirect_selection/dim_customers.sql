{{ config(materialized='view') }}

SELECT
    1 AS customer_id,
    'Alice' AS customer_name
UNION ALL
SELECT
    2 AS customer_id,
    'Bob' AS customer_name
