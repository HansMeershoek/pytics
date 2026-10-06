"""TSK-048: unhashable distinct counts and unavailable duplicate analysis."""

from __future__ import annotations

import decimal

import pandas as pd
import pytest

import pytics.analysis.duplicate as duplicate_module
import pytics.semantics.string_structure_evidence as string_module
from pytics import compare
from pytics import profile
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.target import TargetStatus
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.interpretation import SemanticType


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


def test_decimal_categorical_relationship_remains_deferred() -> None:
    """Known deferred value-aware method eligibility limitation.

    A physical categorical Decimal column can be described. A downstream
    relationship record still cannot retain that vocabulary. TSK-048 does
    not change that boundary.
    """
    frame = pd.DataFrame(
        {
            "x": pd.Categorical(
                [
                    decimal.Decimal("1.0"),
                    decimal.Decimal("2.0"),
                    decimal.Decimal("1.0"),
                ]
            ),
            "y": [1.0, 2.0, 3.0],
        }
    )

    with pytest.raises(TypeError, match="Decimal"):
        profile(frame)
