# SHAP Explainability

## Purpose

SHAP values translate model output into feature-level contributions. The platform provides:

- global mean absolute SHAP importance;
- average signed contribution;
- customer-level local explanations;
- leading positive and negative reason codes;
- additivity validation metadata.

## Delivered Configuration

| Item | Value |
|---|---:|
| Method | Permutation explainer |
| Explanation sample | 60 |
| Background sample | 24 |
| Features | 16 |
| Additivity MAE | approximately 2.46e-16 |

## Interpretation

A positive local SHAP value increases predicted churn probability relative to the background expectation; a negative value reduces it.

Global importance reflects the selected explanation sample. Because the sample emphasizes high-priority production records, it should be described as a priority-cohort explanation rather than an unbiased population estimate.

## Guardrails

- SHAP is not causal evidence.
- Protected or sensitive categories are not direct predictive features.
- Explanations should not expose sensitive information in customer communications.
- Local reasons support human review and action design; they do not override consent or campaign eligibility.

