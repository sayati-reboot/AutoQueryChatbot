
select *
from "miniriskagent_results_1"."main"."account_stage"
qualify row_number() over (
    partition by account_id
    order by record_arrival_date desc
) = 1