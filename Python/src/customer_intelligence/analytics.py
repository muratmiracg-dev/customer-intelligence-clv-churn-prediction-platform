from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import safe_divide


def _quantile_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    percentile = series.rank(method="average", pct=True)
    score = np.ceil(percentile * 5).clip(1, 5).astype(int)
    return score if higher_is_better else (6 - score)


def _rfm_segment(row: pd.Series) -> str:
    r, f, m = int(row["recency_score"]), int(row["frequency_score"]), int(
        row["monetary_score"]
    )
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 4:
        return "Loyal Customers"
    if r >= 4 and f in {2, 3}:
        return "Potential Loyalists"
    if r == 5 and f == 1:
        return "New Customers"
    if r >= 3 and f == 2:
        return "Promising"
    if r in {2, 3} and f >= 3:
        return "Need Attention"
    if r <= 2 and f >= 4:
        return "Can't Lose Them"
    if r <= 2 and f in {2, 3}:
        return "At Risk"
    if r <= 2 and f == 1:
        return "Hibernating"
    return "Lost"


def calculate_rfm(
    customers: pd.DataFrame, orders: pd.DataFrame, analysis_date: str | pd.Timestamp
) -> pd.DataFrame:
    analysis_ts = pd.Timestamp(analysis_date)
    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    window_start = analysis_ts - pd.Timedelta(days=364)
    order_window = orders[
        (orders["order_date"] >= window_start)
        & (orders["order_date"] <= analysis_ts)
    ].copy()
    aggregate = order_window.groupby("customer_id", as_index=False).agg(
        last_order_date=("order_date", "max"),
        frequency=("order_id", "nunique"),
        monetary=("net_revenue", "sum"),
        gross_margin=("gross_margin", "sum"),
    )
    eligible = customers[pd.to_datetime(customers["acquisition_date"]) <= analysis_ts][
        ["customer_id", "acquisition_date"]
    ].copy()
    rfm = eligible.merge(aggregate, on="customer_id", how="left")
    rfm["recency"] = (analysis_ts - pd.to_datetime(rfm["last_order_date"])).dt.days
    tenure = (analysis_ts - pd.to_datetime(rfm["acquisition_date"])).dt.days.clip(lower=0)
    rfm["recency"] = rfm["recency"].fillna(tenure + 365).astype(int)
    rfm[["frequency", "monetary", "gross_margin"]] = rfm[
        ["frequency", "monetary", "gross_margin"]
    ].fillna(0)
    rfm["recency_score"] = _quantile_score(rfm["recency"], higher_is_better=False)
    rfm["frequency_score"] = _quantile_score(rfm["frequency"], higher_is_better=True)
    rfm["monetary_score"] = _quantile_score(rfm["monetary"], higher_is_better=True)
    zero_frequency = rfm["frequency"].eq(0)
    rfm.loc[zero_frequency, ["frequency_score", "monetary_score"]] = 1
    rfm["rfm_score"] = (
        rfm["recency_score"].astype(str)
        + rfm["frequency_score"].astype(str)
        + rfm["monetary_score"].astype(str)
    )
    rfm["rfm_segment"] = rfm.apply(_rfm_segment, axis=1)
    return rfm.drop(columns=["acquisition_date"])


def calculate_cohort_retention(
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = orders[["customer_id", "order_date"]].copy()
    frame["order_month"] = pd.to_datetime(frame["order_date"]).dt.to_period("M")
    first_purchase = frame.groupby("customer_id", as_index=False).agg(
        cohort_month=("order_month", "min")
    )
    frame = frame.merge(first_purchase, on="customer_id", how="left")
    frame["cohort_index"] = (
        (frame["order_month"].dt.year - frame["cohort_month"].dt.year) * 12
        + frame["order_month"].dt.month
        - frame["cohort_month"].dt.month
    )
    active = frame.groupby(
        ["cohort_month", "cohort_index"], as_index=False
    ).agg(active_customers=("customer_id", "nunique"))
    cohort_sizes = first_purchase.groupby("cohort_month", as_index=False).agg(
        cohort_size=("customer_id", "nunique")
    )
    long = active.merge(cohort_sizes, on="cohort_month", how="left")
    long["retention_rate"] = safe_divide(
        long["active_customers"], long["cohort_size"]
    )
    long["cohort_month"] = long["cohort_month"].astype(str)
    matrix = (
        long.pivot(
            index="cohort_month", columns="cohort_index", values="retention_rate"
        )
        .sort_index()
        .reset_index()
    )
    matrix.columns = [
        "cohort_month" if column == "cohort_month" else f"M{int(column)}"
        for column in matrix.columns
    ]
    return long.sort_values(["cohort_month", "cohort_index"]), matrix


def calculate_monthly_metrics(
    customers: pd.DataFrame, orders: pd.DataFrame
) -> pd.DataFrame:
    orders = orders.copy()
    orders["month"] = pd.to_datetime(orders["order_date"]).dt.to_period("M").dt.to_timestamp()
    customer_month = orders.groupby(["month", "customer_id"], as_index=False).agg(
        customer_orders=("order_id", "nunique"),
        customer_revenue=("net_revenue", "sum"),
    )
    summary = orders.groupby("month", as_index=False).agg(
        orders=("order_id", "nunique"),
        active_customers=("customer_id", "nunique"),
        net_revenue=("net_revenue", "sum"),
        gross_margin=("gross_margin", "sum"),
        returned_orders=("returned_flag", "sum"),
    )
    repeat = customer_month[customer_month["customer_orders"] >= 2].groupby(
        "month", as_index=False
    ).agg(repeat_customers=("customer_id", "nunique"))
    customers = customers.copy()
    customers["month"] = (
        pd.to_datetime(customers["acquisition_date"]).dt.to_period("M").dt.to_timestamp()
    )
    new_customers = customers.groupby("month", as_index=False).agg(
        new_customers=("customer_id", "nunique")
    )
    result = (
        summary.merge(repeat, on="month", how="left")
        .merge(new_customers, on="month", how="left")
        .fillna({"repeat_customers": 0, "new_customers": 0})
    )
    result["average_order_value"] = safe_divide(
        result["net_revenue"], result["orders"]
    )
    result["gross_margin_pct"] = safe_divide(
        result["gross_margin"], result["net_revenue"]
    )
    result["repeat_customer_rate"] = safe_divide(
        result["repeat_customers"], result["active_customers"]
    )
    result["return_rate"] = safe_divide(result["returned_orders"], result["orders"])
    return result.sort_values("month")


def summarize_segments(customer_360: pd.DataFrame) -> pd.DataFrame:
    summary = customer_360.groupby("rfm_segment", as_index=False).agg(
        customers=("customer_id", "nunique"),
        revenue_12m=("monetary_12m", "sum"),
        gross_margin_12m=("gross_margin_12m", "sum"),
        predicted_clv_12m=("predicted_clv_12m", "sum"),
        average_churn_probability=("churn_probability", "mean"),
        average_order_value=("avg_order_value_12m", "mean"),
        campaign_selected=("selected_for_campaign", "sum"),
        expected_incremental_margin=("expected_incremental_margin", "sum"),
    )
    summary["customer_share"] = summary["customers"] / summary["customers"].sum()
    summary["revenue_share"] = summary["revenue_12m"] / summary["revenue_12m"].sum()
    return summary.sort_values("predicted_clv_12m", ascending=False)

