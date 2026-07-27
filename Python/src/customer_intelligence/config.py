from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ProjectConfig:
    seed: int = 20260727
    company_name: str = "NovaRetail Group"
    currency: str = "TRY"
    n_customers: int = 6000
    data_start: str = "2022-01-01"
    data_end: str = "2025-12-31"
    production_cutoff: str = "2025-12-31"
    churn_horizon_days: int = 90
    clv_horizon_days: int = 365
    campaign_budget: float = 400_000.0

    @property
    def raw_dir(self) -> Path:
        return PROJECT_ROOT / "Data" / "Raw"

    @property
    def processed_dir(self) -> Path:
        return PROJECT_ROOT / "Data" / "Processed"

    @property
    def model_dir(self) -> Path:
        return PROJECT_ROOT / "Models"

    @property
    def image_dir(self) -> Path:
        return PROJECT_ROOT / "Images"

    @property
    def report_dir(self) -> Path:
        return PROJECT_ROOT / "Reports"


CONFIG = ProjectConfig()


FEATURE_COLUMNS = [
    "recency_days",
    "frequency_12m",
    "monetary_12m",
    "gross_margin_12m",
    "avg_order_value_12m",
    "discount_rate_12m",
    "return_rate_12m",
    "category_diversity_12m",
    "online_order_share_12m",
    "sessions_90d",
    "email_open_rate_12m",
    "support_tickets_12m",
    "days_since_last_session",
    "tenure_days",
    "loyalty_tier_score",
    "consent_flag",
]

