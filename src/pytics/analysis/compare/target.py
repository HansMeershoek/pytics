"""Target drift as a projection of comparison evidence.

Distribution drift is the target column's existing univariate record.
Relationship drift is the subset of relationship-drift records that
include the target. Diagnostic metrics are subtracted only when the
predictive tasks and, for classification, the class sets match.
Leakage evidence is a transition of mechanical statuses.

No branch refits a model, rereads a frame, or calculates a relationship
statistic. A target that was not requested never reaches this module.
"""

from __future__ import annotations

from typing import Optional
from typing import Tuple

from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.models import ColumnComparison
from pytics.analysis.compare.relationship_models import RelationshipDrift
from pytics.analysis.compare.relationship_models import RelationshipFamily
from pytics.analysis.compare.relationship_models import RelationshipSide
from pytics.analysis.compare.relationship_models import RelationshipSideKind
from pytics.analysis.compare.relationship_models import VocabularyStatus
from pytics.analysis.compare.relationship_models import _finite_difference
from pytics.analysis.compare.relationships import _same_levels
from pytics.analysis.compare.target_models import DiagnosticComparisonStatus
from pytics.analysis.compare.target_models import DiagnosticMetricChange
from pytics.analysis.compare.target_models import DiagnosticPredictabilityComparison
from pytics.analysis.compare.target_models import LeakageComparisonStatus
from pytics.analysis.compare.target_models import LeakageEvidenceComparison
from pytics.analysis.compare.target_models import PredictorLeakageTransition
from pytics.analysis.compare.target_models import TargetAlignmentStatus
from pytics.analysis.compare.target_models import TargetColumnRole
from pytics.analysis.compare.target_models import TargetDistributionProjection
from pytics.analysis.compare.target_models import TargetDriftAlignment
from pytics.analysis.compare.target_models import TargetDriftAnalysis
from pytics.analysis.compare.target_models import TargetDriftCoverage
from pytics.analysis.compare.target_models import TargetRelationshipProjection
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.target_diagnostic import ClassificationEvaluation
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import MetricComparison
from pytics.analysis.target_diagnostic import RegressionEvaluation
from pytics.analysis.target_diagnostic import TargetDiagnosticAnalysis
from pytics.analysis.target_leakage import LeakageApplicability
from pytics.analysis.target_leakage import TargetLeakageAnalysis


def compare_target(
    *,
    reference_position: Optional[int],
    comparison_position: Optional[int],
    columns: Tuple[ColumnComparison, ...],
    relationships: Tuple[RelationshipDrift, ...],
    reference: DatasetAnalysis,
    comparison: DatasetAnalysis,
) -> TargetDriftAnalysis:
    """Project target change from a finished comparison.

    ``reference_position`` and ``comparison_position`` are the columns
    the caller resolved. Either may be absent. This function does not
    choose a target.
    """
    _require_requested_analysis(reference, reference_position)
    _require_requested_analysis(comparison, comparison_position)
    if reference_position is None and comparison_position is None:
        return _bare(TargetAlignmentStatus.NOT_IN_EITHER)
    if reference_position is None:
        _, column = _column_by_comparison(columns, comparison_position)  # type: ignore[arg-type]
        return _bare(
            TargetAlignmentStatus.COMPARISON_ONLY,
            comparison_position=comparison_position,
            comparison_column=column,
        )
    if comparison_position is None:
        _, column = _column_by_reference(columns, reference_position)
        return _bare(
            TargetAlignmentStatus.REFERENCE_ONLY,
            reference_position=reference_position,
            reference_column=column,
        )
    reference_index, reference_column = _column_by_reference(
        columns, reference_position
    )
    _, comparison_column = _column_by_comparison(columns, comparison_position)
    if reference_column is not comparison_column:
        return _bare(
            TargetAlignmentStatus.IDENTITY_MISMATCH,
            reference_position=reference_position,
            comparison_position=comparison_position,
            reference_column=reference_column,
            comparison_column=comparison_column,
        )
    alignment = _aligned(reference_column)
    distribution = TargetDistributionProjection(
        column_index=reference_index,
        distribution_status=reference_column.distribution_status,
        distribution=reference_column.distribution,
    )
    projected = _project_relationships(reference_position, relationships)
    diagnostic = _diagnostic(
        reference.target_diagnostic,
        comparison.target_diagnostic,
    )
    leakage = _leakage(
        reference.target_leakage,
        comparison.target_leakage,
        columns,
        reference_position,
    )
    return TargetDriftAnalysis(
        alignment=alignment,
        coverage=_coverage(distribution, projected, diagnostic, leakage),
        distribution=distribution,
        relationships=projected,
        diagnostic=diagnostic,
        leakage=leakage,
    )


def _coverage(distribution, relationships, diagnostic, leakage) -> TargetDriftCoverage:
    transitions = leakage.transitions
    return TargetDriftCoverage(
        distribution_projected=distribution.distribution is not None,
        n_relationship_projections=len(relationships),
        diagnostic_compared=diagnostic.status is DiagnosticComparisonStatus.COMPARED,
        n_diagnostic_metrics=len(diagnostic.metrics),
        n_leakage_transitions=len(transitions),
        n_exact_status_changes=sum(item.exact_status_changed for item in transitions),
        n_mapping_status_changes=sum(
            item.mapping_status_changed for item in transitions
        ),
    )


def _empty_coverage() -> TargetDriftCoverage:
    return TargetDriftCoverage(
        distribution_projected=False,
        n_relationship_projections=0,
        diagnostic_compared=False,
        n_diagnostic_metrics=0,
        n_leakage_transitions=0,
        n_exact_status_changes=0,
        n_mapping_status_changes=0,
    )


def _bare(
    status: TargetAlignmentStatus,
    *,
    reference_position: Optional[int] = None,
    comparison_position: Optional[int] = None,
    reference_column: Optional[ColumnComparison] = None,
    comparison_column: Optional[ColumnComparison] = None,
) -> TargetDriftAnalysis:
    alignment = TargetDriftAlignment(
        status=status,
        reference_position=reference_position,
        comparison_position=comparison_position,
        **_side_fields(reference_column, comparison_column),
    )
    return TargetDriftAnalysis(alignment=alignment, coverage=_empty_coverage())


def _aligned(column: ColumnComparison) -> TargetDriftAlignment:
    alignment = column.alignment
    semantic = column.semantic
    reference = semantic.reference
    comparison = semantic.comparison
    if (
        alignment.reference_position is None
        or alignment.comparison_position is None
        or alignment.occurrence is None
        or reference is None
        or comparison is None
    ):
        raise ValueError("an aligned target column is matched")
    return TargetDriftAlignment(
        status=TargetAlignmentStatus.ALIGNED,
        reference_position=alignment.reference_position,
        comparison_position=alignment.comparison_position,
        occurrence=alignment.occurrence,
        reference_label=alignment.reference_label,
        comparison_label=alignment.comparison_label,
        reference_selected_type=reference.selected_type,
        comparison_selected_type=comparison.selected_type,
        reference_resolution=reference.resolution_status,
        comparison_resolution=comparison.resolution_status,
        selected_type_changed=semantic.selected_type_changed,
        resolution_changed=semantic.resolution_status_changed,
    )


def _side_fields(
    reference_column: Optional[ColumnComparison],
    comparison_column: Optional[ColumnComparison],
) -> dict:
    fields = {}
    if reference_column is not None:
        fields.update(_one_side(reference_column, reference_side=True))
    if comparison_column is not None:
        fields.update(_one_side(comparison_column, reference_side=False))
    return fields


def _one_side(column: ColumnComparison, *, reference_side: bool) -> dict:
    alignment = column.alignment
    snapshot = (
        column.semantic.reference if reference_side else column.semantic.comparison
    )
    if snapshot is None:
        raise ValueError("a present target column has a semantic snapshot")
    prefix = "reference" if reference_side else "comparison"
    label = alignment.reference_label if reference_side else alignment.comparison_label
    return {
        f"{prefix}_label": label,
        f"{prefix}_selected_type": snapshot.selected_type,
        f"{prefix}_resolution": snapshot.resolution_status,
    }


def _project_relationships(
    target_position: int,
    relationships: Tuple[RelationshipDrift, ...],
) -> Tuple[TargetRelationshipProjection, ...]:
    projected = []
    for index, record in enumerate(relationships):
        first = record.alignment.first.reference_position
        second = record.alignment.second.reference_position
        if target_position not in (first, second):
            continue
        target_is_first = target_position == first
        other = record.alignment.second if target_is_first else record.alignment.first
        projected.append(
            TargetRelationshipProjection(
                drift_index=index,
                other_reference_position=other.reference_position,
                other_comparison_position=other.comparison_position,
                reference_role=_role(record.reference, target_is_first),
                comparison_role=_role(record.comparison, target_is_first),
            )
        )
    return tuple(projected)


def _role(side: RelationshipSide, target_is_first: bool) -> TargetColumnRole:
    if side.kind is not RelationshipSideKind.CALCULATED or side.family is None:
        return TargetColumnRole.UNSUPPORTED
    if side.family in (
        RelationshipFamily.NUMERIC_NUMERIC,
        RelationshipFamily.CATEGORICAL_CATEGORICAL,
    ):
        return TargetColumnRole.SYMMETRIC
    if side.family is RelationshipFamily.NUMERIC_CATEGORICAL:
        state = side.numeric_categorical
        if state.numeric_is_first is target_is_first:  # type: ignore[union-attr]
            return TargetColumnRole.NUMERIC
        return TargetColumnRole.CATEGORICAL
    if side.family is RelationshipFamily.NUMERIC_BOOLEAN:
        state = side.numeric_boolean
        if state.numeric_is_first is target_is_first:  # type: ignore[union-attr]
            return TargetColumnRole.NUMERIC
        return TargetColumnRole.BOOLEAN_GROUP
    state = side.boolean_boolean
    if state.conditioning_is_first is target_is_first:  # type: ignore[union-attr]
        return TargetColumnRole.CONDITIONING
    return TargetColumnRole.OUTCOME


def _diagnostic(
    reference: Optional[TargetDiagnosticAnalysis],
    comparison: Optional[TargetDiagnosticAnalysis],
) -> DiagnosticPredictabilityComparison:
    if reference is None or comparison is None:
        return DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.NOT_COLLECTED,
            reference_status=None if reference is None else reference.status,
            comparison_status=None if comparison is None else comparison.status,
            reference_task=None if reference is None else reference.task,
            comparison_task=None if comparison is None else comparison.task,
        )
    if reference.task is not comparison.task:
        return DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.TASK_TRANSITION,
            reference_task=reference.task,
            comparison_task=comparison.task,
            reference_status=reference.status,
            comparison_status=comparison.status,
        )
    vocabulary = _class_vocabulary(reference, comparison)
    if (
        reference.task is not None
        and reference.task.is_classification
        and vocabulary is VocabularyStatus.CHANGED
    ):
        return DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED,
            reference_task=reference.task,
            comparison_task=comparison.task,
            reference_status=reference.status,
            comparison_status=comparison.status,
            class_vocabulary=vocabulary,
        )
    if (
        reference.status is not DiagnosticStatus.AVAILABLE
        or comparison.status is not DiagnosticStatus.AVAILABLE
        or reference.evaluation is None
        or comparison.evaluation is None
    ):
        return DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.EVALUATION_UNAVAILABLE,
            reference_task=reference.task,
            comparison_task=comparison.task,
            reference_status=reference.status,
            comparison_status=comparison.status,
            class_vocabulary=(
                vocabulary
                if reference.task is not None and reference.task.is_classification
                else None
            ),
        )
    if reference.task is not None and reference.task.is_classification:
        if vocabulary is not VocabularyStatus.SAME:
            return DiagnosticPredictabilityComparison(
                status=DiagnosticComparisonStatus.EVALUATION_UNAVAILABLE,
                reference_task=reference.task,
                comparison_task=comparison.task,
                reference_status=reference.status,
                comparison_status=comparison.status,
            )
    return DiagnosticPredictabilityComparison(
        status=DiagnosticComparisonStatus.COMPARED,
        reference_task=reference.task,
        comparison_task=comparison.task,
        reference_status=reference.status,
        comparison_status=comparison.status,
        class_vocabulary=(
            vocabulary
            if reference.task is not None and reference.task.is_classification
            else None
        ),
        metrics=_metric_changes(reference.evaluation, comparison.evaluation),
    )


def _class_vocabulary(
    reference: TargetDiagnosticAnalysis,
    comparison: TargetDiagnosticAnalysis,
) -> Optional[VocabularyStatus]:
    if reference.task is None or not reference.task.is_classification:
        return None
    if comparison.task is None or not comparison.task.is_classification:
        return None
    reference_classes = _class_values(reference)
    comparison_classes = _class_values(comparison)
    if reference_classes is None or comparison_classes is None:
        return None
    if _same_levels(reference_classes, comparison_classes):
        return VocabularyStatus.SAME
    return VocabularyStatus.CHANGED


def _class_values(diagnostic: TargetDiagnosticAnalysis) -> Optional[Tuple[object, ...]]:
    population = diagnostic.population
    if population is None or not population.classes:
        return None
    return tuple(item.value for item in population.classes)


def _metric_changes(
    reference: object,
    comparison: object,
) -> Tuple[DiagnosticMetricChange, ...]:
    if isinstance(reference, ClassificationEvaluation) and isinstance(
        comparison, ClassificationEvaluation
    ):
        pairs = (
            (reference.roc_auc, comparison.roc_auc),
            (reference.balanced_accuracy, comparison.balanced_accuracy),
            (reference.log_loss, comparison.log_loss),
        )
    elif isinstance(reference, RegressionEvaluation) and isinstance(
        comparison, RegressionEvaluation
    ):
        pairs = (
            (reference.r2, comparison.r2),
            (reference.mae, comparison.mae),
            (reference.rmse, comparison.rmse),
        )
    else:
        raise ValueError("diagnostic evaluations do not share a task shape")
    return tuple(_metric_change(left, right) for left, right in pairs)


def _metric_change(
    reference: MetricComparison,
    comparison: MetricComparison,
) -> DiagnosticMetricChange:
    if reference.metric is not comparison.metric:
        raise ValueError("diagnostic metrics do not share an identity")
    return DiagnosticMetricChange(
        metric=reference.metric,
        reference_model=reference.model,
        comparison_model=comparison.model,
        model_change=_metric_difference(comparison.model, reference.model),
        reference_baseline=reference.baseline,
        comparison_baseline=comparison.baseline,
        baseline_change=_metric_difference(comparison.baseline, reference.baseline),
    )


def _metric_difference(
    comparison: Optional[float],
    reference: Optional[float],
) -> Optional[float]:
    if comparison is None or reference is None:
        return None
    return _finite_difference(comparison, reference)


def _leakage(
    reference: Optional[TargetLeakageAnalysis],
    comparison: Optional[TargetLeakageAnalysis],
    columns: Tuple[ColumnComparison, ...],
    target_position: int,
) -> LeakageEvidenceComparison:
    if reference is None or comparison is None:
        return LeakageEvidenceComparison(status=LeakageComparisonStatus.NOT_COLLECTED)
    if (
        reference.applicability is not LeakageApplicability.APPLICABLE
        or comparison.applicability is not LeakageApplicability.APPLICABLE
    ):
        return LeakageEvidenceComparison(status=LeakageComparisonStatus.NOT_APPLICABLE)
    reference_by = {item.position: item for item in reference.predictors}
    comparison_by = {item.position: item for item in comparison.predictors}
    transitions = []
    for column in columns:
        alignment = column.alignment
        if alignment.status is not ColumnMatchStatus.MATCHED:
            continue
        if alignment.reference_position == target_position:
            continue
        if (
            alignment.reference_position is None
            or alignment.comparison_position is None
            or alignment.occurrence is None
        ):
            raise ValueError("a matched predictor has a cross-dataset identity")
        reference_item = reference_by.get(alignment.reference_position)
        comparison_item = comparison_by.get(alignment.comparison_position)
        if reference_item is None or comparison_item is None:
            raise ValueError("a matched predictor is missing leakage evidence")
        transitions.append(
            PredictorLeakageTransition(
                reference_position=alignment.reference_position,
                comparison_position=alignment.comparison_position,
                occurrence=alignment.occurrence,
                reference_exact=reference_item.exact_duplicate.status,
                comparison_exact=comparison_item.exact_duplicate.status,
                reference_mapping=reference_item.deterministic_mapping.status,
                comparison_mapping=comparison_item.deterministic_mapping.status,
            )
        )
    return LeakageEvidenceComparison(
        status=LeakageComparisonStatus.COMPARED,
        transitions=tuple(transitions),
    )


def _column_by_reference(
    columns: Tuple[ColumnComparison, ...],
    position: int,
) -> Tuple[int, ColumnComparison]:
    for index, column in enumerate(columns):
        if column.alignment.reference_position == position:
            return index, column
    raise ValueError("target position is not in the comparison")


def _column_by_comparison(
    columns: Tuple[ColumnComparison, ...],
    position: int,
) -> Tuple[int, ColumnComparison]:
    for index, column in enumerate(columns):
        if column.alignment.comparison_position == position:
            return index, column
    raise ValueError("target position is not in the comparison")


def _require_requested_analysis(
    analysis: DatasetAnalysis, position: Optional[int]
) -> None:
    target = analysis.target_analysis
    if position is None:
        return
    if target is None:
        return
    if target.position != position:
        raise ValueError("target analysis does not match the requested target")
    if analysis.target_diagnostic is None or analysis.target_leakage is None:
        raise ValueError("a target analysis keeps its diagnostic and leakage results")
    if analysis.target_diagnostic.target_position != position:
        raise ValueError("diagnostic target position does not match the request")
    if analysis.target_leakage.target_position != position:
        raise ValueError("leakage target position does not match the request")


def require_target_links(
    target: TargetDriftAnalysis,
    columns: Tuple[ColumnComparison, ...],
    relationships: Tuple[RelationshipDrift, ...],
) -> None:
    """Check that target projections are the comparison's own records."""
    if target.alignment.status is not TargetAlignmentStatus.ALIGNED:
        return
    distribution = target.distribution
    if distribution is None or target.diagnostic is None or target.leakage is None:
        raise ValueError(
            "an aligned target projects distribution, diagnostics, and leakage"
        )
    column = columns[distribution.column_index]
    if column.distribution is not distribution.distribution:
        raise ValueError("target distribution must be the column's distribution record")
    if column.distribution_status is not distribution.distribution_status:
        raise ValueError("target distribution status must be the column status")
    if (
        column.alignment.reference_position != target.alignment.reference_position
        or column.alignment.comparison_position != target.alignment.comparison_position
    ):
        raise ValueError("target distribution must be the aligned target column")
    seen = set()
    for projection in target.relationships:
        if projection.drift_index in seen:
            raise ValueError("a target relationship is projected twice")
        seen.add(projection.drift_index)
        record = relationships[projection.drift_index]
        first = record.alignment.first.reference_position
        second = record.alignment.second.reference_position
        if target.alignment.reference_position not in (first, second):
            raise ValueError("a target relationship must include the target")
        target_is_first = target.alignment.reference_position == first
        other = second if target_is_first else first
        if projection.other_reference_position != other:
            raise ValueError("target relationship partner must be the other column")
        if projection.reference_role is not _role(record.reference, target_is_first):
            raise ValueError("reference target role must follow the relationship")
        if projection.comparison_role is not _role(record.comparison, target_is_first):
            raise ValueError("comparison target role must follow the relationship")
    if target.diagnostic.status is DiagnosticComparisonStatus.COMPARED:
        if target.diagnostic.reference_task is not target.diagnostic.comparison_task:
            raise ValueError("compared diagnostics share a predictive task")
    for transition in target.leakage.transitions:
        if not any(
            column.alignment.reference_position == transition.reference_position
            and column.alignment.comparison_position == transition.comparison_position
            for column in columns
        ):
            raise ValueError("a leakage transition must name an aligned column")
