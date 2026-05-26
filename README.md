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

### Stata-like SQL macros

The catalog includes two SQL macros for working with Stata metadata directly in DuckDB.

**`describe('table_name')`** — list columns with their types and variable labels:

```sql
SELECT * FROM dl.describe('workers');
```
```
┌─────────────┬───────────┬────────────────────┐
│ column_name │ data_type │  variable_label    │
├─────────────┼───────────┼────────────────────┤
│ id          │ INTEGER   │ Worker ID          │
│ wage        │ DOUBLE    │ Annual wage (USD)  │
│ gender      │ INTEGER   │ Gender code        │
│ year        │ INTEGER   │ Survey year        │
└─────────────┴───────────┴────────────────────┘
```

**`decode('label_name', value)`** — look up a value label, usable in any expression:

```sql
SELECT id, dl.decode('gender', gender) AS gender_label
FROM dl.workers;
```
```
┌────┬──────────────┐
│ id │ gender_label │
├────┼──────────────┤
│  1 │ Male         │
│  2 │ Female       │
│  3 │ Male         │
└────┴──────────────┘
```

### Metadata details

- **Variable labels** are stored as column comments on each table.
- **Value labels** are stored in separate lookup tables named `value_label_<name>`, each with `value` (integer) and `label` (text) columns.

## License

MIT. See [LICENSE](LICENSE).
