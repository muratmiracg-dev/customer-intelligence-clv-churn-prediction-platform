"""Validate portfolio deliverables and build a release manifest."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "Delivery"

KEY_FILES = [
    "PowerBI/Customer_Intelligence_PBIP.zip",
    "Excel/Customer_Intelligence_CLV_Churn_Campaign_Planner.xlsx",
    "Tableau/Customer_Intelligence_Dashboard.twb",
    "Presentation/Customer_Intelligence_CLV_Churn_Prediction_Professional_Deck_EN.pptx",
    "Presentation/Musteri_Zekasi_CLV_Churn_Tahmin_Platformu_Profesyonel_Sunum_TR.pptx",
    "Reports/Customer_Intelligence_Executive_Report_12_Page_Vector_HD.pdf",
    "Models/churn_champion.joblib",
    "Models/clv_champion.joblib",
    "SQL/customer_intelligence.db",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pptx_slide_count(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        return len(
            [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
        )


def pdf_page_count(path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("Could not determine PDF page count.")
    return int(match.group(1))


def readme_link_errors() -> list[str]:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    errors = []
    for link in links:
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (ROOT / link.split("#", 1)[0]).resolve()
        if not target.exists():
            errors.append(link)
    return errors


def main() -> None:
    DELIVERY.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, object]] = []

    missing = [name for name in KEY_FILES if not (ROOT / name).exists()]
    checks.append({"check": "required_key_files", "passed": not missing, "details": missing})

    raw_files = list((ROOT / "Data" / "Raw").glob("*.csv"))
    processed_files = list((ROOT / "Data" / "Processed").glob("*.csv"))
    checks.append(
        {
            "check": "dataset_file_counts",
            "passed": len(raw_files) == 8 and len(processed_files) == 23,
            "details": {"raw": len(raw_files), "processed": len(processed_files)},
        }
    )

    customer_rows = len(pd.read_csv(ROOT / "Data" / "Processed" / "customer_360.csv"))
    checks.append(
        {"check": "customer_360_rows", "passed": customer_rows == 6000, "details": customer_rows}
    )

    quality = pd.read_csv(ROOT / "Data" / "Processed" / "data_quality_report.csv")
    quality_passed = int((quality["status"] == "PASS").sum())
    checks.append(
        {
            "check": "pipeline_quality_gates",
            "passed": quality_passed == len(quality) == 10,
            "details": f"{quality_passed}/{len(quality)}",
        }
    )

    pbip = json.loads(
        (ROOT / "PowerBI" / "Customer_Intelligence_PBIP" / "pbip_validation.json").read_text(
            encoding="utf-8"
        )
    )
    checks.append(
        {
            "check": "pbip_validation",
            "passed": bool(pbip.get("valid")) and not pbip.get("errors"),
            "details": pbip,
        }
    )

    formula_scan = json.loads(
        (ROOT / "Excel" / "formula_error_scan.json").read_text(encoding="utf-8")
    )
    no_formula_errors = "matched 0 entries" in formula_scan.get("ndjson", "")
    checks.append(
        {
            "check": "excel_formula_error_scan",
            "passed": no_formula_errors,
            "details": formula_scan.get("ndjson"),
        }
    )

    english_slides = pptx_slide_count(ROOT / KEY_FILES[3])
    turkish_slides = pptx_slide_count(ROOT / KEY_FILES[4])
    checks.append(
        {
            "check": "presentation_slide_counts",
            "passed": english_slides == 20 and turkish_slides == 20,
            "details": {"english": english_slides, "turkish": turkish_slides},
        }
    )

    pdf_pages = pdf_page_count(ROOT / KEY_FILES[5])
    checks.append(
        {"check": "executive_pdf_pages", "passed": pdf_pages == 12, "details": pdf_pages}
    )

    tableau_root = ElementTree.parse(ROOT / KEY_FILES[2]).getroot()
    worksheet_count = len(tableau_root.findall(".//worksheet"))
    dashboard_count = len(tableau_root.findall(".//dashboard"))
    checks.append(
        {
            "check": "tableau_structure",
            "passed": worksheet_count == 8 and dashboard_count == 3,
            "details": {"worksheets": worksheet_count, "dashboards": dashboard_count},
        }
    )

    link_errors = readme_link_errors()
    checks.append(
        {"check": "readme_relative_links", "passed": not link_errors, "details": link_errors}
    )

    manifest = []
    for relative in KEY_FILES:
        file_path = ROOT / relative
        manifest.append(
            {
                "path": relative,
                "size_bytes": file_path.stat().st_size,
                "sha256": sha256(file_path),
            }
        )

    release = {
        "project": "Customer Intelligence, CLV & Churn Prediction Platform",
        "version": "1.0.0",
        "release_date": "2026-07-27",
        "status": "PASS" if all(check["passed"] for check in checks) else "FAIL",
        "checks": checks,
    }
    (DELIVERY / "release_validation.json").write_text(
        json.dumps(release, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (DELIVERY / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if release["status"] != "PASS":
        raise SystemExit(json.dumps(release, indent=2, ensure_ascii=False))
    print(json.dumps(release, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
