"""TSK-040: findings over one dataset comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pytics.analysis.compare import DiagnosticComparisonStatus
from pytics.analysis.compare import RelationshipPairStatus
from pytics.analysis.compare import TargetAlignmentStatus
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare import compare_dataset_analyses
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.findings import DeferredFindingFamily
from pytics.analysis.findings import FindingCode
from pytics.analysis.findings import FindingSeverity
from pytics.analysis.findings import FindingsSource
from pytics.analysis.findings import SuppressionRule
from pytics.analysis.findings import collect_compare_findings
from pytics.analysis.target_diagnostic import PredictiveTask
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import MappingStatus
from pytics.semantics.interpretation import SemanticType
from tests.findings_support import assert_source_free
from tests.findings_support import with_labels

_TARGET_CODES = (
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED,
    FindingCode.TARGET_TASK_CHANGED,
    FindingCode.TARGET_CLASS_VOCABULARY_CHANGED,
)


def _codes(result) -> list:
    return [finding.code for finding in result.findings]


def _categories(values) -> pd.Series:
    return pd.Series(pd.Categorical(values))


def _noise(n_rows: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(size=n_rows)


def test_one_sided_columns_are_findings_and_a_reorder_is_not() -> None:
    reference = pd.DataFrame(
        {"a": [1.0, 2.0, 3.0, 4.0], "gone": [1, 2, 3, 5], "b": [4.0, 3.0, 2.0, 1.0]}
    )
    comparison = pd.DataFrame(
        {"b": [4.0, 3.0, 2.0, 0.0], "a": [1.0, 2.0, 3.0, 9.0], "new": ["p"] * 4}
    )
    comparison_result = compare_dataframes(reference, comparison)
    result = collect_compare_findings(comparison_result)
    assert result.source is FindingsSource.COMPARE
    assert _codes(result) == [
        FindingCode.COLUMN_REFERENCE_ONLY,
        FindingCode.COLUMN_COMPARISON_ONLY,
    ]
    gone, new = result.findings
    assert gone.severity is new.severity is FindingSeverity.NOTABLE
    assert gone.subject.reference_position == 1
    assert gone.subject.comparison_position is None
    assert gone.evidence is comparison_result.columns[1].semantic
    assert gone.evidence.reference.selected_type is SemanticType.NUMERIC
    assert new.subject.comparison_position == 2
    assert new.evidence.reference is None
    assert result.coverage.not_evaluated_codes == _TARGET_CODES
    assert_source_free(result)


def test_a_semantic_change_owns_its_relationship_transitions() -> None:
    n_rows = 12
    reference = pd.DataFrame(
        {
            "x": _noise(n_rows, 1),
            "a": _noise(n_rows, 2),
            "b": _noise(n_rows, 3),
            "c": _noise(n_rows, 4),
        }
    )
    comparison = reference.copy()
    comparison["x"] = [f"s{index}" for index in range(n_rows)]
    comparison_result = compare_dataframes(reference, comparison)
    transitions = [
        record
        for record in comparison_result.relationships
        if record.status is RelationshipPairStatus.ELIGIBILITY_TRANSITION
    ]
    assert len(transitions) == 3
    result = collect_compare_findings(comparison_result)
    assert _codes(result) == [FindingCode.SEMANTIC_TYPE_CHANGED]
    (changed,) = result.findings
    assert changed.subject.reference_position == 0
    assert changed.evidence.semantic is comparison_result.columns[0].semantic
    assert changed.evidence.semantic.reference.selected_type is SemanticType.NUMERIC
    assert changed.evidence.semantic.comparison.selected_type is None
    assert changed.evidence.n_relationship_transitions == 3
    assert result.suppressed == ()


def test_a_removed_column_creates_no_downstream_findings() -> None:
    reference = pd.DataFrame(
        {"x": _noise(10, 1), "a": _noise(10, 2), "b": _noise(10, 3)}
    )
    comparison = reference.drop(columns=["x"])
    result = collect_compare_findings(compare_dataframes(reference, comparison))
    assert _codes(result) == [FindingCode.COLUMN_REFERENCE_ONLY]


def _target_frames(reference_target, comparison_target, n_rows: int = 24):
    reference = pd.DataFrame({"y": reference_target, "x": _noise(n_rows, 5)})
    comparison = pd.DataFrame({"y": comparison_target, "x": _noise(n_rows, 6)})
    return reference, comparison


def test_a_target_task_change_without_a_semantic_change() -> None:
    reference, comparison = _target_frames(
        _categories(["a", "b"] * 12),
        _categories(["a", "b", "c"] * 8),
    )
    comparison_result = compare_dataframes(reference, comparison, target="y")
    diagnostic = comparison_result.target.diagnostic
    assert diagnostic.status is DiagnosticComparisonStatus.TASK_TRANSITION
    result = collect_compare_findings(comparison_result)
    assert _codes(result) == [FindingCode.TARGET_TASK_CHANGED]
    (task,) = result.findings
    assert task.severity is FindingSeverity.NOTABLE
    assert task.evidence is diagnostic
    assert task.evidence.reference_task is PredictiveTask.BINARY_CLASSIFICATION
    assert task.evidence.comparison_task is PredictiveTask.MULTICLASS_CLASSIFICATION
    assert task.subject.reference_position == 0
    assert result.coverage.not_evaluated_codes == ()
    assert_source_free(result)


def test_a_target_class_vocabulary_change() -> None:
    reference, comparison = _target_frames(
        _categories(["a", "b"] * 12),
        _categories(["a", "c"] * 12),
    )
    result = collect_compare_findings(
        compare_dataframes(reference, comparison, target="y")
    )
    assert _codes(result) == [FindingCode.TARGET_CLASS_VOCABULARY_CHANGED]
    assert result.findings[0].evidence.status is (
        DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED
    )


def test_a_target_semantic_change_owns_task_and_leakage_transitions() -> None:
    values = [float(index) + 0.5 for index in range(24)]
    reference = pd.DataFrame({"y": values, "x": values, "z": _noise(24, 7)})
    comparison = pd.DataFrame(
        {"y": _categories(["a", "b"] * 12), "x": values, "z": _noise(24, 8)}
    )
    comparison_result = compare_dataframes(reference, comparison, target="y")
    target = comparison_result.target
    assert target.diagnostic.status is DiagnosticComparisonStatus.TASK_TRANSITION
    copy, _other = target.leakage.transitions
    assert copy.reference_exact is ExactDuplicateStatus.EXACT_DUPLICATE
    assert copy.comparison_exact is ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION

    result = collect_compare_findings(comparison_result)
    assert _codes(result) == [FindingCode.SEMANTIC_TYPE_CHANGED]
    (changed,) = result.findings
    assert changed.subject.reference_position == 0
    assert changed.evidence.n_relationship_transitions == 2
    assert [item.finding.code for item in result.suppressed] == [
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED,
        FindingCode.TARGET_TASK_CHANGED,
    ]
    for item in result.suppressed:
        assert item.root == changed.identity
        assert item.rule is SuppressionRule.SEMANTIC_CHANGE_OWNS_TARGET_COMPARISON
    assert result.coverage.n_candidates == 3


def _boolean_target(n_rows: int = 24) -> list:
    return [index % 3 == 0 for index in range(n_rows)]


def test_an_exact_duplicate_transition_is_a_warning() -> None:
    target = _boolean_target()
    broken = list(target)
    broken[0] = not broken[0]
    reference = pd.DataFrame({"y": target, "copy": target, "x": _noise(24, 9)})
    comparison = pd.DataFrame({"y": target, "copy": broken, "x": _noise(24, 10)})
    comparison_result = compare_dataframes(reference, comparison, target="y")
    transition = comparison_result.target.leakage.transitions[0]
    assert transition.reference_exact is ExactDuplicateStatus.EXACT_DUPLICATE
    assert transition.comparison_exact is ExactDuplicateStatus.NOT_EQUAL
    result = collect_compare_findings(comparison_result)
    assert _codes(result) == [FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED]
    (changed,) = result.findings
    assert changed.severity is FindingSeverity.WARNING
    assert changed.evidence is transition
    assert changed.subject.target.reference_position == 0
    assert changed.subject.predictor.reference_position == 1


def test_a_mapping_status_transition_alone_is_not_a_finding() -> None:
    target = _boolean_target()
    code = ["p" if value else "q" for value in target]
    conflicting = list(code)
    conflicting[1] = "p"
    reference = pd.DataFrame({"y": target, "code": _categories(code)})
    comparison = pd.DataFrame({"y": target, "code": _categories(conflicting)})
    comparison_result = compare_dataframes(reference, comparison, target="y")
    transition = comparison_result.target.leakage.transitions[0]
    assert transition.reference_mapping is MappingStatus.DETERMINISTIC_REPEATED
    assert transition.comparison_mapping is MappingStatus.CONFLICTING
    result = collect_compare_findings(comparison_result)
    assert result.findings == ()
    assert result.suppressed == ()


def test_a_predictor_semantic_change_owns_its_exact_transition() -> None:
    target = _boolean_target()
    reference = pd.DataFrame(
        {"y": target, "copy": [1 if value else 0 for value in target]}
    )
    comparison = pd.DataFrame({"y": target, "copy": target})
    comparison_result = compare_dataframes(reference, comparison, target="y")
    transition = comparison_result.target.leakage.transitions[0]
    assert transition.reference_exact is (
        ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    )
    assert transition.comparison_exact is ExactDuplicateStatus.EXACT_DUPLICATE
    result = collect_compare_findings(comparison_result)
    assert _codes(result) == [FindingCode.SEMANTIC_TYPE_CHANGED]
    (owned,) = result.suppressed
    assert owned.finding.code is FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED
    assert owned.root == result.findings[0].identity
    assert owned.root.subject == (owned.finding.identity.subject[1],)


def test_target_codes_need_an_aligned_target() -> None:
    reference = pd.DataFrame({"y": _boolean_target(), "x": _noise(24, 11)})
    plain = collect_compare_findings(compare_dataframes(reference, reference.copy()))
    assert plain.findings == ()
    assert plain.coverage.not_evaluated_codes == _TARGET_CODES

    removed = compare_dataframes(reference, reference[["x"]], target="y")
    assert removed.target.alignment.status is TargetAlignmentStatus.REFERENCE_ONLY
    result = collect_compare_findings(removed)
    assert _codes(result) == [FindingCode.COLUMN_REFERENCE_ONLY]
    assert result.findings[0].severity is FindingSeverity.NOTABLE
    assert result.coverage.not_evaluated_codes == _TARGET_CODES

    analyses_without_target = compare_dataset_analyses(
        analyze_dataframe(reference), analyze_dataframe(reference.copy())
    )
    assert collect_compare_findings(analyses_without_target).findings == ()


def _drift_frames(n_rows: int, shift: float, seed: int):
    rng = np.random.default_rng(seed)
    reference = pd.DataFrame(
        {
            "v": rng.normal(size=n_rows),
            "changes": rng.normal(size=n_rows),
            "gone": rng.normal(size=n_rows),
        }
    )
    comparison = pd.DataFrame(
        {
            "v": rng.normal(loc=shift, size=n_rows),
            "changes": ["s"] * n_rows,
        }
    )
    return reference, comparison


def _drift_p(comparison_result) -> float:
    return comparison_result.columns[0].distribution.test.p_value


def test_drift_significance_does_not_create_or_escalate_findings() -> None:
    small = compare_dataframes(*_drift_frames(40, 0.04, 1))
    huge = compare_dataframes(*_drift_frames(60000, 0.04, 2))
    assert _drift_p(small) > 0.05
    assert _drift_p(huge) < 1e-4
    assert huge.columns[0].distribution.ks_distance.value < 0.05
    small_result = collect_compare_findings(small)
    huge_result = collect_compare_findings(huge)
    assert [(item.identity, item.severity) for item in small_result.findings] == [
        (item.identity, item.severity) for item in huge_result.findings
    ]
    assert _codes(huge_result) == [
        FindingCode.SEMANTIC_TYPE_CHANGED,
        FindingCode.COLUMN_REFERENCE_ONLY,
    ]
    assert DeferredFindingFamily.DISTRIBUTION_DRIFT in (
        huge_result.coverage.deferred_families
    )


def test_a_large_effect_with_a_large_p_value_is_not_suppressed_or_promoted() -> None:
    reference = pd.DataFrame({"v": [0.0, 1.0, 2.0], "gone": [1.0, 2.0, 3.0]})
    comparison = pd.DataFrame({"v": [10.0, 11.0, 12.0]})
    comparison_result = compare_dataframes(reference, comparison)
    drift = comparison_result.columns[0].distribution
    assert drift.ks_distance.value == 1.0
    assert drift.test.p_value > 0.05
    result = collect_compare_findings(comparison_result)
    assert _codes(result) == [FindingCode.COLUMN_REFERENCE_ONLY]
    assert result.findings[0].severity is FindingSeverity.NOTABLE


def test_duplicate_labels_follow_alignment_occurrence() -> None:
    reference = with_labels([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], ["a", "a", "b"])
    comparison = with_labels(
        [[1.0, 2.5], [5.0, 6.5], [3.0, 4.5], [7.0, 8.0]], ["a", "b", "a", "a"]
    )
    result = collect_compare_findings(compare_dataframes(reference, comparison))
    assert _codes(result) == [FindingCode.COLUMN_COMPARISON_ONLY]
    (extra,) = result.findings
    assert extra.subject.occurrence == 3
    assert extra.subject.comparison_position == 3
    assert extra.identity.subject == (("label", ("str", "a"), 3),)


def test_adversarial_labels_use_canonical_alignment() -> None:
    labels = [True, 1.0, float("nan"), None, 2**53 + 1]
    flags = [[True, False, True], [False, True, True], [True, True, False]]
    reference = with_labels([flags[index % 3] for index in range(5)], labels)
    comparison = with_labels(
        [flags[index % 3] for index in range(4)],
        [1, True, None, float(2**53)],
    )
    result = collect_compare_findings(compare_dataframes(reference, comparison))
    assert _codes(result) == [
        FindingCode.COLUMN_REFERENCE_ONLY,
        FindingCode.COLUMN_REFERENCE_ONLY,
        FindingCode.COLUMN_COMPARISON_ONLY,
    ]
    nan_column, big, near = result.findings
    assert nan_column.subject.reference_position == 2
    assert nan_column.identity.subject == (("label", ("float_nan",), 1),)
    assert big.identity.subject == (("label", ("number", 2**53 + 1), 1),)
    assert near.identity.subject == (("label", ("number", 2**53), 1),)
    assert near.subject.comparison_position == 3
    assert_source_free(result)


def test_unretainable_labels_are_one_sided_with_side_and_position() -> None:
    class Box:
        def __hash__(self) -> int:
            return 1

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Box)

    reference = with_labels([[1.0, 2.0], [3.0, 4.0]], [Box(), "a"])
    comparison = with_labels([[1.0, 2.0], [3.0, 4.0]], ["a", Box()])
    result = collect_compare_findings(compare_dataframes(reference, comparison))
    assert [finding.identity.subject for finding in result.findings] == [
        (("reference_position", 0),),
        (("comparison_position", 1),),
    ]


def test_identity_is_stable_under_reordering_and_repetition() -> None:
    reference = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0],
            "gone": [1.0, 2.0, 3.0, 4.0],
            "b": [4.0, 3.0, 2.0, 1.0],
        }
    )
    comparison = pd.DataFrame(
        {"a": ["s", "t", "u", "v"], "b": [4.0, 3.0, 2.0, 0.0], "new": [1, 2, 3, 4]}
    )
    first = collect_compare_findings(compare_dataframes(reference, comparison))
    again = collect_compare_findings(compare_dataframes(reference, comparison))
    reordered = collect_compare_findings(
        compare_dataframes(reference, comparison[["new", "b", "a"]])
    )
    assert first == again
    assert [item.identity for item in reordered.findings] == [
        item.identity for item in first.findings
    ]


def test_a_dataframe_is_not_accepted() -> None:
    with pytest.raises(TypeError, match="DatasetComparison"):
        collect_compare_findings(pd.DataFrame({"a": [1]}))  # type: ignore[arg-type]
