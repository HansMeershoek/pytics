"""TSK-008: numeric-structure observations beside basic column evidence."""

from __future__ import annotations

import dataclasses
import math
from dataclasses import fields
from typing import Optional

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.semantics as semantics_package
import pytics.semantics.numeric_structure_evidence as numeric_module
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.numeric_structure_evidence import NumericStructureEvidence
from pytics.semantics.numeric_structure_evidence import (
    collect_numeric_structure_evidence,
)
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_series_precedence

_COUNT_FIELDS = (
    "finite_count",
    "positive_count",
    "negative_count",
    "zero_count",
    "positive_infinity_count",
    "negative_infinity_count",
    "integer_like_count",
    "non_integer_like_count",
)


def _collect(series: pd.Series) -> NumericStructureEvidence:
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    evidence = collect_numeric_structure_evidence(series, basic, physical)
    assert evidence.basic is basic
    _assert_invariants(evidence)
    return evidence


def _basic(
    n_non_missing: int, n_unique: int, n_missing: int = 0
) -> BasicColumnEvidence:
    return BasicColumnEvidence(
        n_total=n_non_missing + n_missing,
        n_missing=n_missing,
        n_non_missing=n_non_missing,
        n_unique_non_missing=n_unique,
    )


def _evidence_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "basic": _basic(0, 0),
        "finite_count": 0,
        "positive_count": 0,
        "negative_count": 0,
        "zero_count": 0,
        "positive_infinity_count": 0,
        "negative_infinity_count": 0,
        "integer_like_count": 0,
        "non_integer_like_count": 0,
        "is_non_decreasing": True,
        "is_non_increasing": True,
    }
    values.update(overrides)
    return values


def _assert_ratio(value: Optional[float], expected: Optional[float]) -> None:
    if expected is None:
        assert value is None
        return
    assert type(value) is float
    assert value == expected
    assert not math.isnan(value)
    assert not math.isinf(value)


def _assert_invariants(evidence: NumericStructureEvidence) -> None:
    basic = evidence.basic
    assert (
        evidence.finite_count
        + evidence.positive_infinity_count
        + evidence.negative_infinity_count
        == basic.n_non_missing
    )
    assert (
        evidence.positive_count + evidence.negative_count + evidence.zero_count
        == evidence.finite_count
    )
    assert (
        evidence.integer_like_count + evidence.non_integer_like_count
        == evidence.finite_count
    )
    for name in _COUNT_FIELDS:
        value = getattr(evidence, name)
        assert type(value) is int
        assert value >= 0
    _assert_ratio(
        evidence.finite_ratio,
        (
            None
            if basic.n_non_missing == 0
            else evidence.finite_count / basic.n_non_missing
        ),
    )
    if evidence.finite_count == 0:
        _assert_ratio(evidence.positive_ratio, None)
        _assert_ratio(evidence.negative_ratio, None)
        _assert_ratio(evidence.zero_ratio, None)
        _assert_ratio(evidence.integer_like_ratio, None)
    else:
        _assert_ratio(
            evidence.positive_ratio,
            evidence.positive_count / evidence.finite_count,
        )
        _assert_ratio(
            evidence.negative_ratio,
            evidence.negative_count / evidence.finite_count,
        )
        _assert_ratio(evidence.zero_ratio, evidence.zero_count / evidence.finite_count)
        _assert_ratio(
            evidence.integer_like_ratio,
            evidence.integer_like_count / evidence.finite_count,
        )
    if evidence.finite_count == basic.n_non_missing:
        assert type(evidence.is_non_decreasing) is bool
        assert type(evidence.is_non_increasing) is bool
    else:
        assert evidence.is_non_decreasing is None
        assert evidence.is_non_increasing is None


def test_numeric_structure_evidence_stores_structural_observations_only():
    evidence = _collect(pd.Series([1.0, 2.5, -1.0]))
    names = {field.name for field in fields(evidence)}

    assert names == {
        "basic",
        "finite_count",
        "positive_count",
        "negative_count",
        "zero_count",
        "positive_infinity_count",
        "negative_infinity_count",
        "integer_like_count",
        "non_integer_like_count",
        "is_non_decreasing",
        "is_non_increasing",
    }
    assert "finite_ratio" not in names
    assert "n_total" not in names
    assert "n_missing" not in names
    assert "n_non_missing" not in names
    assert not isinstance(evidence, BasicColumnEvidence)
    assert not issubclass(NumericStructureEvidence, BasicColumnEvidence)
    for absent in (
        "min",
        "max",
        "mean",
        "median",
        "std",
        "variance",
        "regular_step",
        "step_size",
        "sequence_like",
        "semantic_type",
    ):
        assert not hasattr(evidence, absent)
    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.finite_count = 0  # type: ignore[misc]


def test_empty_integer_series_has_zero_counts_and_vacuous_monotonicity():
    series = pd.Series([], dtype="int64")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.n_non_missing == 0
    assert evidence.finite_count == 0
    assert evidence.positive_count == 0
    assert evidence.negative_count == 0
    assert evidence.zero_count == 0
    assert evidence.positive_infinity_count == 0
    assert evidence.negative_infinity_count == 0
    assert evidence.integer_like_count == 0
    assert evidence.non_integer_like_count == 0
    _assert_ratio(evidence.finite_ratio, None)
    _assert_ratio(evidence.integer_like_ratio, None)
    assert evidence.is_non_decreasing is True
    assert evidence.is_non_increasing is True
    assert reading is not None
    assert reading.semantic_type is SemanticType.EMPTY


def test_all_missing_nullable_integer_series_matches_empty_structure():
    series = pd.Series([pd.NA, pd.NA], dtype="Int64")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.n_total == 2
    assert evidence.basic.n_missing == 2
    assert evidence.basic.n_non_missing == 0
    assert evidence.finite_count == 0
    assert evidence.positive_infinity_count == 0
    assert evidence.negative_infinity_count == 0
    assert evidence.integer_like_count == 0
    assert evidence.non_integer_like_count == 0
    _assert_ratio(evidence.finite_ratio, None)
    _assert_ratio(evidence.positive_ratio, None)
    assert evidence.is_non_decreasing is True
    assert evidence.is_non_increasing is True
    assert reading is not None
    assert reading.semantic_type is SemanticType.EMPTY


def test_positive_integers_are_finite_and_integer_like():
    series = pd.Series([1, 4, 9], dtype="int64")
    evidence = _collect(series)

    assert evidence.basic.n_non_missing == 3
    assert evidence.finite_count == 3
    assert evidence.positive_count == 3
    assert evidence.negative_count == 0
    assert evidence.zero_count == 0
    assert evidence.positive_infinity_count == 0
    assert evidence.negative_infinity_count == 0
    assert evidence.integer_like_count == 3
    assert evidence.non_integer_like_count == 0
    _assert_ratio(evidence.finite_ratio, 1.0)
    _assert_ratio(evidence.positive_ratio, 1.0)
    _assert_ratio(evidence.negative_ratio, 0.0)
    _assert_ratio(evidence.zero_ratio, 0.0)
    _assert_ratio(evidence.integer_like_ratio, 1.0)
    assert interpret_series_precedence(series) is None


def test_negative_integers_are_finite_and_not_positive():
    series = pd.Series([-8, -3, -1], dtype="int64")
    evidence = _collect(series)

    assert evidence.finite_count == 3
    assert evidence.negative_count == 3
    assert evidence.positive_count == 0
    assert evidence.zero_count == 0
    assert evidence.integer_like_count == 3
    assert evidence.non_integer_like_count == 0
    _assert_ratio(evidence.negative_ratio, 1.0)
    _assert_ratio(evidence.positive_ratio, 0.0)
    assert interpret_series_precedence(series) is None


def test_zeros_include_negative_zero_without_a_signed_zero_split():
    series = pd.Series([0.0, -0.0, 0.0])
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.zero_count == 3
    assert evidence.positive_count == 0
    assert evidence.negative_count == 0
    assert evidence.finite_count == 3
    assert evidence.integer_like_count == 3
    assert evidence.is_non_decreasing is True
    assert evidence.is_non_increasing is True
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT


def test_mixed_signs_partition_the_finite_values():
    series = pd.Series([-2.0, -0.0, 0.0, 4.0])
    evidence = _collect(series)

    assert evidence.negative_count == 1
    assert evidence.zero_count == 2
    assert evidence.positive_count == 1
    assert evidence.finite_count == 4
    _assert_ratio(evidence.negative_ratio, 1 / 4)
    _assert_ratio(evidence.zero_ratio, 2 / 4)
    _assert_ratio(evidence.positive_ratio, 1 / 4)
    assert interpret_series_precedence(series) is None


def test_integral_floats_are_integer_like():
    series = pd.Series([1.0, -3.0, 0.0])
    evidence = _collect(series)

    assert evidence.integer_like_count == 3
    assert evidence.non_integer_like_count == 0
    assert evidence.positive_count == 1
    assert evidence.negative_count == 1
    assert evidence.zero_count == 1
    _assert_ratio(evidence.integer_like_ratio, 1.0)
    assert interpret_series_precedence(series) is None


def test_non_integral_floats_are_not_integer_like():
    series = pd.Series([1.5, -2.25])
    evidence = _collect(series)

    assert evidence.integer_like_count == 0
    assert evidence.non_integer_like_count == 2
    assert evidence.positive_count == 1
    assert evidence.negative_count == 1
    _assert_ratio(evidence.integer_like_ratio, 0.0)
    assert interpret_series_precedence(series) is None


def test_mixed_integral_and_non_integral_floats_stay_exact():
    series = pd.Series([1.0, 1.5, -3.0, -2.25])
    evidence = _collect(series)

    assert evidence.integer_like_count == 2
    assert evidence.non_integer_like_count == 2
    _assert_ratio(evidence.integer_like_ratio, 0.5)
    assert interpret_series_precedence(series) is None


def test_integer_like_classification_has_no_tolerance():
    series = pd.Series([1.0, 1.0000000001], dtype="float64")
    evidence = _collect(series)

    assert series.iloc[1] != np.trunc(series.iloc[1])
    assert evidence.integer_like_count == 1
    assert evidence.non_integer_like_count == 1
    _assert_ratio(evidence.integer_like_ratio, 0.5)


def test_positive_infinity_is_outside_finite_sign_and_integer_like_counts():
    series = pd.Series([1.0, np.inf, 3.0])
    evidence = _collect(series)

    assert evidence.basic.n_non_missing == 3
    assert evidence.finite_count == 2
    assert evidence.positive_count == 2
    assert evidence.positive_infinity_count == 1
    assert evidence.negative_infinity_count == 0
    assert evidence.integer_like_count == 2
    assert evidence.non_integer_like_count == 0
    _assert_ratio(evidence.finite_ratio, 2 / 3)
    assert evidence.is_non_decreasing is None
    assert evidence.is_non_increasing is None
    assert interpret_series_precedence(series) is None


def test_negative_infinity_is_outside_the_finite_negative_count():
    series = pd.Series([-np.inf, -2.5])
    evidence = _collect(series)

    assert evidence.finite_count == 1
    assert evidence.negative_count == 1
    assert evidence.negative_infinity_count == 1
    assert evidence.positive_infinity_count == 0
    assert evidence.integer_like_count == 0
    assert evidence.non_integer_like_count == 1
    assert evidence.is_non_decreasing is None
    assert evidence.is_non_increasing is None


def test_infinities_finite_values_and_missingness_follow_the_structure_contract():
    series = pd.Series([-np.inf, -2.5, 0.0, 3.0, np.inf, np.nan])
    evidence = _collect(series)

    assert evidence.basic.n_non_missing == 5
    assert evidence.basic.n_missing == 1
    assert evidence.finite_count == 3
    assert evidence.negative_count == 1
    assert evidence.zero_count == 1
    assert evidence.positive_count == 1
    assert evidence.negative_infinity_count == 1
    assert evidence.positive_infinity_count == 1
    assert evidence.integer_like_count == 2
    assert evidence.non_integer_like_count == 1
    _assert_ratio(evidence.finite_ratio, 3 / 5)
    _assert_ratio(evidence.integer_like_ratio, 2 / 3)
    _assert_ratio(evidence.positive_ratio, 1 / 3)
    _assert_ratio(evidence.negative_ratio, 1 / 3)
    _assert_ratio(evidence.zero_ratio, 1 / 3)
    assert evidence.is_non_decreasing is None
    assert evidence.is_non_increasing is None
    assert interpret_series_precedence(series) is None


def test_constant_infinity_keeps_monotonicity_undefined():
    series = pd.Series([np.inf, np.inf])
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.finite_count == 0
    assert evidence.positive_infinity_count == 2
    assert evidence.positive_count == 0
    assert evidence.integer_like_count == 0
    _assert_ratio(evidence.finite_ratio, 0.0)
    _assert_ratio(evidence.positive_ratio, None)
    _assert_ratio(evidence.negative_ratio, None)
    _assert_ratio(evidence.zero_ratio, None)
    _assert_ratio(evidence.integer_like_ratio, None)
    assert evidence.is_non_decreasing is None
    assert evidence.is_non_increasing is None
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT


def test_nullable_integer_dtype_keeps_na_missing_and_values_integral():
    series = pd.Series([1, pd.NA, -2, 0, pd.NA, 4], dtype="Int64")
    evidence = _collect(series)

    assert evidence.basic.n_missing == 2
    assert evidence.basic.n_non_missing == 4
    assert evidence.finite_count == 4
    assert evidence.positive_count == 2
    assert evidence.negative_count == 1
    assert evidence.zero_count == 1
    assert evidence.integer_like_count == 4
    assert evidence.non_integer_like_count == 0
    assert evidence.positive_infinity_count == 0
    assert evidence.negative_infinity_count == 0
    _assert_ratio(evidence.integer_like_ratio, 1.0)
    assert evidence.is_non_decreasing is False
    assert evidence.is_non_increasing is False
    assert interpret_series_precedence(series) is None


def test_nullable_floating_dtype_uses_pandas_missingness():
    series = pd.Series([1.0, pd.NA, 1.5, -0.0, np.nan], dtype="Float64")
    evidence = _collect(series)

    assert evidence.basic.n_missing == 2
    assert evidence.basic.n_non_missing == 3
    assert evidence.finite_count == 3
    assert evidence.positive_count == 2
    assert evidence.negative_count == 0
    assert evidence.zero_count == 1
    assert evidence.integer_like_count == 2
    assert evidence.non_integer_like_count == 1
    assert evidence.positive_infinity_count == 0
    assert evidence.is_non_decreasing is False
    assert evidence.is_non_increasing is False


def test_sparse_floating_values_remain_numeric_structure():
    series = pd.Series(pd.arrays.SparseArray([1.0, np.nan, -2.5, 0.0]))
    evidence = _collect(series)

    assert evidence.basic.n_missing == 1
    assert evidence.finite_count == 3
    assert evidence.positive_count == 1
    assert evidence.negative_count == 1
    assert evidence.zero_count == 1
    assert evidence.integer_like_count == 2
    assert evidence.non_integer_like_count == 1


def test_large_unsigned_integers_keep_order_without_a_float_cast():
    series = pd.Series(
        np.array([np.uint64(2**63 + 1), np.uint64(2**63)], dtype=np.uint64)
    )
    evidence = _collect(series)

    assert np.float64(np.uint64(2**63 + 1)) == np.float64(np.uint64(2**63))
    assert evidence.finite_count == 2
    assert evidence.positive_count == 2
    assert evidence.negative_count == 0
    assert evidence.integer_like_count == 2
    assert evidence.non_integer_like_count == 0
    assert evidence.is_non_decreasing is False
    assert evidence.is_non_increasing is True


def test_increasing_sequence_is_only_non_decreasing():
    series = pd.Series([1, 2, 3])
    evidence = _collect(series)

    assert evidence.is_non_decreasing is True
    assert evidence.is_non_increasing is False
    assert interpret_series_precedence(series) is None


def test_decreasing_sequence_is_only_non_increasing():
    series = pd.Series([3, 2, 1])
    evidence = _collect(series)

    assert evidence.is_non_decreasing is False
    assert evidence.is_non_increasing is True


def test_non_monotonic_sequence_is_neither():
    series = pd.Series([1, 3, 2])
    evidence = _collect(series)

    assert evidence.is_non_decreasing is False
    assert evidence.is_non_increasing is False


def test_duplicate_values_remain_monotonic():
    increasing = _collect(pd.Series([1, 2, 2, 3]))
    decreasing = _collect(pd.Series([3, 2, 2, 1]))

    assert increasing.is_non_decreasing is True
    assert increasing.is_non_increasing is False
    assert decreasing.is_non_decreasing is False
    assert decreasing.is_non_increasing is True


def test_one_finite_value_is_vacuously_monotonic_and_constant():
    series = pd.Series([7])
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.finite_count == 1
    assert evidence.is_non_decreasing is True
    assert evidence.is_non_increasing is True
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT


def test_constant_finite_series_is_monotonic_and_stays_constant():
    series = pd.Series([4, 4, pd.NA], dtype="Int64")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.is_constant is True
    assert evidence.positive_count == 2
    assert evidence.finite_count == 2
    assert evidence.is_non_decreasing is True
    assert evidence.is_non_increasing is True
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT
    assert reading.source is InferenceSource.INFERRED


def test_missing_values_are_ignored_and_finite_order_is_preserved():
    disordered = pd.Series([1.0, np.nan, 3.0, np.nan, 2.0], index=[5, 0, 4, 1, 3])
    ordered = pd.Series([1, pd.NA, 2, pd.NA, 2], dtype="Int64")
    disordered_evidence = _collect(disordered)
    ordered_evidence = _collect(ordered)

    assert disordered_evidence.finite_count == 3
    assert disordered_evidence.is_non_decreasing is False
    assert disordered_evidence.is_non_increasing is False
    assert ordered_evidence.finite_count == 3
    assert ordered_evidence.is_non_decreasing is True
    assert ordered_evidence.is_non_increasing is False


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([True, False]),
        pd.Series([True, False, pd.NA], dtype="boolean"),
    ],
)
def test_boolean_series_is_rejected(series: pd.Series):
    with pytest.raises(TypeError, match="integer and floating"):
        _collect(series)


def test_boolean_labeled_as_integer_is_still_rejected():
    series = pd.Series([True, False])
    physical = PhysicalDtype(
        family=PhysicalDtypeFamily.INTEGER,
        dtype_name=str(series.dtype),
    )

    with pytest.raises(TypeError, match="integer and floating"):
        collect_numeric_structure_evidence(
            series,
            collect_basic_column_evidence(series),
            physical,
        )


@pytest.mark.parametrize(
    "series",
    [
        pd.Series(["1", "2", "3"]),
        pd.Series(["1", "2", "3"], dtype="string"),
        pd.Series([1, 2, 3], dtype=object),
    ],
)
def test_string_and_object_series_are_rejected(series: pd.Series):
    with pytest.raises(TypeError, match="integer and floating"):
        _collect(series)


@pytest.mark.parametrize(
    "series",
    [
        pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"])),
        pd.Series(pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"])),
    ],
)
def test_datetime_series_is_rejected(series: pd.Series):
    with pytest.raises(TypeError, match="integer and floating"):
        _collect(series)


def test_timedelta_series_is_rejected():
    series = pd.Series(pd.to_timedelta(["1 day", "2 days"]))

    with pytest.raises(TypeError, match="integer and floating"):
        _collect(series)


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([1 + 0j, 2 + 1j]),
        pd.Series(pd.Categorical([1, 2, 1])),
        pd.Series(pd.period_range("2024-01", periods=2, freq="M")),
    ],
)
def test_complex_categorical_and_period_series_are_rejected(series: pd.Series):
    with pytest.raises(TypeError, match="integer and floating"):
        _collect(series)


def test_numeric_strings_are_not_coerced(monkeypatch: pytest.MonkeyPatch):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("pd.to_numeric was called")

    monkeypatch.setattr(pd, "to_numeric", _forbidden)
    series = pd.Series(["1", "2", "3"])

    with pytest.raises(TypeError, match="integer and floating"):
        _collect(series)


def test_unique_monotonic_integers_are_not_identifiers():
    series = pd.Series([1, 2, 3, 4])
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.unique_ratio_non_missing == 1.0
    assert evidence.is_non_decreasing is True
    assert evidence.integer_like_ratio == 1.0
    assert reading is None


def test_zero_one_integers_are_not_boolean():
    series = pd.Series([0, 1, 1, 0])
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.zero_count == 2
    assert evidence.positive_count == 2
    assert evidence.integer_like_count == 4
    assert reading is None


def test_zero_one_floats_are_not_binary():
    series = pd.Series([0.0, 1.0, 1.0, 0.0])
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.zero_count == 2
    assert evidence.positive_count == 2
    assert evidence.integer_like_count == 4
    _assert_ratio(evidence.integer_like_ratio, 1.0)
    assert reading is None


def test_integer_like_floats_do_not_create_a_numeric_subtype():
    series = pd.Series([1.0, 2.0, 4.0])
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.integer_like_ratio == 1.0
    assert evidence.is_non_decreasing is True
    assert reading is None


def test_existing_semantic_chain_is_unchanged_beside_numeric_structure():
    empty = pd.Series([], dtype="float64")
    constant = pd.Series([7, np.nan, 7])
    boolean = pd.Series([True, False, pd.NA], dtype="boolean")
    constant_boolean = pd.Series([True, True], dtype=bool)
    native = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))
    aware = pd.Series(pd.to_datetime(["2026-01-01T12:00:00Z", "2026-01-02T12:00:00Z"]))
    duration = pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    ordinary = pd.Series([1, 2, 3])

    empty_reading = interpret_series_precedence(empty)
    constant_reading = interpret_series_precedence(constant)
    boolean_reading = interpret_series_precedence(boolean)
    constant_boolean_reading = interpret_series_precedence(constant_boolean)
    native_reading = interpret_series_precedence(native)
    aware_reading = interpret_series_precedence(aware)
    duration_reading = interpret_series_precedence(duration)
    ordinary_reading = interpret_series_precedence(ordinary)
    empty_evidence = _collect(empty)
    constant_evidence = _collect(constant)

    assert empty_reading is not None
    assert empty_reading.semantic_type is SemanticType.EMPTY
    assert empty_reading.confidence is Confidence.HIGH
    assert empty_reading.source is InferenceSource.INFERRED
    assert empty_evidence.is_non_decreasing is True
    assert empty_evidence.is_non_increasing is True
    assert constant_reading is not None
    assert constant_reading.semantic_type is SemanticType.CONSTANT
    assert constant_reading.source is InferenceSource.INFERRED
    assert constant_evidence.is_non_decreasing is True
    assert constant_evidence.positive_count == 2
    assert constant_boolean_reading is not None
    assert constant_boolean_reading.semantic_type is SemanticType.CONSTANT
    assert boolean_reading is not None
    assert boolean_reading.semantic_type is SemanticType.BOOLEAN
    assert boolean_reading.confidence is Confidence.HIGH
    assert boolean_reading.source is InferenceSource.PHYSICAL_DTYPE
    assert boolean_reading.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert boolean_reading.evidence[0].statement == "physical dtype is boolean"
    assert native_reading is not None
    assert native_reading.semantic_type is SemanticType.DATETIME
    assert native_reading.physical.family is PhysicalDtypeFamily.DATETIME
    assert native_reading.evidence[0].statement == "physical dtype is datetime"
    assert aware_reading is not None
    assert aware_reading.semantic_type is SemanticType.DATETIME
    assert aware_reading.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert duration_reading is not None
    assert duration_reading.semantic_type is SemanticType.TIMEDELTA
    assert duration_reading.confidence is Confidence.HIGH
    assert duration_reading.source is InferenceSource.PHYSICAL_DTYPE
    assert duration_reading.physical.family is PhysicalDtypeFamily.TIMEDELTA
    assert duration_reading.evidence[0].statement == "physical dtype is timedelta"
    assert ordinary_reading is None


def test_precedence_does_not_collect_numeric_structure_evidence(
    monkeypatch: pytest.MonkeyPatch,
):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "numeric structure evidence was collected during precedence"
        )

    monkeypatch.setattr(pd.Series, "dropna", _forbidden)
    monkeypatch.setattr(
        numeric_module,
        "collect_numeric_structure_evidence",
        _forbidden,
    )

    empty = interpret_series_precedence(pd.Series([None, None]))
    constant = interpret_series_precedence(pd.Series([4, 4, 4]))
    ordinary = interpret_series_precedence(pd.Series([1, 2, 3]))

    assert empty is not None
    assert empty.semantic_type is SemanticType.EMPTY
    assert constant is not None
    assert constant.semantic_type is SemanticType.CONSTANT
    assert ordinary is None


def test_basic_evidence_is_reused_without_frequency_or_reclassification(
    monkeypatch: pytest.MonkeyPatch,
):
    series = pd.Series([1.0, np.nan, -2.0, 4.0])
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("basic evidence or frequency evidence was recomputed")

    monkeypatch.setattr(pd.Series, "nunique", _forbidden)
    monkeypatch.setattr(pd.Series, "value_counts", _forbidden)
    monkeypatch.setattr(pd, "to_numeric", _forbidden)
    monkeypatch.setattr(
        "pytics.semantics.column_evidence.collect_basic_column_evidence",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.physical.classify_physical_dtype",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.frequency_evidence.collect_frequency_evidence",
        _forbidden,
    )

    evidence = collect_numeric_structure_evidence(series, basic, physical)

    assert evidence.basic is basic
    assert evidence.finite_count == 3
    assert evidence.negative_count == 1
    assert evidence.positive_count == 2
    assert not hasattr(numeric_module, "collect_basic_column_evidence")
    assert not hasattr(numeric_module, "classify_physical_dtype")
    assert not hasattr(numeric_module, "collect_frequency_evidence")


def test_collection_does_not_mutate_the_series():
    series = pd.Series(
        [1, pd.NA, -2],
        dtype="Int64",
        name="amount",
        index=pd.Index([3, 1, 4], name="row"),
    )
    before = series.copy(deep=True)

    _collect(series)

    pd.testing.assert_series_equal(series, before)
    assert series.name == "amount"
    assert series.index.name == "row"


def test_mismatched_basic_evidence_is_rejected():
    series = pd.Series([1, 2, 3])
    basic = _basic(2, 2)
    physical = classify_physical_dtype(series)

    with pytest.raises(ValueError, match="do not match BasicColumnEvidence"):
        collect_numeric_structure_evidence(series, basic, physical)


def test_mismatched_physical_dtype_is_rejected():
    series = pd.Series([1, 2, 3], dtype="int64")
    physical = PhysicalDtype(family=PhysicalDtypeFamily.INTEGER, dtype_name="int32")

    with pytest.raises(ValueError, match="does not match the Series"):
        collect_numeric_structure_evidence(
            series,
            collect_basic_column_evidence(series),
            physical,
        )


def test_wrong_input_types_are_rejected():
    series = pd.Series([1, 2])
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)

    with pytest.raises(TypeError, match="pandas Series"):
        collect_numeric_structure_evidence([1, 2], basic, physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="BasicColumnEvidence"):
        collect_numeric_structure_evidence(series, "basic", physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="PhysicalDtype"):
        collect_numeric_structure_evidence(series, basic, "physical")  # type: ignore[arg-type]


def test_non_real_numeric_array_is_rejected(monkeypatch: pytest.MonkeyPatch):
    series = pd.Series([1, 2, 3])
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    original = pd.Series.to_numpy

    def _object_array(self: pd.Series, *args: object, **kwargs: object) -> np.ndarray:
        if self.dtype == object:
            return original(self, *args, **kwargs)
        return np.array([1, 2, 3], dtype=object)

    monkeypatch.setattr(pd.Series, "to_numpy", _object_array)

    with pytest.raises(TypeError, match="real integer and floating"):
        collect_numeric_structure_evidence(series, basic, physical)


def test_non_finite_non_infinite_value_is_rejected(monkeypatch: pytest.MonkeyPatch):
    series = pd.Series([1.0, 2.0])
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)

    def _false_mask(values: np.ndarray) -> np.ndarray:
        return np.zeros(values.shape, dtype=bool)

    monkeypatch.setattr(numeric_module.np, "isfinite", _false_mask)
    monkeypatch.setattr(numeric_module.np, "isposinf", _false_mask)
    monkeypatch.setattr(numeric_module.np, "isneginf", _false_mask)

    with pytest.raises(ValueError, match="neither finite nor infinite"):
        collect_numeric_structure_evidence(series, basic, physical)


def test_numeric_structure_evidence_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "NumericStructureEvidence")
    assert not hasattr(pytics, "collect_numeric_structure_evidence")
    assert not hasattr(semantics_package, "NumericStructureEvidence")
    assert not hasattr(semantics_package, "collect_numeric_structure_evidence")


@pytest.mark.parametrize(
    ("overrides", "error", "match"),
    [
        ({"basic": "counts"}, TypeError, "BasicColumnEvidence"),
        ({"finite_count": True}, TypeError, "finite_count"),
        ({"positive_count": -1}, ValueError, "positive_count"),
        (
            {
                "basic": _basic(2, 2),
                "finite_count": 2,
                "positive_count": 2,
                "integer_like_count": 2,
                "positive_infinity_count": 1,
                "is_non_decreasing": True,
                "is_non_increasing": False,
            },
            ValueError,
            "n_non_missing",
        ),
        (
            {
                "basic": _basic(2, 2),
                "finite_count": 2,
                "positive_count": 2,
                "negative_count": 1,
                "integer_like_count": 2,
                "is_non_decreasing": True,
                "is_non_increasing": False,
            },
            ValueError,
            "finite_count",
        ),
        (
            {
                "basic": _basic(2, 2),
                "finite_count": 2,
                "positive_count": 2,
                "integer_like_count": 2,
                "non_integer_like_count": 1,
                "is_non_decreasing": True,
                "is_non_increasing": False,
            },
            ValueError,
            "finite_count",
        ),
        (
            {
                "basic": _basic(1, 1),
                "positive_infinity_count": 1,
                "is_non_decreasing": True,
                "is_non_increasing": True,
            },
            ValueError,
            "undefined",
        ),
        (
            {
                "basic": _basic(2, 2),
                "finite_count": 2,
                "positive_count": 1,
                "negative_count": 1,
                "integer_like_count": 2,
                "is_non_decreasing": None,
                "is_non_increasing": None,
            },
            TypeError,
            "bool",
        ),
        (
            {
                "basic": _basic(1, 1),
                "finite_count": 1,
                "positive_count": 1,
                "integer_like_count": 1,
                "is_non_decreasing": False,
                "is_non_increasing": True,
            },
            ValueError,
            "one finite",
        ),
        (
            {
                "basic": _basic(2, 1),
                "finite_count": 2,
                "positive_count": 2,
                "integer_like_count": 2,
                "is_non_decreasing": True,
                "is_non_increasing": False,
            },
            ValueError,
            "finite constant",
        ),
    ],
)
def test_inconsistent_numeric_structure_evidence_is_rejected(
    overrides: dict[str, object],
    error: type[Exception],
    match: str,
):
    with pytest.raises(error, match=match):
        NumericStructureEvidence(**_evidence_kwargs(**overrides))  # type: ignore[arg-type]
