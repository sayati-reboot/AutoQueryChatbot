import os as os
from datetime import datetime
import pandas as pd
from pathlib import Path


def _ensure_stage_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customer_stage (
            cust_id INTEGER,
            country_of_residence VARCHAR,
            country_of_birth VARCHAR,
            date_of_birth DATE,
            record_arrival_date DATE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transaction_stage (
            transaction_id BIGINT,
            amount DECIMAL(18, 2),
            type VARCHAR,
            originating_country VARCHAR,
            destination_country VARCHAR,
            account_id BIGINT,
            transaction_date DATE,
            record_arrival_date DATE
        )
    """)
    conn.execute(
        "ALTER TABLE transaction_stage "
        "ADD COLUMN IF NOT EXISTS transaction_date DATE"
    )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_stage (
            account_id BIGINT,
            account_number VARCHAR,
            customer_id INTEGER,
            customer_type VARCHAR,
            account_status VARCHAR,
            record_arrival_date DATE
        )
    """)


def _append_dataframe(df, table_name, conn):
    conn.register("incoming_data", df)
    try:
        columns = ", ".join(f'"{column}"' for column in df.columns)
        conn.execute(
            f"INSERT INTO {table_name} ({columns}) "
            f"SELECT {columns} FROM incoming_data"
        )
    finally:
        conn.unregister("incoming_data")


def load_data_to_customer_stage(data_file_dir, file_prefix, conn):
    _ensure_stage_tables(conn)
    filelist = os.listdir(data_file_dir)
    for file in filelist:
        if file.startswith(file_prefix) and file.endswith('.csv'):
            file_arriving_date = datetime.strptime(
                file.split('_')[1].split('.')[0], '%d%m%Y'
            ).date()
            file_path = os.path.join(data_file_dir, file)
            df = pd.read_csv(file_path)
            df['record_arrival_date'] = file_arriving_date
            _append_dataframe(df, 'customer_stage', conn)
            print(f"Loaded data from {file} into customer_stage table.")

def load_data_to_transaction_stage(data_file_dir, file_prefix, conn):
    _ensure_stage_tables(conn)
    filelist = os.listdir(data_file_dir)
    for file in filelist:
        if file.startswith(file_prefix) and file.endswith('.csv'):
            file_arriving_date = datetime.strptime(
                file.split('_')[1].split('.')[0], '%d%m%Y'
            ).date()
            file_path = os.path.join(data_file_dir, file)
            df = pd.read_csv(file_path)
            df['record_arrival_date'] = file_arriving_date
            _append_dataframe(df, 'transaction_stage', conn)
            print(f"Loaded data from {file} into transaction_stage table.")

def load_data_to_account_stage(data_file_dir, file_prefix, conn):
    _ensure_stage_tables(conn)
    filelist = os.listdir(data_file_dir)
    for file in filelist:
        if file.startswith(file_prefix) and file.endswith('.csv'):
            file_arriving_date = datetime.strptime(
                file.split('_')[1].split('.')[0], '%d%m%Y'
            ).date()
            file_path = os.path.join(data_file_dir, file)
            df = pd.read_csv(file_path)
            df['record_arrival_date'] = file_arriving_date
            _append_dataframe(df, 'account_stage', conn)
            print(f"Loaded data from {file} into account_stage table.")

def load_data_to_all_stages(data_file_dir, conn):
    _ensure_stage_tables(conn)
    data_path = Path(data_file_dir)
    archive_dir = data_path.parent / 'archive'
    files_to_archive = list(data_path.glob('*.csv'))

    load_data_to_customer_stage(data_file_dir, 'customer', conn)
    load_data_to_transaction_stage(data_file_dir, 'transaction', conn)
    load_data_to_account_stage(data_file_dir, 'account', conn)

    archive_dir.mkdir(exist_ok=True)
    for file_path in files_to_archive:
        file_path.rename(archive_dir / file_path.name)
        print(f"Archived {file_path.name} in {archive_dir}.")
