"""Slice 005: physical Timedelta after Empty, Constant, Boolean, and Datetime."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

import pytics
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_datetime import (
    interpret_series_precedence as interpret_through_physical_datetime,
)
from pytics.semantics.physical_timedelta import interpret_precedence_from_evidence
from pytics.semantics.physical_timedelta import interpret_series_precedence


def _interpret(series: pd.Series):
    return interpret_series_precedence(series)


def _assert_timedelta(series: pd.Series) -> None:
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.TIMEDELTA
    assert result.semantic_type is not SemanticType.DATETIME
    assert result.confidence is Confidence.HIGH
    assert type(result.confidence) is Confidence
    assert result.source is InferenceSource.PHYSICAL_DTYPE
    assert result.source is not InferenceSource.INFERRED
    assert result.physical == classify_physical_dtype(series)
    assert result.physical.family is PhysicalDtypeFamily.TIMEDELTA
    assert result.physical.categorical_ordered is None
    assert result.subtype is None
    assert result.alternatives == ()
    assert result.evidence == (SemanticEvidence("physical dtype is timedelta"),)


def _assert_precedence(
    series: pd.Series,
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
) -> None:
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is semantic_type
    assert result.semantic_type is not SemanticType.TIMEDELTA
    assert result.confidence is Confidence.HIGH
    assert result.source is InferenceSource.INFERRED
    assert result.physical == classify_physical_dtype(series)
    assert result.physical.family is family
    assert result.subtype is None
    assert result.alternatives == ()
    assert len(result.evidence) == 1
    assert isinstance(result.evidence[0], SemanticEvidence)


def test_physical_timedelta_is_timedelta():
    series = pd.Series(pd.to_timedelta(["1 day", "2 days"]))

    _assert_timedelta(series)


def test_timedelta_with_nat_is_timedelta():
    series = pd.Series(
        [
            pd.Timedelta(days=1),
            pd.NaT,
            pd.Timedelta(days=3),
        ]
    )

    _assert_timedelta(series)


def test_all_nat_timedelta_is_empty():
    series = pd.Series([pd.NaT, pd.NaT], dtype="timedelta64[ns]")

    _assert_precedence(series, SemanticType.EMPTY, PhysicalDtypeFamily.TIMEDELTA)
    assert _interpret(series).evidence[0].statement == (
        "0 non-missing observations out of 2"
    )


def test_zero_length_timedelta_is_empty():
    series = pd.Series([], dtype="timedelta64[ns]")

    _assert_precedence(series, SemanticType.EMPTY, PhysicalDtypeFamily.TIMEDELTA)
    assert _interpret(series).evidence[0].statement == (
        "0 non-missing observations out of 0"
    )


def test_constant_timedelta_is_constant():
    duration = pd.Timedelta(days=1)
    series = pd.Series([duration, duration])

    _assert_precedence(
        series,
        SemanticType.CONSTANT,
        PhysicalDtypeFamily.TIMEDELTA,
    )
    assert _interpret(series).evidence[0].statement == (
        "1 distinct non-missing value among 2 non-missing observations out of 2"
    )


def test_constant_timedelta_with_nat_is_constant():
    duration = pd.Timedelta(days=1)
    series = pd.Series([duration, pd.NaT, duration])

    _assert_precedence(
        series,
        SemanticType.CONSTANT,
        PhysicalDtypeFamily.TIMEDELTA,
    )
    assert _interpret(series).evidence[0].statement == (
        "1 distinct non-missing value among 2 non-missing observations out of 3"
    )


def test_native_datetime_stays_datetime():
    series = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.DATETIME
    assert result.semantic_type is not SemanticType.TIMEDELTA
    assert result.confidence is Confidence.HIGH
    assert result.source is InferenceSource.PHYSICAL_DTYPE
    assert result.physical.family is PhysicalDtypeFamily.DATETIME
    assert result.evidence == (SemanticEvidence("physical dtype is datetime"),)


def test_timezone_aware_datetime_stays_datetime():
    series = pd.Series(
        pd.to_datetime(
            [
                "2026-01-01T12:00:00Z",
                "2026-01-02T12:00:00Z",
            ]
        )
    )
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.DATETIME
    assert result.semantic_type is not SemanticType.TIMEDELTA
    assert result.confidence is Confidence.HIGH
    assert result.source is InferenceSource.PHYSICAL_DTYPE
    assert result.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert result.evidence == (
        SemanticEvidence("physical dtype is timezone-aware datetime"),
    )
    assert series.dtype.tz is not None


def test_physical_boolean_stays_boolean():
    series = pd.Series([True, False, True], dtype=bool)
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.BOOLEAN
    assert result.semantic_type is not SemanticType.TIMEDELTA
    assert result.confidence is Confidence.HIGH
    assert result.source is InferenceSource.PHYSICAL_DTYPE
    assert result.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert result.evidence == (SemanticEvidence("physical dtype is boolean"),)


def test_duration_like_strings_have_no_interpretation():
    cases = (
        pd.Series(["1 day", "2 days"]),
        pd.Series(["5 hours", "10 hours"]),
        pd.Series(["90 minutes", "120 minutes"]),
    )

    for series in cases:
        assert _interpret(series) is None
        physical = classify_physical_dtype(series)
        assert physical.family is PhysicalDtypeFamily.STRING
        assert physical.family is not PhysicalDtypeFamily.TIMEDELTA


def test_single_duration_like_string_stays_constant():
    series = pd.Series(["1 day"])
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.CONSTANT
    assert result.semantic_type is not SemanticType.TIMEDELTA
    assert result.source is InferenceSource.INFERRED
    assert result.physical.family is PhysicalDtypeFamily.STRING


def test_clock_like_strings_have_no_interpretation():
    series = pd.Series(["00:30:00", "01:15:00"])

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.STRING


def test_numeric_duration_like_values_have_no_interpretation():
    seconds = pd.Series([30, 60, 90])
    milliseconds = pd.Series([1000, 2000, 3000])

    for series in (seconds, milliseconds):
        assert _interpret(series) is None
        assert classify_physical_dtype(series).family is PhysicalDtypeFamily.INTEGER


def test_floating_duration_like_values_have_no_interpretation():
    series = pd.Series([0.5, 1.5, 2.5])

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.FLOATING


def test_object_timedelta_values_have_no_interpretation():
    python_durations = pd.Series(
        [timedelta(days=1), timedelta(days=2)],
        dtype=object,
    )
    pandas_durations = pd.Series(
        [pd.Timedelta(days=1), pd.Timedelta(days=2)],
        dtype=object,
    )

    for series in (python_durations, pandas_durations):
        assert _interpret(series) is None
        assert classify_physical_dtype(series).family is PhysicalDtypeFamily.OBJECT
        assert str(series.dtype) == "object"


def test_categorical_timedeltas_have_no_interpretation():
    series = pd.Series(pd.Categorical(pd.to_timedelta(["1 day", "2 days"])))

    assert _interpret(series) is None
    physical = classify_physical_dtype(series)
    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert physical.categorical_ordered is False


def test_period_has_no_interpretation():
    series = pd.Series(pd.period_range("2026-01", periods=3, freq="M"))

    assert _interpret(series) is None
    physical = classify_physical_dtype(series)
    assert physical.family is PhysicalDtypeFamily.PERIOD
    assert physical.family is not PhysicalDtypeFamily.TIMEDELTA


def test_empty_and_constant_precedence_unchanged():
    empty = _interpret(pd.Series([np.nan, np.nan]))
    constant = _interpret(pd.Series([5, 5, 5]))
    constant_bool = _interpret(pd.Series([True, True], dtype=bool))

    assert empty is not None and empty.semantic_type is SemanticType.EMPTY
    assert empty.source is InferenceSource.INFERRED
    assert empty.physical.family is not PhysicalDtypeFamily.TIMEDELTA
    assert constant is not None and constant.semantic_type is SemanticType.CONSTANT
    assert constant.source is InferenceSource.INFERRED
    assert constant.alternatives == ()
    assert constant_bool is not None
    assert constant_bool.semantic_type is SemanticType.CONSTANT
    assert constant_bool.semantic_type is not SemanticType.BOOLEAN


def test_slice_004_chain_does_not_read_timedelta():
    series = pd.Series(pd.to_timedelta(["1 day", "2 days"]))

    assert interpret_through_physical_datetime(series) is None
    assert _interpret(series).semantic_type is SemanticType.TIMEDELTA


def test_column_name_does_not_create_a_timedelta_reading():
    named_strings = pd.Series(["1 day", "2 days"], name="duration")
    named_timedeltas = pd.Series(
        pd.to_timedelta(["1 day", "2 days"]),
        name="event_time",
    )

    assert _interpret(named_strings) is None
    assert _interpret(named_timedeltas).semantic_type is SemanticType.TIMEDELTA


def test_from_evidence_reuses_counts_and_keeps_precedence():
    timedelta = classify_physical_dtype("timedelta64[ns]")
    native = classify_physical_dtype("datetime64[ns]")
    aware = classify_physical_dtype("datetime64[ns, UTC]")
    boolean = classify_physical_dtype("boolean")
    integer = classify_physical_dtype("int64")
    floating = classify_physical_dtype("float64")
    text = classify_physical_dtype("string")
    obj = classify_physical_dtype("object")
    categorical = classify_physical_dtype("category")
    period = classify_physical_dtype("period[M]")
    several = BasicColumnEvidence(4, 1, 3, 2)
    constant = BasicColumnEvidence(3, 1, 2, 1)
    empty = BasicColumnEvidence(2, 2, 0, 0)

    reading = interpret_precedence_from_evidence(several, timedelta)

    assert reading is not None
    assert reading.semantic_type is SemanticType.TIMEDELTA
    assert reading.semantic_type is not SemanticType.DATETIME
    assert reading.confidence is Confidence.HIGH
    assert type(reading.confidence) is Confidence
    assert reading.source is InferenceSource.PHYSICAL_DTYPE
    assert reading.physical is timedelta
    assert reading.physical.family is PhysicalDtypeFamily.TIMEDELTA
    assert reading.subtype is None
    assert reading.alternatives == ()
    assert reading.evidence == (SemanticEvidence("physical dtype is timedelta"),)
    assert (
        interpret_precedence_from_evidence(constant, timedelta).semantic_type
        is SemanticType.CONSTANT
    )
    assert (
        interpret_precedence_from_evidence(empty, timedelta).semantic_type
        is SemanticType.EMPTY
    )
    assert (
        interpret_precedence_from_evidence(several, native).semantic_type
        is SemanticType.DATETIME
    )
    assert (
        interpret_precedence_from_evidence(several, aware).semantic_type
        is SemanticType.DATETIME
    )
    assert (
        interpret_precedence_from_evidence(several, boolean).semantic_type
        is SemanticType.BOOLEAN
    )
    assert interpret_precedence_from_evidence(several, integer) is None
    assert interpret_precedence_from_evidence(several, floating) is None
    assert interpret_precedence_from_evidence(several, text) is None
    assert interpret_precedence_from_evidence(several, obj) is None
    assert interpret_precedence_from_evidence(several, categorical) is None
    assert interpret_precedence_from_evidence(several, period) is None
    assert "UNKNOWN" not in SemanticType.__members__
    assert "OTHER" not in SemanticType.__members__
    assert "UNCLASSIFIED" not in SemanticType.__members__
    assert "DURATION" not in SemanticType.__members__


def test_from_evidence_rejects_bad_inputs():
    evidence = BasicColumnEvidence(2, 0, 2, 2)
    physical = classify_physical_dtype("timedelta64[ns]")

    with pytest.raises(TypeError):
        interpret_precedence_from_evidence(
            evidence,
            "timedelta64[ns]",  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        interpret_precedence_from_evidence(
            object(),  # type: ignore[arg-type]
            physical,
        )


def test_non_series_is_rejected():
    frame = pd.DataFrame({"duration": pd.to_timedelta(["1 day", "2 days"])})

    with pytest.raises(TypeError):
        interpret_series_precedence(frame)  # type: ignore[arg-type]


def test_series_is_unchanged_after_inference():
    durations = pd.Series(
        pd.to_timedelta(["1 day", "2 days", "3 days"]),
        index=[2, 0, 1],
        name="duration",
    )
    with_nat = pd.Series(
        [
            pd.Timedelta(days=1),
            pd.NaT,
            pd.Timedelta(days=3),
        ],
        index=["a", "b", "c"],
        name="duration",
    )
    objects = pd.Series(
        [timedelta(days=1), timedelta(days=2)],
        dtype=object,
        index=["a", "b"],
        name="duration",
    )
    categorical = pd.Series(
        pd.Categorical(pd.to_timedelta(["1 day", "2 days"])),
        index=[5, 6],
        name="duration",
    )
    numeric = pd.Series([30, 60, 90], index=[1, 2, 3], name="seconds")
    text = pd.Series(
        ["1 day", "2 days"],
        index=["x", "y"],
        name="duration",
    )
    cases = (durations, with_nat, objects, categorical, numeric, text)
    originals = [series.copy(deep=True) for series in cases]
    categories = list(categorical.cat.categories)
    ordered = bool(categorical.cat.ordered)

    for series in cases:
        _interpret(series)

    for series, original in zip(cases, originals):
        pd.testing.assert_series_equal(series, original)
    assert list(categorical.cat.categories) == categories
    assert bool(categorical.cat.ordered) is ordered
    assert list(durations.index) == [2, 0, 1]
    assert durations.name == "duration"
    assert objects.dtype == object
    assert str(with_nat.dtype).startswith("timedelta64")


def test_slice_005_names_are_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "interpret_series_precedence")
    assert not hasattr(pytics, "interpret_precedence_from_evidence")
    assert not hasattr(pytics, "datetime_precedence_from_evidence")
