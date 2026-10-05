"""Public profile result.

``ProfileResult`` references one finished ``DatasetAnalysis`` and the
findings read from it. Building the result does not analyze the frame
again, and reading the result does not either. The DataFrame is not
retained.

``pytics.profile`` is still the legacy renderer. It does not return this
object. :func:`profile_result` is the entry point that does.

``ProfileResult._repr_html_`` delegates to the notebook presentation
layer. The HTML is not stored on the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator
from typing import Optional
from typing import Tuple

import pandas as pd

from pytics.analysis.anomaly import AnomalyAnalysis
from pytics.analysis.anomaly import AnomalyCoverage
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column_label import ColumnLabelIdentity
from pytics.analysis.column_label import identify_column_labels
from pytics.analysis.column_label import observed_labels_equal
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.profile import collect_profile_findings
from pytics.analysis.findings.result import FindingsAnalysis
from pytics.analysis.findings.result import FindingsCoverage
from pytics.analysis.missing import MissingAnalysis
from pytics.analysis.relationships.models import RelationshipAnalysis
from pytics.analysis.relationships.models import RelationshipRecord
from pytics.analysis.target import TargetAnalysis
from pytics.analysis.target import TargetStatus
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import TargetDiagnosticAnalysis
from pytics.analysis.target_leakage import TargetLeakageAnalysis
from pytics.results.common import AmbiguousColumnLabel
from pytics.results.common import FindingsView
from pytics.results.common import ResultKind
from pytics.results.common import ResultMetadata
from pytics.results.common import TargetRequest
from pytics.results.common import _index
from pytics.results.common import pytics_version
from pytics.results.equality import content_equal
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


@dataclass(frozen=True, eq=False, repr=False)
class Variable:
    """One physical column, with its canonical identity.

    ``label`` is the original column label. It is not a display string
    and it is not the match key. ``identity`` is the retained label, the
    match key, and the occurrence in this column order. ``record`` is
    the column analysis already stored on the dataset. Nothing here is
    copied from that record.
    """

    _record: ColumnAnalysis
    _identity: ColumnLabelIdentity

    def __post_init__(self) -> None:
        if not isinstance(self._record, ColumnAnalysis):
            raise TypeError("record must be a ColumnAnalysis")
        if not isinstance(self._identity, ColumnLabelIdentity):
            raise TypeError("identity must be a ColumnLabelIdentity")

    @property
    def record(self) -> ColumnAnalysis:
        """Canonical column analysis."""
        return self._record

    @property
    def identity(self) -> ColumnLabelIdentity:
        """Match key and occurrence. Not a display string."""
        return self._identity

    @property
    def position(self) -> int:
        """Physical position on the source column axis."""
        return self._record.position

    @property
    def label(self) -> object:
        """Original column label."""
        return self._record.label

    @property
    def selected_type(self) -> Optional[SemanticType]:
        """Selected semantic type, or ``None`` when resolution did not select one."""
        return self._record.inferred.selected_type

    @property
    def resolution_status(self) -> ResolutionStatus:
        """Resolution state. Not a prose description."""
        return self._record.inferred.resolution.status

    def __repr__(self) -> str:
        return f"Variable(position={self.position})"


@dataclass(frozen=True, eq=False, repr=False)
class VariableIndex:
    """Physical columns in source order.

    Integer indexing is positional. ``True`` is not a position, and a
    column label is not a position, including when the label itself is
    an integer. Label lookup is :meth:`by_label` and :meth:`matching`.
    A label that matches more than one column is ambiguous. It is not
    collapsed to one entry.
    """

    _columns: Tuple[ColumnAnalysis, ...]
    _identities: Tuple[ColumnLabelIdentity, ...]

    def __post_init__(self) -> None:
        if not isinstance(self._columns, tuple):
            raise TypeError("columns must be a tuple")
        if not isinstance(self._identities, tuple):
            raise TypeError("identities must be a tuple")
        if len(self._columns) != len(self._identities):
            raise ValueError("each column has one identity")
        for column, identity in zip(self._columns, self._identities):
            if not isinstance(column, ColumnAnalysis):
                raise TypeError("columns must contain ColumnAnalysis records")
            if not isinstance(identity, ColumnLabelIdentity):
                raise TypeError("identities must contain ColumnLabelIdentity records")

    @classmethod
    def from_columns(cls, columns: Tuple[ColumnAnalysis, ...]) -> "VariableIndex":
        """Identify ``columns`` once, in their existing order."""
        if not isinstance(columns, tuple):
            raise TypeError("columns must be a tuple")
        identities = identify_column_labels(tuple(column.label for column in columns))
        return cls(columns, identities)

    def __iter__(self) -> Iterator[Variable]:
        for column, identity in zip(self._columns, self._identities):
            yield Variable(column, identity)

    def __len__(self) -> int:
        return len(self._columns)

    def __getitem__(self, index: object) -> Variable:
        position = _position(index, len(self._columns))
        return Variable(self._columns[position], self._identities[position])

    def matching(self, label: object) -> Tuple[Variable, ...]:
        """Every column whose label matches ``label``, in physical order.

        ``1`` matches ``1.0``. ``True`` does not match ``1``. Every float
        ``NaN`` matches. An empty result is no match, not an error.
        """
        found = tuple(
            variable
            for variable in self
            if observed_labels_equal(variable.label, label)
        )
        return found

    def by_label(self, label: object) -> Variable:
        """Return the one column ``label`` matches.

        Zero matches raise ``KeyError``. More than one match raises
        :class:`AmbiguousColumnLabel`.
        """
        found = self.matching(label)
        if not found:
            raise KeyError("label matches no column")
        if len(found) > 1:
            raise AmbiguousColumnLabel(label, tuple(item.position for item in found))
        return found[0]

    def __repr__(self) -> str:
        return f"VariableIndex(n={len(self._columns)})"


@dataclass(frozen=True, eq=False, repr=False)
class RelationshipIndex:
    """Calculated relationship records, in canonical pair order.

    The records are the ones the relationship analysis already holds.
    Pairs that were not calculated are counts on that analysis, not
    missing objects in this sequence. :meth:`between` looks up a
    calculated pair by physical position. It does not calculate one.
    """

    _analysis: RelationshipAnalysis
    _variables: VariableIndex

    def __post_init__(self) -> None:
        if not isinstance(self._analysis, RelationshipAnalysis):
            raise TypeError("analysis must be a RelationshipAnalysis")
        if not isinstance(self._variables, VariableIndex):
            raise TypeError("variables must be a VariableIndex")

    def __iter__(self) -> Iterator[RelationshipRecord]:
        return iter(self._analysis.relationships)

    def __len__(self) -> int:
        return len(self._analysis.relationships)

    def __getitem__(self, index: object) -> RelationshipRecord:
        return _index(self._analysis.relationships, index, "relationships")

    @property
    def records(self) -> Tuple[RelationshipRecord, ...]:
        """Calculated pairs. The canonical tuple, not a copy."""
        return self._analysis.relationships

    @property
    def analysis(self) -> RelationshipAnalysis:
        """Coverage and records. Not a second relationship pass."""
        return self._analysis

    def between(self, left: object, right: object) -> RelationshipRecord:
        """Return the calculated record for two physical positions.

        Order does not matter. A pair with no calculated record raises
        ``KeyError``. That absence is not a new status: unimplemented and
        ineligible pairs are counted on ``analysis`` and are not stored
        one by one.
        """
        left_position = _require_position(left, "left")
        right_position = _require_position(right, "right")
        if left_position == right_position:
            raise ValueError("a relationship joins two distinct columns")
        if left_position > right_position:
            left_position, right_position = right_position, left_position
        for record in self._analysis.relationships:
            if (
                record.left_position == left_position
                and record.right_position == right_position
            ):
                return record
        raise KeyError(
            f"no calculated relationship for positions "
            f"({left_position}, {right_position})"
        )

    def between_labels(self, left: object, right: object) -> RelationshipRecord:
        """Resolve two unique labels, then return their calculated record."""
        return self.between(
            self._variables.by_label(left).position,
            self._variables.by_label(right).position,
        )

    def __repr__(self) -> str:
        return f"RelationshipIndex(n={len(self._analysis.relationships)})"


@dataclass(frozen=True, eq=False, repr=False)
class TargetView:
    """The target branch, or an explicit statement that none was requested.

    ``request`` is ``NOT_REQUESTED`` only when analysis, leakage, and the
    diagnostic are all absent. When a target was requested, ``status`` is
    the target-status code and ``diagnostic_status`` is the diagnostic
    code. An unsupported target and an unavailable model are those codes.
    They are not ``NOT_REQUESTED``.
    """

    request: TargetRequest
    analysis: Optional[TargetAnalysis]
    leakage: Optional[TargetLeakageAnalysis]
    diagnostic: Optional[TargetDiagnosticAnalysis]

    def __post_init__(self) -> None:
        if not isinstance(self.request, TargetRequest):
            raise TypeError("request must be a TargetRequest")
        present = (
            self.analysis is not None,
            self.leakage is not None,
            self.diagnostic is not None,
        )
        if self.request is TargetRequest.NOT_REQUESTED:
            if any(present):
                raise ValueError("an unrequested target has no target records")
            return
        if not all(present):
            raise ValueError("a requested target has analysis, leakage, and diagnostic")
        if not isinstance(self.analysis, TargetAnalysis):
            raise TypeError("analysis must be a TargetAnalysis")
        if not isinstance(self.leakage, TargetLeakageAnalysis):
            raise TypeError("leakage must be a TargetLeakageAnalysis")
        if not isinstance(self.diagnostic, TargetDiagnosticAnalysis):
            raise TypeError("diagnostic must be a TargetDiagnosticAnalysis")

    @property
    def status(self) -> Optional[TargetStatus]:
        """Target-status code, or ``None`` when no target was requested."""
        if self.analysis is None:
            return None
        return self.analysis.status

    @property
    def diagnostic_status(self) -> Optional[DiagnosticStatus]:
        """Diagnostic-status code, or ``None`` when no target was requested."""
        if self.diagnostic is None:
            return None
        return self.diagnostic.status

    def __repr__(self) -> str:
        return f"TargetView(request={self.request.value})"


@dataclass(frozen=True, eq=False, repr=False)
class ProfileCoverage:
    """Factual coverage of one profile. Not a score and not a percentage.

    ``relationships`` uses the relationship analysis's own counts:
    supported pairs are the pairs with a calculated record, unimplemented
    pairs are recognized families without a calculator, and ineligible
    pairs are outside the relationship contract. A component inside a
    calculated record can still be unavailable. That is a status on the
    record, not a fourth pair total.

    ``anomalies`` is the anomaly coverage object. ``findings`` lists
    which finding codes were evaluated. Missingness and duplicate-row
    analysis have no request switch: both are present on the profile.
    """

    relationships: RelationshipAnalysis
    anomalies: AnomalyCoverage
    findings: FindingsCoverage

    def __post_init__(self) -> None:
        if not isinstance(self.relationships, RelationshipAnalysis):
            raise TypeError("relationships must be a RelationshipAnalysis")
        if not isinstance(self.anomalies, AnomalyCoverage):
            raise TypeError("anomalies must be an AnomalyCoverage")
        if not isinstance(self.findings, FindingsCoverage):
            raise TypeError("findings must be a FindingsCoverage")

    def __repr__(self) -> str:
        return (
            "ProfileCoverage("
            f"relationships={self.relationships.n_analyzed_pairs}, "
            f"findings={self.findings.n_findings})"
        )


@dataclass(frozen=True, eq=False, repr=False)
class ProfileResult:
    """Public result of profiling one DataFrame.

    The analysis and the findings are retained by reference. Variables,
    relationships, and the target view read those objects. They do not
    recompute them. The result is frozen. It is equal to another profile
    result when the retained content is equal, including float ``NaN``
    labels. It is not hashable, and it has no timestamp.
    """

    _analysis: DatasetAnalysis
    _findings_analysis: FindingsAnalysis
    _metadata: ResultMetadata
    _variables: VariableIndex
    _relationships: RelationshipIndex
    _findings: FindingsView
    _target: TargetView
    _coverage: ProfileCoverage

    def __post_init__(self) -> None:
        if not isinstance(self._analysis, DatasetAnalysis):
            raise TypeError("analysis must be a DatasetAnalysis")
        if not isinstance(self._findings_analysis, FindingsAnalysis):
            raise TypeError("findings must be a FindingsAnalysis")
        if self._findings_analysis.source is not FindingsSource.PROFILE:
            raise ValueError("a profile result requires profile findings")
        if not isinstance(self._metadata, ResultMetadata):
            raise TypeError("metadata must be a ResultMetadata")
        if self._metadata.kind is not ResultKind.PROFILE:
            raise ValueError("metadata kind must be profile")

    @classmethod
    def from_analysis(cls, analysis: DatasetAnalysis) -> "ProfileResult":
        """Wrap a finished analysis. Does not analyze again.

        Findings are collected once from that analysis. The DataFrame is
        not an argument and is not read.
        """
        if not isinstance(analysis, DatasetAnalysis):
            raise TypeError("ProfileResult wraps a DatasetAnalysis")
        findings = collect_profile_findings(analysis)
        requested = analysis.target_analysis is not None
        request = TargetRequest.REQUESTED if requested else TargetRequest.NOT_REQUESTED
        variables = VariableIndex.from_columns(analysis.columns)
        relationships = RelationshipIndex(analysis.relationship_analysis, variables)
        target = TargetView(
            request=request,
            analysis=analysis.target_analysis,
            leakage=analysis.target_leakage,
            diagnostic=analysis.target_diagnostic,
        )
        coverage = ProfileCoverage(
            relationships=analysis.relationship_analysis,
            anomalies=analysis.anomaly_analysis.coverage,
            findings=findings.coverage,
        )
        metadata = ResultMetadata(
            pytics_version=pytics_version(),
            kind=ResultKind.PROFILE,
            target_request=request,
            findings_policy=findings.policy.identifier,
        )
        return cls(
            analysis,
            findings,
            metadata,
            variables,
            relationships,
            FindingsView(findings),
            target,
            coverage,
        )

    def __eq__(self, other: object) -> bool:
        if other.__class__ is not ProfileResult:
            return NotImplemented
        return (
            self._metadata == other._metadata
            and content_equal(self._analysis, other._analysis)
            and content_equal(self._findings_analysis, other._findings_analysis)
        )

    __hash__ = None

    @property
    def metadata(self) -> ResultMetadata:
        return self._metadata

    @property
    def n_rows(self) -> int:
        return self._analysis.n_rows

    @property
    def n_columns(self) -> int:
        return self._analysis.n_columns

    @property
    def n_cells(self) -> int:
        return self._analysis.n_cells

    @property
    def variables(self) -> VariableIndex:
        return self._variables

    @property
    def relationships(self) -> RelationshipIndex:
        return self._relationships

    @property
    def findings(self) -> FindingsView:
        return self._findings

    @property
    def target(self) -> TargetView:
        return self._target

    @property
    def coverage(self) -> ProfileCoverage:
        return self._coverage

    @property
    def missing(self) -> MissingAnalysis:
        """Canonical missingness structure."""
        return self._analysis.missing_analysis

    @property
    def duplicates(self) -> DuplicateAnalysis:
        """Canonical exact duplicate-row groups."""
        return self._analysis.duplicate_analysis

    @property
    def anomalies(self) -> AnomalyAnalysis:
        """Canonical univariate numeric anomaly evidence."""
        return self._analysis.anomaly_analysis

    def __repr__(self) -> str:
        return (
            f"ProfileResult(rows={self.n_rows}, columns={self.n_columns}, "
            f"findings={len(self._findings_analysis.findings)}, "
            f"target={self._metadata.target_request.value})"
        )

    def _repr_html_(self) -> str:
        """Notebook HTML view of this result. Not stored on the result."""
        from pytics.presentation.notebook.profile import render_profile

        return render_profile(self)


def profile_result(
    frame: pd.DataFrame,
    *,
    target: object = None,
) -> ProfileResult:
    """Profile one DataFrame and return the public result.

    This calls the canonical dataset analysis once, then wraps it.
    ``target`` is passed through. ``None`` requests no target. A missing
    or ambiguous target raises from that analysis and does not return a
    result with the target quietly disabled.

    This is not :func:`pytics.profile`. That function still renders the
    legacy report.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("profile_result expects a pandas DataFrame")
    return ProfileResult.from_analysis(analyze_dataframe(frame, target=target))


def _position(index: object, length: int) -> int:
    """Translate an int index, including a negative one, to a position."""
    if type(index) is not int:
        raise TypeError("variables is indexed by an int position, not by a label")
    if index < 0:
        index += length
    if index < 0 or index >= length:
        raise IndexError("variable index out of range")
    return index


def _require_position(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{field} must be a physical column position")
    return value
