from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "Tableau" / "Customer_Intelligence_Dashboard.twb"


FIELDS = [
    ("Customer ID", "string", "dimension", "nominal"),
    ("Snapshot Date", "date", "dimension", "ordinal"),
    ("Region", "string", "dimension", "nominal"),
    ("Age Band", "string", "dimension", "nominal"),
    ("Loyalty Tier", "string", "dimension", "nominal"),
    ("Preferred Channel", "string", "dimension", "nominal"),
    ("Recency Days", "integer", "measure", "quantitative"),
    ("Frequency 12M", "integer", "measure", "quantitative"),
    ("Revenue 12M", "real", "measure", "quantitative"),
    ("Gross Margin 12M", "real", "measure", "quantitative"),
    ("Average Order Value 12M", "real", "measure", "quantitative"),
    ("RFM Segment", "string", "dimension", "nominal"),
    ("Predicted CLV 12M", "real", "measure", "quantitative"),
    ("CLV Band", "string", "dimension", "nominal"),
    ("Churn Probability", "real", "measure", "quantitative"),
    ("Risk Band", "string", "dimension", "nominal"),
    ("Recommended Action", "string", "dimension", "nominal"),
    ("Campaign Priority", "string", "dimension", "nominal"),
    ("Expected Incremental Margin", "real", "measure", "quantitative"),
    ("Selected for Campaign", "integer", "measure", "quantitative"),
]


WORKSHEETS = [
    ("Executive KPI Table", "[Customer ID]", "Measure Values"),
    ("Revenue by RFM Segment", "[RFM Segment]", "SUM([Revenue 12M])"),
    ("CLV by RFM Segment", "[RFM Segment]", "SUM([Predicted CLV 12M])"),
    ("Churn Risk Distribution", "[Risk Band]", "COUNTD([Customer ID])"),
    ("Customer Value Risk Matrix", "[Predicted CLV 12M]", "[Churn Probability]"),
    ("Campaign Recommendations", "[Recommended Action]", "SUM([Expected Incremental Margin])"),
    ("Regional Risk Analysis", "[Region]", "AVG([Churn Probability])"),
    ("Customer Detail", "[Customer ID]", "Measure Values"),
]


def _add_calculation(
    datasource: ET.Element,
    name: str,
    caption: str,
    formula: str,
    datatype: str = "real",
) -> None:
    column = ET.SubElement(
        datasource,
        "column",
        {
            "caption": caption,
            "datatype": datatype,
            "name": f"[{name}]",
            "role": "measure",
            "type": "quantitative",
        },
    )
    ET.SubElement(column, "calculation", {"class": "tableau", "formula": formula})


def build_workbook() -> Path:
    workbook = ET.Element(
        "workbook",
        {
            "original-version": "18.1",
            "source-build": "2026.1",
            "source-platform": "win",
            "version": "18.1",
            "{http://www.w3.org/XML/1998/namespace}base": "https://localhost:8080",
        },
    )
    preferences = ET.SubElement(workbook, "preferences")
    ET.SubElement(
        preferences,
        "preference",
        {"name": "ui.encoding.shelf.height", "value": "24"},
    )
    datasources = ET.SubElement(workbook, "datasources")
    datasource = ET.SubElement(
        datasources,
        "datasource",
        {
            "caption": "Customer 360",
            "inline": "true",
            "name": "federated.customer360",
            "version": "18.1",
        },
    )
    ET.SubElement(
        datasource,
        "connection",
        {
            "class": "textscan",
            "directory": "../Data/Processed",
            "filename": "customer_360.csv",
            "password": "",
            "server": "",
        },
    )
    ET.SubElement(datasource, "aliases", {"enabled": "yes"})
    for name, datatype, role, field_type in FIELDS:
        ET.SubElement(
            datasource,
            "column",
            {
                "datatype": datatype,
                "name": f"[{name}]",
                "role": role,
                "type": field_type,
            },
        )
    _add_calculation(
        datasource,
        "Value at Risk",
        "Value at Risk",
        "IF [Churn Probability] >= 0.55 THEN [Revenue 12M] ELSE 0 END",
    )
    _add_calculation(
        datasource,
        "Strategic Risk Flag",
        "Strategic Risk Flag",
        "IF [CLV Band] = 'Strategic' AND [Risk Band] IN ('High','Critical') THEN 1 ELSE 0 END",
        "integer",
    )
    _add_calculation(
        datasource,
        "Campaign Selected Margin",
        "Campaign Selected Margin",
        "IF [Selected for Campaign] = 1 THEN [Expected Incremental Margin] ELSE 0 END",
    )

    worksheets = ET.SubElement(workbook, "worksheets")
    for name, rows_expression, cols_expression in WORKSHEETS:
        worksheet = ET.SubElement(worksheets, "worksheet", {"name": name})
        table = ET.SubElement(worksheet, "table")
        view = ET.SubElement(table, "view")
        view_datasources = ET.SubElement(view, "datasources")
        ET.SubElement(
            view_datasources,
            "datasource",
            {"caption": "Customer 360", "name": "federated.customer360"},
        )
        slices = ET.SubElement(view, "slices")
        ET.SubElement(slices, "column").text = "[federated.customer360].[Snapshot Date]"
        ET.SubElement(view, "rows").text = (
            rows_expression
            if rows_expression.startswith("[federated")
            else f"[federated.customer360].{rows_expression}"
        )
        ET.SubElement(view, "cols").text = cols_expression

    dashboards = ET.SubElement(workbook, "dashboards")
    dashboard_specs = {
        "Customer Intelligence - Executive Overview": [
            "Executive KPI Table",
            "Revenue by RFM Segment",
            "Churn Risk Distribution",
            "Customer Value Risk Matrix",
        ],
        "Customer Intelligence - Segmentation & CLV": [
            "CLV by RFM Segment",
            "Regional Risk Analysis",
            "Customer Detail",
        ],
        "Customer Intelligence - Campaign Activation": [
            "Campaign Recommendations",
            "Customer Value Risk Matrix",
            "Customer Detail",
        ],
    }
    for dashboard_name, sheets in dashboard_specs.items():
        dashboard = ET.SubElement(
            dashboards,
            "dashboard",
            {"enable-sort-zone-taborder": "true", "name": dashboard_name},
        )
        ET.SubElement(dashboard, "style")
        zones = ET.SubElement(dashboard, "zones")
        ET.SubElement(
            zones,
            "zone",
            {
                "h": "100000",
                "id": "1",
                "type-v2": "layout-basic",
                "w": "100000",
                "x": "0",
                "y": "0",
            },
        )
        width = 100000 // max(1, len(sheets))
        for index, sheet in enumerate(sheets, start=2):
            ET.SubElement(
                zones,
                "zone",
                {
                    "h": "100000",
                    "id": str(index),
                    "name": sheet,
                    "type-v2": "worksheet",
                    "w": str(width),
                    "x": str((index - 2) * width),
                    "y": "0",
                },
            )
    windows = ET.SubElement(workbook, "windows")
    for dashboard_name in dashboard_specs:
        window = ET.SubElement(
            windows, "window", {"class": "dashboard", "name": dashboard_name}
        )
        ET.SubElement(window, "viewpoints")

    ET.indent(workbook, space=" ")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(workbook)
    tree.write(OUTPUT_PATH, encoding="utf-8", xml_declaration=True)
    return OUTPUT_PATH


if __name__ == "__main__":
    print(build_workbook())

