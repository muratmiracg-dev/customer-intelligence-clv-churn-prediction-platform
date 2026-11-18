"""Synthetic data and the comparison guard must not depend on interpreter state."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ORDER_DIGEST = (
    "from customer_intelligence.data_generation import generate_all; import hashlib; "
    "print(hashlib.sha256(generate_all().orders.to_csv(index=False).encode()).hexdigest())"
)


def _orders_digest(hash_seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONPATH": str(ROOT / "Python/src")}
    result = subprocess.run(
        [sys.executable, "-c", ORDER_DIGEST], env=env, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def test_generated_orders_do_not_depend_on_string_hash_seed():
    # primary_category used max() over a set, so ties followed per-process string
    # hashing and each interpreter produced different raw orders.
    digests = {_orders_digest(seed) for seed in ("1", "2", "3")}
    assert len(digests) == 1


def test_committed_orders_match_generation():
    from customer_intelligence.data_generation import generate_all

    committed = pd.read_csv(ROOT / "Data/Raw/fact_orders.csv")
    text = generate_all().orders.to_csv(index=False, date_format="%Y-%m-%d")
    regenerated = pd.read_csv(io.StringIO(text))
    pd.testing.assert_frame_equal(committed, regenerated)


@pytest.fixture()
def compare_outputs():
    spec = importlib.util.spec_from_file_location(
        "compare_outputs", ROOT / "scripts" / "compare_outputs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy(target: Path) -> Path:
    for relative in ("Data/Raw", "Data/Processed", "Models"):
        shutil.copytree(ROOT / relative, target / relative)
    return target


def test_compare_outputs_tolerates_noise_and_flags_drift(tmp_path, compare_outputs):
    committed = _copy(tmp_path / "committed")
    fresh = _copy(tmp_path / "fresh")
    metadata_path = fresh / "Models/model_metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["python_version"] = "3.99.0"
    metadata_path.write_text(json.dumps(metadata))
    assert compare_outputs.compare(committed, fresh) == []

    metadata["churn_threshold"] = metadata["churn_threshold"] + 0.01
    metadata_path.write_text(json.dumps(metadata))
    kpis = fresh / "Data/Processed/executive_kpis.csv"
    kpis.write_text(kpis.read_text().replace("Active Customers 12M,4067.0", "Active Customers 12M,4066.0"))
    errors = compare_outputs.compare(committed, fresh)
    assert any(e.startswith("Models/model_metadata.json.churn_threshold") for e in errors)
    assert any(e.startswith("Data/Processed/executive_kpis.csv row 2 column value") for e in errors)
    assert compare_outputs.main(["compare_outputs.py", str(committed), str(fresh)]) == 1
