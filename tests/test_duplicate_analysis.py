"""TSK-023: exact duplicate-row analysis."""

from __future__ import annotations

import dataclasses
import inspect

import numpy as np
import pandas as pd
import pytest
from pandas.core.groupby.generic import DataFrameGroupBy
from pandas.core.groupby.generic import SeriesGroupBy

import pytics.analysis.duplicate as duplicate_module
from pytics.analysis.anomaly import anomaly_analysis_for_columns
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.duplicate import DuplicateGroup
from pytics.analysis.duplicate import collect_duplicate_analysis
from pytics.analysis.relationship import RelationshipAnalysis
from pytics.analysis.overview import build_dataset_overview
from tests.missing_margins import missing_analysis_for_margins

_NO_ANOMALIES = anomaly_analysis_for_columns((), n_rows=0)

_RETAINED = (
    pd.DataFrame,
    pd.Series,
    pd.Index,
    np.ndarray,
    DataFrameGroupBy,
    SeriesGroupBy,
)


def _analyzed(frame: pd.DataFrame) -> DatasetAnalysis:
    return analyze_dataframe(frame)


def _unique_rows(analysis: DatasetAnalysis) -> int | None:
    return analysis.duplicate_analysis.n_unique_rows(analysis.n_rows)


def _assert_invariants(analysis: DatasetAnalysis) -> None:
    duplicates = analysis.duplicate_analysis
    assert duplicates.available is True
    groups = duplicates.duplicate_groups
    assert duplicates.n_duplicate_groups == len(groups)
    assert duplicates.n_rows_in_duplicate_groups == sum(group.size for group in groups)
    assert duplicates.n_excess_duplicate_rows == sum(
        group.excess_count for group in groups
    )
    unique = _unique_rows(analysis)
    assert unique is not None
    assert duplicates.n_excess_duplicate_rows == analysis.n_rows - unique
    assert 0 <= unique <= analysis.n_rows
    assert duplicates.n_rows_in_duplicate_groups is not None
    assert 0 <= duplicates.n_rows_in_duplicate_groups <= analysis.n_rows
    assert duplicates.n_excess_duplicate_rows is not None
    assert 0 <= duplicates.n_excess_duplicate_rows <= analysis.n_rows
    seen: set[int] = set()
    previous = None
    for group in groups:
        assert group.size == len(group.row_positions) >= 2
        assert group.excess_count == group.size - 1
        assert list(group.row_positions) == sorted(group.row_positions)
        assert len(set(group.row_positions)) == group.size
        assert seen.isdisjoint(group.row_positions)
        seen.update(group.row_positions)
        key = (-group.size, group.row_positions[0], group.row_positions)
        if previous is not None:
            assert previous <= key
        previous = key
        for position in group.row_positions:
            assert 0 <= position < analysis.n_rows
    if analysis.n_rows == 0:
        assert unique == 0
    else:
        assert unique >= 1


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


def test_all_unique_rows_have_no_groups_and_full_unique_ratio():
    summary = _analyzed(pd.DataFrame({"a": [1, 2, 3], "b": ["a", "b", "c"]}))
    _assert_invariants(summary)
    assert summary.n_rows == 3
    assert _unique_rows(summary) == 3
    assert summary.duplicate_analysis.n_duplicate_groups == 0
    assert summary.duplicate_analysis.n_rows_in_duplicate_groups == 0
    assert summary.duplicate_analysis.n_excess_duplicate_rows == 0
    assert summary.duplicate_analysis.duplicate_groups == ()


def test_one_duplicated_pair_keeps_the_other_row_out_of_the_group():
    summary = _analyzed(pd.DataFrame({"a": ["A", "A", "B"]}))
    _assert_invariants(summary)
    assert _unique_rows(summary) == 2
    assert summary.duplicate_analysis.n_duplicate_groups == 1
    assert summary.duplicate_analysis.n_rows_in_duplicate_groups == 2
    assert summary.duplicate_analysis.n_excess_duplicate_rows == 1
    assert summary.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)
    assert summary.duplicate_analysis.duplicate_groups[0].size == 2
    assert summary.duplicate_analysis.duplicate_groups[0].excess_count == 1


def test_one_group_repeated_three_times_counts_two_excess_rows():
    summary = _analyzed(pd.DataFrame({"a": ["A", "A", "A", "B"]}))
    _assert_invariants(summary)
    assert _unique_rows(summary) == 2
    assert summary.duplicate_analysis.n_duplicate_groups == 1
    assert summary.duplicate_analysis.n_rows_in_duplicate_groups == 3
    assert summary.duplicate_analysis.n_excess_duplicate_rows == 2
    assert summary.duplicate_analysis.duplicate_groups[0].row_positions == (0, 1, 2)
    assert summary.duplicate_analysis.duplicate_groups[0].size == 3
    assert summary.duplicate_analysis.duplicate_groups[0].excess_count == 2


def test_all_identical_rows_are_one_group():
    summary = _analyzed(pd.DataFrame({"a": [1, 1, 1], "b": ["x", "x", "x"]}))
    _assert_invariants(summary)
    assert _unique_rows(summary) == 1
    assert summary.duplicate_analysis.n_duplicate_groups == 1
    assert summary.duplicate_analysis.n_rows_in_duplicate_groups == 3
    assert summary.duplicate_analysis.n_excess_duplicate_rows == 2
    assert summary.duplicate_analysis.duplicate_groups[0].row_positions == (0, 1, 2)


def test_groups_order_by_size_then_first_physical_position():
    rows = [f"U{index}" for index in range(13)]
    for position, value in (
        (4, "A"),
        (9, "A"),
        (12, "A"),
        (1, "B"),
        (7, "B"),
        (5, "C"),
        (8, "C"),
    ):
        rows[position] = value
    summary = _analyzed(pd.DataFrame({"a": rows}))
    _assert_invariants(summary)
    assert [group.row_positions for group in summary.duplicate_analysis.duplicate_groups] == [
        (4, 9, 12),
        (1, 7),
        (5, 8),
    ]
    assert summary.n_rows == 13
    assert _unique_rows(summary) == 9
    assert summary.duplicate_analysis.n_duplicate_groups == 3
    assert summary.duplicate_analysis.n_rows_in_duplicate_groups == 7
    assert summary.duplicate_analysis.n_excess_duplicate_rows == 4
    again = collect_duplicate_analysis(pd.DataFrame({"a": rows}))
    assert again.duplicate_groups == summary.duplicate_analysis.duplicate_groups
    assert again.n_duplicate_groups == 3
    assert again.n_rows_in_duplicate_groups == 7
    assert again.n_excess_duplicate_rows == 4
    assert again.n_unique_rows(13) == 9


def test_repeated_collection_is_deterministic():
    frame = pd.DataFrame(
        {
            "a": [3, 1, 3, 2, 1, 2, 3],
            "b": ["x", "y", "x", "z", "y", "z", "x"],
        }
    )
    first = collect_duplicate_analysis(frame)
    second = collect_duplicate_analysis(frame)
    assert first == second
    assert [group.size for group in first.duplicate_groups] == [3, 2, 2]


def test_row_identity_is_physical_position_not_the_index():
    frame = pd.DataFrame({"a": [1, 1, 2]}, index=[10, 99, 10])
    summary = _analyzed(frame)
    _assert_invariants(summary)
    assert summary.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)
    labeled = pd.DataFrame({"a": [1, 2]}, index=[5, 5])
    assert _analyzed(labeled).duplicate_analysis.n_duplicate_groups == 0
    multi = pd.DataFrame(
        {"a": [1, 1]},
        index=pd.MultiIndex.from_tuples([("left", 1), ("right", 2)]),
    )
    assert _analyzed(multi).duplicate_analysis.duplicate_groups == (
        DuplicateGroup((0, 1)),
    )


def test_duplicate_column_labels_keep_every_physical_column():
    frame = pd.DataFrame(
        [[1, 2, 3], [1, 2, 3], [1, 9, 3]],
        columns=["x", "x", "y"],
    )
    summary = _analyzed(frame)
    _assert_invariants(summary)
    assert _unique_rows(summary) == 2
    assert summary.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)


def test_non_string_and_multiindex_labels_do_not_define_row_equality():
    labeled = pd.DataFrame([[1, "a"], [1, "a"], [2, "a"]], columns=[1, 2])
    assert _analyzed(labeled).duplicate_analysis.duplicate_groups == (
        DuplicateGroup((0, 1)),
    )
    columns = pd.MultiIndex.from_tuples([("group", "a"), ("group", "b")])
    frame = pd.DataFrame([[1, "a"], [1, "a"], [1, "b"]], columns=columns)
    summary = _analyzed(frame)
    _assert_invariants(summary)
    assert summary.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)
    assert _unique_rows(summary) == 2


@pytest.mark.parametrize(
    "values",
    [
        pd.Series([1, 1, 2], dtype="int64"),
        pd.Series([1, pd.NA, 1, pd.NA], dtype="Int64"),
        pd.Series([1.5, 2.5, 1.5], dtype="float64"),
        pd.Series([True, False, True]),
        pd.Series([True, pd.NA, True, pd.NA], dtype="boolean"),
        pd.Series(["x", "y", "x"], dtype="object"),
        pd.Series(["x", pd.NA, "x", pd.NA], dtype="string"),
        pd.Categorical(["b", "a", "b", None]),
        pd.to_datetime(["2020-01-01", "2021-01-01", "2020-01-01", None]),
        pd.to_datetime(["2020-01-01", "2021-01-01", "2020-01-01"], utc=True),
        pd.to_timedelta(["1 day", "2 days", "1 day", None]),
    ],
)
def test_representative_dtypes_group_exact_values(values: pd.Series):
    summary = _analyzed(pd.DataFrame({"a": values}))
    _assert_invariants(summary)
    assert summary.n_rows == len(values)
    assert summary.duplicate_analysis.n_duplicate_groups >= 1
    assert summary.duplicate_analysis.duplicate_groups[0].size >= 2


def test_exact_values_are_not_normalized():
    text = _analyzed(
        pd.DataFrame({"a": ["Amsterdam", "amsterdam", " Amsterdam ", "Amsterdam"]})
    )
    _assert_invariants(text)
    assert _unique_rows(text) == 3
    assert text.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 3)),)
    spaces = _analyzed(pd.DataFrame({"a": [" ", " ", "  "]}))
    assert spaces.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)
    floats = _analyzed(pd.DataFrame({"a": [1.0, 1.000001, 1.0]}))
    assert floats.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 2)),)
    assert _unique_rows(floats) == 2
    literal = _analyzed(pd.DataFrame({"a": ["NA", None, "NA", None]}))
    _assert_invariants(literal)
    assert [group.row_positions for group in literal.duplicate_analysis.duplicate_groups] == [
        (0, 2),
        (1, 3),
    ]


def test_negative_zero_matches_zero_under_pandas_equality():
    summary = _analyzed(pd.DataFrame({"a": [0.0, -0.0, 1.0]}))
    _assert_invariants(summary)
    assert summary.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)
    assert _unique_rows(summary) == 2


def test_object_column_follows_pandas_equality_for_equal_heterogeneous_values():
    summary = _analyzed(pd.DataFrame({"a": [1, True, 1.0]}))
    _assert_invariants(summary)
    assert _unique_rows(summary) == 1
    assert summary.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1, 2)),)


def test_same_missing_positions_form_one_group():
    repeated = _analyzed(
        pd.DataFrame(
            {
                "a": pd.Series([1, 1, 2], dtype="Int64"),
                "b": pd.Series([pd.NA, pd.NA, pd.NA], dtype="Int64"),
            }
        )
    )
    _assert_invariants(repeated)
    assert repeated.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)
    nat = _analyzed(pd.DataFrame({"when": [pd.NaT, np.nan, pd.NaT]}))
    assert _unique_rows(nat) == 1
    assert nat.duplicate_analysis.duplicate_groups[0].row_positions == (0, 1, 2)


def test_different_missing_positions_are_not_duplicates():
    summary = _analyzed(pd.DataFrame({"a": [1, None], "b": [None, 1]}))
    _assert_invariants(summary)
    assert summary.duplicate_analysis.n_duplicate_groups == 0
    assert _unique_rows(summary) == 2


def test_object_missing_sentinels_share_one_duplicate_group():
    column = pd.DataFrame({"a": [None, np.nan, pd.NA, None]})
    summary = _analyzed(column)
    _assert_invariants(summary)
    assert _unique_rows(summary) == 1
    assert summary.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1, 2, 3)),)
    paired = pd.DataFrame(
        {"a": [None, np.nan, pd.NA], "b": ["x", "x", "x"]},
    )
    assert list(paired.duplicated(keep=False)) == [True, True, True]
    assert _unique_rows(_analyzed(paired)) == 1


def test_unhashable_cells_make_duplicate_analysis_unavailable():
    for values in ([[1, 2], [1, 2]], [{"a": 1}, {"a": 1}], [{"x", "y"}, {"y", "x"}]):
        frame = pd.DataFrame({"a": values})
        analysis = collect_duplicate_analysis(frame)
        assert analysis.available is False
        assert analysis.duplicate_groups == ()
        assert analysis.n_duplicate_groups is None
        assert analysis.n_unique_rows(len(frame)) is None
    mixed = pd.DataFrame({"a": [1, 1], "b": [[1], [2]]})
    mixed_analysis = collect_duplicate_analysis(mixed)
    assert mixed_analysis.available is False
    assert mixed_analysis.n_excess_duplicate_rows is None
    single = collect_duplicate_analysis(pd.DataFrame({"a": [[1, 2]]}))
    assert single.available is True
    assert single.n_unique_rows(1) == 1
    assert single.duplicate_groups == ()
    profiled = analyze_dataframe(pd.DataFrame({"a": [[1, 2]]}))
    assert profiled.duplicate_analysis.available is True
    assert profiled.columns[0].evidence.basic.n_unique_non_missing is None
    tuples = _analyzed(pd.DataFrame({"a": [(1, 2), (1, 2), (1, 3)]}))
    assert tuples.duplicate_analysis.duplicate_groups == (DuplicateGroup((0, 1)),)


def test_zero_size_frames_follow_the_empty_row_definition():
    empty = _analyzed(pd.DataFrame())
    _assert_invariants(empty)
    assert empty.n_rows == 0
    assert _unique_rows(empty) == 0
    assert empty.duplicate_analysis.n_duplicate_groups == 0
    assert empty.duplicate_analysis.n_rows_in_duplicate_groups == 0
    assert empty.duplicate_analysis.n_excess_duplicate_rows == 0
    assert empty.duplicate_analysis.duplicate_groups == ()
    zero_rows = _analyzed(
        pd.DataFrame({"a": pd.Series(dtype="int64"), "b": pd.Series(dtype="object")})
    )
    _assert_invariants(zero_rows)
    assert (
        zero_rows.n_rows,
        _unique_rows(zero_rows),
        zero_rows.duplicate_analysis.n_duplicate_groups,
    ) == (
        0,
        0,
        0,
    )
    one_columnless = _analyzed(pd.DataFrame(index=[4]))
    _assert_invariants(one_columnless)
    assert one_columnless.n_rows == 1
    assert _unique_rows(one_columnless) == 1
    assert one_columnless.duplicate_analysis.duplicate_groups == ()
    wide_empty = pd.DataFrame(index=range(5))
    summary = _analyzed(wide_empty)
    _assert_invariants(summary)
    assert _unique_rows(summary) == 1
    assert summary.duplicate_analysis.n_duplicate_groups == 1
    assert summary.duplicate_analysis.n_rows_in_duplicate_groups == 5
    assert summary.duplicate_analysis.n_excess_duplicate_rows == 4
    assert summary.duplicate_analysis.duplicate_groups == (
        DuplicateGroup((0, 1, 2, 3, 4)),
    )
    assert len(wide_empty.drop_duplicates()) == 5


def test_missing_patterns_do_not_define_duplicate_groups():
    different = pd.DataFrame({"a": [1, 2], "b": [None, None]})
    summary = _analyzed(different)
    assert summary.duplicate_analysis.n_duplicate_groups == 0
    assert summary.n_rows - summary.missing_analysis.n_complete_rows == 2
    same = pd.DataFrame({"a": [1, 1], "b": [None, None]})
    assert _analyzed(same).duplicate_analysis.n_duplicate_groups == 1


def test_analysis_does_not_mutate_or_retain_the_source():
    frame = pd.DataFrame(
        {
            "ints": pd.Series([1, 1, pd.NA], dtype="Int64"),
            "flags": pd.Series([True, True, False], dtype="boolean"),
            "when": pd.to_datetime(
                ["2020-01-01", "2020-01-01", "2020-06-01"], utc=True
            ),
            "labels": pd.Categorical(
                ["b", "b", "a"], categories=["a", "b"], ordered=True
            ),
            "cities": pd.Series(["Amsterdam", "Amsterdam", "Berlin"], dtype="string"),
        }
    )
    frame.index = pd.Index([4, 4, 9], name="row")
    before = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    pd.testing.assert_frame_equal(frame, before)
    assert frame.index.equals(before.index)
    assert list(frame.columns) == list(before.columns)
    assert frame["labels"].cat.ordered is True
    _assert_no_retained_source(analysis)
    _assert_no_retained_source(analysis.duplicate_analysis)
    assert "duplicate_analysis" in {
        field.name for field in dataclasses.fields(analysis)
    }
    module_source = inspect.getsource(duplicate_module)
    assert ".groupby(" not in module_source
    assert "hash_pandas_object" not in module_source
    assert "drop_duplicates" not in module_source
    assert ".duplicated(" not in module_source


def test_models_are_frozen_and_reject_inconsistent_groups():
    summary = _analyzed(pd.DataFrame({"a": [1, 1]}))
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.n_rows = 0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.duplicate_analysis.duplicate_groups[0].row_positions = ()  # type: ignore[misc]
    with pytest.raises(TypeError):
        summary.duplicate_analysis.duplicate_groups[0] = DuplicateGroup((0, 1))  # type: ignore[index]
    with pytest.raises(ValueError, match="at least two"):
        DuplicateGroup((0,))
    with pytest.raises(ValueError, match="strictly increasing"):
        DuplicateGroup((2, 1))
    with pytest.raises(TypeError, match="tuple"):
        DuplicateGroup([0, 1])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-negative int"):
        DuplicateGroup((True, 1))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="more than one duplicate group"):
        DuplicateAnalysis(
            duplicate_groups=(DuplicateGroup((0, 1)), DuplicateGroup((1, 2)))
        )
    with pytest.raises(ValueError, match="descending size"):
        DuplicateAnalysis(
            duplicate_groups=(DuplicateGroup((3, 4)), DuplicateGroup((0, 1, 2)))
        )
    with pytest.raises(TypeError, match="tuple"):
        DuplicateAnalysis(duplicate_groups=[DuplicateGroup((0, 1))])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DuplicateGroup"):
        DuplicateAnalysis(duplicate_groups=("group",))  # type: ignore[arg-type]
    retained = DuplicateAnalysis(duplicate_groups=(DuplicateGroup((0, 1, 2)),))
    with pytest.raises(ValueError, match="cannot exceed n_rows"):
        retained.n_unique_rows(1)
    with pytest.raises(ValueError, match="at least one unique row"):
        retained.n_unique_rows(2)
    attached = _analyzed(pd.DataFrame({"a": [1, 2]}))
    with pytest.raises(ValueError, match="less than n_rows"):
        DatasetAnalysis(
            n_rows=attached.n_rows,
            n_columns=attached.n_columns,
            n_cells=attached.n_cells,
            columns=attached.columns,
            missing_analysis=attached.missing_analysis,
            duplicate_analysis=DuplicateAnalysis(
                duplicate_groups=(DuplicateGroup((0, 2)),)
            ),
            relationship_analysis=attached.relationship_analysis,
            anomaly_analysis=attached.anomaly_analysis,
            target_analysis=attached.target_analysis,
            target_leakage=attached.target_leakage,
            target_diagnostic=attached.target_diagnostic,
        )
    with pytest.raises(TypeError, match="pandas DataFrame"):
        collect_duplicate_analysis(pd.Series([1, 1]))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="containing every row"):
        DatasetAnalysis(
            n_rows=5,
            n_columns=0,
            n_cells=0,
            columns=(),
            missing_analysis=missing_analysis_for_margins(5, ()),
            duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
            relationship_analysis=RelationshipAnalysis(
                n_rows=0,
                n_total_pairs=0,
                n_supported_pairs=0,
                n_analyzed_pairs=0,
                n_unimplemented_family_pairs=0,
                n_ineligible_pairs=0,
                unimplemented_family_counts=(),
                relationships=(),
            ),
            anomaly_analysis=_NO_ANOMALIES,
        )
    with pytest.raises(TypeError, match="DuplicateAnalysis"):
        DatasetAnalysis(
            n_rows=0,
            n_columns=0,
            n_cells=0,
            columns=(),
            missing_analysis=missing_analysis_for_margins(0, ()),
            duplicate_analysis=None,  # type: ignore[arg-type]
            relationship_analysis=RelationshipAnalysis(
                n_rows=0,
                n_total_pairs=0,
                n_supported_pairs=0,
                n_analyzed_pairs=0,
                n_unimplemented_family_pairs=0,
                n_ineligible_pairs=0,
                unimplemented_family_counts=(),
                relationships=(),
            ),
            anomaly_analysis=_NO_ANOMALIES,
        )


def test_collector_rejects_unsafe_factorize_results(monkeypatch: pytest.MonkeyPatch):
    frame = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    def _short(values: object, sort: bool = False) -> tuple[np.ndarray, np.ndarray]:
        del values, sort
        return np.array([0], dtype=np.int64), np.array([0])

    monkeypatch.setattr(pd, "factorize", _short)
    with pytest.raises(ValueError, match="one code per row"):
        collect_duplicate_analysis(frame)

    def _floats(values: object, sort: bool = False) -> tuple[np.ndarray, np.ndarray]:
        del values, sort
        return np.array([0.5, 1.5]), np.array([0.5, 1.5])

    monkeypatch.setattr(pd, "factorize", _floats)
    with pytest.raises(TypeError, match="integers"):
        collect_duplicate_analysis(frame)

    def _other(values: object, sort: bool = False) -> tuple[np.ndarray, np.ndarray]:
        del values, sort
        raise TypeError("boom")

    monkeypatch.setattr(pd, "factorize", _other)
    with pytest.raises(TypeError, match="boom"):
        collect_duplicate_analysis(frame)


def test_overview_duplicate_counts_follow_the_retained_analysis():
    frames = [
        pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]}),
        pd.DataFrame(),
        pd.DataFrame(index=range(5)),
        pd.DataFrame({"a": pd.Series(dtype="int64")}),
    ]
    for frame in frames:
        analysis = analyze_dataframe(frame)
        overview = build_dataset_overview(analysis)
        _assert_invariants(analysis)
        unique = _unique_rows(analysis)
        excess = analysis.duplicate_analysis.n_excess_duplicate_rows
        assert overview.n_unique_rows == unique
        assert overview.n_excess_duplicate_rows == excess
        if analysis.n_rows == 0:
            assert overview.unique_row_ratio is None
            assert overview.excess_duplicate_row_ratio is None
        else:
            assert unique is not None and excess is not None
            assert overview.unique_row_ratio == pytest.approx(unique / analysis.n_rows)
            assert overview.excess_duplicate_row_ratio == pytest.approx(
                excess / analysis.n_rows
            )
        assert "duplicate_groups" not in {
            field.name for field in dataclasses.fields(overview)
        }
    overview_source = inspect.getsource(build_dataset_overview)
    assert "factorize" not in overview_source
    assert ".duplicated(" not in overview_source


def test_duplicate_counts_are_not_a_separate_overview_scan(
    monkeypatch: pytest.MonkeyPatch,
):
    analysis = analyze_dataframe(pd.DataFrame({"a": [1, 1, 2]}))

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("overview must not rescan duplicate rows")

    monkeypatch.setattr(duplicate_module, "collect_duplicate_analysis", _fail)
    monkeypatch.setattr(pd, "factorize", _fail)
    overview = build_dataset_overview(analysis)
    assert overview.n_unique_rows == 2
    assert overview.n_excess_duplicate_rows == 1
