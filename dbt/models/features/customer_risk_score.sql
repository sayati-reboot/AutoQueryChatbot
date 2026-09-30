{% set customer_id = var('customer_id', none) %}
{% if execute and customer_id is none %}
    {{ exceptions.raise_compiler_error("customer_risk_score requires --vars '{customer_id: <id>}'") }}
{% endif %}
{% set customer_id = customer_id | int if customer_id is not none else -1 %}
{% set risk_intent = var('risk_intent', 'all') | lower %}
{% if execute and risk_intent not in ['geography', 'transaction', 'all'] %}
    {{ exceptions.raise_compiler_error("risk_intent must be geography, transaction, or all") }}
{% endif %}

{{ config(materialized='incremental', incremental_strategy='append') }}
{% if is_incremental() %}
    {{ config(
        pre_hook="delete from " ~ this ~ " where customer_id = " ~ customer_id ~
            " and risk_intent = '" ~ risk_intent ~ "'"
    ) }}
{% endif %}

with ranked_features as (
    select
        customer_id,
        rule_id,
        feature_name,
        feature_value,
        feature_boolean,
        feature_numeric,
        calculation_status,
        calculation_note,
        policy_version,
        section_number,
        rule_description,
        business_term_needed_for_calculation,
        score_to_assign,
        rule_extraction_date,
        feature_calculated_at,
        row_number() over (
            partition by customer_id, rule_id
            order by feature_calculated_at desc, rule_extraction_date desc, policy_version desc
        ) as feature_rank
    from {{ ref('customer_rule_features') }}
    where customer_id = {{ customer_id }}
),
categorized_features as (
    select
        customer_id,
        rule_id,
        feature_name,
        feature_value,
        feature_boolean,
        feature_numeric,
        calculation_status,
        calculation_note,
        policy_version,
        section_number,
        rule_description,
        business_term_needed_for_calculation,
        score_to_assign,
        rule_extraction_date,
        case
            when rule_id like 'geographic_risk_policy-%' then 'geography'
            when rule_id like 'transaction_risk_policy-%' then 'transaction'
            else 'unclassified'
        end as rule_category
    from ranked_features
    where feature_rank = 1
),
scoped_rules as (
    select
        *,
        feature_boolean as rule_hit,
        case
            when feature_boolean is true then score_to_assign
            when feature_boolean is false then 0
            else null
        end as applied_score
    from categorized_features
    where rule_category in ('geography', 'transaction')
),
scored_rules as (
    select
        *,
        sum(coalesce(applied_score, 0)) over (
            partition by customer_id, '{{ risk_intent }}'
        ) as total_score,
        sum(coalesce(applied_score, 0)) over (
            partition by customer_id, '{{ risk_intent }}', rule_category
        ) as category_total_score,
        sum(case when applied_score is null then 1 else 0 end) over (
            partition by customer_id, '{{ risk_intent }}'
        ) as unsupported_rule_count
    from scoped_rules
)
select
    cast(customer_id as varchar) || '|' || '{{ risk_intent }}' || '|' || rule_id
        as customer_risk_score_id,
    customer_id,
    '{{ risk_intent }}' as risk_intent,
    rule_category,
    rule_id,
    feature_name,
    feature_value,
    feature_boolean,
    feature_numeric,
    rule_hit,
    applied_score,
    category_total_score,
    total_score,
    unsupported_rule_count,
    calculation_status,
    calculation_note,
    policy_version,
    section_number,
    rule_description,
    business_term_needed_for_calculation,
    score_to_assign,
    rule_extraction_date,
    current_timestamp as score_calculated_at
from scored_rules