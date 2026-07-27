from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def raw_dir() -> Path:
    return PROJECT_ROOT / "Data" / "Raw"


@pytest.fixture(scope="session")
def processed_dir() -> Path:
    return PROJECT_ROOT / "Data" / "Processed"


@pytest.fixture(scope="session")
def customers(raw_dir: Path) -> pd.DataFrame:
    return pd.read_csv(raw_dir / "dim_customers.csv")


@pytest.fixture(scope="session")
def orders(raw_dir: Path) -> pd.DataFrame:
    return pd.read_csv(raw_dir / "fact_orders.csv")


@pytest.fixture(scope="session")
def customer_360(processed_dir: Path) -> pd.DataFrame:
    return pd.read_csv(processed_dir / "customer_360.csv")

