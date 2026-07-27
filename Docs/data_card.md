# Data Card

## Dataset

**Name:** NovaRetail Synthetic Customer Intelligence Dataset  
**Period:** 2022-01-01 to 2025-12-31  
**Production snapshot:** 2025-12-31  
**Currency:** TRY  
**License:** MIT project license  
**PII status:** No real personal information

## Purpose

The dataset supports portfolio demonstration of:

- customer segmentation;
- cohort retention;
- predictive CLV;
- churn classification;
- explainability;
- campaign targeting and economic prioritization;
- business-intelligence delivery.

## Source Tables

| Table | Rows | Grain |
|---|---:|---|
| `dim_customers` | 6,000 | One row per synthetic customer |
| `dim_products` | 48 | One row per product |
| `fact_orders` | 50,639 | One row per order |
| `fact_order_lines` | 103,044 | One row per order line |
| `fact_interactions_monthly` | 130,671 | Customer-month digital interaction |
| `dim_campaigns` | 8 | One row per campaign definition |
| `fact_campaign_responses` | 12,000 | Customer-campaign exposure |
| `calendar` | 1,461 | One row per day |

## Generation Principles

- deterministic random seed;
- plausible seasonality and customer heterogeneity;
- relational keys and referential integrity;
- behavioral relationships sufficient for meaningful analytical modeling;
- no reproduction of a real individual or company dataset.

## Appropriate Use

- education and portfolio demonstration;
- analytical prototyping;
- BI design;
- model validation and governance examples;
- API and data-engineering demonstrations.

## Inappropriate Use

- direct operational marketing;
- real-person profiling;
- credit, employment, insurance or access decisions;
- claims of real commercial uplift;
- legal or regulatory compliance certification.

## Known Limitations

- synthetic relationships may be cleaner than real production systems;
- missing-data and identity-resolution complexity is simplified;
- treatment effects are simulated, not established through a randomized trial;
- churn is purchase inactivity, which may not transfer to subscription contexts;
- demographic fields are broad analytical categories, not verified identities.

