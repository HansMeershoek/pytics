"""TSK-021: true/false counts for a column selected as Boolean."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.boolean as boolean_module
import pytics.analysis.column as column_module
import pytics.analysis.variables as variables_module
from pytics.analysis.boolean import BooleanDescriptiveAnalysis
from pytics.analysis.boolean import collect_boolean_descriptive_analysis
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import ColumnEvidence
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from tests.missing_margins import missing_analysis_for_margins
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.variables import BooleanVariableDetail
from pytics.analysis.variables import NumericVariableDetail
from pytics.analysis.variables import VariableSummary
from pytics.analysis.variables import build_variables_summary
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus

_RETAINED = (pd.DataFrame, pd.Series, np.ndarray, np.generic)


def _counts(series: pd.Series) -> BooleanDescriptiveAnalysis:
    analyzed = analyze_series(series)
    described = analyzed.boolean_analysis
    assert described is not None
    return described


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


def test_bool_and_nullable_boolean_count_true_and_false():
    native = _counts(pd.Series([True, False, True, False]))
    nullable = _counts(pd.Series([True, False, True, False], dtype="boolean"))
    assert native == nullable
    assert native.true_count == 2
    assert native.false_count == 2
    assert native.n_non_missing == 4
    assert native.true_ratio == 0.5
    assert native.false_ratio == 0.5
    assert native.true_ratio + native.false_ratio == 1.0
    reversed_native = _counts(pd.Series([False, True, False, True]))
    assert reversed_native == native
    uneven = _counts(pd.Series([False, True, False], dtype="boolean"))
    assert uneven.true_count == 1
    assert uneven.false_count == 2
    assert uneven.true_ratio == pytest.approx(1 / 3)
    assert uneven.false_ratio == pytest.approx(2 / 3)
    assert uneven.true_ratio + uneven.false_ratio == pytest.approx(1.0)


def test_missing_values_are_excluded_from_the_boolean_denominator():
    series = pd.Series([True, pd.NA, False, None, True], dtype="boolean")
    before = series.copy()
    analyzed = analyze_series(series)
    described = analyzed.boolean_analysis
    assert analyzed.inferred.selected_type is SemanticType.BOOLEAN
    assert described is not None
    assert described.true_count == 2
    assert described.false_count == 1
    assert described.n_non_missing == 3
    assert described.true_ratio == pytest.approx(2 / 3)
    assert described.false_ratio == pytest.approx(1 / 3)
    assert described.true_ratio != pytest.approx(2 / 5)
    assert analyzed.evidence.basic.n_total == 5
    assert analyzed.evidence.basic.n_missing == 2
    assert analyzed.evidence.basic.n_non_missing == described.n_non_missing
    pd.testing.assert_series_equal(series, before)


def test_empty_and_constant_boolean_columns_are_not_described():
    cases = (
        (pd.Series([True, True], dtype="bool"), SemanticType.CONSTANT),
        (pd.Series([False, False], dtype="bool"), SemanticType.CONSTANT),
        (pd.Series([False, False], dtype="boolean"), SemanticType.CONSTANT),
        (pd.Series([pd.NA, pd.NA], dtype="boolean"), SemanticType.EMPTY),
        (pd.Series([True, pd.NA, True], dtype="boolean"), SemanticType.CONSTANT),
    )
    for series, semantic_type in cases:
        analyzed = analyze_series(series)
        assert analyzed.inferred.selected_type is semantic_type
        assert analyzed.boolean_analysis is None
        assert analyzed.numeric_analysis is None


def test_binary_looking_values_do_not_receive_boolean_analysis():
    numeric_cases = (
        pd.Series([0, 1, 0, 1], dtype="int64"),
        pd.Series([0.0, 1.0, 0.0, 1.0]),
    )
    for series in numeric_cases:
        analyzed = analyze_series(series)
        assert analyzed.inferred.selected_type is SemanticType.NUMERIC
        assert analyzed.boolean_analysis is None
        assert isinstance(analyzed.numeric_analysis, NumericDescriptiveAnalysis)
    unresolved = (
        pd.Series(["true", "false", "true"], dtype="string"),
        pd.Series(["yes", "no", "yes"], dtype="string"),
        pd.Series(["male", "female", "male"], dtype="string"),
        pd.Series([True, False, True], dtype=object),
    )
    for series in unresolved:
        analyzed = analyze_series(series)
        assert analyzed.inferred.resolution.status is (
            ResolutionStatus.INSUFFICIENT_EVIDENCE
        )
        assert analyzed.inferred.selected_type is None
        assert analyzed.boolean_analysis is None
        assert analyzed.numeric_analysis is None
    categorical = analyze_series(pd.Series(pd.Categorical([True, False, True])))
    assert categorical.inferred.selected_type is SemanticType.CATEGORICAL
    assert categorical.physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert categorical.boolean_analysis is None
    assert categorical.numeric_analysis is None


def test_boolean_collection_runs_only_after_a_boolean_selection(
    monkeypatch: pytest.MonkeyPatch,
):
    order: list[str] = []
    real_resolve = column_module.resolve_semantics
    real_boolean = column_module.collect_boolean_descriptive_analysis
    real_numeric = column_module.collect_numeric_descriptive_analysis

    def resolve_spy(*args: object, **kwargs: object):
        order.append("resolve")
        return real_resolve(*args, **kwargs)

    def boolean_spy(series: pd.Series) -> BooleanDescriptiveAnalysis:
        order.append("boolean")
        return real_boolean(series)

    def numeric_spy(series: pd.Series) -> NumericDescriptiveAnalysis:
        order.append("numeric")
        return real_numeric(series)

    monkeypatch.setattr(column_module, "resolve_semantics", resolve_spy)
    monkeypatch.setattr(
        column_module,
        "collect_boolean_descriptive_analysis",
        boolean_spy,
    )
    monkeypatch.setattr(
        column_module,
        "collect_numeric_descriptive_analysis",
        numeric_spy,
    )
    boolean = analyze_series(pd.Series([True, False, pd.NA], dtype="boolean"))
    assert boolean.inferred.selected_type is SemanticType.BOOLEAN
    assert boolean.boolean_analysis is not None
    assert order == ["resolve", "boolean"]
    order.clear()
    numeric = analyze_series(pd.Series([0, 1, 0], dtype="int64"))
    assert numeric.inferred.selected_type is SemanticType.NUMERIC
    assert numeric.boolean_analysis is None
    assert order == ["resolve", "numeric"]
    order.clear()
    untouched = (
        pd.Series([True, True], dtype="bool"),
        pd.Series([False, False], dtype="boolean"),
        pd.Series([pd.NA, pd.NA], dtype="boolean"),
        pd.Series([0.0, 1.0]),
        pd.Series(["true", "false"], dtype="string"),
        pd.Series(["yes", "no"], dtype="string"),
        pd.Series(["male", "female"], dtype="string"),
        pd.Series(pd.Categorical([True, False])),
        pd.Series([True, False], dtype=object),
    )
    for series in untouched:
        analyzed = analyze_series(series)
        assert analyzed.boolean_analysis is None
    assert "boolean" not in order


def test_sparse_boolean_storage_is_described_when_selected_boolean():
    series = pd.Series(pd.arrays.SparseArray([True, False, True, False]))
    analyzed = analyze_series(series)
    described = analyzed.boolean_analysis
    assert analyzed.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert analyzed.inferred.selected_type is SemanticType.BOOLEAN
    assert described is not None
    assert described.true_count == 2
    assert described.false_count == 2


def test_variables_expose_boolean_detail_and_keep_numeric_zero_one_numeric():
    frame = pd.DataFrame(
        {
            "flag": pd.Series([True, pd.NA, False, True], dtype="boolean"),
            "bits": pd.Series([0, 1, 0, 1], dtype="int64"),
            "same": pd.Series([True, True, True], dtype="bool"),
            "blank": pd.Series([pd.NA, pd.NA], dtype="boolean"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_variables_summary(analysis)
    flag = summary.variables[0]
    source = analysis.columns[0].boolean_analysis
    assert flag.selected_type is SemanticType.BOOLEAN
    assert isinstance(flag.detail, BooleanVariableDetail)
    assert not isinstance(flag.detail, NumericVariableDetail)
    assert source is not None
    assert flag.detail.true_count == source.true_count == 2
    assert flag.detail.false_count == source.false_count == 1
    assert flag.detail is not source
    assert flag.detail.n_non_missing == flag.n_non_missing == 3
    assert flag.n_missing == 1
    assert flag.n_total == 4
    assert flag.missing_ratio == pytest.approx(0.25)
    assert flag.detail.true_ratio == pytest.approx(2 / 3)
    assert flag.detail.false_ratio == pytest.approx(1 / 3)
    assert flag.detail.true_ratio + flag.detail.false_ratio == pytest.approx(1.0)
    bits = summary.variables[1]
    assert bits.selected_type is SemanticType.NUMERIC
    assert isinstance(bits.detail, NumericVariableDetail)
    assert bits.detail.descriptive is not None
    assert not isinstance(bits.detail, BooleanVariableDetail)
    assert analysis.columns[1].boolean_analysis is None
    assert summary.variables[2].selected_type is SemanticType.CONSTANT
    assert summary.variables[2].detail is None
    assert analysis.columns[2].boolean_analysis is None
    assert summary.variables[3].selected_type is SemanticType.EMPTY
    assert summary.variables[3].detail is None
    assert summary.variables[3].n_non_missing == 0
    assert summary.variables[3].unique_ratio_non_missing is None
    _walk(summary)
    _walk(analysis)


def test_variables_builder_does_not_rescan_boolean_values(
    monkeypatch: pytest.MonkeyPatch,
):
    frame = pd.DataFrame(
        {"flag": pd.Series([True, False, pd.NA, True], dtype="boolean")}
    )
    analysis = analyze_dataframe(frame)

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("variables builder rescanned or reanalyzed")

    monkeypatch.setattr(column_module, "analyze_series", _fail)
    monkeypatch.setattr(column_module, "collect_boolean_descriptive_analysis", _fail)
    monkeypatch.setattr(boolean_module, "collect_boolean_descriptive_analysis", _fail)
    monkeypatch.setattr(pd.Series, "dropna", _fail)
    monkeypatch.setattr(pd.Series, "isna", _fail)
    monkeypatch.setattr(pd.Series, "sum", _fail)
    summary = build_variables_summary(analysis)
    detail = summary.variables[0].detail
    assert isinstance(detail, BooleanVariableDetail)
    assert detail.true_count == 2
    assert detail.false_count == 1
    assert detail is not analysis.columns[0].boolean_analysis
    _walk(summary)


def test_results_do_not_retain_the_series_or_enter_semantics():
    analyzed = analyze_series(pd.Series([True, False, pd.NA], dtype="boolean"))
    _walk(analyzed)
    assert "boolean_analysis" not in ColumnEvidence.__dataclass_fields__
    assert "boolean_analysis" not in InferredSemanticResult.__dataclass_fields__
    assert "true_ratio" not in BooleanDescriptiveAnalysis.__dataclass_fields__
    assert "false_ratio" not in BooleanDescriptiveAnalysis.__dataclass_fields__
    assert "n_non_missing" not in BooleanDescriptiveAnalysis.__dataclass_fields__
    assert "n_non_missing" not in BooleanVariableDetail.__dataclass_fields__
    semantics = Path(__file__).resolve().parents[1] / "src" / "pytics" / "semantics"
    for path in semantics.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "BooleanDescriptiveAnalysis" not in text
        assert "collect_boolean_descriptive_analysis" not in text
    variables_source = Path(variables_module.__file__).read_text(encoding="utf-8")
    assert "collect_boolean_descriptive_analysis" not in variables_source
    assert "count_nonzero" not in variables_source
    assert "dropna" not in variables_source
    assert "import pandas" not in variables_source
    tree = ast.parse(Path(boolean_module.__file__).read_text(encoding="utf-8"))
    modules = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]
    assert "pytics.semantics" not in modules
    assert not hasattr(pytics, "BooleanDescriptiveAnalysis")
    assert not hasattr(pytics, "collect_boolean_descriptive_analysis")
    assert pytics.__all__ == ["profile", "compare"]


def test_models_are_frozen_and_reject_invalid_counts():
    described = BooleanDescriptiveAnalysis(true_count=1, false_count=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        described.true_count = 0  # type: ignore[misc]
    detail = BooleanVariableDetail(true_count=2, false_count=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        detail.false_count = 0  # type: ignore[misc]
    analyzed = analyze_series(pd.Series([True, False]))
    with pytest.raises(dataclasses.FrozenInstanceError):
        analyzed.boolean_analysis = None  # type: ignore[misc]
    invalid = (
        {"true_count": -1, "false_count": 0},
        {"true_count": 0, "false_count": -1},
        {"true_count": True, "false_count": 0},
        {"true_count": 0, "false_count": 1.0},
    )
    for values in invalid:
        with pytest.raises(ValueError, match="non-negative int"):
            BooleanDescriptiveAnalysis(**values)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="non-negative int"):
            BooleanVariableDetail(**values)  # type: ignore[arg-type]
    empty = BooleanDescriptiveAnalysis(true_count=0, false_count=0)
    assert empty.n_non_missing == 0
    assert empty.true_ratio is None
    assert empty.false_ratio is None
    empty_detail = BooleanVariableDetail(true_count=0, false_count=0)
    assert empty_detail.n_non_missing == 0
    assert empty_detail.true_ratio is None
    assert empty_detail.false_ratio is None


def test_boolean_selection_without_retained_counts_omits_detail():
    base = analyze_series(pd.Series([True, False]), label="flag")
    column = ColumnAnalysis(
        position=base.position,
        label=base.label,
        physical=base.physical,
        evidence=base.evidence,
        inferred=base.inferred,
    )
    assert column.boolean_analysis is None
    summary = build_variables_summary(
        DatasetAnalysis(
            n_rows=2,
            n_columns=1,
            n_cells=2,
            columns=(column,),
            missing_analysis=missing_analysis_for_margins(
                2,
                (column.evidence.basic.n_missing,),
            ),
            duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
        )
    )
    assert summary.variables[0].selected_type is SemanticType.BOOLEAN
    assert summary.variables[0].detail is None


def test_column_and_variable_models_reject_inconsistent_boolean_state():
    boolean = analyze_series(pd.Series([True, False, True], dtype="boolean"))
    with pytest.raises(ValueError, match="n_non_missing"):
        ColumnAnalysis(
            position=boolean.position,
            label=boolean.label,
            physical=boolean.physical,
            evidence=boolean.evidence,
            inferred=boolean.inferred,
            boolean_analysis=BooleanDescriptiveAnalysis(true_count=1, false_count=0),
        )
    numeric = analyze_series(pd.Series([0, 1], dtype="int64"))
    with pytest.raises(ValueError, match="selected semantic type is Boolean"):
        ColumnAnalysis(
            position=numeric.position,
            label=numeric.label,
            physical=numeric.physical,
            evidence=numeric.evidence,
            inferred=numeric.inferred,
            boolean_analysis=BooleanDescriptiveAnalysis(true_count=1, false_count=1),
        )
    physical = PhysicalDtype(family=PhysicalDtypeFamily.BOOLEAN, dtype_name="bool")
    with pytest.raises(ValueError, match="boolean detail counts"):
        VariableSummary(
            position=0,
            label="flag",
            physical=physical,
            resolution_status=ResolutionStatus.RESOLVED,
            selected_type=SemanticType.BOOLEAN,
            n_total=3,
            n_missing=0,
            n_non_missing=3,
            n_unique_non_missing=2,
            detail=BooleanVariableDetail(true_count=1, false_count=1),
        )
    with pytest.raises(TypeError, match="BooleanVariableDetail"):
        VariableSummary(
            position=0,
            label="flag",
            physical=physical,
            resolution_status=ResolutionStatus.RESOLVED,
            selected_type=SemanticType.BOOLEAN,
            n_total=2,
            n_missing=0,
            n_non_missing=2,
            n_unique_non_missing=2,
            detail=NumericVariableDetail(
                n_non_missing=2,
                finite_count=2,
                positive_count=1,
                negative_count=0,
                zero_count=1,
                positive_infinity_count=0,
                negative_infinity_count=0,
                integer_like_count=2,
                non_integer_like_count=0,
                is_non_decreasing=False,
                is_non_increasing=False,
            ),
        )
    with pytest.raises(TypeError, match="only to Numeric"):
        VariableSummary(
            position=0,
            label="when",
            physical=PhysicalDtype(
                family=PhysicalDtypeFamily.DATETIME,
                dtype_name="datetime64[ns]",
            ),
            resolution_status=ResolutionStatus.RESOLVED,
            selected_type=SemanticType.DATETIME,
            n_total=2,
            n_missing=0,
            n_non_missing=2,
            n_unique_non_missing=2,
            detail=BooleanVariableDetail(true_count=1, false_count=1),
        )


def test_collector_rejects_non_boolean_storage():
    rejected = [
        pd.Series([0, 1, 1], dtype="int64"),
        pd.Series([0.0, 1.0]),
        pd.Series(["true", "false"], dtype="string"),
        pd.Series(["yes", "no"], dtype="string"),
        pd.Series([True, False], dtype=object),
        pd.Series(pd.Categorical([True, False])),
        pd.Series(["male", "female"], dtype="string"),
        pd.DataFrame({"flag": [True, False]}),
        [True, False],
        None,
    ]
    for value in rejected:
        with pytest.raises(TypeError):
            collect_boolean_descriptive_analysis(value)  # type: ignore[arg-type]


def test_collector_rejects_a_non_boolean_array(monkeypatch: pytest.MonkeyPatch):
    def _object(*_args: object, **_kwargs: object) -> np.ndarray:
        return np.array([True, False], dtype=object)

    monkeypatch.setattr(pd.Series, "to_numpy", _object)
    with pytest.raises(TypeError, match="boolean values"):
        collect_boolean_descriptive_analysis(pd.Series([True, False]))
