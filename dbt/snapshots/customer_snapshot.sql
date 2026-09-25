{%snapshot customer_snapshot %}
{{
    
    config(
        target_schema='main',
        unique_key='cust_id',
        strategy='check',
        check_cols=['customer_name', 'country_of_residence', 'country_of_birth', 'date_of_birth']
    )
}}

select * from {{ ref('customer_latest') }}

{%endsnapshot %}

