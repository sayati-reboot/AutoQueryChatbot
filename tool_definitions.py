AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "policy_fetcher",
            "description": (
                "Search the policy knowledge base for passages relevant to a general "
                "policy question. Do not use this for customer-specific risk assessment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The policy question to search for.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_db",
            "description": (
                "Retrieve factual data from the curated customer_dim, account_dim, "
                "and transaction_fact tables. Use for data lookups, filters, "
                "comparisons, and aggregations. Provide the user's request in "
                "natural language; do not write SQL yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's natural-language data request.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "risk_assess_customer",
            "description": (
                "Assess the risk of a specific customer based on their attributes "
                "and extracted policy rules. Use for customer-specific risk assessment "
                "questions. Choose risk_intent='geography' for geographic risk, "
                "'transaction' for transaction risk, or 'all' for an overall assessment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": (
                            "The unique identifier of the customer to assess."
                        ),
                    },
                    "question": {
                        "type": "string",
                        "description": (
                            "The specific risk assessment question about the customer."
                        ),
                    },
                    "risk_intent": {
                        "type": "string",
                        "enum": ["geography", "transaction", "all"],
                        "description": (
                            "Score geography-only rules, transaction-only rules, or all rules. "
                            "Use all when the question requests an overall assessment or both categories."
                        ),
                    },
                },
                "required": ["customer_id", "question", "risk_intent"],
                "additionalProperties": False,
            },
        },
    },
]
