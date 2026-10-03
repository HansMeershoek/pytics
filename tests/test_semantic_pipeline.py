"""TSK-016: column-level semantic pipeline integration."""

from __future__ import annotations

import ast
import inspect

import pandas as pd
import pytest

import pytics
import pytics.analysis.column as column_analysis
import pytics.semantics.pipeline as pipeline
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_series_precedence
from pytics.semantics.pipeline import infer_series_semantics
from pytics.semantics.resolution import ResolutionStatus

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_COMPACT_A = "550e8400e29b41d4a716446655440000"
_COMPACT_B = "6ba7b8109dad11d180b400c04fd430c8"
_CANDIDATE_TYPES = (
    SemanticType.IDENTIFIER,
    SemanticType.NUMERIC,
    SemanticType.CATEGORICAL,
    SemanticType.TEXT,
)
_DOWNSTREAM_COLLECTORS = (
    "collect_numeric_structure_evidence",
    "collect_string_structure_evidence",
    "collect_pattern_evidence",
)
_ASSESSORS = (
    "assess_identifier_candidate",
    "assess_numeric_candidate",
    "assess_categorical_candidate",
    "assess_text_candidate",
)


def _hex_token(width: int, last: str) -> str:
    token = ("0123456789abcdef" * ((width // 16) + 1))[:width]
    return token[:-1] + last


def _disposition(result: InferredSemanticResult, semantic_type: SemanticType):
    for candidate in result.resolution.candidates:
        if candidate.semantic_type is semantic_type:
            return candidate.disposition
    raise AssertionError(f"{semantic_type.name} was not assessed")


def _assert_structural(
    series: pd.Series,
    semantic_type: SemanticType,
    source: InferenceSource,
    family: PhysicalDtypeFamily,
) -> InferredSemanticResult:
    result = infer_series_semantics(series)
    assert isinstance(result, InferredSemanticResult)
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.selected_type is semantic_type
    assert result.interpretation is not None
    assert result.interpretation.semantic_type is semantic_type
    assert result.interpretation.confidence is Confidence.HIGH
    assert result.interpretation.source is source
    assert result.interpretation.physical is result.physical
    assert result.physical.family is family
    assert result.physical.dtype_name == str(series.dtype)
    assert result.physical == classify_physical_dtype(series)
    assert result.resolution.candidates == ()
    assert result.resolution.structural_interpretation is result.interpretation
    return result


def _assert_candidate_resolved(
    series: pd.Series,
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
) -> InferredSemanticResult:
    result = infer_series_semantics(series)
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.selected_type is semantic_type
    assert result.interpretation is None
    assert result.resolution.structural_interpretation is None
    assert result.physical.family is family
    assert result.physical.dtype_name == str(series.dtype)
    assert result.physical.categorical_ordered == (
        classify_physical_dtype(series).categorical_ordered
    )
    assert _disposition(result, semantic_type) is CandidateDisposition.SUPPORTED
    for other in _CANDIDATE_TYPES:
        if other is not semantic_type:
            assert _disposition(result, other) is CandidateDisposition.NOT_SUPPORTED
    assert not hasattr(result, "confidence")
    return result


def _assert_insufficient(
    series: pd.Series,
    family: PhysicalDtypeFamily,
) -> InferredSemanticResult:
    result = infer_series_semantics(series)
    assert result.resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert result.selected_type is None
    assert result.interpretation is None
    assert result.physical.family is family
    assert result.physical.dtype_name == str(series.dtype)
    for semantic_type in _CANDIDATE_TYPES:
        assert _disposition(result, semantic_type) is CandidateDisposition.NOT_SUPPORTED
    return result


def _forbid_call(name: str):
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(f"{name} ran")

    return _forbidden


def test_all_missing_series_resolves_empty():
    series = pd.Series([pd.NA, pd.NA], dtype="string")
    _assert_structural(
        series,
        SemanticType.EMPTY,
        InferenceSource.INFERRED,
        PhysicalDtypeFamily.STRING,
    )


def test_zero_length_series_resolves_empty():
    series = pd.Series([], dtype="float64")
    _assert_structural(
        series,
        SemanticType.EMPTY,
        InferenceSource.INFERRED,
        PhysicalDtypeFamily.FLOATING,
    )


def test_repeated_value_resolves_constant():
    series = pd.Series(["same", "same", "same"], dtype="string")
    _assert_structural(
        series,
        SemanticType.CONSTANT,
        InferenceSource.INFERRED,
        PhysicalDtypeFamily.STRING,
    )


def test_constant_with_missing_stays_constant():
    series = pd.Series(["same", None, "same"], dtype="string")
    _assert_structural(
        series,
        SemanticType.CONSTANT,
        InferenceSource.INFERRED,
        PhysicalDtypeFamily.STRING,
    )


def test_constant_uuid_stays_constant():
    series = pd.Series([_UUID_A, _UUID_A, _UUID_A], dtype="string")
    result = _assert_structural(
        series,
        SemanticType.CONSTANT,
        InferenceSource.INFERRED,
        PhysicalDtypeFamily.STRING,
    )
    assert result.selected_type is not SemanticType.IDENTIFIER


def test_physical_bool_resolves_boolean():
    series = pd.Series([True, False, True])
    _assert_structural(
        series,
        SemanticType.BOOLEAN,
        InferenceSource.PHYSICAL_DTYPE,
        PhysicalDtypeFamily.BOOLEAN,
    )


def test_nullable_boolean_resolves_boolean():
    series = pd.Series([True, False, pd.NA], dtype="boolean")
    _assert_structural(
        series,
        SemanticType.BOOLEAN,
        InferenceSource.PHYSICAL_DTYPE,
        PhysicalDtypeFamily.BOOLEAN,
    )


def test_physical_datetime_resolves_datetime():
    series = pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"]))
    _assert_structural(
        series,
        SemanticType.DATETIME,
        InferenceSource.PHYSICAL_DTYPE,
        PhysicalDtypeFamily.DATETIME,
    )


def test_timezone_aware_datetime_preserves_family():
    series = pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"], utc=True))
    result = _assert_structural(
        series,
        SemanticType.DATETIME,
        InferenceSource.PHYSICAL_DTYPE,
        PhysicalDtypeFamily.DATETIME_TZ_AWARE,
    )
    assert result.interpretation is not None
    assert "timezone-aware" in result.interpretation.evidence[0].statement


def test_physical_timedelta_resolves_timedelta():
    series = pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    _assert_structural(
        series,
        SemanticType.TIMEDELTA,
        InferenceSource.PHYSICAL_DTYPE,
        PhysicalDtypeFamily.TIMEDELTA,
    )


def test_integer_series_resolves_numeric_without_interpretation():
    series = pd.Series([1, 2, 3, 4])
    _assert_candidate_resolved(
        series,
        SemanticType.NUMERIC,
        PhysicalDtypeFamily.INTEGER,
    )


def test_floating_series_resolves_numeric_without_interpretation():
    series = pd.Series([1.5, 2.5, 3.5])
    _assert_candidate_resolved(
        series,
        SemanticType.NUMERIC,
        PhysicalDtypeFamily.FLOATING,
    )


def test_zero_one_integers_stay_numeric():
    series = pd.Series([0, 1, 0, 1])
    result = _assert_candidate_resolved(
        series,
        SemanticType.NUMERIC,
        PhysicalDtypeFamily.INTEGER,
    )
    assert result.selected_type is not SemanticType.BOOLEAN


def test_canonical_uuid_resolves_identifier():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    _assert_candidate_resolved(
        series,
        SemanticType.IDENTIFIER,
        PhysicalDtypeFamily.STRING,
    )


def test_compact_uuid_resolves_identifier():
    series = pd.Series([_COMPACT_A, _COMPACT_B], dtype="string")
    _assert_candidate_resolved(
        series,
        SemanticType.IDENTIFIER,
        PhysicalDtypeFamily.STRING,
    )


def test_fixed_width_hex_resolves_identifier():
    series = pd.Series(
        [_hex_token(64, "a"), _hex_token(64, "b")],
        dtype="string",
    )
    _assert_candidate_resolved(
        series,
        SemanticType.IDENTIFIER,
        PhysicalDtypeFamily.STRING,
    )


def test_duplicate_uuids_stay_identifier():
    series = pd.Series([_UUID_A, _UUID_A, _UUID_B], dtype="string")
    result = _assert_candidate_resolved(
        series,
        SemanticType.IDENTIFIER,
        PhysicalDtypeFamily.STRING,
    )
    assert result.physical.family is PhysicalDtypeFamily.STRING


def test_partial_uuid_population_is_insufficient():
    series = pd.Series([_UUID_A, "not-a-uuid"], dtype="string")
    _assert_insufficient(series, PhysicalDtypeFamily.STRING)


def test_ipv4_population_is_insufficient():
    series = pd.Series(["192.168.0.1", "10.0.0.1"], dtype="string")
    _assert_insufficient(series, PhysicalDtypeFamily.STRING)


def test_physical_categorical_resolves_categorical():
    series = pd.Series(
        pd.Categorical(["a", "b", "a"], categories=["a", "b"], ordered=False)
    )
    result = _assert_candidate_resolved(
        series,
        SemanticType.CATEGORICAL,
        PhysicalDtypeFamily.CATEGORICAL,
    )
    assert result.physical.categorical_ordered is False
    assert result.selected_type is not SemanticType.TEXT


def test_ordered_categorical_keeps_ordered_flag():
    series = pd.Series(
        pd.Categorical(["a", "b", "a"], categories=["a", "b"], ordered=True)
    )
    result = _assert_candidate_resolved(
        series,
        SemanticType.CATEGORICAL,
        PhysicalDtypeFamily.CATEGORICAL,
    )
    assert result.physical.categorical_ordered is True
    assert result.selected_type is SemanticType.CATEGORICAL


def test_city_names_are_insufficient():
    series = pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string")
    _assert_insufficient(series, PhysicalDtypeFamily.STRING)


def test_prose_strings_are_insufficient():
    series = pd.Series(
        [
            "The river runs through the city.",
            "Markets open early in the morning.",
        ],
        dtype="string",
    )
    _assert_insufficient(series, PhysicalDtypeFamily.STRING)


def test_object_strings_are_insufficient_and_keep_object_family():
    series = pd.Series(["Amsterdam", "Berlin", "Paris"], dtype=object)
    _assert_insufficient(series, PhysicalDtypeFamily.OBJECT)


def test_object_uuid_strings_resolve_identifier():
    series = pd.Series([_UUID_A, _UUID_B], dtype=object)
    _assert_candidate_resolved(
        series,
        SemanticType.IDENTIFIER,
        PhysicalDtypeFamily.OBJECT,
    )


def test_mixed_object_values_are_insufficient():
    series = pd.Series(["Amsterdam", 1], dtype=object)
    _assert_insufficient(series, PhysicalDtypeFamily.OBJECT)


def test_bytes_object_values_are_not_decoded():
    series = pd.Series([b"ab", b"cd"])
    _assert_insufficient(series, PhysicalDtypeFamily.OBJECT)


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([1 + 2j, 3 + 4j]),
        pd.Series(pd.period_range("2024-01", periods=3, freq="M")),
    ],
)
def test_unsupported_physical_family_is_insufficient(series: pd.Series):
    family = classify_physical_dtype(series).family
    assert family not in (
        PhysicalDtypeFamily.INTEGER,
        PhysicalDtypeFamily.FLOATING,
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
        PhysicalDtypeFamily.CATEGORICAL,
        PhysicalDtypeFamily.BOOLEAN,
        PhysicalDtypeFamily.DATETIME,
        PhysicalDtypeFamily.DATETIME_TZ_AWARE,
        PhysicalDtypeFamily.TIMEDELTA,
    )
    _assert_insufficient(series, family)


def test_missing_like_literals_stay_ordinary_strings():
    series = pd.Series(
        ["NA", "N/A", "None", "null", "nan", "", " "],
        dtype="string",
    )
    result = _assert_insufficient(series, PhysicalDtypeFamily.STRING)
    assert result.selected_type is not SemanticType.EMPTY
    assert result.interpretation is None


def test_series_name_does_not_select_identifier():
    numbers = pd.Series([1, 2, 3], name="customer_id")
    numeric = _assert_candidate_resolved(
        numbers,
        SemanticType.NUMERIC,
        PhysicalDtypeFamily.INTEGER,
    )
    assert numeric.selected_type is SemanticType.NUMERIC
    cities = pd.Series(["Amsterdam", "Berlin"], dtype="string", name="uuid")
    textual = _assert_insufficient(cities, PhysicalDtypeFamily.STRING)
    assert textual.selected_type is not SemanticType.IDENTIFIER


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([1, 2, 3], name="amount", index=[4, 5, 6]),
        pd.Series(["Amsterdam", "Berlin"], dtype="string", name="city"),
        pd.Series(
            pd.Categorical(["a", "b", "a"], categories=["b", "a"], ordered=True),
            name="label",
            index=pd.Index([9, 8, 7], name="row"),
        ),
        pd.Series(
            pd.to_datetime(["2020-01-01", "2020-06-01"], utc=True),
            name="when",
        ),
    ],
)
def test_input_series_is_not_mutated(series: pd.Series):
    values = series.tolist()
    index = series.index.copy()
    name = series.name
    dtype = series.dtype
    infer_series_semantics(series)
    assert series.tolist() == values
    assert series.index.equals(index)
    assert series.index.name == index.name
    assert series.name == name
    assert series.dtype == dtype
    if isinstance(dtype, pd.CategoricalDtype):
        assert list(series.cat.categories) == list(dtype.categories)
        assert series.cat.ordered is dtype.ordered


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([pd.NA, pd.NA], dtype="string"),
        pd.Series([1, 2, 3, 4]),
        pd.Series([_UUID_A, _UUID_B], dtype="string"),
        pd.Series(pd.Categorical(["a", "b", "a"], categories=["a", "b"], ordered=True)),
    ],
)
def test_physical_dtype_is_classified_once(
    series: pd.Series,
    monkeypatch: pytest.MonkeyPatch,
):
    seen = []
    real = column_analysis.classify_physical_dtype

    def spy(source: object):
        seen.append(source)
        return real(source)

    monkeypatch.setattr(column_analysis, "classify_physical_dtype", spy)
    result = infer_series_semantics(series)
    assert seen == [series]
    assert result.physical == classify_physical_dtype(series)


def test_classified_physical_dtype_object_is_reused(
    monkeypatch: pytest.MonkeyPatch,
):
    series = pd.Series([1, 2, 3])
    seen = []
    real = column_analysis.classify_physical_dtype

    def spy(source: object):
        value = real(source)
        seen.append(value)
        return value

    monkeypatch.setattr(column_analysis, "classify_physical_dtype", spy)
    result = infer_series_semantics(series)
    assert len(seen) == 1
    assert result.physical is seen[0]


def test_structural_interpretation_keeps_the_classified_physical_dtype(
    monkeypatch: pytest.MonkeyPatch,
):
    series = pd.Series([True, False, True])
    seen = []
    real = column_analysis.classify_physical_dtype

    def spy(source: object):
        value = real(source)
        seen.append(value)
        return value

    monkeypatch.setattr(column_analysis, "classify_physical_dtype", spy)
    result = infer_series_semantics(series)
    assert len(seen) == 1
    assert result.interpretation is not None
    assert result.interpretation.physical is seen[0]
    assert result.physical is seen[0]


@pytest.mark.parametrize(
    "series",
    [
        pd.Series(["same", "same"], dtype="string"),
        pd.Series([1.5, 2.5, 3.5]),
        pd.Series(["Amsterdam", "Berlin"], dtype="string"),
        pd.Series(pd.Categorical(["a", "b", "a"])),
    ],
)
def test_basic_evidence_is_collected_once(
    series: pd.Series,
    monkeypatch: pytest.MonkeyPatch,
):
    seen = []
    real = column_analysis.collect_basic_column_evidence

    def spy(value: pd.Series):
        seen.append(value)
        return real(value)

    monkeypatch.setattr(column_analysis, "collect_basic_column_evidence", spy)
    infer_series_semantics(series)
    assert seen == [series]


def test_numeric_evidence_reuses_basic_identity(monkeypatch: pytest.MonkeyPatch):
    series = pd.Series([1, 2, 3, 4])
    basic_seen = []
    numeric_seen = []
    assessor_bundles = []
    real_basic = column_analysis.collect_basic_column_evidence
    real_numeric = column_analysis.collect_numeric_structure_evidence
    real_assess = column_analysis.assess_numeric_candidate

    def basic_spy(value: pd.Series):
        evidence = real_basic(value)
        basic_seen.append(evidence)
        return evidence

    def numeric_spy(value, basic, physical):
        evidence = real_numeric(value, basic, physical)
        numeric_seen.append(evidence)
        return evidence

    def assess_spy(basic, physical, **kwargs):
        assessor_bundles.append((basic, kwargs))
        return real_assess(basic, physical, **kwargs)

    monkeypatch.setattr(column_analysis, "collect_basic_column_evidence", basic_spy)
    monkeypatch.setattr(
        column_analysis, "collect_numeric_structure_evidence", numeric_spy
    )
    monkeypatch.setattr(column_analysis, "assess_numeric_candidate", assess_spy)
    infer_series_semantics(series)
    assert len(basic_seen) == 1
    assert len(numeric_seen) == 1
    assert numeric_seen[0].basic is basic_seen[0]
    assert assessor_bundles[0][0] is basic_seen[0]
    assert assessor_bundles[0][1]["numeric_structure"] is numeric_seen[0]
    assert assessor_bundles[0][1]["string_structure"] is None
    assert assessor_bundles[0][1]["pattern"] is None


def test_string_evidence_reuses_structure_identity(monkeypatch: pytest.MonkeyPatch):
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    basic_seen = []
    structure_seen = []
    pattern_parents = []
    assessor_bundles = []
    real_basic = column_analysis.collect_basic_column_evidence
    real_structure = column_analysis.collect_string_structure_evidence
    real_pattern = column_analysis.collect_pattern_evidence
    real_assess = column_analysis.assess_identifier_candidate

    def basic_spy(value: pd.Series):
        evidence = real_basic(value)
        basic_seen.append(evidence)
        return evidence

    def structure_spy(value, basic, physical):
        evidence = real_structure(value, basic, physical)
        structure_seen.append(evidence)
        return evidence

    def pattern_spy(value, string_structure, physical):
        pattern_parents.append(string_structure)
        return real_pattern(value, string_structure, physical)

    def assess_spy(basic, physical, **kwargs):
        assessor_bundles.append((basic, kwargs))
        return real_assess(basic, physical, **kwargs)

    monkeypatch.setattr(column_analysis, "collect_basic_column_evidence", basic_spy)
    monkeypatch.setattr(
        column_analysis, "collect_string_structure_evidence", structure_spy
    )
    monkeypatch.setattr(column_analysis, "collect_pattern_evidence", pattern_spy)
    monkeypatch.setattr(column_analysis, "assess_identifier_candidate", assess_spy)
    infer_series_semantics(series)
    assert len(basic_seen) == 1
    assert len(structure_seen) == 1
    assert structure_seen[0].basic is basic_seen[0]
    assert pattern_parents == [structure_seen[0]]
    basic, kwargs = assessor_bundles[0]
    assert basic is basic_seen[0]
    assert kwargs["string_structure"] is structure_seen[0]
    assert kwargs["pattern"] is not None
    assert kwargs["pattern"].string_structure is structure_seen[0]
    assert kwargs["numeric_structure"] is None
    assert "frequency" not in kwargs


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([pd.NA, pd.NA, pd.NA], dtype="string"),
        pd.Series([_UUID_A, _UUID_A], dtype="string"),
        pd.Series([True, False, True]),
        pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01"])),
        pd.Series(pd.to_timedelta(["1 day", "2 days"])),
    ],
)
def test_structural_early_exit_skips_candidate_work(
    series: pd.Series,
    monkeypatch: pytest.MonkeyPatch,
):
    for name in _DOWNSTREAM_COLLECTORS + _ASSESSORS:
        monkeypatch.setattr(column_analysis, name, _forbid_call(name))
    result = infer_series_semantics(series)
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.interpretation is not None


def test_numeric_path_skips_string_collectors(monkeypatch: pytest.MonkeyPatch):
    for name in (
        "collect_string_structure_evidence",
        "collect_pattern_evidence",
    ):
        monkeypatch.setattr(column_analysis, name, _forbid_call(name))
    result = infer_series_semantics(pd.Series([1, 2, 3, 4]))
    assert result.selected_type is SemanticType.NUMERIC


def test_string_path_skips_numeric_collector(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        column_analysis,
        "collect_numeric_structure_evidence",
        _forbid_call("collect_numeric_structure_evidence"),
    )
    result = infer_series_semantics(pd.Series([_UUID_A, _UUID_B], dtype="string"))
    assert result.selected_type is SemanticType.IDENTIFIER


def test_categorical_path_skips_other_family_collectors(
    monkeypatch: pytest.MonkeyPatch,
):
    for name in _DOWNSTREAM_COLLECTORS:
        monkeypatch.setattr(column_analysis, name, _forbid_call(name))
    series = pd.Series(pd.Categorical(["red", "blue", "red"]))
    result = infer_series_semantics(series)
    assert result.selected_type is SemanticType.CATEGORICAL


def test_ordinary_string_does_not_collect_string_content():
    result = infer_series_semantics(
        pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string")
    )
    assert result.resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert not hasattr(column_analysis, "collect_string_content_evidence")


def test_pipeline_delegates_resolution(monkeypatch: pytest.MonkeyPatch):
    original = column_analysis.resolve_semantics
    calls = []

    def spy(*args, **kwargs):
        value = original(*args, **kwargs)
        calls.append((args, kwargs, value))
        return value

    monkeypatch.setattr(column_analysis, "resolve_semantics", spy)
    structural = infer_series_semantics(pd.Series([pd.NA, pd.NA], dtype="string"))
    numeric = infer_series_semantics(pd.Series([1, 2, 3]))
    assert len(calls) == 2
    structural_args, structural_kwargs, structural_resolution = calls[0]
    assert structural_args == ()
    assert structural_kwargs["structural_interpretation"] is structural.interpretation
    assert "candidates" not in structural_kwargs
    assert structural.resolution is structural_resolution
    numeric_args, numeric_kwargs, numeric_resolution = calls[1]
    assert numeric_args == ()
    assert "structural_interpretation" not in numeric_kwargs
    assessed = numeric_kwargs["candidates"]
    assert tuple(item.semantic_type for item in assessed) == _CANDIDATE_TYPES
    assert numeric.resolution is numeric_resolution
    assert not isinstance(numeric_kwargs["candidates"], pd.Series)


def test_pipeline_delegates_inferred_construction(monkeypatch: pytest.MonkeyPatch):
    original = column_analysis.build_inferred_semantic_result
    calls = []

    def spy(physical, resolution):
        value = original(physical, resolution)
        calls.append((physical, resolution, value))
        return value

    monkeypatch.setattr(column_analysis, "build_inferred_semantic_result", spy)
    result = infer_series_semantics(pd.Series([_UUID_A, _UUID_B], dtype=object))
    assert len(calls) == 1
    physical, resolution, built = calls[0]
    assert built is result
    assert result.physical is physical
    assert result.resolution is resolution
    assert not isinstance(physical, pd.Series)
    assert not isinstance(resolution, pd.Series)


def test_assessors_do_not_receive_the_series(monkeypatch: pytest.MonkeyPatch):
    def wrap(name: str):
        original = getattr(column_analysis, name)

        def spy(basic, physical, **kwargs):
            assert not isinstance(basic, pd.Series)
            assert not isinstance(physical, pd.Series)
            for value in kwargs.values():
                assert not isinstance(value, pd.Series)
            return original(basic, physical, **kwargs)

        return spy

    for name in _ASSESSORS:
        monkeypatch.setattr(column_analysis, name, wrap(name))
    numeric = infer_series_semantics(pd.Series([0, 1, 0, 1]))
    identifier = infer_series_semantics(
        pd.Series([_COMPACT_A, _COMPACT_B], dtype="string")
    )
    categorical = infer_series_semantics(pd.Series(pd.Categorical(["a", "b", "a"])))
    assert numeric.selected_type is SemanticType.NUMERIC
    assert identifier.selected_type is SemanticType.IDENTIFIER
    assert categorical.selected_type is SemanticType.CATEGORICAL


@pytest.mark.parametrize(
    "series",
    [
        pd.Series([pd.NA, pd.NA], dtype="string"),
        pd.Series(["same", "same", "same"], dtype="string"),
        pd.Series([_UUID_A, _UUID_A], dtype="string"),
        pd.Series([True, False], dtype="boolean"),
        pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"], utc=True)),
        pd.Series(pd.to_timedelta(["1 day", "3 days"])),
    ],
)
def test_structural_result_matches_precedence_wrapper(series: pd.Series):
    reading = interpret_series_precedence(series)
    result = infer_series_semantics(series)
    assert reading is not None
    assert result.interpretation == reading
    assert result.interpretation is not None
    assert result.interpretation.confidence is reading.confidence
    assert result.interpretation.source is reading.source
    assert result.interpretation.evidence == reading.evidence
    assert result.interpretation.semantic_type is reading.semantic_type


def test_non_series_input_is_rejected():
    with pytest.raises(TypeError, match="pandas Series"):
        infer_series_semantics(pd.DataFrame({"a": [1, 2]}))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="pandas Series"):
        infer_series_semantics([1, 2, 3])  # type: ignore[arg-type]


def test_unhashable_values_propagate():
    series = pd.Series([[1], [2]])
    with pytest.raises(TypeError, match="unhashable"):
        infer_series_semantics(series)


def test_unrelated_string_collector_type_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
):
    def boom(*_args: object, **_kwargs: object) -> None:
        raise TypeError("basic must be BasicColumnEvidence")

    monkeypatch.setattr(column_analysis, "collect_string_structure_evidence", boom)
    with pytest.raises(TypeError, match="BasicColumnEvidence"):
        infer_series_semantics(pd.Series(["a", "b"], dtype="string"))


def test_public_api_is_unchanged():
    assert pytics.__all__ == ["profile", "compare"]
    assert callable(pytics.profile)
    assert callable(pytics.compare)
    assert not hasattr(pytics, "infer_series_semantics")
    semantics_package = inspect.getsource(
        __import__("pytics.semantics", fromlist=["semantics"])
    )
    assert "infer_series_semantics" not in semantics_package


def test_pipeline_does_not_add_semantic_rules():
    source = inspect.getsource(column_analysis)
    wrapper = inspect.getsource(pipeline)
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert "pytics.profiler" not in imported
    assert "pytics.semantics.frequency_evidence" in imported
    assert "pytics.semantics.string_content_evidence" not in imported
    for token in (
        "collect_string_content_evidence",
        "Confidence",
        "InferenceSource",
        "SemanticInterpretation(",
        "supported_count",
        "random",
        "sample(",
        "override",
        "profile(",
        "DataFrame",
    ):
        assert token not in source
        assert token not in wrapper
    assert "collect_frequency_evidence" in source
    assert "collect_frequency_evidence" not in wrapper
    assert "analyze_series" in wrapper
    assert "collect_basic_column_evidence" not in wrapper
