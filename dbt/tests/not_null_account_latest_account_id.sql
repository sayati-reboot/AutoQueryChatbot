select *
from {{ ref('account_latest') }}
where account_id is null
