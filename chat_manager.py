from llm_planner import MODEL, client, execution_plan, retrieve_policy_context
from query_db import query_db
from generate_report import generate_report


def _generate_answer(query, results):
    policy_context = retrieve_policy_context(query)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a risk analysis assistant. Answer the user's question "
                    "using only the database facts and retrieved policy context. "
                    "When the question asks for a risk rating, calculate it from "
                    "the applicable policy rules, explain each applied rule and "
                    "show the resulting points. Do not invent fields or facts. "
                    "If a policy value or required fact is missing, say so clearly."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{query}\n\n"
                    f"Database facts:\n{results.to_json(orient='records', date_format='iso')}\n\n"
                    f"Retrieved policy context:\n{policy_context}"
                ),
            },
        ],
    )
    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        raise RuntimeError("The Ollama model returned an empty risk analysis.")
    return answer.strip()


def process_manager(query):
    plan = execution_plan(query)
    sql_query = plan["sql_query"]

    query_result = query_db(sql_query)

    if plan["intent"] == "query":
        return {
            "type": "text",
            "query": query_result["query"],
            "results": query_result["results"],
            "answer": _generate_answer(query, query_result["results"]),
        }

    if plan["intent"] == "report":
        report = generate_report(
            query_result["results"],
            query_result["query"],
        )

        return {
            "type": "file",
            "query": report["query"],
            "report": report["report"],
        }

    raise ValueError(f"Unsupported intent: {plan['intent']}")