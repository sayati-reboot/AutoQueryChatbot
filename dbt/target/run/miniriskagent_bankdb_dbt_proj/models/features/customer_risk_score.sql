insert into "miniriskagent_results_1"."main"."customer_risk_score" ("customer_risk_score_id", "customer_id", "risk_intent", "rule_category", "rule_id", "feature_name", "feature_value", "feature_boolean", "feature_numeric", "rule_hit", "applied_score", "category_total_score", "total_score", "unsupported_rule_count", "calculation_status", "calculation_note", "policy_version", "section_number", "rule_description", "business_term_needed_for_calculation", "score_to_assign", "rule_extraction_date", "score_calculated_at")
    (
        select "customer_risk_score_id", "customer_id", "risk_intent", "rule_category", "rule_id", "feature_name", "feature_value", "feature_boolean", "feature_numeric", "rule_hit", "applied_score", "category_total_score", "total_score", "unsupported_rule_count", "calculation_status", "calculation_note", "policy_version", "section_number", "rule_description", "business_term_needed_for_calculation", "score_to_assign", "rule_extraction_date", "score_calculated_at"
        from "customer_risk_score__dbt_tmp20260930193535264296"
    )


  