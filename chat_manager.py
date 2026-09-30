import json

from openai import OpenAI

from config import MODEL
from tool_definitions import AVAILABLE_TOOLS
from tool_registry import TOOL_FUNCTIONS


client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

INTENTS = {
    "database_query": "Retrieve, filter, compare, or aggregate data from the database.",
    "policy_question": "Ask what a policy says, questions about risk rules , risk scored ,"
    "high/low/medium risk geographic locations and related policies etc. without assessing a specific customer."
    "Any questions  asking for policy information should be classified as policy_question.",
    "customer_risk_assessment": "Assess risk for a specific customer using their data.",
    "report_generation": "Create a report from available data.",
    "ambiguous_intent": "The request is unclear or does not fit another category.",
}

MAX_TOOL_ROUNDS = 5
TOOLS_BY_INTENT = {
    "database_query": {"query_db"},
    "policy_question": {"policy_fetcher"},
    "customer_risk_assessment": {"risk_assess_customer", "policy_fetcher"},
    "report_generation": {"query_db"},
    "ambiguous_intent": set(),
}


def classify_intent(query):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the request into exactly one listed intent. Return "
                    "only JSON with one key named intent. Choose report_generation "
                    "for explicit report requests; customer_risk_assessment for "
                    "risk assessment of a specific customer; policy_question for "
                    "general questions about policy rules or classifications; "
                    "database_query for other data requests; and ambiguous_intent "
                    "only when unclear.\n"
                    f"Intent definitions:\n{json.dumps(INTENTS, indent=2)}"
                ),
            },
            {"role": "user", "content": query},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("The Ollama model returned an empty intent response.")
    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"The Ollama model returned invalid intent JSON: {content!r}") from error

    intent = result.get("intent") if isinstance(result, dict) else None
    if intent not in INTENTS:
        raise RuntimeError(f"The Ollama model returned unsupported intent: {result!r}")
    return intent


def run_agent(query, intent):
    allowed_tool_names = TOOLS_BY_INTENT[intent]
    available_tools = [
        tool
        for tool in AVAILABLE_TOOLS
        if tool["function"]["name"] in allowed_tool_names
    ]
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant with access only to the tools provided for "
                "this request's classified intent. Choose among those tools when "
                "useful and base conclusions on their results, not invented facts. "
                "If a needed capability is not available among the provided tools, "
                "explain that limitation. If tool "
                "results include source and section metadata, cite the relevant "
                "source document and numbered section in the final answer. Include "
                "the subsection number too when it appears in the retrieved passage "
                "(for example, Section 4.2). Do not put any section if it was not retrieved. "
                "Preserve titles accurately and do not make up section numbers. "
                "If the intent is database_query, and the user asks for the source SQL, reproduce the exact query "
                "if the intent is database_query and multiple columns are being returned, provide them in table format and unadulted."
                "if the intent is database_query and one or more of the returned columns are masked, do not hide them or remove them from output, please show them with masked condition. show them as masked as is and you can mention that column is masked because of PII masking. "
                "if the intent is database_query and the toolcall return error stating it was not a read only query - please mention that any update insert like operations are blocked. State the original error message you recieved from the toolcall. Never do this for any other intent. "
                "If the intent is policy_question, provide retrieved policy sesctions for the policy documents, no need to show the SQL query for policy fetching"
                "If the intent is policy_fetching, always provide the retrieved policy sections for the policy documents."
                "If the intent is customer_risk_assessment, explain the returned customer risk total and category breakdown using only the tool result. "
                "If the intent is customer_risk_assessment,Always show exactly these three score lines: Geographic risk score, Transaction risk score, and Overall risk score, including scores of 0. "
                "If the intent is customer_risk_assessment,Show rule explanations only for rules in rule_breakdown; those are the only rules that contributed a nonzero score. Do not list zero-score, unmatched, or unsupported rules. "
                "If the intent is customer_risk_assessment,If all three scores are 0, say no supported rules contributed points. If score_completeness is partial, add one brief note that some rules could not be evaluated, without listing them. "
                "If the intent is customer_risk_assessment,If the intent is customer_risk_assessment,For each contributing rule, include its policy section, awarded score, and feature evidence. "
                "If the intent is customer_risk_assessment,For customer_risk_assessment, use only the risk_assess_customer tool. If it reports an error, explain that error briefly and stop; do not invent or request a dbt_output or other tool. "
                f"Classified intent: {intent}"
            ),
        },
        {"role": "user", "content": query},
    ]
    risk_assessment_json = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=available_tools or None,
            tool_choice="auto" if available_tools else "none",
            temperature=0,
        )
        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []
        if not tool_calls:
            answer = assistant_message.content
            if not answer or not answer.strip():
                raise RuntimeError("The model returned an empty response.")
            if intent == "customer_risk_assessment" and risk_assessment_json:
                return (
                    f"{answer.strip()}\n\nRisk assessment details (JSON):\n"
                    f"```json\n{risk_assessment_json}\n```"
                )
            return answer.strip()

        messages.append(assistant_message.model_dump(exclude_none=True))
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            if tool_name not in allowed_tool_names:
                raise RuntimeError(
                    f"Tool '{tool_name}' is not allowed for intent '{intent}'."
                )
            tool_function = TOOL_FUNCTIONS.get(tool_name)
            if tool_function is None:
                raise RuntimeError(
                    f"The model requested an unregistered tool: {tool_name}"
                )
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"The model returned invalid arguments for {tool_name}."
                ) from error
            tool_result = tool_function(**arguments)
            if intent == "customer_risk_assessment" and tool_name == "risk_assess_customer":
                risk_assessment_json = str(tool_result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result),
                }
            )

    raise RuntimeError("The model exceeded the maximum number of tool-call rounds.")


def process_manager(query):
    intent = classify_intent(query)
    if intent == "ambiguous_intent":
        return {
            "type": "text",
            "intent": intent,
            "query": None,
            "results": None,
            "answer": "I’m not sure what you’d like me to do. Could you clarify your request?",
        }
    return {
        "type": "text",
        "intent": intent,
        "query": None,
        "results": None,
        "answer": run_agent(query, intent),
    }