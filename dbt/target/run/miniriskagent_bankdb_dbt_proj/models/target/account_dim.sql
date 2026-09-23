
  
  create view "miniriskagent_results_1"."main"."account_dim__dbt_tmp" as (
    select
    account_id,
    account_number,
    customer_id,
    customer_type,
    account_status,
    record_arrival_date
from "miniriskagent_results_1"."main"."account_snapshot"
where dbt_valid_to is null
  );
