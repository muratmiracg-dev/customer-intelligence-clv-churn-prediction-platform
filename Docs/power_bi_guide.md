# Power BI Guide

## Open the Project

1. Extract `PowerBI/Customer_Intelligence_PBIP.zip` if using the packaged copy.
2. Open `Customer_Intelligence_Analytics.pbip` in a current Power BI Desktop release.
3. Allow the semantic model and report definition to load.

The project uses embedded Power Query data, so a local CSV path should not need to be remapped.

## Report Pages

1. Executive Overview
2. Customer & Value Trends
3. Risk Portfolio
4. CLV & Revenue
5. Churn & Retention
6. RFM Segmentation
7. Campaign Targeting
8. Cohort Analysis
9. Model Performance & Governance
10. Four-Year Trends
11. Model Comparison
12. SHAP Explainability

## Semantic Model

The model includes calendar, customer, segment, cohort, campaign, monthly trend, model-performance, drift and SHAP tables. Calendar relationships use one-to-many, single-direction filtering.

## DAX

Reusable measures are provided in `PowerBI/Customer_Intelligence_Measures.dax`. If a name conflicts with an imported column, prefix the measure with `KPI` or store measures in a dedicated Measures table.

## Validation

`PowerBI/Customer_Intelligence_PBIP/pbip_validation.json` records:

- 12 report pages;
- 97 visuals;
- semantic-table count;
- relationship count;
- validation status and errors.

