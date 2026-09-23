import json
from pathlib import Path

import chromadb
from openai import OpenAI
from config import MODEL


PROJECT_DIR = Path(__file__).resolve().parent
CHROMA_DIR = PROJECT_DIR / "DB" / "chroma_policy"
COLLECTION_NAME = "risk_policies"

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

with open(
    PROJECT_DIR / "schema.json",
    "r",
    encoding="utf-8",
) as schema_file:
    SCHEMA_DETAILS = json.load(schema_file)

SEMANTIC_MODELS = (
    PROJECT_DIR / "dbt" / "models" / "semantic_models.yml"
).read_text(encoding="utf-8")

RELATIONSHIP_CONTEXT = """
RELATIONSHIPS:
- customer_dim.cust_id = account_dim.customer_id
- account_dim.account_id = transaction_fact.account_id
- To connect a customer to transactions, join customer_dim to account_dim,
  then account_dim to transaction_fact.
- Customer to account example:
    FROM customer_dim AS c
    JOIN account_dim AS a ON c.cust_id = a.customer_id
- Customer to transaction example:
    FROM customer_dim AS c
    JOIN account_dim AS a ON c.cust_id = a.customer_id
    JOIN transaction_fact AS t ON a.account_id = t.account_id
- Do not join customer_dim directly to transaction_fact because they do not
    share a customer key.
""".strip()


def retrieve_policy_context(query: str, n_results: int = 3) -> str:
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    policy_results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["metadatas", "documents"],
    )
    policy_chunks = []
    for document, metadata in zip(
        policy_results.get("documents", [[]])[0],
        policy_results.get("metadatas", [[]])[0],
    ):
        policy_chunks.append(
            f"Source: {metadata.get('source')}\n"
            f"Section: {metadata.get('section')}\n"
            f"{document}"
        )
    return "\n\n---\n\n".join(policy_chunks)


def execution_plan(query):
    policy_context = retrieve_policy_context(query)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a database query planner. Translate the user request "
                    "into valid DuckDB SQL. The request may ask for factual data, "
                    "customer risk ratings, transaction risk analysis, or reports "
                    "for risk-rated clients. Use the policy context to identify "
                    "which factual data must be queried, but keep policy scoring "
                    "out of SQL. A risk score is calculated later from policy and "
                    "queried facts. Select the factual columns needed to support "
                    "the final explanation. "
                        "Never invent tables or columns such as geographic_risk_score, "
                        "risk_score, georisk, or geographic_data. Use only the listed "
                        "customer_dim, account_dim, and transaction_fact fields; do not "
                        "query the raw customer_stage, account_stage, or transaction_stage "
                        "tables. Never return an empty sql_query. For example, for a "
                        "customer risk question, query customer_dim by cust_id and "
                        "include the customer geography fields needed to apply the "
                       "retrieved policy. Do not calculate geographic_risk_score or "
                       "transaction_risk_score in SQL, do not invent jurisdiction "
                       "values, and do not add CASE expressions for policy points. "
                    "Do not use SUM, GROUP BY, or any risk-score alias to calculate "
                    "policy points in SQL. Return raw facts; the application will "
                    "apply the policy after the query returns. "
                    "Return only a "
                    "JSON object with exactly these keys: "
                    '"intent" (value "query" or "report") and "sql_query". '
                    "Use intent=report when the user asks for a report. Use only "
                    "tables and columns from the database schema. The SQL should "
                    "return the factual fields needed by the application to apply "
                    "the retrieved policy and produce a risk rating or report.\n\n"
                    f"DATABASE SCHEMA:\n{json.dumps(SCHEMA_DETAILS, indent=2)}\n\n"
                    f"{RELATIONSHIP_CONTEXT}\n\n"
                    f"DBT SEMANTIC LAYER:\n{SEMANTIC_MODELS}\n\n"
                    f"RETRIEVED POLICY CONTEXT:\n{policy_context}"
                ),
            },
            {"role": "user", "content": query},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("The Ollama model returned an empty planning response.")
    try:
        plan = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"The Ollama model returned invalid JSON: {content!r}") from error

    if not isinstance(plan, dict) or not plan.get("sql_query"):
        raise RuntimeError(
            "The Ollama model returned an incomplete execution plan. "
            f"Expected intent and sql_query, received: {plan!r}"
        )
    if plan.get("intent") not in {"query", "report"}:
        raise RuntimeError(
            f"The Ollama model returned an unsupported intent: {plan.get('intent')!r}"
        )
    return plan