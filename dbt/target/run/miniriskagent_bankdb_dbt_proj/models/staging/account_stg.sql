
  
  create view "miniriskagent_results_1"."main"."account_stg__dbt_tmp" as (
    select *
from "miniriskagent_results_1"."main"."account_stage"
  );
