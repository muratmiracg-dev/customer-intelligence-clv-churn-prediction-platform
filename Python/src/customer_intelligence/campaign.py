from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CONFIG

CAMPAIGN_COSTS = {
    "VIP Experience": 95.0,
    "Retain & Reward": 72.0,
    "Win-Back": 61.0,
    "Cross-Sell": 49.0,
    "Onboarding": 34.0,
    "Nurture": 28.0,
    "Suppress": 0.0,
}

BASE_RESPONSE = {
    "VIP Experience": 0.26,
    "Retain & Reward": 0.23,
    "Win-Back": 0.14,
    "Cross-Sell": 0.18,
    "Onboarding": 0.21,
    "Nurture": 0.11,
    "Suppress": 0.0,
}


def _assign_action(row: pd.Series) -> str:
    if not bool(row["marketing_consent"]):
        return "Suppress"
    if row["clv_percentile"] >= 0.80 and row["churn_probability"] >= 0.55:
        return "Win-Back"
    if row["clv_percentile"] >= 0.80 and row["churn_probability"] < 0.55:
        return "VIP Experience"
    if row["rfm_segment"] in {"Champions", "Loyal Customers"}:
        return "Retain & Reward"
    if row["rfm_segment"] in {"New Customers", "Potential Loyalists", "Promising"}:
        return "Onboarding"
    if row["category_diversity_12m"] <= 2 and row["frequency_12m"] >= 2:
        return "Cross-Sell"
    if row["churn_probability"] >= 0.68:
        return "Win-Back"
    if row["frequency_12m"] == 0 and row["recency_days"] > 365:
        return "Suppress"
    return "Nurture"


def recommend_campaigns(
    production_snapshot: pd.DataFrame,
    rfm: pd.DataFrame,
    clv_scores: pd.DataFrame,
    churn_scores: pd.DataFrame,
    budget: float = CONFIG.campaign_budget,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = (
        production_snapshot[
            [
                "customer_id",
                "marketing_consent",
                "frequency_12m",
                "monetary_12m",
                "gross_margin_12m",
                "avg_order_value_12m",
                "category_diversity_12m",
                "recency_days",
                "sessions_90d",
            ]
        ]
        .merge(rfm[["customer_id", "rfm_segment"]], on="customer_id", how="left")
        .merge(clv_scores, on="customer_id", how="left")
        .merge(churn_scores, on="customer_id", how="left")
    )
    frame["recommended_action"] = frame.apply(_assign_action, axis=1)
    frame["contact_cost"] = frame["recommended_action"].map(CAMPAIGN_COSTS).fillna(0)
    engagement_norm = (
        frame["sessions_90d"].rank(pct=True).fillna(0).clip(0, 1)
    )
    response = frame["recommended_action"].map(BASE_RESPONSE).fillna(0)
    response += 0.08 * engagement_norm
    response += 0.06 * frame["clv_percentile"].fillna(0)
    response -= 0.05 * frame["churn_probability"].fillna(0)
    winback = frame["recommended_action"].eq("Win-Back")
    response.loc[winback] += 0.08 * frame.loc[winback, "churn_probability"]
    frame["expected_response_probability"] = response.clip(0, 0.55)
    margin_rate = (
        frame["gross_margin_12m"]
        .div(frame["monetary_12m"].replace(0, np.nan))
        .fillna(0.38)
        .clip(0.18, 0.62)
    )
    expected_order_value = frame["avg_order_value_12m"].clip(lower=450, upper=6500)
    expected_gross_margin = (
        frame["expected_response_probability"]
        * expected_order_value
        * margin_rate
        * (1.18 + 0.22 * frame["clv_percentile"].fillna(0))
    )
    frame["expected_incremental_margin"] = (
        expected_gross_margin - frame["contact_cost"]
    )
    frame["expected_roi"] = np.where(
        frame["contact_cost"] > 0,
        frame["expected_incremental_margin"] / frame["contact_cost"],
        0,
    )
    frame["priority_score"] = (
        0.36 * frame["clv_percentile"].fillna(0)
        + 0.24 * frame["risk_percentile"].fillna(0)
        + 0.25 * frame["expected_roi"].rank(pct=True).fillna(0)
        + 0.15 * engagement_norm
    )
    frame["campaign_priority"] = pd.cut(
        frame["priority_score"],
        bins=[-np.inf, 0.40, 0.60, 0.78, np.inf],
        labels=["Low", "Medium", "High", "Critical"],
    ).astype(str)
    eligible = frame[
        (frame["contact_cost"] > 0)
        & (frame["expected_incremental_margin"] > 0)
        & (frame["marketing_consent"] == 1)
    ].sort_values(["priority_score", "expected_roi"], ascending=False)
    eligible = eligible.copy()
    eligible["cumulative_budget"] = eligible["contact_cost"].cumsum()
    selected_ids = set(
        eligible.loc[eligible["cumulative_budget"] <= budget, "customer_id"]
    )
    frame["selected_for_campaign"] = frame["customer_id"].isin(selected_ids).astype(int)
    frame["allocated_budget"] = np.where(
        frame["selected_for_campaign"].eq(1), frame["contact_cost"], 0
    )
    frame["expected_incremental_margin"] = np.where(
        frame["selected_for_campaign"].eq(1),
        frame["expected_incremental_margin"],
        0,
    )
    frame["expected_roi"] = np.where(
        frame["selected_for_campaign"].eq(1), frame["expected_roi"], 0
    )
    summary = frame.groupby("recommended_action", as_index=False).agg(
        eligible_customers=("customer_id", "nunique"),
        selected_customers=("selected_for_campaign", "sum"),
        allocated_budget=("allocated_budget", "sum"),
        expected_incremental_margin=("expected_incremental_margin", "sum"),
        average_expected_roi=("expected_roi", "mean"),
        average_churn_probability=("churn_probability", "mean"),
        predicted_clv=("predicted_clv_12m", "sum"),
    )
    summary["expected_total_value"] = (
        summary["allocated_budget"] + summary["expected_incremental_margin"]
    )
    return frame.sort_values("priority_score", ascending=False), summary.sort_values(
        "expected_incremental_margin", ascending=False
    )

