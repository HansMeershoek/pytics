"""TSK-006: universal column evidence derived from the four basic counts."""

from __future__ import annotations

import math
from typing import Optional

import pandas as pd
import pytest

import pytics
import pytics.semantics.empty_constant as empty_constant
import pytics.semantics.physical as physical
import pytics.semantics.physical_boolean as physical_boolean
import pytics.semantics.physical_datetime as physical_datetime
import pytics.semantics.physical_timedelta as physical_timedelta
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.empty_constant import interpret_empty_or_constant
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_precedence_from_evidence
from pytics.semantics.physical_timedelta import interpret_series_precedence


def _assert_invariants(evidence: BasicColumnEvidence) -> None:
    assert evidence.n_total >= 0
    assert evidence.n_missing >= 0
    assert evidence.n_non_missing >= 0
    assert evidence.n_unique_non_missing >= 0
    assert evidence.n_missing <= evidence.n_total
    assert evidence.n_non_missing <= evidence.n_total
    assert evidence.n_missing + evidence.n_non_missing == evidence.n_total
    assert evidence.n_unique_non_missing <= evidence.n_non_missing
    assert type(evidence.n_total) is int
    assert type(evidence.n_missing) is int
    assert type(evidence.n_non_missing) is int
    assert type(evidence.n_unique_non_missing) is int


def _assert_ratio(value: Optional[float], expected: Optional[float]) -> None:
    if expected is None:
        assert value is None
        return
    assert type(value) is float
    assert value == expected
    assert not math.isnan(value)
    assert not math.isinf(value)


def _assert_derived(evidence: BasicColumnEvidence) -> None:
    _assert_invariants(evidence)
    if evidence.n_total == 0:
        _assert_ratio(evidence.missing_ratio, None)
    else:
        _assert_ratio(
            evidence.missing_ratio,
            evidence.n_missing / evidence.n_total,
        )
    if evidence.n_non_missing == 0:
        _assert_ratio(evidence.unique_ratio_non_missing, None)
    else:
        _assert_ratio(
            evidence.unique_ratio_non_missing,
            evidence.n_unique_non_missing / evidence.n_non_missing,
        )
    assert evidence.has_missing is (evidence.n_missing > 0)
    assert evidence.is_empty is (evidence.n_non_missing == 0)
    assert evidence.is_constant is (
        evidence.n_non_missing > 0 and evidence.n_unique_non_missing == 1
    )
    assert type(evidence.has_missing) is bool
    assert type(evidence.is_empty) is bool
    assert type(evidence.is_constant) is bool
    assert not hasattr(evidence, "unique_ratio")


def test_stored_fields_remain_the_four_primary_counts():
    evidence = BasicColumnEvidence(
        n_total=4,
        n_missing=1,
        n_non_missing=3,
        n_unique_non_missing=2,
    )

    assert set(BasicColumnEvidence.__dataclass_fields__) == {
        "n_total",
        "n_missing",
        "n_non_missing",
        "n_unique_non_missing",
    }
    _assert_derived(evidence)
    _assert_ratio(evidence.missing_ratio, 1 / 4)
    _assert_ratio(evidence.unique_ratio_non_missing, 2 / 3)
    assert evidence.has_missing is True
    assert evidence.is_empty is False
    assert evidence.is_constant is False


def test_mixed_series_counts_and_ratios():
    series = pd.Series([1, 1, 2, None])

    evidence = collect_basic_column_evidence(series)

    assert evidence == BasicColumnEvidence(4, 1, 3, 2)
    _assert_derived(evidence)
    _assert_ratio(evidence.missing_ratio, 1 / 4)
    _assert_ratio(evidence.unique_ratio_non_missing, 2 / 3)
    assert evidence.has_missing is True
    assert evidence.is_empty is False
    assert evidence.is_constant is False


def test_no_missing_values_have_a_zero_missing_ratio():
    series = pd.Series([1, 2, 3])

    evidence = collect_basic_column_evidence(series)

    _assert_derived(evidence)
    _assert_ratio(evidence.missing_ratio, 0.0)
    assert evidence.has_missing is False
    assert evidence.is_empty is False


def test_zero_length_series_has_undefined_ratios_and_is_empty():
    series = pd.Series([], dtype="float64")

    evidence = collect_basic_column_evidence(series)

    assert evidence.n_total == 0
    assert evidence.n_non_missing == 0
    _assert_derived(evidence)
    assert evidence.missing_ratio is None
    assert evidence.unique_ratio_non_missing is None
    assert evidence.is_empty is True
    assert evidence.is_constant is False
    assert evidence.has_missing is False


def test_all_missing_series_is_empty_and_not_constant():
    series = pd.Series([None, None, None])

    evidence = collect_basic_column_evidence(series)

    assert evidence.n_total == 3
    assert evidence.n_missing == 3
    assert evidence.n_non_missing == 0
    _assert_derived(evidence)
    _assert_ratio(evidence.missing_ratio, 1.0)
    assert evidence.unique_ratio_non_missing is None
    assert evidence.has_missing is True
    assert evidence.is_empty is True
    assert evidence.is_constant is False


def test_constant_non_missing_series():
    series = pd.Series([7, 7, 7])

    evidence = collect_basic_column_evidence(series)

    _assert_derived(evidence)
    _assert_ratio(evidence.unique_ratio_non_missing, 1 / 3)
    _assert_ratio(evidence.missing_ratio, 0.0)
    assert evidence.is_constant is True
    assert evidence.is_empty is False


def test_constant_plus_missing_stays_constant():
    series = pd.Series([7, None, 7])

    evidence = collect_basic_column_evidence(series)

    _assert_derived(evidence)
    _assert_ratio(evidence.unique_ratio_non_missing, 1 / 2)
    _assert_ratio(evidence.missing_ratio, 1 / 3)
    assert evidence.is_constant is True
    assert evidence.is_empty is False
    assert evidence.has_missing is True


def test_one_row_non_missing_series_is_constant():
    series = pd.Series([7])

    evidence = collect_basic_column_evidence(series)

    _assert_derived(evidence)
    _assert_ratio(evidence.unique_ratio_non_missing, 1.0)
    assert evidence.is_constant is True
    assert evidence.is_empty is False


def test_fully_unique_non_missing_ratio_is_one_without_identifier():
    series = pd.Series([1, 2, 3])

    evidence = collect_basic_column_evidence(series)
    reading = interpret_series_precedence(series)

    _assert_derived(evidence)
    _assert_ratio(evidence.unique_ratio_non_missing, 1.0)
    assert evidence.is_constant is False
    assert reading is None
    assert interpret_empty_or_constant(series) is None


def test_missing_like_literals_stay_observed_values():
    series = pd.Series(["", "NA", "N/A", "null", "?"])

    evidence = collect_basic_column_evidence(series)

    assert evidence.n_total == 5
    assert evidence.n_missing == 0
    assert evidence.n_non_missing == 5
    assert evidence.n_unique_non_missing == 5
    _assert_derived(evidence)
    _assert_ratio(evidence.missing_ratio, 0.0)
    _assert_ratio(evidence.unique_ratio_non_missing, 1.0)
    assert evidence.has_missing is False
    assert evidence.is_empty is False
    assert interpret_empty_or_constant(series) is None


def test_unhashable_values_raise_and_are_not_normalized():
    series = pd.Series([[1], [2]])
    original = series.copy(deep=True)

    with pytest.raises(TypeError, match="unhashable"):
        collect_basic_column_evidence(series)

    pd.testing.assert_series_equal(series, original)


def test_derived_facts_agree_with_empty_and_constant_readings():
    empty = pd.Series([None, None])
    constant = pd.Series([7, None, 7])
    ordinary = pd.Series([1, 1, 2, None])

    empty_evidence = collect_basic_column_evidence(empty)
    constant_evidence = collect_basic_column_evidence(constant)
    ordinary_evidence = collect_basic_column_evidence(ordinary)
    empty_reading = interpret_empty_or_constant(empty)
    constant_reading = interpret_empty_or_constant(constant)
    ordinary_reading = interpret_empty_or_constant(ordinary)

    assert empty_evidence.is_empty is True
    assert empty_evidence.is_constant is False
    assert empty_reading is not None
    assert empty_reading.semantic_type is SemanticType.EMPTY
    assert empty_reading.confidence is Confidence.HIGH
    assert empty_reading.source is InferenceSource.INFERRED
    assert empty_reading.evidence[0].statement == (
        "0 non-missing observations out of 2"
    )
    assert constant_evidence.is_constant is True
    assert constant_evidence.is_empty is False
    assert constant_reading is not None
    assert constant_reading.semantic_type is SemanticType.CONSTANT
    assert constant_reading.confidence is Confidence.HIGH
    assert constant_reading.source is InferenceSource.INFERRED
    assert constant_reading.evidence[0].statement == (
        "1 distinct non-missing value among 2 non-missing observations out of 3"
    )
    assert ordinary_evidence.is_empty is False
    assert ordinary_evidence.is_constant is False
    assert ordinary_reading is None


def test_physical_readings_stay_on_the_same_precedence():
    boolean = pd.Series([True, False, pd.NA], dtype="boolean")
    constant_boolean = pd.Series([True, True], dtype=bool)
    native = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))
    aware = pd.Series(
        pd.to_datetime(
            [
                "2026-01-01T12:00:00Z",
                "2026-01-02T12:00:00Z",
            ]
        )
    )
    duration = pd.Series(pd.to_timedelta(["1 day", "2 days"]))

    boolean_evidence = collect_basic_column_evidence(boolean)
    boolean_reading = interpret_series_precedence(boolean)
    constant_reading = interpret_series_precedence(constant_boolean)
    native_reading = interpret_series_precedence(native)
    aware_reading = interpret_series_precedence(aware)
    duration_reading = interpret_series_precedence(duration)

    assert boolean_evidence.is_empty is False
    assert boolean_evidence.is_constant is False
    assert boolean_reading is not None
    assert boolean_reading.semantic_type is SemanticType.BOOLEAN
    assert boolean_reading.confidence is Confidence.HIGH
    assert boolean_reading.source is InferenceSource.PHYSICAL_DTYPE
    assert boolean_reading.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert boolean_reading.evidence[0].statement == "physical dtype is boolean"
    assert constant_reading is not None
    assert constant_reading.semantic_type is SemanticType.CONSTANT
    assert constant_reading.source is InferenceSource.INFERRED
    assert native_reading is not None
    assert native_reading.semantic_type is SemanticType.DATETIME
    assert native_reading.physical.family is PhysicalDtypeFamily.DATETIME
    assert native_reading.evidence[0].statement == "physical dtype is datetime"
    assert aware_reading is not None
    assert aware_reading.semantic_type is SemanticType.DATETIME
    assert aware_reading.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert aware_reading.evidence[0].statement == (
        "physical dtype is timezone-aware datetime"
    )
    assert duration_reading is not None
    assert duration_reading.semantic_type is SemanticType.TIMEDELTA
    assert duration_reading.physical.family is PhysicalDtypeFamily.TIMEDELTA
    assert duration_reading.evidence[0].statement == "physical dtype is timedelta"
    assert duration_reading.confidence is Confidence.HIGH
    assert duration_reading.source is InferenceSource.PHYSICAL_DTYPE


def test_from_evidence_does_not_rescan_the_series(monkeypatch: pytest.MonkeyPatch):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("basic evidence was recomputed")

    monkeypatch.setattr(pd.Series, "isna", _forbidden)
    monkeypatch.setattr(pd.Series, "nunique", _forbidden)
    evidence = BasicColumnEvidence(4, 1, 3, 2)
    physical_dtype = classify_physical_dtype("int64")

    assert interpret_precedence_from_evidence(evidence, physical_dtype) is None
    assert evidence.is_empty is False
    assert evidence.is_constant is False


def test_series_precedence_classifies_and_collects_once(
    monkeypatch: pytest.MonkeyPatch,
):
    series = pd.Series([1, 1, 2, None])
    scans = {"isna": 0, "nunique": 0, "classify": 0}
    original_isna = pd.Series.isna
    original_nunique = pd.Series.nunique
    real_classify = physical.classify_physical_dtype

    def _isna(self: pd.Series, *args: object, **kwargs: object) -> pd.Series:
        scans["isna"] += 1
        return original_isna(self, *args, **kwargs)

    def _nunique(self: pd.Series, *args: object, **kwargs: object) -> int:
        scans["nunique"] += 1
        return original_nunique(self, *args, **kwargs)

    def _classify(source: object) -> object:
        scans["classify"] += 1
        return real_classify(source)

    monkeypatch.setattr(pd.Series, "isna", _isna)
    monkeypatch.setattr(pd.Series, "nunique", _nunique)
    for module in (
        empty_constant,
        physical_boolean,
        physical_datetime,
        physical_timedelta,
    ):
        monkeypatch.setattr(module, "classify_physical_dtype", _classify)

    assert interpret_series_precedence(series) is None
    assert scans == {"isna": 1, "nunique": 1, "classify": 1}


def test_derived_names_are_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "BasicColumnEvidence")
    assert not hasattr(pytics, "collect_basic_column_evidence")
    assert not hasattr(pytics, "missing_ratio")
    assert not hasattr(pytics, "unique_ratio_non_missing")
