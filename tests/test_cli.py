"""Tests for stata2ducklake.cli."""

from pathlib import Path

import duckdb
from click.testing import CliRunner

from stata2ducklake.cli import main
from stata2ducklake.writer import CATALOG_NAME


def _query(catalog: Path, sql: str) -> list:
    con = duckdb.connect()
    con.execute("LOAD ducklake")
    con.execute(f"ATTACH 'ducklake:{catalog}' AS {CATALOG_NAME}")
    result = con.execute(sql).fetchall()
    con.close()
    return result


def test_single_file(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(main, [str(sample_dta), str(catalog)])
    assert result.exit_code == 0
    assert "sample.dta -> sample:" in result.output
    assert "3 rows" in result.output
    rows = _query(catalog, f"SELECT count(*) FROM {CATALOG_NAME}.sample")
    assert rows[0][0] == 3


def test_custom_table_name(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(
        main, [str(sample_dta), str(catalog), "--table-name", "workers"]
    )
    assert result.exit_code == 0
    assert "sample.dta -> workers:" in result.output
    rows = _query(catalog, f"SELECT count(*) FROM {CATALOG_NAME}.workers")
    assert rows[0][0] == 3


def test_partition_by(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(
        main, [str(sample_dta), str(catalog), "--partition-by", "year"]
    )
    assert result.exit_code == 0
    assert "partitioned by year" in result.output


def test_multiple_files(sample_dta: Path, tmp_path: Path) -> None:
    # Create a second .dta
    import pandas as pd

    second = tmp_path / "other.dta"
    pd.DataFrame({"x": [1, 2]}).to_stata(second, write_index=False)

    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(main, [str(sample_dta), str(second), str(catalog)])
    assert result.exit_code == 0
    assert "sample.dta -> sample:" in result.output
    assert "other.dta -> other:" in result.output


def test_table_name_with_multiple_files_errors(sample_dta: Path, tmp_path: Path) -> None:
    import pandas as pd

    second = tmp_path / "other.dta"
    pd.DataFrame({"x": [1, 2]}).to_stata(second, write_index=False)

    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(
        main, [str(sample_dta), str(second), str(catalog), "--table-name", "t"]
    )
    assert result.exit_code != 0
    assert "--table-name" in result.output


def test_value_label_output(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(main, [str(sample_dta), str(catalog)])
    assert "1 value label table(s)" in result.output


def test_invalid_partition_column(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(
        main, [str(sample_dta), str(catalog), "--partition-by", "nonexistent"]
    )
    assert result.exit_code != 0
    assert "nonexistent" in result.output


def test_quiet_flag(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(main, [str(sample_dta), str(catalog), "-q"])
    assert result.exit_code == 0
    assert result.output == ""


def test_verbose_flag(sample_dta: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "out.ducklake"
    result = CliRunner().invoke(main, [str(sample_dta), str(catalog), "-v"])
    assert result.exit_code == 0
    assert "Worker ID" in result.output
    assert "value_label_gender: 2 entries" in result.output
