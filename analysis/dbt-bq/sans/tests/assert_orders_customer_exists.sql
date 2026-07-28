-- Singular Custom Data Test comparing fct_orders and dim_customers
SELECT
    o.order_id,
    o.customer_id
FROM {{ ref('fct_orders') }} AS o
LEFT JOIN {{ ref('dim_customers') }} AS c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
