"""TSK-038: univariate distribution drift between two datasets.

Expected values come from independent calculations in this file: exact
Fraction ECDFs, permutation enumeration, hand-built contingency tables,
hypergeometric sums, and a definitional Benjamini–Hochberg. Production
helpers are not used to check themselves.
"""

from __future__ import annotations

import dataclasses
import itertools
import math
import uuid
from dataclasses import replace
from fractions import Fraction
from typing import List
from typing import Sequence

import numpy as np
import pandas as pd
import pytest
from scipy.stats import chi2
from scipy.stats import fisher_exact
from scipy.stats import ks_2samp
from scipy.stats import wasserstein_distance

import pytics.analysis.compare.distribution as distribution_module
from pytics.analysis.compare import DatasetComparison
from pytics.analysis.compare import DescriptiveComparisonReason
from pytics.analysis.compare import DistributionDriftStatus
from pytics.analysis.compare import DriftEffectMethod
from pytics.analysis.compare import DriftPopulationRule
from pytics.analysis.compare import DriftTestMethod
from pytics.analysis.compare import DriftUnavailabilityReason
from pytics.analysis.compare import NumericDistributionDrift
from pytics.analysis.compare import PValueComputation
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare import compare_dataset_analyses
from pytics.analysis.compare.distribution import numeric_distribution_drift
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability

AVAILABLE = ResultAvailability.AVAILABLE
UNAVAILABLE = ResultAvailability.UNAVAILABLE


# Independent references -------------------------------------------------


def _ecdf(sample: Sequence[object], x: object) -> Fraction:
    return Fraction(sum(1 for value in sample if value <= x), len(sample))


def _manual_ks(reference: Sequence[object], comparison: Sequence[object]) -> Fraction:
    pooled = sorted(set(reference) | set(comparison))
    return max(abs(_ecdf(comparison, x) - _ecdf(reference, x)) for x in pooled)


def _manual_wasserstein(
    reference: Sequence[object],
    comparison: Sequence[object],
) -> Fraction:
    pooled = sorted(set(reference) | set(comparison))
    total = Fraction(0)
    for lower, upper in zip(pooled[:-1], pooled[1:]):
        gap = Fraction(upper) - Fraction(lower)
        total += abs(_ecdf(comparison, lower) - _ecdf(reference, lower)) * gap
    return total


def _permutation_ks_p(reference: List[float], comparison: List[float]) -> Fraction:
    """Exact permutation p-value of the KS distance, by full enumeration."""
    pooled = reference + comparison
    observed = _manual_ks(reference, comparison)
    n_reference = len(reference)
    at_least = 0
    total = 0
    for chosen in itertools.combinations(range(len(pooled)), n_reference):
        selected = set(chosen)
        left = [pooled[i] for i in selected]
        right = [pooled[i] for i in range(len(pooled)) if i not in selected]
        total += 1
        if _manual_ks(left, right) >= observed:
            at_least += 1
    return Fraction(at_least, total)


def _manual_chi_square(table: List[List[int]]) -> Fraction:
    n = sum(map(sum, table))
    rows = [sum(row) for row in table]
    columns = [sum(column) for column in zip(*table)]
    statistic = Fraction(0)
    for i, row in enumerate(table):
        for j, observed in enumerate(row):
            expected = Fraction(rows[i] * columns[j], n)
            statistic += (observed - expected) ** 2 / expected
    return statistic


def _manual_expected(table: List[List[int]]) -> List[Fraction]:
    n = sum(map(sum, table))
    rows = [sum(row) for row in table]
    columns = [sum(column) for column in zip(*table)]
    return [Fraction(r * c, n) for r in rows for c in columns]


def _manual_fisher(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher p for [[a, b], [c, d]] from hypergeometric terms."""
    row = a + b
    column = a + c
    n = a + b + c + d

    def probability(x: int) -> Fraction:
        return Fraction(
            math.comb(row, x) * math.comb(n - row, column - x),
            math.comb(n, column),
        )

    observed = probability(a)
    low = max(0, column - (n - row))
    high = min(row, column)
    total = sum(
        probability(x)
        for x in range(low, high + 1)
        if probability(x) <= observed * Fraction(10**7 + 1, 10**7)
    )
    return float(total)


def _manual_bh(p_values: Sequence[float]) -> List[float]:
    """``adj_i = min(1, min over ranks k with p_(k) >= p_i of m * p_(k) / k)``."""
    m = len(p_values)
    ordered = sorted(p_values)
    return [
        min(
            1.0,
            min(
                m * ordered[k - 1] / k
                for k in range(1, m + 1)
                if ordered[k - 1] >= value
            ),
        )
        for value in p_values
    ]


def _column(result: DatasetComparison, label: object):
    for column in result.columns:
        alignment = column.alignment
        retained = alignment.reference_label or alignment.comparison_label
        if retained.value == label:
            return column
    raise KeyError(label)


def _drift(reference: Sequence[object], comparison: Sequence[object], dtype=None):
    return numeric_distribution_drift(
        np.asarray(reference, dtype=dtype),
        np.asarray(comparison, dtype=dtype),
    )


# Numeric ----------------------------------------------------------------


def test_numeric_ecdf_fixture_matches_manual_ks_wasserstein_and_scipy() -> None:
    reference = [1.0, 2.0, 3.0, 4.0]
    comparison = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    result = compare_dataframes(
        pd.DataFrame({"x": reference + [math.inf, None]}),
        pd.DataFrame({"x": comparison}),
    )
    column = _column(result, "x")
    assert column.distribution_status is DistributionDriftStatus.NUMERIC
    drift = column.distribution
    assert drift.population.rule is DriftPopulationRule.FINITE_NON_MISSING
    assert (drift.population.n_reference, drift.population.n_comparison) == (4, 6)
    assert column.numeric.positive_infinity_count.reference == 1
    assert column.missingness.missing_count.reference == 1
    assert drift.ks_distance.value == float(Fraction(2, 3))
    assert drift.ks_distance.value == float(_manual_ks(reference, comparison))
    assert drift.ks_location.value == 4.0
    assert drift.ks_location.reference_cumulative_proportion == 1.0
    assert drift.ks_location.comparison_cumulative_proportion == pytest.approx(1 / 3)
    assert drift.wasserstein_distance.value == 3.0
    assert drift.wasserstein_distance.value == float(
        _manual_wasserstein(reference, comparison)
    )
    assert drift.wasserstein_distance.value == pytest.approx(
        wasserstein_distance(reference, comparison)
    )
    scipy_result = ks_2samp(reference, comparison)
    assert drift.ks_distance.value == pytest.approx(scipy_result.statistic)
    assert drift.test.computation is PValueComputation.EXACT
    assert drift.test.p_value == pytest.approx(scipy_result.pvalue, rel=1e-12)
    assert drift.ties_present is True
    assert drift.n_distinct_pooled_values == 8
    assert drift.test.p_value >= float(_permutation_ks_p(reference, comparison))
    untied_reference = [1.0, 2.0, 3.0, 4.0]
    untied_comparison = [3.5, 4.5, 5.0, 6.0, 7.0, 8.0]
    untied = _drift(untied_reference, untied_comparison)
    assert untied.ties_present is False
    assert untied.test.p_value == pytest.approx(
        float(_permutation_ks_p(untied_reference, untied_comparison)), rel=1e-12
    )


def test_identical_numeric_samples_have_zero_distance_and_unit_p() -> None:
    values = [0.5, 1.5, 2.5, 9.0, -3.0]
    drift = (
        compare_dataframes(
            pd.DataFrame({"x": values}), pd.DataFrame({"x": values[::-1]})
        )
        .columns[0]
        .distribution
    )
    assert drift.ks_distance.value == 0.0
    assert drift.wasserstein_distance.value == 0.0
    assert drift.ks_location is None
    assert drift.test.p_value == 1.0


def test_location_scale_tail_and_same_mean_shapes_are_distinguished() -> None:
    grid = np.linspace(-3.0, 3.0, 301)
    shift = _drift(grid, grid + 0.5)
    assert shift.wasserstein_distance.value == pytest.approx(0.5, rel=1e-12)
    assert shift.ks_distance.value == pytest.approx(ks_2samp(grid, grid + 0.5)[0])
    scale = _drift(grid, grid * 2.0)
    assert scale.wasserstein_distance.value == pytest.approx(
        wasserstein_distance(grid, grid * 2.0), rel=1e-12
    )
    assert scale.ks_distance.value == pytest.approx(ks_2samp(grid, grid * 2.0)[0])
    base = list(range(1000))
    tail = list(range(990)) + list(range(10_000, 10_010))
    tail_drift = _drift(base, tail)
    assert tail_drift.ks_distance.value == 0.01
    assert tail_drift.wasserstein_distance.value == float(
        Fraction(sum(tail) - sum(base), 1000)
    )
    narrow = [-1.0, 1.0] * 50
    wide = [-2.0, 0.0, 0.0, 2.0] * 25
    same_mean = compare_dataframes(
        pd.DataFrame({"x": narrow}), pd.DataFrame({"x": wide})
    ).columns[0]
    assert same_mean.numeric.mean.change == 0.0
    assert same_mean.distribution.ks_distance.value == float(_manual_ks(narrow, wide))
    assert same_mean.distribution.ks_distance.value == 0.25
    assert same_mean.distribution.wasserstein_distance.value == float(
        _manual_wasserstein(narrow, wide)
    )


def test_discrete_numeric_ties_are_retained_and_ks_p_is_conservative() -> None:
    reference = [0] * 6 + [1] * 4
    comparison = [0] * 2 + [1] * 6
    result = compare_dataframes(
        pd.DataFrame({"x": reference}), pd.DataFrame({"x": comparison})
    )
    drift = _column(result, "x").distribution
    assert isinstance(drift, NumericDistributionDrift)
    assert drift.ties_present is True
    assert drift.n_distinct_pooled_values == 2
    assert drift.ks_distance.value == float(_manual_ks(reference, comparison))
    assert drift.ks_distance.value == pytest.approx(0.6 - 0.25)
    assert drift.ks_location.value == 0
    permutation = float(
        _permutation_ks_p([float(v) for v in reference], [float(v) for v in comparison])
    )
    assert drift.test.p_value == pytest.approx(ks_2samp(reference, comparison)[1])
    assert drift.test.p_value >= permutation


def test_finite_constant_populations_stay_numeric_and_are_compared() -> None:
    result = compare_dataframes(
        pd.DataFrame({"x": [5.0, 5.0, math.inf]}),
        pd.DataFrame({"x": [7.0, 7.0, math.inf]}),
    )
    drift = result.columns[0].distribution
    assert drift.ks_distance.value == 1.0
    assert drift.wasserstein_distance.value == 2.0
    assert drift.test.p_value == pytest.approx(1 / 3)


def test_empty_finite_populations_name_the_empty_side() -> None:
    infinite = pd.DataFrame({"x": [math.inf, -math.inf, None]})
    finite = pd.DataFrame({"x": [1.0, 2.0, 2.0]})
    reference_empty = compare_dataframes(infinite, finite).columns[0].distribution
    assert reference_empty.ks_distance.reason is (
        DriftUnavailabilityReason.REFERENCE_POPULATION_EMPTY
    )
    assert reference_empty.wasserstein_distance.availability is UNAVAILABLE
    assert reference_empty.test.availability is UNAVAILABLE
    assert reference_empty.n_distinct_pooled_values == 2
    comparison_empty = compare_dataframes(finite, infinite).columns[0].distribution
    assert comparison_empty.test.reason is (
        DriftUnavailabilityReason.COMPARISON_POPULATION_EMPTY
    )
    both = compare_dataframes(infinite, infinite.copy())
    assert both.columns[0].distribution.test.reason is (
        DriftUnavailabilityReason.BOTH_POPULATIONS_EMPTY
    )
    assert both.columns[0].distribution.n_distinct_pooled_values == 0
    assert both.coverage.n_distribution_tests == 0
    assert both.coverage.n_distribution_tests_unavailable == 1
    assert both.coverage.n_distribution_primary_effects_unavailable == 1


def test_one_observation_per_side_keeps_effects_and_a_weak_test() -> None:
    drift = (
        compare_dataframes(
            pd.DataFrame({"x": [1.0, math.inf]}),
            pd.DataFrame({"x": [2.0, math.inf]}),
        )
        .columns[0]
        .distribution
    )
    assert drift.ks_distance.value == 1.0
    assert drift.wasserstein_distance.value == 1.0
    assert drift.test.availability is AVAILABLE
    assert drift.test.p_value == 1.0


def test_integers_beyond_float64_keep_exact_order_and_gaps() -> None:
    base = 2**60
    reference = [base, base + 1, base + 2]
    comparison = [base + 1, base + 2, base + 3]
    assert len({float(v) for v in reference + comparison}) == 1
    drift = (
        compare_dataframes(
            pd.DataFrame({"x": np.array(reference, dtype=np.int64)}),
            pd.DataFrame({"x": np.array(comparison, dtype=np.int64)}),
        )
        .columns[0]
        .distribution
    )
    assert drift.ks_distance.value == float(_manual_ks(reference, comparison))
    assert drift.ks_distance.value == pytest.approx(1 / 3)
    assert drift.wasserstein_distance.value == 1.0
    assert drift.n_distinct_pooled_values == 4
    assert drift.ks_location.value == base
    assert type(drift.ks_location.value) is int


def test_uint64_near_the_top_of_its_range_is_exact() -> None:
    top = 2**64 - 1
    reference = [top - 2, top - 1, top]
    comparison = [top - 1, top, top]
    drift = (
        compare_dataframes(
            pd.DataFrame({"x": np.array(reference, dtype=np.uint64)}),
            pd.DataFrame({"x": np.array(comparison, dtype=np.uint64)}),
        )
        .columns[0]
        .distribution
    )
    assert drift.ks_distance.value == float(_manual_ks(reference, comparison))
    assert drift.wasserstein_distance.value == float(
        _manual_wasserstein(reference, comparison)
    )
    assert drift.ks_location.value == top - 2


def test_signed_and_unsigned_samples_that_share_no_dtype_pool_exactly() -> None:
    reference = [-1, 0, 1]
    comparison = [2**63, 2**63 + 1, 2**63 + 5]
    drift = _drift(
        np.array(reference, dtype=np.int64), np.array(comparison, dtype=np.uint64)
    )
    assert drift.ks_distance.value == 1.0
    assert drift.wasserstein_distance.value == float(
        _manual_wasserstein(reference, comparison)
    )
    assert drift.ks_location.value == 1
    compatible = _drift(
        np.array([0, 1, 2], dtype=np.int64),
        np.array([2, 3, 2**64 - 1], dtype=np.uint64),
    )
    assert compatible.wasserstein_distance.value == float(
        _manual_wasserstein([0, 1, 2], [2, 3, 2**64 - 1])
    )
    narrow = _drift(
        np.array([-5, 1, 2], dtype=np.int64), np.array([2, 3, 4], dtype=np.uint64)
    )
    assert narrow.ks_distance.value == float(_manual_ks([-5, 1, 2], [2, 3, 4]))


def test_large_integers_against_floats_compare_without_float_collapse() -> None:
    top = 2**53
    reference = [top + 1, top + 3]
    comparison = [float(top), float(top + 2), float(top + 4)]
    assert float(top + 1) == float(top)
    result = compare_dataframes(
        pd.DataFrame({"x": np.array(reference, dtype=np.int64)}),
        pd.DataFrame({"x": np.array(comparison, dtype=np.float64)}),
    )
    drift = result.columns[0].distribution
    assert drift.n_distinct_pooled_values == 5
    assert drift.ks_distance.value == float(_manual_ks(reference, comparison))
    assert drift.wasserstein_distance.value == float(
        _manual_wasserstein(reference, comparison)
    )
    small = _drift(np.array([1, 2, 3], dtype=np.int64), np.array([1.5, 2.0, 9.0]))
    assert small.ks_distance.value == float(_manual_ks([1, 2, 3], [1.5, 2.0, 9.0]))
    assert small.ks_location.value == 1.0


def test_extreme_subnormal_and_signed_zero_floats() -> None:
    huge = 1.7e308
    wide = (
        compare_dataframes(
            pd.DataFrame({"x": [-huge, huge]}),
            pd.DataFrame({"x": [huge, huge, math.inf]}),
        )
        .columns[0]
        .distribution
    )
    assert wide.ks_distance.value == 0.5
    assert wide.wasserstein_distance.value == pytest.approx(huge, rel=1e-15)
    overflow = (
        compare_dataframes(
            pd.DataFrame({"x": [-huge, -huge, math.inf]}),
            pd.DataFrame({"x": [huge, huge, math.inf]}),
        )
        .columns[0]
        .distribution
    )
    assert overflow.ks_distance.value == 1.0
    assert overflow.wasserstein_distance.reason is (
        DriftUnavailabilityReason.NON_FINITE_RESULT
    )
    assert overflow.test.availability is AVAILABLE
    tiny = 5e-324
    subnormal = _drift([tiny, 2 * tiny], [2 * tiny, 3 * tiny])
    assert subnormal.wasserstein_distance.value == float(
        _manual_wasserstein([tiny, 2 * tiny], [2 * tiny, 3 * tiny])
    )
    assert subnormal.wasserstein_distance.value == tiny
    zeros = _drift([-0.0, 1.0], [0.0, 1.0])
    assert zeros.ks_distance.value == 0.0
    assert zeros.wasserstein_distance.value == 0.0
    shifted_zero = _drift([-0.0, 1.0], [0.5, 1.0])
    assert math.copysign(1.0, shifted_zero.ks_location.value) == 1.0
    for value in (wide, overflow, subnormal, zeros):
        for effect in (value.ks_distance, value.wasserstein_distance):
            assert effect.value is None or math.isfinite(effect.value)


def test_large_samples_use_the_asymptotic_ks_tail_scipy_uses() -> None:
    grid = np.linspace(0.0, 1.0, 12_001)
    drift = _drift(grid, grid + 0.002)
    assert drift.test.computation is PValueComputation.ASYMPTOTIC
    scipy_result = ks_2samp(grid, grid + 0.002)
    assert drift.ks_distance.value == pytest.approx(scipy_result.statistic, abs=1e-15)
    assert drift.test.p_value == pytest.approx(scipy_result.pvalue, rel=1e-9)
    at_limit = _drift(grid[:10_000], grid[:9_000] + 0.01)
    assert at_limit.test.computation is PValueComputation.EXACT
    assert at_limit.test.p_value == pytest.approx(
        ks_2samp(grid[:10_000], grid[:9_000] + 0.01).pvalue, rel=1e-9
    )


def test_abandoned_exact_ks_calculation_is_labelled_asymptotic(monkeypatch) -> None:
    def warning_ks(*args, **kwargs):
        import warnings

        warnings.warn("Exact calculation unsuccessful", RuntimeWarning)
        return (0.5, 0.25)

    monkeypatch.setattr(distribution_module, "ks_2samp", warning_ks)
    drift = _drift([1.0, 2.0, 3.0], [2.5, 4.0, 5.0])
    assert drift.test.computation is PValueComputation.ASYMPTOTIC
    assert drift.test.p_value != 0.25


# Categorical ------------------------------------------------------------


def _categorical_frames(reference: List[object], comparison: List[object]):
    return (
        pd.DataFrame({"c": pd.Categorical(reference)}),
        pd.DataFrame({"c": pd.Categorical(comparison)}),
    )


def test_categorical_tvd_chi_square_and_expected_counts_are_verified() -> None:
    reference = ["A", "A", "B", "B"]
    comparison = ["A", "A", "A", "B"]
    column = compare_dataframes(*_categorical_frames(reference, comparison)).columns[0]
    drift = column.distribution
    assert column.distribution_status is DistributionDriftStatus.CATEGORICAL
    assert drift.total_variation_distance.value == 0.25
    assert drift.total_variation_distance.value == 0.5 * (
        abs(0.50 - 0.75) + abs(0.50 - 0.25)
    )
    table = [[2, 2], [3, 1]]
    statistic = _manual_chi_square(table)
    assert drift.test.statistic == pytest.approx(float(statistic), rel=1e-15)
    assert drift.test.degrees_of_freedom == 1
    assert drift.test.p_value == pytest.approx(chi2.sf(float(statistic), 1), rel=1e-12)
    assert drift.test.computation is PValueComputation.ASYMPTOTIC
    expected = _manual_expected(table)
    assert expected == [Fraction(5, 2), Fraction(3, 2), Fraction(5, 2), Fraction(3, 2)]
    counts = drift.expected_counts
    assert counts.minimum_expected_count == float(min(expected))
    assert counts.n_cells_expected_below_5 == sum(1 for e in expected if e < 5)
    assert counts.n_cells_expected_below_1 == sum(1 for e in expected if e < 1)
    assert counts.fraction_cells_expected_below_5 == 1.0


def test_new_and_disappeared_levels_are_drift_evidence_without_smoothing() -> None:
    reference = ["a", "a", "b", "b", "c"]
    comparison = ["a", "b", "b", "d", "d", "d"]
    column = compare_dataframes(*_categorical_frames(reference, comparison)).columns[0]
    drift = column.distribution
    assert [level.value for level in column.categorical.reference_only_levels] == ["c"]
    assert [level.value for level in column.categorical.comparison_only_levels] == ["d"]
    assert drift.n_levels == 4
    assert drift.n_reference_only_observations == 1
    assert drift.n_comparison_only_observations == 3
    manual = Fraction(1, 2) * sum(
        abs(Fraction(reference.count(v), 5) - Fraction(comparison.count(v), 6))
        for v in "abcd"
    )
    assert drift.total_variation_distance.value == float(manual)
    table = [[2, 2, 1, 0], [1, 2, 0, 3]]
    assert drift.test.statistic == pytest.approx(
        float(_manual_chi_square(table)), rel=1e-15
    )
    assert drift.test.degrees_of_freedom == 3
    expected = _manual_expected(table)
    assert drift.expected_counts.minimum_expected_count == pytest.approx(
        float(min(expected))
    )
    assert drift.expected_counts.n_cells_expected_below_5 == 8
    assert drift.expected_counts.n_cells_expected_below_1 == sum(
        1 for e in expected if e < 1
    )
    disjoint = compare_dataframes(*_categorical_frames(["x", "y"], ["p", "q"]))
    assert disjoint.columns[0].distribution.total_variation_distance.value == 1.0


def test_identical_and_dominant_categorical_distributions() -> None:
    same = compare_dataframes(
        *_categorical_frames(["a", "b", "b", None], ["b", "a", "b"])
    ).columns[0]
    assert same.distribution.population.n_reference == 3
    assert same.missingness.missing_count.change == -1
    assert same.distribution.total_variation_distance.value == 0.0
    assert same.distribution.test.statistic == 0.0
    assert same.distribution.test.p_value == 1.0
    dominant = (
        compare_dataframes(
            *_categorical_frames(["a"] * 98 + ["b", "c"], ["a"] * 90 + ["b"] * 10)
        )
        .columns[0]
        .distribution
    )
    assert dominant.total_variation_distance.value == pytest.approx(0.09)
    assert dominant.expected_counts.n_cells_expected_below_5 >= 1


def test_sparse_singleton_table_keeps_its_asymptotic_p_value() -> None:
    reference = [f"r{i}" for i in range(30)]
    comparison = [f"c{i}" for i in range(20)] + ["r0"] * 10
    drift = (
        compare_dataframes(*_categorical_frames(reference, comparison))
        .columns[0]
        .distribution
    )
    assert drift.n_levels == 50
    levels = sorted(set(reference) | set(comparison))
    table = [
        [reference.count(v) for v in levels],
        [comparison.count(v) for v in levels],
    ]
    expected = _manual_expected(table)
    assert drift.expected_counts.n_cells_expected_below_1 == sum(
        1 for e in expected if e < 1
    )
    assert drift.expected_counts.n_cells_expected_below_5 == 98
    assert drift.expected_counts.fraction_cells_expected_below_5 == 0.98
    assert drift.expected_counts.minimum_expected_count == float(min(expected))
    assert drift.test.availability is AVAILABLE
    assert drift.test.degrees_of_freedom == 49


def test_typed_category_identity_is_not_stringified() -> None:
    reference = pd.DataFrame({"c": pd.Categorical([1, 2, 2])})
    comparison = pd.DataFrame({"c": pd.Categorical(["1", "2", "2"])})
    drift = compare_dataframes(reference, comparison).columns[0].distribution
    assert drift.n_levels == 4
    assert drift.total_variation_distance.value == 1.0


def test_high_cardinality_drift_retains_no_per_level_copy() -> None:
    n_levels = 5000
    reference = pd.DataFrame(
        {
            "c": pd.Categorical.from_codes(
                np.arange(n_levels) % n_levels, list(range(n_levels))
            )
        }
    )
    comparison = pd.DataFrame(
        {
            "c": pd.Categorical.from_codes(
                (np.arange(n_levels) + 7) % n_levels, list(range(n_levels))
            )
        }
    )
    drift = compare_dataframes(reference, comparison).columns[0].distribution
    assert drift.n_levels == n_levels
    assert drift.total_variation_distance.value == 0.0
    for field in dataclasses.fields(drift):
        assert not isinstance(getattr(drift, field.name), tuple)


# Boolean ----------------------------------------------------------------


def test_boolean_difference_and_fisher_p_are_verified() -> None:
    reference = [True, False, False, False]
    comparison = [True, True, True, False, None]
    column = compare_dataframes(
        pd.DataFrame({"f": pd.array(reference, dtype="boolean")}),
        pd.DataFrame({"f": pd.array(comparison, dtype="boolean")}),
    ).columns[0]
    drift = column.distribution
    assert column.distribution_status is DistributionDriftStatus.BOOLEAN
    assert (drift.population.n_reference, drift.population.n_comparison) == (4, 4)
    assert drift.true_proportion_difference.value == 0.75 - 0.25
    assert (
        drift.true_proportion_difference.value == column.boolean.true_proportion.change
    )
    assert drift.test.method is DriftTestMethod.FISHER_EXACT_TWO_SAMPLE
    assert drift.test.computation is PValueComputation.EXACT
    assert drift.test.p_value == pytest.approx(_manual_fisher(3, 1, 1, 3), rel=1e-12)
    assert drift.test.p_value == pytest.approx(
        fisher_exact([[3, 1], [1, 3]])[1], rel=1e-12
    )
    names = {field.name for field in dataclasses.fields(drift)}
    assert names == {"population", "true_proportion_difference", "test"}


def test_identical_boolean_shares_and_constant_boolean_sides() -> None:
    same = (
        compare_dataframes(
            pd.DataFrame({"f": [True, False, True, False]}),
            pd.DataFrame({"f": [False, True]}),
        )
        .columns[0]
        .distribution
    )
    assert same.true_proportion_difference.value == 0.0
    assert same.test.p_value == 1.0
    one_side_all_true = compare_dataframes(
        pd.DataFrame({"f": [True, False]}), pd.DataFrame({"f": [True, True]})
    ).columns[0]
    assert one_side_all_true.descriptive_reason is (
        DescriptiveComparisonReason.SEMANTIC_MISMATCH
    )
    assert one_side_all_true.distribution_status is DistributionDriftStatus.NOT_ELIGIBLE
    opposite = compare_dataframes(
        pd.DataFrame({"f": [True, True]}), pd.DataFrame({"f": [False, False]})
    ).columns[0]
    assert opposite.descriptive_reason is DescriptiveComparisonReason.CONSTANT
    assert opposite.distribution is None


# Effect size before significance ----------------------------------------


def test_tiny_effects_with_huge_samples_stay_tiny_despite_tiny_p() -> None:
    n = 1_000_000
    numeric = _drift(np.arange(n), np.arange(n) + n // 100)
    assert numeric.ks_distance.value == 0.01
    assert numeric.wasserstein_distance.value == n // 100
    assert numeric.test.computation is PValueComputation.ASYMPTOTIC
    assert numeric.test.p_value < 1e-30
    rows = 200_000
    reference = np.zeros(rows, dtype=np.int8)
    reference[: rows // 2] = 1
    comparison = np.zeros(rows, dtype=np.int8)
    comparison[: rows // 2 + rows // 100] = 1
    result = compare_dataframes(
        pd.DataFrame(
            {
                "c": pd.Categorical.from_codes(reference, ["a", "b"]),
                "f": reference.astype(bool),
            }
        ),
        pd.DataFrame(
            {
                "c": pd.Categorical.from_codes(comparison, ["a", "b"]),
                "f": comparison.astype(bool),
            }
        ),
    )
    categorical = _column(result, "c").distribution
    boolean = _column(result, "f").distribution
    assert categorical.total_variation_distance.value == pytest.approx(0.01)
    assert categorical.test.p_value < 1e-8
    assert boolean.true_proportion_difference.value == pytest.approx(0.01)
    assert boolean.test.p_value < 1e-8


def test_large_effects_with_small_samples_stay_large_despite_weak_p() -> None:
    numeric = (
        compare_dataframes(
            pd.DataFrame({"x": [1.0, 2.0, 3.0]}), pd.DataFrame({"x": [4.0, 5.0, 6.0]})
        )
        .columns[0]
        .distribution
    )
    assert numeric.ks_distance.value == 1.0
    assert numeric.test.p_value == pytest.approx(0.1)
    assert numeric.test.adjusted_p_value >= numeric.test.p_value
    categorical = (
        compare_dataframes(*_categorical_frames(["a", "a", "b"], ["b", "b", "a"]))
        .columns[0]
        .distribution
    )
    assert categorical.total_variation_distance.value == pytest.approx(1 / 3)
    assert categorical.test.p_value > 0.3
    boolean = (
        compare_dataframes(
            pd.DataFrame({"f": [True, False, False, False]}),
            pd.DataFrame({"f": [True, True, True, False]}),
        )
        .columns[0]
        .distribution
    )
    assert boolean.true_proportion_difference.value == 0.5
    assert boolean.test.p_value > 0.4
    for record in (numeric, categorical, boolean):
        names = {field.name for field in dataclasses.fields(record)}
        assert not names & {"significant", "severity", "score", "drifted", "label"}


# Multiple testing -------------------------------------------------------


def test_drift_family_is_one_primary_p_per_tested_column() -> None:
    reference = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "b": [1.0, 2.0, 3.0, 4.0, 5.0],
            "c": pd.Categorical(["x", "y", "x", "y", "x"]),
            "empty_finite": [math.inf, -math.inf, None, None, None],
            "f": [True, False, True, False, True],
            "when": pd.date_range("2020", periods=5),
            "id": [str(uuid.UUID(int=i)) for i in range(5)],
        }
    )
    comparison = pd.DataFrame(
        {
            "a": [6.0, 7.0, 8.0, 9.0, 10.0],
            "b": [1.5, 2.0, 3.5, 4.0, 5.5],
            "c": pd.Categorical(["x", "x", "x", "y", "z"]),
            "empty_finite": [1.0, 2.0, None, None, None],
            "f": [True, True, True, True, False],
            "when": pd.date_range("2021", periods=5),
            "id": [str(uuid.UUID(int=i + 9)) for i in range(5)],
        }
    )
    result = compare_dataframes(reference, comparison)
    tested = [
        column
        for column in result.columns
        if column.distribution is not None
        and column.distribution.test.availability is AVAILABLE
    ]
    assert [column.alignment.reference_label.value for column in tested] == [
        "a",
        "b",
        "c",
        "f",
    ]
    raw = [column.distribution.test.p_value for column in tested]
    stored = [column.distribution.test.adjusted_p_value for column in tested]
    assert stored == pytest.approx(_manual_bh(raw), rel=1e-15)
    assert result.coverage.n_distribution_tests == 4
    assert result.coverage.n_distribution_tests_unavailable == 1
    assert result.coverage.n_distribution_not_eligible == 2
    for column in tested:
        assert column.distribution.test.adjustment is (
            MultipleTestingAdjustment.BENJAMINI_HOCHBERG
        )
    untested = _column(result, "empty_finite").distribution.test
    assert untested.adjustment is MultipleTestingAdjustment.NOT_APPLIED
    assert untested.adjusted_p_value is None
    order = sorted(range(len(raw)), key=lambda i: raw[i])
    assert [stored[i] for i in order] == sorted(stored)
    for p, adjusted in zip(raw, stored):
        assert adjusted >= p
    tampered = replace(
        tested[0],
        distribution=replace(
            tested[0].distribution,
            test=replace(tested[0].distribution.test, adjusted_p_value=1.0),
        ),
    )
    columns = tuple(
        tampered if column is tested[0] else column for column in result.columns
    )
    with pytest.raises(ValueError, match="drift family"):
        DatasetComparison(
            overview=result.overview,
            columns=columns,
            coverage=result.coverage,
            relationships=result.relationships,
            relationship_coverage=result.relationship_coverage,
            target=result.target,
        )


def test_benjamini_hochberg_reference_handles_ties_and_order() -> None:
    raw = [0.04, 0.01, 0.03, 0.01, 0.2]
    assert _manual_bh(raw) == pytest.approx([0.05, 0.025, 0.05, 0.025, 0.2])
    from pytics.analysis.relationships.adjustment import benjamini_hochberg

    assert list(benjamini_hochberg(tuple(raw))) == pytest.approx(_manual_bh(raw))


# Eligibility, sources, determinism --------------------------------------


def test_semantic_types_without_a_drift_method_are_not_coerced() -> None:
    reference = pd.DataFrame(
        {
            "id": [str(uuid.UUID(int=i)) for i in range(4)],
            "when": pd.date_range("2020", periods=4),
            "span": pd.to_timedelta([1, 2, 3, 4], unit="D"),
            "text": ["alpha beta", "gamma", "delta epsilon", "zeta"],
            "constant": [3, 3, 3, 3],
            "empty": [None] * 4,
            "changed": [1.0, 2.0, 3.0, 4.0],
        }
    )
    comparison = reference.copy()
    comparison["changed"] = pd.Categorical(["a", "b", "a", "b"])
    result = compare_dataframes(reference, comparison)
    for column in result.columns:
        assert column.distribution_status is DistributionDriftStatus.NOT_ELIGIBLE
        assert column.distribution is None
    assert (
        _column(result, "id").descriptive_reason
        is DescriptiveComparisonReason.IDENTIFIER
    )
    assert _column(result, "changed").descriptive_reason is (
        DescriptiveComparisonReason.SEMANTIC_MISMATCH
    )
    assert result.coverage.n_distribution_tests == 0


def test_analyses_without_frames_record_drift_as_not_collected() -> None:
    reference = pd.DataFrame({"x": [1.0, 2.0, 3.0], "f": [True, False, True]})
    comparison = pd.DataFrame({"x": [2.0, 3.0, 9.0], "f": [False, False, True]})
    reference_analysis = analyze_dataframe(reference)
    comparison_analysis = analyze_dataframe(comparison)
    plain = compare_dataset_analyses(reference_analysis, comparison_analysis)
    for column in plain.columns:
        assert column.distribution_status is (
            DistributionDriftStatus.SOURCE_VALUES_NOT_SUPPLIED
        )
        assert column.distribution is None
    assert plain.coverage.n_distribution_source_not_supplied == 2
    sourced = compare_dataset_analyses(
        reference_analysis,
        comparison_analysis,
        reference_frame=reference,
        comparison_frame=comparison,
    )
    assert sourced == compare_dataframes(reference, comparison)
    assert sourced.columns[0].numeric == plain.columns[0].numeric
    with pytest.raises(ValueError, match="both source frames"):
        compare_dataset_analyses(
            reference_analysis, comparison_analysis, reference_frame=reference
        )
    with pytest.raises(ValueError, match="shape"):
        compare_dataset_analyses(
            reference_analysis,
            comparison_analysis,
            reference_frame=reference.iloc[:2],
            comparison_frame=comparison,
        )
    with pytest.raises(ValueError, match="labels"):
        compare_dataset_analyses(
            reference_analysis,
            comparison_analysis,
            reference_frame=reference.rename(columns={"x": "y"}),
            comparison_frame=comparison,
        )
    with pytest.raises(ValueError, match="numeric profile"):
        compare_dataset_analyses(
            reference_analysis,
            comparison_analysis,
            reference_frame=reference.assign(x=[1.0, None, 3.0]),
            comparison_frame=comparison,
        )
    with pytest.raises(TypeError):
        compare_dataset_analyses(
            reference_analysis,
            comparison_analysis,
            reference_frame=[1, 2, 3],
            comparison_frame=comparison,
        )


def test_missingness_change_is_separate_from_value_drift() -> None:
    reference = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0]})
    comparison = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0, None, None, None, None]})
    column = compare_dataframes(reference, comparison).columns[0]
    assert column.missingness.missing_count.change == 4
    assert column.distribution.ks_distance.value == 0.0
    assert column.distribution.test.p_value == 1.0


def test_results_are_deterministic_and_source_independent(monkeypatch) -> None:
    rng = np.random.default_rng(38)
    reference = pd.DataFrame(
        {
            "x": rng.normal(size=300),
            "big": np.arange(300, dtype=np.int64) + 2**60,
            "c": pd.Categorical(rng.choice(list("abcd"), 300)),
            "f": rng.random(300) < 0.4,
        }
    )
    comparison = pd.DataFrame(
        {
            "x": rng.normal(0.2, 1.3, size=250),
            "big": np.arange(250, dtype=np.int64) + 2**60 + 7,
            "c": pd.Categorical(rng.choice(list("abce"), 250)),
            "f": rng.random(250) < 0.6,
        }
    )
    first = compare_dataframes(reference, comparison)
    second = compare_dataframes(reference.copy(), comparison.copy())
    assert first == second
    reindexed = reference.copy()
    reindexed.index = np.arange(300)[::-1] * 7
    assert compare_dataframes(reindexed, comparison) == first

    def fail(*args, **kwargs):
        raise AssertionError("source values were read after collection")

    for name in ("_finite_values", "ks_2samp", "kstwo", "_fisher_p_value"):
        monkeypatch.setattr(distribution_module, name, fail)
    assert repr(first)
    assert first.coverage.n_distribution_tests == 4
    forbidden = (pd.DataFrame, pd.Series, pd.Index, np.ndarray, np.generic)
    for item in _walk(first):
        assert not isinstance(item, forbidden)
        assert not callable(item) or isinstance(item, type)
        module = type(item).__module__
        assert not module.startswith(("numpy", "pandas", "scipy"))


def _walk(value: object):
    seen = set()

    def walk(item: object):
        if id(item) in seen:
            return
        seen.add(id(item))
        yield item
        if isinstance(item, tuple):
            for child in item:
                yield from walk(child)
        elif dataclasses.is_dataclass(item) and not isinstance(item, type):
            for field in dataclasses.fields(item):
                yield from walk(getattr(item, field.name))

    yield from walk(value)


def test_drift_effect_methods_are_named() -> None:
    result = compare_dataframes(
        pd.DataFrame({"x": [1.0, 2.0], "c": pd.Categorical(["a", "b"])}),
        pd.DataFrame({"x": [1.0, 3.0], "c": pd.Categorical(["a", "c"])}),
    )
    numeric = _column(result, "x").distribution
    categorical = _column(result, "c").distribution
    assert numeric.ks_distance.method is DriftEffectMethod.KOLMOGOROV_SMIRNOV_DISTANCE
    assert (
        numeric.wasserstein_distance.method is DriftEffectMethod.WASSERSTEIN_1_DISTANCE
    )
    assert numeric.test.method is DriftTestMethod.KOLMOGOROV_SMIRNOV_TWO_SAMPLE
    assert categorical.total_variation_distance.method is (
        DriftEffectMethod.TOTAL_VARIATION_DISTANCE
    )
    assert categorical.test.method is DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY
