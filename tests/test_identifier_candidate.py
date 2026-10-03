"""TSK-011: Identifier candidate assessment without resolution."""

from __future__ import annotations

import dataclasses
import inspect
from typing import Optional

import pandas as pd
import pytest

import pytics
import pytics.semantics as semantics_package
import pytics.semantics.empty_constant as empty_constant_module
import pytics.semantics.identifier_candidate as identifier_module
import pytics.semantics.physical_boolean as physical_boolean_module
import pytics.semantics.physical_datetime as physical_datetime_module
import pytics.semantics.physical_timedelta as physical_timedelta_module
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.frequency_evidence import FrequencyEvidence
from pytics.semantics.frequency_evidence import collect_frequency_evidence
from pytics.semantics.identifier_candidate import assess_identifier_candidate
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.numeric_structure_evidence import NumericStructureEvidence
from pytics.semantics.numeric_structure_evidence import (
    collect_numeric_structure_evidence,
)
from pytics.semantics.pattern_evidence import PatternEvidence
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_series_precedence
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import collect_string_structure_evidence

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_UUID_C = "123e4567-e89b-12d3-a456-426614174000"
_COMPACT_A = "550e8400e29b41d4a716446655440000"
_COMPACT_B = "6ba7b8109dad11d180b400c04fd430c8"

_Inputs = tuple[
    BasicColumnEvidence,
    PhysicalDtype,
    FrequencyEvidence,
    Optional[NumericStructureEvidence],
    Optional[StringStructureEvidence],
    Optional[PatternEvidence],
]


def _hex_token(width: int, last: str = "a") -> str:
    token = ("0123456789abcdef" * ((width // 16) + 1))[:width]
    return token[:-1] + last


def _uuid_statement(count: int) -> str:
    return f"All {count} non-missing values match the UUID syntax."


def _hex_statement(count: int, width: int) -> str:
    return f"All {count} non-missing values are {width}-character ASCII hexadecimal tokens."


def _inputs(series: pd.Series) -> _Inputs:
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
        numeric = collect_numeric_structure_evidence(series, basic, physical)
    elif physical.family in (
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    ):
        structure = collect_string_structure_evidence(series, basic, physical)
        pattern = collect_pattern_evidence(series, structure, physical)
    return basic, physical, frequency, numeric, structure, pattern


def _assess(series: pd.Series) -> CandidateAssessment:
    return _assess_inputs(_inputs(series))


def _assess_inputs(inputs: _Inputs) -> CandidateAssessment:
    basic, physical, frequency, numeric, structure, pattern = inputs
    return assess_identifier_candidate(
        basic,
        physical,
        frequency=frequency,
        numeric_structure=numeric,
        string_structure=structure,
        pattern=pattern,
    )


def _assert_identifier(result: CandidateAssessment) -> None:
    assert isinstance(result, CandidateAssessment)
    assert not isinstance(result, SemanticInterpretation)
    assert result.semantic_type is SemanticType.IDENTIFIER
    assert result.contradicting_evidence == ()
    assert not hasattr(result, "confidence")
    assert not hasattr(result, "score")


def _assert_not_supported(series: pd.Series) -> CandidateAssessment:
    result = _assess(series)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED
    assert result.supporting_evidence == ()
    return result


def _assert_supported(
    series: pd.Series, statements: tuple[str, ...]
) -> CandidateAssessment:
    result = _assess(series)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert tuple(item.statement for item in result.supporting_evidence) == statements
    for statement in statements:
        lowered = statement.lower()
        assert "identifier" not in lowered
        assert "unique" not in lowered
        assert "sha" not in lowered
        assert "md5" not in lowered
        assert "hash" not in lowered
    return result


def _equal_basic(basic: BasicColumnEvidence) -> BasicColumnEvidence:
    return BasicColumnEvidence(
        n_total=basic.n_total,
        n_missing=basic.n_missing,
        n_non_missing=basic.n_non_missing,
        n_unique_non_missing=basic.n_unique_non_missing,
    )


def test_assessor_consumes_evidence_and_does_not_take_a_series():
    assert list(inspect.signature(assess_identifier_candidate).parameters) == [
        "basic",
        "physical",
        "frequency",
        "numeric_structure",
        "string_structure",
        "pattern",
    ]


def test_identifier_rules_do_not_read_weak_signals_or_assign_confidence():
    source = inspect.getsource(identifier_module)
    for token in (
        "unique_ratio",
        "singleton_ratio",
        "most_frequent",
        "is_non_decreasing",
        "is_non_increasing",
        "integer_like",
        "step_size",
        "regular_step",
        "Confidence",
        "SemanticInterpretation",
        "CandidateDisposition.CONTRADICTED",
        "sha256",
        "md5",
    ):
        assert token not in source
    # ``n_non_missing`` is the pattern population. Missingness is not read.
    assert "n_missing" not in source.replace("n_non_missing", "")


def test_canonical_uuid_population_is_supported():
    series = pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string")
    result = _assert_supported(series, (_uuid_statement(3),))
    assert result.supporting_evidence[0].statement == (
        "All 3 non-missing values match the UUID syntax."
    )


def test_compact_uuid_population_is_supported():
    series = pd.Series([_COMPACT_A, _COMPACT_B], dtype="string")
    _assert_supported(series, (_uuid_statement(2), _hex_statement(2, 32)))


def test_uppercase_uuid_population_is_supported():
    series = pd.Series([_UUID_A.upper(), _UUID_B.upper()], dtype="string")
    _assert_supported(series, (_uuid_statement(2),))


def test_duplicate_uuids_stay_supported():
    series = pd.Series([_UUID_A, _UUID_A, _UUID_B], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].is_constant is False
    assert inputs[0].unique_ratio_non_missing is not None
    assert inputs[0].unique_ratio_non_missing < 1.0
    assert inputs[5] is not None and inputs[5].uuid_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert tuple(item.statement for item in result.supporting_evidence) == (
        _uuid_statement(3),
    )


def test_unique_uuids_are_supported_without_making_uniqueness_the_reason():
    series = pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].unique_ratio_non_missing == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert "unique" not in result.supporting_evidence[0].statement.lower()


def test_object_uuid_population_is_supported():
    series = pd.Series([_UUID_A, _UUID_B], dtype=object)
    inputs = _inputs(series)
    assert inputs[1].family is PhysicalDtypeFamily.OBJECT
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert tuple(item.statement for item in result.supporting_evidence) == (
        _uuid_statement(2),
    )


def test_uuid_with_missing_values_stays_supported():
    series = pd.Series([_UUID_A, pd.NA, _UUID_B], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].n_missing == 1
    assert inputs[5] is not None and inputs[5].uuid_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert tuple(item.statement for item in result.supporting_evidence) == (
        _uuid_statement(2),
    )


@pytest.mark.parametrize("width", [32, 40, 64, 128])
def test_fixed_width_hex_population_is_supported(width: int):
    series = pd.Series(
        [_hex_token(width, "a"), _hex_token(width, "b")],
        dtype="string",
    )
    if width == 32:
        statements = (_uuid_statement(2), _hex_statement(2, 32))
    else:
        statements = (_hex_statement(2, width),)
    result = _assert_supported(series, statements)
    assert "sha" not in result.supporting_evidence[-1].statement.lower()
    assert "md5" not in result.supporting_evidence[-1].statement.lower()


def test_duplicate_fixed_width_hex_stays_supported():
    token_a = _hex_token(64, "a")
    token_b = _hex_token(64, "b")
    series = pd.Series([token_a, token_a, token_b], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].unique_ratio_non_missing is not None
    assert inputs[0].unique_ratio_non_missing < 1.0
    assert inputs[5] is not None and inputs[5].hex_64_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert tuple(item.statement for item in result.supporting_evidence) == (
        _hex_statement(3, 64),
    )


def test_compact_uuid_and_hex_32_overlap_is_supported_without_a_score():
    series = pd.Series([_COMPACT_A, _COMPACT_B], dtype="string")
    inputs = _inputs(series)
    pattern = inputs[5]
    assert pattern is not None
    assert pattern.uuid_ratio == 1.0
    assert pattern.hex_32_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert tuple(item.statement for item in result.supporting_evidence) == (
        _uuid_statement(2),
        _hex_statement(2, 32),
    )
    assert [field.name for field in dataclasses.fields(result)] == [
        "semantic_type",
        "disposition",
        "supporting_evidence",
        "contradicting_evidence",
    ]


def test_unique_arbitrary_strings_are_not_supported():
    series = pd.Series(["apple", "banana", "cherry", "pear"], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].unique_ratio_non_missing == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED
    assert result.supporting_evidence == ()


def test_column_name_does_not_support_identifier():
    series = pd.Series(
        ["apple", "banana", "cherry", "pear"],
        dtype="string",
        name="user_id",
    )
    _assert_not_supported(series)


def test_unique_arbitrary_integers_are_not_supported():
    series = pd.Series([1, 7, 42, 103])
    inputs = _inputs(series)
    assert inputs[0].unique_ratio_non_missing == 1.0
    assert inputs[3] is not None
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_unique_arbitrary_floats_are_not_supported():
    series = pd.Series([10.2, 11.7, 14.9, 19.3])
    inputs = _inputs(series)
    assert inputs[0].unique_ratio_non_missing == 1.0
    assert inputs[0].n_missing == 0
    assert inputs[3] is not None
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_zero_missing_ordinary_strings_are_not_supported():
    series = pd.Series(["red", "blue", "red"], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].n_missing == 0
    assert inputs[0].is_constant is False
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_high_singleton_ratio_alone_is_not_supported():
    series = pd.Series(["apple", "banana", "cherry", "pear"], dtype="string")
    inputs = _inputs(series)
    assert inputs[2].singleton_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED
    assert result.supporting_evidence == ()


def test_partial_uuid_ratio_is_not_supported():
    values = [_UUID_A, _UUID_B] * 4 + [_UUID_A, "not-a-uuid"]
    series = pd.Series(values, dtype="string")
    inputs = _inputs(series)
    assert inputs[5] is not None and inputs[5].uuid_ratio == 0.9
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_partial_hex_ratio_is_not_supported():
    series = pd.Series([_hex_token(64)] * 19 + ["nope"], dtype="string")
    inputs = _inputs(series)
    assert inputs[5] is not None and inputs[5].hex_64_ratio == 0.95
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_full_ipv4_population_is_not_supported():
    series = pd.Series(["192.0.2.1", "192.0.2.2", "192.0.2.3"], dtype="string")
    inputs = _inputs(series)
    assert inputs[5] is not None and inputs[5].ipv4_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_full_ipv6_population_is_not_supported():
    series = pd.Series(["2001:db8::1", "2001:db8::2"], dtype="string")
    inputs = _inputs(series)
    assert inputs[5] is not None and inputs[5].ipv6_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_mixed_strong_patterns_are_not_a_union_rule():
    series = pd.Series([_UUID_A, "192.0.2.1", _hex_token(64)], dtype="string")
    inputs = _inputs(series)
    pattern = inputs[5]
    assert pattern is not None
    assert pattern.uuid_count == 1
    assert pattern.ipv4_count == 1
    assert pattern.hex_64_count == 1
    assert pattern.uuid_count + pattern.ipv4_count + pattern.hex_64_count == 3
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_date_looking_strings_are_not_supported():
    _assert_not_supported(pd.Series(["2020-01-01", "2020-01-02"], dtype="string"))


def test_email_looking_strings_are_not_supported():
    _assert_not_supported(pd.Series(["a@example.com", "b@example.com"], dtype="string"))


def test_url_looking_strings_are_not_supported():
    _assert_not_supported(
        pd.Series(["https://example.com/a", "https://example.org/b"], dtype="string")
    )


def test_ordinary_labels_are_not_supported():
    _assert_not_supported(pd.Series(["red", "blue", "green"], dtype="string"))


def test_physical_categorical_is_not_supported():
    series = pd.Series(["red", "blue", "green"], dtype="category")
    inputs = _inputs(series)
    assert inputs[1].family is PhysicalDtypeFamily.CATEGORICAL
    assert inputs[4] is None
    assert inputs[5] is None
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_physical_boolean_is_not_supported():
    series = pd.Series([True, False, True])
    inputs = _inputs(series)
    assert inputs[1].family is PhysicalDtypeFamily.BOOLEAN
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_physical_datetime_is_not_supported():
    series = pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"]))
    inputs = _inputs(series)
    assert inputs[1].family is PhysicalDtypeFamily.DATETIME
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_physical_timezone_aware_datetime_is_not_supported():
    series = pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"], utc=True))
    inputs = _inputs(series)
    assert inputs[1].family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_physical_timedelta_is_not_supported():
    series = pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    inputs = _inputs(series)
    assert inputs[1].family is PhysicalDtypeFamily.TIMEDELTA
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_empty_string_column_is_not_supported():
    series = pd.Series([pd.NA, pd.NA], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].is_empty is True
    assert inputs[5] is not None and inputs[5].uuid_ratio is None
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_zero_length_string_column_is_not_supported():
    series = pd.Series([], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].n_total == 0
    assert inputs[0].is_empty is True
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_constant_ordinary_string_is_not_supported():
    series = pd.Series(["apple", "apple"], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].is_constant is True
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_constant_uuid_is_not_supported():
    series = pd.Series([_UUID_A, _UUID_A, _UUID_A], dtype="string")
    inputs = _inputs(series)
    assert inputs[0].is_constant is True
    assert inputs[5] is not None and inputs[5].uuid_ratio == 1.0
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED
    assert result.supporting_evidence == ()


@pytest.mark.parametrize(
    ("values", "non_decreasing"),
    [
        ([1, 2, 3, 4, 5], True),
        ([1001, 1002, 1003, 1004], True),
        ([10, 20, 30, 40], True),
        ([5, 4, 3, 2, 1], False),
    ],
)
def test_numeric_sequences_are_not_identifier_candidates(
    values: list[int],
    non_decreasing: bool,
):
    series = pd.Series(values)
    inputs = _inputs(series)
    basic = inputs[0]
    numeric = inputs[3]
    assert numeric is not None
    assert basic.n_missing == 0
    assert basic.unique_ratio_non_missing == 1.0
    assert numeric.integer_like_ratio == 1.0
    assert numeric.is_non_decreasing is non_decreasing
    assert numeric.is_non_increasing is not non_decreasing
    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED
    assert result.supporting_evidence == ()


def test_uuid_values_without_pattern_evidence_are_not_supported():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic, physical, frequency, _numeric, _structure, _pattern = _inputs(series)
    result = assess_identifier_candidate(basic, physical, frequency=frequency)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED


def test_frequency_from_another_basic_is_rejected():
    series = pd.Series(["apple", "banana"], dtype="string")
    basic = collect_basic_column_evidence(series)
    other = _equal_basic(basic)
    assert other == basic
    assert other is not basic
    frequency = collect_frequency_evidence(series, other)
    physical = classify_physical_dtype(series)

    with pytest.raises(ValueError, match="frequency evidence was not collected"):
        assess_identifier_candidate(basic, physical, frequency=frequency)


def test_numeric_structure_from_another_basic_is_rejected():
    series = pd.Series([1, 2, 3, 4])
    basic = collect_basic_column_evidence(series)
    other = _equal_basic(basic)
    physical = classify_physical_dtype(series)
    numeric = collect_numeric_structure_evidence(series, other, physical)
    assert numeric.basic is other
    assert numeric.basic is not basic

    with pytest.raises(
        ValueError, match="numeric structure evidence was not collected"
    ):
        assess_identifier_candidate(basic, physical, numeric_structure=numeric)


def test_string_structure_from_another_basic_is_rejected():
    series = pd.Series(["apple", "banana"], dtype="string")
    basic = collect_basic_column_evidence(series)
    other = _equal_basic(basic)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, other, physical)

    with pytest.raises(ValueError, match="string structure evidence was not collected"):
        assess_identifier_candidate(basic, physical, string_structure=structure)


def test_pattern_from_another_string_structure_is_rejected():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    pattern = collect_pattern_evidence(series, structure, physical)
    other = StringStructureEvidence(
        basic=basic,
        empty_string_count=structure.empty_string_count,
        whitespace_only_count=structure.whitespace_only_count,
        contains_whitespace_count=structure.contains_whitespace_count,
        contains_alpha_count=structure.contains_alpha_count,
        contains_digit_count=structure.contains_digit_count,
        contains_other_count=structure.contains_other_count,
        min_length=structure.min_length,
        max_length=structure.max_length,
    )
    assert other == structure
    assert other is not structure
    assert pattern.string_structure is structure

    with pytest.raises(ValueError, match="pattern evidence was not collected"):
        assess_identifier_candidate(
            basic,
            physical,
            string_structure=other,
            pattern=pattern,
        )


def test_pattern_without_string_structure_is_rejected():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic, physical, _frequency, _numeric, structure, pattern = _inputs(series)
    assert structure is not None and pattern is not None
    assert pattern.string_structure is structure

    with pytest.raises(ValueError, match="pattern evidence was not collected"):
        assess_identifier_candidate(basic, physical, pattern=pattern)


def test_string_evidence_rejects_a_non_string_physical_dtype():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic, _physical, _frequency, _numeric, structure, pattern = _inputs(series)
    integer = PhysicalDtype(PhysicalDtypeFamily.INTEGER, "int64")

    with pytest.raises(ValueError, match="string structure evidence does not apply"):
        assess_identifier_candidate(
            basic,
            integer,
            string_structure=structure,
            pattern=pattern,
        )


def test_numeric_evidence_rejects_a_non_numeric_physical_dtype():
    series = pd.Series([1, 2, 3, 4])
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    numeric = collect_numeric_structure_evidence(series, basic, physical)
    string_physical = PhysicalDtype(PhysicalDtypeFamily.STRING, "string")

    with pytest.raises(ValueError, match="numeric structure evidence does not apply"):
        assess_identifier_candidate(
            basic,
            string_physical,
            numeric_structure=numeric,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("basic", object(), "basic must be BasicColumnEvidence"),
        ("physical", object(), "physical must be a PhysicalDtype"),
        ("frequency", object(), "frequency must be FrequencyEvidence"),
        (
            "numeric_structure",
            object(),
            "numeric_structure must be NumericStructureEvidence",
        ),
        (
            "string_structure",
            object(),
            "string_structure must be StringStructureEvidence",
        ),
        ("pattern", object(), "pattern must be PatternEvidence"),
    ],
)
def test_wrong_evidence_types_are_rejected(field: str, value: object, message: str):
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic, physical, frequency, numeric, structure, pattern = _inputs(series)
    kwargs = {
        "basic": basic,
        "physical": physical,
        "frequency": frequency,
        "numeric_structure": numeric,
        "string_structure": structure,
        "pattern": pattern,
    }
    kwargs[field] = value
    with pytest.raises(TypeError, match=message):
        assess_identifier_candidate(**kwargs)  # type: ignore[arg-type]


def test_assessment_does_not_recollect_observations(monkeypatch: pytest.MonkeyPatch):
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    inputs = _inputs(series)

    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("candidate assessment recollected observations")

    monkeypatch.setattr(
        "pytics.semantics.column_evidence.collect_basic_column_evidence",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.frequency_evidence.collect_frequency_evidence",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.numeric_structure_evidence.collect_numeric_structure_evidence",
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
    monkeypatch.setattr(
        "pytics.semantics.physical.classify_physical_dtype",
        _forbidden,
    )
    for name in (
        "collect_basic_column_evidence",
        "collect_frequency_evidence",
        "collect_numeric_structure_evidence",
        "collect_string_structure_evidence",
        "collect_pattern_evidence",
        "classify_physical_dtype",
    ):
        assert not hasattr(identifier_module, name)

    result = _assess_inputs(inputs)
    _assert_identifier(result)
    assert result.disposition is CandidateDisposition.SUPPORTED


def test_precedence_does_not_assess_identifier(monkeypatch: pytest.MonkeyPatch):
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("precedence called Identifier assessment")

    monkeypatch.setattr(identifier_module, "assess_identifier_candidate", _forbidden)
    for module in (
        empty_constant_module,
        physical_boolean_module,
        physical_datetime_module,
        physical_timedelta_module,
    ):
        assert "assess_identifier_candidate" not in inspect.getsource(module)

    empty = interpret_series_precedence(pd.Series([pd.NA, pd.NA], dtype="string"))
    constant = interpret_series_precedence(
        pd.Series(["apple", "apple"], dtype="string")
    )
    boolean = interpret_series_precedence(pd.Series([True, False, True]))
    datetime = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"]))
    )
    timedelta = interpret_series_precedence(
        pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    )
    numeric = interpret_series_precedence(pd.Series([1.5, 2.5, 3.5]))
    text = interpret_series_precedence(pd.Series(["apple", "banana"], dtype="string"))
    uuids = interpret_series_precedence(pd.Series([_UUID_A, _UUID_B], dtype="string"))

    assert empty is not None and empty.semantic_type is SemanticType.EMPTY
    assert constant is not None and constant.semantic_type is SemanticType.CONSTANT
    assert boolean is not None and boolean.semantic_type is SemanticType.BOOLEAN
    assert datetime is not None and datetime.semantic_type is SemanticType.DATETIME
    assert timedelta is not None and timedelta.semantic_type is SemanticType.TIMEDELTA
    assert numeric is None
    assert text is None
    assert uuids is None


def test_supported_candidate_does_not_change_the_uuid_precedence_result():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    assessment = _assert_supported(series, (_uuid_statement(2),))
    assert assessment.disposition is CandidateDisposition.SUPPORTED
    assert interpret_series_precedence(series) is None


def test_identifier_assessment_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "assess_identifier_candidate")
    assert not hasattr(pytics, "CandidateAssessment")
    assert not hasattr(semantics_package, "assess_identifier_candidate")
    assert not hasattr(semantics_package, "CandidateAssessment")
