--DELETE FROM transaction_stage;
--DELETE FROM account_stage;
--DELETE FROM customer_stage;

DELETE FROM transaction_stage;
DELETE FROM account_stage;
DELETE FROM customer_stage;

INSERT INTO customer_stage (
    cust_id,
    country_of_residence,
    country_of_birth,
    date_of_birth,
    record_arrival_date
)
SELECT
    CAST(sequence.cust_id AS INTEGER),
    CASE sequence.cust_id % 5
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'United States'
        WHEN 2 THEN 'United Kingdom'
        WHEN 3 THEN 'Canada'
        ELSE 'Australia'
    END,
    CASE (sequence.cust_id + 1) % 5
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'United States'
        WHEN 2 THEN 'United Kingdom'
        WHEN 3 THEN 'Canada'
        ELSE 'Australia'
    END,
    DATE '1980-01-01' + CAST(sequence.cust_id * 100 AS INTEGER),
    DATE '2026-08-01' + CAST(sequence.cust_id % 10 AS INTEGER)
FROM range(1, 101) AS sequence(cust_id);

INSERT INTO account_stage (
    account_id,
    account_number,
    customer_id,
    customer_type,
    account_status,
    record_arrival_date
)
SELECT
    500000 + sequence.customer_id,
    concat('ACCT-', lpad(CAST(sequence.customer_id AS VARCHAR), 6, '0')),
    CAST(sequence.customer_id AS INTEGER),
    CASE sequence.customer_id % 3
        WHEN 0 THEN 'business'
        WHEN 1 THEN 'individual'
        ELSE 'premium'
    END,
    CASE sequence.customer_id % 4
        WHEN 0 THEN 'closed'
        WHEN 1 THEN 'active'
        WHEN 2 THEN 'active'
        ELSE 'dormant'
    END,
    DATE '2026-08-01' + CAST(sequence.customer_id % 10 AS INTEGER)
FROM range(1, 101) AS sequence(customer_id);

INSERT INTO transaction_stage (
    transaction_id,
    amount,
    "type",
    originating_country,
    destination_country,
    account_id,
    record_arrival_date
)
SELECT
    100000 + sequence.transaction_number,
    CAST(100.00 + (sequence.transaction_number * 12.50) AS DECIMAL(18, 2)),
    CASE sequence.transaction_number % 4
        WHEN 0 THEN 'purchase'
        WHEN 1 THEN 'transfer'
        WHEN 2 THEN 'withdrawal'
        ELSE 'payment'
    END,
    CASE sequence.transaction_number % 5
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'United States'
        WHEN 2 THEN 'United Kingdom'
        WHEN 3 THEN 'Canada'
        ELSE 'Australia'
    END,
    CASE (sequence.transaction_number + 2) % 5
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'United States'
        WHEN 2 THEN 'United Kingdom'
        WHEN 3 THEN 'Canada'
        ELSE 'Australia'
    END,
    500000 + sequence.transaction_number,
    DATE '2026-08-01' + CAST(sequence.transaction_number % 10 AS INTEGER)
FROM range(1, 101) AS sequence(transaction_number);
