from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import FEATURE_COLUMNS


def _permutation_shap_fallback(
    model: Any,
    x_eval: pd.DataFrame,
    background: pd.DataFrame,
    permutations: int = 48,
    seed: int = 20260727,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Deterministic Shapley approximation for environments without shap."""
    rng = np.random.default_rng(seed)
    baseline_vector = background.median(axis=0).to_numpy(dtype=float)
    x_values = x_eval.to_numpy(dtype=float)
    n_rows, n_features = x_values.shape
    contributions = np.zeros((n_rows, n_features), dtype=float)
    baseline_matrix = np.tile(baseline_vector, (n_rows, 1))
    base_values = model.predict_proba(baseline_matrix)[:, 1]
    for _ in range(permutations):
        order = rng.permutation(n_features)
        current = baseline_matrix.copy()
        previous = base_values.copy()
        for feature_index in order:
            current[:, feature_index] = x_values[:, feature_index]
            updated = model.predict_proba(current)[:, 1]
            contributions[:, feature_index] += updated - previous
            previous = updated
    contributions /= permutations
    return contributions, base_values, "deterministic_permutation_shap"


def calculate_shap_outputs(
    model: Any,
    production_frame: pd.DataFrame,
    background_frame: pd.DataFrame,
    sample_size: int = 60,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    selected = production_frame.nlargest(
        min(sample_size, len(production_frame)), "recency_days"
    ).copy()
    x_eval = selected[FEATURE_COLUMNS]
    background = background_frame[FEATURE_COLUMNS].sample(
        n=min(24, len(background_frame)), random_state=20260727
    )
    method = "shap_permutation_explainer"
    try:
        import shap

        def prediction_function(values: np.ndarray) -> np.ndarray:
            frame = pd.DataFrame(values, columns=FEATURE_COLUMNS)
            return model.predict_proba(frame)[:, 1]
        explainer = shap.Explainer(
            prediction_function,
            background.to_numpy(),
            feature_names=FEATURE_COLUMNS,
            algorithm="permutation",
        )
        explanation = explainer(
            x_eval.to_numpy(),
            max_evals=2 * len(FEATURE_COLUMNS) + 1,
            silent=True,
        )
        shap_values = np.asarray(explanation.values)
        base_values = np.asarray(explanation.base_values)
    except Exception:
        shap_values, base_values, method = _permutation_shap_fallback(
            model, x_eval, background
        )

    global_importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "mean_abs_shap": np.mean(np.abs(shap_values), axis=0),
            "mean_shap": np.mean(shap_values, axis=0),
        }
    ).sort_values("mean_abs_shap", ascending=False)
    global_importance["importance_share"] = (
        global_importance["mean_abs_shap"]
        / global_importance["mean_abs_shap"].sum()
    )

    local_rows: list[dict[str, object]] = []
    probabilities = model.predict_proba(x_eval)[:, 1]
    for row_index, customer_id in enumerate(selected["customer_id"]):
        top_features = np.argsort(-np.abs(shap_values[row_index]))[:5]
        for rank, feature_index in enumerate(top_features, start=1):
            feature = FEATURE_COLUMNS[int(feature_index)]
            local_rows.append(
                {
                    "customer_id": customer_id,
                    "rank": rank,
                    "feature": feature,
                    "feature_value": float(x_eval.iloc[row_index, feature_index]),
                    "shap_value": float(shap_values[row_index, feature_index]),
                    "base_value": float(np.ravel(base_values)[row_index % len(np.ravel(base_values))]),
                    "churn_probability": float(probabilities[row_index]),
                    "direction": (
                        "Increases risk"
                        if shap_values[row_index, feature_index] > 0
                        else "Decreases risk"
                    ),
                }
            )
    metadata = {
        "method": method,
        "sample_size": len(selected),
        "background_size": len(background),
        "feature_count": len(FEATURE_COLUMNS),
        "additivity_mean_absolute_error": float(
            np.mean(
                np.abs(
                    np.ravel(base_values)[: len(selected)]
                    + shap_values.sum(axis=1)
                    - probabilities
                )
            )
        ),
    }
    return global_importance, pd.DataFrame(local_rows), metadata
