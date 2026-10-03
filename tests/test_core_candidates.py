"""TSK-012: Numeric, Categorical, and Text candidates without resolution."""

from __future__ import annotations

import dataclasses
import inspect
import re

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
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.core_candidates import assess_categorical_candidate
from pytics.semantics.core_candidates import assess_numeric_candidate
from pytics.semantics.core_candidates import assess_text_candidate
from pytics.semantics.frequency_evidence import collect_frequency_evidence
from pytics.semantics.identifier_candidate import assess_identifier_candidate
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.numeric_structure_evidence import (
    collect_numeric_structure_evidence,
)
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_series_precedence
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import collect_string_structure_evidence

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_INTEGER_STATEMENT = "Physical dtype family INTEGER supports a Numeric reading."
_FLOATING_STATEMENT = "Physical dtype family FLOATING supports a Numeric reading."
_CATEGORICAL_STATEMENT = "Physical categorical storage supports a Categorical reading."

_ASSESSORS = (
    assess_numeric_candidate,
    assess_categorical_candidate,
    assess_text_candidate,
)


def _inputs(series: pd.Series) -> tuple:
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


def _call(assess, inputs: tuple) -> CandidateAssessment:
    basic, physical, frequency, numeric, structure, pattern = inputs
    return assess(
        basic,
        physical,
        frequency=frequency,
        numeric_structure=numeric,
        string_structure=structure,
        pattern=pattern,
    )


def _assert_assessment(
    result: CandidateAssessment,
    semantic_type: SemanticType,
) -> None:
    assert isinstance(result, CandidateAssessment)
    assert not isinstance(result, SemanticInterpretation)
    assert [field.name for field in dataclasses.fields(result)] == [
        "semantic_type",
        "disposition",
        "supporting_evidence",
        "contradicting_evidence",
    ]
    assert result.semantic_type is semantic_type
    assert result.contradicting_evidence == ()
    assert not hasattr(result, "confidence")
    assert not hasattr(result, "score")


def _assert_supported(
    result: CandidateAssessment,
    semantic_type: SemanticType,
    statement: str,
) -> None:
    _assert_assessment(result, semantic_type)
    assert result.disposition is CandidateDisposition.SUPPORTED
    assert tuple(item.statement for item in result.supporting_evidence) == (statement,)
    lowered = statement.lower()
    assert "this column is" not in lowered
    assert "boolean" not in lowered
    assert "binary" not in lowered
    assert "ordinal" not in lowered


def _assert_not(
    result: CandidateAssessment,
    semantic_type: SemanticType,
) -> None:
    _assert_assessment(result, semantic_type)
    assert result.disposition is CandidateDisposition.NOT_SUPPORTED
    assert result.supporting_evidence == ()


def _equal_basic(basic: BasicColumnEvidence) -> BasicColumnEvidence:
    return BasicColumnEvidence(
        n_total=basic.n_total,
        n_missing=basic.n_missing,
        n_non_missing=basic.n_non_missing,
        n_unique_non_missing=basic.n_unique_non_missing,
    )


def _aware_datetimes() -> pd.Series:
    return pd.Series(pd.to_datetime(["2026-01-01T12:00:00Z", "2026-01-02T12:00:00Z"]))


def test_assessors_consume_evidence_and_do_not_take_a_series():
    expected = [
        "basic",
        "physical",
        "frequency",
        "numeric_structure",
        "string_structure",
        "pattern",
    ]
    for assess in _ASSESSORS:
        assert list(inspect.signature(assess).parameters) == expected
    source = inspect.getsource(core_module)
    assert "CONTRADICTED" not in source
    assert "assess_identifier_candidate" not in source
    assert "import pandas" not in source
    assert "import numpy" not in source
    for token in (
        "to_numeric",
        "to_datetime",
        "unique_ratio",
        "most_frequent",
        "singleton",
        "max_length",
        "min_length",
        "contains_whitespace",
        "finite_ratio",
        "integer_like",
        "is_non_decreasing",
        "is_non_increasing",
        "step_size",
        "constant_step",
        "regular_sequence",
        "consecutive",
        "word_count",
        "token_count",
        "Confidence",
        "SemanticInterpretation",
        "ORDINAL",
        "ordinal",
        "Binary",
        "score",
        "weight",
        "probability",
        "candidate_rank",
        "resolve_",
        "astype",
        "float(",
        "int(",
        "pd.",
        "np.",
    ):
        assert token not in source
    assert re.search(r"\d", source) is None
    assert "<=" not in source
    assert ">=" not in source
    assert "==" not in source


def test_numeric_assessment_does_not_consult_other_candidates(
    monkeypatch: pytest.MonkeyPatch,
):
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("numeric assessment consulted another candidate")

    monkeypatch.setattr(core_module, "assess_categorical_candidate", _forbidden)
    monkeypatch.setattr(core_module, "assess_text_candidate", _forbidden)
    monkeypatch.setattr(identifier_module, "assess_identifier_candidate", _forbidden)
    result = _call(assess_numeric_candidate, _inputs(pd.Series([1, 2, 3, 4, 5])))
    _assert_supported(result, SemanticType.NUMERIC, _INTEGER_STATEMENT)


def test_assessment_does_not_recollect_observations(monkeypatch: pytest.MonkeyPatch):
    numeric_inputs = _inputs(pd.Series([-5, -1, 0, 4, 9]))
    text_inputs = _inputs(pd.Series(["red", "blue", "green"], dtype="string"))

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
    monkeypatch.setattr("pytics.semantics.physical.classify_physical_dtype", _forbidden)
    monkeypatch.setattr(pd, "to_numeric", _forbidden)
    for name in (
        "collect_basic_column_evidence",
        "collect_frequency_evidence",
        "collect_numeric_structure_evidence",
        "collect_string_structure_evidence",
        "collect_pattern_evidence",
        "classify_physical_dtype",
    ):
        assert not hasattr(core_module, name)

    _assert_supported(
        _call(assess_numeric_candidate, numeric_inputs),
        SemanticType.NUMERIC,
        _INTEGER_STATEMENT,
    )
    _assert_not(_call(assess_text_candidate, text_inputs), SemanticType.TEXT)
    _assert_not(
        _call(assess_categorical_candidate, text_inputs),
        SemanticType.CATEGORICAL,
    )


def test_precedence_does_not_assess_candidates(monkeypatch: pytest.MonkeyPatch):
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("precedence called a candidate assessor")

    monkeypatch.setattr(identifier_module, "assess_identifier_candidate", _forbidden)
    monkeypatch.setattr(core_module, "assess_numeric_candidate", _forbidden)
    monkeypatch.setattr(core_module, "assess_categorical_candidate", _forbidden)
    monkeypatch.setattr(core_module, "assess_text_candidate", _forbidden)
    for module in (
        empty_constant_module,
        physical_boolean_module,
        physical_datetime_module,
        physical_timedelta_module,
    ):
        source = inspect.getsource(module)
        for name in (
            "assess_identifier_candidate",
            "assess_numeric_candidate",
            "assess_categorical_candidate",
            "assess_text_candidate",
        ):
            assert name not in source

    empty = interpret_series_precedence(pd.Series([pd.NA, pd.NA], dtype="string"))
    constant = interpret_series_precedence(
        pd.Series(["apple", "apple"], dtype="string")
    )
    boolean = interpret_series_precedence(pd.Series([True, False, True]))
    native = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"]))
    )
    aware = interpret_series_precedence(_aware_datetimes())
    duration = interpret_series_precedence(
        pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    )
    numeric = interpret_series_precedence(pd.Series([1.5, 2.5, 3.5]))
    labels = interpret_series_precedence(pd.Series(["apple", "banana"], dtype="string"))
    uuids = interpret_series_precedence(pd.Series([_UUID_A, _UUID_B], dtype="string"))

    assert empty is not None and empty.semantic_type is SemanticType.EMPTY
    assert constant is not None and constant.semantic_type is SemanticType.CONSTANT
    assert boolean is not None and boolean.semantic_type is SemanticType.BOOLEAN
    assert native is not None and native.semantic_type is SemanticType.DATETIME
    assert native.physical.family is PhysicalDtypeFamily.DATETIME
    assert aware is not None and aware.semantic_type is SemanticType.DATETIME
    assert aware.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert duration is not None and duration.semantic_type is SemanticType.TIMEDELTA
    assert numeric is None
    assert labels is None
    assert uuids is None


def test_core_candidates_are_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    for name in (
        "assess_numeric_candidate",
        "assess_categorical_candidate",
        "assess_text_candidate",
        "assess_identifier_candidate",
        "CandidateAssessment",
    ):
        assert not hasattr(pytics, name)
        assert not hasattr(semantics_package, name)


@pytest.mark.parametrize(
    ("series", "statement"),
    [
        pytest.param(
            pd.Series([-5, -1, 0, 4, 9]),
            _INTEGER_STATEMENT,
            id="signed-integer",
        ),
        pytest.param(
            pd.Series([1, 2, 3], dtype="uint64"),
            _INTEGER_STATEMENT,
            id="unsigned-integer",
        ),
        pytest.param(
            pd.Series([1, pd.NA, 4], dtype="UInt64"),
            _INTEGER_STATEMENT,
            id="nullable-unsigned-integer",
        ),
        pytest.param(
            pd.Series([1, pd.NA, -2], dtype="Int64"),
            _INTEGER_STATEMENT,
            id="nullable-integer",
        ),
        pytest.param(
            pd.Series([0.1, 0.5, 0.9]),
            _FLOATING_STATEMENT,
            id="non-integer-float",
        ),
        pytest.param(
            pd.Series([1.0, pd.NA, -2.5], dtype="Float64"),
            _FLOATING_STATEMENT,
            id="nullable-float",
        ),
        pytest.param(
            pd.Series(pd.arrays.SparseArray([1.0, 0.0, 2.5])),
            _FLOATING_STATEMENT,
            id="sparse-float",
        ),
        pytest.param(
            pd.Series(pd.arrays.SparseArray([1, 0, 2])),
            _INTEGER_STATEMENT,
            id="sparse-integer",
        ),
        pytest.param(
            pd.Series([1.0, np.inf, -4.0]),
            _FLOATING_STATEMENT,
            id="finite-and-infinite-float",
        ),
        pytest.param(
            pd.Series([0, 0, 0, 1, 0]),
            _INTEGER_STATEMENT,
            id="zero-heavy-integer",
        ),
        pytest.param(
            pd.Series([1.0, 2.0, 3.0]),
            _FLOATING_STATEMENT,
            id="integer-like-float",
        ),
        pytest.param(
            pd.Series([1, 2, 3, 4, 5]),
            _INTEGER_STATEMENT,
            id="increasing-integer-sequence",
        ),
        pytest.param(
            pd.Series([5, 4, 3, 2, 1]),
            _INTEGER_STATEMENT,
            id="decreasing-integer-sequence",
        ),
        pytest.param(
            pd.Series([0, 1, 0, 1]),
            _INTEGER_STATEMENT,
            id="zero-one-integer",
        ),
        pytest.param(
            pd.Series([0.0, 1.0, 0.0, 1.0]),
            _FLOATING_STATEMENT,
            id="zero-one-float",
        ),
    ],
)
def test_physical_numeric_storage_supports_numeric(series: pd.Series, statement: str):
    inputs = _inputs(series)
    assert inputs[0].is_empty is False
    assert inputs[0].is_constant is False
    result = _call(assess_numeric_candidate, inputs)
    _assert_supported(result, SemanticType.NUMERIC, statement)
    assert inputs[3] is not None


def test_numeric_support_does_not_require_numeric_structure():
    series = pd.Series([-5, -1, 0, 4, 9])
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    result = assess_numeric_candidate(basic, physical)
    _assert_supported(result, SemanticType.NUMERIC, _INTEGER_STATEMENT)


def test_infinities_remain_numeric_context_without_a_finite_cutoff():
    series = pd.Series([1.0, np.inf, -np.inf, 0.0])
    inputs = _inputs(series)
    numeric = inputs[3]
    assert numeric is not None
    assert numeric.positive_infinity_count == 1
    assert numeric.finite_count == 2
    result = _call(assess_numeric_candidate, inputs)
    _assert_supported(result, SemanticType.NUMERIC, _FLOATING_STATEMENT)
    assert "finite" not in result.supporting_evidence[0].statement.lower()
    assert "infinity" not in result.supporting_evidence[0].statement.lower()


def test_numeric_looking_strings_are_not_parsed(monkeypatch: pytest.MonkeyPatch):
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("numeric candidate parsed strings")

    collected = [
        _inputs(pd.Series(values, dtype="string"))
        for values in (["1", "2", "3"], ["1.2", "4.7", "9.1"])
    ]
    monkeypatch.setattr(pd, "to_numeric", _forbidden)
    for inputs in collected:
        _assert_not(
            _call(assess_numeric_candidate, inputs),
            SemanticType.NUMERIC,
        )


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(pd.Series(["1", "2", "3"], dtype="string"), id="digit-strings"),
        pytest.param(
            pd.Series(["1.2", "4.7", "9.1"], dtype="string"),
            id="decimal-strings",
        ),
        pytest.param(pd.Series([True, False, True]), id="boolean"),
        pytest.param(
            pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"])),
            id="datetime",
        ),
        pytest.param(_aware_datetimes(), id="timezone-aware-datetime"),
        pytest.param(
            pd.Series(pd.to_timedelta(["1 day", "2 days"])),
            id="timedelta",
        ),
        pytest.param(pd.Series([], dtype="int64"), id="zero-length-integer"),
        pytest.param(
            pd.Series([pd.NA, pd.NA], dtype="Int64"),
            id="all-missing-integer",
        ),
        pytest.param(pd.Series([4, 4, 4]), id="constant-integer"),
        pytest.param(pd.Series([1.5, 1.5]), id="constant-float"),
        pytest.param(pd.Series([1 + 1j, 2 + 0j, 3 + 1j]), id="complex"),
        pytest.param(
            pd.Series(pd.Categorical(["red", "blue", "red"])),
            id="categorical-storage",
        ),
    ],
)
def test_numeric_candidate_is_not_supported_outside_its_rule(series: pd.Series):
    inputs = _inputs(series)
    basic = inputs[0]
    physical = inputs[1]
    if physical.family in (
        PhysicalDtypeFamily.INTEGER,
        PhysicalDtypeFamily.FLOATING,
    ):
        assert basic.is_empty or basic.is_constant
    result = _call(assess_numeric_candidate, inputs)
    _assert_not(result, SemanticType.NUMERIC)


def test_zero_one_storage_supports_numeric_without_boolean_inference():
    series = pd.Series([0, 1, 0, 1])
    inputs = _inputs(series)
    assert inputs[1].family is PhysicalDtypeFamily.INTEGER
    _assert_supported(
        _call(assess_numeric_candidate, inputs),
        SemanticType.NUMERIC,
        _INTEGER_STATEMENT,
    )
    _assert_not(
        _call(assess_categorical_candidate, inputs),
        SemanticType.CATEGORICAL,
    )
    _assert_not(_call(assess_text_candidate, inputs), SemanticType.TEXT)
    _assert_not(
        _call(assess_identifier_candidate, inputs),
        SemanticType.IDENTIFIER,
    )
    assert interpret_series_precedence(series) is None


@pytest.mark.parametrize(
    ("series", "ordered"),
    [
        pytest.param(
            pd.Series(pd.Categorical(["red", "blue", "red"])),
            False,
            id="unordered",
        ),
        pytest.param(
            pd.Series(
                pd.Categorical(
                    ["low", "high", "low"],
                    categories=["low", "medium", "high"],
                    ordered=True,
                )
            ),
            True,
            id="ordered",
        ),
        pytest.param(
            pd.Series(
                pd.Categorical(
                    ["red", "blue", "red"],
                    categories=["red", "blue", "green"],
                )
            ),
            False,
            id="unused-level",
        ),
    ],
)
def test_physical_categorical_storage_supports_categorical(
    series: pd.Series,
    ordered: bool,
):
    inputs = _inputs(series)
    physical = inputs[1]
    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert physical.categorical_ordered is ordered
    assert inputs[0].is_constant is False
    result = _call(assess_categorical_candidate, inputs)
    _assert_supported(result, SemanticType.CATEGORICAL, _CATEGORICAL_STATEMENT)
    assert "ORDINAL" not in SemanticType.__members__


def test_unused_categorical_level_does_not_change_the_storage_rule():
    series = pd.Series(
        pd.Categorical(
            ["red", "blue", "red"],
            categories=["red", "blue", "green"],
        )
    )
    inputs = _inputs(series)
    assert inputs[0].n_unique_non_missing == 2
    assert "green" in list(series.cat.categories)
    _assert_supported(
        _call(assess_categorical_candidate, inputs),
        SemanticType.CATEGORICAL,
        _CATEGORICAL_STATEMENT,
    )


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(
            pd.Series(pd.Categorical([None, None])),
            id="empty-categorical",
        ),
        pytest.param(
            pd.Series(pd.Categorical(["red", "red"])),
            id="constant-categorical",
        ),
        pytest.param(
            pd.Series(
                pd.Categorical(
                    ["red", "red"],
                    categories=["red", "blue"],
                    ordered=True,
                )
            ),
            id="constant-ordered-categorical",
        ),
    ],
)
def test_empty_or_constant_categorical_storage_is_not_supported(series: pd.Series):
    inputs = _inputs(series)
    basic = inputs[0]
    physical = inputs[1]
    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert basic.is_empty or basic.is_constant
    ordered = physical.categorical_ordered
    _assert_not(
        _call(assess_categorical_candidate, inputs),
        SemanticType.CATEGORICAL,
    )
    assert physical.categorical_ordered is ordered


def test_repeated_strings_are_not_categorical_without_a_vocabulary_rule():
    series = pd.Series(["red", "blue", "red", "green"], dtype="string")
    inputs = _inputs(series)
    basic, _physical, frequency, _numeric, structure, _pattern = inputs
    assert basic.n_unique_non_missing == 3
    assert frequency.most_frequent_count == 2
    assert structure is not None
    _assert_not(
        _call(assess_categorical_candidate, inputs),
        SemanticType.CATEGORICAL,
    )
    _assert_not(_call(assess_text_candidate, inputs), SemanticType.TEXT)


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(
            pd.Series(["Amsterdam", "Berlin", "Paris", "London"], dtype="string"),
            id="unique-labels",
        ),
        pytest.param(pd.Series(["yes", "no", "yes"], dtype="string"), id="yes-no"),
        pytest.param(pd.Series(["Y", "N", "Y"], dtype="string"), id="y-n"),
        pytest.param(
            pd.Series(["true", "false", "true"], dtype="string"),
            id="true-false",
        ),
        pytest.param(
            pd.Series(["low", "medium", "high", "low"], dtype="string"),
            id="ordered-looking-labels",
        ),
        pytest.param(pd.Series([1, 2, 1, 3, 2]), id="repeated-integers"),
        pytest.param(pd.Series([0, 1, 0, 1]), id="zero-one-integers"),
        pytest.param(pd.Series([True, False, True]), id="boolean"),
        pytest.param(
            pd.Series([_UUID_A, _UUID_B, _UUID_A], dtype="string"),
            id="uuid",
        ),
        pytest.param(
            pd.Series(["192.0.2.1", "198.51.100.2", "192.0.2.1"], dtype="string"),
            id="ipv4",
        ),
        pytest.param(
            pd.Series(["2001:db8::1", "2001:db8::2"], dtype="string"),
            id="ipv6",
        ),
    ],
)
def test_categorical_candidate_is_not_supported_without_categorical_storage(
    series: pd.Series,
):
    inputs = _inputs(series)
    assert inputs[1].family is not PhysicalDtypeFamily.CATEGORICAL
    _assert_not(
        _call(assess_categorical_candidate, inputs),
        SemanticType.CATEGORICAL,
    )
    assert "ORDINAL" not in SemanticType.__members__


def test_low_cardinality_integers_support_numeric_not_categorical():
    series = pd.Series([1, 2, 1, 3, 2])
    inputs = _inputs(series)
    assert inputs[0].n_unique_non_missing == 3
    _assert_supported(
        _call(assess_numeric_candidate, inputs),
        SemanticType.NUMERIC,
        _INTEGER_STATEMENT,
    )
    _assert_not(
        _call(assess_categorical_candidate, inputs),
        SemanticType.CATEGORICAL,
    )


def test_prose_like_strings_do_not_support_text():
    series = pd.Series(
        [
            "This is a long sentence about the city and its river.",
            "Another sentence follows with several ordinary words.",
        ],
        dtype="string",
    )
    inputs = _inputs(series)
    basic = inputs[0]
    structure = inputs[4]
    assert structure is not None
    assert structure.max_length == max(len(value) for value in series)
    assert structure.contains_whitespace_count == basic.n_non_missing
    assert structure.contains_other_count == basic.n_non_missing
    _assert_not(_call(assess_text_candidate, inputs), SemanticType.TEXT)
    _assert_not(
        _call(assess_categorical_candidate, inputs),
        SemanticType.CATEGORICAL,
    )
    _assert_not(
        _call(assess_identifier_candidate, inputs),
        SemanticType.IDENTIFIER,
    )
    _assert_not(_call(assess_numeric_candidate, inputs), SemanticType.NUMERIC)


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(
            pd.Series(["alpha", "beta", "gamma"], dtype="string"),
            id="ordinary-words",
        ),
        pytest.param(
            pd.Series(["red", "blue", "red", "green"], dtype="string"),
            id="repeated-labels",
        ),
        pytest.param(
            pd.Series(["Amsterdam", "Berlin", "Paris", "London"], dtype="string"),
            id="unique-labels",
        ),
        pytest.param(
            pd.Series(["red blue", "green yellow"], dtype="string"),
            id="internal-whitespace",
        ),
        pytest.param(
            pd.Series(["antidisestablishmentarianism", "x" * 80], dtype="string"),
            id="long-strings",
        ),
        pytest.param(
            pd.Series(["hello,", "world!"], dtype="string"),
            id="punctuation",
        ),
        pytest.param(
            pd.Series(["room 12", "aisle 4"], dtype="string"),
            id="mixed-alphanumeric",
        ),
        pytest.param(
            pd.Series([_UUID_A, _UUID_B], dtype="string"),
            id="uuid",
        ),
        pytest.param(
            pd.Series(["0123456789abcdef" * 4, "fedcba9876543210" * 4], dtype="string"),
            id="hex",
        ),
        pytest.param(
            pd.Series(["192.0.2.1", "198.51.100.2"], dtype="string"),
            id="ipv4",
        ),
        pytest.param(
            pd.Series(["2001:db8::1", "2001:db8::2"], dtype="string"),
            id="ipv6",
        ),
        pytest.param(
            pd.Series(["1", "2", "3"], dtype="string"),
            id="numeric-looking",
        ),
        pytest.param(
            pd.Series(["user@example.com", "other@example.com"], dtype="string"),
            id="email-like",
        ),
        pytest.param(
            pd.Series(
                ["https://example.com/a", "https://example.com/b"],
                dtype="string",
            ),
            id="url-like",
        ),
        pytest.param(pd.Series([], dtype="string"), id="zero-length-string"),
        pytest.param(
            pd.Series([pd.NA, pd.NA], dtype="string"),
            id="all-missing-string",
        ),
        pytest.param(
            pd.Series(
                [
                    "This is a paragraph of text.",
                    "This is a paragraph of text.",
                ],
                dtype="string",
            ),
            id="constant-paragraph",
        ),
        pytest.param(
            pd.Series(pd.Categorical(["alpha", "beta", "alpha"])),
            id="categorical-labels",
        ),
        pytest.param(pd.Series([1, 2, 3]), id="numeric"),
        pytest.param(pd.Series([True, False, True]), id="boolean"),
        pytest.param(
            pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"])),
            id="datetime",
        ),
        pytest.param(
            pd.Series(["Amsterdam", "Berlin", "Paris"], dtype=object),
            id="object-strings",
        ),
    ],
)
def test_current_observations_do_not_support_text(series: pd.Series):
    _assert_not(_call(assess_text_candidate, _inputs(series)), SemanticType.TEXT)


@pytest.mark.parametrize(
    ("series", "expected"),
    [
        pytest.param(
            pd.Series([1, 2, 3, 4, 5]),
            {
                SemanticType.NUMERIC: CandidateDisposition.SUPPORTED,
                SemanticType.IDENTIFIER: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.CATEGORICAL: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.TEXT: CandidateDisposition.NOT_SUPPORTED,
            },
            id="ordinary-numeric",
        ),
        pytest.param(
            pd.Series(pd.Categorical(["red", "blue", "red"])),
            {
                SemanticType.CATEGORICAL: CandidateDisposition.SUPPORTED,
                SemanticType.NUMERIC: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.TEXT: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.IDENTIFIER: CandidateDisposition.NOT_SUPPORTED,
            },
            id="physical-categorical",
        ),
        pytest.param(
            pd.Series([_UUID_A, _UUID_B], dtype="string"),
            {
                SemanticType.IDENTIFIER: CandidateDisposition.SUPPORTED,
                SemanticType.NUMERIC: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.CATEGORICAL: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.TEXT: CandidateDisposition.NOT_SUPPORTED,
            },
            id="uuid-strings",
        ),
        pytest.param(
            pd.Series(["Amsterdam", "Berlin", "Paris", "London"], dtype="string"),
            {
                SemanticType.IDENTIFIER: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.NUMERIC: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.CATEGORICAL: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.TEXT: CandidateDisposition.NOT_SUPPORTED,
            },
            id="ordinary-strings",
        ),
        pytest.param(
            pd.Series([_UUID_A, _UUID_A], dtype="string"),
            {
                SemanticType.IDENTIFIER: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.NUMERIC: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.CATEGORICAL: CandidateDisposition.NOT_SUPPORTED,
                SemanticType.TEXT: CandidateDisposition.NOT_SUPPORTED,
            },
            id="constant-uuid",
        ),
    ],
)
def test_candidates_are_assessed_independently(
    series: pd.Series,
    expected: dict,
):
    inputs = _inputs(series)
    if inputs[0].is_constant and inputs[5] is not None:
        assert inputs[5].uuid_count == inputs[0].n_non_missing
    assessed = {
        SemanticType.NUMERIC: _call(assess_numeric_candidate, inputs),
        SemanticType.CATEGORICAL: _call(assess_categorical_candidate, inputs),
        SemanticType.TEXT: _call(assess_text_candidate, inputs),
        SemanticType.IDENTIFIER: _call(assess_identifier_candidate, inputs),
    }
    for semantic_type, disposition in expected.items():
        result = assessed[semantic_type]
        _assert_assessment(result, semantic_type)
        assert result.disposition is disposition
        if disposition is CandidateDisposition.NOT_SUPPORTED:
            assert result.supporting_evidence == ()
    reading = interpret_series_precedence(series)
    assert not isinstance(reading, CandidateAssessment)
    if inputs[0].is_constant:
        assert reading is not None
        assert reading.semantic_type is SemanticType.CONSTANT


def test_frequency_from_another_column_is_rejected():
    series = pd.Series(["apple", "banana"], dtype="string")
    basic = collect_basic_column_evidence(series)
    other = _equal_basic(basic)
    frequency = collect_frequency_evidence(series, other)
    physical = classify_physical_dtype(series)
    assert other == basic
    assert other is not basic
    for assess in _ASSESSORS:
        with pytest.raises(ValueError, match="frequency evidence was not collected"):
            assess(basic, physical, frequency=frequency)


def test_numeric_structure_from_another_column_is_rejected():
    series = pd.Series([1, 2, 3, 4])
    basic = collect_basic_column_evidence(series)
    other = _equal_basic(basic)
    physical = classify_physical_dtype(series)
    numeric = collect_numeric_structure_evidence(series, other, physical)
    for assess in _ASSESSORS:
        with pytest.raises(
            ValueError,
            match="numeric structure evidence was not collected",
        ):
            assess(basic, physical, numeric_structure=numeric)


def test_string_structure_from_another_column_is_rejected():
    series = pd.Series(["apple", "banana"], dtype="string")
    basic = collect_basic_column_evidence(series)
    other = _equal_basic(basic)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, other, physical)
    for assess in _ASSESSORS:
        with pytest.raises(
            ValueError,
            match="string structure evidence was not collected",
        ):
            assess(basic, physical, string_structure=structure)


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
    for assess in _ASSESSORS:
        with pytest.raises(ValueError, match="pattern evidence was not collected"):
            assess(basic, physical, string_structure=other, pattern=pattern)


def test_pattern_without_string_structure_is_rejected():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic, physical, _frequency, _numeric, _structure, pattern = _inputs(series)
    for assess in _ASSESSORS:
        with pytest.raises(ValueError, match="pattern evidence was not collected"):
            assess(basic, physical, pattern=pattern)


def test_string_evidence_rejects_a_non_string_physical_dtype():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic, _physical, _frequency, _numeric, structure, pattern = _inputs(series)
    integer = PhysicalDtype(PhysicalDtypeFamily.INTEGER, "int64")
    for assess in _ASSESSORS:
        with pytest.raises(
            ValueError, match="string structure evidence does not apply"
        ):
            assess(
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
    for assess in _ASSESSORS:
        with pytest.raises(
            ValueError,
            match="numeric structure evidence does not apply",
        ):
            assess(basic, string_physical, numeric_structure=numeric)


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
    basic, physical, frequency, numeric, structure, pattern = _inputs(
        pd.Series([1, 2, 3, 4])
    )
    kwargs = {
        "basic": basic,
        "physical": physical,
        "frequency": frequency,
        "numeric_structure": numeric,
        "string_structure": structure,
        "pattern": pattern,
    }
    kwargs[field] = value
    for assess in _ASSESSORS:
        with pytest.raises(TypeError, match=message):
            assess(**kwargs)
