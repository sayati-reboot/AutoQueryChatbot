CREATE TABLE IF NOT EXISTS customer_stage (
    cust_id INTEGER,
    country_of_residence VARCHAR,
    country_of_birth VARCHAR,
    date_of_birth DATE,
    record_arrival_date DATE
);

CREATE TABLE IF NOT EXISTS transaction_stage (
    transaction_id BIGINT,
    amount DECIMAL(18, 2),
    type VARCHAR,
    originating_country VARCHAR,
    destination_country VARCHAR,
    account_id BIGINT,
    transaction_date DATE,
    record_arrival_date DATE
);

CREATE TABLE IF NOT EXISTS account_stage (
    account_id BIGINT,
    account_number VARCHAR,
    customer_id INTEGER,
    customer_type VARCHAR,
    account_status VARCHAR,
    record_arrival_date DATE
);
