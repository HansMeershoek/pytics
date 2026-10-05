"""Physical and semantic state of one column on each side.

Physical dtype and the inferred semantic reading are separate facts. A
dtype-name change is not a semantic-type change. Confidence is compared
as a category and is not subtracted. Both sides are the inferred state.
An effective override is not represented, because overrides are not
implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.compare.values import _require_optional
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus


@dataclass(frozen=True)
class PhysicalDtypeSnapshot:
    """Physical storage of one column, without the source dtype object."""

    family: PhysicalDtypeFamily
    dtype_name: str
    categorical_ordered: Optional[bool] = None

    def __post_init__(self) -> None:
        if not isinstance(self.family, PhysicalDtypeFamily):
            raise TypeError("family must be a PhysicalDtypeFamily")
        if type(self.dtype_name) is not str or not self.dtype_name.strip():
            raise ValueError("dtype_name must be a non-empty string")
        if (
            self.categorical_ordered is not None
            and type(self.categorical_ordered) is not bool
        ):
            raise TypeError("categorical_ordered must be a bool or None")


@dataclass(frozen=True)
class PhysicalDtypeComparison:
    """Physical dtype on each side that has the column.

    ``family_changed`` is ``None`` when the column exists on only one
    side. A dtype-name change is not a semantic-type change.
    """

    reference: Optional[PhysicalDtypeSnapshot]
    comparison: Optional[PhysicalDtypeSnapshot]

    def __post_init__(self) -> None:
        _require_optional(self.reference, PhysicalDtypeSnapshot, "reference")
        _require_optional(self.comparison, PhysicalDtypeSnapshot, "comparison")
        if self.reference is None and self.comparison is None:
            raise ValueError("a physical comparison needs at least one side")

    @property
    def family_changed(self) -> Optional[bool]:
        """Whether the physical families differ, when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.family is not self.comparison.family

    @property
    def dtype_name_changed(self) -> Optional[bool]:
        """Whether the dtype display names differ, when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.dtype_name != self.comparison.dtype_name

    @property
    def categorical_ordered_changed(self) -> Optional[bool]:
        """Whether ordered-categorical metadata differs, when both sides exist.

        ``None`` on a snapshot means that side is not categorical. ``False``
        to ``True`` is a change. Both ``None`` is not a change.
        """
        if self.reference is None or self.comparison is None:
            return None
        return (
            self.reference.categorical_ordered
            is not self.comparison.categorical_ordered
        )


@dataclass(frozen=True)
class SemanticSnapshot:
    """Inferred semantic state of one column.

    ``confidence`` is the structural interpretation's confidence. It is
    ``None`` when resolution did not keep an interpretation, including a
    candidate-derived selection. There is no effective-interpretation
    override to compare yet.
    """

    resolution_status: ResolutionStatus
    selected_type: Optional[SemanticType]
    confidence: Optional[Confidence]

    def __post_init__(self) -> None:
        if not isinstance(self.resolution_status, ResolutionStatus):
            raise TypeError("resolution_status must be a ResolutionStatus")
        if self.selected_type is not None and not isinstance(
            self.selected_type, SemanticType
        ):
            raise TypeError("selected_type must be a SemanticType or None")
        if self.confidence is not None and not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence or None")
        if self.resolution_status is ResolutionStatus.RESOLVED:
            if self.selected_type is None:
                raise ValueError("a resolved column has a selected semantic type")
        elif self.selected_type is not None:
            raise ValueError("an unresolved column has no selected semantic type")


@dataclass(frozen=True)
class SemanticComparison:
    """Inferred semantic state on each side that has the column.

    Confidence is compared as a category. Levels are not subtracted.
    Both sides are the inferred state. An effective override is not
    represented, because overrides are not implemented.
    """

    reference: Optional[SemanticSnapshot]
    comparison: Optional[SemanticSnapshot]

    def __post_init__(self) -> None:
        _require_optional(self.reference, SemanticSnapshot, "reference")
        _require_optional(self.comparison, SemanticSnapshot, "comparison")
        if self.reference is None and self.comparison is None:
            raise ValueError("a semantic comparison needs at least one side")

    @property
    def selected_type_changed(self) -> Optional[bool]:
        """Whether the selected types differ, when both sides exist.

        ``None`` and a selected type differ. Two ``None`` values do not.
        """
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.selected_type is not self.comparison.selected_type

    @property
    def resolution_status_changed(self) -> Optional[bool]:
        """Whether the resolution statuses differ, when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.resolution_status is not self.comparison.resolution_status

    @property
    def confidence_changed(self) -> Optional[bool]:
        """Whether the confidence categories differ, when both sides exist.

        ``None`` is its own category. This is not a numeric step.
        """
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.confidence is not self.comparison.confidence


def physical_comparison(
    reference: Optional[ColumnAnalysis],
    comparison: Optional[ColumnAnalysis],
) -> PhysicalDtypeComparison:
    """Physical snapshots for the sides that have the column."""
    return PhysicalDtypeComparison(
        reference=None if reference is None else _physical_snapshot(reference),
        comparison=None if comparison is None else _physical_snapshot(comparison),
    )


def semantic_comparison(
    reference: Optional[ColumnAnalysis],
    comparison: Optional[ColumnAnalysis],
) -> SemanticComparison:
    """Inferred semantic snapshots for the sides that have the column."""
    return SemanticComparison(
        reference=None if reference is None else _semantic_snapshot(reference),
        comparison=None if comparison is None else _semantic_snapshot(comparison),
    )


def _physical_snapshot(column: ColumnAnalysis) -> PhysicalDtypeSnapshot:
    physical = column.physical
    return PhysicalDtypeSnapshot(
        family=physical.family,
        dtype_name=physical.dtype_name,
        categorical_ordered=physical.categorical_ordered,
    )


def _semantic_snapshot(column: ColumnAnalysis) -> SemanticSnapshot:
    interpretation = column.inferred.interpretation
    confidence = None if interpretation is None else interpretation.confidence
    return SemanticSnapshot(
        resolution_status=column.inferred.resolution.status,
        selected_type=column.inferred.selected_type,
        confidence=confidence,
    )
