"""Internal analysis of one pandas DataFrame.

Each physical column is analyzed once, in source order. The result keeps
dataset dimensions, the column analyses, missing-cell totals derived from
basic evidence already retained, and the exact missingness aggregates
collected from one DataFrame pass. It does not keep the DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from typing import Tuple

import pandas as pd

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import analyze_series
from pytics.analysis.missing import MissingAnalysis
from pytics.analysis.missing import _require_missing_attachment
from pytics.analysis.missing import collect_missing_analysis


@dataclass(frozen=True)
class DatasetAnalysis:
    """Internal analysis of one DataFrame.

    ``n_rows``, ``n_columns``, and ``n_cells`` are stored dimensions.
    ``n_cells`` is ``n_rows * n_columns``. ``columns`` has one record per
    physical column, in source order, including duplicate labels.

    ``n_missing_cells``, ``n_non_missing_cells``, and ``missing_ratio``
    are read from those dimensions and from each column's basic evidence.
    They are not stored. ``missing_ratio`` is ``None`` when ``n_cells``
    is zero.

    ``missing_analysis`` is the retained row distribution and exact
    missingness patterns. Those facts are cross-column, so they are not
    derived from the column records. The boolean mask is not stored.
    """

    n_rows: int
    n_columns: int
    n_cells: int
    columns: Tuple[ColumnAnalysis, ...]
    missing_analysis: MissingAnalysis

    def __post_init__(self) -> None:
        _require_count(self.n_rows, "n_rows")
        _require_count(self.n_columns, "n_columns")
        _require_count(self.n_cells, "n_cells")
        if self.n_cells != self.n_rows * self.n_columns:
            raise ValueError("n_cells must equal n_rows * n_columns")
        if not isinstance(self.columns, tuple):
            raise TypeError("columns must be a tuple")
        if len(self.columns) != self.n_columns:
            raise ValueError("columns must contain one record per column")
        for position, column in enumerate(self.columns):
            if not isinstance(column, ColumnAnalysis):
                raise TypeError("columns must contain ColumnAnalysis records")
            if column.position != position:
                raise ValueError("column position must match dataset column order")
            if column.evidence.basic.n_total != self.n_rows:
                raise ValueError("column n_total must equal n_rows")
        _require_missing_attachment(
            self.missing_analysis,
            n_rows=self.n_rows,
            n_columns=self.n_columns,
            n_missing_cells=self.n_missing_cells,
            missing_counts=tuple(
                column.evidence.basic.n_missing for column in self.columns
            ),
        )

    @property
    def n_missing_cells(self) -> int:
        """Missing cells, summed from retained basic evidence."""
        return sum(column.evidence.basic.n_missing for column in self.columns)

    @property
    def n_non_missing_cells(self) -> int:
        """Cells that are not missing.

        Zero when the frame has no cells. This count is defined when the
        missing ratio is not.
        """
        return self.n_cells - self.n_missing_cells

    @property
    def missing_ratio(self) -> Optional[float]:
        """Missing cells divided by all cells.

        ``None`` when there are no cells. A zero numerator with a positive
        cell count is ``0.0``.
        """
        if self.n_cells == 0:
            return None
        return self.n_missing_cells / self.n_cells


def analyze_dataframe(frame: pd.DataFrame) -> DatasetAnalysis:
    """Analyze each physical column of a DataFrame once.

    The argument must already be a pandas DataFrame. Other inputs are not
    converted. Column order is the DataFrame's column order. Duplicate
    labels stay distinct records. After the column analyses, one
    missingness pass counts exact row patterns. The DataFrame is not
    copied and is not modified, and it is not stored on the result.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("analyze_dataframe expects a pandas DataFrame")
    n_rows = frame.shape[0]
    n_columns = frame.shape[1]
    columns = tuple(
        analyze_series(
            frame.iloc[:, position],
            position=position,
            label=frame.columns[position],
        )
        for position in range(n_columns)
    )
    return DatasetAnalysis(
        n_rows=n_rows,
        n_columns=n_columns,
        n_cells=n_rows * n_columns,
        columns=columns,
        missing_analysis=collect_missing_analysis(frame),
    )


def _require_count(value: int, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")
