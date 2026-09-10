from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from customer_intelligence.campaign import recommend_campaigns


@pytest.fixture
def campaign_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    production_snapshot = pd.DataFrame(
        {
            "customer_id": ["C001", "C002"],
            "marketing_consent": [1, 1],
            "frequency_12m": [5, 2],
            "monetary_12m": [5_000.0, 1_500.0],
            "gross_margin_12m": [2_000.0, 600.0],
            "avg_order_value_12m": [1_000.0, 750.0],
            "category_diversity_12m": [4, 2],
            "recency_days": [30, 90],
            "sessions_90d": [10, 4],
        }
    )
    rfm = pd.DataFrame(
        {"customer_id": ["C001", "C002"], "rfm_segment": ["Champions", "Promising"]}
    )
    clv_scores = pd.DataFrame(
        {
            "customer_id": ["C001", "C002"],
            "clv_percentile": [0.9, 0.6],
            "predicted_clv_12m": [8_000.0, 3_000.0],
        }
    )
    churn_scores = pd.DataFrame(
        {
            "customer_id": ["C001", "C002"],
            "churn_probability": [0.2, 0.4],
            "risk_percentile": [0.3, 0.7],
        }
    )
    return production_snapshot, rfm, clv_scores, churn_scores


@pytest.mark.parametrize("budget", [-1.0, np.nan, np.inf, "400000", True])
def test_recommend_campaigns_rejects_invalid_budget(
    campaign_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
    budget: object,
) -> None:
    with pytest.raises(ValueError, match="Campaign budget"):
        recommend_campaigns(*campaign_inputs, budget=budget)


def test_recommend_campaigns_rejects_duplicate_customers(
    campaign_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    production_snapshot, rfm, clv_scores, churn_scores = campaign_inputs
    duplicate_clv_scores = pd.concat([clv_scores, clv_scores.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="clv_scores must contain one row per customer_id"):
        recommend_campaigns(
            production_snapshot,
            rfm,
            duplicate_clv_scores,
            churn_scores,
        )


@pytest.mark.parametrize(
    ("frame_index", "column", "value"),
    [(2, "clv_percentile", 1.01), (3, "churn_probability", -0.01), (3, "risk_percentile", np.nan)],
)
def test_recommend_campaigns_rejects_invalid_model_scores(
    campaign_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
    frame_index: int,
    column: str,
    value: float,
) -> None:
    inputs = [frame.copy() for frame in campaign_inputs]
    inputs[frame_index].loc[0, column] = value

    with pytest.raises(ValueError, match=column):
        recommend_campaigns(*inputs)


def test_recommend_campaigns_keeps_allocation_within_budget(
    campaign_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    targets, _ = recommend_campaigns(*campaign_inputs, budget=95.0)

    assert targets["allocated_budget"].sum() <= 95.0
    assert targets["customer_id"].is_unique
