
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select *
from "miniriskagent_results_1"."main"."transaction_latest"
where transaction_id is null
  
  
      
    ) dbt_internal_test