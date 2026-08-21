CREATE TABLE IF NOT EXISTS customer (
    custid INTEGER,
    country VARCHAR,
    transaction_id BIGINT,
    name VARCHAR,
    dateof_birth DATE
);

CREATE TABLE IF NOT EXISTS transaction_details (
    transaction_id BIGINT,
    customer_id INTEGER,
    amount DECIMAL(18, 2),
    type VARCHAR,
    originating_country VARCHAR,
    target_country VARCHAR
);
