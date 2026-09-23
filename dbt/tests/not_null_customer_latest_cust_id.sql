select *
from {{ ref('customer_latest') }}
where cust_id is null
