
      update "miniriskagent_results_1"."main"."account_snapshot" as DBT_INTERNAL_TARGET
    set dbt_valid_to = DBT_INTERNAL_SOURCE.dbt_valid_to
    from "account_snapshot__dbt_tmp20260922133217898417" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_scd_id::text = DBT_INTERNAL_TARGET.dbt_scd_id::text
      and DBT_INTERNAL_SOURCE.dbt_change_type::text in ('update'::text, 'delete'::text)
      
        and DBT_INTERNAL_TARGET.dbt_valid_to is null;
      

    insert into "miniriskagent_results_1"."main"."account_snapshot" ("account_id", "account_number", "customer_id", "customer_type", "account_status", "record_arrival_date", "dbt_updated_at", "dbt_valid_from", "dbt_valid_to", "dbt_scd_id")
    select DBT_INTERNAL_SOURCE."account_id",DBT_INTERNAL_SOURCE."account_number",DBT_INTERNAL_SOURCE."customer_id",DBT_INTERNAL_SOURCE."customer_type",DBT_INTERNAL_SOURCE."account_status",DBT_INTERNAL_SOURCE."record_arrival_date",DBT_INTERNAL_SOURCE."dbt_updated_at",DBT_INTERNAL_SOURCE."dbt_valid_from",DBT_INTERNAL_SOURCE."dbt_valid_to",DBT_INTERNAL_SOURCE."dbt_scd_id"
    from "account_snapshot__dbt_tmp20260922133217898417" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_change_type::text = 'insert'::text;


  