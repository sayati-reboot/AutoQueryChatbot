
  
  create view "miniriskagent_results_1"."main"."transaction_fact__dbt_tmp" as (
    select
    transaction_id,
    amount,
    type,
    originating_country,
    destination_country,
    account_id,
    transaction_date,
    record_arrival_date
from "miniriskagent_results_1"."main"."transaction_snapshot"
where dbt_valid_to is null
  );
