import json
from openai import OpenAI
from config import MODEL

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

with open(
    "/Users/swarnalidatta/Desktop/AutoQueryChatbot/schema.json",
    "r",
    encoding="utf-8",
) as schema_file:
    SCHEMA_DETAILS = json.load(schema_file)


def execution_plan(query):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You translate user questions into DuckDB SQL queries. "
                    "Return a json object containing  two details. One is the intent, so user wants to query and see results or user wants to create a report. intent can have then outcome value query|report. The second value is the SQL query. Use only tables and columns "
                    f"from this schema:\n{json.dumps(SCHEMA_DETAILS, indent=2)}"
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    return json.loads(response.choices[0].message.content)