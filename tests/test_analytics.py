from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from customer_intelligence.analytics import calculate_rfm
from customer_intelligence.features import build_customer_snapshot


def test_rfm_scores_are_valid(processed_dir: Path) -> None:
    rfm = pd.read_csv(processed_dir / "rfm_scores.csv")
    for column in ["recency_score", "frequency_score", "monetary_score"]:
        assert rfm[column].between(1, 5).all()
    assert rfm["rfm_segment"].nunique() >= 7


def test_cohort_retention_is_bounded(processed_dir: Path) -> None:
    cohort = pd.read_csv(processed_dir / "cohort_retention_long.csv")
    assert cohort["retention_rate"].between(0, 1).all()
    month_zero = cohort[cohort["cohort_index"] == 0]
    assert month_zero["retention_rate"].round(8).eq(1).all()


def test_customer_360_is_one_row_per_customer(customer_360: pd.DataFrame) -> None:
    assert len(customer_360) == 6000
    assert customer_360["customer_id"].is_unique
    assert customer_360["rfm_segment"].notna().all()
    assert customer_360["risk_band"].notna().all()
    assert customer_360["clv_band"].notna().all()


def test_campaign_budget_and_economics(processed_dir: Path) -> None:
    targets = pd.read_csv(processed_dir / "campaign_targets.csv")
    selected = targets[targets["selected_for_campaign"] == 1]
    assert selected["allocated_budget"].sum() <= 400_000
    assert selected["expected_incremental_margin"].ge(0).all()
    assert selected["marketing_consent"].eq(1).all()


def test_executive_kpis_are_populated(processed_dir: Path) -> None:
    kpis = pd.read_csv(processed_dir / "executive_kpis.csv")
    assert len(kpis) >= 15
    assert kpis["value"].notna().all()


def test_rfm_rejects_ambiguous_customer_and_financial_inputs() -> None:
    customers = pd.DataFrame({"customer_id": ["C1", "C1"], "acquisition_date": ["2025-01-01"] * 2})
    orders = pd.DataFrame(
        {
            "customer_id": ["C1"],
            "order_id": ["O1"],
            "order_date": ["2026-01-01"],
            "net_revenue": [100.0],
            "gross_margin": [30.0],
        }
    )
    with pytest.raises(ValueError, match="unique, non-null"):
        calculate_rfm(customers, orders, "2026-02-01")
    with pytest.raises(ValueError, match="finite numeric"):
        calculate_rfm(customers.iloc[:1], orders.assign(net_revenue=np.inf), "2026-02-01")


@pytest.mark.parametrize("horizon", [True, 0, -1, 3661, 90.5, "90"])
def test_snapshot_rejects_invalid_horizon_before_processing(horizon: object) -> None:
    with pytest.raises((TypeError, ValueError), match="horizon_days"):
        build_customer_snapshot(
            pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "2026-01-01", horizon
        )  # type: ignore[arg-type]
