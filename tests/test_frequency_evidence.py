"""TSK-007: exact frequency observations beside basic column evidence."""

from __future__ import annotations

import math
from dataclasses import fields
from typing import Optional

import pandas as pd
import pytest

import pytics
import pytics.semantics as semantics_package
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.frequency_evidence import EXACT_DISTINCT_VALUE_RETENTION_LIMIT
from pytics.semantics.frequency_evidence import FrequencyEvidence
from pytics.semantics.frequency_evidence import collect_frequency_evidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical_timedelta import interpret_series_precedence


def _collect(series: pd.Series) -> FrequencyEvidence:
    basic = collect_basic_column_evidence(series)
    return collect_frequency_evidence(series, basic)


def _basic(n_non_missing: int, n_unique: int) -> BasicColumnEvidence:
    return BasicColumnEvidence(
        n_total=n_non_missing,
        n_missing=0,
        n_non_missing=n_non_missing,
        n_unique_non_missing=n_unique,
    )


def _assert_ratio(value: Optional[float], expected: Optional[float]) -> None:
    if expected is None:
        assert value is None
        return
    assert type(value) is float
    assert value == expected
    assert not math.isnan(value)
    assert not math.isinf(value)


def _assert_bounded(evidence: FrequencyEvidence) -> None:
    assert set(evidence.__dict__) == set(FrequencyEvidence.__dataclass_fields__)
    for field in fields(evidence):
        value = getattr(evidence, field.name)
        assert not isinstance(value, (dict, list, tuple, set))
        if type(value) is frozenset:
            assert len(value) <= EXACT_DISTINCT_VALUE_RETENTION_LIMIT


def test_frequency_evidence_stores_observations_only():
    evidence = _collect(pd.Series(["a", "a", "b"]))

    assert set(FrequencyEvidence.__dataclass_fields__) == {
        "basic",
        "most_frequent_count",
        "singleton_count",
        "exact_distinct_non_missing_values",
    }
    assert "most_frequent_ratio" not in FrequencyEvidence.__dataclass_fields__
    assert "singleton_ratio" not in FrequencyEvidence.__dataclass_fields__
    assert not issubclass(FrequencyEvidence, BasicColumnEvidence)
    forbidden = (
        "is_low_cardinality",
        "is_high_cardinality",
        "looks_categorical",
        "looks_identifier",
        "is_binary",
        "likely_text",
        "category_strength",
        "identifier_score",
        "n_missing",
        "missing_ratio",
        "has_missing",
        "n_non_missing",
        "n_unique_non_missing",
        "confidence",
    )
    for name in forbidden:
        assert name not in FrequencyEvidence.__dataclass_fields__
    assert evidence.basic.n_non_missing == 3
    assert type(evidence.most_frequent_count) is int
    assert type(evidence.singleton_count) is int


def test_empty_series_has_zero_frequency_counts_and_an_empty_value_set():
    series = pd.Series([], dtype="float64")

    evidence = _collect(series)

    assert evidence.basic.n_non_missing == 0
    assert evidence.basic.n_unique_non_missing == 0
    assert evidence.basic.is_empty is True
    assert evidence.most_frequent_count == 0
    assert evidence.singleton_count == 0
    _assert_ratio(evidence.most_frequent_ratio, None)
    _assert_ratio(evidence.singleton_ratio, None)
    assert evidence.exact_distinct_non_missing_values == frozenset()
    assert type(evidence.exact_distinct_non_missing_values) is frozenset


def test_all_missing_series_matches_empty_frequency_facts():
    series = pd.Series([None, None, None])

    evidence = _collect(series)

    assert evidence.basic.n_total == 3
    assert evidence.basic.n_missing == 3
    assert evidence.basic.n_non_missing == 0
    assert evidence.basic.is_empty is True
    assert evidence.basic.is_constant is False
    assert evidence.most_frequent_count == 0
    assert evidence.singleton_count == 0
    _assert_ratio(evidence.most_frequent_ratio, None)
    _assert_ratio(evidence.singleton_ratio, None)
    assert evidence.exact_distinct_non_missing_values == frozenset()
    assert interpret_series_precedence(series) is not None
    assert interpret_series_precedence(series).semantic_type is SemanticType.EMPTY


def test_one_value_is_a_singleton_and_retains_that_value():
    series = pd.Series(["a"])

    evidence = _collect(series)

    assert evidence.basic.is_constant is True
    assert evidence.most_frequent_count == 1
    _assert_ratio(evidence.most_frequent_ratio, 1.0)
    assert evidence.singleton_count == 1
    _assert_ratio(evidence.singleton_ratio, 1.0)
    assert evidence.exact_distinct_non_missing_values == frozenset({"a"})


def test_repeated_constant_has_no_singleton():
    series = pd.Series(["a", "a", "a"])

    evidence = _collect(series)

    assert evidence.basic.n_non_missing == 3
    assert evidence.basic.n_unique_non_missing == 1
    assert evidence.basic.is_constant is True
    assert evidence.most_frequent_count == evidence.basic.n_non_missing
    _assert_ratio(evidence.most_frequent_ratio, 1.0)
    assert evidence.singleton_count == 0
    _assert_ratio(evidence.singleton_ratio, 0.0)
    assert evidence.exact_distinct_non_missing_values == frozenset({"a"})
    reading = interpret_series_precedence(series)
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT


def test_constant_with_missing_counts_only_non_missing_occurrences():
    series = pd.Series(["a", None, "a"])

    evidence = _collect(series)

    assert evidence.basic.is_constant is True
    assert evidence.basic.n_missing == 1
    assert evidence.basic.n_non_missing == 2
    assert evidence.basic.n_unique_non_missing == 1
    assert evidence.most_frequent_count == evidence.basic.n_non_missing
    _assert_ratio(evidence.most_frequent_ratio, 1.0)
    assert evidence.singleton_count == 0
    _assert_ratio(evidence.singleton_ratio, 0.0)
    assert evidence.exact_distinct_non_missing_values == frozenset({"a"})
    reading = interpret_series_precedence(series)
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT


def test_mixed_distribution_uses_the_specified_denominators():
    series = pd.Series(["a", "a", "b", "c", "c", "d"])
    basic = collect_basic_column_evidence(series)

    evidence = collect_frequency_evidence(series, basic)

    assert evidence.basic is basic
    assert evidence.most_frequent_count == 2
    _assert_ratio(evidence.most_frequent_ratio, 2 / 6)
    assert evidence.singleton_count == 2
    _assert_ratio(evidence.singleton_ratio, 2 / 4)
    assert evidence.exact_distinct_non_missing_values == frozenset({"a", "b", "c", "d"})
    assert evidence.singleton_ratio == (
        evidence.singleton_count / evidence.basic.n_unique_non_missing
    )


def test_missing_values_are_outside_the_frequency_population():
    series = pd.Series(["a", "a", None, "b", "c", None])

    evidence = _collect(series)

    assert evidence.basic.n_missing == 2
    assert evidence.basic.n_non_missing == 4
    assert evidence.basic.n_unique_non_missing == 3
    assert evidence.basic.missing_ratio == 2 / 6
    assert evidence.most_frequent_count == 2
    _assert_ratio(evidence.most_frequent_ratio, 2 / 4)
    assert evidence.singleton_count == 2
    _assert_ratio(evidence.singleton_ratio, 2 / 3)
    retained = evidence.exact_distinct_non_missing_values
    assert retained == frozenset({"a", "b", "c"})
    assert None not in retained
    assert "n_missing" not in FrequencyEvidence.__dataclass_fields__
    assert "missing_ratio" not in FrequencyEvidence.__dataclass_fields__
    assert "has_missing" not in FrequencyEvidence.__dataclass_fields__


def test_missing_like_literals_remain_ordinary_values():
    series = pd.Series(["NA", "null", "", "NA"])
    original = series.copy(deep=True)

    evidence = _collect(series)

    pd.testing.assert_series_equal(series, original)
    assert evidence.basic.n_missing == 0
    assert evidence.basic.n_non_missing == 4
    assert evidence.basic.n_unique_non_missing == 3
    assert evidence.most_frequent_count == 2
    _assert_ratio(evidence.most_frequent_ratio, 2 / 4)
    assert evidence.singleton_count == 2
    _assert_ratio(evidence.singleton_ratio, 2 / 3)
    assert evidence.exact_distinct_non_missing_values == frozenset({"NA", "null", ""})


def test_fully_unique_values_are_singletons_without_identifier_inference():
    series = pd.Series(["a", "b", "c", "d"])

    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.most_frequent_count == 1
    _assert_ratio(evidence.most_frequent_ratio, 1 / 4)
    assert evidence.singleton_count == 4
    _assert_ratio(evidence.singleton_ratio, 1.0)
    assert reading is None
    assert evidence.basic.is_constant is False


def test_retention_limit_keeps_exactly_the_operational_boundary():
    assert EXACT_DISTINCT_VALUE_RETENTION_LIMIT == 32
    limit = EXACT_DISTINCT_VALUE_RETENTION_LIMIT
    series = pd.Series([f"v{index}" for index in range(limit)])

    evidence = _collect(series)
    retained = evidence.exact_distinct_non_missing_values

    assert evidence.basic.n_unique_non_missing == limit
    assert retained is not None
    assert type(retained) is frozenset
    assert len(retained) == limit
    assert retained == frozenset(series.tolist())
    assert evidence.singleton_count == limit
    _assert_ratio(evidence.singleton_ratio, 1.0)
    assert interpret_series_precedence(series) is None


def test_one_past_the_retention_limit_does_not_keep_distinct_values():
    limit = EXACT_DISTINCT_VALUE_RETENTION_LIMIT
    series = pd.Series([f"v{index}" for index in range(limit + 1)])

    evidence = _collect(series)

    assert evidence.basic.n_unique_non_missing == limit + 1
    assert evidence.exact_distinct_non_missing_values is None
    assert evidence.most_frequent_count == 1
    assert evidence.singleton_count == limit + 1
    _assert_ratio(evidence.most_frequent_ratio, 1 / (limit + 1))
    _assert_ratio(evidence.singleton_ratio, 1.0)
    assert interpret_series_precedence(series) is None
    _assert_bounded(evidence)


def test_high_cardinality_result_does_not_retain_a_frequency_table():
    series = pd.Series([f"v{index}" for index in range(100)])

    evidence = _collect(series)

    assert evidence.exact_distinct_non_missing_values is None
    assert evidence.most_frequent_count == 1
    assert evidence.singleton_count == 100
    _assert_bounded(evidence)
    assert interpret_series_precedence(series) is None


def test_heterogeneous_hashable_values_need_no_shared_order():
    series = pd.Series(["a", 1, (2,), "a", 3.5], dtype=object)
    original = series.copy(deep=True)

    evidence = _collect(series)

    pd.testing.assert_series_equal(series, original)
    retained = evidence.exact_distinct_non_missing_values
    assert retained == frozenset({"a", 1, (2,), 3.5})
    assert (2,) in retained
    assert 1 in retained
    assert 3.5 in retained
    assert evidence.most_frequent_count == 2
    assert evidence.singleton_count == 3
    _assert_ratio(evidence.most_frequent_ratio, 2 / 5)
    _assert_ratio(evidence.singleton_ratio, 3 / 4)
    assert not any(isinstance(value, str) and value != "a" for value in retained)


def test_python_equal_values_stay_one_pandas_frequency_key():
    series = pd.Series([True, 1, 1, True], dtype=object)

    evidence = _collect(series)
    retained = evidence.exact_distinct_non_missing_values

    assert evidence.basic.n_unique_non_missing == 1
    assert evidence.most_frequent_count == 4
    assert evidence.singleton_count == 0
    assert retained is not None
    assert len(retained) == 1
    retained_value = next(iter(retained))
    assert retained_value == 1
    assert not isinstance(retained_value, str)


def test_unobserved_categorical_levels_are_not_frequency_keys():
    series = pd.Series(pd.Categorical(["a", "a"], categories=["a", "b", "c"]))

    evidence = _collect(series)

    assert evidence.basic.n_unique_non_missing == 1
    assert evidence.most_frequent_count == 2
    assert evidence.singleton_count == 0
    assert evidence.exact_distinct_non_missing_values == frozenset({"a"})
    assert "b" not in evidence.exact_distinct_non_missing_values
    assert "c" not in evidence.exact_distinct_non_missing_values
    assert interpret_series_precedence(series) is not None
    assert interpret_series_precedence(series).semantic_type is SemanticType.CONSTANT


def test_unhashable_values_fail_without_a_second_normalization_policy():
    series = pd.Series([[1], [2]])
    original = series.copy(deep=True)

    evidence = collect_basic_column_evidence(series)
    assert evidence.n_unique_non_missing is None

    basic = BasicColumnEvidence(
        n_total=2,
        n_missing=0,
        n_non_missing=2,
        n_unique_non_missing=2,
    )
    with pytest.raises(TypeError, match="unhashable"):
        collect_frequency_evidence(series, basic)

    pd.testing.assert_series_equal(series, original)
    assert series.tolist() == [[1], [2]]


def test_unhashable_values_above_the_retention_limit_still_fail():
    width = EXACT_DISTINCT_VALUE_RETENTION_LIMIT + 1
    series = pd.Series([[index] for index in range(width)])
    basic = BasicColumnEvidence(
        n_total=width,
        n_missing=0,
        n_non_missing=width,
        n_unique_non_missing=width,
    )

    with pytest.raises(TypeError, match="unhashable"):
        collect_frequency_evidence(series, basic)

    assert series.tolist() == [[index] for index in range(width)]


def test_frequency_observations_do_not_select_a_semantic_type():
    dominant = pd.Series(["a"] * 9 + ["b"])
    unique = pd.Series(["alpha", "beta", "gamma"])
    binary_codes = pd.Series([0, 1, 1, 0])

    dominant_evidence = _collect(dominant)
    unique_evidence = _collect(unique)
    binary_evidence = _collect(binary_codes)

    _assert_ratio(dominant_evidence.most_frequent_ratio, 0.9)
    assert interpret_series_precedence(dominant) is None
    _assert_ratio(unique_evidence.singleton_ratio, 1.0)
    assert interpret_series_precedence(unique) is None
    assert binary_evidence.exact_distinct_non_missing_values == frozenset({0, 1})
    assert binary_evidence.basic.n_unique_non_missing == 2
    assert interpret_series_precedence(binary_codes) is None


def test_existing_semantic_chain_is_unchanged_beside_frequency_evidence():
    empty = pd.Series([None, None])
    constant = pd.Series([7, None, 7])
    boolean = pd.Series([True, False, pd.NA], dtype="boolean")
    constant_boolean = pd.Series([True, True], dtype=bool)
    native = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))
    aware = pd.Series(pd.to_datetime(["2026-01-01T12:00:00Z", "2026-01-02T12:00:00Z"]))
    duration = pd.Series(pd.to_timedelta(["1 day", "2 days"]))

    empty_reading = interpret_series_precedence(empty)
    constant_reading = interpret_series_precedence(constant)
    boolean_reading = interpret_series_precedence(boolean)
    constant_boolean_reading = interpret_series_precedence(constant_boolean)
    native_reading = interpret_series_precedence(native)
    aware_reading = interpret_series_precedence(aware)
    duration_reading = interpret_series_precedence(duration)
    boolean_evidence = _collect(boolean)
    duration_evidence = _collect(duration)

    assert empty_reading is not None
    assert empty_reading.semantic_type is SemanticType.EMPTY
    assert empty_reading.confidence is Confidence.HIGH
    assert empty_reading.source is InferenceSource.INFERRED
    assert constant_reading is not None
    assert constant_reading.semantic_type is SemanticType.CONSTANT
    assert constant_reading.source is InferenceSource.INFERRED
    assert constant_boolean_reading is not None
    assert constant_boolean_reading.semantic_type is SemanticType.CONSTANT
    assert boolean_reading is not None
    assert boolean_reading.semantic_type is SemanticType.BOOLEAN
    assert boolean_reading.confidence is Confidence.HIGH
    assert boolean_reading.source is InferenceSource.PHYSICAL_DTYPE
    assert boolean_reading.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert boolean_reading.evidence[0].statement == "physical dtype is boolean"
    assert boolean_evidence.most_frequent_count == 1
    assert boolean_evidence.singleton_count == 2
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
    assert duration_evidence.basic.n_unique_non_missing == 2
    assert duration_evidence.exact_distinct_non_missing_values is not None


def test_precedence_does_not_collect_frequency_evidence(
    monkeypatch: pytest.MonkeyPatch,
):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("frequency evidence was collected during precedence")

    monkeypatch.setattr(pd.Series, "value_counts", _forbidden)

    empty = interpret_series_precedence(pd.Series([None, None]))
    constant = interpret_series_precedence(pd.Series([4, 4, 4]))
    ordinary = interpret_series_precedence(pd.Series([1, 2, 3]))

    assert empty is not None
    assert empty.semantic_type is SemanticType.EMPTY
    assert constant is not None
    assert constant.semantic_type is SemanticType.CONSTANT
    assert ordinary is None


def test_collection_uses_one_frequency_pass_and_not_basic_counts(
    monkeypatch: pytest.MonkeyPatch,
):
    series = pd.Series(["a", "a", "b", "c", "c", "d"])
    basic = collect_basic_column_evidence(series)
    calls = {"value_counts": 0}
    original = pd.Series.value_counts

    def _value_counts(
        self: pd.Series,
        *args: object,
        **kwargs: object,
    ) -> pd.Series:
        calls["value_counts"] += 1
        return original(self, *args, **kwargs)

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("basic counts were recomputed")

    monkeypatch.setattr(pd.Series, "value_counts", _value_counts)
    monkeypatch.setattr(pd.Series, "nunique", _forbidden)
    monkeypatch.setattr(pd.Series, "isna", _forbidden)

    evidence = collect_frequency_evidence(series, basic)

    assert calls["value_counts"] == 1
    assert evidence.most_frequent_count == 2
    assert evidence.singleton_count == 2
    assert evidence.basic is basic


def test_frequency_collection_rejects_a_mismatched_basic_evidence():
    series = pd.Series(["a", "b"])
    basic = BasicColumnEvidence(
        n_total=2,
        n_missing=0,
        n_non_missing=2,
        n_unique_non_missing=1,
    )

    with pytest.raises(ValueError, match="do not match BasicColumnEvidence"):
        collect_frequency_evidence(series, basic)


def test_frequency_collection_rejects_the_wrong_input_types():
    basic = _basic(1, 1)

    with pytest.raises(TypeError, match="pandas Series"):
        collect_frequency_evidence(["a"], basic)
    with pytest.raises(TypeError, match="BasicColumnEvidence"):
        collect_frequency_evidence(pd.Series(["a"]), "basic")


def test_frequency_evidence_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "FrequencyEvidence")
    assert not hasattr(pytics, "collect_frequency_evidence")
    assert not hasattr(pytics, "EXACT_DISTINCT_VALUE_RETENTION_LIMIT")
    assert not hasattr(semantics_package, "FrequencyEvidence")
    assert not hasattr(semantics_package, "collect_frequency_evidence")


@pytest.mark.parametrize(
    ("arguments", "error"),
    [
        (
            {
                "basic": "counts",
                "most_frequent_count": 0,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset(),
            },
            TypeError,
        ),
        (
            {
                "basic": _basic(0, 0),
                "most_frequent_count": True,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset(),
            },
            TypeError,
        ),
        (
            {
                "basic": _basic(0, 0),
                "most_frequent_count": -1,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset(),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(0, 0),
                "most_frequent_count": 1,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset(),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(3, 0),
                "most_frequent_count": 1,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset(),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(3, 2),
                "most_frequent_count": 0,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset({"a", "b"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(3, 2),
                "most_frequent_count": 4,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset({"a", "b"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(2, 2),
                "most_frequent_count": 1,
                "singleton_count": 3,
                "exact_distinct_non_missing_values": frozenset({"a", "b"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(3, 1),
                "most_frequent_count": 2,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset({"a"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(3, 1),
                "most_frequent_count": 3,
                "singleton_count": 1,
                "exact_distinct_non_missing_values": frozenset({"a"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(1, 1),
                "most_frequent_count": 1,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset({"a"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(4, 2),
                "most_frequent_count": 1,
                "singleton_count": 2,
                "exact_distinct_non_missing_values": frozenset({"a", "b"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(4, 2),
                "most_frequent_count": 2,
                "singleton_count": 2,
                "exact_distinct_non_missing_values": frozenset({"a", "b"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(5, 2),
                "most_frequent_count": 2,
                "singleton_count": 0,
                "exact_distinct_non_missing_values": frozenset({"a", "b"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(1, 1),
                "most_frequent_count": 1,
                "singleton_count": 1,
                "exact_distinct_non_missing_values": None,
            },
            TypeError,
        ),
        (
            {
                "basic": _basic(1, 1),
                "most_frequent_count": 1,
                "singleton_count": 1,
                "exact_distinct_non_missing_values": {"a"},
            },
            TypeError,
        ),
        (
            {
                "basic": _basic(2, 2),
                "most_frequent_count": 1,
                "singleton_count": 2,
                "exact_distinct_non_missing_values": frozenset({"a"}),
            },
            ValueError,
        ),
        (
            {
                "basic": _basic(40, 40),
                "most_frequent_count": 1,
                "singleton_count": 40,
                "exact_distinct_non_missing_values": frozenset({"a"}),
            },
            ValueError,
        ),
    ],
)
def test_inconsistent_frequency_evidence_is_rejected(
    arguments: dict[str, object],
    error: type[Exception],
):
    with pytest.raises(error):
        FrequencyEvidence(**arguments)


def test_direct_over_limit_evidence_keeps_ratios_on_basic_counts():
    evidence = FrequencyEvidence(
        basic=_basic(40, 40),
        most_frequent_count=1,
        singleton_count=40,
        exact_distinct_non_missing_values=None,
    )

    _assert_ratio(evidence.most_frequent_ratio, 1 / 40)
    _assert_ratio(evidence.singleton_ratio, 1.0)
    assert evidence.exact_distinct_non_missing_values is None
