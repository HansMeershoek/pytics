"""TSK-022: dataset missingness structure and the missingness summary."""

from __future__ import annotations

import dataclasses
import inspect

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.dataset as dataset_module
import pytics.analysis.missing as missing_module
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.relationship import RelationshipAnalysis
from pytics.analysis.missing import ColumnMissingness
from pytics.analysis.missing import MissingAnalysis
from pytics.analysis.missing import MissingSummary
from pytics.analysis.missing import MissingnessPattern
from pytics.analysis.missing import RowMissingnessBucket
from pytics.analysis.missing import build_missing_summary
from pytics.analysis.missing import collect_missing_analysis
from pytics.analysis.overview import build_dataset_overview
from pytics.analysis.variables import build_variables_summary

_RETAINED = (pd.DataFrame, pd.Series, pd.Index, np.ndarray)
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


def _summary(frame: pd.DataFrame) -> MissingSummary:
    return build_missing_summary(analyze_dataframe(frame))


def _assert_invariants(summary: MissingSummary) -> None:
    assert summary.n_cells == summary.n_rows * summary.n_columns
    assert summary.n_missing_cells + summary.n_non_missing_cells == summary.n_cells
    assert summary.n_complete_rows + summary.n_rows_with_missing == summary.n_rows
    assert summary.n_complete_columns + summary.n_columns_with_missing == (
        summary.n_columns
    )
    assert summary.n_patterns == len(summary.patterns)
    assert len(summary.columns) == summary.n_columns
    assert sum(column.n_missing for column in summary.columns) == (
        summary.n_missing_cells
    )
    assert sum(bucket.row_count for bucket in summary.row_distribution) == (
        summary.n_rows
    )
    assert sum(pattern.row_count for pattern in summary.patterns) == summary.n_rows
    weighted = sum(
        len(pattern.positions) * pattern.row_count for pattern in summary.patterns
    )
    assert weighted == summary.n_missing_cells
    by_width: dict[int, int] = {}
    for pattern in summary.patterns:
        assert pattern.positions == tuple(sorted(set(pattern.positions)))
        assert all(0 <= position < summary.n_columns for position in pattern.positions)
        width = len(pattern.positions)
        by_width[width] = by_width.get(width, 0) + pattern.row_count
    distribution = {
        bucket.missing_columns_count: bucket.row_count
        for bucket in summary.row_distribution
    }
    assert distribution == by_width
    assert all(
        0 <= bucket.missing_columns_count <= summary.n_columns
        for bucket in summary.row_distribution
    )
    assert list(distribution) == sorted(distribution)
    keys = [(-pattern.row_count, pattern.positions) for pattern in summary.patterns]
    assert keys == sorted(keys)
    if summary.n_cells == 0:
        assert summary.missing_ratio is None
        assert summary.completeness_ratio is None
    else:
        assert summary.missing_ratio == pytest.approx(
            summary.n_missing_cells / summary.n_cells
        )
        assert summary.completeness_ratio == pytest.approx(
            summary.n_non_missing_cells / summary.n_cells
        )
    if summary.n_rows == 0:
        assert summary.complete_row_ratio is None
        assert summary.incomplete_row_ratio is None
        assert summary.row_distribution == ()
        assert summary.patterns == ()
    else:
        assert summary.complete_row_ratio == pytest.approx(
            summary.n_complete_rows / summary.n_rows
        )
        assert summary.incomplete_row_ratio == pytest.approx(
            summary.n_rows_with_missing / summary.n_rows
        )
        for bucket in summary.row_distribution:
            assert bucket.row_ratio(summary.n_rows) == pytest.approx(
                bucket.row_count / summary.n_rows
            )
        for pattern in summary.patterns:
            assert pattern.row_ratio(summary.n_rows) == pytest.approx(
                pattern.row_count / summary.n_rows
            )


def _ordered_frame() -> pd.DataFrame:
    """Rows are ordered so first-seen patterns are not the result order."""
    return pd.DataFrame(
        {
            "a": pd.Series(
                [1, 1, pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 1, 1],
                dtype="Int64",
            ),
            "b": pd.Series(
                [1, 1, 1, 1, pd.NA, pd.NA, pd.NA, 1, 1],
                dtype="Int64",
            ),
            "c": pd.Series(
                [pd.NA, pd.NA, 1, 1, 1, 1, 1, 1, 1],
                dtype="Int64",
            ),
        }
    )


def test_dataset_facts_for_no_some_and_all_missing():
    complete = _summary(pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}))
    _assert_invariants(complete)
    assert complete.n_rows == 2
    assert complete.n_columns == 2
    assert complete.n_cells == 4
    assert complete.n_missing_cells == 0
    assert complete.n_non_missing_cells == 4
    assert complete.missing_ratio == 0.0
    assert complete.completeness_ratio == 1.0
    assert complete.n_complete_rows == 2
    assert complete.n_rows_with_missing == 0
    assert complete.complete_row_ratio == 1.0
    assert complete.incomplete_row_ratio == 0.0
    assert complete.n_complete_columns == 2
    assert complete.n_columns_with_missing == 0

    partial = _summary(_ordered_frame())
    _assert_invariants(partial)
    assert partial.n_rows == 9
    assert partial.n_cells == 27
    assert partial.n_missing_cells == 10
    assert partial.n_non_missing_cells == 17
    assert partial.missing_ratio == pytest.approx(10 / 27)
    assert partial.completeness_ratio == pytest.approx(17 / 27)
    assert partial.n_complete_rows == 2
    assert partial.n_rows_with_missing == 7
    assert partial.complete_row_ratio == pytest.approx(2 / 9)
    assert partial.incomplete_row_ratio == pytest.approx(7 / 9)

    missing = _summary(
        pd.DataFrame(
            {
                "a": pd.Series([pd.NA, pd.NA], dtype="Int64"),
                "b": pd.Series([None, None], dtype="object"),
            }
        )
    )
    _assert_invariants(missing)
    assert missing.n_missing_cells == 4
    assert missing.n_non_missing_cells == 0
    assert missing.missing_ratio == 1.0
    assert missing.completeness_ratio == 0.0
    assert missing.n_complete_rows == 0
    assert missing.n_rows_with_missing == 2
    assert missing.complete_row_ratio == 0.0
    assert missing.incomplete_row_ratio == 1.0
    assert missing.n_complete_columns == 0
    assert missing.n_columns_with_missing == 2


def test_column_records_keep_order_counts_and_labels():
    summary = _summary(_ordered_frame())
    _assert_invariants(summary)
    assert [column.position for column in summary.columns] == [0, 1, 2]
    assert [column.label for column in summary.columns] == ["a", "b", "c"]
    assert [(column.n_missing, column.n_non_missing) for column in summary.columns] == [
        (5, 4),
        (3, 6),
        (2, 7),
    ]
    assert summary.columns[0].n_total == 9
    assert summary.columns[0].missing_ratio == pytest.approx(5 / 9)
    assert summary.columns[0].n_missing + summary.columns[0].n_non_missing == 9

    duplicate = _summary(
        pd.DataFrame(
            [[1, pd.NA, 2], [pd.NA, 3, pd.NA], [4, 5, 6]],
            columns=["x", "x", "y"],
        )
    )
    _assert_invariants(duplicate)
    assert [column.label for column in duplicate.columns] == ["x", "x", "y"]
    assert [column.n_missing for column in duplicate.columns] == [1, 1, 1]
    assert duplicate.patterns == (
        MissingnessPattern((), 1),
        MissingnessPattern((0, 2), 1),
        MissingnessPattern((1,), 1),
    )

    labeled = pd.DataFrame([[1, "a"], [pd.NA, "b"]])
    labeled.columns = [42, ("group", "value")]
    non_string = _summary(labeled)
    _assert_invariants(non_string)
    assert non_string.columns[0].label == 42
    assert type(non_string.columns[0].label) is int
    assert non_string.columns[1].label == ("group", "value")
    assert non_string.columns[0].n_missing == 1
    assert non_string.columns[1].n_missing == 0

    columns = pd.MultiIndex.from_tuples([("group", "value"), ("group", "value")])
    multi = _summary(pd.DataFrame([[1, pd.NA], [2, "b"]], columns=columns))
    _assert_invariants(multi)
    assert multi.columns[0].label == ("group", "value")
    assert multi.columns[1].label == ("group", "value")
    assert multi.columns[0].position == 0
    assert multi.columns[1].position == 1
    assert [column.n_missing for column in multi.columns] == [0, 1]
    assert multi.patterns == (
        MissingnessPattern((), 1),
        MissingnessPattern((1,), 1),
    )


def test_row_distribution_counts_complete_partial_and_full_rows():
    summary = _summary(_ordered_frame())
    _assert_invariants(summary)
    assert summary.row_distribution == (
        RowMissingnessBucket(0, 2),
        RowMissingnessBucket(1, 4),
        RowMissingnessBucket(2, 3),
    )
    assert summary.n_complete_rows == 2
    assert [bucket.missing_columns_count for bucket in summary.row_distribution] == [
        0,
        1,
        2,
    ]
    assert 3 not in {
        bucket.missing_columns_count for bucket in summary.row_distribution
    }

    mixed = _summary(
        pd.DataFrame(
            {
                "a": pd.Series([1, pd.NA, pd.NA], dtype="Int64"),
                "b": pd.Series([2, 3, pd.NA], dtype="Int64"),
            }
        )
    )
    _assert_invariants(mixed)
    assert mixed.row_distribution == (
        RowMissingnessBucket(0, 1),
        RowMissingnessBucket(1, 1),
        RowMissingnessBucket(2, 1),
    )
    assert mixed.patterns == (
        MissingnessPattern((), 1),
        MissingnessPattern((0,), 1),
        MissingnessPattern((0, 1), 1),
    )


def test_patterns_use_positions_and_deterministic_order():
    summary = _summary(_ordered_frame())
    _assert_invariants(summary)
    assert summary.patterns == (
        MissingnessPattern((0, 1), 3),
        MissingnessPattern((), 2),
        MissingnessPattern((0,), 2),
        MissingnessPattern((2,), 2),
    )
    assert summary.patterns[1].positions == ()
    assert summary.patterns[1].row_count == summary.n_complete_rows
    reversed_rows = _summary(_ordered_frame().iloc[::-1])
    _assert_invariants(reversed_rows)
    assert reversed_rows.patterns == summary.patterns
    assert reversed_rows.row_distribution == summary.row_distribution

    tied = _summary(
        pd.DataFrame(
            {
                "a": pd.Series([1, 1, 1, 1], dtype="Int64"),
                "b": pd.Series([pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64"),
                "c": pd.Series([1, 1, pd.NA, pd.NA], dtype="Int64"),
            }
        )
    )
    _assert_invariants(tied)
    assert tied.patterns == (
        MissingnessPattern((1,), 2),
        MissingnessPattern((1, 2), 2),
    )


def test_missing_markers_follow_pandas_and_literals_stay_observed():
    literals = _summary(
        pd.DataFrame(
            {"text": ["", " ", "NA", "N/A", "null", "None", "-"]},
        )
    )
    _assert_invariants(literals)
    assert literals.columns[0].n_missing == 0
    assert literals.columns[0].n_non_missing == 7
    assert literals.patterns == (MissingnessPattern((), 7),)
    assert literals.n_rows_with_missing == 0

    markers = pd.DataFrame(
        {
            "obj": pd.Series([None, "", " ", "NA"], dtype="object"),
            "flt": pd.Series([np.nan, 1.0, 2.0, 3.0]),
            "num": pd.Series([pd.NA, 1, 2, 3], dtype="Int64"),
            "when": pd.to_datetime(["NaT", "2020-01-01", "2020-01-02", "2020-01-03"]),
            "span": pd.to_timedelta(["NaT", "1 day", "2 days", "3 days"]),
        }
    )
    summary = _summary(markers)
    _assert_invariants(summary)
    assert [column.n_missing for column in summary.columns] == [1, 1, 1, 1, 1]
    assert summary.columns[0].n_non_missing == 3
    assert summary.patterns == (
        MissingnessPattern((), 3),
        MissingnessPattern((0, 1, 2, 3, 4), 1),
    )
    assert markers["obj"].tolist()[1:] == ["", " ", "NA"]


def test_zero_size_frames_have_explicit_ratios():
    empty = _summary(pd.DataFrame())
    _assert_invariants(empty)
    assert empty.columns == ()
    assert empty.row_distribution == ()
    assert empty.patterns == ()
    assert empty.n_complete_rows == 0
    assert empty.n_rows_with_missing == 0
    assert empty.n_complete_columns == 0
    assert empty.n_columns_with_missing == 0
    assert empty.missing_ratio is None
    assert empty.completeness_ratio is None
    assert empty.complete_row_ratio is None
    assert empty.incomplete_row_ratio is None

    zero_rows = _summary(
        pd.DataFrame(
            {
                "amount": pd.Series(dtype="int64"),
                "city": pd.Series(dtype="string"),
            }
        )
    )
    _assert_invariants(zero_rows)
    assert len(zero_rows.columns) == 2
    assert all(column.n_total == 0 for column in zero_rows.columns)
    assert all(column.n_missing == 0 for column in zero_rows.columns)
    assert all(column.n_non_missing == 0 for column in zero_rows.columns)
    assert all(column.missing_ratio is None for column in zero_rows.columns)
    assert zero_rows.n_complete_columns == 2
    assert zero_rows.row_distribution == ()
    assert zero_rows.patterns == ()
    assert zero_rows.missing_ratio is None
    assert zero_rows.complete_row_ratio is None

    zero_columns = _summary(pd.DataFrame(index=[0, 1, 2]))
    _assert_invariants(zero_columns)
    assert zero_columns.n_rows == 3
    assert zero_columns.n_columns == 0
    assert zero_columns.n_cells == 0
    assert zero_columns.columns == ()
    assert zero_columns.n_complete_rows == 3
    assert zero_columns.n_rows_with_missing == 0
    assert zero_columns.complete_row_ratio == 1.0
    assert zero_columns.incomplete_row_ratio == 0.0
    assert zero_columns.missing_ratio is None
    assert zero_columns.completeness_ratio is None
    assert zero_columns.row_distribution == (RowMissingnessBucket(0, 3),)
    assert zero_columns.patterns == (MissingnessPattern((), 3),)
    assert zero_columns.patterns[0].row_ratio(3) == 1.0


def test_duplicate_index_does_not_define_pattern_identity():
    frame = pd.DataFrame({"a": [1, None, 1]}, index=["row", "row", 7])
    summary = _summary(frame)
    _assert_invariants(summary)
    assert summary.n_rows == 3
    assert summary.patterns == (
        MissingnessPattern((), 2),
        MissingnessPattern((0,), 1),
    )


def test_builder_reads_retained_analysis_only(monkeypatch: pytest.MonkeyPatch):
    frame = _ordered_frame()
    analysis = analyze_dataframe(frame)

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("missing summary must not rescan")

    monkeypatch.setattr(missing_module, "collect_missing_analysis", _fail)
    monkeypatch.setattr(dataset_module, "collect_missing_analysis", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(dataset_module, "analyze_series", _fail)
    monkeypatch.setattr(pd.DataFrame, "isna", _fail)
    monkeypatch.setattr(pd.Series, "isna", _fail)
    monkeypatch.setattr(pd, "isna", _fail)
    monkeypatch.setattr(np, "unique", _fail)
    summary = build_missing_summary(analysis)
    _assert_invariants(summary)
    assert summary.n_missing_cells == analysis.n_missing_cells
    assert summary.patterns[0] is not analysis.missing_analysis.patterns[0]
    assert summary.patterns == analysis.missing_analysis.patterns
    source = inspect.getsource(build_missing_summary)
    assert ".isna" not in source
    assert "import pandas" not in source
    assert "import numpy" not in source


def test_analysis_does_not_mutate_or_retain_the_source():
    frame = pd.DataFrame(
        {
            "ints": pd.Series([1, pd.NA], dtype="Int64"),
            "flags": pd.Series([True, pd.NA], dtype="boolean"),
            "when": pd.to_datetime(["2020-01-01", "NaT"], utc=True),
            "labels": pd.Categorical(["b", None], categories=["a", "b"]),
            "cities": pd.Series(["", "NA"], dtype="string"),
        }
    )
    frame.index = pd.Index([4, 4], name="row")
    before = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    summary = build_missing_summary(analysis)
    pd.testing.assert_frame_equal(frame, before)
    assert frame.index.equals(before.index)
    _assert_no_retained_source(analysis)
    _assert_no_retained_source(summary)
    _assert_no_retained_source(analysis.missing_analysis)
    assert "missing_analysis" in {field.name for field in dataclasses.fields(analysis)}
    assert not hasattr(summary, "mask")
    assert not hasattr(analysis.missing_analysis, "mask")


def test_models_are_frozen_and_reject_inconsistent_facts():
    summary = _summary(pd.DataFrame({"a": [1, None]}))
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.n_rows = 0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.columns[0].n_missing = 0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.patterns[0].row_count = 1  # type: ignore[misc]
    with pytest.raises(TypeError):
        summary.patterns[0] = MissingnessPattern((), 1)  # type: ignore[index]
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.row_distribution[0].row_count = 1  # type: ignore[misc]

    column = analyze_series(pd.Series([1, None]), position=0, label="a")
    other = analyze_series(pd.Series([None, 2]), position=1, label="b")
    with pytest.raises(TypeError, match="MissingAnalysis"):
        DatasetAnalysis(
            n_rows=2,
            n_columns=1,
            n_cells=2,
            columns=(column,),
            missing_analysis=None,  # type: ignore[arg-type]
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(ValueError, match="sum to n_rows"):
        DatasetAnalysis(
            n_rows=2,
            n_columns=1,
            n_cells=2,
            columns=(column,),
            missing_analysis=MissingAnalysis(
                row_distribution=(RowMissingnessBucket(0, 1),),
                patterns=(MissingnessPattern((), 1),),
            ),
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(ValueError, match="less than n_columns"):
        DatasetAnalysis(
            n_rows=2,
            n_columns=1,
            n_cells=2,
            columns=(column,),
            missing_analysis=MissingAnalysis(
                row_distribution=(
                    RowMissingnessBucket(0, 1),
                    RowMissingnessBucket(1, 1),
                ),
                patterns=(
                    MissingnessPattern((), 1),
                    MissingnessPattern((1,), 1),
                ),
            ),
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(ValueError, match="weighted pattern cells"):
        DatasetAnalysis(
            n_rows=2,
            n_columns=2,
            n_cells=4,
            columns=(column, analyze_series(pd.Series([1, 2]), position=1, label="b")),
            missing_analysis=MissingAnalysis(
                row_distribution=(
                    RowMissingnessBucket(0, 1),
                    RowMissingnessBucket(2, 1),
                ),
                patterns=(
                    MissingnessPattern((), 1),
                    MissingnessPattern((0, 1), 1),
                ),
            ),
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )
    with pytest.raises(ValueError, match="pattern margins"):
        DatasetAnalysis(
            n_rows=2,
            n_columns=2,
            n_cells=4,
            columns=(column, other),
            missing_analysis=MissingAnalysis(
                row_distribution=(RowMissingnessBucket(1, 2),),
                patterns=(MissingnessPattern((0,), 2),),
            ),
            duplicate_analysis=_NO_DUPLICATE_GROUPS,
            relationship_analysis=_NO_RELATIONSHIPS,
        )

    with pytest.raises(ValueError, match="positive int"):
        RowMissingnessBucket(missing_columns_count=0, row_count=0)
    with pytest.raises(ValueError, match="non-negative int"):
        RowMissingnessBucket(missing_columns_count=True, row_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-negative int"):
        MissingnessPattern((), 1).row_ratio(-1)
    assert MissingnessPattern((), 1).row_ratio(0) is None
    with pytest.raises(TypeError, match="tuple"):
        MissingnessPattern([0], 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="strictly increasing"):
        MissingnessPattern((1, 1), 1)
    with pytest.raises(ValueError, match="strictly increasing"):
        MissingnessPattern((2, 0), 1)
    with pytest.raises(ValueError, match="non-negative int"):
        MissingnessPattern((-1,), 1)
    with pytest.raises(TypeError, match="patterns must be a tuple"):
        MissingAnalysis(
            row_distribution=(),
            patterns=[MissingnessPattern((), 1)],  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="RowMissingnessBucket"):
        MissingAnalysis(
            row_distribution=("bucket",),  # type: ignore[arg-type]
            patterns=(),
        )
    with pytest.raises(ValueError, match="increasing missing_columns_count"):
        MissingAnalysis(
            row_distribution=(
                RowMissingnessBucket(1, 1),
                RowMissingnessBucket(0, 1),
            ),
            patterns=(),
        )
    with pytest.raises(TypeError, match="MissingnessPattern"):
        MissingAnalysis(
            row_distribution=(),
            patterns=("pattern",),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="position must be a non-negative int"):
        ColumnMissingness(
            position=-1,
            label="a",
            n_total=1,
            n_missing=0,
            n_non_missing=1,
        )
    with pytest.raises(ValueError, match="n_non_missing must equal"):
        ColumnMissingness(
            position=0,
            label="a",
            n_total=2,
            n_missing=0,
            n_non_missing=1,
        )
    valid_pattern = (MissingnessPattern((), 1),)
    valid_bucket = (RowMissingnessBucket(0, 1),)
    valid_column = ColumnMissingness(
        position=0,
        label="a",
        n_total=1,
        n_missing=0,
        n_non_missing=1,
    )
    with pytest.raises(ValueError, match="n_cells must equal"):
        MissingSummary(
            n_rows=1,
            n_columns=1,
            n_cells=2,
            n_missing_cells=0,
            n_non_missing_cells=2,
            columns=(valid_column,),
            row_distribution=valid_bucket,
            patterns=valid_pattern,
        )
    with pytest.raises(ValueError, match="must sum to n_cells"):
        MissingSummary(
            n_rows=1,
            n_columns=1,
            n_cells=1,
            n_missing_cells=1,
            n_non_missing_cells=1,
            columns=(valid_column,),
            row_distribution=valid_bucket,
            patterns=valid_pattern,
        )
    with pytest.raises(TypeError, match="columns must be a tuple"):
        MissingSummary(
            n_rows=1,
            n_columns=1,
            n_cells=1,
            n_missing_cells=0,
            n_non_missing_cells=1,
            columns=[valid_column],  # type: ignore[arg-type]
            row_distribution=valid_bucket,
            patterns=valid_pattern,
        )
    with pytest.raises(ValueError, match="one record per column"):
        MissingSummary(
            n_rows=1,
            n_columns=1,
            n_cells=1,
            n_missing_cells=0,
            n_non_missing_cells=1,
            columns=(),
            row_distribution=valid_bucket,
            patterns=valid_pattern,
        )
    with pytest.raises(TypeError, match="ColumnMissingness"):
        MissingSummary(
            n_rows=1,
            n_columns=1,
            n_cells=1,
            n_missing_cells=0,
            n_non_missing_cells=1,
            columns=("column",),  # type: ignore[arg-type]
            row_distribution=valid_bucket,
            patterns=valid_pattern,
        )
    with pytest.raises(ValueError, match="n_total must equal n_rows"):
        MissingSummary(
            n_rows=2,
            n_columns=1,
            n_cells=2,
            n_missing_cells=0,
            n_non_missing_cells=2,
            columns=(valid_column,),
            row_distribution=(RowMissingnessBucket(0, 2),),
            patterns=(MissingnessPattern((), 2),),
        )
    with pytest.raises(ValueError, match="column missing counts must sum"):
        MissingSummary(
            n_rows=1,
            n_columns=1,
            n_cells=1,
            n_missing_cells=1,
            n_non_missing_cells=0,
            columns=(valid_column,),
            row_distribution=valid_bucket,
            patterns=valid_pattern,
        )
    with pytest.raises(ValueError, match="unique"):
        MissingAnalysis(
            row_distribution=(RowMissingnessBucket(0, 2),),
            patterns=(MissingnessPattern((), 1), MissingnessPattern((), 1)),
        )
    with pytest.raises(ValueError, match="ordered by descending"):
        MissingAnalysis(
            row_distribution=(RowMissingnessBucket(1, 2),),
            patterns=(
                MissingnessPattern((1,), 1),
                MissingnessPattern((0,), 1),
            ),
        )
    with pytest.raises(ValueError, match="match the row distribution"):
        MissingAnalysis(
            row_distribution=(RowMissingnessBucket(1, 1),),
            patterns=(MissingnessPattern((), 1),),
        )
    with pytest.raises(TypeError, match="tuple"):
        MissingAnalysis(
            row_distribution=[RowMissingnessBucket(0, 1)],  # type: ignore[arg-type]
            patterns=(MissingnessPattern((), 1),),
        )
    with pytest.raises(ValueError, match="n_missing cannot exceed"):
        ColumnMissingness(
            position=0,
            label="a",
            n_total=1,
            n_missing=2,
            n_non_missing=0,
        )
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_missing_summary(pd.DataFrame({"a": [1]}))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="pandas DataFrame"):
        collect_missing_analysis(pd.Series([1, None]))  # type: ignore[arg-type]


def test_collector_rejects_a_mask_that_is_not_boolean_missingness(
    monkeypatch: pytest.MonkeyPatch,
):
    frame = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    def _ints(self: pd.DataFrame) -> pd.DataFrame:
        del self
        return pd.DataFrame([[0, 1], [1, 0]])

    monkeypatch.setattr(pd.DataFrame, "isna", _ints)
    with pytest.raises(TypeError, match="boolean"):
        collect_missing_analysis(frame)

    def _array(self: pd.DataFrame) -> np.ndarray:
        del self
        return np.ones((2, 2), dtype=bool)

    monkeypatch.setattr(pd.DataFrame, "isna", _array)
    with pytest.raises(TypeError, match="DataFrame"):
        collect_missing_analysis(frame)

    def _short(self: pd.DataFrame) -> pd.DataFrame:
        del self
        return pd.DataFrame([[True]])

    monkeypatch.setattr(pd.DataFrame, "isna", _short)
    with pytest.raises(ValueError, match="shape"):
        collect_missing_analysis(frame)


def test_missingness_pass_is_one_dataframe_isna(monkeypatch: pytest.MonkeyPatch):
    calls = {"frame": 0}
    original = pd.DataFrame.isna

    def _isna(self: pd.DataFrame, *args: object, **kwargs: object) -> pd.DataFrame:
        calls["frame"] += 1
        return original(self, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "isna", _isna)
    summary = _summary(pd.DataFrame({"a": [1, None, 3], "b": [None, "x", "y"]}))
    _assert_invariants(summary)
    assert calls["frame"] == 1


def test_overview_and_variables_share_missing_counts():
    frame = pd.DataFrame(
        {
            "amount": pd.Series([1, pd.NA, 3], dtype="Int64"),
            "city": pd.Series(["", "NA", pd.NA], dtype="string"),
            "flag": pd.Series([True, False, pd.NA], dtype="boolean"),
        }
    )
    analysis = analyze_dataframe(frame)
    overview = build_dataset_overview(analysis)
    variables = build_variables_summary(analysis)
    missing = build_missing_summary(analysis)
    _assert_invariants(missing)
    assert overview.n_missing_cells == missing.n_missing_cells
    assert overview.n_non_missing_cells == missing.n_non_missing_cells
    assert overview.n_rows == missing.n_rows
    assert overview.n_columns == missing.n_columns
    assert overview.n_cells == missing.n_cells
    assert len(variables.variables) == len(missing.columns)
    for variable, column in zip(variables.variables, missing.columns):
        assert variable.position == column.position
        assert variable.label == column.label
        assert variable.n_total == column.n_total
        assert variable.n_missing == column.n_missing
        assert variable.n_non_missing == column.n_non_missing
        assert variable.missing_ratio == column.missing_ratio


def test_summary_fields_stay_structural():
    summary = _summary(pd.DataFrame({"a": [1, None]}))
    assert {field.name for field in dataclasses.fields(summary)} == {
        "n_rows",
        "n_columns",
        "n_cells",
        "n_missing_cells",
        "n_non_missing_cells",
        "columns",
        "row_distribution",
        "patterns",
    }
    assert {field.name for field in dataclasses.fields(MissingAnalysis)} == {
        "row_distribution",
        "patterns",
    }
    source = inspect.getsource(missing_module)
    assert ".groupby(" not in source
    assert not hasattr(pytics, "build_missing_summary")
    assert not hasattr(pytics, "MissingSummary")


def test_retained_analysis_exposes_derived_row_facts():
    analysis = analyze_dataframe(_ordered_frame())
    assert analysis.missing_analysis.n_patterns == 4
    assert analysis.missing_analysis.n_complete_rows == 2
    empty = analyze_dataframe(
        pd.DataFrame({"a": pd.Series([pd.NA, pd.NA], dtype="Int64")})
    )
    assert empty.missing_analysis.n_complete_rows == 0
    assert empty.missing_analysis.n_patterns == 1


def test_direct_summary_rejects_a_column_gap():
    with pytest.raises(ValueError, match="column position"):
        MissingSummary(
            n_rows=1,
            n_columns=1,
            n_cells=1,
            n_missing_cells=0,
            n_non_missing_cells=1,
            columns=(
                ColumnMissingness(
                    position=1,
                    label="a",
                    n_total=1,
                    n_missing=0,
                    n_non_missing=1,
                ),
            ),
            row_distribution=(RowMissingnessBucket(0, 1),),
            patterns=(MissingnessPattern((), 1),),
        )


def _assert_no_retained_source(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _RETAINED)
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_no_retained_source(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_retained_source(item, seen)
