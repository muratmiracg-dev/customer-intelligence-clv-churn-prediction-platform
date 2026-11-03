# Changelog

## Unreleased

- Pinned `scikit-learn==1.9.0`, the version that pickled `Models/churn_champion.joblib` and
  `Models/clv_champion.joblib`. With the previous `>=1.5` bound, CI and Docker installed 1.9.1, and
  every API start-up emitted scikit-learn's `InconsistentVersionWarning` ("might lead to breaking
  code or invalid results").
- Added `tests/test_model_artifacts.py`, which fails if the installed scikit-learn differs from the
  version recorded in the committed models and checks that both bundles still predict.

## 1.0.0 — 2026-07-27

- Added deterministic four-year synthetic customer, product, order, interaction and campaign data.
- Added RFM segmentation and M0–M12 cohort retention analysis.
- Added calibrated 90-day churn classification and 12-month predictive CLV.
- Added SHAP global and local explanations.
- Added fairness, feature-drift and data-quality monitoring.
- Added next-best-action targeting and campaign budget optimization.
- Added SQLite schema, views and reusable analytical queries.
- Added FastAPI scoring service and Streamlit application.
- Added 12-page Power BI PBIP, Tableau workbook and 24-sheet Excel decision model.
- Added 20-slide English and Turkish presentations.
- Added 12-page vector HD executive PDF.
- Added automated testing, CI workflow and governance documentation.
