"""TSK-048: unhashable distinct counts and unavailable duplicate analysis."""

from __future__ import annotations

import decimal
import uuid
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import pytics.analysis.duplicate as duplicate_module
import pytics.analysis.relationships.numeric_categorical as numeric_categorical_module
import pytics.analysis.target_diagnostic_fit as diagnostic_fit_module
import pytics.analysis.target_leakage as leakage_module
import pytics.semantics.string_structure_evidence as string_module
from pytics import compare
from pytics import profile
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.numeric import _from_finite
from pytics.analysis.relationship import CategoricalCategoricalRelationship
from pytics.analysis.relationship import CategoricalGroupSummary
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericCategoricalRelationship
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.target import TargetStatus
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import PredictorDecision
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


def _frame(payload: list) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [20, 30, 40, 50],
            "payload": payload,
        }
    )


@pytest.mark.parametrize(
    "payload",
    [
        [[1, 2], [3], [4, 5], [6]],
        [{"a": 1}, {"b": 2}, {"a": 1}, {"c": 3}],
        ["a", ["b"], "c", "d"],
    ],
)
def test_unhashable_column_abstains_and_keeps_the_neighbor(payload: list) -> None:
    frame = _frame(payload)
    original = frame.copy(deep=True)

    result = profile(frame)

    pd.testing.assert_frame_equal(frame, original)
    age = result.variables.by_label("age")
    column = result.variables.by_label("payload")
    assert age.selected_type is SemanticType.NUMERIC
    assert column.selected_type is None
    assert column.resolution_status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert column.record.inferred.resolution.reason == (
        "Exact distinct values are unavailable."
    )
    assert column.record.evidence.basic.n_non_missing == 4
    assert column.record.evidence.basic.n_unique_non_missing is None
    assert column.record.evidence.basic.is_constant is False
    assert column.record.evidence.basic.unique_ratio_non_missing is None
    assert column.record.categorical_analysis is None
    assert result.duplicates.available is False
    assert result.duplicates.n_duplicate_groups is None
    assert all(item.code is not FindingCode.DUPLICATE_ROWS for item in result.findings)


def test_eligible_relationship_survives_an_unhashable_column() -> None:
    frame = pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0],
            "y": [2.0, 3.0, 4.0, 5.0],
            "payload": [[1], [2], [3], [4]],
        }
    )

    result = profile(frame)

    assert len(result.relationships) == 1
    assert result.relationships.between_labels("x", "y").family.value == (
        "numeric_numeric"
    )
    assert result.relationships.analysis.n_ineligible_pairs == 2
    with pytest.raises(KeyError):
        result.relationships.between_labels("x", "payload")


def test_unhashable_target_stays_unresolved() -> None:
    frame = pd.DataFrame(
        {
            "age": [20, 30, 40, 50],
            "payload": [[1], [2], [3], [4]],
        }
    )

    result = profile(frame, target="payload")

    assert result.target.status is TargetStatus.UNRESOLVED
    assert result.target.diagnostic is not None
    assert result.target.diagnostic.status is DiagnosticStatus.TARGET_TYPE_UNSUPPORTED
    assert result.variables.by_label("age").selected_type is SemanticType.NUMERIC


def test_known_duplicates_stay_available() -> None:
    frame = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})

    result = profile(frame)

    assert result.duplicates.available is True
    assert result.duplicates.n_duplicate_groups == 1
    assert result.duplicates.n_unique_rows(3) == 2
    assert any(item.code is FindingCode.DUPLICATE_ROWS for item in result.findings)


def test_fewer_than_two_rows_is_a_real_empty_duplicate_result() -> None:
    frame = pd.DataFrame({"payload": [[1, 2]]})

    result = profile(frame)

    assert result.duplicates.available is True
    assert result.duplicates.duplicate_groups == ()
    assert result.duplicates.n_duplicate_groups == 0
    assert result.duplicates.n_unique_rows(1) == 1
    assert result.variables[0].record.evidence.basic.n_unique_non_missing is None
    assert result.variables[0].selected_type is None


def test_unexpected_distinct_count_type_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(self: pd.Series, dropna: bool = True) -> int:
        del self, dropna
        raise TypeError("unhashable unexpected internal bug")

    monkeypatch.setattr(pd.Series, "nunique", boom)
    with pytest.raises(TypeError, match="unexpected internal bug"):
        profile(pd.DataFrame({"age": [1, 2, 3]}))


def test_unexpected_factorize_type_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise TypeError("unhashable unexpected internal bug")

    monkeypatch.setattr(duplicate_module.pd, "factorize", boom)
    with pytest.raises(TypeError, match="unexpected internal bug"):
        profile(pd.DataFrame({"age": [1, 2, 3]}))


def test_unexpected_string_structure_type_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_value: object) -> None:
        raise TypeError("unexpected bug")

    monkeypatch.setattr(string_module, "_observe_string", boom)
    with pytest.raises(TypeError, match="unexpected bug"):
        profile(pd.DataFrame({"text": ["alpha", "beta", "alpha"]}))


def test_bytes_column_still_skips_string_structure() -> None:
    frame = pd.DataFrame({"b": [b"a", b"b", b"a"], "n": [1, 2, 3]})

    result = profile(frame)

    column = result.variables.by_label("b")
    assert column.selected_type is None
    assert column.resolution_status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert column.record.evidence.string_structure is None
    assert column.record.evidence.basic.n_unique_non_missing == 2
    assert result.duplicates.available is True
    assert result.variables.by_label("n").selected_type is SemanticType.NUMERIC


def test_unavailable_duplicates_are_not_shown_as_zero() -> None:
    result = profile(_frame([[1], [2], [1], [2]]))

    html = result._repr_html_()
    assert "Exact duplicate groups" in html
    assert "Unavailable" in html
    assert "Excess duplicate rows" not in html

    compared = compare(
        _frame([[1], [2], [1], [2]]),
        _frame([[3], [4], [5], [6]]),
    )
    compared_html = compared._repr_html_()
    assert "Unavailable" in compared_html
    assert compared.overview.n_duplicate_groups.reference is None
    assert compared.overview.n_duplicate_groups.comparison is None
    assert compared.overview.n_duplicate_groups.change is None
    assert compared.overview.n_unique_rows.reference is None


_VOCABULARY = UnavailabilityReason.CATEGORY_VOCABULARY_NOT_RETAINABLE


class _Token:
    """Hashable category scalar outside the closed relationship vocabulary."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Token) and self.name == other.name


def _assert_vocabulary_withheld(record: object, n_paired: int) -> None:
    assert record.n_paired == n_paired  # type: ignore[attr-defined]
    if isinstance(record, NumericCategoricalRelationship):
        assert record.groups == ()
        components = (
            record.effect,
            record.corrected_effect,
        )
        for component in components:
            assert component.availability is ResultAvailability.UNAVAILABLE
            assert component.value is None
            assert component.reason is _VOCABULARY
        assert record.omnibus.statistic is None
        assert record.omnibus.statistic_reason is _VOCABULARY
        frequentist = record.omnibus.frequentist
    elif isinstance(record, CategoricalCategoricalRelationship):
        assert record.table.left_levels == ()
        assert record.table.right_levels == ()
        assert record.table.observed_counts == ()
        for component in (record.association, record.corrected_association):
            assert component.availability is ResultAvailability.UNAVAILABLE
            assert component.value is None
            assert component.reason is _VOCABULARY
        assert record.expected_counts.availability is ResultAvailability.UNAVAILABLE
        assert record.expected_counts.reason is _VOCABULARY
        assert record.independence.statistic is None
        assert record.independence.statistic_reason is _VOCABULARY
        frequentist = record.independence.frequentist
    else:
        raise AssertionError("withheld vocabulary belongs to a categorical family")
    assert frequentist.availability is ResultAvailability.UNAVAILABLE
    assert frequentist.p_value is None
    assert frequentist.adjusted_p_value is None
    assert frequentist.reason is _VOCABULARY
    assert frequentist.adjustment is MultipleTestingAdjustment.NOT_APPLIED


def test_decimal_categorical_relationship_keeps_the_profile() -> None:
    """A Decimal vocabulary is described and is not stored on the relationship."""
    frame = pd.DataFrame(
        {
            "x": pd.Categorical(
                [
                    decimal.Decimal("1.0"),
                    decimal.Decimal("2.0"),
                    decimal.Decimal("1.0"),
                    None,
                ]
            ),
            "y": [1.0, 2.0, float("nan"), 4.0],
        }
    )
    original = frame.copy(deep=True)

    result = profile(frame)

    pd.testing.assert_frame_equal(frame, original)
    column = result.variables.by_label("x")
    assert column.selected_type is SemanticType.CATEGORICAL
    assert result.variables.by_label("y").selected_type is SemanticType.NUMERIC
    levels = tuple(level.value for level in column.record.categorical_analysis.levels)
    assert levels == (decimal.Decimal("1.0"), decimal.Decimal("2.0"))
    assert all(type(level) is decimal.Decimal for level in levels)
    analysis = result.relationships.analysis
    assert analysis.n_analyzed_pairs == analysis.n_supported_pairs == 1
    record = result.relationships.between_labels("x", "y")
    _assert_vocabulary_withheld(record, n_paired=2)


@pytest.mark.parametrize(
    "categories",
    [
        [
            uuid.UUID(int=1),
            uuid.UUID(int=2),
            uuid.UUID(int=1),
        ],
        [_Token("a"), _Token("b"), _Token("a")],
    ],
)
def test_unretainable_hashable_categories_withhold_the_relationship(
    categories: list,
) -> None:
    frame = pd.DataFrame(
        {
            "group": pd.Categorical(categories),
            "y": [1.0, 2.0, 3.0],
        }
    )

    result = profile(frame)

    record = result.relationships.between_labels("group", "y")
    _assert_vocabulary_withheld(record, n_paired=3)
    assert result.relationships.analysis.n_analyzed_pairs == (
        result.relationships.analysis.n_supported_pairs
    )


def test_unused_unretainable_level_withholds_the_relationship() -> None:
    frame = pd.DataFrame(
        {
            "group": pd.Categorical(
                ["a", "b", "a"],
                categories=["a", "b", decimal.Decimal("9")],
            ),
            "y": [1.0, 2.0, 3.0],
        }
    )

    result = profile(frame)

    levels = result.variables.by_label("group").record.categorical_analysis.levels
    assert tuple(level.value for level in levels) == ("a", "b")
    record = result.relationships.between_labels("group", "y")
    _assert_vocabulary_withheld(record, n_paired=3)


def test_pairs_that_avoid_the_unretainable_column_stay_calculated() -> None:
    frame = pd.DataFrame(
        {
            "n1": [1.0, 2.0, 3.0, 4.0],
            "n2": [1.0, 2.0, 3.0, 5.0],
            "labels": pd.Categorical(["a", "a", "b", "b"]),
            "other": pd.Categorical(["x", "x", "y", "y"]),
            "amounts": pd.Categorical(
                [
                    decimal.Decimal("1"),
                    decimal.Decimal("1"),
                    decimal.Decimal("2"),
                    decimal.Decimal("2"),
                ]
            ),
        }
    )

    result = profile(frame)

    analysis = result.relationships.analysis
    assert analysis.n_analyzed_pairs == analysis.n_supported_pairs == 10
    numeric = result.relationships.between_labels("n1", "n2")
    assert isinstance(numeric, NumericNumericRelationship)
    assert numeric.spearman.estimate.availability is ResultAvailability.AVAILABLE
    labels = result.relationships.between_labels("n1", "labels")
    assert isinstance(labels, NumericCategoricalRelationship)
    assert labels.effect.availability is ResultAvailability.AVAILABLE
    assert labels.groups[0].category == "a"
    strings = result.relationships.between_labels("labels", "other")
    assert isinstance(strings, CategoricalCategoricalRelationship)
    assert strings.association.availability is ResultAvailability.AVAILABLE
    assert strings.association.value == 1.0
    _assert_vocabulary_withheld(
        result.relationships.between_labels("n1", "amounts"),
        n_paired=4,
    )
    _assert_vocabulary_withheld(
        result.relationships.between_labels("labels", "amounts"),
        n_paired=4,
    )


def test_withheld_vocabulary_does_not_enter_benjamini_hochberg() -> None:
    frame = pd.DataFrame(
        {
            "n1": [1.0, 2.0, 3.0, 4.0],
            "n2": [1.0, 2.0, 3.0, 5.0],
            "labels": pd.Categorical(["a", "a", "b", "b"]),
            "amounts": pd.Categorical(
                [
                    decimal.Decimal("1"),
                    decimal.Decimal("1"),
                    decimal.Decimal("2"),
                    decimal.Decimal("2"),
                ]
            ),
        }
    )

    result = profile(frame)

    adjusted = 0
    for record in result.relationships:
        if isinstance(record, NumericNumericRelationship):
            frequentist = record.spearman.frequentist
        elif isinstance(record, NumericCategoricalRelationship):
            frequentist = record.omnibus.frequentist
        else:
            frequentist = record.independence.frequentist
        if frequentist.reason is _VOCABULARY:
            assert frequentist.p_value is None
            assert frequentist.adjustment is MultipleTestingAdjustment.NOT_APPLIED
            continue
        if frequentist.availability is ResultAvailability.AVAILABLE:
            assert frequentist.adjustment is (
                MultipleTestingAdjustment.BENJAMINI_HOCHBERG
            )
            adjusted += 1
    assert adjusted == 3


def test_withheld_vocabulary_record_rejects_stored_groups() -> None:
    frame = pd.DataFrame(
        {
            "group": pd.Categorical(
                [decimal.Decimal("1"), decimal.Decimal("2"), decimal.Decimal("1")]
            ),
            "y": [1.0, 2.0, 3.0],
        }
    )
    record = profile(frame).relationships.between_labels("group", "y")
    group = CategoricalGroupSummary(
        category="a",
        descriptive=_from_finite(np.array([1.0, 2.0, 3.0])),
    )

    with pytest.raises(ValueError, match="no groups"):
        replace(record, groups=(group,))


def test_unexpected_category_type_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_value: object) -> None:
        raise TypeError("unexpected internal bug")

    monkeypatch.setattr(numeric_categorical_module, "_retain_category", boom)
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0],
            "group": pd.Categorical(["a", "b", "a"]),
        }
    )
    with pytest.raises(TypeError, match="unexpected internal bug"):
        profile(frame)


def test_unexpected_anova_type_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise TypeError("unexpected internal bug")

    monkeypatch.setattr(numeric_categorical_module, "f_oneway", boom)
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, 4.0],
            "group": pd.Categorical(["a", "a", "b", "b"]),
        }
    )
    with pytest.raises(TypeError, match="unexpected internal bug"):
        profile(frame)


def _modeling_rows(n: int = 24) -> range:
    return range(n)


def _decimal_labels(n: int = 24) -> list:
    return [
        decimal.Decimal("1") if index % 2 == 0 else decimal.Decimal("2")
        for index in _modeling_rows(n)
    ]


def _string_labels(n: int = 24) -> list:
    return ["a" if index % 2 == 0 else "b" for index in _modeling_rows(n)]


def _leakage_predictor(result: object, label: str):
    leakage = result.target.leakage  # type: ignore[attr-defined]
    assert leakage is not None
    for item in leakage.predictors:
        if item.label == label:
            return item
    raise AssertionError(label)


def test_numeric_target_excludes_an_unretained_categorical_predictor() -> None:
    n = 24
    frame = pd.DataFrame(
        {
            "y": [float(index) for index in _modeling_rows(n)],
            "x": [float(index % 5) for index in _modeling_rows(n)],
            "amounts": pd.Categorical(_decimal_labels(n)),
        }
    )
    original = frame.copy(deep=True)

    result = profile(frame, target="y")
    again = profile(frame, target="y")

    pd.testing.assert_frame_equal(frame, original)
    assert result == again
    diagnostic = result.target.diagnostic
    assert diagnostic is not None
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    assert diagnostic.evaluation is not None
    decisions = {item.label: item.decision for item in diagnostic.predictors}
    assert decisions["x"] is PredictorDecision.INCLUDED
    assert decisions["amounts"] is PredictorDecision.VOCABULARY_NOT_RETAINABLE
    included = diagnostic.included_predictors
    assert tuple(item.label for item in included) == ("x",)


def test_unretained_categorical_target_is_not_fitted() -> None:
    n = 24
    frame = pd.DataFrame(
        {
            "target": pd.Categorical(_decimal_labels(n)),
            "x": [float(index) for index in _modeling_rows(n)],
            "group": pd.Categorical(
                ["x" if index % 3 == 0 else "y" for index in _modeling_rows(n)]
            ),
        }
    )

    result = profile(frame, target="target")
    again = profile(frame, target="target")

    assert result == again
    diagnostic = result.target.diagnostic
    assert diagnostic is not None
    assert diagnostic.status is DiagnosticStatus.TARGET_VOCABULARY_NOT_RETAINABLE
    assert diagnostic.evaluation is None
    assert diagnostic.predictors == ()
    group = _leakage_predictor(result, "group")
    assert group.exact_duplicate.status is (
        ExactDuplicateStatus.CATEGORY_VOCABULARY_NOT_RETAINABLE
    )
    assert group.exact_duplicate.n_equal_rows == 0
    assert group.exact_duplicate.n_unequal_rows == 0
    assert all(
        item.code is not FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE
        for item in result.findings
    )
    assert "category vocabulary was not retained" in result._repr_html_()


def test_string_target_abstains_from_an_unretained_predictor() -> None:
    n = 24
    frame = pd.DataFrame(
        {
            "target": pd.Categorical(_string_labels(n)),
            "x": [float(index) for index in _modeling_rows(n)],
            "amounts": pd.Categorical(_decimal_labels(n)),
        }
    )

    result = profile(frame, target="target")

    diagnostic = result.target.diagnostic
    assert diagnostic is not None
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    decisions = {item.label: item.decision for item in diagnostic.predictors}
    assert decisions["x"] is PredictorDecision.INCLUDED
    assert decisions["amounts"] is PredictorDecision.VOCABULARY_NOT_RETAINABLE
    amounts = _leakage_predictor(result, "amounts")
    assert amounts.exact_duplicate.status is (
        ExactDuplicateStatus.CATEGORY_VOCABULARY_NOT_RETAINABLE
    )
    assert amounts.exact_duplicate.n_equal_rows == 0
    assert all(
        item.code is not FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE
        for item in result.findings
    )


def test_ordinary_categorical_target_still_uses_its_predictors() -> None:
    n = 24
    frame = pd.DataFrame(
        {
            "target": pd.Categorical(_string_labels(n)),
            "x": [float(index) for index in _modeling_rows(n)],
            "group": pd.Categorical(
                ["x" if index % 3 == 0 else "y" for index in _modeling_rows(n)]
            ),
        }
    )

    result = profile(frame, target="target")

    diagnostic = result.target.diagnostic
    assert diagnostic is not None
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    assert diagnostic.evaluation is not None
    decisions = {item.label: item.decision for item in diagnostic.predictors}
    assert decisions["x"] is PredictorDecision.INCLUDED
    assert decisions["group"] is PredictorDecision.INCLUDED
    group = _leakage_predictor(result, "group")
    assert group.exact_duplicate.status is not (
        ExactDuplicateStatus.CATEGORY_VOCABULARY_NOT_RETAINABLE
    )
    assert group.exact_duplicate.status is not ExactDuplicateStatus.EXACT_DUPLICATE


def test_unexpected_categorical_reader_type_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_series: object) -> None:
        raise TypeError("unexpected internal bug")

    monkeypatch.setattr(leakage_module, "_read_categorical_column", boom)
    frame = pd.DataFrame(
        {
            "target": pd.Categorical(["a", "b", "a", "b"]),
            "x": [1.0, 2.0, 3.0, 4.0],
        }
    )
    with pytest.raises(TypeError, match="unexpected internal bug"):
        profile(frame, target="target")

    monkeypatch.setattr(diagnostic_fit_module, "_read_categorical_column", boom)
    numeric = pd.DataFrame(
        {
            "y": [float(index) for index in range(24)],
            "group": pd.Categorical(
                ["a" if index % 2 == 0 else "b" for index in range(24)]
            ),
        }
    )
    with pytest.raises(TypeError, match="unexpected internal bug"):
        profile(numeric, target="y")
