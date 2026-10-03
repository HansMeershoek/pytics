"""TSK-013: token and vocabulary observations without a semantic reading."""

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
import pytics.semantics.core_candidates as core_module
import pytics.semantics.empty_constant as empty_constant_module
import pytics.semantics.identifier_candidate as identifier_module
import pytics.semantics.physical_boolean as physical_boolean_module
import pytics.semantics.physical_datetime as physical_datetime_module
import pytics.semantics.physical_timedelta as physical_timedelta_module
import pytics.semantics.string_content_evidence as content_module
import pytics.semantics.string_structure_evidence as string_module
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.core_candidates import assess_categorical_candidate
from pytics.semantics.core_candidates import assess_numeric_candidate
from pytics.semantics.core_candidates import assess_text_candidate
from pytics.semantics.frequency_evidence import collect_frequency_evidence
from pytics.semantics.identifier_candidate import assess_identifier_candidate
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_series_precedence
from pytics.semantics.string_content_evidence import StringContentEvidence
from pytics.semantics.string_content_evidence import collect_string_content_evidence
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import (
    collect_string_structure_evidence,
)

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_APPLICABILITY = "string-structure evidence"
_STORED_COUNTS = (
    "total_token_count",
    "strings_with_zero_tokens_count",
    "strings_with_one_token_count",
    "strings_with_multiple_tokens_count",
    "total_character_count",
    "n_distinct_tokens",
    "singleton_token_count",
    "most_frequent_token_count",
)
_DERIVED = (
    "zero_token_ratio",
    "one_token_ratio",
    "multiple_token_ratio",
    "mean_tokens_per_non_missing",
    "mean_characters_per_non_missing",
    "token_singleton_ratio",
    "most_frequent_token_ratio",
)


class _Token(str):
    """A ``str`` subclass used to pin the ``isinstance`` contract."""


def _collect(series: pd.Series) -> StringContentEvidence:
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    evidence = collect_string_content_evidence(series, structure, physical)
    assert evidence.string_structure is structure
    assert evidence.string_structure.basic is basic
    _assert_bounded(evidence)
    return evidence


def _basic(
    n_non_missing: int,
    n_unique: int,
    n_missing: int = 0,
) -> BasicColumnEvidence:
    return BasicColumnEvidence(
        n_total=n_non_missing + n_missing,
        n_missing=n_missing,
        n_non_missing=n_non_missing,
        n_unique_non_missing=n_unique,
    )


def _structure(
    n_non_missing: int,
    n_unique: Optional[int] = None,
    n_missing: int = 0,
    *,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
    empty: int = 0,
    whitespace_only: int = 0,
    contains_whitespace: Optional[int] = None,
) -> StringStructureEvidence:
    if n_unique is None:
        n_unique = n_non_missing
    if n_non_missing == 0:
        minimum = None
        maximum = None
    else:
        if minimum is None:
            minimum = 0 if empty else 1
        if maximum is None:
            maximum = minimum
    if contains_whitespace is None:
        contains_whitespace = whitespace_only
    return StringStructureEvidence(
        basic=_basic(n_non_missing, n_unique, n_missing),
        empty_string_count=empty,
        whitespace_only_count=whitespace_only,
        contains_whitespace_count=contains_whitespace,
        contains_alpha_count=0,
        contains_digit_count=0,
        contains_other_count=0,
        min_length=minimum,
        max_length=maximum,
    )


def _baseline() -> StringContentEvidence:
    """Two one-character, one-token strings with two distinct tokens."""
    return StringContentEvidence(
        string_structure=_structure(2),
        total_token_count=2,
        strings_with_zero_tokens_count=0,
        strings_with_one_token_count=2,
        strings_with_multiple_tokens_count=0,
        total_character_count=2,
        n_distinct_tokens=2,
        singleton_token_count=2,
        most_frequent_token_count=1,
    )


def _content(**overrides: object) -> StringContentEvidence:
    evidence = _baseline()
    values = {field.name: getattr(evidence, field.name) for field in fields(evidence)}
    values.update(overrides)
    return StringContentEvidence(**values)  # type: ignore[arg-type]


def _assert_ratio(value: Optional[float], expected: Optional[float]) -> None:
    if expected is None:
        assert value is None
        return
    assert type(value) is float
    assert value == expected
    assert not math.isnan(value)
    assert not math.isinf(value)


def _assert_bounded(evidence: StringContentEvidence, *forbidden: str) -> None:
    stored = [field.name for field in fields(evidence)]
    assert stored[0] == "string_structure"
    assert stored[1:] == list(_STORED_COUNTS)
    for name in _DERIVED:
        assert name not in stored
    for name in (
        "n_total",
        "n_missing",
        "n_non_missing",
        "n_unique_non_missing",
        "most_frequent_count",
        "singleton_count",
        "min_length",
        "max_length",
        "tokens",
        "vocabulary",
    ):
        assert name not in stored
    rendered = repr(evidence)
    for text in forbidden:
        assert text not in rendered
    assert not hasattr(evidence, "tokens")
    assert not hasattr(evidence, "vocabulary")


def _assert_not_supported(
    result: CandidateAssessment, semantic_type: SemanticType
) -> None:
    assert result.semantic_type is semantic_type
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED
    assert result.supporting_evidence == ()
    assert result.contradicting_evidence == ()


def _assess_inputs(series: pd.Series) -> tuple:
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    frequency = collect_frequency_evidence(series, basic)
    numeric = None
    structure = None
    pattern = None
    if physical.family in (
        PhysicalDtypeFamily.INTEGER,
        PhysicalDtypeFamily.FLOATING,
    ):
        from pytics.semantics.numeric_structure_evidence import (
            collect_numeric_structure_evidence,
        )

        numeric = collect_numeric_structure_evidence(series, basic, physical)
    elif physical.family in (
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    ):
        structure = collect_string_structure_evidence(series, basic, physical)
        pattern = collect_pattern_evidence(series, structure, physical)
    return basic, physical, frequency, numeric, structure, pattern


def _assess(assess, series: pd.Series) -> CandidateAssessment:
    basic, physical, frequency, numeric, structure, pattern = _assess_inputs(series)
    return assess(
        basic,
        physical,
        frequency=frequency,
        numeric_structure=numeric,
        string_structure=structure,
        pattern=pattern,
    )


def test_evidence_is_a_frozen_composed_dataclass() -> None:
    evidence = _baseline()
    assert dataclasses.is_dataclass(evidence)
    assert type(evidence).__dataclass_params__.frozen is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.total_token_count = 0  # type: ignore[misc]
    assert not issubclass(StringContentEvidence, StringStructureEvidence)
    assert not issubclass(StringContentEvidence, BasicColumnEvidence)


def test_composition_identity_is_the_supplied_object() -> None:
    series = pd.Series(["red car", "blue car"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    evidence = collect_string_content_evidence(series, structure, physical)
    assert evidence.string_structure is structure
    assert evidence.string_structure.basic is basic


def test_zero_population_counts_and_undefined_ratios() -> None:
    evidence = _collect(pd.Series([pd.NA, pd.NA], dtype="string"))
    assert evidence.string_structure.basic.n_non_missing == 0
    for name in _STORED_COUNTS:
        assert getattr(evidence, name) == 0
    for name in _DERIVED:
        assert getattr(evidence, name) is None
    assert evidence.string_structure.min_length is None
    assert evidence.string_structure.max_length is None


def test_zero_length_string_column_matches_the_empty_population() -> None:
    evidence = _collect(pd.Series([], dtype="string"))
    assert evidence.string_structure.basic.n_total == 0
    assert evidence.total_token_count == 0
    assert evidence.total_character_count == 0
    assert evidence.mean_tokens_per_non_missing is None
    assert evidence.token_singleton_ratio is None


def test_derived_ratios_use_the_documented_denominators() -> None:
    evidence = _collect(pd.Series(["red car", "blue car"], dtype="string"))
    _assert_ratio(evidence.zero_token_ratio, 0.0)
    _assert_ratio(evidence.one_token_ratio, 0.0)
    _assert_ratio(evidence.multiple_token_ratio, 1.0)
    _assert_ratio(evidence.mean_tokens_per_non_missing, 2.0)
    _assert_ratio(evidence.mean_characters_per_non_missing, 7.5)
    _assert_ratio(evidence.token_singleton_ratio, 2 / 3)
    _assert_ratio(evidence.most_frequent_token_ratio, 2 / 4)
    assert evidence.token_singleton_ratio != evidence.most_frequent_token_ratio
    assert evidence.token_singleton_ratio != 2 / 4
    assert evidence.most_frequent_token_ratio != 2 / 3


def test_punctuation_only_has_zero_mean_tokens_and_undefined_vocabulary() -> None:
    evidence = _collect(pd.Series(["???", "..."], dtype="string"))
    assert evidence.total_token_count == 0
    assert evidence.n_distinct_tokens == 0
    assert evidence.strings_with_zero_tokens_count == 2
    _assert_ratio(evidence.mean_tokens_per_non_missing, 0.0)
    _assert_ratio(evidence.zero_token_ratio, 1.0)
    assert evidence.token_singleton_ratio is None
    assert evidence.most_frequent_token_ratio is None
    assert evidence.mean_tokens_per_non_missing is not None


def test_means_are_not_stored() -> None:
    evidence = _baseline()
    stored = {field.name for field in fields(evidence)}
    assert "mean_tokens_per_non_missing" not in stored
    assert "mean_characters_per_non_missing" not in stored
    assert "mean_length" not in stored


@pytest.mark.parametrize(
    ("field", "value", "error", "match"),
    [
        ("total_token_count", -1, ValueError, "total_token_count must be >= 0"),
        ("total_token_count", True, TypeError, "total_token_count must be an int"),
        ("n_distinct_tokens", 1.0, TypeError, "n_distinct_tokens must be an int"),
        ("string_structure", object(), TypeError, "StringStructureEvidence"),
    ],
)
def test_invalid_stored_fields_are_rejected(
    field: str,
    value: object,
    error: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error, match=match):
        _content(**{field: value})


def test_token_classes_must_partition_the_non_missing_strings() -> None:
    with pytest.raises(ValueError, match="partition n_non_missing"):
        _content(strings_with_zero_tokens_count=1)


def test_token_occurrences_cannot_fall_below_the_string_partition() -> None:
    with pytest.raises(ValueError, match="below the one-token"):
        _content(total_token_count=1)


def test_token_occurrences_require_a_token_bearing_string() -> None:
    with pytest.raises(ValueError, match="require a string that contains a token"):
        _content(
            total_token_count=2,
            strings_with_zero_tokens_count=2,
            strings_with_one_token_count=0,
            strings_with_multiple_tokens_count=0,
        )


def test_character_total_is_zero_when_the_population_is_empty() -> None:
    with pytest.raises(ValueError, match="total_character_count is 0"):
        StringContentEvidence(
            string_structure=_structure(0),
            total_token_count=0,
            strings_with_zero_tokens_count=0,
            strings_with_one_token_count=0,
            strings_with_multiple_tokens_count=0,
            total_character_count=1,
            n_distinct_tokens=0,
            singleton_token_count=0,
            most_frequent_token_count=0,
        )


def test_character_total_cannot_be_below_the_token_occurrences() -> None:
    with pytest.raises(ValueError, match="below the token occurrences"):
        StringContentEvidence(
            string_structure=_structure(2, minimum=1, maximum=10),
            total_token_count=6,
            strings_with_zero_tokens_count=0,
            strings_with_one_token_count=0,
            strings_with_multiple_tokens_count=2,
            total_character_count=5,
            n_distinct_tokens=1,
            singleton_token_count=0,
            most_frequent_token_count=6,
        )


def test_character_total_must_lie_inside_the_length_bounds() -> None:
    with pytest.raises(ValueError, match="outside min_length and max_length"):
        _content(total_character_count=3)
    with pytest.raises(ValueError, match="outside min_length and max_length"):
        _content(
            total_token_count=1,
            strings_with_zero_tokens_count=1,
            strings_with_one_token_count=1,
            total_character_count=1,
            n_distinct_tokens=1,
            singleton_token_count=1,
            most_frequent_token_count=1,
        )


def test_empty_and_whitespace_only_strings_are_zero_token_strings() -> None:
    with pytest.raises(ValueError, match="no alphanumeric token"):
        StringContentEvidence(
            string_structure=_structure(2, minimum=0, maximum=1, empty=1),
            total_token_count=2,
            strings_with_zero_tokens_count=0,
            strings_with_one_token_count=2,
            strings_with_multiple_tokens_count=0,
            total_character_count=2,
            n_distinct_tokens=2,
            singleton_token_count=2,
            most_frequent_token_count=1,
        )
    with pytest.raises(ValueError, match="no alphanumeric token"):
        StringContentEvidence(
            string_structure=_structure(
                2,
                minimum=1,
                maximum=3,
                whitespace_only=1,
                contains_whitespace=1,
            ),
            total_token_count=4,
            strings_with_zero_tokens_count=0,
            strings_with_one_token_count=0,
            strings_with_multiple_tokens_count=2,
            total_character_count=4,
            n_distinct_tokens=4,
            singleton_token_count=4,
            most_frequent_token_count=1,
        )


def test_no_tokens_cannot_claim_a_vocabulary() -> None:
    with pytest.raises(ValueError, match="no distinct, singleton"):
        StringContentEvidence(
            string_structure=_structure(1),
            total_token_count=0,
            strings_with_zero_tokens_count=1,
            strings_with_one_token_count=0,
            strings_with_multiple_tokens_count=0,
            total_character_count=1,
            n_distinct_tokens=1,
            singleton_token_count=0,
            most_frequent_token_count=0,
        )


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"n_distinct_tokens": 0, "most_frequent_token_count": 2}, "must be positive"),
        ({"n_distinct_tokens": 3}, "cannot exceed total_token_count"),
        (
            {
                "n_distinct_tokens": 1,
                "singleton_token_count": 0,
                "most_frequent_token_count": 0,
            },
            "must be >= 1",
        ),
        (
            {
                "n_distinct_tokens": 1,
                "singleton_token_count": 0,
                "most_frequent_token_count": 3,
            },
            "cannot exceed total_token_count",
        ),
        (
            {
                "n_distinct_tokens": 1,
                "singleton_token_count": 2,
                "most_frequent_token_count": 2,
            },
            "cannot exceed n_distinct_tokens",
        ),
        (
            {
                "n_distinct_tokens": 1,
                "singleton_token_count": 1,
                "most_frequent_token_count": 2,
            },
            "occurs once",
        ),
        (
            {
                "n_distinct_tokens": 1,
                "singleton_token_count": 0,
                "most_frequent_token_count": 1,
            },
            "only distinct token",
        ),
    ],
)
def test_impossible_vocabulary_counts_are_rejected(
    overrides: dict[str, int],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        _content(**overrides)


def test_repeated_token_must_leave_a_non_singleton() -> None:
    with pytest.raises(ValueError, match="not a singleton"):
        StringContentEvidence(
            string_structure=_structure(2, minimum=1, maximum=10),
            total_token_count=4,
            strings_with_zero_tokens_count=0,
            strings_with_one_token_count=0,
            strings_with_multiple_tokens_count=2,
            total_character_count=4,
            n_distinct_tokens=2,
            singleton_token_count=2,
            most_frequent_token_count=2,
        )


def test_token_counts_must_be_internally_possible() -> None:
    with pytest.raises(ValueError, match="inconsistent with total_token_count"):
        StringContentEvidence(
            string_structure=_structure(2, minimum=1, maximum=10),
            total_token_count=3,
            strings_with_zero_tokens_count=0,
            strings_with_one_token_count=1,
            strings_with_multiple_tokens_count=1,
            total_character_count=3,
            n_distinct_tokens=3,
            singleton_token_count=0,
            most_frequent_token_count=2,
        )


def test_every_token_occurring_once_must_match_the_distinct_count() -> None:
    with pytest.raises(ValueError, match="every token occurs once"):
        StringContentEvidence(
            string_structure=_structure(2, minimum=1, maximum=10),
            total_token_count=3,
            strings_with_zero_tokens_count=0,
            strings_with_one_token_count=1,
            strings_with_multiple_tokens_count=1,
            total_character_count=3,
            n_distinct_tokens=2,
            singleton_token_count=2,
            most_frequent_token_count=1,
        )


@pytest.mark.parametrize(
    ("value", "tokens", "characters"),
    [
        ("hello", 1, 5),
        ("hello world", 2, 11),
        ("hello-world", 2, 11),
        ("hello_world", 2, 11),
        ("abc.def", 2, 7),
        ("abc123", 1, 6),
        ("123", 1, 3),
        ("", 0, 0),
        ("   ", 0, 3),
        ("\t\n", 0, 2),
        ("één twee", 2, 8),
        ("東京 データ", 2, 6),
        ("🙂", 0, 1),
        ("hello🙂world", 2, 11),
        ("don't", 2, 5),
    ],
)
def test_token_observations_follow_alphanumeric_runs(
    value: str,
    tokens: int,
    characters: int,
) -> None:
    evidence = _collect(pd.Series([value], dtype="string"))
    assert evidence.total_token_count == tokens
    assert evidence.total_character_count == characters
    assert evidence.string_structure.min_length == characters
    assert evidence.string_structure.max_length == characters
    if tokens == 0:
        assert evidence.strings_with_zero_tokens_count == 1
        assert evidence.n_distinct_tokens == 0
        assert evidence.most_frequent_token_count == 0
    elif tokens == 1:
        assert evidence.strings_with_one_token_count == 1
        assert evidence.n_distinct_tokens == 1
        assert evidence.singleton_token_count == 1
        assert evidence.most_frequent_token_count == 1
    else:
        assert evidence.strings_with_multiple_tokens_count == 1
        assert evidence.n_distinct_tokens == tokens
        assert evidence.singleton_token_count == tokens
        assert evidence.most_frequent_token_count == 1
    if value:
        _assert_bounded(evidence, value)
    else:
        _assert_bounded(evidence)


def test_repeated_token_inside_one_string_is_one_distinct_token() -> None:
    evidence = _collect(pd.Series(["car car"], dtype="string"))
    assert evidence.total_token_count == 2
    assert evidence.strings_with_multiple_tokens_count == 1
    assert evidence.n_distinct_tokens == 1
    assert evidence.singleton_token_count == 0
    assert evidence.most_frequent_token_count == 2
    _assert_bounded(evidence, "car")


def test_vocabulary_of_shared_and_unshared_tokens() -> None:
    evidence = _collect(pd.Series(["red car", "blue car"], dtype="string"))
    assert evidence.total_token_count == 4
    assert evidence.n_distinct_tokens == 3
    assert evidence.singleton_token_count == 2
    assert evidence.most_frequent_token_count == 2
    _assert_bounded(evidence, "red car", "blue car", "car")


def test_all_distinct_tokens_are_singletons() -> None:
    evidence = _collect(pd.Series(["alpha", "beta", "gamma"], dtype="string"))
    assert evidence.total_token_count == 3
    assert evidence.n_distinct_tokens == 3
    assert evidence.singleton_token_count == 3
    assert evidence.most_frequent_token_count == 1
    _assert_ratio(evidence.token_singleton_ratio, 1.0)
    _assert_ratio(evidence.most_frequent_token_ratio, 1 / 3)


def test_one_repeated_token_has_no_singleton() -> None:
    evidence = _collect(pd.Series(["same", "same", "same"], dtype="string"))
    assert evidence.total_token_count == 3
    assert evidence.n_distinct_tokens == 1
    assert evidence.singleton_token_count == 0
    assert evidence.most_frequent_token_count == 3
    _assert_ratio(evidence.token_singleton_ratio, 0.0)
    _assert_ratio(evidence.most_frequent_token_ratio, 1.0)


def test_case_is_a_distinct_token_observation() -> None:
    evidence = _collect(pd.Series(["A", "a"], dtype="string"))
    assert evidence.n_distinct_tokens == 2
    assert evidence.singleton_token_count == 2
    assert evidence.most_frequent_token_count == 1
    phrases = _collect(pd.Series(["Apple pie", "apple pie"], dtype="string"))
    assert phrases.total_token_count == 4
    assert phrases.n_distinct_tokens == 3
    assert phrases.singleton_token_count == 2
    assert phrases.most_frequent_token_count == 2
    _assert_bounded(phrases, "Apple", "apple")


def test_accents_are_not_normalized() -> None:
    composed = "café"
    decomposed = "cafe\u0301"
    evidence = _collect(pd.Series([composed, decomposed], dtype="string"))
    assert evidence.total_character_count == len(composed) + len(decomposed)
    assert len(composed) != len(decomposed)
    assert evidence.n_distinct_tokens == 2
    assert evidence.total_token_count == 2
    _assert_bounded(evidence, composed, decomposed)


def test_whole_value_frequency_is_not_token_frequency() -> None:
    series = pd.Series(["red car", "blue car"], dtype="string")
    basic = collect_basic_column_evidence(series)
    frequency = collect_frequency_evidence(series, basic)
    evidence = _collect(series)
    assert frequency.basic.n_unique_non_missing == 2
    assert frequency.most_frequent_count == 1
    assert frequency.singleton_count == 2
    assert evidence.n_distinct_tokens == 3
    assert evidence.most_frequent_token_count == 2
    assert evidence.singleton_token_count == 2
    assert not isinstance(evidence, type(frequency))
    assert "exact_distinct_non_missing_values" not in {
        field.name for field in fields(evidence)
    }


def test_source_values_are_not_rewritten() -> None:
    series = pd.Series(["  Hello  ", "café", "hello-world"], dtype="string")
    original = series.copy(deep=True)
    evidence = _collect(series)
    pd.testing.assert_series_equal(series, original)
    assert evidence.total_character_count == 9 + 4 + 11
    assert evidence.string_structure.min_length == 4
    assert evidence.string_structure.max_length == 11
    assert evidence.total_token_count == 4
    assert evidence.n_distinct_tokens == 4


def test_column_name_does_not_change_the_observations() -> None:
    values = ["red", "blue"]
    named = _collect(pd.Series(values, dtype="string", name="category"))
    other = _collect(pd.Series(values, dtype="string", name="free_text"))
    assert named.total_token_count == other.total_token_count == 2
    assert named.n_distinct_tokens == other.n_distinct_tokens == 2
    assert "category" not in repr(named)
    assert "free_text" not in repr(other)


def test_missing_values_are_excluded_and_not_rewritten_as_empty() -> None:
    series = pd.Series(["hello", None, "world", np.nan], dtype=object)
    evidence = _collect(series)
    assert evidence.string_structure.basic.n_missing == 2
    assert evidence.string_structure.basic.n_non_missing == 2
    assert evidence.total_token_count == 2
    assert evidence.strings_with_zero_tokens_count == 0
    assert evidence.n_distinct_tokens == 2


def test_missing_literals_remain_ordinary_tokens() -> None:
    evidence = _collect(pd.Series(["nan", "None", "NA", ""], dtype="string"))
    assert evidence.string_structure.basic.n_non_missing == 4
    assert evidence.string_structure.empty_string_count == 1
    assert evidence.total_token_count == 3
    assert evidence.strings_with_zero_tokens_count == 1
    assert evidence.n_distinct_tokens == 3
    _assert_bounded(evidence, "nan", "None", "NA")


def test_empty_string_is_observed_and_has_no_token() -> None:
    evidence = _collect(pd.Series(["", "hello"], dtype="string"))
    assert evidence.string_structure.basic.n_missing == 0
    assert evidence.string_structure.empty_string_count == 1
    assert evidence.string_structure.min_length == 0
    assert evidence.strings_with_zero_tokens_count == 1
    assert evidence.strings_with_one_token_count == 1
    assert evidence.total_character_count == 5


def test_whitespace_only_string_is_observed_and_has_no_token() -> None:
    evidence = _collect(pd.Series(["   ", "\t\n", "hello"], dtype="string"))
    assert evidence.string_structure.whitespace_only_count == 2
    assert evidence.strings_with_zero_tokens_count == 2
    assert evidence.total_token_count == 1
    assert evidence.total_character_count == 3 + 2 + 5


def test_object_strings_and_string_subclasses_are_eligible() -> None:
    evidence = _collect(pd.Series([_Token("hello"), _Token("world")], dtype=object))
    assert evidence.total_token_count == 2
    assert evidence.n_distinct_tokens == 2
    assert evidence.string_structure.basic.n_non_missing == 2


def test_hyphenated_uuid_tokens_do_not_replace_the_uuid_pattern_count() -> None:
    series = pd.Series([_UUID_A], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    pattern = collect_pattern_evidence(series, structure, physical)
    evidence = collect_string_content_evidence(series, structure, physical)
    assert pattern.uuid_count == 1
    assert evidence.total_token_count == 5
    assert evidence.strings_with_multiple_tokens_count == 1
    assert evidence.string_structure is structure
    _assert_bounded(evidence, _UUID_A)


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([1, 2, 3]),
        pd.Series([1.5, 2.5]),
        pd.Series([True, False]),
        pd.Series(pd.to_datetime(["2020-01-01", "2020-01-02"])),
        pd.Series(pd.to_timedelta(["1 day", "2 days"])),
        pd.Series(["Amsterdam", "Berlin"], dtype="category"),
    ],
)
def test_ineligible_storage_is_rejected(series: pd.Series) -> None:
    physical = classify_physical_dtype(series)
    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_string_content_evidence(series, _structure(0), physical)


def test_all_missing_object_column_is_not_a_string_population() -> None:
    series = pd.Series([None, None], dtype=object)
    physical = classify_physical_dtype(series)
    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_string_content_evidence(series, _structure(0, n_missing=2), physical)


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([b"hello", b"world"], dtype=object),
        pd.Series(["hello", 1], dtype=object),
    ],
)
def test_non_string_object_values_are_rejected(series: pd.Series) -> None:
    physical = classify_physical_dtype(series)
    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_string_content_evidence(series, _structure(len(series)), physical)


def test_all_missing_string_column_is_eligible() -> None:
    evidence = _collect(pd.Series([pd.NA, None], dtype="string"))
    assert evidence.string_structure.basic.is_empty is True
    assert evidence.total_token_count == 0
    assert evidence.mean_characters_per_non_missing is None


def test_population_counts_must_match_the_supplied_basic_evidence() -> None:
    series = pd.Series(["hello", "world"], dtype="string")
    physical = classify_physical_dtype(series)
    with pytest.raises(ValueError, match="do not match BasicColumnEvidence"):
        collect_string_content_evidence(series, _structure(1), physical)


def test_physical_dtype_name_must_match_the_series() -> None:
    series = pd.Series(["hello"], dtype="string")
    physical = classify_physical_dtype(series)
    renamed = PhysicalDtype(physical.family, "object")
    with pytest.raises(ValueError, match="does not match the Series"):
        collect_string_content_evidence(series, _structure(1), renamed)


def test_collector_rejects_the_wrong_argument_types() -> None:
    series = pd.Series(["hello"], dtype="string")
    physical = classify_physical_dtype(series)
    structure = _structure(1)
    with pytest.raises(TypeError, match="pandas Series"):
        collect_string_content_evidence(["hello"], structure, physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="StringStructureEvidence"):
        collect_string_content_evidence(series, "structure", physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="PhysicalDtype"):
        collect_string_content_evidence(series, structure, "physical")  # type: ignore[arg-type]


def test_categorical_labels_are_not_read_as_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    series = pd.Series(["Amsterdam", "Berlin"], dtype="category")
    physical = classify_physical_dtype(series)

    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("categorical storage was coerced")

    monkeypatch.setattr(pd.Series, "astype", _forbidden)
    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_string_content_evidence(series, _structure(0), physical)


def test_supplied_evidence_is_not_recollected(monkeypatch: pytest.MonkeyPatch) -> None:
    series = pd.Series(["red car", pd.NA, "blue car"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)

    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("string content recollected existing evidence")

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
        "pytics.semantics.frequency_evidence.collect_frequency_evidence",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.string_structure_evidence.collect_string_structure_evidence",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.pattern_evidence.collect_pattern_evidence",
        _forbidden,
    )
    monkeypatch.setattr("pytics.semantics.physical.classify_physical_dtype", _forbidden)
    evidence = collect_string_content_evidence(series, structure, physical)
    assert evidence.string_structure is structure
    assert evidence.total_token_count == 4
    assert evidence.n_distinct_tokens == 3


def test_string_structure_collection_does_not_collect_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("string structure collected string content")

    monkeypatch.setattr(content_module, "collect_string_content_evidence", _forbidden)
    source = inspect.getsource(string_module)
    assert "collect_string_content_evidence" not in source
    assert "StringContentEvidence" not in source
    series = pd.Series(["hello world"], dtype="string")
    structure = collect_string_structure_evidence(
        series,
        collect_basic_column_evidence(series),
        classify_physical_dtype(series),
    )
    assert structure.contains_whitespace_count == 1


def test_candidate_assessors_do_not_collect_string_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a candidate assessor collected string content")

    monkeypatch.setattr(content_module, "collect_string_content_evidence", _forbidden)
    for module in (core_module, identifier_module):
        source = inspect.getsource(module)
        assert "collect_string_content_evidence" not in source
        assert "StringContentEvidence" not in source
    cities = pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string")
    _assert_not_supported(
        _assess(assess_categorical_candidate, cities), SemanticType.CATEGORICAL
    )
    _assert_not_supported(_assess(assess_text_candidate, cities), SemanticType.TEXT)


def test_one_token_labels_do_not_support_categorical_or_text() -> None:
    series = pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string")
    evidence = _collect(series)
    assert evidence.one_token_ratio == 1.0
    assert evidence.n_distinct_tokens == 3
    _assert_not_supported(
        _assess(assess_categorical_candidate, series),
        SemanticType.CATEGORICAL,
    )
    _assert_not_supported(_assess(assess_text_candidate, series), SemanticType.TEXT)


def test_multiple_token_sentences_do_not_support_text_or_categorical() -> None:
    series = pd.Series(
        ["This is one sentence.", "This is another sentence."],
        dtype="string",
    )
    evidence = _collect(series)
    assert evidence.multiple_token_ratio == 1.0
    assert evidence.total_token_count > evidence.string_structure.basic.n_non_missing
    _assert_not_supported(_assess(assess_text_candidate, series), SemanticType.TEXT)
    _assert_not_supported(
        _assess(assess_categorical_candidate, series),
        SemanticType.CATEGORICAL,
    )


def test_multi_word_place_names_do_not_support_text() -> None:
    series = pd.Series(["New York", "Los Angeles"], dtype="string")
    evidence = _collect(series)
    assert evidence.strings_with_multiple_tokens_count == 2
    _assert_not_supported(_assess(assess_text_candidate, series), SemanticType.TEXT)
    _assert_not_supported(
        _assess(assess_categorical_candidate, series),
        SemanticType.CATEGORICAL,
    )


def test_existing_candidate_rules_stay_in_place() -> None:
    numbers = pd.Series([1, 2, 3, 4])
    numeric = _assess(assess_numeric_candidate, numbers)
    assert numeric.disposition is CandidateDisposition.SUPPORTED
    assert numeric.semantic_type is SemanticType.NUMERIC
    binary = pd.Series([0, 1, 0, 1])
    binary_numeric = _assess(assess_numeric_candidate, binary)
    assert binary_numeric.disposition is CandidateDisposition.SUPPORTED
    _assert_not_supported(
        _assess(assess_categorical_candidate, binary),
        SemanticType.CATEGORICAL,
    )
    _assert_not_supported(_assess(assess_text_candidate, binary), SemanticType.TEXT)
    labels = pd.Series(["red", "blue", "red"], dtype="category")
    categorical = _assess(assess_categorical_candidate, labels)
    assert categorical.disposition is CandidateDisposition.SUPPORTED
    assert categorical.semantic_type is SemanticType.CATEGORICAL
    uuids = pd.Series([_UUID_A, _UUID_B], dtype="string")
    identifier = _assess(assess_identifier_candidate, uuids)
    assert identifier.disposition is CandidateDisposition.SUPPORTED
    assert identifier.semantic_type is SemanticType.IDENTIFIER
    _assert_not_supported(
        _assess(assess_categorical_candidate, uuids),
        SemanticType.CATEGORICAL,
    )
    _assert_not_supported(_assess(assess_text_candidate, uuids), SemanticType.TEXT)


def test_precedence_does_not_collect_string_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("precedence collected string content")

    monkeypatch.setattr(content_module, "collect_string_content_evidence", _forbidden)
    for module in (
        empty_constant_module,
        physical_boolean_module,
        physical_datetime_module,
        physical_timedelta_module,
        string_module,
        core_module,
        identifier_module,
    ):
        source = inspect.getsource(module)
        assert "collect_string_content_evidence" not in source

    empty = interpret_series_precedence(pd.Series([pd.NA, pd.NA], dtype="string"))
    constant = interpret_series_precedence(pd.Series(["aa", "aa"], dtype="string"))
    boolean = interpret_series_precedence(pd.Series([True, False, True]))
    native = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"]))
    )
    aware = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2026-01-01T12:00:00Z", "2026-01-02T12:00:00Z"]))
    )
    duration = interpret_series_precedence(
        pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    )
    numeric = interpret_series_precedence(pd.Series([1.5, 2.5, 3.5]))
    ordinary = interpret_series_precedence(
        pd.Series(["apple", "banana"], dtype="string")
    )
    uuids = interpret_series_precedence(pd.Series([_UUID_A, _UUID_B], dtype="string"))

    assert empty is not None and empty.semantic_type is SemanticType.EMPTY
    assert constant is not None and constant.semantic_type is SemanticType.CONSTANT
    assert boolean is not None and boolean.semantic_type is SemanticType.BOOLEAN
    assert boolean.source is InferenceSource.PHYSICAL_DTYPE
    assert native is not None and native.semantic_type is SemanticType.DATETIME
    assert aware is not None
    assert aware.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert duration is not None and duration.semantic_type is SemanticType.TIMEDELTA
    assert numeric is None
    assert ordinary is None
    assert uuids is None


def test_string_content_is_not_part_of_the_public_api() -> None:
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "collect_string_content_evidence")
    assert not hasattr(pytics, "StringContentEvidence")
    assert not hasattr(semantics_package, "collect_string_content_evidence")
    assert not hasattr(semantics_package, "StringContentEvidence")


def test_collector_signature_does_not_accept_a_column_name() -> None:
    parameters = list(inspect.signature(collect_string_content_evidence).parameters)
    assert parameters == ["series", "string_structure", "physical"]
