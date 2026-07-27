from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import PercentFormatter

from .config import CONFIG, PROJECT_ROOT

BG = "#07111F"
PANEL = "#101C2D"
PANEL_ALT = "#142238"
TEXT = "#F4F7FB"
MUTED = "#9AA9BE"
GRID = "#26364D"
TEAL = "#36D7B7"
BLUE = "#4CA6FF"
PURPLE = "#A78BFA"
AMBER = "#FFB547"
RED = "#FF647C"
CYAN = "#67E8F9"


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(CONFIG.processed_dir / f"{name}.csv")


def _money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"TRY {value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"TRY {value / 1_000:.0f}K"
    return f"TRY {value:,.0f}"


def _style_figure(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.patch.set_facecolor(BG)
    fig.text(0.035, 0.955, title, color=TEXT, fontsize=29, fontweight="bold", va="top")
    fig.text(0.035, 0.918, subtitle, color=MUTED, fontsize=12, va="top")
    fig.text(
        0.965,
        0.955,
        "NOVARETAIL GROUP  |  CUSTOMER INTELLIGENCE",
        color=TEAL,
        fontsize=10,
        ha="right",
        va="top",
        fontweight="bold",
    )
    fig.text(
        0.035,
        0.022,
        "Synthetic portfolio data  |  Production snapshot: 31 Dec 2025  |  Murat Miraç Gedik",
        color=MUTED,
        fontsize=8.5,
    )


def _panel(ax: plt.Axes, title: str | None = None) -> None:
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(color=GRID, alpha=0.48, linewidth=0.65)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=TEXT, fontsize=12, fontweight="bold", loc="left", pad=12)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, facecolor=BG, bbox_inches=None)
    plt.close(fig)


def _kpi_card(
    fig: plt.Figure,
    left: float,
    top: float,
    width: float,
    height: float,
    label: str,
    value: str,
    detail: str,
    color: str,
) -> None:
    box = FancyBboxPatch(
        (left, top - height),
        width,
        height,
        transform=fig.transFigure,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        facecolor=PANEL,
        edgecolor=GRID,
        linewidth=1,
    )
    fig.patches.append(box)
    fig.text(left + 0.015, top - 0.035, label.upper(), color=MUTED, fontsize=8.5)
    fig.text(
        left + 0.015,
        top - 0.085,
        value,
        color=TEXT,
        fontsize=20,
        fontweight="bold",
    )
    fig.text(left + 0.015, top - height + 0.026, detail, color=color, fontsize=8.5)
    fig.add_artist(
        plt.Line2D(
            [left, left],
            [top - height + 0.012, top - 0.012],
            transform=fig.transFigure,
            color=color,
            linewidth=3,
        )
    )


def executive_overview() -> None:
    kpis = _load("executive_kpis").set_index("kpi")["value"]
    monthly = _load("monthly_customer_metrics")
    monthly["month"] = pd.to_datetime(monthly["month"])
    segments = _load("segment_summary")
    customer_360 = _load("customer_360")
    campaign = _load("campaign_summary")

    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Executive Customer Intelligence Overview",
        "Value, retention risk and next-best-action performance in one decision surface",
    )
    cards = [
        (
            "Customers",
            f"{int(kpis['Customers']):,}",
            f"{int(kpis['Active Customers 12M']):,} active in last 12 months",
            BLUE,
        ),
        (
            "Revenue 12M",
            _money(kpis["Net Revenue 12M"]),
            f"{kpis['Gross Margin 12M']/kpis['Net Revenue 12M']:.1%} gross margin rate",
            TEAL,
        ),
        (
            "Predicted CLV",
            _money(kpis["Predicted CLV 12M"]),
            "Next 12-month gross-margin contribution",
            PURPLE,
        ),
        (
            "High / Critical Risk",
            f"{int(kpis['High/Critical Risk Customers']):,}",
            f"{_money(kpis['Revenue at Risk'])} revenue at risk",
            RED,
        ),
        (
            "Campaign Upside",
            _money(kpis["Expected Incremental Margin"]),
            f"{_money(kpis['Campaign Budget Allocated'])} allocated budget",
            AMBER,
        ),
    ]
    card_width = 0.177
    for index, card in enumerate(cards):
        _kpi_card(fig, 0.035 + index * 0.19, 0.875, card_width, 0.145, *card)

    grid = fig.add_gridspec(
        2,
        3,
        left=0.035,
        right=0.965,
        bottom=0.07,
        top=0.68,
        width_ratios=[1.55, 1.0, 1.0],
        hspace=0.28,
        wspace=0.20,
    )
    ax = fig.add_subplot(grid[0, :2])
    _panel(ax, "Monthly Net Revenue")
    ax.plot(monthly["month"], monthly["net_revenue"] / 1e6, color=BLUE, linewidth=2.5)
    ax.fill_between(
        monthly["month"], monthly["net_revenue"] / 1e6, color=BLUE, alpha=0.12
    )
    ax.set_ylabel("TRY millions")
    ax.set_xlabel("")

    ax = fig.add_subplot(grid[0, 2])
    _panel(ax, "Customer Risk Mix")
    risk_counts = (
        customer_360["risk_band"]
        .value_counts()
        .reindex(["Low", "Medium", "High", "Critical"])
        .fillna(0)
    )
    colors = [TEAL, BLUE, AMBER, RED]
    wedges, _ = ax.pie(
        risk_counts,
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.36, "edgecolor": BG},
    )
    ax.text(
        0,
        0.08,
        f"{customer_360['churn_probability'].mean():.1%}",
        color=TEXT,
        fontsize=18,
        fontweight="bold",
        ha="center",
    )
    ax.text(0, -0.15, "avg risk", color=MUTED, fontsize=9, ha="center")
    ax.legend(
        wedges,
        [f"{label}  {int(value):,}" for label, value in risk_counts.items()],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.16),
        frameon=False,
        labelcolor=MUTED,
        fontsize=8,
        ncol=2,
    )

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "Predicted CLV by RFM Segment")
    top_segments = segments.nlargest(7, "predicted_clv_12m").sort_values(
        "predicted_clv_12m"
    )
    ax.barh(
        top_segments["rfm_segment"],
        top_segments["predicted_clv_12m"] / 1e6,
        color=PURPLE,
    )
    ax.set_xlabel("TRY millions")

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "Campaign Portfolio Economics")
    campaign_plot = campaign[campaign["recommended_action"] != "Suppress"].sort_values(
        "expected_incremental_margin"
    )
    ax.barh(
        campaign_plot["recommended_action"],
        campaign_plot["expected_incremental_margin"] / 1000,
        color=TEAL,
        label="Incremental margin",
    )
    ax.set_xlabel("TRY thousands")

    ax = fig.add_subplot(grid[1, 2])
    _panel(ax, "Decision Signals")
    ax.axis("off")
    signals = [
        ("MODEL", f"ROC-AUC  {kpis['Churn ROC-AUC']:.3f}", BLUE),
        ("RETENTION", f"M3  {kpis['M3 Cohort Retention']:.1%}", TEAL),
        ("LIFT", f"Top 10%  {kpis['Lift at Top 10%']:.2f}x", AMBER),
        (
            "ACTION",
            f"{int(customer_360['selected_for_campaign'].sum()):,} prioritized",
            PURPLE,
        ),
    ]
    for index, (label, value, color) in enumerate(signals):
        y = 0.86 - index * 0.23
        ax.text(0.02, y, label, color=color, fontsize=8.5, fontweight="bold")
        ax.text(0.02, y - 0.09, value, color=TEXT, fontsize=15, fontweight="bold")
        ax.plot([0.02, 0.98], [y - 0.16, y - 0.16], color=GRID, linewidth=0.8)
    _save(fig, CONFIG.image_dir / "executive-overview.png")


def customer_360_view() -> None:
    frame = _load("customer_360")
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Customer 360: Value, Risk and Action",
        "A unified customer-level view that connects behavior, future value and campaign treatment",
    )
    grid = fig.add_gridspec(
        2,
        3,
        left=0.04,
        right=0.965,
        bottom=0.07,
        top=0.87,
        width_ratios=[1.45, 1.0, 1.0],
        height_ratios=[1.2, 1.0],
        wspace=0.20,
        hspace=0.24,
    )
    ax = fig.add_subplot(grid[:, 0])
    _panel(ax, "Value-Risk Portfolio")
    color_map = {"Low": TEAL, "Medium": BLUE, "High": AMBER, "Critical": RED}
    sample = frame.sample(n=min(2500, len(frame)), random_state=11)
    for risk, group in sample.groupby("risk_band"):
        ax.scatter(
            group["predicted_clv_12m"],
            group["churn_probability"],
            s=np.clip(group["monetary_12m"] / 700, 8, 90),
            alpha=0.48,
            color=color_map.get(risk, MUTED),
            label=risk,
            linewidths=0,
        )
    ax.axhline(0.55, color=AMBER, linestyle="--", linewidth=1)
    ax.axvline(frame["predicted_clv_12m"].quantile(0.80), color=PURPLE, linestyle="--")
    ax.set_xlabel("Predicted 12M CLV (TRY)")
    ax.set_ylabel("Churn probability")
    ax.legend(frameon=False, labelcolor=MUTED, ncol=4, loc="upper center")

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "Risk by Region")
    region = frame.groupby("region", as_index=False).agg(
        risk=("churn_probability", "mean")
    )
    region = region.sort_values("risk")
    ax.barh(region["region"], region["risk"], color=BLUE)
    ax.set_xlim(0, max(0.75, region["risk"].max() * 1.12))
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")

    ax = fig.add_subplot(grid[0, 2])
    _panel(ax, "CLV Band Mix")
    band = (
        frame["clv_band"]
        .value_counts()
        .reindex(["Low", "Developing", "High", "Strategic"])
        .fillna(0)
    )
    ax.bar(band.index, band.values, color=[MUTED, BLUE, PURPLE, TEAL])
    ax.tick_params(axis="x", rotation=20)
    ax.set_ylabel("Customers")

    ax = fig.add_subplot(grid[1, 1:])
    _panel(ax, "Top Prioritized Customer Actions")
    ax.axis("off")
    table = (
        frame[frame["selected_for_campaign"] == 1]
        .nlargest(8, "expected_incremental_margin")[
            [
                "customer_id",
                "rfm_segment",
                "risk_band",
                "clv_band",
                "recommended_action",
                "expected_incremental_margin",
            ]
        ]
        .copy()
    )
    table["expected_incremental_margin"] = table[
        "expected_incremental_margin"
    ].map(lambda value: f"TRY {value:,.0f}")
    rendered = ax.table(
        cellText=table.values,
        colLabels=["Customer", "RFM Segment", "Risk", "CLV", "Next Action", "Expected Margin"],
        loc="center",
        cellLoc="left",
        colLoc="left",
        bbox=[0, 0.02, 1, 0.94],
    )
    rendered.auto_set_font_size(False)
    rendered.set_fontsize(8.4)
    for (row, _column), cell in rendered.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_facecolor(PANEL_ALT if row else "#1B2D47")
        cell.get_text().set_color(TEXT if row else TEAL)
    _save(fig, CONFIG.image_dir / "customer-360.png")


def rfm_segmentation() -> None:
    summary = _load("segment_summary")
    rfm = _load("rfm_scores")
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "RFM Segmentation",
        "Recency, frequency and monetary behavior translated into differentiated customer strategies",
    )
    grid = fig.add_gridspec(
        2, 2, left=0.075, right=0.965, bottom=0.07, top=0.87, hspace=0.25, wspace=0.18
    )
    ax = fig.add_subplot(grid[:, 0])
    _panel(ax, "Segment Size and Revenue Share")
    ordered = summary.sort_values("customers")
    ax.barh(ordered["rfm_segment"], ordered["customers"], color=BLUE, alpha=0.85)
    for y, (_, row) in enumerate(ordered.iterrows()):
        ax.text(
            row["customers"] + 12,
            y,
            f"{row['revenue_share']:.1%} rev.",
            color=MUTED,
            fontsize=8,
            va="center",
        )
    ax.set_xlabel("Customers")

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "RFM Value Matrix")
    matrix = (
        rfm.pivot_table(
            index="recency_score",
            columns="frequency_score",
            values="monetary",
            aggfunc="mean",
        )
        .sort_index(ascending=False)
        .fillna(0)
    )
    sns.heatmap(
        matrix,
        ax=ax,
        cmap=sns.color_palette(["#142238", "#275B88", "#3B82F6", "#36D7B7"], as_cmap=True),
        cbar_kws={"label": "Average monetary value"},
        annot=False,
        linewidths=0.5,
        linecolor=BG,
    )
    ax.set_xlabel("Frequency score")
    ax.set_ylabel("Recency score")
    ax.collections[0].colorbar.ax.tick_params(colors=MUTED)

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "Segment Churn Risk vs Predicted CLV")
    ax.scatter(
        summary["average_churn_probability"],
        summary["predicted_clv_12m"] / 1e6,
        s=np.clip(summary["customers"] * 0.55, 70, 700),
        c=summary["average_churn_probability"],
        cmap="RdYlGn_r",
        alpha=0.82,
        edgecolors=BG,
        linewidths=1,
    )
    for row in summary.itertuples():
        ax.annotate(
            row.rfm_segment,
            (row.average_churn_probability, row.predicted_clv_12m / 1e6),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=7.5,
            color=MUTED,
        )
    ax.set_xlabel("Average churn probability")
    ax.set_ylabel("Predicted CLV (TRY millions)")
    _save(fig, CONFIG.image_dir / "rfm-segmentation.png")


def cohort_retention() -> None:
    matrix = _load("cohort_retention_matrix").tail(24)
    long = _load("cohort_retention_long")
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Cohort Retention Analysis",
        "Acquisition-month cohorts reveal the durability of customer relationships over time",
    )
    grid = fig.add_gridspec(
        2, 3, left=0.04, right=0.965, bottom=0.07, top=0.87, hspace=0.25, wspace=0.20
    )
    ax = fig.add_subplot(grid[:, :2])
    _panel(ax, "Monthly Retention Heatmap")
    heat = matrix.set_index("cohort_month")
    columns = [column for column in heat.columns if int(column[1:]) <= 12]
    sns.heatmap(
        heat[columns],
        ax=ax,
        cmap=sns.color_palette(["#101C2D", "#24557E", "#3B82F6", "#36D7B7"], as_cmap=True),
        vmin=0,
        vmax=1,
        linewidths=0.3,
        linecolor=BG,
        cbar_kws={"label": "Retention rate"},
    )
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Acquisition cohort")
    ax.collections[0].colorbar.ax.tick_params(colors=MUTED)
    ax.collections[0].colorbar.ax.yaxis.set_major_formatter(PercentFormatter(1.0))

    ax = fig.add_subplot(grid[0, 2])
    _panel(ax, "Retention Curve: Recent Cohorts")
    selected_cohorts = sorted(long["cohort_month"].unique())[-12::3]
    for color, cohort in zip([TEAL, BLUE, PURPLE, AMBER], selected_cohorts, strict=False):
        subset = long[(long["cohort_month"] == cohort) & (long["cohort_index"] <= 12)]
        ax.plot(
            subset["cohort_index"],
            subset["retention_rate"],
            marker="o",
            linewidth=2,
            color=color,
            label=cohort,
        )
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlabel("Month index")
    ax.set_ylabel("Retention")
    ax.legend(frameon=False, labelcolor=MUTED, fontsize=8)

    ax = fig.add_subplot(grid[1, 2])
    _panel(ax, "Retention Checkpoints")
    checkpoints = (
        long[long["cohort_index"].isin([1, 3, 6, 12])]
        .groupby("cohort_index", as_index=False)["retention_rate"]
        .mean()
    )
    bars = ax.bar(
        checkpoints["cohort_index"].astype(str),
        checkpoints["retention_rate"],
        color=[BLUE, TEAL, PURPLE, AMBER][: len(checkpoints)],
    )
    ax.bar_label(bars, labels=[f"{v:.1%}" for v in checkpoints["retention_rate"]], color=TEXT)
    ax.set_xlabel("Month")
    ax.set_ylabel("Average retention")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    _save(fig, CONFIG.image_dir / "cohort-retention.png")


def clv_analysis() -> None:
    customer = _load("customer_360")
    test = _load("clv_test_predictions")
    comparison = _load("clv_model_comparison")
    segments = _load("segment_summary")
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Customer Lifetime Value Analytics",
        "Future 12-month gross-margin contribution estimated with time-based validation",
    )
    grid = fig.add_gridspec(
        2, 3, left=0.04, right=0.965, bottom=0.07, top=0.87, hspace=0.25, wspace=0.20
    )
    ax = fig.add_subplot(grid[0, :2])
    _panel(ax, "Actual vs Predicted CLV: Holdout Period")
    sample = test.sample(n=min(2500, len(test)), random_state=13)
    ax.scatter(
        sample["future_gross_margin"],
        sample["predicted_clv_12m"],
        s=12,
        alpha=0.28,
        color=PURPLE,
        linewidths=0,
    )
    max_value = np.quantile(
        np.concatenate(
            [sample["future_gross_margin"], sample["predicted_clv_12m"]]
        ),
        0.98,
    )
    ax.plot([0, max_value], [0, max_value], linestyle="--", color=TEAL)
    ax.set_xlim(0, max_value)
    ax.set_ylim(0, max_value)
    ax.set_xlabel("Actual future gross margin (TRY)")
    ax.set_ylabel("Predicted CLV (TRY)")

    ax = fig.add_subplot(grid[0, 2])
    _panel(ax, "CLV Model Comparison")
    ordered = comparison.sort_values("r2")
    ax.barh(ordered["model"], ordered["r2"], color=[MUTED, BLUE, TEAL])
    ax.set_xlabel("R²")
    ax.set_xlim(0, max(0.7, ordered["r2"].max() * 1.15))

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "CLV Distribution by Band")
    band_order = ["Low", "Developing", "High", "Strategic"]
    sns.violinplot(
        data=customer,
        x="clv_band",
        y="predicted_clv_12m",
        hue="clv_band",
        order=band_order,
        palette={
            "Low": MUTED,
            "Developing": BLUE,
            "High": PURPLE,
            "Strategic": TEAL,
        },
        inner="quartile",
        cut=0,
        ax=ax,
        legend=False,
    )
    ax.tick_params(axis="x", rotation=15)
    ax.set_xlabel("")
    ax.set_ylabel("Predicted CLV (TRY)")

    ax = fig.add_subplot(grid[1, 1:])
    _panel(ax, "CLV Concentration by Segment")
    top = segments.nlargest(8, "predicted_clv_12m").sort_values("predicted_clv_12m")
    ax.barh(top["rfm_segment"], top["predicted_clv_12m"] / 1e6, color=TEAL)
    ax.set_xlabel("Predicted CLV (TRY millions)")
    _save(fig, CONFIG.image_dir / "clv-analysis.png")


def churn_risk() -> None:
    customer = _load("customer_360")
    calibration = _load("churn_calibration")
    lift = _load("churn_lift_curve")
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Churn Risk Intelligence",
        "Calibrated 90-day churn probabilities translated into actionable risk tiers",
    )
    grid = fig.add_gridspec(
        2, 3, left=0.04, right=0.965, bottom=0.07, top=0.87, hspace=0.25, wspace=0.20
    )
    ax = fig.add_subplot(grid[:, 0])
    _panel(ax, "Churn Risk by Recency and Engagement")
    sample = customer.sample(n=min(2800, len(customer)), random_state=17)
    scatter = ax.scatter(
        sample["recency_days"],
        sample["sessions_90d"],
        c=sample["churn_probability"],
        cmap=LinearSegmentedColormap.from_list(
            "risk_scale", ["#36D7B7", "#FFB547", "#FF647C"]
        ),
        s=np.clip(sample["predicted_clv_12m"] / 80, 8, 80),
        alpha=0.52,
        linewidths=0,
    )
    cbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label("Churn probability", color=MUTED)
    cbar.ax.tick_params(colors=MUTED)
    ax.set_xlabel("Recency days")
    ax.set_ylabel("Sessions in last 90 days")

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "Probability Calibration")
    ax.plot(
        calibration["mean_predicted_probability"],
        calibration["observed_churn_rate"],
        color=BLUE,
        marker="o",
        linewidth=2.2,
    )
    ax.plot([0, 1], [0, 1], color=MUTED, linestyle="--")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed churn rate")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax = fig.add_subplot(grid[0, 2])
    _panel(ax, "Cumulative Gain")
    ax.plot(lift["population_pct"], lift["cumulative_gain"], color=TEAL, linewidth=2.5)
    ax.plot([0, 1], [0, 1], color=MUTED, linestyle="--")
    ax.fill_between(
        lift["population_pct"],
        lift["population_pct"],
        lift["cumulative_gain"],
        color=TEAL,
        alpha=0.12,
    )
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlabel("Population targeted")
    ax.set_ylabel("Churners captured")

    ax = fig.add_subplot(grid[1, 1:])
    _panel(ax, "Value at Risk by Risk Band")
    risk = customer.groupby("risk_band", as_index=False).agg(
        customers=("customer_id", "nunique"),
        revenue=("monetary_12m", "sum"),
        clv=("predicted_clv_12m", "sum"),
    )
    order = ["Low", "Medium", "High", "Critical"]
    risk["risk_band"] = pd.Categorical(risk["risk_band"], categories=order, ordered=True)
    risk = risk.sort_values("risk_band")
    x = np.arange(len(risk))
    ax.bar(x - 0.18, risk["revenue"] / 1e6, width=0.36, color=BLUE, label="Revenue 12M")
    ax.bar(x + 0.18, risk["clv"] / 1e6, width=0.36, color=PURPLE, label="Predicted CLV")
    ax.set_xticks(x, risk["risk_band"])
    ax.set_ylabel("TRY millions")
    ax.legend(frameon=False, labelcolor=MUTED)
    _save(fig, CONFIG.image_dir / "churn-risk.png")


def model_performance() -> None:
    churn = _load("churn_model_comparison")
    clv = _load("clv_model_comparison")
    drift = _load("drift_monitoring")
    fairness = _load("fairness_audit")
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Model Performance & Governance",
        "Accuracy, calibration, stability and group diagnostics monitored as independent quality gates",
    )
    grid = fig.add_gridspec(
        2, 2, left=0.04, right=0.965, bottom=0.07, top=0.87, hspace=0.25, wspace=0.18
    )
    ax = fig.add_subplot(grid[0, 0])
    _panel(ax, "Churn Model Comparison")
    base = churn[~churn["model"].str.contains("calibrated")].copy()
    x = np.arange(len(base))
    ax.bar(x - 0.17, base["roc_auc"], 0.34, color=BLUE, label="ROC-AUC")
    ax.bar(x + 0.17, base["pr_auc"], 0.34, color=TEAL, label="PR-AUC")
    ax.set_xticks(x, [name.replace("Histogram ", "Hist. ") for name in base["model"]])
    ax.tick_params(axis="x", rotation=12)
    ax.set_ylim(0.75, 0.95)
    ax.legend(frameon=False, labelcolor=MUTED)

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, "CLV Model Error vs Explanatory Power")
    scatter = ax.scatter(
        clv["mae"],
        clv["r2"],
        s=220,
        c=[TEAL, BLUE, MUTED],
        edgecolors=BG,
    )
    for row in clv.itertuples():
        ax.annotate(
            row.model,
            (row.mae, row.r2),
            xytext=(6, 5),
            textcoords="offset points",
            color=MUTED,
            fontsize=8,
        )
    ax.set_xlabel("MAE (TRY)")
    ax.set_ylabel("R²")
    _ = scatter

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "Feature Stability (PSI)")
    top = drift.head(10).sort_values("psi")
    colors = [TEAL if status == "Stable" else AMBER if status == "Watch" else RED for status in top["status"]]
    ax.barh(top["feature"], top["psi"], color=colors)
    ax.axvline(0.10, color=AMBER, linestyle="--", linewidth=1)
    ax.axvline(0.25, color=RED, linestyle="--", linewidth=1)
    ax.set_xlabel("Population Stability Index")

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "Fairness Audit: True Positive Rate")
    audit = fairness[fairness["audit_attribute"] == "region"].sort_values(
        "true_positive_rate"
    )
    ax.barh(audit["audit_group"], audit["true_positive_rate"], color=PURPLE)
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlim(0, 1)
    ax.set_xlabel("True positive rate")
    _save(fig, CONFIG.image_dir / "model-performance.png")


def shap_explainability() -> None:
    global_importance = _load("shap_global_importance")
    local = _load("shap_local_explanations")
    customer = _load("customer_360")
    top_customer = customer.nlargest(1, "churn_probability").iloc[0]["customer_id"]
    local_customer = local[local["customer_id"] == top_customer].sort_values(
        "shap_value"
    )
    if local_customer.empty:
        top_customer = local.iloc[0]["customer_id"]
        local_customer = local[local["customer_id"] == top_customer].sort_values(
            "shap_value"
        )

    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "SHAP Explainability",
        "Global and customer-level explanations make churn scores transparent and reviewable",
    )
    grid = fig.add_gridspec(
        2, 2, left=0.04, right=0.965, bottom=0.07, top=0.87, hspace=0.25, wspace=0.20
    )
    ax = fig.add_subplot(grid[:, 0])
    _panel(ax, "Global Churn Drivers")
    top = global_importance.head(12).sort_values("mean_abs_shap")
    ax.barh(top["feature"], top["mean_abs_shap"], color=PURPLE)
    ax.set_xlabel("Mean |SHAP value|")

    ax = fig.add_subplot(grid[0, 1])
    _panel(ax, f"Local Explanation: {top_customer}")
    colors = [RED if value > 0 else TEAL for value in local_customer["shap_value"]]
    ax.barh(local_customer["feature"], local_customer["shap_value"], color=colors)
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.set_xlabel("Contribution to churn probability")

    ax = fig.add_subplot(grid[1, 1])
    _panel(ax, "Explanation Contract")
    ax.axis("off")
    statements = [
        ("01", "Point-in-time features", "Only information available at the scoring date is used."),
        ("02", "Additive attribution", "SHAP contributions reconcile exactly to the model output."),
        ("03", "Behavior-first design", "Protected attributes are excluded from model features."),
        ("04", "Human review", "Campaign actions remain recommendations, not automatic decisions."),
    ]
    for index, (number, heading, body) in enumerate(statements):
        y = 0.88 - index * 0.22
        ax.text(0.02, y, number, color=TEAL, fontsize=11, fontweight="bold")
        ax.text(0.10, y, heading, color=TEXT, fontsize=12, fontweight="bold")
        ax.text(0.10, y - 0.075, body, color=MUTED, fontsize=9)
        ax.plot([0.02, 0.98], [y - 0.14, y - 0.14], color=GRID, linewidth=0.8)
    _save(fig, CONFIG.image_dir / "shap-explainability.png")


def campaign_targeting() -> None:
    summary = _load("campaign_summary")
    targets = _load("campaign_targets")
    selected = targets[targets["selected_for_campaign"] == 1]
    plot = summary[summary["recommended_action"] != "Suppress"].copy()
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Campaign Targeting & Budget Optimization",
        "Next-best-action recommendations ranked by expected incremental margin and business priority",
    )
    grid = fig.add_gridspec(
        2, 3, left=0.04, right=0.965, bottom=0.07, top=0.87, hspace=0.25, wspace=0.20
    )
    ax = fig.add_subplot(grid[0, :2])
    _panel(ax, "Budget vs Expected Incremental Margin")
    x = np.arange(len(plot))
    ax.bar(
        x - 0.18,
        plot["allocated_budget"] / 1000,
        0.36,
        color=BLUE,
        label="Allocated budget",
    )
    ax.bar(
        x + 0.18,
        plot["expected_incremental_margin"] / 1000,
        0.36,
        color=TEAL,
        label="Expected incremental margin",
    )
    ax.set_xticks(x, plot["recommended_action"])
    ax.tick_params(axis="x", rotation=12)
    ax.set_ylabel("TRY thousands")
    ax.legend(frameon=False, labelcolor=MUTED)

    ax = fig.add_subplot(grid[0, 2])
    _panel(ax, "Selected Customer Mix")
    counts = selected["recommended_action"].value_counts()
    wedges, _ = ax.pie(
        counts,
        colors=[PURPLE, BLUE, TEAL, AMBER, CYAN, RED][: len(counts)],
        startangle=90,
        wedgeprops={"width": 0.35, "edgecolor": BG},
    )
    ax.text(0, 0.05, f"{len(selected):,}", color=TEXT, fontsize=19, fontweight="bold", ha="center")
    ax.text(0, -0.15, "targets", color=MUTED, fontsize=9, ha="center")
    ax.legend(
        wedges,
        counts.index,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.20),
        frameon=False,
        labelcolor=MUTED,
        fontsize=7.5,
        ncol=2,
    )

    ax = fig.add_subplot(grid[1, 0])
    _panel(ax, "Expected ROI by Action")
    roi = plot.sort_values("average_expected_roi")
    colors = [TEAL if value >= 1 else AMBER for value in roi["average_expected_roi"]]
    ax.barh(roi["recommended_action"], roi["average_expected_roi"], color=colors)
    ax.axvline(1, color=MUTED, linestyle="--")
    ax.set_xlabel("Expected ROI multiple")

    ax = fig.add_subplot(grid[1, 1:])
    _panel(ax, "Priority Portfolio")
    portfolio = (
        selected.groupby(["campaign_priority", "recommended_action"], as_index=False)
        .agg(
            customers=("customer_id", "nunique"),
            margin=("expected_incremental_margin", "sum"),
        )
    )
    pivot = portfolio.pivot(
        index="recommended_action", columns="campaign_priority", values="customers"
    ).fillna(0)
    priority_order = [
        column for column in ["Low", "Medium", "High", "Critical"] if column in pivot.columns
    ]
    pivot[priority_order].plot(
        kind="barh",
        stacked=True,
        ax=ax,
        color=[MUTED, BLUE, AMBER, RED][: len(priority_order)],
    )
    ax.set_xlabel("Selected customers")
    ax.legend(frameon=False, labelcolor=MUTED, title="", ncol=4)
    _save(fig, CONFIG.image_dir / "campaign-targeting.png")


def architecture() -> None:
    fig = plt.figure(figsize=(19.2, 10.8))
    _style_figure(
        fig,
        "Customer Intelligence Platform Architecture",
        "A modular path from governed source data to explainable predictions and business activation",
    )
    ax = fig.add_axes([0.035, 0.07, 0.93, 0.80])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    columns = [
        (
            "DATA SOURCES",
            ["Customers", "Orders & Lines", "Digital Interactions", "Campaign History"],
            BLUE,
        ),
        (
            "DATA PLATFORM",
            ["CSV Data Lake", "SQLite / SQL Views", "Quality Gates", "Calendar Model"],
            TEAL,
        ),
        (
            "INTELLIGENCE",
            ["RFM & Cohorts", "Predictive CLV", "Churn Model", "SHAP & Monitoring"],
            PURPLE,
        ),
        (
            "ACTIVATION",
            ["Campaign Optimizer", "FastAPI Scoring", "Power BI / Tableau", "Excel Planner"],
            AMBER,
        ),
    ]
    x_positions = [0.02, 0.27, 0.52, 0.77]
    for x, (heading, items, color) in zip(x_positions, columns, strict=False):
        outer = FancyBboxPatch(
            (x, 0.12),
            0.21,
            0.72,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            facecolor=PANEL,
            edgecolor=color,
            linewidth=1.4,
        )
        ax.add_patch(outer)
        ax.text(x + 0.02, 0.78, heading, color=color, fontsize=11, fontweight="bold")
        for index, item in enumerate(items):
            y = 0.64 - index * 0.13
            inner = FancyBboxPatch(
                (x + 0.018, y - 0.035),
                0.174,
                0.083,
                boxstyle="round,pad=0.008,rounding_size=0.012",
                facecolor=PANEL_ALT,
                edgecolor=GRID,
                linewidth=0.8,
            )
            ax.add_patch(inner)
            ax.text(x + 0.032, y + 0.006, item, color=TEXT, fontsize=9, va="center")
    for left, right, color in zip(x_positions[:-1], x_positions[1:], [TEAL, PURPLE, AMBER], strict=False):
        arrow = FancyArrowPatch(
            (left + 0.213, 0.48),
            (right - 0.006, 0.48),
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=1.8,
            color=color,
        )
        ax.add_patch(arrow)
    ax.text(
        0.50,
        0.035,
        "Governance layer: point-in-time features  •  no protected attributes  •  calibrated probabilities  •  PSI monitoring  •  human review",
        color=MUTED,
        fontsize=10,
        ha="center",
    )
    _save(fig, CONFIG.image_dir / "architecture.png")


def generate_all_visuals() -> None:
    sns.set_theme(style="darkgrid")
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["figure.autolayout"] = False
    executive_overview()
    customer_360_view()
    rfm_segmentation()
    cohort_retention()
    clv_analysis()
    churn_risk()
    model_performance()
    shap_explainability()
    campaign_targeting()
    architecture()


if __name__ == "__main__":
    generate_all_visuals()
    print(f"Generated 10 4K visuals in {PROJECT_ROOT / 'Images'}")
