import json
import re
from pathlib import Path

import duckdb
import yaml
from openai import OpenAI

from config import DUCKDB_FILE, MODEL
from pii_masker import mask_sql_for_pii

from sql_validator import SQLValidator



PROJECT_DIR = Path(__file__).resolve().parent
TARGET_SCHEMA = yaml.safe_load(
    (PROJECT_DIR / "dbt" / "models" / "target" / "target_schema_config.yml")
    .read_text(encoding="utf-8")
)
SEMANTIC_MODELS = (
    PROJECT_DIR / "dbt" / "models" / "semantic_models.yml"
).read_text(encoding="utf-8")

TABLE_GRAINS = {
    "customer_dim": "One current row per customer (cust_id).",
    "account_dim": "One current row per account (account_id).",
    "transaction_fact": "One row per transaction (transaction_id).",
}

RELATIONSHIP_CONTEXT = {
    "tables": [
        {
            "name": model["name"],
            "grain": TABLE_GRAINS.get(model["name"], "See model description."),
            "columns": [column["name"] for column in model.get("columns", [])],
        }
        for model in TARGET_SCHEMA.get("models", [])
    ],
    "relationships": [
        {
            "from_table": "customer_dim",
            "from_column": "cust_id",
            "to_table": "account_dim",
            "to_column": "customer_id",
            "cardinality": "one_to_many",
        },
        {
            "from_table": "account_dim",
            "from_column": "account_id",
            "to_table": "transaction_fact",
            "to_column": "account_id",
            "cardinality": "one_to_many",
        },
    ],
    "join_paths": [
        {
            "from_table": "customer_dim",
            "to_table": "transaction_fact",
            "via_tables": ["account_dim"],
            "joins": [
                {
                    "left_table": "customer_dim",
                    "left_column": "cust_id",
                    "right_table": "account_dim",
                    "right_column": "customer_id",
                },
                {
                    "left_table": "account_dim",
                    "left_column": "account_id",
                    "right_table": "transaction_fact",
                    "right_column": "account_id",
                },
            ],
            "direct_relationship": False,
        },
    ],
    "join_rules": [
        "when users question is mainly about customer information, the query must atleast contain customer_dim table and then other tables are joined only if required filter columns or selection columns are in different tables."
        "when users question is mainly about transaction information, the query must atleast contain transaction_fact table and then other tables are joined only if required filter columns or selection columns are in different tables."
        "when users question is mainly about account information, the query must atleast contain account_dim table and then other tables are joined only if required filter columns or selection columns are in different tables."
        "If one table contains all requested output and filter columns, query only that table.",
        "If requested output and filter columns span multiple tables, use only the declared relationship keys to join them. Also check the join paths to join them.",
        "Do not invent columns or join paths.",
        "A customer-to-transaction query must follow the declared join_path through account_dim.",
        "when user is seeking customer information and transaction information, join customer_dim to account_dim first, then account_dim to transaction_fact.",
        "Never join customer_dim directly to transaction_fact.",
        "Use the fewest tables necessary.",
        "Do not join merely because a relationship exists.",
        "Use joins only when requested fields span related tables.",
        

    ],
}

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def generate_sql_query(query: str, previous_sql: str = "", execution_error: str = "") -> str:
    instructions = (
        "Translate the user's natural-language request into one read-only DuckDB SELECT query. "
        "Use DuckDB syntax and never quote identifiers with backticks; use unquoted identifiers or double quotes. "
        "Return only JSON with one key named sql_query." 
        "First map each requested output and filter columns to its owning table. Use a single table "
        "when it contains everything required; do not select non-existent or imaginery columns from tables." 
        "Do not add joins unnecessarily." 
        "While you see needed columns are from multiple tables, "
        "use only the declared relationship keys and always check the join paths to join them. "
        "When fields span tables, use only the declared relationship keys. "
        "Please make sure you use joining conditions only mentioned in relationships and join_paths Use "
        "only listed curated tables and columns; never use raw stage tables or "
        "invent columns. direct join is possible between account_dim and transaction_fact, between customer_dim and account_dim. But direct join is not possible between customer_dim and transaction_fact."
        " Do not directly join customer_dim to transaction_fact. If both are needed, "
        "the SQL must join customer_dim to account_dim first, then account_dim "
        "to transaction_fact. "
        "Select only relevant factual columns and limit unaggregated results to "
        "100 rows."
        "if the query is going for any measures mentioned in the semantic layer, use the semantic layer definitions" 
        "to generate the SQL. "
        "do not create query with column names that are not found in the schema or semantic layer. "
    )
    context = "\n\n".join(
        (
            f"TARGET TABLE SCHEMA:\n{json.dumps(TARGET_SCHEMA, indent=2)}",
            f"SEMANTIC LAYER:\n{SEMANTIC_MODELS}",
            f"TABLES, GRAINS, RELATIONSHIPS, JOIN RULES:\n{json.dumps(RELATIONSHIP_CONTEXT, indent=2)}",
        )
    )
    user_request = query
    if previous_sql and execution_error:
        user_request += (
            "\n\nThe previous SQL attempt failed during DuckDB binding. Correct it "
            "using the schema and relationship rules above."
            f"\nPrevious SQL:\n{previous_sql}"
            f"\nDuckDB error:\n{execution_error}"
        )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"{instructions}\n\n{context}"},
            {"role": "user", "content": user_request},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("The SQL planner returned an empty response.")
    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"The SQL planner returned invalid JSON: {content!r}") from error
    sql_query = result.get("sql_query") if isinstance(result, dict) else None
    if not isinstance(sql_query, str) or not sql_query.strip():
        raise RuntimeError(f"The SQL planner returned no SQL query: {result!r}")
    return sql_query.strip()


def query_db(query: str) -> str:
    previous_sql = ""
    execution_error = ""

    for attempt in range(2):
        sql_query = generate_sql_query(
            query,
            previous_sql=previous_sql,
            execution_error=execution_error,
        ).strip().rstrip(";")
        #if not re.match(r"^(select|with)\b", sql_query, flags=re.IGNORECASE):
         #   raise ValueError("Generated SQL must be a read-only SELECT query.")
        if ";" in sql_query:
            raise ValueError("Generated SQL must contain exactly one statement.")
        sql_query = mask_sql_for_pii(sql_query)
        if not SQLValidator.validate_sql(sql_query):
            return json.dumps({
                "error": "I can only run read-only queries. Please rephrase your request."
            })
        if SQLValidator.validate_sql(sql_query):
            connection = duckdb.connect(DUCKDB_FILE, read_only=True)
            try:
                cursor = connection.execute(sql_query)
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchmany(101)
                truncated = len(rows) > 100
                rows = rows[:100]
                return json.dumps({
                    "query": sql_query,
                    "row_count_returned": len(rows),
                    "truncated": truncated,
                    "results": [dict(zip(columns, row)) for row in rows],
                }, default=str)
            except duckdb.Error as error:
                if attempt == 1:
                    raise RuntimeError(
                        f"Generated SQL failed after one correction attempt: {error}"
                    ) from error
                previous_sql = sql_query
                execution_error = str(error)
            finally:
                connection.close()
    #print("Could not generate an executable SQL query for the given request.")
    #raise RuntimeError("Could not generate an executable SQL query for the given request.")
    print(f"Query failed after retry: {error}")
    return json.dumps({
        "error": "I couldn't run that query. Please try rephrasing it."
    })