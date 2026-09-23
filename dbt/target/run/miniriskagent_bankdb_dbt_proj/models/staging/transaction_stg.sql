
  
  create view "miniriskagent_results_1"."main"."transaction_stg__dbt_tmp" as (
    select *
from "miniriskagent_results_1"."main"."transaction_stage"
  );
