# stata2ducklake

Convert Stata `.dta` files into partitioned Parquet files with a [DuckLake](https://ducklake.select/) metadata catalog. Preserves variable labels (as column comments) and value labels (as lookup tables).

## Install

```bash
uv tool install git+https://github.com/codedthinking/stata2ducklake.git
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
  USE dl;
  SELECT * FROM data LIMIT 10;
"
```

### Stata-like SQL macros

The catalog includes two SQL macros for working with Stata metadata directly in DuckDB. Run `USE <catalog>` after attaching to make them available.

**`labels('table_name')`** — list columns with their types, value labels, and variable labels (like Stata's `describe`):

```sql
SELECT * FROM labels('workers');
```
```
┌─────────────┬───────────┬─────────────┬────────────────────┐
│ column_name │ data_type │ value_label │  variable_label    │
├─────────────┼───────────┼─────────────┼────────────────────┤
│ id          │ INTEGER   │             │ Worker ID          │
│ wage        │ DOUBLE    │             │ Annual wage (USD)  │
│ gender      │ INTEGER   │ gender      │ Gender code        │
│ year        │ INTEGER   │             │ Survey year        │
└─────────────┴───────────┴─────────────┴────────────────────┘
```

**`decode('label_name', value)`** — look up a value label, usable in any expression:

```sql
SELECT id, decode('gender', gender) AS gender_label
FROM workers;
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
- **Value labels** are stored in separate lookup tables named `value_label_<name>`, each with `value` (integer) and `label` (text) columns. These tables are typically small enough that DuckLake inlines them directly in the metadata catalog rather than writing separate Parquet files — this is expected and they are fully queryable.

## License

MIT. See [LICENSE](LICENSE).

## Trademark notice

Stata is a registered trademark of [StataCorp LLC](https://www.stata.com/). Coded Thinking OÜ is not affiliated with StataCorp LLC, and this software has not been reviewed or endorsed by StataCorp LLC.
