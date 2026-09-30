insert into "miniriskagent_results_1"."main"."customer_rule_features" ("customer_rule_feature_id", "customer_id", "rule_id", "feature_name", "policy_version", "section_number", "rule_description", "business_term_needed_for_calculation", "score_to_assign", "rule_extraction_date", "feature_value", "feature_boolean", "feature_numeric", "calculation_status", "calculation_note", "feature_calculated_at")
    (
        select "customer_rule_feature_id", "customer_id", "rule_id", "feature_name", "policy_version", "section_number", "rule_description", "business_term_needed_for_calculation", "score_to_assign", "rule_extraction_date", "feature_value", "feature_boolean", "feature_numeric", "calculation_status", "calculation_note", "feature_calculated_at"
        from "customer_rule_features__dbt_tmp20260930193535205961"
    )


  