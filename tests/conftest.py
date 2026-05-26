"""Shared fixtures for stata2ducklake tests."""

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def sample_dta(tmp_path: Path) -> Path:
    """Create a small .dta file with variable labels and value labels."""
    df = pd.DataFrame(
        {
            "id": pd.array([1, 2, 3], dtype="int32"),
            "wage": [50000.0, 60000.0, 70000.0],
            "gender": pd.array([1, 2, 1], dtype="int32"),
            "year": pd.array([2020, 2021, 2020], dtype="int32"),
        }
    )
    path = tmp_path / "sample.dta"
    df.to_stata(
        path,
        variable_labels={
            "id": "Worker ID",
            "wage": "Annual wage (USD)",
            "gender": "Gender code",
            "year": "Survey year",
        },
        value_labels={"gender": {1: "Male", 2: "Female"}},
        write_index=False,
    )
    return path
