"""Retained relationship-drift records.

A relationship state is an effect inside one dataset. A relationship
change is the difference between the corresponding effects. A formal
change test, where one exists, has its own null. A within-dataset
p-value is not copied here and is not a change.

The primary change is one measure per implemented family: Spearman rho,
eta squared, Hedges' g, phi, or Cramér's V. Complementary changes stay
beside that measure. Nothing in this module combines those measures
into one score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.compare.values import _require_count
from pytics.analysis.compare.values import _require_optional
from pytics.analysis.compare.values import _require_type
from pytics.analysis.relationships.models.common import RelationshipFamily
from pytics.analysis.relationships.models.common import ResultAvailability
from pytics.analysis.relationships.models.common import UnavailabilityReason
from pytics.analysis.relationships.models.common import _require_category_scalar
from pytics.analysis.relationships.models.common import _require_closed_interval
from pytics.analysis.relationships.models.common import _require_unit_interval
from pytics.analysis.relationships.models.coverage import (
    UnimplementedRelationshipFamily,
)

_SIGNED_MEASURES = frozenset()  # filled after the enum is created


class RelationshipPairStatus(Enum):
    """How the two sides of one aligned pair relate.

    ``SAME_FAMILY`` is the only status that can carry an effect change.
    ``FAMILY_TRANSITION`` means the semantic families differ, including a
    move between a calculated family and an unimplemented one.
    ``UNIMPLEMENTED`` means both sides are the same recognized family this
    version does not calculate. ``ELIGIBILITY_TRANSITION`` means exactly
    one side is not a relationship candidate. None of these is a claim
    that an effect moved.
    """

    SAME_FAMILY = "same_family"
    FAMILY_TRANSITION = "family_transition"
    UNIMPLEMENTED = "unimplemented"
    ELIGIBILITY_TRANSITION = "eligibility_transition"


class RelationshipSideKind(Enum):
    """What one dataset contributes for an aligned pair."""

    CALCULATED = "calculated"
    UNIMPLEMENTED = "unimplemented"
    INELIGIBLE = "ineligible"


class RelationshipChangeMeasure(Enum):
    """One cross-dataset relationship effect.

    The first five members are the primary measures of the implemented
    families. The others are complementary. They are not interchangeable
    and they are not summed.
    """

    SPEARMAN_RHO = "spearman_rho"
    ETA_SQUARED = "eta_squared"
    HEDGES_G = "hedges_g"
    PHI = "phi"
    CRAMERS_V = "cramers_v"
    PEARSON_R = "pearson_r"
    MEAN_DIFFERENCE = "mean_difference"
    PROBABILITY_DIFFERENCE = "probability_difference"


_PRIMARY_MEASURE = {
    RelationshipFamily.NUMERIC_NUMERIC: RelationshipChangeMeasure.SPEARMAN_RHO,
    RelationshipFamily.NUMERIC_CATEGORICAL: RelationshipChangeMeasure.ETA_SQUARED,
    RelationshipFamily.NUMERIC_BOOLEAN: RelationshipChangeMeasure.HEDGES_G,
    RelationshipFamily.BOOLEAN_BOOLEAN: RelationshipChangeMeasure.PHI,
    RelationshipFamily.CATEGORICAL_CATEGORICAL: (RelationshipChangeMeasure.CRAMERS_V),
}
_COMPLEMENTARY_MEASURE = {
    RelationshipFamily.NUMERIC_NUMERIC: RelationshipChangeMeasure.PEARSON_R,
    RelationshipFamily.NUMERIC_BOOLEAN: RelationshipChangeMeasure.MEAN_DIFFERENCE,
    RelationshipFamily.BOOLEAN_BOOLEAN: (
        RelationshipChangeMeasure.PROBABILITY_DIFFERENCE
    ),
}
_SIGNED_MEASURES = frozenset(
    {
        RelationshipChangeMeasure.SPEARMAN_RHO,
        RelationshipChangeMeasure.HEDGES_G,
        RelationshipChangeMeasure.PHI,
        RelationshipChangeMeasure.PEARSON_R,
        RelationshipChangeMeasure.MEAN_DIFFERENCE,
        RelationshipChangeMeasure.PROBABILITY_DIFFERENCE,
    }
)
_BOUNDED_UNIT = frozenset(
    {
        RelationshipChangeMeasure.ETA_SQUARED,
        RelationshipChangeMeasure.CRAMERS_V,
    }
)
_CLOSED_CORRELATION = frozenset(
    {
        RelationshipChangeMeasure.SPEARMAN_RHO,
        RelationshipChangeMeasure.PEARSON_R,
        RelationshipChangeMeasure.PHI,
        RelationshipChangeMeasure.PROBABILITY_DIFFERENCE,
    }
)


class EffectChangeReason(Enum):
    """Why an effect change has no numeric difference.

    ``None`` on a source effect is not stored as a zero change.
    ``ORIENTATION_NOT_SHARED`` means a directional contrast does not name
    the same logical column on both sides, so the two numbers are not one
    series.
    """

    REFERENCE_EFFECT_UNAVAILABLE = "reference_effect_unavailable"
    COMPARISON_EFFECT_UNAVAILABLE = "comparison_effect_unavailable"
    BOTH_EFFECTS_UNAVAILABLE = "both_effects_unavailable"
    ORIENTATION_NOT_SHARED = "orientation_not_shared"
    NON_FINITE_DIFFERENCE = "non_finite_difference"


class VocabularyStatus(Enum):
    """Whether two observed category sets are the same set.

    Order is not part of the comparison. A changed set does not by itself
    make a numeric effect change unavailable, and it is not proof that
    the effect moved.
    """

    SAME = "same"
    CHANGED = "changed"


class PearsonChangeNull(Enum):
    """Null hypothesis of the complementary Pearson change test."""

    EQUAL_PEARSON_CORRELATIONS = "equal_pearson_correlations"


class PearsonChangeAssumption(Enum):
    """Assumptions of the complementary Pearson change test.

    These are properties the procedure uses. They are not checks that
    were applied to the two datasets.
    """

    INDEPENDENT_PAIR_POPULATIONS = "independent_pair_populations"
    APPROXIMATE_BIVARIATE_NORMALITY = "approximate_bivariate_normality"
    FISHER_Z_ASYMPTOTIC = "fisher_z_asymptotic"


class PearsonChangeReason(Enum):
    """Why the complementary Pearson change test has no result.

    The test is undefined when either Pearson correlation is missing,
    when either pair has fewer than four observations, when either
    correlation is on the boundary ``±1``, or when the transform is not
    finite. It is not withheld because a within-dataset p-value crossed
    a threshold.
    """

    PEARSON_UNAVAILABLE = "pearson_unavailable"
    INSUFFICIENT_PAIRED_OBSERVATIONS = "insufficient_paired_observations"
    BOUNDARY_CORRELATION = "boundary_correlation"
    NON_FINITE_RESULT = "non_finite_result"


PEARSON_CHANGE_ASSUMPTIONS: Tuple[PearsonChangeAssumption, ...] = (
    PearsonChangeAssumption.INDEPENDENT_PAIR_POPULATIONS,
    PearsonChangeAssumption.APPROXIMATE_BIVARIATE_NORMALITY,
    PearsonChangeAssumption.FISHER_Z_ASYMPTOTIC,
)


@dataclass(frozen=True)
class RelationshipColumnIdentity:
    """One column of an aligned relationship pair.

    Positions are physical indexes. ``occurrence`` is the cross-dataset
    label occurrence from column alignment. The label values are the
    retained forms, not the original objects.
    """

    occurrence: int
    reference_position: int
    comparison_position: int
    reference_label: RetainedColumnLabel
    comparison_label: RetainedColumnLabel

    def __post_init__(self) -> None:
        _require_count(self.occurrence, "occurrence")
        if self.occurrence < 1:
            raise ValueError("occurrence must be a positive int")
        _require_count(self.reference_position, "reference_position")
        _require_count(self.comparison_position, "comparison_position")
        _require_type(self.reference_label, RetainedColumnLabel, "reference_label")
        _require_type(self.comparison_label, RetainedColumnLabel, "comparison_label")

    @property
    def reordered(self) -> bool:
        """Whether this column's physical positions differ."""
        return self.reference_position != self.comparison_position


@dataclass(frozen=True)
class RelationshipPairAlignment:
    """The two columns of one logical relationship.

    ``first`` has the smaller reference position. That order is pair
    identity. It is not the orientation of a directed family effect.
    """

    first: RelationshipColumnIdentity
    second: RelationshipColumnIdentity

    def __post_init__(self) -> None:
        _require_type(self.first, RelationshipColumnIdentity, "first")
        _require_type(self.second, RelationshipColumnIdentity, "second")
        if self.first.reference_position >= self.second.reference_position:
            raise ValueError("pair columns follow ascending reference positions")
        if (
            self.first.reference_position == self.second.reference_position
            or self.first.comparison_position == self.second.comparison_position
        ):
            raise ValueError("a pair uses two distinct columns on each side")


@dataclass(frozen=True)
class NumericNumericState:
    """Spearman and Pearson values copied from one numeric pair.

    Spearman is the primary effect. Pearson is complementary. Neither
    field is a p-value.
    """

    n_paired: int
    spearman: Optional[float]
    spearman_reason: Optional[UnavailabilityReason]
    pearson: Optional[float]
    pearson_reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_count(self.n_paired, "n_paired")
        _require_effect(
            self.spearman,
            self.spearman_reason,
            RelationshipChangeMeasure.SPEARMAN_RHO,
            "spearman",
        )
        _require_effect(
            self.pearson,
            self.pearson_reason,
            RelationshipChangeMeasure.PEARSON_R,
            "pearson",
        )


@dataclass(frozen=True)
class NumericCategoricalState:
    """Eta squared and the observed grouping categories of one pair.

    ``categories`` is the relationship's observed groups, in that
    record's vocabulary order. It is not recomputed from source rows.
    ``numeric_is_first`` names the numeric column in pair order.
    """

    n_paired: int
    numeric_is_first: bool
    categories: Tuple[object, ...]
    eta_squared: Optional[float]
    eta_squared_reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_count(self.n_paired, "n_paired")
        if type(self.numeric_is_first) is not bool:
            raise TypeError("numeric_is_first must be a bool")
        _require_levels(self.categories, "categories")
        _require_effect(
            self.eta_squared,
            self.eta_squared_reason,
            RelationshipChangeMeasure.ETA_SQUARED,
            "eta_squared",
        )


@dataclass(frozen=True)
class NumericBooleanState:
    """Hedges' g and the True − False mean difference of one pair.

    ``numeric_is_first`` names the numeric column in pair order. The
    sign of both effects is True minus False, not physical column order.
    """

    n_paired: int
    numeric_is_first: bool
    hedges_g: Optional[float]
    hedges_g_reason: Optional[UnavailabilityReason]
    mean_difference: Optional[float]
    mean_difference_reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_count(self.n_paired, "n_paired")
        if type(self.numeric_is_first) is not bool:
            raise TypeError("numeric_is_first must be a bool")
        _require_effect(
            self.hedges_g,
            self.hedges_g_reason,
            RelationshipChangeMeasure.HEDGES_G,
            "hedges_g",
        )
        _require_effect(
            self.mean_difference,
            self.mean_difference_reason,
            RelationshipChangeMeasure.MEAN_DIFFERENCE,
            "mean_difference",
        )


@dataclass(frozen=True)
class BooleanBooleanState:
    """Phi and the directional probability difference of one Boolean pair.

    ``conditioning_is_first`` follows the record's conditioning column,
    mapped into pair order. Phi does not use that role. The probability
    difference does.
    """

    n_paired: int
    conditioning_is_first: bool
    phi: Optional[float]
    phi_reason: Optional[UnavailabilityReason]
    probability_difference: Optional[float]
    probability_difference_reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_count(self.n_paired, "n_paired")
        if type(self.conditioning_is_first) is not bool:
            raise TypeError("conditioning_is_first must be a bool")
        _require_effect(
            self.phi,
            self.phi_reason,
            RelationshipChangeMeasure.PHI,
            "phi",
        )
        _require_effect(
            self.probability_difference,
            self.probability_difference_reason,
            RelationshipChangeMeasure.PROBABILITY_DIFFERENCE,
            "probability_difference",
        )


@dataclass(frozen=True)
class CategoricalCategoricalState:
    """Cramér's V and the observed levels of one categorical pair.

    Levels are stored in pair order, not in the source record's physical
    left/right order. ``n_positive_cells`` is the count of positive
    contingency cells. It is not an effect.
    """

    n_paired: int
    first_levels: Tuple[object, ...]
    second_levels: Tuple[object, ...]
    n_positive_cells: int
    cramers_v: Optional[float]
    cramers_v_reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_count(self.n_paired, "n_paired")
        _require_levels(self.first_levels, "first_levels")
        _require_levels(self.second_levels, "second_levels")
        _require_count(self.n_positive_cells, "n_positive_cells")
        rectangle = len(self.first_levels) * len(self.second_levels)
        if self.n_positive_cells > rectangle:
            raise ValueError("positive cells cannot exceed the level rectangle")
        _require_effect(
            self.cramers_v,
            self.cramers_v_reason,
            RelationshipChangeMeasure.CRAMERS_V,
            "cramers_v",
        )


@dataclass(frozen=True)
class RelationshipSide:
    """One dataset's relationship state for an aligned pair.

    A calculated side keeps exactly one family payload. An unimplemented
    side names the recognized family and keeps no effect. An ineligible
    side keeps neither. The payload is a projection of retained fields,
    not the source relationship object.
    """

    kind: RelationshipSideKind
    family: Optional[RelationshipFamily] = None
    unimplemented_family: Optional[UnimplementedRelationshipFamily] = None
    numeric_numeric: Optional[NumericNumericState] = None
    numeric_categorical: Optional[NumericCategoricalState] = None
    numeric_boolean: Optional[NumericBooleanState] = None
    boolean_boolean: Optional[BooleanBooleanState] = None
    categorical_categorical: Optional[CategoricalCategoricalState] = None

    def __post_init__(self) -> None:
        _require_type(self.kind, RelationshipSideKind, "kind")
        _require_optional(self.family, RelationshipFamily, "family")
        _require_optional(
            self.unimplemented_family,
            UnimplementedRelationshipFamily,
            "unimplemented_family",
        )
        payloads = _payloads(self)
        if self.kind is RelationshipSideKind.CALCULATED:
            if self.family is None or self.unimplemented_family is not None:
                raise ValueError("a calculated side names its implemented family")
            expected = _PAYLOAD_FIELD[self.family]
            if {name for name, _payload in payloads} != {expected}:
                raise ValueError("a calculated side keeps its own family payload")
            return
        if payloads:
            raise ValueError("only a calculated side keeps an effect payload")
        if self.kind is RelationshipSideKind.UNIMPLEMENTED:
            if self.family is not None or self.unimplemented_family is None:
                raise ValueError("an unimplemented side names its recognized family")
            return
        if self.family is not None or self.unimplemented_family is not None:
            raise ValueError("an ineligible side names no relationship family")

    def payload(self) -> object:
        """The calculated family payload, if this side has one."""
        payloads = _payloads(self)
        if len(payloads) != 1:
            return None
        return payloads[0][1]


@dataclass(frozen=True)
class EffectChange:
    """``comparison - reference`` for one relationship effect.

    ``change`` is that difference when both effects exist and the
    difference is finite. Otherwise it is ``None``. ``None`` is not zero.
    ``magnitude_change`` is ``|comparison| - |reference|`` for a signed
    effect when both values exist. It is absent for an unsigned effect,
    whose ordinary difference already carries the direction. ``sign_reversal``
    is true only when both signed effects exist and are nonzero with
    opposite signs. Zero is not a sign, so a move from or to zero is not
    a reversal.
    """

    measure: RelationshipChangeMeasure
    availability: ResultAvailability
    reference: Optional[float]
    comparison: Optional[float]
    change: Optional[float]
    magnitude_change: Optional[float]
    sign_reversal: Optional[bool]
    reason: Optional[EffectChangeReason]

    def __post_init__(self) -> None:
        _require_type(self.measure, RelationshipChangeMeasure, "measure")
        _require_type(self.availability, ResultAvailability, "availability")
        _require_optional_effect(self.reference, self.measure, "reference")
        _require_optional_effect(self.comparison, self.measure, "comparison")
        signed = self.measure in _SIGNED_MEASURES
        if self.availability is ResultAvailability.AVAILABLE:
            if self.reason is not None:
                raise ValueError("an available effect change has no reason")
            if self.reference is None or self.comparison is None or self.change is None:
                raise ValueError("an available effect change has both effects")
            expected = _finite_difference(self.comparison, self.reference)
            if expected is None or self.change != expected:
                raise ValueError("effect change must be comparison minus reference")
            _require_signed_companions(self, signed, both_values=True)
            return
        if self.change is not None:
            raise ValueError("an unavailable effect change has no difference")
        if self.reason is None:
            raise ValueError("an unavailable effect change names why")
        _require_type(self.reason, EffectChangeReason, "reason")
        if self.reason is EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE:
            if self.reference is not None or self.comparison is not None:
                raise ValueError("a two-sided gap stores neither effect")
        elif self.reason is EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE:
            if self.reference is not None or self.comparison is None:
                raise ValueError("a reference gap stores only the comparison effect")
        elif self.reason is EffectChangeReason.COMPARISON_EFFECT_UNAVAILABLE:
            if self.comparison is not None or self.reference is None:
                raise ValueError("a comparison gap stores only the reference effect")
        elif self.reason is EffectChangeReason.ORIENTATION_NOT_SHARED:
            if self.reference is not None or self.comparison is not None:
                raise ValueError("an unshared orientation is not one effect series")
        elif self.reference is None or self.comparison is None:
            raise ValueError("a non-finite difference still has both effects")
        both = self.reference is not None and self.comparison is not None
        _require_signed_companions(self, signed, both_values=both)


@dataclass(frozen=True)
class GroupingVocabulary:
    """Observed categories of one grouping variable across the two datasets."""

    status: VocabularyStatus
    reference_n_levels: int
    comparison_n_levels: int

    def __post_init__(self) -> None:
        _require_type(self.status, VocabularyStatus, "status")
        _require_count(self.reference_n_levels, "reference_n_levels")
        _require_count(self.comparison_n_levels, "comparison_n_levels")
        same_count = self.reference_n_levels == self.comparison_n_levels
        if self.status is VocabularyStatus.SAME and not same_count:
            raise ValueError("the same category set has the same level count")
        if self.status is VocabularyStatus.CHANGED and (
            same_count
            and self.reference_n_levels == 0
            and self.comparison_n_levels == 0
        ):
            raise ValueError("two empty category sets are the same set")


@dataclass(frozen=True)
class ContingencyVocabulary:
    """Observed levels of both categorical columns, in pair order.

    ``reference_shape`` is ``(n_first, n_second)`` on the reference.
    A changed shape or a changed level set is ``CHANGED`` overall.
    Cramér's V can still be subtracted when the shape changes.
    """

    first: GroupingVocabulary
    second: GroupingVocabulary
    reference_shape: Tuple[int, int]
    comparison_shape: Tuple[int, int]
    status: VocabularyStatus

    def __post_init__(self) -> None:
        _require_type(self.first, GroupingVocabulary, "first")
        _require_type(self.second, GroupingVocabulary, "second")
        _require_type(self.status, VocabularyStatus, "status")
        _require_shape(self.reference_shape, "reference_shape")
        _require_shape(self.comparison_shape, "comparison_shape")
        if self.reference_shape != (
            self.first.reference_n_levels,
            self.second.reference_n_levels,
        ):
            raise ValueError("reference shape must match the two level counts")
        if self.comparison_shape != (
            self.first.comparison_n_levels,
            self.second.comparison_n_levels,
        ):
            raise ValueError("comparison shape must match the two level counts")
        changed = (
            self.first.status is VocabularyStatus.CHANGED
            or self.second.status is VocabularyStatus.CHANGED
        )
        if changed is not (self.status is VocabularyStatus.CHANGED):
            raise ValueError("contingency vocabulary follows the two axes")


@dataclass(frozen=True)
class PearsonCorrelationChangeTest:
    """Complementary test that two Pearson correlations are equal.

    The statistic is the Fisher z difference. ``p_value`` belongs to that
    statistic. It is not a within-dataset correlation p-value, and it is
    not adjusted: this test is not a primary relationship-change family.
    Spearman rho is not the parameter under the null.
    """

    availability: ResultAvailability
    statistic: Optional[float]
    p_value: Optional[float]
    null: Optional[PearsonChangeNull]
    assumptions: Tuple[PearsonChangeAssumption, ...]
    reason: Optional[PearsonChangeReason]

    def __post_init__(self) -> None:
        _require_type(self.availability, ResultAvailability, "availability")
        if not isinstance(self.assumptions, tuple):
            raise TypeError("assumptions must be a tuple")
        if self.availability is ResultAvailability.AVAILABLE:
            if type(self.statistic) is not float or not math.isfinite(self.statistic):
                raise ValueError("statistic must be a finite float")
            if self.statistic == 0.0 and math.copysign(1.0, self.statistic) < 0.0:
                raise ValueError("statistic must not be negative zero")
            _require_probability(self.p_value)
            if self.null is not PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS:
                raise ValueError("the Pearson change null is equality of correlations")
            if self.assumptions != PEARSON_CHANGE_ASSUMPTIONS:
                raise ValueError("the Pearson change test names its assumptions")
            if self.reason is not None:
                raise ValueError("an available Pearson change test has no reason")
            return
        if (
            self.statistic is not None
            or self.p_value is not None
            or self.null is not None
            or self.assumptions
        ):
            raise ValueError("an unavailable Pearson change test has no result")
        _require_type(self.reason, PearsonChangeReason, "reason")


@dataclass(frozen=True)
class RelationshipDrift:
    """Change between one aligned relationship and its counterpart.

    ``primary`` exists only for the same implemented family. Complementary
    changes use the same rule. A family transition does not subtract
    effects. A formal Pearson change test exists only for a numeric pair
    that stayed numeric. Category-vocabulary diagnostics qualify a
    same-family categorical effect. They do not replace it.
    """

    alignment: RelationshipPairAlignment
    status: RelationshipPairStatus
    reference: RelationshipSide
    comparison: RelationshipSide
    primary: Optional[EffectChange] = None
    complementary: Tuple[EffectChange, ...] = ()
    grouping_vocabulary: Optional[GroupingVocabulary] = None
    contingency_vocabulary: Optional[ContingencyVocabulary] = None
    pearson_change_test: Optional[PearsonCorrelationChangeTest] = None

    def __post_init__(self) -> None:
        _require_type(self.alignment, RelationshipPairAlignment, "alignment")
        _require_type(self.status, RelationshipPairStatus, "status")
        _require_type(self.reference, RelationshipSide, "reference")
        _require_type(self.comparison, RelationshipSide, "comparison")
        if (
            self.reference.kind is RelationshipSideKind.INELIGIBLE
            and self.comparison.kind is RelationshipSideKind.INELIGIBLE
        ):
            raise ValueError("two ineligible sides are not a relationship record")
        if self.status is not pair_status(self.reference, self.comparison):
            raise ValueError("pair status must follow the two sides")
        _require_optional(self.primary, EffectChange, "primary")
        if not isinstance(self.complementary, tuple):
            raise TypeError("complementary must be a tuple")
        for item in self.complementary:
            _require_type(item, EffectChange, "complementary")
        _require_optional(
            self.grouping_vocabulary, GroupingVocabulary, "grouping_vocabulary"
        )
        _require_optional(
            self.contingency_vocabulary,
            ContingencyVocabulary,
            "contingency_vocabulary",
        )
        _require_optional(
            self.pearson_change_test,
            PearsonCorrelationChangeTest,
            "pearson_change_test",
        )
        _require_change_shape(self)


@dataclass(frozen=True)
class RelationshipDriftCoverage:
    """How many aligned pairs received each relationship-drift outcome.

    Counts describe the result. They are not a score. Effect-change
    counts cover same-family pairs only. Formal-test counts cover
    same-family numeric pairs only, because that is the only family with
    a change test.
    """

    n_aligned_pairs: int
    n_same_family: int
    n_family_transition: int
    n_unimplemented: int
    n_eligibility_transition: int
    n_effect_change_available: int
    n_effect_change_unavailable: int
    n_formal_change_tests: int
    n_formal_change_tests_unavailable: int
    n_numeric_numeric: int
    n_numeric_categorical: int
    n_numeric_boolean: int
    n_boolean_boolean: int
    n_categorical_categorical: int

    def __post_init__(self) -> None:
        for field in (
            "n_aligned_pairs",
            "n_same_family",
            "n_family_transition",
            "n_unimplemented",
            "n_eligibility_transition",
            "n_effect_change_available",
            "n_effect_change_unavailable",
            "n_formal_change_tests",
            "n_formal_change_tests_unavailable",
            "n_numeric_numeric",
            "n_numeric_categorical",
            "n_numeric_boolean",
            "n_boolean_boolean",
            "n_categorical_categorical",
        ):
            _require_count(getattr(self, field), field)
        classified = (
            self.n_same_family
            + self.n_family_transition
            + self.n_unimplemented
            + self.n_eligibility_transition
        )
        if classified != self.n_aligned_pairs:
            raise ValueError("relationship pair statuses must sum to aligned pairs")
        if (
            self.n_effect_change_available + self.n_effect_change_unavailable
            != self.n_same_family
        ):
            raise ValueError("effect changes must account for every same-family pair")
        if (
            self.n_numeric_numeric
            + self.n_numeric_categorical
            + self.n_numeric_boolean
            + self.n_boolean_boolean
            + self.n_categorical_categorical
            != self.n_same_family
        ):
            raise ValueError("same-family counts must sum to same-family pairs")
        if (
            self.n_formal_change_tests + self.n_formal_change_tests_unavailable
            != self.n_numeric_numeric
        ):
            raise ValueError("formal change tests must account for numeric pairs")


def pair_status(
    reference: RelationshipSide,
    comparison: RelationshipSide,
) -> RelationshipPairStatus:
    """Classify two sides. Both-ineligible is not a returned status."""
    if (
        reference.kind is RelationshipSideKind.INELIGIBLE
        or comparison.kind is RelationshipSideKind.INELIGIBLE
    ):
        return RelationshipPairStatus.ELIGIBILITY_TRANSITION
    if (
        reference.kind is RelationshipSideKind.UNIMPLEMENTED
        and comparison.kind is RelationshipSideKind.UNIMPLEMENTED
        and reference.unimplemented_family is comparison.unimplemented_family
    ):
        return RelationshipPairStatus.UNIMPLEMENTED
    if (
        reference.kind is RelationshipSideKind.CALCULATED
        and comparison.kind is RelationshipSideKind.CALCULATED
        and reference.family is comparison.family
    ):
        return RelationshipPairStatus.SAME_FAMILY
    return RelationshipPairStatus.FAMILY_TRANSITION


def coverage_from_relationships(
    relationships: Tuple[RelationshipDrift, ...],
) -> RelationshipDriftCoverage:
    """Count relationship-drift outcomes. Nothing is recalculated."""
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    status_counts = {status: 0 for status in RelationshipPairStatus}
    family_counts = {family: 0 for family in RelationshipFamily}
    n_available = 0
    n_unavailable = 0
    n_tests = 0
    n_tests_unavailable = 0
    for record in relationships:
        if not isinstance(record, RelationshipDrift):
            raise TypeError("relationships must contain RelationshipDrift records")
        status_counts[record.status] += 1
        if record.status is not RelationshipPairStatus.SAME_FAMILY:
            continue
        family = record.reference.family
        if family is None:
            raise ValueError("a same-family pair names its family")
        family_counts[family] += 1
        primary = record.primary
        if primary is None:
            raise ValueError("a same-family pair has a primary effect change")
        if primary.availability is ResultAvailability.AVAILABLE:
            n_available += 1
        else:
            n_unavailable += 1
        if family is RelationshipFamily.NUMERIC_NUMERIC:
            test = record.pearson_change_test
            if test is None:
                raise ValueError("a numeric pair has a Pearson change test")
            if test.availability is ResultAvailability.AVAILABLE:
                n_tests += 1
            else:
                n_tests_unavailable += 1
    return RelationshipDriftCoverage(
        n_aligned_pairs=len(relationships),
        n_same_family=status_counts[RelationshipPairStatus.SAME_FAMILY],
        n_family_transition=status_counts[RelationshipPairStatus.FAMILY_TRANSITION],
        n_unimplemented=status_counts[RelationshipPairStatus.UNIMPLEMENTED],
        n_eligibility_transition=status_counts[
            RelationshipPairStatus.ELIGIBILITY_TRANSITION
        ],
        n_effect_change_available=n_available,
        n_effect_change_unavailable=n_unavailable,
        n_formal_change_tests=n_tests,
        n_formal_change_tests_unavailable=n_tests_unavailable,
        n_numeric_numeric=family_counts[RelationshipFamily.NUMERIC_NUMERIC],
        n_numeric_categorical=family_counts[RelationshipFamily.NUMERIC_CATEGORICAL],
        n_numeric_boolean=family_counts[RelationshipFamily.NUMERIC_BOOLEAN],
        n_boolean_boolean=family_counts[RelationshipFamily.BOOLEAN_BOOLEAN],
        n_categorical_categorical=family_counts[
            RelationshipFamily.CATEGORICAL_CATEGORICAL
        ],
    )


def _payloads(side: RelationshipSide) -> Tuple[Tuple[str, object], ...]:
    items = (
        ("numeric_numeric", side.numeric_numeric),
        ("numeric_categorical", side.numeric_categorical),
        ("numeric_boolean", side.numeric_boolean),
        ("boolean_boolean", side.boolean_boolean),
        ("categorical_categorical", side.categorical_categorical),
    )
    return tuple(item for item in items if item[1] is not None)


_PAYLOAD_FIELD = {
    RelationshipFamily.NUMERIC_NUMERIC: "numeric_numeric",
    RelationshipFamily.NUMERIC_CATEGORICAL: "numeric_categorical",
    RelationshipFamily.NUMERIC_BOOLEAN: "numeric_boolean",
    RelationshipFamily.BOOLEAN_BOOLEAN: "boolean_boolean",
    RelationshipFamily.CATEGORICAL_CATEGORICAL: "categorical_categorical",
}
_PAYLOAD_TYPE = {
    RelationshipFamily.NUMERIC_NUMERIC: NumericNumericState,
    RelationshipFamily.NUMERIC_CATEGORICAL: NumericCategoricalState,
    RelationshipFamily.NUMERIC_BOOLEAN: NumericBooleanState,
    RelationshipFamily.BOOLEAN_BOOLEAN: BooleanBooleanState,
    RelationshipFamily.CATEGORICAL_CATEGORICAL: CategoricalCategoricalState,
}


def _require_change_shape(record: RelationshipDrift) -> None:
    same = record.status is RelationshipPairStatus.SAME_FAMILY
    family = record.reference.family if same else None
    if same:
        if record.primary is None or family is None:
            raise ValueError("a same-family pair has a primary effect change")
        if record.primary.measure is not _PRIMARY_MEASURE[family]:
            raise ValueError("the primary measure must be that family's effect")
        _require_primary_values(record)
        expected = _COMPLEMENTARY_MEASURE.get(family)
        if expected is None:
            if record.complementary:
                raise ValueError("this family has no complementary change")
        elif len(record.complementary) != 1 or (
            record.complementary[0].measure is not expected
        ):
            raise ValueError("the complementary measure must match the family")
        else:
            _require_complementary_values(record)
    elif record.primary is not None or record.complementary:
        raise ValueError("only a same-family pair compares effects")
    if family is RelationshipFamily.NUMERIC_CATEGORICAL:
        if record.grouping_vocabulary is None:
            raise ValueError("a numeric-categorical pair records group vocabulary")
    elif record.grouping_vocabulary is not None:
        raise ValueError("group vocabulary belongs to a numeric-categorical pair")
    if family is RelationshipFamily.CATEGORICAL_CATEGORICAL:
        if record.contingency_vocabulary is None:
            raise ValueError("a categorical pair records contingency vocabulary")
    elif record.contingency_vocabulary is not None:
        raise ValueError("contingency vocabulary belongs to a categorical pair")
    if family is RelationshipFamily.NUMERIC_NUMERIC:
        if record.pearson_change_test is None:
            raise ValueError("a numeric pair records the Pearson change test")
        return
    if record.pearson_change_test is not None:
        raise ValueError("the Pearson change test belongs to a numeric pair")


def _require_primary_values(record: RelationshipDrift) -> None:
    primary = record.primary
    reference = record.reference.payload()
    comparison = record.comparison.payload()
    if not isinstance(reference, _PAYLOAD_TYPE[record.reference.family]):  # type: ignore[index]
        raise ValueError("primary values must come from the reference payload")
    if not isinstance(comparison, _PAYLOAD_TYPE[record.comparison.family]):  # type: ignore[index]
        raise ValueError("primary values must come from the comparison payload")
    reference_value, comparison_value = _primary_pair(reference, comparison)
    if primary.reference != reference_value or primary.comparison != comparison_value:  # type: ignore[union-attr]
        raise ValueError("primary change must copy the two retained effects")


def _primary_pair(
    reference: object, comparison: object
) -> Tuple[Optional[float], Optional[float]]:
    if isinstance(reference, NumericNumericState):
        return reference.spearman, comparison.spearman  # type: ignore[attr-defined]
    if isinstance(reference, NumericCategoricalState):
        return reference.eta_squared, comparison.eta_squared  # type: ignore[attr-defined]
    if isinstance(reference, NumericBooleanState):
        return reference.hedges_g, comparison.hedges_g  # type: ignore[attr-defined]
    if isinstance(reference, BooleanBooleanState):
        return reference.phi, comparison.phi  # type: ignore[attr-defined]
    return reference.cramers_v, comparison.cramers_v  # type: ignore[attr-defined]


def _require_complementary_values(record: RelationshipDrift) -> None:
    change = record.complementary[0]
    reference = record.reference.payload()
    comparison = record.comparison.payload()
    if isinstance(reference, NumericNumericState):
        if change.reference != reference.pearson or change.comparison != comparison.pearson:  # type: ignore[attr-defined]
            raise ValueError("Pearson change must copy the two Pearson correlations")
        return
    if isinstance(reference, NumericBooleanState):
        if (
            change.reference != reference.mean_difference
            or change.comparison != comparison.mean_difference  # type: ignore[attr-defined]
        ):
            raise ValueError("mean-difference change must copy the two differences")
        return
    if not isinstance(reference, BooleanBooleanState):
        raise ValueError("this family has no complementary change")
    shared = reference.conditioning_is_first is comparison.conditioning_is_first  # type: ignore[attr-defined]
    if shared:
        if (
            change.reference != reference.probability_difference
            or change.comparison != comparison.probability_difference  # type: ignore[attr-defined]
        ):
            raise ValueError(
                "probability-difference change must copy the shared contrast"
            )
        return
    if change.reason is not EffectChangeReason.ORIENTATION_NOT_SHARED:
        raise ValueError("a flipped conditioning role is not one probability contrast")


def _require_effect(
    value: Optional[float],
    reason: Optional[UnavailabilityReason],
    measure: RelationshipChangeMeasure,
    field: str,
) -> None:
    if value is None:
        _require_type(reason, UnavailabilityReason, field)
        return
    if reason is not None:
        raise ValueError(f"an available {field} has no unavailability reason")
    _require_measure_value(value, measure, field)


def _require_optional_effect(
    value: Optional[float],
    measure: RelationshipChangeMeasure,
    field: str,
) -> None:
    if value is not None:
        _require_measure_value(value, measure, field)


def _require_measure_value(
    value: float,
    measure: RelationshipChangeMeasure,
    field: str,
) -> None:
    if measure in _BOUNDED_UNIT:
        _require_unit_interval(value, field)
        return
    if measure in _CLOSED_CORRELATION:
        _require_closed_interval(value, -1.0, 1.0, field)
        return
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


def _require_signed_companions(
    change: EffectChange,
    signed: bool,
    *,
    both_values: bool,
) -> None:
    if not signed:
        if change.magnitude_change is not None or change.sign_reversal is not None:
            raise ValueError("an unsigned effect has no magnitude change or reversal")
        return
    if not both_values:
        if change.magnitude_change is not None or change.sign_reversal is not None:
            raise ValueError("magnitude change and reversal need both signed effects")
        return
    expected_magnitude = _finite_difference(
        abs(change.comparison),  # type: ignore[arg-type]
        abs(change.reference),  # type: ignore[arg-type]
    )
    if change.magnitude_change != expected_magnitude:
        raise ValueError("magnitude change must be the absolute-value difference")
    expected_reversal = _sign_reversal(
        change.reference,  # type: ignore[arg-type]
        change.comparison,  # type: ignore[arg-type]
    )
    if change.sign_reversal is not expected_reversal:
        raise ValueError("sign reversal must follow the two nonzero signs")


def _sign_reversal(reference: float, comparison: float) -> bool:
    if reference == 0.0 or comparison == 0.0:
        return False
    return (reference > 0.0) != (comparison > 0.0)


def _finite_difference(comparison: float, reference: float) -> Optional[float]:
    change = comparison - reference
    if change == 0.0:
        return 0.0
    if not math.isfinite(change):
        return None
    return change


def _require_levels(levels: object, field: str) -> None:
    if not isinstance(levels, tuple):
        raise TypeError(f"{field} must be a tuple")
    for level in levels:
        _require_category_scalar(level)


def _require_shape(shape: object, field: str) -> None:
    if not (isinstance(shape, tuple) and len(shape) == 2):
        raise TypeError(f"{field} must be a pair of counts")
    _require_count(shape[0], field)
    _require_count(shape[1], field)


def _require_probability(value: Optional[float]) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("p_value must be a finite float")
    if value < 0.0 or value > 1.0:
        raise ValueError("p_value must lie on [0, 1]")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError("p_value must not be negative zero")
