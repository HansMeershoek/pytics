"""Relationship result models shared by relationship families.

These values describe pair identity, component availability, and the
dataset relationship record. They do not calculate a correlation and
they do not import a statistical library. Numeric × Numeric details
that are only meaningful for that family, including Pearson and
Spearman, live with that family's calculation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

# Two-sided 95% interval. The level is not configurable in this slice.
_CONFIDENCE_LEVEL = 0.95


class AssociationMethod(Enum):
    """Machine-readable association method.

    Display names are not this identity.
    """

    SPEARMAN = "spearman"
    PEARSON = "pearson"


class RelationshipFamily(Enum):
    """Implemented relationship family.

    Further families are not members of this enum until a method exists.
    """

    NUMERIC_NUMERIC = "numeric_numeric"


class UnimplementedRelationshipFamily(Enum):
    """Accepted pair direction that this slice does not calculate.

    A count of these pairs is not a claim that the family was analyzed.
    """

    NUMERIC_BOOLEAN = "numeric_boolean"
    NUMERIC_CATEGORICAL = "numeric_categorical"
    BOOLEAN_BOOLEAN = "boolean_boolean"
    CATEGORICAL_CATEGORICAL = "categorical_categorical"
    DATETIME_NUMERIC = "datetime_numeric"
    DATETIME_CATEGORICAL = "datetime_categorical"


class ResultAvailability(Enum):
    """Whether one statistical component has a value."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class UnavailabilityReason(Enum):
    """Why a component has no value.

    These are analytical states, not user-facing prose.
    """

    INSUFFICIENT_PAIRED_OBSERVATIONS = "insufficient_paired_observations"
    CONSTANT_PAIRED_VALUES = "constant_paired_values"
    PRECISION_COLLAPSED = "precision_collapsed"
    NON_FINITE_RESULT = "non_finite_result"
    BOUNDARY_CORRELATION = "boundary_correlation"
    INTERVAL_NOT_DEFINED_FOR_METHOD = "interval_not_defined_for_method"


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


class MultipleTestingAdjustment(Enum):
    """Multiple-testing status of a stored p-value.

    ``NOT_APPLIED`` means the raw p-value has no adjusted companion yet.
    """

    NOT_APPLIED = "not_applied"


class PairPopulation(Enum):
    """Which rows enter a Numeric × Numeric correlation."""

    PAIRWISE_FINITE = "pairwise_finite"


class NumericComputation(Enum):
    """Computational representation passed to the correlation routines.

    ``FLOAT64`` does not claim exact integer correlation above ``2**53``.
    """

    FLOAT64 = "float64"


@dataclass(frozen=True)
class UnimplementedFamilyCount:
    """How many physical pairs share one recognized, unimplemented family.

    ``n_pairs`` is at least one. A family with no pairs is omitted.
    """

    family: UnimplementedRelationshipFamily
    n_pairs: int

    def __post_init__(self) -> None:
        if not isinstance(self.family, UnimplementedRelationshipFamily):
            raise TypeError("family must be an UnimplementedRelationshipFamily")
        if type(self.n_pairs) is not int or self.n_pairs < 1:
            raise ValueError("n_pairs must be a positive int")


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
        _require_enum(self.reason, UnavailabilityReason, "reason")


@dataclass(frozen=True)
class FrequentistEvidence:
    """Raw frequentist evidence attached to one estimate.

    ``p_value`` is the two-sided SciPy p-value when the test is available.
    ``adjusted_p_value`` stays ``None`` while adjustment is not applied.
    The p-value is not a significance flag.
    """

    availability: ResultAvailability
    p_value: Optional[float]
    adjusted_p_value: Optional[float]
    adjustment: MultipleTestingAdjustment
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        _require_enum(self.adjustment, MultipleTestingAdjustment, "adjustment")
        if self.adjusted_p_value is not None:
            raise ValueError("an unadjusted test has no adjusted p-value")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_p_value(self.p_value)
            if self.reason is not None:
                raise ValueError("an available test has no unavailability reason")
            return
        if self.p_value is not None:
            raise ValueError("an unavailable test has no p-value")
        _require_enum(self.reason, UnavailabilityReason, "reason")


@dataclass(frozen=True)
class CorrelationInterval:
    """Uncertainty interval for one correlation estimate.

    An available interval records its level and method. Spearman has no
    interval in this slice, so its interval stays unavailable even when
    the estimate exists.
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
        _require_enum(self.reason, UnavailabilityReason, "reason")


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
        _require_component_consistency(self)


@dataclass(frozen=True)
class NumericNumericRelationship:
    """One selected Numeric × selected Numeric pair.

    ``left_position`` is less than ``right_position``. Both are physical
    positions. ``n_paired`` counts rows where both source values are
    finite. ``n_excluded`` is every other row, including rows where either
    value is missing or infinite. The paired arrays are not stored.

    ``methods`` is Spearman, then Pearson. Both records exist when a
    method is unavailable.
    """

    left_position: int
    left_label: object
    right_position: int
    right_label: object
    n_total_rows: int
    n_paired: int
    methods: Tuple[AssociationResult, ...]

    def __post_init__(self) -> None:
        _require_position(self.left_position, "left_position")
        _require_position(self.right_position, "right_position")
        if self.left_position >= self.right_position:
            raise ValueError("left_position must be less than right_position")
        if type(self.n_total_rows) is not int or self.n_total_rows < 0:
            raise ValueError("n_total_rows must be a non-negative int")
        if type(self.n_paired) is not int or self.n_paired < 0:
            raise ValueError("n_paired must be a non-negative int")
        if self.n_paired > self.n_total_rows:
            raise ValueError("n_paired cannot exceed n_total_rows")
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
    def n_excluded(self) -> int:
        """Rows that are not in the pairwise finite population.

        A row is excluded when either value is missing or not finite.
        """
        return self.n_total_rows - self.n_paired

    @property
    def spearman(self) -> AssociationResult:
        """Spearman result. This is the primary descriptive association."""
        return self.methods[0]

    @property
    def pearson(self) -> AssociationResult:
        """Pearson result. This does not replace Spearman."""
        return self.methods[1]


@dataclass(frozen=True)
class RelationshipAnalysis:
    """Retained relationship facts for one dataset.

    Only supported Numeric × Numeric pairs are stored as records.
    Unimplemented recognized families and ineligible pairs are counts.
    ``n_analyzed_pairs`` is the number of retained records, including
    records whose methods are unavailable. It is not a count of
    significant tests.

    ``primary_method`` is Spearman. ``computation`` is float64. Those
    conventions are properties of this implementation, not a second copy
    of the estimates.
    """

    n_rows: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[NumericNumericRelationship, ...]

    def __post_init__(self) -> None:
        _require_nonnegative(self.n_rows, "n_rows")
        _require_nonnegative(self.n_total_pairs, "n_total_pairs")
        _require_nonnegative(self.n_supported_pairs, "n_supported_pairs")
        _require_nonnegative(self.n_analyzed_pairs, "n_analyzed_pairs")
        _require_nonnegative(
            self.n_unimplemented_family_pairs,
            "n_unimplemented_family_pairs",
        )
        _require_nonnegative(self.n_ineligible_pairs, "n_ineligible_pairs")
        if (
            self.n_supported_pairs
            + self.n_unimplemented_family_pairs
            + self.n_ineligible_pairs
            != self.n_total_pairs
        ):
            raise ValueError("pair counts must sum to n_total_pairs")
        if self.n_analyzed_pairs != self.n_supported_pairs:
            raise ValueError("every supported pair is analyzed")
        _require_family_counts(
            self.unimplemented_family_counts,
            self.n_unimplemented_family_pairs,
        )
        _require_relationships(self.relationships, self.n_rows, self.n_analyzed_pairs)

    @property
    def n_unsupported_pairs(self) -> int:
        """Pairs that were not analyzed.

        This is the unimplemented recognized families plus the ineligible
        pairs. Unsupported does not mean the data are invalid.
        """
        return self.n_unimplemented_family_pairs + self.n_ineligible_pairs

    @property
    def primary_method(self) -> AssociationMethod:
        """Spearman is the primary descriptive association."""
        return AssociationMethod.SPEARMAN

    @property
    def population(self) -> PairPopulation:
        """Pairwise finite source values."""
        return PairPopulation.PAIRWISE_FINITE

    @property
    def computation(self) -> NumericComputation:
        """Float64 image used for SciPy. Not an exact integer claim."""
        return NumericComputation.FLOAT64

    @property
    def confidence_level(self) -> float:
        """Level used when a Pearson interval is available."""
        return _CONFIDENCE_LEVEL

    @property
    def multiple_testing(self) -> MultipleTestingAdjustment:
        """Adjustment is not applied. Raw p-values stay raw."""
        return MultipleTestingAdjustment.NOT_APPLIED

    @property
    def implemented_family(self) -> RelationshipFamily:
        """The only family this analysis calculates."""
        return RelationshipFamily.NUMERIC_NUMERIC


@dataclass(frozen=True)
class RelationshipsSummary:
    """Product projection of a retained relationship analysis.

    The builder copies counts and relationship records. It does not read
    a DataFrame and does not calculate a correlation.
    """

    n_rows: int
    n_columns: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[NumericNumericRelationship, ...]

    def __post_init__(self) -> None:
        _require_nonnegative(self.n_rows, "n_rows")
        _require_nonnegative(self.n_columns, "n_columns")
        expected = self.n_columns * (self.n_columns - 1) // 2
        if self.n_total_pairs != expected:
            raise ValueError("n_total_pairs must equal the unordered column pairs")
        _require_nonnegative(self.n_supported_pairs, "n_supported_pairs")
        _require_nonnegative(self.n_analyzed_pairs, "n_analyzed_pairs")
        _require_nonnegative(
            self.n_unimplemented_family_pairs,
            "n_unimplemented_family_pairs",
        )
        _require_nonnegative(self.n_ineligible_pairs, "n_ineligible_pairs")
        if (
            self.n_supported_pairs
            + self.n_unimplemented_family_pairs
            + self.n_ineligible_pairs
            != self.n_total_pairs
        ):
            raise ValueError("pair counts must sum to n_total_pairs")
        if self.n_analyzed_pairs != self.n_supported_pairs:
            raise ValueError("every supported pair is analyzed")
        _require_family_counts(
            self.unimplemented_family_counts,
            self.n_unimplemented_family_pairs,
        )
        _require_relationships(self.relationships, self.n_rows, self.n_analyzed_pairs)

    @property
    def n_unsupported_pairs(self) -> int:
        """Pairs that were not analyzed."""
        return self.n_unimplemented_family_pairs + self.n_ineligible_pairs

    @property
    def primary_method(self) -> AssociationMethod:
        """Spearman is the primary descriptive association."""
        return AssociationMethod.SPEARMAN

    @property
    def population(self) -> PairPopulation:
        """Pairwise finite source values."""
        return PairPopulation.PAIRWISE_FINITE

    @property
    def computation(self) -> NumericComputation:
        """Float64 image used for SciPy. Not an exact integer claim."""
        return NumericComputation.FLOAT64

    @property
    def confidence_level(self) -> float:
        """Level used when a Pearson interval is available."""
        return _CONFIDENCE_LEVEL

    @property
    def multiple_testing(self) -> MultipleTestingAdjustment:
        """Adjustment is not applied. Raw p-values stay raw."""
        return MultipleTestingAdjustment.NOT_APPLIED

    @property
    def implemented_family(self) -> RelationshipFamily:
        """The only family this summary projects."""
        return RelationshipFamily.NUMERIC_NUMERIC


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


def _require_relationships(
    relationships: Tuple[NumericNumericRelationship, ...],
    n_rows: int,
    n_analyzed: int,
) -> None:
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    if len(relationships) != n_analyzed:
        raise ValueError("n_analyzed_pairs must equal the relationship records")
    previous = (-1, -1)
    for relationship in relationships:
        if not isinstance(relationship, NumericNumericRelationship):
            raise TypeError(
                "relationships must contain NumericNumericRelationship values"
            )
        if relationship.n_total_rows != n_rows:
            raise ValueError("relationship rows must equal the dataset row count")
        key = (relationship.left_position, relationship.right_position)
        if key <= previous:
            raise ValueError("relationships must be ordered by ascending positions")
        previous = key


def _require_family_counts(
    counts: Tuple[UnimplementedFamilyCount, ...],
    n_pairs: int,
) -> None:
    if not isinstance(counts, tuple):
        raise TypeError("unimplemented_family_counts must be a tuple")
    seen = []
    total = 0
    for item in counts:
        if not isinstance(item, UnimplementedFamilyCount):
            raise TypeError(
                "unimplemented_family_counts must contain UnimplementedFamilyCount values"
            )
        seen.append(item.family)
        total += item.n_pairs
    if len(seen) != len(set(seen)):
        raise ValueError("an unimplemented family is counted more than once")
    order = {
        family: index for index, family in enumerate(UnimplementedRelationshipFamily)
    }
    if seen != sorted(seen, key=lambda family: order[family]):
        raise ValueError("unimplemented families must follow definition order")
    if total != n_pairs:
        raise ValueError("unimplemented family counts must sum to the family total")


def _require_correlation(value: Optional[float], field: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value < -1.0 or value > 1.0:
        raise ValueError(f"{field} must lie on [-1, 1]")


def _require_p_value(value: Optional[float]) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("p_value must be a finite float")
    if value < 0.0 or value > 1.0:
        raise ValueError("p_value must lie on [0, 1]")


def _require_enum(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _require_type(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _require_position(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_nonnegative(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")
