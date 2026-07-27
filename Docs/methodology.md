# Analytical Methodology

## 1. Data Generation

The project creates deterministic synthetic data for a fictional retailer from 1 January 2022 through 31 December 2025. The generator preserves realistic relationships between acquisition channel, loyalty, ordering behavior, seasonality, engagement, returns, discounts and campaign response.

The random seed is fixed at `20260727`, allowing the complete dataset and all downstream outputs to be reproduced.

## 2. Data Quality

Before modeling, the pipeline checks:

- primary-key uniqueness;
- foreign-key validity;
- non-negative order revenue;
- valid order-date ranges;
- valid interaction-customer relationships;
- valid snapshot features.

All 10 implemented gates pass in the delivered release.

## 3. Customer Snapshots

A snapshot contains information available on or before a cutoff date. Features include:

- recency, frequency and 12-month monetary value;
- 12-month gross margin, average order value, discount and return rate;
- category diversity and online-order share;
- sessions, email-open rate and support tickets;
- days since last session and customer tenure;
- loyalty-tier score and marketing-consent flag.

Historical targets are calculated strictly after the snapshot:

- churn: no order during the next 90 days;
- CLV: gross-margin contribution during the next 365 days.

## 4. Churn Modeling

Training snapshots: 31 March, 30 June and 30 September 2024.

Time-based holdout: 31 December 2024, evaluated on the following 90 days.

Production scoring: 31 December 2025.

Candidate classifiers include Random Forest, Histogram Gradient Boosting and Logistic Regression. The Random Forest champion is probability-calibrated. The operating threshold is selected on training predictions by F1 and then applied unchanged to the holdout.

## 5. CLV Modeling

Training snapshots: 31 March 2023, 30 September 2023, 31 March 2024 and 30 June 2024.

Time-based holdout: 31 December 2024, evaluated against realized 2025 gross margin.

Candidate regressors include Random Forest, Histogram Gradient Boosting and Ridge Regression. Negative predictions are clipped to zero.

## 6. Explainability

Permutation-based SHAP values are calculated for a controlled high-priority production sample. Global outputs summarize mean absolute contribution; local outputs expose customer-specific reason codes. Additivity is validated.

## 7. Campaign Decisioning

Eligibility and treatment logic combine:

1. marketing consent;
2. risk probability and tier;
3. predicted CLV and recent gross margin;
4. RFM segment;
5. expected response probability;
6. treatment cost;
7. expected incremental margin;
8. available campaign budget.

## 8. Monitoring

The project outputs:

- model performance metrics;
- calibration and lift tables;
- fairness diagnostics by region and age band;
- PSI feature-drift results;
- pipeline data-quality results;
- model and data metadata.

