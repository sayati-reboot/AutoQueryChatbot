{{ config(materialized='table') }}
select *
from {{ source('transaction_stage', 'transaction_stage') }}
qualify row_number() over (
    partition by transaction_id
    order by record_arrival_date desc
) = 1
