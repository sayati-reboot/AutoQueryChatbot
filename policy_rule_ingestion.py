import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
from openai import OpenAI

from config import DUCKDB_FILE, MODEL


PROJECT_DIR = Path(__file__).resolve().parent
POLICY_DIR = PROJECT_DIR / "Policy_Docs"
POLICY_CLIENT = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
RULE_TABLE = "rule_extraction_details"
RULE_EXTRACTOR_VERSION = "2"


def _extract_policy_rules(policy_key: str, policy_text: str) -> list[dict[str, Any]]:
    current_section = None
    section_rule_counts: dict[str, int] = {}
    source_rules = []
    for line in policy_text.splitlines():
        heading = re.match(
            r"^#{1,6}\s+(\d+(?:\.\d+)*)(?:\.(?=\s)|(?=\s|$))",
            line,
        )
        if heading:
            current_section = heading.group(1)
            continue

        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        if not bullet or current_section is None:
            continue
        score_matches = list(
            re.finditer(r"\+\s*(\d+)\s+risk points?\b", bullet.group(1), re.IGNORECASE)
        )
        if not score_matches:
            continue
        if len(score_matches) > 1:
            raise ValueError(
                f"Multiple scores in one policy bullet in section {current_section} "
                f"of '{policy_key}'; split the bullet into separate rules."
            )

        section_rule_counts[current_section] = section_rule_counts.get(current_section, 0) + 1
        ordinal = section_rule_counts[current_section]
        source_rules.append(
            {
                "rule_id": f"{policy_key}-S{current_section}-R{ordinal:02d}",
                "section_number": current_section,
                "rule_description": bullet.group(1).strip(),
                "score_to_assign": int(score_matches[0].group(1)),
            }
        )

    if not source_rules:
        raise ValueError(f"No numbered sections found in policy '{policy_key}'.")

    response = POLICY_CLIENT.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "For each supplied scoring rule, identify only the source data terms "
                    "needed to evaluate its condition. Do not rewrite, summarize, merge, "
                    "split, or omit rules. Do not return descriptions, sections, or scores. "
                    "Return JSON only as {\"rules\": [{\"rule_id\": ..., "
                    "\"business_term_needed_for_calculation\": ...}]}. Return exactly "
                    "one entry for every supplied rule and copy each rule_id exactly. "
                    "Do not infer policy behavior beyond the supplied rule and policy text."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"policy_text": policy_text, "scoring_rules": source_rules},
                    ensure_ascii=False,
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError(f"The policy extractor returned no rules for '{policy_key}'.")
    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"The policy extractor returned invalid JSON for '{policy_key}'."
        ) from error

    extracted_rules = result.get("rules") if isinstance(result, dict) else None
    if not isinstance(extracted_rules, list):
        raise ValueError(f"No business terms were extracted from '{policy_key}'.")

    business_terms = {}
    for extracted_rule in extracted_rules:
        if not isinstance(extracted_rule, dict):
            raise ValueError(f"Invalid rule entry in policy '{policy_key}'.")
        rule_id = str(extracted_rule.get("rule_id", "")).strip()
        business_term = str(
            extracted_rule.get("business_term_needed_for_calculation", "")
        ).strip()
        if not rule_id or not business_term or rule_id in business_terms:
            raise ValueError(
                f"Missing or duplicate business-term result for rule '{rule_id}' "
                f"in '{policy_key}'."
            )
        business_terms[rule_id] = business_term

    expected_rule_ids = {rule["rule_id"] for rule in source_rules}
    if set(business_terms) != expected_rule_ids:
        raise ValueError(
            f"The extractor returned an incomplete or unexpected rule list for '{policy_key}'."
        )

    return [
        {
            **rule,
            "business_term_needed_for_calculation": business_terms[rule["rule_id"]],
        }
        for rule in source_rules
    ]


def ingest_policy_rules() -> dict[str, int]:
    policy_files = sorted(POLICY_DIR.glob("*_policy.md"))
    if not policy_files:
        raise FileNotFoundError(f"No policy Markdown files found in {POLICY_DIR}.")

    connection = duckdb.connect(str(DUCKDB_FILE))
    try:
        connection.execute(
            f"""CREATE TABLE IF NOT EXISTS {RULE_TABLE} (
                rule_id VARCHAR NOT NULL,
                policy_version VARCHAR NOT NULL,
                section_number VARCHAR NOT NULL,
                rule_description VARCHAR NOT NULL,
                business_term_needed_for_calculation VARCHAR NOT NULL,
                score_to_assign INTEGER NOT NULL,
                rule_extraction_date TIMESTAMP NOT NULL,
                PRIMARY KEY (rule_id, policy_version)
            )"""
        )

        existing_versions = {
            row[0]
            for row in connection.execute(
                f"SELECT DISTINCT policy_version FROM {RULE_TABLE}"
            ).fetchall()
        }
        extractions = []
        unchanged_count = 0
        for policy_path in policy_files:
            policy_text = policy_path.read_text(encoding="utf-8")
            policy_key = policy_path.stem
            extraction_input = f"{RULE_EXTRACTOR_VERSION}\0{policy_text}"
            checksum = hashlib.sha256(extraction_input.encode("utf-8")).hexdigest()
            policy_version = f"{policy_key}:{checksum}"
            if policy_version in existing_versions:
                unchanged_count += 1
                print(f"Policy unchanged; skipping rule extraction: {policy_path.name}")
                continue

            rules = _extract_policy_rules(policy_key, policy_text)
            extractions.append({"policy_version": policy_version, "rules": rules})

        extraction_date = datetime.now(timezone.utc).replace(tzinfo=None)
        new_rule_count = sum(len(extraction["rules"]) for extraction in extractions)
        if extractions:
            connection.execute("BEGIN TRANSACTION")
            try:
                for extraction in extractions:
                    policy_version = extraction["policy_version"]
                    connection.execute(
                        f"DELETE FROM {RULE_TABLE} WHERE policy_version = ?",
                        [policy_version],
                    )
                    connection.executemany(
                        f"""INSERT INTO {RULE_TABLE} (
                            rule_id,
                            policy_version,
                            section_number,
                            rule_description,
                            business_term_needed_for_calculation,
                            score_to_assign,
                            rule_extraction_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        [
                            (
                                rule["rule_id"],
                                policy_version,
                                rule["section_number"],
                                rule["rule_description"],
                                rule["business_term_needed_for_calculation"],
                                rule["score_to_assign"],
                                extraction_date,
                            )
                            for rule in extraction["rules"]
                        ],
                    )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

        return {
            "policies_extracted": len(extractions),
            "policies_unchanged": unchanged_count,
            "rules_stored": new_rule_count,
        }
    finally:
        connection.close()