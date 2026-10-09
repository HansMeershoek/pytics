"""Numeric × Categorical relationship records.

These records retain observed groups, eta squared, epsilon squared, and
classical one-way ANOVA. They do not calculate those facts and they do
not import a statistical library. Group descriptions reuse the Numeric
descriptive model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

from pytics.analysis.column_label import install_column_label_equality
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.relationships.models.common import FrequentistEvidence
from pytics.analysis.relationships.models.common import RelationshipFamily
from pytics.analysis.relationships.models.common import ResultAvailability
from pytics.analysis.relationships.models.common import UnavailabilityReason
from pytics.analysis.relationships.models.common import _require_canonical_positions
from pytics.analysis.relationships.models.common import _require_category_scalar
from pytics.analysis.relationships.models.common import _require_enum
from pytics.analysis.relationships.models.common import _require_nonnegative_float
from pytics.analysis.relationships.models.common import _require_population_counts
from pytics.analysis.relationships.models.common import _require_position
from pytics.analysis.relationships.models.common import _require_reason
from pytics.analysis.relationships.models.common import _require_type
from pytics.analysis.relationships.models.common import _require_unit_interval

_GROUP_EFFECT_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.INSUFFICIENT_GROUPS,
        UnavailabilityReason.ZERO_TOTAL_VARIATION,
        UnavailabilityReason.PRECISION_COLLAPSED,
        UnavailabilityReason.NON_FINITE_RESULT,
        UnavailabilityReason.CATEGORY_VOCABULARY_NOT_RETAINABLE,
    }
)
_ANOVA_COMPONENT_REASONS = _GROUP_EFFECT_REASONS | {
    UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM,
    UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
}


class GroupEffectMethod(Enum):
    """Omnibus effect identity for Numeric × Categorical.

    ``ETA_SQUARED`` is the descriptive ratio of observed variation.
    ``EPSILON_SQUARED`` is Kelley's bias-corrected companion of that
    ratio. Neither is a causal share and neither is a strength label.
    """

    ETA_SQUARED = "eta_squared"
    EPSILON_SQUARED = "epsilon_squared"


# The same absolute tolerance the calculator uses when a float ratio
# sits just outside its mathematical bound.
_EFFECT_TOLERANCE = 1e-8


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
    """One between-group effect for a Numeric × Categorical pair.

    Eta squared lies on ``[0, 1]``. It is the proportion of observed
    numeric variation associated with differences among group means.
    Epsilon squared uses the same denominator and subtracts the
    between-group degrees of freedom times the within-group mean square
    from the numerator. That correction can be negative. It is never
    stored above 1, and it is never NaN. ``reason`` is set only when the
    effect is unavailable. Unavailable is not stored as zero.
    """

    method: GroupEffectMethod
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.method, GroupEffectMethod, "method")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            if self.method is GroupEffectMethod.EPSILON_SQUARED:
                _require_epsilon_squared(self.value)
            else:
                _require_unit_interval(self.value, "effect")
            if self.reason is not None:
                raise ValueError("an available effect has no unavailability reason")
            return
        if self.value is not None:
            raise ValueError("an unavailable effect has no value")
        allowed = _GROUP_EFFECT_REASONS
        if self.method is GroupEffectMethod.EPSILON_SQUARED:
            allowed = _GROUP_EFFECT_REASONS | {
                UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM,
            }
        _require_reason(self.reason, allowed, "reason")


@dataclass(frozen=True)
class OmnibusAnovaResult:
    """Classical one-way ANOVA for one Numeric × Categorical pair.

    ``statistic`` is the finite F ratio when that ratio exists. Zero
    within-group variation does not store an infinite F or a p-value.
    ``frequentist`` holds the upper-tail p-value when the F ratio is
    finite. The calculator stores that raw p-value. Dataset-level
    correction may later set the adjusted companion of the same test.
    Those components do not share one availability flag with the F
    statistic. The p-value is not a significance flag, and this record
    does not name which groups differ.
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

    ``effect`` is eta squared, the descriptive ratio. ``corrected_effect``
    is epsilon squared, the bias-corrected companion of that same ratio.
    ``omnibus`` is classical one-way ANOVA. Those are separate components.
    This record has no correlation method, no confidence interval, and no
    primary-method field. A component can be unavailable without
    discarding the record. When the physical category vocabulary cannot
    be retained as itself, every component shares
    ``CATEGORY_VOCABULARY_NOT_RETAINABLE``, ``groups`` is empty, and
    ``n_paired`` is still the paired-row count. Those labels are not
    stored.

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
    corrected_effect: GroupEffectEstimate
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
        _require_type(self.effect, GroupEffectEstimate, "effect")
        _require_type(self.corrected_effect, GroupEffectEstimate, "corrected_effect")
        _require_type(self.omnibus, OmnibusAnovaResult, "omnibus")
        if counted != self.n_paired and not _vocabulary_groups_withheld(self):
            raise ValueError("group sizes must sum to n_paired")
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
    if effect.method is not GroupEffectMethod.ETA_SQUARED:
        raise ValueError("the descriptive effect is eta squared")
    if effect.availability is ResultAvailability.UNAVAILABLE:
        if (
            effect.reason is UnavailabilityReason.CATEGORY_VOCABULARY_NOT_RETAINABLE
            and relationship.groups
        ):
            raise ValueError(
                "a category vocabulary that cannot be retained has no groups"
            )
        if omnibus.statistic_availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("an undefined effect has no F statistic")
        if omnibus.statistic_reason is not effect.reason:
            raise ValueError("an undefined effect and its F statistic share a reason")
        if frequentist.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("an undefined effect has no omnibus p-value")
        if frequentist.reason is not effect.reason:
            raise ValueError("an undefined effect and its p-value share a reason")
        _require_epsilon_companion(relationship)
        return
    if omnibus.statistic_availability is ResultAvailability.AVAILABLE:
        _require_epsilon_companion(relationship)
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
        _require_epsilon_companion(relationship)
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
        corrected = relationship.corrected_effect
        if (
            corrected.availability is not ResultAvailability.AVAILABLE
            or corrected.value != 1.0
        ):
            raise ValueError("zero within-group variation leaves epsilon squared at 1")
        _require_epsilon_companion(relationship)
        return
    if reason is not UnavailabilityReason.NON_FINITE_RESULT:
        raise ValueError("an available effect has an unsupported F-statistic state")
    if frequentist.availability is not ResultAvailability.UNAVAILABLE:
        raise ValueError("an unavailable F statistic has no p-value")
    if frequentist.reason is not UnavailabilityReason.NON_FINITE_RESULT:
        raise ValueError("a non-finite omnibus result stays non-finite")
    _require_epsilon_companion(relationship)


def _vocabulary_groups_withheld(relationship: NumericCategoricalRelationship) -> bool:
    """True when empty groups are the withheld vocabulary, not an empty population."""
    return (
        not relationship.groups
        and relationship.effect.reason
        is UnavailabilityReason.CATEGORY_VOCABULARY_NOT_RETAINABLE
    )


def _require_epsilon_squared(value: Optional[float]) -> None:
    """Epsilon squared is finite and not above 1. A negative value is kept."""
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("epsilon squared must be a finite float")
    if value > 1.0:
        raise ValueError("epsilon squared cannot exceed 1")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError("epsilon squared must not be negative zero")


def _require_epsilon_companion(relationship: NumericCategoricalRelationship) -> None:
    """Keep epsilon squared as the companion of the same sums of squares.

    An undefined eta squared has no epsilon squared. One observation in
    every group leaves the within-group mean square undefined, so epsilon
    squared is absent while eta squared can still be 1. A defined epsilon
    squared cannot exceed eta squared: the correction subtracts a
    non-negative term.
    """
    effect = relationship.effect
    corrected = relationship.corrected_effect
    if corrected.method is not GroupEffectMethod.EPSILON_SQUARED:
        raise ValueError("the corrected effect is epsilon squared")
    if effect.availability is ResultAvailability.UNAVAILABLE:
        if (
            corrected.availability is not ResultAvailability.UNAVAILABLE
            or corrected.reason is not effect.reason
        ):
            raise ValueError("an undefined eta squared has no epsilon squared")
        return
    if corrected.availability is ResultAvailability.UNAVAILABLE:
        if (
            corrected.reason
            is UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
        ):
            if relationship.n_paired != relationship.n_groups:
                raise ValueError(
                    "epsilon squared needs within-group degrees of freedom"
                )
            return
        if corrected.reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError("epsilon squared is unavailable only when it is undefined")
        return
    if corrected.value > effect.value + _EFFECT_TOLERANCE:  # type: ignore[operator]
        raise ValueError("epsilon squared cannot exceed eta squared")


install_column_label_equality(NumericCategoricalRelationship)
