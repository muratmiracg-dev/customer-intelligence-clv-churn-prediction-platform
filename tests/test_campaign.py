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
    rfm = pd.DataFrame({"customer_id": ["C001", "C002"], "rfm_segment": ["Champions", "Promising"]})
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


@pytest.mark.parametrize("frame_index", [1, 2, 3])
def test_recommend_campaigns_rejects_misaligned_customer_populations(
    campaign_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
    frame_index: int,
) -> None:
    inputs = [frame.copy() for frame in campaign_inputs]
    inputs[frame_index] = inputs[frame_index].iloc[[0]].copy()

    with pytest.raises(ValueError, match="exactly match production_snapshot"):
        recommend_campaigns(*inputs)


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


def test_campaign_allocation_is_stable_when_equal_priority_rows_are_reordered(
    campaign_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    customer_ids = ["C001", "C003", "C004", "C005"]
    tied_inputs = []
    for frame in campaign_inputs:
        rows = pd.concat([frame.iloc[[0]].copy() for _ in customer_ids], ignore_index=True)
        rows["customer_id"] = customer_ids
        tied_inputs.append(rows)

    first, _ = recommend_campaigns(*tied_inputs, budget=95.0)
    reordered = [frame.iloc[::-1].reset_index(drop=True) for frame in tied_inputs]
    second, _ = recommend_campaigns(*reordered, budget=95.0)

    selected_first = sorted(first.loc[first["selected_for_campaign"].eq(1), "customer_id"])
    selected_second = sorted(second.loc[second["selected_for_campaign"].eq(1), "customer_id"])
    assert selected_first == ["C001"]
    assert selected_second == selected_first


def test_recommend_campaigns_keeps_allocation_within_budget(
    campaign_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    targets, _ = recommend_campaigns(*campaign_inputs, budget=95.0)

    assert targets["allocated_budget"].sum() <= 95.0
    assert targets["customer_id"].is_unique
