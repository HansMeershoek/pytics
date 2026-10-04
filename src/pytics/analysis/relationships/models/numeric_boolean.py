"""Numeric × Boolean relationship records.

These records retain the paired Numeric description of each Boolean
group, the True − False mean difference, Hedges' g, a Welch interval for
that difference, and Welch's two-sample t-test. They do not calculate
those facts and they do not import a statistical library. Group
descriptions reuse the Numeric descriptive model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.relationships.models.common import BooleanLevel
from pytics.analysis.relationships.models.common import FrequentistEvidence
from pytics.analysis.relationships.models.common import RelationshipFamily
from pytics.analysis.relationships.models.common import ResultAvailability
from pytics.analysis.relationships.models.common import UnavailabilityReason
from pytics.analysis.relationships.models.common import _require_canonical_positions
from pytics.analysis.relationships.models.common import _require_enum
from pytics.analysis.relationships.models.common import _require_population_counts
from pytics.analysis.relationships.models.common import _require_position
from pytics.analysis.relationships.models.common import _require_reason
from pytics.analysis.relationships.models.common import _require_type
from pytics.analysis.relationships.models.common import (
    _require_unavailable_component,
)

# Level of an available Welch interval. The level is stored on that
# interval. It is not a dataset-wide confidence level, and it is not
# configurable in this slice.
_WELCH_INTERVAL_LEVEL = 0.95

# A group without paired rows is absent. Every component that compares the
# two groups shares that state.
_GROUP_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
    }
)
_MEAN_DIFFERENCE_REASONS = _GROUP_REASONS | {UnavailabilityReason.NON_FINITE_RESULT}
# Zero pooled variation leaves a standardized difference undefined when the
# means are equal and unbounded when they are not. Zero within-group
# variation leaves the Welch ratio without a finite value.
_STANDARDIZED_REASONS = _MEAN_DIFFERENCE_REASONS | {
    UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM,
    UnavailabilityReason.CONSTANT_PAIRED_VALUES,
    UnavailabilityReason.MATHEMATICALLY_UNBOUNDED,
    UnavailabilityReason.PRECISION_COLLAPSED,
}
_WELCH_REASONS = _MEAN_DIFFERENCE_REASONS | {
    UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM,
    UnavailabilityReason.CONSTANT_PAIRED_VALUES,
    UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
    UnavailabilityReason.PRECISION_COLLAPSED,
}


class NumericBooleanPopulation(Enum):
    """Rows that enter a Numeric × Boolean relationship.

    The numeric value is finite and the Boolean value is non-missing.
    """

    FINITE_NUMERIC_NON_MISSING_BOOLEAN = "finite_numeric_non_missing_boolean"


class BooleanGroupContrast(Enum):
    """Direction of every signed Numeric × Boolean component.

    The True group minus the False group. This orientation does not follow
    the physical column order, and it is not a causal order.
    """

    TRUE_MINUS_FALSE = "true_minus_false"


class StandardizedDifferenceMethod(Enum):
    """Standardized mean difference for two Boolean groups.

    This is a descriptive standardized separation. It is not a strength
    label.
    """

    HEDGES_G = "hedges_g"


class MeanDifferenceIntervalMethod(Enum):
    """How a mean-difference interval was obtained."""

    WELCH_SATTERTHWAITE = "welch_satterthwaite"


class MeanDifferenceTestMethod(Enum):
    """Frequentist test of a difference between two group means.

    Welch's two-sample t-test does not assume equal variances. It is not
    selected by an assumption test.
    """

    WELCH_T = "welch_t"


@dataclass(frozen=True)
class BooleanGroupSummary:
    """Paired Numeric description of one Boolean group.

    ``level`` is the Boolean value that defines the group. ``descriptive``
    uses the finite-population definitions of a Numeric column, on the
    paired rows of that level only. A level with no paired finite Numeric
    value is absent from the analytical population: it is unavailable
    and has no description. It is not a group of size zero.
    """

    level: BooleanLevel
    availability: ResultAvailability
    descriptive: Optional[NumericDescriptiveAnalysis]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.level, BooleanLevel, "level")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_type(self.descriptive, NumericDescriptiveAnalysis, "descriptive")
            if self.descriptive.finite_count < 1:  # type: ignore[union-attr]
                raise ValueError("an observed group has at least one paired value")
            if self.reason is not None:
                raise ValueError("an observed group has no unavailability reason")
            return
        if self.descriptive is not None:
            raise ValueError("an absent group has no description")
        _require_reason(self.reason, _GROUP_REASONS, "reason")

    @property
    def n(self) -> int:
        """Paired finite Numeric observations at this level. Zero when absent."""
        if self.descriptive is None:
            return 0
        return self.descriptive.finite_count


@dataclass(frozen=True)
class MeanDifferenceEstimate:
    """True-group mean minus False-group mean, in the Numeric variable's units.

    ``value`` is a finite Python float when both groups are observed. It is
    signed, and ``0.0`` is an observed zero difference. It is not the
    difference of the two stored group means: those are float64 roundings
    of each mean and can coincide for large magnitudes while the groups
    differ. An absent group leaves the difference unavailable. It is not
    stored as zero.
    """

    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_finite_float(self.value, "mean difference")
            if self.reason is not None:
                raise ValueError(
                    "an available mean difference has no unavailability reason"
                )
            return
        if self.value is not None:
            raise ValueError("an unavailable mean difference has no value")
        _require_reason(self.reason, _MEAN_DIFFERENCE_REASONS, "reason")


@dataclass(frozen=True)
class StandardizedMeanDifference:
    """Standardized True − False mean difference.

    Hedges' g is the mean difference divided by the pooled within-group
    sample standard deviation, multiplied by the exact small-sample
    correction for ``n_paired - 2`` degrees of freedom. That correction
    makes the estimate unbiased when both groups are normal with a common
    variance, a condition that is not tested. Some references keep the
    name g for the uncorrected ratio. Its sign is the sign of the mean
    difference. It uses a pooled scale and is not a Welch quantity. Zero pooled variation leaves it unavailable: the reason is
    ``CONSTANT_PAIRED_VALUES`` when every paired value is equal, and
    ``MATHEMATICALLY_UNBOUNDED`` when the group means differ.
    """

    method: StandardizedDifferenceMethod
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.method, StandardizedDifferenceMethod, "method")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_finite_float(self.value, "standardized difference")
            if self.reason is not None:
                raise ValueError(
                    "an available standardized difference has no unavailability reason"
                )
            return
        if self.value is not None:
            raise ValueError("an unavailable standardized difference has no value")
        _require_reason(self.reason, _STANDARDIZED_REASONS, "reason")


@dataclass(frozen=True)
class MeanDifferenceInterval:
    """Two-sided interval for the True − False mean difference.

    An available interval records its own level and method. The bounds
    are in the Numeric variable's units. Zero within-group variation does
    not produce a zero-width interval. That state is unavailable.
    """

    availability: ResultAvailability
    level: Optional[float]
    method: Optional[MeanDifferenceIntervalMethod]
    lower: Optional[float]
    upper: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            if self.level != _WELCH_INTERVAL_LEVEL:
                raise ValueError("confidence level must be 0.95")
            if self.method is not MeanDifferenceIntervalMethod.WELCH_SATTERTHWAITE:
                raise ValueError("interval method must be Welch–Satterthwaite")
            _require_finite_float(self.lower, "lower")
            _require_finite_float(self.upper, "upper")
            if self.lower > self.upper:  # type: ignore[operator]
                raise ValueError("interval bounds are out of order")
            if self.reason is not None:
                raise ValueError("an available interval has no unavailability reason")
            return
        if (
            self.level is not None
            or self.method is not None
            or self.lower is not None
            or self.upper is not None
        ):
            raise ValueError("an unavailable interval has no bounds")
        _require_reason(self.reason, _WELCH_REASONS, "reason")


@dataclass(frozen=True)
class MeanDifferenceTest:
    """Welch's two-sample t-test for the True − False mean difference.

    ``statistic`` is the t ratio, with the sign of the mean difference.
    ``degrees_of_freedom`` is the Welch–Satterthwaite value. ``frequentist``
    holds the two-sided p-value. The calculator stores that raw p-value.
    Dataset-level correction may later set the adjusted companion of the
    same test. The null hypothesis is equal population means of the
    finite Numeric values in the two Boolean groups. The p-value is not
    a significance flag and not an effect size. Zero within-group
    variation does not store an infinite t or a p-value of zero.
    """

    method: MeanDifferenceTestMethod
    statistic_availability: ResultAvailability
    statistic: Optional[float]
    degrees_of_freedom: Optional[float]
    statistic_reason: Optional[UnavailabilityReason]
    frequentist: FrequentistEvidence

    def __post_init__(self) -> None:
        _require_enum(self.method, MeanDifferenceTestMethod, "method")
        _require_enum(
            self.statistic_availability,
            ResultAvailability,
            "statistic_availability",
        )
        _require_type(self.frequentist, FrequentistEvidence, "frequentist")
        if (
            self.frequentist.reason is not None
            and self.frequentist.reason not in _WELCH_REASONS
        ):
            raise ValueError("Welch p-value reason is not a Welch reason")
        if self.statistic_availability is ResultAvailability.AVAILABLE:
            _require_finite_float(self.statistic, "t statistic")
            _require_finite_float(self.degrees_of_freedom, "degrees of freedom")
            if self.degrees_of_freedom < 1.0:  # type: ignore[operator]
                raise ValueError("Welch degrees of freedom are at least 1")
            if self.statistic_reason is not None:
                raise ValueError(
                    "an available t statistic has no unavailability reason"
                )
            if (
                self.frequentist.availability is ResultAvailability.UNAVAILABLE
                and self.frequentist.reason
                is not UnavailabilityReason.NON_FINITE_RESULT
            ):
                raise ValueError(
                    "a finite t statistic leaves the p-value unavailable only when "
                    "it is non-finite"
                )
            return
        if self.statistic is not None or self.degrees_of_freedom is not None:
            raise ValueError("an unavailable t statistic has no value")
        _require_reason(self.statistic_reason, _WELCH_REASONS, "statistic_reason")
        _require_unavailable_component(
            self.frequentist.availability,
            self.frequentist.reason,
            self.statistic_reason,  # type: ignore[arg-type]
            "Welch p-value",
        )


@dataclass(frozen=True)
class NumericBooleanRelationship:
    """One selected Numeric × selected Boolean pair.

    ``left_position`` is less than ``right_position``. Both are physical
    positions. ``numeric_position`` and ``boolean_position`` are those same
    positions, assigned by semantic role. Every signed component is the
    True group minus the False group, whichever side is Boolean. That
    orientation is not causal.

    ``n_paired`` counts rows where the numeric value is finite and the
    Boolean value is non-missing. ``n_excluded`` is every other row.
    ``false_group`` and ``true_group`` describe those paired rows at each
    level. An absent level is an explicit unavailable group. The paired
    arrays are not stored.

    ``mean_difference`` is in the Numeric variable's units.
    ``standardized_mean_difference`` is Hedges' g.
    ``mean_difference_interval`` is the 95% Welch–Satterthwaite interval.
    ``mean_difference_test`` is Welch's t-test with its raw p-value. Those
    components do not share one availability flag. This record has no
    strength label, no significance flag, and no target role.
    """

    left_position: int
    left_label: object
    right_position: int
    right_label: object
    numeric_position: int
    boolean_position: int
    n_total_rows: int
    n_paired: int
    false_group: BooleanGroupSummary
    true_group: BooleanGroupSummary
    mean_difference: MeanDifferenceEstimate
    standardized_mean_difference: StandardizedMeanDifference
    mean_difference_interval: MeanDifferenceInterval
    mean_difference_test: MeanDifferenceTest

    def __post_init__(self) -> None:
        _require_canonical_positions(self.left_position, self.right_position)
        _require_position(self.numeric_position, "numeric_position")
        _require_position(self.boolean_position, "boolean_position")
        roles = {self.numeric_position, self.boolean_position}
        if roles != {self.left_position, self.right_position}:
            raise ValueError("roles must be the two physical pair positions")
        _require_population_counts(self.n_total_rows, self.n_paired)
        _require_type(self.false_group, BooleanGroupSummary, "false_group")
        _require_type(self.true_group, BooleanGroupSummary, "true_group")
        if self.false_group.level is not BooleanLevel.FALSE:
            raise ValueError("false_group describes the False level")
        if self.true_group.level is not BooleanLevel.TRUE:
            raise ValueError("true_group describes the True level")
        if self.false_group.n + self.true_group.n != self.n_paired:
            raise ValueError("group sizes must sum to n_paired")
        _require_type(self.mean_difference, MeanDifferenceEstimate, "mean_difference")
        _require_type(
            self.standardized_mean_difference,
            StandardizedMeanDifference,
            "standardized_mean_difference",
        )
        _require_type(
            self.mean_difference_interval,
            MeanDifferenceInterval,
            "mean_difference_interval",
        )
        _require_type(
            self.mean_difference_test,
            MeanDifferenceTest,
            "mean_difference_test",
        )
        _require_numeric_boolean_components(self)

    @property
    def family(self) -> RelationshipFamily:
        """The implemented family this record belongs to."""
        return RelationshipFamily.NUMERIC_BOOLEAN

    @property
    def population(self) -> NumericBooleanPopulation:
        """Rows with a finite numeric value and a non-missing Boolean value."""
        return NumericBooleanPopulation.FINITE_NUMERIC_NON_MISSING_BOOLEAN

    @property
    def contrast(self) -> BooleanGroupContrast:
        """True group minus False group. Not the physical column order."""
        return BooleanGroupContrast.TRUE_MINUS_FALSE

    @property
    def n_excluded(self) -> int:
        """Rows outside the finite-numeric, non-missing-Boolean population.

        A row is excluded when the numeric value is missing or infinite, or
        when the Boolean value is missing.
        """
        return self.n_total_rows - self.n_paired


def _require_numeric_boolean_components(
    relationship: NumericBooleanRelationship,
) -> None:
    """Keep components consistent with the group sizes and group extrema.

    Group sizes decide which components can exist. Exact group extrema
    decide whether within-group variation is zero. The constructor checks
    those states. It does not recompute a statistic.
    """
    false_group = relationship.false_group
    true_group = relationship.true_group
    if relationship.n_paired == 0:
        absent: Optional[UnavailabilityReason] = (
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        )
    elif false_group.n == 0 or true_group.n == 0:
        absent = UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    else:
        absent = None
    for group in (false_group, true_group):
        if group.availability is ResultAvailability.UNAVAILABLE:
            _require_unavailable_component(
                group.availability,
                group.reason,
                absent,  # type: ignore[arg-type]
                "an absent group",
            )
    if absent is not None:
        _require_all_unavailable(relationship, absent)
        return
    false_summary = false_group.descriptive
    true_summary = true_group.descriptive
    false_constant = false_summary.minimum == false_summary.maximum  # type: ignore[union-attr]
    true_constant = true_summary.minimum == true_summary.maximum  # type: ignore[union-attr]
    all_equal = (
        false_constant
        and true_constant
        and false_summary.minimum == true_summary.minimum  # type: ignore[union-attr]
    )
    difference = relationship.mean_difference
    if all_equal and (
        difference.availability is not ResultAvailability.AVAILABLE
        or difference.value != 0.0
    ):
        raise ValueError("equal paired values have mean difference 0")
    _require_standardized_state(
        relationship.standardized_mean_difference,
        difference,
        degrees_of_freedom=relationship.n_paired - 2,
        zero_scale=false_constant and true_constant,
        all_equal=all_equal,
    )
    test = relationship.mean_difference_test
    _require_welch_state(
        test,
        difference,
        min_n=min(false_group.n, true_group.n),
        n_paired=relationship.n_paired,
        zero_scale=false_constant and true_constant,
        all_equal=all_equal,
    )
    _require_interval_state(relationship.mean_difference_interval, test, difference)


def _require_all_unavailable(
    relationship: NumericBooleanRelationship,
    reason: UnavailabilityReason,
) -> None:
    difference = relationship.mean_difference
    standardized = relationship.standardized_mean_difference
    interval = relationship.mean_difference_interval
    test = relationship.mean_difference_test
    _require_unavailable_component(
        difference.availability, difference.reason, reason, "mean difference"
    )
    _require_unavailable_component(
        standardized.availability,
        standardized.reason,
        reason,
        "standardized difference",
    )
    _require_unavailable_component(
        interval.availability, interval.reason, reason, "mean-difference interval"
    )
    _require_unavailable_component(
        test.statistic_availability, test.statistic_reason, reason, "Welch statistic"
    )


def _require_standardized_state(
    standardized: StandardizedMeanDifference,
    difference: MeanDifferenceEstimate,
    *,
    degrees_of_freedom: int,
    zero_scale: bool,
    all_equal: bool,
) -> None:
    """Pooled degrees of freedom, then zero pooled scale, then the value.

    With no pooled degree of freedom there is no pooled variance. With
    one, the uncorrected ratio has no finite mean and the correction has
    only a limit of zero. Hedges' g therefore needs at least two. Every
    group is constant exactly when the pooled scale is zero.
    """
    if degrees_of_freedom < 2:
        _require_unavailable_component(
            standardized.availability,
            standardized.reason,
            UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM,
            "standardized difference",
        )
        return
    if zero_scale:
        expected = (
            UnavailabilityReason.CONSTANT_PAIRED_VALUES
            if all_equal
            else UnavailabilityReason.MATHEMATICALLY_UNBOUNDED
        )
        _require_unavailable_component(
            standardized.availability,
            standardized.reason,
            expected,
            "standardized difference",
        )
        return
    _require_numerical_state(
        standardized.availability,
        standardized.reason,
        standardized.value,
        difference,
        "standardized difference",
    )


def _require_welch_state(
    test: MeanDifferenceTest,
    difference: MeanDifferenceEstimate,
    *,
    min_n: int,
    n_paired: int,
    zero_scale: bool,
    all_equal: bool,
) -> None:
    """Each group needs a variance, then a positive standard error."""
    if min_n < 2:
        _require_unavailable_component(
            test.statistic_availability,
            test.statistic_reason,
            UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM,
            "Welch statistic",
        )
        return
    if zero_scale:
        expected = (
            UnavailabilityReason.CONSTANT_PAIRED_VALUES
            if all_equal
            else UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION
        )
        _require_unavailable_component(
            test.statistic_availability,
            test.statistic_reason,
            expected,
            "Welch statistic",
        )
        return
    _require_numerical_state(
        test.statistic_availability,
        test.statistic_reason,
        test.statistic,
        difference,
        "Welch statistic",
    )
    if test.statistic_availability is ResultAvailability.AVAILABLE:
        degrees_of_freedom = test.degrees_of_freedom
        if not min_n - 1 <= degrees_of_freedom <= n_paired - 2:  # type: ignore[operator]
            raise ValueError(
                "Welch degrees of freedom lie between the smaller group's "
                "degrees of freedom and n_paired - 2"
            )


def _require_numerical_state(
    availability: ResultAvailability,
    reason: Optional[UnavailabilityReason],
    value: Optional[float],
    difference: MeanDifferenceEstimate,
    field: str,
) -> None:
    """A defined scale leaves only numerical failures or a signed value.

    The value is a positive multiple of the mean difference. A float
    quotient can underflow to zero, so only a nonzero value is required
    to carry the difference's sign.
    """
    if difference.availability is ResultAvailability.UNAVAILABLE:
        _require_unavailable_component(
            availability,
            reason,
            UnavailabilityReason.NON_FINITE_RESULT,
            field,
        )
        return
    if availability is ResultAvailability.UNAVAILABLE:
        if reason not in {
            UnavailabilityReason.NON_FINITE_RESULT,
            UnavailabilityReason.PRECISION_COLLAPSED,
        }:
            raise ValueError(f"a defined {field} is unavailable only numerically")
        return
    if difference.value == 0.0 and value != 0.0:
        raise ValueError(f"a zero mean difference has {field} 0")
    if value != 0.0 and (value > 0.0) != (difference.value > 0.0):  # type: ignore[operator]
        raise ValueError(f"{field} must carry the sign of the mean difference")


def _require_interval_state(
    interval: MeanDifferenceInterval,
    test: MeanDifferenceTest,
    difference: MeanDifferenceEstimate,
) -> None:
    """The interval and the test share every non-numerical state."""
    numerical = {
        UnavailabilityReason.NON_FINITE_RESULT,
        UnavailabilityReason.PRECISION_COLLAPSED,
    }
    if (
        test.statistic_availability is ResultAvailability.UNAVAILABLE
        and test.statistic_reason not in numerical
    ):
        _require_unavailable_component(
            interval.availability,
            interval.reason,
            test.statistic_reason,  # type: ignore[arg-type]
            "mean-difference interval",
        )
        return
    if interval.availability is ResultAvailability.UNAVAILABLE:
        if interval.reason not in numerical:
            raise ValueError(
                "a mean-difference interval with a defined scale is unavailable "
                "only numerically"
            )
        return
    if difference.availability is not ResultAvailability.AVAILABLE:
        raise ValueError("an interval requires a mean difference")
    if not interval.lower <= difference.value <= interval.upper:  # type: ignore[operator]
        raise ValueError("the interval must contain the mean difference")


def _require_finite_float(value: object, field: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")
