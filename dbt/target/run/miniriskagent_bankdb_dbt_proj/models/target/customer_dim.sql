
  
  create view "miniriskagent_results_1"."main"."customer_dim__dbt_tmp" as (
    select
    cust_id,
    country_of_residence,
    country_of_birth,
    date_of_birth,
    record_arrival_date
from "miniriskagent_results_1"."main"."customer_snapshot"
where dbt_valid_to is null
  );
