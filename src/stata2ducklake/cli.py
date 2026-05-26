"""CLI entry point for stata2ducklake."""

import click


@click.command()
@click.argument("dta_path", type=click.Path(exists=True))
@click.argument("ducklake_path", type=click.Path())
@click.option("--partition-by", multiple=True, help="Columns to partition by.")
@click.option("--table-name", default=None, help="Target table name (default: stem of .dta file).")
def main(dta_path: str, ducklake_path: str, partition_by: tuple[str, ...], table_name: str | None) -> None:
    """Convert a Stata .dta file into partitioned Parquet with DuckLake metadata."""
    raise NotImplementedError
