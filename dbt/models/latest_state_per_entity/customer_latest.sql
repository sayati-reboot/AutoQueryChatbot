{{ config(materialized='table') }}

select *
from {{ source('customer_stage', 'customer_stage') }}
qualify row_number() over (
    partition by cust_id
    order by record_arrival_date desc
) = 1
