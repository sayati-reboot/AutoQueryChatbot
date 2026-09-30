from sqlglot import parse_one
import re

class SQLValidator:
    blocked_statements = ("Insert", "Update", "Delete", "Drop", "Alter", "Truncate")

    @staticmethod
    def validate_sql(sql_query):
        sql_query = sql_query.strip().rstrip(";")
        match = re.match(r"^(select|with)\b", sql_query, flags=re.IGNORECASE)
        if not match:
            print(f"SQL is not a select or ready-only statement: {sql_query}")
            return False
         #  raise ValueError("Only read-only SELECT queries are allowed.") 
        operation = match.group(1).upper()
        if operation in SQLValidator.blocked_statements:
            print(f"SQL statement is blocked: {sql_query}")
            return False
        return True