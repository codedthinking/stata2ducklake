# stata2ducklake

Convert Stata `.dta` files into partitioned Parquet with DuckLake metadata.

## Install

```bash
uv pip install .
```

## Usage

```bash
stata2ducklake data.dta catalog.ducklake --partition-by year --partition-by region --table-name my_table
```

## What it does

1. Reads the `.dta` file (via pandas) including variable labels and value labels.
2. Creates a DuckLake catalog and writes the data as partitioned Parquet.
3. Stores variable labels as column comments.
4. Creates `value_label_<name>` tables for each value label set, linked via PK-FK.
