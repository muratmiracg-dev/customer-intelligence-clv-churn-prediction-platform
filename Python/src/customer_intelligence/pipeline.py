from __future__ import annotations

import argparse
import platform
import sys

import joblib
import pandas as pd
import sklearn

from .analytics import (
    calculate_cohort_retention,
    calculate_monthly_metrics,
    calculate_rfm,
    summarize_segments,
)
from .campaign import recommend_campaigns
from .config import CONFIG, FEATURE_COLUMNS, PROJECT_ROOT
from .data_generation import generate_all
from .explainability import calculate_shap_outputs
from .features import (
    build_customer_360,
    build_customer_snapshot,
    validate_feature_matrix,
)
from .modeling import (
    build_drift_report,
    train_churn_models,
    train_clv_models,
)
from .sql_layer import build_sqlite_database
from .utils import ensure_directories, write_csv, write_json


def _calendar_table() -> pd.DataFrame:
    dates = pd.date_range(CONFIG.data_start, CONFIG.data_end, freq="D")
    calendar = pd.DataFrame({"date": dates})
    calendar["year"] = calendar["date"].dt.year
    calendar["quarter"] = "Q" + calendar["date"].dt.quarter.astype(str)
    calendar["month_number"] = calendar["date"].dt.month
    calendar["month_name"] = calendar["date"].dt.month_name()
    calendar["year_month"] = calendar["date"].dt.strftime("%Y-%m")
    calendar["month_start"] = calendar["date"].dt.to_period("M").dt.to_timestamp()
    calendar["week_of_year"] = calendar["date"].dt.isocalendar().week.astype(int)
    calendar["day_of_week"] = calendar["date"].dt.day_name()
    calendar["is_weekend"] = calendar["date"].dt.dayofweek.ge(5).astype(int)
    return calendar


def _data_quality_report(
    customers: pd.DataFrame,
    products: pd.DataFrame,
    orders: pd.DataFrame,
    order_lines: pd.DataFrame,
    interactions: pd.DataFrame,
    production_snapshot: pd.DataFrame,
) -> pd.DataFrame:
    customer_ids = set(customers["customer_id"])
    order_ids = set(orders["order_id"])
    checks = [
        ("customer_primary_key_unique", not customers["customer_id"].duplicated().any()),
        ("product_primary_key_unique", not products["product_id"].duplicated().any()),
        ("order_primary_key_unique", not orders["order_id"].duplicated().any()),
        (
            "order_line_primary_key_unique",
            not order_lines["order_line_id"].duplicated().any(),
        ),
        (
            "orders_customer_fk_valid",
            set(orders["customer_id"]).issubset(customer_ids),
        ),
        (
            "order_lines_order_fk_valid",
            set(order_lines["order_id"]).issubset(order_ids),
        ),
        (
            "interactions_customer_fk_valid",
            set(interactions["customer_id"]).issubset(customer_ids),
        ),
        ("order_revenue_nonnegative", bool(orders["net_revenue"].ge(0).all())),
        (
            "order_dates_in_range",
            bool(
                pd.to_datetime(orders["order_date"]).between(
                    CONFIG.data_start, CONFIG.data_end
                ).all()
            ),
        ),
        (
            "snapshot_features_valid",
            len(validate_feature_matrix(production_snapshot)) == 0,
        ),
    ]
    return pd.DataFrame(
        {
            "check_name": [name for name, _ in checks],
            "status": ["PASS" if passed else "FAIL" for _, passed in checks],
            "passed": [int(passed) for _, passed in checks],
        }
    )


def _executive_kpis(
    customer_360: pd.DataFrame,
    cohort_long: pd.DataFrame,
    churn_comparison: pd.DataFrame,
    clv_comparison: pd.DataFrame,
    campaign_summary: pd.DataFrame,
) -> pd.DataFrame:
    active = customer_360["frequency_12m"].gt(0)
    high_risk = customer_360["risk_band"].isin(["High", "Critical"])
    recent_cohorts = cohort_long[
        (cohort_long["cohort_index"] == 3)
        & (cohort_long["cohort_month"] >= "2024-01")
    ]
    champion_churn = churn_comparison.iloc[0]
    champion_clv = clv_comparison.iloc[0]
    values = [
        ("Customers", customer_360["customer_id"].nunique(), "count"),
        ("Active Customers 12M", int(active.sum()), "count"),
        ("Net Revenue 12M", customer_360["monetary_12m"].sum(), "TRY"),
        ("Gross Margin 12M", customer_360["gross_margin_12m"].sum(), "TRY"),
        ("Predicted CLV 12M", customer_360["predicted_clv_12m"].sum(), "TRY"),
        ("High/Critical Risk Customers", int(high_risk.sum()), "count"),
        (
            "Revenue at Risk",
            customer_360.loc[high_risk, "monetary_12m"].sum(),
            "TRY",
        ),
        (
            "Average Churn Probability",
            customer_360["churn_probability"].mean(),
            "percent",
        ),
        (
            "M3 Cohort Retention",
            recent_cohorts["retention_rate"].mean(),
            "percent",
        ),
        ("Churn ROC-AUC", champion_churn["roc_auc"], "decimal"),
        ("Churn PR-AUC", champion_churn["pr_auc"], "decimal"),
        ("Lift at Top 10%", champion_churn["lift_at_10pct"], "multiple"),
        ("CLV Test MAE", champion_clv["mae"], "TRY"),
        ("CLV Test R2", champion_clv["r2"], "decimal"),
        (
            "Campaign Budget Allocated",
            campaign_summary["allocated_budget"].sum(),
            "TRY",
        ),
        (
            "Expected Incremental Margin",
            campaign_summary["expected_incremental_margin"].sum(),
            "TRY",
        ),
    ]
    return pd.DataFrame(values, columns=["kpi", "value", "format"])


def run_pipeline(seed: int = CONFIG.seed) -> dict[str, object]:
    ensure_directories(PROJECT_ROOT)
    generated = generate_all(seed)
    calendar = _calendar_table()
    raw_tables = {
        "dim_customers": generated.customers,
        "dim_products": generated.products,
        "fact_orders": generated.orders,
        "fact_order_lines": generated.order_lines,
        "fact_interactions_monthly": generated.interactions,
        "dim_campaigns": generated.campaigns,
        "fact_campaign_responses": generated.campaign_responses,
        "calendar": calendar,
    }
    for name, frame in raw_tables.items():
        write_csv(frame, CONFIG.raw_dir / f"{name}.csv")

    rfm = calculate_rfm(
        generated.customers, generated.orders, CONFIG.production_cutoff
    )
    cohort_long, cohort_matrix = calculate_cohort_retention(generated.orders)
    monthly_metrics = calculate_monthly_metrics(
        generated.customers, generated.orders
    )
    churn = train_churn_models(
        generated.customers, generated.orders, generated.interactions
    )
    clv = train_clv_models(
        generated.customers, generated.orders, generated.interactions
    )
    production_snapshot = build_customer_snapshot(
        generated.customers,
        generated.orders,
        generated.interactions,
        CONFIG.production_cutoff,
    )
    shap_global, shap_local, shap_metadata = calculate_shap_outputs(
        churn.model,
        production_snapshot,
        churn.train_frame,
    )
    drift = build_drift_report(churn.test_frame, production_snapshot)
    campaign_targets, campaign_summary = recommend_campaigns(
        production_snapshot,
        rfm,
        clv.production_scored,
        churn.production_scored,
    )
    customer_360 = build_customer_360(
        production_snapshot,
        rfm,
        clv.production_scored,
        churn.production_scored,
        campaign_targets,
    )
    segment_summary = summarize_segments(customer_360)
    executive_kpis = _executive_kpis(
        customer_360,
        cohort_long,
        churn.comparison,
        clv.comparison,
        campaign_summary,
    )
    quality = _data_quality_report(
        generated.customers,
        generated.products,
        generated.orders,
        generated.order_lines,
        generated.interactions,
        production_snapshot,
    )
    if quality["status"].ne("PASS").any():
        failed = quality.loc[quality["status"].ne("PASS"), "check_name"].tolist()
        raise ValueError(f"Data quality gates failed: {failed}")

    processed_tables = {
        "customer_snapshot_features": production_snapshot,
        "rfm_scores": rfm,
        "cohort_retention_long": cohort_long,
        "cohort_retention_matrix": cohort_matrix,
        "monthly_customer_metrics": monthly_metrics,
        "churn_model_comparison": churn.comparison,
        "churn_test_predictions": churn.test_scored,
        "churn_predictions": churn.production_scored,
        "churn_calibration": churn.calibration,
        "churn_lift_curve": churn.lift,
        "fairness_audit": churn.fairness,
        "clv_model_comparison": clv.comparison,
        "clv_test_predictions": clv.test_scored,
        "clv_predictions": clv.production_scored,
        "shap_global_importance": shap_global,
        "shap_local_explanations": shap_local,
        "drift_monitoring": drift,
        "campaign_targets": campaign_targets,
        "campaign_summary": campaign_summary,
        "customer_360": customer_360,
        "segment_summary": segment_summary,
        "executive_kpis": executive_kpis,
        "data_quality_report": quality,
    }
    for name, frame in processed_tables.items():
        write_csv(frame, CONFIG.processed_dir / f"{name}.csv")

    joblib.dump(
        {
            "model": churn.model,
            "features": FEATURE_COLUMNS,
            "threshold": churn.threshold,
            "snapshot_date": CONFIG.production_cutoff,
        },
        CONFIG.model_dir / "churn_champion.joblib",
        compress=3,
    )
    joblib.dump(
        {
            "model": clv.model,
            "features": FEATURE_COLUMNS,
            "snapshot_date": CONFIG.production_cutoff,
        },
        CONFIG.model_dir / "clv_champion.joblib",
        compress=3,
    )
    metadata = {
        "project": "Customer Intelligence, CLV & Churn Prediction Platform",
        "company": CONFIG.company_name,
        "seed": seed,
        "data_period": [CONFIG.data_start, CONFIG.data_end],
        "production_snapshot": CONFIG.production_cutoff,
        "churn_horizon_days": CONFIG.churn_horizon_days,
        "clv_horizon_days": CONFIG.clv_horizon_days,
        "churn_champion": str(churn.comparison.iloc[0]["model"]),
        "clv_champion": str(clv.comparison.iloc[0]["model"]),
        "churn_threshold": churn.threshold,
        "feature_columns": FEATURE_COLUMNS,
        "explainability": shap_metadata,
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
        "generated_rows": {name: len(frame) for name, frame in raw_tables.items()},
    }
    write_json(metadata, CONFIG.model_dir / "model_metadata.json")
    build_sqlite_database(
        PROJECT_ROOT / "SQL" / "customer_intelligence.db",
        raw_tables,
        {
            "customer_360": customer_360,
            "rfm_scores": rfm,
            "cohort_retention_long": cohort_long,
            "campaign_targets": campaign_targets,
            "executive_kpis": executive_kpis,
        },
    )
    return {
        "raw": raw_tables,
        "processed": processed_tables,
        "metadata": metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the customer intelligence platform.")
    parser.add_argument("--seed", type=int, default=CONFIG.seed)
    args = parser.parse_args()
    outputs = run_pipeline(seed=args.seed)
    print(
        f"Pipeline complete: {len(outputs['raw'])} raw tables, "
        f"{len(outputs['processed'])} processed tables."
    )


if __name__ == "__main__":
    sys.exit(main())
