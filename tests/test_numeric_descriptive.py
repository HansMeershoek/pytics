"""TSK-020: finite-population descriptive statistics for Numeric columns."""

from __future__ import annotations

import ast
import dataclasses
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.column as column_module
import pytics.analysis.numeric as numeric_module
import pytics.analysis.variables as variables_module
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import ColumnEvidence
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from tests.missing_margins import missing_analysis_for_margins
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.numeric import _on_segment
from pytics.analysis.numeric import collect_numeric_descriptive_analysis
from pytics.analysis.variables import BooleanVariableDetail
from pytics.analysis.variables import CategoricalVariableDetail
from pytics.analysis.variables import IdentifierVariableDetail
from pytics.analysis.variables import NumericVariableDetail
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
_RETAINED = (pd.DataFrame, pd.Series, np.ndarray, np.generic)


def _sample_std(values: list[float]) -> float:
    """Independent sample standard deviation, dividing by n - 1."""
    count = len(values)
    center = sum(values) / count
    variance = sum((item - center) ** 2 for item in values) / (count - 1)
    return math.sqrt(variance)


def _one_value() -> NumericDescriptiveAnalysis:
    return NumericDescriptiveAnalysis(
        finite_count=1,
        minimum=5,
        maximum=5,
        mean=5.0,
        median=5,
        standard_deviation=None,
        q1=5,
        q3=5,
    )


def _walk(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return
    seen.add(identity)
    assert not isinstance(value, _RETAINED)
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _walk(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _walk(item, seen)


def test_integer_float_and_nullable_populations_match_the_sample_rule():
    cases = {
        "int64": pd.Series([1, 2, 3, 4], dtype="int64"),
        "float64": pd.Series([1.0, 2.0, 3.0, 4.0]),
        "Int64": pd.Series([1, pd.NA, 2, 3, 4], dtype="Int64"),
        "Float64": pd.Series([1.0, pd.NA, 2.0, 3.0, 4.0], dtype="Float64"),
        "float32": pd.Series([1.0, 2.0, 3.0, 4.0], dtype="float32"),
        "uint64": pd.Series(np.array([1, 2, 3, 4], dtype=np.uint64)),
        "UInt64": pd.Series([1, pd.NA, 2, 3, 4], dtype="UInt64"),
    }
    for series in cases.values():
        described = collect_numeric_descriptive_analysis(series)
        assert described.finite_count == 4
        assert described.minimum == 1
        assert described.maximum == 4
        assert described.mean == pytest.approx(2.5)
        assert described.q1 == pytest.approx(1.75)
        assert described.median == pytest.approx(2.5)
        assert described.q3 == pytest.approx(3.25)
        assert described.range == pytest.approx(3)
        assert described.interquartile_range == pytest.approx(1.5)
        assert described.standard_deviation == pytest.approx(
            _sample_std([1.0, 2.0, 3.0, 4.0])
        )
        assert type(described.mean) is float
        assert type(described.standard_deviation) is float


def test_sample_standard_deviation_uses_one_degree_of_freedom():
    described = collect_numeric_descriptive_analysis(
        pd.Series([1, 2, 3], dtype="int64")
    )
    population = math.sqrt(((1 - 2) ** 2 + (3 - 2) ** 2) / 3)
    assert described.standard_deviation == pytest.approx(1.0)
    assert described.standard_deviation != pytest.approx(population)


def test_missing_values_are_excluded_from_the_finite_population():
    complete = collect_numeric_descriptive_analysis(pd.Series([1.0, 3.0]))
    with_missing = collect_numeric_descriptive_analysis(
        pd.Series([1.0, None, np.nan, 3.0], dtype="float64")
    )
    nullable = collect_numeric_descriptive_analysis(
        pd.Series([1.0, pd.NA, 3.0], dtype="Float64")
    )
    assert with_missing == complete
    assert nullable == complete
    assert with_missing.finite_count == 2
    assert with_missing.mean == pytest.approx(2.0)


def test_positive_and_negative_infinity_are_excluded():
    positive = analyze_series(pd.Series([1.0, 2.0, np.inf]))
    negative = analyze_series(pd.Series([-np.inf, 1.0, 2.0]))
    mixed = analyze_series(pd.Series([1.0, np.nan, np.inf, -np.inf, 3.0]))
    for analyzed in (positive, negative, mixed):
        assert analyzed.inferred.selected_type is SemanticType.NUMERIC
        structure = analyzed.evidence.numeric_structure
        described = analyzed.numeric_analysis
        assert structure is not None and described is not None
        assert described.finite_count == structure.finite_count == 2
        assert described.minimum == 1.0
    assert positive.evidence.numeric_structure is not None
    assert positive.evidence.numeric_structure.positive_infinity_count == 1
    assert positive.evidence.numeric_structure.finite_count == 2
    assert positive.numeric_analysis is not None
    assert positive.numeric_analysis.mean == pytest.approx(1.5)
    assert positive.numeric_analysis.q1 == pytest.approx(1.25)
    assert positive.numeric_analysis.median == pytest.approx(1.5)
    assert positive.numeric_analysis.q3 == pytest.approx(1.75)
    assert negative.evidence.numeric_structure is not None
    assert negative.evidence.numeric_structure.negative_infinity_count == 1
    assert negative.numeric_analysis == positive.numeric_analysis
    assert mixed.numeric_analysis is not None
    assert mixed.numeric_analysis.minimum == 1.0
    assert mixed.numeric_analysis.maximum == 3.0
    assert mixed.evidence.numeric_structure is not None
    assert mixed.evidence.numeric_structure.positive_infinity_count == 1
    assert mixed.evidence.numeric_structure.negative_infinity_count == 1


def test_no_finite_observations_leave_every_metric_undefined():
    series = pd.Series([np.inf, -np.inf, np.nan])
    analyzed = analyze_series(series)
    described = analyzed.numeric_analysis
    structure = analyzed.evidence.numeric_structure
    assert analyzed.inferred.selected_type is SemanticType.NUMERIC
    assert analyzed.inferred.interpretation is None
    assert structure is not None and described is not None
    assert structure.finite_count == 0
    assert structure.positive_infinity_count == 1
    assert structure.negative_infinity_count == 1
    assert described.finite_count == 0
    assert described.minimum is None
    assert described.maximum is None
    assert described.mean is None
    assert described.median is None
    assert described.standard_deviation is None
    assert described.q1 is None
    assert described.q3 is None
    assert described.range is None
    assert described.interquartile_range is None


def test_one_finite_value_is_every_landmark_and_has_no_standard_deviation():
    analyzed = analyze_series(pd.Series([1.0, np.inf]))
    described = analyzed.numeric_analysis
    assert analyzed.inferred.selected_type is SemanticType.NUMERIC
    assert described is not None
    assert described.finite_count == 1
    assert described.minimum == described.maximum == 1.0
    assert described.q1 == described.median == described.q3 == 1.0
    assert described.mean == pytest.approx(1.0)
    assert described.standard_deviation is None
    assert described.range == 0.0
    assert described.interquartile_range == 0.0
    direct = collect_numeric_descriptive_analysis(pd.Series([5], dtype="int64"))
    assert direct.minimum == direct.maximum == direct.q1 == direct.median == direct.q3
    assert direct.minimum == 5
    assert type(direct.minimum) is int
    assert direct.mean == 5.0
    assert type(direct.mean) is float
    assert direct.standard_deviation is None
    assert direct.range == 0
    assert direct.interquartile_range == 0


def test_zero_population_deviation_stays_zero_and_unrepresentable_deviation_is_rejected():
    analyzed = analyze_series(pd.Series([0.0, 0.0, np.inf]))
    described = analyzed.numeric_analysis
    assert analyzed.inferred.selected_type is SemanticType.NUMERIC
    assert described is not None
    assert described.finite_count == 2
    assert described.standard_deviation == 0.0
    assert described.minimum == described.maximum == 0.0
    limit = float(np.finfo(float).max)
    with pytest.raises(ValueError, match="finite"):
        collect_numeric_descriptive_analysis(pd.Series([-limit, limit]))


def test_two_equal_finite_values_have_zero_sample_deviation():
    analyzed = analyze_series(pd.Series([1.0, 1.0, np.inf]))
    described = analyzed.numeric_analysis
    assert described is not None
    assert described.finite_count == 2
    assert described.minimum == described.maximum == 1.0
    assert described.standard_deviation == 0.0
    assert described.range == 0.0
    assert described.interquartile_range == 0.0


def test_odd_and_even_quantiles_use_one_linear_rule():
    odd = collect_numeric_descriptive_analysis(
        pd.Series([1, 2, 3, 4, 5], dtype="int64")
    )
    even = collect_numeric_descriptive_analysis(pd.Series([1, 2, 3, 4], dtype="int64"))
    pair = collect_numeric_descriptive_analysis(pd.Series([1.0, 3.0]))
    assert (odd.q1, odd.median, odd.q3) == (2, 3, 4)
    assert odd.standard_deviation == pytest.approx(_sample_std([1, 2, 3, 4, 5]))
    assert even.q1 == pytest.approx(1.75)
    assert even.median == pytest.approx(2.5)
    assert even.q3 == pytest.approx(3.25)
    assert pair.q1 == pytest.approx(1.5)
    assert pair.median == pytest.approx(2.0)
    assert pair.q3 == pytest.approx(2.5)
    assert pair.standard_deviation == pytest.approx(math.sqrt(2.0))
    oracle = np.quantile(
        np.array([1.0, 3.0, 4.0, 8.0, 10.0, 12.0]),
        [0.25, 0.5, 0.75],
        method="linear",
    )
    described = collect_numeric_descriptive_analysis(
        pd.Series([10.0, 1.0, 8.0, 3.0, 12.0, 4.0])
    )
    assert described.q1 == pytest.approx(oracle[0])
    assert described.median == pytest.approx(oracle[1])
    assert described.q3 == pytest.approx(oracle[2])
    assert (
        described.median == described.q1
        or described.q1 <= described.median <= described.q3
    )


def test_negative_zero_is_stored_as_zero_and_large_integers_stay_exact():
    signed_zero = collect_numeric_descriptive_analysis(pd.Series([-0.0, 0.0, 2.0]))
    assert signed_zero.minimum == 0.0
    assert math.copysign(1.0, signed_zero.minimum) > 0.0
    signed = collect_numeric_descriptive_analysis(
        pd.Series([np.int64(-(2**63)), np.int64(0)], dtype="int64")
    )
    assert signed.minimum == -(2**63)
    assert type(signed.minimum) is int
    assert signed.maximum == 0
    wide = collect_numeric_descriptive_analysis(
        pd.Series(np.array([np.uint64(2**63), np.uint64(2**63 + 1)]))
    )
    assert wide.minimum == 2**63
    assert wide.maximum == 2**63 + 1
    assert type(wide.minimum) is int
    assert type(wide.maximum) is int
    assert wide.minimum < wide.q1 <= wide.median <= wide.q3 < wide.maximum
    assert isinstance(wide.q1, Fraction)
    # Float64 cannot separate these two integers, so the sample deviation collapses.
    assert wide.standard_deviation == 0.0
    huge = collect_numeric_descriptive_analysis(
        pd.Series(np.array([np.uint64(0), np.uint64(2**64 - 1)]))
    )
    assert huge.minimum == 0
    assert huge.maximum == 2**64 - 1
    assert type(huge.maximum) is int
    assert huge.minimum <= huge.q1 <= huge.median <= huge.q3 <= huge.maximum


def test_extreme_floats_stay_finite_and_ordered():
    described = collect_numeric_descriptive_analysis(pd.Series([-1e308, 0.0, 1e308]))
    assert described.minimum == -1e308
    assert described.maximum == 1e308
    assert described.mean == pytest.approx(0.0)
    assert described.standard_deviation == pytest.approx(1e308)
    assert math.isfinite(described.standard_deviation or 0.0)
    assert described.minimum <= described.q1 <= described.median <= described.q3
    assert described.q3 <= described.maximum


def test_collection_does_not_mutate_or_coerce_storage():
    series = pd.Series([1, pd.NA, 4], dtype="Int64")
    before = series.copy()
    described = collect_numeric_descriptive_analysis(series)
    pd.testing.assert_series_equal(series, before)
    assert str(series.dtype) == "Int64"
    assert described.finite_count == 2
    assert described.minimum == 1
    assert described.maximum == 4
    sparse = pd.Series(pd.arrays.SparseArray([1.0, np.nan, -2.5, 0.0]))
    sparse_before = sparse.copy()
    sparse_described = collect_numeric_descriptive_analysis(sparse)
    pd.testing.assert_series_equal(sparse, sparse_before)
    assert sparse_described.finite_count == 3
    assert sparse_described.minimum == -2.5
    assert sparse_described.maximum == 1.0


def test_collector_rejects_non_numeric_storage():
    rejected = [
        pd.Series([True, False]),
        pd.Series([True, False], dtype="boolean"),
        pd.Series(["1", "2"], dtype="string"),
        pd.Series([1, "2"], dtype=object),
        pd.Series([1 + 2j, 3 + 4j]),
        pd.Series(pd.to_datetime(["2020-01-01", "2020-01-02"])),
        pd.DataFrame({"amount": [1, 2]}),
        [1, 2, 3],
        None,
    ]
    for value in rejected:
        with pytest.raises(TypeError):
            collect_numeric_descriptive_analysis(value)  # type: ignore[arg-type]


def test_descriptive_collection_runs_only_after_selected_numeric(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[pd.Series] = []
    real = column_module.collect_numeric_descriptive_analysis

    def spy(series: pd.Series) -> NumericDescriptiveAnalysis:
        calls.append(series)
        return real(series)

    original_identifier = column_module.assess_identifier_candidate
    monkeypatch.setattr(column_module, "collect_numeric_descriptive_analysis", spy)
    numeric = analyze_series(pd.Series([1, 2, 3], dtype="int64"))
    assert numeric.inferred.selected_type is SemanticType.NUMERIC
    assert numeric.numeric_analysis is not None
    assert len(calls) == 1
    calls.clear()
    untouched = (
        pd.Series([5, 5, 5], dtype="int64"),
        pd.Series([pd.NA, pd.NA], dtype="Int64"),
        pd.Series([True, False], dtype="boolean"),
        pd.Series([_UUID_A, _UUID_B], dtype="string"),
        pd.Series(["Amsterdam", "Berlin"], dtype="string"),
        pd.Series([1 + 1j, 2 + 2j]),
        pd.Series([np.nan, np.nan]),
    )
    for series in untouched:
        analyzed = analyze_series(series)
        assert analyzed.numeric_analysis is None
        assert analyzed.inferred.selected_type is not SemanticType.NUMERIC
    assert calls == []

    def supported_identifier(*_args: object, **_kwargs: object) -> CandidateAssessment:
        return CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.SUPPORTED,
            supporting_evidence=(SemanticEvidence(statement="synthetic support"),),
        )

    monkeypatch.setattr(
        column_module,
        "assess_identifier_candidate",
        supported_identifier,
    )
    ambiguous = analyze_series(pd.Series([1, 2, 3], dtype="int64"))
    assert ambiguous.inferred.resolution.status is ResolutionStatus.AMBIGUOUS
    assert ambiguous.inferred.selected_type is None
    assert ambiguous.numeric_analysis is None
    assert calls == []

    def numeric_not_supported(*_args: object, **_kwargs: object) -> CandidateAssessment:
        return CandidateAssessment(
            semantic_type=SemanticType.NUMERIC,
            disposition=CandidateDisposition.NOT_SUPPORTED,
        )

    monkeypatch.setattr(
        column_module,
        "assess_numeric_candidate",
        numeric_not_supported,
    )
    monkeypatch.setattr(
        column_module,
        "assess_identifier_candidate",
        original_identifier,
    )
    unresolved = analyze_series(pd.Series([1, 2, 3], dtype="int64"))
    assert (
        unresolved.inferred.resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    )
    assert unresolved.numeric_analysis is None
    assert calls == []


def test_binary_looking_numbers_stay_numeric_and_are_described():
    for series in (
        pd.Series([0, 1, 0, 1], dtype="int64"),
        pd.Series([0.0, 1.0, 0.0, 1.0]),
    ):
        analyzed = analyze_series(series)
        described = analyzed.numeric_analysis
        assert analyzed.inferred.selected_type is SemanticType.NUMERIC
        assert described is not None
        assert described.finite_count == 4
        assert described.minimum == 0
        assert described.maximum == 1
        assert described.mean == pytest.approx(0.5)


def test_variables_copy_descriptive_facts_and_keep_structure():
    frame = pd.DataFrame(
        {
            "amount": [-2.0, -1.5, 0.0, 4.0, np.nan],
            "group": pd.Series(pd.Categorical(["red", "red", "blue", "blue", "red"])),
            "code": pd.Series(
                [_UUID_A, _UUID_B, _UUID_A, _UUID_B, _UUID_A], dtype="string"
            ),
            "flag": pd.Series([True, False, True, False, True], dtype="boolean"),
            "constant": pd.Series([5, 5, 5, 5, 5], dtype="int64"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    amount = summary.variables[0]
    detail = amount.detail
    source = analysis.columns[0].numeric_analysis
    structure = analysis.columns[0].evidence.numeric_structure
    assert isinstance(detail, NumericVariableDetail)
    assert source is not None and structure is not None
    assert detail.descriptive == source
    assert detail.descriptive is not source
    assert detail.descriptive is not None
    assert (
        detail.finite_count == structure.finite_count == detail.descriptive.finite_count
    )
    assert detail.positive_count == structure.positive_count == 1
    assert detail.negative_count == structure.negative_count == 2
    assert detail.zero_count == structure.zero_count == 1
    assert detail.integer_like_count == structure.integer_like_count
    assert detail.descriptive.minimum == -2.0
    assert detail.descriptive.maximum == 4.0
    assert detail.descriptive.mean == pytest.approx((-2.0 - 1.5 + 4.0) / 4.0)
    assert isinstance(summary.variables[1].detail, CategoricalVariableDetail)
    assert not hasattr(summary.variables[1].detail, "descriptive")
    assert isinstance(summary.variables[2].detail, IdentifierVariableDetail)
    assert summary.variables[2].detail.uuid_count == 5
    assert summary.variables[3].selected_type is SemanticType.BOOLEAN
    assert isinstance(summary.variables[3].detail, BooleanVariableDetail)
    assert not isinstance(summary.variables[3].detail, NumericVariableDetail)
    assert summary.variables[4].selected_type is SemanticType.CONSTANT
    assert summary.variables[4].detail is None
    assert analysis.columns[3].numeric_analysis is None
    assert analysis.columns[4].numeric_analysis is None
    _walk(summary)
    _walk(analysis.columns[0].numeric_analysis)


def test_results_do_not_retain_source_arrays_or_semantic_evidence():
    analyzed = analyze_series(pd.Series([1.0, 2.0, np.inf, np.nan]))
    _walk(analyzed)
    assert "numeric_analysis" not in ColumnEvidence.__dataclass_fields__
    assert "numeric_analysis" not in InferredSemanticResult.__dataclass_fields__
    assert "range" not in NumericDescriptiveAnalysis.__dataclass_fields__
    assert "interquartile_range" not in NumericDescriptiveAnalysis.__dataclass_fields__
    semantics = Path(__file__).resolve().parents[1] / "src" / "pytics" / "semantics"
    for path in semantics.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "NumericDescriptiveAnalysis" not in text
        assert "collect_numeric_descriptive_analysis" not in text
    variables_source = Path(variables_module.__file__).read_text(encoding="utf-8")
    assert "ddof" not in variables_source
    assert "quantile" not in variables_source
    assert "np." not in variables_source
    tree = ast.parse(Path(numeric_module.__file__).read_text(encoding="utf-8"))
    modules = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]
    assert "pytics.semantics" not in modules
    assert not hasattr(pytics, "NumericDescriptiveAnalysis")
    assert not hasattr(pytics, "collect_numeric_descriptive_analysis")


def test_models_are_frozen_and_reject_inconsistent_state():
    described = _one_value()
    with pytest.raises(dataclasses.FrozenInstanceError):
        described.mean = 0.0  # type: ignore[misc]
    analyzed = analyze_series(pd.Series([1, 2, 3], dtype="int64"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        analyzed.numeric_analysis = None  # type: ignore[misc]
    with pytest.raises(ValueError, match="finite_count is 0"):
        NumericDescriptiveAnalysis(
            finite_count=0,
            minimum=0,
            maximum=None,
            mean=None,
            median=None,
            standard_deviation=None,
            q1=None,
            q3=None,
        )
    with pytest.raises(ValueError, match="one finite value"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=1,
            maximum=2,
            mean=1.0,
            median=1,
            standard_deviation=None,
            q1=1,
            q3=1,
        )
    with pytest.raises(ValueError, match="undefined for one finite"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=1,
            maximum=1,
            mean=1.0,
            median=1,
            standard_deviation=0.0,
            q1=1,
            q3=1,
        )
    with pytest.raises(ValueError, match="at least two"):
        NumericDescriptiveAnalysis(
            finite_count=2,
            minimum=1,
            maximum=2,
            mean=1.5,
            median=1.5,
            standard_deviation=None,
            q1=1.25,
            q3=1.75,
        )
    with pytest.raises(ValueError, match="cannot be negative"):
        NumericDescriptiveAnalysis(
            finite_count=2,
            minimum=1,
            maximum=2,
            mean=1.5,
            median=1.5,
            standard_deviation=-0.1,
            q1=1.25,
            q3=1.75,
        )
    with pytest.raises(ValueError, match="out of order"):
        NumericDescriptiveAnalysis(
            finite_count=3,
            minimum=0,
            maximum=10,
            mean=5.0,
            median=1.0,
            standard_deviation=1.0,
            q1=4.0,
            q3=8.0,
        )
    with pytest.raises(ValueError, match="negative zero"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=-0.0,
            maximum=-0.0,
            mean=0.0,
            median=-0.0,
            standard_deviation=None,
            q1=-0.0,
            q3=-0.0,
        )
    with pytest.raises(TypeError, match="int or a float"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=True,  # type: ignore[arg-type]
            maximum=1,
            mean=1.0,
            median=1,
            standard_deviation=None,
            q1=1,
            q3=1,
        )
    with pytest.raises(TypeError, match="int or a float"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=np.int64(5),  # type: ignore[arg-type]
            maximum=5,
            mean=5.0,
            median=5,
            standard_deviation=None,
            q1=5,
            q3=5,
        )
    with pytest.raises(ValueError, match="finite"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=1.0,
            maximum=1.0,
            mean=float("nan"),
            median=1.0,
            standard_deviation=None,
            q1=1.0,
            q3=1.0,
        )
    with pytest.raises(ValueError, match="non-negative"):
        NumericDescriptiveAnalysis(
            finite_count=-1,
            minimum=None,
            maximum=None,
            mean=None,
            median=None,
            standard_deviation=None,
            q1=None,
            q3=None,
        )
    with pytest.raises(TypeError, match="must be a float"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=5,
            maximum=5,
            mean=5,  # type: ignore[arg-type]
            median=5,
            standard_deviation=None,
            q1=5,
            q3=5,
        )
    constant = analyze_series(pd.Series([5, 5, 5], dtype="int64"))
    with pytest.raises(ValueError, match="selected"):
        ColumnAnalysis(
            position=constant.position,
            label=constant.label,
            physical=constant.physical,
            evidence=constant.evidence,
            inferred=constant.inferred,
            numeric_analysis=_one_value(),
        )
    mismatched = analyze_series(pd.Series([1, 2, 3], dtype="int64"))
    with pytest.raises(ValueError, match="finite_count"):
        ColumnAnalysis(
            position=mismatched.position,
            label=mismatched.label,
            physical=mismatched.physical,
            evidence=mismatched.evidence,
            inferred=mismatched.inferred,
            numeric_analysis=_one_value(),
        )
    with pytest.raises(ValueError, match="required when finite_count"):
        NumericDescriptiveAnalysis(
            finite_count=2,
            minimum=None,
            maximum=2,
            mean=1.5,
            median=1.5,
            standard_deviation=0.5,
            q1=1.25,
            q3=1.75,
        )
    with pytest.raises(ValueError, match="median is required"):
        NumericDescriptiveAnalysis(
            finite_count=2,
            minimum=1,
            maximum=2,
            mean=1.5,
            median=None,
            standard_deviation=0.5,
            q1=1.25,
            q3=1.75,
        )
    with pytest.raises(ValueError, match="mean is required"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=1,
            maximum=1,
            mean=None,
            median=1,
            standard_deviation=None,
            q1=1,
            q3=1,
        )
    with pytest.raises(TypeError, match="Fraction"):
        NumericDescriptiveAnalysis(
            finite_count=1,
            minimum=1,
            maximum=1,
            mean=1.0,
            median=np.float64(1.0),  # type: ignore[arg-type]
            standard_deviation=None,
            q1=1,
            q3=1,
        )
    with pytest.raises(ValueError, match="descriptive finite_count"):
        NumericVariableDetail(
            n_non_missing=3,
            finite_count=3,
            positive_count=3,
            negative_count=0,
            zero_count=0,
            positive_infinity_count=0,
            negative_infinity_count=0,
            integer_like_count=3,
            non_integer_like_count=0,
            is_non_decreasing=True,
            is_non_increasing=False,
            descriptive=_one_value(),
        )


def test_numeric_detail_may_omit_descriptive_analysis():
    analyzed = analyze_series(pd.Series([1, 2, 3], dtype="int64"), label="amount")
    column = ColumnAnalysis(
        position=0,
        label=analyzed.label,
        physical=analyzed.physical,
        evidence=analyzed.evidence,
        inferred=analyzed.inferred,
    )
    summary = build_variables_summary(
        DatasetAnalysis(
            n_rows=3,
            n_columns=1,
            n_cells=3,
            columns=(column,),
            missing_analysis=missing_analysis_for_margins(
                3,
                (column.evidence.basic.n_missing,),
            ),
            duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
        )
    )
    detail = summary.variables[0].detail
    assert isinstance(detail, NumericVariableDetail)
    assert detail.finite_count == 3
    assert detail.descriptive is None
    with pytest.raises(TypeError, match="NumericDescriptiveAnalysis"):
        NumericVariableDetail(
            n_non_missing=3,
            finite_count=3,
            positive_count=3,
            negative_count=0,
            zero_count=0,
            positive_infinity_count=0,
            negative_infinity_count=0,
            integer_like_count=3,
            non_integer_like_count=0,
            is_non_decreasing=True,
            is_non_increasing=False,
            descriptive=object(),  # type: ignore[arg-type]
        )


def test_collector_rejects_a_non_real_numeric_array(monkeypatch: pytest.MonkeyPatch):
    series = pd.Series([1.0, 2.0])

    def _list(self: pd.Series, *args: object, **kwargs: object) -> list[float]:
        del self, args, kwargs
        return [1.0, 2.0]

    monkeypatch.setattr(pd.Series, "to_numpy", _list)
    with pytest.raises(TypeError, match="real integer"):
        collect_numeric_descriptive_analysis(series)

    def _complex(self: pd.Series, *args: object, **kwargs: object) -> np.ndarray:
        del self, args, kwargs
        return np.array([1 + 0j, 2 + 0j])

    monkeypatch.setattr(pd.Series, "to_numpy", _complex)
    with pytest.raises(TypeError, match="real integer"):
        collect_numeric_descriptive_analysis(series)


def test_float_segment_guard_pulls_rounding_back_onto_the_segment():
    assert _on_segment(1.5, 1.0, 2.0) == 1.5
    assert _on_segment(0.0, 1.0, 2.0) == 1.0
    assert _on_segment(3.0, 1.0, 2.0) == 2.0
    assert _on_segment(float("inf"), 1.0, 2.0) == 1.0


def test_ambiguous_column_without_descriptive_analysis_has_no_detail():
    physical = PhysicalDtype(family=PhysicalDtypeFamily.INTEGER, dtype_name="int64")
    basic = BasicColumnEvidence(
        n_total=3,
        n_missing=0,
        n_non_missing=3,
        n_unique_non_missing=3,
    )
    supported = (
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.SUPPORTED,
            supporting_evidence=(SemanticEvidence(statement="synthetic identifier"),),
        ),
        CandidateAssessment(
            semantic_type=SemanticType.NUMERIC,
            disposition=CandidateDisposition.SUPPORTED,
            supporting_evidence=(SemanticEvidence(statement="synthetic numeric"),),
        ),
    )
    column = ColumnAnalysis(
        position=0,
        label="mixed",
        physical=physical,
        evidence=ColumnEvidence(basic=basic),
        inferred=InferredSemanticResult(
            physical=physical,
            resolution=SemanticResolution(
                status=ResolutionStatus.AMBIGUOUS,
                reason="Multiple candidates are supported: Identifier, Numeric.",
                candidates=supported,
            ),
        ),
    )
    assert column.numeric_analysis is None
    summary = build_variables_summary(
        DatasetAnalysis(
            n_rows=3,
            n_columns=1,
            n_cells=3,
            columns=(column,),
            missing_analysis=missing_analysis_for_margins(
                3,
                (column.evidence.basic.n_missing,),
            ),
            duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
        )
    )
    assert summary.variables[0].resolution_status is ResolutionStatus.AMBIGUOUS
    assert summary.variables[0].detail is None
