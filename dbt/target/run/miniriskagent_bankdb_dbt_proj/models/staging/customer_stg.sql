
  
  create view "miniriskagent_results_1"."main"."customer_stg__dbt_tmp" as (
    select * 
from "miniriskagent_results_1"."main"."customer_stage"
  );
