"""Invariant rejects for relationship-drift and target-drift records."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from pytics.analysis.column_label import retain_column_label
from pytics.analysis.compare import DiagnosticComparisonStatus
from pytics.analysis.compare import DistributionDriftStatus
from pytics.analysis.compare import EffectChangeReason
from pytics.analysis.compare import LeakageComparisonStatus
from pytics.analysis.compare import PearsonChangeNull
from pytics.analysis.compare import PearsonChangeReason
from pytics.analysis.compare import RelationshipChangeMeasure
from pytics.analysis.compare import RelationshipPairStatus
from pytics.analysis.compare import TargetAlignmentStatus
from pytics.analysis.compare import TargetColumnRole
from pytics.analysis.compare import VocabularyStatus
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare import compare_dataset_analyses
from pytics.analysis.compare.relationship_models import CategoricalCategoricalState
from pytics.analysis.compare.relationship_models import ContingencyVocabulary
from pytics.analysis.compare.relationship_models import EffectChange
from pytics.analysis.compare.relationship_models import GroupingVocabulary
from pytics.analysis.compare.relationship_models import NumericNumericState
from pytics.analysis.compare.relationship_models import PEARSON_CHANGE_ASSUMPTIONS
from pytics.analysis.compare.relationship_models import PearsonCorrelationChangeTest
from pytics.analysis.compare.relationship_models import RelationshipColumnIdentity
from pytics.analysis.compare.relationship_models import RelationshipDriftCoverage
from pytics.analysis.compare.relationship_models import RelationshipPairAlignment
from pytics.analysis.compare.relationship_models import RelationshipSide
from pytics.analysis.compare.relationship_models import RelationshipSideKind
from pytics.analysis.compare.relationship_models import coverage_from_relationships
from pytics.analysis.compare.target_models import DiagnosticMetricChange
from pytics.analysis.compare.target_models import DiagnosticPredictabilityComparison
from pytics.analysis.compare.target_models import LeakageEvidenceComparison
from pytics.analysis.compare.target_models import PredictorLeakageTransition
from pytics.analysis.compare.target_models import TargetDriftAlignment
from pytics.analysis.compare.target_models import TargetDriftAnalysis
from pytics.analysis.compare.target_models import TargetDriftCoverage
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationships.models import RelationshipFamily
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import UnavailabilityReason
from pytics.analysis.relationships.models import UnimplementedRelationshipFamily
from pytics.analysis.target_diagnostic import DiagnosticMetric
from pytics.analysis.target_diagnostic import PredictiveTask
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import MappingStatus
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


def _signed_change(**overrides: object) -> EffectChange:
    values = {
        "measure": RelationshipChangeMeasure.SPEARMAN_RHO,
        "availability": ResultAvailability.AVAILABLE,
        "reference": 0.2,
        "comparison": 0.5,
        "change": 0.3,
        "magnitude_change": 0.3,
        "sign_reversal": False,
        "reason": None,
    }
    values.update(overrides)
    return EffectChange(**values)  # type: ignore[arg-type]


def _numeric_pair():
    reference = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [1, 2, 4, 3, 6]})
    comparison = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [1, 3, 2, 5, 4]})
    return compare_dataframes(reference, comparison).relationships[0]


def _categorical_pair():
    reference = pd.DataFrame(
        {"y": [1, 2, 8, 9], "g": pd.Series(["a", "a", "b", "b"], dtype="category")}
    )
    comparison = pd.DataFrame(
        {"y": [1, 1, 9, 9], "g": pd.Series(["a", "a", "b", "b"], dtype="category")}
    )
    return compare_dataframes(reference, comparison).relationships[0]


def test_effect_change_rejects_inconsistent_states() -> None:
    with pytest.raises(ValueError, match="no reason"):
        _signed_change(reason=EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE)
    with pytest.raises(ValueError, match="comparison minus reference"):
        _signed_change(change=0.0)
    with pytest.raises(ValueError, match="no difference"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            reference=None,
            comparison=None,
            change=0.0,
            magnitude_change=None,
            sign_reversal=None,
            reason=EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE,
        )
    with pytest.raises(ValueError, match="names why"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            reference=None,
            comparison=None,
            change=None,
            magnitude_change=None,
            sign_reversal=None,
            reason=None,
        )
    with pytest.raises(ValueError, match="neither effect"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            reference=0.2,
            comparison=None,
            change=None,
            magnitude_change=None,
            sign_reversal=None,
            reason=EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE,
        )
    with pytest.raises(ValueError, match="only the comparison"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            reference=0.2,
            comparison=None,
            change=None,
            magnitude_change=None,
            sign_reversal=None,
            reason=EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE,
        )
    with pytest.raises(ValueError, match="only the reference"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            reference=None,
            comparison=None,
            change=None,
            magnitude_change=None,
            sign_reversal=None,
            reason=EffectChangeReason.COMPARISON_EFFECT_UNAVAILABLE,
        )
    with pytest.raises(ValueError, match="not one effect series"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            measure=RelationshipChangeMeasure.PROBABILITY_DIFFERENCE,
            reference=0.1,
            comparison=None,
            change=None,
            magnitude_change=None,
            sign_reversal=None,
            reason=EffectChangeReason.ORIENTATION_NOT_SHARED,
        )
    with pytest.raises(ValueError, match="both effects"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            reference=None,
            comparison=0.5,
            change=None,
            magnitude_change=None,
            sign_reversal=None,
            reason=EffectChangeReason.NON_FINITE_DIFFERENCE,
        )
    with pytest.raises(ValueError, match="absolute-value"):
        _signed_change(magnitude_change=1.0)
    with pytest.raises(ValueError, match="no magnitude"):
        EffectChange(
            measure=RelationshipChangeMeasure.ETA_SQUARED,
            availability=ResultAvailability.AVAILABLE,
            reference=0.2,
            comparison=0.5,
            change=0.3,
            magnitude_change=0.3,
            sign_reversal=None,
            reason=None,
        )
    with pytest.raises(ValueError, match="both signed effects"):
        _signed_change(
            availability=ResultAvailability.UNAVAILABLE,
            reference=0.2,
            comparison=None,
            change=None,
            magnitude_change=0.2,
            sign_reversal=None,
            reason=EffectChangeReason.COMPARISON_EFFECT_UNAVAILABLE,
        )


def test_relationship_record_rejects_a_mismatched_family_payload() -> None:
    record = _numeric_pair()
    with pytest.raises(ValueError, match="family's effect"):
        forged_primary = EffectChange(
            measure=RelationshipChangeMeasure.ETA_SQUARED,
            availability=ResultAvailability.AVAILABLE,
            reference=0.2,
            comparison=0.5,
            change=0.3,
            magnitude_change=None,
            sign_reversal=None,
            reason=None,
        )
        replace(record, primary=forged_primary)
    with pytest.raises(ValueError, match="pair status"):
        replace(record, status=RelationshipPairStatus.FAMILY_TRANSITION)
    with pytest.raises(ValueError, match="group vocabulary belongs"):
        replace(
            record,
            grouping_vocabulary=GroupingVocabulary(
                status=VocabularyStatus.SAME,
                reference_n_levels=1,
                comparison_n_levels=1,
            ),
        )
    with pytest.raises(ValueError, match="Pearson change test"):
        replace(record, pearson_change_test=None)
    copied = record.complementary[0]
    forged = replace(
        copied,
        reference=0.0,
        comparison=0.0,
        change=0.0,
        magnitude_change=0.0,
        sign_reversal=False,
    )
    with pytest.raises(ValueError, match="Pearson change must copy"):
        replace(record, complementary=(forged,))

    categorical = _categorical_pair()
    with pytest.raises(ValueError, match="belongs to a numeric pair"):
        replace(categorical, pearson_change_test=record.pearson_change_test)
    with pytest.raises(ValueError, match="no complementary"):
        replace(categorical, complementary=record.complementary)


def test_unshared_orientation_cannot_store_one_probability_series() -> None:
    reference = pd.DataFrame(
        {"a": [True, True, False, False], "b": [True, False, True, False]}
    )
    comparison = pd.DataFrame(
        {"b": [True, False, True, False], "a": [True, True, False, False]}
    )
    record = compare_dataframes(reference, comparison).relationships[0]
    assert record.complementary[0].reason is EffectChangeReason.ORIENTATION_NOT_SHARED
    forged = replace(
        record.complementary[0],
        availability=ResultAvailability.AVAILABLE,
        reference=0.0,
        comparison=0.25,
        change=0.25,
        magnitude_change=0.25,
        sign_reversal=False,
        reason=None,
    )
    with pytest.raises(ValueError, match="flipped conditioning"):
        replace(record, complementary=(forged,))


def test_component_vocabulary_and_pearson_test_invariants() -> None:
    with pytest.raises(ValueError, match="no unavailability reason"):
        NumericNumericState(
            n_paired=5,
            spearman=0.2,
            spearman_reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
            pearson=0.2,
            pearson_reason=None,
        )
    with pytest.raises(ValueError, match="same level count"):
        GroupingVocabulary(
            status=VocabularyStatus.SAME,
            reference_n_levels=1,
            comparison_n_levels=2,
        )
    with pytest.raises(ValueError, match="empty category sets"):
        GroupingVocabulary(
            status=VocabularyStatus.CHANGED,
            reference_n_levels=0,
            comparison_n_levels=0,
        )
    same = GroupingVocabulary(
        status=VocabularyStatus.SAME,
        reference_n_levels=1,
        comparison_n_levels=1,
    )
    with pytest.raises(ValueError, match="reference shape"):
        ContingencyVocabulary(
            first=same,
            second=same,
            reference_shape=(2, 1),
            comparison_shape=(1, 1),
            status=VocabularyStatus.SAME,
        )
    side = RelationshipSide(kind=RelationshipSideKind.INELIGIBLE)
    assert side.payload() is None
    with pytest.raises(ValueError, match="own family payload"):
        RelationshipSide(
            kind=RelationshipSideKind.CALCULATED,
            family=RelationshipFamily.NUMERIC_NUMERIC,
        )
    with pytest.raises(ValueError, match="p_value must lie"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=0.0,
            p_value=1.5,
            null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
            assumptions=PEARSON_CHANGE_ASSUMPTIONS,
            reason=None,
        )
    with pytest.raises(ValueError, match="no result"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.UNAVAILABLE,
            statistic=0.0,
            p_value=None,
            null=None,
            assumptions=(),
            reason=PearsonChangeReason.BOUNDARY_CORRELATION,
        )


def test_relationship_coverage_must_reconcile() -> None:
    with pytest.raises(ValueError, match="sum to aligned pairs"):
        RelationshipDriftCoverage(
            n_aligned_pairs=2,
            n_same_family=1,
            n_family_transition=0,
            n_unimplemented=0,
            n_eligibility_transition=0,
            n_effect_change_available=1,
            n_effect_change_unavailable=0,
            n_formal_change_tests=1,
            n_formal_change_tests_unavailable=0,
            n_numeric_numeric=1,
            n_numeric_categorical=0,
            n_numeric_boolean=0,
            n_boolean_boolean=0,
            n_categorical_categorical=0,
        )


def test_non_finite_mean_difference_is_not_stored_as_a_number() -> None:
    huge = 1e308
    reference = pd.DataFrame(
        {
            "flag": [False, False, False, True, True, True],
            "amount": [0.0, 0.0, 0.0, huge, huge, huge],
        }
    )
    comparison = pd.DataFrame(
        {
            "flag": [False, False, False, True, True, True],
            "amount": [0.0, 0.0, 0.0, -huge, -huge, -huge],
        }
    )
    record = compare_dataframes(reference, comparison).relationships[0]
    change = record.complementary[0]
    assert change.reason is EffectChangeReason.NON_FINITE_DIFFERENCE
    assert change.reference == pytest.approx(huge)
    assert change.comparison == pytest.approx(-huge)
    assert change.change is None
    assert change.sign_reversal is True
    assert record.primary is not None
    assert record.primary.reason is EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE


def test_numeric_target_keeps_the_numeric_role_of_a_categorical_pair() -> None:
    reference = pd.DataFrame(
        {
            "y": [1, 2, 8, 9],
            "g": pd.Series(["a", "a", "b", "b"], dtype="category"),
        }
    )
    comparison = pd.DataFrame(
        {
            "g": pd.Series(["a", "a", "b", "b"], dtype="category"),
            "y": [1, 1, 9, 9],
        }
    )
    result = compare_dataframes(reference, comparison, target="y")
    assert result.target is not None
    assert result.target.relationships[0].reference_role is TargetColumnRole.NUMERIC
    assert result.target.relationships[0].comparison_role is TargetColumnRole.NUMERIC


def test_requested_target_position_must_match_the_analysis() -> None:
    frame = pd.DataFrame({"a": [1, 2, 3, 4, 5, 6], "y": [1, 2, 4, 3, 6, 5]})
    analysis = analyze_dataframe(frame, target="y")
    with pytest.raises(ValueError, match="does not match"):
        compare_dataset_analyses(
            analysis,
            analysis,
            target_reference_position=0,
            target_comparison_position=0,
            target_requested=True,
        )


def test_reference_only_predictor_is_not_a_leakage_transition() -> None:
    reference = pd.DataFrame(
        {"y": list(range(24)), "x": list(range(24)), "extra": list(range(24))}
    )
    comparison = pd.DataFrame({"y": list(range(24)), "x": list(reversed(range(24)))})
    result = compare_dataframes(reference, comparison, target="y")
    assert result.target is not None and result.target.leakage is not None
    positions = {item.reference_position for item in result.target.leakage.transitions}
    assert positions == {1}


def _aligned_target() -> TargetDriftAlignment:
    label = retain_column_label("y")
    return TargetDriftAlignment(
        status=TargetAlignmentStatus.ALIGNED,
        reference_position=0,
        comparison_position=1,
        occurrence=1,
        reference_label=label,
        comparison_label=label,
        reference_selected_type=SemanticType.NUMERIC,
        comparison_selected_type=SemanticType.NUMERIC,
        reference_resolution=ResolutionStatus.RESOLVED,
        comparison_resolution=ResolutionStatus.RESOLVED,
        selected_type_changed=False,
        resolution_changed=False,
    )


def test_target_alignment_and_diagnostic_records_reject_inconsistent_states() -> None:
    with pytest.raises(ValueError, match="positive int or None"):
        replace(_aligned_target(), occurrence=0)
    with pytest.raises(ValueError, match="follow the two types"):
        replace(
            _aligned_target(),
            comparison_selected_type=SemanticType.CATEGORICAL,
        )
    label = retain_column_label("y")
    with pytest.raises(ValueError, match="no selected type"):
        TargetDriftAlignment(
            status=TargetAlignmentStatus.REFERENCE_ONLY,
            reference_position=0,
            reference_label=label,
            reference_resolution=ResolutionStatus.INSUFFICIENT_EVIDENCE,
            reference_selected_type=SemanticType.NUMERIC,
        )
    with pytest.raises(ValueError, match="has a selected type"):
        TargetDriftAlignment(
            status=TargetAlignmentStatus.REFERENCE_ONLY,
            reference_position=0,
            reference_label=label,
            reference_resolution=ResolutionStatus.RESOLVED,
            reference_selected_type=None,
        )
    with pytest.raises(ValueError, match="no column"):
        TargetDriftAlignment(
            status=TargetAlignmentStatus.NOT_IN_EITHER,
            reference_position=0,
        )
    metric = DiagnosticMetricChange(
        metric=DiagnosticMetric.R2,
        reference_model=0.2,
        comparison_model=0.5,
        model_change=0.3,
        reference_baseline=0.0,
        comparison_baseline=0.0,
        baseline_change=0.0,
    )
    with pytest.raises(ValueError, match="comparison minus reference"):
        replace(metric, model_change=1.0)
    with pytest.raises(ValueError, match="share a predictive task"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.COMPARED,
            reference_task=PredictiveTask.REGRESSION,
            comparison_task=PredictiveTask.BINARY_CLASSIFICATION,
            metrics=(metric,),
        )
    with pytest.raises(ValueError, match="only a compared diagnostic"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.TASK_TRANSITION,
            reference_task=PredictiveTask.REGRESSION,
            comparison_task=PredictiveTask.BINARY_CLASSIFICATION,
            metrics=(metric,),
        )
    with pytest.raises(ValueError, match="records that change"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED,
            reference_task=PredictiveTask.BINARY_CLASSIFICATION,
            comparison_task=PredictiveTask.BINARY_CLASSIFICATION,
            class_vocabulary=VocabularyStatus.SAME,
        )
    with pytest.raises(ValueError, match="two different tasks"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.TASK_TRANSITION,
            reference_task=PredictiveTask.REGRESSION,
            comparison_task=PredictiveTask.REGRESSION,
        )
    with pytest.raises(ValueError, match="no class vocabulary"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.COMPARED,
            reference_task=PredictiveTask.REGRESSION,
            comparison_task=PredictiveTask.REGRESSION,
            class_vocabulary=VocabularyStatus.SAME,
            metrics=(metric,),
        )
    transition = PredictorLeakageTransition(
        reference_position=1,
        comparison_position=0,
        occurrence=1,
        reference_exact=ExactDuplicateStatus.NOT_EQUAL,
        comparison_exact=ExactDuplicateStatus.EXACT_DUPLICATE,
        reference_mapping=MappingStatus.NOT_APPLICABLE,
        comparison_mapping=MappingStatus.NOT_APPLICABLE,
    )
    with pytest.raises(ValueError, match="only a compared leakage"):
        LeakageEvidenceComparison(
            status=LeakageComparisonStatus.NOT_APPLICABLE,
            transitions=(transition,),
        )
    with pytest.raises(ValueError, match="exactly when metrics"):
        TargetDriftCoverage(
            distribution_projected=False,
            n_relationship_projections=0,
            diagnostic_compared=True,
            n_diagnostic_metrics=0,
            n_leakage_transitions=0,
            n_exact_status_changes=0,
            n_mapping_status_changes=0,
        )


def test_target_projection_links_must_name_the_aligned_target() -> None:
    wide_reference = pd.DataFrame(
        {
            "y": [1, 2, 3, 4, 5, 6],
            "x": [1, 2, 4, 3, 6, 8],
            "z": [1, 1, 1, 2, 2, 2],
        }
    )
    wide_comparison = pd.DataFrame(
        {
            "z": [1, 1, 1, 2, 2, 2],
            "x": [1, 3, 5, 2, 4, 7],
            "y": [1, 1, 2, 2, 9, 9],
        }
    )
    wide = compare_dataframes(wide_reference, wide_comparison, target="y")
    assert wide.target is not None
    target = wide.target
    distribution = target.distribution
    assert distribution is not None
    other_index = 1 if distribution.column_index == 0 else 0
    with pytest.raises(ValueError, match="distribution record"):
        replace(
            wide,
            target=replace(
                target,
                distribution=replace(distribution, column_index=other_index),
            ),
        )
    projection = target.relationships[0]
    wrong_role = (
        TargetColumnRole.OUTCOME
        if projection.reference_role is not TargetColumnRole.OUTCOME
        else TargetColumnRole.CONDITIONING
    )
    with pytest.raises(ValueError, match="reference target role"):
        replace(
            wide,
            target=replace(
                target,
                relationships=(replace(projection, reference_role=wrong_role),)
                + target.relationships[1:],
            ),
        )
    foreign = next(
        index
        for index, record in enumerate(wide.relationships)
        if target.alignment.reference_position
        not in (
            record.alignment.first.reference_position,
            record.alignment.second.reference_position,
        )
    )
    stolen = replace(projection, drift_index=foreign)
    ordered = tuple(
        sorted(
            (stolen,) + target.relationships[1:],
            key=lambda item: item.drift_index,
        )
    )
    with pytest.raises(ValueError, match="include the target"):
        replace(wide, target=replace(target, relationships=ordered))


def _label(name: str):
    return retain_column_label(name)


def _column(reference: int, comparison: int, occurrence: int = 1):
    return RelationshipColumnIdentity(
        occurrence=occurrence,
        reference_position=reference,
        comparison_position=comparison,
        reference_label=_label("a"),
        comparison_label=_label("b"),
    )


def test_pair_identity_and_side_shape_are_rejected_when_inconsistent() -> None:
    with pytest.raises(ValueError, match="positive int"):
        _column(0, 1, occurrence=0)
    with pytest.raises(ValueError, match="ascending reference"):
        RelationshipPairAlignment(first=_column(2, 0), second=_column(1, 1))
    with pytest.raises(ValueError, match="two distinct columns"):
        RelationshipPairAlignment(first=_column(0, 1), second=_column(1, 1))
    with pytest.raises(ValueError, match="positive cells"):
        CategoricalCategoricalState(
            n_paired=1,
            first_levels=("a",),
            second_levels=("b",),
            n_positive_cells=2,
            cramers_v=0.0,
            cramers_v_reason=None,
        )
    with pytest.raises(ValueError, match="implemented family"):
        RelationshipSide(
            kind=RelationshipSideKind.CALCULATED,
            unimplemented_family=UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN,
        )
    state = NumericNumericState(
        n_paired=4,
        spearman=0.0,
        spearman_reason=None,
        pearson=0.0,
        pearson_reason=None,
    )
    with pytest.raises(ValueError, match="only a calculated side"):
        RelationshipSide(
            kind=RelationshipSideKind.INELIGIBLE,
            numeric_numeric=state,
        )
    with pytest.raises(ValueError, match="recognized family"):
        RelationshipSide(kind=RelationshipSideKind.UNIMPLEMENTED)
    with pytest.raises(ValueError, match="names no relationship family"):
        RelationshipSide(
            kind=RelationshipSideKind.INELIGIBLE,
            family=RelationshipFamily.NUMERIC_NUMERIC,
        )
    alignment = RelationshipPairAlignment(first=_column(0, 1), second=_column(1, 0))
    empty = RelationshipSide(kind=RelationshipSideKind.INELIGIBLE)
    with pytest.raises(ValueError, match="two ineligible"):
        from pytics.analysis.compare.relationship_models import RelationshipDrift

        RelationshipDrift(
            alignment=alignment,
            status=RelationshipPairStatus.ELIGIBILITY_TRANSITION,
            reference=empty,
            comparison=empty,
        )
    record = _numeric_pair()
    with pytest.raises(TypeError, match="complementary must be a tuple"):
        replace(record, complementary=[])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="only a same-family"):
        replace(
            record,
            status=RelationshipPairStatus.FAMILY_TRANSITION,
            reference=RelationshipSide(
                kind=RelationshipSideKind.UNIMPLEMENTED,
                unimplemented_family=UnimplementedRelationshipFamily.DATETIME_NUMERIC,
            ),
            comparison=record.comparison,
            complementary=(),
            pearson_change_test=None,
        )
    categorical = _categorical_pair()
    with pytest.raises(ValueError, match="records group vocabulary"):
        replace(categorical, grouping_vocabulary=None)
    with pytest.raises(ValueError, match="effect changes must account"):
        RelationshipDriftCoverage(
            n_aligned_pairs=1,
            n_same_family=1,
            n_family_transition=0,
            n_unimplemented=0,
            n_eligibility_transition=0,
            n_effect_change_available=0,
            n_effect_change_unavailable=0,
            n_formal_change_tests=1,
            n_formal_change_tests_unavailable=0,
            n_numeric_numeric=1,
            n_numeric_categorical=0,
            n_numeric_boolean=0,
            n_boolean_boolean=0,
            n_categorical_categorical=0,
        )
    with pytest.raises(ValueError, match="sum to same-family"):
        RelationshipDriftCoverage(
            n_aligned_pairs=1,
            n_same_family=1,
            n_family_transition=0,
            n_unimplemented=0,
            n_eligibility_transition=0,
            n_effect_change_available=1,
            n_effect_change_unavailable=0,
            n_formal_change_tests=0,
            n_formal_change_tests_unavailable=0,
            n_numeric_numeric=0,
            n_numeric_categorical=0,
            n_numeric_boolean=0,
            n_boolean_boolean=0,
            n_categorical_categorical=0,
        )
    with pytest.raises(ValueError, match="account for numeric"):
        RelationshipDriftCoverage(
            n_aligned_pairs=1,
            n_same_family=1,
            n_family_transition=0,
            n_unimplemented=0,
            n_eligibility_transition=0,
            n_effect_change_available=1,
            n_effect_change_unavailable=0,
            n_formal_change_tests=0,
            n_formal_change_tests_unavailable=0,
            n_numeric_numeric=1,
            n_numeric_categorical=0,
            n_numeric_boolean=0,
            n_boolean_boolean=0,
            n_categorical_categorical=0,
        )
    with pytest.raises(TypeError, match="must be a tuple"):
        coverage_from_relationships([])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite float"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=float("nan"),
            p_value=0.5,
            null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
            assumptions=PEARSON_CHANGE_ASSUMPTIONS,
            reason=None,
        )
    with pytest.raises(ValueError, match="negative zero"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=-0.0,
            p_value=1.0,
            null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
            assumptions=PEARSON_CHANGE_ASSUMPTIONS,
            reason=None,
        )
    with pytest.raises(ValueError, match="names its assumptions"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=0.0,
            p_value=1.0,
            null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
            assumptions=(),
            reason=None,
        )


def test_target_record_shape_rejects_incomplete_payloads() -> None:
    frame = pd.DataFrame({"y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], "x": [1, 2, 4, 3, 6, 8]})
    result = compare_dataframes(frame, frame.copy(), target="y")
    assert result.target is not None
    target = result.target
    with pytest.raises(ValueError, match="no projected change"):
        replace(
            target,
            alignment=TargetDriftAlignment(status=TargetAlignmentStatus.NOT_IN_EITHER),
        )
    with pytest.raises(ValueError, match="projects distribution"):
        replace(target, diagnostic=None)
    wrong_coverage = replace(target.coverage, n_relationship_projections=99)
    with pytest.raises(ValueError, match="does not match the target record"):
        replace(target, coverage=wrong_coverage)
    if len(target.relationships) >= 2:
        with pytest.raises(ValueError, match="drift index"):
            replace(
                target,
                relationships=(target.relationships[1], target.relationships[0]),
            )
    with pytest.raises(TypeError, match="distribution-drift record"):
        replace(target.distribution, distribution=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="has its metrics"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.COMPARED,
            reference_task=PredictiveTask.REGRESSION,
            comparison_task=PredictiveTask.REGRESSION,
            metrics=(),
        )
    roc = DiagnosticMetricChange(
        metric=DiagnosticMetric.ROC_AUC,
        reference_model=0.25,
        comparison_model=0.75,
        model_change=0.5,
        reference_baseline=0.5,
        comparison_baseline=0.5,
        baseline_change=0.0,
    )
    with pytest.raises(ValueError, match="shares a class set"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.COMPARED,
            reference_task=PredictiveTask.BINARY_CLASSIFICATION,
            comparison_task=PredictiveTask.BINARY_CLASSIFICATION,
            class_vocabulary=None,
            metrics=(roc,),
        )
    with pytest.raises(ValueError, match="within one task"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED,
            reference_task=PredictiveTask.BINARY_CLASSIFICATION,
            comparison_task=PredictiveTask.MULTICLASS_CLASSIFICATION,
            class_vocabulary=VocabularyStatus.CHANGED,
        )
    with pytest.raises(ValueError, match="belongs to classification"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED,
            reference_task=PredictiveTask.REGRESSION,
            comparison_task=PredictiveTask.REGRESSION,
            class_vocabulary=VocabularyStatus.CHANGED,
        )
    with pytest.raises(ValueError, match="positive int"):
        PredictorLeakageTransition(
            reference_position=1,
            comparison_position=0,
            occurrence=0,
            reference_exact=ExactDuplicateStatus.NOT_EQUAL,
            comparison_exact=ExactDuplicateStatus.NOT_EQUAL,
            reference_mapping=MappingStatus.NOT_APPLICABLE,
            comparison_mapping=MappingStatus.NOT_APPLICABLE,
        )
    with pytest.raises(ValueError, match="both metric values"):
        DiagnosticMetricChange(
            metric=DiagnosticMetric.R2,
            reference_model=None,
            comparison_model=0.2,
            model_change=0.2,
            reference_baseline=None,
            comparison_baseline=None,
            baseline_change=None,
        )
    label = retain_column_label("y")
    with pytest.raises(ValueError, match="only a reference position"):
        TargetDriftAlignment(
            status=TargetAlignmentStatus.REFERENCE_ONLY,
            comparison_position=0,
            comparison_label=label,
            comparison_resolution=ResolutionStatus.RESOLVED,
            comparison_selected_type=SemanticType.NUMERIC,
        )
    with pytest.raises(ValueError, match="has an occurrence"):
        TargetDriftAlignment(
            status=TargetAlignmentStatus.ALIGNED,
            reference_position=0,
            comparison_position=0,
            reference_label=label,
            comparison_label=label,
            reference_resolution=ResolutionStatus.RESOLVED,
            comparison_resolution=ResolutionStatus.RESOLVED,
            reference_selected_type=SemanticType.NUMERIC,
            comparison_selected_type=SemanticType.NUMERIC,
            selected_type_changed=False,
            resolution_changed=False,
        )
    with pytest.raises(ValueError, match="cannot exceed"):
        TargetDriftCoverage(
            distribution_projected=False,
            n_relationship_projections=0,
            diagnostic_compared=False,
            n_diagnostic_metrics=0,
            n_leakage_transitions=0,
            n_exact_status_changes=1,
            n_mapping_status_changes=0,
        )


def test_remaining_record_contracts_reject_inconsistent_metadata() -> None:
    with pytest.raises(TypeError, match="assumptions must be a tuple"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=0.0,
            p_value=1.0,
            null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
            assumptions=None,  # type: ignore[arg-type]
            reason=None,
        )
    with pytest.raises(ValueError, match="null is equality"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=0.0,
            p_value=1.0,
            null=None,
            assumptions=PEARSON_CHANGE_ASSUMPTIONS,
            reason=None,
        )
    with pytest.raises(ValueError, match="no reason"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=0.0,
            p_value=1.0,
            null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
            assumptions=PEARSON_CHANGE_ASSUMPTIONS,
            reason=PearsonChangeReason.BOUNDARY_CORRELATION,
        )
    with pytest.raises(ValueError, match="finite float"):
        PearsonCorrelationChangeTest(
            availability=ResultAvailability.AVAILABLE,
            statistic=0.0,
            p_value=float("nan"),
            null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
            assumptions=PEARSON_CHANGE_ASSUMPTIONS,
            reason=None,
        )
    same = GroupingVocabulary(
        status=VocabularyStatus.SAME,
        reference_n_levels=2,
        comparison_n_levels=2,
    )
    with pytest.raises(ValueError, match="comparison shape"):
        ContingencyVocabulary(
            first=same,
            second=same,
            reference_shape=(2, 2),
            comparison_shape=(2, 1),
            status=VocabularyStatus.SAME,
        )
    with pytest.raises(ValueError, match="follows the two axes"):
        ContingencyVocabulary(
            first=same,
            second=same,
            reference_shape=(2, 2),
            comparison_shape=(2, 2),
            status=VocabularyStatus.CHANGED,
        )
    first = PredictorLeakageTransition(
        reference_position=2,
        comparison_position=0,
        occurrence=1,
        reference_exact=ExactDuplicateStatus.NOT_EQUAL,
        comparison_exact=ExactDuplicateStatus.NOT_EQUAL,
        reference_mapping=MappingStatus.NOT_APPLICABLE,
        comparison_mapping=MappingStatus.NOT_APPLICABLE,
    )
    second = replace(first, reference_position=1, comparison_position=2)
    with pytest.raises(ValueError, match="reference position"):
        LeakageEvidenceComparison(
            status=LeakageComparisonStatus.COMPARED,
            transitions=(first, second),
        )
    with pytest.raises(TypeError, match="metrics must be a tuple"):
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.EVALUATION_UNAVAILABLE,
            metrics=[],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="cannot exceed"):
        TargetDriftCoverage(
            distribution_projected=False,
            n_relationship_projections=0,
            diagnostic_compared=False,
            n_diagnostic_metrics=0,
            n_leakage_transitions=1,
            n_exact_status_changes=0,
            n_mapping_status_changes=2,
        )
    label = retain_column_label("y")
    with pytest.raises(ValueError, match="only an aligned target has an occurrence"):
        TargetDriftAlignment(
            status=TargetAlignmentStatus.REFERENCE_ONLY,
            reference_position=0,
            occurrence=1,
            reference_label=label,
            reference_resolution=ResolutionStatus.RESOLVED,
            reference_selected_type=SemanticType.NUMERIC,
        )
    with pytest.raises(ValueError, match="resolution change must follow"):
        replace(_aligned_target(), resolution_changed=True)
