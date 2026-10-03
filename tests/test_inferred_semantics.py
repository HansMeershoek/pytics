"""TSK-015: inferred semantic state after resolution, without invented confidence."""

from __future__ import annotations

import ast
import dataclasses
import inspect

import pandas as pd
import pytest

import pytics
import pytics.semantics as semantics_package
import pytics.semantics.empty_constant as empty_constant_module
import pytics.semantics.inferred as inferred_module
import pytics.semantics.physical_boolean as physical_boolean_module
import pytics.semantics.physical_datetime as physical_datetime_module
import pytics.semantics.physical_timedelta as physical_timedelta_module
import pytics.semantics.resolution as resolution_module
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.core_candidates import assess_categorical_candidate
from pytics.semantics.core_candidates import assess_numeric_candidate
from pytics.semantics.core_candidates import assess_text_candidate
from pytics.semantics.frequency_evidence import collect_frequency_evidence
from pytics.semantics.identifier_candidate import assess_identifier_candidate
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.inferred import build_inferred_semantic_result
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
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
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.resolution import resolve_semantics
from pytics.semantics.string_structure_evidence import collect_string_structure_evidence

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_CANDIDATE_TYPES = (
    SemanticType.IDENTIFIER,
    SemanticType.NUMERIC,
    SemanticType.CATEGORICAL,
    SemanticType.TEXT,
)
_PRECEDENCE_MODULES = (
    empty_constant_module,
    physical_boolean_module,
    physical_datetime_module,
    physical_timedelta_module,
)
_PIPELINE_TARGETS = (
    "pytics.semantics.column_evidence.collect_basic_column_evidence",
    "pytics.semantics.frequency_evidence.collect_frequency_evidence",
    "pytics.semantics.numeric_structure_evidence.collect_numeric_structure_evidence",
    "pytics.semantics.string_structure_evidence.collect_string_structure_evidence",
    "pytics.semantics.pattern_evidence.collect_pattern_evidence",
    "pytics.semantics.string_content_evidence.collect_string_content_evidence",
    "pytics.semantics.physical.classify_physical_dtype",
    "pytics.semantics.identifier_candidate.assess_identifier_candidate",
    "pytics.semantics.core_candidates.assess_numeric_candidate",
    "pytics.semantics.core_candidates.assess_categorical_candidate",
    "pytics.semantics.core_candidates.assess_text_candidate",
)


def _evidence(statement: str) -> SemanticEvidence:
    return SemanticEvidence(statement)


def _supported(
    semantic_type: SemanticType,
    statements: tuple = ("constructed support",),
) -> CandidateAssessment:
    return CandidateAssessment(
        semantic_type=semantic_type,
        disposition=CandidateDisposition.SUPPORTED,
        supporting_evidence=tuple(_evidence(statement) for statement in statements),
    )


def _unsupported(semantic_type: SemanticType) -> CandidateAssessment:
    return CandidateAssessment(
        semantic_type=semantic_type,
        disposition=CandidateDisposition.NOT_SUPPORTED,
    )


def _contradicted(semantic_type: SemanticType) -> CandidateAssessment:
    return CandidateAssessment(
        semantic_type=semantic_type,
        disposition=CandidateDisposition.CONTRADICTED,
        contradicting_evidence=(_evidence("constructed contradiction"),),
    )


def _quad(supported: SemanticType) -> tuple:
    return tuple(
        (
            _supported(semantic_type)
            if semantic_type is supported
            else _unsupported(semantic_type)
        )
        for semantic_type in _CANDIDATE_TYPES
    )


def _assess_current(series: pd.Series) -> tuple:
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
    arguments = {
        "frequency": frequency,
        "numeric_structure": numeric,
        "string_structure": structure,
        "pattern": pattern,
    }
    return tuple(
        assessor(basic, physical, **arguments)
        for assessor in (
            assess_identifier_candidate,
            assess_numeric_candidate,
            assess_categorical_candidate,
            assess_text_candidate,
        )
    )


def _physical(
    family: PhysicalDtypeFamily,
    dtype_name: str,
    categorical_ordered: bool | None = None,
) -> PhysicalDtype:
    return PhysicalDtype(
        family=family,
        dtype_name=dtype_name,
        categorical_ordered=categorical_ordered,
    )


def test_inferred_result_stores_only_physical_dtype_and_resolution():
    physical = _physical(PhysicalDtypeFamily.INTEGER, "int64")
    resolution = resolve_semantics(candidates=_quad(SemanticType.NUMERIC))
    result = build_inferred_semantic_result(physical, resolution)
    assert dataclasses.is_dataclass(result)
    assert result.__dataclass_params__.frozen is True
    assert [field.name for field in dataclasses.fields(result)] == [
        "physical",
        "resolution",
    ]
    assert result.physical is physical
    assert result.resolution is resolution
    assert result.selected_type is resolution.selected_type
    assert result.interpretation is resolution.structural_interpretation
    assert result.selected_type is SemanticType.NUMERIC
    assert result.interpretation is None
    again = build_inferred_semantic_result(physical, resolution)
    assert again == result
    assert again.selected_type is result.selected_type
    assert again.interpretation is result.interpretation
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.physical = physical  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.resolution = resolution  # type: ignore[misc]
    with pytest.raises(TypeError):
        InferredSemanticResult(
            physical=physical,
            resolution=resolution,
            interpretation=None,  # type: ignore[call-arg]
        )


@pytest.mark.parametrize(
    ("series", "semantic_type", "source"),
    [
        (
            pd.Series([pd.NA, pd.NA], dtype="string"),
            SemanticType.EMPTY,
            InferenceSource.INFERRED,
        ),
        (
            pd.Series(["apple", "apple"], dtype="string"),
            SemanticType.CONSTANT,
            InferenceSource.INFERRED,
        ),
        (
            pd.Series([True, False, True]),
            SemanticType.BOOLEAN,
            InferenceSource.PHYSICAL_DTYPE,
        ),
        (
            pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"])),
            SemanticType.DATETIME,
            InferenceSource.PHYSICAL_DTYPE,
        ),
        (
            pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"], utc=True)),
            SemanticType.DATETIME,
            InferenceSource.PHYSICAL_DTYPE,
        ),
        (
            pd.Series(pd.to_timedelta(["1 day", "2 days"])),
            SemanticType.TIMEDELTA,
            InferenceSource.PHYSICAL_DTYPE,
        ),
    ],
)
def test_structural_result_preserves_the_existing_interpretation(
    series: pd.Series,
    semantic_type: SemanticType,
    source: InferenceSource,
):
    reading = interpret_series_precedence(series)
    assert reading is not None
    assert reading.semantic_type is semantic_type
    assert reading.confidence is Confidence.HIGH
    assert reading.source is source
    physical = classify_physical_dtype(series)
    assert physical == reading.physical
    resolution = resolve_semantics(
        reading,
        candidates=(
            _supported(SemanticType.NUMERIC),
            _supported(SemanticType.IDENTIFIER),
        ),
    )
    result = build_inferred_semantic_result(physical, resolution)
    assert result.resolution is resolution
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.physical is physical
    assert result.physical == reading.physical
    assert result.interpretation is reading
    assert result.interpretation.physical is reading.physical
    assert result.interpretation.confidence is Confidence.HIGH
    assert result.interpretation.source is source
    assert result.selected_type is semantic_type
    if semantic_type is SemanticType.DATETIME:
        assert result.physical.family in (
            PhysicalDtypeFamily.DATETIME,
            PhysicalDtypeFamily.DATETIME_TZ_AWARE,
        )


def test_structural_confidence_is_not_rewritten():
    physical = _physical(PhysicalDtypeFamily.BOOLEAN, "bool")
    reading = SemanticInterpretation(
        semantic_type=SemanticType.BOOLEAN,
        confidence=Confidence.MEDIUM,
        source=InferenceSource.PHYSICAL_DTYPE,
        physical=physical,
        evidence=(_evidence("physical dtype is boolean"),),
    )
    resolution = resolve_semantics(reading)
    result = build_inferred_semantic_result(physical, resolution)
    assert result.interpretation is reading
    assert result.interpretation.confidence is Confidence.MEDIUM
    assert result.interpretation.source is InferenceSource.PHYSICAL_DTYPE


def test_equal_physical_dtype_matches_without_replacing_the_interpretation():
    series = pd.Series([pd.NA, pd.NA], dtype="string")
    reading = interpret_series_precedence(series)
    assert reading is not None
    physical = _physical(
        reading.physical.family,
        reading.physical.dtype_name,
        reading.physical.categorical_ordered,
    )
    assert physical == reading.physical
    assert physical is not reading.physical
    resolution = resolve_semantics(reading)
    result = build_inferred_semantic_result(physical, resolution)
    assert result.physical is physical
    assert result.interpretation is reading
    assert result.interpretation.physical is reading.physical


@pytest.mark.parametrize(
    ("series", "other"),
    [
        (
            pd.Series([True, False, True]),
            _physical(PhysicalDtypeFamily.INTEGER, "int64"),
        ),
        (
            pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"])),
            _physical(PhysicalDtypeFamily.TIMEDELTA, "timedelta64[ns]"),
        ),
        (
            pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"])),
            _physical(PhysicalDtypeFamily.DATETIME, "datetime64[ns]"),
        ),
    ],
)
def test_structural_physical_dtype_mismatch_is_rejected(
    series: pd.Series,
    other: PhysicalDtype,
):
    reading = interpret_series_precedence(series)
    assert reading is not None
    assert other != reading.physical
    resolution = resolve_semantics(reading)
    with pytest.raises(ValueError, match="physical dtype must match"):
        build_inferred_semantic_result(other, resolution)
    assert reading.physical == classify_physical_dtype(series)
    assert reading.confidence is Confidence.HIGH


def test_categorical_ordered_flag_mismatch_is_rejected():
    series = pd.Series(pd.Categorical(["red", "red"], ordered=True))
    reading = interpret_series_precedence(series)
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT
    assert reading.physical.categorical_ordered is True
    other = _physical(
        PhysicalDtypeFamily.CATEGORICAL,
        reading.physical.dtype_name,
        categorical_ordered=False,
    )
    resolution = resolve_semantics(reading)
    with pytest.raises(ValueError, match="categorical_ordered=False"):
        build_inferred_semantic_result(other, resolution)
    assert reading.physical.categorical_ordered is True


@pytest.mark.parametrize(
    ("series", "semantic_type", "family"),
    [
        (pd.Series([1, 2, 3, 4, 5]), SemanticType.NUMERIC, PhysicalDtypeFamily.INTEGER),
        (
            pd.Series([1.5, 2.5, 3.5]),
            SemanticType.NUMERIC,
            PhysicalDtypeFamily.FLOATING,
        ),
        (
            pd.Series([_UUID_A, _UUID_B], dtype="string"),
            SemanticType.IDENTIFIER,
            PhysicalDtypeFamily.STRING,
        ),
        (
            pd.Series([_UUID_A, _UUID_B], dtype=object),
            SemanticType.IDENTIFIER,
            PhysicalDtypeFamily.OBJECT,
        ),
    ],
)
def test_candidate_derived_results_keep_observed_storage_without_confidence(
    series: pd.Series,
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
):
    physical = classify_physical_dtype(series)
    assert physical.family is family
    resolution = resolve_semantics(candidates=_assess_current(series))
    result = build_inferred_semantic_result(physical, resolution)
    assert result.resolution is resolution
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.selected_type is semantic_type
    assert result.physical is physical
    assert result.physical.family is family
    assert result.interpretation is None
    assert not isinstance(result, SemanticInterpretation)


@pytest.mark.parametrize("ordered", [False, True])
def test_categorical_resolution_keeps_observed_categorical_storage(ordered: bool):
    series = pd.Series(pd.Categorical(["red", "blue", "red"], ordered=ordered))
    physical = classify_physical_dtype(series)
    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert physical.categorical_ordered is ordered
    resolution = resolve_semantics(candidates=_assess_current(series))
    result = build_inferred_semantic_result(physical, resolution)
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.selected_type is SemanticType.CATEGORICAL
    assert result.physical is physical
    assert result.physical.categorical_ordered is ordered
    assert result.interpretation is None


@pytest.mark.parametrize(
    "series",
    [
        pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string"),
        pd.Series(
            [
                "This is a long sentence about the city and its river.",
                "Another sentence follows with several ordinary words.",
            ],
            dtype="string",
        ),
    ],
)
def test_insufficient_evidence_is_a_complete_inferred_result(series: pd.Series):
    physical = classify_physical_dtype(series)
    resolution = resolve_semantics(candidates=_assess_current(series))
    assert resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    result = build_inferred_semantic_result(physical, resolution)
    assert isinstance(result, InferredSemanticResult)
    assert result.physical is physical
    assert result.physical.family is PhysicalDtypeFamily.STRING
    assert result.resolution is resolution
    assert result.resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert result.interpretation is None
    assert result.selected_type is None


def test_ambiguity_keeps_both_candidates_and_assigns_no_confidence():
    physical = _physical(PhysicalDtypeFamily.INTEGER, "int64")
    resolution = resolve_semantics(
        candidates=(
            _supported(SemanticType.IDENTIFIER),
            _supported(SemanticType.NUMERIC),
            _unsupported(SemanticType.CATEGORICAL),
            _unsupported(SemanticType.TEXT),
        )
    )
    result = build_inferred_semantic_result(physical, resolution)
    supported = tuple(
        item.semantic_type
        for item in result.resolution.candidates
        if item.disposition is CandidateDisposition.SUPPORTED
    )
    assert result.physical is physical
    assert result.resolution is resolution
    assert result.resolution.status is ResolutionStatus.AMBIGUOUS
    assert result.interpretation is None
    assert result.selected_type is None
    assert supported == (SemanticType.IDENTIFIER, SemanticType.NUMERIC)
    assert result.resolution.structural_interpretation is None


@pytest.mark.parametrize(
    ("semantic_type", "family", "dtype_name", "ordered"),
    [
        (SemanticType.NUMERIC, PhysicalDtypeFamily.STRING, "string", None),
        (SemanticType.IDENTIFIER, PhysicalDtypeFamily.INTEGER, "int64", None),
        (SemanticType.CATEGORICAL, PhysicalDtypeFamily.FLOATING, "float64", None),
        (SemanticType.TEXT, PhysicalDtypeFamily.BOOLEAN, "bool", None),
        (SemanticType.TEXT, PhysicalDtypeFamily.CATEGORICAL, "category", False),
    ],
)
def test_supplied_physical_dtype_is_preserved_for_any_selected_type(
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
    dtype_name: str,
    ordered: bool | None,
):
    physical = _physical(family, dtype_name, ordered)
    resolution = resolve_semantics(candidates=_quad(semantic_type))
    result = build_inferred_semantic_result(physical, resolution)
    assert result.physical is physical
    assert result.physical.family is family
    assert result.physical.dtype_name == dtype_name
    assert result.physical.categorical_ordered is ordered
    assert result.selected_type is semantic_type
    assert result.interpretation is None
    assert result.resolution.status is ResolutionStatus.RESOLVED


@pytest.mark.parametrize(
    "statements",
    [
        ("constructed support",),
        ("first constructed support", "second constructed support"),
    ],
)
def test_support_quantity_does_not_create_an_interpretation(statements: tuple):
    resolution = resolve_semantics(
        candidates=(
            _supported(SemanticType.NUMERIC, statements),
            _unsupported(SemanticType.IDENTIFIER),
            _unsupported(SemanticType.CATEGORICAL),
            _unsupported(SemanticType.TEXT),
        )
    )
    result = build_inferred_semantic_result(
        _physical(PhysicalDtypeFamily.INTEGER, "int64"),
        resolution,
    )
    numeric = next(
        item
        for item in result.resolution.candidates
        if item.semantic_type is SemanticType.NUMERIC
    )
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.selected_type is SemanticType.NUMERIC
    assert len(numeric.supporting_evidence) == len(statements)
    assert result.interpretation is None


def test_missing_contradiction_does_not_create_an_interpretation():
    resolution = resolve_semantics(candidates=_quad(SemanticType.CATEGORICAL))
    result = build_inferred_semantic_result(
        _physical(
            PhysicalDtypeFamily.CATEGORICAL, "category", categorical_ordered=False
        ),
        resolution,
    )
    assert result.selected_type is SemanticType.CATEGORICAL
    assert result.interpretation is None
    assert all(
        item.disposition is not CandidateDisposition.CONTRADICTED
        for item in result.resolution.candidates
    )


def test_a_contradicted_neighbor_does_not_create_an_interpretation():
    resolution = resolve_semantics(
        candidates=(
            _supported(SemanticType.NUMERIC),
            _contradicted(SemanticType.IDENTIFIER),
            _unsupported(SemanticType.CATEGORICAL),
            _unsupported(SemanticType.TEXT),
        )
    )
    result = build_inferred_semantic_result(
        _physical(PhysicalDtypeFamily.INTEGER, "int64"),
        resolution,
    )
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.selected_type is SemanticType.NUMERIC
    assert result.interpretation is None


@pytest.mark.parametrize(
    "physical",
    ["int64", None, SemanticType.NUMERIC, pd.Series([1, 2, 3])],
)
def test_physical_argument_must_be_a_physical_dtype(physical: object):
    resolution = resolve_semantics(candidates=_quad(SemanticType.NUMERIC))
    with pytest.raises(TypeError, match="physical must be a PhysicalDtype"):
        build_inferred_semantic_result(physical, resolution)  # type: ignore[arg-type]


def test_resolution_argument_must_be_a_resolution():
    physical = _physical(PhysicalDtypeFamily.INTEGER, "int64")
    with pytest.raises(TypeError, match="resolution must be a SemanticResolution"):
        build_inferred_semantic_result(physical, physical)  # type: ignore[arg-type]


def test_construction_does_not_recollect_or_reresolve(
    monkeypatch: pytest.MonkeyPatch,
):
    physical = _physical(PhysicalDtypeFamily.STRING, "string")
    resolution = resolve_semantics(candidates=_quad(SemanticType.TEXT))

    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("inferred construction reran the pipeline")

    for target in _PIPELINE_TARGETS:
        monkeypatch.setattr(target, _forbidden)
    monkeypatch.setattr(resolution_module, "resolve_semantics", _forbidden)
    for name in (
        "collect_basic_column_evidence",
        "collect_frequency_evidence",
        "collect_numeric_structure_evidence",
        "collect_string_structure_evidence",
        "collect_pattern_evidence",
        "collect_string_content_evidence",
        "classify_physical_dtype",
        "assess_identifier_candidate",
        "assess_numeric_candidate",
        "assess_categorical_candidate",
        "assess_text_candidate",
        "resolve_semantics",
        "pd",
        "pandas",
    ):
        assert not hasattr(inferred_module, name)

    result = build_inferred_semantic_result(physical, resolution)
    assert result.physical is physical
    assert result.resolution is resolution
    assert result.selected_type is SemanticType.TEXT
    assert result.interpretation is None


def test_inferred_module_does_not_import_pipeline_or_confidence_policy():
    source = inspect.getsource(inferred_module)
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert imported == [
        "__future__",
        "dataclasses",
        "typing",
        "typing",
        "pytics.semantics.interpretation",
        "pytics.semantics.interpretation",
        "pytics.semantics.physical",
        "pytics.semantics.resolution",
    ]
    for token in (
        "pandas",
        "PhysicalDtypeFamily",
        "Confidence",
        "InferenceSource",
        "SemanticAlternative",
        "EvidenceStrength",
        "collect_",
        "assess_",
        "resolve_semantics",
        "Series",
        "DataFrame",
        "override",
        "eligibility",
        "UNKNOWN",
    ):
        assert token not in source


def test_precedence_chain_does_not_build_an_inferred_result(
    monkeypatch: pytest.MonkeyPatch,
):
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("precedence built an inferred result")

    monkeypatch.setattr(inferred_module, "build_inferred_semantic_result", _forbidden)
    monkeypatch.setattr(inferred_module, "InferredSemanticResult", _forbidden)
    for module in _PRECEDENCE_MODULES:
        source = inspect.getsource(module)
        assert "build_inferred_semantic_result" not in source
        assert "InferredSemanticResult" not in source
        assert "semantics.inferred" not in source
    resolution_source = inspect.getsource(resolution_module)
    assert "build_inferred_semantic_result" not in resolution_source
    assert "InferredSemanticResult" not in resolution_source

    empty = interpret_series_precedence(pd.Series([pd.NA, pd.NA], dtype="string"))
    constant = interpret_series_precedence(
        pd.Series(["apple", "apple"], dtype="string")
    )
    boolean = interpret_series_precedence(pd.Series([True, False, True]))
    native = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"]))
    )
    aware = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01"], utc=True))
    )
    duration = interpret_series_precedence(
        pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    )
    numeric = interpret_series_precedence(pd.Series([1, 2, 3, 4, 5]))
    cities = interpret_series_precedence(
        pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string")
    )
    uuids = interpret_series_precedence(pd.Series([_UUID_A, _UUID_B], dtype="string"))

    assert empty is not None and empty.semantic_type is SemanticType.EMPTY
    assert constant is not None and constant.semantic_type is SemanticType.CONSTANT
    assert boolean is not None and boolean.semantic_type is SemanticType.BOOLEAN
    assert native is not None and native.semantic_type is SemanticType.DATETIME
    assert aware is not None and aware.physical.family is (
        PhysicalDtypeFamily.DATETIME_TZ_AWARE
    )
    assert duration is not None and duration.semantic_type is SemanticType.TIMEDELTA
    assert numeric is None
    assert cities is None
    assert uuids is None


def test_inferred_result_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "build_inferred_semantic_result")
    assert not hasattr(pytics, "InferredSemanticResult")
    assert not hasattr(semantics_package, "build_inferred_semantic_result")
    assert not hasattr(semantics_package, "InferredSemanticResult")
