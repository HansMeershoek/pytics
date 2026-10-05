"""Univariate distribution drift for matched columns.

Eligibility is the descriptive comparison's. A column gets a drift record
only when it already has a typed Numeric, Categorical, or Boolean
descriptive comparison. Nothing here decides a semantic type.

Categorical and Boolean drift read the counts the descriptive comparison
already holds. They do not read a frame. Numeric drift needs both
empirical distributions, which the retained profiles do not keep, so it
reads each side's finite values once through the same reader the
Numeric profile used and checks the count against that profile. This is
the only module of the comparison package that reads source values. The
arrays are discarded before a record is returned.

Numeric values are compared exactly. Two float samples pool as float64.
Two integer samples pool as one integer dtype, or as Python integers when
``int64`` and ``uint64`` cannot share one. An integer sample that fits the
exact float64 range pools with a float sample as float64; otherwise both
pool as Python numbers, whose mixed comparisons are exact. The KS test
receives dense ranks of that pooled order, which keep every ``<``, ``>``,
and tie of the original values. The Wasserstein distance needs the real
gaps between values, so the gaps are taken exactly before one float64
rounding.

The KS p-value is exact when the larger side has at most 10,000 values
and asymptotic above that, which is SciPy's automatic rule. The exact
probability comes from ``scipy.stats.ks_2samp``. The asymptotic tail is
``scipy.stats.kstwo.sf(D, round(n_r * n_c / (n_r + n_c)))``, the same
approximation that function uses, evaluated on the exact distance so the
pooled sample is not sorted a second time.

Pearson's chi-square, its expected-count checkpoints, Fisher's exact
p-value, and Benjamini–Hochberg are the relationship package's
implementations. They are not reimplemented here.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from dataclasses import replace
from fractions import Fraction
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from scipy.stats import kstwo

from pytics.analysis.compare.descriptive import BooleanDescriptiveComparison
from pytics.analysis.compare.descriptive import CategoricalDescriptiveComparison
from pytics.analysis.compare.distribution_models import BooleanDistributionDrift
from pytics.analysis.compare.distribution_models import CategoricalDistributionDrift
from pytics.analysis.compare.distribution_models import DistributionDrift
from pytics.analysis.compare.distribution_models import DriftEffect
from pytics.analysis.compare.distribution_models import DriftEffectMethod
from pytics.analysis.compare.distribution_models import DriftPopulation
from pytics.analysis.compare.distribution_models import DriftPopulationRule
from pytics.analysis.compare.distribution_models import DriftTest
from pytics.analysis.compare.distribution_models import DriftTestMethod
from pytics.analysis.compare.distribution_models import DriftUnavailabilityReason
from pytics.analysis.compare.distribution_models import KolmogorovSmirnovLocation
from pytics.analysis.compare.distribution_models import NumericDistributionDrift
from pytics.analysis.compare.distribution_models import PValueComputation
from pytics.analysis.numeric import _finite_values
from pytics.analysis.relationships.adjustment import benjamini_hochberg
from pytics.analysis.relationships.boolean_boolean import _INT64_MAX
from pytics.analysis.relationships.boolean_boolean import _fisher_p_value
from pytics.analysis.relationships.categorical_categorical import (
    _expected_count_diagnostics,
)
from pytics.analysis.relationships.categorical_categorical import (
    _pearson_chi_square_from_counts,
)
from pytics.analysis.relationships.categorical_categorical import _pearson_p_value
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability

# SciPy's ``ks_2samp(method="auto")`` attempts the exact distribution when
# neither sample is larger than this.
_EXACT_KS_LIMIT = 10_000

# Integers in [-2**53, 2**53] convert to float64 without rounding.
_FLOAT64_EXACT_INTEGER = 2**53


@dataclass(frozen=True)
class _PooledSample:
    """Pooled order of two finite samples. Temporary, never retained.

    ``distinct`` is the sorted distinct values: a NumPy array, or a tuple
    of Python numbers on the exact fallback. The cumulative counts give
    each side's observations at or below each distinct value. The ranks
    are each observation's index in ``distinct``.
    """

    distinct: Sequence[object]
    reference_cumulative: np.ndarray
    comparison_cumulative: np.ndarray
    reference_ranks: np.ndarray
    comparison_ranks: np.ndarray


def read_numeric_population(series: pd.Series, finite_count: int) -> np.ndarray:
    """Return one side's finite non-missing values.

    The reader is the Numeric profile's own, so the population is the
    profile's population. A count that disagrees with the retained
    profile means the frame is not the one that was analyzed.
    """
    values = _finite_values(series)
    if int(values.size) != finite_count:
        raise ValueError("source frame does not match the retained numeric profile")
    return values


def numeric_distribution_drift(
    reference: np.ndarray,
    comparison: np.ndarray,
) -> NumericDistributionDrift:
    """KS distance, Wasserstein distance, and the KS test of two finite samples."""
    population = DriftPopulation(
        rule=DriftPopulationRule.FINITE_NON_MISSING,
        n_reference=int(reference.size),
        n_comparison=int(comparison.size),
    )
    empty = population.empty_reason
    if empty is not None:
        observed = reference if reference.size else comparison
        return NumericDistributionDrift(
            population=population,
            n_distinct_pooled_values=int(np.unique(observed).size),
            ks_distance=_unavailable_effect(
                DriftEffectMethod.KOLMOGOROV_SMIRNOV_DISTANCE, empty
            ),
            ks_location=None,
            wasserstein_distance=_unavailable_effect(
                DriftEffectMethod.WASSERSTEIN_1_DISTANCE, empty
            ),
            test=_unavailable_test(DriftTestMethod.KOLMOGOROV_SMIRNOV_TWO_SAMPLE, empty),
        )
    n_reference = population.n_reference
    n_comparison = population.n_comparison
    pooled = _pooled_sample(reference, comparison)
    n_product = n_reference * n_comparison
    weights = _ecdf_gap_weights(pooled, n_reference, n_comparison)
    peak = int(np.argmax(weights))
    peak_weight = int(weights[peak])
    distance = _unit_quotient(peak_weight, n_product)
    location = None
    if peak_weight > 0:
        location = KolmogorovSmirnovLocation(
            value=_python_number(pooled.distinct[peak]),
            reference_cumulative_proportion=_unit_quotient(
                int(pooled.reference_cumulative[peak]), n_reference
            ),
            comparison_cumulative_proportion=_unit_quotient(
                int(pooled.comparison_cumulative[peak]), n_comparison
            ),
        )
    return NumericDistributionDrift(
        population=population,
        n_distinct_pooled_values=len(pooled.distinct),
        ks_distance=_available_effect(
            DriftEffectMethod.KOLMOGOROV_SMIRNOV_DISTANCE, distance
        ),
        ks_location=location,
        wasserstein_distance=_wasserstein_effect(pooled, weights, n_product),
        test=_ks_test(distance, pooled, n_reference, n_comparison),
    )


def categorical_distribution_drift(
    descriptive: CategoricalDescriptiveComparison,
) -> CategoricalDistributionDrift:
    """Total variation distance and chi-square homogeneity from retained levels.

    Levels are the descriptive partition, so category identity is the
    partition's. Shared levels come first, then reference-only, then
    comparison-only. Only the 2 by k margins and positive cells are
    built, so memory stays linear in the number of levels.
    """
    n_reference = descriptive.n_non_missing.reference
    n_comparison = descriptive.n_non_missing.comparison
    population = DriftPopulation(
        rule=DriftPopulationRule.NON_MISSING,
        n_reference=n_reference,
        n_comparison=n_comparison,
    )
    levels = (
        descriptive.shared_levels
        + descriptive.reference_only_levels
        + descriptive.comparison_only_levels
    )
    reference_only = sum(
        level.reference_count for level in descriptive.reference_only_levels
    )
    comparison_only = sum(
        level.comparison_count for level in descriptive.comparison_only_levels
    )
    empty = population.empty_reason
    if empty is not None:
        return CategoricalDistributionDrift(
            population=population,
            n_levels=len(levels),
            n_reference_only_observations=reference_only,
            n_comparison_only_observations=comparison_only,
            total_variation_distance=_unavailable_effect(
                DriftEffectMethod.TOTAL_VARIATION_DISTANCE, empty
            ),
            expected_counts=None,
            test=_unavailable_test(
                DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY, empty
            ),
        )
    numerator = 0
    cells: List[Tuple[int, int, int]] = []
    pooled_totals: List[int] = []
    for index, level in enumerate(levels):
        reference_count = level.reference_count or 0
        comparison_count = level.comparison_count or 0
        numerator += abs(reference_count * n_comparison - comparison_count * n_reference)
        if reference_count:
            cells.append((0, index, reference_count))
        if comparison_count:
            cells.append((1, index, comparison_count))
        pooled_totals.append(reference_count + comparison_count)
    side_totals = (n_reference, n_comparison)
    n_pooled = n_reference + n_comparison
    return CategoricalDistributionDrift(
        population=population,
        n_levels=len(levels),
        n_reference_only_observations=reference_only,
        n_comparison_only_observations=comparison_only,
        total_variation_distance=_available_effect(
            DriftEffectMethod.TOTAL_VARIATION_DISTANCE,
            _unit_quotient(numerator, 2 * n_reference * n_comparison),
        ),
        expected_counts=_expected_count_diagnostics(
            side_totals, tuple(pooled_totals), n_pooled
        ),
        test=_homogeneity_test(
            tuple(cells), side_totals, tuple(pooled_totals), n_pooled
        ),
    )


def boolean_distribution_drift(
    descriptive: BooleanDescriptiveComparison,
) -> BooleanDistributionDrift:
    """True-share difference and Fisher's exact test from retained counts.

    The difference is the descriptive True-proportion change, reused so
    the comparison holds one value for it. The Fisher table is side by
    False and True. Its two-sided p-value does not depend on that
    orientation.
    """
    reference_true = descriptive.true_count.reference
    reference_false = descriptive.false_count.reference
    comparison_true = descriptive.true_count.comparison
    comparison_false = descriptive.false_count.comparison
    population = DriftPopulation(
        rule=DriftPopulationRule.NON_MISSING,
        n_reference=reference_true + reference_false,
        n_comparison=comparison_true + comparison_false,
    )
    method = DriftTestMethod.FISHER_EXACT_TWO_SAMPLE
    empty = population.empty_reason
    if empty is not None:
        return BooleanDistributionDrift(
            population=population,
            true_proportion_difference=_unavailable_effect(
                DriftEffectMethod.TRUE_PROPORTION_DIFFERENCE, empty
            ),
            test=_unavailable_test(method, empty),
        )
    difference = descriptive.true_proportion.change
    if difference is None:
        raise ValueError("two non-empty Boolean samples have a proportion change")
    if reference_true + comparison_true == 0 or reference_false + comparison_false == 0:
        test = _unavailable_test(method, DriftUnavailabilityReason.SINGLE_POOLED_LEVEL)
    elif max(reference_true, reference_false, comparison_true, comparison_false) > (
        _INT64_MAX
    ):
        test = _unavailable_test(method, DriftUnavailabilityReason.NON_FINITE_RESULT)
    else:
        p_value = _fisher_p_value(
            reference_false, reference_true, comparison_false, comparison_true
        )
        test = _p_value_test(method, PValueComputation.EXACT, p_value)
    return BooleanDistributionDrift(
        population=population,
        true_proportion_difference=_available_effect(
            DriftEffectMethod.TRUE_PROPORTION_DIFFERENCE, difference
        ),
        test=test,
    )


def adjust_drift_tests(
    records: Tuple[Optional[DistributionDrift], ...],
) -> Tuple[Optional[DistributionDrift], ...]:
    """Benjamini–Hochberg over the available primary drift tests.

    Each record contributes its one primary test when the raw p-value is
    available. Effects do not enter. An unavailable test stays
    unadjusted. ``m`` is the number of available p-values. Records keep
    their order.
    """
    members = [
        index
        for index, record in enumerate(records)
        if record is not None
        and record.test.availability is ResultAvailability.AVAILABLE
    ]
    if not members:
        return records
    adjusted = benjamini_hochberg(
        tuple(records[index].test.p_value for index in members)  # type: ignore[union-attr]
    )
    updated = list(records)
    for index, value in zip(members, adjusted):
        record = records[index]
        updated[index] = replace(  # type: ignore[type-var]
            record,
            test=replace(
                record.test,  # type: ignore[union-attr]
                adjusted_p_value=value,
                adjustment=MultipleTestingAdjustment.BENJAMINI_HOCHBERG,
            ),
        )
    return tuple(updated)


def _pooled_sample(reference: np.ndarray, comparison: np.ndarray) -> _PooledSample:
    image = _common_image(reference, comparison)
    if image is None:
        return _pooled_python_numbers(reference, comparison)
    reference_image, comparison_image = image
    n_reference = int(reference_image.size)
    distinct, inverse = np.unique(
        np.concatenate((reference_image, comparison_image)),
        return_inverse=True,
    )
    inverse = inverse.reshape(-1)
    return _from_ranks(
        distinct, inverse[:n_reference], inverse[n_reference:], int(distinct.size)
    )


def _common_image(
    reference: np.ndarray,
    comparison: np.ndarray,
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """One NumPy dtype that holds both samples exactly, or ``None``."""
    reference_kind = reference.dtype.kind
    comparison_kind = comparison.dtype.kind
    kinds = {reference_kind, comparison_kind}
    if not kinds <= {"i", "u", "f"}:
        raise TypeError("numeric drift compares integer and floating values")
    if kinds == {"f"}:
        return (
            reference.astype(np.float64, copy=False),
            comparison.astype(np.float64, copy=False),
        )
    if "f" not in kinds:
        if reference_kind == comparison_kind:
            target = np.int64 if reference_kind == "i" else np.uint64
            return reference.astype(target, copy=False), comparison.astype(
                target, copy=False
            )
        signed, unsigned = (
            (reference, comparison) if reference_kind == "i" else (comparison, reference)
        )
        if int(signed.min()) >= 0:
            target = np.uint64
        elif int(unsigned.max()) <= _INT64_MAX:
            target = np.int64
        else:
            return None
        return reference.astype(target, copy=False), comparison.astype(
            target, copy=False
        )
    integer = reference if reference_kind != "f" else comparison
    if (
        int(integer.min()) < -_FLOAT64_EXACT_INTEGER
        or int(integer.max()) > _FLOAT64_EXACT_INTEGER
    ):
        return None
    return (
        reference.astype(np.float64, copy=False),
        comparison.astype(np.float64, copy=False),
    )


def _pooled_python_numbers(
    reference: np.ndarray,
    comparison: np.ndarray,
) -> _PooledSample:
    """Exact pooling through Python ints and floats.

    Python compares an int with a float exactly, so ``2**53 + 1`` stays
    above ``float(2**53)`` and equal values remain one tie. Slower than
    the NumPy path, and only used when no NumPy dtype holds both samples.
    """
    reference_values = reference.tolist()
    comparison_values = comparison.tolist()
    distinct = tuple(sorted(set(reference_values) | set(comparison_values)))
    index = {value: position for position, value in enumerate(distinct)}
    reference_ranks = np.fromiter(
        (index[value] for value in reference_values),
        dtype=np.int64,
        count=len(reference_values),
    )
    comparison_ranks = np.fromiter(
        (index[value] for value in comparison_values),
        dtype=np.int64,
        count=len(comparison_values),
    )
    return _from_ranks(distinct, reference_ranks, comparison_ranks, len(distinct))


def _from_ranks(
    distinct: Sequence[object],
    reference_ranks: np.ndarray,
    comparison_ranks: np.ndarray,
    n_distinct: int,
) -> _PooledSample:
    return _PooledSample(
        distinct=distinct,
        reference_cumulative=np.cumsum(
            np.bincount(reference_ranks, minlength=n_distinct)
        ),
        comparison_cumulative=np.cumsum(
            np.bincount(comparison_ranks, minlength=n_distinct)
        ),
        reference_ranks=reference_ranks,
        comparison_ranks=comparison_ranks,
    )


def _ecdf_gap_weights(
    pooled: _PooledSample,
    n_reference: int,
    n_comparison: int,
) -> np.ndarray:
    """``|F_r - F_c| * n_r * n_c`` at each distinct value, as exact integers.

    The ECDFs are right-continuous step functions that change only at
    the pooled values, so their largest gap is attained at one of them.
    """
    reference_cumulative = pooled.reference_cumulative
    comparison_cumulative = pooled.comparison_cumulative
    if n_reference * n_comparison > _INT64_MAX:
        reference_cumulative = reference_cumulative.astype(object)
        comparison_cumulative = comparison_cumulative.astype(object)
    return np.abs(
        reference_cumulative * n_comparison - comparison_cumulative * n_reference
    )


def _wasserstein_effect(
    pooled: _PooledSample,
    weights: np.ndarray,
    n_product: int,
) -> DriftEffect:
    """``sum_i |F_r - F_c|(x_i) * (x_{i+1} - x_i)`` over consecutive distinct values."""
    method = DriftEffectMethod.WASSERSTEIN_1_DISTANCE
    if len(pooled.distinct) < 2:
        return _available_effect(method, 0.0)
    if isinstance(pooled.distinct, tuple):
        value = _exact_wasserstein(pooled.distinct, weights, n_product)
    else:
        value = _float_wasserstein(pooled.distinct, weights, n_product)
    if value is None:
        return _unavailable_effect(method, DriftUnavailabilityReason.NON_FINITE_RESULT)
    return _available_effect(method, value)


def _float_wasserstein(
    distinct: np.ndarray,
    weights: np.ndarray,
    n_product: int,
) -> Optional[float]:
    """Gaps exact before one float64 rounding, then a float64 sum.

    Integer gaps are taken in unsigned 64-bit arithmetic, which is exact
    for any two sorted 64-bit integers. A float gap is one correctly
    rounded subtraction. Integer weights multiply the gaps before the one
    division by ``n_r * n_c``, so subnormal gaps are not rounded away.
    When that product overflows, each gap is scaled by its CDF share
    first, and a float gap that overflows is taken from the halved
    endpoints, so a distance that fits float64 is not lost.
    """
    scale = float(n_product)
    weights = np.asarray(weights[:-1], dtype=np.float64)
    moved = weights > 0.0
    with np.errstate(over="ignore", invalid="ignore"):
        if distinct.dtype.kind == "f":
            gaps = np.diff(distinct)
        else:
            unsigned = distinct.view(np.uint64)
            gaps = (unsigned[1:] - unsigned[:-1]).astype(np.float64)
        total = float(np.sum(np.where(moved, weights * gaps, 0.0))) / scale
        if not math.isfinite(total):
            shares = weights / scale
            terms = np.where(moved, shares * gaps, 0.0)
            overflowed = moved & ~np.isfinite(gaps)
            if overflowed.any():
                upper = distinct[1:][overflowed] * 0.5
                lower = distinct[:-1][overflowed] * 0.5
                terms[overflowed] = 2.0 * (shares[overflowed] * (upper - lower))
            total = float(np.sum(terms))
    if not math.isfinite(total) or total < 0.0:
        return None
    return 0.0 if total == 0.0 else total


def _exact_wasserstein(
    distinct: Tuple[object, ...],
    weights: np.ndarray,
    n_product: int,
) -> Optional[float]:
    total = Fraction(0)
    for weight, lower, upper in zip(weights[:-1].tolist(), distinct[:-1], distinct[1:]):
        if weight:
            total += weight * (Fraction(upper) - Fraction(lower))
    try:
        value = float(total / n_product)
    except OverflowError:
        return None
    return 0.0 if value == 0.0 else value


def _ks_test(
    distance: float,
    pooled: _PooledSample,
    n_reference: int,
    n_comparison: int,
) -> DriftTest:
    method = DriftTestMethod.KOLMOGOROV_SMIRNOV_TWO_SAMPLE
    if max(n_reference, n_comparison) <= _EXACT_KS_LIMIT:
        exact = _exact_ks_p_value(pooled.reference_ranks, pooled.comparison_ranks)
        if exact is not None:
            return _p_value_test(method, PValueComputation.EXACT, exact)
    asymptotic = _asymptotic_ks_p_value(distance, n_reference, n_comparison)
    return _p_value_test(method, PValueComputation.ASYMPTOTIC, asymptotic)


def _exact_ks_p_value(
    reference_ranks: np.ndarray,
    comparison_ranks: np.ndarray,
) -> Optional[float]:
    """SciPy's exact two-sided probability on the dense-rank image.

    SciPy warns when it abandons the exact computation. That result is
    not used, so a p-value labelled exact is the exact calculation.
    """
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = ks_2samp(
                reference_ranks.astype(np.float64),
                comparison_ranks.astype(np.float64),
                "two-sided",
                "exact",
            )
    except (ValueError, FloatingPointError, OverflowError):
        return None
    if any(issubclass(item.category, RuntimeWarning) for item in caught):
        return None
    return _as_p_value(result[1])


def _asymptotic_ks_p_value(
    distance: float,
    n_reference: int,
    n_comparison: int,
) -> Optional[float]:
    larger, smaller = sorted((float(n_reference), float(n_comparison)), reverse=True)
    effective = larger * smaller / (larger + smaller)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            raw = kstwo.sf(distance, np.round(effective))
    except (ValueError, FloatingPointError, OverflowError):
        return None
    return _as_p_value(raw)


def _homogeneity_test(
    cells: Tuple[Tuple[int, int, int], ...],
    side_totals: Tuple[int, int],
    level_totals: Tuple[int, ...],
    n_pooled: int,
) -> DriftTest:
    method = DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY
    if len(level_totals) < 2:
        return _unavailable_test(method, DriftUnavailabilityReason.SINGLE_POOLED_LEVEL)
    statistic = _pearson_chi_square_from_counts(
        cells, side_totals, level_totals, n_pooled
    )
    if statistic is None:
        return _unavailable_test(method, DriftUnavailabilityReason.NON_FINITE_RESULT)
    degrees_of_freedom = len(level_totals) - 1
    p_value = _pearson_p_value(statistic, degrees_of_freedom)
    if p_value is None:
        return _unavailable_test(method, DriftUnavailabilityReason.NON_FINITE_RESULT)
    return DriftTest(
        method=method,
        computation=PValueComputation.ASYMPTOTIC,
        availability=ResultAvailability.AVAILABLE,
        statistic=statistic,
        degrees_of_freedom=degrees_of_freedom,
        p_value=p_value,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )


def _p_value_test(
    method: DriftTestMethod,
    computation: PValueComputation,
    p_value: Optional[float],
) -> DriftTest:
    if p_value is None:
        return _unavailable_test(method, DriftUnavailabilityReason.NON_FINITE_RESULT)
    return DriftTest(
        method=method,
        computation=computation,
        availability=ResultAvailability.AVAILABLE,
        statistic=None,
        degrees_of_freedom=None,
        p_value=p_value,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )


def _unavailable_test(
    method: DriftTestMethod,
    reason: DriftUnavailabilityReason,
) -> DriftTest:
    return DriftTest(
        method=method,
        computation=None,
        availability=ResultAvailability.UNAVAILABLE,
        statistic=None,
        degrees_of_freedom=None,
        p_value=None,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=reason,
    )


def _available_effect(method: DriftEffectMethod, value: float) -> DriftEffect:
    return DriftEffect(
        method=method,
        availability=ResultAvailability.AVAILABLE,
        value=0.0 if value == 0.0 else value,
        reason=None,
    )


def _unavailable_effect(
    method: DriftEffectMethod,
    reason: DriftUnavailabilityReason,
) -> DriftEffect:
    return DriftEffect(
        method=method,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _unit_quotient(numerator: int, denominator: int) -> float:
    """``numerator / denominator`` for exact integers, rounded once."""
    value = numerator / denominator
    return 0.0 if value == 0.0 else value


def _python_number(value: object) -> object:
    if isinstance(value, np.generic):
        value = value.item()
    if type(value) is float and value == 0.0:
        return 0.0
    return value


def _as_p_value(value: object) -> Optional[float]:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0.0 or number > 1.0:
        return None
    return 0.0 if number == 0.0 else number
