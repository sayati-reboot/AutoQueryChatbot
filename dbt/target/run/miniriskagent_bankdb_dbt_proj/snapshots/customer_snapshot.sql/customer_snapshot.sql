
      update "miniriskagent_results_1"."main"."customer_snapshot" as DBT_INTERNAL_TARGET
    set dbt_valid_to = DBT_INTERNAL_SOURCE.dbt_valid_to
    from "customer_snapshot__dbt_tmp20260922133217937419" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_scd_id::text = DBT_INTERNAL_TARGET.dbt_scd_id::text
      and DBT_INTERNAL_SOURCE.dbt_change_type::text in ('update'::text, 'delete'::text)
      
        and DBT_INTERNAL_TARGET.dbt_valid_to is null;
      

    insert into "miniriskagent_results_1"."main"."customer_snapshot" ("cust_id", "country_of_residence", "country_of_birth", "date_of_birth", "record_arrival_date", "dbt_updated_at", "dbt_valid_from", "dbt_valid_to", "dbt_scd_id")
    select DBT_INTERNAL_SOURCE."cust_id",DBT_INTERNAL_SOURCE."country_of_residence",DBT_INTERNAL_SOURCE."country_of_birth",DBT_INTERNAL_SOURCE."date_of_birth",DBT_INTERNAL_SOURCE."record_arrival_date",DBT_INTERNAL_SOURCE."dbt_updated_at",DBT_INTERNAL_SOURCE."dbt_valid_from",DBT_INTERNAL_SOURCE."dbt_valid_to",DBT_INTERNAL_SOURCE."dbt_scd_id"
    from "customer_snapshot__dbt_tmp20260922133217937419" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_change_type::text = 'insert'::text;


  