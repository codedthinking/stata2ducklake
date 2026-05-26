"""Tests for stata2ducklake.writer."""

from pathlib import Path

import duckdb
import pytest

from stata2ducklake.reader import read_dta
from stata2ducklake.writer import CATALOG_NAME, write_ducklake


@pytest.fixture
def ducklake_from_sample(sample_dta: Path, tmp_path: Path) -> Path:
    """Write sample .dta to DuckLake and return the catalog path."""
    catalog = tmp_path / "test.ducklake"
    stata_data = read_dta(sample_dta)
    write_ducklake(stata_data, catalog, "workers", partition_by=("year",))
    return catalog


def _connect(catalog: Path, alias: str = CATALOG_NAME) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("LOAD ducklake")
    con.execute(f"ATTACH 'ducklake:{catalog}' AS {alias}")
    con.execute(f"USE {alias}")
    return con


def _query(catalog: Path, sql: str, alias: str = CATALOG_NAME) -> list:
    con = _connect(catalog, alias)
    result = con.execute(sql).fetchall()
    con.close()
    return result


def test_data_round_trip(ducklake_from_sample: Path) -> None:
    rows = _query(ducklake_from_sample, "SELECT * FROM workers ORDER BY id")
    assert len(rows) == 3
    assert rows[0][0] == 1  # id
    assert rows[0][1] == 50000.0  # wage


def test_column_comments(ducklake_from_sample: Path) -> None:
    rows = _query(
        ducklake_from_sample,
        f"SELECT column_name, comment FROM duckdb_columns() "
        f"WHERE database_name='{CATALOG_NAME}' AND table_name='workers' "
        f"ORDER BY column_name",
    )
    comments = {r[0]: r[1] for r in rows}
    assert comments["id"] == "Worker ID"
    assert comments["wage"] == "Annual wage (USD)"
    assert comments["gender"] == "Gender code"
    assert comments["year"] == "Survey year"


def test_value_label_table(ducklake_from_sample: Path) -> None:
    rows = _query(
        ducklake_from_sample,
        "SELECT value, label FROM value_label_gender ORDER BY value",
    )
    assert rows == [(1, "Male"), (2, "Female")]


def test_partitioned_data_queryable(ducklake_from_sample: Path) -> None:
    rows = _query(
        ducklake_from_sample,
        "SELECT count(*) FROM workers WHERE year = 2020",
    )
    assert rows[0][0] == 2


def test_no_partition(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "no_part.ducklake"
    stata_data = read_dta(sample_dta)
    write_ducklake(stata_data, catalog, "workers")
    rows = _query(catalog, "SELECT count(*) FROM workers")
    assert rows[0][0] == 3


def test_labels_macro(ducklake_from_sample: Path) -> None:
    rows = _query(
        ducklake_from_sample,
        "SELECT * FROM labels('workers') ORDER BY column_name",
    )
    # columns: column_name, data_type, value_label, variable_label
    result = {r[0]: (r[1], r[2], r[3]) for r in rows}
    assert result["id"] == ("INTEGER", None, "Worker ID")
    assert result["wage"] == ("DOUBLE", None, "Annual wage (USD)")
    assert result["gender"] == ("INTEGER", "gender", "Gender code")
    assert result["year"][1] is None
    assert result["year"][2] == "Survey year"


def test_decode_macro(ducklake_from_sample: Path) -> None:
    rows = _query(ducklake_from_sample, "SELECT decode('gender', 1)")
    assert rows[0][0] == "Male"

    rows = _query(ducklake_from_sample, "SELECT decode('gender', 2)")
    assert rows[0][0] == "Female"


def test_decode_in_query(ducklake_from_sample: Path) -> None:
    rows = _query(
        ducklake_from_sample,
        "SELECT id, decode('gender', gender) AS gender_label "
        "FROM workers ORDER BY id",
    )
    assert rows[0] == (1, "Male")
    assert rows[1] == (2, "Female")
    assert rows[2] == (3, "Male")


def test_macros_portable_across_alias(ducklake_from_sample: Path) -> None:
    """Macros work when catalog is attached with any alias, after USE."""
    rows = _query(
        ducklake_from_sample,
        "SELECT * FROM labels('workers') ORDER BY column_name",
        alias="dl",
    )
    result = {r[0]: (r[1], r[2], r[3]) for r in rows}
    assert result["id"] == ("INTEGER", None, "Worker ID")
    assert result["gender"] == ("INTEGER", "gender", "Gender code")

    rows = _query(
        ducklake_from_sample,
        "SELECT decode('gender', 1)",
        alias="dl",
    )
    assert rows[0][0] == "Male"

    rows = _query(
        ducklake_from_sample,
        "SELECT id, decode('gender', gender) AS gender_label "
        "FROM workers ORDER BY id",
        alias="dl",
    )
    assert rows[0] == (1, "Male")
