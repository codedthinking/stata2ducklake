"""Write data and metadata into DuckLake."""

from pathlib import Path

import duckdb

from stata2ducklake.reader import StataData

CATALOG_NAME = "ducklake_catalog"


def write_ducklake(
    stata_data: StataData,
    ducklake_path: str | Path,
    table_name: str,
    partition_by: tuple[str, ...] = (),
) -> None:
    """Write StataData into a DuckLake catalog.

    Creates the main data table, sets column comments from variable labels,
    creates value_label_<name> lookup tables, and optionally partitions.

    Args:
        stata_data: Data and metadata from read_dta.
        ducklake_path: Path to the DuckLake metadata file.
        table_name: Name for the target table.
        partition_by: Column names to partition by.
    """
    con = duckdb.connect()
    try:
        con.execute("INSTALL ducklake")
        con.execute("LOAD ducklake")
        con.execute(
            f"ATTACH 'ducklake:{ducklake_path}' AS {CATALOG_NAME}"
        )

        _create_data_table(con, stata_data, table_name)
        _set_partition_keys(con, table_name, partition_by)
        _add_column_comments(con, stata_data, table_name)
        _create_value_label_tables(con, stata_data)
    finally:
        con.close()


def _create_data_table(
    con: duckdb.DuckDBPyConnection,
    stata_data: StataData,
    table_name: str,
) -> None:
    con.register("_df", stata_data.data)
    con.execute(
        f"CREATE TABLE {CATALOG_NAME}.{table_name} AS SELECT * FROM _df"
    )
    con.unregister("_df")


def _set_partition_keys(
    con: duckdb.DuckDBPyConnection,
    table_name: str,
    partition_by: tuple[str, ...],
) -> None:
    if not partition_by:
        return
    cols = ", ".join(partition_by)
    con.execute(
        f"ALTER TABLE {CATALOG_NAME}.{table_name} SET PARTITIONED BY ({cols})"
    )


def _add_column_comments(
    con: duckdb.DuckDBPyConnection,
    stata_data: StataData,
    table_name: str,
) -> None:
    for col, label in stata_data.variable_labels.items():
        escaped = label.replace("'", "''")
        con.execute(
            f"COMMENT ON COLUMN {CATALOG_NAME}.{table_name}.{col} IS '{escaped}'"
        )


def _create_value_label_tables(
    con: duckdb.DuckDBPyConnection,
    stata_data: StataData,
) -> None:
    for label_name, mapping in stata_data.value_labels.items():
        tbl = f"value_label_{label_name}"
        con.execute(
            f"CREATE TABLE {CATALOG_NAME}.{tbl} (value INTEGER, label VARCHAR)"
        )
        for value, label in mapping.items():
            escaped = label.replace("'", "''")
            con.execute(
                f"INSERT INTO {CATALOG_NAME}.{tbl} VALUES ({value}, '{escaped}')"
            )
