"""TSK-033: exact observed distribution for a Categorical column."""

from __future__ import annotations

import dataclasses
import math
from typing import Optional
from typing import Sequence
from typing import Tuple

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.categorical as categorical_module
import pytics.analysis.column as column_module
import pytics.analysis.target as target_module
from pytics.analysis.categorical import CategoricalDescriptiveAnalysis
from pytics.analysis.categorical import ObservedCategoryCount
from pytics.analysis.categorical import collect_categorical_descriptive_analysis
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.semantics.interpretation import SemanticType

_RETAINED = (pd.DataFrame, pd.Series, pd.Index, np.ndarray, np.generic)
_Level = Tuple[object, int]


def _missing(value: object) -> bool:
    if value is None or value is pd.NA or value is pd.NaT:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def _independent_observed(
    values: Sequence[object],
    categories: Sequence[object],
) -> Tuple[_Level, ...]:
    """Count the fixture without calling the categorical collector.

    Missing values are excluded. Unused vocabulary entries stay at zero
    and are then dropped. The remaining order is the vocabulary order.
    """
    counts = [0 for _ in categories]
    for value in values:
        if _missing(value):
            continue
        matched = [
            index
            for index, category in enumerate(categories)
            if value == category and type(value) is type(category)
        ]
        assert len(matched) == 1
        counts[matched[0]] += 1
    return tuple(
        (categories[index], counts[index])
        for index in range(len(categories))
        if counts[index] > 0
    )


def _assert_matches_fixture(
    result: CategoricalDescriptiveAnalysis,
    values: Sequence[object],
    categories: Sequence[object],
    *,
    ordered: bool,
) -> None:
    expected = _independent_observed(values, categories)
    n_missing = sum(1 for value in values if _missing(value))
    n_non_missing = len(values) - n_missing
    assert [(level.value, level.count) for level in result.levels] == list(expected)
    assert result.n_non_missing == n_non_missing
    assert result.n_observed == len(expected)
    assert result.ordered is ordered
    assert sum(level.count for level in result.levels) == n_non_missing
    if n_non_missing == 0:
        assert result.proportions == ()
        assert result.most_frequent_proportion is None
        assert result.least_frequent_proportion is None
        assert result.most_frequent_values == ()
        assert result.least_frequent_values == ()
        return
    proportions = tuple(count / n_non_missing for _value, count in expected)
    assert result.proportions == pytest.approx(proportions)
    assert sum(result.proportions) == pytest.approx(1.0)
    assert all(math.isfinite(item) and 0.0 < item <= 1.0 for item in result.proportions)
    largest = max(count for _value, count in expected)
    smallest = min(count for _value, count in expected)
    assert result.most_frequent_count == largest
    assert result.least_frequent_count == smallest
    assert result.most_frequent_proportion == pytest.approx(largest / n_non_missing)
    assert result.least_frequent_proportion == pytest.approx(smallest / n_non_missing)
    assert result.most_frequent_values == tuple(
        value for value, count in expected if count == largest
    )
    assert result.least_frequent_values == tuple(
        value for value, count in expected if count == smallest
    )
    assert result.singleton_count == sum(1 for _value, count in expected if count == 1)


def _describe(
    values: Sequence[object],
    categories: Sequence[object],
    *,
    ordered: bool,
) -> CategoricalDescriptiveAnalysis:
    series = pd.Series(
        pd.Categorical(list(values), categories=list(categories), ordered=ordered)
    )
    before = series.copy()
    result = collect_categorical_descriptive_analysis(series)
    pd.testing.assert_series_equal(series, before)
    return result


def _walk(value: object, seen: Optional[set[int]] = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _RETAINED)
    assert not callable(value)
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _walk(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _walk(item, seen)


def test_ordinary_categorical_distribution_matches_an_independent_count():
    values = ["b", "a", "b", None, "a", "c"]
    categories = ["c", "a", "b", "d"]
    result = _describe(values, categories, ordered=False)
    _assert_matches_fixture(result, values, categories, ordered=False)
    assert result.most_frequent_values == ("a", "b")
    assert result.least_frequent_values == ("c",)
    assert "d" not in [level.value for level in result.levels]
    repeated = _describe(list(reversed(values)), categories, ordered=False)
    assert repeated == result


def test_ordered_categorical_drops_unused_levels_and_keeps_vocabulary_order():
    values = ["b", "a", "b", None]
    categories = ["c", "b", "a"]
    result = _describe(values, categories, ordered=True)
    _assert_matches_fixture(result, values, categories, ordered=True)
    assert [level.value for level in result.levels] == ["b", "a"]
    assert result.ordered is True
    analyzed = analyze_series(
        pd.Series(
            pd.Categorical(values, categories=categories, ordered=True),
            name="rank",
        ),
        label="rank",
    )
    assert analyzed.inferred.selected_type is SemanticType.CATEGORICAL
    assert analyzed.physical.categorical_ordered is True
    assert analyzed.categorical_analysis == result
    assert analyzed.categorical_analysis is not None
    assert (
        analyzed.categorical_analysis.ordered is analyzed.physical.categorical_ordered
    )


def test_one_observed_level_is_described_only_outside_constant_resolution():
    values = ["only", "only", None]
    categories = ["unused", "only"]
    result = _describe(values, categories, ordered=False)
    _assert_matches_fixture(result, values, categories, ordered=False)
    assert result.n_observed == 1
    assert result.singleton_count == 0
    assert result.most_frequent_values == ("only",)
    constant = analyze_series(pd.Series(pd.Categorical(["only", "only"])))
    assert constant.inferred.selected_type is SemanticType.CONSTANT
    assert constant.categorical_analysis is None
    assert constant.evidence.frequency is None


def test_missing_values_are_not_a_class_and_reconcile_with_the_population():
    values = ["a", None, "b", pd.NA, "a", np.nan]
    categories = ["b", "a"]
    series = pd.Series(pd.Categorical(values, categories=categories))
    analyzed = analyze_series(series, label="city")
    result = analyzed.categorical_analysis
    assert result is not None
    _assert_matches_fixture(
        result, ["a", None, "b", None, "a", None], categories, ordered=False
    )
    basic = analyzed.evidence.basic
    assert result.n_non_missing + basic.n_missing == basic.n_total == len(values)
    assert sum(level.count for level in result.levels) == basic.n_non_missing
    assert None not in [level.value for level in result.levels]
    assert result.proportions[0] != pytest.approx(result.levels[0].count / len(values))
    empty = collect_categorical_descriptive_analysis(
        pd.Series(pd.Categorical([None, None], categories=["a", "b"]))
    )
    assert empty.n_non_missing == 0
    assert empty.levels == ()
    assert empty.n_observed == 0
    all_missing = analyze_series(pd.Series([pd.NA, pd.NA], dtype="category"))
    assert all_missing.inferred.selected_type is SemanticType.EMPTY
    assert all_missing.categorical_analysis is None


def test_non_string_categories_keep_their_values():
    integers = [2, 1, 2, None, 1]
    integer_categories = [3, 2, 1]
    integer_result = _describe(integers, integer_categories, ordered=False)
    _assert_matches_fixture(
        integer_result,
        integers,
        integer_categories,
        ordered=False,
    )
    assert all(type(level.value) is int for level in integer_result.levels)
    tuples = [(3,), (1, 2), (1, 2), None]
    tuple_categories = [(1, 2), (3,), (1,)]
    tuple_result = _describe(tuples, tuple_categories, ordered=True)
    _assert_matches_fixture(tuple_result, tuples, tuple_categories, ordered=True)
    assert type(tuple_result.levels[0].value) is tuple
    early = pd.Timestamp("2020-01-01")
    late = pd.Timestamp("2020-01-02")
    unused = pd.Timestamp("2020-01-03")
    stamps = [late, early, pd.NaT, late]
    stamp_categories = [unused, early, late]
    stamp_result = _describe(stamps, stamp_categories, ordered=True)
    _assert_matches_fixture(stamp_result, stamps, stamp_categories, ordered=True)
    assert stamp_result.levels[0].value == early
    assert type(stamp_result.levels[0].value) is pd.Timestamp
    numpy_integers = pd.Series(
        pd.Categorical(np.array([np.int64(2), np.int64(1), np.int64(2)]))
    )
    retained = collect_categorical_descriptive_analysis(numpy_integers)
    assert [type(level.value) for level in retained.levels] == [int, int]
    negative_zero = collect_categorical_descriptive_analysis(
        pd.Series(pd.Categorical([-0.0, 1.0, -0.0]))
    )
    assert negative_zero.levels[0].value == 0.0
    assert math.copysign(1.0, negative_zero.levels[0].value) == 1.0


def test_pandas_equality_can_collapse_one_true_and_one_point_zero():
    raw = [1, True, 1.0, 2]
    series = pd.Series(raw, dtype="category")
    result = collect_categorical_descriptive_analysis(series)
    assert list(series.cat.categories) == [1, 2]
    assert [(level.value, level.count) for level in result.levels] == [(1, 3), (2, 1)]
    assert type(result.levels[0].value) is int
    kind_counts = {}
    for value in raw:
        kind_counts[type(value)] = kind_counts.get(type(value), 0) + 1
    assert kind_counts == {int: 2, bool: 1, float: 1}
    with pytest.raises(ValueError, match="unique"):
        pd.Categorical(raw, categories=[1, True, 1.0, 2])
    with pytest.raises(ValueError, match="Python equality"):
        CategoricalDescriptiveAnalysis(
            n_non_missing=2,
            ordered=False,
            levels=(
                ObservedCategoryCount(value=1, count=1),
                ObservedCategoryCount(value=True, count=1),
            ),
        )


def test_high_cardinality_distribution_stays_exact():
    n_levels = 4000
    categories = [f"level-{index:04d}" for index in range(n_levels)]
    values: list[object] = []
    for index, label in enumerate(categories):
        values.extend([label] * ((index % 3) + 1))
    values.append(None)
    result = _describe(values, categories, ordered=False)
    _assert_matches_fixture(result, values, categories, ordered=False)
    assert result.n_observed == n_levels
    assert result.levels[0].count == 1
    assert result.levels[2].count == 3
    analyzed = analyze_series(pd.Series(pd.Categorical(categories)))
    assert analyzed.evidence.frequency is not None
    assert analyzed.evidence.frequency.exact_distinct_non_missing_values is None
    assert analyzed.categorical_analysis is not None
    assert analyzed.categorical_analysis.n_observed == n_levels
    assert analyzed.categorical_analysis.singleton_count == n_levels


def test_categorical_description_does_not_require_target_selection(
    monkeypatch: pytest.MonkeyPatch,
):
    frame = pd.DataFrame(
        {
            "city": pd.Series(["a", "b", "a", None], dtype="category"),
            "amount": [1, 2, 3, 4],
            "other": pd.Series(["x", "y", "x", "z"], dtype="category"),
        }
    )
    calls = {"n": 0}
    real = categorical_module.collect_categorical_descriptive_analysis

    def spy(series: pd.Series) -> CategoricalDescriptiveAnalysis:
        calls["n"] += 1
        return real(series)

    monkeypatch.setattr(column_module, "collect_categorical_descriptive_analysis", spy)
    plain = analyze_dataframe(frame)
    assert plain.target_analysis is None
    assert calls["n"] == 2
    assert plain.columns[0].categorical_analysis is not None
    assert plain.columns[1].categorical_analysis is None
    assert plain.columns[1].numeric_analysis is not None
    assert plain.columns[1].boolean_analysis is None
    assert plain.columns[2].categorical_analysis is not None
    calls["n"] = 0
    targeted = analyze_dataframe(frame, target="city")
    assert calls["n"] == 2
    target = targeted.target_analysis
    assert target is not None
    assert target.categorical_facts is targeted.columns[0].categorical_analysis
    assert target.numeric_facts is None
    assert target.boolean_facts is None
    calls["n"] = 0
    project = target_module.project_target_analysis(
        targeted.columns,
        targeted.relationship_analysis.relationships,
        position=0,
        n_rows=targeted.n_rows,
    )
    assert calls["n"] == 0
    assert project.categorical_facts is target.categorical_facts
    numeric = analyze_series(pd.Series([0, 1, 0, 1], dtype="int64"))
    boolean = analyze_series(pd.Series([True, False, True]))
    assert numeric.categorical_analysis is None
    assert numeric.numeric_analysis is not None
    assert boolean.categorical_analysis is None
    assert boolean.boolean_analysis is not None


def test_categorical_target_exposes_the_distribution_without_a_verdict():
    frame = pd.DataFrame(
        {
            "city": pd.Series(
                pd.Categorical(
                    ["b", "a", "b", None, "a"],
                    categories=["c", "b", "a"],
                    ordered=True,
                )
            ),
            "amount": [1.0, 2.0, 3.0, 4.0, 5.0],
            "note": pd.Series(["x", "y", "x", "y", "z"], dtype="category"),
        }
    )
    plain = analyze_dataframe(frame)
    analysis = analyze_dataframe(frame, target="city")
    target = analysis.target_analysis
    assert target is not None
    facts = target.categorical_facts
    assert facts is analysis.columns[0].categorical_analysis
    assert facts is not None
    assert facts.ordered is True
    assert [(level.value, level.count) for level in facts.levels] == [
        ("b", 2),
        ("a", 2),
    ]
    assert facts.n_non_missing == 4
    assert target.population.n_target_non_missing == 4
    assert target.population.n_target_missing == 1
    assert (
        target.population.n_target_non_missing + target.population.n_target_missing
        == analysis.n_rows
    )
    assert sum(level.count for level in facts.levels) == facts.n_non_missing
    assert sum(facts.proportions) == pytest.approx(1.0)
    assert "problem_type" not in target.__dataclass_fields__
    assert not any("balance" in name for name in target.__dataclass_fields__)
    assert [link.other_position for link in target.relationships] == [1, 2]
    assert analysis.relationship_analysis == plain.relationship_analysis
    for link in target.relationships:
        if link.relationship is None:
            continue
        retained = next(
            record
            for record in analysis.relationship_analysis.relationships
            if record.left_position == link.relationship.left_position
            and record.right_position == link.relationship.right_position
        )
        assert link.relationship is retained


def test_target_attachment_rejects_a_copied_categorical_distribution() -> None:
    frame = pd.DataFrame(
        {
            "city": pd.Series(["a", "a", "b", None], dtype="category"),
            "amount": [1.0, 2.0, 3.0, 4.0],
        }
    )
    analysis = analyze_dataframe(frame, target="city")
    assert analysis.target_analysis is not None
    assert analysis.target_analysis.categorical_facts is not None
    with pytest.raises(ValueError, match="retained descriptive analysis"):
        DatasetAnalysis(
            n_rows=analysis.n_rows,
            n_columns=analysis.n_columns,
            n_cells=analysis.n_cells,
            columns=analysis.columns,
            missing_analysis=analysis.missing_analysis,
            duplicate_analysis=analysis.duplicate_analysis,
            relationship_analysis=analysis.relationship_analysis,
            anomaly_analysis=analysis.anomaly_analysis,
            target_analysis=dataclasses.replace(
                analysis.target_analysis,
                categorical_facts=dataclasses.replace(
                    analysis.target_analysis.categorical_facts
                ),
            ),
        )
    facts = analysis.target_analysis.categorical_facts
    assert [(level.value, level.count) for level in facts.levels] == [
        ("a", 2),
        ("b", 1),
    ]
    _walk(analysis.target_analysis)


def test_collector_rejects_non_label_storage():
    rejected = [
        pd.Series([1, 2], dtype="int64"),
        pd.Series([True, False]),
        pd.Series([1.0, 2.0]),
        pd.DataFrame({"city": ["a", "b"]}),
        ["a", "b"],
        None,
    ]
    for value in rejected:
        with pytest.raises(TypeError):
            collect_categorical_descriptive_analysis(value)  # type: ignore[arg-type]
    labels = collect_categorical_descriptive_analysis(
        pd.Series(["b", "a", "b"], dtype="string")
    )
    assert labels.ordered is None
    assert [(level.value, level.count) for level in labels.levels] == [
        ("b", 2),
        ("a", 1),
    ]


def test_models_reject_inconsistent_distributions():
    with pytest.raises(ValueError, match="positive int"):
        ObservedCategoryCount(value="a", count=0)
    with pytest.raises(ValueError, match="non-negative int"):
        CategoricalDescriptiveAnalysis(
            n_non_missing=-1,
            ordered=False,
            levels=(),
        )
    with pytest.raises(TypeError, match="ordered"):
        CategoricalDescriptiveAnalysis(
            n_non_missing=0,
            ordered=np.True_,  # type: ignore[arg-type]
            levels=(),
        )
    with pytest.raises(TypeError, match="tuple"):
        CategoricalDescriptiveAnalysis(
            n_non_missing=0,
            ordered=None,
            levels=["a"],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="sum"):
        CategoricalDescriptiveAnalysis(
            n_non_missing=2,
            ordered=False,
            levels=(ObservedCategoryCount(value="a", count=1),),
        )
    with pytest.raises(ValueError, match="no observed levels"):
        CategoricalDescriptiveAnalysis(
            n_non_missing=0,
            ordered=False,
            levels=(ObservedCategoryCount(value="a", count=1),),
        )
    with pytest.raises(ValueError, match="has observed levels"):
        CategoricalDescriptiveAnalysis(n_non_missing=1, ordered=False, levels=())
    with pytest.raises(TypeError, match="container"):
        ObservedCategoryCount(value=pd.Index(["a"]), count=1)
    with pytest.raises(TypeError, match="callable"):
        ObservedCategoryCount(value=len, count=1)
    with pytest.raises(TypeError, match="finite"):
        ObservedCategoryCount(value=float("nan"), count=1)
    with pytest.raises(TypeError, match="hashable"):
        ObservedCategoryCount(value=["a"], count=1)
    with pytest.raises(TypeError, match="observed category counts"):
        CategoricalDescriptiveAnalysis(
            n_non_missing=1,
            ordered=False,
            levels=("a",),  # type: ignore[arg-type]
        )
    empty = CategoricalDescriptiveAnalysis(n_non_missing=0, ordered=None, levels=())
    assert empty.most_frequent_count == 0
    assert empty.least_frequent_count == 0
    assert empty.most_frequent_proportion is None
    assert empty.least_frequent_proportion is None
    assert empty.most_frequent_values == ()
    assert empty.least_frequent_values == ()
    kept = ObservedCategoryCount(value=1 + 2j, count=1)
    assert kept.value == 1 + 2j
    with pytest.raises(TypeError, match="finite"):
        ObservedCategoryCount(value=complex(float("nan"), 0.0), count=1)
    blank = collect_categorical_descriptive_analysis(
        pd.Series(pd.Categorical([], categories=["a", "b"]))
    )
    assert blank.n_non_missing == 0
    assert blank.levels == ()
    assert not hasattr(pytics, "CategoricalDescriptiveAnalysis")
    assert not hasattr(pytics, "collect_categorical_descriptive_analysis")


def test_column_analysis_rejects_a_mismatched_distribution():
    analyzed = analyze_series(
        pd.Series(pd.Categorical(["a", "b", "a"], ordered=False)),
        label="city",
    )
    other = CategoricalDescriptiveAnalysis(
        n_non_missing=3,
        ordered=False,
        levels=(
            ObservedCategoryCount(value="a", count=2),
            ObservedCategoryCount(value="b", count=1),
        ),
    )
    assert analyzed.categorical_analysis == other
    numeric = analyze_series(pd.Series([1, 2, 3]))
    with pytest.raises(ValueError, match="selected semantic type is Categorical"):
        ColumnAnalysis(
            position=numeric.position,
            label=numeric.label,
            physical=numeric.physical,
            evidence=numeric.evidence,
            inferred=numeric.inferred,
            categorical_analysis=other,
        )
    with pytest.raises(ValueError, match="n_non_missing"):
        ColumnAnalysis(
            position=analyzed.position,
            label=analyzed.label,
            physical=analyzed.physical,
            evidence=analyzed.evidence,
            inferred=analyzed.inferred,
            categorical_analysis=CategoricalDescriptiveAnalysis(
                n_non_missing=1,
                ordered=False,
                levels=(ObservedCategoryCount(value="a", count=1),),
            ),
        )


def test_code_counts_reject_a_broken_code_array(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    series = pd.Series(pd.Categorical(["a", "b"]))

    def _two_dimensional(*_args: object, **_kwargs: object) -> np.ndarray:
        return np.array([[0, 1]])

    monkeypatch.setattr(categorical_module.np, "asarray", _two_dimensional)
    with pytest.raises(ValueError, match="one-dimensional"):
        collect_categorical_descriptive_analysis(series)


def test_code_counts_reject_non_integer_and_out_of_range_codes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    series = pd.Series(pd.Categorical(["a", "b"]))

    def _floats(*_args: object, **_kwargs: object) -> np.ndarray:
        return np.array([0.5, 1.5])

    monkeypatch.setattr(categorical_module.np, "asarray", _floats)
    with pytest.raises(TypeError, match="integers"):
        collect_categorical_descriptive_analysis(series)
    monkeypatch.undo()

    def _below(*_args: object, **_kwargs: object) -> np.ndarray:
        return np.array([-2, 0])

    monkeypatch.setattr(categorical_module.np, "asarray", _below)
    with pytest.raises(ValueError, match="vocabulary index"):
        collect_categorical_descriptive_analysis(series)
    monkeypatch.undo()

    def _outside(*_args: object, **_kwargs: object) -> np.ndarray:
        return np.array([0, 5])

    monkeypatch.setattr(categorical_module.np, "asarray", _outside)
    with pytest.raises(ValueError, match="outside the categorical vocabulary"):
        collect_categorical_descriptive_analysis(series)


def test_code_counts_reject_a_bincount_that_drops_observations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    series = pd.Series(pd.Categorical(["a", "b"]))

    def _short(observed: np.ndarray, minlength: int) -> np.ndarray:
        del observed, minlength
        return np.array([1])

    monkeypatch.setattr(categorical_module.np, "bincount", _short)
    with pytest.raises(ValueError, match="do not match"):
        collect_categorical_descriptive_analysis(series)
