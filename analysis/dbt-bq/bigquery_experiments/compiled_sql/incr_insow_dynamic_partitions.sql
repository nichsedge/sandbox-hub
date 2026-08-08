-- Generated script to merge partitions into `ichsanul-dev`.`dev`.`fact_orders_static`
DECLARE dbt_partitions_for_replacement ARRAY<DATE>;

-- 1. Create a temp table with model data
CREATE OR REPLACE TABLE `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`
PARTITION BY order_date
OPTIONS (
    expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 12 HOUR)
) AS (
    SELECT *
    FROM `ichsanul-dev`.`dev`.`stg_orders`
    WHERE order_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
);

-- 2. Define partitions to update
SET (dbt_partitions_for_replacement) = (
    SELECT AS STRUCT
        -- IGNORE NULLS: this needs to be aligned to _dbt_max_partition, which ignores null
        ARRAY_AGG(DISTINCT DATE(order_date) IGNORE NULLS)
    FROM `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`
);

-- 3. Run the merge statement
MERGE INTO `ichsanul-dev`.`dev`.`fact_orders_static` AS dbt_internal_dest
USING (
    SELECT *
    FROM `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`
) AS dbt_internal_source
    ON FALSE
WHEN NOT MATCHED BY SOURCE
    AND DATE(dbt_internal_dest.order_date) IN UNNEST(dbt_partitions_for_replacement)
    THEN DELETE
WHEN NOT MATCHED THEN
    INSERT (`order_id`, `order_date`, `updated_at`, `amount`)
    VALUES (`order_id`, `order_date`, `updated_at`, `amount`);

-- 4. Clean up the temp table
DROP TABLE IF EXISTS `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`;
