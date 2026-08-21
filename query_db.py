import duckdb
from config import DUCKDB_FILE

def query_db(sql_query):
    conn=duckdb.connect(DUCKDB_FILE)
    try:
        result=conn.execute(sql_query).fetchdf()
        return result
    except Exception:
        raise
    finally:
        conn.close()