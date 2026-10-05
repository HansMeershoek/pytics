"""TSK-040: findings over one dataset analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.findings import DeferredFindingFamily
from pytics.analysis.findings import FindingCode
from pytics.analysis.findings import FindingSeverity
from pytics.analysis.findings import FindingsSource
from pytics.analysis.findings import SuppressionRule
from pytics.analysis.findings import collect_profile_findings
from pytics.analysis.relationships.models import CategoricalCategoricalRelationship
from pytics.analysis.relationships.models import NumericNumericRelationship
from pytics.analysis.target_diagnostic import PredictorDecision
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import MappingStatus
from pytics.semantics.interpretation import SemanticType
from tests.findings_support import assert_source_free
from tests.findings_support import with_labels

_TARGET_CODES = (
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
    FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE,
)


def _codes(result) -> list:
    return [finding.code for finding in result.findings]


def _categories(values, categories=None) -> pd.Series:
    return pd.Series(pd.Categorical(values, categories=categories))


def _structural_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "x": [1.0, 2.5, 3.0, 4.5, 5.0, 6.0],
            "empty": [None] * 6,
            "constant": [7, 7, None, 7, 7, 7],
            "flag": [True, False, True, False, True, True],
        }
    )


def test_structural_columns_and_duplicate_rows_are_selected_in_policy_order() -> None:
    frame = _structural_frame()
    frame = pd.concat([frame, frame.iloc[[0, 1, 1]]], ignore_index=True)
    analysis = analyze_dataframe(frame)
    result = collect_profile_findings(analysis)
    assert result.source is FindingsSource.PROFILE
    assert _codes(result) == [
        FindingCode.EMPTY_COLUMN,
        FindingCode.CONSTANT_COLUMN,
        FindingCode.DUPLICATE_ROWS,
    ]
    empty, constant, duplicates = result.findings
    assert empty.severity is FindingSeverity.NOTABLE
    assert constant.severity is FindingSeverity.NOTABLE
    assert duplicates.severity is FindingSeverity.INFO
    assert empty.subject.position == 1
    assert constant.subject.position == 2
    assert empty.evidence is analysis.columns[1].evidence.basic
    assert constant.evidence is analysis.columns[2].evidence.basic
    assert constant.evidence.n_missing == 1
    groups = analysis.duplicate_analysis
    assert duplicates.subject is None
    assert duplicates.evidence.n_rows == analysis.n_rows
    assert duplicates.evidence.n_duplicate_groups == groups.n_duplicate_groups == 2
    assert duplicates.evidence.n_rows_in_duplicate_groups == (
        groups.n_rows_in_duplicate_groups
    )
    assert duplicates.evidence.n_excess_duplicate_rows == groups.n_excess_duplicate_rows
    assert result.coverage.not_evaluated_codes == _TARGET_CODES
    assert result.coverage.n_notable == 2
    assert result.coverage.n_info == 1
    assert result.suppressed == ()
    assert_source_free(result)


@pytest.mark.parametrize(
    "values",
    [
        pd.Series([np.nan, np.nan, np.nan], dtype="float64"),
        pd.Series([None, None, None], dtype="boolean"),
        _categories([None, None, None], ["a", "b"]),
        pd.Series([None, None, None], dtype="object"),
        pd.Series([], dtype="float64"),
    ],
)
def test_an_all_missing_column_is_one_empty_finding(values: pd.Series) -> None:
    frame = pd.DataFrame({"gone": values, "row": np.arange(len(values), dtype=float)})
    analysis = analyze_dataframe(frame)
    assert analysis.columns[0].inferred.selected_type is SemanticType.EMPTY
    result = collect_profile_findings(analysis)
    about_gone = [
        item.code
        for item in result.findings
        if item.subject is not None and item.subject.position == 0
    ]
    assert about_gone == [FindingCode.EMPTY_COLUMN]
    assert FindingCode.CONSTANT_COLUMN not in _codes(result)
    assert FindingCode.CONSTANT_COLUMN in result.coverage.evaluated_codes
    empty_columns = sum(
        column.inferred.selected_type is SemanticType.EMPTY
        for column in analysis.columns
    )
    assert _codes(result) == [FindingCode.EMPTY_COLUMN] * empty_columns


def test_an_empty_target_and_empty_predictors_add_no_target_finding() -> None:
    frame = pd.DataFrame(
        {
            "y": [None] * 8,
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        }
    )
    result = collect_profile_findings(analyze_dataframe(frame, target="y"))
    assert _codes(result) == [FindingCode.EMPTY_COLUMN]
    assert result.coverage.evaluated_codes[:2] == _TARGET_CODES


def test_facts_that_are_not_findings_stay_silent() -> None:
    rng = np.random.default_rng(40)
    skewed = np.exp(rng.normal(size=400))
    frame = pd.DataFrame(
        {
            "id": [f"{index:032x}" for index in range(400)],
            "text": [f"value {index % 7}" for index in range(400)],
            "skewed": skewed,
            "partial": np.where(np.arange(400) % 3 == 0, np.nan, skewed),
            "linear": 2.0 * skewed + 1.0,
        }
    )
    analysis = analyze_dataframe(frame)
    assert analysis.columns[0].inferred.selected_type is SemanticType.IDENTIFIER
    assert analysis.columns[1].inferred.selected_type is None
    anomalies = analysis.anomaly_analysis.numeric_univariate
    assert sum(len(record.observations) for record in anomalies) > 20
    result = collect_profile_findings(analysis)
    assert result.findings == ()
    assert result.coverage.n_candidates == 0
    assert DeferredFindingFamily.UNIVARIATE_ANOMALY in result.coverage.deferred_families
    assert DeferredFindingFamily.MISSINGNESS_LEVEL in result.coverage.deferred_families
    assert DeferredFindingFamily.RELATIONSHIP_STRENGTH in (
        result.coverage.deferred_families
    )


def test_many_duplicate_groups_are_one_dataset_finding() -> None:
    base = pd.DataFrame({"a": np.arange(500), "b": np.arange(500) % 3})
    frame = pd.concat([base, base, base.iloc[:100]], ignore_index=True)
    analysis = analyze_dataframe(frame)
    result = collect_profile_findings(analysis)
    assert _codes(result) == [FindingCode.DUPLICATE_ROWS]
    evidence = result.findings[0].evidence
    assert evidence.n_duplicate_groups == 500
    assert evidence.n_rows_in_duplicate_groups == 1100
    assert evidence.n_excess_duplicate_rows == 600


def test_an_exact_target_copy_is_one_warning_and_owns_its_mapping() -> None:
    target = ["a", "b", "c"] * 10
    frame = pd.DataFrame(
        {
            "y": _categories(target),
            "copy": _categories(target),
            "noise": np.random.default_rng(3).normal(size=30),
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    copy = analysis.target_leakage.predictors[0]
    assert copy.exact_duplicate.status is ExactDuplicateStatus.EXACT_DUPLICATE
    assert copy.deterministic_mapping.status is MappingStatus.DETERMINISTIC_REPEATED
    relationship = next(
        record
        for record in analysis.relationship_analysis.relationships
        if isinstance(record, CategoricalCategoricalRelationship)
    )
    assert relationship.association.value == pytest.approx(1.0)
    decisions = {
        item.position: item.decision for item in analysis.target_diagnostic.predictors
    }
    assert decisions[1] is PredictorDecision.IDENTICAL_TO_TARGET

    result = collect_profile_findings(analysis)
    assert _codes(result) == [FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE]
    exact = result.findings[0]
    assert exact.severity is FindingSeverity.WARNING
    assert exact.evidence is copy.exact_duplicate
    assert exact.subject.target.position == 0
    assert exact.subject.predictor.position == 1
    (owned,) = result.suppressed
    assert owned.rule is SuppressionRule.EXACT_DUPLICATE_OWNS_MAPPING
    assert owned.root == exact.identity
    assert owned.finding.code is FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE
    assert owned.finding.evidence is copy.deterministic_mapping
    assert result.coverage.n_candidates == 2
    assert_source_free(result)


def test_a_mapping_finding_needs_every_predictor_value_to_repeat() -> None:
    target = [True, False] * 8
    frame = pd.DataFrame(
        {
            "y": target,
            "relabeled": _categories(["yes" if value else "no" for value in target]),
            "row": np.arange(16, dtype=float),
            "spare": _categories(
                ["p" if value else "q" for value in target[:-1]] + ["r"]
            ),
        }
    )
    frame = pd.concat([frame, frame.iloc[[0, 1]]], ignore_index=True)
    analysis = analyze_dataframe(frame, target="y")
    by_position = {item.position: item for item in analysis.target_leakage.predictors}
    row = by_position[2].deterministic_mapping
    assert row.status is MappingStatus.DETERMINISTIC_REPEATED
    assert row.n_singleton_groups > 0
    spare = by_position[3].deterministic_mapping
    assert spare.status is MappingStatus.DETERMINISTIC_REPEATED
    assert spare.n_singleton_groups == 1

    result = collect_profile_findings(analysis)
    mappings = [
        finding
        for finding in result.findings
        if finding.code is FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE
    ]
    assert [finding.subject.predictor.position for finding in mappings] == [1]
    assert mappings[0].severity is FindingSeverity.WARNING
    assert mappings[0].evidence.n_singleton_groups == 0
    assert _codes(result) == [
        FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE,
        FindingCode.DUPLICATE_ROWS,
    ]


def test_a_numeric_target_copy_has_no_mapping_candidate() -> None:
    values = [1.5, 2.0, 3.25, 4.0, 5.5, 6.0, 7.75, 8.0, 9.5, 10.0]
    frame = pd.DataFrame({"y": values, "copy": values, "other": values[::-1]})
    result = collect_profile_findings(analyze_dataframe(frame, target="y"))
    assert _codes(result) == [FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE]
    assert result.suppressed == ()
    assert result.coverage.evaluated_codes[:2] == _TARGET_CODES


def test_duplicate_labels_stay_distinct_subjects() -> None:
    frame = with_labels(
        [
            [None, None, None, None],
            [5, 5, 5, 5],
            [1, 2, 3, 4],
            [None, None, None, None],
        ],
        ["a", "a", "b", "a"],
    )
    analysis = analyze_dataframe(frame)
    result = collect_profile_findings(analysis)
    assert _codes(result) == [
        FindingCode.EMPTY_COLUMN,
        FindingCode.EMPTY_COLUMN,
        FindingCode.CONSTANT_COLUMN,
    ]
    first, last, constant = result.findings
    assert (first.subject.position, first.subject.occurrence) == (0, 1)
    assert (last.subject.position, last.subject.occurrence) == (3, 3)
    assert (constant.subject.position, constant.subject.occurrence) == (1, 2)
    assert first.evidence is analysis.columns[0].evidence.basic
    assert last.evidence is analysis.columns[3].evidence.basic
    assert constant.evidence is analysis.columns[1].evidence.basic
    identities = {finding.identity for finding in result.findings}
    assert len(identities) == 3
    assert collect_profile_findings(analysis) == result


def test_adversarial_labels_do_not_collapse_identity() -> None:
    labels = [True, 1, 1.0, float("nan"), None, 2**53 + 1, float(2**53), "1"]
    frame = with_labels(
        [[None, None]] * len(labels) + [[1.0, 2.0]],
        labels + ["row"],
    )
    result = collect_profile_findings(analyze_dataframe(frame))
    assert [finding.subject.position for finding in result.findings] == list(
        range(len(labels))
    )
    identities = [finding.identity for finding in result.findings]
    assert len(set(identities)) == len(labels)
    keys = [finding.subject.key for finding in result.findings]
    assert keys[1][1] == keys[2][1] == ("number", 1)
    assert (keys[1][2], keys[2][2]) == (1, 2)
    assert keys[0][1] == ("bool", True)
    assert keys[3][1] == ("float_nan",)
    assert keys[4][1] == ("none",)
    assert keys[5][1] == ("number", 2**53 + 1)
    assert keys[6][1] == ("number", 2**53)
    assert keys[7][1] == ("str", "1")
    assert_source_free(result)


def test_unretainable_labels_fall_back_to_position() -> None:
    class Box:
        def __hash__(self) -> int:
            return 1

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Box)

    frame = with_labels([[None, None], [None, None], [1.0, 2.0]], [Box(), Box(), "row"])
    result = collect_profile_findings(analyze_dataframe(frame))
    assert [finding.subject.key for finding in result.findings] == [
        ("position", 0),
        ("position", 1),
    ]
    assert all(finding.subject.occurrence is None for finding in result.findings)
    assert_source_free(result)


def test_identity_and_relative_order_survive_an_unrelated_column() -> None:
    frame = _structural_frame()
    before = collect_profile_findings(analyze_dataframe(frame))
    widened = frame.copy()
    widened.insert(0, "new_empty", [None] * len(frame))
    widened.insert(3, "unrelated", np.arange(len(frame), dtype=float))
    after = collect_profile_findings(analyze_dataframe(widened))
    old = [finding.identity for finding in before.findings]
    new = [finding.identity for finding in after.findings]
    assert [identity for identity in new if identity in old] == old
    assert set(new) - set(old) == {
        identity for identity in new if identity.subject[0][1] == ("str", "new_empty")
    }
    reordered = collect_profile_findings(analyze_dataframe(frame[frame.columns[::-1]]))
    assert {finding.identity for finding in reordered.findings} == set(old)


def test_repeated_execution_is_identical() -> None:
    frame = _structural_frame()
    frame["y"] = [True, False, True, False, True, False]
    frame["copy"] = frame["y"]
    analysis = analyze_dataframe(frame, target="y")
    first = collect_profile_findings(analysis)
    second = collect_profile_findings(analyze_dataframe(frame.copy(), target="y"))
    assert first == second
    assert [item.identity for item in first.findings] == [
        item.identity for item in second.findings
    ]


def _spearman_p(analysis) -> float:
    record = next(
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, NumericNumericRelationship)
    )
    return record.methods[0].frequentist.p_value


def test_relationship_significance_does_not_create_or_change_findings() -> None:
    def frame(n_rows: int) -> pd.DataFrame:
        rng = np.random.default_rng(n_rows)
        x = rng.normal(size=n_rows)
        return pd.DataFrame(
            {
                "x": x,
                "y": 0.05 * x + rng.normal(size=n_rows),
                "empty": [None] * n_rows,
                "constant": ["k"] * n_rows,
            }
        )

    small = analyze_dataframe(frame(30))
    large = analyze_dataframe(frame(60000))
    assert _spearman_p(small) > 0.05
    assert _spearman_p(large) < 1e-6
    small_result = collect_profile_findings(small)
    large_result = collect_profile_findings(large)
    assert [(item.identity, item.severity) for item in small_result.findings] == [
        (item.identity, item.severity) for item in large_result.findings
    ]
    assert _codes(small_result) == [
        FindingCode.EMPTY_COLUMN,
        FindingCode.CONSTANT_COLUMN,
    ]


def test_a_dataframe_is_not_accepted() -> None:
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        collect_profile_findings(_structural_frame())  # type: ignore[arg-type]
