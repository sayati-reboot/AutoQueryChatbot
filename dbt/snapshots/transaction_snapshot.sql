{% snapshot transaction_snapshot %}
{{
    config(
        target_schema='main',
        unique_key='transaction_id',
        strategy='check',
        check_cols=[
            'amount',
            'type',
            'originating_country',
            'destination_country',
            'account_id',
            'transaction_date'
        ]
    )
}}

select *
from {{ ref('transaction_latest') }}

{% endsnapshot %}
