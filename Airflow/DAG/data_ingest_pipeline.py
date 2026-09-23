from datetime import datetime, timedelta
from pathlib import Path
import sys

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
import duckdb

sys.path.insert(0, "/Users/swarnalidatta/Desktop/AutoQueryChatbot")

from config import DUCKDB_FILE
from stage_load import load_data_to_all_stages

DATA_INPUT_DIR = Path('/Users/swarnalidatta/Desktop/AutoQueryChatbot/Data/In')

#check if any csv file arrived in the input directory
def check_for_csv_files():
    file_exist = any(DATA_INPUT_DIR.glob('*.csv'))
    return file_exist

def load_data_to_staging():
    conn = duckdb.connect(DUCKDB_FILE)
    try:
        load_data_to_all_stages(str(DATA_INPUT_DIR), conn)
    except Exception as e:
        print(f"Error loading data to staging: {e}")
        raise
    finally:
        conn.close()

with DAG(
    dag_id="mini_riskagent_file_ingestion",
    start_date=datetime(2026, 1, 1),
    schedule="*/1 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "autoquery",
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
) as dag:

    wait_for_csv = PythonSensor(
        task_id="wait_for_csv",
        python_callable=check_for_csv_files,
        poke_interval=30,
        timeout=3600,
        mode="reschedule",
    )

    load_all_stages = PythonOperator(
        task_id="load_data_to_all_staging_tables",
        python_callable=load_data_to_staging,
    )

    DBT_PROJECT_DIR = "/Users/swarnalidatta/Desktop/AutoQueryChatbot/dbt"
    DBT_PROFILES_DIR = "/Users/swarnalidatta/.dbt"
    DBT_BIN = "/Users/swarnalidatta/Desktop/AutoQueryChatbot/.airflow-venv/bin/dbt"

    dbt_latest = BashOperator(
        task_id="run_dbt_latest_state_models",
        bash_command=(
            f"{DBT_BIN} run "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--select path:models/latest_state_per_entity"
        ),
    )

    dbt_latest_tests = BashOperator(
        task_id="run_dbt_latest_state_tests",
        bash_command=(
            f"{DBT_BIN} test "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--select path:tests"
        ),
    )

    dbt_snapshot = BashOperator(
        task_id="run_dbt_snapshots",
        bash_command=(
            f"{DBT_BIN} snapshot "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR}"
        ),
    )

    dbt_target = BashOperator(
        task_id="run_dbt_target_models",
        bash_command=(
            f"{DBT_BIN} run "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--select path:models/target"
        ),
    )

    wait_for_csv >> load_all_stages >> dbt_latest >> dbt_latest_tests >> dbt_snapshot >> dbt_target





