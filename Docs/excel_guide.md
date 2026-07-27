# Excel Decision Model Guide

## File

`Excel/Customer_Intelligence_CLV_Churn_Campaign_Planner.xlsx`

## Workbook Design

The workbook contains 24 sheets:

- Cover;
- Executive Dashboard;
- Assumptions;
- RFM Segmentation;
- Cohort Retention;
- CLV Analysis;
- Churn Analysis;
- Campaign Planner;
- Model Performance;
- SHAP Drivers;
- Fairness and Drift;
- Customer 360;
- Monthly Trends;
- QA Checks;
- Data Dictionary;
- Sources;
- eight supporting data sheets.

## Input Convention

- Yellow cells: user-editable assumptions.
- Green values: linked or formula-driven outputs.
- Dark navy rows: section or table headers.
- Red conditional formatting: failed control or adverse result.

## Campaign Scenario

Edit the campaign budget and response multipliers on the Assumptions sheet. The Campaign Planner recalculates:

- scenario budget;
- scenario margin;
- scenario ROI;
- Invest / Test / Hold decision.

## Quality Assurance

The QA Checks sheet contains formula-backed reconciliation controls and the pipeline’s data-quality results. The delivered version has:

- no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` or `#N/A` formula errors;
- all workbook QA checks passing;
- all pipeline quality gates passing.

