"""TSK-014: semantic resolution without a confidence-bearing candidate reading."""

from __future__ import annotations

import ast
import dataclasses
import inspect
import itertools

import pandas as pd
import pytest

import pytics
import pytics.semantics as semantics_package
import pytics.semantics.empty_constant as empty_constant_module
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
from pytics.semantics.resolution import SemanticResolution
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


def _reading(
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
    dtype_name: str,
    source: InferenceSource,
    statement: str,
    confidence: Confidence = Confidence.HIGH,
) -> SemanticInterpretation:
    return SemanticInterpretation(
        semantic_type=semantic_type,
        confidence=confidence,
        source=source,
        physical=PhysicalDtype(family=family, dtype_name=dtype_name),
        evidence=(_evidence(statement),),
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


def _assert_resolved_type(
    result: SemanticResolution,
    semantic_type: SemanticType,
) -> None:
    assert result.status is ResolutionStatus.RESOLVED
    assert result.selected_type is semantic_type
    assert result.structural_interpretation is None
    assert result.reason == (
        f"Exactly one candidate is supported: {semantic_type.name.title()}."
    )
    assert not isinstance(result, SemanticInterpretation)


def _assert_insufficient(result: SemanticResolution) -> None:
    assert result.status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert result.selected_type is None
    assert result.structural_interpretation is None
    assert result.reason == "No candidate is supported."
    assert not any(
        item.disposition is CandidateDisposition.SUPPORTED for item in result.candidates
    )


def _assert_ambiguous(
    result: SemanticResolution,
    semantic_types: tuple,
) -> None:
    listed = ", ".join(semantic_type.name.title() for semantic_type in semantic_types)
    assert result.status is ResolutionStatus.AMBIGUOUS
    assert result.selected_type is None
    assert result.structural_interpretation is None
    assert result.reason == f"Multiple candidates are supported: {listed}."


def test_resolution_model_is_frozen():
    result = resolve_semantics(candidates=_quad(SemanticType.NUMERIC))
    assert dataclasses.is_dataclass(result)
    assert result.__dataclass_params__.frozen is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.status = ResolutionStatus.AMBIGUOUS  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.candidates = ()  # type: ignore[misc]


def test_candidate_collection_is_an_immutable_tuple():
    items = [
        _unsupported(SemanticType.TEXT),
        _supported(SemanticType.NUMERIC),
        _unsupported(SemanticType.IDENTIFIER),
    ]
    result = resolve_semantics(candidates=items)
    items.append(_supported(SemanticType.CATEGORICAL))
    items[0] = _supported(SemanticType.TEXT)
    assert isinstance(result.candidates, tuple)
    assert result.candidates is not items
    assert [item.semantic_type for item in result.candidates] == [
        SemanticType.IDENTIFIER,
        SemanticType.NUMERIC,
        SemanticType.TEXT,
    ]
    _assert_resolved_type(result, SemanticType.NUMERIC)


def test_valid_resolution_states_keep_their_fields():
    structural = _reading(
        SemanticType.EMPTY,
        PhysicalDtypeFamily.STRING,
        "string",
        InferenceSource.INFERRED,
        "0 non-missing observations out of 2",
    )
    resolved = resolve_semantics(structural)
    insufficient = resolve_semantics(candidates=())
    ambiguous = resolve_semantics(
        candidates=(
            _supported(SemanticType.IDENTIFIER),
            _supported(SemanticType.NUMERIC),
        )
    )
    assert [field.name for field in dataclasses.fields(SemanticResolution)] == [
        "status",
        "reason",
        "candidates",
        "selected_type",
        "structural_interpretation",
    ]
    assert "confidence" not in {
        field.name for field in dataclasses.fields(SemanticResolution)
    }
    assert resolved.status is ResolutionStatus.RESOLVED
    assert resolved.selected_type is SemanticType.EMPTY
    assert resolved.structural_interpretation is structural
    _assert_insufficient(insufficient)
    assert insufficient.candidates == ()
    _assert_ambiguous(ambiguous, (SemanticType.IDENTIFIER, SemanticType.NUMERIC))


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        pytest.param(
            {
                "status": ResolutionStatus.RESOLVED,
                "reason": "missing selection",
            },
            "RESOLVED requires a selected semantic type",
            id="resolved-without-selection",
        ),
        pytest.param(
            {
                "status": ResolutionStatus.RESOLVED,
                "reason": "selection without support",
                "selected_type": SemanticType.NUMERIC,
                "candidates": (_unsupported(SemanticType.NUMERIC),),
            },
            "exactly one supported candidate",
            id="resolved-without-support",
        ),
        pytest.param(
            {
                "status": ResolutionStatus.RESOLVED,
                "reason": "selection among several",
                "selected_type": SemanticType.NUMERIC,
                "candidates": (
                    _supported(SemanticType.NUMERIC),
                    _supported(SemanticType.IDENTIFIER),
                ),
            },
            "exactly one supported candidate",
            id="resolved-with-two-supported",
        ),
        pytest.param(
            {
                "status": ResolutionStatus.INSUFFICIENT_EVIDENCE,
                "reason": "selected anyway",
                "selected_type": SemanticType.TEXT,
            },
            "only a resolved result has a selected semantic type",
            id="insufficient-with-selection",
        ),
        pytest.param(
            {
                "status": ResolutionStatus.INSUFFICIENT_EVIDENCE,
                "reason": "support was present",
                "candidates": (_supported(SemanticType.TEXT),),
            },
            "cannot include a supported candidate",
            id="insufficient-with-support",
        ),
        pytest.param(
            {
                "status": ResolutionStatus.AMBIGUOUS,
                "reason": "selected anyway",
                "selected_type": SemanticType.NUMERIC,
                "candidates": (
                    _supported(SemanticType.NUMERIC),
                    _supported(SemanticType.TEXT),
                ),
            },
            "only a resolved result has a selected semantic type",
            id="ambiguous-with-selection",
        ),
        pytest.param(
            {
                "status": ResolutionStatus.AMBIGUOUS,
                "reason": "only one",
                "candidates": (_supported(SemanticType.NUMERIC),),
            },
            "at least two supported candidates",
            id="ambiguous-with-one",
        ),
        pytest.param(
            {
                "status": ResolutionStatus.AMBIGUOUS,
                "reason": "none",
                "candidates": (),
            },
            "at least two supported candidates",
            id="ambiguous-with-none",
        ),
    ],
)
def test_impossible_resolution_states_are_rejected(kwargs: dict, match: str):
    with pytest.raises(ValueError, match=match):
        SemanticResolution(**kwargs)


def test_invalid_status_and_reason_are_rejected():
    with pytest.raises(TypeError, match="status must be a ResolutionStatus"):
        SemanticResolution(status="resolved", reason="No candidate is supported.")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason must be a non-empty string"):
        SemanticResolution(
            status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
            reason="   ",
        )
    with pytest.raises(TypeError, match="selected_type must be a SemanticType"):
        SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            reason="Exactly one candidate is supported: Numeric.",
            selected_type="numeric",  # type: ignore[arg-type]
            candidates=(_supported(SemanticType.NUMERIC),),
        )


def test_structural_result_rejects_a_selected_type_mismatch():
    reading = _reading(
        SemanticType.CONSTANT,
        PhysicalDtypeFamily.INTEGER,
        "int64",
        InferenceSource.INFERRED,
        "1 distinct non-missing value",
    )
    with pytest.raises(ValueError, match="must match the structural interpretation"):
        SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            reason="Structural interpretation Constant takes precedence.",
            selected_type=SemanticType.EMPTY,
            structural_interpretation=reading,
        )
    with pytest.raises(
        ValueError,
        match="only a resolved result has a structural interpretation",
    ):
        SemanticResolution(
            status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
            reason="No candidate is supported.",
            structural_interpretation=reading,
        )


@pytest.mark.parametrize(
    ("semantic_type", "family", "dtype_name", "source", "statement"),
    [
        (
            SemanticType.EMPTY,
            PhysicalDtypeFamily.STRING,
            "string",
            InferenceSource.INFERRED,
            "0 non-missing observations out of 4",
        ),
        (
            SemanticType.CONSTANT,
            PhysicalDtypeFamily.STRING,
            "string",
            InferenceSource.INFERRED,
            "1 distinct non-missing value among 3 non-missing observations out of 4",
        ),
        (
            SemanticType.BOOLEAN,
            PhysicalDtypeFamily.BOOLEAN,
            "bool",
            InferenceSource.PHYSICAL_DTYPE,
            "physical dtype is boolean",
        ),
        (
            SemanticType.DATETIME,
            PhysicalDtypeFamily.DATETIME,
            "datetime64[ns]",
            InferenceSource.PHYSICAL_DTYPE,
            "physical dtype is datetime",
        ),
        (
            SemanticType.DATETIME,
            PhysicalDtypeFamily.DATETIME_TZ_AWARE,
            "datetime64[ns, UTC]",
            InferenceSource.PHYSICAL_DTYPE,
            "physical dtype is timezone-aware datetime",
        ),
        (
            SemanticType.TIMEDELTA,
            PhysicalDtypeFamily.TIMEDELTA,
            "timedelta64[ns]",
            InferenceSource.PHYSICAL_DTYPE,
            "physical dtype is timedelta",
        ),
    ],
)
def test_structural_readings_resolve_without_candidate_displacement(
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
    dtype_name: str,
    source: InferenceSource,
    statement: str,
):
    reading = _reading(semantic_type, family, dtype_name, source, statement)
    competitors = (
        _supported(SemanticType.IDENTIFIER),
        _supported(SemanticType.NUMERIC),
        _supported(SemanticType.CATEGORICAL),
        _supported(SemanticType.TEXT),
    )
    result = resolve_semantics(reading, candidates=competitors)
    assert result.status is ResolutionStatus.RESOLVED
    assert result.selected_type is semantic_type
    assert result.structural_interpretation is reading
    assert result.structural_interpretation.confidence is Confidence.HIGH
    assert result.structural_interpretation.source is source
    assert result.structural_interpretation.evidence[0].statement == statement
    assert result.structural_interpretation.physical.family is family
    assert result.reason == (
        f"Structural interpretation {semantic_type.name.title()} takes precedence."
    )
    assert result.structural_interpretation.alternatives == ()


def test_structural_confidence_is_preserved_rather_than_reassigned():
    reading = _reading(
        SemanticType.EMPTY,
        PhysicalDtypeFamily.OBJECT,
        "object",
        InferenceSource.INFERRED,
        "0 non-missing observations out of 0",
        confidence=Confidence.LOW,
    )
    result = resolve_semantics(reading, candidates=_quad(SemanticType.TEXT))
    assert result.structural_interpretation is reading
    assert result.structural_interpretation.confidence is Confidence.LOW
    assert result.selected_type is SemanticType.EMPTY


def test_constant_uuid_and_constant_integer_stay_constant():
    constant = _reading(
        SemanticType.CONSTANT,
        PhysicalDtypeFamily.STRING,
        "string",
        InferenceSource.INFERRED,
        "1 distinct non-missing value among 4 non-missing observations out of 4",
    )
    uuid_candidates = (
        _supported(SemanticType.IDENTIFIER),
        _unsupported(SemanticType.NUMERIC),
        _unsupported(SemanticType.CATEGORICAL),
        _unsupported(SemanticType.TEXT),
    )
    integer_candidates = (
        _unsupported(SemanticType.IDENTIFIER),
        _supported(SemanticType.NUMERIC),
        _unsupported(SemanticType.CATEGORICAL),
        _unsupported(SemanticType.TEXT),
    )
    for candidates in (uuid_candidates, integer_candidates):
        result = resolve_semantics(constant, candidates=candidates)
        assert result.status is ResolutionStatus.RESOLVED
        assert result.selected_type is SemanticType.CONSTANT
        assert result.structural_interpretation is constant
        assert result.reason == ("Structural interpretation Constant takes precedence.")


@pytest.mark.parametrize(
    "semantic_type",
    [
        SemanticType.NUMERIC,
        SemanticType.IDENTIFIER,
        SemanticType.CATEGORICAL,
        SemanticType.TEXT,
    ],
)
def test_non_structural_interpretation_cannot_bypass_candidates(
    semantic_type: SemanticType,
):
    reading = _reading(
        semantic_type,
        PhysicalDtypeFamily.INTEGER,
        "int64",
        InferenceSource.INFERRED,
        "not a structural reading",
    )
    with pytest.raises(ValueError, match=f"not {semantic_type.name}"):
        resolve_semantics(reading, candidates=_quad(SemanticType.NUMERIC))
    with pytest.raises(ValueError, match=f"not {semantic_type.name}"):
        SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            reason="Structural interpretation Numeric takes precedence.",
            selected_type=semantic_type,
            structural_interpretation=reading,
        )


@pytest.mark.parametrize("semantic_type", _CANDIDATE_TYPES)
def test_exactly_one_supported_candidate_resolves_that_type(
    semantic_type: SemanticType,
):
    forward = _quad(semantic_type)
    backward = tuple(reversed(forward))
    resolved = resolve_semantics(candidates=forward)
    _assert_resolved_type(resolved, semantic_type)
    assert resolve_semantics(candidates=backward) == resolved
    assert resolved.structural_interpretation is None


def test_text_support_can_be_resolved_from_a_constructed_assessment():
    result = resolve_semantics(
        candidates=(
            _unsupported(SemanticType.IDENTIFIER),
            _unsupported(SemanticType.NUMERIC),
            _unsupported(SemanticType.CATEGORICAL),
            _supported(SemanticType.TEXT),
        )
    )
    _assert_resolved_type(result, SemanticType.TEXT)


@pytest.mark.parametrize(
    ("series", "semantic_type"),
    [
        (pd.Series([1, 2, 3, 4, 5]), SemanticType.NUMERIC),
        (pd.Series([_UUID_A, _UUID_B], dtype="string"), SemanticType.IDENTIFIER),
        (
            pd.Series(pd.Categorical(["red", "blue", "red"])),
            SemanticType.CATEGORICAL,
        ),
    ],
)
def test_current_assessors_resolve_their_single_supported_candidate(
    series: pd.Series,
    semantic_type: SemanticType,
):
    result = resolve_semantics(candidates=_assess_current(series))
    _assert_resolved_type(result, semantic_type)
    supported = [
        item.semantic_type
        for item in result.candidates
        if item.disposition is CandidateDisposition.SUPPORTED
    ]
    assert supported == [semantic_type]


def test_all_unsupported_candidates_are_insufficient():
    result = resolve_semantics(
        candidates=tuple(
            _unsupported(semantic_type) for semantic_type in _CANDIDATE_TYPES
        )
    )
    _assert_insufficient(result)


def test_zero_candidates_are_insufficient():
    assert resolve_semantics() == resolve_semantics(candidates=())
    _assert_insufficient(resolve_semantics())


def test_contradictions_without_support_are_insufficient():
    result = resolve_semantics(
        candidates=(
            _contradicted(SemanticType.NUMERIC),
            _unsupported(SemanticType.TEXT),
            _contradicted(SemanticType.IDENTIFIER),
            _unsupported(SemanticType.CATEGORICAL),
        )
    )
    _assert_insufficient(result)
    assert result.reason == "No candidate is supported."


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
def test_current_string_candidates_are_insufficient(series: pd.Series):
    candidates = _assess_current(series)
    assert {item.disposition for item in candidates} == {
        CandidateDisposition.NOT_SUPPORTED
    }
    result = resolve_semantics(candidates=candidates)
    _assert_insufficient(result)
    assert result.selected_type is None


@pytest.mark.parametrize(
    "supported",
    [
        (SemanticType.NUMERIC, SemanticType.IDENTIFIER),
        (SemanticType.CATEGORICAL, SemanticType.TEXT),
        (SemanticType.IDENTIFIER, SemanticType.TEXT),
    ],
)
def test_multiple_supported_candidates_stay_ambiguous(supported: tuple):
    candidates = tuple(
        (
            _supported(semantic_type)
            if semantic_type in supported
            else _unsupported(semantic_type)
        )
        for semantic_type in _CANDIDATE_TYPES
    )
    expected = tuple(sorted(supported, key=lambda semantic_type: semantic_type.name))
    result = resolve_semantics(candidates=tuple(reversed(candidates)))
    _assert_ambiguous(result, expected)
    assert resolve_semantics(candidates=candidates) == result


def test_more_supporting_statements_do_not_select_a_candidate():
    result = resolve_semantics(
        candidates=(
            _supported(
                SemanticType.NUMERIC,
                ("one structural fact", "another structural fact", "a third fact"),
            ),
            _supported(SemanticType.IDENTIFIER, ("one syntax fact",)),
            _unsupported(SemanticType.CATEGORICAL),
            _unsupported(SemanticType.TEXT),
        )
    )
    _assert_ambiguous(result, (SemanticType.IDENTIFIER, SemanticType.NUMERIC))


def test_one_supported_candidate_survives_a_different_contradiction():
    result = resolve_semantics(
        candidates=(
            _supported(SemanticType.NUMERIC),
            _contradicted(SemanticType.TEXT),
            _unsupported(SemanticType.IDENTIFIER),
            _unsupported(SemanticType.CATEGORICAL),
        )
    )
    _assert_resolved_type(result, SemanticType.NUMERIC)


def test_a_contradicted_candidate_is_not_a_fallback():
    result = resolve_semantics(
        candidates=(
            _contradicted(SemanticType.NUMERIC),
            _unsupported(SemanticType.TEXT),
        )
    )
    _assert_insufficient(result)


@pytest.mark.parametrize(
    "order",
    list(itertools.permutations(range(4))),
    ids=lambda order: "-".join(str(index) for index in order),
)
def test_ambiguous_result_is_the_same_for_every_input_order(order: tuple):
    base = (
        _supported(SemanticType.IDENTIFIER),
        _supported(SemanticType.NUMERIC),
        _unsupported(SemanticType.CATEGORICAL),
        _unsupported(SemanticType.TEXT),
    )
    result = resolve_semantics(candidates=tuple(base[index] for index in order))
    assert result == resolve_semantics(candidates=base)
    _assert_ambiguous(result, (SemanticType.IDENTIFIER, SemanticType.NUMERIC))


@pytest.mark.parametrize(
    "order",
    list(itertools.permutations(range(4))),
    ids=lambda order: "-".join(str(index) for index in order),
)
def test_single_support_is_the_same_for_every_input_order(order: tuple):
    base = _quad(SemanticType.NUMERIC)
    result = resolve_semantics(candidates=tuple(base[index] for index in order))
    assert result == resolve_semantics(candidates=base)
    _assert_resolved_type(result, SemanticType.NUMERIC)


def test_duplicate_candidate_types_are_rejected():
    duplicated = (
        _supported(SemanticType.NUMERIC),
        _unsupported(SemanticType.NUMERIC),
    )
    identical = (_supported(SemanticType.TEXT), _supported(SemanticType.TEXT))
    for candidates in (duplicated, identical, tuple(reversed(duplicated))):
        with pytest.raises(
            ValueError,
            match="duplicate candidate semantic type: ",
        ):
            resolve_semantics(candidates=candidates)
    with pytest.raises(ValueError, match="duplicate candidate semantic type: NUMERIC"):
        SemanticResolution(
            status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
            reason="No candidate is supported.",
            candidates=duplicated,
        )


@pytest.mark.parametrize(
    "candidates",
    [
        "numeric",
        None,
        _supported(SemanticType.NUMERIC),
        {"semantic_type": SemanticType.NUMERIC},
        (_supported(SemanticType.NUMERIC), "not an assessment"),
    ],
)
def test_candidate_input_must_be_a_sequence_of_assessments(candidates: object):
    with pytest.raises(TypeError, match="candidates must"):
        resolve_semantics(candidates=candidates)  # type: ignore[arg-type]


def test_structural_input_must_be_an_interpretation():
    with pytest.raises(TypeError, match="structural_interpretation must"):
        resolve_semantics(structural_interpretation=SemanticType.BOOLEAN)  # type: ignore[arg-type]


def test_resolution_does_not_recollect_evidence(monkeypatch: pytest.MonkeyPatch):
    prepared = _quad(SemanticType.CATEGORICAL)
    structural = _reading(
        SemanticType.BOOLEAN,
        PhysicalDtypeFamily.BOOLEAN,
        "bool",
        InferenceSource.PHYSICAL_DTYPE,
        "physical dtype is boolean",
    )

    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("resolution recollected evidence")

    for target in (
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
    ):
        monkeypatch.setattr(target, _forbidden)
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
        "pd",
        "pandas",
    ):
        assert not hasattr(resolution_module, name)

    _assert_resolved_type(
        resolve_semantics(candidates=prepared),
        SemanticType.CATEGORICAL,
    )
    structural_result = resolve_semantics(
        structural,
        candidates=(
            _supported(SemanticType.NUMERIC),
            _supported(SemanticType.IDENTIFIER),
        ),
    )
    assert structural_result.structural_interpretation is structural
    assert structural_result.selected_type is SemanticType.BOOLEAN


def test_resolution_module_does_not_import_pandas_or_collectors():
    source = inspect.getsource(resolution_module)
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
        "enum",
        "typing",
        "typing",
        "typing",
        "typing",
        "pytics.semantics.candidate",
        "pytics.semantics.candidate",
        "pytics.semantics.interpretation",
        "pytics.semantics.interpretation",
    ]
    for token in (
        "pandas",
        "collect_",
        "assess_",
        "score",
        "weight",
        "rank",
        "priority",
        "points",
        "probability",
        "threshold",
        "DataFrame",
        "Series",
        "override",
        "UNKNOWN",
        "winner",
    ):
        assert token not in source


def test_precedence_chain_does_not_call_resolution(monkeypatch: pytest.MonkeyPatch):
    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("precedence called the resolver")

    monkeypatch.setattr(resolution_module, "resolve_semantics", _forbidden)
    for module in _PRECEDENCE_MODULES:
        source = inspect.getsource(module)
        assert "resolve_semantics" not in source
        assert "resolution" not in source
        assert not hasattr(module, "resolve_semantics")

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


def test_resolution_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "resolve_semantics")
    assert not hasattr(pytics, "SemanticResolution")
    assert not hasattr(pytics, "ResolutionStatus")
    assert not hasattr(semantics_package, "resolve_semantics")
    assert not hasattr(semantics_package, "SemanticResolution")
