
      update "miniriskagent_results_1"."main"."transaction_snapshot" as DBT_INTERNAL_TARGET
    set dbt_valid_to = DBT_INTERNAL_SOURCE.dbt_valid_to
    from "transaction_snapshot__dbt_tmp20260922133217957323" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_scd_id::text = DBT_INTERNAL_TARGET.dbt_scd_id::text
      and DBT_INTERNAL_SOURCE.dbt_change_type::text in ('update'::text, 'delete'::text)
      
        and DBT_INTERNAL_TARGET.dbt_valid_to is null;
      

    insert into "miniriskagent_results_1"."main"."transaction_snapshot" ("transaction_id", "amount", "type", "originating_country", "destination_country", "account_id", "transaction_date", "record_arrival_date", "dbt_updated_at", "dbt_valid_from", "dbt_valid_to", "dbt_scd_id")
    select DBT_INTERNAL_SOURCE."transaction_id",DBT_INTERNAL_SOURCE."amount",DBT_INTERNAL_SOURCE."type",DBT_INTERNAL_SOURCE."originating_country",DBT_INTERNAL_SOURCE."destination_country",DBT_INTERNAL_SOURCE."account_id",DBT_INTERNAL_SOURCE."transaction_date",DBT_INTERNAL_SOURCE."record_arrival_date",DBT_INTERNAL_SOURCE."dbt_updated_at",DBT_INTERNAL_SOURCE."dbt_valid_from",DBT_INTERNAL_SOURCE."dbt_valid_to",DBT_INTERNAL_SOURCE."dbt_scd_id"
    from "transaction_snapshot__dbt_tmp20260922133217957323" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_change_type::text = 'insert'::text;


  