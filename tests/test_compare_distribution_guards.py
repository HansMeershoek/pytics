"""TSK-038: distribution-drift record contracts and calculator edge states."""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import pytics.analysis.compare.distribution as distribution_module
from pytics.analysis.compare import BooleanDescriptiveComparison
from pytics.analysis.compare import ComparedCategoryLevel
from pytics.analysis.compare import ComparisonCoverage
from pytics.analysis.compare import CountComparison
from pytics.analysis.compare import DistributionDriftStatus
from pytics.analysis.compare import DriftEffect
from pytics.analysis.compare import DriftEffectMethod
from pytics.analysis.compare import DriftPopulation
from pytics.analysis.compare import DriftPopulationRule
from pytics.analysis.compare import DriftTest
from pytics.analysis.compare import DriftTestMethod
from pytics.analysis.compare import DriftUnavailabilityReason
from pytics.analysis.compare import KolmogorovSmirnovLocation
from pytics.analysis.compare import ProportionDifference
from pytics.analysis.compare import PValueComputation
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare.distribution import boolean_distribution_drift
from pytics.analysis.compare.distribution import categorical_distribution_drift
from pytics.analysis.compare.distribution import numeric_distribution_drift
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability

AVAILABLE = ResultAvailability.AVAILABLE
UNAVAILABLE = ResultAvailability.UNAVAILABLE
NOT_APPLIED = MultipleTestingAdjustment.NOT_APPLIED


def _mixed_result():
    return compare_dataframes(
        pd.DataFrame(
            {
                "x": [1.0, 2.0, 3.0],
                "c": pd.Categorical(["a", "b", "a"]),
                "f": [True, False, True],
            }
        ),
        pd.DataFrame(
            {
                "x": [2.0, 3.0, 5.0],
                "c": pd.Categorical(["a", "b", "b"]),
                "f": [False, False, True],
            }
        ),
    )


def _level(value, reference, comparison):
    return ComparedCategoryLevel(
        value=value,
        reference_count=reference,
        comparison_count=comparison,
        reference_proportion=None if reference is None else 1.0,
        comparison_proportion=None if comparison is None else 1.0,
    )


def test_categorical_calculator_handles_empty_and_single_level_sides() -> None:
    descriptive = _mixed_result().columns[1].categorical
    empty_reference = replace(
        descriptive,
        n_non_missing=CountComparison(0, 3),
        n_observed=CountComparison(0, 1),
        shared_levels=(),
        reference_only_levels=(),
        comparison_only_levels=(_level("a", None, 3),),
    )
    drift = categorical_distribution_drift(empty_reference)
    assert drift.total_variation_distance.reason is (
        DriftUnavailabilityReason.REFERENCE_POPULATION_EMPTY
    )
    assert drift.expected_counts is None
    assert drift.n_comparison_only_observations == 3
    single = replace(
        descriptive,
        n_non_missing=CountComparison(2, 3),
        n_observed=CountComparison(1, 1),
        shared_levels=(_level("a", 2, 3),),
        reference_only_levels=(),
        comparison_only_levels=(),
    )
    drift = categorical_distribution_drift(single)
    assert drift.total_variation_distance.value == 0.0
    assert drift.test.reason is DriftUnavailabilityReason.SINGLE_POOLED_LEVEL
    assert drift.expected_counts.availability is AVAILABLE


def test_boolean_calculator_handles_empty_and_single_value_pools() -> None:
    empty = BooleanDescriptiveComparison(
        true_count=CountComparison(0, 2),
        false_count=CountComparison(0, 1),
        missing_count=CountComparison(3, 0),
        true_proportion=ProportionDifference(None, 2 / 3),
        false_proportion=ProportionDifference(None, 1 / 3),
    )
    drift = boolean_distribution_drift(empty)
    assert drift.true_proportion_difference.reason is (
        DriftUnavailabilityReason.REFERENCE_POPULATION_EMPTY
    )
    all_false = BooleanDescriptiveComparison(
        true_count=CountComparison(0, 0),
        false_count=CountComparison(3, 2),
        missing_count=CountComparison(0, 0),
        true_proportion=ProportionDifference(0.0, 0.0),
        false_proportion=ProportionDifference(1.0, 1.0),
    )
    drift = boolean_distribution_drift(all_false)
    assert drift.true_proportion_difference.value == 0.0
    assert drift.test.reason is DriftUnavailabilityReason.SINGLE_POOLED_LEVEL


def test_numeric_product_beyond_int64_uses_python_integers(monkeypatch) -> None:
    reference = np.array([1.0, 2.0, 3.0, 7.0])
    comparison = np.array([2.0, 4.0, 4.0])
    expected = numeric_distribution_drift(reference, comparison)
    monkeypatch.setattr(distribution_module, "_INT64_MAX", 5)
    assert numeric_distribution_drift(reference, comparison) == expected


def test_one_pooled_value_has_zero_distances() -> None:
    drift = numeric_distribution_drift(np.array([5, 5]), np.array([5]))
    assert drift.n_distinct_pooled_values == 1
    assert drift.ks_distance.value == 0.0
    assert drift.wasserstein_distance.value == 0.0
    assert drift.test.p_value == 1.0


def test_drift_effect_and_test_records_reject_inconsistent_values() -> None:
    with pytest.raises(ValueError, match="range"):
        DriftEffect(DriftEffectMethod.TOTAL_VARIATION_DISTANCE, AVAILABLE, 1.5, None)
    with pytest.raises(ValueError, match="range"):
        DriftEffect(DriftEffectMethod.TRUE_PROPORTION_DIFFERENCE, AVAILABLE, -1.5, None)
    with pytest.raises(ValueError, match="range"):
        DriftEffect(DriftEffectMethod.WASSERSTEIN_1_DISTANCE, AVAILABLE, -1.0, None)
    with pytest.raises(ValueError, match="negative zero"):
        DriftEffect(
            DriftEffectMethod.KOLMOGOROV_SMIRNOV_DISTANCE, AVAILABLE, -0.0, None
        )
    with pytest.raises(ValueError, match="finite"):
        DriftEffect(DriftEffectMethod.WASSERSTEIN_1_DISTANCE, AVAILABLE, math.inf, None)
    with pytest.raises(ValueError, match="no value"):
        DriftEffect(
            DriftEffectMethod.TOTAL_VARIATION_DISTANCE,
            UNAVAILABLE,
            0.1,
            DriftUnavailabilityReason.NON_FINITE_RESULT,
        )
    with pytest.raises(ValueError, match="no unavailability reason"):
        DriftEffect(
            DriftEffectMethod.TOTAL_VARIATION_DISTANCE,
            AVAILABLE,
            0.1,
            DriftUnavailabilityReason.NON_FINITE_RESULT,
        )
    ks = DriftTest(
        method=DriftTestMethod.KOLMOGOROV_SMIRNOV_TWO_SAMPLE,
        computation=PValueComputation.EXACT,
        availability=AVAILABLE,
        statistic=None,
        degrees_of_freedom=None,
        p_value=0.2,
        adjusted_p_value=None,
        adjustment=NOT_APPLIED,
        reason=None,
    )
    with pytest.raises(ValueError, match="computation"):
        replace(
            ks,
            method=DriftTestMethod.FISHER_EXACT_TWO_SAMPLE,
            computation=PValueComputation.ASYMPTOTIC,
        )
    with pytest.raises(ValueError, match="only the chi-square"):
        replace(ks, statistic=1.0)
    with pytest.raises(ValueError, match="degrees of freedom"):
        replace(
            ks,
            method=DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY,
            computation=PValueComputation.ASYMPTOTIC,
            statistic=1.0,
        )
    with pytest.raises(ValueError, match="not negative"):
        replace(
            ks,
            method=DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY,
            computation=PValueComputation.ASYMPTOTIC,
            statistic=-1.0,
            degrees_of_freedom=1,
        )
    with pytest.raises(ValueError, match="unadjusted"):
        replace(ks, adjusted_p_value=0.3)
    with pytest.raises(ValueError, match="less than its raw"):
        replace(
            ks,
            adjusted_p_value=0.1,
            adjustment=MultipleTestingAdjustment.BENJAMINI_HOCHBERG,
        )
    with pytest.raises(ValueError, match="no values"):
        replace(
            ks,
            availability=UNAVAILABLE,
            reason=DriftUnavailabilityReason.NON_FINITE_RESULT,
        )
    with pytest.raises(ValueError, match="not adjusted"):
        replace(
            ks,
            availability=UNAVAILABLE,
            computation=None,
            p_value=None,
            adjustment=MultipleTestingAdjustment.BENJAMINI_HOCHBERG,
            reason=DriftUnavailabilityReason.NON_FINITE_RESULT,
        )
    with pytest.raises(ValueError, match="no unavailability reason"):
        replace(ks, reason=DriftUnavailabilityReason.NON_FINITE_RESULT)
    with pytest.raises(ValueError, match="lie on"):
        replace(ks, p_value=1.5)
    with pytest.raises(ValueError, match="negative zero"):
        KolmogorovSmirnovLocation(-0.0, 0.5, 0.5)
    with pytest.raises(TypeError):
        DriftPopulation("finite", 1, 1)  # type: ignore[arg-type]


def test_family_records_reject_inconsistent_components() -> None:
    result = _mixed_result()
    numeric = result.columns[0].distribution
    categorical = result.columns[1].distribution
    boolean = result.columns[2].distribution
    with pytest.raises(ValueError, match="finite non-missing"):
        replace(
            numeric,
            population=replace(
                numeric.population, rule=DriftPopulationRule.NON_MISSING
            ),
        )
    with pytest.raises(ValueError, match="attain"):
        replace(
            numeric,
            ks_location=replace(
                numeric.ks_location, reference_cumulative_proportion=0.0
            ),
        )
    with pytest.raises(ValueError, match="has a location"):
        replace(numeric, ks_location=None)
    with pytest.raises(ValueError, match="exceed"):
        replace(numeric, n_distinct_pooled_values=7)
    with pytest.raises(ValueError, match="distinct value"):
        replace(numeric, n_distinct_pooled_values=0)
    with pytest.raises(ValueError, match="KS distance"):
        replace(
            numeric,
            ks_distance=DriftEffect(
                DriftEffectMethod.KOLMOGOROV_SMIRNOV_DISTANCE,
                UNAVAILABLE,
                None,
                DriftUnavailabilityReason.NON_FINITE_RESULT,
            ),
        )
    with pytest.raises(ValueError, match="empty population"):
        replace(
            numeric,
            test=replace(
                numeric.test,
                availability=UNAVAILABLE,
                computation=None,
                p_value=None,
                adjusted_p_value=None,
                adjustment=NOT_APPLIED,
                reason=DriftUnavailabilityReason.BOTH_POPULATIONS_EMPTY,
            ),
        )
    with pytest.raises(ValueError, match="empty side"):
        replace(
            numeric,
            population=replace(numeric.population, n_reference=0),
            n_distinct_pooled_values=3,
        )
    with pytest.raises(ValueError, match="effect must be"):
        replace(numeric, wasserstein_distance=numeric.ks_distance)
    with pytest.raises(ValueError, match="KS test"):
        replace(numeric, test=categorical.test)
    with pytest.raises(ValueError, match="n_levels - 1"):
        replace(categorical, n_levels=5)
    with pytest.raises(ValueError, match="exceed the reference"):
        replace(categorical, n_reference_only_observations=9)
    with pytest.raises(ValueError, match="expected counts"):
        replace(categorical, expected_counts=None)
    with pytest.raises(ValueError, match="homogeneity"):
        replace(categorical, test=boolean.test)
    with pytest.raises(ValueError, match="non-missing"):
        replace(
            boolean,
            population=replace(
                boolean.population, rule=DriftPopulationRule.FINITE_NON_MISSING
            ),
        )
    with pytest.raises(ValueError, match="Fisher"):
        replace(boolean, test=numeric.test)
    with pytest.raises(ValueError, match="empty side"):
        replace(boolean, population=replace(boolean.population, n_comparison=0))


def test_column_comparison_ties_drift_to_the_descriptive_record() -> None:
    result = _mixed_result()
    numeric_column, categorical_column, boolean_column = result.columns
    with pytest.raises(ValueError, match="match the drift status"):
        replace(numeric_column, distribution=None)
    with pytest.raises(ValueError, match="no drift payload"):
        replace(
            numeric_column,
            distribution_status=DistributionDriftStatus.SOURCE_VALUES_NOT_SUPPLIED,
        )
    with pytest.raises(ValueError, match="eligible for distribution drift"):
        replace(
            numeric_column,
            distribution_status=DistributionDriftStatus.NOT_ELIGIBLE,
            distribution=None,
        )
    with pytest.raises(ValueError, match="descriptive comparison"):
        replace(
            numeric_column,
            distribution=replace(
                numeric_column.distribution,
                population=replace(
                    numeric_column.distribution.population, n_reference=2
                ),
                n_distinct_pooled_values=4,
            ),
        )
    with pytest.raises(ValueError, match="partition"):
        replace(
            categorical_column,
            distribution=replace(
                categorical_column.distribution, n_comparison_only_observations=1
            ),
        )
    with pytest.raises(ValueError, match="proportion change"):
        replace(
            boolean_column,
            distribution=replace(
                boolean_column.distribution,
                true_proportion_difference=replace(
                    boolean_column.distribution.true_proportion_difference, value=0.5
                ),
            ),
        )
    with pytest.raises(ValueError, match="descriptive counts"):
        replace(
            boolean_column,
            distribution=replace(
                boolean_column.distribution,
                population=replace(
                    boolean_column.distribution.population, n_reference=9
                ),
            ),
        )
    unmatched = compare_dataframes(
        pd.DataFrame({"a": [1.0, 2.0]}), pd.DataFrame({"b": [1.0, 2.0]})
    ).columns[0]
    with pytest.raises(ValueError, match="waits for source values"):
        replace(
            unmatched,
            distribution_status=DistributionDriftStatus.SOURCE_VALUES_NOT_SUPPLIED,
        )
    coverage = result.coverage
    with pytest.raises(ValueError, match="sum to n_columns"):
        replace(coverage, n_distribution_not_eligible=1)
    with pytest.raises(ValueError, match="every drift record"):
        replace(coverage, n_distribution_tests=2)
    with pytest.raises(ValueError, match="exceed drift records"):
        replace(coverage, n_distribution_primary_effects_unavailable=4)
    with pytest.raises(ValueError, match="numeric records"):
        replace(coverage, n_wasserstein_distances_unavailable=2)
    assert isinstance(coverage, ComparisonCoverage)
    assert coverage.n_distribution_drift_records == 3
