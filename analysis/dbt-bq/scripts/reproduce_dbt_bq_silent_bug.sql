-- ==============================================================================
-- DEMO: dbt BigQuery insert_overwrite Silent Data Bug
-- Dynamic Partitioning vs Static Partitioning on Empty Staging
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. SETUP STAGING TABLE AND SEED DATA (H-3 to H-1)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dev.stg_orders (
    order_id INT64,
    order_date DATE,
    updated_at TIMESTAMP,
    amount NUMERIC
);

TRUNCATE TABLE dev.stg_orders;

INSERT INTO dev.stg_orders (order_id, order_date, updated_at, amount) VALUES
(1, DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), CURRENT_TIMESTAMP(), 101),
(2, DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), CURRENT_TIMESTAMP(), 102),
(3, DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), CURRENT_TIMESTAMP(), 103),
(4, DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY), CURRENT_TIMESTAMP(), 104),
(5, DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY), CURRENT_TIMESTAMP(), 105),
(6, DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY), CURRENT_TIMESTAMP(), 106),
(7, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), CURRENT_TIMESTAMP(), 107),
(8, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), CURRENT_TIMESTAMP(), 108),
(9, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), CURRENT_TIMESTAMP(), 109);

-- ------------------------------------------------------------------------------
-- 2. INITIALIZE TARGET TABLE (SIMULATING FULL REFRESH)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE TABLE dev.fact_orders_target
PARTITION BY order_date AS
SELECT * FROM dev.stg_orders;

-- Verify initial state (Should show rows for H-3, H-2, H-1)
SELECT order_date, COUNT(*) AS row_cnt FROM dev.fact_orders_target GROUP BY 1 ORDER BY 1;

-- ------------------------------------------------------------------------------
-- 3. SIMULATE STAGING CORRECTION (DATA FOR H-1 DELETED IN SOURCE)
-- ------------------------------------------------------------------------------
DELETE FROM dev.stg_orders
WHERE order_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);

-- Verify staging state (H-1 is now EMPTY!)
SELECT order_date, COUNT(*) AS stg_cnt FROM dev.stg_orders GROUP BY 1 ORDER BY 1;

-- ------------------------------------------------------------------------------
-- 4A. DYNAMIC PARTITIONING (DEFAULT dbt BEHAVIOR - BUG)
-- ------------------------------------------------------------------------------
-- dbt Step A: Create temp table from staging for H-1
CREATE OR REPLACE TEMP TABLE fact_orders__dbt_tmp AS (
    SELECT * FROM dev.stg_orders
    WHERE order_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
);

-- dbt Step B: Detect partitions dynamically from temp table (Result: EMPTY ARRAY [])
DECLARE dbt_partitions_for_replacement ARRAY<DATE>;
SET (dbt_partitions_for_replacement) = (
    SELECT AS STRUCT ARRAY_AGG(DISTINCT DATE(order_date) IGNORE NULLS)
    FROM fact_orders__dbt_tmp
);

-- dbt Step C: MERGE INTO target using dynamic array
MERGE INTO dev.fact_orders_target AS dbt_internal_dest
USING fact_orders__dbt_tmp AS dbt_internal_source
    ON FALSE
WHEN NOT MATCHED BY SOURCE
AND DATE(dbt_internal_dest.order_date) IN UNNEST(dbt_partitions_for_replacement)
THEN DELETE
WHEN NOT MATCHED THEN
    INSERT (order_id, order_date, updated_at, amount)
    VALUES (order_id, order_date, updated_at, amount);

-- Check Target Table after Dynamic Merge:
-- BUG RESULT: H-1 STILL EXISTS IN TARGET even though source was empty!
SELECT 'DYNAMIC_PARTITION_RESULT' AS test, order_date, COUNT(*) AS row_cnt
FROM dev.fact_orders_target GROUP BY 1, 2 ORDER BY 2;

-- ------------------------------------------------------------------------------
-- 4B. STATIC PARTITIONING (dbt WITH partitions CONFIG - FIX)
-- ------------------------------------------------------------------------------
-- MERGE INTO target using static partition definition (directly specifying H-1 date)
MERGE INTO dev.fact_orders_target AS dbt_internal_dest
USING (
    SELECT * FROM dev.stg_orders
    WHERE order_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
) AS dbt_internal_source
    ON FALSE
WHEN NOT MATCHED BY SOURCE
AND DATE(dbt_internal_dest.order_date) IN (DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
THEN DELETE
WHEN NOT MATCHED THEN
    INSERT (order_id, order_date, updated_at, amount)
    VALUES (order_id, order_date, updated_at, amount);

-- Check Target Table after Static Merge:
-- EXPECTED FIX: H-1 IS SUCCESSFULLY DELETED FROM TARGET!
SELECT 'STATIC_PARTITION_RESULT' AS test, order_date, COUNT(*) AS row_cnt
FROM dev.fact_orders_target GROUP BY 1, 2 ORDER BY 2;
