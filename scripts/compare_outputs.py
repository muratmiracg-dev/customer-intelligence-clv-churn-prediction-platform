"""Compare regenerated analytical outputs with a copy of the committed ones.

Usage: python scripts/compare_outputs.py COMMITTED_ROOT [REGENERATED_ROOT]

COMMITTED_ROOT holds copies of the committed ``Data/Raw``, ``Data/Processed`` and
``Models/model_metadata.json`` (same relative paths). REGENERATED_ROOT defaults to the
repository after ``python -m customer_intelligence.pipeline``.

The tests read the committed tables but never rebuild them, so nothing showed that the
pipeline still produces them (it did not: raw data depended on Python's per-process
string hashing). This check compares a fresh run with the committed values: CSV and
JSON values, numbers within a relative 1e-9 (parallel tree fitting sums in varying
order). The interpreter version recorded in the metadata is ignored. Exit 1 on drift.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

REL_TOL = 1e-9
ABS_TOL = 1e-12
COMPARED_DIRS = ("Data/Raw", "Data/Processed", "Models")
SUFFIXES = {".csv", ".json"}
# Environment details, not analytical results.
IGNORED_KEYS = {"python_version"}


def _same_value(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, int | float) and isinstance(right, int | float):
        if isinstance(left, float) and math.isnan(left):
            return isinstance(right, float) and math.isnan(right)
        return math.isclose(left, right, rel_tol=REL_TOL, abs_tol=ABS_TOL)
    return left == right


def _compare_json(left: object, right: object, where: str, errors: list[str]) -> None:
    if isinstance(left, dict) and isinstance(right, dict):
        keys = (left.keys() | right.keys()) - IGNORED_KEYS
        missing = sorted(key for key in keys if key not in left or key not in right)
        if missing:
            errors.append(f"{where}: keys differ {missing}")
            return
        for key in sorted(keys):
            _compare_json(left[key], right[key], f"{where}.{key}", errors)
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            errors.append(f"{where}: length {len(left)} != {len(right)}")
            return
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            _compare_json(a, b, f"{where}[{index}]", errors)
    elif not _same_value(left, right):
        errors.append(f"{where}: {left!r} != {right!r}")


def _compare_csv(old: Path, new: Path, relative: str, errors: list[str]) -> None:
    left = pd.read_csv(old, keep_default_na=False, na_values=[""])
    right = pd.read_csv(new, keep_default_na=False, na_values=[""])
    if list(left.columns) != list(right.columns):
        errors.append(f"{relative}: columns differ")
        return
    if len(left) != len(right):
        errors.append(f"{relative}: {len(left)} rows != {len(right)} rows")
        return
    left = left.astype(object).where(left.notna(), None)
    right = right.astype(object).where(right.notna(), None)
    for row_number, (a, b) in enumerate(
        zip(left.itertuples(index=False), right.itertuples(index=False), strict=True), start=1
    ):
        for column, x, y in zip(left.columns, a, b, strict=True):
            if not _same_value(x, y):
                errors.append(f"{relative} row {row_number} column {column}: {x!r} != {y!r}")
                return


def compare(committed: Path, regenerated: Path) -> list[str]:
    errors: list[str] = []
    for directory in COMPARED_DIRS:
        names = {
            path.relative_to(root).as_posix()
            for root in (committed, regenerated)
            for path in (root / directory).glob("*")
            if path.suffix in SUFFIXES
        }
        for relative in sorted(names):
            old, new = committed / relative, regenerated / relative
            if not old.is_file() or not new.is_file():
                side = "committed" if new.is_file() else "regenerated"
                errors.append(f"{relative}: missing in {side} outputs")
            elif old.suffix == ".csv":
                _compare_csv(old, new, relative, errors)
            else:
                _compare_json(
                    json.loads(old.read_text(encoding="utf-8")),
                    json.loads(new.read_text(encoding="utf-8")),
                    relative,
                    errors,
                )
    return errors


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    committed = Path(argv[1])
    regenerated = Path(argv[2]) if len(argv) == 3 else Path(__file__).resolve().parents[1]
    errors = compare(committed, regenerated)
    for error in errors[:50]:
        print(f"DRIFT {error}")
    if errors:
        print(f"{len(errors)} difference(s) between committed and regenerated outputs.")
        return 1
    print("Regenerated outputs match the committed data and model metadata.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
