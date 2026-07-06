

    
    
        
	

        -- 1. run the merge statement
        

    merge into `ichsanul-dev`.`dev`.`fact_orders_static` as DBT_INTERNAL_DEST
        using (
    

SELECT 
    *
from `ichsanul-dev`.`dev`.`stg_orders`


WHERE order_date = date_sub(current_date(), interval 1 day)

  ) as DBT_INTERNAL_SOURCE
        on FALSE

    when not matched by source
         and date(dbt_internal_dest.order_date) in (
                date_sub(current_date(), interval 1 day)
            ) 
        then delete

    when not matched then insert
        (`order_id`, `order_date`, `updated_at`, `amount`)
    values
        (`order_id`, `order_date`, `updated_at`, `amount`)

;

    
    


    