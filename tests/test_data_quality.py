from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_required_raw_tables_exist(raw_dir: Path) -> None:
    expected = {
        "dim_customers.csv",
        "dim_products.csv",
        "fact_orders.csv",
        "fact_order_lines.csv",
        "fact_interactions_monthly.csv",
        "dim_campaigns.csv",
        "fact_campaign_responses.csv",
        "calendar.csv",
    }
    assert expected.issubset({path.name for path in raw_dir.glob("*.csv")})


def test_customer_primary_key(customers: pd.DataFrame) -> None:
    assert len(customers) == 6000
    assert customers["customer_id"].is_unique
    assert customers["customer_id"].notna().all()


def test_order_primary_key_and_foreign_key(
    customers: pd.DataFrame, orders: pd.DataFrame
) -> None:
    assert len(orders) > 40_000
    assert orders["order_id"].is_unique
    assert set(orders["customer_id"]).issubset(set(customers["customer_id"]))


def test_order_values_and_dates(orders: pd.DataFrame) -> None:
    dates = pd.to_datetime(orders["order_date"])
    assert dates.min() >= pd.Timestamp("2022-01-01")
    assert dates.max() <= pd.Timestamp("2025-12-31")
    assert orders["net_revenue"].ge(0).all()
    assert orders["gross_revenue"].ge(orders["net_revenue"]).all()


def test_pipeline_quality_gates(processed_dir: Path) -> None:
    quality = pd.read_csv(processed_dir / "data_quality_report.csv")
    assert len(quality) >= 10
    assert quality["status"].eq("PASS").all()

