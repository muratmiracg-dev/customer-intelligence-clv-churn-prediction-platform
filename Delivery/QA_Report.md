# Quality Assurance Report

## Release

**Version:** 1.0.0  
**Date:** 2026-07-27  
**Status:** PASS

## Data & Pipeline

- Raw tables generated: 8
- Processed analytical tables generated: 23
- Customer records: 6,000
- Pipeline data-quality gates: 10/10 PASS
- Primary and foreign-key controls: PASS
- Churn probabilities within [0, 1]: PASS
- Cohort retention within [0, 1]: PASS

## Automated Testing

- Tests: 28 passed
- API statement and branch coverage: 100%
- Ruff linting: PASS
- SQL validation: PASS

## Model Validation

- Churn time-based holdout: PASS
- Churn probability calibration: PASS
- CLV time-based holdout: PASS
- Non-negative CLV control: PASS
- SHAP additivity MAE: approximately 2.46e-16
- Fairness audit generated: PASS
- Drift report generated: PASS

## Power BI

- Pages: 12
- Visuals: 97
- Semantic tables: 10
- Relationships: 1
- PBIP validation errors: 0

## Excel

- Sheets: 24
- Formula error scan: 0 matches
- Workbook QA checks: all PASS
- Pipeline quality table: all PASS
- Critical sheets rendered and visually reviewed

## Tableau

- Workbook XML parse: PASS
- Worksheets: 8
- Dashboards: 3
- Relative data connection documented

## Presentations

- English slides: 20
- Turkish slides: 20
- Every slide rendered
- English overflow test: PASS
- Turkish overflow test: PASS
- Montage visual review: PASS

## Executive PDF

- Pages: 12
- Page ratio: 16:9
- Vector text, charts, diagrams and tables
- Fonts embedded: PASS
- Every page rendered at 216 DPI
- Montage visual review: PASS

## Release Decision

The project is suitable for portfolio presentation and GitHub publication after owner approval.

