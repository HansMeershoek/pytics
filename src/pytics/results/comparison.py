"""Public comparison result.

``ComparisonResult`` references one finished ``DatasetComparison`` and
the findings read from it. It does not compare the frames again.
``pytics.compare`` is still the legacy renderer. :func:`comparison_result`
is the entry point that returns this object.

``ComparisonResult._repr_html_`` delegates to the notebook presentation
layer. The HTML is not stored on the result.

Columns are the alignment sequence: reference order, then
comparison-only columns. That is not a second variables table.
Relationships here are relationship-drift records, not within-dataset
relationship records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator
from typing import Optional
from typing import Tuple

import pandas as pd

from pytics.analysis.compare.collector import compare_dataframes
from pytics.analysis.compare.models import ColumnComparison
from pytics.analysis.compare.models import ComparisonCoverage
from pytics.analysis.compare.models import DatasetComparison
from pytics.analysis.compare.overview import DatasetOverviewComparison
from pytics.analysis.compare.relationship_models import RelationshipDrift
from pytics.analysis.compare.relationship_models import RelationshipDriftCoverage
from pytics.analysis.compare.target_models import TargetAlignmentStatus
from pytics.analysis.compare.target_models import TargetDriftAnalysis
from pytics.analysis.compare.target_models import TargetDriftCoverage
from pytics.analysis.findings.compare import collect_compare_findings
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.result import FindingsAnalysis
from pytics.analysis.findings.result import FindingsCoverage
from pytics.results.common import AmbiguousColumnLabel
from pytics.results.common import FindingsView
from pytics.results.common import ResultKind
from pytics.results.common import ResultMetadata
from pytics.results.common import TargetRequest
from pytics.results.common import _index
from pytics.results.common import pytics_version
from pytics.results.common import retained_label_matches
from pytics.results.equality import content_equal


@dataclass(frozen=True, eq=False, repr=False)
class ComparisonColumnIndex:
    """Aligned columns in canonical comparison order.

    Integer indexing follows that order. It is not a physical position in
    either frame. Label lookup uses the match key against the retained
    label on either side. Duplicate labels stay distinct and are
    ambiguous to :meth:`by_label`.
    """

    _columns: Tuple[ColumnComparison, ...]

    def __post_init__(self) -> None:
        if not isinstance(self._columns, tuple):
            raise TypeError("columns must be a tuple")
        for column in self._columns:
            if not isinstance(column, ColumnComparison):
                raise TypeError("columns must contain ColumnComparison records")

    def __iter__(self) -> Iterator[ColumnComparison]:
        return iter(self._columns)

    def __len__(self) -> int:
        return len(self._columns)

    def __getitem__(self, index: object) -> ColumnComparison:
        return _index(self._columns, index, "columns")

    @property
    def records(self) -> Tuple[ColumnComparison, ...]:
        """Aligned columns. The canonical tuple, not a copy."""
        return self._columns

    def matching(self, label: object) -> Tuple[ColumnComparison, ...]:
        """Every aligned column whose retained label matches ``label``."""
        return tuple(
            column
            for column in self._columns
            if retained_label_matches(column.alignment.reference_label, label)
            or retained_label_matches(column.alignment.comparison_label, label)
        )

    def by_label(self, label: object) -> ColumnComparison:
        """Return the one aligned column ``label`` matches.

        Zero matches raise ``KeyError``. More than one match raises
        :class:`AmbiguousColumnLabel`. Positions in that error are
        indexes in this alignment sequence.
        """
        found = self.matching(label)
        if not found:
            raise KeyError("label matches no column")
        if len(found) > 1:
            found_ids = {id(column) for column in found}
            positions = tuple(
                index
                for index, column in enumerate(self._columns)
                if id(column) in found_ids
            )
            raise AmbiguousColumnLabel(label, positions)
        return found[0]

    def __repr__(self) -> str:
        return f"ComparisonColumnIndex(n={len(self._columns)})"


@dataclass(frozen=True, eq=False, repr=False)
class ComparisonRelationshipIndex:
    """Relationship-drift records, in ascending reference-position order.

    The records are the comparison's own drift records. :meth:`between`
    looks up a pair by reference physical position. Comparison-only
    columns have no reference position and are not members of a drift pair.
    """

    _records: Tuple[RelationshipDrift, ...]
    _coverage: RelationshipDriftCoverage
    _columns: ComparisonColumnIndex

    def __post_init__(self) -> None:
        if not isinstance(self._records, tuple):
            raise TypeError("records must be a tuple")
        for record in self._records:
            if not isinstance(record, RelationshipDrift):
                raise TypeError("records must contain RelationshipDrift records")
        if not isinstance(self._coverage, RelationshipDriftCoverage):
            raise TypeError("coverage must be a RelationshipDriftCoverage")
        if not isinstance(self._columns, ComparisonColumnIndex):
            raise TypeError("columns must be a ComparisonColumnIndex")

    def __iter__(self) -> Iterator[RelationshipDrift]:
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, index: object) -> RelationshipDrift:
        return _index(self._records, index, "relationships")

    @property
    def records(self) -> Tuple[RelationshipDrift, ...]:
        """Drift records. The canonical tuple, not a copy."""
        return self._records

    @property
    def coverage(self) -> RelationshipDriftCoverage:
        """Pair-outcome counts. Not a score."""
        return self._coverage

    def between(self, left: object, right: object) -> RelationshipDrift:
        """Return the drift record for two reference positions.

        Order does not matter. A pair with no drift record raises
        ``KeyError``.
        """
        left_position = _require_position(left, "left")
        right_position = _require_position(right, "right")
        if left_position == right_position:
            raise ValueError("a relationship joins two distinct columns")
        if left_position > right_position:
            left_position, right_position = right_position, left_position
        for record in self._records:
            alignment = record.alignment
            if (
                alignment.first.reference_position == left_position
                and alignment.second.reference_position == right_position
            ):
                return record
        raise KeyError(
            f"no relationship drift for reference positions "
            f"({left_position}, {right_position})"
        )

    def between_labels(self, left: object, right: object) -> RelationshipDrift:
        """Resolve two unique labels to reference positions and look up the pair.

        A column that is not on the reference side has no reference
        position, so it cannot key a drift pair.
        """
        return self.between(
            _reference_position(self._columns.by_label(left)),
            _reference_position(self._columns.by_label(right)),
        )

    def __repr__(self) -> str:
        return f"ComparisonRelationshipIndex(n={len(self._records)})"


@dataclass(frozen=True, eq=False, repr=False)
class ComparisonTargetView:
    """Target drift, or an explicit statement that no target was requested.

    ``NOT_REQUESTED`` means ``analysis`` is absent. A requested target
    that is missing from one or both datasets still has an analysis.
    ``alignment_status`` is that record's code, including
    ``NOT_IN_EITHER``. That code is not ``NOT_REQUESTED``.
    """

    request: TargetRequest
    analysis: Optional[TargetDriftAnalysis]

    def __post_init__(self) -> None:
        if not isinstance(self.request, TargetRequest):
            raise TypeError("request must be a TargetRequest")
        if self.request is TargetRequest.NOT_REQUESTED:
            if self.analysis is not None:
                raise ValueError("an unrequested target has no target drift")
            return
        if not isinstance(self.analysis, TargetDriftAnalysis):
            raise TypeError("a requested target has a TargetDriftAnalysis")

    @property
    def alignment_status(self) -> Optional[TargetAlignmentStatus]:
        """Alignment code, or ``None`` when no target was requested."""
        if self.analysis is None:
            return None
        return self.analysis.alignment.status

    def __repr__(self) -> str:
        return f"ComparisonTargetView(request={self.request.value})"


@dataclass(frozen=True, eq=False, repr=False)
class ComparisonCoverageView:
    """Factual coverage of one comparison. Not a score.

    ``columns`` includes distribution-drift counts and the deferred
    comparison families. ``relationships`` counts drift outcomes.
    ``findings`` lists which comparison finding codes were evaluated.
    ``target`` is present only when a target was requested.
    """

    columns: ComparisonCoverage
    relationships: RelationshipDriftCoverage
    findings: FindingsCoverage
    target: Optional[TargetDriftCoverage]

    def __post_init__(self) -> None:
        if not isinstance(self.columns, ComparisonCoverage):
            raise TypeError("columns must be a ComparisonCoverage")
        if not isinstance(self.relationships, RelationshipDriftCoverage):
            raise TypeError("relationships must be a RelationshipDriftCoverage")
        if not isinstance(self.findings, FindingsCoverage):
            raise TypeError("findings must be a FindingsCoverage")
        if self.target is not None and not isinstance(self.target, TargetDriftCoverage):
            raise TypeError("target must be a TargetDriftCoverage")

    def __repr__(self) -> str:
        return (
            "ComparisonCoverageView("
            f"columns={self.columns.n_columns}, "
            f"relationships={self.relationships.n_aligned_pairs})"
        )


@dataclass(frozen=True, eq=False, repr=False)
class ComparisonResult:
    """Public result of comparing two DataFrames.

    The comparison and the findings are retained by reference. The source
    frames are not. Equality follows the same label-aware content rule as
    a profile result. The result is frozen and not hashable.
    """

    _comparison: DatasetComparison
    _findings_analysis: FindingsAnalysis
    _metadata: ResultMetadata
    _columns: ComparisonColumnIndex
    _relationships: ComparisonRelationshipIndex
    _findings: FindingsView
    _target: ComparisonTargetView
    _coverage: ComparisonCoverageView

    def __post_init__(self) -> None:
        if not isinstance(self._comparison, DatasetComparison):
            raise TypeError("comparison must be a DatasetComparison")
        if not isinstance(self._findings_analysis, FindingsAnalysis):
            raise TypeError("findings must be a FindingsAnalysis")
        if self._findings_analysis.source is not FindingsSource.COMPARE:
            raise ValueError("a comparison result requires comparison findings")
        if not isinstance(self._metadata, ResultMetadata):
            raise TypeError("metadata must be a ResultMetadata")
        if self._metadata.kind is not ResultKind.COMPARISON:
            raise ValueError("metadata kind must be comparison")

    @classmethod
    def from_comparison(cls, comparison: DatasetComparison) -> "ComparisonResult":
        """Wrap a finished comparison. Does not compare again."""
        if not isinstance(comparison, DatasetComparison):
            raise TypeError("ComparisonResult wraps a DatasetComparison")
        findings = collect_compare_findings(comparison)
        requested = comparison.target is not None
        request = TargetRequest.REQUESTED if requested else TargetRequest.NOT_REQUESTED
        columns = ComparisonColumnIndex(comparison.columns)
        relationships = ComparisonRelationshipIndex(
            comparison.relationships,
            comparison.relationship_coverage,
            columns,
        )
        target = ComparisonTargetView(request=request, analysis=comparison.target)
        target_coverage = None
        if comparison.target is not None:
            target_coverage = comparison.target.coverage
        coverage = ComparisonCoverageView(
            columns=comparison.coverage,
            relationships=comparison.relationship_coverage,
            findings=findings.coverage,
            target=target_coverage,
        )
        metadata = ResultMetadata(
            pytics_version=pytics_version(),
            kind=ResultKind.COMPARISON,
            target_request=request,
            findings_policy=findings.policy.identifier,
        )
        return cls(
            comparison,
            findings,
            metadata,
            columns,
            relationships,
            FindingsView(findings),
            target,
            coverage,
        )

    def __eq__(self, other: object) -> bool:
        if other.__class__ is not ComparisonResult:
            return NotImplemented
        return (
            self._metadata == other._metadata
            and content_equal(self._comparison, other._comparison)
            and content_equal(self._findings_analysis, other._findings_analysis)
        )

    __hash__ = None

    @property
    def metadata(self) -> ResultMetadata:
        return self._metadata

    @property
    def overview(self) -> DatasetOverviewComparison:
        """Dataset-level counts for the two sides."""
        return self._comparison.overview

    @property
    def columns(self) -> ComparisonColumnIndex:
        return self._columns

    @property
    def relationships(self) -> ComparisonRelationshipIndex:
        return self._relationships

    @property
    def findings(self) -> FindingsView:
        return self._findings

    @property
    def target(self) -> ComparisonTargetView:
        return self._target

    @property
    def coverage(self) -> ComparisonCoverageView:
        return self._coverage

    def __repr__(self) -> str:
        rows = self._comparison.overview.n_rows
        return (
            "ComparisonResult("
            f"rows={rows.reference}/{rows.comparison}, "
            f"columns={len(self._columns)}, "
            f"findings={len(self._findings_analysis.findings)}, "
            f"target={self._metadata.target_request.value})"
        )

    def _repr_html_(self) -> str:
        """Notebook HTML view of this result. Not stored on the result."""
        from pytics.presentation.notebook.comparison import render_comparison

        return render_comparison(self)


def comparison_result(
    reference: pd.DataFrame,
    comparison: pd.DataFrame,
    *,
    target: object = None,
) -> ComparisonResult:
    """Compare two DataFrames and return the public result.

    Each frame is analyzed once, then compared once, including
    distribution drift. The frames are not retained. ``target`` ``None``
    requests no target drift. A label that matches neither column is a
    target-drift record whose alignment status says so. It is not treated
    as an omitted request.

    This is not :func:`pytics.compare`. That function still renders the
    legacy report.
    """
    if not isinstance(reference, pd.DataFrame) or not isinstance(
        comparison, pd.DataFrame
    ):
        raise TypeError("comparison_result expects two pandas DataFrames")
    return ComparisonResult.from_comparison(
        compare_dataframes(reference, comparison, target=target)
    )


def _require_position(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{field} must be a reference column position")
    return value


def _reference_position(column: ColumnComparison) -> int:
    position = column.alignment.reference_position
    if position is None:
        raise ValueError("relationship drift is keyed by reference positions")
    return position
