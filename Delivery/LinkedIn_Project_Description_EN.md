Project Name: Customer Intelligence, CLV & Churn Prediction Platform

Tools Used: Python, SQL, Power BI, DAX, Power Query, Excel, Tableau, Scikit-learn, SHAP, FastAPI, Streamlit, SQLite, Plotly, Pytest, Ruff, GitHub Actions, Docker, PBIP

Description:

- Developed an end-to-end customer intelligence platform that transforms four years of synthetic retail data into customer value, retention-risk and next-best-action decisions. Built a relational portfolio of 6,000 customers, 50,639 orders, 103,044 order lines, 130,671 monthly interactions and 12,000 campaign responses.

- Engineered reusable snapshots for RFM segmentation, M0–M12 cohort retention, 90-day churn and 12-month predictive CLV. Used time-based validation to prevent leakage and compared multiple classification and regression models.

- Selected a calibrated Random Forest churn champion with 0.867 ROC-AUC, 0.908 PR-AUC and 1.77x top-decile lift. Built a Random Forest CLV champion with TRY 1,258 MAE, 0.564 R² and 0.792 Spearman correlation.

- Added SHAP explanations, probability calibration, PSI drift monitoring, region/age-band fairness diagnostics, model cards and automated data-quality gates.

- Designed a next-best-action engine combining churn risk, CLV, RFM, consent, expected response, treatment cost and budget constraints. Prioritized 3,501 customers with TRY 236K budget and TRY 547K expected incremental margin.

- Delivered a 12-page Power BI PBIP, 24-sheet formula-driven Excel planner, Tableau workbook, SQLite database, FastAPI service, Streamlit app, 20-slide English/Turkish decks and a 12-page vector HD report.

- Implemented 28 automated tests, 100% API coverage, 10/10 passing data-quality controls and GitHub Actions CI.
