import json
import os
from typing import Dict, Iterable, Optional, Set

import requests
import sqlglot
from sqlglot import exp


DATAHUB_URL = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
DATAHUB_TOKEN = os.getenv("DATAHUB_GMS_TOKEN", "")

def _safe_tags(field):
    global_tags = field.get("globalTags") or {}
    tags = global_tags.get("tags") or []
    return tags

def _normalize_table_name(name: Optional[str]) -> str:
    if not name:
        return ""
    normalized = str(name).strip().lower().replace('"', '')
    if "." in normalized:
        normalized = normalized.split(".")[-1]
    return normalized


def _dataset_name_from_urn(urn: str) -> str:
    if not urn:
        return ""
    if urn.startswith("urn:li:dataset:"):
        inner = urn[len("urn:li:dataset:") :]
        if inner.startswith("(") and inner.endswith(")"):
            inner = inner[1:-1]
        if "," in inner:
            inner = inner.rsplit(",", 1)[0]
        if "," in inner:
            return _normalize_table_name(inner.split(",")[-1])
        return _normalize_table_name(inner)
    return _normalize_table_name(urn)


def _get_pii_direct_fields_from_datahub(datahub_url: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Set[str]]:
    url = (datahub_url or DATAHUB_URL).rstrip("/")
    auth_token = token if token is not None else DATAHUB_TOKEN
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    query = """
    query searchDataset($input: SearchInput!) {
      search(input: $input) {
        searchResults {
          entity {
            ... on Dataset {
              urn
              schemaMetadata {
                fields {
                  fieldPath
                  globalTags {
                    tags {
                      tag {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {
            "input": {
                "type": "DATASET",
                "query": "*",
                "start": 0,
                "count": 1000,
            }
        },
    }

    try:
        response = requests.post(
            f"{url}/api/graphql",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
    except Exception:
        return {}

    pii_direct_fields: Dict[str, Set[str]] = {}
    search_results = result.get("data", {}).get("search", {}).get("searchResults", [])
    for item in search_results:
        entity = item.get("entity", {})
        urn = entity.get("urn", "")
        dataset_name = _dataset_name_from_urn(urn)
        if not dataset_name:
            continue
        schema_metadata = entity.get("schemaMetadata") or {}
        for field in schema_metadata.get("fields") or []:
            #global_tags = field.get("globalTags") or {}
            #tags = global_tags.get("tags") or []
            tags = _safe_tags(field)
            tag_names = {tag.get("tag", {}).get("name") for tag in tags}
            if tag_names & {"pii_direct", "dbt:pii_direct"}:
                pii_direct_fields.setdefault(dataset_name, set()).add(
                    str(field.get("fieldPath", "")).strip()
                )
    return pii_direct_fields


def _resolve_table_aliases(statement: exp.Expression) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for table in statement.find_all(exp.Table):
        table_name = table.name
        if not table_name:
            continue
        normalized_table_name = _normalize_table_name(table_name)
        aliases[normalized_table_name] = normalized_table_name
        if table.alias:
            aliases[_normalize_table_name(table.alias)] = normalized_table_name
    return aliases


def _column_fully_qualified_name(column: exp.Column, alias_map: Dict[str, str]) -> Set[str]:
    candidates: Set[str] = set()
    raw_name = column.name.lower()
    if column.table:
        resolved_table = alias_map.get(_normalize_table_name(column.table), _normalize_table_name(column.table))
        candidates.add(f"{resolved_table}.{raw_name}")
        candidates.add(raw_name)
    else:
        for table_name in alias_map.values():
            candidates.add(f"{table_name}.{raw_name}")
        candidates.add(raw_name)
    return {candidate.lower() for candidate in candidates}


def _matches_pii_column(column: exp.Column, alias_map: Dict[str, str], pii_columns: Dict[str, Set[str]]) -> bool:
    candidates = _column_fully_qualified_name(column, alias_map)
    for table_name, fields in pii_columns.items():
        normalized_table = _normalize_table_name(table_name)
        for field in fields:
            normalized_field = str(field).strip().lower().replace('"', '')
            full_name = f"{normalized_table}.{normalized_field}"
            if full_name in candidates:
                return True
            if normalized_field == column.name.lower() and normalized_table in alias_map.values():
                return True
    return False


def mask_sql_for_pii(sql: str, pii_direct_fields: Optional[Dict[str, Set[str]]] = None, datahub_url: Optional[str] = None, token: Optional[str] = None) -> str:
    if not sql or not sql.strip():
        return sql

    if "`" in sql:
        sql = sqlglot.parse_one(sql, read="mysql").sql(dialect="duckdb")

    if pii_direct_fields is None:
        pii_direct_fields = _get_pii_direct_fields_from_datahub(datahub_url=datahub_url, token=token)
    if not pii_direct_fields:
        return sql

    statement = sqlglot.parse_one(sql, read="duckdb")
    alias_map = _resolve_table_aliases(statement)

    for select in statement.find_all(exp.Select):
        for expr in list(select.expressions):
            candidate = expr
            if isinstance(candidate, exp.Alias):
                candidate = candidate.this
            if isinstance(candidate, exp.Column) and _matches_pii_column(candidate, alias_map, pii_direct_fields):
                replacement = exp.Literal.string("***MASKED***")
                if isinstance(expr, exp.Alias):
                    expr.set("this", replacement)
                else:
                    select.expressions[select.expressions.index(expr)] = replacement

    return statement.sql(dialect="duckdb")
