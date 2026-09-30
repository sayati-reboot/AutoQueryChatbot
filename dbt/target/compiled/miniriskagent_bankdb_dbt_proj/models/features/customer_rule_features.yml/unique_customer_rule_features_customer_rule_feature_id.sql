
    
    

select
    customer_rule_feature_id as unique_field,
    count(*) as n_records

from "miniriskagent_results_1"."main"."customer_rule_features"
where customer_rule_feature_id is not null
group by customer_rule_feature_id
having count(*) > 1


