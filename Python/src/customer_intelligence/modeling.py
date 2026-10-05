from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import CONFIG, FEATURE_COLUMNS
from .features import build_customer_snapshot


@dataclass
class ClassificationArtifacts:
    model: Any
    threshold: float
    comparison: pd.DataFrame
    test_scored: pd.DataFrame
    production_scored: pd.DataFrame
    calibration: pd.DataFrame
    lift: pd.DataFrame
    fairness: pd.DataFrame
    train_frame: pd.DataFrame
    test_frame: pd.DataFrame


@dataclass
class RegressionArtifacts:
    model: Any
    comparison: pd.DataFrame
    test_scored: pd.DataFrame
    production_scored: pd.DataFrame
    train_frame: pd.DataFrame
    test_frame: pd.DataFrame


def _optimal_f1_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    thresholds = np.linspace(0.15, 0.85, 71)
    scores = [f1_score(y_true, probabilities >= threshold) for threshold in thresholds]
    return float(thresholds[int(np.argmax(scores))])


def _classification_metrics(
    y_true: pd.Series, probabilities: np.ndarray, threshold: float
) -> dict[str, float]:
    predictions = probabilities >= threshold
    order = np.argsort(-probabilities)
    top_10 = order[: max(1, int(len(order) * 0.10))]
    top_20 = order[: max(1, int(len(order) * 0.20))]
    base_rate = float(np.mean(y_true))
    lift_10 = float(np.mean(y_true.iloc[top_10]) / base_rate) if base_rate else 0.0
    recall_20 = (
        float(np.sum(y_true.iloc[top_20]) / max(1, np.sum(y_true))) if len(y_true) else 0.0
    )
    return {
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "f1": float(f1_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "lift_at_10pct": lift_10,
        "recall_at_20pct": recall_20,
        "threshold": threshold,
    }


def _calibration_table(
    y_true: pd.Series, probabilities: np.ndarray, bins: int = 10
) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": y_true.to_numpy(), "probability": probabilities})
    frame["decile"] = pd.qcut(
        frame["probability"].rank(method="first"), q=bins, labels=False, duplicates="drop"
    )
    return (
        frame.groupby("decile", as_index=False)
        .agg(
            customers=("actual", "size"),
            mean_predicted_probability=("probability", "mean"),
            observed_churn_rate=("actual", "mean"),
        )
        .sort_values("mean_predicted_probability")
    )


def _lift_table(y_true: pd.Series, probabilities: np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": y_true.to_numpy(), "probability": probabilities})
    frame = frame.sort_values("probability", ascending=False).reset_index(drop=True)
    frame["population_pct"] = (np.arange(len(frame)) + 1) / len(frame)
    frame["cumulative_churners"] = frame["actual"].cumsum()
    total_churners = max(1, int(frame["actual"].sum()))
    frame["cumulative_gain"] = frame["cumulative_churners"] / total_churners
    frame["cumulative_lift"] = frame["cumulative_gain"] / frame["population_pct"]
    checkpoints = np.linspace(0.1, 1.0, 10)
    rows = []
    for checkpoint in checkpoints:
        index = min(len(frame) - 1, max(0, int(np.ceil(checkpoint * len(frame))) - 1))
        row = frame.iloc[index]
        rows.append(
            {
                "population_pct": checkpoint,
                "cumulative_gain": float(row["cumulative_gain"]),
                "cumulative_lift": float(row["cumulative_lift"]),
            }
        )
    return pd.DataFrame(rows)


def _fairness_audit(
    test_frame: pd.DataFrame,
    probabilities: np.ndarray,
    threshold: float,
) -> pd.DataFrame:
    scored = test_frame[
        ["customer_id", "region", "age_band", "churn_90d"]
    ].copy()
    scored["probability"] = probabilities
    scored["prediction"] = (probabilities >= threshold).astype(int)
    rows: list[dict[str, object]] = []
    for attribute in ["region", "age_band"]:
        for group, frame in scored.groupby(attribute):
            if len(frame) < 25:
                continue
            y = frame["churn_90d"]
            auc = (
                float(roc_auc_score(y, frame["probability"])) if y.nunique() > 1 else np.nan
            )
            positives = max(1, int(y.sum()))
            true_positives = int(((frame["prediction"] == 1) & (y == 1)).sum())
            rows.append(
                {
                    "audit_attribute": attribute,
                    "audit_group": group,
                    "customers": len(frame),
                    "observed_churn_rate": float(y.mean()),
                    "average_predicted_risk": float(frame["probability"].mean()),
                    "roc_auc": auc,
                    "true_positive_rate": true_positives / positives,
                }
            )
    return pd.DataFrame(rows)


def train_churn_models(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    interactions: pd.DataFrame,
) -> ClassificationArtifacts:
    train_cutoffs = ["2024-03-31", "2024-06-30", "2024-09-30"]
    train_frames = [
        build_customer_snapshot(
            customers,
            orders,
            interactions,
            cutoff=cutoff,
            horizon_days=CONFIG.churn_horizon_days,
            include_churn_target=True,
        )
        for cutoff in train_cutoffs
    ]
    train_frame = pd.concat(train_frames, ignore_index=True)
    test_frame = build_customer_snapshot(
        customers,
        orders,
        interactions,
        cutoff="2024-12-31",
        horizon_days=CONFIG.churn_horizon_days,
        include_churn_target=True,
    )
    production_frame = build_customer_snapshot(
        customers,
        orders,
        interactions,
        cutoff=CONFIG.production_cutoff,
        include_churn_target=False,
    )

    x_train = train_frame[FEATURE_COLUMNS]
    y_train = train_frame["churn_90d"]
    x_test = test_frame[FEATURE_COLUMNS]
    y_test = test_frame["churn_90d"]

    models = {
        "Logistic Regression": Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2500,
                        class_weight="balanced",
                        C=0.75,
                        random_state=CONFIG.seed,
                    ),
                ),
            ]
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=260,
            max_depth=14,
            min_samples_leaf=12,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=CONFIG.seed,
            n_jobs=-1,
        ),
        "Histogram Gradient Boosting": HistGradientBoostingClassifier(
            learning_rate=0.055,
            max_iter=220,
            max_leaf_nodes=25,
            min_samples_leaf=24,
            l2_regularization=0.75,
            class_weight="balanced",
            random_state=CONFIG.seed,
        ),
    }
    comparison_rows: list[dict[str, object]] = []
    fitted: dict[str, Any] = {}
    for name, model in models.items():
        estimator = clone(model)
        estimator.fit(x_train, y_train)
        train_prob = estimator.predict_proba(x_train)[:, 1]
        threshold = _optimal_f1_threshold(y_train, train_prob)
        test_prob = estimator.predict_proba(x_test)[:, 1]
        metrics = _classification_metrics(y_test, test_prob, threshold)
        comparison_rows.append({"model": name, **metrics})
        fitted[name] = estimator
    comparison = pd.DataFrame(comparison_rows)
    comparison["selection_score"] = (
        0.45 * comparison["roc_auc"]
        + 0.35 * comparison["pr_auc"]
        + 0.20 * (1 - comparison["brier_score"])
    )
    comparison = comparison.sort_values("selection_score", ascending=False).reset_index(
        drop=True
    )
    champion_name = str(comparison.loc[0, "model"])
    calibrated = CalibratedClassifierCV(
        estimator=clone(models[champion_name]), method="sigmoid", cv=3
    )
    calibrated.fit(x_train, y_train)
    train_prob = calibrated.predict_proba(x_train)[:, 1]
    threshold = _optimal_f1_threshold(y_train, train_prob)
    test_prob = calibrated.predict_proba(x_test)[:, 1]
    production_prob = calibrated.predict_proba(production_frame[FEATURE_COLUMNS])[:, 1]

    champion_metrics = _classification_metrics(y_test, test_prob, threshold)
    comparison = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "model": f"{champion_name} (calibrated champion)",
                        **champion_metrics,
                        "selection_score": 0.45 * champion_metrics["roc_auc"]
                        + 0.35 * champion_metrics["pr_auc"]
                        + 0.20 * (1 - champion_metrics["brier_score"]),
                    }
                ]
            ),
            comparison,
        ],
        ignore_index=True,
    )
    test_scored = test_frame[
        ["customer_id", "snapshot_date", "region", "age_band", "churn_90d"]
    ].copy()
    test_scored["churn_probability"] = test_prob
    test_scored["predicted_churn"] = (test_prob >= threshold).astype(int)
    production_scored = production_frame[["customer_id", "snapshot_date"]].copy()
    production_scored["churn_probability"] = production_prob
    production_scored["risk_percentile"] = production_scored[
        "churn_probability"
    ].rank(pct=True)
    production_scored["risk_band"] = pd.cut(
        production_scored["churn_probability"],
        bins=[-np.inf, 0.35, 0.55, 0.72, np.inf],
        labels=["Low", "Medium", "High", "Critical"],
    ).astype(str)
    return ClassificationArtifacts(
        model=calibrated,
        threshold=threshold,
        comparison=comparison,
        test_scored=test_scored,
        production_scored=production_scored,
        calibration=_calibration_table(y_test, test_prob),
        lift=_lift_table(y_test, test_prob),
        fairness=_fairness_audit(test_frame, test_prob, threshold),
        train_frame=train_frame,
        test_frame=test_frame,
    )


def _regression_metrics(
    y_true: pd.Series, predictions: np.ndarray
) -> dict[str, float]:
    clipped = np.clip(predictions, 0, None)
    correlation = spearmanr(y_true, clipped).statistic
    return {
        "mae": float(mean_absolute_error(y_true, clipped)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, clipped))),
        "r2": float(r2_score(y_true, clipped)),
        "spearman_correlation": float(correlation if np.isfinite(correlation) else 0),
    }


def train_clv_models(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    interactions: pd.DataFrame,
) -> RegressionArtifacts:
    train_cutoffs = ["2023-03-31", "2023-09-30", "2024-03-31", "2024-06-30"]
    train_frames = [
        build_customer_snapshot(
            customers,
            orders,
            interactions,
            cutoff=cutoff,
            horizon_days=CONFIG.clv_horizon_days,
            include_clv_target=True,
        )
        for cutoff in train_cutoffs
    ]
    train_frame = pd.concat(train_frames, ignore_index=True)
    test_frame = build_customer_snapshot(
        customers,
        orders,
        interactions,
        cutoff="2024-12-31",
        horizon_days=CONFIG.clv_horizon_days,
        include_clv_target=True,
    )
    production_frame = build_customer_snapshot(
        customers,
        orders,
        interactions,
        cutoff=CONFIG.production_cutoff,
    )
    x_train = train_frame[FEATURE_COLUMNS]
    y_train = train_frame["future_gross_margin"]
    x_test = test_frame[FEATURE_COLUMNS]
    y_test = test_frame["future_gross_margin"]

    models = {
        "Ridge Regression": Pipeline(
            [("scale", StandardScaler()), ("model", Ridge(alpha=18.0))]
        ),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=240,
            max_depth=14,
            min_samples_leaf=10,
            max_features=0.80,
            random_state=CONFIG.seed,
            n_jobs=-1,
        ),
        "Histogram Gradient Boosting Regressor": HistGradientBoostingRegressor(
            learning_rate=0.055,
            max_iter=230,
            max_leaf_nodes=25,
            min_samples_leaf=24,
            l2_regularization=1.0,
            loss="squared_error",
            random_state=CONFIG.seed,
        ),
    }
    rows: list[dict[str, object]] = []
    fitted: dict[str, Any] = {}
    for name, model in models.items():
        estimator = clone(model)
        estimator.fit(x_train, y_train)
        predictions = estimator.predict(x_test)
        rows.append({"model": name, **_regression_metrics(y_test, predictions)})
        fitted[name] = estimator
    comparison = pd.DataFrame(rows)
    comparison["normalized_mae"] = comparison["mae"] / max(1.0, y_test.mean())
    comparison["selection_score"] = (
        0.45 * (1 - comparison["normalized_mae"].clip(upper=1))
        + 0.35 * comparison["spearman_correlation"].clip(lower=0)
        + 0.20 * comparison["r2"].clip(lower=0)
    )
    comparison = comparison.sort_values("selection_score", ascending=False).reset_index(
        drop=True
    )
    champion_name = str(comparison.loc[0, "model"])
    champion = fitted[champion_name]
    test_predictions = np.clip(champion.predict(x_test), 0, None)
    production_predictions = np.clip(
        champion.predict(production_frame[FEATURE_COLUMNS]), 0, None
    )
    test_scored = test_frame[
        ["customer_id", "snapshot_date", "future_gross_margin"]
    ].copy()
    test_scored["predicted_clv_12m"] = test_predictions
    production_scored = production_frame[["customer_id", "snapshot_date"]].copy()
    production_scored["predicted_clv_12m"] = production_predictions
    production_scored["clv_percentile"] = production_scored[
        "predicted_clv_12m"
    ].rank(pct=True)
    production_scored["clv_band"] = pd.qcut(
        production_scored["predicted_clv_12m"].rank(method="first"),
        q=4,
        labels=["Low", "Developing", "High", "Strategic"],
    ).astype(str)
    return RegressionArtifacts(
        model=champion,
        comparison=comparison,
        test_scored=test_scored,
        production_scored=production_scored,
        train_frame=train_frame,
        test_frame=test_frame,
    )


def population_stability_index(
    reference: pd.Series, current: pd.Series, bins: int = 10
) -> float:
    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer greater than or equal to 2")
    reference = pd.to_numeric(reference, errors="coerce")
    current = pd.to_numeric(current, errors="coerce")
    if reference.empty or current.empty:
        raise ValueError("PSI requires non-empty reference and current samples")
    if reference.isna().any() or current.isna().any():
        raise ValueError("PSI samples must contain only finite numeric values")
    if not np.isfinite(reference.to_numpy()).all() or not np.isfinite(
        current.to_numpy()
    ).all():
        raise ValueError("PSI samples must contain only finite numeric values")
    boundaries = np.unique(
        np.quantile(reference, np.linspace(0, 1, bins + 1))
    )
    if len(boundaries) < 3:
        return 0.0
    boundaries[0] = -np.inf
    boundaries[-1] = np.inf
    reference_bins = pd.cut(reference, boundaries, include_lowest=True)
    current_bins = pd.cut(current, boundaries, include_lowest=True)
    ref_pct = reference_bins.value_counts(normalize=True, sort=False).clip(lower=1e-6)
    cur_pct = current_bins.value_counts(normalize=True, sort=False).clip(lower=1e-6)
    cur_pct = cur_pct.reindex(ref_pct.index, fill_value=1e-6)
    return float(((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)).sum())


def build_drift_report(
    reference_snapshot: pd.DataFrame, production_snapshot: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    for feature in FEATURE_COLUMNS:
        psi = population_stability_index(
            reference_snapshot[feature], production_snapshot[feature]
        )
        status = "Stable" if psi < 0.10 else "Watch" if psi < 0.25 else "Investigate"
        rows.append(
            {
                "feature": feature,
                "psi": psi,
                "status": status,
                "reference_mean": float(reference_snapshot[feature].mean()),
                "production_mean": float(production_snapshot[feature].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("psi", ascending=False)
