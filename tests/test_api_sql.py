from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from API.main import _clv_band, _risk_band, app
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_api_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_model_info() -> None:
    response = TestClient(app).get("/model-info")
    assert response.status_code == 200
    assert response.json()["feature_count"] == 16
    assert response.json()["explainability_method"].startswith("shap_")


def test_api_scoring_contract() -> None:
    payload = {
        "recency_days": 94,
        "frequency_12m": 4,
        "monetary_12m": 12450,
        "gross_margin_12m": 3480,
        "avg_order_value_12m": 3112.5,
        "discount_rate_12m": 0.16,
        "return_rate_12m": 0.0,
        "category_diversity_12m": 3,
        "online_order_share_12m": 0.75,
        "sessions_90d": 8,
        "email_open_rate_12m": 0.42,
        "support_tickets_12m": 1,
        "days_since_last_session": 18,
        "tenure_days": 720,
        "loyalty_tier_score": 3,
        "consent_flag": 1,
    }
    response = TestClient(app).post("/score", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert 0 <= result["churn_probability"] <= 1
    assert result["predicted_clv_12m"] >= 0
    assert result["churn_risk_band"] in {"Low", "Medium", "High", "Critical"}


def test_api_rejects_invalid_features() -> None:
    response = TestClient(app).post(
        "/score",
        json={
            "recency_days": -1,
            "frequency_12m": 1,
            "monetary_12m": 500,
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("probability", "expected"),
    [(0.20, "Low"), (0.40, "Medium"), (0.60, "High"), (0.90, "Critical")],
)
def test_risk_band_boundaries(probability: float, expected: str) -> None:
    assert _risk_band(probability) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(100, "Low"), (900, "Developing"), (2500, "High"), (5000, "Strategic")],
)
def test_clv_band_boundaries(value: float, expected: str) -> None:
    assert _clv_band(value) == expected


def test_sqlite_views() -> None:
    database = PROJECT_ROOT / "SQL" / "customer_intelligence.db"
    with sqlite3.connect(database) as connection:
        customer_count = connection.execute(
            "SELECT COUNT(*) FROM customer_360"
        ).fetchone()[0]
        view_count = connection.execute(
            "SELECT COUNT(*) FROM vw_campaign_portfolio"
        ).fetchone()[0]
    assert customer_count == 6000
    assert view_count > 0
