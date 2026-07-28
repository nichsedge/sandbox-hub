{{ config(materialized='view') }}

SELECT
    customer_id,
    UPPER(customer_name) AS customer_name_upper
FROM {{ ref('dim_customers') }}
