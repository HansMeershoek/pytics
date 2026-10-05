"""Target drift projects existing evidence. It does not refit or rescore."""

from __future__ import annotations

import dataclasses

import pandas as pd
import pytest

from pytics.analysis.compare import DiagnosticComparisonStatus
from pytics.analysis.compare import DistributionDriftStatus
from pytics.analysis.compare import LeakageComparisonStatus
from pytics.analysis.compare import TargetAlignmentStatus
from pytics.analysis.compare import TargetColumnRole
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare import compare_dataset_analyses
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.target import TargetPosition
from pytics.analysis.target_diagnostic import DiagnosticMetric
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import MappingStatus


def _regression(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"x": list(range(len(values))), "y": values})


def test_omitting_a_target_does_not_infer_one() -> None:
    frame = pd.DataFrame({"y": [1, 2, 3, 4], "x": [1, 2, 3, 5]})
    result = compare_dataframes(frame, frame.copy())
    assert result.target is None


def test_target_configuration_preserves_non_target_truth() -> None:
    reference = pd.DataFrame(
        {
            "y": [1, 2, 3, 4, 5, 6],
            "x": [1, 2, 4, 3, 6, 5],
            "flag": [True, False, True, False, True, False],
        }
    )
    comparison = pd.DataFrame(
        {
            "flag": [False, True, False, True, False, True],
            "x": [1, 3, 5, 2, 4, 6],
            "y": [6, 5, 4, 3, 2, 1],
        }
    )
    plain = compare_dataframes(reference, comparison)
    targeted = compare_dataframes(reference, comparison, target="y")
    assert plain.columns == targeted.columns
    assert plain.relationships == targeted.relationships
    assert plain.overview == targeted.overview
    assert plain.coverage == targeted.coverage
    assert plain.relationship_coverage == targeted.relationship_coverage
    assert plain.target is None
    assert targeted.target is not None
    assert targeted.target.alignment.status is TargetAlignmentStatus.ALIGNED
    assert targeted.target.alignment.reference_position == 0
    assert targeted.target.alignment.comparison_position == 2
    assert targeted.target.alignment.selected_type_changed is False


def test_distribution_and_relationships_are_projections() -> None:
    reference = pd.DataFrame(
        {
            "y": [1, 2, 3, 4, 5, 6],
            "x": [1, 2, 3, 4, 5, 8],
            "flag": [True, False, True, False, True, False],
        }
    )
    comparison = pd.DataFrame(
        {
            "flag": [True, True, False, False, True, False],
            "y": [1, 1, 2, 2, 9, 9],
            "x": [2, 3, 4, 5, 6, 7],
        }
    )
    result = compare_dataframes(reference, comparison, target="y")
    target = result.target
    assert target is not None
    distribution = target.distribution
    assert distribution is not None
    column = result.columns[distribution.column_index]
    assert distribution.distribution is column.distribution
    assert distribution.distribution_status is DistributionDriftStatus.NUMERIC
    assert target.coverage.distribution_projected is True
    roles = {item.reference_role for item in target.relationships}
    assert TargetColumnRole.SYMMETRIC in roles
    assert TargetColumnRole.NUMERIC in roles
    for projection in target.relationships:
        record = result.relationships[projection.drift_index]
        positions = (
            record.alignment.first.reference_position,
            record.alignment.second.reference_position,
        )
        assert target.alignment.reference_position in positions
        assert projection.reference_role in (
            TargetColumnRole.SYMMETRIC,
            TargetColumnRole.NUMERIC,
        )


def test_target_edges_are_explicit() -> None:
    reference = pd.DataFrame({"a": [1, 2, 3, 4], "y": [1, 2, 3, 4]})
    comparison = pd.DataFrame({"y": [1, 2, 3, 9], "a": [4, 3, 2, 1]})
    mismatch = compare_dataframes(reference, comparison, target=TargetPosition(0))
    assert mismatch.target is not None
    assert mismatch.target.alignment.status is TargetAlignmentStatus.IDENTITY_MISMATCH
    assert mismatch.target.distribution is None
    assert mismatch.target.relationships == ()
    assert mismatch.target.diagnostic is None

    missing = compare_dataframes(reference, comparison, target="missing")
    assert missing.target is not None
    assert missing.target.alignment.status is TargetAlignmentStatus.NOT_IN_EITHER

    reference_only = compare_dataframes(
        reference,
        pd.DataFrame({"a": [1, 2, 3, 4]}),
        target="y",
    )
    assert reference_only.target is not None
    assert (
        reference_only.target.alignment.status is TargetAlignmentStatus.REFERENCE_ONLY
    )
    assert reference_only.target.alignment.reference_position == 1
    assert reference_only.target.distribution is None

    dated = compare_dataframes(
        pd.DataFrame(
            {"when": pd.date_range("2020-01-01", periods=4), "x": [1, 2, 3, 4]}
        ),
        pd.DataFrame(
            {"x": [1, 2, 3, 9], "when": pd.date_range("2021-01-01", periods=4)}
        ),
        target="when",
    )
    assert dated.target is not None
    assert dated.target.alignment.status is TargetAlignmentStatus.ALIGNED
    assert dated.target.distribution is not None
    assert dated.target.distribution.distribution_status is (
        DistributionDriftStatus.NOT_ELIGIBLE
    )
    assert dated.target.coverage.distribution_projected is False
    assert dated.target.diagnostic is not None
    assert dated.target.diagnostic.status is (
        DiagnosticComparisonStatus.EVALUATION_UNAVAILABLE
    )
    assert dated.target.leakage is not None
    assert dated.target.leakage.status is LeakageComparisonStatus.NOT_APPLICABLE


def test_diagnostic_metric_change_is_descriptive_and_task_bound() -> None:
    reference = _regression([float(value * 2) for value in range(40)])
    comparison = _regression([float(value % 2) for value in range(40)])
    result = compare_dataframes(reference, comparison, target="y")
    target = result.target
    assert target is not None and target.diagnostic is not None
    diagnostic = target.diagnostic
    assert diagnostic.status is DiagnosticComparisonStatus.COMPARED
    assert diagnostic.reference_task is diagnostic.comparison_task
    metrics = {item.metric: item for item in diagnostic.metrics}
    assert set(metrics) == {
        DiagnosticMetric.R2,
        DiagnosticMetric.MAE,
        DiagnosticMetric.RMSE,
    }
    source_reference = analyze_dataframe(reference, target="y").target_diagnostic
    source_comparison = analyze_dataframe(comparison, target="y").target_diagnostic
    assert source_reference is not None and source_comparison is not None
    assert source_reference.evaluation is not None
    assert source_comparison.evaluation is not None
    assert metrics[DiagnosticMetric.R2].reference_model == (
        source_reference.evaluation.r2.model
    )
    assert metrics[DiagnosticMetric.R2].comparison_model == (
        source_comparison.evaluation.r2.model
    )
    assert metrics[DiagnosticMetric.R2].model_change == pytest.approx(
        source_comparison.evaluation.r2.model - source_reference.evaluation.r2.model
    )
    assert metrics[DiagnosticMetric.MAE].model_change == pytest.approx(
        source_comparison.evaluation.mae.model - source_reference.evaluation.mae.model
    )
    assert not hasattr(metrics[DiagnosticMetric.R2], "p_value")
    names = {field.name for field in dataclasses.fields(diagnostic)}
    assert "importance" not in names
    assert "score" not in names

    transition = compare_dataframes(
        reference,
        pd.DataFrame(
            {
                "x": list(range(40)),
                "y": pd.Series(["a", "b"] * 20, dtype="category"),
            }
        ),
        target="y",
    )
    assert transition.target is not None and transition.target.diagnostic is not None
    assert transition.target.alignment.selected_type_changed is True
    assert transition.target.diagnostic.status is (
        DiagnosticComparisonStatus.TASK_TRANSITION
    )
    assert transition.target.diagnostic.metrics == ()

    reference_labels = ["a"] * 8 + ["b"] * 8 + ["c"] * 8
    comparison_labels = ["a"] * 8 + ["b"] * 8 + ["d"] * 8
    multiclass = compare_dataframes(
        pd.DataFrame(
            {
                "x": list(range(24)),
                "y": pd.Series(reference_labels, dtype="category"),
            }
        ),
        pd.DataFrame(
            {
                "x": list(range(24)),
                "y": pd.Series(comparison_labels, dtype="category"),
            }
        ),
        target="y",
    )
    assert multiclass.target is not None and multiclass.target.diagnostic is not None
    assert multiclass.target.diagnostic.status is (
        DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED
    )
    assert multiclass.target.diagnostic.metrics == ()


def test_leakage_transition_is_mechanical() -> None:
    reference = pd.DataFrame({"y": list(range(24)), "x": list(range(24))})
    comparison = pd.DataFrame({"y": list(range(24)), "x": list(reversed(range(24)))})
    result = compare_dataframes(reference, comparison, target="y")
    assert result.target is not None and result.target.leakage is not None
    leakage = result.target.leakage
    assert leakage.status is LeakageComparisonStatus.COMPARED
    assert len(leakage.transitions) == 1
    transition = leakage.transitions[0]
    assert transition.reference_exact is ExactDuplicateStatus.EXACT_DUPLICATE
    assert transition.comparison_exact is ExactDuplicateStatus.NOT_EQUAL
    assert transition.exact_status_changed is True
    assert transition.reference_mapping is MappingStatus.NOT_APPLICABLE
    assert transition.mapping_status_changed is False

    repeated = ["a", "a", "b", "b"] * 6
    conflicting = ["a", "b", "a", "b"] * 6
    classes = [True, True, False, False] * 6
    classified = compare_dataframes(
        pd.DataFrame(
            {
                "y": pd.Series(classes, dtype="boolean"),
                "group": pd.Series(repeated, dtype="category"),
            }
        ),
        pd.DataFrame(
            {
                "group": pd.Series(conflicting, dtype="category"),
                "y": pd.Series(classes, dtype="boolean"),
            }
        ),
        target="y",
    )
    assert classified.target is not None and classified.target.leakage is not None
    mapping = classified.target.leakage.transitions[0]
    assert mapping.reference_mapping is MappingStatus.DETERMINISTIC_REPEATED
    assert mapping.comparison_mapping is MappingStatus.CONFLICTING
    assert mapping.mapping_status_changed is True
    assert mapping.reference_exact is ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    assert mapping.comparison_exact is ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    assert mapping.exact_status_changed is False


def test_unrequested_target_on_an_analysis_is_not_compared() -> None:
    frame = pd.DataFrame({"y": [1, 2, 3, 4, 5, 6], "x": [1, 2, 3, 4, 5, 8]})
    plain = compare_dataset_analyses(
        analyze_dataframe(frame),
        analyze_dataframe(frame.iloc[:, ::-1]),
    )
    stored = compare_dataset_analyses(
        analyze_dataframe(frame, target="y"),
        analyze_dataframe(frame.iloc[:, ::-1], target="y"),
    )
    assert plain == stored
    assert plain.target is None


def test_comparison_only_and_uncollected_target_are_explicit() -> None:
    comparison_only = compare_dataframes(
        pd.DataFrame({"a": [1, 2, 3, 4]}),
        pd.DataFrame({"a": [1, 2, 3, 4], "y": [1, 2, 3, 9]}),
        target="y",
    )
    assert comparison_only.target is not None
    assert comparison_only.target.alignment.status is (
        TargetAlignmentStatus.COMPARISON_ONLY
    )
    assert comparison_only.target.diagnostic is None

    frame = pd.DataFrame({"y": [1, 2, 3, 4, 5, 6], "x": [1, 2, 4, 3, 6, 5]})
    uncollected = compare_dataset_analyses(
        analyze_dataframe(frame),
        analyze_dataframe(frame),
        reference_frame=frame,
        comparison_frame=frame,
        target_reference_position=0,
        target_comparison_position=0,
        target_requested=True,
    )
    assert uncollected.target is not None
    assert uncollected.target.diagnostic is not None
    assert uncollected.target.diagnostic.status is (
        DiagnosticComparisonStatus.NOT_COLLECTED
    )
    assert uncollected.target.leakage is not None
    assert uncollected.target.leakage.status is LeakageComparisonStatus.NOT_COLLECTED


def test_target_roles_follow_the_family_without_recomputing_effects() -> None:
    reference = pd.DataFrame(
        {
            "y": pd.Series(["a", "a", "b", "b"], dtype="category"),
            "x": [1, 2, 8, 9],
            "flag": [True, False, True, False],
            "other": [True, True, False, False],
            "when": pd.date_range("2020-01-01", periods=4),
        }
    )
    comparison = reference.copy()
    comparison["x"] = [1, 1, 9, 9]
    result = compare_dataframes(reference, comparison, target="y")
    assert result.target is not None
    by_role = {
        (item.reference_role, item.comparison_role)
        for item in result.target.relationships
    }
    assert (TargetColumnRole.CATEGORICAL, TargetColumnRole.CATEGORICAL) in by_role
    assert (TargetColumnRole.UNSUPPORTED, TargetColumnRole.UNSUPPORTED) in by_role

    boolean = compare_dataframes(
        pd.DataFrame(
            {
                "y": [True, True, False, False],
                "other": [True, False, True, False],
            }
        ),
        pd.DataFrame(
            {
                "other": [False, True, False, True],
                "y": [True, True, False, False],
            }
        ),
        target="y",
    )
    assert boolean.target is not None
    roles = {item.reference_role for item in boolean.target.relationships}
    assert TargetColumnRole.CONDITIONING in roles or TargetColumnRole.OUTCOME in roles
    assert boolean.target.relationships[0].reference_role is not (
        boolean.target.relationships[0].comparison_role
    )


def test_binary_diagnostic_metrics_stay_raw_differences() -> None:
    labels = [True, False] * 20
    reference = pd.DataFrame(
        {
            "x": [float(index) for index in range(40)],
            "y": pd.Series(labels, dtype="boolean"),
        }
    )
    comparison = pd.DataFrame(
        {
            "x": [float(index % 3) for index in range(40)],
            "y": pd.Series(labels, dtype="boolean"),
        }
    )
    result = compare_dataframes(reference, comparison, target="y")
    assert result.target is not None and result.target.diagnostic is not None
    diagnostic = result.target.diagnostic
    assert diagnostic.status is DiagnosticComparisonStatus.COMPARED
    metrics = {item.metric: item for item in diagnostic.metrics}
    assert DiagnosticMetric.ROC_AUC in metrics
    assert DiagnosticMetric.LOG_LOSS in metrics
    change = metrics[DiagnosticMetric.ROC_AUC]
    assert change.model_change == pytest.approx(
        change.comparison_model - change.reference_model
    )
    assert not hasattr(change, "p_value")
    frame = _regression([float(value) for value in range(24)])
    result = compare_dataframes(frame, frame.copy(), target="y")
    assert result.target is not None
    names = {field.name for field in dataclasses.fields(result.target)}
    assert "score" not in names
    text = repr(result.target).lower()
    assert "concept drift" not in text
    assert "degradation" not in text
