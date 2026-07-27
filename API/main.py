from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHURN_BUNDLE = joblib.load(PROJECT_ROOT / "Models" / "churn_champion.joblib")
CLV_BUNDLE = joblib.load(PROJECT_ROOT / "Models" / "clv_champion.joblib")
MODEL_METADATA = json.loads(
    (PROJECT_ROOT / "Models" / "model_metadata.json").read_text(encoding="utf-8")
)

app = FastAPI(
    title="Customer Intelligence Scoring API",
    version="1.0.0",
    description="Scores 90-day churn risk and predicted 12-month customer lifetime value.",
)


class CustomerFeatures(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    recency_days: float = Field(ge=0)
    frequency_12m: float = Field(ge=0)
    monetary_12m: float = Field(ge=0)
    gross_margin_12m: float
    avg_order_value_12m: float = Field(ge=0)
    discount_rate_12m: float = Field(ge=0, le=1)
    return_rate_12m: float = Field(ge=0, le=1)
    category_diversity_12m: float = Field(ge=0)
    online_order_share_12m: float = Field(ge=0, le=1)
    sessions_90d: float = Field(ge=0)
    email_open_rate_12m: float = Field(ge=0, le=1)
    support_tickets_12m: float = Field(ge=0)
    days_since_last_session: float = Field(ge=0)
    tenure_days: float = Field(ge=0)
    loyalty_tier_score: float = Field(ge=1, le=4)
    consent_flag: float = Field(ge=0, le=1)


def _risk_band(probability: float) -> str:
    if probability < 0.35:
        return "Low"
    if probability < 0.55:
        return "Medium"
    if probability < 0.72:
        return "High"
    return "Critical"


def _clv_band(clv: float) -> str:
    if clv < 500:
        return "Low"
    if clv < 1500:
        return "Developing"
    if clv < 3500:
        return "High"
    return "Strategic"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/model-info")
def model_info() -> dict[str, object]:
    return {
        "production_snapshot": MODEL_METADATA["production_snapshot"],
        "churn_champion": MODEL_METADATA["churn_champion"],
        "clv_champion": MODEL_METADATA["clv_champion"],
        "feature_count": len(MODEL_METADATA["feature_columns"]),
        "explainability_method": MODEL_METADATA["explainability"]["method"],
    }


@app.post("/score")
def score(payload: CustomerFeatures) -> dict[str, object]:
    features = CHURN_BUNDLE["features"]
    frame = pd.DataFrame([payload.model_dump()])[features]
    churn_probability = float(
        CHURN_BUNDLE["model"].predict_proba(frame)[:, 1][0]
    )
    predicted_clv = max(0.0, float(CLV_BUNDLE["model"].predict(frame)[0]))
    return {
        "churn_probability": round(churn_probability, 6),
        "churn_risk_band": _risk_band(churn_probability),
        "predicted_clv_12m": round(predicted_clv, 2),
        "clv_band": _clv_band(predicted_clv),
        "decision_threshold": round(float(CHURN_BUNDLE["threshold"]), 4),
        "model_snapshot": CHURN_BUNDLE["snapshot_date"],
    }

