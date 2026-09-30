
    
    

with all_values as (

    select
        calculation_status as value_field,
        count(*) as n_records

    from "miniriskagent_results_1"."main"."customer_rule_features"
    group by calculation_status

)

select *
from all_values
where value_field not in (
    'calculated','metric_only','unsupported'
)


