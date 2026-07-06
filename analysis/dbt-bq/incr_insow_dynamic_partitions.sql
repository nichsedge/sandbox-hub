

    
    
        -- generated script to merge partitions into `ichsanul-dev`.`dev`.`fact_orders_static`
      declare dbt_partitions_for_replacement array<date>;

      
      
       -- 1. create a temp table with model data
        
  
    

    create or replace table `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`
      
    partition by order_date
    

    
    OPTIONS(
      expiration_timestamp=TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 12 hour)
    )
    as (
      

SELECT 
    *
from `ichsanul-dev`.`dev`.`stg_orders`


WHERE order_date = date_sub(current_date(), interval 1 day)

    );
  
      -- 2. define partitions to update
      set (dbt_partitions_for_replacement) = (
          select as struct
              -- IGNORE NULLS: this needs to be aligned to _dbt_max_partition, which ignores null
              array_agg(distinct date(order_date) IGNORE NULLS)
          from `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`
      );

      -- 3. run the merge statement
      

    merge into `ichsanul-dev`.`dev`.`fact_orders_static` as DBT_INTERNAL_DEST
        using (
        select
        * from `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`
      ) as DBT_INTERNAL_SOURCE
        on FALSE

    when not matched by source
         and date(DBT_INTERNAL_DEST.order_date) in unnest(dbt_partitions_for_replacement) 
        then delete

    when not matched then insert
        (`order_id`, `order_date`, `updated_at`, `amount`)
    values
        (`order_id`, `order_date`, `updated_at`, `amount`)

;

      -- 4. clean up the temp table
      drop table if exists `ichsanul-dev`.`dev`.`fact_orders_static__dbt_tmp195903749846`

  


    


    