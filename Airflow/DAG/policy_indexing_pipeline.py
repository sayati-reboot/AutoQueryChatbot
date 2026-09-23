from datetime import datetime, timedelta
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/Users/swarnalidatta/Desktop/AutoQueryChatbot")

from policy_chunker import index_policy_directory


with DAG(
    dag_id="policy_document_indexing",
    start_date=datetime(2026, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "autoquery",
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
) as dag:

    index_policy_documents = PythonOperator(
        task_id="index_policy_documents",
        python_callable=index_policy_directory,
    )
