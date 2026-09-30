{% set customer_id = var('customer_id', none) %}
{% if execute and customer_id is none %}
    {{ exceptions.raise_compiler_error("customer_rule_features requires --vars '{customer_id: <id>}'") }}
{% endif %}
{% set customer_id = customer_id | int if customer_id is not none else -1 %}

{{ config(materialized='incremental', incremental_strategy='append') }}
{% if is_incremental() %}
    {{ config(pre_hook="delete from " ~ this ~ " where customer_id = " ~ customer_id) }}
{% endif %}

with risk_jurisdictions as (
    select * from (values
        ('IRAN', 'sanctioned'),
        ('NORTH KOREA', 'sanctioned'),
        ('RUSSIA', 'sanctioned'),
        ('SYRIA', 'sanctioned'),
        ('CUBA', 'sanctioned'),
        ('BELARUS', 'sanctioned'),
        ('MYANMAR', 'sanctioned'),
        ('VENEZUELA', 'sanctioned'),
        ('AFGHANISTAN', 'high_risk'),
        ('PAKISTAN', 'high_risk'),
        ('SUDAN', 'high_risk'),
        ('YEMEN', 'high_risk'),
        ('IRAQ', 'high_risk'),
        ('LIBYA', 'high_risk'),
        ('SOMALIA', 'high_risk'),
        ('UKRAINE', 'high_risk')
    ) as jurisdictions(country_name, risk_level)
),
ranked_rules as (
    select
        rule_id,
        policy_version,
        section_number,
        rule_description,
        business_term_needed_for_calculation,
        score_to_assign,
        rule_extraction_date,
        row_number() over (
            partition by rule_id
            order by rule_extraction_date desc, policy_version desc
        ) as version_rank
    from {{ source('policy_rule_store', 'rule_extraction_details') }}
),
latest_rules as (
    select
        rule_id,
        policy_version,
        section_number,
        rule_description,
        business_term_needed_for_calculation,
        score_to_assign,
        rule_extraction_date
    from ranked_rules
    where version_rank = 1
),
transaction_detail as (
    select
        acct.customer_id,
        txn.transaction_id,
        abs(try_cast(txn.amount as double)) as absolute_amount,
        txn.originating_country,
        txn.destination_country,
        origin.risk_level as origin_risk_level,
        destination.risk_level as destination_risk_level
    from {{ ref('account_dim') }} as acct
    inner join {{ ref('transaction_fact') }} as txn
        on acct.account_id = txn.account_id
    left join risk_jurisdictions as origin
        on upper(trim(txn.originating_country)) = origin.country_name
    left join risk_jurisdictions as destination
        on upper(trim(txn.destination_country)) = destination.country_name
    where acct.customer_id = {{ customer_id }}
),
transaction_metrics as (
    select
        customer_id,
        count(transaction_id) as transaction_count,
        sum(absolute_amount) as absolute_transaction_amount_sum,
        max(absolute_amount) as maximum_absolute_transaction_amount,
        sum(
            case
                when originating_country is not null
                    and destination_country is not null
                    and upper(trim(originating_country)) <> upper(trim(destination_country))
                then 1 else 0
            end
        ) as cross_border_transaction_count,
        sum(
            case
                when originating_country is not null
                    and destination_country is not null
                    and upper(trim(originating_country)) <> upper(trim(destination_country))
                    and (origin_risk_level is not null or destination_risk_level is not null)
                then 1 else 0
            end
        ) as cross_border_risky_transaction_count,
        sum(case when origin_risk_level = 'sanctioned' then 1 else 0 end)
            as sanctioned_origin_transaction_count,
        sum(case when origin_risk_level = 'high_risk' then 1 else 0 end)
            as high_risk_origin_transaction_count,
        sum(case when destination_risk_level = 'sanctioned' then 1 else 0 end)
            as sanctioned_destination_transaction_count,
        sum(case when destination_risk_level = 'high_risk' then 1 else 0 end)
            as high_risk_destination_transaction_count,
        sum(
            case
                when origin_risk_level is not null and destination_risk_level is not null
                then 1 else 0
            end
        ) as both_ends_risky_transaction_count
    from transaction_detail
    group by customer_id
),
customer_inputs as (
    select
        customer.cust_id as customer_id,
        customer.country_of_birth,
        customer.country_of_residence,
        birth.risk_level as birth_risk_level,
        residence.risk_level as residence_risk_level,
        coalesce(metrics.transaction_count, 0) as transaction_count,
        coalesce(metrics.absolute_transaction_amount_sum, 0) as absolute_transaction_amount_sum,
        coalesce(metrics.maximum_absolute_transaction_amount, 0)
            as maximum_absolute_transaction_amount,
        coalesce(metrics.cross_border_transaction_count, 0) as cross_border_transaction_count,
        coalesce(metrics.cross_border_risky_transaction_count, 0)
            as cross_border_risky_transaction_count,
        coalesce(metrics.sanctioned_origin_transaction_count, 0)
            as sanctioned_origin_transaction_count,
        coalesce(metrics.high_risk_origin_transaction_count, 0)
            as high_risk_origin_transaction_count,
        coalesce(metrics.sanctioned_destination_transaction_count, 0)
            as sanctioned_destination_transaction_count,
        coalesce(metrics.high_risk_destination_transaction_count, 0)
            as high_risk_destination_transaction_count,
        coalesce(metrics.both_ends_risky_transaction_count, 0)
            as both_ends_risky_transaction_count
    from {{ ref('customer_dim') }} as customer
    left join risk_jurisdictions as birth
        on upper(trim(customer.country_of_birth)) = birth.country_name
    left join risk_jurisdictions as residence
        on upper(trim(customer.country_of_residence)) = residence.country_name
    left join transaction_metrics as metrics
        on customer.cust_id = metrics.customer_id
    where customer.cust_id = {{ customer_id }}
),
customer_rule_inputs as (
    select
        customer_inputs.*,
        latest_rules.rule_id,
        latest_rules.policy_version,
        latest_rules.section_number,
        latest_rules.rule_description,
        latest_rules.business_term_needed_for_calculation,
        latest_rules.score_to_assign,
        latest_rules.rule_extraction_date,
        lower(
            coalesce(latest_rules.rule_description, '') || ' ' ||
            coalesce(latest_rules.business_term_needed_for_calculation, '')
        ) as rule_text
    from customer_inputs
    cross join latest_rules
),
evaluated_features as (
    select
        *,
        case
            when regexp_matches(rule_text, 'cross.?border')
                and regexp_matches(rule_text, 'sanctioned|high[- ]risk|prohibited')
            then cross_border_risky_transaction_count > 0

            when regexp_matches(rule_text, 'originating_country|origin country|transaction origin')
                and regexp_matches(rule_text, 'destination_country|destination country|transaction destination')
                and regexp_matches(rule_text, 'both')
                and regexp_matches(rule_text, 'sanctioned|high[- ]risk|prohibited')
            then both_ends_risky_transaction_count > 0

            when regexp_matches(rule_text, 'originating_country|origin country|transaction origin')
                and regexp_matches(rule_text, 'sanctioned|prohibited')
            then sanctioned_origin_transaction_count > 0

            when regexp_matches(rule_text, 'originating_country|origin country|transaction origin')
                and regexp_matches(rule_text, 'high[- ]risk')
            then high_risk_origin_transaction_count > 0

            when regexp_matches(rule_text, 'destination_country|destination country|transaction destination')
                and regexp_matches(rule_text, 'sanctioned|prohibited')
            then sanctioned_destination_transaction_count > 0

            when regexp_matches(rule_text, 'destination_country|destination country|transaction destination')
                and regexp_matches(rule_text, 'high[- ]risk')
            then high_risk_destination_transaction_count > 0

            when regexp_matches(rule_text, 'country[_ ]of[_ ]birth|birth country')
                and regexp_matches(rule_text, 'country[_ ]of[_ ]residence|residence country')
                and regexp_matches(rule_text, 'both')
                and regexp_matches(rule_text, 'high[- ]risk')
            then case
                when country_of_birth is null or trim(country_of_birth) = ''
                    or country_of_residence is null or trim(country_of_residence) = ''
                then null
                else coalesce(birth_risk_level = 'high_risk', false)
                    and coalesce(residence_risk_level = 'high_risk', false)
            end

            when regexp_matches(rule_text, 'country[_ ]of[_ ]birth|birth country')
                and regexp_matches(rule_text, 'country[_ ]of[_ ]residence|residence country')
                and regexp_matches(rule_text, 'high[- ]risk')
            then case
                when coalesce(birth_risk_level = 'high_risk', false)
                    or coalesce(residence_risk_level = 'high_risk', false)
                then true
                when country_of_birth is null or trim(country_of_birth) = ''
                    or country_of_residence is null or trim(country_of_residence) = ''
                then null
                else false
            end

            when regexp_matches(rule_text, 'country[_ ]of[_ ]birth|birth country')
                and regexp_matches(rule_text, 'unknown|blank|missing')
            then country_of_birth is null or trim(country_of_birth) = ''

            when regexp_matches(rule_text, 'country[_ ]of[_ ]residence|residence country')
                and regexp_matches(rule_text, 'unknown|blank|missing')
            then country_of_residence is null or trim(country_of_residence) = ''

            when regexp_matches(rule_text, 'country[_ ]of[_ ]birth|birth country')
                and regexp_matches(rule_text, 'sanctioned|prohibited')
            then case
                when country_of_birth is null or trim(country_of_birth) = '' then null
                else coalesce(birth_risk_level = 'sanctioned', false)
            end

            when regexp_matches(rule_text, 'country[_ ]of[_ ]birth|birth country')
                and regexp_matches(rule_text, 'high[- ]risk')
            then case
                when country_of_birth is null or trim(country_of_birth) = '' then null
                else coalesce(birth_risk_level = 'high_risk', false)
            end

            when regexp_matches(rule_text, 'country[_ ]of[_ ]residence|residence country')
                and regexp_matches(rule_text, 'sanctioned|prohibited')
            then case
                when country_of_residence is null or trim(country_of_residence) = '' then null
                else coalesce(residence_risk_level = 'sanctioned', false)
            end

            when regexp_matches(rule_text, 'country[_ ]of[_ ]residence|residence country')
                and regexp_matches(rule_text, 'high[- ]risk')
            then case
                when country_of_residence is null or trim(country_of_residence) = '' then null
                else coalesce(residence_risk_level = 'high_risk', false)
            end

            else null
        end as feature_boolean,
        case
            when regexp_matches(rule_text, 'transaction')
                and regexp_matches(rule_text, 'amount|value|volume|aggregate|sum|total')
                and regexp_matches(rule_text, 'aggregate|sum|total|rolling|24.hour|30.day')
            then cast(absolute_transaction_amount_sum as double)

            when regexp_matches(rule_text, 'transaction')
                and regexp_matches(rule_text, 'amount|value|volume')
            then cast(maximum_absolute_transaction_amount as double)

            when regexp_matches(rule_text, 'transaction')
                and regexp_matches(rule_text, 'frequency|count|number of transactions')
            then cast(transaction_count as double)

            else null
        end as feature_numeric
    from customer_rule_inputs
)
select
    cast(customer_id as varchar) || '|' || rule_id as customer_rule_feature_id,
    customer_id,
    rule_id,
    rule_id || '-cust-feature' as feature_name,
    policy_version,
    section_number,
    rule_description,
    business_term_needed_for_calculation,
    score_to_assign,
    rule_extraction_date,
    case
        when feature_boolean is not null then case when feature_boolean then 'Y' else 'N' end
        when feature_numeric is not null then cast(feature_numeric as varchar)
        else null
    end as feature_value,
    feature_boolean,
    feature_numeric,
    case
        when feature_boolean is not null then 'calculated'
        when feature_numeric is not null then 'metric_only'
        else 'unsupported'
    end as calculation_status,
    case
        when feature_boolean is not null then 'Rule condition evaluated from current customer or transaction data.'
        when feature_numeric is not null then 'Absolute metric supplied; policy threshold or historical comparison may still need implementation.'
        when regexp_matches(rule_text, 'country[_ ]of[_ ]birth|birth country')
            and (country_of_birth is null or trim(country_of_birth) = '')
        then 'Cannot evaluate this rule because customer country_of_birth is missing.'
        when regexp_matches(rule_text, 'country[_ ]of[_ ]residence|residence country')
            and (country_of_residence is null or trim(country_of_residence) = '')
        then 'Cannot evaluate this rule because customer country_of_residence is missing.'
        else 'Required business logic or reference data is not available in this model.'
    end as calculation_note,
    current_timestamp as feature_calculated_at
from evaluated_features