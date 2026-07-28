-- 1. Run the merge statement
MERGE INTO `ichsanul-dev`.`dev`.`fact_orders_static` AS dbt_internal_dest
USING (
    SELECT *
    FROM `ichsanul-dev`.`dev`.`stg_orders`
    WHERE order_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
) AS dbt_internal_source
    ON FALSE
WHEN NOT MATCHED BY SOURCE
    AND DATE(dbt_internal_dest.order_date) IN (
        DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    )
    THEN DELETE
WHEN NOT MATCHED THEN
    INSERT (`order_id`, `order_date`, `updated_at`, `amount`)
    VALUES (`order_id`, `order_date`, `updated_at`, `amount`);