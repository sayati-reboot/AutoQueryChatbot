{%snapshot customer_snapshot %}
{{
    
    config(
        target_schema='main',
        unique_key='cust_id',
        strategy='check',
        check_cols=['country_of_residence', 'country_of_birth', 'date_of_birth']
    )
}}

from {{ ref('customer_latest') }}

{%endsnapshot %}

