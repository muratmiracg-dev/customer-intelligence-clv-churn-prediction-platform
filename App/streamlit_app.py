from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "Data" / "Processed"

st.set_page_config(
    page_title="Customer Intelligence Platform",
    page_icon="◎",
    layout="wide",
)
st.title("Customer Intelligence, CLV & Churn Prediction")
st.caption("NovaRetail Group | Production snapshot: 31 December 2025")

customer_360 = pd.read_csv(DATA_DIR / "customer_360.csv")
segment_summary = pd.read_csv(DATA_DIR / "segment_summary.csv")
monthly = pd.read_csv(DATA_DIR / "monthly_customer_metrics.csv")
shap_importance = pd.read_csv(DATA_DIR / "shap_global_importance.csv")

segments = st.sidebar.multiselect(
    "RFM Segment",
    sorted(customer_360["rfm_segment"].dropna().unique()),
    default=sorted(customer_360["rfm_segment"].dropna().unique()),
)
risk = st.sidebar.multiselect(
    "Risk Band",
    ["Low", "Medium", "High", "Critical"],
    default=["Low", "Medium", "High", "Critical"],
)
filtered = customer_360[
    customer_360["rfm_segment"].isin(segments)
    & customer_360["risk_band"].isin(risk)
]

cols = st.columns(4)
cols[0].metric("Customers", f"{filtered['customer_id'].nunique():,}")
cols[1].metric("Revenue 12M", f"₺{filtered['monetary_12m'].sum()/1_000_000:.1f}M")
cols[2].metric("Predicted CLV", f"₺{filtered['predicted_clv_12m'].sum()/1_000_000:.1f}M")
cols[3].metric("Average Churn Risk", f"{filtered['churn_probability'].mean():.1%}")

left, right = st.columns(2)
with left:
    fig = px.treemap(
        segment_summary,
        path=["rfm_segment"],
        values="predicted_clv_12m",
        color="average_churn_probability",
        color_continuous_scale=["#36D7B7", "#FFB547", "#FF5B72"],
        title="Segment Value and Risk Portfolio",
    )
    st.plotly_chart(fig, use_container_width=True)
with right:
    fig = px.scatter(
        filtered,
        x="predicted_clv_12m",
        y="churn_probability",
        color="risk_band",
        size="monetary_12m",
        hover_data=["customer_id", "rfm_segment", "recommended_action"],
        color_discrete_map={
            "Low": "#36D7B7",
            "Medium": "#4CA6FF",
            "High": "#FFB547",
            "Critical": "#FF5B72",
        },
        title="Customer Value-Risk Matrix",
    )
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    monthly["month"] = pd.to_datetime(monthly["month"])
    fig = px.line(
        monthly,
        x="month",
        y="net_revenue",
        title="Monthly Revenue Trend",
        markers=True,
    )
    fig.update_traces(line_color="#4CA6FF")
    st.plotly_chart(fig, use_container_width=True)
with right:
    fig = px.bar(
        shap_importance.head(10).sort_values("mean_abs_shap"),
        x="mean_abs_shap",
        y="feature",
        orientation="h",
        title="Top SHAP Churn Drivers",
        color_discrete_sequence=["#8B5CF6"],
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Prioritized Campaign Targets")
columns = [
    "customer_id",
    "rfm_segment",
    "clv_band",
    "risk_band",
    "predicted_clv_12m",
    "churn_probability",
    "recommended_action",
    "campaign_priority",
    "expected_incremental_margin",
]
st.dataframe(
    filtered[filtered["selected_for_campaign"] == 1][columns]
    .sort_values("expected_incremental_margin", ascending=False)
    .head(250),
    use_container_width=True,
)

