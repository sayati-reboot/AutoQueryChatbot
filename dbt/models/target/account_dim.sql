select
    account_id,
    account_number,
    customer_id,
    customer_type,
    account_status,
    record_arrival_date
from {{ ref('account_snapshot') }}
where dbt_valid_to is null