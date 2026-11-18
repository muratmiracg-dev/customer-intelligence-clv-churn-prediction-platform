# Changelog

## Unreleased

- Made the synthetic data reproducible. Each order's `primary_category` was
  `max(set(categories), key=count)`, so ties were broken by string-hash order, which Python
  randomises per process: every pipeline run produced different raw orders and therefore
  different features, models, predictions and KPIs (three runs, three different
  `fact_orders.csv` digests). Ties now go to the first category bought. Regenerated `Data/`,
  `Models/` and `SQL/`; headline figures move slightly (high/critical-risk customers 2,682 ->
  2,683, revenue at risk TRY 5.97M -> 5.93M, churn ROC-AUC 0.8666 -> 0.8668, operating
  threshold 0.33 -> 0.32, CLV MAE TRY 1,258 -> 1,259, campaign budget TRY 236.4K -> 236.5K). README, model cards and delivery notes
  updated; the Excel, deck, PDF, Power BI and Tableau files are static exports of the earlier run.
- Seeded SHAP's permutation explainer. Without a seed the sampled permutations changed every
  run, so `shap_global_importance.csv` moved by up to ~1.5% (sessions_90d mean |SHAP| 0.2758 to
  0.2797 across runs) and local explanations by more.
- CI now rebuilds the pipeline and compares every committed CSV/JSON value with the rebuild
  (`scripts/compare_outputs.py`, relative tolerance 1e-9).
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
