import os

import requests


class DataHubMetadataService:
    def __init__(self, datahub_url: str | None = None, token: str | None = None):
        self.datahub_url = (datahub_url or os.getenv("DATAHUB_GMS_URL") or "http://localhost:8080").rstrip("/")
        self.token = token if token is not None else os.getenv("DATAHUB_GMS_TOKEN", "")

    @property
    def headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def execute_graphql(self, query, variables=None):
        response = requests.post(
            f"{self.datahub_url}/api/graphql",
            json={"query": query, "variables": variables or {}},
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_pii_columns(self, pii_tag="pii_direct"):
        """Return {dataset_name: {field_path_1, field_path_2}} for direct-PII fields."""
        graphql_query = """
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

        variables = {
            "input": {
                "type": "DATASET",
                "query": "*",
                "start": 0,
                "count": 1000,
            }
        }

        result = self.execute_graphql(graphql_query, variables)
        pii_columns = {}

        for dataset in result.get("data", {}).get("search", {}).get("searchResults", []):
            entity = dataset.get("entity", {})
            urn = entity.get("urn", "")
            dataset_name = urn.rsplit(":", 1)[-1].rsplit(",", 1)[0] if urn else ""
            dataset_name = dataset_name.rsplit("(", 1)[0] if dataset_name else ""
            dataset_name = dataset_name.strip().lower()
            if not dataset_name:
                continue

            for field in entity.get("schemaMetadata", {}).get("fields", []):
                field_name = str(field.get("fieldPath", "")).strip()
                tags = field.get("globalTags", {}).get("tags", [])
                tag_names = {tag.get("tag", {}).get("name") for tag in tags}
                if pii_tag in tag_names:
                    pii_columns.setdefault(dataset_name, set()).add(field_name)

        return pii_columns