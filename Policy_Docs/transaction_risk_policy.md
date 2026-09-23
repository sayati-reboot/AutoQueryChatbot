# Transaction Risk Policy

## 1. Purpose
This policy establishes the methodological framework for identifying and assessing transaction risk across customer activity, payment flows, and account-level behaviour. It is designed to support transaction monitoring, suspicious activity detection, and enhanced review where transaction patterns indicate elevated financial crime or regulatory risk.

## 2. Scope
This policy applies to all card, account, payment, and transfer activity processed through the institution’s financial systems. It covers:
- cross-border payments and transfers
- aggregate transaction volumes
- unusual transaction patterns
- customer behaviour versus expected activity
- transactions involving sanctioned, high-risk, or unusual geographies

## 3. Risk Categories
Transaction risk is assessed across the following categories:
- geographic risk
- volume and frequency risk
- velocity risk
- pattern or behavioural anomaly risk
- destination or counterpart risk

## 4. Geographic Transaction Risk
Transactions involving geography that is high-risk, sanctioned, or unusually inconsistent with the customer profile shall receive additional review.

### 4.1 Cross-Border Transactions
- If the transaction originates in one country and settles in another country, and either geography is sanctioned or high-risk: +20 risk points
- If both origin and destination are in sanctioned or high-risk jurisdictions: +35 risk points
- If the transaction is cross-border and a customer has no prior activity in that geography: +10 risk points

### 4.2 Country-of-Residence Mismatch
- If the transaction destination country differs materially from the customer’s country of residence and the destination is high-risk: +15 risk points
- If the transaction destination country is sanctioned and differs from the customer’s country of residence: +25 risk points

### 4.3 Unusual Transaction Geography
- If the transaction occurs in a geography inconsistent with the customer’s normal activity pattern: +10 risk points
- If the transaction involves a geography not previously used by the customer during the preceding 90-day period: +8 risk points

## 5. Aggregate Transaction Risk
Aggregate risk focuses on cumulative value, frequency, and concentration across accounts, customers, or counterparties.

### 5.1 Aggregate Value Thresholds
- If a customer conducts aggregate transactions above the institution’s internal threshold within a 24-hour period: +10 risk points
- If aggregate transaction value exceeds the customer’s rolling 30-day average by 200% or more: +15 risk points
- If aggregate value is concentrated in a high-risk geography or counterparty set: +10 risk points

### 5.2 Aggregate Frequency Thresholds
- If the number of transactions exceeds the customer’s typical pattern by more than 3 standard deviations in a 7-day period: +10 risk points
- If repeated activity occurs in the same risky geography across multiple transactions in a short period: +15 risk points

### 5.3 Aggregation Across Related Accounts
- If related customer or account activity is routed through multiple accounts to a high-risk geography: +20 risk points
- If the same counterpart or destination is used across multiple accounts in a short time window: +15 risk points

## 6. High-Volume Transaction Risk
High-volume activity is evaluated for both volume and behavioural deviation.

### 6.1 High-Volume Thresholds
- If a single transaction exceeds the customer’s normal pattern by a material margin: +15 risk points
- If a customer’s transaction amount exceeds internal risk thresholds for the product type: +20 risk points
- If the transaction volume is substantially higher than the historical rolling median for the customer: +10 risk points

### 6.2 High-Volume Geographic Exposure
- If high-volume activity occurs in a sanctioned or high-risk country: +25 risk points
- If high-volume activity is routed to multiple risky geographies within one day: +20 risk points

## 7. Risk Thresholds and Outcomes
The institution shall use the following thresholds to determine the action to be taken:

- 0 to 9 points: Low transaction risk
- 10 to 19 points: Moderate transaction risk
- 20 to 29 points: Elevated transaction risk
- 30 points and above: High transaction risk; escalation required

### Escalation and Review
- Any transaction exceeding 30 points requires escalation to the Financial Crime or Risk Operations function
- Transactions involving sanctioned jurisdictions require immediate review and escalation according to internal controls
- A pattern of repeated high-risk transactions across the same geography shall be treated as a heightened risk event

## 8. Examples of Elevated Transaction Risk
### Example 1: Cross-border transfer to a sanctioned country
- originating_country = United States
- destination_country = Russia
- transaction amount = high relative to customer pattern
- Risk score impact: +20 geographical points + additional high-volume or behavioural review points

### Example 2: Customer with no prior activity in a risky geography
- customer normally transacts within domestic market only
- activity suddenly appears in Pakistan and the amount is unusually high
- Risk score impact: +10 for unusual geography + +15 for unusual volume + additional review triggers

### Example 3: Aggregated activity in risky geography
- a customer performs multiple small transfers into a sanctioned jurisdiction across several days
- aggregate activity is material and concentrated in one risky geography
- Risk score impact: +15 or more depending on value concentration and repeated exposure

## 9. Governance and Oversight
The Transaction Risk Policy shall be reviewed periodically to account for changes in sanctions lists, jurisdictional developments, operational risk conditions, and emerging crime typologies. Departments responsible for transaction monitoring, fraud prevention, and compliance shall review the policy at least annually and update thresholds where necessary.

## 10. Policy Statement
The institution shall treat suspicious or unusually concentrated transaction activity in sanctioned or high-risk geographies as a priority monitoring concern. Transactions that materially deviate from expected customer behaviour or demonstrate elevated cross-border or aggregate risk shall be escalated for investigation and possible intervention.
