"""Read Stata .dta files and extract data + metadata."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class StataData:
    """Data and metadata extracted from a .dta file."""

    data: pd.DataFrame
    variable_labels: dict[str, str]
    value_labels: dict[str, dict[int, str]]
    column_to_label: dict[str, str]


def read_dta(path: str | Path) -> StataData:
    """Read a .dta file and return data with all metadata.

    Args:
        path: Path to the .dta file.

    Returns:
        StataData with the DataFrame, variable labels, value labels,
        and column-to-value-label mapping.
    """
    path = Path(path)

    # First pass: read with categoricals to populate the value label dict
    with pd.io.stata.StataReader(path, convert_categoricals=True) as reader:
        reader.read()
        value_labels = {
            name: {int(k): v for k, v in mapping.items()}
            for name, mapping in reader._value_label_dict.items()
        }

    # Second pass: read without categoricals to get raw numeric data + metadata
    with pd.io.stata.StataReader(path, convert_categoricals=False) as reader:
        df = reader.read()
        variable_labels = dict(zip(reader._varlist, reader._variable_labels))
        variable_labels = {k: v for k, v in variable_labels.items() if v}
        column_to_label = {
            col: lbl
            for col, lbl in zip(reader._varlist, reader._lbllist)
            if lbl
        }

    return StataData(
        data=df,
        variable_labels=variable_labels,
        value_labels=value_labels,
        column_to_label=column_to_label,
    )
