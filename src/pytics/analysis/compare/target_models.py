"""Retained target-drift records.

Target drift is four separate readings of one aligned target: its
existing univariate distribution drift, the relationship-drift records
that include it, a descriptive comparison of held-out diagnostic
metrics, and mechanical leakage-evidence transitions. There is no
target-drift score and no claim that a concept changed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.compare.distribution_models import BooleanDistributionDrift
from pytics.analysis.compare.distribution_models import CategoricalDistributionDrift
from pytics.analysis.compare.distribution_models import DistributionDriftStatus
from pytics.analysis.compare.distribution_models import NumericDistributionDrift
from pytics.analysis.compare.relationship_models import VocabularyStatus
from pytics.analysis.compare.values import _require_count
from pytics.analysis.compare.values import _require_optional
from pytics.analysis.compare.values import _require_type
from pytics.analysis.target_diagnostic import DiagnosticMetric
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import PredictiveTask
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import MappingStatus
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


class TargetAlignmentStatus(Enum):
    """Where the requested target sits across the two datasets.

    ``ALIGNED`` is one logical column. ``IDENTITY_MISMATCH`` means the
    two resolved positions are different columns. ``NOT_IN_EITHER`` means
    the request named a column that is in neither dataset. A missing
    target request is not a member of this enum: the comparison then has
    no target-drift record at all.
    """

    ALIGNED = "aligned"
    REFERENCE_ONLY = "reference_only"
    COMPARISON_ONLY = "comparison_only"
    IDENTITY_MISMATCH = "identity_mismatch"
    NOT_IN_EITHER = "not_in_either"


class TargetColumnRole(Enum):
    """How the target sits in one side of a relationship-drift record.

    ``SYMMETRIC`` means the effect does not assign the target an
    analytical side. The other members are the roles already stored on
    the relationship. ``UNSUPPORTED`` means that side has no calculated
    family. None of these roles moves the target to the left of an effect.
    """

    SYMMETRIC = "symmetric"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN_GROUP = "boolean_group"
    CONDITIONING = "conditioning"
    OUTCOME = "outcome"
    UNSUPPORTED = "unsupported"


class DiagnosticComparisonStatus(Enum):
    """Whether held-out diagnostic metrics can be subtracted.

    ``COMPARED`` is a descriptive difference of metrics from two separate
    holdout fits. It is not a test and not a degradation label.
    ``TASK_TRANSITION`` means the predictive tasks differ, including a
    task present on only one side. ``CLASS_VOCABULARY_CHANGED`` means a
    classification task stayed the same kind of task while the class set
    did not. Metrics are not subtracted in that case.
    """

    COMPARED = "compared"
    NOT_COLLECTED = "not_collected"
    TASK_TRANSITION = "task_transition"
    CLASS_VOCABULARY_CHANGED = "class_vocabulary_changed"
    EVALUATION_UNAVAILABLE = "evaluation_unavailable"


class LeakageComparisonStatus(Enum):
    """Whether mechanical leakage evidence can be placed side by side.

    A transition of statuses is not a leakage verdict.
    """

    COMPARED = "compared"
    NOT_COLLECTED = "not_collected"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class TargetDriftAlignment:
    """Identity of the requested target.

    ``selected_type_changed`` and ``resolution_changed`` are set only
    when the target is one aligned column. They are not set by comparing
    two different columns.
    """

    status: TargetAlignmentStatus
    reference_position: Optional[int] = None
    comparison_position: Optional[int] = None
    occurrence: Optional[int] = None
    reference_label: Optional[RetainedColumnLabel] = None
    comparison_label: Optional[RetainedColumnLabel] = None
    reference_selected_type: Optional[SemanticType] = None
    comparison_selected_type: Optional[SemanticType] = None
    reference_resolution: Optional[ResolutionStatus] = None
    comparison_resolution: Optional[ResolutionStatus] = None
    selected_type_changed: Optional[bool] = None
    resolution_changed: Optional[bool] = None

    def __post_init__(self) -> None:
        _require_type(self.status, TargetAlignmentStatus, "status")
        _require_optional_position(self.reference_position, "reference_position")
        _require_optional_position(self.comparison_position, "comparison_position")
        _require_optional(self.reference_label, RetainedColumnLabel, "reference_label")
        _require_optional(
            self.comparison_label, RetainedColumnLabel, "comparison_label"
        )
        _require_optional(
            self.reference_selected_type, SemanticType, "reference_selected_type"
        )
        _require_optional(
            self.comparison_selected_type, SemanticType, "comparison_selected_type"
        )
        _require_optional(
            self.reference_resolution, ResolutionStatus, "reference_resolution"
        )
        _require_optional(
            self.comparison_resolution, ResolutionStatus, "comparison_resolution"
        )
        _require_optional_bool(self.selected_type_changed, "selected_type_changed")
        _require_optional_bool(self.resolution_changed, "resolution_changed")
        if self.occurrence is not None and (
            type(self.occurrence) is not int or self.occurrence < 1
        ):
            raise ValueError("occurrence must be a positive int or None")
        _require_alignment_shape(self)


@dataclass(frozen=True)
class TargetDistributionProjection:
    """The target column's existing distribution-drift record.

    ``distribution`` is that column record's object when one exists.
    This projection does not calculate another distance or another test.
    """

    column_index: int
    distribution_status: DistributionDriftStatus
    distribution: Optional[DistributionDrift]

    def __post_init__(self) -> None:
        _require_count(self.column_index, "column_index")
        _require_type(
            self.distribution_status,
            DistributionDriftStatus,
            "distribution_status",
        )
        if self.distribution is not None and not isinstance(
            self.distribution,
            (
                NumericDistributionDrift,
                CategoricalDistributionDrift,
                BooleanDistributionDrift,
            ),
        ):
            raise TypeError("distribution must be a distribution-drift record")


@dataclass(frozen=True)
class TargetRelationshipProjection:
    """One relationship-drift record read from the target.

    ``drift_index`` locates the record. The effect stays on that record.
    Roles say which analytical side the target already occupies. They do
    not recompute the effect.
    """

    drift_index: int
    other_reference_position: int
    other_comparison_position: int
    reference_role: TargetColumnRole
    comparison_role: TargetColumnRole

    def __post_init__(self) -> None:
        _require_count(self.drift_index, "drift_index")
        _require_count(self.other_reference_position, "other_reference_position")
        _require_count(self.other_comparison_position, "other_comparison_position")
        _require_type(self.reference_role, TargetColumnRole, "reference_role")
        _require_type(self.comparison_role, TargetColumnRole, "comparison_role")


@dataclass(frozen=True)
class DiagnosticMetricChange:
    """``comparison - reference`` for one held-out metric.

    Model and baseline are stored separately. A missing value stays
    missing: the change is not zero. The sign of ``model_change`` is the
    arithmetic direction, not an improvement flag.
    """

    metric: DiagnosticMetric
    reference_model: Optional[float]
    comparison_model: Optional[float]
    model_change: Optional[float]
    reference_baseline: Optional[float]
    comparison_baseline: Optional[float]
    baseline_change: Optional[float]

    def __post_init__(self) -> None:
        _require_type(self.metric, DiagnosticMetric, "metric")
        _require_metric_change(
            self.reference_model, self.comparison_model, self.model_change, "model"
        )
        _require_metric_change(
            self.reference_baseline,
            self.comparison_baseline,
            self.baseline_change,
            "baseline",
        )


@dataclass(frozen=True)
class DiagnosticPredictabilityComparison:
    """Descriptive change in held-out diagnostic metrics.

    Two independently fitted holdout models are not a test that
    predictive performance drifted. No probability is stored.
    """

    status: DiagnosticComparisonStatus
    reference_task: Optional[PredictiveTask] = None
    comparison_task: Optional[PredictiveTask] = None
    reference_status: Optional[DiagnosticStatus] = None
    comparison_status: Optional[DiagnosticStatus] = None
    class_vocabulary: Optional[VocabularyStatus] = None
    metrics: Tuple[DiagnosticMetricChange, ...] = ()

    def __post_init__(self) -> None:
        _require_type(self.status, DiagnosticComparisonStatus, "status")
        _require_optional(self.reference_task, PredictiveTask, "reference_task")
        _require_optional(self.comparison_task, PredictiveTask, "comparison_task")
        _require_optional(self.reference_status, DiagnosticStatus, "reference_status")
        _require_optional(
            self.comparison_status, DiagnosticStatus, "comparison_status"
        )
        _require_optional(self.class_vocabulary, VocabularyStatus, "class_vocabulary")
        if not isinstance(self.metrics, tuple):
            raise TypeError("metrics must be a tuple")
        for item in self.metrics:
            _require_type(item, DiagnosticMetricChange, "metrics")
        if self.status is DiagnosticComparisonStatus.COMPARED:
            if not self.metrics:
                raise ValueError("a compared diagnostic has its metrics")
            if (
                self.reference_task is None
                or self.reference_task is not self.comparison_task
            ):
                raise ValueError("compared diagnostics share a predictive task")
            if self.reference_task.is_classification:
                if self.class_vocabulary is not VocabularyStatus.SAME:
                    raise ValueError("compared classification shares a class set")
            elif self.class_vocabulary is not None:
                raise ValueError("regression has no class vocabulary")
            return
        if self.metrics:
            raise ValueError("only a compared diagnostic stores metric changes")
        if self.status is DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED:
            if self.class_vocabulary is not VocabularyStatus.CHANGED:
                raise ValueError("a class-vocabulary failure records that change")
            if self.reference_task is None or self.reference_task is not self.comparison_task:
                raise ValueError("class vocabulary is compared within one task")
            if not self.reference_task.is_classification:
                raise ValueError("class vocabulary belongs to classification")
        if self.status is DiagnosticComparisonStatus.TASK_TRANSITION:
            if self.reference_task is self.comparison_task:
                raise ValueError("a task transition has two different tasks")


@dataclass(frozen=True)
class PredictorLeakageTransition:
    """Mechanical leakage statuses for one aligned predictor.

    A changed status is evidence that the mechanical finding differs.
    It is not a determination that the column contaminates the target.
    """

    reference_position: int
    comparison_position: int
    occurrence: int
    reference_exact: ExactDuplicateStatus
    comparison_exact: ExactDuplicateStatus
    reference_mapping: MappingStatus
    comparison_mapping: MappingStatus

    def __post_init__(self) -> None:
        _require_count(self.reference_position, "reference_position")
        _require_count(self.comparison_position, "comparison_position")
        _require_count(self.occurrence, "occurrence")
        if self.occurrence < 1:
            raise ValueError("occurrence must be a positive int")
        _require_type(self.reference_exact, ExactDuplicateStatus, "reference_exact")
        _require_type(self.comparison_exact, ExactDuplicateStatus, "comparison_exact")
        _require_type(self.reference_mapping, MappingStatus, "reference_mapping")
        _require_type(self.comparison_mapping, MappingStatus, "comparison_mapping")

    @property
    def exact_status_changed(self) -> bool:
        """Whether the exact-duplicate statuses differ."""
        return self.reference_exact is not self.comparison_exact

    @property
    def mapping_status_changed(self) -> bool:
        """Whether the repeated-mapping statuses differ."""
        return self.reference_mapping is not self.comparison_mapping


@dataclass(frozen=True)
class LeakageEvidenceComparison:
    """Leakage-evidence transitions for predictors aligned with the target."""

    status: LeakageComparisonStatus
    transitions: Tuple[PredictorLeakageTransition, ...] = ()

    def __post_init__(self) -> None:
        _require_type(self.status, LeakageComparisonStatus, "status")
        if not isinstance(self.transitions, tuple):
            raise TypeError("transitions must be a tuple")
        previous = -1
        for item in self.transitions:
            _require_type(item, PredictorLeakageTransition, "transitions")
            if item.reference_position <= previous:
                raise ValueError("leakage transitions follow reference position")
            previous = item.reference_position
        if self.status is not LeakageComparisonStatus.COMPARED and self.transitions:
            raise ValueError("only a compared leakage result stores transitions")


@dataclass(frozen=True)
class TargetDriftCoverage:
    """Counts for one target-drift result. They are not a score."""

    distribution_projected: bool
    n_relationship_projections: int
    diagnostic_compared: bool
    n_diagnostic_metrics: int
    n_leakage_transitions: int
    n_exact_status_changes: int
    n_mapping_status_changes: int

    def __post_init__(self) -> None:
        if type(self.distribution_projected) is not bool:
            raise TypeError("distribution_projected must be a bool")
        if type(self.diagnostic_compared) is not bool:
            raise TypeError("diagnostic_compared must be a bool")
        _require_count(self.n_relationship_projections, "n_relationship_projections")
        _require_count(self.n_diagnostic_metrics, "n_diagnostic_metrics")
        _require_count(self.n_leakage_transitions, "n_leakage_transitions")
        _require_count(self.n_exact_status_changes, "n_exact_status_changes")
        _require_count(self.n_mapping_status_changes, "n_mapping_status_changes")
        if self.n_exact_status_changes > self.n_leakage_transitions:
            raise ValueError("exact-status changes cannot exceed leakage transitions")
        if self.n_mapping_status_changes > self.n_leakage_transitions:
            raise ValueError("mapping-status changes cannot exceed leakage transitions")
        if self.diagnostic_compared is not (self.n_diagnostic_metrics > 0):
            raise ValueError("diagnostic metrics exist exactly when metrics are compared")


@dataclass(frozen=True)
class TargetDriftAnalysis:
    """Target-related change for one explicit comparison target.

    Branches that do not apply to the alignment are absent. A configured
    target that is not aligned still has this record, so absence of a
    target request and failure to align stay distinct.
    """

    alignment: TargetDriftAlignment
    coverage: TargetDriftCoverage
    distribution: Optional[TargetDistributionProjection] = None
    relationships: Tuple[TargetRelationshipProjection, ...] = ()
    diagnostic: Optional[DiagnosticPredictabilityComparison] = None
    leakage: Optional[LeakageEvidenceComparison] = None

    def __post_init__(self) -> None:
        _require_type(self.alignment, TargetDriftAlignment, "alignment")
        _require_type(self.coverage, TargetDriftCoverage, "coverage")
        _require_optional(
            self.distribution, TargetDistributionProjection, "distribution"
        )
        if not isinstance(self.relationships, tuple):
            raise TypeError("relationships must be a tuple")
        previous = -1
        for item in self.relationships:
            _require_type(item, TargetRelationshipProjection, "relationships")
            if item.drift_index <= previous:
                raise ValueError("target relationships follow drift index")
            previous = item.drift_index
        _require_optional(
            self.diagnostic, DiagnosticPredictabilityComparison, "diagnostic"
        )
        _require_optional(self.leakage, LeakageEvidenceComparison, "leakage")
        aligned = self.alignment.status is TargetAlignmentStatus.ALIGNED
        if not aligned:
            if (
                self.distribution is not None
                or self.relationships
                or self.diagnostic is not None
                or self.leakage is not None
            ):
                raise ValueError("an unaligned target has no projected change")
        elif self.distribution is None or self.diagnostic is None or self.leakage is None:
            raise ValueError("an aligned target projects distribution, diagnostics, and leakage")
        if self.coverage != coverage_from_target(self):
            raise ValueError("target coverage does not match the target record")


def coverage_from_target(target: TargetDriftAnalysis) -> TargetDriftCoverage:
    """Count one target-drift result. Nothing is recalculated."""
    distribution = target.distribution
    projected = distribution is not None and distribution.distribution is not None
    diagnostic = target.diagnostic
    compared = (
        diagnostic is not None
        and diagnostic.status is DiagnosticComparisonStatus.COMPARED
    )
    leakage = target.leakage
    transitions = () if leakage is None else leakage.transitions
    return TargetDriftCoverage(
        distribution_projected=projected,
        n_relationship_projections=len(target.relationships),
        diagnostic_compared=compared,
        n_diagnostic_metrics=0 if diagnostic is None else len(diagnostic.metrics),
        n_leakage_transitions=len(transitions),
        n_exact_status_changes=sum(
            item.exact_status_changed for item in transitions
        ),
        n_mapping_status_changes=sum(
            item.mapping_status_changed for item in transitions
        ),
    )


def _require_alignment_shape(alignment: TargetDriftAlignment) -> None:
    status = alignment.status
    reference = alignment.reference_position is not None
    comparison = alignment.comparison_position is not None
    if status is TargetAlignmentStatus.NOT_IN_EITHER:
        if reference or comparison or alignment.occurrence is not None:
            raise ValueError("a missing target has no column")
        _require_side_absent(alignment, reference_side=True)
        _require_side_absent(alignment, reference_side=False)
        _require_no_change_flags(alignment)
        return
    if status is TargetAlignmentStatus.REFERENCE_ONLY:
        if not reference or comparison:
            raise ValueError("a reference-only target has only a reference position")
        _require_side_present(alignment, reference_side=True)
        _require_side_absent(alignment, reference_side=False)
        _require_no_change_flags(alignment)
        if alignment.occurrence is not None:
            raise ValueError("only an aligned target has an occurrence")
        return
    if status is TargetAlignmentStatus.COMPARISON_ONLY:
        if not comparison or reference:
            raise ValueError("a comparison-only target has only a comparison position")
        _require_side_present(alignment, reference_side=False)
        _require_side_absent(alignment, reference_side=True)
        _require_no_change_flags(alignment)
        if alignment.occurrence is not None:
            raise ValueError("only an aligned target has an occurrence")
        return
    if not reference or not comparison:
        raise ValueError("this target status has two positions")
    if status is TargetAlignmentStatus.IDENTITY_MISMATCH:
        _require_side_present(alignment, reference_side=True)
        _require_side_present(alignment, reference_side=False)
        _require_no_change_flags(alignment)
        if alignment.occurrence is not None:
            raise ValueError("only an aligned target has an occurrence")
        return
    if alignment.occurrence is None:
        raise ValueError("an aligned target has an occurrence")
    if alignment.reference_label is None or alignment.comparison_label is None:
        raise ValueError("an aligned target has two labels")
    if alignment.selected_type_changed is None or alignment.resolution_changed is None:
        raise ValueError("an aligned target records semantic change")
    if alignment.selected_type_changed is not (
        alignment.reference_selected_type is not alignment.comparison_selected_type
    ):
        raise ValueError("selected-type change must follow the two types")
    if alignment.resolution_changed is not (
        alignment.reference_resolution is not alignment.comparison_resolution
    ):
        raise ValueError("resolution change must follow the two statuses")


def _require_side_present(alignment: TargetDriftAlignment, *, reference_side: bool) -> None:
    if reference_side:
        label = alignment.reference_label
        resolution = alignment.reference_resolution
        selected = alignment.reference_selected_type
    else:
        label = alignment.comparison_label
        resolution = alignment.comparison_resolution
        selected = alignment.comparison_selected_type
    if label is None or resolution is None:
        raise ValueError("this target side has its label and resolution")
    if resolution is ResolutionStatus.RESOLVED:
        if selected is None:
            raise ValueError("a resolved target side has a selected type")
        return
    if selected is not None:
        raise ValueError("an unresolved target side has no selected type")


def _require_side_absent(alignment: TargetDriftAlignment, *, reference_side: bool) -> None:
    if reference_side:
        if (
            alignment.reference_label is not None
            or alignment.reference_selected_type is not None
            or alignment.reference_resolution is not None
        ):
            raise ValueError("this target status has no reference state")
        return
    if (
        alignment.comparison_label is not None
        or alignment.comparison_selected_type is not None
        or alignment.comparison_resolution is not None
    ):
        raise ValueError("this target status has no comparison state")


def _require_no_change_flags(alignment: TargetDriftAlignment) -> None:
    if (
        alignment.selected_type_changed is not None
        or alignment.resolution_changed is not None
    ):
        raise ValueError("semantic-change flags belong to an aligned target")


def _require_metric_change(
    reference: Optional[float],
    comparison: Optional[float],
    change: Optional[float],
    field: str,
) -> None:
    _require_optional_finite(reference, field)
    _require_optional_finite(comparison, field)
    _require_optional_finite(change, field)
    if reference is None or comparison is None:
        if change is not None:
            raise ValueError(f"{field} change requires both metric values")
        return
    expected = comparison - reference
    if expected == 0.0:
        expected = 0.0
    if not math.isfinite(expected):
        if change is not None:
            raise ValueError(f"a non-finite {field} change is absent")
        return
    if change != expected:
        raise ValueError(f"{field} change must be comparison minus reference")


def _require_optional_finite(value: Optional[float], field: str) -> None:
    if value is None:
        return
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float or None")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


def _require_optional_position(value: Optional[int], field: str) -> None:
    if value is None:
        return
    _require_count(value, field)


def _require_optional_bool(value: Optional[bool], field: str) -> None:
    if value is not None and type(value) is not bool:
        raise TypeError(f"{field} must be a bool or None")
