"""Which reference column corresponds to which comparison column.

Inside one frame, physical position is the column identity. Across
frames, a column aligns by its label match key plus a 1-based occurrence
in physical order. A reordered column is matched, not removed and added.
An unsupported label has no occurrence and is never matched. Rows are
not aligned.

The aligned sequence follows the reference physical order, then the
comparison-only columns in comparison physical order. Every later
comparison layer reads this sequence. None of them aligns columns again.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import Optional
from typing import Tuple

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.column_label import column_label_match_key
from pytics.analysis.column_label import retain_column_label
from pytics.analysis.compare.values import _require_optional
from pytics.analysis.compare.values import _require_optional_position


class ColumnMatchStatus(Enum):
    """How one column sits relative to the other dataset.

    A reordered column is ``MATCHED``. It is not removed and added.
    """

    MATCHED = "matched"
    REFERENCE_ONLY = "reference_only"
    COMPARISON_ONLY = "comparison_only"


@dataclass(frozen=True)
class ColumnAlignment:
    """Where one aligned column sits in each dataset.

    ``occurrence`` counts labels that share a match key, starting at 1,
    in physical order on that side. Matched columns share one occurrence.
    An unsupported label has no occurrence and is never matched.
    ``reordered`` is ``None`` unless both physical positions exist.
    """

    status: ColumnMatchStatus
    reference_label: Optional[RetainedColumnLabel]
    comparison_label: Optional[RetainedColumnLabel]
    occurrence: Optional[int]
    reference_position: Optional[int]
    comparison_position: Optional[int]

    def __post_init__(self) -> None:
        if not isinstance(self.status, ColumnMatchStatus):
            raise TypeError("status must be a ColumnMatchStatus")
        _require_optional(self.reference_label, RetainedColumnLabel, "reference_label")
        _require_optional(
            self.comparison_label, RetainedColumnLabel, "comparison_label"
        )
        _require_optional_position(self.reference_position, "reference_position")
        _require_optional_position(self.comparison_position, "comparison_position")
        if self.occurrence is not None and (
            type(self.occurrence) is not int or self.occurrence < 1
        ):
            raise ValueError("occurrence must be a positive int or None")
        if self.status is ColumnMatchStatus.MATCHED:
            if self.reference_position is None or self.comparison_position is None:
                raise ValueError("a matched column has two physical positions")
            if self.reference_label is None or self.comparison_label is None:
                raise ValueError("a matched column has two labels")
            if self.occurrence is None:
                raise ValueError("a matched column has an occurrence")
        elif self.status is ColumnMatchStatus.REFERENCE_ONLY:
            if self.reference_position is None or self.comparison_position is not None:
                raise ValueError(
                    "a reference-only column has only a reference position"
                )
            if self.reference_label is None or self.comparison_label is not None:
                raise ValueError("a reference-only column has only a reference label")
        else:
            if self.comparison_position is None or self.reference_position is not None:
                raise ValueError(
                    "a comparison-only column has only a comparison position"
                )
            if self.comparison_label is None or self.reference_label is not None:
                raise ValueError("a comparison-only column has only a comparison label")

    @property
    def reordered(self) -> Optional[bool]:
        """Whether the two physical positions differ.

        ``None`` when the column is missing from either side. Equal
        positions are not reordered.
        """
        if self.reference_position is None or self.comparison_position is None:
            return None
        return self.reference_position != self.comparison_position


@dataclass(frozen=True)
class _AlignedColumn:
    """One aligned column and the analyses on the sides that have it.

    Temporary. The column analyses are not part of a comparison result.
    """

    alignment: ColumnAlignment
    reference: Optional[ColumnAnalysis]
    comparison: Optional[ColumnAnalysis]


@dataclass(frozen=True)
class _IndexedColumn:
    column: ColumnAnalysis
    label: RetainedColumnLabel
    occurrence: Optional[int]
    key: Optional[Tuple[object, ...]]


def align_columns(
    reference_columns: Tuple[ColumnAnalysis, ...],
    comparison_columns: Tuple[ColumnAnalysis, ...],
) -> Tuple[_AlignedColumn, ...]:
    """Align two column sequences by label identity and occurrence.

    Matching is one pass per side and a dict lookup, expected linear in
    the column count.
    """
    reference_index = _index_columns(reference_columns)
    comparison_index = _index_columns(comparison_columns)
    comparison_by_key: Dict[Tuple[object, ...], _IndexedColumn] = {}
    for indexed in comparison_index:
        if indexed.key is None:
            continue
        comparison_by_key[(indexed.key, indexed.occurrence)] = indexed
    matched_ids = set()
    aligned = []
    for indexed in reference_index:
        partner = None
        if indexed.key is not None:
            partner = comparison_by_key.get((indexed.key, indexed.occurrence))
        if partner is None:
            aligned.append(_unmatched(indexed, reference_side=True))
            continue
        matched_ids.add(id(partner))
        aligned.append(_matched(indexed, partner))
    for indexed in comparison_index:
        if id(indexed) in matched_ids:
            continue
        aligned.append(_unmatched(indexed, reference_side=False))
    return tuple(aligned)


def _index_columns(
    columns: Tuple[ColumnAnalysis, ...],
) -> Tuple[_IndexedColumn, ...]:
    counts: Dict[Tuple[object, ...], int] = {}
    indexed = []
    for column in columns:
        label = retain_column_label(column.label)
        key = column_label_match_key(column.label)
        occurrence = None
        if key is not None:
            counts[key] = counts.get(key, 0) + 1
            occurrence = counts[key]
        indexed.append(
            _IndexedColumn(
                column=column,
                label=label,
                occurrence=occurrence,
                key=key,
            )
        )
    return tuple(indexed)


def _matched(reference: _IndexedColumn, comparison: _IndexedColumn) -> _AlignedColumn:
    return _AlignedColumn(
        alignment=ColumnAlignment(
            status=ColumnMatchStatus.MATCHED,
            reference_label=reference.label,
            comparison_label=comparison.label,
            occurrence=reference.occurrence,
            reference_position=reference.column.position,
            comparison_position=comparison.column.position,
        ),
        reference=reference.column,
        comparison=comparison.column,
    )


def _unmatched(indexed: _IndexedColumn, *, reference_side: bool) -> _AlignedColumn:
    if reference_side:
        return _AlignedColumn(
            alignment=ColumnAlignment(
                status=ColumnMatchStatus.REFERENCE_ONLY,
                reference_label=indexed.label,
                comparison_label=None,
                occurrence=indexed.occurrence,
                reference_position=indexed.column.position,
                comparison_position=None,
            ),
            reference=indexed.column,
            comparison=None,
        )
    return _AlignedColumn(
        alignment=ColumnAlignment(
            status=ColumnMatchStatus.COMPARISON_ONLY,
            reference_label=None,
            comparison_label=indexed.label,
            occurrence=indexed.occurrence,
            reference_position=None,
            comparison_position=indexed.column.position,
        ),
        reference=None,
        comparison=indexed.column,
    )
