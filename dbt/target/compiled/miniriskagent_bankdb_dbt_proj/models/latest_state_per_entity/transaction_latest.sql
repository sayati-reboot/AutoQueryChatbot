
select *
from "miniriskagent_results_1"."main"."transaction_stage"
qualify row_number() over (
    partition by transaction_id
    order by record_arrival_date desc
) = 1