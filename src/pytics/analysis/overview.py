"""Dataset overview aggregated from an existing dataset analysis.

The builder reads stored dimensions, missing-cell totals, and each
column's resolved semantic state. It does not read a DataFrame, rescan
values, reclassify storage, recollect evidence, or choose a semantic
type. The result does not keep the analysis it was built from.

Semantic type counts include only types that at least one resolved
column selected. A zero count is omitted. Order is ``SemanticType``
definition order, which is a neutral enum order and not an importance
ranking. A selected type counts whether or not a confidence-bearing
interpretation exists.

Cell completeness is the complement of the missing-cell ratio. It is
not a complete-row ratio. Semantic-resolution coverage is resolved
columns divided by columns. Unique-row and excess-duplicate ratios use
the row count. Those ratios use different denominators, and each is
``None`` when its denominator is zero. Duplicate groups are not copied
onto the overview.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from pytics.analysis.dataset import DatasetAnalysis
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


@dataclass(frozen=True)
class ColumnRef:
    """Identity of one physical column inside an overview group.

    ``position`` is the column's place on the source column axis.
    ``label`` is the original label object. It is not rewritten into a
    display string. The label alone does not identify the column.
    """

    position: int
    label: object

    def __post_init__(self) -> None:
        if type(self.position) is not int or self.position < 0:
            raise ValueError("position must be a non-negative int")


@dataclass(frozen=True)
class SemanticTypeCount:
    """How many resolved columns selected one semantic type.

    ``count`` is at least one. A semantic type with no resolved column
    is omitted from the overview rather than stored as zero.
    """

    semantic_type: SemanticType
    count: int

    def __post_init__(self) -> None:
        if not isinstance(self.semantic_type, SemanticType):
            raise TypeError("semantic_type must be a SemanticType")
        if type(self.count) is not int or self.count < 1:
            raise ValueError("count must be a positive int")


@dataclass(frozen=True)
class DatasetOverview:
    """Compact dataset summary derived from one dataset analysis.

    Dimensions and cell counts are copies of facts the analysis already
    established. ``semantic_type_counts`` partitions resolved columns by
    the semantic type resolution selected. The column tuples name the
    physical columns in each notable or unresolved group, in source
    position order. Counts of those groups are the lengths of the tuples.

    ``completeness_ratio`` is cell completeness. ``semantic_resolution_ratio``
    is the share of columns whose semantic resolution selected a type.
    ``n_unique_rows`` and ``n_excess_duplicate_rows`` are copied from the
    retained duplicate analysis. Their ratios use ``n_rows``. None of
    these ratios is a quality score.
    """

    n_rows: int
    n_columns: int
    n_cells: int
    n_missing_cells: int
    n_non_missing_cells: int
    n_unique_rows: Optional[int]
    n_excess_duplicate_rows: Optional[int]
    semantic_type_counts: Tuple[SemanticTypeCount, ...]
    insufficient_evidence_columns: Tuple[ColumnRef, ...]
    ambiguous_columns: Tuple[ColumnRef, ...]
    empty_columns: Tuple[ColumnRef, ...]
    constant_columns: Tuple[ColumnRef, ...]
    identifier_columns: Tuple[ColumnRef, ...]

    def __post_init__(self) -> None:
        _require_count(self.n_rows, "n_rows")
        _require_count(self.n_columns, "n_columns")
        _require_count(self.n_cells, "n_cells")
        _require_count(self.n_missing_cells, "n_missing_cells")
        _require_count(self.n_non_missing_cells, "n_non_missing_cells")
        if self.n_cells != self.n_rows * self.n_columns:
            raise ValueError("n_cells must equal n_rows * n_columns")
        if self.n_missing_cells + self.n_non_missing_cells != self.n_cells:
            raise ValueError("missing and non-missing cells must sum to n_cells")
        unique_rows = self.n_unique_rows
        excess_rows = self.n_excess_duplicate_rows
        if unique_rows is None or excess_rows is None:
            if unique_rows is not None or excess_rows is not None:
                raise ValueError(
                    "n_unique_rows and n_excess_duplicate_rows are both known "
                    "or both unavailable"
                )
        else:
            _require_count(unique_rows, "n_unique_rows")
            _require_count(excess_rows, "n_excess_duplicate_rows")
            if unique_rows > self.n_rows:
                raise ValueError("n_unique_rows cannot exceed n_rows")
            if excess_rows != self.n_rows - unique_rows:
                raise ValueError(
                    "n_excess_duplicate_rows must equal n_rows - n_unique_rows"
                )
            if self.n_rows > 0 and unique_rows < 1:
                raise ValueError("a dataset with rows has at least one unique row")
        counts = _validate_semantic_counts(self.semantic_type_counts)
        groups = (
            ("insufficient_evidence_columns", self.insufficient_evidence_columns),
            ("ambiguous_columns", self.ambiguous_columns),
            ("empty_columns", self.empty_columns),
            ("constant_columns", self.constant_columns),
            ("identifier_columns", self.identifier_columns),
        )
        occupied: Set[int] = set()
        for field, group in groups:
            positions = _validate_column_group(group, field, self.n_columns)
            if occupied.intersection(positions):
                raise ValueError(
                    f"{field} repeats a column already named in another group"
                )
            occupied.update(positions)
        _require_group_count(self.empty_columns, counts, SemanticType.EMPTY, "empty")
        _require_group_count(
            self.constant_columns,
            counts,
            SemanticType.CONSTANT,
            "constant",
        )
        _require_group_count(
            self.identifier_columns,
            counts,
            SemanticType.IDENTIFIER,
            "identifier",
        )
        resolved = sum(item.count for item in counts)
        unresolved = len(self.insufficient_evidence_columns) + len(
            self.ambiguous_columns
        )
        if resolved + unresolved != self.n_columns:
            raise ValueError(
                "resolved, insufficient-evidence, and ambiguous columns "
                "must sum to n_columns"
            )

    @property
    def missing_ratio(self) -> Optional[float]:
        """Missing cells divided by all cells.

        ``None`` when there are no cells. A zero numerator with a
        positive cell count is ``0.0``.
        """
        if self.n_cells == 0:
            return None
        return self.n_missing_cells / self.n_cells

    @property
    def completeness_ratio(self) -> Optional[float]:
        """Non-missing cells divided by all cells.

        This is cell completeness, not a complete-row ratio. ``None``
        when there are no cells. When the cell count is positive, this
        ratio and ``missing_ratio`` sum to ``1`` within ordinary
        floating-point arithmetic.
        """
        if self.n_cells == 0:
            return None
        return self.n_non_missing_cells / self.n_cells

    @property
    def unique_row_ratio(self) -> Optional[float]:
        """Distinct row values divided by all rows.

        ``None`` when there are no rows, and ``None`` when the distinct
        row count is unavailable. This is the same ratio as the duplicate
        summary when that count is known. It is not a quality score.
        ``None`` is not zero.
        """
        if self.n_rows == 0 or self.n_unique_rows is None:
            return None
        return self.n_unique_rows / self.n_rows

    @property
    def excess_duplicate_row_ratio(self) -> Optional[float]:
        """Excess duplicate rows divided by all rows.

        ``None`` when there are no rows, and ``None`` when the excess
        count is unavailable. Excess rows are occurrences beyond one of
        each distinct row value. ``None`` is not zero.
        """
        if self.n_rows == 0 or self.n_excess_duplicate_rows is None:
            return None
        return self.n_excess_duplicate_rows / self.n_rows

    @property
    def resolved_column_count(self) -> int:
        """Columns whose resolution selected a semantic type."""
        return sum(item.count for item in self.semantic_type_counts)

    @property
    def insufficient_evidence_column_count(self) -> int:
        """Columns whose resolution abstained for lack of support."""
        return len(self.insufficient_evidence_columns)

    @property
    def ambiguous_column_count(self) -> int:
        """Columns whose resolution found more than one supported candidate."""
        return len(self.ambiguous_columns)

    @property
    def semantic_resolution_ratio(self) -> Optional[float]:
        """Resolved columns divided by all columns.

        ``None`` when the schema has no columns. An empty schema is not
        treated as fully resolved.
        """
        if self.n_columns == 0:
            return None
        return self.resolved_column_count / self.n_columns

    @property
    def empty_column_count(self) -> int:
        """Columns whose selected semantic type is Empty."""
        return len(self.empty_columns)

    @property
    def constant_column_count(self) -> int:
        """Columns whose selected semantic type is Constant."""
        return len(self.constant_columns)

    @property
    def identifier_column_count(self) -> int:
        """Columns whose selected semantic type is Identifier."""
        return len(self.identifier_columns)


def build_dataset_overview(analysis: DatasetAnalysis) -> DatasetOverview:
    """Summarize one dataset analysis.

    The argument must already be a ``DatasetAnalysis``. A DataFrame is
    not accepted and is not analyzed. Unique-row and excess-duplicate
    counts are read from the retained duplicate analysis. They are not
    recomputed from raw values. The analysis is not modified.
    """
    if not isinstance(analysis, DatasetAnalysis):
        raise TypeError("build_dataset_overview expects a DatasetAnalysis")
    type_order = tuple(SemanticType)
    type_index = {
        semantic_type: index for index, semantic_type in enumerate(type_order)
    }
    counts = [0] * len(type_order)
    empty: List[ColumnRef] = []
    constant: List[ColumnRef] = []
    identifier: List[ColumnRef] = []
    insufficient: List[ColumnRef] = []
    ambiguous: List[ColumnRef] = []
    for column in analysis.columns:
        ref = ColumnRef(position=column.position, label=column.label)
        status = column.inferred.resolution.status
        if status is ResolutionStatus.RESOLVED:
            selected = column.inferred.selected_type
            if not isinstance(selected, SemanticType):
                raise ValueError("a resolved column has no selected semantic type")
            # Every selected SemanticType is counted, including types that
            # have no dedicated column list. The three lists below only
            # retain identity for groups the overview names explicitly.
            counts[type_index[selected]] += 1
            if selected is SemanticType.EMPTY:
                empty.append(ref)
            elif selected is SemanticType.CONSTANT:
                constant.append(ref)
            elif selected is SemanticType.IDENTIFIER:
                identifier.append(ref)
        elif status is ResolutionStatus.INSUFFICIENT_EVIDENCE:
            insufficient.append(ref)
        elif status is ResolutionStatus.AMBIGUOUS:
            ambiguous.append(ref)
        else:
            raise ValueError(f"unrecognized resolution status: {status!r}")
    semantic_type_counts = tuple(
        SemanticTypeCount(semantic_type=semantic_type, count=count)
        for semantic_type, count in zip(type_order, counts)
        if count > 0
    )
    duplicate = analysis.duplicate_analysis
    return DatasetOverview(
        n_rows=analysis.n_rows,
        n_columns=analysis.n_columns,
        n_cells=analysis.n_cells,
        n_missing_cells=analysis.n_missing_cells,
        n_non_missing_cells=analysis.n_non_missing_cells,
        n_unique_rows=duplicate.n_unique_rows(analysis.n_rows),
        n_excess_duplicate_rows=duplicate.n_excess_duplicate_rows,
        semantic_type_counts=semantic_type_counts,
        insufficient_evidence_columns=tuple(insufficient),
        ambiguous_columns=tuple(ambiguous),
        empty_columns=tuple(empty),
        constant_columns=tuple(constant),
        identifier_columns=tuple(identifier),
    )


def _validate_semantic_counts(
    counts: Tuple[SemanticTypeCount, ...],
) -> Tuple[SemanticTypeCount, ...]:
    if not isinstance(counts, tuple):
        raise TypeError("semantic_type_counts must be a tuple")
    order = {semantic_type: index for index, semantic_type in enumerate(SemanticType)}
    previous = -1
    for item in counts:
        if not isinstance(item, SemanticTypeCount):
            raise TypeError(
                "semantic_type_counts must contain SemanticTypeCount values"
            )
        index = order[item.semantic_type]
        if index <= previous:
            raise ValueError(
                "semantic type counts must be unique and follow "
                "SemanticType definition order"
            )
        previous = index
    return counts


def _validate_column_group(
    group: Tuple[ColumnRef, ...],
    field: str,
    n_columns: int,
) -> Set[int]:
    if not isinstance(group, tuple):
        raise TypeError(f"{field} must be a tuple")
    positions: Set[int] = set()
    previous = -1
    for item in group:
        if not isinstance(item, ColumnRef):
            raise TypeError(f"{field} must contain ColumnRef values")
        if item.position >= n_columns:
            raise ValueError(f"{field} position must be less than n_columns")
        if item.position <= previous:
            raise ValueError(
                f"{field} must follow source position order without duplicates"
            )
        previous = item.position
        positions.add(item.position)
    return positions


def _require_group_count(
    group: Tuple[ColumnRef, ...],
    counts: Tuple[SemanticTypeCount, ...],
    semantic_type: SemanticType,
    field: str,
) -> None:
    expected = 0
    for item in counts:
        if item.semantic_type is semantic_type:
            expected = item.count
    if len(group) != expected:
        raise ValueError(f"{field} columns must match the {semantic_type.name} count")


def _require_count(value: int, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")
