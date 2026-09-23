

select *
from "miniriskagent_results_1"."main"."customer_stage"
qualify row_number() over (
    partition by cust_id
    order by record_arrival_date desc
) = 1