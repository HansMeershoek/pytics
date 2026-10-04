"""TSK-032: explicit target projection over retained analytical facts."""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.numeric as numeric_module
import pytics.analysis.relationships.adjustment as adjustment_module
import pytics.analysis.relationships.collector as collector_module
import pytics.analysis.target as target_module
from pytics.analysis.boolean import BooleanDescriptiveAnalysis
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.relationships.models.coverage import SelectedPairClass
from pytics.analysis.relationships.models.coverage import SelectedPairCoverage
from pytics.analysis.relationships.models.coverage import (
    UnimplementedRelationshipFamily,
)
from pytics.analysis.relationships.models.coverage import classify_selected_pair
from pytics.analysis.categorical import CategoricalDescriptiveAnalysis
from pytics.analysis.categorical import ObservedCategoryCount
from pytics.analysis.target import TargetPhysicalSide
from pytics.analysis.target import TargetPopulation
from pytics.analysis.target import TargetPosition
from pytics.analysis.target import TargetRecordRole
from pytics.analysis.target import TargetRelationship
from pytics.analysis.target import TargetStatus
from pytics.analysis.target import build_target_summary
from pytics.analysis.target import project_target_analysis
from pytics.analysis.target import resolve_target_position
from pytics.analysis.target import status_for_target
from pytics.analysis.variables import build_variables_summary
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus

_RETAINED = (pd.DataFrame, pd.Series, pd.Index, np.ndarray)
_UUIDS = (
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
)


def _flag(values: list[object]) -> pd.Series:
    return pd.Series(values, dtype="boolean")


def _mixed_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "amount": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "flag": _flag([True, False, True, False, True, False]),
            "city": pd.Series(
                ["a", "a", "b", "b", "a", "b"],
                dtype="category",
            ),
            "when": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-01-02",
                    "2020-01-03",
                    "2020-01-04",
                    "2020-01-05",
                    "2020-01-06",
                ]
            ),
            "code": pd.Series(_UUIDS + _UUIDS[:2], dtype="string"),
        }
    )


def _assert_no_source(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _RETAINED)
    assert not type(value).__module__.startswith(("scipy", "pandas.core", "numpy"))
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_no_source(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_source(item, seen)


def _fail(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("target projection used a source-dependent operation")


def test_target_status_matrix_is_explicit() -> None:
    expected = {
        SemanticType.NUMERIC: TargetStatus.SUPPORTED,
        SemanticType.CATEGORICAL: TargetStatus.SUPPORTED,
        SemanticType.BOOLEAN: TargetStatus.SUPPORTED,
        SemanticType.DATETIME: TargetStatus.UNSUPPORTED,
        SemanticType.TIMEDELTA: TargetStatus.UNSUPPORTED,
        SemanticType.TEXT: TargetStatus.UNSUPPORTED,
        SemanticType.EMPTY: TargetStatus.INELIGIBLE,
        SemanticType.CONSTANT: TargetStatus.INELIGIBLE,
        SemanticType.IDENTIFIER: TargetStatus.INELIGIBLE,
    }
    assert set(expected) == set(SemanticType)
    for semantic_type, status in expected.items():
        assert status_for_target(semantic_type, ResolutionStatus.RESOLVED) is status
    assert (
        status_for_target(None, ResolutionStatus.INSUFFICIENT_EVIDENCE)
        is TargetStatus.UNRESOLVED
    )
    assert (
        status_for_target(None, ResolutionStatus.AMBIGUOUS) is TargetStatus.UNRESOLVED
    )
    with pytest.raises(ValueError, match="no selected semantic type"):
        status_for_target(SemanticType.NUMERIC, ResolutionStatus.AMBIGUOUS)
    with pytest.raises(ValueError, match="selected semantic type"):
        status_for_target(None, ResolutionStatus.RESOLVED)
    with pytest.raises(TypeError, match="resolution_status"):
        status_for_target(SemanticType.NUMERIC, "resolved")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="selected_type"):
        status_for_target("numeric", ResolutionStatus.RESOLVED)  # type: ignore[arg-type]


def test_no_target_leaves_dataset_analysis_unchanged() -> None:
    frame = _mixed_frame()
    plain = analyze_dataframe(frame)
    same = analyze_dataframe(frame, target=None)
    assert plain.target_analysis is None
    assert plain == same
    assert build_target_summary(plain) is None
    targeted = analyze_dataframe(frame, target="amount")
    assert plain.target_leakage is None
    assert plain.target_diagnostic is None
    assert targeted.target_leakage is not None
    assert targeted.target_diagnostic is not None
    assert (
        dataclasses.replace(
            targeted,
            target_analysis=None,
            target_leakage=None,
            target_diagnostic=None,
        )
        == plain
    )
    assert targeted.columns == plain.columns
    assert targeted.relationship_analysis == plain.relationship_analysis


def test_unique_string_label_selects_that_column() -> None:
    analysis = analyze_dataframe(_mixed_frame(), target="flag")
    target = analysis.target_analysis
    assert target is not None
    assert target.position == 1
    assert target.label == "flag"
    assert target.selected_type is SemanticType.BOOLEAN
    assert target.resolution_status is ResolutionStatus.RESOLVED
    assert target.status is TargetStatus.SUPPORTED
    assert target.confidence is Confidence.HIGH
    assert target.inference_source is InferenceSource.PHYSICAL_DTYPE
    assert target.boolean_facts is analysis.columns[1].boolean_analysis
    assert target.numeric_facts is None
    assert target.categorical_facts is None


def test_non_string_and_tuple_labels_select_by_equality() -> None:
    frame = pd.DataFrame(
        [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
        columns=[("group", 1), 7, "plain"],
    )
    by_tuple = analyze_dataframe(frame, target=("group", 1))
    assert by_tuple.target_analysis is not None
    assert by_tuple.target_analysis.position == 0
    assert by_tuple.target_analysis.label == ("group", 1)
    by_int = analyze_dataframe(frame, target=7)
    assert by_int.target_analysis is not None
    assert by_int.target_analysis.position == 1
    assert by_int.target_analysis.label == 7
    numpy_label = np.int64(7)
    columns = pd.Index([numpy_label, "other"])
    assert resolve_target_position(columns, 7) == 0


def test_integer_label_is_not_a_position_and_bool_stays_distinct() -> None:
    frame = pd.DataFrame([[10, 20, 30], [11, 21, 31]], columns=[10, 11, 0])
    selected = analyze_dataframe(frame, target=0)
    assert selected.target_analysis is not None
    assert selected.target_analysis.position == 2
    assert selected.target_analysis.label == 0
    with pytest.raises(ValueError, match="not found"):
        analyze_dataframe(frame, target=1)
    by_position = analyze_dataframe(frame, target=TargetPosition(1))
    assert by_position.target_analysis is not None
    assert by_position.target_analysis.position == 1
    assert by_position.target_analysis.label == 11

    mixed = pd.DataFrame([[1, 2]], columns=[1, True])
    assert analyze_dataframe(mixed, target=1).target_analysis.position == 0
    assert analyze_dataframe(mixed, target=True).target_analysis.position == 1


def test_duplicate_label_is_rejected_until_a_position_is_given() -> None:
    frame = pd.DataFrame([[1, 2, 3], [4, 5, 6]], columns=["a", "a", "b"])
    with pytest.raises(ValueError, match="more than one column"):
        analyze_dataframe(frame, target="a")
    selected = analyze_dataframe(frame, target=TargetPosition(0))
    assert selected.target_analysis is not None
    assert selected.target_analysis.position == 0
    assert selected.target_analysis.label == "a"
    second = analyze_dataframe(frame, target=TargetPosition(1))
    assert second.target_analysis is not None
    assert second.target_analysis.position == 1
    with pytest.raises(ValueError, match="outside the column axis"):
        analyze_dataframe(frame, target=TargetPosition(3))
    with pytest.raises(ValueError, match="not found"):
        analyze_dataframe(frame, target="missing")
    with pytest.raises(ValueError, match="non-negative"):
        TargetPosition(True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-negative"):
        TargetPosition(-1)


def test_bad_selector_does_not_start_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(dataset_module, "analyze_series", _fail)
    frame = pd.DataFrame({"amount": [1, 2, 3]})
    with pytest.raises(ValueError, match="not found"):
        analyze_dataframe(frame, target="missing")
    with pytest.raises(TypeError, match="column axis"):
        resolve_target_position("amount", "amount")  # type: ignore[arg-type]


def test_numeric_target_reuses_descriptive_analysis_and_population() -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, np.nan, np.inf, 4.0],
            "x": [1.0, 2.0, 3.0, 4.0],
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    target = analysis.target_analysis
    assert target is not None
    assert target.status is TargetStatus.SUPPORTED
    assert target.selected_type is SemanticType.NUMERIC
    assert target.confidence is None
    assert target.inference_source is None
    assert target.population == TargetPopulation(
        n_total_rows=4,
        n_target_non_missing=3,
        n_target_missing=1,
    )
    assert (
        target.population.n_target_non_missing + target.population.n_target_missing
        == analysis.n_rows
    )
    assert target.numeric_facts is analysis.columns[0].numeric_analysis
    assert target.numeric_facts is not None
    assert target.numeric_facts.finite_count == 2
    assert target.numeric_facts.finite_count < target.population.n_target_non_missing
    assert analysis.n_rows == 4
    assert analysis.relationship_analysis.relationships[0].n_total_rows == 4
    assert target.boolean_facts is None


def test_boolean_and_categorical_facts_match_retained_descriptions() -> None:
    frame = pd.DataFrame(
        {
            "flag": _flag([True, False, pd.NA, True]),
            "city": pd.Series(["a", "a", "b", None], dtype="category"),
            "amount": [1.0, 2.0, 3.0, 4.0],
        }
    )
    boolean = analyze_dataframe(frame, target="flag").target_analysis
    assert boolean is not None
    assert boolean.population == TargetPopulation(4, 3, 1)
    assert boolean.boolean_facts is not None
    assert boolean.boolean_facts.true_count == 2
    assert boolean.boolean_facts.false_count == 1
    assert boolean.boolean_facts.n_non_missing == 3
    assert boolean.boolean_facts.n_observed_classes == 2
    assert boolean.boolean_facts.largest_class_count == 2
    assert boolean.boolean_facts.smallest_class_count == 1
    assert boolean.boolean_facts.largest_class_values == (True,)
    assert boolean.boolean_facts.smallest_class_values == (False,)
    assert boolean.boolean_facts.largest_class_proportion == pytest.approx(2 / 3)
    assert boolean.boolean_facts.smallest_class_proportion == pytest.approx(1 / 3)

    without_target = analyze_dataframe(frame)
    targeted = analyze_dataframe(frame, target="city")
    categorical = targeted.target_analysis
    assert categorical is not None
    column = targeted.columns[1]
    assert without_target.columns[1].categorical_analysis is not None
    assert column.categorical_analysis == without_target.columns[1].categorical_analysis
    assert categorical.categorical_facts is column.categorical_analysis
    assert categorical.categorical_facts is not None
    assert [level.value for level in categorical.categorical_facts.levels] == ["a", "b"]
    assert [level.count for level in categorical.categorical_facts.levels] == [2, 1]
    detail = build_variables_summary(without_target).variables[1].detail
    assert detail is not None
    assert (
        categorical.categorical_facts.most_frequent_count == detail.most_frequent_count
    )
    assert categorical.categorical_facts.singleton_count == detail.singleton_count
    assert categorical.categorical_facts.most_frequent_proportion == (
        detail.most_frequent_ratio
    )
    assert (
        categorical.categorical_facts.n_non_missing
        == categorical.population.n_target_non_missing
    )
    assert "problem_type" not in categorical.__dataclass_fields__
    assert not any("balance" in name for name in categorical.__dataclass_fields__)


def test_zero_one_numeric_is_not_a_boolean_target() -> None:
    frame = pd.DataFrame({"y": [0, 1, 0, 1, 1], "x": [1.0, 2.0, 3.0, 4.0, 5.0]})
    target = analyze_dataframe(frame, target="y").target_analysis
    assert target is not None
    assert target.selected_type is SemanticType.NUMERIC
    assert target.status is TargetStatus.SUPPORTED
    assert target.boolean_facts is None
    assert target.numeric_facts is not None


def test_ineligible_and_unsupported_targets_keep_their_status() -> None:
    constant = analyze_dataframe(
        pd.DataFrame({"y": [1, 1, 1], "x": [1.0, 2.0, 3.0]}),
        target="y",
    ).target_analysis
    assert constant is not None
    assert constant.selected_type is SemanticType.CONSTANT
    assert constant.status is TargetStatus.INELIGIBLE
    assert constant.confidence is Confidence.HIGH
    assert constant.numeric_facts is None
    assert constant.relationships[0].coverage is SelectedPairCoverage.INELIGIBLE

    empty = analyze_dataframe(
        pd.DataFrame({"y": pd.Series([pd.NA, pd.NA], dtype="Int64")}),
        target="y",
    ).target_analysis
    assert empty is not None
    assert empty.selected_type is SemanticType.EMPTY
    assert empty.status is TargetStatus.INELIGIBLE
    assert empty.population == TargetPopulation(2, 0, 2)
    assert empty.relationships == ()

    identifier = analyze_dataframe(
        pd.DataFrame(
            {
                "y": pd.Series(_UUIDS, dtype="string"),
                "x": [1.0, 2.0, 3.0, 4.0],
            }
        ),
        target="y",
    ).target_analysis
    assert identifier is not None
    assert identifier.selected_type is SemanticType.IDENTIFIER
    assert identifier.status is TargetStatus.INELIGIBLE
    assert identifier.confidence is None
    assert identifier.relationships[0].coverage is SelectedPairCoverage.INELIGIBLE

    unresolved = analyze_dataframe(
        pd.DataFrame(
            {
                "y": pd.Series(["Amsterdam", "Berlin"], dtype="string"),
                "x": [1.0, 2.0],
            }
        ),
        target="y",
    ).target_analysis
    assert unresolved is not None
    assert unresolved.selected_type is None
    assert unresolved.resolution_status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert unresolved.status is TargetStatus.UNRESOLVED
    assert unresolved.confidence is None

    dated = _mixed_frame()
    datetime_target = analyze_dataframe(dated, target="when").target_analysis
    assert datetime_target is not None
    assert datetime_target.selected_type is SemanticType.DATETIME
    assert datetime_target.status is TargetStatus.UNSUPPORTED
    assert datetime_target.confidence is Confidence.HIGH
    assert datetime_target.numeric_facts is None
    families = {
        link.other_label: link.unimplemented_family
        for link in datetime_target.relationships
        if link.coverage is SelectedPairCoverage.UNIMPLEMENTED
    }
    assert families["amount"] is UnimplementedRelationshipFamily.DATETIME_NUMERIC
    assert families["city"] is UnimplementedRelationshipFamily.DATETIME_CATEGORICAL
    flag_link = next(
        link for link in datetime_target.relationships if link.other_label == "flag"
    )
    assert flag_link.coverage is SelectedPairCoverage.INELIGIBLE
    assert flag_link.relationship is None

    duration = analyze_dataframe(
        pd.DataFrame(
            {
                "y": pd.to_timedelta(["1 day", "2 days", "3 days"]),
                "x": [1.0, 2.0, 3.0],
            }
        ),
        target="y",
    ).target_analysis
    assert duration is not None
    assert duration.selected_type is SemanticType.TIMEDELTA
    assert duration.status is TargetStatus.UNSUPPORTED


def test_ambiguous_target_is_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def supported_identifier(*_args: object, **_kwargs: object) -> CandidateAssessment:
        return CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.SUPPORTED,
            supporting_evidence=(SemanticEvidence(statement="synthetic support"),),
        )

    monkeypatch.setattr(
        column_module,
        "assess_identifier_candidate",
        supported_identifier,
    )
    target = analyze_dataframe(
        pd.DataFrame({"y": [1, 2, 3], "x": [4, 5, 6]}),
        target="y",
    ).target_analysis
    assert target is not None
    assert target.resolution_status is ResolutionStatus.AMBIGUOUS
    assert target.selected_type is None
    assert target.status is TargetStatus.UNRESOLVED
    assert target.numeric_facts is None


def test_target_relationships_are_the_retained_records() -> None:
    frame = _mixed_frame()
    plain = analyze_dataframe(frame)
    analysis = analyze_dataframe(frame, target="flag")
    target = analysis.target_analysis
    assert target is not None
    assert analysis.relationship_analysis == plain.relationship_analysis
    assert [link.other_position for link in target.relationships] == [0, 2, 3, 4]
    calculated = [
        link
        for link in target.relationships
        if link.coverage is SelectedPairCoverage.CALCULATED
    ]
    unimplemented = [
        link
        for link in target.relationships
        if link.coverage is SelectedPairCoverage.UNIMPLEMENTED
    ]
    ineligible = [
        link
        for link in target.relationships
        if link.coverage is SelectedPairCoverage.INELIGIBLE
    ]
    assert [link.other_label for link in calculated] == ["amount"]
    assert [link.other_label for link in unimplemented] == ["city"]
    assert unimplemented[0].unimplemented_family is (
        UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN
    )
    assert {link.other_label for link in ineligible} == {"when", "code"}
    assert (
        target.n_calculated_relationships
        + target.n_unimplemented_relationships
        + target.n_ineligible_relationships
        == target.n_other_columns
        == analysis.n_columns - 1
    )
    link = calculated[0]
    retained = analysis.relationship_analysis.relationships[0]
    assert link.relationship is retained
    assert link.record_role is TargetRecordRole.BOOLEAN_GROUP
    assert link.target_side is TargetPhysicalSide.RIGHT
    frequentist = retained.mean_difference_test.frequentist
    assert link.relationship.mean_difference is retained.mean_difference
    assert link.relationship.mean_difference_test.frequentist.p_value == (
        frequentist.p_value
    )
    assert link.relationship.mean_difference_test.frequentist.adjusted_p_value == (
        frequentist.adjusted_p_value
    )
    assert frequentist.adjusted_p_value is not None


def test_relationships_stay_in_physical_order() -> None:
    generator = np.random.default_rng(32)
    weak = generator.normal(size=50)
    strong = np.linspace(0.0, 1.0, 50)
    target_values = strong * 10.0 + 0.01 * generator.normal(size=50)
    frame = pd.DataFrame({"weak": weak, "strong": strong, "y": target_values})
    analysis = analyze_dataframe(frame, target="y")
    target = analysis.target_analysis
    assert target is not None
    assert [link.other_label for link in target.relationships] == ["weak", "strong"]
    weak_link, strong_link = target.relationships
    assert weak_link.relationship is not None
    assert strong_link.relationship is not None
    weak_value = abs(weak_link.relationship.methods[0].estimate.value)
    strong_value = abs(strong_link.relationship.methods[0].estimate.value)
    assert strong_value > weak_value
    assert weak_link.other_position < strong_link.other_position


def test_numeric_boolean_orientation_keeps_true_minus_false() -> None:
    amount = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    flag = _flag([True, False, True, False, True, False])
    numeric_first = pd.DataFrame({"amount": amount, "flag": flag})
    boolean_first = pd.DataFrame({"flag": flag, "amount": amount})
    boolean_on_right = analyze_dataframe(numeric_first, target="flag").target_analysis
    numeric_on_left = analyze_dataframe(numeric_first, target="amount").target_analysis
    boolean_on_left = analyze_dataframe(boolean_first, target="flag").target_analysis
    assert boolean_on_right is not None
    assert numeric_on_left is not None
    assert boolean_on_left is not None
    right_link = boolean_on_right.relationships[0]
    left_link = boolean_on_left.relationships[0]
    numeric_link = numeric_on_left.relationships[0]
    assert right_link.record_role is TargetRecordRole.BOOLEAN_GROUP
    assert right_link.target_side is TargetPhysicalSide.RIGHT
    assert left_link.record_role is TargetRecordRole.BOOLEAN_GROUP
    assert left_link.target_side is TargetPhysicalSide.LEFT
    assert numeric_link.record_role is TargetRecordRole.NUMERIC
    assert numeric_link.target_side is TargetPhysicalSide.LEFT
    right_value = right_link.relationship.mean_difference.value
    left_value = left_link.relationship.mean_difference.value
    numeric_value = numeric_link.relationship.mean_difference.value
    assert right_value == left_value == numeric_value
    assert right_link.relationship.contrast.value == "true_minus_false"


def test_boolean_boolean_orientation_keeps_conditioning_and_outcome() -> None:
    frame = pd.DataFrame(
        {
            "left": _flag([True, True, False, False, True, False]),
            "right": _flag([True, False, True, False, True, True]),
        }
    )
    by_left = analyze_dataframe(frame, target="left")
    by_right = analyze_dataframe(frame, target="right")
    left_target = by_left.target_analysis
    right_target = by_right.target_analysis
    assert left_target is not None
    assert right_target is not None
    left_link = left_target.relationships[0]
    right_link = right_target.relationships[0]
    assert left_link.record_role is TargetRecordRole.CONDITIONING
    assert left_link.target_side is TargetPhysicalSide.LEFT
    assert right_link.record_role is TargetRecordRole.OUTCOME
    assert right_link.target_side is TargetPhysicalSide.RIGHT
    assert left_link.relationship is by_left.relationship_analysis.relationships[0]
    assert right_link.relationship is by_right.relationship_analysis.relationships[0]
    left_difference = left_link.relationship.probability_difference.value
    right_difference = right_link.relationship.probability_difference.value
    assert left_difference == (
        by_left.relationship_analysis.relationships[0].probability_difference.value
    )
    assert right_difference == (
        by_right.relationship_analysis.relationships[0].probability_difference.value
    )
    assert left_difference == right_difference


def test_symmetric_roles_follow_physical_side() -> None:
    frame = pd.DataFrame(
        {
            "left": [1.0, 2.0, 3.0, 4.0],
            "right": [1.0, 2.0, 4.0, 8.0],
        }
    )
    left = analyze_dataframe(frame, target="left").target_analysis
    right = analyze_dataframe(frame, target="right").target_analysis
    assert left is not None and right is not None
    assert left.relationships[0].record_role is TargetRecordRole.SYMMETRIC_LEFT
    assert right.relationships[0].record_role is TargetRecordRole.SYMMETRIC_RIGHT
    cities = pd.DataFrame(
        {
            "left": pd.Series(["a", "a", "b", "b"], dtype="category"),
            "right": pd.Series(["x", "y", "x", "y"], dtype="category"),
        }
    )
    categorical = analyze_dataframe(cities, target="right").target_analysis
    assert categorical is not None
    assert categorical.relationships[0].record_role is TargetRecordRole.SYMMETRIC_RIGHT


def test_numeric_categorical_role_follows_the_target() -> None:
    frame = pd.DataFrame(
        {
            "city": pd.Series(["a", "a", "b", "b"], dtype="category"),
            "amount": [1.0, 2.0, 3.0, 4.0],
        }
    )
    categorical = analyze_dataframe(frame, target="city").target_analysis
    numeric = analyze_dataframe(frame, target="amount").target_analysis
    assert categorical is not None and numeric is not None
    assert categorical.relationships[0].record_role is TargetRecordRole.CATEGORICAL
    assert numeric.relationships[0].record_role is TargetRecordRole.NUMERIC
    city = analyze_dataframe(frame, target="city")
    assert city.target_analysis is not None
    assert (
        city.target_analysis.relationships[0].relationship
        is city.relationship_analysis.relationships[0]
    )


def test_requesting_a_target_does_not_rerun_relationship_calculation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _mixed_frame()
    counts = {"calls": 0, "adjustments": 0}
    original_analyze = collector_module._analyze_numeric_boolean
    original_adjust = collector_module.adjust_primary_p_values

    def spy_analyze(*args: object, **kwargs: object) -> object:
        counts["calls"] += 1
        return original_analyze(*args, **kwargs)

    def spy_adjust(records: object) -> object:
        counts["adjustments"] += 1
        return original_adjust(records)

    monkeypatch.setattr(collector_module, "_analyze_numeric_boolean", spy_analyze)
    monkeypatch.setattr(collector_module, "adjust_primary_p_values", spy_adjust)
    plain = analyze_dataframe(frame)
    once = counts["calls"]
    adjustments = counts["adjustments"]
    assert once > 0
    assert adjustments == 1
    counts["calls"] = 0
    counts["adjustments"] = 0
    targeted = analyze_dataframe(frame, target="flag")
    assert counts["calls"] == once
    assert counts["adjustments"] == 1
    assert targeted.relationship_analysis == plain.relationship_analysis
    counts["calls"] = 0
    counts["adjustments"] = 0
    projected = project_target_analysis(
        targeted.columns,
        targeted.relationship_analysis.relationships,
        position=1,
        n_rows=targeted.n_rows,
    )
    assert counts["calls"] == 0
    assert counts["adjustments"] == 0
    assert projected == targeted.target_analysis


def test_summary_copies_facts_after_calculators_are_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = analyze_dataframe(_mixed_frame(), target="amount")
    monkeypatch.setattr(collector_module, "_read_numeric_column", _fail)
    monkeypatch.setattr(collector_module, "_read_categorical_column", _fail)
    monkeypatch.setattr(collector_module, "_read_boolean_column", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_categorical", _fail)
    monkeypatch.setattr(collector_module, "_analyze_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_categorical_categorical", _fail)
    monkeypatch.setattr(collector_module, "collect_relationship_analysis", _fail)
    monkeypatch.setattr(collector_module, "adjust_primary_p_values", _fail)
    monkeypatch.setattr(adjustment_module, "adjust_primary_p_values", _fail)
    monkeypatch.setattr(column_module, "analyze_series", _fail)
    monkeypatch.setattr(column_module, "resolve_semantics", _fail)
    monkeypatch.setattr(numeric_module, "collect_numeric_descriptive_analysis", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(target_module, "project_target_analysis", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    summary = build_target_summary(analysis)
    retained = analysis.target_analysis
    assert summary is not None and retained is not None
    assert summary.position == retained.position
    assert summary.status is retained.status
    assert summary.population == retained.population
    assert summary.numeric_facts == retained.numeric_facts
    assert summary.numeric_facts is not retained.numeric_facts
    copied = summary.relationships[0].relationship
    retained_record = retained.relationships[0].relationship
    assert copied == retained_record
    assert copied is not retained_record
    assert copied.mean_difference_test.frequentist.p_value == (
        retained_record.mean_difference_test.frequentist.p_value
    )
    assert copied.mean_difference_test.frequentist.adjusted_p_value == (
        retained_record.mean_difference_test.frequentist.adjusted_p_value
    )
    _assert_no_source(summary)
    _assert_no_source(retained)
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_target_summary(analysis.columns)


def test_target_projection_rejects_inconsistent_records() -> None:
    frame = pd.DataFrame(
        {"y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 4.0], "z": [2.0, 3.0, 4.0]}
    )
    analysis = analyze_dataframe(frame, target="y")
    target = analysis.target_analysis
    assert target is not None
    with pytest.raises(ValueError, match="must reconcile"):
        TargetPopulation(3, 2, 2)
    with pytest.raises(ValueError, match="outside the column axis"):
        project_target_analysis(
            analysis.columns,
            analysis.relationship_analysis.relationships,
            position=3,
            n_rows=analysis.n_rows,
        )
    with pytest.raises(TypeError, match="tuple"):
        project_target_analysis(
            list(analysis.columns),  # type: ignore[arg-type]
            analysis.relationship_analysis.relationships,
            position=0,
            n_rows=analysis.n_rows,
        )
    record = analysis.relationship_analysis.relationships[0]
    with pytest.raises(ValueError, match="unique"):
        project_target_analysis(
            analysis.columns,
            (record, record),
            position=0,
            n_rows=analysis.n_rows,
        )
    with pytest.raises(ValueError, match="retained descriptive analysis"):
        DatasetAnalysis(
            n_rows=analysis.n_rows,
            n_columns=analysis.n_columns,
            n_cells=analysis.n_cells,
            columns=analysis.columns,
            missing_analysis=analysis.missing_analysis,
            duplicate_analysis=analysis.duplicate_analysis,
            relationship_analysis=analysis.relationship_analysis,
            target_analysis=dataclasses.replace(
                target,
                numeric_facts=NumericDescriptiveAnalysis(
                    finite_count=target.numeric_facts.finite_count,
                    minimum=target.numeric_facts.minimum,
                    maximum=target.numeric_facts.maximum,
                    mean=target.numeric_facts.mean,
                    median=target.numeric_facts.median,
                    standard_deviation=target.numeric_facts.standard_deviation,
                    q1=target.numeric_facts.q1,
                    q3=target.numeric_facts.q3,
                ),
            ),
        )
    with pytest.raises(ValueError, match="ascending"):
        dataclasses.replace(
            target,
            relationships=tuple(reversed(target.relationships)),
        )
    with pytest.raises(ValueError, match="descriptive facts"):
        dataclasses.replace(
            target,
            status=TargetStatus.INELIGIBLE,
            selected_type=SemanticType.CONSTANT,
            confidence=Confidence.HIGH,
            inference_source=InferenceSource.INFERRED,
        )
    with pytest.raises(ValueError, match="confidence and inference source"):
        dataclasses.replace(target, confidence=Confidence.HIGH)
    link = target.relationships[0]
    with pytest.raises(ValueError, match="calculated target link"):
        dataclasses.replace(link, relationship=None, record_role=None)
    with pytest.raises(ValueError, match="target side"):
        dataclasses.replace(
            target,
            relationships=(
                dataclasses.replace(link, target_side=TargetPhysicalSide.RIGHT),
            ),
        )
    with pytest.raises(ValueError, match="target role"):
        dataclasses.replace(
            target,
            relationships=(
                dataclasses.replace(link, record_role=TargetRecordRole.SYMMETRIC_RIGHT),
            ),
        )


def test_supported_target_requires_its_retained_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        column_module, "collect_numeric_descriptive_analysis", _fail_none
    )
    with pytest.raises(ValueError, match="retained numeric description"):
        analyze_dataframe(pd.DataFrame({"y": [1, 2, 3]}), target="y")

    monkeypatch.setattr(column_module, "collect_frequency_evidence", _fail_none)
    with pytest.raises(ValueError, match="retained frequency evidence"):
        analyze_dataframe(
            pd.DataFrame({"y": pd.Series(["a", "b", "a"], dtype="category")}),
            target="y",
        )


def _fail_none(*_args: object, **_kwargs: object) -> None:
    return None


def test_pair_classification_rejects_inconsistent_family_metadata() -> None:
    with pytest.raises(ValueError, match="names its recognized family"):
        SelectedPairClass(coverage=SelectedPairCoverage.UNIMPLEMENTED)
    with pytest.raises(ValueError, match="only an unimplemented pair"):
        SelectedPairClass(
            coverage=SelectedPairCoverage.CALCULATED,
            unimplemented_family=UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN,
        )
    with pytest.raises(TypeError, match="SemanticType"):
        classify_selected_pair("numeric", SemanticType.NUMERIC)  # type: ignore[arg-type]
    classified = classify_selected_pair(SemanticType.DATETIME, SemanticType.BOOLEAN)
    assert classified.coverage is SelectedPairCoverage.INELIGIBLE
    assert classified.unimplemented_family is None
    calculated = classify_selected_pair(SemanticType.NUMERIC, SemanticType.BOOLEAN)
    assert calculated.coverage is SelectedPairCoverage.CALCULATED


def test_public_profile_is_not_the_target_analysis_entry_point() -> None:
    import pytics
    from pytics.profiler import profile

    assert "analyze_dataframe" not in pytics.__all__
    assert "target" in profile.__code__.co_varnames
    assert not hasattr(pytics.profiler, "analyze_dataframe")


def test_summaries_for_each_supported_kind_copy_only_that_kind() -> None:
    numeric = analyze_dataframe(
        pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 4.0]}),
        target="y",
    )
    boolean = analyze_dataframe(
        pd.DataFrame(
            {
                "y": _flag([True, False, True, False]),
                "x": [1.0, 2.0, 3.0, 4.0],
            }
        ),
        target="y",
    )
    categorical = analyze_dataframe(
        pd.DataFrame(
            {
                "y": pd.Series(["a", "a", "b"], dtype="category"),
                "x": [1.0, 2.0, 3.0],
            }
        ),
        target="y",
    )
    unsupported = analyze_dataframe(
        pd.DataFrame(
            {
                "y": pd.to_datetime(["2020-01-01", "2020-01-02"]),
                "x": [1.0, 2.0],
            }
        ),
        target="y",
    )
    for analysis in (numeric, boolean, categorical, unsupported):
        summary = build_target_summary(analysis)
        retained = analysis.target_analysis
        assert summary is not None and retained is not None
        assert summary.n_other_columns == retained.n_other_columns
        assert summary.n_calculated_relationships == retained.n_calculated_relationships
        assert summary.n_unimplemented_relationships == (
            retained.n_unimplemented_relationships
        )
        assert summary.n_ineligible_relationships == retained.n_ineligible_relationships
        assert summary.numeric_facts == retained.numeric_facts
        assert summary.boolean_facts == retained.boolean_facts
        assert summary.categorical_facts == retained.categorical_facts
        if retained.numeric_facts is not None:
            assert summary.numeric_facts is not retained.numeric_facts
        if retained.boolean_facts is not None:
            assert summary.boolean_facts is not retained.boolean_facts
        if retained.categorical_facts is not None:
            assert summary.categorical_facts is not retained.categorical_facts


def test_boolean_target_requires_retained_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        column_module,
        "collect_boolean_descriptive_analysis",
        _fail_none,
    )
    with pytest.raises(ValueError, match="retained boolean description"):
        analyze_dataframe(
            pd.DataFrame({"y": _flag([True, False, True])}),
            target="y",
        )


def test_label_resolution_rejects_ambiguous_equality() -> None:
    sentinel = object()
    assert resolve_target_position((sentinel,), sentinel) == 0
    assert resolve_target_position((np.True_,), True) == 0
    with pytest.raises(ValueError, match="not found"):
        resolve_target_position((np.True_,), False)
    with pytest.raises(ValueError, match="not found"):
        resolve_target_position((np.array([1, 2]),), np.array([1, 2]))

    class _Odd:
        def __eq__(self, other: object) -> str:
            return "neither"

    with pytest.raises(ValueError, match="not found"):
        resolve_target_position((_Odd(),), _Odd())

    class _Unequal:
        def __eq__(self, other: object) -> bool:
            raise TypeError("labels are not comparable")

    with pytest.raises(ValueError, match="not found"):
        resolve_target_position((_Unequal(),), _Unequal())
    with pytest.raises(TypeError, match="column axis"):
        resolve_target_position(object(), "y")  # type: ignore[arg-type]


def test_boolean_facts_must_match_the_target_population() -> None:
    frame = pd.DataFrame(
        {
            "flag": _flag([True, False, True, False]),
            "amount": [1.0, 2.0, 3.0, 4.0],
        }
    )
    target = analyze_dataframe(frame, target="flag").target_analysis
    assert target is not None
    with pytest.raises(ValueError, match="boolean counts"):
        dataclasses.replace(
            target,
            boolean_facts=BooleanDescriptiveAnalysis(true_count=1, false_count=0),
        )
    with pytest.raises(ValueError, match="categorical facts only"):
        dataclasses.replace(
            target,
            selected_type=SemanticType.CATEGORICAL,
            confidence=None,
            inference_source=None,
            boolean_facts=None,
            numeric_facts=None,
            categorical_facts=None,
        )


def test_attachment_and_record_guards() -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, 4.0],
            "x": [1.0, 2.0, 4.0, 8.0],
            "z": [2.0, 3.0, 4.0, 5.0],
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    target = analysis.target_analysis
    assert target is not None
    fields = dict(
        n_rows=analysis.n_rows,
        n_columns=analysis.n_columns,
        n_cells=analysis.n_cells,
        columns=analysis.columns,
        missing_analysis=analysis.missing_analysis,
        duplicate_analysis=analysis.duplicate_analysis,
        relationship_analysis=analysis.relationship_analysis,
    )
    with pytest.raises(TypeError, match="TargetAnalysis"):
        DatasetAnalysis(**fields, target_analysis="y")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must match the selected column"):
        DatasetAnalysis(
            **fields, target_analysis=dataclasses.replace(target, label="z")
        )
    copied_boolean = analyze_dataframe(
        pd.DataFrame(
            {
                "flag": _flag([True, False, True, False]),
                "amount": [1.0, 2.0, 3.0, 4.0],
            }
        ),
        target="flag",
    )
    boolean_target = copied_boolean.target_analysis
    assert boolean_target is not None and boolean_target.boolean_facts is not None
    with pytest.raises(ValueError, match="boolean target facts"):
        DatasetAnalysis(
            n_rows=copied_boolean.n_rows,
            n_columns=copied_boolean.n_columns,
            n_cells=copied_boolean.n_cells,
            columns=copied_boolean.columns,
            missing_analysis=copied_boolean.missing_analysis,
            duplicate_analysis=copied_boolean.duplicate_analysis,
            relationship_analysis=copied_boolean.relationship_analysis,
            target_analysis=dataclasses.replace(
                boolean_target,
                boolean_facts=BooleanDescriptiveAnalysis(
                    true_count=boolean_target.boolean_facts.true_count,
                    false_count=boolean_target.boolean_facts.false_count,
                ),
            ),
        )
    summary = build_target_summary(analysis)
    assert summary is not None
    copied_link = dataclasses.replace(
        target.relationships[0],
        relationship=summary.relationships[0].relationship,
    )
    with pytest.raises(ValueError, match="retained relationship record"):
        DatasetAnalysis(
            **fields,
            target_analysis=dataclasses.replace(
                target,
                relationships=(copied_link, target.relationships[1]),
            ),
        )
    with pytest.raises(ValueError, match="column position"):
        project_target_analysis(
            (analysis.columns[1], analysis.columns[0], analysis.columns[2]),
            analysis.relationship_analysis.relationships,
            position=0,
            n_rows=analysis.n_rows,
        )
    with pytest.raises(ValueError, match="n_total"):
        project_target_analysis(
            analysis.columns,
            analysis.relationship_analysis.relationships,
            position=0,
            n_rows=analysis.n_rows + 1,
        )
    with pytest.raises(TypeError, match="ColumnAnalysis"):
        project_target_analysis(
            ("column",),  # type: ignore[arg-type]
            (),
            position=0,
            n_rows=0,
        )
    with pytest.raises(TypeError, match="tuple"):
        project_target_analysis(
            analysis.columns,
            [analysis.relationship_analysis.relationships[0]],  # type: ignore[arg-type]
            position=0,
            n_rows=analysis.n_rows,
        )
    with pytest.raises(TypeError, match="calculated relationship"):
        project_target_analysis(
            analysis.columns,
            ("record",),  # type: ignore[arg-type]
            position=0,
            n_rows=analysis.n_rows,
        )
    with pytest.raises(TypeError, match="status"):
        dataclasses.replace(target, status="supported")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="selected semantic state"):
        dataclasses.replace(target, status=TargetStatus.INELIGIBLE)
    with pytest.raises(ValueError, match="no confidence"):
        dataclasses.replace(
            target,
            confidence=Confidence.HIGH,
            inference_source=InferenceSource.INFERRED,
        )
    with pytest.raises(ValueError, match="relationship record"):
        project_target_analysis(
            analysis.columns,
            (),
            position=0,
            n_rows=analysis.n_rows,
        )
    with pytest.raises(ValueError, match="keeps its confidence"):
        dataclasses.replace(
            target,
            selected_type=SemanticType.BOOLEAN,
            confidence=None,
            inference_source=None,
        )
    with pytest.raises(ValueError, match="only a supported target"):
        dataclasses.replace(
            target,
            selected_type=SemanticType.DATETIME,
            status=TargetStatus.UNSUPPORTED,
            confidence=Confidence.HIGH,
            inference_source=InferenceSource.PHYSICAL_DTYPE,
        )
    with pytest.raises(ValueError, match="numeric facts only"):
        dataclasses.replace(
            target,
            boolean_facts=BooleanDescriptiveAnalysis(true_count=1, false_count=1),
        )
    assert target.numeric_facts is not None
    with pytest.raises(ValueError, match="cannot exceed"):
        dataclasses.replace(
            target,
            numeric_facts=dataclasses.replace(
                target.numeric_facts,
                finite_count=target.population.n_target_non_missing + 1,
            ),
        )
    with pytest.raises(ValueError, match="boolean facts only"):
        dataclasses.replace(
            boolean_target,
            numeric_facts=target.numeric_facts,
        )
    categorical = analyze_dataframe(
        pd.DataFrame(
            {
                "city": pd.Series(["a", "a", "b", "b"], dtype="category"),
                "amount": [1.0, 2.0, 3.0, 4.0],
            }
        ),
        target="city",
    ).target_analysis
    assert categorical is not None and categorical.categorical_facts is not None
    with pytest.raises(ValueError, match="target population"):
        dataclasses.replace(
            categorical,
            categorical_facts=CategoricalDescriptiveAnalysis(
                n_non_missing=1,
                ordered=False,
                levels=(ObservedCategoryCount(value="a", count=1),),
            ),
        )
    calculated = target.relationships[0]
    with pytest.raises(ValueError, match="selected semantic pair"):
        dataclasses.replace(
            target,
            relationships=(
                dataclasses.replace(
                    calculated,
                    coverage=SelectedPairCoverage.INELIGIBLE,
                    relationship=None,
                    record_role=None,
                ),
                target.relationships[1],
            ),
        )
    dated = analyze_dataframe(
        pd.DataFrame(
            {
                "when": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
                "amount": [1.0, 2.0, 3.0],
            }
        ),
        target="when",
    ).target_analysis
    assert dated is not None
    with pytest.raises(ValueError, match="recognized family"):
        dataclasses.replace(
            dated,
            relationships=(
                dataclasses.replace(
                    dated.relationships[0],
                    unimplemented_family=(
                        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL
                    ),
                ),
            ),
        )
    with pytest.raises(ValueError, match="target pair"):
        dataclasses.replace(
            target,
            relationships=(
                dataclasses.replace(
                    target.relationships[0],
                    relationship=target.relationships[1].relationship,
                ),
                target.relationships[1],
            ),
        )
    with pytest.raises(TypeError, match="tuple"):
        dataclasses.replace(target, relationships=[calculated])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TargetRelationship"):
        dataclasses.replace(target, relationships=("link",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot name the target"):
        dataclasses.replace(
            target,
            relationships=(
                dataclasses.replace(calculated, other_position=target.position),
            ),
        )
    with pytest.raises(ValueError, match="selected semantic type"):
        TargetRelationship(
            other_position=1,
            other_label="x",
            other_selected_type=None,
            other_resolution_status=ResolutionStatus.RESOLVED,
            coverage=SelectedPairCoverage.INELIGIBLE,
            unimplemented_family=None,
            target_side=TargetPhysicalSide.LEFT,
            record_role=None,
            relationship=None,
        )
    with pytest.raises(ValueError, match="no selected semantic type"):
        TargetRelationship(
            other_position=1,
            other_label="x",
            other_selected_type=SemanticType.NUMERIC,
            other_resolution_status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
            coverage=SelectedPairCoverage.INELIGIBLE,
            unimplemented_family=None,
            target_side=TargetPhysicalSide.LEFT,
            record_role=None,
            relationship=None,
        )
    with pytest.raises(ValueError, match="only a calculated"):
        dataclasses.replace(
            calculated,
            coverage=SelectedPairCoverage.INELIGIBLE,
            record_role=TargetRecordRole.SYMMETRIC_LEFT,
        )
    with pytest.raises(TypeError, match="coverage"):
        dataclasses.replace(calculated, coverage="calculated")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="other_selected_type"):
        dataclasses.replace(
            calculated,
            other_selected_type="numeric",  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="coverage"):
        SelectedPairClass(coverage="calculated")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="SemanticType"):
        classify_selected_pair(SemanticType.NUMERIC, "boolean")  # type: ignore[arg-type]
