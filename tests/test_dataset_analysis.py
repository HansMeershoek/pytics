"""TSK-017: dataset analysis and retained column evidence."""

from __future__ import annotations

import dataclasses
import inspect
import warnings

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.column as column_analysis
import pytics.analysis.dataset as dataset
import pytics.semantics.pipeline as pipeline
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import ColumnEvidence
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.missing import MissingAnalysis
from pytics.analysis.relationship import RelationshipAnalysis
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.frequency_evidence import collect_frequency_evidence
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.numeric_structure_evidence import NumericStructureEvidence
from pytics.semantics.numeric_structure_evidence import (
    collect_numeric_structure_evidence,
)
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.pipeline import infer_series_semantics
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import (
    collect_string_structure_evidence,
)

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_NO_OBSERVED_ROWS = MissingAnalysis(row_distribution=(), patterns=())
_NO_DUPLICATE_GROUPS = DuplicateAnalysis(duplicate_groups=())
_NO_RELATIONSHIPS = RelationshipAnalysis(
    n_rows=0,
    n_total_pairs=0,
    n_supported_pairs=0,
    n_analyzed_pairs=0,
    n_unimplemented_family_pairs=0,
    n_ineligible_pairs=0,
    unimplemented_family_counts=(),
    relationships=(),
)


def _numeric_column() -> ColumnAnalysis:
    return analyze_series(pd.Series([1, 2, 3]), position=0, label="amount")


def test_column_analysis_is_frozen_and_keeps_identity():
    series = pd.Series([1, 2, 3], name="customer_id")
    label = ["not", "a", "string"]
    analyzed = analyze_series(series, position=2, label=label)
    assert analyzed.position == 2
    assert analyzed.label is label
    assert analyzed.physical == classify_physical_dtype(series)
    assert analyzed.inferred.physical is analyzed.physical
    assert analyzed.evidence.basic.n_total == 3
    assert analyzed.evidence.numeric_structure is not None
    assert analyzed.evidence.numeric_structure.basic is analyzed.evidence.basic
    assert analyzed.evidence.string_structure is None
    assert analyzed.evidence.pattern is None
    assert analyzed.inferred.selected_type is SemanticType.NUMERIC
    assert not isinstance(analyzed.inferred, pd.Series)
    for field in dataclasses.fields(analyzed):
        value = getattr(analyzed, field.name)
        assert value is not series
        assert not isinstance(value, (pd.Series, pd.DataFrame, np.ndarray))
    with pytest.raises(dataclasses.FrozenInstanceError):
        analyzed.position = 0  # type: ignore[misc]


def test_bare_series_does_not_take_its_name_as_a_label():
    series = pd.Series([1, 2, 3], name="customer_id")
    analyzed = analyze_series(series)
    assert analyzed.position == 0
    assert analyzed.label is None
    assert analyzed.inferred.selected_type is SemanticType.NUMERIC


def test_column_evidence_rejects_invalid_composition():
    numbers = pd.Series([1, 2, 3])
    basic = collect_basic_column_evidence(numbers)
    other = collect_basic_column_evidence(numbers)
    physical = classify_physical_dtype(numbers)
    numeric = collect_numeric_structure_evidence(numbers, basic, physical)
    with pytest.raises(TypeError, match="basic"):
        ColumnEvidence(basic="counts")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="numeric_structure"):
        ColumnEvidence(basic=basic, numeric_structure="counts")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="numeric_structure.basic"):
        ColumnEvidence(basic=other, numeric_structure=numeric)

    texts = pd.Series(["aa", "bb"], dtype="string")
    text_basic = collect_basic_column_evidence(texts)
    text_physical = classify_physical_dtype(texts)
    structure = collect_string_structure_evidence(texts, text_basic, text_physical)
    other_structure = collect_string_structure_evidence(
        texts,
        text_basic,
        text_physical,
    )
    pattern = collect_pattern_evidence(texts, structure, text_physical)
    with pytest.raises(TypeError, match="string_structure"):
        ColumnEvidence(basic=text_basic, string_structure="counts")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="string_structure.basic"):
        ColumnEvidence(basic=other, string_structure=structure)
    with pytest.raises(TypeError, match="pattern"):
        ColumnEvidence(basic=text_basic, pattern="counts")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pattern evidence requires"):
        ColumnEvidence(basic=text_basic, pattern=pattern)
    with pytest.raises(ValueError, match="pattern.string_structure"):
        ColumnEvidence(
            basic=text_basic,
            string_structure=other_structure,
            pattern=pattern,
        )

    categories = pd.Series(pd.Categorical(["a", "b", "a"]))
    category_basic = collect_basic_column_evidence(categories)
    other_category_basic = collect_basic_column_evidence(categories)
    frequency = collect_frequency_evidence(categories, category_basic)
    with pytest.raises(TypeError, match="frequency"):
        ColumnEvidence(basic=category_basic, frequency="counts")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="frequency.basic"):
        ColumnEvidence(basic=other_category_basic, frequency=frequency)
    retained = ColumnEvidence(basic=category_basic, frequency=frequency)
    assert retained.frequency is frequency
    assert retained.frequency.basic is retained.basic


def test_column_evidence_rejects_both_numeric_and_string_families():
    empty = pd.Series([], dtype="int64")
    basic = collect_basic_column_evidence(empty)
    physical = classify_physical_dtype(empty)
    numeric = collect_numeric_structure_evidence(empty, basic, physical)
    string_structure = StringStructureEvidence(
        basic=basic,
        empty_string_count=0,
        whitespace_only_count=0,
        contains_whitespace_count=0,
        contains_alpha_count=0,
        contains_digit_count=0,
        contains_other_count=0,
        min_length=None,
        max_length=None,
    )
    with pytest.raises(ValueError, match="do not apply"):
        ColumnEvidence(
            basic=basic,
            numeric_structure=numeric,
            string_structure=string_structure,
        )


def test_column_analysis_rejects_a_mismatched_physical_dtype():
    analyzed = _numeric_column()
    other = classify_physical_dtype(pd.Series([1.0, 2.0]))
    with pytest.raises(ValueError, match="position"):
        ColumnAnalysis(
            position=-1,
            label="amount",
            physical=analyzed.physical,
            evidence=analyzed.evidence,
            inferred=analyzed.inferred,
        )
    with pytest.raises(ValueError, match="position"):
        ColumnAnalysis(
            position=True,  # type: ignore[arg-type]
            label="amount",
            physical=analyzed.physical,
            evidence=analyzed.evidence,
            inferred=analyzed.inferred,
        )
    with pytest.raises(TypeError, match="physical"):
        ColumnAnalysis(
            position=0,
            label="amount",
            physical="int64",  # type: ignore[arg-type]
            evidence=analyzed.evidence,
            inferred=analyzed.inferred,
        )
    with pytest.raises(TypeError, match="evidence"):
        ColumnAnalysis(
            position=0,
            label="amount",
            physical=analyzed.physical,
            evidence=analyzed.evidence.basic,  # type: ignore[arg-type]
            inferred=analyzed.inferred,
        )
    with pytest.raises(TypeError, match="inferred"):
        ColumnAnalysis(
            position=0,
            label="amount",
            physical=analyzed.physical,
            evidence=analyzed.evidence,
            inferred=analyzed.physical,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="inferred.physical"):
        ColumnAnalysis(
            position=0,
            label="amount",
            physical=other,
            evidence=analyzed.evidence,
            inferred=analyzed.inferred,
        )


@pytest.mark.parametrize(
    ("series", "semantic_type", "status"),
    [
        (
            pd.Series([pd.NA, pd.NA], dtype="string"),
            SemanticType.EMPTY,
            ResolutionStatus.RESOLVED,
        ),
        (
            pd.Series(["same", "same"], dtype="string"),
            SemanticType.CONSTANT,
            ResolutionStatus.RESOLVED,
        ),
        (
            pd.Series([True, False, True]),
            SemanticType.BOOLEAN,
            ResolutionStatus.RESOLVED,
        ),
        (
            pd.Series([1, 2, 3, 4]),
            SemanticType.NUMERIC,
            ResolutionStatus.RESOLVED,
        ),
        (
            pd.Series([_UUID_A, _UUID_B], dtype="string"),
            SemanticType.IDENTIFIER,
            ResolutionStatus.RESOLVED,
        ),
        (
            pd.Series(pd.Categorical(["a", "b", "a"])),
            SemanticType.CATEGORICAL,
            ResolutionStatus.RESOLVED,
        ),
        (
            pd.Series(["Amsterdam", "Berlin"], dtype="string"),
            None,
            ResolutionStatus.INSUFFICIENT_EVIDENCE,
        ),
        (
            pd.Series([1 + 2j, 3 + 4j]),
            None,
            ResolutionStatus.INSUFFICIENT_EVIDENCE,
        ),
    ],
)
def test_column_analysis_matches_series_inference(
    series: pd.Series,
    semantic_type: SemanticType | None,
    status: ResolutionStatus,
):
    analyzed = analyze_series(series)
    inferred = infer_series_semantics(series)
    assert analyzed.inferred == inferred
    assert isinstance(analyzed.inferred, InferredSemanticResult)
    assert analyzed.inferred.resolution.status is status
    assert analyzed.inferred.selected_type is semantic_type


def test_string_evidence_is_retained_by_identity():
    series = pd.Series([_UUID_A, _UUID_B], dtype="string")
    analyzed = analyze_series(series, position=1, label="id")
    evidence = analyzed.evidence
    assert evidence.string_structure is not None
    assert evidence.pattern is not None
    assert evidence.numeric_structure is None
    assert evidence.string_structure.basic is evidence.basic
    assert evidence.pattern.string_structure is evidence.string_structure
    assert analyzed.inferred.selected_type is SemanticType.IDENTIFIER
    assert not hasattr(evidence, "string_content")
    assert evidence.frequency is None


def test_structural_columns_keep_basic_evidence_only():
    cases = [
        pd.Series([pd.NA, pd.NA], dtype="string"),
        pd.Series(["same", "same"], dtype="string"),
        pd.Series([True, False, pd.NA], dtype="boolean"),
        pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01"])),
        pd.Series(pd.to_timedelta(["1 day", "2 days"])),
    ]
    for series in cases:
        analyzed = analyze_series(series)
        assert analyzed.evidence.basic is not None
        assert analyzed.evidence.numeric_structure is None
        assert analyzed.evidence.string_structure is None
        assert analyzed.evidence.pattern is None
        assert analyzed.evidence.frequency is None
        assert analyzed.numeric_analysis is None
        assert analyzed.inferred.interpretation is not None


def test_dataset_analysis_rejects_inconsistent_records():
    column = _numeric_column()
    with pytest.raises(ValueError, match="n_rows"):
        DatasetAnalysis(
            n_rows=True,  # type: ignore[arg-type]
            n_columns=0,
            n_cells=0,
            columns=(),
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(ValueError, match="n_cells"):
        DatasetAnalysis(
            n_rows=3,
            n_columns=1,
            n_cells=2,
            columns=(column,),
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(TypeError, match="tuple"):
        DatasetAnalysis(
            n_rows=3,
            n_columns=1,
            n_cells=3,
            columns=[column],  # type: ignore[arg-type]
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(ValueError, match="one record"):
        DatasetAnalysis(
            n_rows=3,
            n_columns=0,
            n_cells=0,
            columns=(column,),
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(TypeError, match="ColumnAnalysis"):
        DatasetAnalysis(
            n_rows=0,
            n_columns=1,
            n_cells=0,
            columns=("column",),  # type: ignore[arg-type]
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    shifted = analyze_series(pd.Series([1, 2, 3]), position=1, label="amount")
    with pytest.raises(ValueError, match="column position"):
        DatasetAnalysis(
            n_rows=3,
            n_columns=1,
            n_cells=3,
            columns=(shifted,),
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(ValueError, match="n_total"):
        DatasetAnalysis(
            n_rows=2,
            n_columns=1,
            n_cells=2,
            columns=(column,),
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(dataclasses.FrozenInstanceError):
        DatasetAnalysis(
            n_rows=0,
            n_columns=0,
            n_cells=0,
            columns=(),
            missing_analysis=_NO_OBSERVED_ROWS,
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        ).n_rows = 1  # type: ignore[misc]


def test_dataset_facts_for_a_rectangular_frame():
    frame = pd.DataFrame(
        {
            "a": pd.Series([1, pd.NA, 3], dtype="Int64"),
            "b": pd.Series(["x", "y", pd.NA], dtype="string"),
        }
    )
    analyzed = analyze_dataframe(frame)
    assert analyzed.n_rows == 3
    assert analyzed.n_columns == 2
    assert analyzed.n_cells == 6
    assert analyzed.n_missing_cells == 2
    assert analyzed.n_non_missing_cells == 4
    assert analyzed.missing_ratio == pytest.approx(2 / 6)
    stored = {field.name for field in dataclasses.fields(analyzed)}
    assert stored == {
        "n_rows",
        "n_columns",
        "n_cells",
        "columns",
        "missing_analysis",
        "duplicate_analysis",
        "relationship_analysis",
        "target_analysis",
    }
    assert analyzed.target_analysis is None
    assert isinstance(analyzed.missing_analysis, MissingAnalysis)
    assert isinstance(analyzed.columns, tuple)


def test_dataset_facts_for_zero_size_frames():
    empty = analyze_dataframe(pd.DataFrame())
    assert (empty.n_rows, empty.n_columns, empty.n_cells) == (0, 0, 0)
    assert empty.columns == ()
    assert empty.n_missing_cells == 0
    assert empty.n_non_missing_cells == 0
    assert empty.missing_ratio is None

    zero_rows = analyze_dataframe(
        pd.DataFrame(
            {
                "amount": pd.Series(dtype="int64"),
                "city": pd.Series(dtype="string"),
            }
        )
    )
    assert (zero_rows.n_rows, zero_rows.n_columns, zero_rows.n_cells) == (0, 2, 0)
    assert [column.label for column in zero_rows.columns] == ["amount", "city"]
    assert [column.position for column in zero_rows.columns] == [0, 1]
    assert all(
        column.inferred.selected_type is SemanticType.EMPTY
        for column in zero_rows.columns
    )
    assert zero_rows.columns[1].evidence.string_structure is None
    assert zero_rows.n_missing_cells == 0
    assert zero_rows.missing_ratio is None

    zero_columns = analyze_dataframe(pd.DataFrame(index=[0, 1, 2]))
    assert (zero_columns.n_rows, zero_columns.n_columns, zero_columns.n_cells) == (
        3,
        0,
        0,
    )
    assert zero_columns.columns == ()
    assert zero_columns.n_missing_cells == 0
    assert zero_columns.n_non_missing_cells == 0
    assert zero_columns.missing_ratio is None


def test_complete_and_fully_missing_frames_use_defined_ratios():
    complete = analyze_dataframe(pd.DataFrame({"a": [1, 2], "b": [3, 4]}))
    assert complete.n_missing_cells == 0
    assert complete.missing_ratio == 0.0
    missing = analyze_dataframe(
        pd.DataFrame(
            {
                "a": pd.Series([pd.NA, pd.NA], dtype="Int64"),
                "b": pd.Series([pd.NA, pd.NA], dtype="string"),
            }
        )
    )
    assert missing.n_missing_cells == 4
    assert missing.n_non_missing_cells == 0
    assert missing.missing_ratio == 1.0


def test_mixed_frame_preserves_order_and_current_semantics():
    frame = pd.DataFrame(
        {
            "ints": pd.Series([1, 2, pd.NA], dtype="Int64"),
            "floats": pd.Series([1.5, np.nan, 2.5]),
            "flags": pd.Series([True, False, True], dtype="boolean"),
            "when": pd.to_datetime(
                ["2020-01-01", "2020-06-01", "2021-01-01"],
                utc=True,
            ),
            "span": pd.to_timedelta(["1 day", "2 days", "3 days"]),
            "ids": pd.Series([_UUID_A, _UUID_B, _UUID_A], dtype="string"),
            "cities": pd.Series(["Amsterdam", "Berlin", pd.NA], dtype="string"),
            "labels": pd.Categorical(
                ["red", "blue", "red"],
                categories=["red", "blue"],
                ordered=True,
            ),
        }
    )
    analyzed = analyze_dataframe(frame)
    assert analyzed.n_rows == 3
    assert analyzed.n_columns == 8
    assert analyzed.n_cells == 24
    assert [column.label for column in analyzed.columns] == list(frame.columns)
    assert [column.position for column in analyzed.columns] == list(range(8))
    expected = {
        "ints": (PhysicalDtypeFamily.INTEGER, SemanticType.NUMERIC),
        "floats": (PhysicalDtypeFamily.FLOATING, SemanticType.NUMERIC),
        "flags": (PhysicalDtypeFamily.BOOLEAN, SemanticType.BOOLEAN),
        "when": (PhysicalDtypeFamily.DATETIME_TZ_AWARE, SemanticType.DATETIME),
        "span": (PhysicalDtypeFamily.TIMEDELTA, SemanticType.TIMEDELTA),
        "ids": (PhysicalDtypeFamily.STRING, SemanticType.IDENTIFIER),
        "cities": (PhysicalDtypeFamily.STRING, None),
        "labels": (PhysicalDtypeFamily.CATEGORICAL, SemanticType.CATEGORICAL),
    }
    for column, series in zip(analyzed.columns, (frame.iloc[:, i] for i in range(8))):
        family, semantic_type = expected[column.label]
        assert column.physical.family is family
        assert column.inferred == infer_series_semantics(series)
        assert column.inferred.selected_type is semantic_type
    assert analyzed.columns[0].evidence.numeric_structure is not None
    assert analyzed.columns[0].evidence.string_structure is None
    assert analyzed.columns[1].evidence.numeric_structure is not None
    assert analyzed.columns[2].evidence.numeric_structure is None
    assert analyzed.columns[5].evidence.string_structure is not None
    assert analyzed.columns[5].evidence.pattern is not None
    assert (
        analyzed.columns[5].evidence.pattern.string_structure
        is analyzed.columns[5].evidence.string_structure
    )
    assert analyzed.columns[6].evidence.pattern is not None
    assert analyzed.columns[6].inferred.resolution.status is (
        ResolutionStatus.INSUFFICIENT_EVIDENCE
    )
    assert analyzed.columns[7].evidence.string_structure is None
    assert analyzed.columns[7].evidence.frequency is not None
    assert (
        analyzed.columns[7].evidence.frequency.basic
        is analyzed.columns[7].evidence.basic
    )
    assert analyzed.columns[7].physical.categorical_ordered is True
    assert analyzed.columns[0].evidence.frequency is None
    assert analyzed.columns[2].evidence.frequency is None
    assert analyzed.columns[5].evidence.frequency is None
    assert analyzed.columns[6].evidence.frequency is None
    assert analyzed.n_missing_cells == 3
    assert analyzed.missing_ratio == pytest.approx(3 / 24)


def test_duplicate_labels_stay_independent_records():
    left = pd.Series([1, 3], dtype="int64")
    right = pd.Series(["Amsterdam", "Berlin"], dtype="string")
    frame = pd.concat([left, right], axis=1)
    frame.columns = ["x", "x"]
    analyzed = analyze_dataframe(frame)
    assert len(analyzed.columns) == 2
    assert [column.position for column in analyzed.columns] == [0, 1]
    assert [column.label for column in analyzed.columns] == ["x", "x"]
    assert analyzed.columns[0] is not analyzed.columns[1]
    assert analyzed.columns[0].inferred.selected_type is SemanticType.NUMERIC
    assert analyzed.columns[1].inferred.resolution.status is (
        ResolutionStatus.INSUFFICIENT_EVIDENCE
    )
    assert analyzed.columns[0].evidence.numeric_structure is not None
    assert analyzed.columns[1].evidence.string_structure is not None
    assert analyzed.columns[0].evidence.basic is not analyzed.columns[1].evidence.basic


def test_non_string_labels_are_preserved():
    frame = pd.DataFrame([[1, "a"], [2, "b"]])
    frame.columns = [42, ("group", "value")]
    analyzed = analyze_dataframe(frame)
    assert analyzed.columns[0].label == frame.columns[0]
    assert type(analyzed.columns[0].label) is type(frame.columns[0])
    assert not isinstance(analyzed.columns[0].label, str)
    assert analyzed.columns[1].label == ("group", "value")
    assert isinstance(analyzed.columns[1].label, tuple)
    assert analyzed.columns[1].label != "group.value"


def test_multiindex_labels_are_not_flattened():
    columns = pd.MultiIndex.from_tuples(
        [("group", "value"), ("group", "value")],
    )
    frame = pd.DataFrame([[1, "Amsterdam"], [2, "Berlin"]], columns=columns)
    analyzed = analyze_dataframe(frame)
    assert len(analyzed.columns) == 2
    assert analyzed.columns[0].label == ("group", "value")
    assert analyzed.columns[1].label == ("group", "value")
    assert analyzed.columns[0].position == 0
    assert analyzed.columns[1].position == 1
    assert not isinstance(analyzed.columns[0].label, str)
    assert analyzed.columns[0].inferred.selected_type is SemanticType.NUMERIC
    assert analyzed.columns[1].inferred.resolution.status is (
        ResolutionStatus.INSUFFICIENT_EVIDENCE
    )


def test_dataframe_analysis_calls_column_analysis_once(
    monkeypatch: pytest.MonkeyPatch,
):
    returned = []
    real = dataset.analyze_series

    def spy(series: pd.Series, **kwargs: object) -> ColumnAnalysis:
        value = real(series, **kwargs)
        returned.append(value)
        return value

    basic_calls = []
    real_basic = column_analysis.collect_basic_column_evidence

    def basic_spy(series: pd.Series):
        basic_calls.append(series)
        return real_basic(series)

    physical_calls = []
    real_physical = column_analysis.classify_physical_dtype

    def physical_spy(source: object):
        physical_calls.append(source)
        return real_physical(source)

    numeric_calls = []
    real_numeric = column_analysis.collect_numeric_structure_evidence

    def numeric_spy(series, basic, physical):
        numeric_calls.append(series)
        return real_numeric(series, basic, physical)

    string_calls = []
    real_string = column_analysis.collect_string_structure_evidence

    def string_spy(series, basic, physical):
        string_calls.append(series)
        return real_string(series, basic, physical)

    def wrapper_must_not_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("infer_series_semantics ran")

    monkeypatch.setattr(dataset, "analyze_series", spy)
    monkeypatch.setattr(column_analysis, "collect_basic_column_evidence", basic_spy)
    monkeypatch.setattr(column_analysis, "classify_physical_dtype", physical_spy)
    monkeypatch.setattr(
        column_analysis,
        "collect_numeric_structure_evidence",
        numeric_spy,
    )
    monkeypatch.setattr(
        column_analysis,
        "collect_string_structure_evidence",
        string_spy,
    )
    monkeypatch.setattr(pipeline, "infer_series_semantics", wrapper_must_not_run)
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3],
            "city": pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string"),
            "flag": [True, False, True],
            "same": pd.Series(["x", "x", "x"], dtype="string"),
        }
    )
    analyzed = analyze_dataframe(frame)
    assert returned == list(analyzed.columns)
    assert len(basic_calls) == 4
    assert len(physical_calls) == 4
    assert len(numeric_calls) == 1
    assert len(string_calls) == 1
    assert analyzed.columns[2].evidence.numeric_structure is None
    assert analyzed.columns[3].evidence.string_structure is None


def test_analysis_does_not_mutate_the_dataframe():
    frame = pd.DataFrame(
        {
            "ints": pd.Series([1, pd.NA], dtype="Int64"),
            "flags": pd.Series([True, False], dtype="boolean"),
            "when": pd.to_datetime(["2020-01-01", "2020-06-01"], utc=True),
            "labels": pd.Categorical(["b", "a"], categories=["a", "b"], ordered=True),
            "cities": pd.Series(["Amsterdam", "Berlin"], dtype="string"),
        }
    )
    frame.index = pd.Index([4, 9], name="row")
    frame.index.name = "row"
    before = frame.copy(deep=True)
    analyze_dataframe(frame)
    pd.testing.assert_frame_equal(frame, before)
    assert frame.index.equals(before.index)
    assert frame.index.name == "row"
    assert list(frame.columns) == list(before.columns)
    assert frame["labels"].cat.ordered is True
    assert list(frame["labels"].cat.categories) == ["a", "b"]
    assert frame["when"].dt.tz == before["when"].dt.tz


def test_analysis_does_not_retain_source_values():
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3],
            "city": pd.Series(["Amsterdam", "Berlin", "Paris"], dtype="string"),
        }
    )
    analyzed = analyze_dataframe(frame)
    assert not isinstance(analyzed, (pd.DataFrame, pd.Series))
    for column in analyzed.columns:
        for value in (
            column.label,
            column.physical,
            column.evidence,
            column.evidence.basic,
            column.evidence.numeric_structure,
            column.evidence.string_structure,
            column.evidence.pattern,
            column.inferred,
            column.numeric_analysis,
            column.boolean_analysis,
        ):
            assert not isinstance(value, (pd.DataFrame, pd.Series, np.ndarray))
    assert not isinstance(
        analyzed.missing_analysis,
        (pd.DataFrame, pd.Series, np.ndarray),
    )
    for pattern in analyzed.missing_analysis.patterns:
        assert not isinstance(pattern.positions, (pd.Index, np.ndarray))
    assert not any(
        isinstance(value, NumericStructureEvidence) and hasattr(value, "values")
        for value in (column.evidence.numeric_structure for column in analyzed.columns)
    )


def test_dataset_entry_rejects_non_dataframes():
    values = [
        pd.Series([1, 2]),
        {"a": [1, 2]},
        [{"a": 1}],
        np.array([[1, 2], [3, 4]]),
        None,
    ]
    for value in values:
        with pytest.raises(TypeError, match="pandas DataFrame"):
            analyze_dataframe(value)  # type: ignore[arg-type]


def test_column_entry_rejects_non_series():
    frame = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(TypeError, match="pandas Series"):
        analyze_series(frame)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="position"):
        analyze_series(pd.Series([1, 2]), position=-1)
    with pytest.raises(ValueError, match="position"):
        analyze_series(pd.Series([1, 2]), position=True)  # type: ignore[arg-type]


def test_empty_duplicate_and_unresolved_frames_do_not_warn():
    duplicate = pd.DataFrame([[1, "a"]], columns=["x", "x"])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        analyze_dataframe(pd.DataFrame())
        analyze_dataframe(duplicate)
        analyze_series(pd.Series(["Amsterdam", "Berlin"], dtype="string"))


def test_public_api_and_analysis_source_stay_internal():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "analyze_dataframe")
    assert not hasattr(pytics, "analyze_series")
    assert not hasattr(pytics, "DatasetAnalysis")
    column_source = inspect.getsource(column_analysis)
    dataset_source = inspect.getsource(dataset)
    pipeline_source = inspect.getsource(pipeline)
    source = "\n".join((column_source, dataset_source, pipeline_source))
    for token in (
        "memory_usage",
        "drop_duplicates",
        "tqdm",
        "ThreadPool",
        "ProcessPool",
        "joblib",
        "warnings",
        ".copy(",
        "collect_string_content_evidence",
    ):
        assert token not in source
    assert "collect_frequency_evidence" in column_source
    assert "collect_frequency_evidence" not in dataset_source
    assert "collect_frequency_evidence" not in pipeline_source


def test_dataset_columns_are_not_keyed_by_label():
    frame = pd.DataFrame([[1, 2], [3, 4]], columns=["x", "x"])
    analyzed = analyze_dataframe(frame)
    assert not isinstance(analyzed.columns, dict)
    assert analyzed.columns[0].evidence.basic.n_unique_non_missing == 2
    assert analyzed.columns[1].evidence.basic.n_unique_non_missing == 2
    assert analyzed.columns[0].evidence.numeric_structure is not None
    assert analyzed.columns[0].evidence.numeric_structure.finite_count == 2
