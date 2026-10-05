"""Retained findings: what is surfaced, about which subject, and why.

A finding selects one fact that a canonical analysis already retained
and marks it for attention. It names a code, a subject, a severity, and
typed evidence. It is not a statistic, a verdict, or a recommendation.
A finding does not say that data is wrong, that a column leaks the
target, or that a dataset is worse.

Each code has one scope, one subject type, and one evidence type.
Evidence is the canonical record by reference where one already holds
the trigger. The two snapshot records here copy counts exactly. No
field holds prose.

Identity is the code and a subject key. A column key is the label match
key plus occurrence used to align columns across datasets, so moving a
column, or inserting another one, keeps identity. A label that cannot be
retained falls back to its physical position. Severity is not part of
identity.

Severity is the attention level a policy assigns to a code. It is not
statistical significance, semantic confidence, or effect size. The
policy and the ordered result are in ``result``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.column_label import retained_column_label_match_key
from pytics.analysis.compare.alignment import ColumnAlignment
from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.schema import SemanticComparison
from pytics.analysis.compare.target_models import DiagnosticComparisonStatus
from pytics.analysis.compare.target_models import DiagnosticPredictabilityComparison
from pytics.analysis.compare.target_models import PredictorLeakageTransition
from pytics.analysis.compare.values import _require_count
from pytics.analysis.compare.values import _require_type
from pytics.analysis.target_leakage import ExactDuplicateEvidence
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import MappingEvidence
from pytics.analysis.target_leakage import MappingStatus
from pytics.semantics.column_evidence import BasicColumnEvidence


class FindingsSource(Enum):
    """Which canonical result a findings pass read."""

    PROFILE = "profile"
    COMPARE = "compare"


class FindingScope(Enum):
    """What kind of subject a finding is about.

    The scope says which analytical view holds the evidence. It follows
    from the code and is not stored separately.
    """

    DATASET = "dataset"
    COLUMN = "column"
    TARGET_PREDICTOR = "target_predictor"
    COMPARISON_COLUMN = "comparison_column"
    COMPARISON_TARGET = "comparison_target"
    COMPARISON_TARGET_PREDICTOR = "comparison_target_predictor"


class FindingCode(Enum):
    """The v0.1 catalog. A code names a condition, not a judgement.

    Comparison codes name the reference and comparison sides. They do
    not say added, removed, appeared, or disappeared, because neither
    dataset is assumed to be the older one.
    """

    EMPTY_COLUMN = "empty_column"
    CONSTANT_COLUMN = "constant_column"
    DUPLICATE_ROWS = "duplicate_rows"
    TARGET_EXACT_DUPLICATE_EVIDENCE = "target_exact_duplicate_evidence"
    TARGET_DETERMINISTIC_MAPPING_EVIDENCE = "target_deterministic_mapping_evidence"
    COLUMN_REFERENCE_ONLY = "column_reference_only"
    COLUMN_COMPARISON_ONLY = "column_comparison_only"
    SEMANTIC_TYPE_CHANGED = "semantic_type_changed"
    TARGET_TASK_CHANGED = "target_task_changed"
    TARGET_CLASS_VOCABULARY_CHANGED = "target_class_vocabulary_changed"
    TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED = "target_exact_duplicate_evidence_changed"


class FindingSeverity(Enum):
    """Attention level. Not significance, confidence, or effect size.

    ``INFO`` is a structural fact; every analysis that applies to the
    subject applies as computed. ``NOTABLE`` means analyses are removed
    from the subject, or a cross-dataset reading of it is unavailable or
    not like-for-like. ``WARNING`` is mechanical evidence that a retained
    result about the subject cannot be read at face value, because it
    measures sameness or a determined mapping. None of them means that
    the data is wrong.
    """

    INFO = "info"
    NOTABLE = "notable"
    WARNING = "warning"


class SuppressionRule(Enum):
    """Why a candidate finding is owned by another finding.

    ``EXACT_DUPLICATE_OWNS_MAPPING``: in a profile, an exact copy of a
    classification target is also a conflict-free mapping onto it.
    ``SEMANTIC_CHANGE_OWNS_TARGET_COMPARISON``: a semantic-type change
    determines the diagnostic task, the class set, and whether exact
    duplication is compared, so a difference in those is not
    like-for-like.
    """

    EXACT_DUPLICATE_OWNS_MAPPING = "exact_duplicate_owns_mapping"
    SEMANTIC_CHANGE_OWNS_TARGET_COMPARISON = "semantic_change_owns_target_comparison"


class DeferredFindingFamily(Enum):
    """Conditions with no v0.1 finding, because a policy is not decided.

    Their absence from a findings result is not evidence that the
    condition is absent.
    """

    MISSINGNESS_LEVEL = "missingness_level"
    CARDINALITY = "cardinality"
    UNIVARIATE_ANOMALY = "univariate_anomaly"
    NON_FINITE_VALUES = "non_finite_values"
    RELATIONSHIP_STRENGTH = "relationship_strength"
    RELATIONSHIP_CHANGE = "relationship_change"
    DISTRIBUTION_DRIFT = "distribution_drift"
    TARGET_DIAGNOSTIC_PERFORMANCE = "target_diagnostic_performance"


DEFERRED_FINDING_FAMILIES: Tuple[DeferredFindingFamily, ...] = tuple(
    DeferredFindingFamily
)


@dataclass(frozen=True)
class ColumnSubject:
    """One physical column of one dataset.

    ``position`` locates the column. ``occurrence`` counts labels with
    the same match key, from 1, in physical order. It is ``None`` exactly
    when the label could not be retained.
    """

    position: int
    label: RetainedColumnLabel
    occurrence: Optional[int]

    def __post_init__(self) -> None:
        _require_count(self.position, "position")
        _require_type(self.label, RetainedColumnLabel, "label")
        _require_occurrence(self.occurrence, self.label)

    @property
    def key(self) -> Tuple[object, ...]:
        """Identity of this column. Position only for an unsupported label."""
        if self.occurrence is None:
            return ("position", self.position)
        return ("label", retained_column_label_match_key(self.label), self.occurrence)


@dataclass(frozen=True)
class TargetPredictorSubject:
    """The explicit target and one other column of the same dataset."""

    target: ColumnSubject
    predictor: ColumnSubject

    def __post_init__(self) -> None:
        _require_type(self.target, ColumnSubject, "target")
        _require_type(self.predictor, ColumnSubject, "predictor")
        if self.target.position == self.predictor.position:
            raise ValueError("a predictor is a column other than the target")


@dataclass(frozen=True)
class ComparedTargetPredictorSubject:
    """The aligned target and one other aligned column."""

    target: ColumnAlignment
    predictor: ColumnAlignment

    def __post_init__(self) -> None:
        _require_type(self.target, ColumnAlignment, "target")
        _require_type(self.predictor, ColumnAlignment, "predictor")
        for alignment, field in (
            (self.target, "target"),
            (self.predictor, "predictor"),
        ):
            if alignment.status is not ColumnMatchStatus.MATCHED:
                raise ValueError(f"the {field} is a matched column")
        if self.target.reference_position == self.predictor.reference_position:
            raise ValueError("a predictor is a column other than the target")


Subject = Union[
    None,
    ColumnSubject,
    TargetPredictorSubject,
    ColumnAlignment,
    ComparedTargetPredictorSubject,
]


@dataclass(frozen=True)
class DuplicateRowsEvidence:
    """Exact duplicate-row counts copied from the duplicate analysis.

    The groups themselves stay on that analysis. A repeated row is not
    called an error.
    """

    n_rows: int
    n_duplicate_groups: int
    n_rows_in_duplicate_groups: int

    def __post_init__(self) -> None:
        _require_count(self.n_rows, "n_rows")
        _require_count(self.n_duplicate_groups, "n_duplicate_groups")
        _require_count(self.n_rows_in_duplicate_groups, "n_rows_in_duplicate_groups")
        if self.n_duplicate_groups < 1:
            raise ValueError("duplicate-row evidence has at least one group")
        if self.n_rows_in_duplicate_groups < 2 * self.n_duplicate_groups:
            raise ValueError("each duplicate group has at least two rows")
        if self.n_rows_in_duplicate_groups > self.n_rows:
            raise ValueError("duplicate rows cannot exceed n_rows")

    @property
    def n_excess_duplicate_rows(self) -> int:
        """Rows beyond one occurrence of each repeated row value."""
        return self.n_rows_in_duplicate_groups - self.n_duplicate_groups


@dataclass(frozen=True)
class SemanticTransitionEvidence:
    """A matched column whose selected semantic type differs.

    ``n_relationship_transitions`` counts aligned pairs with this column
    whose relationship family or eligibility differs between the sides.
    Those pairs are consequences of this change and are not findings.
    """

    semantic: SemanticComparison
    n_relationship_transitions: int

    def __post_init__(self) -> None:
        _require_type(self.semantic, SemanticComparison, "semantic")
        _require_count(self.n_relationship_transitions, "n_relationship_transitions")
        if self.semantic.selected_type_changed is not True:
            raise ValueError("a semantic transition has two different selected types")


Evidence = Union[
    BasicColumnEvidence,
    DuplicateRowsEvidence,
    ExactDuplicateEvidence,
    MappingEvidence,
    SemanticComparison,
    SemanticTransitionEvidence,
    DiagnosticPredictabilityComparison,
    PredictorLeakageTransition,
]


@dataclass(frozen=True)
class _Contract:
    source: FindingsSource
    scope: FindingScope
    subject: Optional[type]
    evidence: type


_CONTRACTS: Dict[FindingCode, _Contract] = {
    FindingCode.EMPTY_COLUMN: _Contract(
        FindingsSource.PROFILE,
        FindingScope.COLUMN,
        ColumnSubject,
        BasicColumnEvidence,
    ),
    FindingCode.CONSTANT_COLUMN: _Contract(
        FindingsSource.PROFILE,
        FindingScope.COLUMN,
        ColumnSubject,
        BasicColumnEvidence,
    ),
    FindingCode.DUPLICATE_ROWS: _Contract(
        FindingsSource.PROFILE,
        FindingScope.DATASET,
        None,
        DuplicateRowsEvidence,
    ),
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE: _Contract(
        FindingsSource.PROFILE,
        FindingScope.TARGET_PREDICTOR,
        TargetPredictorSubject,
        ExactDuplicateEvidence,
    ),
    FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE: _Contract(
        FindingsSource.PROFILE,
        FindingScope.TARGET_PREDICTOR,
        TargetPredictorSubject,
        MappingEvidence,
    ),
    FindingCode.COLUMN_REFERENCE_ONLY: _Contract(
        FindingsSource.COMPARE,
        FindingScope.COMPARISON_COLUMN,
        ColumnAlignment,
        SemanticComparison,
    ),
    FindingCode.COLUMN_COMPARISON_ONLY: _Contract(
        FindingsSource.COMPARE,
        FindingScope.COMPARISON_COLUMN,
        ColumnAlignment,
        SemanticComparison,
    ),
    FindingCode.SEMANTIC_TYPE_CHANGED: _Contract(
        FindingsSource.COMPARE,
        FindingScope.COMPARISON_COLUMN,
        ColumnAlignment,
        SemanticTransitionEvidence,
    ),
    FindingCode.TARGET_TASK_CHANGED: _Contract(
        FindingsSource.COMPARE,
        FindingScope.COMPARISON_TARGET,
        ColumnAlignment,
        DiagnosticPredictabilityComparison,
    ),
    FindingCode.TARGET_CLASS_VOCABULARY_CHANGED: _Contract(
        FindingsSource.COMPARE,
        FindingScope.COMPARISON_TARGET,
        ColumnAlignment,
        DiagnosticPredictabilityComparison,
    ),
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED: _Contract(
        FindingsSource.COMPARE,
        FindingScope.COMPARISON_TARGET_PREDICTOR,
        ComparedTargetPredictorSubject,
        PredictorLeakageTransition,
    ),
}


def codes_for(source: FindingsSource) -> Tuple[FindingCode, ...]:
    """Codes a findings pass over ``source`` can evaluate, in enum order."""
    return tuple(code for code in FindingCode if _CONTRACTS[code].source is source)


@dataclass(frozen=True)
class FindingIdentity:
    """Stable identity of one finding: its code and its subject key.

    The key is built from label match keys, occurrences, and fallback
    positions. Severity, evidence values, and policy are not part of it.
    """

    code: FindingCode
    subject: Tuple[object, ...]

    def __post_init__(self) -> None:
        _require_type(self.code, FindingCode, "code")
        if not isinstance(self.subject, tuple):
            raise TypeError("subject must be a tuple")


@dataclass(frozen=True)
class Finding:
    """One retained fact selected for attention.

    ``subject`` and ``evidence`` must have the types the code's contract
    names, and the evidence must hold the condition the code states.
    """

    code: FindingCode
    severity: FindingSeverity
    subject: Subject
    evidence: Evidence

    def __post_init__(self) -> None:
        _require_type(self.code, FindingCode, "code")
        _require_type(self.severity, FindingSeverity, "severity")
        contract = _CONTRACTS[self.code]
        if contract.subject is None:
            if self.subject is not None:
                raise ValueError(f"{self.code.name} is about the dataset")
        elif type(self.subject) is not contract.subject:
            raise TypeError(
                f"{self.code.name} subject must be a {contract.subject.__name__}"
            )
        if type(self.evidence) is not contract.evidence:
            raise TypeError(
                f"{self.code.name} evidence must be a {contract.evidence.__name__}"
            )
        _require_condition(self)

    @property
    def scope(self) -> FindingScope:
        return _CONTRACTS[self.code].scope

    @property
    def source(self) -> FindingsSource:
        return _CONTRACTS[self.code].source

    @property
    def identity(self) -> FindingIdentity:
        return FindingIdentity(code=self.code, subject=subject_key(self.subject))


@dataclass(frozen=True)
class SuppressedFinding:
    """A candidate finding owned by an emitted root finding.

    The candidate is kept whole, so the suppression can be inspected.
    It is not listed among the findings.
    """

    finding: Finding
    root: FindingIdentity
    rule: SuppressionRule

    def __post_init__(self) -> None:
        _require_type(self.finding, Finding, "finding")
        _require_type(self.root, FindingIdentity, "root")
        _require_type(self.rule, SuppressionRule, "rule")
        identity = self.finding.identity
        if identity == self.root:
            raise ValueError("a finding does not suppress itself")
        if self.rule is SuppressionRule.EXACT_DUPLICATE_OWNS_MAPPING:
            if (
                identity.code is not FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE
                or self.root.code is not FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE
            ):
                raise ValueError("a mapping is owned by the exact duplicate evidence")
            if identity.subject != self.root.subject:
                raise ValueError("the exact duplicate owns the same predictor")
            return
        if identity.code not in _TARGET_COMPARISON_CODES:
            raise ValueError("a semantic change owns target comparison findings")
        if self.root.code is not FindingCode.SEMANTIC_TYPE_CHANGED:
            raise ValueError("the root of a target comparison is a semantic change")
        if len(self.root.subject) != 1 or self.root.subject[0] not in identity.subject:
            raise ValueError("the semantic change is about a column of the finding")


_TARGET_COMPARISON_CODES = frozenset(
    {
        FindingCode.TARGET_TASK_CHANGED,
        FindingCode.TARGET_CLASS_VOCABULARY_CHANGED,
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED,
    }
)


def subject_key(subject: Subject) -> Tuple[object, ...]:
    """The identity key of a subject. Labels, not positions, where possible."""
    if subject is None:
        return ()
    if isinstance(subject, ColumnSubject):
        return (subject.key,)
    if isinstance(subject, TargetPredictorSubject):
        return (subject.target.key, subject.predictor.key)
    if isinstance(subject, ColumnAlignment):
        return (_alignment_key(subject),)
    if isinstance(subject, ComparedTargetPredictorSubject):
        return (_alignment_key(subject.target), _alignment_key(subject.predictor))
    raise TypeError("subject is not a finding subject")


def subject_order(subject: Subject) -> Tuple[int, ...]:
    """Dataset order of a subject. Not identity.

    Profile subjects follow physical position, and a target–predictor
    subject follows the predictor. Comparison columns follow alignment
    order: reference physical order, then comparison-only columns.
    """
    if subject is None:
        return ()
    if isinstance(subject, ColumnSubject):
        return (subject.position,)
    if isinstance(subject, TargetPredictorSubject):
        return (subject.predictor.position,)
    if isinstance(subject, ColumnAlignment):
        return _alignment_order(subject)
    if isinstance(subject, ComparedTargetPredictorSubject):
        return _alignment_order(subject.predictor)
    raise TypeError("subject is not a finding subject")


def _alignment_key(alignment: ColumnAlignment) -> Tuple[object, ...]:
    if alignment.occurrence is None:
        if alignment.reference_position is not None:
            return ("reference_position", alignment.reference_position)
        return ("comparison_position", alignment.comparison_position)
    label = alignment.reference_label
    if label is None:
        label = alignment.comparison_label
    return (
        "label",
        retained_column_label_match_key(label),  # type: ignore[arg-type]
        alignment.occurrence,
    )


def _alignment_order(alignment: ColumnAlignment) -> Tuple[int, ...]:
    if alignment.reference_position is not None:
        return (0, alignment.reference_position)
    return (1, alignment.comparison_position)  # type: ignore[return-value]


def _require_occurrence(occurrence: Optional[int], label: RetainedColumnLabel) -> None:
    unsupported = label.kind is ColumnLabelKind.UNSUPPORTED
    if occurrence is None:
        if not unsupported:
            raise ValueError("a retained label has an occurrence")
        return
    if unsupported:
        raise ValueError("an unsupported label has no occurrence")
    if type(occurrence) is not int or occurrence < 1:
        raise ValueError("occurrence must be a positive int")


def _require_condition(finding: Finding) -> None:
    """The evidence must hold the condition the code names."""
    code = finding.code
    evidence = finding.evidence
    subject = finding.subject
    if code is FindingCode.EMPTY_COLUMN:
        if not evidence.is_empty:  # type: ignore[union-attr]
            raise ValueError("an empty column has no non-missing value")
    elif code is FindingCode.CONSTANT_COLUMN:
        if not evidence.is_constant:  # type: ignore[union-attr]
            raise ValueError("a constant column has one distinct non-missing value")
    elif code is FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE:
        if evidence.status is not ExactDuplicateStatus.EXACT_DUPLICATE:  # type: ignore[union-attr]
            raise ValueError("exact duplicate evidence has that status")
    elif code is FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE:
        if not is_complete_repeated_mapping(evidence):  # type: ignore[arg-type]
            raise ValueError(
                "mapping evidence is a repeated mapping with no singleton value"
            )
    elif code is FindingCode.COLUMN_REFERENCE_ONLY:
        _require_one_side(subject, evidence, ColumnMatchStatus.REFERENCE_ONLY)  # type: ignore[arg-type]
    elif code is FindingCode.COLUMN_COMPARISON_ONLY:
        _require_one_side(subject, evidence, ColumnMatchStatus.COMPARISON_ONLY)  # type: ignore[arg-type]
    elif code is FindingCode.SEMANTIC_TYPE_CHANGED:
        if subject.status is not ColumnMatchStatus.MATCHED:  # type: ignore[union-attr]
            raise ValueError("a semantic change is about a matched column")
    elif code in (
        FindingCode.TARGET_TASK_CHANGED,
        FindingCode.TARGET_CLASS_VOCABULARY_CHANGED,
    ):
        _require_target_comparability(code, subject, evidence)  # type: ignore[arg-type]
    elif code is FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED:
        _require_exact_transition(subject, evidence)  # type: ignore[arg-type]


def is_complete_repeated_mapping(evidence: MappingEvidence) -> bool:
    """A repeated mapping in which every observed predictor value repeats.

    ``DETERMINISTIC_REPEATED`` needs only one repeated value. Exact
    duplicate rows give a nearly unique predictor such a value, so that
    status alone does not select attention. With no singleton value,
    every jointly observed row lies in a repeated, conflict-free group.
    """
    return (
        evidence.status is MappingStatus.DETERMINISTIC_REPEATED
        and evidence.n_singleton_groups == 0
    )


def _require_one_side(
    subject: ColumnAlignment,
    evidence: SemanticComparison,
    status: ColumnMatchStatus,
) -> None:
    if subject.status is not status:
        raise ValueError(f"the column alignment is {status.value}")
    reference_side = status is ColumnMatchStatus.REFERENCE_ONLY
    if (evidence.reference is not None) is not reference_side or (
        evidence.comparison is not None
    ) is reference_side:
        raise ValueError("the semantic snapshot is on the side that has the column")


def _require_target_comparability(
    code: FindingCode,
    subject: ColumnAlignment,
    evidence: DiagnosticPredictabilityComparison,
) -> None:
    if subject.status is not ColumnMatchStatus.MATCHED:
        raise ValueError("a target comparison is about the aligned target")
    expected = (
        DiagnosticComparisonStatus.TASK_TRANSITION
        if code is FindingCode.TARGET_TASK_CHANGED
        else DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED
    )
    if evidence.status is not expected:
        raise ValueError(f"the diagnostic comparison status is {expected.value}")


def _require_exact_transition(
    subject: ComparedTargetPredictorSubject,
    evidence: PredictorLeakageTransition,
) -> None:
    promoted = ExactDuplicateStatus.EXACT_DUPLICATE
    if (evidence.reference_exact is promoted) is (
        evidence.comparison_exact is promoted
    ):
        raise ValueError("exactly one side has exact duplicate evidence")
    predictor = subject.predictor
    if (
        evidence.reference_position != predictor.reference_position
        or evidence.comparison_position != predictor.comparison_position
    ):
        raise ValueError("the leakage transition is the predictor's")
