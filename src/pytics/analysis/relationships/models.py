"""Relationship result models.

Shared records describe availability, pair coverage, and the dataset
container. Family records describe that family's population rule and
statistical components. The dataset container does not claim one method
for every pair. These models do not calculate a statistic and they do
not import a statistical library. Numeric descriptive facts reused for
category groups come from the Numeric descriptive model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet
from typing import Optional
from typing import Tuple
from typing import Union

from pytics.analysis.numeric import NumericDescriptiveAnalysis

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


class RelationshipFamily(Enum):
    """Relationship family this version calculates.

    A member means the family is implemented. It does not mean one
    dataset contains a pair of that family. Families present in a
    dataset are the retained relationship records. Further families are
    not members until a calculation exists.
    """

    NUMERIC_NUMERIC = "numeric_numeric"
    NUMERIC_CATEGORICAL = "numeric_categorical"


class UnimplementedRelationshipFamily(Enum):
    """Accepted pair direction that this slice does not calculate.

    A count of these pairs is not a claim that the family was analyzed.
    """

    NUMERIC_BOOLEAN = "numeric_boolean"
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
    INSUFFICIENT_GROUPS = "insufficient_groups"
    ZERO_TOTAL_VARIATION = "zero_total_variation"
    INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM = (
        "insufficient_within_group_degrees_of_freedom"
    )
    ZERO_WITHIN_GROUP_VARIATION = "zero_within_group_variation"


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
_GROUP_EFFECT_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.INSUFFICIENT_GROUPS,
        UnavailabilityReason.ZERO_TOTAL_VARIATION,
        UnavailabilityReason.PRECISION_COLLAPSED,
        UnavailabilityReason.NON_FINITE_RESULT,
    }
)
_ANOVA_COMPONENT_REASONS = _GROUP_EFFECT_REASONS | {
    UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM,
    UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
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


class MultipleTestingAdjustment(Enum):
    """Multiple-testing status of a stored p-value.

    ``NOT_APPLIED`` means the raw p-value has no adjusted companion yet.
    """

    NOT_APPLIED = "not_applied"


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
        _require_reason(self.reason, _CORRELATION_COMPONENT_REASONS, "reason")


@dataclass(frozen=True)
class FrequentistEvidence:
    """Raw frequentist evidence for one inferential result.

    A correlation test and a one-way ANOVA p-value both use this record.
    ``adjustment`` belongs to this result. It is not a dataset-wide
    correction status. ``adjusted_p_value`` stays ``None`` while
    adjustment is not applied. The p-value is not a significance flag.
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


class GroupEffectMethod(Enum):
    """Omnibus effect identity for Numeric × Categorical.

    This is a descriptive ratio of observed variation. It is not a
    causal share and not a strength label.
    """

    ETA_SQUARED = "eta_squared"


class OmnibusTestMethod(Enum):
    """Frequentist omnibus test for Numeric × Categorical.

    Classical one-way ANOVA is the foundation. It is not selected by an
    assumption test, and it is not a pairwise comparison.
    """

    ONE_WAY_ANOVA = "one_way_anova"


class NumericCategoricalPopulation(Enum):
    """Rows that enter a Numeric × Categorical relationship.

    The numeric value is finite and the categorical value is observed.
    """

    FINITE_NUMERIC_OBSERVED_CATEGORY = "finite_numeric_observed_category"


class CategoryGroupOrder(Enum):
    """Presentation order of observed category groups.

    This is the physical categorical vocabulary with unused levels
    removed. It is not an ordinal score and it is not used by the
    omnibus test.
    """

    PHYSICAL_CATEGORICAL_VOCABULARY = "physical_categorical_vocabulary"


@dataclass(frozen=True)
class GroupEffectEstimate:
    """Overall between-group effect for one Numeric × Categorical pair.

    ``value`` is eta squared on ``[0, 1]`` when available: the proportion
    of observed numeric variation associated with differences among group
    means. It is never NaN. ``reason`` is set only when the effect is
    unavailable. Unavailable is not stored as zero.
    """

    method: GroupEffectMethod
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.method, GroupEffectMethod, "method")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_unit_interval(self.value, "effect")
            if self.reason is not None:
                raise ValueError("an available effect has no unavailability reason")
            return
        if self.value is not None:
            raise ValueError("an unavailable effect has no value")
        _require_reason(self.reason, _GROUP_EFFECT_REASONS, "reason")


@dataclass(frozen=True)
class OmnibusAnovaResult:
    """Classical one-way ANOVA for one Numeric × Categorical pair.

    ``statistic`` is the finite F ratio when that ratio exists. Zero
    within-group variation does not store an infinite F or a p-value.
    ``frequentist`` holds the raw upper-tail p-value when the F ratio
    is finite. Those two components do not share one availability flag.
    ``adjusted_p_value`` stays absent. The p-value is not a significance
    flag, and this record does not name which groups differ.
    """

    method: OmnibusTestMethod
    statistic_availability: ResultAvailability
    statistic: Optional[float]
    statistic_reason: Optional[UnavailabilityReason]
    frequentist: FrequentistEvidence

    def __post_init__(self) -> None:
        _require_enum(self.method, OmnibusTestMethod, "method")
        _require_enum(
            self.statistic_availability,
            ResultAvailability,
            "statistic_availability",
        )
        _require_type(self.frequentist, FrequentistEvidence, "frequentist")
        if self.frequentist.adjustment is not MultipleTestingAdjustment.NOT_APPLIED:
            raise ValueError("multiple-testing adjustment is not applied")
        if (
            self.frequentist.reason is not None
            and self.frequentist.reason not in _ANOVA_COMPONENT_REASONS
        ):
            raise ValueError("omnibus p-value reason is not an ANOVA reason")
        if self.statistic_availability is ResultAvailability.AVAILABLE:
            _require_nonnegative_float(self.statistic, "F statistic")
            if self.statistic_reason is not None:
                raise ValueError(
                    "an available F statistic has no unavailability reason"
                )
            return
        if self.statistic is not None:
            raise ValueError("an unavailable F statistic has no value")
        _require_reason(
            self.statistic_reason,
            _ANOVA_COMPONENT_REASONS,
            "statistic_reason",
        )


@dataclass(frozen=True)
class CategoricalGroupSummary:
    """Descriptive facts for one observed category.

    ``category`` is the source category scalar. It is not a display
    string and not a pandas container. ``descriptive`` uses the same
    finite-population definitions as a Numeric column. ``n`` is
    ``descriptive.finite_count``.
    """

    category: object
    descriptive: NumericDescriptiveAnalysis

    def __post_init__(self) -> None:
        _require_category_scalar(self.category)
        _require_type(self.descriptive, NumericDescriptiveAnalysis, "descriptive")
        if self.descriptive.finite_count < 1:
            raise ValueError("a category group has at least one paired observation")

    @property
    def n(self) -> int:
        """Paired finite numeric observations with this category."""
        return self.descriptive.finite_count


@dataclass(frozen=True)
class NumericCategoricalRelationship:
    """One selected Numeric × selected Categorical pair.

    ``left_position`` is less than ``right_position``. Both are physical
    positions. ``numeric_position`` and ``categorical_position`` are those
    same positions, assigned by semantic role. Swapping which side is
    numeric does not change the statistical population.

    ``n_paired`` counts rows where the numeric value is finite and the
    categorical value is non-missing. ``n_excluded`` is every other row.
    ``groups`` contains only categories that occur in that population,
    in physical categorical vocabulary order. The paired arrays are not
    stored.

    ``effect`` is eta squared. ``omnibus`` is classical one-way ANOVA.
    Those are separate components. This record has no correlation method,
    no confidence interval, and no primary-method field. Either component
    can be unavailable without discarding the record.

    ``population`` is the finite-numeric, observed-category rule.
    ``n_total_rows``, ``n_paired``, and ``n_excluded`` are the pair counts
    for that rule. The count fields use the same shape as a Numeric ×
    Numeric record. The eligibility rule does not.
    """

    left_position: int
    left_label: object
    right_position: int
    right_label: object
    numeric_position: int
    categorical_position: int
    n_total_rows: int
    n_paired: int
    groups: Tuple[CategoricalGroupSummary, ...]
    effect: GroupEffectEstimate
    omnibus: OmnibusAnovaResult

    def __post_init__(self) -> None:
        _require_canonical_positions(self.left_position, self.right_position)
        _require_position(self.numeric_position, "numeric_position")
        _require_position(self.categorical_position, "categorical_position")
        roles = {self.numeric_position, self.categorical_position}
        if roles != {self.left_position, self.right_position}:
            raise ValueError("roles must be the two physical pair positions")
        _require_population_counts(self.n_total_rows, self.n_paired)
        if not isinstance(self.groups, tuple):
            raise TypeError("groups must be a tuple")
        counted = 0
        for group in self.groups:
            _require_type(group, CategoricalGroupSummary, "groups")
            counted += group.n
        if counted != self.n_paired:
            raise ValueError("group sizes must sum to n_paired")
        _require_type(self.effect, GroupEffectEstimate, "effect")
        _require_type(self.omnibus, OmnibusAnovaResult, "omnibus")
        _require_numeric_categorical_components(self)

    @property
    def family(self) -> RelationshipFamily:
        """The implemented family this record belongs to."""
        return RelationshipFamily.NUMERIC_CATEGORICAL

    @property
    def population(self) -> NumericCategoricalPopulation:
        """Rows with a finite numeric value and an observed category."""
        return NumericCategoricalPopulation.FINITE_NUMERIC_OBSERVED_CATEGORY

    @property
    def group_order(self) -> CategoryGroupOrder:
        """Vocabulary order of observed categories. Not an ordinal score."""
        return CategoryGroupOrder.PHYSICAL_CATEGORICAL_VOCABULARY

    @property
    def n_excluded(self) -> int:
        """Rows outside the finite-numeric, observed-category population."""
        return self.n_total_rows - self.n_paired

    @property
    def n_groups(self) -> int:
        """Observed categories in the paired population."""
        return len(self.groups)


RelationshipRecord = Union[
    NumericNumericRelationship,
    NumericCategoricalRelationship,
]


@dataclass(frozen=True)
class RelationshipAnalysis:
    """Coverage and retained relationship records for one dataset.

    This container answers which relationship analyses were performed
    and how pair coverage was counted. It does not name one statistical
    method, one population rule, one computational image, or one
    confidence level for every record.

    Supported pairs are family-specific records, in ascending physical
    position order. ``RelationshipFamily`` names the families this
    version can calculate. Records name the families present in this
    dataset. Unimplemented recognized families and ineligible pairs are
    counts, because those pairs have no record. ``n_analyzed_pairs`` is
    the number of retained records, including records whose statistical
    components are unavailable. It is not a count of significant tests.
    """

    n_rows: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[RelationshipRecord, ...]

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


@dataclass(frozen=True)
class RelationshipsSummary:
    """Product projection of a retained relationship analysis.

    The summary is not a second statistical analysis. It copies coverage
    counts and family records so a later Relationships view can read them
    without the rest of ``DatasetAnalysis``. ``n_columns`` is copied so
    the unordered-pair total can be checked against the schema.

    The builder does not read a DataFrame, infer a family, or calculate
    a statistic. It does not restate a method, a population rule, a
    computational image, or a confidence level that is not already on
    the copied record.
    """

    n_rows: int
    n_columns: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[RelationshipRecord, ...]

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
    relationships: Tuple[RelationshipRecord, ...],
    n_rows: int,
    n_analyzed: int,
) -> None:
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    if len(relationships) != n_analyzed:
        raise ValueError("n_analyzed_pairs must equal the relationship records")
    previous = (-1, -1)
    for relationship in relationships:
        if not isinstance(
            relationship,
            (NumericNumericRelationship, NumericCategoricalRelationship),
        ):
            raise TypeError(
                "relationships must contain calculated relationship records"
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


def _require_canonical_positions(left: object, right: object) -> None:
    _require_position(left, "left_position")
    _require_position(right, "right_position")
    if left >= right:  # type: ignore[operator]
        raise ValueError("left_position must be less than right_position")


def _require_population_counts(n_total_rows: object, n_paired: object) -> None:
    """Shared pair-count shape. The eligibility rule stays on the record."""
    if type(n_total_rows) is not int or n_total_rows < 0:
        raise ValueError("n_total_rows must be a non-negative int")
    if type(n_paired) is not int or n_paired < 0:
        raise ValueError("n_paired must be a non-negative int")
    if n_paired > n_total_rows:
        raise ValueError("n_paired cannot exceed n_total_rows")


def _require_reason(
    reason: object,
    allowed: FrozenSet[UnavailabilityReason],
    field: str,
) -> None:
    _require_enum(reason, UnavailabilityReason, field)
    if reason not in allowed:
        raise ValueError(f"{field} is not a reason for this component")


def _require_nonnegative(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_unit_interval(value: Optional[float], field: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field} must lie on [0, 1]")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


def _require_nonnegative_float(value: Optional[float], field: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value < 0.0:
        raise ValueError(f"{field} cannot be negative")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


def _require_category_scalar(value: object) -> None:
    """Reject containers. Pandas scalar category values stay scalars."""
    if isinstance(value, tuple):
        for item in value:
            _require_category_scalar(item)
        return
    if isinstance(value, (list, dict, set, bytearray)):
        raise TypeError("category must be a retained scalar")
    module = type(value).__module__
    if module.startswith(("numpy", "pandas.core", "scipy")):
        raise TypeError(
            "category must not be a NumPy object, a pandas container, or a SciPy object"
        )


def _require_numeric_categorical_components(
    relationship: NumericCategoricalRelationship,
) -> None:
    """Keep an unavailable effect from carrying a defined omnibus result.

    A defined effect may still have an undefined F statistic. One
    observation in every group has no within-group degrees of freedom.
    Zero within-group variation with differing group means leaves eta
    squared at 1 and makes the ANOVA p-value unavailable with the F.
    """
    effect = relationship.effect
    omnibus = relationship.omnibus
    frequentist = omnibus.frequentist
    if effect.availability is ResultAvailability.UNAVAILABLE:
        if omnibus.statistic_availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("an undefined effect has no F statistic")
        if omnibus.statistic_reason is not effect.reason:
            raise ValueError("an undefined effect and its F statistic share a reason")
        if frequentist.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("an undefined effect has no omnibus p-value")
        if frequentist.reason is not effect.reason:
            raise ValueError("an undefined effect and its p-value share a reason")
        return
    if omnibus.statistic_availability is ResultAvailability.AVAILABLE:
        return
    reason = omnibus.statistic_reason
    if reason is UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM:
        if relationship.n_paired != relationship.n_groups:
            raise ValueError(
                "within-group degrees of freedom require n_paired == n_groups"
            )
        if any(group.n != 1 for group in relationship.groups):
            raise ValueError(
                "that degree-of-freedom state is one observation per group"
            )
        if effect.value != 1.0:
            raise ValueError(
                "one observation per group leaves no within-group variation"
            )
        if frequentist.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("that degree-of-freedom state has no p-value")
        if frequentist.reason is not reason:
            raise ValueError("the missing p-value uses the F statistic's reason")
        return
    if reason is UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION:
        if relationship.n_paired <= relationship.n_groups:
            raise ValueError(
                "zero within-group variation requires within-group degrees of freedom"
            )
        if effect.value != 1.0:
            raise ValueError(
                "zero within-group variation with group differences has eta squared 1"
            )
        if frequentist.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("zero within-group variation has no ANOVA p-value")
        if frequentist.reason is not reason:
            raise ValueError("the missing p-value uses the F statistic's reason")
        return
    if reason is not UnavailabilityReason.NON_FINITE_RESULT:
        raise ValueError("an available effect has an unsupported F-statistic state")
    if frequentist.availability is not ResultAvailability.UNAVAILABLE:
        raise ValueError("an unavailable F statistic has no p-value")
    if frequentist.reason is not UnavailabilityReason.NON_FINITE_RESULT:
        raise ValueError("a non-finite omnibus result stays non-finite")
