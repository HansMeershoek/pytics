"""Numeric × Numeric relationship records.

These records retain Spearman and Pearson. They do not calculate either
method and they do not import a statistical library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

from pytics.analysis.relationships.models.common import FrequentistEvidence
from pytics.analysis.relationships.models.common import RelationshipFamily
from pytics.analysis.relationships.models.common import ResultAvailability
from pytics.analysis.relationships.models.common import UnavailabilityReason
from pytics.analysis.relationships.models.common import _require_canonical_positions
from pytics.analysis.relationships.models.common import _require_enum
from pytics.analysis.relationships.models.common import _require_population_counts
from pytics.analysis.relationships.models.common import _require_reason
from pytics.analysis.relationships.models.common import _require_type

# Fisher-z level for an available Pearson interval. The level is stored on
# that interval. It is not a dataset-wide confidence level, and it is not
# configurable in this slice.
_CONFIDENCE_LEVEL = 0.95


class AssociationMethod(Enum):
    """Numeric × Numeric association method.

    This is not a catalog of every relationship method. Display names
    are not this identity.
    """

    SPEARMAN = "spearman"
    PEARSON = "pearson"


# Correlation components may share numerical reasons. Interval-only
# reasons stay off the estimate and the test. Group-analysis reasons
# stay off correlation components.
_CORRELATION_COMPONENT_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        UnavailabilityReason.PRECISION_COLLAPSED,
        UnavailabilityReason.NON_FINITE_RESULT,
    }
)
_CORRELATION_INTERVAL_REASONS = _CORRELATION_COMPONENT_REASONS | {
    UnavailabilityReason.BOUNDARY_CORRELATION,
    UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD,
}


class EffectDirection(Enum):
    """Sign of a correlation estimate.

    A nonzero floating-point value keeps its sign. Strength is not a
    direction.
    """

    NEGATIVE = "negative"
    ZERO = "zero"
    POSITIVE = "positive"


class CorrelationIntervalMethod(Enum):
    """How a correlation interval was obtained."""

    FISHER_Z = "fisher_z"


class PairPopulation(Enum):
    """Which rows enter a Numeric × Numeric correlation."""

    PAIRWISE_FINITE = "pairwise_finite"


class NumericComputation(Enum):
    """Float64 image passed to Spearman and Pearson.

    This is not an exact-versus-sampled execution mode, not the pairwise
    filter, and not the Numeric × Categorical centered-integer image.
    ``FLOAT64`` does not claim exact integer correlation above ``2**53``.
    """

    FLOAT64 = "float64"


@dataclass(frozen=True)
class CorrelationEstimate:
    """Effect estimate for one association method.

    ``value`` is a Python float in ``[-1, 1]`` when available. It is never
    NaN. ``direction`` is the sign of that value. ``reason`` is set only
    when the estimate is unavailable.
    """

    availability: ResultAvailability
    value: Optional[float]
    direction: Optional[EffectDirection]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_correlation(self.value, "estimate")
            _require_enum(self.direction, EffectDirection, "direction")
            if self.reason is not None:
                raise ValueError("an available estimate has no unavailability reason")
            if _direction(self.value) is not self.direction:  # type: ignore[arg-type]
                raise ValueError("direction must match the estimate sign")
            return
        if self.value is not None or self.direction is not None:
            raise ValueError("an unavailable estimate has no value or direction")
        _require_reason(self.reason, _CORRELATION_COMPONENT_REASONS, "reason")


@dataclass(frozen=True)
class CorrelationInterval:
    """Uncertainty interval for one correlation estimate.

    An available interval records its own level and method. That level
    is the confidence metadata for this interval. Spearman has no
    interval in this slice, so its interval stays unavailable even when
    the estimate exists. A Numeric × Categorical record has no interval.
    """

    availability: ResultAvailability
    level: Optional[float]
    method: Optional[CorrelationIntervalMethod]
    lower: Optional[float]
    upper: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            if self.level != _CONFIDENCE_LEVEL:
                raise ValueError("confidence level must be 0.95")
            if self.method is not CorrelationIntervalMethod.FISHER_Z:
                raise ValueError("confidence interval method must be Fisher z")
            _require_correlation(self.lower, "lower")
            _require_correlation(self.upper, "upper")
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
        _require_reason(self.reason, _CORRELATION_INTERVAL_REASONS, "reason")


@dataclass(frozen=True)
class AssociationResult:
    """One association method on one numeric pair.

    ``n_observations`` is the pairwise finite count the method considered.
    The estimate, the test, and the interval do not share one availability
    flag. Spearman does not carry a confidence interval in this slice.
    """

    method: AssociationMethod
    n_observations: int
    estimate: CorrelationEstimate
    frequentist: FrequentistEvidence
    confidence_interval: CorrelationInterval

    def __post_init__(self) -> None:
        _require_enum(self.method, AssociationMethod, "method")
        if type(self.n_observations) is not int or self.n_observations < 0:
            raise ValueError("n_observations must be a non-negative int")
        _require_type(self.estimate, CorrelationEstimate, "estimate")
        _require_type(self.frequentist, FrequentistEvidence, "frequentist")
        _require_type(
            self.confidence_interval,
            CorrelationInterval,
            "confidence_interval",
        )
        if (
            self.frequentist.reason is not None
            and self.frequentist.reason not in _CORRELATION_COMPONENT_REASONS
        ):
            raise ValueError("frequentist reason is not a correlation-test reason")
        _require_component_consistency(self)


@dataclass(frozen=True)
class NumericNumericRelationship:
    """One selected Numeric × selected Numeric pair.

    ``left_position`` is less than ``right_position``. Both are physical
    positions. ``n_paired`` counts rows where both source values are
    finite. ``n_excluded`` is every other row, including rows where either
    value is missing or infinite. The paired arrays are not stored.

    ``methods`` is Spearman, then Pearson. Spearman is the primary
    descriptive association of this family because this record exposes
    it as the Spearman component. Pearson is complementary. There is no
    separate primary-method field. Both records exist when a method is
    unavailable.

    ``population`` is the pairwise finite eligibility rule. ``n_total_rows``,
    ``n_paired``, and ``n_excluded`` are the pair counts for that rule.
    ``computation`` is the float64 correlation image shared by both
    methods on this pair.
    """

    left_position: int
    left_label: object
    right_position: int
    right_label: object
    n_total_rows: int
    n_paired: int
    methods: Tuple[AssociationResult, ...]

    def __post_init__(self) -> None:
        _require_canonical_positions(self.left_position, self.right_position)
        _require_population_counts(self.n_total_rows, self.n_paired)
        if not isinstance(self.methods, tuple):
            raise TypeError("methods must be a tuple")
        if len(self.methods) != 2:
            raise ValueError("a numeric pair records Spearman and Pearson")
        spearman, pearson = self.methods
        _require_type(spearman, AssociationResult, "methods")
        _require_type(pearson, AssociationResult, "methods")
        if spearman.method is not AssociationMethod.SPEARMAN:
            raise ValueError("the first method must be Spearman")
        if pearson.method is not AssociationMethod.PEARSON:
            raise ValueError("the second method must be Pearson")
        if (
            spearman.n_observations != self.n_paired
            or pearson.n_observations != self.n_paired
        ):
            raise ValueError("method observations must equal n_paired")

    @property
    def family(self) -> RelationshipFamily:
        """The implemented family this record belongs to."""
        return RelationshipFamily.NUMERIC_NUMERIC

    @property
    def population(self) -> PairPopulation:
        """Rows in which both source values are finite."""
        return PairPopulation.PAIRWISE_FINITE

    @property
    def computation(self) -> NumericComputation:
        """Float64 image used by Spearman and Pearson on this pair.

        Not an exact integer claim. Not a dataset execution mode.
        """
        return NumericComputation.FLOAT64

    @property
    def n_excluded(self) -> int:
        """Rows that are not in the pairwise finite population.

        A row is excluded when either value is missing or not finite.
        """
        return self.n_total_rows - self.n_paired

    @property
    def spearman(self) -> AssociationResult:
        """Spearman result. The primary descriptive association of this pair."""
        return self.methods[0]

    @property
    def pearson(self) -> AssociationResult:
        """Pearson result. This does not replace Spearman."""
        return self.methods[1]


def _direction(value: float) -> EffectDirection:
    if value < 0.0:
        return EffectDirection.NEGATIVE
    if value > 0.0:
        return EffectDirection.POSITIVE
    return EffectDirection.ZERO


def _require_component_consistency(result: AssociationResult) -> None:
    estimate = result.estimate
    interval = result.confidence_interval
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        if result.frequentist.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("a test requires an estimate")
        if result.frequentist.reason is not estimate.reason:
            raise ValueError("an unavailable estimate and its test share a reason")
        if interval.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("an interval requires an estimate")
        if interval.reason is not estimate.reason:
            raise ValueError("an unavailable estimate and its interval share a reason")
        return
    if result.method is AssociationMethod.SPEARMAN:
        if interval.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("Spearman has no confidence interval in this slice")
        if interval.reason is not UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD:
            raise ValueError("Spearman interval is not defined for this method")


def _require_correlation(value: Optional[float], field: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value < -1.0 or value > 1.0:
        raise ValueError(f"{field} must lie on [-1, 1]")
