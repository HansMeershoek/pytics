"""TSK-024: Numeric × Numeric relationship analysis."""

from __future__ import annotations

import dataclasses
import inspect
import math
import warnings

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

import pytics
import pytics.analysis.relationship as relationship_module
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.missing import MissingAnalysis
from pytics.analysis.relationship import AssociationMethod
from pytics.analysis.relationship import AssociationResult
from pytics.analysis.relationship import CorrelationEstimate
from pytics.analysis.relationship import CorrelationInterval
from pytics.analysis.relationship import CorrelationIntervalMethod
from pytics.analysis.relationship import EffectDirection
from pytics.analysis.relationship import FrequentistEvidence
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericComputation
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import PairPopulation
from pytics.analysis.relationship import RelationshipAnalysis
from pytics.analysis.relationship import RelationshipFamily
from pytics.analysis.relationship import RelationshipsSummary
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.relationship import UnimplementedFamilyCount
from pytics.analysis.relationship import UnimplementedRelationshipFamily
from pytics.analysis.relationship import build_relationships_summary
from pytics.analysis.relationship import collect_relationship_analysis
from pytics.analysis.relationship import relationship_analysis_for_columns
from pytics.semantics.interpretation import SemanticType

_RETAINED = (pd.DataFrame, pd.Series, pd.Index, np.ndarray)
_UUIDS = (
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
)
_NORMAL_Z_95 = 1.959963984540054


def _summary(frame: pd.DataFrame) -> RelationshipsSummary:
    return build_relationships_summary(analyze_dataframe(frame))


def _only(frame: pd.DataFrame) -> NumericNumericRelationship:
    summary = _summary(frame)
    assert summary.n_analyzed_pairs == 1
    return summary.relationships[0]


def _fisher_z(estimate: float, n_paired: int) -> tuple[float, float]:
    transformed = math.atanh(estimate)
    half_width = _NORMAL_Z_95 / math.sqrt(n_paired - 3)
    return (
        math.tanh(transformed - half_width),
        math.tanh(transformed + half_width),
    )


def _assert_no_retained_source(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _RETAINED)
    assert not type(value).__module__.startswith(("scipy", "pandas.core", "numpy"))
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_no_retained_source(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_retained_source(item, seen)


def _assert_counts(summary: RelationshipsSummary) -> None:
    expected = summary.n_columns * (summary.n_columns - 1) // 2
    assert summary.n_total_pairs == expected
    assert summary.n_supported_pairs == len(summary.relationships)
    assert summary.n_analyzed_pairs == summary.n_supported_pairs
    assert (
        summary.n_supported_pairs
        + summary.n_unimplemented_family_pairs
        + summary.n_ineligible_pairs
        == summary.n_total_pairs
    )
    assert summary.n_unsupported_pairs == (
        summary.n_unimplemented_family_pairs + summary.n_ineligible_pairs
    )
    assert sum(item.n_pairs for item in summary.unimplemented_family_counts) == (
        summary.n_unimplemented_family_pairs
    )
    assert summary.primary_method is AssociationMethod.SPEARMAN
    assert summary.population is PairPopulation.PAIRWISE_FINITE
    assert summary.computation is NumericComputation.FLOAT64
    assert summary.confidence_level == 0.95
    assert summary.multiple_testing is MultipleTestingAdjustment.NOT_APPLIED
    assert summary.implemented_family is RelationshipFamily.NUMERIC_NUMERIC
    for relationship in summary.relationships:
        assert relationship.family is RelationshipFamily.NUMERIC_NUMERIC
        assert relationship.population is PairPopulation.PAIRWISE_FINITE
        assert relationship.left_position < relationship.right_position
        assert (
            relationship.n_excluded == relationship.n_total_rows - relationship.n_paired
        )
        assert relationship.spearman.method is AssociationMethod.SPEARMAN
        assert relationship.pearson.method is AssociationMethod.PEARSON
        assert relationship.spearman.n_observations == relationship.n_paired
        assert relationship.pearson.n_observations == relationship.n_paired
        for method in relationship.methods:
            assert (
                method.frequentist.adjustment is MultipleTestingAdjustment.NOT_APPLIED
            )
            assert method.frequentist.adjusted_p_value is None
            if method.estimate.availability is ResultAvailability.AVAILABLE:
                assert method.estimate.value is not None
                assert math.isfinite(method.estimate.value)
                assert type(method.estimate.value) is float
            else:
                assert method.estimate.value is None
            assert not hasattr(method, "is_significant")


def test_one_numeric_pair_keeps_spearman_and_pearson() -> None:
    frame = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    before = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    summary = build_relationships_summary(analysis)
    pd.testing.assert_frame_equal(frame, before)
    _assert_counts(summary)
    _assert_no_retained_source(analysis)
    _assert_no_retained_source(summary)
    assert summary.n_total_pairs == 1
    assert summary.n_supported_pairs == 1
    assert summary.n_ineligible_pairs == 0
    relationship = summary.relationships[0]
    assert (relationship.left_position, relationship.right_position) == (0, 1)
    assert relationship.left_label == "x"
    assert relationship.right_label == "y"
    assert relationship.n_total_rows == 5
    assert relationship.n_paired == 5
    assert relationship.n_excluded == 0
    assert relationship.spearman.estimate.value == pytest.approx(1.0)
    assert relationship.spearman.estimate.direction is EffectDirection.POSITIVE
    assert relationship.spearman.frequentist.p_value == pytest.approx(0.0)
    assert relationship.spearman.confidence_interval.reason is (
        UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD
    )
    assert relationship.pearson.estimate.value == pytest.approx(1.0)
    assert relationship.pearson.estimate.direction is EffectDirection.POSITIVE
    assert relationship.pearson.frequentist.p_value == pytest.approx(0.0)
    assert relationship.pearson.confidence_interval.reason is (
        UnavailabilityReason.BOUNDARY_CORRELATION
    )
    retained = analysis.relationship_analysis
    assert retained.primary_method is AssociationMethod.SPEARMAN
    assert retained.population is PairPopulation.PAIRWISE_FINITE
    assert retained.computation is NumericComputation.FLOAT64
    assert retained.confidence_level == 0.95
    assert retained.multiple_testing is MultipleTestingAdjustment.NOT_APPLIED
    assert retained.implemented_family is RelationshipFamily.NUMERIC_NUMERIC
    assert retained.n_unsupported_pairs == 0
    assert summary.relationships[0] is not retained.relationships[0]
    assert summary.relationships == analysis.relationship_analysis.relationships
    assert not hasattr(pytics, "build_relationships_summary")
    assert not hasattr(pytics, "RelationshipAnalysis")


def test_duplicate_labels_stay_distinct_physical_pairs() -> None:
    frame = pd.DataFrame(
        [[1, 10, 2], [2, 20, 3], [3, 30, 4], [4, 40, 5]],
        columns=["x", "x", "y"],
    )
    summary = _summary(frame)
    _assert_counts(summary)
    assert summary.n_total_pairs == 3
    assert summary.n_supported_pairs == 3
    assert [
        (item.left_position, item.right_position) for item in summary.relationships
    ] == [
        (0, 1),
        (0, 2),
        (1, 2),
    ]
    assert [item.left_label for item in summary.relationships] == ["x", "x", "x"]
    assert [item.right_label for item in summary.relationships] == ["x", "y", "y"]
    assert summary.relationships[0].spearman.estimate.value == pytest.approx(1.0)
    assert summary.relationships[1].pearson.estimate.value == pytest.approx(1.0)
    assert (
        summary.relationships[2].pearson.estimate.direction is EffectDirection.POSITIVE
    )


def test_non_string_and_multiindex_labels_are_preserved() -> None:
    numbered = pd.DataFrame([[1, 2], [2, 3], [3, 4], [4, 5]])
    numbered.columns = [7, ("group", "value")]
    summary = _summary(numbered)
    relationship = summary.relationships[0]
    assert relationship.left_label == 7
    assert type(relationship.left_label) is int
    assert relationship.right_label == ("group", "value")
    nested = pd.DataFrame([[1, 3], [2, 4], [3, 5], [4, 6]])
    nested.columns = pd.MultiIndex.from_tuples([("left", "x"), ("left", "y")])
    nested_summary = _summary(nested)
    assert nested_summary.relationships[0].left_label == ("left", "x")
    assert nested_summary.relationships[0].right_label == ("left", "y")


def test_unsupported_semantic_pairs_are_not_numeric_relationships(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3, 4],
            "flag": pd.Series([True, False, True, False]),
            "group": pd.Categorical(["a", "b", "a", "b"]),
            "when": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
            ),
            "fixed": [5, 5, 5, 5],
            "blank": pd.Series([pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64"),
            "code": pd.Series(_UUIDS, dtype="string"),
            "note": pd.Series(["alpha", "beta", "gamma", "delta"], dtype="string"),
        }
    )

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("an unsupported pair must not read numeric values")

    monkeypatch.setattr(relationship_module, "_read_numeric_column", _fail)
    analysis = analyze_dataframe(frame)
    summary = build_relationships_summary(analysis)
    _assert_counts(summary)
    assert summary.n_supported_pairs == 0
    assert summary.relationships == ()
    assert summary.n_unimplemented_family_pairs == 4
    assert summary.unimplemented_family_counts == (
        UnimplementedFamilyCount(UnimplementedRelationshipFamily.NUMERIC_BOOLEAN, 1),
        UnimplementedFamilyCount(
            UnimplementedRelationshipFamily.NUMERIC_CATEGORICAL, 1
        ),
        UnimplementedFamilyCount(UnimplementedRelationshipFamily.DATETIME_NUMERIC, 1),
        UnimplementedFamilyCount(
            UnimplementedRelationshipFamily.DATETIME_CATEGORICAL, 1
        ),
    )
    assert analysis.columns[4].inferred.selected_type is SemanticType.CONSTANT
    assert analysis.columns[5].inferred.selected_type is SemanticType.EMPTY
    assert analysis.columns[6].inferred.selected_type is SemanticType.IDENTIFIER
    assert analysis.columns[7].inferred.selected_type is None
    assert summary.n_ineligible_pairs == summary.n_total_pairs - 4


def test_recognized_families_are_counted_without_raw_scans(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "a": [1, 2, 3, 4],
            "b": [2, 3, 4, 5],
            "c": pd.Series([True, False, True, False]),
            "d": pd.Series([False, True, False, True]),
            "e": pd.Categorical(["a", "b", "a", "b"]),
            "f": pd.Categorical(["b", "a", "b", "a"]),
            "g": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
            ),
        }
    )
    read_positions: list[int] = []
    original = relationship_module._read_numeric_column

    def _spy(series: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        read_positions.append(len(read_positions))
        return original(series)

    monkeypatch.setattr(relationship_module, "_read_numeric_column", _spy)
    summary = _summary(frame)
    _assert_counts(summary)
    assert read_positions == [0, 1]
    assert summary.n_total_pairs == 21
    assert summary.n_supported_pairs == 1
    counts = {item.family: item.n_pairs for item in summary.unimplemented_family_counts}
    assert counts == {
        UnimplementedRelationshipFamily.NUMERIC_BOOLEAN: 4,
        UnimplementedRelationshipFamily.NUMERIC_CATEGORICAL: 4,
        UnimplementedRelationshipFamily.BOOLEAN_BOOLEAN: 1,
        UnimplementedRelationshipFamily.CATEGORICAL_CATEGORICAL: 1,
        UnimplementedRelationshipFamily.DATETIME_NUMERIC: 2,
        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL: 2,
    }
    assert summary.n_ineligible_pairs == 6


def test_binary_integers_stay_numeric_pairs() -> None:
    summary = _summary(pd.DataFrame({"a": [0, 1, 0, 1], "b": [0, 1, 1, 0]}))
    _assert_counts(summary)
    assert summary.n_supported_pairs == 1
    assert summary.relationships[0].n_paired == 4
    assert summary.relationships[0].spearman.estimate.availability is (
        ResultAvailability.AVAILABLE
    )


def test_pairwise_finite_population_excludes_missing_and_infinity() -> None:
    frame = pd.DataFrame(
        {
            "x": [1.0, np.nan, 3.0, 4.0, np.inf, 6.0, -np.inf],
            "y": [1.0, 2.0, np.nan, 4.0, 5.0, np.inf, 7.0],
        }
    )
    relationship = _only(frame)
    assert relationship.n_total_rows == 7
    assert relationship.n_paired == 2
    assert relationship.n_excluded == 5
    assert relationship.spearman.estimate.value == pytest.approx(1.0)
    assert relationship.spearman.frequentist.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )


def test_nullable_numeric_dtypes_use_pairwise_complete_rows() -> None:
    frame = pd.DataFrame(
        {
            "x": pd.Series([1, pd.NA, 3, 4], dtype="Int64"),
            "y": pd.Series([1.0, 2.0, pd.NA, 4.0], dtype="Float64"),
        }
    )
    relationship = _only(frame)
    assert relationship.n_paired == 2
    assert relationship.n_excluded == 2
    assert relationship.pearson.estimate.value == pytest.approx(1.0)
    assert (
        relationship.pearson.frequentist.availability is ResultAvailability.UNAVAILABLE
    )


def test_unsigned_integers_are_correlated() -> None:
    frame = pd.DataFrame(
        {
            "x": pd.Series([1, 2, 3, 4], dtype="uint64"),
            "y": pd.Series([2, 4, 6, 8], dtype="uint64"),
        }
    )
    relationship = _only(frame)
    assert relationship.pearson.estimate.value == pytest.approx(1.0)
    assert relationship.pearson.estimate.direction is EffectDirection.POSITIVE


def test_spearman_and_pearson_both_exist_for_a_nonlinear_monotonic_pair() -> None:
    frame = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [1, 4, 9, 16, 25]})
    relationship = _only(frame)
    spearman = relationship.spearman.estimate.value
    pearson = relationship.pearson.estimate.value
    assert spearman is not None and pearson is not None
    assert spearman == pytest.approx(1.0)
    assert pearson == pytest.approx(0.981104910251593)
    assert spearman > pearson
    assert relationship.spearman.estimate.direction is EffectDirection.POSITIVE
    assert relationship.pearson.estimate.direction is EffectDirection.POSITIVE
    assert relationship.spearman.frequentist.p_value is not None
    assert relationship.pearson.frequentist.p_value is not None
    assert relationship.spearman.confidence_interval.availability is (
        ResultAvailability.UNAVAILABLE
    )
    lower, upper = _fisher_z(pearson, relationship.n_paired)
    interval = relationship.pearson.confidence_interval
    assert interval.availability is ResultAvailability.AVAILABLE
    assert interval.level == 0.95
    assert interval.method is relationship_module.CorrelationIntervalMethod.FISHER_Z
    assert interval.lower == pytest.approx(lower)
    assert interval.upper == pytest.approx(upper)
    assert norm.ppf(0.975) == pytest.approx(_NORMAL_Z_95)


def test_negative_linear_association() -> None:
    relationship = _only(pd.DataFrame({"x": [1, 2, 3, 4], "y": [8, 6, 4, 2]}))
    assert relationship.spearman.estimate.value == pytest.approx(-1.0)
    assert relationship.spearman.estimate.direction is EffectDirection.NEGATIVE
    assert relationship.pearson.estimate.value == pytest.approx(-1.0)
    assert relationship.pearson.estimate.direction is EffectDirection.NEGATIVE
    assert relationship.pearson.confidence_interval.reason is (
        UnavailabilityReason.BOUNDARY_CORRELATION
    )


def test_zero_pearson_correlation_has_no_strength_label() -> None:
    relationship = _only(pd.DataFrame({"x": [1, 2, 3, 4], "y": [1, 2, 2, 1]}))
    assert relationship.pearson.estimate.value == pytest.approx(0.0)
    assert relationship.pearson.estimate.direction is EffectDirection.ZERO
    assert relationship.pearson.frequentist.availability is ResultAvailability.AVAILABLE
    interval = relationship.pearson.confidence_interval
    assert interval.lower is not None and interval.upper is not None
    assert interval.lower < 0.0 < interval.upper
    assert not hasattr(relationship, "strength")
    assert not hasattr(relationship.pearson, "is_significant")


def test_tied_ranks_do_not_reject_spearman() -> None:
    relationship = _only(pd.DataFrame({"x": [1, 2, 2, 3], "y": [1, 2, 2, 4]}))
    assert relationship.spearman.estimate.availability is ResultAvailability.AVAILABLE
    assert relationship.spearman.estimate.value == pytest.approx(1.0)
    assert relationship.pearson.estimate.value == pytest.approx(0.9733285267845753)


def test_constant_after_pairwise_filtering_is_method_unavailability() -> None:
    frame = pd.DataFrame({"x": [1, 1, 2], "y": [5, 6, None]})
    analysis = analyze_dataframe(frame)
    assert analysis.columns[0].inferred.selected_type is SemanticType.NUMERIC
    assert analysis.columns[1].inferred.selected_type is SemanticType.NUMERIC
    relationship = analysis.relationship_analysis.relationships[0]
    assert relationship.n_paired == 2
    assert relationship.spearman.estimate.reason is (
        UnavailabilityReason.CONSTANT_PAIRED_VALUES
    )
    assert relationship.pearson.estimate.reason is (
        UnavailabilityReason.CONSTANT_PAIRED_VALUES
    )
    assert relationship.spearman.estimate.value is None
    assert relationship.pearson.frequentist.p_value is None


def test_sample_size_rules_separate_estimate_test_and_interval() -> None:
    empty_pair = _only(pd.DataFrame({"x": [1, 2, None, None], "y": [None, None, 3, 4]}))
    assert empty_pair.n_paired == 0
    assert empty_pair.spearman.estimate.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert empty_pair.pearson.confidence_interval.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )

    one = _only(pd.DataFrame({"x": [1, 2, None, None], "y": [10, None, 11, None]}))
    assert one.n_paired == 1
    assert one.pearson.estimate.availability is ResultAvailability.UNAVAILABLE

    two = _only(pd.DataFrame({"x": [1, 2, None], "y": [4, 3, None]}))
    assert two.n_paired == 2
    assert two.spearman.estimate.value == pytest.approx(-1.0)
    assert two.pearson.estimate.value == pytest.approx(-1.0)
    assert two.spearman.frequentist.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert two.spearman.confidence_interval.reason is (
        UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD
    )
    assert two.pearson.confidence_interval.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )

    three = _only(pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 4]}))
    assert three.n_paired == 3
    assert three.pearson.estimate.availability is ResultAvailability.AVAILABLE
    assert three.pearson.frequentist.availability is ResultAvailability.AVAILABLE
    assert three.pearson.confidence_interval.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert three.spearman.confidence_interval.reason is (
        UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD
    )


def test_large_integers_that_collapse_in_float64_are_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    big = np.uint64(2**63)
    frame = pd.DataFrame(
        {
            "x": pd.Series(
                [big, big + np.uint64(1), big, big + np.uint64(1)],
                dtype="UInt64",
            ),
            "y": [1, 2, 3, 4],
        }
    )

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("collapsed integers must not call SciPy")

    monkeypatch.setattr(relationship_module, "spearmanr", _fail)
    monkeypatch.setattr(relationship_module, "pearsonr", _fail)
    relationship = _only(frame)
    assert relationship.n_paired == 4
    assert (
        relationship.spearman.estimate.reason
        is UnavailabilityReason.PRECISION_COLLAPSED
    )
    assert (
        relationship.pearson.estimate.reason is UnavailabilityReason.PRECISION_COLLAPSED
    )
    assert relationship.spearman.estimate.value is None


def test_two_large_integers_use_source_order_when_float64_still_varies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    big = np.uint64(2**63)
    frame = pd.DataFrame(
        {
            "x": pd.Series([big, big + np.uint64(4096)], dtype="UInt64"),
            "y": [1, 2],
        }
    )

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("two-point correlation must not call SciPy")

    monkeypatch.setattr(relationship_module, "spearmanr", _fail)
    monkeypatch.setattr(relationship_module, "pearsonr", _fail)
    relationship = _only(frame)
    assert relationship.spearman.estimate.value == pytest.approx(1.0)
    assert relationship.pearson.estimate.value == pytest.approx(1.0)
    assert (
        relationship.spearman.frequentist.availability is ResultAvailability.UNAVAILABLE
    )


def test_extreme_finite_floats_do_not_fail_the_relationship_pass() -> None:
    mild = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 4.0]})
    columns = analyze_dataframe(mild).columns
    extreme = pd.DataFrame(
        {
            "x": [1e308, -1e308, 1e308, -1e308],
            "y": [1e308, 1e308, -1e308, -1e308],
        }
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        retained = collect_relationship_analysis(extreme, columns)
    relationship = retained.relationships[0]
    assert relationship.spearman.estimate.availability is ResultAvailability.AVAILABLE
    assert (
        relationship.pearson.estimate.reason is UnavailabilityReason.NON_FINITE_RESULT
    )
    assert relationship.pearson.estimate.value is None
    ordinary = analyze_dataframe(
        pd.DataFrame(
            {
                "x": [1e200, -1e200, 1e200, -1e200],
                "y": [1.0, 2.0, 3.0, 4.0],
            }
        )
    )
    assert ordinary.relationship_analysis.n_analyzed_pairs == 1


def test_builder_does_not_recompute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = analyze_dataframe(pd.DataFrame({"x": [1, 2, 3, 4], "y": [1, 3, 2, 4]}))

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("summary builder recomputed a relationship")

    monkeypatch.setattr(relationship_module, "spearmanr", _fail)
    monkeypatch.setattr(relationship_module, "pearsonr", _fail)
    monkeypatch.setattr(relationship_module, "_read_numeric_column", _fail)
    monkeypatch.setattr(relationship_module, "collect_relationship_analysis", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    summary = build_relationships_summary(analysis)
    _assert_counts(summary)
    assert summary.relationships[0].spearman.estimate.availability is (
        ResultAvailability.AVAILABLE
    )


def test_zero_and_narrow_frames_follow_semantic_selections() -> None:
    empty = _summary(pd.DataFrame())
    _assert_counts(empty)
    assert empty.n_total_pairs == 0
    assert empty.relationships == ()

    no_columns = _summary(pd.DataFrame(index=range(5)))
    _assert_counts(no_columns)
    assert no_columns.n_rows == 5
    assert no_columns.n_total_pairs == 0

    one_column = _summary(pd.DataFrame({"a": [1, 2, 3]}))
    _assert_counts(one_column)
    assert one_column.n_total_pairs == 0

    zero_rows = _summary(pd.DataFrame({"a": [], "b": [], "c": []}))
    _assert_counts(zero_rows)
    assert zero_rows.n_rows == 0
    assert zero_rows.n_columns == 3
    assert zero_rows.n_total_pairs == 3
    assert zero_rows.n_supported_pairs == 0
    assert zero_rows.n_ineligible_pairs == 3
    assert zero_rows.relationships == ()


def test_multiple_numeric_columns_analyze_every_canonical_pair() -> None:
    summary = _summary(
        pd.DataFrame(
            {
                "a": [1, 2, 3, 4],
                "b": [4, 3, 2, 1],
                "c": [1, 2, 2, 1],
            }
        )
    )
    _assert_counts(summary)
    assert summary.n_total_pairs == 3
    assert summary.n_supported_pairs == 3
    assert (
        summary.relationships[0].spearman.estimate.direction is EffectDirection.NEGATIVE
    )


def test_models_are_frozen_and_reject_inconsistent_results() -> None:
    summary = _summary(pd.DataFrame({"x": [1, 2, 3, 4], "y": [1, 2, 3, 5]}))
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.n_rows = 0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.relationships[0].n_paired = 0  # type: ignore[misc]
    with pytest.raises(ValueError, match="less than right_position"):
        NumericNumericRelationship(
            left_position=1,
            left_label="b",
            right_position=1,
            right_label="b",
            n_total_rows=4,
            n_paired=4,
            methods=summary.relationships[0].methods,
        )
    with pytest.raises(ValueError, match="no value"):
        CorrelationEstimate(
            availability=ResultAvailability.UNAVAILABLE,
            value=0.0,
            direction=None,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_relationships_summary(pd.DataFrame({"x": [1, 2]}))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="pandas DataFrame"):
        collect_relationship_analysis(pd.Series([1, 2]), ())  # type: ignore[arg-type]
    left = analyze_series(pd.Series([1, 2, 3]), position=0, label="a")
    right = analyze_series(pd.Series([1, 2, 4]), position=1, label="b")
    with pytest.raises(ValueError, match="selected Numeric pairs"):
        relationship_analysis_for_columns((left, right), n_rows=3)


def test_rejected_values_and_library_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    estimate = CorrelationEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=0.5,
        direction=EffectDirection.POSITIVE,
        reason=None,
    )
    test = FrequentistEvidence(
        availability=ResultAvailability.AVAILABLE,
        p_value=0.2,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )
    spearman_interval = CorrelationInterval(
        availability=ResultAvailability.UNAVAILABLE,
        level=None,
        method=None,
        lower=None,
        upper=None,
        reason=UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD,
    )
    unavailable = CorrelationEstimate(
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        direction=None,
        reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
    )
    unavailable_test = FrequentistEvidence(
        availability=ResultAvailability.UNAVAILABLE,
        p_value=None,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
    )
    unavailable_interval = CorrelationInterval(
        availability=ResultAvailability.UNAVAILABLE,
        level=None,
        method=None,
        lower=None,
        upper=None,
        reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
    )
    with pytest.raises(ValueError, match="direction must match"):
        CorrelationEstimate(
            availability=ResultAvailability.AVAILABLE,
            value=0.5,
            direction=EffectDirection.NEGATIVE,
            reason=None,
        )
    with pytest.raises(ValueError, match="available estimate has no"):
        CorrelationEstimate(
            availability=ResultAvailability.AVAILABLE,
            value=0.5,
            direction=EffectDirection.POSITIVE,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(ValueError, match="finite float"):
        CorrelationEstimate(
            availability=ResultAvailability.AVAILABLE,
            value=float("nan"),
            direction=EffectDirection.POSITIVE,
            reason=None,
        )
    with pytest.raises(ValueError, match="\\[-1, 1\\]"):
        CorrelationEstimate(
            availability=ResultAvailability.AVAILABLE,
            value=1.5,
            direction=EffectDirection.POSITIVE,
            reason=None,
        )
    with pytest.raises(TypeError, match="availability"):
        CorrelationEstimate(
            availability="available",  # type: ignore[arg-type]
            value=None,
            direction=None,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(ValueError, match="adjusted p-value"):
        FrequentistEvidence(
            availability=ResultAvailability.UNAVAILABLE,
            p_value=None,
            adjusted_p_value=0.2,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(ValueError, match="available test has no"):
        FrequentistEvidence(
            availability=ResultAvailability.AVAILABLE,
            p_value=0.2,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(ValueError, match="no p-value"):
        FrequentistEvidence(
            availability=ResultAvailability.UNAVAILABLE,
            p_value=0.2,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        FrequentistEvidence(
            availability=ResultAvailability.AVAILABLE,
            p_value=1.5,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=None,
        )
    with pytest.raises(ValueError, match="0.95"):
        CorrelationInterval(
            availability=ResultAvailability.AVAILABLE,
            level=0.9,
            method=CorrelationIntervalMethod.FISHER_Z,
            lower=-0.1,
            upper=0.2,
            reason=None,
        )
    with pytest.raises(ValueError, match="Fisher z"):
        CorrelationInterval(
            availability=ResultAvailability.AVAILABLE,
            level=0.95,
            method=None,
            lower=-0.1,
            upper=0.2,
            reason=None,
        )
    with pytest.raises(ValueError, match="out of order"):
        CorrelationInterval(
            availability=ResultAvailability.AVAILABLE,
            level=0.95,
            method=CorrelationIntervalMethod.FISHER_Z,
            lower=0.4,
            upper=0.2,
            reason=None,
        )
    with pytest.raises(ValueError, match="no bounds"):
        CorrelationInterval(
            availability=ResultAvailability.UNAVAILABLE,
            level=0.95,
            method=None,
            lower=None,
            upper=None,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    pearson_interval = CorrelationInterval(
        availability=ResultAvailability.AVAILABLE,
        level=0.95,
        method=CorrelationIntervalMethod.FISHER_Z,
        lower=-0.1,
        upper=0.4,
        reason=None,
    )
    with pytest.raises(ValueError, match="no confidence interval"):
        AssociationResult(
            method=AssociationMethod.SPEARMAN,
            n_observations=4,
            estimate=estimate,
            frequentist=test,
            confidence_interval=pearson_interval,
        )
    with pytest.raises(ValueError, match="not defined for this method"):
        AssociationResult(
            method=AssociationMethod.SPEARMAN,
            n_observations=4,
            estimate=estimate,
            frequentist=test,
            confidence_interval=CorrelationInterval(
                availability=ResultAvailability.UNAVAILABLE,
                level=None,
                method=None,
                lower=None,
                upper=None,
                reason=UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            ),
        )
    with pytest.raises(ValueError, match="test requires an estimate"):
        AssociationResult(
            method=AssociationMethod.PEARSON,
            n_observations=4,
            estimate=unavailable,
            frequentist=test,
            confidence_interval=unavailable_interval,
        )
    with pytest.raises(ValueError, match="share a reason"):
        AssociationResult(
            method=AssociationMethod.PEARSON,
            n_observations=4,
            estimate=unavailable,
            frequentist=FrequentistEvidence(
                availability=ResultAvailability.UNAVAILABLE,
                p_value=None,
                adjusted_p_value=None,
                adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                reason=UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            ),
            confidence_interval=unavailable_interval,
        )
    with pytest.raises(ValueError, match="interval requires an estimate"):
        AssociationResult(
            method=AssociationMethod.PEARSON,
            n_observations=4,
            estimate=unavailable,
            frequentist=unavailable_test,
            confidence_interval=pearson_interval,
        )
    with pytest.raises(ValueError, match="n_observations"):
        AssociationResult(
            method=AssociationMethod.PEARSON,
            n_observations=-1,
            estimate=estimate,
            frequentist=test,
            confidence_interval=pearson_interval,
        )
    spearman = AssociationResult(
        method=AssociationMethod.SPEARMAN,
        n_observations=4,
        estimate=estimate,
        frequentist=test,
        confidence_interval=spearman_interval,
    )
    pearson = AssociationResult(
        method=AssociationMethod.PEARSON,
        n_observations=4,
        estimate=estimate,
        frequentist=test,
        confidence_interval=pearson_interval,
    )
    with pytest.raises(ValueError, match="n_paired cannot exceed"):
        NumericNumericRelationship(
            left_position=0,
            left_label="a",
            right_position=1,
            right_label="b",
            n_total_rows=2,
            n_paired=4,
            methods=(spearman, pearson),
        )
    with pytest.raises(ValueError, match="method observations"):
        NumericNumericRelationship(
            left_position=0,
            left_label="a",
            right_position=1,
            right_label="b",
            n_total_rows=4,
            n_paired=3,
            methods=(spearman, pearson),
        )
    with pytest.raises(ValueError, match="first method must be Spearman"):
        NumericNumericRelationship(
            left_position=0,
            left_label="a",
            right_position=1,
            right_label="b",
            n_total_rows=4,
            n_paired=4,
            methods=(pearson, spearman),
        )
    with pytest.raises(TypeError, match="methods must be a tuple"):
        NumericNumericRelationship(
            left_position=0,
            left_label="a",
            right_position=1,
            right_label="b",
            n_total_rows=4,
            n_paired=4,
            methods=[spearman, pearson],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="non-negative int"):
        RelationshipAnalysis(
            n_rows=-1,
            n_total_pairs=0,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(),
        )
    with pytest.raises(ValueError, match="sum to n_total_pairs"):
        RelationshipAnalysis(
            n_rows=0,
            n_total_pairs=2,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=1,
            unimplemented_family_counts=(),
            relationships=(),
        )
    with pytest.raises(ValueError, match="unordered column pairs"):
        RelationshipsSummary(
            n_rows=0,
            n_columns=2,
            n_total_pairs=0,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(),
        )
    with pytest.raises(ValueError, match="every supported pair"):
        RelationshipsSummary(
            n_rows=1,
            n_columns=2,
            n_total_pairs=1,
            n_supported_pairs=1,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(),
        )
    with pytest.raises(ValueError, match="more than once"):
        RelationshipsSummary(
            n_rows=0,
            n_columns=3,
            n_total_pairs=3,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=2,
            n_ineligible_pairs=1,
            unimplemented_family_counts=(
                UnimplementedFamilyCount(
                    UnimplementedRelationshipFamily.BOOLEAN_BOOLEAN, 1
                ),
                UnimplementedFamilyCount(
                    UnimplementedRelationshipFamily.BOOLEAN_BOOLEAN, 1
                ),
            ),
            relationships=(),
        )
    with pytest.raises(ValueError, match="definition order"):
        RelationshipsSummary(
            n_rows=0,
            n_columns=3,
            n_total_pairs=3,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=2,
            n_ineligible_pairs=1,
            unimplemented_family_counts=(
                UnimplementedFamilyCount(
                    UnimplementedRelationshipFamily.DATETIME_NUMERIC, 1
                ),
                UnimplementedFamilyCount(
                    UnimplementedRelationshipFamily.NUMERIC_BOOLEAN, 1
                ),
            ),
            relationships=(),
        )
    with pytest.raises(ValueError, match="family total"):
        RelationshipsSummary(
            n_rows=0,
            n_columns=2,
            n_total_pairs=1,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=1,
            unimplemented_family_counts=(
                UnimplementedFamilyCount(
                    UnimplementedRelationshipFamily.NUMERIC_BOOLEAN, 1
                ),
            ),
            relationships=(),
        )
    with pytest.raises(TypeError, match="RelationshipAnalysis"):
        DatasetAnalysis(
            n_rows=0,
            n_columns=0,
            n_cells=0,
            columns=(),
            missing_analysis=MissingAnalysis(row_distribution=(), patterns=()),
            duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
            relationship_analysis=None,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="selected semantic pair counts"):
        DatasetAnalysis(
            n_rows=0,
            n_columns=0,
            n_cells=0,
            columns=(),
            missing_analysis=MissingAnalysis(row_distribution=(), patterns=()),
            duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
            relationship_analysis=RelationshipAnalysis(
                n_rows=0,
                n_total_pairs=1,
                n_supported_pairs=0,
                n_analyzed_pairs=0,
                n_unimplemented_family_pairs=0,
                n_ineligible_pairs=1,
                unimplemented_family_counts=(),
                relationships=(),
            ),
        )

    left = np.array([1.0, 2.0, 3.0, 4.0])
    right = np.array([1.0, 2.0, 4.0, 3.0])

    def _raise_value(*args: object, **kwargs: object) -> None:
        raise ValueError("library rejected the pair")

    monkeypatch.setattr(relationship_module, "spearmanr", _raise_value)
    failed = relationship_module._spearman_result(left, right, 4)
    assert failed.estimate.reason is UnavailabilityReason.NON_FINITE_RESULT
    monkeypatch.undo()

    def _tuple_result(*args: object, **kwargs: object) -> tuple[float, float]:
        return (0.25, 0.5)

    monkeypatch.setattr(relationship_module, "pearsonr", _tuple_result)
    from_tuple = relationship_module._pearson_result(left, right, 4)
    assert from_tuple.estimate.value == pytest.approx(0.25)
    assert from_tuple.frequentist.p_value == pytest.approx(0.5)
    monkeypatch.undo()

    def _statistic(*args: object, **kwargs: object) -> object:
        return type("Result", (), {"statistic": 0.4, "pvalue": 0.0})()

    monkeypatch.setattr(relationship_module, "spearmanr", _statistic)
    from_statistic = relationship_module._spearman_result(left, right, 4)
    assert from_statistic.estimate.value == pytest.approx(0.4)
    assert from_statistic.frequentist.p_value == pytest.approx(0.0)
    monkeypatch.undo()

    def _junk(*args: object, **kwargs: object) -> object:
        return object()

    monkeypatch.setattr(relationship_module, "pearsonr", _junk)
    junk = relationship_module._pearson_result(left, right, 4)
    assert junk.estimate.reason is UnavailabilityReason.NON_FINITE_RESULT
    monkeypatch.undo()

    def _wild(*args: object, **kwargs: object) -> object:
        return type("Result", (), {"correlation": 2.0, "pvalue": 0.2})()

    monkeypatch.setattr(relationship_module, "pearsonr", _wild)
    wild = relationship_module._pearson_result(left, right, 4)
    assert wild.estimate.reason is UnavailabilityReason.NON_FINITE_RESULT
    monkeypatch.undo()

    def _clamp(*args: object, **kwargs: object) -> object:
        return type("Result", (), {"correlation": 1.0 + 1e-12, "pvalue": -0.0})()

    monkeypatch.setattr(relationship_module, "pearsonr", _clamp)
    clamped = relationship_module._pearson_result(left, right, 4)
    assert clamped.estimate.value == pytest.approx(1.0)
    assert clamped.frequentist.p_value == pytest.approx(0.0)
    assert (
        clamped.confidence_interval.reason is UnavailabilityReason.BOUNDARY_CORRELATION
    )
    monkeypatch.undo()

    def _bad_p(*args: object, **kwargs: object) -> object:
        return type("Result", (), {"correlation": 0.2, "pvalue": True})()

    monkeypatch.setattr(relationship_module, "spearmanr", _bad_p)
    bad_p = relationship_module._spearman_result(left, right, 4)
    assert bad_p.estimate.value == pytest.approx(0.2)
    assert bad_p.frequentist.reason is UnavailabilityReason.NON_FINITE_RESULT
    monkeypatch.undo()

    small = relationship_module._spearman_result(left[:2], right[:2], 2)
    assert small.frequentist.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )

    assert relationship_module._bound_endpoint(float("nan")) is None
    assert relationship_module._bound_endpoint(2.0) is None
    assert relationship_module._bound_endpoint(1.0 + 1e-12) == pytest.approx(1.0)
    assert relationship_module._bound_endpoint(-1.0 - 1e-12) == pytest.approx(-1.0)
    assert relationship_module._bound_endpoint(0.0) == 0.0
    assert relationship_module._fisher_z_bounds(2.0, 10) is None
    assert relationship_module._fisher_z_bounds(0.2, 3) is None
    monkeypatch.setattr(relationship_module.norm, "ppf", lambda _quantile: float("nan"))
    assert relationship_module._fisher_z_bounds(0.2, 10) is None

    converted = relationship_module._to_float64(np.array([1, 2, 3], dtype=object))
    assert converted is not None
    assert converted.dtype == np.float64
    overflow = relationship_module._association_methods(
        np.array([10**1000, 2], dtype=object),
        np.array([1, 2], dtype=object),
    )
    assert overflow[0].estimate.reason is UnavailabilityReason.NON_FINITE_RESULT
    with pytest.raises(ValueError, match="aligned"):
        relationship_module._association_methods(
            np.array([1.0, 2.0]),
            np.array([1.0]),
        )
    with pytest.raises(TypeError, match="pandas Series"):
        relationship_module._read_numeric_column([1, 2, 3])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="boolean or complex"):
        relationship_module._read_numeric_column(pd.Series([True, False]))
    with pytest.raises(TypeError, match="boolean or complex"):
        relationship_module._read_numeric_column(pd.Series([1 + 0j, 2 + 0j]))
    with pytest.raises(TypeError, match="integer and floating"):
        relationship_module._read_numeric_column(pd.Series(["a", "b"]))

    integer_series = pd.Series([1, 2], dtype="int64")

    def _float_values(self: pd.Series, *args: object, **kwargs: object) -> np.ndarray:
        del self, args
        if kwargs.get("dtype") is bool:
            return np.array([True, True])
        return np.array([1.0, 2.0])

    monkeypatch.setattr(pd.Series, "to_numpy", _float_values)
    with pytest.raises(TypeError, match="stay integers"):
        relationship_module._read_integer_column(integer_series)
    monkeypatch.undo()

    calls = {"count": 0}

    def _short_values(self: pd.Series, *args: object, **kwargs: object) -> np.ndarray:
        del self, args, kwargs
        calls["count"] += 1
        if calls["count"] == 1:
            return np.array([True, True])
        return np.array([1], dtype=np.int64)

    monkeypatch.setattr(pd.Series, "to_numpy", _short_values)
    with pytest.raises(ValueError, match="one entry per row"):
        relationship_module._read_integer_column(integer_series)
    monkeypatch.undo()

    column = analyze_series(pd.Series([1, 2, 3]), position=0, label="a")
    with pytest.raises(TypeError, match="tuple"):
        relationship_analysis_for_columns([column], n_rows=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="n_total"):
        relationship_analysis_for_columns((column,), n_rows=1)
    shifted = analyze_series(pd.Series([1, 2, 3]), position=1, label="a")
    with pytest.raises(ValueError, match="column position"):
        relationship_analysis_for_columns((shifted,), n_rows=3)
    frame = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    columns = analyze_dataframe(frame).columns
    with pytest.raises(ValueError, match="DataFrame label"):
        collect_relationship_analysis(
            pd.DataFrame({"a": [1, 2, 3], "c": [4, 5, 6]}),
            columns,
        )
    with pytest.raises(ValueError, match="one record per DataFrame"):
        collect_relationship_analysis(frame.iloc[:, :1], columns)


def test_remaining_model_and_pair_rejections(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(TypeError, match="UnimplementedRelationshipFamily"):
        UnimplementedFamilyCount(family="numeric_boolean", n_pairs=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive int"):
        UnimplementedFamilyCount(
            family=UnimplementedRelationshipFamily.NUMERIC_BOOLEAN,
            n_pairs=0,
        )
    with pytest.raises(ValueError, match="available interval has no"):
        CorrelationInterval(
            availability=ResultAvailability.AVAILABLE,
            level=0.95,
            method=CorrelationIntervalMethod.FISHER_Z,
            lower=-0.2,
            upper=0.2,
            reason=UnavailabilityReason.NON_FINITE_RESULT,
        )
    estimate = CorrelationEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=0.2,
        direction=EffectDirection.POSITIVE,
        reason=None,
    )
    frequentist = FrequentistEvidence(
        availability=ResultAvailability.AVAILABLE,
        p_value=0.4,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )
    spearman_interval = CorrelationInterval(
        availability=ResultAvailability.UNAVAILABLE,
        level=None,
        method=None,
        lower=None,
        upper=None,
        reason=UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD,
    )
    spearman = AssociationResult(
        method=AssociationMethod.SPEARMAN,
        n_observations=4,
        estimate=estimate,
        frequentist=frequentist,
        confidence_interval=spearman_interval,
    )
    pearson_interval = CorrelationInterval(
        availability=ResultAvailability.AVAILABLE,
        level=0.95,
        method=CorrelationIntervalMethod.FISHER_Z,
        lower=-0.2,
        upper=0.5,
        reason=None,
    )
    pearson = AssociationResult(
        method=AssociationMethod.PEARSON,
        n_observations=4,
        estimate=estimate,
        frequentist=frequentist,
        confidence_interval=pearson_interval,
    )
    with pytest.raises(ValueError, match="n_total_rows"):
        NumericNumericRelationship(0, "a", 1, "b", True, 4, (spearman, pearson))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="n_paired"):
        NumericNumericRelationship(0, "a", 1, "b", 4, True, (spearman, pearson))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Spearman and Pearson"):
        NumericNumericRelationship(0, "a", 1, "b", 4, 4, (spearman,))
    with pytest.raises(ValueError, match="second method must be Pearson"):
        NumericNumericRelationship(0, "a", 1, "b", 4, 4, (spearman, spearman))
    with pytest.raises(ValueError, match="non-negative int"):
        NumericNumericRelationship(-1, "a", 1, "b", 4, 4, (spearman, pearson))
    with pytest.raises(ValueError, match="every supported pair"):
        RelationshipAnalysis(
            n_rows=4,
            n_total_pairs=1,
            n_supported_pairs=1,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(),
        )
    with pytest.raises(ValueError, match="sum to n_total_pairs"):
        RelationshipsSummary(
            n_rows=4,
            n_columns=2,
            n_total_pairs=1,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(),
        )
    unavailable = CorrelationEstimate(
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        direction=None,
        reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
    )
    with pytest.raises(ValueError, match="interval share a reason"):
        AssociationResult(
            method=AssociationMethod.PEARSON,
            n_observations=4,
            estimate=unavailable,
            frequentist=FrequentistEvidence(
                availability=ResultAvailability.UNAVAILABLE,
                p_value=None,
                adjusted_p_value=None,
                adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
            ),
            confidence_interval=CorrelationInterval(
                availability=ResultAvailability.UNAVAILABLE,
                level=None,
                method=None,
                lower=None,
                upper=None,
                reason=UnavailabilityReason.NON_FINITE_RESULT,
            ),
        )
    with pytest.raises(TypeError, match="estimate"):
        AssociationResult(
            method=AssociationMethod.PEARSON,
            n_observations=4,
            estimate="estimate",  # type: ignore[arg-type]
            frequentist=frequentist,
            confidence_interval=pearson_interval,
        )
    with pytest.raises(ValueError, match="finite float"):
        FrequentistEvidence(
            availability=ResultAvailability.AVAILABLE,
            p_value=float("nan"),
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=None,
        )

    frame = pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 2, 4, 3]})
    analysis = analyze_dataframe(frame)
    recorded = analysis.relationship_analysis.relationships[0]
    columns = analysis.columns
    with pytest.raises(TypeError, match="relationships must be a tuple"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=[recorded],  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="NumericNumericRelationship"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=("missing",),  # type: ignore[arg-type]
        )
    wrong_position = NumericNumericRelationship(
        0,
        "a",
        2,
        "b",
        4,
        recorded.n_paired,
        recorded.methods,
    )
    with pytest.raises(ValueError, match="positions must follow"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=(wrong_position,),
        )
    wrong_rows = NumericNumericRelationship(
        0,
        "a",
        1,
        "b",
        5,
        recorded.n_paired,
        recorded.methods,
    )
    with pytest.raises(ValueError, match="dataset row count"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=(wrong_rows,),
        )
    wrong_left = NumericNumericRelationship(
        0,
        "other",
        1,
        "b",
        4,
        recorded.n_paired,
        recorded.methods,
    )
    wrong_right = NumericNumericRelationship(
        0,
        "a",
        1,
        "other",
        4,
        recorded.n_paired,
        recorded.methods,
    )
    with pytest.raises(ValueError, match="source column label"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=(wrong_left,),
        )
    with pytest.raises(ValueError, match="source column label"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=(wrong_right,),
        )
    with pytest.raises(TypeError, match="relationships must be a tuple"):
        RelationshipAnalysis(
            n_rows=4,
            n_total_pairs=1,
            n_supported_pairs=1,
            n_analyzed_pairs=1,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=[recorded],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="n_analyzed_pairs must equal"):
        RelationshipAnalysis(
            n_rows=4,
            n_total_pairs=1,
            n_supported_pairs=1,
            n_analyzed_pairs=1,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(),
        )
    with pytest.raises(TypeError, match="NumericNumericRelationship"):
        RelationshipAnalysis(
            n_rows=4,
            n_total_pairs=1,
            n_supported_pairs=1,
            n_analyzed_pairs=1,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=("missing",),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="dataset row count"):
        RelationshipAnalysis(
            n_rows=3,
            n_total_pairs=1,
            n_supported_pairs=1,
            n_analyzed_pairs=1,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(recorded,),
        )
    second = NumericNumericRelationship(
        0,
        "a",
        2,
        "c",
        4,
        recorded.n_paired,
        recorded.methods,
    )
    with pytest.raises(ValueError, match="ascending positions"):
        RelationshipAnalysis(
            n_rows=4,
            n_total_pairs=2,
            n_supported_pairs=2,
            n_analyzed_pairs=2,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=(),
            relationships=(second, recorded),
        )
    with pytest.raises(TypeError, match="unimplemented_family_counts must be a tuple"):
        RelationshipAnalysis(
            n_rows=0,
            n_total_pairs=0,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=0,
            n_ineligible_pairs=0,
            unimplemented_family_counts=[],  # type: ignore[arg-type]
            relationships=(),
        )
    with pytest.raises(TypeError, match="UnimplementedFamilyCount"):
        RelationshipAnalysis(
            n_rows=2,
            n_total_pairs=1,
            n_supported_pairs=0,
            n_analyzed_pairs=0,
            n_unimplemented_family_pairs=1,
            n_ineligible_pairs=0,
            unimplemented_family_counts=("count",),  # type: ignore[arg-type]
            relationships=(),
        )
    with pytest.raises(TypeError, match="ColumnAnalysis"):
        relationship_analysis_for_columns(("column",), n_rows=0)  # type: ignore[arg-type]

    class _Incomparable:
        def __eq__(self, other: object) -> bool:
            raise TypeError("incomparable")

    assert relationship_module._labels_match(_Incomparable(), _Incomparable()) is False
    assert relationship_module._labels_match(np.array([1]), np.array([1])) is False

    monkeypatch.setattr(relationship_module, "_fisher_z_bounds", lambda *_args: None)
    unavailable_interval = relationship_module._pearson_interval(estimate, 10)
    assert unavailable_interval.reason is UnavailabilityReason.NON_FINITE_RESULT
    monkeypatch.undo()
    assert relationship_module._fisher_z_bounds(float("nan"), 10) is None
    monkeypatch.setattr(relationship_module, "_bound_endpoint", lambda _value: None)
    assert relationship_module._fisher_z_bounds(0.2, 10) is None
    assert relationship_module._has_variation(np.array([1.0])) is False

    def _wide_p(*_args: object, **_kwargs: object) -> object:
        return type("Result", (), {"correlation": 0.2, "pvalue": 1.5})()

    monkeypatch.setattr(relationship_module, "spearmanr", _wide_p)
    wide = relationship_module._spearman_result(
        np.array([1.0, 2.0, 3.0, 4.0]),
        np.array([1.0, 3.0, 2.0, 4.0]),
        4,
    )
    assert wide.frequentist.reason is UnavailabilityReason.NON_FINITE_RESULT
    monkeypatch.undo()

    def _array_correlation(*_args: object, **_kwargs: object) -> object:
        return type("Result", (), {"correlation": np.array([0.2]), "pvalue": 0.2})()

    monkeypatch.setattr(relationship_module, "pearsonr", _array_correlation)
    array_result = relationship_module._pearson_result(
        np.array([1.0, 2.0, 3.0, 4.0]),
        np.array([1.0, 3.0, 2.0, 4.0]),
        4,
    )
    assert array_result.estimate.reason is UnavailabilityReason.NON_FINITE_RESULT


def test_relationship_module_does_not_gate_methods_on_normality() -> None:
    source = inspect.getsource(relationship_module)
    assert "shapiro" not in source
    assert "normaltest" not in source
    assert "anderson" not in source.lower()
    assert "is_significant" not in source
    assert "statsmodels" not in source
