CREATE OR REPLACE VIEW vw_customer_value_risk AS
SELECT
    customer_id,
    rfm_segment,
    clv_band,
    risk_band,
    monetary_12m,
    gross_margin_12m,
    predicted_clv_12m,
    churn_probability,
    recommended_action,
    campaign_priority
FROM customer_360;

CREATE OR REPLACE VIEW vw_segment_portfolio AS
SELECT
    rfm_segment,
    COUNT(*) AS customers,
    SUM(monetary_12m) AS revenue_12m,
    SUM(predicted_clv_12m) AS predicted_clv_12m,
    AVG(churn_probability) AS average_churn_probability,
    SUM(expected_incremental_margin) AS expected_incremental_margin
FROM customer_360
GROUP BY rfm_segment;

