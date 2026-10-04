"""Boolean × Boolean relationship records.

These records retain the 2×2 table, the directional probability
effects, phi, and the Fisher exact evidence. They do not calculate
those facts and they do not import a statistical library.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pytics.analysis.relationships.models.common import FrequentistEvidence
from pytics.analysis.relationships.models.common import MultipleTestingAdjustment
from pytics.analysis.relationships.models.common import RelationshipFamily
from pytics.analysis.relationships.models.common import ResultAvailability
from pytics.analysis.relationships.models.common import UnavailabilityReason
from pytics.analysis.relationships.models.common import _require_canonical_positions
from pytics.analysis.relationships.models.common import _require_closed_interval
from pytics.analysis.relationships.models.common import _require_enum
from pytics.analysis.relationships.models.common import _require_nonnegative
from pytics.analysis.relationships.models.common import _require_nonnegative_float
from pytics.analysis.relationships.models.common import _require_population_counts
from pytics.analysis.relationships.models.common import _require_position
from pytics.analysis.relationships.models.common import _require_reason
from pytics.analysis.relationships.models.common import _require_type
from pytics.analysis.relationships.models.common import _require_unit_interval

# A conditional probability is undefined when its conditioning level was
# not observed. A probability ratio can also be an exact 0/0 or an exact
# infinity. Those ratio states are not correlation failures.
_CONDITIONAL_PROBABILITY_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
    }
)
_PROBABILITY_DIFFERENCE_REASONS = _CONDITIONAL_PROBABILITY_REASONS | {
    UnavailabilityReason.NON_FINITE_RESULT,
}
_PROBABILITY_RATIO_REASONS = _PROBABILITY_DIFFERENCE_REASONS | {
    UnavailabilityReason.MATHEMATICALLY_UNBOUNDED,
    UnavailabilityReason.UNDEFINED_RATIO,
}
# Phi and the exact independence test both need variation in each
# variable. A non-finite library p-value uses the shared numerical reason.
_BOOLEAN_MARGINAL_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        UnavailabilityReason.NON_FINITE_RESULT,
    }
)


class BooleanLevel(Enum):
    """One logical Boolean value.

    False precedes True. This is not a display label and not source order.
    """

    FALSE = "false"
    TRUE = "true"


class BooleanBooleanPopulation(Enum):
    """Rows that enter a Boolean × Boolean relationship.

    Both source values are non-missing Boolean values. This is not the
    pairwise finite numeric rule.
    """

    PAIRWISE_NON_MISSING_BOOLEAN = "pairwise_non_missing_boolean"


class BooleanDirectionalMethod(Enum):
    """Directional observed-probability effect for Boolean × Boolean.

    The conditioning variable is the left physical column. The outcome
    variable is the right physical column. Neither role is a cause.
    """

    PROBABILITY_DIFFERENCE = "probability_difference"
    PROBABILITY_RATIO = "probability_ratio"


class BooleanAssociationMethod(Enum):
    """Symmetric association for two Boolean variables.

    Phi does not depend on which variable is the conditioning variable.
    """

    PHI = "phi"


class BooleanIndependenceMethod(Enum):
    """Frequentist independence test for a 2×2 Boolean table.

    Fisher's exact test is conditional on the observed margins. It is
    not an omnibus ANOVA and not a chi-square test.
    """

    FISHER_EXACT = "fisher_exact"


@dataclass(frozen=True)
class BooleanContingencyTable:
    """Observed 2×2 counts for one Boolean pair.

    The first index is the conditioning value. The second is the outcome
    value. False precedes True on both axes. All four cells are stored,
    including zeros. Marginal counts are the sums of these cells.
    """

    conditioning_false_outcome_false: int
    conditioning_false_outcome_true: int
    conditioning_true_outcome_false: int
    conditioning_true_outcome_true: int

    def __post_init__(self) -> None:
        _require_nonnegative(
            self.conditioning_false_outcome_false,
            "conditioning_false_outcome_false",
        )
        _require_nonnegative(
            self.conditioning_false_outcome_true,
            "conditioning_false_outcome_true",
        )
        _require_nonnegative(
            self.conditioning_true_outcome_false,
            "conditioning_true_outcome_false",
        )
        _require_nonnegative(
            self.conditioning_true_outcome_true,
            "conditioning_true_outcome_true",
        )

    @property
    def n_conditioning_false(self) -> int:
        """Paired rows whose conditioning value is False."""
        return (
            self.conditioning_false_outcome_false + self.conditioning_false_outcome_true
        )

    @property
    def n_conditioning_true(self) -> int:
        """Paired rows whose conditioning value is True."""
        return (
            self.conditioning_true_outcome_false + self.conditioning_true_outcome_true
        )

    @property
    def n_outcome_false(self) -> int:
        """Paired rows whose outcome value is False."""
        return (
            self.conditioning_false_outcome_false + self.conditioning_true_outcome_false
        )

    @property
    def n_outcome_true(self) -> int:
        """Paired rows whose outcome value is True."""
        return (
            self.conditioning_false_outcome_true + self.conditioning_true_outcome_true
        )


@dataclass(frozen=True)
class ConditionalOutcomeProbability:
    """Observed probability that the outcome is True at one conditioning level.

    ``value`` is that level's outcome-True count divided by the level's
    paired count, on ``[0, 1]``, when the level was observed. Zero events
    in an observed level are ``0.0``. An unobserved level is unavailable.
    It is not stored as zero.
    """

    conditioning_value: BooleanLevel
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.conditioning_value, BooleanLevel, "conditioning_value")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_unit_interval(self.value, "conditional probability")
            if self.reason is not None:
                raise ValueError(
                    "an available conditional probability has no unavailability reason"
                )
            return
        if self.value is not None:
            raise ValueError("an unavailable conditional probability has no value")
        _require_reason(self.reason, _CONDITIONAL_PROBABILITY_REASONS, "reason")


@dataclass(frozen=True)
class BooleanDirectionalEstimate:
    """One directional Boolean effect.

    Probability difference lies on ``[-1, 1]`` when available. Probability
    ratio is a finite value of at least zero when available. An exact
    infinite ratio is unavailable. It is not stored as a large finite
    number and not as infinity. ``reason`` is set only when the estimate
    is unavailable.
    """

    method: BooleanDirectionalMethod
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.method, BooleanDirectionalMethod, "method")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.method is BooleanDirectionalMethod.PROBABILITY_DIFFERENCE:
            allowed = _PROBABILITY_DIFFERENCE_REASONS
            if self.availability is ResultAvailability.AVAILABLE:
                _require_closed_interval(
                    self.value, -1.0, 1.0, "probability difference"
                )
        elif self.availability is ResultAvailability.AVAILABLE:
            allowed = _PROBABILITY_RATIO_REASONS
            _require_nonnegative_float(self.value, "probability ratio")
        else:
            allowed = _PROBABILITY_RATIO_REASONS
        if self.availability is ResultAvailability.AVAILABLE:
            if self.reason is not None:
                raise ValueError("an available effect has no unavailability reason")
            return
        if self.value is not None:
            raise ValueError("an unavailable effect has no value")
        _require_reason(self.reason, allowed, "reason")


@dataclass(frozen=True)
class BooleanAssociationEstimate:
    """Signed phi coefficient for one Boolean pair.

    ``value`` lies on ``[-1, 1]`` when both variables vary in the paired
    population. The sign follows False = 0 and True = 1. Swapping the two
    variables does not change that sign. A constant margin is unavailable,
    not zero.
    """

    method: BooleanAssociationMethod
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.method, BooleanAssociationMethod, "method")
        if self.method is not BooleanAssociationMethod.PHI:
            raise ValueError("the Boolean association method is phi")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_closed_interval(self.value, -1.0, 1.0, "phi")
            if self.reason is not None:
                raise ValueError(
                    "an available association has no unavailability reason"
                )
            return
        if self.value is not None:
            raise ValueError("an unavailable association has no value")
        _require_reason(self.reason, _BOOLEAN_MARGINAL_REASONS, "reason")


@dataclass(frozen=True)
class BooleanIndependenceTest:
    """Two-sided Fisher's exact test for one Boolean pair.

    ``frequentist`` holds the raw conditional p-value when every margin
    is positive. SciPy's odds-ratio statistic is not stored. A constant
    margin does not store the p-value ``1.0`` that the library returns
    for a degenerate table. ``adjusted_p_value`` stays absent.
    """

    method: BooleanIndependenceMethod
    frequentist: FrequentistEvidence

    def __post_init__(self) -> None:
        _require_enum(self.method, BooleanIndependenceMethod, "method")
        if self.method is not BooleanIndependenceMethod.FISHER_EXACT:
            raise ValueError("the Boolean independence method is Fisher's exact test")
        _require_type(self.frequentist, FrequentistEvidence, "frequentist")
        if self.frequentist.adjustment is not MultipleTestingAdjustment.NOT_APPLIED:
            raise ValueError("multiple-testing adjustment is not applied")
        if (
            self.frequentist.reason is not None
            and self.frequentist.reason not in _BOOLEAN_MARGINAL_REASONS
        ):
            raise ValueError(
                "independence p-value reason is not a Boolean margin reason"
            )


@dataclass(frozen=True)
class BooleanBooleanRelationship:
    """One selected Boolean × selected Boolean pair.

    ``left_position`` is less than ``right_position``. Both are physical
    positions. ``conditioning_position`` is that left position and
    ``outcome_position`` is that right position. Directional effects
    compare the outcome-True probability at conditioning True with the
    outcome-True probability at conditioning False. That assignment is a
    reporting orientation. It is not a causal order.

    ``n_paired`` counts rows where both Boolean values are non-missing.
    ``n_excluded`` is every other row. Missing Boolean values are not
    imputed and are not a third table level. ``table`` stores the four
    logical cells. The paired arrays are not stored.

    ``probability_difference`` and ``probability_ratio`` are directional.
    ``phi`` is symmetric. ``independence`` is the raw two-sided Fisher
    exact p-value. Those components do not share one availability flag.
    This record has no confidence interval and no strength label.
    """

    left_position: int
    left_label: object
    right_position: int
    right_label: object
    conditioning_position: int
    outcome_position: int
    n_total_rows: int
    n_paired: int
    table: BooleanContingencyTable
    outcome_true_given_conditioning_false: ConditionalOutcomeProbability
    outcome_true_given_conditioning_true: ConditionalOutcomeProbability
    probability_difference: BooleanDirectionalEstimate
    probability_ratio: BooleanDirectionalEstimate
    phi: BooleanAssociationEstimate
    independence: BooleanIndependenceTest

    def __post_init__(self) -> None:
        _require_canonical_positions(self.left_position, self.right_position)
        _require_position(self.conditioning_position, "conditioning_position")
        _require_position(self.outcome_position, "outcome_position")
        if self.conditioning_position != self.left_position:
            raise ValueError("conditioning role is the left physical column")
        if self.outcome_position != self.right_position:
            raise ValueError("outcome role is the right physical column")
        _require_population_counts(self.n_total_rows, self.n_paired)
        _require_type(self.table, BooleanContingencyTable, "table")
        _require_type(
            self.outcome_true_given_conditioning_false,
            ConditionalOutcomeProbability,
            "outcome_true_given_conditioning_false",
        )
        _require_type(
            self.outcome_true_given_conditioning_true,
            ConditionalOutcomeProbability,
            "outcome_true_given_conditioning_true",
        )
        if (
            self.outcome_true_given_conditioning_false.conditioning_value
            is not BooleanLevel.FALSE
        ):
            raise ValueError("the first conditional probability conditions on False")
        if (
            self.outcome_true_given_conditioning_true.conditioning_value
            is not BooleanLevel.TRUE
        ):
            raise ValueError("the second conditional probability conditions on True")
        _require_type(
            self.probability_difference,
            BooleanDirectionalEstimate,
            "probability_difference",
        )
        _require_type(
            self.probability_ratio,
            BooleanDirectionalEstimate,
            "probability_ratio",
        )
        if (
            self.probability_difference.method
            is not BooleanDirectionalMethod.PROBABILITY_DIFFERENCE
        ):
            raise ValueError("probability_difference must use that method")
        if (
            self.probability_ratio.method
            is not BooleanDirectionalMethod.PROBABILITY_RATIO
        ):
            raise ValueError("probability_ratio must use that method")
        _require_type(self.phi, BooleanAssociationEstimate, "phi")
        _require_type(self.independence, BooleanIndependenceTest, "independence")
        _require_boolean_boolean_components(self)

    @property
    def family(self) -> RelationshipFamily:
        """The implemented family this record belongs to."""
        return RelationshipFamily.BOOLEAN_BOOLEAN

    @property
    def population(self) -> BooleanBooleanPopulation:
        """Rows in which both Boolean values are non-missing."""
        return BooleanBooleanPopulation.PAIRWISE_NON_MISSING_BOOLEAN

    @property
    def n_excluded(self) -> int:
        """Rows that are not in the pairwise non-missing Boolean population.

        A row is excluded when either Boolean value is missing.
        """
        return self.n_total_rows - self.n_paired


def _require_boolean_boolean_components(
    relationship: BooleanBooleanRelationship,
) -> None:
    """Keep Boolean components consistent with the stored 2×2 counts.

    Counts determine which levels and margins exist. The constructor
    checks those states. It does not recompute phi or a p-value.
    """
    table = relationship.table
    n_ff = table.conditioning_false_outcome_false
    n_ft = table.conditioning_false_outcome_true
    n_tf = table.conditioning_true_outcome_false
    n_tt = table.conditioning_true_outcome_true
    if n_ff + n_ft + n_tf + n_tt != relationship.n_paired:
        raise ValueError("contingency counts must sum to n_paired")
    n_conditioning_false = n_ff + n_ft
    n_conditioning_true = n_tf + n_tt
    n_outcome_false = n_ff + n_tf
    n_outcome_true = n_ft + n_tt
    _require_conditional_count(
        relationship.outcome_true_given_conditioning_false,
        group=n_conditioning_false,
        events=n_ft,
        n_paired=relationship.n_paired,
    )
    _require_conditional_count(
        relationship.outcome_true_given_conditioning_true,
        group=n_conditioning_true,
        events=n_tt,
        n_paired=relationship.n_paired,
    )
    _require_probability_difference(
        relationship.probability_difference,
        n_conditioning_false=n_conditioning_false,
        n_conditioning_true=n_conditioning_true,
        n_ft=n_ft,
        n_tt=n_tt,
        n_paired=relationship.n_paired,
    )
    _require_probability_ratio(
        relationship.probability_ratio,
        n_conditioning_false=n_conditioning_false,
        n_conditioning_true=n_conditioning_true,
        n_ft=n_ft,
        n_tt=n_tt,
        n_paired=relationship.n_paired,
    )
    _require_phi_margins(
        relationship.phi,
        n_ff=n_ff,
        n_ft=n_ft,
        n_tf=n_tf,
        n_tt=n_tt,
        n_conditioning_false=n_conditioning_false,
        n_conditioning_true=n_conditioning_true,
        n_outcome_false=n_outcome_false,
        n_outcome_true=n_outcome_true,
        n_paired=relationship.n_paired,
    )
    _require_fisher_margins(
        relationship.independence,
        n_conditioning_false=n_conditioning_false,
        n_conditioning_true=n_conditioning_true,
        n_outcome_false=n_outcome_false,
        n_outcome_true=n_outcome_true,
        n_paired=relationship.n_paired,
    )


def _require_conditional_count(
    probability: ConditionalOutcomeProbability,
    *,
    group: int,
    events: int,
    n_paired: int,
) -> None:
    if n_paired == 0:
        _require_unavailable_component(
            probability.availability,
            probability.reason,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            "conditional probability",
        )
        return
    if group == 0:
        _require_unavailable_component(
            probability.availability,
            probability.reason,
            UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
            "conditional probability",
        )
        return
    if probability.availability is not ResultAvailability.AVAILABLE:
        raise ValueError("an observed conditioning level has a conditional probability")
    if events == 0:
        expected = 0.0
    elif events == group:
        expected = 1.0
    else:
        expected = events / group
    if probability.value != expected:
        raise ValueError("conditional probability must match the contingency counts")


def _require_probability_difference(
    estimate: BooleanDirectionalEstimate,
    *,
    n_conditioning_false: int,
    n_conditioning_true: int,
    n_ft: int,
    n_tt: int,
    n_paired: int,
) -> None:
    if n_paired == 0:
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            "probability difference",
        )
        return
    if n_conditioning_false == 0 or n_conditioning_true == 0:
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
            "probability difference",
        )
        return
    if n_tt * n_conditioning_false == n_ft * n_conditioning_true:
        if (
            estimate.availability is not ResultAvailability.AVAILABLE
            or estimate.value != 0.0
        ):
            raise ValueError(
                "equal conditional probabilities have probability difference 0"
            )
        return
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        if estimate.reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError(
                "a defined probability difference is unavailable only when non-finite"
            )


def _require_probability_ratio(
    estimate: BooleanDirectionalEstimate,
    *,
    n_conditioning_false: int,
    n_conditioning_true: int,
    n_ft: int,
    n_tt: int,
    n_paired: int,
) -> None:
    if n_paired == 0:
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            "probability ratio",
        )
        return
    if n_conditioning_false == 0 or n_conditioning_true == 0:
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
            "probability ratio",
        )
        return
    if n_ft == 0 and n_tt == 0:
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.UNDEFINED_RATIO,
            "probability ratio",
        )
        return
    if n_ft == 0:
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.MATHEMATICALLY_UNBOUNDED,
            "probability ratio",
        )
        return
    if n_tt == 0:
        if (
            estimate.availability is not ResultAvailability.AVAILABLE
            or estimate.value != 0.0
        ):
            raise ValueError("a zero outcome-True count has probability ratio 0")
        return
    if n_tt * n_conditioning_false == n_ft * n_conditioning_true:
        if (
            estimate.availability is not ResultAvailability.AVAILABLE
            or estimate.value != 1.0
        ):
            raise ValueError("equal conditional probabilities have probability ratio 1")
        return
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        if estimate.reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError(
                "a defined probability ratio is unavailable only when non-finite"
            )


def _require_phi_margins(
    estimate: BooleanAssociationEstimate,
    *,
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
    n_conditioning_false: int,
    n_conditioning_true: int,
    n_outcome_false: int,
    n_outcome_true: int,
    n_paired: int,
) -> None:
    if n_paired == 0:
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            "phi",
        )
        return
    margins = (
        n_conditioning_false,
        n_conditioning_true,
        n_outcome_false,
        n_outcome_true,
    )
    if any(margin == 0 for margin in margins):
        _require_unavailable_component(
            estimate.availability,
            estimate.reason,
            UnavailabilityReason.CONSTANT_PAIRED_VALUES,
            "phi",
        )
        return
    numerator = n_tt * n_ff - n_tf * n_ft
    if numerator == 0:
        if (
            estimate.availability is not ResultAvailability.AVAILABLE
            or estimate.value != 0.0
        ):
            raise ValueError("a zero phi numerator is phi 0")
        return
    if n_ft == 0 and n_tf == 0:
        if (
            estimate.availability is not ResultAvailability.AVAILABLE
            or estimate.value != 1.0
        ):
            raise ValueError("perfect agreement has phi 1")
        return
    if n_ff == 0 and n_tt == 0:
        if (
            estimate.availability is not ResultAvailability.AVAILABLE
            or estimate.value != -1.0
        ):
            raise ValueError("perfect disagreement has phi -1")
        return
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        if estimate.reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError("a defined phi is unavailable only when non-finite")


def _require_fisher_margins(
    test: BooleanIndependenceTest,
    *,
    n_conditioning_false: int,
    n_conditioning_true: int,
    n_outcome_false: int,
    n_outcome_true: int,
    n_paired: int,
) -> None:
    frequentist = test.frequentist
    if n_paired == 0:
        _require_unavailable_component(
            frequentist.availability,
            frequentist.reason,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            "independence test",
        )
        return
    margins = (
        n_conditioning_false,
        n_conditioning_true,
        n_outcome_false,
        n_outcome_true,
    )
    if any(margin == 0 for margin in margins):
        _require_unavailable_component(
            frequentist.availability,
            frequentist.reason,
            UnavailabilityReason.CONSTANT_PAIRED_VALUES,
            "independence test",
        )
        return
    if frequentist.availability is ResultAvailability.UNAVAILABLE:
        if frequentist.reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError(
                "a defined independence test is unavailable only when non-finite"
            )


def _require_unavailable_component(
    availability: ResultAvailability,
    reason: Optional[UnavailabilityReason],
    expected: UnavailabilityReason,
    field: str,
) -> None:
    if availability is not ResultAvailability.UNAVAILABLE or reason is not expected:
        raise ValueError(f"{field} must be unavailable because {expected.value}")
