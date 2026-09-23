select *
from {{ ref('transaction_latest') }}
where transaction_id is null
