# Privacy, Ethics & Responsible Use

## Privacy

The delivered dataset is synthetic and contains no real personally identifiable information. A real implementation should apply:

- purpose limitation;
- data minimization;
- retention limits;
- access control and audit logging;
- encryption in transit and at rest;
- consent and suppression enforcement;
- documented data-subject processes.

## Responsible Use

The platform is intended for customer-retention and marketing prioritization. It must not be used for:

- credit or lending;
- employment;
- insurance;
- housing;
- essential-service access;
- decisions that create legal or similarly significant effects without appropriate governance.

## Fairness

Region and age band are used for auditing, not direct prediction. Monitoring compares observed churn, predicted risk, ROC-AUC and true-positive rate across groups.

These diagnostics are not proof of legal compliance. Material gaps require investigation into sample size, behavior, data quality, policy and treatment design.

## Human Oversight

- Campaign owners approve targeting policy.
- Model owners approve releases and thresholds.
- Marketing consent remains a hard gate.
- SHAP explanations support review but do not establish causality.
- Customers should not receive sensitive or manipulative explanation language.

