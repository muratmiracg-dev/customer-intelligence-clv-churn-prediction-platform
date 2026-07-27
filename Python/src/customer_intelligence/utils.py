from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def ensure_directories(root: Path) -> None:
    directories = [
        "API",
        "App",
        "Data/Raw",
        "Data/Processed",
        "Delivery",
        "Docs",
        "Excel",
        "Images",
        "Models",
        "Notebooks",
        "PowerBI",
        "Presentation",
        "Reports",
        "SQL",
        "Tableau",
        "Tests",
        ".github/workflows",
    ]
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, date_format="%Y-%m-%d")


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    class Encoder(json.JSONEncoder):
        def default(self, obj: Any) -> Any:
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, (np.ndarray,)):
                return obj.tolist()
            if isinstance(obj, (pd.Timestamp,)):
                return obj.isoformat()
            return super().default(obj)

    path.write_text(json.dumps(payload, indent=2, cls=Encoder), encoding="utf-8")


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator.div(denominator).replace([np.inf, -np.inf], np.nan).fillna(0.0)

