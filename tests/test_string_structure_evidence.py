"""TSK-009: string-structure observations beside basic column evidence."""

from __future__ import annotations

import dataclasses
import inspect
import math
from dataclasses import fields
from typing import Optional

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.semantics as semantics_package
import pytics.semantics.empty_constant as empty_constant_module
import pytics.semantics.physical_boolean as physical_boolean_module
import pytics.semantics.physical_datetime as physical_datetime_module
import pytics.semantics.physical_timedelta as physical_timedelta_module
import pytics.semantics.string_structure_evidence as string_module
from pytics.semantics.column_evidence import AnalyticalInapplicability
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_series_precedence
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import (
    collect_string_structure_evidence,
)

_COUNT_FIELDS = (
    "empty_string_count",
    "whitespace_only_count",
    "contains_whitespace_count",
    "contains_alpha_count",
    "contains_digit_count",
    "contains_other_count",
)

_APPLICABILITY = "physical string dtype"


class _Token(str):
    """A ``str`` subclass used to pin the ``isinstance`` contract."""


def _collect(series: pd.Series) -> StringStructureEvidence:
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    evidence = collect_string_structure_evidence(series, basic, physical)
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
        "empty_string_count": 0,
        "whitespace_only_count": 0,
        "contains_whitespace_count": 0,
        "contains_alpha_count": 0,
        "contains_digit_count": 0,
        "contains_other_count": 0,
        "min_length": None,
        "max_length": None,
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


def _assert_invariants(evidence: StringStructureEvidence) -> None:
    basic = evidence.basic
    for name in _COUNT_FIELDS:
        value = getattr(evidence, name)
        assert type(value) is int
        assert 0 <= value <= basic.n_non_missing
    assert evidence.whitespace_only_count <= evidence.contains_whitespace_count
    assert (
        evidence.empty_string_count + evidence.whitespace_only_count
        <= basic.n_non_missing
    )
    if basic.n_non_missing == 0:
        assert evidence.min_length is None
        assert evidence.max_length is None
    else:
        assert type(evidence.min_length) is int
        assert type(evidence.max_length) is int
        assert evidence.min_length is not None
        assert evidence.max_length is not None
        assert 0 <= evidence.min_length <= evidence.max_length
        if evidence.empty_string_count > 0:
            assert evidence.min_length == 0
        if evidence.min_length == 0:
            assert evidence.empty_string_count > 0
    for name in (
        "empty_string_ratio",
        "whitespace_only_ratio",
        "contains_whitespace_ratio",
        "contains_alpha_ratio",
        "contains_digit_ratio",
        "contains_other_ratio",
    ):
        _assert_ratio(
            getattr(evidence, name),
            (
                None
                if basic.n_non_missing == 0
                else getattr(evidence, name.removesuffix("_ratio") + "_count")
                / basic.n_non_missing
            ),
        )


def test_string_structure_evidence_stores_structural_observations_only():
    evidence = _collect(pd.Series(["ab", "c-1"], dtype="string"))
    names = {field.name for field in fields(evidence)}

    assert names == {
        "basic",
        "empty_string_count",
        "whitespace_only_count",
        "contains_whitespace_count",
        "contains_alpha_count",
        "contains_digit_count",
        "contains_other_count",
        "min_length",
        "max_length",
    }
    assert "empty_string_ratio" not in names
    _assert_ratio(evidence.empty_string_ratio, 0.0)
    for absent in (
        "n_total",
        "n_missing",
        "n_non_missing",
        "n_unique_non_missing",
        "most_frequent_count",
        "word_count",
        "mean_word_count",
        "token_count",
        "pattern",
        "semantic_type",
        "confidence",
    ):
        assert absent not in names
        assert not hasattr(evidence, absent)
    assert not isinstance(evidence, BasicColumnEvidence)
    assert not issubclass(StringStructureEvidence, BasicColumnEvidence)
    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.empty_string_count = 0  # type: ignore[misc]


@pytest.mark.parametrize("dtype", ["string", "str"])
def test_native_string_dtype_records_structure_over_every_observation(dtype: str):
    series = pd.Series(["ab", "ab", "c"], dtype=dtype)
    evidence = _collect(series)

    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.STRING
    assert evidence.contains_alpha_count == 3
    assert evidence.contains_digit_count == 0
    assert evidence.empty_string_count == 0
    assert evidence.min_length == 1
    assert evidence.max_length == 2
    _assert_ratio(evidence.contains_alpha_ratio, 1.0)
    assert interpret_series_precedence(series) is None


def test_nullable_string_keeps_missing_values_out_of_the_structure_population():
    series = pd.Series(["a", pd.NA, "b c"], dtype="string")
    evidence = _collect(series)

    assert evidence.basic.n_total == 3
    assert evidence.basic.n_missing == 1
    assert evidence.basic.n_non_missing == 2
    assert evidence.contains_alpha_count == 2
    assert evidence.contains_whitespace_count == 1
    assert evidence.whitespace_only_count == 0
    _assert_ratio(evidence.contains_whitespace_ratio, 0.5)
    assert interpret_series_precedence(series) is None


@pytest.mark.parametrize("dtype", ["string", "str"])
def test_all_missing_native_string_has_zero_counts_and_undefined_lengths(dtype: str):
    series = pd.Series([pd.NA, pd.NA], dtype=dtype)
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.n_non_missing == 0
    for name in _COUNT_FIELDS:
        assert getattr(evidence, name) == 0
    assert evidence.min_length is None
    assert evidence.max_length is None
    _assert_ratio(evidence.empty_string_ratio, None)
    _assert_ratio(evidence.contains_alpha_ratio, None)
    assert reading is not None
    assert reading.semantic_type is SemanticType.EMPTY
    assert reading.confidence is Confidence.HIGH
    assert reading.source is InferenceSource.INFERRED


def test_zero_length_native_string_matches_all_missing_structure():
    series = pd.Series([], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.n_total == 0
    assert evidence.min_length is None
    assert evidence.max_length is None
    _assert_ratio(evidence.contains_digit_ratio, None)
    assert reading is not None
    assert reading.semantic_type is SemanticType.EMPTY


def test_eligible_object_strings_use_the_same_structure_rules():
    series = pd.Series(["a", "b", None], dtype=object)
    evidence = _collect(series)

    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.OBJECT
    assert evidence.basic.n_missing == 1
    assert evidence.contains_alpha_count == 2
    assert evidence.min_length == 1
    assert evidence.max_length == 1
    _assert_ratio(evidence.contains_alpha_ratio, 1.0)


def test_object_empty_and_whitespace_strings_keep_their_distinctions():
    series = pd.Series(["", " ", "abc"], dtype=object)
    evidence = _collect(series)

    assert evidence.empty_string_count == 1
    assert evidence.whitespace_only_count == 1
    assert evidence.contains_whitespace_count == 1
    assert evidence.contains_alpha_count == 1
    assert evidence.contains_digit_count == 0
    assert evidence.contains_other_count == 0
    assert evidence.min_length == 0
    assert evidence.max_length == 3
    _assert_ratio(evidence.empty_string_ratio, 1 / 3)


def test_str_subclasses_are_eligible_object_values():
    series = pd.Series([_Token("ab"), _Token(""), np.str_("7")], dtype=object)
    evidence = _collect(series)

    assert evidence.empty_string_count == 1
    assert evidence.contains_alpha_count == 1
    assert evidence.contains_digit_count == 1
    assert evidence.min_length == 0
    assert evidence.max_length == 2


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(pd.Series(["a", 1, None], dtype=object), id="mixed"),
        pytest.param(pd.Series(["a", "b", 1], dtype=object), id="non-string-at-end"),
        pytest.param(pd.Series([1, 2, 3], dtype=object), id="numeric-object"),
        pytest.param(pd.Series([b"ab", b"cd"], dtype=object), id="bytes-object"),
        pytest.param(pd.Series([], dtype=object), id="empty-object"),
        pytest.param(pd.Series([None, None], dtype=object), id="all-missing-none"),
        pytest.param(pd.Series([pd.NA, pd.NA], dtype=object), id="all-missing-na"),
        pytest.param(pd.Series([np.nan, np.nan], dtype=object), id="all-missing-nan"),
    ],
)
def test_ineligible_object_series_raise_type_error(series: pd.Series):
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.OBJECT
    with pytest.raises(AnalyticalInapplicability, match=_APPLICABILITY):
        _collect(series)


def test_all_missing_object_stays_empty_in_the_precedence_chain():
    series = pd.Series([None, None], dtype=object)
    reading = interpret_series_precedence(series)

    assert reading is not None
    assert reading.semantic_type is SemanticType.EMPTY
    with pytest.raises(AnalyticalInapplicability, match=_APPLICABILITY):
        _collect(series)


def test_categorical_string_labels_are_not_string_structure():
    unordered = pd.Series(pd.Categorical(["a", "b", "a"]))
    ordered = pd.Series(pd.Categorical(["a", "b"], categories=["a", "b"], ordered=True))

    for series in (unordered, ordered):
        physical = classify_physical_dtype(series)
        assert physical.family is PhysicalDtypeFamily.CATEGORICAL
        with pytest.raises(AnalyticalInapplicability, match=_APPLICABILITY):
            _collect(series)
    assert classify_physical_dtype(ordered).categorical_ordered is True


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(pd.Series([True, False]), id="boolean"),
        pytest.param(
            pd.Series([True, False, pd.NA], dtype="boolean"),
            id="nullable-boolean",
        ),
        pytest.param(pd.Series([1, 2, 3], dtype="int64"), id="integer"),
        pytest.param(pd.Series([1, pd.NA], dtype="Int64"), id="nullable-integer"),
        pytest.param(pd.Series([1.0, 2.5]), id="floating"),
        pytest.param(pd.Series([1.0, pd.NA], dtype="Float64"), id="nullable-floating"),
        pytest.param(
            pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"])),
            id="datetime",
        ),
        pytest.param(
            pd.Series(pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"])),
            id="datetime-tz",
        ),
        pytest.param(
            pd.Series(pd.to_timedelta(["1 day", "2 days"])),
            id="timedelta",
        ),
        pytest.param(pd.Series([1 + 0j, 2 + 1j]), id="complex"),
        pytest.param(
            pd.Series(pd.period_range("2024-01", periods=2, freq="M")),
            id="period",
        ),
        pytest.param(pd.Series(pd.interval_range(start=0, periods=2)), id="interval"),
    ],
)
def test_unsupported_physical_families_raise_type_error(series: pd.Series):
    assert classify_physical_dtype(series).family is not PhysicalDtypeFamily.STRING
    assert classify_physical_dtype(series).family is not PhysicalDtypeFamily.OBJECT
    with pytest.raises(AnalyticalInapplicability, match=_APPLICABILITY):
        _collect(series)


def test_numpy_byte_strings_are_not_decoded():
    series = pd.Series(np.array([b"ab", b"c1"]))

    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.STRING
    with pytest.raises(AnalyticalInapplicability, match=_APPLICABILITY):
        _collect(series)


def test_empty_string_is_zero_length_and_not_whitespace_or_content():
    series = pd.Series([""], dtype="string")
    evidence = _collect(series)

    assert evidence.empty_string_count == 1
    assert evidence.whitespace_only_count == 0
    assert evidence.contains_whitespace_count == 0
    assert evidence.contains_alpha_count == 0
    assert evidence.contains_digit_count == 0
    assert evidence.contains_other_count == 0
    assert evidence.min_length == 0
    assert evidence.max_length == 0
    _assert_ratio(evidence.empty_string_ratio, 1.0)
    _assert_ratio(evidence.whitespace_only_ratio, 0.0)
    _assert_ratio(evidence.contains_alpha_ratio, 0.0)


def test_spaces_tabs_and_newlines_are_whitespace_only():
    series = pd.Series([" ", "\t", "\n", " \t\n"], dtype="string")
    evidence = _collect(series)

    assert evidence.empty_string_count == 0
    assert evidence.whitespace_only_count == 4
    assert evidence.contains_whitespace_count == 4
    assert evidence.contains_alpha_count == 0
    assert evidence.contains_digit_count == 0
    assert evidence.contains_other_count == 0
    assert evidence.min_length == 1
    assert evidence.max_length == 3
    _assert_ratio(evidence.whitespace_only_ratio, 1.0)


def test_non_breaking_space_is_unicode_whitespace():
    series = pd.Series(["\u00a0"], dtype="string")
    evidence = _collect(series)

    assert evidence.whitespace_only_count == 1
    assert evidence.contains_whitespace_count == 1
    assert evidence.empty_string_count == 0
    assert evidence.contains_other_count == 0
    assert evidence.min_length == 1


def test_embedded_whitespace_is_not_whitespace_only():
    series = pd.Series(["hello world", " hello", "\tfoo"], dtype="string")
    evidence = _collect(series)

    assert evidence.whitespace_only_count == 0
    assert evidence.contains_whitespace_count == 3
    assert evidence.contains_alpha_count == 3
    assert evidence.contains_digit_count == 0
    assert evidence.contains_other_count == 0
    assert evidence.min_length == 4
    assert evidence.max_length == 11


def test_alphabetic_digit_and_punctuation_strings_use_character_classes():
    letters = _collect(pd.Series(["Abc"], dtype="string"))
    digits = _collect(pd.Series(["123"], dtype="string"))
    marks = _collect(pd.Series(["!!!"], dtype="string"))

    assert letters.contains_alpha_count == 1
    assert letters.contains_digit_count == 0
    assert letters.contains_other_count == 0
    assert letters.contains_whitespace_count == 0
    assert digits.contains_digit_count == 1
    assert digits.contains_alpha_count == 0
    assert digits.contains_other_count == 0
    assert marks.contains_other_count == 1
    assert marks.contains_alpha_count == 0
    assert marks.contains_digit_count == 0
    assert marks.contains_whitespace_count == 0


def test_one_string_can_satisfy_several_content_flags():
    series = pd.Series(["abc-123"], dtype="string")
    evidence = _collect(series)

    assert evidence.basic.n_non_missing == 1
    assert evidence.contains_alpha_count == 1
    assert evidence.contains_digit_count == 1
    assert evidence.contains_other_count == 1
    assert evidence.contains_whitespace_count == 0
    assert (
        evidence.contains_alpha_count
        + evidence.contains_digit_count
        + evidence.contains_other_count
        > evidence.basic.n_non_missing
    )
    assert evidence.min_length == 7
    assert evidence.max_length == 7


def test_overlapping_content_counts_are_a_valid_evidence_object():
    evidence = StringStructureEvidence(
        **_evidence_kwargs(  # type: ignore[arg-type]
            basic=_basic(1, 1),
            contains_whitespace_count=1,
            contains_alpha_count=1,
            contains_digit_count=1,
            contains_other_count=1,
            min_length=5,
            max_length=5,
        )
    )

    assert (
        evidence.contains_alpha_count
        + evidence.contains_digit_count
        + evidence.contains_other_count
        + evidence.contains_whitespace_count
        > evidence.basic.n_non_missing
    )


def test_missing_like_literals_remain_ordinary_strings():
    series = pd.Series(["", " ", "NA", "N/A", "null", "None", "?"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.n_missing == 0
    assert evidence.basic.n_non_missing == 7
    assert evidence.empty_string_count == 1
    assert evidence.whitespace_only_count == 1
    assert evidence.contains_whitespace_count == 1
    assert evidence.contains_alpha_count == 4
    assert evidence.contains_digit_count == 0
    assert evidence.contains_other_count == 2
    assert evidence.min_length == 0
    assert evidence.max_length == 4
    assert reading is None


def test_observed_zero_length_differs_from_no_observations():
    observed = _collect(pd.Series([""], dtype="string"))
    absent = _collect(pd.Series([pd.NA], dtype="string"))

    assert observed.min_length == 0
    assert observed.max_length == 0
    assert observed.empty_string_count == 1
    _assert_ratio(observed.empty_string_ratio, 1.0)
    assert absent.min_length is None
    assert absent.max_length is None
    assert absent.empty_string_count == 0
    _assert_ratio(absent.empty_string_ratio, None)


def test_min_and_max_length_use_python_len_of_the_original_strings():
    series = pd.Series(["bb", "a", "ccc"], dtype="string")
    evidence = _collect(series)

    assert evidence.min_length == 1
    assert evidence.max_length == 3
    assert evidence.contains_alpha_count == 3


def test_ratios_use_the_non_missing_denominator():
    series = pd.Series(["", pd.NA, "ab"], dtype="string")
    evidence = _collect(series)

    assert evidence.basic.n_total == 3
    assert evidence.basic.n_non_missing == 2
    _assert_ratio(evidence.empty_string_ratio, 0.5)
    _assert_ratio(evidence.contains_alpha_ratio, 0.5)
    _assert_ratio(evidence.contains_digit_ratio, 0.0)
    _assert_ratio(evidence.contains_other_ratio, 0.0)
    _assert_ratio(evidence.whitespace_only_ratio, 0.0)
    _assert_ratio(evidence.contains_whitespace_ratio, 0.0)


def test_unicode_letters_digits_and_emoji_follow_python_string_methods():
    letters = _collect(pd.Series(["caf\u00e9", "\u6771\u4eac"], dtype="string"))
    digit = _collect(pd.Series(["\u0663"], dtype="string"))
    emoji = _collect(pd.Series(["\U0001f642"], dtype="string"))

    assert letters.contains_alpha_count == 2
    assert letters.contains_digit_count == 0
    assert letters.contains_other_count == 0
    assert letters.min_length == 2
    assert letters.max_length == 4
    assert digit.contains_digit_count == 1
    assert digit.contains_alpha_count == 0
    assert digit.contains_other_count == 0
    assert digit.min_length == 1
    assert emoji.contains_other_count == 1
    assert emoji.contains_alpha_count == 0
    assert emoji.contains_digit_count == 0
    assert emoji.contains_whitespace_count == 0
    assert emoji.min_length == 1


def test_strings_are_not_unicode_normalized_or_casefolded():
    composed = "caf\u00e9"
    decomposed = "cafe\u0301"
    dotted = "\u0130"
    evidence = _collect(pd.Series([composed, decomposed, dotted], dtype="string"))

    assert len(composed) == 4
    assert len(decomposed) == 5
    assert len(dotted) == 1
    assert evidence.min_length == 1
    assert evidence.max_length == 5
    assert evidence.contains_alpha_count == 3
    assert evidence.contains_other_count == 1
    assert evidence.contains_digit_count == 0


def test_long_strings_are_not_inferred_as_text():
    series = pd.Series(
        ["a short sentence about data", "another different sentence"],
        dtype="string",
    )
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.max_length > 10
    assert evidence.contains_whitespace_count == 2
    assert reading is None
    assert not hasattr(evidence, "semantic_type")


def test_repeated_short_strings_are_not_inferred_as_categorical():
    series = pd.Series(["red", "red", "blue"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.n_unique_non_missing == 2
    assert evidence.contains_alpha_count == 3
    assert reading is None


def test_unique_strings_are_not_inferred_as_identifier():
    series = pd.Series(["a", "bb", "ccc"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.basic.unique_ratio_non_missing == 1.0
    assert evidence.min_length == 1
    assert evidence.max_length == 3
    assert reading is None


def test_zero_and_one_strings_are_not_inferred_as_binary():
    series = pd.Series(["0", "1", "1", "0"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.contains_digit_count == 4
    assert evidence.contains_alpha_count == 0
    assert evidence.contains_other_count == 0
    assert reading is None


def test_date_looking_strings_are_not_inferred_as_datetime():
    series = pd.Series(["2026-01-01", "2026-02-02"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.contains_digit_count == 2
    assert evidence.contains_other_count == 2
    assert evidence.contains_alpha_count == 0
    assert reading is None


def test_numeric_looking_strings_are_not_inferred_as_numeric():
    series = pd.Series(["123", "45.6"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.contains_digit_count == 2
    assert evidence.contains_other_count == 1
    assert evidence.contains_alpha_count == 0
    assert reading is None


def test_uuid_email_and_url_strings_are_not_pattern_evidence():
    series = pd.Series(
        [
            "123e4567-e89b-12d3-a456-426614174000",
            "a@b.com",
            "https://example.com",
        ],
        dtype="string",
    )
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.contains_alpha_count == 3
    assert evidence.contains_digit_count == 1
    assert evidence.contains_other_count == 3
    assert reading is None
    for absent in (
        "is_uuid",
        "is_email",
        "is_url",
        "pattern",
        "word_count",
        "token_count",
    ):
        assert not hasattr(evidence, absent)


def test_constant_strings_keep_constant_precedence_and_count_every_row():
    series = pd.Series(["abc", "abc", "abc"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    assert evidence.contains_alpha_count == 3
    assert evidence.min_length == 3
    assert evidence.max_length == 3
    _assert_ratio(evidence.contains_alpha_ratio, 1.0)
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT
    assert reading.source is InferenceSource.INFERRED
    assert reading.confidence is Confidence.HIGH


def test_existing_semantic_chain_is_unchanged_beside_string_structure():
    empty = pd.Series([pd.NA, pd.NA], dtype="string")
    constant = pd.Series(["abc", None, "abc"], dtype=object)
    boolean = pd.Series([True, False, pd.NA], dtype="boolean")
    native = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))
    aware = pd.Series(pd.to_datetime(["2026-01-01T12:00:00Z", "2026-01-02T12:00:00Z"]))
    duration = pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    ordinary = pd.Series(["a", "bb"], dtype="string")

    empty_reading = interpret_series_precedence(empty)
    constant_reading = interpret_series_precedence(constant)
    boolean_reading = interpret_series_precedence(boolean)
    native_reading = interpret_series_precedence(native)
    aware_reading = interpret_series_precedence(aware)
    duration_reading = interpret_series_precedence(duration)
    ordinary_reading = interpret_series_precedence(ordinary)

    assert empty_reading is not None
    assert empty_reading.semantic_type is SemanticType.EMPTY
    assert constant_reading is not None
    assert constant_reading.semantic_type is SemanticType.CONSTANT
    assert constant_reading.physical.family is PhysicalDtypeFamily.OBJECT
    assert boolean_reading is not None
    assert boolean_reading.semantic_type is SemanticType.BOOLEAN
    assert boolean_reading.source is InferenceSource.PHYSICAL_DTYPE
    assert boolean_reading.evidence[0].statement == "physical dtype is boolean"
    assert native_reading is not None
    assert native_reading.semantic_type is SemanticType.DATETIME
    assert native_reading.evidence[0].statement == "physical dtype is datetime"
    assert aware_reading is not None
    assert aware_reading.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert duration_reading is not None
    assert duration_reading.semantic_type is SemanticType.TIMEDELTA
    assert duration_reading.evidence[0].statement == "physical dtype is timedelta"
    assert ordinary_reading is None


def test_precedence_does_not_collect_string_structure_evidence(
    monkeypatch: pytest.MonkeyPatch,
):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "string structure evidence was collected during precedence"
        )

    monkeypatch.setattr(pd.Series, "dropna", _forbidden)
    monkeypatch.setattr(
        string_module,
        "collect_string_structure_evidence",
        _forbidden,
    )
    for module in (
        empty_constant_module,
        physical_boolean_module,
        physical_datetime_module,
        physical_timedelta_module,
    ):
        source = inspect.getsource(module)
        assert "StringStructureEvidence" not in source
        assert "collect_string_structure_evidence" not in source

    empty = interpret_series_precedence(pd.Series([None, None]))
    constant = interpret_series_precedence(pd.Series(["aa", "aa"]))
    ordinary = interpret_series_precedence(pd.Series(["a", "b"]))

    assert empty is not None
    assert empty.semantic_type is SemanticType.EMPTY
    assert constant is not None
    assert constant.semantic_type is SemanticType.CONSTANT
    assert ordinary is None


def test_basic_evidence_and_physical_classification_are_reused(
    monkeypatch: pytest.MonkeyPatch,
):
    series = pd.Series(["a", pd.NA, "b-2"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("basic evidence or frequency evidence was recomputed")

    monkeypatch.setattr(pd.Series, "nunique", _forbidden)
    monkeypatch.setattr(pd.Series, "value_counts", _forbidden)
    monkeypatch.setattr(pd.Series, "astype", _forbidden)
    monkeypatch.setattr(pd, "to_numeric", _forbidden)
    monkeypatch.setattr(pd, "to_datetime", _forbidden)
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

    evidence = collect_string_structure_evidence(series, basic, physical)

    assert evidence.basic is basic
    assert evidence.contains_alpha_count == 2
    assert evidence.contains_digit_count == 1
    assert evidence.contains_other_count == 1
    assert not hasattr(string_module, "collect_basic_column_evidence")
    assert not hasattr(string_module, "classify_physical_dtype")
    assert not hasattr(string_module, "collect_frequency_evidence")
    parameters = list(inspect.signature(collect_string_structure_evidence).parameters)
    assert parameters == ["series", "basic", "physical"]


def test_collection_does_not_mutate_the_series():
    series = pd.Series(
        ["a", None, " b"],
        dtype=object,
        name="label",
        index=pd.Index([3, 1, 4], name="row"),
    )
    before = series.copy(deep=True)

    _collect(series)

    pd.testing.assert_series_equal(series, before)
    assert series.name == "label"
    assert series.index.name == "row"


def test_string_structure_evidence_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "StringStructureEvidence")
    assert not hasattr(pytics, "collect_string_structure_evidence")
    assert not hasattr(semantics_package, "StringStructureEvidence")
    assert not hasattr(semantics_package, "collect_string_structure_evidence")


def test_mismatched_basic_evidence_is_rejected():
    series = pd.Series(["a", "b", "c"], dtype="string")
    physical = classify_physical_dtype(series)

    with pytest.raises(ValueError, match="do not match BasicColumnEvidence"):
        collect_string_structure_evidence(series, _basic(2, 2), physical)


def test_mismatched_physical_dtype_is_rejected():
    series = pd.Series(["a", "b"], dtype="string")
    physical = PhysicalDtype(family=PhysicalDtypeFamily.STRING, dtype_name="object")

    with pytest.raises(ValueError, match="does not match the Series"):
        collect_string_structure_evidence(
            series,
            collect_basic_column_evidence(series),
            physical,
        )


def test_wrong_input_types_are_rejected():
    series = pd.Series(["a", "b"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)

    with pytest.raises(TypeError, match="pandas Series"):
        collect_string_structure_evidence(["a", "b"], basic, physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="BasicColumnEvidence"):
        collect_string_structure_evidence(series, "basic", physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="PhysicalDtype"):
        collect_string_structure_evidence(series, basic, "physical")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("overrides", "error", "match"),
    [
        ({"basic": "counts"}, TypeError, "BasicColumnEvidence"),
        ({"empty_string_count": True}, TypeError, "empty_string_count"),
        ({"contains_alpha_count": -1}, ValueError, "contains_alpha_count"),
        (
            {
                "basic": _basic(1, 1),
                "contains_digit_count": 2,
                "min_length": 1,
                "max_length": 1,
            },
            ValueError,
            "cannot exceed n_non_missing",
        ),
        (
            {
                "basic": _basic(1, 1),
                "whitespace_only_count": 1,
                "min_length": 1,
                "max_length": 1,
            },
            ValueError,
            "also contain whitespace",
        ),
        (
            {
                "basic": _basic(1, 1),
                "empty_string_count": 1,
                "whitespace_only_count": 1,
                "contains_whitespace_count": 1,
                "min_length": 0,
                "max_length": 1,
            },
            ValueError,
            "cannot overlap",
        ),
        (
            {"min_length": 0, "max_length": 0},
            ValueError,
            "undefined when n_non_missing is 0",
        ),
        (
            {
                "basic": _basic(1, 1),
                "contains_alpha_count": 1,
                "min_length": None,
                "max_length": 1,
            },
            TypeError,
            "must be ints",
        ),
        (
            {
                "basic": _basic(1, 1),
                "min_length": -1,
                "max_length": 1,
            },
            ValueError,
            "must be >= 0",
        ),
        (
            {
                "basic": _basic(1, 1),
                "contains_alpha_count": 1,
                "min_length": 4,
                "max_length": 2,
            },
            ValueError,
            "cannot exceed max_length",
        ),
        (
            {
                "basic": _basic(1, 1),
                "empty_string_count": 1,
                "min_length": 1,
                "max_length": 1,
            },
            ValueError,
            "requires min_length == 0",
        ),
        (
            {
                "basic": _basic(1, 1),
                "contains_alpha_count": 1,
                "min_length": 0,
                "max_length": 1,
            },
            ValueError,
            "requires an empty string",
        ),
    ],
)
def test_inconsistent_string_structure_evidence_is_rejected(
    overrides: dict[str, object],
    error: type[Exception],
    match: str,
):
    with pytest.raises(error, match=match):
        StringStructureEvidence(**_evidence_kwargs(**overrides))  # type: ignore[arg-type]
