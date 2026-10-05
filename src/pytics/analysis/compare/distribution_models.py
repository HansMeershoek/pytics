"""Frozen records of univariate distribution drift.

The question is how the distribution of one matched variable differs
from the reference dataset to the comparison dataset, how large that
difference is, and what frequentist evidence speaks against equal source
distributions. Drift here means a difference between two observed
distributions. It is not degradation, not an error, and not a cause.
A small p-value does not make a difference important, and a large
distance does not make the comparison dataset invalid.

Each record keeps its population, one or two effects, and one primary
test as separate components. Effects come first. A component can be
unavailable on its own, with a reason, and that does not erase the
others. There is no score, no severity, no threshold, and no
significance flag.

Missing values are not part of any population. Missingness change is
the column's missingness comparison. Numeric infinities are not part of
the Numeric population. Their counts are on the Numeric descriptive
comparison.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Union

from pytics.analysis.compare.values import _require_count
from pytics.analysis.compare.values import _require_optional
from pytics.analysis.compare.values import _require_type
from pytics.analysis.relationships.models import ExpectedCountDiagnostics
from pytics.analysis.relationships.models import InferentialInvalidityReason
from pytics.analysis.relationships.models import InferentialValidity
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import chi_square_inferential_status

# A float evaluation of a bounded quantity, or of the same rational
# number reached by two roundings, may differ from it by a few ulps.
_FLOAT_AGREEMENT = 1e-12


class DistributionDriftStatus(Enum):
    """Whether one column received a distribution-drift record.

    ``NOT_ELIGIBLE`` follows the descriptive comparison: a column without
    a typed Numeric, Categorical, or Boolean descriptive comparison has
    no distribution drift. The descriptive status and reason say why.
    ``SOURCE_VALUES_NOT_SUPPLIED`` means the column was eligible and the
    drift pass did not run, because the comparison was built from the two
    analyses without their source frames. Neither status means the
    distributions were equal.
    """

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    NOT_ELIGIBLE = "not_eligible"
    SOURCE_VALUES_NOT_SUPPLIED = "source_values_not_supplied"


class DriftPopulationRule(Enum):
    """Which observations of each side a drift record compares.

    ``FINITE_NON_MISSING`` drops missing values and both infinities. It is
    the population of the Numeric descriptive profile. ``NON_MISSING``
    drops missing values only. Missing is never a category.
    """

    FINITE_NON_MISSING = "finite_non_missing"
    NON_MISSING = "non_missing"


class DriftEffectMethod(Enum):
    """How one drift effect is defined.

    ``KOLMOGOROV_SMIRNOV_DISTANCE`` is ``sup_x |F_c(x) - F_r(x)|`` over the
    two empirical CDFs, on ``[0, 1]``. It depends only on order and
    equality, so it does not change under a strictly increasing
    transformation of the values and it is comparable across columns.

    ``WASSERSTEIN_1_DISTANCE`` is ``integral |F_c(x) - F_r(x)| dx``, the
    mean distance mass must move to turn one empirical distribution into
    the other. It is in the units of the column, so it is not comparable
    across columns with different units or scales. It is not normalized.

    ``TOTAL_VARIATION_DISTANCE`` is ``1/2 * sum_i |p_c(i) - p_r(i)|`` over
    the union of observed levels, on ``[0, 1]``. It is the largest
    difference in probability the two distributions give to any set of
    levels, and the share of mass that would have to move to make them
    equal.

    ``TRUE_PROPORTION_DIFFERENCE`` is ``p_c(True) - p_r(True)``, on
    ``[-1, 1]``. Its absolute value is the total variation distance of
    the two Bernoulli distributions, which is not stored separately.
    """

    KOLMOGOROV_SMIRNOV_DISTANCE = "kolmogorov_smirnov_distance"
    WASSERSTEIN_1_DISTANCE = "wasserstein_1_distance"
    TOTAL_VARIATION_DISTANCE = "total_variation_distance"
    TRUE_PROPORTION_DIFFERENCE = "true_proportion_difference"


class DriftTestMethod(Enum):
    """The primary frequentist test of one drift family.

    Every null hypothesis is that the reference and comparison
    observations come from one common distribution. A p-value measures
    incompatibility with that null. It is not the size of the difference.

    ``KOLMOGOROV_SMIRNOV_TWO_SAMPLE`` is the two-sided two-sample KS test
    on the KS distance. Its null distribution assumes a continuous common
    distribution. With tied values the reported p-value is conservative:
    under the null, a distance at least as large is at most that likely.

    ``PEARSON_CHI_SQUARE_HOMOGENEITY`` is the uncorrected Pearson
    statistic on the 2 by k table of side by observed level, with
    ``k - 1`` degrees of freedom and an asymptotic upper tail.

    ``FISHER_EXACT_TWO_SAMPLE`` is the two-sided Fisher exact test on the
    2 by 2 table of side by Boolean value, conditional on its margins.
    """

    KOLMOGOROV_SMIRNOV_TWO_SAMPLE = "kolmogorov_smirnov_two_sample"
    PEARSON_CHI_SQUARE_HOMOGENEITY = "pearson_chi_square_homogeneity"
    FISHER_EXACT_TWO_SAMPLE = "fisher_exact_two_sample"


class PValueComputation(Enum):
    """Whether a p-value is an exact null probability or an approximation."""

    EXACT = "exact"
    ASYMPTOTIC = "asymptotic"


class DriftUnavailabilityReason(Enum):
    """Why one drift component has no value."""

    REFERENCE_POPULATION_EMPTY = "reference_population_empty"
    COMPARISON_POPULATION_EMPTY = "comparison_population_empty"
    BOTH_POPULATIONS_EMPTY = "both_populations_empty"
    SINGLE_POOLED_LEVEL = "single_pooled_level"
    NON_FINITE_RESULT = "non_finite_result"


_POPULATION_REASONS = frozenset(
    {
        DriftUnavailabilityReason.REFERENCE_POPULATION_EMPTY,
        DriftUnavailabilityReason.COMPARISON_POPULATION_EMPTY,
        DriftUnavailabilityReason.BOTH_POPULATIONS_EMPTY,
    }
)

_TEST_COMPUTATIONS = {
    DriftTestMethod.KOLMOGOROV_SMIRNOV_TWO_SAMPLE: frozenset(
        {PValueComputation.EXACT, PValueComputation.ASYMPTOTIC}
    ),
    DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY: frozenset(
        {PValueComputation.ASYMPTOTIC}
    ),
    DriftTestMethod.FISHER_EXACT_TWO_SAMPLE: frozenset({PValueComputation.EXACT}),
}


@dataclass(frozen=True)
class DriftPopulation:
    """Observations each side contributes to one drift record."""

    rule: DriftPopulationRule
    n_reference: int
    n_comparison: int

    def __post_init__(self) -> None:
        _require_type(self.rule, DriftPopulationRule, "rule")
        _require_count(self.n_reference, "n_reference")
        _require_count(self.n_comparison, "n_comparison")

    @property
    def empty_reason(self) -> Optional[DriftUnavailabilityReason]:
        """The population reason a component is unavailable, if any side is empty."""
        if self.n_reference == 0 and self.n_comparison == 0:
            return DriftUnavailabilityReason.BOTH_POPULATIONS_EMPTY
        if self.n_reference == 0:
            return DriftUnavailabilityReason.REFERENCE_POPULATION_EMPTY
        if self.n_comparison == 0:
            return DriftUnavailabilityReason.COMPARISON_POPULATION_EMPTY
        return None


@dataclass(frozen=True)
class DriftEffect:
    """One effect of a drift record, named by its method.

    The value is a finite float within the method's range. ``-0.0`` is
    not stored. An unavailable effect has no value and names why.
    """

    method: DriftEffectMethod
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[DriftUnavailabilityReason]

    def __post_init__(self) -> None:
        _require_type(self.method, DriftEffectMethod, "method")
        _require_type(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.UNAVAILABLE:
            if self.value is not None:
                raise ValueError("an unavailable effect has no value")
            _require_type(self.reason, DriftUnavailabilityReason, "reason")
            return
        if self.reason is not None:
            raise ValueError("an available effect has no unavailability reason")
        _require_plain_float(self.value, "value")
        if self.method is DriftEffectMethod.WASSERSTEIN_1_DISTANCE:
            lower, upper = 0.0, math.inf
        elif self.method is DriftEffectMethod.TRUE_PROPORTION_DIFFERENCE:
            lower, upper = -1.0, 1.0
        else:
            lower, upper = 0.0, 1.0
        if self.value < lower or self.value > upper:  # type: ignore[operator]
            raise ValueError(f"{self.method.value} lies outside its range")


@dataclass(frozen=True)
class KolmogorovSmirnovLocation:
    """Where the two empirical CDFs differ most.

    ``value`` is the smallest pooled observed value at which
    ``|F_c - F_r|`` reaches the KS distance. The two proportions are the
    shares of each side at or below that value. When the comparison share
    is larger, the comparison has more mass at or below ``value``. The
    location is a Python int or finite float, never a NumPy scalar.
    """

    value: Union[int, float]
    reference_cumulative_proportion: float
    comparison_cumulative_proportion: float

    def __post_init__(self) -> None:
        if type(self.value) is not int:
            _require_plain_float(self.value, "value")
        _require_unit(
            self.reference_cumulative_proportion,
            "reference_cumulative_proportion",
        )
        _require_unit(
            self.comparison_cumulative_proportion,
            "comparison_cumulative_proportion",
        )

    @property
    def cumulative_difference(self) -> float:
        """``comparison_cumulative_proportion - reference_cumulative_proportion``."""
        return (
            self.comparison_cumulative_proportion - self.reference_cumulative_proportion
        )


@dataclass(frozen=True)
class DriftTest:
    """The primary frequentist test of one drift record.

    ``p_value`` is the raw p-value. ``0.0`` is kept when the library
    tail underflows. ``availability`` says the tail was computed.
    ``inferential_validity`` says whether that tail may be read as an
    inferential probability. A chi-square tail that fails Cochran's
    expected-count convention stays computed and is not valid.
    ``adjusted_p_value`` is the Benjamini–Hochberg companion of an
    inferentially valid raw p-value inside one dataset comparison.
    Neither is a significance flag. ``statistic`` and
    ``degrees_of_freedom`` are kept for the chi-square test only: the KS
    statistic is the KS distance effect, and the Fisher test has no
    separate statistic.

    Omitting ``inferential_validity`` means ``NOT_APPLICABLE`` when no
    p-value was computed and ``VALID`` when one was. The chi-square
    calculator passes ``INVALID`` when Cochran's convention fails.
    """

    method: DriftTestMethod
    computation: Optional[PValueComputation]
    availability: ResultAvailability
    statistic: Optional[float]
    degrees_of_freedom: Optional[int]
    p_value: Optional[float]
    adjusted_p_value: Optional[float]
    adjustment: MultipleTestingAdjustment
    reason: Optional[DriftUnavailabilityReason]
    inferential_validity: Optional[InferentialValidity] = None
    invalidity_reason: Optional[InferentialInvalidityReason] = None

    def __post_init__(self) -> None:
        _require_type(self.method, DriftTestMethod, "method")
        _require_type(self.availability, ResultAvailability, "availability")
        _require_type(self.adjustment, MultipleTestingAdjustment, "adjustment")
        _resolve_drift_validity(self)
        if self.availability is ResultAvailability.UNAVAILABLE:
            if (
                self.computation is not None
                or self.statistic is not None
                or self.degrees_of_freedom is not None
                or self.p_value is not None
                or self.adjusted_p_value is not None
            ):
                raise ValueError("an unavailable test has no values")
            if self.adjustment is not MultipleTestingAdjustment.NOT_APPLIED:
                raise ValueError("an unavailable test is not adjusted")
            if self.inferential_validity is not InferentialValidity.NOT_APPLICABLE:
                raise ValueError("an unavailable test has no inferential p-value")
            if self.invalidity_reason is not None:
                raise ValueError("an unavailable test has no invalidity reason")
            _require_type(self.reason, DriftUnavailabilityReason, "reason")
            return
        if self.reason is not None:
            raise ValueError("an available test has no unavailability reason")
        if self.inferential_validity is InferentialValidity.NOT_APPLICABLE:
            raise ValueError("a computed p-value has an inferential status")
        if self.inferential_validity is InferentialValidity.INVALID:
            _require_type(
                self.invalidity_reason,
                InferentialInvalidityReason,
                "invalidity_reason",
            )
            if self.adjustment is not MultipleTestingAdjustment.NOT_APPLIED:
                raise ValueError("an inferentially invalid p-value is not adjusted")
            if self.adjusted_p_value is not None:
                raise ValueError(
                    "an inferentially invalid p-value has no adjusted p-value"
                )
        elif self.inferential_validity is not InferentialValidity.VALID:
            raise ValueError("inferential validity is not recognized")
        elif self.invalidity_reason is not None:
            raise ValueError("a valid p-value has no invalidity reason")
        _require_type(self.computation, PValueComputation, "computation")
        if self.computation not in _TEST_COMPUTATIONS[self.method]:
            raise ValueError("p-value computation does not fit the test method")
        if self.method is DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY:
            _require_plain_float(self.statistic, "statistic")
            if self.statistic < 0.0:  # type: ignore[operator]
                raise ValueError("a chi-square statistic is not negative")
            if type(self.degrees_of_freedom) is not int or self.degrees_of_freedom < 1:
                raise ValueError("chi-square degrees of freedom must be a positive int")
        elif self.statistic is not None or self.degrees_of_freedom is not None:
            raise ValueError("only the chi-square test keeps a statistic")
        _require_unit(self.p_value, "p_value")
        if self.inferential_validity is InferentialValidity.INVALID:
            return
        if self.adjustment is MultipleTestingAdjustment.NOT_APPLIED:
            if self.adjusted_p_value is not None:
                raise ValueError("an unadjusted test has no adjusted p-value")
            return
        _require_unit(self.adjusted_p_value, "adjusted_p_value")
        if self.adjusted_p_value + _FLOAT_AGREEMENT < self.p_value:  # type: ignore[operator]
            raise ValueError("an adjusted p-value cannot be less than its raw p-value")


@dataclass(frozen=True)
class NumericDistributionDrift:
    """Distribution drift of one Numeric-to-Numeric column.

    The population is the finite non-missing values on each side, the
    same population as each Numeric descriptive profile. Values are
    compared exactly: integers beyond ``2**53``, ``uint64`` values, and a
    mix of integer and float storage keep their order and equality.

    ``ks_distance`` is the primary effect. ``wasserstein_distance`` is in
    the column's units and is not comparable across columns. The test is
    the two-sample KS test on that same distance. Its p-value is exact
    when the larger side has at most 10,000 values, SciPy's own
    automatic rule, and asymptotic above that.

    ``n_distinct_pooled_values`` is the number of distinct values across
    both sides. When it is smaller than the pooled count, the data have
    ties and the KS p-value is conservative. Numeric semantics do not
    imply a continuous variable.
    """

    population: DriftPopulation
    n_distinct_pooled_values: int
    ks_distance: DriftEffect
    ks_location: Optional[KolmogorovSmirnovLocation]
    wasserstein_distance: DriftEffect
    test: DriftTest

    def __post_init__(self) -> None:
        _require_type(self.population, DriftPopulation, "population")
        _require_type(self.ks_distance, DriftEffect, "ks_distance")
        _require_optional(self.ks_location, KolmogorovSmirnovLocation, "ks_location")
        _require_type(self.wasserstein_distance, DriftEffect, "wasserstein_distance")
        _require_type(self.test, DriftTest, "test")
        if self.population.rule is not DriftPopulationRule.FINITE_NON_MISSING:
            raise ValueError("numeric drift compares finite non-missing values")
        _require_method(self.ks_distance, DriftEffectMethod.KOLMOGOROV_SMIRNOV_DISTANCE)
        _require_method(
            self.wasserstein_distance, DriftEffectMethod.WASSERSTEIN_1_DISTANCE
        )
        if self.test.method is not DriftTestMethod.KOLMOGOROV_SMIRNOV_TWO_SAMPLE:
            raise ValueError("numeric drift uses the two-sample KS test")
        _require_count(self.n_distinct_pooled_values, "n_distinct_pooled_values")
        n_pooled = self.population.n_reference + self.population.n_comparison
        if self.n_distinct_pooled_values > n_pooled:
            raise ValueError("distinct pooled values cannot exceed pooled values")
        if (self.n_distinct_pooled_values == 0) is not (n_pooled == 0):
            raise ValueError("a non-empty pooled population has a distinct value")
        empty = self.population.empty_reason
        if empty is not None:
            for component in (self.ks_distance, self.wasserstein_distance, self.test):
                if component.reason is not empty:
                    raise ValueError("an empty side leaves every component unavailable")
            if self.ks_location is not None:
                raise ValueError("an empty side has no KS location")
            return
        if self.ks_distance.availability is not ResultAvailability.AVAILABLE:
            raise ValueError("two non-empty samples define a KS distance")
        _require_not_population_reason(self.wasserstein_distance.reason)
        _require_not_population_reason(self.test.reason)
        if self.ks_distance.value == 0.0:
            if self.ks_location is not None:
                raise ValueError("equal empirical CDFs have no KS location")
            return
        if self.ks_location is None:
            raise ValueError("a positive KS distance has a location")
        gap = abs(self.ks_location.cumulative_difference)
        if abs(gap - self.ks_distance.value) > _FLOAT_AGREEMENT:  # type: ignore[operator]
            raise ValueError("the KS location must attain the KS distance")

    @property
    def ties_present(self) -> bool:
        """Whether two pooled observations share a value."""
        n_pooled = self.population.n_reference + self.population.n_comparison
        return self.n_distinct_pooled_values < n_pooled

    @property
    def primary_effect(self) -> DriftEffect:
        """The KS distance."""
        return self.ks_distance


@dataclass(frozen=True)
class CategoricalDistributionDrift:
    """Distribution drift of one Categorical-to-Categorical column.

    The population is the non-missing observations on each side.
    ``n_levels`` is the number of levels observed on either side, under
    the category equality of the descriptive partition. Declared levels
    that neither side observed are not levels. The per-level counts are
    the column's descriptive partition and are not copied here.

    ``n_reference_only_observations`` is how many reference observations
    fall in levels the comparison never observed. Its comparison
    counterpart is defined the same way. Their shares are the part of the
    total variation distance that comes from disappeared and new levels.
    No smoothing is applied.

    The test is Pearson's chi-square of homogeneity. ``expected_counts``
    are the Cochran checkpoints of the 2 by k table, with the same rules
    as Categorical × Categorical relationships. They do not suppress the
    computed asymptotic p-value. They do mark that p-value inferentially
    invalid when Cochran's convention fails, and an invalid p-value does
    not enter the drift correction family.
    """

    population: DriftPopulation
    n_levels: int
    n_reference_only_observations: int
    n_comparison_only_observations: int
    total_variation_distance: DriftEffect
    expected_counts: Optional[ExpectedCountDiagnostics]
    test: DriftTest

    def __post_init__(self) -> None:
        _require_type(self.population, DriftPopulation, "population")
        _require_type(
            self.total_variation_distance, DriftEffect, "total_variation_distance"
        )
        _require_optional(
            self.expected_counts, ExpectedCountDiagnostics, "expected_counts"
        )
        _require_type(self.test, DriftTest, "test")
        if self.population.rule is not DriftPopulationRule.NON_MISSING:
            raise ValueError("categorical drift compares non-missing values")
        _require_method(
            self.total_variation_distance,
            DriftEffectMethod.TOTAL_VARIATION_DISTANCE,
        )
        if self.test.method is not DriftTestMethod.PEARSON_CHI_SQUARE_HOMOGENEITY:
            raise ValueError("categorical drift uses the chi-square homogeneity test")
        _require_count(self.n_levels, "n_levels")
        _require_count(
            self.n_reference_only_observations, "n_reference_only_observations"
        )
        _require_count(
            self.n_comparison_only_observations, "n_comparison_only_observations"
        )
        if self.n_reference_only_observations > self.population.n_reference:
            raise ValueError("reference-only observations exceed the reference")
        if self.n_comparison_only_observations > self.population.n_comparison:
            raise ValueError("comparison-only observations exceed the comparison")
        empty = self.population.empty_reason
        if empty is not None:
            if self.total_variation_distance.reason is not empty:
                raise ValueError("an empty side leaves the distance unavailable")
            if self.test.reason is not empty:
                raise ValueError("an empty side leaves the test unavailable")
            if self.expected_counts is not None:
                raise ValueError("an empty side has no expected counts")
            return
        if self.n_levels < 1:
            raise ValueError("a non-empty population observes a level")
        if self.total_variation_distance.availability is not (
            ResultAvailability.AVAILABLE
        ):
            raise ValueError("two non-empty samples define a total variation distance")
        if self.expected_counts is None:
            raise ValueError("two non-empty samples have expected counts")
        if self.test.availability is ResultAvailability.AVAILABLE:
            if self.test.degrees_of_freedom != self.n_levels - 1:
                raise ValueError("homogeneity degrees of freedom are n_levels - 1")
            _require_homogeneity_validity(self)
        elif self.n_levels == 1:
            if self.test.reason is not DriftUnavailabilityReason.SINGLE_POOLED_LEVEL:
                raise ValueError("one pooled level has no homogeneity test")
        else:
            _require_not_population_reason(self.test.reason)

    @property
    def primary_effect(self) -> DriftEffect:
        """The total variation distance."""
        return self.total_variation_distance


@dataclass(frozen=True)
class BooleanDistributionDrift:
    """Distribution drift of one Boolean-to-Boolean column.

    The population is the non-missing values on each side. The effect is
    the signed True-share difference, comparison minus reference. It is
    the same number as the descriptive True-proportion change. The test
    is the two-sided Fisher exact test of side by value. This is a
    two-sample comparison of independent datasets, not the paired
    Boolean × Boolean relationship.
    """

    population: DriftPopulation
    true_proportion_difference: DriftEffect
    test: DriftTest

    def __post_init__(self) -> None:
        _require_type(self.population, DriftPopulation, "population")
        _require_type(
            self.true_proportion_difference,
            DriftEffect,
            "true_proportion_difference",
        )
        _require_type(self.test, DriftTest, "test")
        if self.population.rule is not DriftPopulationRule.NON_MISSING:
            raise ValueError("boolean drift compares non-missing values")
        _require_method(
            self.true_proportion_difference,
            DriftEffectMethod.TRUE_PROPORTION_DIFFERENCE,
        )
        if self.test.method is not DriftTestMethod.FISHER_EXACT_TWO_SAMPLE:
            raise ValueError("boolean drift uses the Fisher exact test")
        empty = self.population.empty_reason
        if empty is not None:
            if self.true_proportion_difference.reason is not empty:
                raise ValueError("an empty side leaves the difference unavailable")
            if self.test.reason is not empty:
                raise ValueError("an empty side leaves the test unavailable")
            return
        if self.true_proportion_difference.availability is not (
            ResultAvailability.AVAILABLE
        ):
            raise ValueError("two non-empty samples define a proportion difference")
        _require_not_population_reason(self.test.reason)

    @property
    def primary_effect(self) -> DriftEffect:
        """The True-share difference."""
        return self.true_proportion_difference


DistributionDrift = Union[
    NumericDistributionDrift,
    CategoricalDistributionDrift,
    BooleanDistributionDrift,
]


def _resolve_drift_validity(test: DriftTest) -> None:
    """Fill an omitted status. An explicit status is left unchanged."""
    if test.inferential_validity is not None:
        _require_type(
            test.inferential_validity, InferentialValidity, "inferential_validity"
        )
        return
    if test.invalidity_reason is not None:
        raise ValueError("an unspecified inferential status has no invalidity reason")
    validity = (
        InferentialValidity.NOT_APPLICABLE
        if test.availability is ResultAvailability.UNAVAILABLE
        else InferentialValidity.VALID
    )
    object.__setattr__(test, "inferential_validity", validity)


def _require_homogeneity_validity(record: CategoricalDistributionDrift) -> None:
    """The stored chi-square status must be the Cochran reading of the diagnostics."""
    diagnostics = record.expected_counts
    if diagnostics is None:
        raise ValueError("a computed homogeneity test has expected counts")
    validity, reason = chi_square_inferential_status(
        diagnostics_available=diagnostics.availability is ResultAvailability.AVAILABLE,
        minimum_expected_count=diagnostics.minimum_expected_count,
        n_cells_expected_below_5=diagnostics.n_cells_expected_below_5,
        n_cells=2 * record.n_levels,
    )
    test = record.test
    if (
        test.inferential_validity is not validity
        or test.invalidity_reason is not reason
    ):
        raise ValueError(
            "chi-square inferential validity must follow Cochran's convention"
        )


def _require_method(effect: DriftEffect, expected: DriftEffectMethod) -> None:
    if effect.method is not expected:
        raise ValueError(f"effect must be {expected.value}")


def _require_not_population_reason(reason: object) -> None:
    if reason in _POPULATION_REASONS:
        raise ValueError("two non-empty samples are not an empty population")


def _require_plain_float(value: object, field: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


def _require_unit(value: object, field: str) -> None:
    _require_plain_float(value, field)
    if value < 0.0 or value > 1.0:  # type: ignore[operator]
        raise ValueError(f"{field} must lie on [0, 1]")
