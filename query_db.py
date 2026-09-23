import pandas as pd
import duckdb
from config import DUCKDB_FILE


def query_db(sql_query):
    connection = duckdb.connect(DUCKDB_FILE, read_only=True)
    try:
        results = connection.execute(sql_query).fetchdf()
        return {
            "query": sql_query,
            "results": results,
        }
    finally:
        connection.close()