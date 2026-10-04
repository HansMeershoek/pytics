"""Internal analysis of one pandas DataFrame.

Each physical column is analyzed once, in source order. The result keeps
dataset dimensions, the column analyses, missing-cell totals derived from
basic evidence already retained, the exact missingness aggregates
collected from one DataFrame pass, the exact duplicate-row groups
collected from a separate pass, and the heterogeneous relationship
records collected from selected semantic types, the univariate
numeric anomaly evidence read from the retained numeric profiles,
and, when the caller names one, the target projection of those facts,
the leakage evidence for that target, and the diagnostic model of that
target. It does not keep the DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from typing import Tuple

import pandas as pd

from pytics.analysis.anomaly import AnomalyAnalysis
from pytics.analysis.anomaly import _require_anomaly_attachment
from pytics.analysis.anomaly import collect_anomaly_analysis
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import analyze_series
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.duplicate import _require_duplicate_attachment
from pytics.analysis.duplicate import collect_duplicate_analysis
from pytics.analysis.missing import MissingAnalysis
from pytics.analysis.missing import _require_missing_attachment
from pytics.analysis.missing import collect_missing_analysis
from pytics.analysis.relationship import RelationshipAnalysis
from pytics.analysis.relationship import _require_relationship_attachment
from pytics.analysis.relationship import collect_relationship_analysis
from pytics.analysis.target import TargetAnalysis
from pytics.analysis.target import _require_target_attachment
from pytics.analysis.target import project_target_analysis
from pytics.analysis.target import resolve_target_position
from pytics.analysis.target_diagnostic import TargetDiagnosticAnalysis
from pytics.analysis.target_diagnostic import _require_diagnostic_attachment
from pytics.analysis.target_diagnostic_fit import analyze_target_diagnostic
from pytics.analysis.target_leakage import TargetLeakageAnalysis
from pytics.analysis.target_leakage import _require_exact_duplicate_consumption
from pytics.analysis.target_leakage import _require_leakage_attachment
from pytics.analysis.target_leakage import analyze_target_leakage


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
    missingness patterns. ``duplicate_analysis`` is the retained exact
    duplicate groups. ``relationship_analysis`` is the retained
    heterogeneous relationship records and the pair-coverage counts.
    It does not name one method for every pair. ``anomaly_analysis``
    is the retained univariate numeric anomaly evidence. Its quartiles
    are the numeric profiles already stored on the columns. It does not
    read the relationship, missingness, duplicate, or target results.
    All four are cross-column, so they are not derived from one column
    record. The missingness mask, the row values, and the paired arrays
    are not stored. The passes do not call each other.

    ``target_analysis`` is ``None`` when the caller did not name a
    target. When it is present, it is a projection of the selected
    column and of the relationship records already stored here. It is
    not a second statistical pass.

    ``target_leakage`` and ``target_diagnostic`` are present exactly when
    ``target_analysis`` is. Leakage evidence is collected before the
    diagnostic model and does not read relationship records. The
    diagnostic model excludes a predictor that leakage evidence records
    as an exact duplicate. An unavailable model is a status on the
    diagnostic record and does not change ``target_analysis`` or the
    leakage evidence.
    """

    n_rows: int
    n_columns: int
    n_cells: int
    columns: Tuple[ColumnAnalysis, ...]
    missing_analysis: MissingAnalysis
    duplicate_analysis: DuplicateAnalysis
    relationship_analysis: RelationshipAnalysis
    anomaly_analysis: AnomalyAnalysis
    target_analysis: Optional[TargetAnalysis] = None
    target_leakage: Optional[TargetLeakageAnalysis] = None
    target_diagnostic: Optional[TargetDiagnosticAnalysis] = None

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
        _require_duplicate_attachment(
            self.duplicate_analysis,
            n_rows=self.n_rows,
            n_columns=self.n_columns,
        )
        _require_relationship_attachment(
            self.relationship_analysis,
            self.columns,
            n_rows=self.n_rows,
        )
        _require_target_attachment(
            self.target_analysis,
            self.columns,
            self.relationship_analysis.relationships,
            n_rows=self.n_rows,
        )
        _require_leakage_attachment(
            self.target_leakage,
            self.target_analysis,
            self.columns,
        )
        _require_diagnostic_attachment(
            self.target_diagnostic,
            self.target_analysis,
            self.columns,
        )
        _require_exact_duplicate_consumption(
            self.target_leakage,
            self.target_diagnostic,
        )
        _require_anomaly_attachment(
            self.anomaly_analysis,
            self.columns,
            n_rows=self.n_rows,
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


def analyze_dataframe(
    frame: pd.DataFrame,
    *,
    target: object = None,
) -> DatasetAnalysis:
    """Analyze each physical column of a DataFrame once.

    The argument must already be a pandas DataFrame. Other inputs are not
    converted. Column order is the DataFrame's column order. Duplicate
    labels stay distinct records. After the column analyses, the
    relationship pass describes the pairs of each calculated family.
    Anomaly analysis then locates finite numeric values outside the
    retained Tukey fences. It does not read the other passes. When a
    target was named, the target projection, leakage evidence, and
    diagnostic model run next, in that order. Missingness patterns
    and exact duplicate rows are collected when the result is built.
    Those passes do not call each other. The DataFrame is not copied
    and is not modified, and it is not stored on the result.

    ``target`` requests one column. ``None`` requests no target analysis.
    A label must match exactly one column. ``TargetPosition`` selects a
    physical position when labels are duplicated. A missing or ambiguous
    target raises. It does not guess a column, and it does not return a
    dataset with target analysis disabled. The target projection reads
    retained records and does not calculate them again. Leakage evidence
    reads the frame and does not read relationship records. The
    diagnostic model reads the frame, consumes exact-duplicate positions
    from the leakage result, and does not change the target projection,
    the leakage evidence, or the relationship records.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("analyze_dataframe expects a pandas DataFrame")
    target_position = None
    if target is not None:
        target_position = resolve_target_position(frame.columns, target)
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
    relationship_analysis = collect_relationship_analysis(frame, columns)
    anomaly_analysis = collect_anomaly_analysis(frame, columns)
    target_analysis = None
    target_leakage = None
    target_diagnostic = None
    if target_position is not None:
        target_analysis = project_target_analysis(
            columns,
            relationship_analysis.relationships,
            position=target_position,
            n_rows=n_rows,
        )
        target_leakage = analyze_target_leakage(frame, columns, target_analysis)
        target_diagnostic = analyze_target_diagnostic(
            frame,
            columns,
            target_analysis,
            target_leakage,
        )
    return DatasetAnalysis(
        n_rows=n_rows,
        n_columns=n_columns,
        n_cells=n_rows * n_columns,
        columns=columns,
        missing_analysis=collect_missing_analysis(frame),
        duplicate_analysis=collect_duplicate_analysis(frame),
        relationship_analysis=relationship_analysis,
        anomaly_analysis=anomaly_analysis,
        target_analysis=target_analysis,
        target_leakage=target_leakage,
        target_diagnostic=target_diagnostic,
    )


def _require_count(value: int, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")
