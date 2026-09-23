select
    transaction_id,
    amount,
    type,
    originating_country,
    destination_country,
    account_id,
    transaction_date,
    record_arrival_date
from {{ ref('transaction_snapshot') }}
where dbt_valid_to is null