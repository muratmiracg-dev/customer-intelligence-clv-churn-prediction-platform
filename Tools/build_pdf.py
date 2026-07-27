"""Build a vector-first, 16:9 executive PDF for the customer intelligence project."""

from __future__ import annotations

from pathlib import Path
from textwrap import wrap

import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data" / "Processed"
OUTPUT = ROOT / "Reports" / "Customer_Intelligence_Executive_Report_12_Page_Vector_HD.pdf"

PAGE_W = 960
PAGE_H = 540

COLORS = {
    "navy": HexColor("#071423"),
    "navy2": HexColor("#102238"),
    "blue": HexColor("#2E8BFF"),
    "cyan": HexColor("#2AC7E8"),
    "teal": HexColor("#26C6A5"),
    "purple": HexColor("#987CF5"),
    "amber": HexColor("#F5A623"),
    "red": HexColor("#F2556D"),
    "green": HexColor("#16A079"),
    "white": HexColor("#FFFFFF"),
    "canvas": HexColor("#F4F7FB"),
    "panel": HexColor("#FFFFFF"),
    "line": HexColor("#D5DFEB"),
    "muted": HexColor("#68778A"),
    "ink": HexColor("#122033"),
    "pale_blue": HexColor("#EAF3FF"),
    "pale_teal": HexColor("#E8F8F4"),
    "pale_purple": HexColor("#F0ECFF"),
    "pale_amber": HexColor("#FFF4DF"),
    "pale_red": HexColor("#FDECEF"),
}

pdfmetrics.registerFont(TTFont("Inter", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(
    TTFont("Inter-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
)


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


executive = load("executive_kpis.csv")
segments = load("segment_summary.csv")
cohort = load("cohort_retention_matrix.csv")
churn_models = load("churn_model_comparison.csv")
clv_models = load("clv_model_comparison.csv")
campaigns = load("campaign_summary.csv")
shap = load("shap_global_importance.csv")
fairness = load("fairness_audit.csv")
drift = load("drift_monitoring.csv")
monthly = load("monthly_customer_metrics.csv")
customer = load("customer_360.csv")
quality = load("data_quality_report.csv")

KPI = dict(zip(executive["kpi"], executive["value"], strict=True))


def fmt_try(value: float, digits: int = 1) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"TRY {value / 1_000_000:.{digits}f}M"
    if abs(value) >= 1_000:
        return f"TRY {value / 1_000:.{digits}f}K"
    return f"TRY {value:,.0f}"


def fmt_num(value: float) -> str:
    return f"{int(round(float(value))):,}"


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def set_fill(c: canvas.Canvas, color) -> None:
    c.setFillColor(color)


def set_stroke(c: canvas.Canvas, color) -> None:
    c.setStrokeColor(color)


def round_rect(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill,
    stroke=COLORS["line"],
    radius: float = 9,
    line_width: float = 0.8,
) -> None:
    set_fill(c, fill)
    set_stroke(c, stroke)
    c.setLineWidth(line_width)
    c.roundRect(x, y, width, height, radius, stroke=1, fill=1)


def draw_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    size: float = 11,
    color=COLORS["ink"],
    bold: bool = False,
    max_width: float | None = None,
    leading: float | None = None,
    align: str = "left",
) -> float:
    font = "Inter-Bold" if bold else "Inter"
    c.setFont(font, size)
    set_fill(c, color)
    leading = leading or size * 1.3
    if max_width:
        approx_chars = max(8, int(max_width / (size * 0.56)))
        lines = []
        for paragraph in str(text).split("\n"):
            lines.extend(wrap(paragraph, width=approx_chars) or [""])
    else:
        lines = str(text).split("\n")
    cursor = y
    for line in lines:
        if align == "right":
            c.drawRightString(x, cursor, line)
        elif align == "center":
            c.drawCentredString(x, cursor, line)
        else:
            c.drawString(x, cursor, line)
        cursor -= leading
    return cursor


def header(c: canvas.Canvas, title: str, subtitle: str, page: int) -> None:
    set_fill(c, COLORS["canvas"])
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    draw_text(
        c,
        "NOVARETAIL GROUP  |  CUSTOMER INTELLIGENCE",
        36,
        512,
        7.5,
        COLORS["blue"],
        True,
    )
    draw_text(c, title, 36, 480, 22, COLORS["navy"], True, 600)
    draw_text(c, subtitle, 924, 482, 8.3, COLORS["muted"], False, 285, align="right")
    set_fill(c, COLORS["blue"])
    c.rect(36, 448, 888, 2.2, stroke=0, fill=1)
    draw_text(c, f"{page:02d}", 924, 20, 7.5, COLORS["muted"], True, align="right")
    draw_text(
        c,
        "Synthetic portfolio data • 2022–2025 • Production snapshot: 31 Dec 2025 • TRY",
        36,
        20,
        6.5,
        COLORS["muted"],
    )


def source_line(c: canvas.Canvas, text: str) -> None:
    draw_text(c, f"Sources: {text}", 36, 36, 6.2, COLORS["muted"])


def metric_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    label: str,
    value: str,
    note: str,
    accent,
    height: float = 82,
) -> None:
    round_rect(c, x, y, width, height, COLORS["white"])
    set_fill(c, accent)
    c.roundRect(x, y, 4, height, 2, stroke=0, fill=1)
    draw_text(c, label.upper(), x + 14, y + height - 20, 6.8, COLORS["muted"], True)
    draw_text(c, value, x + 14, y + height - 47, 16, accent, True)
    draw_text(c, note, x + 14, y + 11, 6.5, COLORS["muted"], False, width - 28)


def insight(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    accent,
    fill,
) -> None:
    round_rect(c, x, y, width, height, fill, accent)
    set_fill(c, accent)
    c.rect(x, y, 4, height, stroke=0, fill=1)
    draw_text(c, title, x + 14, y + height - 22, 9.5, accent, True)
    draw_text(c, body, x + 14, y + height - 42, 7.4, COLORS["ink"], False, width - 28, 10)


def line_chart(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    values: list[float],
    color,
    label: str,
    categories: list[str] | None = None,
) -> None:
    round_rect(c, x, y, width, height, COLORS["white"])
    draw_text(c, label, x + 14, y + height - 20, 9.5, COLORS["navy"], True)
    plot_x = x + 40
    plot_y = y + 28
    plot_w = width - 58
    plot_h = height - 62
    max_v = max(values) if values else 1
    min_v = min(values) if values else 0
    span = max(max_v - min_v, 1)
    set_stroke(c, COLORS["line"])
    c.setLineWidth(0.6)
    for index in range(5):
        grid_y = plot_y + index * plot_h / 4
        c.line(plot_x, grid_y, plot_x + plot_w, grid_y)
    points = []
    for index, value in enumerate(values):
        px = plot_x + index * plot_w / max(len(values) - 1, 1)
        py = plot_y + (value - min_v) / span * plot_h
        points.append((px, py))
    set_stroke(c, color)
    c.setLineWidth(2)
    for current, following in zip(points, points[1:]):
        c.line(current[0], current[1], following[0], following[1])
    if categories:
        for index in [0, len(categories) // 2, len(categories) - 1]:
            px = plot_x + index * plot_w / max(len(categories) - 1, 1)
            draw_text(c, str(categories[index])[:7], px, y + 10, 5.8, COLORS["muted"], align="center")
    draw_text(c, f"{max_v / 1_000_000:.1f}M", x + 8, plot_y + plot_h - 3, 5.7, COLORS["muted"])
    draw_text(c, f"{min_v / 1_000_000:.1f}M", x + 8, plot_y, 5.7, COLORS["muted"])


def horizontal_bars(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    labels: list[str],
    values: list[float],
    colors: list,
    title: str,
    value_formatter=None,
) -> None:
    round_rect(c, x, y, width, height, COLORS["white"])
    draw_text(c, title, x + 14, y + height - 20, 9.5, COLORS["navy"], True)
    chart_top = y + height - 42
    chart_bottom = y + 18
    row_height = (chart_top - chart_bottom) / max(len(labels), 1)
    max_v = max(values) if values else 1
    label_width = min(115, width * 0.34)
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        center_y = chart_top - (index + 0.5) * row_height
        draw_text(c, label[:24], x + 12, center_y - 3, 6.5, COLORS["muted"])
        bar_x = x + label_width
        bar_w = (width - label_width - 54) * value / max_v
        set_fill(c, colors[index % len(colors)])
        c.roundRect(bar_x, center_y - 5, max(1, bar_w), 10, 4, stroke=0, fill=1)
        value_text = value_formatter(value) if value_formatter else f"{value:,.1f}"
        draw_text(c, value_text, x + width - 10, center_y - 3, 6.3, COLORS["ink"], True, align="right")


def comparison_bars(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    labels: list[str],
    first: list[float],
    second: list[float],
    first_name: str,
    second_name: str,
    first_color,
    second_color,
) -> None:
    round_rect(c, x, y, width, height, COLORS["white"])
    draw_text(c, first_name, x + 14, y + height - 19, 6.5, first_color, True)
    draw_text(c, second_name, x + 115, y + height - 19, 6.5, second_color, True)
    max_v = max(first + second) if first or second else 1
    plot_y = y + 35
    plot_h = height - 66
    slot = width / max(len(labels), 1)
    for index, label in enumerate(labels):
        center = x + slot * (index + 0.5)
        bar_max_h = plot_h
        h1 = first[index] / max_v * bar_max_h
        h2 = second[index] / max_v * bar_max_h
        set_fill(c, first_color)
        c.rect(center - 11, plot_y, 9, h1, stroke=0, fill=1)
        set_fill(c, second_color)
        c.rect(center + 2, plot_y, 9, h2, stroke=0, fill=1)
        draw_text(c, label[:10], center, y + 14, 5.6, COLORS["muted"], align="center")


def table(
    c: canvas.Canvas,
    x: float,
    y: float,
    widths: list[float],
    headers: list[str],
    rows: list[list[str]],
    row_height: float = 24,
) -> None:
    total = sum(widths)
    set_fill(c, COLORS["navy"])
    c.rect(x, y + len(rows) * row_height, total, row_height, stroke=0, fill=1)
    cursor = x
    for header_text, width in zip(headers, widths, strict=True):
        draw_text(c, header_text, cursor + 6, y + len(rows) * row_height + 8, 6.5, COLORS["white"], True)
        cursor += width
    for row_index, row in enumerate(rows):
        row_y = y + (len(rows) - 1 - row_index) * row_height
        set_fill(c, COLORS["white"] if row_index % 2 == 0 else COLORS["canvas"])
        set_stroke(c, COLORS["line"])
        c.rect(x, row_y, total, row_height, stroke=1, fill=1)
        cursor = x
        for value, width in zip(row, widths, strict=True):
            draw_text(c, str(value), cursor + 6, row_y + 8, 6.2, COLORS["ink"], False, width - 12)
            cursor += width


def next_page(c: canvas.Canvas) -> None:
    c.showPage()


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Customer Intelligence, CLV & Churn Prediction Platform")
    c.setAuthor("Murat Miraç Gedik")
    c.setSubject("Executive customer intelligence and predictive analytics report")

    # 1 — Cover
    set_fill(c, COLORS["navy"])
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    set_fill(c, COLORS["blue"])
    c.rect(710, 0, 250, PAGE_H, stroke=0, fill=1)
    set_fill(c, COLORS["teal"])
    c.circle(823, 410, 61, stroke=0, fill=1)
    set_fill(c, COLORS["purple"])
    c.circle(820, 222, 92, stroke=0, fill=1)
    draw_text(c, "NOVARETAIL GROUP  |  CUSTOMER INTELLIGENCE", 42, 500, 8, HexColor("#8FD8FF"), True)
    draw_text(c, "Customer Intelligence,\nCLV & Churn Prediction Platform", 42, 390, 31, COLORS["white"], True, 610, 39)
    draw_text(
        c,
        "A production-style analytics portfolio connecting customer value, retention risk, explainability and next-best-action decisions.",
        42,
        245,
        12,
        HexColor("#D8E6F6"),
        False,
        590,
        17,
    )
    draw_text(c, "Murat Miraç Gedik  |  Professional Portfolio Project  |  July 2026", 42, 112, 8.5, COLORS["white"])
    draw_text(c, "RFM\nCLV\nCHURN\nSHAP", 820, 335, 18, COLORS["white"], True, align="center")
    draw_text(c, "Synthetic portfolio data • 2022–2025 • Production snapshot: 31 Dec 2025 • TRY", 42, 36, 6.5, HexColor("#B7C7D9"))
    next_page(c)

    # 2 — Executive decision summary
    header(c, "Executive Decision Summary", "Value, risk, retention and campaign economics in one view", 2)
    metric_card(c, 36, 350, 166, "Customers", fmt_num(KPI["Customers"]), "4,067 active in last 12 months", COLORS["blue"])
    metric_card(c, 216, 350, 166, "Net Revenue 12M", fmt_try(KPI["Net Revenue 12M"]), "21.3% gross-margin rate", COLORS["teal"])
    metric_card(c, 396, 350, 166, "Predicted CLV", fmt_try(KPI["Predicted CLV 12M"]), "Forward 12-month margin", COLORS["purple"])
    metric_card(c, 576, 350, 166, "High / Critical Risk", fmt_num(KPI["High/Critical Risk Customers"]), fmt_try(KPI["Revenue at Risk"]) + " exposure", COLORS["red"])
    metric_card(c, 756, 350, 168, "Campaign Upside", fmt_try(KPI["Expected Incremental Margin"], 0), "TRY 236K allocated budget", COLORS["amber"])
    line_chart(
        c,
        36,
        82,
        570,
        242,
        monthly["net_revenue"].tolist(),
        COLORS["blue"],
        "Four-Year Monthly Net Revenue",
        monthly["month"].astype(str).tolist(),
    )
    risk_counts = customer.groupby("risk_band").size().reindex(["Low", "Medium", "High", "Critical"]).fillna(0)
    horizontal_bars(
        c,
        624,
        180,
        300,
        144,
        risk_counts.index.tolist(),
        risk_counts.tolist(),
        [COLORS["teal"], COLORS["blue"], COLORS["amber"], COLORS["red"]],
        "Customer Risk Mix",
        fmt_num,
    )
    insight(
        c,
        624,
        82,
        300,
        82,
        "Decision message",
        f"{fmt_num(KPI['High/Critical Risk Customers'])} customers require value-aware retention. "
        f"The champion model produces {KPI['Lift at Top 10%']:.2f}x top-decile lift.",
        COLORS["red"],
        COLORS["pale_red"],
    )
    source_line(c, "executive_kpis.csv; monthly_customer_metrics.csv; customer_360.csv")
    next_page(c)

    # 3 — Problem and decision model
    header(c, "Business Problem & Decision Framework", "From fragmented signals to controlled customer action", 3)
    problems = [
        ("Fragmented view", "Transactions, engagement, support and campaign signals are often disconnected.", COLORS["blue"], COLORS["pale_blue"]),
        ("Reactive churn", "Interventions begin after value and relationship strength have already deteriorated.", COLORS["red"], COLORS["pale_red"]),
        ("Value-blind targeting", "Risk alone can overfund low-value customers and miss profitable retention.", COLORS["amber"], COLORS["pale_amber"]),
        ("Opaque decisions", "Unexplained scores reduce trust, adoption and governance quality.", COLORS["purple"], COLORS["pale_purple"]),
    ]
    for index, item in enumerate(problems):
        x = 36 + (index % 2) * 453
        y = 296 - (index // 2) * 138
        insight(c, x, y, 426, 116, item[0], item[1], item[2], item[3])
    insight(
        c,
        36,
        72,
        879,
        75,
        "Core decision",
        "Which customer should receive which intervention, at what time and with what budget?",
        COLORS["navy"],
        COLORS["white"],
    )
    source_line(c, "methodology.md; campaign_playbook.md")
    next_page(c)

    # 4 — Architecture
    header(c, "Solution Architecture", "A reproducible path from source data to executive action", 4)
    layers = [
        ("DATA", ["Customer", "Orders", "Products", "Interactions"], COLORS["blue"], COLORS["pale_blue"]),
        ("ANALYTICS", ["RFM & Cohorts", "CLV Regression", "Churn Classification", "SHAP"], COLORS["teal"], COLORS["pale_teal"]),
        ("DECISION", ["Risk × Value", "Consent Gate", "Expected ROI", "Next Best Action"], COLORS["purple"], COLORS["pale_purple"]),
        ("DELIVERY", ["Power BI", "Excel & Tableau", "FastAPI", "Executive Report"], COLORS["amber"], COLORS["pale_amber"]),
    ]
    for index, (name, items, accent, fill) in enumerate(layers):
        x = 36 + index * 222
        round_rect(c, x, 125, 197, 285, fill, accent)
        draw_text(c, f"{index + 1:02d}", x + 15, 384, 8, accent, True)
        draw_text(c, name, x + 15, 355, 13, COLORS["navy"], True)
        for item_index, item in enumerate(items):
            round_rect(c, x + 15, 287 - item_index * 50, 167, 35, COLORS["white"], COLORS["line"], 5)
            draw_text(c, item, x + 27, 299 - item_index * 50, 7.3, COLORS["ink"])
        if index < len(layers) - 1:
            draw_text(c, "→", x + 208, 263, 18, COLORS["muted"], True, align="center")
    insight(
        c,
        36,
        67,
        879,
        42,
        "Operating principle",
        "One customer key, one governed feature set and one validated decision record across every delivery channel.",
        COLORS["teal"],
        COLORS["pale_teal"],
    )
    source_line(c, "pipeline.py; schema.sql; API/main.py")
    next_page(c)

    # 5 — Data foundation
    header(c, "Data Foundation & Customer 360", "Four years of relational, privacy-safe synthetic portfolio data", 5)
    data_cards = [
        ("6,000", "Customers", COLORS["blue"]),
        ("50,639", "Orders", COLORS["cyan"]),
        ("103,044", "Order lines", COLORS["teal"]),
        ("130,671", "Interactions", COLORS["purple"]),
        ("12,000", "Campaign responses", COLORS["amber"]),
        ("1,461", "Calendar days", COLORS["green"]),
    ]
    for index, (value, label_text, accent) in enumerate(data_cards):
        x = 36 + (index % 3) * 296
        y = 314 - (index // 3) * 112
        metric_card(c, x, y, 268, label_text, value, "Validated synthetic records", accent, 91)
    fields = [
        "Identity & consent",
        "12M behavior",
        "RFM segment",
        "Predictive CLV",
        "Churn probability",
        "SHAP reasons",
        "Recommended action",
        "Expected margin",
    ]
    round_rect(c, 36, 83, 879, 95, COLORS["white"])
    draw_text(c, "Customer 360 decision record", 51, 156, 10, COLORS["navy"], True)
    for index, field in enumerate(fields):
        x = 51 + (index % 4) * 211
        y = 119 - (index // 4) * 34
        set_fill(c, [COLORS["blue"], COLORS["teal"], COLORS["purple"], COLORS["amber"]][index % 4])
        c.circle(x, y + 2, 3.5, stroke=0, fill=1)
        draw_text(c, field, x + 9, y, 7, COLORS["ink"])
    source_line(c, "dim_customers.csv; fact_orders.csv; customer_360.csv; data_quality_report.csv")
    next_page(c)

    # 6 — RFM
    header(c, "RFM Segmentation", "Behavioral groups linked to portfolio value and retention risk", 6)
    ordered = segments.sort_values("predicted_clv_12m", ascending=False)
    horizontal_bars(
        c,
        36,
        114,
        555,
        300,
        ordered["rfm_segment"].tolist(),
        ordered["predicted_clv_12m"].tolist(),
        [COLORS["purple"]],
        "Predicted CLV by RFM Segment",
        lambda v: fmt_try(v, 1),
    )
    horizontal_bars(
        c,
        610,
        235,
        305,
        179,
        ordered["rfm_segment"].tolist(),
        ordered["average_churn_probability"].tolist(),
        [COLORS["red"], COLORS["amber"], COLORS["blue"], COLORS["teal"]],
        "Average Churn Risk",
        fmt_pct,
    )
    insight(
        c,
        610,
        114,
        305,
        102,
        "Commercial interpretation",
        "Champions anchor the value pool. At-risk and hibernating groups require selective, economics-led treatment rather than blanket discounting.",
        COLORS["amber"],
        COLORS["pale_amber"],
    )
    source_line(c, "rfm_scores.csv; segment_summary.csv")
    next_page(c)

    # 7 — Cohort
    header(c, "Cohort Retention", "Acquisition quality measured beyond the first purchase", 7)
    cohort_view = cohort.tail(18).iloc[:, :14]
    heat_x = 36
    heat_y = 114
    cell_w = 47
    cell_h = 17
    draw_text(c, "First Purchase Cohort × Months Since Acquisition", 36, 418, 10, COLORS["navy"], True)
    month_columns = cohort_view.columns[1:]
    for index, col in enumerate(month_columns):
        draw_text(c, col, heat_x + 108 + index * cell_w + cell_w / 2, 395, 5.5, COLORS["muted"], True, align="center")
    for row_index, (_, row) in enumerate(cohort_view.iterrows()):
        y = heat_y + (len(cohort_view) - 1 - row_index) * cell_h
        draw_text(c, str(row.iloc[0])[:7], heat_x, y + 5, 5.5, COLORS["muted"])
        for col_index, value in enumerate(row.iloc[1:]):
            if pd.isna(value):
                fill = COLORS["canvas"]
            else:
                intensity = max(0, min(1, float(value)))
                fill = Color(
                    0.92 - 0.70 * intensity,
                    0.96 - 0.25 * intensity,
                    1.00 - 0.10 * intensity,
                )
            set_fill(c, fill)
            set_stroke(c, COLORS["white"])
            c.rect(heat_x + 108 + col_index * cell_w, y, cell_w, cell_h, stroke=1, fill=1)
            if not pd.isna(value):
                draw_text(
                    c,
                    f"{float(value) * 100:.0f}%",
                    heat_x + 108 + col_index * cell_w + cell_w / 2,
                    y + 5,
                    4.8,
                    COLORS["ink"],
                    align="center",
                )
    metric_card(c, 778, 302, 137, "M3 Retention", fmt_pct(KPI["M3 Cohort Retention"]), "Average across cohorts", COLORS["teal"], 95)
    insight(
        c,
        778,
        114,
        137,
        169,
        "Management use",
        "Compare acquisition months, identify early decay and connect cohort quality to channel, onboarding and offer strategy.",
        COLORS["purple"],
        COLORS["pale_purple"],
    )
    source_line(c, "cohort_retention_matrix.csv; cohort_retention_long.csv")
    next_page(c)

    # 8 — CLV
    header(c, "Predictive Customer Lifetime Value", "Twelve-month gross-margin contribution for value-based prioritization", 8)
    clv_rows = [
        [
            row.model,
            fmt_try(row.mae, 1),
            fmt_try(row.rmse, 1),
            f"{row.r2:.3f}",
            f"{row.spearman_correlation:.3f}",
        ]
        for row in clv_models.itertuples()
    ]
    table(c, 36, 293, [226, 91, 91, 74, 86], ["Model", "MAE", "RMSE", "R²", "Spearman"], clv_rows, 28)
    metric_card(c, 635, 318, 136, "Portfolio CLV", fmt_try(KPI["Predicted CLV 12M"]), "Forward 12 months", COLORS["purple"], 96)
    metric_card(c, 779, 318, 136, "Champion R²", f"{clv_models.iloc[0]['r2']:.3f}", "Time-based holdout", COLORS["teal"], 96)
    horizontal_bars(
        c,
        36,
        82,
        879,
        188,
        ordered["rfm_segment"].tolist(),
        ordered["predicted_clv_12m"].tolist(),
        [COLORS["purple"], COLORS["blue"], COLORS["teal"]],
        "CLV Portfolio by RFM Segment",
        lambda v: fmt_try(v, 1),
    )
    source_line(c, "clv_model_comparison.csv; clv_predictions.csv; modeling.py")
    next_page(c)

    # 9 — Churn
    header(c, "Churn Prediction & Risk Portfolio", "Champion selection balances discrimination, calibration and business lift", 9)
    labels = [str(value).replace(" (calibrated champion)", "")[:16] for value in churn_models["model"]]
    comparison_bars(
        c,
        36,
        184,
        555,
        230,
        labels,
        churn_models["roc_auc"].tolist(),
        churn_models["pr_auc"].tolist(),
        "ROC-AUC",
        "PR-AUC",
        COLORS["blue"],
        COLORS["teal"],
    )
    champion = churn_models.iloc[0]
    metric_card(c, 610, 318, 145, "ROC-AUC", f"{champion.roc_auc:.3f}", "Discrimination", COLORS["blue"], 96)
    metric_card(c, 770, 318, 145, "Top 10% Lift", f"{champion.lift_at_10pct:.2f}x", "Targeting power", COLORS["amber"], 96)
    horizontal_bars(
        c,
        610,
        82,
        305,
        215,
        risk_counts.index.tolist(),
        risk_counts.tolist(),
        [COLORS["teal"], COLORS["blue"], COLORS["amber"], COLORS["red"]],
        "Risk Tier Distribution",
        fmt_num,
    )
    insight(
        c,
        36,
        82,
        555,
        82,
        "Leakage control",
        "Training snapshots precede the 31 Dec 2024 holdout; production scoring uses the 31 Dec 2025 portfolio. "
        "The operating threshold is selected before the holdout is evaluated.",
        COLORS["red"],
        COLORS["pale_red"],
    )
    source_line(c, "churn_model_comparison.csv; churn_predictions.csv; model_metadata.json")
    next_page(c)

    # 10 — SHAP / fairness / drift
    header(c, "Explainability, Fairness & Drift", "Responsible use requires transparent drivers and post-approval controls", 10)
    top_shap = shap.head(8)
    horizontal_bars(
        c,
        36,
        162,
        490,
        252,
        top_shap["feature"].str.replace("_", " ").tolist(),
        top_shap["importance_share"].tolist(),
        [COLORS["purple"]],
        "Top Global SHAP Drivers",
        fmt_pct,
    )
    region = fairness[fairness["audit_attribute"] == "region"].head(6)
    table(
        c,
        545,
        240,
        [112, 60, 78, 78, 70],
        ["Region", "N", "Observed", "Avg Risk", "AUC"],
        [
            [
                row.audit_group,
                fmt_num(row.customers),
                fmt_pct(row.observed_churn_rate),
                fmt_pct(row.average_predicted_risk),
                f"{row.roc_auc:.3f}",
            ]
            for row in region.itertuples()
        ],
        24,
    )
    watch = drift.sort_values("psi", ascending=False).iloc[0]
    metric_card(c, 545, 112, 188, "Drift Watch", watch.feature.replace("_", " "), f"PSI {watch.psi:.3f}", COLORS["amber"], 100)
    metric_card(c, 747, 112, 196, "Quality Gates", f"{(quality.status == 'PASS').sum()}/{len(quality)}", "All pipeline checks PASS", COLORS["teal"], 100)
    insight(
        c,
        36,
        82,
        490,
        63,
        "Interpretation boundary",
        "SHAP explains model association, not causality. Human review and campaign eligibility remain above the score.",
        COLORS["blue"],
        COLORS["pale_blue"],
    )
    source_line(c, "shap_global_importance.csv; fairness_audit.csv; drift_monitoring.csv")
    next_page(c)

    # 11 — Campaign economics
    header(c, "Campaign Targeting & Economics", "Budget allocated by expected incremental margin and controlled ROI", 11)
    portfolio = campaigns[campaigns["recommended_action"] != "Suppress"]
    comparison_bars(
        c,
        36,
        142,
        555,
        272,
        portfolio["recommended_action"].tolist(),
        (portfolio["allocated_budget"] / 1000).tolist(),
        (portfolio["expected_incremental_margin"] / 1000).tolist(),
        "Budget (TRY K)",
        "Expected Margin (TRY K)",
        COLORS["amber"],
        COLORS["teal"],
    )
    campaign_rows = [
        [
            row.recommended_action,
            fmt_num(row.selected_customers),
            fmt_try(row.allocated_budget, 0),
            fmt_try(row.expected_incremental_margin, 0),
            f"{row.average_expected_roi:.2f}x",
        ]
        for row in portfolio.itertuples()
    ]
    table(c, 610, 211, [110, 54, 64, 72, 46], ["Action", "Selected", "Budget", "Margin", "ROI"], campaign_rows, 25)
    metric_card(c, 610, 88, 146, "Prioritized", fmt_num(portfolio["selected_customers"].sum()), "Customer actions", COLORS["blue"], 100)
    metric_card(c, 769, 88, 146, "Expected Margin", fmt_try(portfolio["expected_incremental_margin"].sum(), 0), "Incremental contribution", COLORS["teal"], 100)
    source_line(c, "campaign_summary.csv; campaign_targets.csv; campaign.py")
    next_page(c)

    # 12 — Delivery and roadmap
    header(c, "Delivery Architecture & 90-Day Roadmap", "From portfolio prototype to an operating customer-intelligence capability", 12)
    stack = [
        ("Power BI", "12-page PBIP\nDAX + semantic model", COLORS["blue"], COLORS["pale_blue"]),
        ("Excel", "24-sheet decision model\nScenario + QA", COLORS["green"], COLORS["pale_teal"]),
        ("Tableau", "3 dashboards\n8 worksheets", COLORS["cyan"], COLORS["pale_blue"]),
        ("Python & SQL", "Reproducible pipeline\nSQLite layer", COLORS["purple"], COLORS["pale_purple"]),
        ("API & App", "FastAPI scoring\nStreamlit exploration", COLORS["amber"], COLORS["pale_amber"]),
        ("Governance", "Tests, cards, drift\nFairness + CI", COLORS["red"], COLORS["pale_red"]),
    ]
    for index, (name, body, accent, fill) in enumerate(stack):
        x = 36 + (index % 3) * 296
        y = 330 - (index // 3) * 105
        round_rect(c, x, y, 268, 87, fill, accent)
        draw_text(c, name, x + 14, y + 61, 10, accent, True)
        draw_text(c, body, x + 14, y + 38, 7, COLORS["ink"], False, 230, 10)
    phases = [
        ("0–30", "Foundation", "Sources • KPI dictionary • pilot cohort", COLORS["blue"]),
        ("31–60", "Model & Experiment", "Validation • A/B design • approval gate", COLORS["teal"]),
        ("61–90", "Operate", "BI release • API • monitoring cadence", COLORS["purple"]),
    ]
    set_stroke(c, COLORS["line"])
    c.setLineWidth(2)
    c.line(92, 137, 840, 137)
    for index, (days, phase, body, accent) in enumerate(phases):
        x = 92 + index * 360
        set_fill(c, accent)
        c.circle(x, 137, 7, stroke=0, fill=1)
        draw_text(c, f"Days {days}", x, 165, 8, accent, True, align="center")
        draw_text(c, phase, x, 111, 9, COLORS["navy"], True, align="center")
        draw_text(c, body, x, 92, 6.5, COLORS["muted"], False, 225, 9, "center")
    draw_text(c, "Know customer value. Anticipate risk. Act with discipline.", 480, 51, 12, COLORS["navy"], True, align="center")
    source_line(c, "README.md; PowerBI; Excel; Tableau; API; Docs")
    c.save()
    return OUTPUT


if __name__ == "__main__":
    print(build())
