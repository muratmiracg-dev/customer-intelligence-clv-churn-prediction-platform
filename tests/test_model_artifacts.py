"""Committed model bundles must load cleanly with the pinned scikit-learn."""

from __future__ import annotations

import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import InconsistentVersionWarning

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUNDLES = {
    "churn_champion.joblib": {"model", "features", "threshold", "snapshot_date"},
    "clv_champion.joblib": {"model", "features", "snapshot_date"},
}


@pytest.mark.parametrize(("filename", "keys"), BUNDLES.items())
def test_bundle_loads_without_version_mismatch(filename: str, keys: set[str]) -> None:
    with warnings.catch_warnings():
        # scikit-learn warns that estimators unpickled in another version
        # "might lead to breaking code or invalid results"; treat that as a failure.
        warnings.simplefilter("error", InconsistentVersionWarning)
        bundle = joblib.load(PROJECT_ROOT / "Models" / filename)
    assert keys <= set(bundle)


@pytest.mark.parametrize("filename", BUNDLES)
def test_bundle_predicts_finite_values(filename: str, processed_dir: Path) -> None:
    bundle = joblib.load(PROJECT_ROOT / "Models" / filename)
    features = list(bundle["features"])
    sample = pd.read_csv(processed_dir / "customer_360.csv", usecols=features).head(50)
    model = bundle["model"]
    if hasattr(model, "predict_proba"):
        predictions = model.predict_proba(sample[features])[:, 1]
        assert ((predictions >= 0) & (predictions <= 1)).all()
    else:
        predictions = model.predict(sample[features])
    assert np.isfinite(predictions).all()
