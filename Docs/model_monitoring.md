# Model Monitoring Plan

## Cadence

| Control | Cadence | Owner |
|---|---|---|
| Schema and data quality | Every pipeline run | Data Engineering |
| Score distribution | Monthly | Analytics |
| Churn performance and calibration | Monthly after labels mature | Model Risk |
| CLV performance | Quarterly / annually as target matures | Analytics |
| Feature PSI | Monthly | Model Risk |
| Fairness diagnostics | Quarterly | Governance |
| Campaign lift and margin | Every campaign | CRM / Marketing |
| Model-card review | At least annually | Model Owner |

## Alert Thresholds

- PSI below 0.10: stable;
- PSI 0.10–0.25: watch and investigate;
- PSI above 0.25: material drift and remediation review;

PSI is fail-closed: reference and current samples must be non-empty and contain
only finite numeric values, and the requested bin count must be an integer of at
least two. Invalid monitoring inputs stop the report instead of being silently
converted to zero and understating drift.
- material ROC-AUC, PR-AUC or lift decline: investigate and consider retraining;
- calibration deterioration: recalibrate before changing risk thresholds;
- fairness-gap deterioration: pause affected use case and complete root-cause review;
- failed primary or foreign-key controls: stop downstream publication.

## Retraining Triggers

- material feature or target drift;
- sustained performance decline;
- major pricing, product, channel or policy change;
- new data source or feature definition;
- campaign-response behavior changes;
- monitoring or audit finding.

## Rollback

Retain the previous approved model, feature schema and threshold. If a new release violates a control, restore the previous version and replay the affected scoring run.
