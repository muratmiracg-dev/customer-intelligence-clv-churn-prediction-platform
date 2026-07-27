# Data Dictionary

This dictionary focuses on the primary source and analytical tables. Exact schemas can also be inspected in the CSV headers and `SQL/schema.sql`.

## `dim_customers`

| Field | Meaning |
|---|---|
| `customer_id` | Anonymous synthetic customer key |
| `acquisition_date` | Customer acquisition date |
| `region` | Broad geographic region |
| `acquisition_channel` | Channel credited with acquisition |
| `loyalty_tier` | Current loyalty-program level |
| `marketing_consent` | Whether marketing contact is permitted |
| `age_band` | Broad synthetic age category |

## `fact_orders`

| Field | Meaning |
|---|---|
| `order_id` | Unique order key |
| `customer_id` | Customer foreign key |
| `order_date` | Transaction date |
| `order_status` | Order lifecycle status |
| `channel` | Order channel |
| `gross_revenue` | Revenue before discount and returns |
| `discount_amount` | Applied discount |
| `returned_value` | Value of returned items |
| `net_revenue` | Revenue after discounts and returns |
| `gross_margin` | Net revenue less product cost |

## `fact_interactions_monthly`

| Field | Meaning |
|---|---|
| `customer_id` | Customer foreign key |
| `month` | Interaction month |
| `sessions` | Digital sessions |
| `email_sent` | Marketing emails sent |
| `email_opens` | Marketing email opens |
| `support_tickets` | Support contacts |

## `customer_snapshot_features`

| Field | Meaning |
|---|---|
| `snapshot_date` | Feature cutoff |
| `recency_days` | Days since last order |
| `frequency_12m` | Orders in trailing 12 months |
| `monetary_12m` | Net revenue in trailing 12 months |
| `gross_margin_12m` | Gross margin in trailing 12 months |
| `avg_order_value_12m` | Average trailing order value |
| `discount_rate_12m` | Discount divided by gross revenue |
| `return_rate_12m` | Returned-order share |
| `category_diversity_12m` | Distinct categories purchased |
| `online_order_share_12m` | Online-order share |
| `sessions_90d` | Sessions in trailing 90 days |
| `email_open_rate_12m` | Email opens divided by sent emails |
| `support_tickets_12m` | Support contacts in trailing 12 months |
| `days_since_last_session` | Days since latest digital session |
| `tenure_days` | Days since acquisition |
| `loyalty_tier_score` | Numeric loyalty representation |
| `consent_flag` | Numeric marketing-consent control |

## `customer_360`

The production customer decision table combines:

- customer attributes and consent;
- RFM segment and scores;
- recent revenue and margin;
- predicted CLV and value band;
- churn probability and risk band;
- SHAP reason codes;
- recommended campaign action;
- treatment cost, expected incremental margin and expected ROI.

