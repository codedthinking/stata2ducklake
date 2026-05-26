# Contributing

## Setup

```bash
git clone https://github.com/codedthinking/stata2ducklake.git
cd stata2ducklake
uv venv
uv pip install -e '.[dev]'
```

## Running tests

```bash
pytest
```

## Project structure

```
src/stata2ducklake/
├── cli.py      # Click CLI entry point
├── reader.py   # Read .dta files and extract metadata (via pandas)
└── writer.py   # Write data and metadata into DuckLake (via duckdb)
tests/
├── conftest.py     # Shared fixtures (sample .dta file)
├── test_reader.py
├── test_writer.py
└── test_cli.py
```

## Guidelines

- Keep tests alongside the code they test. Each module has a corresponding `test_<module>.py`.
- Run the full test suite before submitting a PR.
- Use type annotations for function signatures.
