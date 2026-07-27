# KPI Dictionary

| KPI | Definition | Grain / Window | Format |
|---|---|---|---|
| Customers | Distinct customer records | Portfolio | Count |
| Active Customers 12M | Customers with at least one order in the trailing 365 days | Production snapshot | Count |
| Net Revenue 12M | Gross order value less discounts and returned value in trailing 365 days | Customer / portfolio | TRY |
| Gross Margin 12M | Net revenue less product cost in trailing 365 days | Customer / portfolio | TRY |
| Predicted CLV 12M | Model-estimated gross-margin contribution over the following 365 days | Customer | TRY |
| Churn Probability | Calibrated probability of no purchase in the following 90 days | Customer | Percent |
| High / Critical Risk | Customers above configured risk-tier cutoffs | Portfolio | Count |
| Revenue at Risk | Trailing 12-month revenue associated with high / critical-risk customers | Portfolio | TRY |
| M3 Cohort Retention | Share of an acquisition cohort active in month three | Cohort | Percent |
| ROC-AUC | Probability that a randomly selected churned customer ranks above a non-churned customer | Holdout | Decimal |
| PR-AUC | Area under precision-recall curve | Holdout | Decimal |
| Brier Score | Mean squared error of predicted churn probability | Holdout | Decimal; lower is better |
| Lift at Top 10% | Churn concentration in highest-risk decile divided by portfolio churn rate | Holdout | Multiple |
| CLV MAE | Mean absolute difference between predicted and realized future gross margin | Holdout | TRY |
| CLV R² | Share of holdout target variance explained by the CLV model | Holdout | Decimal |
| Expected Incremental Margin | Expected treatment response value less treatment cost | Customer / campaign | TRY |
| Expected ROI | Expected incremental margin divided by allocated treatment cost | Campaign | Multiple |

## Time Conventions

- Trailing values use information available by the snapshot date.
- Future targets begin after the snapshot date.
- Monthly cohort index M0 is the first-purchase month.
- CLV in this project is a 12-month predictive contribution measure, not an infinite-horizon lifetime value.

