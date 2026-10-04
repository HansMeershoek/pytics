"""TSK-018: dataset overview aggregated from dataset analysis."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
from typing import Optional
from typing import Tuple

import pandas as pd
import pytest

import pytics
import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.overview as overview_module
import pytics.semantics.column_evidence as basic_evidence
import pytics.semantics.frequency_evidence as frequency_evidence
import pytics.semantics.numeric_structure_evidence as numeric_evidence
import pytics.semantics.pattern_evidence as pattern_evidence
import pytics.semantics.physical as physical
import pytics.semantics.pipeline as pipeline
import pytics.semantics.resolution as resolution_module
import pytics.semantics.string_structure_evidence as string_evidence
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import ColumnEvidence
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.relationship import relationship_analysis_for_columns
from tests.missing_margins import missing_analysis_for_margins
from pytics.analysis.overview import ColumnRef
from pytics.analysis.overview import DatasetOverview
from pytics.analysis.overview import SemanticTypeCount
from pytics.analysis.overview import build_dataset_overview
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.resolution import SemanticResolution

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_UUID_C = "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
_UUID_D = "6ba7b812-9dad-11d1-80b4-00c04fd430c8"

_NOTABLE = (
    SemanticType.EMPTY,
    SemanticType.CONSTANT,
    SemanticType.IDENTIFIER,
)


def _overview(frame: pd.DataFrame) -> DatasetOverview:
    return build_dataset_overview(analyze_dataframe(frame))


def _type_counts(overview: DatasetOverview) -> dict:
    return {item.semantic_type: item.count for item in overview.semantic_type_counts}


def _assert_invariants(overview: DatasetOverview) -> None:
    resolved = overview.resolved_column_count
    insufficient = overview.insufficient_evidence_column_count
    ambiguous = overview.ambiguous_column_count
    assert resolved + insufficient + ambiguous == overview.n_columns
    assert sum(item.count for item in overview.semantic_type_counts) == resolved
    assert overview.empty_column_count <= resolved
    assert overview.constant_column_count <= resolved
    assert overview.identifier_column_count <= resolved
    assert overview.empty_column_count == len(overview.empty_columns)
    assert overview.constant_column_count == len(overview.constant_columns)
    assert overview.identifier_column_count == len(overview.identifier_columns)
    assert overview.insufficient_evidence_column_count == len(
        overview.insufficient_evidence_columns
    )
    assert overview.ambiguous_column_count == len(overview.ambiguous_columns)
    assert overview.n_missing_cells + overview.n_non_missing_cells == overview.n_cells
    if overview.n_cells == 0:
        assert overview.missing_ratio is None
        assert overview.completeness_ratio is None
    else:
        assert overview.missing_ratio == pytest.approx(
            overview.n_missing_cells / overview.n_cells
        )
        assert overview.completeness_ratio == pytest.approx(
            overview.n_non_missing_cells / overview.n_cells
        )
        assert overview.missing_ratio + overview.completeness_ratio == pytest.approx(1)
        assert 0.0 <= overview.missing_ratio <= 1.0
        assert 0.0 <= overview.completeness_ratio <= 1.0
    assert overview.n_excess_duplicate_rows == (
        overview.n_rows - overview.n_unique_rows
    )
    assert 0 <= overview.n_unique_rows <= overview.n_rows
    if overview.n_rows == 0:
        assert overview.unique_row_ratio is None
        assert overview.excess_duplicate_row_ratio is None
    else:
        assert overview.n_unique_rows >= 1
        assert overview.unique_row_ratio == pytest.approx(
            overview.n_unique_rows / overview.n_rows
        )
        assert overview.excess_duplicate_row_ratio == pytest.approx(
            overview.n_excess_duplicate_rows / overview.n_rows
        )
    if overview.n_columns == 0:
        assert overview.semantic_resolution_ratio is None
    else:
        assert overview.semantic_resolution_ratio == pytest.approx(
            resolved / overview.n_columns
        )
        assert 0.0 <= overview.semantic_resolution_ratio <= 1.0
    indexes = [
        list(SemanticType).index(item.semantic_type)
        for item in overview.semantic_type_counts
    ]
    assert indexes == sorted(indexes)
    assert len(indexes) == len(set(indexes))
    assert all(item.count > 0 for item in overview.semantic_type_counts)
    seen = set()
    for group in (
        overview.insufficient_evidence_columns,
        overview.ambiguous_columns,
        overview.empty_columns,
        overview.constant_columns,
        overview.identifier_columns,
    ):
        positions = [ref.position for ref in group]
        assert positions == sorted(positions)
        assert len(positions) == len(set(positions))
        assert seen.isdisjoint(positions)
        seen.update(positions)
        for ref in group:
            assert 0 <= ref.position < overview.n_columns
    for semantic_type in _NOTABLE:
        grouped = {
            SemanticType.EMPTY: overview.empty_column_count,
            SemanticType.CONSTANT: overview.constant_column_count,
            SemanticType.IDENTIFIER: overview.identifier_column_count,
        }[semantic_type]
        assert _type_counts(overview).get(semantic_type, 0) == grouped


def _mixed_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "empty_col": pd.Series([None, None, None, None], dtype="object"),
            "constant_col": pd.Series([5, 5, 5, 5], dtype="int64"),
            "flag": pd.Series([True, False, True, False]),
            "when": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-06-01", "2021-01-01"]
            ),
            "span": pd.to_timedelta(["1 days", "2 days", "3 days", "4 days"]),
            "amount": pd.Series([1.0, 2.0, None, 4.0]),
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C, _UUID_D], dtype="string"),
            "group": pd.Series(pd.Categorical(["a", "b", "a", "b"])),
            "note": pd.Series(["alpha", "beta", "gamma", "delta"], dtype="string"),
            "wave": pd.Series([1 + 1j, 2 + 2j, 3 + 3j, 4 + 4j]),
        }
    )


def _physical() -> PhysicalDtype:
    return PhysicalDtype(family=PhysicalDtypeFamily.OBJECT, dtype_name="object")


def _evidence(n_rows: int, n_missing: int, n_unique: int) -> ColumnEvidence:
    return ColumnEvidence(
        basic=BasicColumnEvidence(
            n_total=n_rows,
            n_missing=n_missing,
            n_non_missing=n_rows - n_missing,
            n_unique_non_missing=n_unique,
        )
    )


def _supported(semantic_type: SemanticType) -> CandidateAssessment:
    return CandidateAssessment(
        semantic_type=semantic_type,
        disposition=CandidateDisposition.SUPPORTED,
        supporting_evidence=(SemanticEvidence(statement="synthetic support"),),
    )


def _resolution(
    status: ResolutionStatus,
    semantic_type: Optional[SemanticType],
    physical: PhysicalDtype,
) -> SemanticResolution:
    if status is ResolutionStatus.RESOLVED:
        if semantic_type in (
            SemanticType.EMPTY,
            SemanticType.CONSTANT,
            SemanticType.BOOLEAN,
            SemanticType.DATETIME,
            SemanticType.TIMEDELTA,
        ):
            interpretation = SemanticInterpretation(
                semantic_type=semantic_type,
                confidence=Confidence.HIGH,
                source=InferenceSource.INFERRED,
                physical=physical,
                evidence=(SemanticEvidence(statement="synthetic structural"),),
            )
            return SemanticResolution(
                status=status,
                reason=(
                    f"Structural interpretation {semantic_type.name.title()} "
                    "takes precedence."
                ),
                selected_type=semantic_type,
                structural_interpretation=interpretation,
            )
        return SemanticResolution(
            status=status,
            reason=f"Exactly one candidate is supported: {semantic_type.name.title()}.",
            candidates=(_supported(semantic_type),),
            selected_type=semantic_type,
        )
    if status is ResolutionStatus.INSUFFICIENT_EVIDENCE:
        return SemanticResolution(status=status, reason="No candidate is supported.")
    return SemanticResolution(
        status=status,
        reason="Multiple candidates are supported: Identifier, Numeric.",
        candidates=(
            _supported(SemanticType.IDENTIFIER),
            _supported(SemanticType.NUMERIC),
        ),
    )


def _column(
    position: int,
    label: object,
    *,
    n_rows: int,
    status: ResolutionStatus = ResolutionStatus.RESOLVED,
    semantic_type: Optional[SemanticType] = None,
    n_missing: int = 0,
    n_unique: Optional[int] = None,
) -> ColumnAnalysis:
    physical = _physical()
    if n_unique is None:
        n_unique = 0 if n_missing == n_rows else 2
    inferred = InferredSemanticResult(
        physical=physical,
        resolution=_resolution(status, semantic_type, physical),
    )
    return ColumnAnalysis(
        position=position,
        label=label,
        physical=physical,
        evidence=_evidence(n_rows, n_missing, n_unique),
        inferred=inferred,
    )


def _manual_analysis(
    columns: Tuple[ColumnAnalysis, ...], n_rows: int
) -> DatasetAnalysis:
    n_columns = len(columns)
    return DatasetAnalysis(
        n_rows=n_rows,
        n_columns=n_columns,
        n_cells=n_rows * n_columns,
        columns=columns,
        missing_analysis=missing_analysis_for_margins(
            n_rows,
            tuple(column.evidence.basic.n_missing for column in columns),
        ),
        duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
        relationship_analysis=relationship_analysis_for_columns(
            columns,
            n_rows=n_rows,
        ),
    )


def _direct_overview(**overrides: object) -> DatasetOverview:
    values = {
        "n_rows": 1,
        "n_columns": 1,
        "n_cells": 1,
        "n_missing_cells": 0,
        "n_non_missing_cells": 1,
        "n_unique_rows": 1,
        "n_excess_duplicate_rows": 0,
        "semantic_type_counts": (SemanticTypeCount(SemanticType.NUMERIC, 1),),
        "insufficient_evidence_columns": (),
        "ambiguous_columns": (),
        "empty_columns": (),
        "constant_columns": (),
        "identifier_columns": (),
    }
    values.update(overrides)
    return DatasetOverview(**values)  # type: ignore[arg-type]


def test_ordinary_populated_dataset_copies_dimensions_and_cell_counts():
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3, 4],
            "weight": [1.0, None, 3.0, 4.0],
            "note": ["alpha", "beta", "gamma", "delta"],
        }
    )
    analysis = analyze_dataframe(frame)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert overview.n_rows == 4
    assert overview.n_columns == 3
    assert overview.n_cells == 12
    assert overview.n_rows == analysis.n_rows
    assert overview.n_columns == analysis.n_columns
    assert overview.n_cells == analysis.n_cells
    assert overview.n_missing_cells == analysis.n_missing_cells == 1
    assert overview.n_non_missing_cells == analysis.n_non_missing_cells == 11
    assert overview.missing_ratio == pytest.approx(1 / 12)
    assert overview.completeness_ratio == pytest.approx(11 / 12)


def test_complete_dataset_is_separate_from_semantic_resolution():
    overview = _overview(
        pd.DataFrame(
            {
                "amount": [1, 2, 3],
                "note": ["alpha", "beta", "gamma"],
            }
        )
    )
    _assert_invariants(overview)
    assert overview.n_missing_cells == 0
    assert overview.n_non_missing_cells == overview.n_cells
    assert overview.missing_ratio == 0.0
    assert overview.completeness_ratio == 1.0
    assert overview.resolved_column_count == 1
    assert overview.insufficient_evidence_column_count == 1
    assert overview.semantic_resolution_ratio == pytest.approx(0.5)
    assert _type_counts(overview) == {SemanticType.NUMERIC: 1}


def test_partially_missing_dataset_does_not_mark_numeric_empty():
    overview = _overview(
        pd.DataFrame(
            {
                "amount": [1.0, None, 3.0, 4.0],
                "flag": [True, False, True, False],
            }
        )
    )
    _assert_invariants(overview)
    assert overview.n_cells == 8
    assert overview.n_missing_cells == 1
    assert overview.n_non_missing_cells == 7
    assert overview.missing_ratio == pytest.approx(0.125)
    assert overview.completeness_ratio == pytest.approx(0.875)
    assert overview.empty_column_count == 0
    assert _type_counts(overview)[SemanticType.NUMERIC] == 1
    assert _type_counts(overview)[SemanticType.BOOLEAN] == 1


def test_all_missing_populated_dataset_uses_column_semantics():
    overview = _overview(
        pd.DataFrame(
            {
                "left": pd.Series([None, None, None], dtype="object"),
                "right": pd.Series([None, None, None], dtype="float64"),
            }
        )
    )
    _assert_invariants(overview)
    assert overview.n_rows == 3
    assert overview.n_columns == 2
    assert overview.n_cells == 6
    assert overview.n_missing_cells == 6
    assert overview.n_non_missing_cells == 0
    assert overview.missing_ratio == 1.0
    assert overview.completeness_ratio == 0.0
    assert overview.resolved_column_count == 2
    assert overview.empty_column_count == 2
    assert _type_counts(overview) == {SemanticType.EMPTY: 2}
    assert [ref.label for ref in overview.empty_columns] == ["left", "right"]


def test_zero_by_zero_dataset_leaves_both_ratios_undefined():
    overview = _overview(pd.DataFrame())
    _assert_invariants(overview)
    assert overview.n_rows == 0
    assert overview.n_columns == 0
    assert overview.n_cells == 0
    assert overview.n_missing_cells == 0
    assert overview.n_non_missing_cells == 0
    assert overview.resolved_column_count == 0
    assert overview.insufficient_evidence_column_count == 0
    assert overview.ambiguous_column_count == 0
    assert overview.semantic_type_counts == ()
    assert overview.semantic_resolution_ratio is None
    assert overview.missing_ratio is None
    assert overview.completeness_ratio is None
    assert overview.n_unique_rows == 0
    assert overview.n_excess_duplicate_rows == 0
    assert overview.unique_row_ratio is None
    assert overview.excess_duplicate_row_ratio is None


def test_zero_row_schema_is_resolved_empty_without_cell_ratios():
    frame = pd.DataFrame(
        {
            "amount": pd.Series(dtype="int64"),
            "note": pd.Series(dtype="string"),
            "flag": pd.Series(dtype="boolean"),
            "when": pd.Series(dtype="datetime64[ns]"),
        }
    )
    analysis = analyze_dataframe(frame)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert overview.n_rows == 0
    assert overview.n_unique_rows == 0
    assert overview.n_excess_duplicate_rows == 0
    assert overview.unique_row_ratio is None
    assert overview.n_columns == 4
    assert overview.n_cells == 0
    assert overview.missing_ratio is None
    assert overview.completeness_ratio is None
    assert overview.resolved_column_count == 4
    assert overview.empty_column_count == 4
    assert overview.semantic_resolution_ratio == 1.0
    assert _type_counts(overview) == {SemanticType.EMPTY: 4}
    assert [column.inferred.selected_type for column in analysis.columns] == [
        SemanticType.EMPTY,
        SemanticType.EMPTY,
        SemanticType.EMPTY,
        SemanticType.EMPTY,
    ]
    assert [ref.position for ref in overview.empty_columns] == [0, 1, 2, 3]


def test_rows_without_columns_have_no_resolution_ratio():
    overview = _overview(pd.DataFrame(index=range(5)))
    _assert_invariants(overview)
    assert overview.n_rows == 5
    assert overview.n_unique_rows == 1
    assert overview.n_excess_duplicate_rows == 4
    assert overview.unique_row_ratio == pytest.approx(1 / 5)
    assert overview.excess_duplicate_row_ratio == pytest.approx(4 / 5)
    assert overview.n_columns == 0
    assert overview.n_cells == 0
    assert overview.missing_ratio is None
    assert overview.completeness_ratio is None
    assert overview.semantic_resolution_ratio is None
    assert overview.resolved_column_count == 0


def test_mixed_dataset_aggregates_selected_semantic_types():
    frame = _mixed_frame()
    analysis = analyze_dataframe(frame)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert [column.inferred.selected_type for column in analysis.columns] == [
        SemanticType.EMPTY,
        SemanticType.CONSTANT,
        SemanticType.BOOLEAN,
        SemanticType.DATETIME,
        SemanticType.TIMEDELTA,
        SemanticType.NUMERIC,
        SemanticType.IDENTIFIER,
        SemanticType.CATEGORICAL,
        None,
        None,
    ]
    assert [column.inferred.resolution.status for column in analysis.columns] == [
        ResolutionStatus.RESOLVED,
        ResolutionStatus.RESOLVED,
        ResolutionStatus.RESOLVED,
        ResolutionStatus.RESOLVED,
        ResolutionStatus.RESOLVED,
        ResolutionStatus.RESOLVED,
        ResolutionStatus.RESOLVED,
        ResolutionStatus.RESOLVED,
        ResolutionStatus.INSUFFICIENT_EVIDENCE,
        ResolutionStatus.INSUFFICIENT_EVIDENCE,
    ]
    assert _type_counts(overview) == {
        SemanticType.NUMERIC: 1,
        SemanticType.CATEGORICAL: 1,
        SemanticType.BOOLEAN: 1,
        SemanticType.DATETIME: 1,
        SemanticType.TIMEDELTA: 1,
        SemanticType.IDENTIFIER: 1,
        SemanticType.CONSTANT: 1,
        SemanticType.EMPTY: 1,
    }
    assert SemanticType.TEXT not in _type_counts(overview)
    assert overview.resolved_column_count == 8
    assert overview.insufficient_evidence_column_count == 2
    assert overview.ambiguous_column_count == 0
    assert overview.semantic_resolution_ratio == pytest.approx(0.8)
    assert [(ref.position, ref.label) for ref in overview.empty_columns] == [
        (0, "empty_col")
    ]
    assert [(ref.position, ref.label) for ref in overview.constant_columns] == [
        (1, "constant_col")
    ]
    assert [(ref.position, ref.label) for ref in overview.identifier_columns] == [
        (6, "code")
    ]
    assert [
        (ref.position, ref.label) for ref in overview.insufficient_evidence_columns
    ] == [(8, "note"), (9, "wave")]
    for position in (5, 6, 7):
        assert analysis.columns[position].inferred.interpretation is None
        assert analysis.columns[position].inferred.selected_type is not None


def test_candidate_selected_types_count_without_an_interpretation():
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3],
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string"),
            "group": pd.Series(pd.Categorical(["red", "blue", "red"])),
        }
    )
    analysis = analyze_dataframe(frame)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert _type_counts(overview) == {
        SemanticType.NUMERIC: 1,
        SemanticType.CATEGORICAL: 1,
        SemanticType.IDENTIFIER: 1,
    }
    assert overview.resolved_column_count == 3
    assert overview.semantic_resolution_ratio == 1.0
    for column in analysis.columns:
        assert column.inferred.interpretation is None
        assert column.inferred.resolution.status is ResolutionStatus.RESOLVED


def test_constant_uuid_counts_as_constant():
    overview = _overview(
        pd.DataFrame(
            {
                "repeated": pd.Series([_UUID_A, _UUID_A, _UUID_A], dtype="string"),
                "code": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string"),
            }
        )
    )
    _assert_invariants(overview)
    assert _type_counts(overview) == {
        SemanticType.IDENTIFIER: 1,
        SemanticType.CONSTANT: 1,
    }
    assert overview.constant_column_count == 1
    assert overview.identifier_column_count == 1
    assert overview.constant_columns[0].label == "repeated"
    assert overview.identifier_columns[0].label == "code"


def test_synthetic_text_selection_is_counted():
    text = _column(0, "body", n_rows=2, semantic_type=SemanticType.TEXT)
    assert text.inferred.interpretation is None
    assert text.inferred.selected_type is SemanticType.TEXT
    overview = build_dataset_overview(_manual_analysis((text,), n_rows=2))
    _assert_invariants(overview)
    assert _type_counts(overview) == {SemanticType.TEXT: 1}
    assert overview.resolved_column_count == 1
    assert overview.empty_column_count == 0


def test_insufficient_evidence_and_ambiguity_stay_separate():
    columns = (
        _column(
            0,
            "note",
            n_rows=3,
            status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
        ),
        _column(
            1,
            "mixed",
            n_rows=3,
            status=ResolutionStatus.AMBIGUOUS,
        ),
        _column(2, "amount", n_rows=3, semantic_type=SemanticType.NUMERIC),
    )
    overview = build_dataset_overview(_manual_analysis(columns, n_rows=3))
    _assert_invariants(overview)
    assert overview.resolved_column_count == 1
    assert overview.insufficient_evidence_column_count == 1
    assert overview.ambiguous_column_count == 1
    assert overview.semantic_resolution_ratio == pytest.approx(1 / 3)
    assert overview.insufficient_evidence_columns == (ColumnRef(0, "note"),)
    assert overview.ambiguous_columns == (ColumnRef(1, "mixed"),)
    assert _type_counts(overview) == {SemanticType.NUMERIC: 1}
    assert columns[0].inferred.selected_type is None
    assert columns[1].inferred.selected_type is None
    assert columns[1].inferred.interpretation is None


def test_duplicate_labels_remain_distinct_columns():
    frame = pd.DataFrame([[7, 1], [7, 2], [7, 3]], columns=["x", "x"])
    analysis = analyze_dataframe(frame)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert analysis.columns[0].label == analysis.columns[1].label == "x"
    assert analysis.columns[0].position == 0
    assert analysis.columns[1].position == 1
    assert analysis.columns[0].inferred.selected_type is SemanticType.CONSTANT
    assert analysis.columns[1].inferred.selected_type is SemanticType.NUMERIC
    assert overview.n_columns == 2
    assert overview.resolved_column_count == 2
    assert _type_counts(overview) == {
        SemanticType.NUMERIC: 1,
        SemanticType.CONSTANT: 1,
    }
    assert overview.constant_columns == (ColumnRef(position=0, label="x"),)
    assert overview.identifier_column_count == 0


def test_two_constant_columns_may_share_a_label():
    frame = pd.DataFrame([[1, 2], [1, 2], [1, 2]], columns=["x", "x"])
    overview = _overview(frame)
    _assert_invariants(overview)
    assert overview.constant_column_count == 2
    assert overview.constant_columns == (
        ColumnRef(0, "x"),
        ColumnRef(1, "x"),
    )
    assert _type_counts(overview) == {SemanticType.CONSTANT: 2}


def test_non_string_labels_are_not_stringified():
    frame = pd.DataFrame(
        {
            "left": pd.Series([None, None], dtype="object"),
            "right": pd.Series([None, None], dtype="object"),
        }
    )
    frame.columns = [42, ("group", "value")]
    analysis = analyze_dataframe(frame)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert overview.empty_columns[0].label is analysis.columns[0].label
    assert overview.empty_columns[1].label is analysis.columns[1].label
    assert overview.empty_columns[0].label == 42
    assert isinstance(overview.empty_columns[0].label, int)
    assert overview.empty_columns[1].label == ("group", "value")
    assert not isinstance(overview.empty_columns[0].label, str)
    assert not isinstance(overview.empty_columns[1].label, str)


def test_manual_analysis_needs_no_dataframe_scan():
    columns = (
        _column(
            0, 42, n_rows=4, semantic_type=SemanticType.EMPTY, n_missing=4, n_unique=0
        ),
        _column(
            1,
            ("group", "value"),
            n_rows=4,
            semantic_type=SemanticType.CONSTANT,
            n_unique=1,
        ),
        _column(2, "code", n_rows=4, semantic_type=SemanticType.IDENTIFIER),
        _column(3, "body", n_rows=4, semantic_type=SemanticType.TEXT, n_missing=1),
        _column(4, "note", n_rows=4, status=ResolutionStatus.INSUFFICIENT_EVIDENCE),
        _column(5, "mixed", n_rows=4, status=ResolutionStatus.AMBIGUOUS),
    )
    analysis = _manual_analysis(columns, n_rows=4)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert overview.n_rows == 4
    assert overview.n_columns == 6
    assert overview.n_cells == 24
    assert overview.n_missing_cells == 5
    assert overview.n_non_missing_cells == 19
    assert overview.missing_ratio == pytest.approx(5 / 24)
    assert overview.completeness_ratio == pytest.approx(19 / 24)
    assert _type_counts(overview) == {
        SemanticType.TEXT: 1,
        SemanticType.IDENTIFIER: 1,
        SemanticType.CONSTANT: 1,
        SemanticType.EMPTY: 1,
    }
    assert overview.empty_columns == (ColumnRef(0, 42),)
    assert overview.constant_columns == (ColumnRef(1, ("group", "value")),)
    assert overview.identifier_columns == (ColumnRef(2, "code"),)
    assert overview.insufficient_evidence_columns == (ColumnRef(4, "note"),)
    assert overview.ambiguous_columns == (ColumnRef(5, "mixed"),)
    assert overview.semantic_resolution_ratio == pytest.approx(4 / 6)


def test_equal_analyses_produce_equal_overviews():
    frame = _mixed_frame()
    first = _overview(frame)
    second = _overview(frame)
    _assert_invariants(first)
    assert first == second
    assert build_dataset_overview(analyze_dataframe(frame)) == first


def test_builder_does_not_call_analysis_or_semantic_collection(monkeypatch):
    analysis = analyze_dataframe(_mixed_frame())

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("overview must not call analysis or collection")

    targets = (
        (dataset_module, "analyze_dataframe"),
        (dataset_module, "collect_duplicate_analysis"),
        (dataset_module, "collect_relationship_analysis"),
        (column_module, "analyze_series"),
        (pipeline, "infer_series_semantics"),
        (physical, "classify_physical_dtype"),
        (basic_evidence, "collect_basic_column_evidence"),
        (frequency_evidence, "collect_frequency_evidence"),
        (numeric_evidence, "collect_numeric_structure_evidence"),
        (string_evidence, "collect_string_structure_evidence"),
        (pattern_evidence, "collect_pattern_evidence"),
        (resolution_module, "resolve_semantics"),
    )
    for module, name in targets:
        monkeypatch.setattr(module, name, _fail)
        if name in vars(overview_module):
            monkeypatch.setattr(overview_module, name, _fail)
    overview = build_dataset_overview(analysis)
    _assert_invariants(overview)
    assert overview.n_columns == 10


def test_overview_module_does_not_import_pandas_or_collectors():
    source = Path(overview_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    modules = []
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            names.extend(alias.name for alias in node.names)
    assert "pandas" not in modules
    assert "pd" not in names
    forbidden = {
        "analyze_dataframe",
        "analyze_series",
        "infer_series_semantics",
        "classify_physical_dtype",
        "collect_basic_column_evidence",
        "collect_frequency_evidence",
        "collect_numeric_structure_evidence",
        "collect_string_structure_evidence",
        "collect_pattern_evidence",
        "resolve_semantics",
        "collect_duplicate_analysis",
        "collect_missing_analysis",
        "collect_relationship_analysis",
    }
    assert forbidden.isdisjoint(names)


def test_overview_models_are_frozen():
    ref = ColumnRef(position=0, label="amount")
    count = SemanticTypeCount(semantic_type=SemanticType.NUMERIC, count=1)
    overview = _direct_overview()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.position = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        count.count = 2  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        overview.n_rows = 0  # type: ignore[misc]


def test_builder_rejects_anything_other_than_dataset_analysis():
    frame = pd.DataFrame({"amount": [1, 2, 3]})
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_dataset_overview(frame)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_dataset_overview(frame["amount"])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_dataset_overview({"amount": [1, 2, 3]})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_dataset_overview(None)  # type: ignore[arg-type]
    assert list(frame["amount"]) == [1, 2, 3]


def test_builder_rejects_a_resolved_column_without_a_selected_type():
    analysis = analyze_dataframe(pd.DataFrame({"amount": [1, 2, 3]}))

    class _Resolution:
        status = ResolutionStatus.RESOLVED

    class _Inferred:
        resolution = _Resolution()
        selected_type = None

    object.__setattr__(analysis.columns[0], "inferred", _Inferred())
    with pytest.raises(ValueError, match="no selected semantic type"):
        build_dataset_overview(analysis)


def test_builder_rejects_an_unrecognized_resolution_status():
    analysis = analyze_dataframe(pd.DataFrame({"amount": [1, 2, 3]}))

    class _Resolution:
        status = "unresolved"

    class _Inferred:
        resolution = _Resolution()
        selected_type = None

    object.__setattr__(analysis.columns[0], "inferred", _Inferred())
    with pytest.raises(ValueError, match="unrecognized resolution status"):
        build_dataset_overview(analysis)


def test_overview_rejects_inconsistent_duplicate_counts():
    with pytest.raises(ValueError, match="cannot exceed n_rows"):
        _direct_overview(n_unique_rows=2)
    with pytest.raises(ValueError, match="must equal n_rows - n_unique_rows"):
        _direct_overview(n_excess_duplicate_rows=1)
    with pytest.raises(ValueError, match="at least one unique row"):
        _direct_overview(n_unique_rows=0, n_excess_duplicate_rows=1)
    with pytest.raises(ValueError, match="n_unique_rows"):
        _direct_overview(n_unique_rows=-1)


def test_overview_rejects_inconsistent_dimensions():
    with pytest.raises(ValueError, match="n_rows"):
        _direct_overview(n_rows=-1)
    with pytest.raises(ValueError, match="n_rows"):
        _direct_overview(n_rows=True)
    with pytest.raises(ValueError, match="n_cells must equal"):
        _direct_overview(n_rows=2, n_columns=2, n_cells=3, n_non_missing_cells=3)
    with pytest.raises(ValueError, match="must sum to n_cells"):
        _direct_overview(n_missing_cells=1, n_non_missing_cells=1)


def test_overview_rejects_inconsistent_semantic_counts():
    with pytest.raises(TypeError, match="semantic_type_counts must be a tuple"):
        _direct_overview(
            semantic_type_counts=[SemanticTypeCount(SemanticType.NUMERIC, 1)]
        )
    with pytest.raises(TypeError, match="SemanticTypeCount"):
        _direct_overview(semantic_type_counts=("numeric",))
    with pytest.raises(ValueError, match="definition order"):
        _direct_overview(
            n_columns=2,
            n_cells=2,
            n_non_missing_cells=2,
            semantic_type_counts=(
                SemanticTypeCount(SemanticType.EMPTY, 1),
                SemanticTypeCount(SemanticType.NUMERIC, 1),
            ),
            empty_columns=(ColumnRef(0, "a"),),
        )
    with pytest.raises(ValueError, match="definition order"):
        _direct_overview(
            n_columns=2,
            n_cells=2,
            n_non_missing_cells=2,
            semantic_type_counts=(
                SemanticTypeCount(SemanticType.NUMERIC, 1),
                SemanticTypeCount(SemanticType.NUMERIC, 1),
            ),
        )
    with pytest.raises(ValueError, match="positive int"):
        SemanticTypeCount(SemanticType.NUMERIC, 0)
    with pytest.raises(ValueError, match="positive int"):
        SemanticTypeCount(SemanticType.NUMERIC, True)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="SemanticType"):
        SemanticTypeCount("numeric", 1)  # type: ignore[arg-type]


def test_overview_rejects_inconsistent_column_groups():
    with pytest.raises(
        TypeError, match="insufficient_evidence_columns must be a tuple"
    ):
        _direct_overview(insufficient_evidence_columns=[])
    with pytest.raises(TypeError, match="ColumnRef"):
        _direct_overview(insufficient_evidence_columns=("note",))
    with pytest.raises(ValueError, match="less than n_columns"):
        _direct_overview(
            n_columns=1,
            semantic_type_counts=(),
            insufficient_evidence_columns=(ColumnRef(1, "note"),),
        )
    with pytest.raises(ValueError, match="source position order"):
        _direct_overview(
            n_columns=2,
            n_cells=2,
            n_non_missing_cells=2,
            semantic_type_counts=(),
            insufficient_evidence_columns=(ColumnRef(0, "a"), ColumnRef(0, "a")),
        )
    with pytest.raises(ValueError, match="another group"):
        _direct_overview(
            semantic_type_counts=(SemanticTypeCount(SemanticType.EMPTY, 1),),
            insufficient_evidence_columns=(ColumnRef(0, "a"),),
            empty_columns=(ColumnRef(0, "a"),),
        )
    with pytest.raises(ValueError, match="EMPTY count"):
        _direct_overview(
            semantic_type_counts=(SemanticTypeCount(SemanticType.EMPTY, 1),),
            empty_columns=(),
        )
    with pytest.raises(ValueError, match="must sum to n_columns"):
        _direct_overview(n_columns=2, n_cells=2, n_non_missing_cells=2)
    with pytest.raises(ValueError, match="position"):
        ColumnRef(position=-1, label="a")
    with pytest.raises(ValueError, match="position"):
        ColumnRef(position=True, label="a")  # type: ignore[arg-type]


def test_overview_does_not_store_the_analysis_or_a_quality_score():
    overview = _overview(_mixed_frame())
    names = {field.name for field in dataclasses.fields(overview)}
    assert "analysis" not in names
    forbidden = {
        "quality_score",
        "health_score",
        "dataset_score",
        "readiness_score",
        "overall_score",
        "severity",
        "findings",
    }
    assert forbidden.isdisjoint(names)
    assert forbidden.isdisjoint(dir(overview))
    for field in dataclasses.fields(overview):
        value = getattr(overview, field.name)
        assert not isinstance(value, (pd.DataFrame, pd.Series, dict, list))


def test_column_references_follow_source_order_when_groups_are_not_contiguous():
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3],
            "blank": pd.Series([None, None, None], dtype="object"),
            "same": [4, 4, 4],
            "also_blank": pd.Series([None, None, None], dtype="float64"),
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C], dtype="string"),
        }
    )
    overview = _overview(frame)
    _assert_invariants(overview)
    assert [ref.position for ref in overview.empty_columns] == [1, 3]
    assert [ref.label for ref in overview.empty_columns] == ["blank", "also_blank"]
    assert [ref.position for ref in overview.constant_columns] == [2]
    assert [ref.position for ref in overview.identifier_columns] == [4]
    assert _type_counts(overview)[SemanticType.NUMERIC] == 1
    assert _type_counts(overview)[SemanticType.EMPTY] == 2
