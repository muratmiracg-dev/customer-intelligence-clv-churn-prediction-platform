from __future__ import annotations

import base64
import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "Data" / "Processed"
POWERBI_DIR = PROJECT_ROOT / "PowerBI"
OUTPUT_ROOT = POWERBI_DIR / "Customer_Intelligence_PBIP"
PROJECT_NAME = "Customer_Intelligence_Analytics"
REPORT_NAME = f"{PROJECT_NAME}.Report"
MODEL_NAME = f"{PROJECT_NAME}.SemanticModel"
PBIP_PATH = OUTPUT_ROOT / f"{PROJECT_NAME}.pbip"
TEMPLATE_ROOT = (
    PROJECT_ROOT.parent
    / "integrated-fpa-budgeting-forecasting-scenario-planning"
    / "PowerBI"
    / "Integrated_FPA_PBIP"
)


def csv_m_expression(frame: pd.DataFrame, type_map: dict[str, str]) -> list[str]:
    export = frame.copy()
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d")
    csv_text = export.to_csv(index=False, lineterminator="\n")
    encoded = base64.b64encode(csv_text.encode("utf-8")).decode("ascii")
    type_pairs = ", ".join(
        f'{{"{column}", {power_query_type}}}'
        for column, power_query_type in type_map.items()
    )
    return [
        "let",
        f'    Binary = Binary.FromText("{encoded}", BinaryEncoding.Base64),',
        f'    Source = Csv.Document(Binary, [Delimiter=",", Columns={len(frame.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{type_pairs}}}, "en-US")',
        "in",
        "    Typed",
    ]


def infer_type_map(frame: pd.DataFrame) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for column in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[column]):
            mapping[column] = "type date"
        elif pd.api.types.is_bool_dtype(frame[column]):
            mapping[column] = "type logical"
        elif pd.api.types.is_integer_dtype(frame[column]):
            mapping[column] = "Int64.Type"
        elif pd.api.types.is_numeric_dtype(frame[column]):
            mapping[column] = "type number"
        else:
            mapping[column] = "type text"
    return mapping


def column_metadata(frame: pd.DataFrame, type_map: dict[str, str]) -> list[dict]:
    columns: list[dict] = []
    for column in frame.columns:
        power_query_type = type_map[column]
        if power_query_type == "type date":
            item = {
                "name": column,
                "dataType": "dateTime",
                "sourceColumn": column,
                "formatString": "mmm yyyy" if "Month" in column else "yyyy-mm-dd",
            }
        elif power_query_type == "Int64.Type":
            item = {
                "name": column,
                "dataType": "int64",
                "sourceColumn": column,
                "formatString": "#,0",
            }
        elif power_query_type == "type number":
            item = {"name": column, "dataType": "double", "sourceColumn": column}
        elif power_query_type == "type logical":
            item = {"name": column, "dataType": "boolean", "sourceColumn": column}
        else:
            item = {"name": column, "dataType": "string", "sourceColumn": column}
        columns.append(item)
    return columns


def table_metadata(
    name: str,
    frame: pd.DataFrame,
    measures: list[dict] | None = None,
) -> dict:
    type_map = infer_type_map(frame)
    table = {
        "name": name,
        "columns": column_metadata(frame, type_map),
        "partitions": [
            {
                "name": name,
                "mode": "import",
                "source": {
                    "type": "m",
                    "expression": csv_m_expression(frame, type_map),
                },
            }
        ],
    }
    if measures:
        table["measures"] = measures
    return table


def _measure(name: str, expression: str, format_string: str) -> dict:
    return {
        "name": name,
        "expression": expression,
        "formatString": format_string,
    }


def build_model_frames() -> dict[str, tuple[pd.DataFrame, list[dict]]]:
    monthly = pd.read_csv(DATA_DIR / "monthly_customer_metrics.csv", parse_dates=["month"])
    customer = pd.read_csv(
        DATA_DIR / "customer_360.csv", parse_dates=["snapshot_date"]
    )
    segment = pd.read_csv(DATA_DIR / "segment_summary.csv")
    campaign = pd.read_csv(DATA_DIR / "campaign_summary.csv")
    cohort = pd.read_csv(DATA_DIR / "cohort_retention_long.csv")
    churn_models = pd.read_csv(DATA_DIR / "churn_model_comparison.csv")
    shap = pd.read_csv(DATA_DIR / "shap_global_importance.csv")
    drift = pd.read_csv(DATA_DIR / "drift_monitoring.csv")

    monthly = monthly.rename(
        columns={
            "month": "Month",
            "orders": "Orders",
            "active_customers": "Active Customers",
            "net_revenue": "Net Revenue",
            "gross_margin": "Gross Margin",
            "returned_orders": "Returned Orders",
            "repeat_customers": "Repeat Customers",
            "new_customers": "New Customers",
            "average_order_value": "Average Order Value",
            "gross_margin_pct": "Gross Margin Rate",
            "repeat_customer_rate": "Repeat Customer Rate",
            "return_rate": "Return Rate",
        }
    )
    monthly["Month Key"] = monthly["Month"].dt.strftime("%Y-%m")
    final_mask = monthly["Month"].eq(monthly["Month"].max())
    total_predicted_clv = float(customer["predicted_clv_12m"].sum())
    risk_mask = customer["risk_band"].isin(["High", "Critical"])
    revenue_at_risk = float(customer.loc[risk_mask, "monetary_12m"].sum())
    avg_churn = float(customer["churn_probability"].mean())
    avg_recency = float(customer["recency_days"].mean())
    campaign_budget = float(campaign["allocated_budget"].sum())
    campaign_margin = float(campaign["expected_incremental_margin"].sum())
    campaign_roi = campaign_margin / campaign_budget if campaign_budget else 0.0
    churn_auc = float(churn_models.iloc[0]["roc_auc"])
    monthly["Predicted CLV"] = np.where(final_mask, total_predicted_clv, np.nan)
    monthly["Revenue at Risk"] = np.where(final_mask, revenue_at_risk, np.nan)
    monthly["Customers"] = np.where(final_mask, len(customer), np.nan)
    monthly["Churn Probability"] = np.where(
        final_mask, avg_churn, 1 - monthly["Repeat Customer Rate"].clip(0, 1)
    )
    monthly["Average Recency Days"] = np.where(final_mask, avg_recency, np.nan)
    monthly["Campaign Budget"] = np.where(final_mask, campaign_budget, np.nan)
    monthly["Campaign Expected Margin"] = np.where(
        final_mask, campaign_margin, np.nan
    )
    monthly["Campaign ROI"] = np.where(final_mask, campaign_roi, np.nan)
    monthly["Churn ROC-AUC"] = np.where(final_mask, churn_auc, np.nan)
    monthly = monthly[
        [
            "Month",
            "Month Key",
            "Net Revenue",
            "Gross Margin",
            "Active Customers",
            "New Customers",
            "Orders",
            "Average Order Value",
            "Gross Margin Rate",
            "Repeat Customer Rate",
            "Return Rate",
            "Predicted CLV",
            "Revenue at Risk",
            "Customers",
            "Churn Probability",
            "Average Recency Days",
            "Campaign Budget",
            "Campaign Expected Margin",
            "Campaign ROI",
            "Churn ROC-AUC",
        ]
    ]

    calendar = pd.DataFrame(
        {
            "Date": pd.date_range(
                monthly["Month"].min(), monthly["Month"].max(), freq="MS"
            )
        }
    )
    calendar["Month"] = calendar["Date"].dt.strftime("%b %Y")
    calendar["Month Key"] = calendar["Date"].dt.strftime("%Y-%m")
    calendar["Year"] = calendar["Date"].dt.year
    calendar["Quarter"] = "Q" + calendar["Date"].dt.quarter.astype(str)

    segment = segment.rename(
        columns={
            "rfm_segment": "RFM Segment",
            "customers": "Customers",
            "revenue_12m": "Revenue 12M",
            "gross_margin_12m": "Gross Margin 12M",
            "predicted_clv_12m": "Predicted CLV 12M",
            "average_churn_probability": "Average Churn Probability",
            "average_order_value": "Average Order Value",
            "campaign_selected": "Campaign Selected",
            "expected_incremental_margin": "Expected Incremental Margin",
            "customer_share": "Customer Share",
            "revenue_share": "Revenue Share",
        }
    )
    campaign = campaign.rename(
        columns={
            "recommended_action": "Recommended Action",
            "eligible_customers": "Eligible Customers",
            "selected_customers": "Selected Customers",
            "allocated_budget": "Allocated Budget",
            "expected_incremental_margin": "Expected Incremental Margin",
            "average_expected_roi": "Average Expected ROI",
            "average_churn_probability": "Average Churn Probability",
            "predicted_clv": "Predicted CLV",
            "expected_total_value": "Expected Total Value",
        }
    )
    risk = (
        customer.groupby("risk_band", as_index=False)
        .agg(
            Customers=("customer_id", "nunique"),
            Revenue=("monetary_12m", "sum"),
            Predicted_CLV=("predicted_clv_12m", "sum"),
        )
        .rename(
            columns={
                "risk_band": "Risk Band",
                "Predicted_CLV": "Predicted CLV",
            }
        )
    )
    risk["Risk Order"] = risk["Risk Band"].map(
        {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    )
    model_comparison = churn_models.rename(
        columns={
            "model": "Model",
            "roc_auc": "ROC-AUC",
            "pr_auc": "PR-AUC",
            "brier_score": "Brier Score",
            "f1": "F1",
            "lift_at_10pct": "Lift at 10%",
        }
    )[["Model", "ROC-AUC", "PR-AUC", "Brier Score", "F1", "Lift at 10%"]]
    shap = shap.rename(
        columns={
            "feature": "Feature",
            "mean_abs_shap": "Mean Abs SHAP",
            "mean_shap": "Mean SHAP",
            "importance_share": "Importance Share",
        }
    )
    drift = drift.rename(
        columns={
            "feature": "Feature",
            "psi": "PSI",
            "status": "Status",
            "reference_mean": "Reference Mean",
            "production_mean": "Production Mean",
        }
    )
    cohort["cohort_month"] = pd.to_datetime(cohort["cohort_month"] + "-01")
    cohort = cohort.rename(
        columns={
            "cohort_month": "Cohort Month",
            "cohort_index": "Cohort Index",
            "active_customers": "Active Customers",
            "cohort_size": "Cohort Size",
            "retention_rate": "Retention Rate",
        }
    )
    customer_model = customer[
        [
            "customer_id",
            "snapshot_date",
            "region",
            "age_band",
            "loyalty_tier",
            "preferred_channel",
            "recency_days",
            "frequency_12m",
            "monetary_12m",
            "gross_margin_12m",
            "avg_order_value_12m",
            "rfm_segment",
            "predicted_clv_12m",
            "clv_band",
            "churn_probability",
            "risk_band",
            "recommended_action",
            "campaign_priority",
            "expected_incremental_margin",
            "selected_for_campaign",
        ]
    ].rename(
        columns={
            "customer_id": "Customer ID",
            "snapshot_date": "Snapshot Date",
            "region": "Region",
            "age_band": "Age Band",
            "loyalty_tier": "Loyalty Tier",
            "preferred_channel": "Preferred Channel",
            "recency_days": "Recency Days",
            "frequency_12m": "Frequency 12M",
            "monetary_12m": "Revenue 12M",
            "gross_margin_12m": "Gross Margin 12M",
            "avg_order_value_12m": "Average Order Value 12M",
            "rfm_segment": "RFM Segment",
            "predicted_clv_12m": "Predicted CLV 12M",
            "clv_band": "CLV Band",
            "churn_probability": "Churn Probability",
            "risk_band": "Risk Band",
            "recommended_action": "Recommended Action",
            "campaign_priority": "Campaign Priority",
            "expected_incremental_margin": "Expected Incremental Margin",
            "selected_for_campaign": "Selected for Campaign",
        }
    )

    monthly_measures = [
        _measure("KPI Net Revenue", "SUM(monthly_customer_metrics[Net Revenue])", "₺#,0"),
        _measure(
            "KPI Revenue Prior Year",
            "CALCULATE([KPI Net Revenue],DATEADD(dim_calendar[Date],-1,YEAR))",
            "₺#,0",
        ),
        _measure(
            "KPI Gross Margin",
            "SUM(monthly_customer_metrics[Gross Margin])",
            "₺#,0",
        ),
        _measure(
            "KPI Active Customers",
            "SUM(monthly_customer_metrics[Active Customers])",
            "#,0",
        ),
        _measure(
            "KPI Predicted CLV",
            "MAX(monthly_customer_metrics[Predicted CLV])",
            "₺#,0",
        ),
        _measure(
            "KPI Revenue at Risk",
            "MAX(monthly_customer_metrics[Revenue at Risk])",
            "₺#,0",
        ),
        _measure(
            "KPI New Customers",
            "SUM(monthly_customer_metrics[New Customers])",
            "#,0",
        ),
        _measure(
            "KPI Campaign Budget",
            "MAX(monthly_customer_metrics[Campaign Budget])",
            "₺#,0",
        ),
        _measure(
            "KPI Customers",
            "MAX(monthly_customer_metrics[Customers])",
            "#,0",
        ),
        _measure(
            "KPI Recency Days",
            "AVERAGE(monthly_customer_metrics[Average Recency Days])",
            "0.0",
        ),
        _measure(
            "KPI Gross Margin Rate",
            "DIVIDE([KPI Gross Margin],[KPI Net Revenue],0)",
            "0.0%",
        ),
        _measure(
            "KPI Churn Probability",
            "MAX(monthly_customer_metrics[Churn Probability])",
            "0.0%",
        ),
        _measure(
            "KPI Campaign ROI",
            "MAX(monthly_customer_metrics[Campaign ROI])",
            "0.00x",
        ),
        _measure(
            "KPI Churn ROC-AUC",
            "MAX(monthly_customer_metrics[Churn ROC-AUC])",
            "0.000",
        ),
        _measure(
            "KPI Net Revenue PY",
            "CALCULATE([KPI Net Revenue],DATEADD(dim_calendar[Date],-1,YEAR))",
            "₺#,0",
        ),
        _measure(
            "KPI Predicted CLV Benchmark",
            "[KPI Predicted CLV]",
            "₺#,0",
        ),
        _measure(
            "KPI Net Revenue YoY %",
            "DIVIDE([KPI Net Revenue]-[KPI Net Revenue PY],[KPI Net Revenue PY],0)",
            "0.0%",
        ),
        _measure(
            "KPI Revenue YoY Change",
            "[KPI Net Revenue]-[KPI Net Revenue PY]",
            "₺#,0",
        ),
    ]
    segment_measures = [
        _measure("Segment Revenue", "SUM(segment_summary[Revenue 12M])", "₺#,0"),
        _measure(
            "Segment Predicted CLV",
            "SUM(segment_summary[Predicted CLV 12M])",
            "₺#,0",
        ),
        _measure(
            "Segment Churn Risk",
            "AVERAGE(segment_summary[Average Churn Probability])",
            "0.0%",
        ),
        _measure("Segment Customers", "SUM(segment_summary[Customers])", "#,0"),
    ]
    campaign_measures = [
        _measure(
            "Campaign Budget",
            "SUM(campaign_summary[Allocated Budget])",
            "₺#,0",
        ),
        _measure(
            "Campaign Expected Margin",
            "SUM(campaign_summary[Expected Incremental Margin])",
            "₺#,0",
        ),
    ]
    risk_measures = [
        _measure("Risk Band Customers", "SUM(risk_bands[Customers])", "#,0")
    ]
    model_measures = [
        _measure("Model ROC-AUC", "AVERAGE(model_comparison[ROC-AUC])", "0.000"),
        _measure("Model PR-AUC", "AVERAGE(model_comparison[PR-AUC])", "0.000"),
    ]
    shap_measures = [
        _measure(
            "SHAP Importance",
            "SUM(shap_importance[Mean Abs SHAP])",
            "0.000",
        ),
        _measure(
            "SHAP Share",
            "SUM(shap_importance[Importance Share])",
            "0.0%",
        ),
    ]
    drift_measures = [
        _measure("Average PSI", "AVERAGE(drift_monitoring[PSI])", "0.000")
    ]
    return {
        "dim_calendar": (calendar, []),
        "monthly_customer_metrics": (monthly, monthly_measures),
        "segment_summary": (segment, segment_measures),
        "campaign_summary": (campaign, campaign_measures),
        "risk_bands": (risk, risk_measures),
        "model_comparison": (model_comparison, model_measures),
        "shap_importance": (shap, shap_measures),
        "drift_monitoring": (drift, drift_measures),
        "cohort_retention": (cohort, []),
        "customer_360": (customer_model, []),
    }


def build_semantic_model(model_dir: Path) -> None:
    template_model = (
        TEMPLATE_ROOT
        / "Integrated_FPA_Planning_Analytics.SemanticModel"
        / "model.bim"
    )
    model = json.loads(template_model.read_text(encoding="utf-8"))
    frames = build_model_frames()
    model["model"]["tables"] = [
        table_metadata(name, frame, measures)
        for name, (frame, measures) in frames.items()
    ]
    model["model"]["relationships"] = [
        {
            "name": "rel_monthly_calendar",
            "fromTable": "monthly_customer_metrics",
            "fromColumn": "Month",
            "toTable": "dim_calendar",
            "toColumn": "Date",
        }
    ]
    (model_dir / "model.bim").write_text(
        json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8"
    )


REPLACEMENTS = {
    "monthly_performance.KPI Revenue Variance": "monthly_customer_metrics.KPI Revenue YoY Change",
    "monthly_performance.KPI Revenue YoY %": "monthly_customer_metrics.KPI Net Revenue YoY %",
    "monthly_performance.KPI Forecast Accuracy": "monthly_customer_metrics.KPI Churn ROC-AUC",
    "monthly_performance.KPI EBITDA Attainment": "monthly_customer_metrics.KPI Campaign ROI",
    "monthly_performance.KPI EBITDA Margin": "monthly_customer_metrics.KPI Churn Probability",
    "monthly_performance.KPI Gross Margin": "monthly_customer_metrics.KPI Gross Margin Rate",
    "monthly_performance.KPI Budget Revenue": "monthly_customer_metrics.KPI Revenue Prior Year",
    "monthly_performance.KPI Budget EBITDA": "monthly_customer_metrics.KPI Revenue at Risk",
    "monthly_performance.KPI Operating Expense": "monthly_customer_metrics.KPI Active Customers",
    "monthly_performance.KPI Ending Cash": "monthly_customer_metrics.KPI Revenue at Risk",
    "monthly_performance.KPI Gross Profit": "monthly_customer_metrics.KPI Gross Margin",
    "monthly_performance.KPI Revenue PY": "monthly_customer_metrics.KPI Net Revenue PY",
    "monthly_performance.KPI EBITDA PY": "monthly_customer_metrics.KPI Predicted CLV Benchmark",
    "monthly_performance.KPI Cash Target": "monthly_customer_metrics.KPI Campaign Budget",
    "monthly_performance.KPI Headcount": "monthly_customer_metrics.KPI Customers",
    "monthly_performance.KPI CCC Days": "monthly_customer_metrics.KPI Recency Days",
    "monthly_performance.KPI Net Income": "monthly_customer_metrics.KPI New Customers",
    "monthly_performance.KPI Revenue": "monthly_customer_metrics.KPI Net Revenue",
    "monthly_performance.KPI EBITDA": "monthly_customer_metrics.KPI Predicted CLV",
    "department_performance.Dept Budget Revenue": "segment_summary.Segment Predicted CLV",
    "department_performance.Dept EBITDA Margin": "segment_summary.Segment Churn Risk",
    "department_performance.Dept Headcount": "segment_summary.Segment Customers",
    "department_performance.Dept Revenue": "segment_summary.Segment Revenue",
    "business_unit_performance.BU Gross Profit": "campaign_summary.Campaign Expected Margin",
    "business_unit_performance.BU Revenue": "campaign_summary.Campaign Budget",
    "scenario_summary.Scenario EBITDA": "model_comparison.Model PR-AUC",
    "scenario_summary.Scenario Revenue": "model_comparison.Model ROC-AUC",
    "P&L Stages.P&L Stage Value": "risk_bands.Risk Band Customers",
    "monthly_performance": "monthly_customer_metrics",
    "department_performance": "segment_summary",
    "business_unit_performance": "campaign_summary",
    "scenario_summary": "model_comparison",
    "P&L Stages": "risk_bands",
    "KPI Revenue Variance": "KPI Revenue YoY Change",
    "KPI Revenue YoY %": "KPI Net Revenue YoY %",
    "KPI Forecast Accuracy": "KPI Churn ROC-AUC",
    "KPI EBITDA Attainment": "KPI Campaign ROI",
    "KPI EBITDA Margin": "KPI Churn Probability",
    "KPI Gross Margin": "KPI Gross Margin Rate",
    "KPI Budget Revenue": "KPI Revenue Prior Year",
    "KPI Budget EBITDA": "KPI Revenue at Risk",
    "KPI Operating Expense": "KPI Active Customers",
    "KPI Ending Cash": "KPI Revenue at Risk",
    "KPI Gross Profit": "KPI Gross Margin",
    "KPI Revenue PY": "KPI Net Revenue PY",
    "KPI EBITDA PY": "KPI Predicted CLV Benchmark",
    "KPI Cash Target": "KPI Campaign Budget",
    "KPI Headcount": "KPI Customers",
    "KPI CCC Days": "KPI Recency Days",
    "KPI Net Income": "KPI New Customers",
    "KPI Revenue": "KPI Net Revenue",
    "KPI EBITDA": "KPI Predicted CLV",
    "Dept Budget Revenue": "Segment Predicted CLV",
    "Dept EBITDA Margin": "Segment Churn Risk",
    "Dept Headcount": "Segment Customers",
    "Dept Revenue": "Segment Revenue",
    "BU Gross Profit": "Campaign Expected Margin",
    "BU Revenue": "Campaign Budget",
    "Scenario EBITDA": "Model PR-AUC",
    "Scenario Revenue": "Model ROC-AUC",
    "P&L Stage Value": "Risk Band Customers",
    "Department": "RFM Segment",
    "Business Unit": "Recommended Action",
    "Scenario": "Model",
    "Stage": "Risk Band",
    "INTEGRATED FP&A ANALYTICS": "CUSTOMER INTELLIGENCE ANALYTICS",
    "Integrated FP&A Analytics": "Customer Intelligence Analytics",
    "Revenue & Margin": "Customer & Value Trends",
    "P&L Waterfall": "Risk Portfolio",
    "Budget vs Actual": "CLV & Revenue",
    "Rolling Forecast": "Churn & Retention",
    "Department Performance": "RFM Segmentation",
    "Business Unit Analysis": "Campaign Targeting",
    "Cash & Working Capital": "Cohort Analysis",
    "Operating Expense": "Model Performance & Governance",
    "Long-Range Trends": "Four-Year Trends",
    "Scenario Planning & Risk": "Model Comparison",
    "Revenue vs Budget": "Revenue vs Prior Year",
    "EBITDA vs Budget": "Predicted CLV vs Revenue at Risk",
    "Department Revenue vs Budget": "Segment Revenue vs Predicted CLV",
    "Selected Month P&L Flow": "Selected Month Risk Portfolio",
    "Gross & EBITDA Margins": "Margin & Churn Signals",
    "Ending Cash & Target Trend": "Revenue at Risk & Campaign Budget",
    "Historical & Forecast Revenue Trend": "Four-Year Revenue Trend",
    "Operating Expense and Net Income": "Active and New Customers",
    "Revenue by Business Unit": "Budget by Recommended Action",
    "Revenue Mix by Business Unit": "Campaign Budget Mix",
    "Revenue and Gross Profit by Business Unit": "Budget and Expected Margin by Action",
    "Revenue by Scenario": "ROC-AUC by Model",
    "Revenue Mix by Scenario": "Model Performance Mix",
    "Revenue and EBITDA by Scenario": "ROC-AUC and PR-AUC by Model",
    "OPERATING EXPENSE": "MODEL PERFORMANCE & GOVERNANCE",
    "SCENARIO PLANNING & RISK": "MODEL COMPARISON",
    "BUSINESS UNIT ANALYSIS": "CAMPAIGN TARGETING",
    "CASH & WORKING CAPITAL": "COHORT ANALYSIS",
    "DEPARTMENT PERFORMANCE": "RFM SEGMENTATION",
    "DEPARTMENT EBITDA MARGIN": "SEGMENT CHURN RISK",
    "DEPARTMENT REVENUE": "SEGMENT REVENUE",
    "DEPARTMENT BUDGET": "SEGMENT PREDICTED CLV",
    "EBITDA ATTAINMENT": "CAMPAIGN ROI",
    "FORECAST EBITDA": "PREDICTED CLV",
    "BUDGET EBITDA": "REVENUE AT RISK",
    "EBITDA MARGIN": "CHURN PROBABILITY",
    "ENDING CASH VALUE": "REVENUE AT RISK",
    "ENDING CASH": "REVENUE AT RISK",
    "GROSS PROFIT": "GROSS MARGIN",
    "BUDGET REVENUE": "REVENUE PRIOR YEAR",
    "CASH BUDGET": "CAMPAIGN BUDGET",
    "'OPERATING EXPENSE'": "'ACTIVE CUSTOMERS'",
    "'EBITDA'": "'PREDICTED CLV'",
    "'BUDGET'": "'PRIOR YEAR'",
}


PAGE_NAMES = [
    "1. Executive Overview",
    "2. Customer & Value Trends",
    "3. Risk Portfolio",
    "4. CLV & Revenue",
    "5. Churn & Retention",
    "6. RFM Segmentation",
    "7. Campaign Targeting",
    "8. Cohort Analysis",
    "9. Model Performance & Governance",
    "10. Four-Year Trends",
    "11. Model Comparison",
    "12. SHAP Explainability",
]


def replace_report_content(report_dir: Path) -> None:
    for path in report_dir.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        for old, new in sorted(
            REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True
        ):
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def clone_shap_page(report_dir: Path) -> None:
    pages_root = report_dir / "definition" / "pages"
    meta_path = pages_root / "pages.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    source_name = meta["pageOrder"][6]
    new_name = "ReportSection" + uuid.uuid5(
        uuid.NAMESPACE_URL, "customer-intelligence-shap-page"
    ).hex[:20]
    shutil.copytree(pages_root / source_name, pages_root / new_name)
    page_path = pages_root / new_name / "page.json"
    page = json.loads(page_path.read_text(encoding="utf-8"))
    page["name"] = new_name
    page["displayName"] = PAGE_NAMES[-1]
    page_path.write_text(
        json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shap_replacements = {
        "campaign_summary.Campaign Expected Margin": "shap_importance.SHAP Share",
        "campaign_summary.Campaign Budget": "shap_importance.SHAP Importance",
        "campaign_summary": "shap_importance",
        "Campaign Expected Margin": "SHAP Share",
        "Campaign Budget": "SHAP Importance",
        "Recommended Action": "Feature",
        "CAMPAIGN TARGETING": "SHAP EXPLAINABILITY",
        "Campaign Targeting": "SHAP Explainability",
        "Budget by Recommended Action": "SHAP Importance by Feature",
        "Campaign Budget Mix": "Global Importance Share",
        "Budget and Expected Margin by Action": "SHAP Magnitude and Share",
    }
    for path in (pages_root / new_name).rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        for old, new in sorted(
            shap_replacements.items(), key=lambda item: len(item[0]), reverse=True
        ):
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    meta["pageOrder"].append(new_name)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_page_names(report_dir: Path) -> None:
    pages_root = report_dir / "definition" / "pages"
    meta = json.loads((pages_root / "pages.json").read_text(encoding="utf-8"))
    for display_name, page_name in zip(PAGE_NAMES, meta["pageOrder"], strict=True):
        page_path = pages_root / page_name / "page.json"
        page = json.loads(page_path.read_text(encoding="utf-8"))
        page["displayName"] = display_name
        page_path.write_text(
            json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def update_theme_and_metadata(report_dir: Path, model_dir: Path) -> None:
    resources = report_dir / "StaticResources" / "RegisteredResources"
    theme_files = list(resources.glob("*.json"))
    if not theme_files:
        raise FileNotFoundError("Power BI theme resource not found.")
    old_theme = theme_files[0]
    new_theme_name = "CustomerIntelligenceDark-92a7c4d1.json"
    new_theme = old_theme.with_name(new_theme_name)
    theme = json.loads(old_theme.read_text(encoding="utf-8"))
    theme["name"] = "Customer Intelligence Dark"
    theme["dataColors"] = [
        "#36D7B7",
        "#4CA6FF",
        "#A78BFA",
        "#FFB547",
        "#FF647C",
        "#67E8F9",
    ]
    theme["background"] = "#07111F"
    theme["foreground"] = "#F4F7FB"
    theme["tableAccent"] = "#36D7B7"
    new_theme.write_text(
        json.dumps(theme, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if old_theme != new_theme:
        old_theme.unlink()

    report_json_path = report_dir / "definition" / "report.json"
    report_json = json.loads(report_json_path.read_text(encoding="utf-8"))
    report_json["themeCollection"]["customTheme"]["name"] = new_theme_name
    report_json["resourcePackages"][0]["items"][0]["name"] = new_theme_name
    report_json["resourcePackages"][0]["items"][0]["path"] = new_theme_name
    report_json_path.write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for platform_path, logical_seed in (
        (report_dir / ".platform", "customer-intelligence-report"),
        (model_dir / ".platform", "customer-intelligence-model"),
    ):
        platform = json.loads(platform_path.read_text(encoding="utf-8"))
        platform["metadata"]["displayName"] = "Customer Intelligence Analytics"
        platform["config"]["logicalId"] = str(
            uuid.uuid5(uuid.NAMESPACE_URL, logical_seed)
        )
        platform_path.write_text(
            json.dumps(platform, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def write_measure_catalog() -> None:
    frames = build_model_frames()
    lines = [
        "// Customer Intelligence, CLV & Churn Prediction Platform",
        "// Reusable DAX measure catalog",
        "",
    ]
    for table_name, (_frame, measures) in frames.items():
        if not measures:
            continue
        lines.append(f"// [{table_name}]")
        for measure in measures:
            lines.append(f"{measure['name']} = {measure['expression']}")
        lines.append("")
    (POWERBI_DIR / "Customer_Intelligence_Measures.dax").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def validate(report_dir: Path, model_dir: Path) -> dict:
    errors: list[str] = []
    json_paths = (
        list(report_dir.rglob("*.json"))
        + [
            report_dir / ".platform",
            report_dir / "definition.pbir",
            model_dir / ".platform",
            model_dir / "definition.pbism",
            model_dir / "model.bim",
            PBIP_PATH,
        ]
    )
    for path in json_paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            errors.append(f"Invalid JSON: {path.relative_to(OUTPUT_ROOT)}: {error}")

    pages_root = report_dir / "definition" / "pages"
    page_files = list(pages_root.glob("*/page.json"))
    if len(page_files) != 12:
        errors.append(f"Expected 12 pages, found {len(page_files)}")
    for page_file in page_files:
        page = json.loads(page_file.read_text(encoding="utf-8"))
        if page.get("width") != 1280 or page.get("height") != 720:
            errors.append(f"Non-HD page: {page.get('displayName')}")
        visual_count = len(list(page_file.parent.glob("visuals/*/visual.json")))
        if visual_count < 4:
            errors.append(f"Too few visuals: {page.get('displayName')}")

    model = json.loads((model_dir / "model.bim").read_text(encoding="utf-8"))
    table_names = {table["name"] for table in model["model"]["tables"]}
    entities: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            entity = value.get("Entity")
            if isinstance(entity, str):
                entities.add(entity)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for visual_path in report_dir.rglob("visual.json"):
        walk(json.loads(visual_path.read_text(encoding="utf-8")))
    unknown = sorted(entities - table_names)
    if unknown:
        errors.append(f"Unknown visual entities: {unknown}")
    report_text = "\n".join(
        path.read_text(encoding="utf-8") for path in report_dir.rglob("*.json")
    )
    legacy_tokens = [
        "monthly_performance",
        "department_performance",
        "business_unit_performance",
        "scenario_summary",
        "INTEGRATED FP&A",
    ]
    for token in legacy_tokens:
        if token in report_text:
            errors.append(f"Legacy token remains: {token}")
    result = {
        "project": PROJECT_NAME,
        "pages": len(page_files),
        "visuals": len(list(report_dir.rglob("visual.json"))),
        "tables": sorted(table_names),
        "relationships": len(model["model"].get("relationships", [])),
        "valid": not errors,
        "errors": errors,
    }
    (OUTPUT_ROOT / "pbip_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def build_pbip() -> Path:
    if not TEMPLATE_ROOT.exists():
        raise FileNotFoundError(f"PBIP build template not found: {TEMPLATE_ROOT}")
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    report_dir = OUTPUT_ROOT / REPORT_NAME
    model_dir = OUTPUT_ROOT / MODEL_NAME
    shutil.copytree(
        TEMPLATE_ROOT / "Integrated_FPA_Planning_Analytics.Report", report_dir
    )
    shutil.copytree(
        TEMPLATE_ROOT / "Integrated_FPA_Planning_Analytics.SemanticModel",
        model_dir,
    )

    definition = json.loads(
        (report_dir / "definition.pbir").read_text(encoding="utf-8")
    )
    definition["datasetReference"]["byPath"]["path"] = f"../{MODEL_NAME}"
    (report_dir / "definition.pbir").write_text(
        json.dumps(definition, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pbip = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": REPORT_NAME}}],
        "settings": {"enableAutoRecovery": True},
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    PBIP_PATH.write_text(
        json.dumps(pbip, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    build_semantic_model(model_dir)
    replace_report_content(report_dir)
    clone_shap_page(report_dir)
    update_page_names(report_dir)
    update_theme_and_metadata(report_dir, model_dir)
    write_measure_catalog()

    readme = """Customer Intelligence, CLV & Churn Prediction - Power BI Project

Open Customer_Intelligence_Analytics.pbip in a current version of Power BI Desktop.
The semantic model embeds the synthetic portfolio data as Base64 Power Query partitions,
so no local CSV path remapping is required.

Report pages:
1. Executive Overview
2. Customer & Value Trends
3. Risk Portfolio
4. CLV & Revenue
5. Churn & Retention
6. RFM Segmentation
7. Campaign Targeting
8. Cohort Analysis
9. Model Performance & Governance
10. Four-Year Trends
11. Model Comparison
12. SHAP Explainability

The package includes 10 semantic-model tables, reusable DAX measures and a dark
1280 x 720 report canvas. All data is synthetic and contains no real PII.
"""
    (OUTPUT_ROOT / "README.txt").write_text(readme, encoding="utf-8")
    validation = validate(report_dir, model_dir)
    if not validation["valid"]:
        raise RuntimeError(json.dumps(validation, ensure_ascii=False, indent=2))
    archive_path = POWERBI_DIR / "Customer_Intelligence_PBIP.zip"
    if archive_path.exists():
        archive_path.unlink()
    shutil.make_archive(
        str(archive_path.with_suffix("")),
        "zip",
        root_dir=OUTPUT_ROOT,
    )
    return PBIP_PATH


if __name__ == "__main__":
    print(build_pbip())
