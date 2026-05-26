"""Tests for stata2ducklake.reader."""

from pathlib import Path

from stata2ducklake.reader import StataData, read_dta


def test_read_dta_returns_stata_data(sample_dta: Path) -> None:
    result = read_dta(sample_dta)
    assert isinstance(result, StataData)


def test_read_dta_data_shape(sample_dta: Path) -> None:
    result = read_dta(sample_dta)
    assert result.data.shape == (3, 4)
    assert list(result.data.columns) == ["id", "wage", "gender", "year"]


def test_read_dta_variable_labels(sample_dta: Path) -> None:
    result = read_dta(sample_dta)
    assert result.variable_labels == {
        "id": "Worker ID",
        "wage": "Annual wage (USD)",
        "gender": "Gender code",
        "year": "Survey year",
    }


def test_read_dta_value_labels(sample_dta: Path) -> None:
    result = read_dta(sample_dta)
    assert "gender" in result.value_labels
    assert result.value_labels["gender"] == {1: "Male", 2: "Female"}


def test_read_dta_column_to_label(sample_dta: Path) -> None:
    result = read_dta(sample_dta)
    assert result.column_to_label == {"gender": "gender"}


def test_read_dta_data_values(sample_dta: Path) -> None:
    result = read_dta(sample_dta)
    assert list(result.data["wage"]) == [50000.0, 60000.0, 70000.0]
    assert list(result.data["gender"]) == [1, 2, 1]
