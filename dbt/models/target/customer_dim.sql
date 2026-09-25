select
    cust_id,
    customer_name,
    country_of_residence,
    country_of_birth,
    date_of_birth,
    record_arrival_date
from {{ ref('customer_snapshot') }}
where dbt_valid_to is null