from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from customer_intelligence.modeling import population_stability_index

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_churn_model_quality(processed_dir: Path) -> None:
    metrics = pd.read_csv(processed_dir / "churn_model_comparison.csv").iloc[0]
    assert metrics["roc_auc"] >= 0.80
    assert metrics["pr_auc"] >= 0.80
    assert metrics["lift_at_10pct"] >= 1.40
    assert metrics["brier_score"] <= 0.20


def test_clv_model_quality(processed_dir: Path) -> None:
    metrics = pd.read_csv(processed_dir / "clv_model_comparison.csv").iloc[0]
    assert metrics["r2"] >= 0.40
    assert metrics["spearman_correlation"] >= 0.65


def test_shap_explanations_are_additive(processed_dir: Path) -> None:
    metadata = json.loads(
        (PROJECT_ROOT / "Models" / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["explainability"]["method"].startswith("shap_")
    assert metadata["explainability"]["additivity_mean_absolute_error"] < 1e-6
    importance = pd.read_csv(processed_dir / "shap_global_importance.csv")
    assert abs(importance["importance_share"].sum() - 1) < 1e-6


def test_drift_report_has_statuses(processed_dir: Path) -> None:
    drift = pd.read_csv(processed_dir / "drift_monitoring.csv")
    assert set(drift["status"]).issubset({"Stable", "Watch", "Investigate"})
    assert drift["psi"].ge(0).all()


@pytest.mark.parametrize(
    ("reference", "current", "bins"),
    [
        (pd.Series(dtype=float), pd.Series([1.0]), 10),
        (pd.Series([1.0, np.nan]), pd.Series([1.0, 2.0]), 10),
        (pd.Series([1.0, 2.0]), pd.Series([1.0, np.inf]), 10),
        (pd.Series([1.0, 2.0]), pd.Series([1.0, 2.0]), 1),
        (pd.Series([1.0, 2.0]), pd.Series([1.0, 2.0]), True),
    ],
)
def test_psi_rejects_invalid_monitoring_inputs(
    reference: pd.Series, current: pd.Series, bins: int
) -> None:
    with pytest.raises(ValueError):
        population_stability_index(reference, current, bins)


def test_fairness_audit_has_required_groups(processed_dir: Path) -> None:
    fairness = pd.read_csv(processed_dir / "fairness_audit.csv")
    assert {"region", "age_band"}.issubset(set(fairness["audit_attribute"]))
    assert fairness["true_positive_rate"].between(0, 1).all()
