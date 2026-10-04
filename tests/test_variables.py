"""TSK-019: variables summary aggregated from dataset analysis."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.boolean as boolean_descriptive
import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.numeric as numeric_descriptive
import pytics.analysis.variables as variables_module
import pytics.semantics.column_evidence as basic_evidence
import pytics.semantics.core_candidates as core_candidates
import pytics.semantics.frequency_evidence as frequency_evidence
import pytics.semantics.identifier_candidate as identifier_candidate
import pytics.semantics.numeric_structure_evidence as numeric_evidence
import pytics.semantics.pattern_evidence as pattern_evidence
import pytics.semantics.physical as physical
import pytics.semantics.pipeline as pipeline
import pytics.semantics.resolution as resolution_module
import pytics.semantics.string_content_evidence as string_content_evidence
import pytics.semantics.string_structure_evidence as string_evidence
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import ColumnEvidence
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.duplicate import DuplicateAnalysis
from tests.missing_margins import missing_analysis_for_margins
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.variables import BooleanVariableDetail
from pytics.analysis.variables import CategoricalVariableDetail
from pytics.analysis.variables import IdentifierVariableDetail
from pytics.analysis.variables import NumericVariableDetail
from pytics.analysis.variables import VariableSummary
from pytics.analysis.variables import VariablesSummary
from pytics.analysis.variables import build_variables_summary
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.resolution import SemanticResolution

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_UUID_C = "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
_COMPACT_A = "550e8400e29b41d4a716446655440000"
_COMPACT_B = "6ba7b8109dad11d180b400c04fd430c8"
_FORBIDDEN_TYPES = (
    pd.DataFrame,
    pd.Series,
    np.ndarray,
    np.generic,
    DatasetAnalysis,
    ColumnAnalysis,
)


def _summary(frame: pd.DataFrame) -> VariablesSummary:
    return build_variables_summary(analyze_dataframe(frame))


def _assert_invariants(
    summary: VariablesSummary,
    analysis: DatasetAnalysis | None = None,
) -> None:
    assert summary.n_variables == len(summary.variables)
    assert isinstance(summary.variables, tuple)
    if analysis is not None:
        assert summary.n_variables == analysis.n_columns
    assert [item.position for item in summary.variables] == list(
        range(summary.n_variables)
    )
    totals = {item.n_total for item in summary.variables}
    assert len(totals) <= 1
    for variable in summary.variables:
        assert variable.n_missing + variable.n_non_missing == variable.n_total
        assert variable.n_unique_non_missing <= variable.n_non_missing
        assert "confidence" not in variable.__dataclass_fields__
        assert "source" not in variable.__dataclass_fields__
        if variable.n_total == 0:
            assert variable.missing_ratio is None
        else:
            assert variable.missing_ratio == pytest.approx(
                variable.n_missing / variable.n_total
            )
            assert 0.0 <= variable.missing_ratio <= 1.0
        if variable.n_non_missing == 0:
            assert variable.unique_ratio_non_missing is None
        else:
            assert variable.unique_ratio_non_missing == pytest.approx(
                variable.n_unique_non_missing / variable.n_non_missing
            )
        if variable.resolution_status is ResolutionStatus.RESOLVED:
            assert isinstance(variable.selected_type, SemanticType)
        else:
            assert variable.selected_type is None
            assert variable.detail is None
        _assert_detail_matches(variable)


def _assert_detail_matches(variable: VariableSummary) -> None:
    detail = variable.detail
    if variable.selected_type is SemanticType.NUMERIC:
        assert detail is None or isinstance(detail, NumericVariableDetail)
    elif variable.selected_type is SemanticType.CATEGORICAL:
        assert detail is None or isinstance(detail, CategoricalVariableDetail)
    elif variable.selected_type is SemanticType.IDENTIFIER:
        assert detail is None or isinstance(detail, IdentifierVariableDetail)
    elif variable.selected_type is SemanticType.BOOLEAN:
        assert detail is None or isinstance(detail, BooleanVariableDetail)
    else:
        assert detail is None


def _assert_no_source(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return
    seen.add(identity)
    assert not isinstance(value, _FORBIDDEN_TYPES)
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_no_source(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_source(item, seen)


def _supported(semantic_type: SemanticType) -> CandidateAssessment:
    return CandidateAssessment(
        semantic_type=semantic_type,
        disposition=CandidateDisposition.SUPPORTED,
        supporting_evidence=(SemanticEvidence(statement="synthetic support"),),
    )


def _candidate_resolution(semantic_type: SemanticType) -> SemanticResolution:
    return SemanticResolution(
        status=ResolutionStatus.RESOLVED,
        reason=f"Exactly one candidate is supported: {semantic_type.name.title()}.",
        candidates=(_supported(semantic_type),),
        selected_type=semantic_type,
    )


def _with_resolution(
    column: ColumnAnalysis,
    resolution: SemanticResolution,
) -> ColumnAnalysis:
    return ColumnAnalysis(
        position=column.position,
        label=column.label,
        physical=column.physical,
        evidence=column.evidence,
        inferred=InferredSemanticResult(
            physical=column.physical,
            resolution=resolution,
        ),
    )


def _analysis_of(column: ColumnAnalysis) -> DatasetAnalysis:
    n_rows = column.evidence.basic.n_total
    return DatasetAnalysis(
        n_rows=n_rows,
        n_columns=1,
        n_cells=n_rows,
        columns=(column,),
        missing_analysis=missing_analysis_for_margins(
            n_rows,
            (column.evidence.basic.n_missing,),
        ),
        duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
    )


def _hex_token(width: int, last: str) -> str:
    token = ("0123456789abcdef" * ((width // 16) + 1))[:width]
    return token[:-1] + last


def _numeric_detail(
    *,
    n_non_missing: int = 3,
    finite_count: int = 3,
    positive_count: int = 3,
    negative_count: int = 0,
    zero_count: int = 0,
    positive_infinity_count: int = 0,
    negative_infinity_count: int = 0,
    integer_like_count: int = 3,
    non_integer_like_count: int = 0,
    is_non_decreasing: bool | None = True,
    is_non_increasing: bool | None = False,
) -> NumericVariableDetail:
    return NumericVariableDetail(
        n_non_missing=n_non_missing,
        finite_count=finite_count,
        positive_count=positive_count,
        negative_count=negative_count,
        zero_count=zero_count,
        positive_infinity_count=positive_infinity_count,
        negative_infinity_count=negative_infinity_count,
        integer_like_count=integer_like_count,
        non_integer_like_count=non_integer_like_count,
        is_non_decreasing=is_non_decreasing,
        is_non_increasing=is_non_increasing,
    )


def _variable(**overrides: object) -> VariableSummary:
    values: dict[str, object] = {
        "position": 0,
        "label": "amount",
        "physical": PhysicalDtype(
            family=PhysicalDtypeFamily.INTEGER,
            dtype_name="int64",
        ),
        "resolution_status": ResolutionStatus.RESOLVED,
        "selected_type": SemanticType.NUMERIC,
        "n_total": 3,
        "n_missing": 0,
        "n_non_missing": 3,
        "n_unique_non_missing": 3,
        "detail": _numeric_detail(),
    }
    values.update(overrides)
    return VariableSummary(**values)  # type: ignore[arg-type]


def test_common_summary_uses_basic_evidence_and_source_order():
    frame = pd.DataFrame(
        {
            "amount": pd.Series([1.0, None, 4.0, 4.0]),
            "city": pd.Series(
                ["Amsterdam", "Berlin", None, "Amsterdam"], dtype="string"
            ),
            "flag": pd.Series([True, False, True, None], dtype="boolean"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    assert [item.label for item in summary.variables] == ["amount", "city", "flag"]
    assert [item.position for item in summary.variables] == [0, 1, 2]
    amount = summary.variables[0]
    assert amount.physical.family is PhysicalDtypeFamily.FLOATING
    assert amount.resolution_status is ResolutionStatus.RESOLVED
    assert amount.selected_type is SemanticType.NUMERIC
    assert amount.n_total == 4
    assert amount.n_missing == 1
    assert amount.n_non_missing == 3
    assert amount.n_unique_non_missing == 2
    assert amount.missing_ratio == pytest.approx(0.25)
    assert amount.unique_ratio_non_missing == pytest.approx(2 / 3)
    assert amount.unique_ratio_non_missing != pytest.approx(2 / 4)
    city = summary.variables[1]
    assert city.resolution_status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert city.n_unique_non_missing == 2
    assert city.unique_ratio_non_missing == pytest.approx(2 / 3)


def test_candidate_selections_are_resolved_without_an_interpretation():
    frame = pd.DataFrame(
        {
            "amount": pd.Series([1, 2, 3], dtype="int64"),
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string"),
            "group": pd.Series(pd.Categorical(["red", "blue", "red"])),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    expected = (
        SemanticType.NUMERIC,
        SemanticType.IDENTIFIER,
        SemanticType.CATEGORICAL,
    )
    for variable, column, semantic_type in zip(
        summary.variables,
        analysis.columns,
        expected,
    ):
        assert column.inferred.interpretation is None
        assert variable.resolution_status is ResolutionStatus.RESOLVED
        assert variable.selected_type is semantic_type
        assert variable.detail is not None


def test_ordinary_strings_stay_unresolved_without_specialized_detail():
    frame = pd.DataFrame(
        {
            "city": pd.Series(
                ["Amsterdam", "Berlin", "Amsterdam"],
                dtype="string",
            )
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    variable = summary.variables[0]
    assert analysis.columns[0].evidence.string_structure is not None
    assert analysis.columns[0].evidence.frequency is None
    assert variable.resolution_status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert variable.selected_type is None
    assert variable.detail is None
    assert variable.n_unique_non_missing == 2


def test_ambiguous_column_keeps_common_facts_and_no_detail():
    base = analyze_series(pd.Series([1, 2, 3], dtype="int64"), label="mixed")
    column = _with_resolution(
        base,
        SemanticResolution(
            status=ResolutionStatus.AMBIGUOUS,
            reason="Multiple candidates are supported: Identifier, Numeric.",
            candidates=(
                _supported(SemanticType.IDENTIFIER),
                _supported(SemanticType.NUMERIC),
            ),
        ),
    )
    assert column.evidence.numeric_structure is not None
    summary = build_variables_summary(_analysis_of(column))
    _assert_invariants(summary)
    variable = summary.variables[0]
    assert variable.label == "mixed"
    assert variable.resolution_status is ResolutionStatus.AMBIGUOUS
    assert variable.selected_type is None
    assert variable.detail is None
    assert variable.n_non_missing == 3


def test_synthetic_text_selection_has_no_text_detail():
    base = analyze_series(
        pd.Series(["The quick brown fox", "jumps over the lazy dog"], dtype="string"),
        label="prose",
    )
    column = _with_resolution(base, _candidate_resolution(SemanticType.TEXT))
    assert column.evidence.string_structure is not None
    summary = build_variables_summary(_analysis_of(column))
    variable = summary.variables[0]
    assert variable.resolution_status is ResolutionStatus.RESOLVED
    assert variable.selected_type is SemanticType.TEXT
    assert variable.detail is None
    assert column.inferred.interpretation is None


def test_resolved_selection_without_retained_evidence_omits_detail():
    physical_dtype = PhysicalDtype(
        family=PhysicalDtypeFamily.INTEGER,
        dtype_name="int64",
    )
    basic = BasicColumnEvidence(
        n_total=3,
        n_missing=0,
        n_non_missing=3,
        n_unique_non_missing=3,
    )
    column = ColumnAnalysis(
        position=0,
        label="amount",
        physical=physical_dtype,
        evidence=ColumnEvidence(basic=basic),
        inferred=InferredSemanticResult(
            physical=physical_dtype,
            resolution=_candidate_resolution(SemanticType.NUMERIC),
        ),
    )
    summary = build_variables_summary(_analysis_of(column))
    assert summary.variables[0].selected_type is SemanticType.NUMERIC
    assert summary.variables[0].detail is None


def test_numeric_detail_copies_structure_counts_and_ratios():
    series = pd.Series([-2.0, -1.5, 0.0, 4.0, np.nan])
    analysis = analyze_dataframe(pd.DataFrame({"amount": series}))
    evidence = analysis.columns[0].evidence.numeric_structure
    assert evidence is not None
    summary = build_variables_summary(analysis)
    detail = summary.variables[0].detail
    assert isinstance(detail, NumericVariableDetail)
    assert detail is not evidence
    assert detail.finite_count == evidence.finite_count == 4
    assert detail.positive_count == 1
    assert detail.negative_count == 2
    assert detail.zero_count == 1
    assert detail.positive_infinity_count == 0
    assert detail.negative_infinity_count == 0
    assert detail.integer_like_count == 3
    assert detail.non_integer_like_count == 1
    assert detail.is_non_decreasing is True
    assert detail.is_non_increasing is False
    assert detail.infinity_count == 0
    assert detail.finite_ratio == pytest.approx(1.0)
    assert detail.positive_ratio == pytest.approx(0.25)
    assert detail.negative_ratio == pytest.approx(0.5)
    assert detail.zero_ratio == pytest.approx(0.25)
    assert detail.integer_like_ratio == pytest.approx(0.75)
    assert summary.variables[0].n_missing == 1
    assert summary.variables[0].unique_ratio_non_missing == pytest.approx(1.0)


def test_numeric_monotonicity_directions_and_infinities():
    increasing = _summary(pd.DataFrame({"amount": [1, 2, 3]})).variables[0].detail
    decreasing = _summary(pd.DataFrame({"amount": [3, 2, 1]})).variables[0].detail
    mixed = _summary(pd.DataFrame({"amount": [1, 3, 2]})).variables[0].detail
    infinite = (
        _summary(pd.DataFrame({"amount": [1.0, np.inf, -np.inf]})).variables[0].detail
    )
    assert isinstance(increasing, NumericVariableDetail)
    assert isinstance(decreasing, NumericVariableDetail)
    assert isinstance(mixed, NumericVariableDetail)
    assert isinstance(infinite, NumericVariableDetail)
    assert increasing.is_non_decreasing is True
    assert increasing.is_non_increasing is False
    assert decreasing.is_non_decreasing is False
    assert decreasing.is_non_increasing is True
    assert mixed.is_non_decreasing is False
    assert mixed.is_non_increasing is False
    assert infinite.is_non_decreasing is None
    assert infinite.is_non_increasing is None
    assert infinite is not False
    assert infinite.positive_infinity_count == 1
    assert infinite.negative_infinity_count == 1
    assert infinite.infinity_count == 2
    assert infinite.finite_count == 1
    assert infinite.finite_ratio == pytest.approx(1 / 3)
    assert infinite.integer_like_count == 1
    assert infinite.non_integer_like_count == 0


def test_all_infinite_numeric_ratios_use_the_finite_denominator():
    detail = _summary(pd.DataFrame({"amount": [np.inf, -np.inf]})).variables[0].detail
    assert isinstance(detail, NumericVariableDetail)
    assert detail.finite_count == 0
    assert detail.finite_ratio == pytest.approx(0.0)
    assert detail.zero_ratio is None
    assert detail.positive_ratio is None
    assert detail.negative_ratio is None
    assert detail.integer_like_ratio is None
    assert detail.is_non_decreasing is None
    assert detail.is_non_increasing is None


def test_binary_looking_numbers_stay_numeric():
    integers = _summary(pd.DataFrame({"code": pd.Series([0, 1, 0, 1], dtype="int64")}))
    floats = _summary(pd.DataFrame({"code": pd.Series([0.0, 1.0, 0.0, 1.0])}))
    for summary in (integers, floats):
        _assert_invariants(summary)
        variable = summary.variables[0]
        assert variable.selected_type is SemanticType.NUMERIC
        assert isinstance(variable.detail, NumericVariableDetail)
        assert variable.detail.zero_count == 2
        assert variable.detail.positive_count == 2
        assert variable.detail.integer_like_count == 4
        assert not isinstance(variable.detail, CategoricalVariableDetail)


def test_categorical_detail_copies_frequency_counts():
    frame = pd.DataFrame(
        {"group": pd.Series(pd.Categorical(["red", "red", "blue", None]))}
    )
    analysis = analyze_dataframe(frame)
    frequency = analysis.columns[0].evidence.frequency
    assert frequency is not None
    assert frequency.basic is analysis.columns[0].evidence.basic
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    variable = summary.variables[0]
    detail = variable.detail
    assert variable.selected_type is SemanticType.CATEGORICAL
    assert isinstance(detail, CategoricalVariableDetail)
    assert detail is not frequency
    assert detail.most_frequent_count == frequency.most_frequent_count == 2
    assert detail.singleton_count == frequency.singleton_count == 1
    assert detail.most_frequent_ratio == pytest.approx(2 / 3)
    assert detail.singleton_ratio == pytest.approx(0.5)
    assert variable.n_missing == 1
    assert not hasattr(detail, "top_value")
    assert not hasattr(detail, "exact_distinct_non_missing_values")


def test_categorical_singletons_ordered_storage_and_unused_levels():
    singletons = _summary(
        pd.DataFrame({"group": pd.Series(pd.Categorical(["a", "b", "c"]))})
    ).variables[0]
    ordered = analyze_dataframe(
        pd.DataFrame(
            {
                "group": pd.Categorical(
                    ["red", "red", "blue"],
                    categories=["red", "blue", "green"],
                    ordered=True,
                )
            }
        )
    )
    summary = build_variables_summary(ordered)
    variable = summary.variables[0]
    detail = variable.detail
    frequency = ordered.columns[0].evidence.frequency
    assert isinstance(singletons.detail, CategoricalVariableDetail)
    assert singletons.detail.most_frequent_count == 1
    assert singletons.detail.singleton_count == 3
    assert singletons.detail.singleton_ratio == pytest.approx(1.0)
    assert singletons.detail.most_frequent_ratio == pytest.approx(1 / 3)
    assert isinstance(detail, CategoricalVariableDetail)
    assert variable.physical.categorical_ordered is True
    assert variable.selected_type is SemanticType.CATEGORICAL
    assert "ORDINAL" not in SemanticType.__members__
    assert not hasattr(detail, "is_ordered_storage")
    assert frequency is not None
    assert frequency.exact_distinct_non_missing_values == frozenset({"red", "blue"})
    assert "green" not in frequency.exact_distinct_non_missing_values
    assert detail.most_frequent_count == 2
    assert detail.singleton_count == 1


def test_frequency_retention_bound_stays_on_evidence_not_the_detail():
    labels = [f"c{index}" for index in range(33)]
    analysis = analyze_dataframe(
        pd.DataFrame({"group": pd.Series(pd.Categorical(labels))})
    )
    frequency = analysis.columns[0].evidence.frequency
    detail = build_variables_summary(analysis).variables[0].detail
    assert frequency is not None
    assert frequency.exact_distinct_non_missing_values is None
    assert isinstance(detail, CategoricalVariableDetail)
    assert detail.most_frequent_count == 1
    assert detail.singleton_count == 33
    assert detail.singleton_ratio == pytest.approx(1.0)


def test_identifier_detail_copies_pattern_counts_without_scoring():
    canonical = _summary(
        pd.DataFrame({"code": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string")})
    ).variables[0]
    compact = _summary(
        pd.DataFrame({"code": pd.Series([_COMPACT_A, _COMPACT_B], dtype="string")})
    ).variables[0]
    assert isinstance(canonical.detail, IdentifierVariableDetail)
    assert canonical.detail.uuid_count == 3
    assert canonical.detail.uuid_ratio == pytest.approx(1.0)
    assert canonical.detail.hex_32_count == 0
    assert canonical.detail.hex_32_ratio == pytest.approx(0.0)
    assert canonical.detail.ipv4_count == 0
    assert canonical.detail.ipv6_count == 0
    assert canonical.detail.ipv4_ratio == pytest.approx(0.0)
    assert canonical.detail.ipv6_ratio == pytest.approx(0.0)
    assert isinstance(compact.detail, IdentifierVariableDetail)
    assert compact.detail.uuid_count == 2
    assert compact.detail.hex_32_count == 2
    assert compact.detail.uuid_ratio == pytest.approx(1.0)
    assert compact.detail.hex_32_ratio == pytest.approx(1.0)
    assert compact.detail.hex_40_count == 0
    assert not hasattr(compact.detail, "score")
    assert not hasattr(compact.detail, "confidence")


@pytest.mark.parametrize("width", [40, 64, 128])
def test_supported_hex_widths_are_identifier_pattern_facts(width: int):
    series = pd.Series(
        [_hex_token(width, "a"), _hex_token(width, "b")],
        dtype="string",
    )
    variable = _summary(pd.DataFrame({"code": series})).variables[0]
    assert variable.selected_type is SemanticType.IDENTIFIER
    detail = variable.detail
    assert isinstance(detail, IdentifierVariableDetail)
    assert getattr(detail, f"hex_{width}_count") == 2
    assert getattr(detail, f"hex_{width}_ratio") == pytest.approx(1.0)
    assert detail.uuid_count == 0
    for other in (32, 40, 64, 128):
        if other != width:
            assert getattr(detail, f"hex_{other}_count") == 0


def test_duplicate_and_missing_uuids_remain_identifier():
    duplicate = _summary(
        pd.DataFrame({"code": pd.Series([_UUID_A, _UUID_A, _UUID_B], dtype="string")})
    ).variables[0]
    missing = _summary(
        pd.DataFrame({"code": pd.Series([_UUID_A, pd.NA, _UUID_B], dtype="string")})
    ).variables[0]
    assert duplicate.selected_type is SemanticType.IDENTIFIER
    assert isinstance(duplicate.detail, IdentifierVariableDetail)
    assert duplicate.detail.uuid_count == 3
    assert duplicate.detail.uuid_ratio == pytest.approx(1.0)
    assert duplicate.n_non_missing == 3
    assert duplicate.n_unique_non_missing == 2
    assert missing.selected_type is SemanticType.IDENTIFIER
    assert isinstance(missing.detail, IdentifierVariableDetail)
    assert missing.n_missing == 1
    assert missing.detail.uuid_count == 2
    assert missing.detail.uuid_ratio == pytest.approx(1.0)
    assert missing.detail.n_non_missing == 2


def test_constant_and_empty_uuid_columns_do_not_get_identifier_detail():
    frame = pd.DataFrame(
        {
            "same": pd.Series([_UUID_A, _UUID_A], dtype="string"),
            "blank": pd.Series([pd.NA, pd.NA], dtype="string"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    constant = summary.variables[0]
    empty = summary.variables[1]
    assert constant.selected_type is SemanticType.CONSTANT
    assert constant.detail is None
    assert analysis.columns[0].evidence.pattern is None
    assert analysis.columns[0].evidence.frequency is None
    assert not hasattr(constant, "constant_value")
    assert empty.selected_type is SemanticType.EMPTY
    assert empty.detail is None
    assert empty.n_non_missing == 0
    assert empty.unique_ratio_non_missing is None


@pytest.mark.parametrize(
    ("series", "semantic_type", "family"),
    [
        (
            pd.Series([None, None], dtype="object"),
            SemanticType.EMPTY,
            PhysicalDtypeFamily.OBJECT,
        ),
        (
            pd.Series([5, 5, pd.NA], dtype="Int64"),
            SemanticType.CONSTANT,
            PhysicalDtypeFamily.INTEGER,
        ),
        (
            pd.Series([True, False, True]),
            SemanticType.BOOLEAN,
            PhysicalDtypeFamily.BOOLEAN,
        ),
        (
            pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01"])),
            SemanticType.DATETIME,
            PhysicalDtypeFamily.DATETIME,
        ),
        (
            pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01"], utc=True)),
            SemanticType.DATETIME,
            PhysicalDtypeFamily.DATETIME_TZ_AWARE,
        ),
        (
            pd.Series(pd.to_timedelta(["1 day", "2 days"])),
            SemanticType.TIMEDELTA,
            PhysicalDtypeFamily.TIMEDELTA,
        ),
    ],
)
def test_structural_types_have_common_facts_and_no_specialized_detail(
    series: pd.Series,
    semantic_type: SemanticType,
    family: PhysicalDtypeFamily,
):
    analysis = analyze_dataframe(pd.DataFrame({"value": series}))
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    variable = summary.variables[0]
    assert variable.selected_type is semantic_type
    assert variable.physical.family is family
    if semantic_type is SemanticType.BOOLEAN:
        assert isinstance(variable.detail, BooleanVariableDetail)
        assert variable.detail.true_count == 2
        assert variable.detail.false_count == 1
    else:
        assert variable.detail is None
    assert analysis.columns[0].evidence.frequency is None
    assert analysis.columns[0].inferred.interpretation is not None


def test_semantic_first_detail_follows_the_selected_type():
    frame = pd.DataFrame(
        {
            "uuid": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string"),
            "same_uuid": pd.Series([_UUID_A, _UUID_A, _UUID_A], dtype="string"),
            "bits": pd.Series([0, 1, 0], dtype="int64"),
            "ordered": pd.Categorical(
                ["low", "high", "low"],
                categories=["low", "high"],
                ordered=True,
            ),
            "city": pd.Series(["Amsterdam", "Berlin", "Amsterdam"], dtype="string"),
            "prose": pd.Series(
                [
                    "The quick brown fox",
                    "jumps over the lazy dog",
                    "and keeps running today",
                ],
                dtype="string",
            ),
            "address": pd.Series(
                ["192.0.2.1", "198.51.100.14", "203.0.113.8"],
                dtype="string",
            ),
            "mixed": pd.Series([1, "a", None]),
            "wave": pd.Series([1 + 1j, 2 + 2j, 3 + 4j]),
            "period": pd.Series(pd.period_range("2020-01", periods=3, freq="M")),
            "codes": pd.Series(pd.Categorical([1, 1, 2])),
            "yes_no": pd.Series(["yes", "no", "yes"], dtype="string"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    by_label = {variable.label: variable for variable in summary.variables}
    assert isinstance(by_label["uuid"].detail, IdentifierVariableDetail)
    assert not isinstance(by_label["uuid"].detail, CategoricalVariableDetail)
    assert by_label["same_uuid"].selected_type is SemanticType.CONSTANT
    assert by_label["same_uuid"].detail is None
    assert isinstance(by_label["bits"].detail, NumericVariableDetail)
    assert by_label["bits"].selected_type is SemanticType.NUMERIC
    assert by_label["ordered"].selected_type is SemanticType.CATEGORICAL
    assert isinstance(by_label["ordered"].detail, CategoricalVariableDetail)
    assert by_label["ordered"].physical.categorical_ordered is True
    assert by_label["city"].resolution_status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert by_label["city"].detail is None
    assert by_label["prose"].detail is None
    assert by_label["prose"].selected_type is None
    address = next(column for column in analysis.columns if column.label == "address")
    assert address.evidence.pattern is not None
    assert address.evidence.pattern.ipv4_count == 3
    assert by_label["address"].detail is None
    assert by_label["address"].resolution_status is (
        ResolutionStatus.INSUFFICIENT_EVIDENCE
    )
    assert by_label["mixed"].detail is None
    assert by_label["wave"].detail is None
    assert by_label["wave"].physical.family is PhysicalDtypeFamily.COMPLEX
    assert by_label["period"].detail is None
    assert by_label["period"].physical.family is PhysicalDtypeFamily.PERIOD
    assert isinstance(by_label["codes"].detail, CategoricalVariableDetail)
    assert by_label["codes"].selected_type is SemanticType.CATEGORICAL
    assert by_label["yes_no"].detail is None
    assert by_label["yes_no"].resolution_status is (
        ResolutionStatus.INSUFFICIENT_EVIDENCE
    )


def test_duplicate_labels_keep_distinct_variable_details():
    frame = pd.concat(
        [
            pd.Series([1, 2, 3], dtype="int64"),
            pd.Series(pd.Categorical(["a", "a", "b"])),
        ],
        axis=1,
    )
    frame.columns = ["x", "x"]
    summary = _summary(frame)
    _assert_invariants(summary)
    assert summary.n_variables == 2
    assert summary.variables[0].label == "x"
    assert summary.variables[1].label == "x"
    assert summary.variables[0].position == 0
    assert summary.variables[1].position == 1
    assert isinstance(summary.variables[0].detail, NumericVariableDetail)
    assert isinstance(summary.variables[1].detail, CategoricalVariableDetail)
    assert summary.variables[0] is not summary.variables[1]


def test_non_string_and_multiindex_labels_stay_original_objects():
    frame = pd.DataFrame(
        [
            [None, None, None],
        ],
        columns=[42, ("group", "value"), pd.Timestamp("2020-01-01")],
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    assert summary.variables[0].label == 42
    assert type(summary.variables[0].label) is int
    assert summary.variables[1].label == ("group", "value")
    assert isinstance(summary.variables[1].label, tuple)
    assert summary.variables[2].label == pd.Timestamp("2020-01-01")
    assert not isinstance(summary.variables[2].label, str)
    columns = pd.MultiIndex.from_tuples([("group", "value"), ("group", "value")])
    nested = pd.DataFrame([[1, "Amsterdam"], [2, "Berlin"]], columns=columns)
    nested_summary = _summary(nested)
    assert nested_summary.variables[0].label == ("group", "value")
    assert nested_summary.variables[1].label == ("group", "value")
    assert nested_summary.variables[0].label != "group.value"
    assert isinstance(nested_summary.variables[0].detail, NumericVariableDetail)
    assert nested_summary.variables[1].detail is None


def test_variables_stay_in_dataframe_order():
    frame = pd.DataFrame(
        {
            "flag": pd.Series([True, False]),
            "amount": pd.Series([1, 2], dtype="int64"),
            "when": pd.to_datetime(["2020-01-01", "2021-01-01"]),
            "city": pd.Series(["Amsterdam", "Berlin"], dtype="string"),
        }
    )
    summary = _summary(frame)
    assert [item.selected_type for item in summary.variables] == [
        SemanticType.BOOLEAN,
        SemanticType.NUMERIC,
        SemanticType.DATETIME,
        None,
    ]
    assert [item.position for item in summary.variables] == [0, 1, 2, 3]


def test_product_models_do_not_retain_analysis_sources():
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3],
            "group": pd.Categorical(["a", "b", "a"]),
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string"),
        }
    )
    summary = _summary(frame)
    _assert_no_source(summary)
    assert not hasattr(summary, "analysis")
    assert not hasattr(summary.variables[0], "evidence")
    assert not hasattr(summary.variables[0], "series")


def test_builder_does_not_rescan_after_analysis(monkeypatch: pytest.MonkeyPatch):
    frame = pd.DataFrame(
        {
            "amount": [-1.0, 0.0, 2.0],
            "group": pd.Categorical(["red", "blue", "red"]),
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string"),
        }
    )
    analysis = analyze_dataframe(frame)
    frame.iloc[:, 0] = [9.0, 9.0, 9.0]

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("variables builder rescanned or reanalyzed")

    targets = (
        (dataset_module, "analyze_dataframe"),
        (column_module, "analyze_series"),
        (pipeline, "infer_series_semantics"),
        (physical, "classify_physical_dtype"),
        (basic_evidence, "collect_basic_column_evidence"),
        (frequency_evidence, "collect_frequency_evidence"),
        (numeric_evidence, "collect_numeric_structure_evidence"),
        (numeric_descriptive, "collect_numeric_descriptive_analysis"),
        (boolean_descriptive, "collect_boolean_descriptive_analysis"),
        (string_evidence, "collect_string_structure_evidence"),
        (pattern_evidence, "collect_pattern_evidence"),
        (string_content_evidence, "collect_string_content_evidence"),
        (resolution_module, "resolve_semantics"),
        (identifier_candidate, "assess_identifier_candidate"),
        (core_candidates, "assess_numeric_candidate"),
        (core_candidates, "assess_categorical_candidate"),
        (core_candidates, "assess_text_candidate"),
    )
    for module, name in targets:
        monkeypatch.setattr(module, name, _fail)
        if name in vars(variables_module):
            monkeypatch.setattr(variables_module, name, _fail)
    monkeypatch.setattr(pd.Series, "value_counts", _fail)
    monkeypatch.setattr(pd.Series, "nunique", _fail)
    monkeypatch.setattr(pd.Series, "isna", _fail)
    monkeypatch.setattr(pd.Series, "dropna", _fail)
    monkeypatch.setattr(pd.Series, "quantile", _fail)
    monkeypatch.setattr(pd.Series, "std", _fail)
    monkeypatch.setattr(pd.Series, "mean", _fail)
    summary = build_variables_summary(analysis)
    _assert_invariants(summary, analysis)
    detail = summary.variables[0].detail
    assert isinstance(detail, NumericVariableDetail)
    assert detail.negative_count == 1
    assert detail.zero_count == 1
    assert detail.positive_count == 1
    assert detail.descriptive is not None
    assert detail.descriptive is not analysis.columns[0].numeric_analysis
    assert detail.descriptive.minimum == -1.0
    assert detail.descriptive.maximum == 2.0
    assert detail.descriptive.mean == pytest.approx((-1.0 + 0.0 + 2.0) / 3.0)


def test_frequency_is_collected_only_for_nonstructural_categoricals(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[pd.Series] = []
    real = column_module.collect_frequency_evidence

    def spy(series: pd.Series, basic: BasicColumnEvidence):
        calls.append(series)
        return real(series, basic)

    monkeypatch.setattr(column_module, "collect_frequency_evidence", spy)
    untouched = (
        pd.Series([1, 2, 3], dtype="int64"),
        pd.Series(["Amsterdam", "Berlin"], dtype="string"),
        pd.Series([True, False]),
        pd.Series([pd.NA, pd.NA], dtype="string"),
        pd.Series(["same", "same"], dtype="string"),
        pd.Series(pd.Categorical(["red", "red"])),
        pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01"])),
    )
    for series in untouched:
        analyze_series(series)
    assert calls == []
    varying = pd.Series(pd.Categorical(["red", "blue", "red"]))
    analyzed = analyze_series(varying)
    assert len(calls) == 1
    assert analyzed.evidence.frequency is not None
    assert analyzed.evidence.frequency.basic is analyzed.evidence.basic
    assert analyzed.inferred.selected_type is SemanticType.CATEGORICAL


def test_variables_module_does_not_import_pandas_or_collectors():
    source = Path(variables_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    modules: list[str] = []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            names.extend(alias.name for alias in node.names)
    assert "pandas" not in modules
    assert "numpy" not in modules
    forbidden = {
        "analyze_dataframe",
        "analyze_series",
        "infer_series_semantics",
        "classify_physical_dtype",
        "collect_basic_column_evidence",
        "collect_frequency_evidence",
        "collect_numeric_structure_evidence",
        "collect_numeric_descriptive_analysis",
        "collect_string_structure_evidence",
        "collect_pattern_evidence",
        "collect_string_content_evidence",
        "resolve_semantics",
    }
    assert forbidden.isdisjoint(names)


def test_models_are_frozen():
    summary = _summary(pd.DataFrame({"amount": [1, 2, 3]}))
    detail = summary.variables[0].detail
    assert isinstance(detail, NumericVariableDetail)
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.variables = ()  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.variables[0].position = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        detail.finite_count = 0  # type: ignore[misc]


def test_builder_rejects_anything_other_than_dataset_analysis(
    monkeypatch: pytest.MonkeyPatch,
):
    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("builder analyzed a frame")

    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    frame = pd.DataFrame({"amount": [1, 2, 3]})
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_variables_summary(frame)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_variables_summary(frame["amount"])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_variables_summary(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_variables_summary({"amount": [1, 2, 3]})  # type: ignore[arg-type]


def test_zero_size_datasets():
    empty = _summary(pd.DataFrame())
    _assert_invariants(empty)
    assert empty.n_variables == 0
    assert empty.variables == ()
    no_columns = _summary(pd.DataFrame(index=range(4)))
    _assert_invariants(no_columns)
    assert no_columns.n_variables == 0
    no_rows = _summary(
        pd.DataFrame(
            {
                "amount": pd.Series([], dtype="int64"),
                "city": pd.Series([], dtype="string"),
                "flag": pd.Series([], dtype="boolean"),
            }
        )
    )
    _assert_invariants(no_rows)
    assert no_rows.n_variables == 3
    for variable in no_rows.variables:
        assert variable.selected_type is SemanticType.EMPTY
        assert variable.detail is None
        assert variable.n_total == 0
        assert variable.n_missing == 0
        assert variable.n_non_missing == 0
        assert variable.n_unique_non_missing == 0
        assert variable.missing_ratio is None
        assert variable.unique_ratio_non_missing is None


def test_equal_analyses_produce_equal_summaries():
    frame = pd.DataFrame(
        {
            "amount": [1, 2, None],
            "group": pd.Categorical(["a", "a", "b"]),
        }
    )
    assert _summary(frame) == _summary(frame)


def test_public_api_is_unchanged():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "build_variables_summary")
    assert not hasattr(pytics, "VariablesSummary")
    assert not hasattr(pytics, "VariableSummary")


def test_invalid_variable_models_are_rejected():
    with pytest.raises(ValueError, match="position"):
        _variable(position=-1)
    with pytest.raises(TypeError, match="physical"):
        _variable(physical="float")
    with pytest.raises(ValueError, match="selected semantic type"):
        _variable(selected_type=None)
    with pytest.raises(ValueError, match="no selected semantic type"):
        _variable(
            resolution_status=ResolutionStatus.AMBIGUOUS,
            selected_type=SemanticType.NUMERIC,
            detail=None,
        )
    with pytest.raises(ValueError, match="n_non_missing must equal"):
        _variable(n_non_missing=2)
    with pytest.raises(TypeError, match="NumericVariableDetail"):
        _variable(
            detail=CategoricalVariableDetail(
                n_non_missing=3,
                n_unique_non_missing=3,
                most_frequent_count=1,
                singleton_count=3,
            )
        )
    with pytest.raises(TypeError, match="BooleanVariableDetail"):
        _variable(
            resolution_status=ResolutionStatus.RESOLVED,
            selected_type=SemanticType.BOOLEAN,
            physical=PhysicalDtype(
                family=PhysicalDtypeFamily.BOOLEAN,
                dtype_name="bool",
            ),
            detail=_numeric_detail(),
        )
    with pytest.raises(ValueError, match="numeric detail n_non_missing"):
        _variable(
            detail=_numeric_detail(
                n_non_missing=2,
                finite_count=2,
                positive_count=2,
                integer_like_count=2,
            )
        )
    with pytest.raises(ValueError, match="one distinct"):
        _variable(
            detail=_numeric_detail(is_non_decreasing=True, is_non_increasing=True)
        )
    with pytest.raises(ValueError, match="source order"):
        VariablesSummary(variables=(_variable(position=1),))
    first = _variable()
    with pytest.raises(ValueError, match="share n_total"):
        VariablesSummary(
            variables=(
                first,
                _variable(
                    position=1,
                    n_total=4,
                    n_missing=0,
                    n_non_missing=4,
                    n_unique_non_missing=4,
                    detail=_numeric_detail(
                        n_non_missing=4,
                        finite_count=4,
                        positive_count=4,
                        integer_like_count=4,
                    ),
                ),
            )
        )
    with pytest.raises(TypeError, match="tuple"):
        VariablesSummary(variables=[first])  # type: ignore[arg-type]


def test_builder_rejects_incoherent_resolution_state():
    analysis = analyze_dataframe(pd.DataFrame({"amount": [1, 2, 3]}))

    class _Resolution:
        def __init__(self, status: object, selected: object) -> None:
            self.status = status
            self.selected_type = selected

    class _Inferred:
        def __init__(self, status: object, selected: object) -> None:
            self.resolution = _Resolution(status, selected)
            self.selected_type = selected

    column = analysis.columns[0]
    object.__setattr__(
        column,
        "inferred",
        _Inferred(ResolutionStatus.RESOLVED, None),
    )
    with pytest.raises(ValueError, match="no selected semantic type"):
        build_variables_summary(analysis)
    object.__setattr__(
        column,
        "inferred",
        _Inferred(ResolutionStatus.INSUFFICIENT_EVIDENCE, SemanticType.NUMERIC),
    )
    with pytest.raises(ValueError, match="unresolved column has a selected"):
        build_variables_summary(analysis)
    object.__setattr__(column, "inferred", _Inferred("unresolved", None))
    with pytest.raises(ValueError, match="unrecognized resolution status"):
        build_variables_summary(analysis)


def test_selected_type_without_its_evidence_omits_detail():
    categorical_physical = PhysicalDtype(
        family=PhysicalDtypeFamily.CATEGORICAL,
        dtype_name="category",
        categorical_ordered=False,
    )
    string_physical = PhysicalDtype(
        family=PhysicalDtypeFamily.STRING,
        dtype_name="string",
    )
    basic = BasicColumnEvidence(
        n_total=3,
        n_missing=0,
        n_non_missing=3,
        n_unique_non_missing=2,
    )
    categorical = ColumnAnalysis(
        position=0,
        label="group",
        physical=categorical_physical,
        evidence=ColumnEvidence(basic=basic),
        inferred=InferredSemanticResult(
            physical=categorical_physical,
            resolution=_candidate_resolution(SemanticType.CATEGORICAL),
        ),
    )
    identifier = ColumnAnalysis(
        position=0,
        label="code",
        physical=string_physical,
        evidence=ColumnEvidence(basic=basic),
        inferred=InferredSemanticResult(
            physical=string_physical,
            resolution=_candidate_resolution(SemanticType.IDENTIFIER),
        ),
    )
    assert (
        build_variables_summary(_analysis_of(categorical)).variables[0].detail is None
    )
    assert build_variables_summary(_analysis_of(identifier)).variables[0].detail is None


def test_undefined_numeric_ratios_and_empty_pattern_ratios():
    empty_numeric = _numeric_detail(
        n_non_missing=0,
        finite_count=0,
        positive_count=0,
        negative_count=0,
        zero_count=0,
        integer_like_count=0,
        non_integer_like_count=0,
        is_non_decreasing=True,
        is_non_increasing=True,
    )
    assert empty_numeric.finite_ratio is None
    assert empty_numeric.zero_ratio is None
    assert empty_numeric.infinity_count == 0
    empty_identifier = IdentifierVariableDetail(
        n_non_missing=0,
        uuid_count=0,
        ipv4_count=0,
        ipv6_count=0,
        hex_32_count=0,
        hex_40_count=0,
        hex_64_count=0,
        hex_128_count=0,
    )
    assert empty_identifier.uuid_ratio is None
    assert empty_identifier.hex_128_ratio is None
    empty_categorical = CategoricalVariableDetail(
        n_non_missing=0,
        n_unique_non_missing=0,
        most_frequent_count=0,
        singleton_count=0,
    )
    assert empty_categorical.most_frequent_ratio is None
    assert empty_categorical.singleton_ratio is None
    repeated = CategoricalVariableDetail(
        n_non_missing=3,
        n_unique_non_missing=1,
        most_frequent_count=3,
        singleton_count=0,
    )
    assert repeated.most_frequent_ratio == pytest.approx(1.0)
    assert repeated.singleton_ratio == pytest.approx(0.0)
    once = CategoricalVariableDetail(
        n_non_missing=1,
        n_unique_non_missing=1,
        most_frequent_count=1,
        singleton_count=1,
    )
    assert once.singleton_ratio == pytest.approx(1.0)


def test_specialized_details_reject_inconsistent_counts():
    with pytest.raises(ValueError, match="finite and infinite"):
        _numeric_detail(
            n_non_missing=3, finite_count=1, positive_count=1, integer_like_count=1
        )
    with pytest.raises(ValueError, match="positive, negative, and zero"):
        _numeric_detail(positive_count=1)
    with pytest.raises(ValueError, match="integer-like"):
        _numeric_detail(integer_like_count=1, non_integer_like_count=0)
    with pytest.raises(
        ValueError, match="undefined when a non-missing value is infinite"
    ):
        _numeric_detail(
            n_non_missing=2,
            finite_count=1,
            positive_count=1,
            integer_like_count=1,
            positive_infinity_count=1,
            is_non_decreasing=True,
            is_non_increasing=False,
        )
    with pytest.raises(TypeError, match="monotonicity is a bool"):
        _numeric_detail(is_non_decreasing=None, is_non_increasing=None)
    with pytest.raises(ValueError, match="both"):
        _numeric_detail(
            n_non_missing=1,
            finite_count=1,
            positive_count=1,
            integer_like_count=1,
            is_non_decreasing=True,
            is_non_increasing=False,
        )
    with pytest.raises(ValueError, match="non-negative int"):
        _numeric_detail(zero_count=-1)
    with pytest.raises(ValueError, match="cannot exceed n_non_missing"):
        IdentifierVariableDetail(
            n_non_missing=1,
            uuid_count=2,
            ipv4_count=0,
            ipv6_count=0,
            hex_32_count=0,
            hex_40_count=0,
            hex_64_count=0,
            hex_128_count=0,
        )
    with pytest.raises(ValueError, match="cannot exceed n_non_missing"):
        CategoricalVariableDetail(
            n_non_missing=1,
            n_unique_non_missing=2,
            most_frequent_count=1,
            singleton_count=1,
        )
    frequency_cases = (
        (
            dict(
                n_non_missing=0,
                n_unique_non_missing=0,
                most_frequent_count=1,
                singleton_count=0,
            ),
            "empty frequency population",
        ),
        (
            dict(
                n_non_missing=2,
                n_unique_non_missing=0,
                most_frequent_count=2,
                singleton_count=0,
            ),
            "must be positive",
        ),
        (
            dict(
                n_non_missing=2,
                n_unique_non_missing=2,
                most_frequent_count=0,
                singleton_count=2,
            ),
            "must be >= 1",
        ),
        (
            dict(
                n_non_missing=2,
                n_unique_non_missing=1,
                most_frequent_count=3,
                singleton_count=0,
            ),
            "cannot exceed n_non_missing",
        ),
        (
            dict(
                n_non_missing=4,
                n_unique_non_missing=2,
                most_frequent_count=2,
                singleton_count=3,
            ),
            "cannot exceed n_unique",
        ),
        (
            dict(
                n_non_missing=3,
                n_unique_non_missing=1,
                most_frequent_count=2,
                singleton_count=0,
            ),
            "occurs n_non_missing times",
        ),
        (
            dict(
                n_non_missing=1,
                n_unique_non_missing=1,
                most_frequent_count=1,
                singleton_count=0,
            ),
            "singleton_count is 1 only",
        ),
        (
            dict(
                n_non_missing=3,
                n_unique_non_missing=2,
                most_frequent_count=1,
                singleton_count=1,
            ),
            "occurs once",
        ),
        (
            dict(
                n_non_missing=4,
                n_unique_non_missing=2,
                most_frequent_count=2,
                singleton_count=2,
            ),
            "not a singleton",
        ),
        (
            dict(
                n_non_missing=10,
                n_unique_non_missing=3,
                most_frequent_count=2,
                singleton_count=0,
            ),
            "inconsistent",
        ),
    )
    for kwargs, message in frequency_cases:
        with pytest.raises(ValueError, match=message):
            CategoricalVariableDetail(**kwargs)


def test_summary_rejects_detail_that_disagrees_with_universal_counts():
    categorical_physical = PhysicalDtype(
        family=PhysicalDtypeFamily.CATEGORICAL,
        dtype_name="category",
        categorical_ordered=False,
    )
    string_physical = PhysicalDtype(
        family=PhysicalDtypeFamily.STRING,
        dtype_name="string",
    )
    with pytest.raises(TypeError, match="resolution_status"):
        _variable(resolution_status="resolved")
    with pytest.raises(ValueError, match="n_missing cannot exceed"):
        _variable(n_missing=4)
    with pytest.raises(ValueError, match="n_unique_non_missing cannot exceed"):
        _variable(n_unique_non_missing=4)
    with pytest.raises(TypeError, match="CategoricalVariableDetail"):
        _variable(
            selected_type=SemanticType.CATEGORICAL,
            physical=categorical_physical,
            detail=_numeric_detail(),
        )
    with pytest.raises(TypeError, match="IdentifierVariableDetail"):
        _variable(
            selected_type=SemanticType.IDENTIFIER,
            physical=string_physical,
            detail=_numeric_detail(),
        )
    with pytest.raises(ValueError, match="categorical detail n_non_missing"):
        _variable(
            selected_type=SemanticType.CATEGORICAL,
            physical=categorical_physical,
            detail=CategoricalVariableDetail(
                n_non_missing=2,
                n_unique_non_missing=2,
                most_frequent_count=1,
                singleton_count=2,
            ),
        )
    with pytest.raises(ValueError, match="n_unique_non_missing must match"):
        _variable(
            selected_type=SemanticType.CATEGORICAL,
            physical=categorical_physical,
            n_unique_non_missing=3,
            detail=CategoricalVariableDetail(
                n_non_missing=3,
                n_unique_non_missing=2,
                most_frequent_count=2,
                singleton_count=1,
            ),
        )
    with pytest.raises(ValueError, match="identifier detail n_non_missing"):
        _variable(
            selected_type=SemanticType.IDENTIFIER,
            physical=string_physical,
            detail=IdentifierVariableDetail(
                n_non_missing=2,
                uuid_count=2,
                ipv4_count=0,
                ipv6_count=0,
                hex_32_count=0,
                hex_40_count=0,
                hex_64_count=0,
                hex_128_count=0,
            ),
        )
    with pytest.raises(ValueError, match="finite constant"):
        _variable(
            n_unique_non_missing=1,
            detail=_numeric_detail(is_non_decreasing=False, is_non_increasing=False),
        )
    with pytest.raises(TypeError, match="VariableSummary"):
        VariablesSummary(variables=("amount",))  # type: ignore[arg-type]
