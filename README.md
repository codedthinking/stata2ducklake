# stata2ducklake

Convert Stata `.dta` files into partitioned Parquet with DuckLake metadata.

## Install

```bash
uv pip install .
```

## Usage

```bash
# Single file
stata2ducklake data.dta catalog.ducklake

# With partitioning and custom table name
stata2ducklake data.dta catalog.ducklake --partition-by year --partition-by region --table-name my_table

# Multiple files into one catalog
stata2ducklake workers.dta firms.dta catalog.ducklake

# Verbose output (shows variable labels and value label details)
stata2ducklake data.dta catalog.ducklake -v

# Quiet mode
stata2ducklake data.dta catalog.ducklake -q
```

## What it does

1. Reads `.dta` files (via pandas) including variable labels and value labels.
2. Creates a DuckLake catalog and writes each file as a table with Parquet storage.
3. Stores variable labels as column comments.
4. Creates `value_label_<name>` lookup tables for each value label set (with `value` and `label` columns).
5. Optionally partitions tables by specified columns.

## Querying the output

```bash
duckdb -c "
  LOAD ducklake;
  ATTACH 'ducklake:catalog.ducklake' AS dl;
  SELECT * FROM dl.my_table LIMIT 10;
"
```

## Development

```bash
uv pip install -e '.[dev]'
pytest
```
