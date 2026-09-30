import json
import subprocess
from pathlib import Path

import duckdb

from config import DUCKDB_FILE


PROJECT_DIR = Path(__file__).resolve().parent
DBT_PROJECT_DIR = PROJECT_DIR / "dbt"
DBT_PROFILES_DIR = Path.home() / ".dbt"
DBT_BIN = PROJECT_DIR / ".dbt-venv" / "bin" / "dbt"


def risk_assess_customer(customer_id: str, question: str, risk_intent: str) -> str:
    try:
        customer_id_value = int(str(customer_id).strip())
    except (TypeError, ValueError):
        return json.dumps(
            {"status": "invalid_customer_id", "message": "Customer ID must be an integer."}
        )
    risk_intent = str(risk_intent).strip().lower()
    if risk_intent not in {"geography", "transaction", "all"}:
        return json.dumps(
            {
                "status": "invalid_risk_intent",
                "message": "Risk intent must be geography, transaction, or all.",
            }
        )

    if not DBT_BIN.is_file():
        return json.dumps(
            {"status": "dbt_unavailable", "message": f"dbt executable not found: {DBT_BIN}"}
        )

    connection = duckdb.connect(str(DUCKDB_FILE), read_only=True)
    try:
        customer_exists = connection.execute(
            "select 1 from customer_dim where cust_id = ? limit 1",
            [customer_id_value],
        ).fetchone()
    finally:
        connection.close()
    if not customer_exists:
        return json.dumps(
            {
                "status": "customer_not_found",
                "customer_id": customer_id_value,
                "message": "No customer with that ID exists in customer_dim.",
            }
        )

    command = [
        str(DBT_BIN),
        "run",
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROFILES_DIR),
        "--select",
        "customer_rule_features",
        "customer_risk_score",
        "--vars",
        json.dumps(
            {"customer_id": customer_id_value, "risk_intent": risk_intent}
        ),
    ]
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return json.dumps(
            {
                "status": "dbt_timeout",
                "customer_id": customer_id_value,
                "message": "Customer feature calculation timed out.",
            }
        )

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "No dbt output was produced.").strip()
        print(f"dbt customer_rule_features failed for customer {customer_id_value}:\n{details}")
        return json.dumps(
            {
                "status": "feature_calculation_failed",
                "customer_id": customer_id_value,
                "message": "Customer feature calculation failed; check the dbt output for details.",
            }
        )

    connection = duckdb.connect(str(DUCKDB_FILE), read_only=True)
    try:
        cursor = connection.execute(
            """select
                   risk_intent,
                   rule_category,
                   rule_id,
                   feature_name,
                   feature_value,
                   feature_boolean,
                   feature_numeric,
                   rule_hit,
                   applied_score,
                   category_total_score,
                   total_score,
                   unsupported_rule_count,
                   calculation_status,
                   calculation_note,
                   policy_version,
                   section_number,
                   rule_description,
                   business_term_needed_for_calculation,
                   score_to_assign,
                   rule_extraction_date,
                   score_calculated_at
               from customer_risk_score
               where customer_id = ? and risk_intent = ?
               qualify row_number() over (
                   partition by rule_id
                   order by score_calculated_at desc
               ) = 1
               order by rule_category, rule_id""",
            [customer_id_value, risk_intent],
        )
        columns = [description[0] for description in cursor.description]
        score_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()

    if not score_rows:
        return json.dumps(
            {
                "status": "no_policy_rules",
                "customer_id": customer_id_value,
                "risk_intent": risk_intent,
                "message": "No extracted policy rules were available for this risk scope.",
            }
        )

    scores_by_category = {"geography": 0, "transaction": 0}
    unsupported_rule_count = 0
    rule_breakdown = []
    for row in score_rows:
        if row["applied_score"] is None:
            unsupported_rule_count += 1
            continue
        scores_by_category[row["rule_category"]] += row["applied_score"]
        if row["applied_score"] == 0:
            continue
        rule_breakdown.append(
            {
                "rule_id": row["rule_id"],
                "category": row["rule_category"],
                "score_awarded": row["applied_score"],
                "feature_name": row["feature_name"],
                "feature_value": row["feature_value"],
                "calculation_status": row["calculation_status"],
                "calculation_note": row["calculation_note"],
                "policy_source": row["policy_version"].split(":", 1)[0],
                "policy_version": row["policy_version"],
                "section_number": row["section_number"],
                "rule_description": row["rule_description"],
                "business_term_needed_for_calculation": row[
                    "business_term_needed_for_calculation"
                ],
                "rule_extraction_date": row["rule_extraction_date"],
            }
        )

    total_score = scores_by_category["geography"] + scores_by_category["transaction"]

    return json.dumps(
        {
            "status": "features_calculated",
            "customer_id": customer_id_value,
            "risk_intent": risk_intent,
            "total_score": total_score,
            "scores_by_category": scores_by_category,
            "matched_rule_count": len(rule_breakdown),
            "unsupported_rule_count": unsupported_rule_count,
            "score_completeness": (
                "partial" if unsupported_rule_count else "complete"
            ),
            "rule_breakdown": rule_breakdown,
            "message": (
                "Only nonzero contributing rules are included in the breakdown. "
                "Unsupported rules are excluded from the totals."
            ),
        },
        default=str,
    )
