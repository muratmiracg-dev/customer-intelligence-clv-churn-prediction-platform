# Model Card — 90-Day Churn Prediction

## Summary

| Item | Value |
|---|---|
| Champion | Calibrated Random Forest |
| Target | No purchase during the next 90 days |
| Production snapshot | 2025-12-31 |
| Operating threshold | 0.33 |
| Feature count | 16 |
| Intended use | Retention prioritization and campaign planning |

## Training and Validation

Training snapshots:

- 2024-03-31
- 2024-06-30
- 2024-09-30

Time-based holdout snapshot: 2024-12-31.

The model is evaluated on outcomes after the holdout cutoff. Features contain only information available on or before each snapshot.

## Holdout Results

| Metric | Result |
|---|---:|
| ROC-AUC | 0.8666 |
| PR-AUC | 0.9083 |
| Brier score | 0.1455 |
| F1 | 0.7917 |
| Precision | 0.8085 |
| Recall | 0.7755 |
| Lift at top 10% | 1.7738x |
| Recall in top 20% | 0.3545 |

## Features

The model uses behavioral and engagement features such as recency, 12-month frequency and value, margin, discount and return rates, category diversity, online-order share, recent sessions, email-open rate, support contacts, digital inactivity, tenure, loyalty and consent.

Direct region and age-band values are excluded from the predictive feature list and are retained for fairness auditing.

## Explainability

Permutation SHAP is used for:

- global importance;
- local contribution values;
- customer-level reason codes;
- additivity validation.

The delivered SHAP sample focuses on priority production records and should not be interpreted as a population causal study.

## Risks and Limitations

- Churn is defined through purchase inactivity, not explicit cancellation.
- Synthetic data cannot establish real-world intervention effects.
- Risk can reflect seasonality, product cycles or delayed purchase—not only dissatisfaction.
- Scores must not be used for credit, employment, insurance or essential-service access.
- Marketing consent and business eligibility must remain independent controls.

## Monitoring

- monthly ROC-AUC, PR-AUC, Brier, precision, recall and lift;
- probability and risk-tier distribution;
- feature PSI;
- region and age-band fairness diagnostics;
- campaign response and incremental-margin outcomes;
- data-quality gates and schema validity.

