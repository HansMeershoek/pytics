"""Slice 004: physical Datetime after Empty, Constant, and physical Boolean."""

from __future__ import annotations

from datetime import datetime

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
from pytics.semantics.physical_boolean import (
    interpret_empty_constant_or_physical_boolean,
)
from pytics.semantics.physical_datetime import interpret_precedence_from_evidence
from pytics.semantics.physical_datetime import interpret_series_precedence


def _interpret(series: pd.Series):
    return interpret_series_precedence(series)


def _assert_datetime(
    series: pd.Series,
    family: PhysicalDtypeFamily,
    statement: str,
) -> None:
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.DATETIME
    assert result.confidence is Confidence.HIGH
    assert type(result.confidence) is Confidence
    assert result.source is InferenceSource.PHYSICAL_DTYPE
    assert result.source is not InferenceSource.INFERRED
    assert result.physical == classify_physical_dtype(series)
    assert result.physical.family is family
    assert result.physical.categorical_ordered is None
    assert result.subtype is None
    assert result.alternatives == ()
    assert result.evidence == (SemanticEvidence(statement),)


def _assert_precedence(
    series: pd.Series,
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
) -> None:
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is semantic_type
    assert result.semantic_type is not SemanticType.DATETIME
    assert result.confidence is Confidence.HIGH
    assert result.source is InferenceSource.INFERRED
    assert result.physical == classify_physical_dtype(series)
    assert result.physical.family is family
    assert result.subtype is None
    assert result.alternatives == ()
    assert len(result.evidence) == 1
    assert isinstance(result.evidence[0], SemanticEvidence)


def test_native_datetime_is_datetime():
    series = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))

    _assert_datetime(
        series,
        PhysicalDtypeFamily.DATETIME,
        "physical dtype is datetime",
    )
    assert getattr(series.dtype, "tz", None) is None


def test_datetime_with_nat_is_datetime():
    series = pd.Series(
        [
            pd.Timestamp("2026-01-01"),
            pd.NaT,
            pd.Timestamp("2026-01-02"),
        ]
    )

    _assert_datetime(
        series,
        PhysicalDtypeFamily.DATETIME,
        "physical dtype is datetime",
    )


def test_timezone_aware_datetime_is_datetime():
    series = pd.Series(
        pd.to_datetime(
            [
                "2026-01-01T12:00:00Z",
                "2026-01-02T12:00:00Z",
            ]
        )
    )

    _assert_datetime(
        series,
        PhysicalDtypeFamily.DATETIME_TZ_AWARE,
        "physical dtype is timezone-aware datetime",
    )
    assert series.dtype.tz is not None


def test_all_nat_datetime_is_empty():
    series = pd.Series([pd.NaT, pd.NaT], dtype="datetime64[ns]")

    _assert_precedence(series, SemanticType.EMPTY, PhysicalDtypeFamily.DATETIME)
    assert _interpret(series).evidence[0].statement == (
        "0 non-missing observations out of 2"
    )


def test_zero_length_datetime_is_empty():
    series = pd.Series([], dtype="datetime64[ns]")

    _assert_precedence(series, SemanticType.EMPTY, PhysicalDtypeFamily.DATETIME)
    assert _interpret(series).evidence[0].statement == (
        "0 non-missing observations out of 0"
    )


def test_constant_datetime_is_constant():
    stamp = pd.Timestamp("2026-01-01")
    series = pd.Series([stamp, stamp])

    _assert_precedence(
        series,
        SemanticType.CONSTANT,
        PhysicalDtypeFamily.DATETIME,
    )
    assert _interpret(series).evidence[0].statement == (
        "1 distinct non-missing value among 2 non-missing observations out of 2"
    )


def test_constant_datetime_with_nat_is_constant():
    stamp = pd.Timestamp("2026-01-01")
    series = pd.Series([stamp, pd.NaT, stamp])

    _assert_precedence(
        series,
        SemanticType.CONSTANT,
        PhysicalDtypeFamily.DATETIME,
    )
    assert _interpret(series).evidence[0].statement == (
        "1 distinct non-missing value among 2 non-missing observations out of 3"
    )


def test_datetime_like_strings_have_no_interpretation():
    iso_dates = pd.Series(["2026-01-01", "2026-01-02"])
    us_dates = pd.Series(["01/02/2026", "03/04/2026"])
    zulu = pd.Series(
        [
            "2026-01-01T12:00:00Z",
            "2026-01-02T12:00:00Z",
        ]
    )

    for series in (iso_dates, us_dates, zulu):
        assert _interpret(series) is None
        physical = classify_physical_dtype(series)
        assert physical.family is PhysicalDtypeFamily.STRING
        assert physical.family is not PhysicalDtypeFamily.DATETIME
        assert physical.family is not PhysicalDtypeFamily.DATETIME_TZ_AWARE


def test_single_datetime_like_string_stays_constant():
    series = pd.Series(["2026-10-03T12:00:00Z"])
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.CONSTANT
    assert result.semantic_type is not SemanticType.DATETIME
    assert result.source is InferenceSource.INFERRED
    assert result.physical.family is PhysicalDtypeFamily.STRING


def test_object_datetime_values_have_no_interpretation():
    py_datetimes = pd.Series(
        [datetime(2026, 1, 1), datetime(2026, 1, 2)],
        dtype=object,
    )
    timestamps = pd.Series(
        [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")],
        dtype=object,
    )

    for series in (py_datetimes, timestamps):
        assert _interpret(series) is None
        assert classify_physical_dtype(series).family is PhysicalDtypeFamily.OBJECT
        assert str(series.dtype) == "object"


def test_integer_timestamps_have_no_interpretation():
    series = pd.Series([1_704_067_200, 1_704_153_600])

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.INTEGER


def test_floating_timestamps_have_no_interpretation():
    series = pd.Series([1_704_067_200.0, 1_704_153_600.0])

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.FLOATING


def test_timedelta_has_no_interpretation():
    series = pd.Series(pd.to_timedelta(["1 days", "2 days"]))
    result = _interpret(series)

    assert result is None
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.TIMEDELTA
    assert "TIMEDELTA" in SemanticType.__members__


def test_period_has_no_interpretation():
    series = pd.Series(pd.period_range("2026-01", periods=3, freq="M"))

    assert _interpret(series) is None
    physical = classify_physical_dtype(series)
    assert physical.family is PhysicalDtypeFamily.PERIOD
    assert physical.family is not PhysicalDtypeFamily.DATETIME


def test_categorical_timestamps_have_no_interpretation():
    series = pd.Series(pd.Categorical(pd.to_datetime(["2026-01-01", "2026-01-02"])))

    assert _interpret(series) is None
    physical = classify_physical_dtype(series)
    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert physical.categorical_ordered is False


def test_physical_boolean_still_boolean():
    series = pd.Series([True, False, True], dtype=bool)
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.BOOLEAN
    assert result.confidence is Confidence.HIGH
    assert result.source is InferenceSource.PHYSICAL_DTYPE
    assert result.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert result.evidence == (SemanticEvidence("physical dtype is boolean"),)
    assert result.alternatives == ()


def test_empty_and_constant_precedence_unchanged():
    empty = _interpret(pd.Series([np.nan, np.nan]))
    constant = _interpret(pd.Series([5, 5, 5]))
    constant_bool = _interpret(pd.Series([True, True], dtype=bool))

    assert empty is not None and empty.semantic_type is SemanticType.EMPTY
    assert empty.source is InferenceSource.INFERRED
    assert constant is not None and constant.semantic_type is SemanticType.CONSTANT
    assert constant.source is InferenceSource.INFERRED
    assert constant.alternatives == ()
    assert constant_bool is not None
    assert constant_bool.semantic_type is SemanticType.CONSTANT
    assert constant_bool.semantic_type is not SemanticType.BOOLEAN


def test_slice_003_chain_does_not_read_datetime():
    series = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))

    assert interpret_empty_constant_or_physical_boolean(series) is None
    assert _interpret(series).semantic_type is SemanticType.DATETIME


def test_column_name_does_not_create_a_datetime_reading():
    named_strings = pd.Series(
        ["2026-01-01", "2026-01-02"],
        name="event_time",
    )
    named_datetimes = pd.Series(
        pd.to_datetime(["2026-01-01", "2026-01-02"]),
        name="measurement",
    )

    assert _interpret(named_strings) is None
    assert _interpret(named_datetimes).semantic_type is SemanticType.DATETIME


def test_from_evidence_reuses_counts_and_keeps_precedence():
    native = classify_physical_dtype("datetime64[ns]")
    aware = classify_physical_dtype("datetime64[ns, UTC]")
    boolean = classify_physical_dtype("boolean")
    timedelta = classify_physical_dtype("timedelta64[ns]")
    period = classify_physical_dtype("period[M]")
    several = BasicColumnEvidence(4, 1, 3, 2)
    constant = BasicColumnEvidence(3, 1, 2, 1)
    empty = BasicColumnEvidence(2, 2, 0, 0)

    native_reading = interpret_precedence_from_evidence(several, native)
    aware_reading = interpret_precedence_from_evidence(several, aware)

    assert native_reading is not None
    assert native_reading.semantic_type is SemanticType.DATETIME
    assert native_reading.confidence is Confidence.HIGH
    assert native_reading.source is InferenceSource.PHYSICAL_DTYPE
    assert native_reading.physical is native
    assert native_reading.physical.family is PhysicalDtypeFamily.DATETIME
    assert native_reading.evidence == (SemanticEvidence("physical dtype is datetime"),)
    assert aware_reading is not None
    assert aware_reading.semantic_type is SemanticType.DATETIME
    assert aware_reading.physical is aware
    assert aware_reading.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert aware_reading.evidence == (
        SemanticEvidence("physical dtype is timezone-aware datetime"),
    )
    assert (
        interpret_precedence_from_evidence(constant, native).semantic_type
        is SemanticType.CONSTANT
    )
    assert (
        interpret_precedence_from_evidence(empty, aware).semantic_type
        is SemanticType.EMPTY
    )
    assert (
        interpret_precedence_from_evidence(several, boolean).semantic_type
        is SemanticType.BOOLEAN
    )
    assert interpret_precedence_from_evidence(several, timedelta) is None
    assert interpret_precedence_from_evidence(several, period) is None
    assert "UNKNOWN" not in SemanticType.__members__
    assert "OTHER" not in SemanticType.__members__
    assert "UNCLASSIFIED" not in SemanticType.__members__


def test_from_evidence_rejects_bad_inputs():
    evidence = BasicColumnEvidence(2, 0, 2, 2)
    physical = classify_physical_dtype("datetime64[ns]")

    with pytest.raises(TypeError):
        interpret_precedence_from_evidence(
            evidence,
            "datetime64[ns]",  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        interpret_precedence_from_evidence(
            object(),  # type: ignore[arg-type]
            physical,
        )


def test_non_series_is_rejected():
    frame = pd.DataFrame({"event_time": pd.to_datetime(["2026-01-01", "2026-01-02"])})

    with pytest.raises(TypeError):
        interpret_series_precedence(frame)  # type: ignore[arg-type]


def test_series_is_unchanged_after_inference():
    native = pd.Series(
        pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
        index=[2, 0, 1],
        name="event_time",
    )
    with_nat = pd.Series(
        [
            pd.Timestamp("2026-01-01"),
            pd.NaT,
            pd.Timestamp("2026-01-03"),
        ],
        index=["a", "b", "c"],
        name="event_time",
    )
    aware = pd.Series(
        pd.to_datetime(
            [
                "2026-01-01T12:00:00Z",
                "2026-01-02T12:00:00Z",
                "2026-01-03T12:00:00Z",
            ]
        ),
        index=[10, 20, 30],
        name="event_time",
    )
    objects = pd.Series(
        [datetime(2026, 1, 1), datetime(2026, 1, 2)],
        dtype=object,
        index=["a", "b"],
        name="event_time",
    )
    deltas = pd.Series(
        pd.to_timedelta(["1 days", "2 days"]),
        index=[1, 2],
        name="duration",
    )
    categorical = pd.Series(
        pd.Categorical(pd.to_datetime(["2026-01-01", "2026-01-02"])),
        index=[5, 6],
        name="event_time",
    )
    cases = (native, with_nat, aware, objects, deltas, categorical)
    originals = [series.copy(deep=True) for series in cases]
    aware_tz = aware.dtype.tz
    categories = list(categorical.cat.categories)
    ordered = bool(categorical.cat.ordered)

    for series in cases:
        _interpret(series)

    for series, original in zip(cases, originals):
        pd.testing.assert_series_equal(series, original)
    assert aware.dtype.tz == aware_tz
    assert list(categorical.cat.categories) == categories
    assert bool(categorical.cat.ordered) is ordered
    assert list(native.index) == [2, 0, 1]
    assert native.name == "event_time"
    assert objects.dtype == object


def test_slice_004_names_are_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "interpret_series_precedence")
    assert not hasattr(pytics, "interpret_precedence_from_evidence")
