# Model Card — Predictive Customer Lifetime Value

## Summary

| Item | Value |
|---|---|
| Champion | Random Forest Regressor |
| Target | Gross-margin contribution over the next 365 days |
| Production snapshot | 2025-12-31 |
| Horizon | 12 months |
| Intended use | Customer-value ranking and campaign economics |

## Training and Validation

Training snapshots:

- 2023-03-31
- 2023-09-30
- 2024-03-31
- 2024-06-30

Time-based holdout snapshot: 2024-12-31, with realized 2025 gross margin as the target.

## Holdout Results

| Metric | Result |
|---|---:|
| MAE | TRY 1,258.38 |
| RMSE | TRY 2,151.56 |
| R² | 0.5645 |
| Spearman correlation | 0.7915 |

Spearman correlation is important because the primary business use is value ranking and resource prioritization.

## Output Controls

- Predictions are clipped at zero.
- CLV is labelled as a 12-month contribution forecast.
- Portfolio totals are reconciled to the customer-level output.
- Results are combined with consent, risk and treatment economics before action.

## Risks and Limitations

- The target is future gross margin, not revenue and not infinite-horizon lifetime value.
- Economic conditions, assortment and pricing changes may shift the target distribution.
- High predicted CLV does not guarantee treatment responsiveness.
- Individual predictions can have large errors even when portfolio ranking is useful.
- Real deployment requires backtesting by acquisition channel and customer segment.

## Monitoring

- MAE and RMSE;
- R² and Spearman correlation;
- prediction distribution by segment;
- actual-to-predicted calibration by CLV band;
- feature and target drift;
- treatment ROI by CLV band.

