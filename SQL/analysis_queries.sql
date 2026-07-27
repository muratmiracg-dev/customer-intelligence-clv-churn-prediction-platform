-- 1. Highest-value customers requiring retention action
SELECT
    customer_id,
    rfm_segment,
    predicted_clv_12m,
    churn_probability,
    recommended_action,
    expected_incremental_margin
FROM customer_360
WHERE clv_band = 'Strategic'
  AND risk_band IN ('High', 'Critical')
ORDER BY predicted_clv_12m DESC
LIMIT 100;

-- 2. Segment economics
SELECT
    rfm_segment,
    COUNT(*) AS customers,
    ROUND(SUM(monetary_12m), 2) AS revenue_12m,
    ROUND(SUM(gross_margin_12m), 2) AS margin_12m,
    ROUND(AVG(churn_probability), 4) AS avg_churn_probability,
    ROUND(SUM(predicted_clv_12m), 2) AS predicted_clv_12m
FROM customer_360
GROUP BY rfm_segment
ORDER BY predicted_clv_12m DESC;

-- 3. Campaign portfolio economics
SELECT
    recommended_action,
    campaign_priority,
    SUM(selected_for_campaign) AS targeted_customers,
    ROUND(SUM(allocated_budget), 2) AS allocated_budget,
    ROUND(SUM(expected_incremental_margin), 2) AS expected_incremental_margin,
    ROUND(
        SUM(expected_incremental_margin) / NULLIF(SUM(allocated_budget), 0),
        3
    ) AS portfolio_roi
FROM campaign_targets
WHERE selected_for_campaign = 1
GROUP BY recommended_action, campaign_priority
ORDER BY expected_incremental_margin DESC;

-- 4. Cohort retention curve
SELECT
    cohort_month,
    cohort_index,
    cohort_size,
    active_customers,
    ROUND(retention_rate, 4) AS retention_rate
FROM cohort_retention_long
WHERE cohort_index IN (0, 1, 3, 6, 12)
ORDER BY cohort_month, cohort_index;

