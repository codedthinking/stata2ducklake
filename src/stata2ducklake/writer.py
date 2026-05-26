"""Write data and metadata into DuckLake."""

from pathlib import Path

import duckdb

from stata2ducklake.reader import StataData

CATALOG_NAME = "ducklake_catalog"


def _qi(name: str) -> str:
    """Quote a SQL identifier."""
    return '"' + name.replace('"', '""') + '"'


def table_exists(ducklake_path: str | Path, table_name: str) -> bool:
    """Check if a table already exists in the DuckLake catalog."""
    con = duckdb.connect()
    try:
        con.execute("INSTALL ducklake")
        con.execute("LOAD ducklake")
        con.execute(
            f"ATTACH 'ducklake:{ducklake_path}' AS {CATALOG_NAME}"
        )
        rows = con.execute(
            f"SELECT count(*) FROM duckdb_tables() "
            f"WHERE database_name = '{CATALOG_NAME}' AND table_name = '{table_name}'"
        ).fetchone()
        return rows[0] > 0
    except Exception:
        return False
    finally:
        con.close()


def write_ducklake(
    stata_data: StataData,
    ducklake_path: str | Path,
    table_name: str,
    partition_by: tuple[str, ...] = (),
    force: bool = False,
) -> None:
    """Write StataData into a DuckLake catalog.

    Creates the main data table, sets column comments from variable labels,
    creates value_label_<name> lookup tables, and optionally partitions.
    SQL macros (labels, decode) are created with unqualified table
    references so they work regardless of the attach alias.

    Args:
        stata_data: Data and metadata from read_dta.
        ducklake_path: Path to the DuckLake metadata file.
        table_name: Name for the target table.
        partition_by: Column names to partition by.
        force: If True, drop existing table before creating.
    """
    con = duckdb.connect()
    try:
        con.execute("INSTALL ducklake")
        con.execute("LOAD ducklake")
        con.execute(
            f"ATTACH 'ducklake:{ducklake_path}' AS {CATALOG_NAME}"
        )
        con.execute(f"USE {CATALOG_NAME}")

        if force:
            con.execute(f"DROP TABLE IF EXISTS {_qi(table_name)}")
            for label_name in stata_data.value_labels:
                con.execute(f"DROP TABLE IF EXISTS {_qi(f'value_label_{label_name}')}")
            if _meta_table_exists(con):
                con.execute(
                    "DELETE FROM _column_value_labels WHERE table_name = $1",
                    [table_name],
                )

        _create_data_table(con, stata_data, table_name)
        _set_partition_keys(con, table_name, partition_by)
        _add_column_comments(con, stata_data, table_name)
        _create_value_label_tables(con, stata_data)
        _create_column_label_map(con, stata_data, table_name)
        _create_macros(con)
    finally:
        con.close()


def _meta_table_exists(con: duckdb.DuckDBPyConnection) -> bool:
    rows = con.execute(
        "SELECT count(*) FROM duckdb_tables() "
        f"WHERE database_name = '{CATALOG_NAME}' AND table_name = '_column_value_labels'"
    ).fetchone()
    return rows[0] > 0


def _create_data_table(
    con: duckdb.DuckDBPyConnection,
    stata_data: StataData,
    table_name: str,
) -> None:
    con.register("_df", stata_data.data)
    con.execute(
        f"CREATE TABLE {_qi(table_name)} AS SELECT * FROM _df"
    )
    con.unregister("_df")


def _set_partition_keys(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    partition_by: tuple[str, ...],
) -> None:
    if not partition_by:
        return
    cols = ", ".join(_qi(c) for c in partition_by)
    con.execute(
        f"ALTER TABLE {_qi(table_name)} SET PARTITIONED BY ({cols})"
    )


def _add_column_comments(
    con: duckdb.DuckDBPyConnection,
    stata_data: StataData,
    table_name: str,
) -> None:
    for col, label in stata_data.variable_labels.items():
        escaped = label.replace("'", "''")
        con.execute(
            f"COMMENT ON COLUMN {_qi(table_name)}.{_qi(col)} IS '{escaped}'"
        )


def _create_value_label_tables(
    con: duckdb.DuckDBPyConnection,
    stata_data: StataData,
) -> None:
    for label_name, mapping in stata_data.value_labels.items():
        tbl = _qi(f"value_label_{label_name}")
        con.execute(
            f"CREATE TABLE {tbl} (value INTEGER, label VARCHAR)"
        )
        for value, label in mapping.items():
            escaped = label.replace("'", "''")
            con.execute(
                f"INSERT INTO {tbl} VALUES ({value}, '{escaped}')"
            )


def _create_column_label_map(
    con: duckdb.DuckDBPyConnection,
    stata_data: StataData,
    table_name: str,
) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS _column_value_labels (
            table_name VARCHAR,
            column_name VARCHAR,
            label_name VARCHAR
        )
    """)
    for col, lbl in stata_data.column_to_label.items():
        escaped_tbl = table_name.replace("'", "''")
        escaped_col = col.replace("'", "''")
        escaped_lbl = lbl.replace("'", "''")
        con.execute(
            f"INSERT INTO _column_value_labels VALUES ('{escaped_tbl}', '{escaped_col}', '{escaped_lbl}')"
        )


def _create_macros(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE OR REPLACE MACRO labels(tbl) AS TABLE
        SELECT
            c.column_name,
            c.data_type,
            m.label_name AS value_label,
            c.comment AS variable_label
        FROM duckdb_columns() c
        LEFT JOIN _column_value_labels m
            ON m.table_name = tbl
            AND m.column_name = c.column_name
        WHERE c.database_name = current_catalog()
            AND c.table_name = tbl
    """)
    con.execute("""
        CREATE OR REPLACE MACRO decode(lbl, val) AS (
            SELECT label FROM query_table('value_label_' || lbl)
            WHERE value = val
        )
    """)
