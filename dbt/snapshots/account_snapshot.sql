{% snapshot account_snapshot %}
{{
    config(
        target_schema='main',
        unique_key='account_id',
        strategy='check',
        check_cols=[
            'account_number',
            'customer_id',
            'customer_type',
            'account_status'
        ]
    )
}}

select *
from {{ ref('account_latest') }}

{% endsnapshot %}