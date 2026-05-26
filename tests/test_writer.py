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


def _query(catalog: Path, sql: str) -> list:
    con = duckdb.connect()
    con.execute("LOAD ducklake")
    con.execute(f"ATTACH 'ducklake:{catalog}' AS {CATALOG_NAME}")
    result = con.execute(sql).fetchall()
    con.close()
    return result


def test_data_round_trip(ducklake_from_sample: Path) -> None:
    rows = _query(ducklake_from_sample, f"SELECT * FROM {CATALOG_NAME}.workers ORDER BY id")
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
        f"SELECT value, label FROM {CATALOG_NAME}.value_label_gender ORDER BY value",
    )
    assert rows == [(1, "Male"), (2, "Female")]


def test_partitioned_data_queryable(ducklake_from_sample: Path) -> None:
    rows = _query(
        ducklake_from_sample,
        f"SELECT count(*) FROM {CATALOG_NAME}.workers WHERE year = 2020",
    )
    assert rows[0][0] == 2


def test_no_partition(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "no_part.ducklake"
    stata_data = read_dta(sample_dta)
    write_ducklake(stata_data, catalog, "workers")
    rows = _query(catalog, f"SELECT count(*) FROM {CATALOG_NAME}.workers")
    assert rows[0][0] == 3
