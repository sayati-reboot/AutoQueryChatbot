# Geographic Risk Policy

## 1. Purpose
This policy establishes the enterprise framework for identifying and assessing geographic risk associated with customers, accounts, and financial transactions. The policy applies to customer onboarding, transaction monitoring, sanctions screening, and portfolio risk assessment. Geographic risk is assessed using country of birth, country of residence, transaction origin, transaction destination, and material risk indicators linked to sanctioned or high-risk jurisdictions.

## 2. Scope
This policy governs the review of geographic exposure across the following domains:
- customer identity and onboarding data
- account-level risk assessment
- transaction-level risk monitoring
- cross-border payment activity
- financial crime and sanction-related screening controls

This policy should be read alongside the institution’s broader financial crime, customer onboarding, and regulatory compliance framework.

## 3. Risk Jurisdictions
The institution classifies jurisdictions into the following categories for risk treatment purposes:

### 3.1 Sanctioned or Prohibited Jurisdictions
The following countries are treated as sanctioned or prohibited geographies for the purposes of this policy:
- Iran
- North Korea
- Russia
- Syria
- Cuba
- Belarus
- Myanmar
- Venezuela

### 3.2 High-Risk Jurisdictions
The following countries are treated as high-risk geographies requiring enhanced review and risk weighting:
- Afghanistan
- Pakistan
- Sudan
- Yemen
- Iraq
- Libya
- Somalia
- Ukraine, where sanctions overlays or elevated regional risk conditions are applicable

## 4. Geographic Risk Scoring Methodology
Geographic risk is measured using a points-based model. Scores are additive and should be applied to the relevant customer or transaction record for assessment and escalation.

### 4.1 Customer Country of Birth
- If country_of_birth is in a sanctioned or prohibited jurisdiction: +30 risk points
- If country_of_birth is in a high-risk jurisdiction: +15 risk points
- If country_of_birth is unknown or blank: +5 risk points

### 4.2 Customer Country of Residence
- If country_of_residence is in a sanctioned or prohibited jurisdiction: +25 risk points
- If country_of_residence is in a high-risk jurisdiction: +12 risk points
- If country_of_residence is unknown or blank: +3 risk points

### 4.3 Transaction Origin Country
- If originating_country is in a sanctioned or prohibited jurisdiction: +20 risk points
- If originating_country is in a high-risk jurisdiction: +10 risk points

### 4.4 Transaction Destination Country
- If destination_country is in a sanctioned or prohibited jurisdiction: +20 risk points
- If destination_country is in a high-risk jurisdiction: +10 risk points

### 4.5 Cross-Border Risk Overlay
- If the transaction origin and destination differ and either country is sanctioned or high-risk: +10 risk points
- If either the origin or destination country matches the customer’s country of residence or country of birth and that country is high-risk: +5 risk points

## 5. Industry and Business-Line Risk Considerations
Certain products, channels, and customer segments carry elevated geographic exposure and therefore require enhanced review.

### 5.1 Cross-Border Payment Transactions
- For payment, transfer, or wire-related activity, if either the origin or destination is in a sanctioned or high-risk geography, add +10 risk points
- If both origin and destination are in sanctioned or high-risk geographies, add +20 risk points

### 5.2 Customer Onboarding and Account Opening
- If country_of_birth or country_of_residence is high-risk, add +8 risk points
- If both fields are high-risk, add +15 risk points

### 5.3 Financial Crime and Fraud Monitoring
- Transactions involving sanctioned or high-risk geographies should be reviewed under enhanced due diligence procedures
- If country_of_residence and transaction destination are both high-risk, add +15 risk points

## 6. Risk Thresholds and Escalation
The institution applies the following risk thresholds to determine action levels:

- 0 to 9 points: Low geographic risk
- 10 to 19 points: Moderate geographic risk
- 20 to 29 points: Elevated geographic risk
- 30 points and above: High geographic risk, requiring escalation and review

### Escalation Requirements
- Any record with a sanctioned or prohibited geography match must be escalated for manual review
- Any record scoring 30 points or more must be subject to enhanced due diligence review
- Geographic risk output should be retained with the underlying record to support auditability and downstream decision-making

## 7. Illustrative Examples
### Example 1: Customer born in a sanctioned jurisdiction
- country_of_birth = Iran
- country_of_residence = United States
- Risk score impact: +30 points

### Example 2: Customer resident in a high-risk jurisdiction
- country_of_residence = Pakistan
- Risk score impact: +12 points

### Example 3: Transaction to a sanctioned jurisdiction
- originating_country = United States
- destination_country = Russia
- Risk score impact: +20 points

### Example 4: Combined customer and transaction geography risk
- country_of_residence = Syria
- destination_country = Syria
- Risk score impact: +25 points + 20 points + 5 points = +50 points

## 8. Governance and Review
This policy shall be reviewed periodically to ensure alignment with current sanctions frameworks, jurisdictional restrictions, and internal risk appetite. Country classifications may be amended where regulatory obligations, sanctions changes, or operational risk conditions require it.

## 9. Policy Statement
The organization shall incorporate geographic risk controls into customer due diligence, transaction monitoring, and operational decisioning processes. Geographic risk may result in enhanced review, escalation, or denial of service where the risk posture exceeds stated tolerance thresholds.
