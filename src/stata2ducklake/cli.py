"""CLI entry point for stata2ducklake."""

from pathlib import Path

import click

from stata2ducklake.reader import read_dta
from stata2ducklake.writer import write_ducklake


@click.command()
@click.argument("dta_paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.argument("ducklake_path", type=click.Path())
@click.option("--partition-by", multiple=True, help="Columns to partition by.")
@click.option(
    "--table-name",
    default=None,
    help="Target table name (default: stem of .dta file). Only valid with a single input file.",
)
def main(
    dta_paths: tuple[str, ...],
    ducklake_path: str,
    partition_by: tuple[str, ...],
    table_name: str | None,
) -> None:
    """Convert Stata .dta files into partitioned Parquet with DuckLake metadata."""
    if table_name and len(dta_paths) > 1:
        raise click.UsageError("--table-name can only be used with a single input file.")

    for dta_path in dta_paths:
        path = Path(dta_path)
        name = table_name or path.stem
        stata_data = read_dta(path)
        write_ducklake(stata_data, ducklake_path, name, partition_by)
        n_labels = len(stata_data.value_labels)
        click.echo(
            f"{path.name} -> {name}: "
            f"{len(stata_data.data)} rows, "
            f"{len(stata_data.data.columns)} cols"
            + (f", partitioned by {', '.join(partition_by)}" if partition_by else "")
            + (f", {n_labels} value label table(s)" if n_labels else "")
        )
