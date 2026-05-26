# stata2ducklake

Convert Stata `.dta` files into partitioned Parquet files with a [DuckLake](https://ducklake.select/) metadata catalog. Preserves variable labels (as column comments) and value labels (as lookup tables).

## Install

```bash
uv pip install git+https://github.com/codedthinking/stata2ducklake.git
```

Or from a local clone:

```bash
git clone https://github.com/codedthinking/stata2ducklake.git
cd stata2ducklake
uv pip install .
```

Requires Python 3.11+.

## Usage

```bash
# Convert a single file
stata2ducklake data.dta catalog.ducklake

# Partition by one or more columns
stata2ducklake data.dta catalog.ducklake --partition-by year --partition-by region

# Choose a table name (default: filename without extension)
stata2ducklake data.dta catalog.ducklake --table-name survey_2020

# Convert multiple files into one catalog (each becomes a separate table)
stata2ducklake workers.dta firms.dta catalog.ducklake

# Verbose: show variable labels and value label details
stata2ducklake data.dta catalog.ducklake -v

# Quiet: suppress all output
stata2ducklake data.dta catalog.ducklake -q
```

## What you get

The command creates a `.ducklake` metadata catalog and a `.ducklake.files/` directory containing Parquet data files. You can query the result with DuckDB:

```bash
duckdb -c "
  LOAD ducklake;
  ATTACH 'ducklake:catalog.ducklake' AS dl;
  SELECT * FROM dl.data LIMIT 10;
"
```

### Metadata preserved from Stata

- **Variable labels** are stored as column comments. Query them with:
  ```sql
  SELECT column_name, comment FROM duckdb_columns()
  WHERE database_name = 'dl';
  ```
- **Value labels** are stored in separate lookup tables named `value_label_<name>`, each with `value` (integer) and `label` (text) columns. For example, if the `.dta` file has a value label `gender` mapping `1 → Male, 2 → Female`, the catalog will contain a table `value_label_gender`.

## License

MIT. See [LICENSE](LICENSE).
