{{ config(materialized='view') }}

SELECT
    101 AS order_id,
    1 AS customer_id,
    150.0 AS amount
UNION ALL
SELECT
    102 AS order_id,
    2 AS customer_id,
    200.0 AS amount
