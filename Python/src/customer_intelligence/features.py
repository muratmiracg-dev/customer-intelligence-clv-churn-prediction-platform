from __future__ import annotations

import numpy as np
import pandas as pd

from .config import FEATURE_COLUMNS
from .utils import safe_divide


def build_customer_snapshot(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    interactions: pd.DataFrame,
    cutoff: str | pd.Timestamp,
    horizon_days: int = 90,
    include_churn_target: bool = False,
    include_clv_target: bool = False,
) -> pd.DataFrame:
    """Create leakage-safe customer features as known at a point in time."""
    cutoff_ts = pd.Timestamp(cutoff).normalize()
    customers = customers.copy()
    customers["acquisition_date"] = pd.to_datetime(customers["acquisition_date"])
    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    interactions = interactions.copy()
    interactions["month"] = pd.to_datetime(interactions["month"])

    eligible = customers[customers["acquisition_date"] <= cutoff_ts].copy()
    snapshot = eligible[
        [
            "customer_id",
            "acquisition_date",
            "region",
            "age_band",
            "loyalty_tier",
            "preferred_channel",
            "marketing_consent",
        ]
    ].copy()
    snapshot["snapshot_date"] = cutoff_ts
    snapshot["tenure_days"] = (
        cutoff_ts - snapshot["acquisition_date"]
    ).dt.days.clip(lower=0)

    history = orders[orders["order_date"] <= cutoff_ts].copy()
    window_start = cutoff_ts - pd.Timedelta(days=364)
    history_12m = history[history["order_date"] >= window_start].copy()

    lifetime_agg = history.groupby("customer_id", as_index=False).agg(
        last_order_date=("order_date", "max"),
        lifetime_orders=("order_id", "nunique"),
        lifetime_revenue=("net_revenue", "sum"),
        lifetime_margin=("gross_margin", "sum"),
    )
    snapshot = snapshot.merge(lifetime_agg, on="customer_id", how="left")
    snapshot["recency_days"] = (
        cutoff_ts - pd.to_datetime(snapshot["last_order_date"])
    ).dt.days
    snapshot["recency_days"] = snapshot["recency_days"].fillna(
        snapshot["tenure_days"].clip(lower=1) + 365
    )

    aggregate_12m = history_12m.groupby("customer_id", as_index=False).agg(
        frequency_12m=("order_id", "nunique"),
        monetary_12m=("net_revenue", "sum"),
        gross_margin_12m=("gross_margin", "sum"),
        gross_revenue_12m=("gross_revenue", "sum"),
        discount_amount_12m=("discount_amount", "sum"),
        returned_orders_12m=("returned_flag", "sum"),
        category_diversity_12m=("primary_category", "nunique"),
    )
    online_agg = (
        history_12m.assign(
            online_flag=history_12m["channel"].isin(["Mobile App", "Web"]).astype(int)
        )
        .groupby("customer_id", as_index=False)
        .agg(online_orders_12m=("online_flag", "sum"))
    )
    snapshot = snapshot.merge(aggregate_12m, on="customer_id", how="left").merge(
        online_agg, on="customer_id", how="left"
    )
    numeric_fill = [
        "lifetime_orders",
        "lifetime_revenue",
        "lifetime_margin",
        "frequency_12m",
        "monetary_12m",
        "gross_margin_12m",
        "gross_revenue_12m",
        "discount_amount_12m",
        "returned_orders_12m",
        "category_diversity_12m",
        "online_orders_12m",
    ]
    snapshot[numeric_fill] = snapshot[numeric_fill].fillna(0)
    snapshot["avg_order_value_12m"] = safe_divide(
        snapshot["monetary_12m"], snapshot["frequency_12m"]
    )
    snapshot["discount_rate_12m"] = safe_divide(
        snapshot["discount_amount_12m"], snapshot["gross_revenue_12m"]
    )
    snapshot["return_rate_12m"] = safe_divide(
        snapshot["returned_orders_12m"], snapshot["frequency_12m"]
    )
    snapshot["online_order_share_12m"] = safe_divide(
        snapshot["online_orders_12m"], snapshot["frequency_12m"]
    )

    interactions_hist = interactions[interactions["month"] <= cutoff_ts].copy()
    interactions_12m = interactions_hist[
        interactions_hist["month"] >= window_start
    ].copy()
    interactions_90d = interactions_hist[
        interactions_hist["month"] >= cutoff_ts - pd.Timedelta(days=89)
    ].copy()
    interaction_agg = interactions_12m.groupby("customer_id", as_index=False).agg(
        email_sent_12m=("email_sent", "sum"),
        email_opens_12m=("email_opens", "sum"),
        support_tickets_12m=("support_tickets", "sum"),
    )
    session_agg = interactions_90d.groupby("customer_id", as_index=False).agg(
        sessions_90d=("sessions", "sum")
    )
    session_rows = interactions_hist[interactions_hist["sessions"] > 0]
    last_session = session_rows.groupby("customer_id", as_index=False).agg(
        last_session_month=("month", "max")
    )
    snapshot = (
        snapshot.merge(interaction_agg, on="customer_id", how="left")
        .merge(session_agg, on="customer_id", how="left")
        .merge(last_session, on="customer_id", how="left")
    )
    for column in [
        "email_sent_12m",
        "email_opens_12m",
        "support_tickets_12m",
        "sessions_90d",
    ]:
        snapshot[column] = snapshot[column].fillna(0)
    snapshot["email_open_rate_12m"] = safe_divide(
        snapshot["email_opens_12m"], snapshot["email_sent_12m"]
    )
    snapshot["days_since_last_session"] = (
        cutoff_ts - pd.to_datetime(snapshot["last_session_month"])
    ).dt.days
    snapshot["days_since_last_session"] = snapshot["days_since_last_session"].fillna(
        snapshot["tenure_days"].clip(lower=1) + 90
    )
    snapshot["loyalty_tier_score"] = snapshot["loyalty_tier"].map(
        {"Bronze": 1, "Silver": 2, "Gold": 3, "Platinum": 4}
    )
    snapshot["consent_flag"] = snapshot["marketing_consent"].astype(int)

    if include_churn_target:
        future_end = cutoff_ts + pd.Timedelta(days=horizon_days)
        future_orders = orders[
            (orders["order_date"] > cutoff_ts) & (orders["order_date"] <= future_end)
        ]
        purchased = set(future_orders["customer_id"].unique())
        snapshot["churn_90d"] = (~snapshot["customer_id"].isin(purchased)).astype(int)

    if include_clv_target:
        future_end = cutoff_ts + pd.Timedelta(days=horizon_days)
        future_orders = orders[
            (orders["order_date"] > cutoff_ts) & (orders["order_date"] <= future_end)
        ]
        future_margin = future_orders.groupby("customer_id", as_index=False).agg(
            future_gross_margin=("gross_margin", "sum"),
            future_revenue=("net_revenue", "sum"),
            future_orders=("order_id", "nunique"),
        )
        snapshot = snapshot.merge(future_margin, on="customer_id", how="left")
        snapshot[["future_gross_margin", "future_revenue", "future_orders"]] = snapshot[
            ["future_gross_margin", "future_revenue", "future_orders"]
        ].fillna(0)

    for column in FEATURE_COLUMNS:
        snapshot[column] = pd.to_numeric(snapshot[column], errors="coerce").fillna(0)
    return snapshot


def build_customer_360(
    production_snapshot: pd.DataFrame,
    rfm: pd.DataFrame,
    clv_scores: pd.DataFrame,
    churn_scores: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> pd.DataFrame:
    base_columns = [
        "customer_id",
        "snapshot_date",
        "region",
        "age_band",
        "loyalty_tier",
        "preferred_channel",
        "marketing_consent",
        "lifetime_orders",
        "lifetime_revenue",
        "lifetime_margin",
        *FEATURE_COLUMNS,
    ]
    customer_360 = production_snapshot[base_columns].copy()
    customer_360 = (
        customer_360.merge(
            rfm[
                [
                    "customer_id",
                    "rfm_segment",
                    "rfm_score",
                    "recency_score",
                    "frequency_score",
                    "monetary_score",
                ]
            ],
            on="customer_id",
            how="left",
        )
        .merge(
            clv_scores[
                [
                    "customer_id",
                    "predicted_clv_12m",
                    "clv_band",
                    "clv_percentile",
                ]
            ],
            on="customer_id",
            how="left",
        )
        .merge(
            churn_scores[
                [
                    "customer_id",
                    "churn_probability",
                    "risk_band",
                    "risk_percentile",
                ]
            ],
            on="customer_id",
            how="left",
        )
        .merge(
            campaigns[
                [
                    "customer_id",
                    "recommended_action",
                    "campaign_priority",
                    "expected_incremental_margin",
                    "expected_roi",
                    "selected_for_campaign",
                ]
            ],
            on="customer_id",
            how="left",
        )
    )
    return customer_360


def validate_feature_matrix(frame: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        issues.append(f"Missing feature columns: {missing}")
    if frame["customer_id"].duplicated().any():
        issues.append("Duplicate customer_id values found in snapshot.")
    numeric = frame[[column for column in FEATURE_COLUMNS if column in frame.columns]]
    if numeric.isna().any().any():
        issues.append("Feature matrix contains null values.")
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        issues.append("Feature matrix contains infinite values.")
    return issues
