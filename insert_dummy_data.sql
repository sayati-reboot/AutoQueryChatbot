INSERT INTO customer (custid, country, transaction_id, name, dateof_birth)
SELECT
    CAST(sequence.custid AS INTEGER),
    CASE sequence.custid % 5
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'United States'
        WHEN 2 THEN 'United Kingdom'
        WHEN 3 THEN 'Canada'
        ELSE 'Australia'
    END,
    100000 + sequence.custid,
    concat('Customer ', sequence.custid),
    DATE '1980-01-01' + CAST(sequence.custid * 100 AS INTEGER)
FROM range(1, 101) AS sequence(custid);

INSERT INTO transaction_details (
    transaction_id,
    customer_id,
    amount,
    "type",
    originating_country,
    target_country
)
SELECT
    100000 + sequence.customer_id,
    CAST(sequence.customer_id AS INTEGER),
    CAST(100.00 + (sequence.customer_id * 12.50) AS DECIMAL(18, 2)),
    CASE sequence.customer_id % 4
        WHEN 0 THEN 'purchase'
        WHEN 1 THEN 'transfer'
        WHEN 2 THEN 'withdrawal'
        ELSE 'payment'
    END,
    CASE sequence.customer_id % 5
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'United States'
        WHEN 2 THEN 'United Kingdom'
        WHEN 3 THEN 'Canada'
        ELSE 'Australia'
    END,
    CASE (sequence.customer_id + 2) % 5
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'United States'
        WHEN 2 THEN 'United Kingdom'
        WHEN 3 THEN 'Canada'
        ELSE 'Australia'
    END
FROM range(1, 101) AS sequence(customer_id);
