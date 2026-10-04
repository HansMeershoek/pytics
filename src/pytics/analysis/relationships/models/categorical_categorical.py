"""Categorical × Categorical relationship records.

These records retain the observed contingency table, classical
Cramér's V, expected-count diagnostics, and the Pearson chi-square
test of independence. They do not calculate those facts and they do
not import a statistical library. Boolean × Boolean keeps its own 2×2
table. This is not a generic contingency model.
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
from pytics.analysis.relationships.models.common import _require_category_scalar
from pytics.analysis.relationships.models.common import _require_enum
from pytics.analysis.relationships.models.common import _require_nonnegative_float
from pytics.analysis.relationships.models.common import _require_population_counts
from pytics.analysis.relationships.models.common import _require_reason
from pytics.analysis.relationships.models.common import _require_type
from pytics.analysis.relationships.models.common import _require_unit_interval

# A constant paired margin has no association and no independence test.
# A non-finite chi-square removes V with it. A non-finite p-value does
# not remove a finite chi-square or a finite V.
_ASSOCIATION_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        UnavailabilityReason.NON_FINITE_RESULT,
    }
)
# Expected counts are defined for every non-empty table, including a
# table with one observed level. They are not an independence result.
_DIAGNOSTIC_REASONS = frozenset(
    {
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        UnavailabilityReason.NON_FINITE_RESULT,
    }
)


class CategoricalCategoricalPopulation(Enum):
    """Rows that enter a Categorical × Categorical relationship.

    Both source values are non-missing categories. A missing value is
    not a category.
    """

    PAIRWISE_NON_MISSING_CATEGORICAL = "pairwise_non_missing_categorical"


class CategoricalAxisOrder(Enum):
    """Order of both observed categorical axes.

    This is the physical categorical vocabulary with unused levels
    removed. It is not an ordinal score. Both axes use it. The left
    axis is the left physical column.
    """

    PHYSICAL_CATEGORICAL_VOCABULARY = "physical_categorical_vocabulary"


class CategoricalAssociationMethod(Enum):
    """Symmetric association for two categorical variables.

    This is classical Cramér's V. It is not a bias-corrected variant
    and it has no sign.
    """

    CRAMERS_V = "cramers_v"


class CategoricalIndependenceMethod(Enum):
    """Frequentist independence test for an observed contingency table.

    Pearson's chi-square without Yates's correction is the foundation
    for every table shape, including 2×2. It is not Fisher's exact test.
    """

    PEARSON_CHI_SQUARE = "pearson_chi_square"


@dataclass(frozen=True)
class CategoricalContingencyTable:
    """Observed counts for one categorical pair.

    Rows follow ``left_levels``. Columns follow ``right_levels``. Both
    sequences are the observed vocabulary order. A level with a zero
    paired margin is omitted, so no retained row or column is all zero.

    ``observed_counts`` stores only cells whose count is positive, as
    ``(left_index, right_index, count)``, in row-major order. Zero cells
    are not stored. Marginal totals still describe the full rectangle,
    including those zeros. The grand total is the sum of either margin.

    Counts are Python integers. This is not a DataFrame, and it is not
    one record per cell.
    """

    left_levels: Tuple[object, ...]
    right_levels: Tuple[object, ...]
    observed_counts: Tuple[Tuple[int, int, int], ...]
    left_totals: Tuple[int, ...]
    right_totals: Tuple[int, ...]

    def __post_init__(self) -> None:
        _require_level_axis(self.left_levels, self.left_totals, "left")
        _require_level_axis(self.right_levels, self.right_totals, "right")
        if not isinstance(self.observed_counts, tuple):
            raise TypeError("observed_counts must be a tuple")
        if not self.left_levels and not self.right_levels and not self.observed_counts:
            return
        if not self.left_levels or not self.right_levels:
            raise ValueError("a contingency axis cannot be empty on its own")
        _require_observed_cells(
            self.observed_counts,
            len(self.left_levels),
            len(self.right_levels),
            self.left_totals,
            self.right_totals,
        )

    @property
    def n_left_levels(self) -> int:
        """Observed left categories. Unused vocabulary levels are omitted."""
        return len(self.left_levels)

    @property
    def n_right_levels(self) -> int:
        """Observed right categories. Unused vocabulary levels are omitted."""
        return len(self.right_levels)

    @property
    def n_observed_cells(self) -> int:
        """Positive cells. This is not the product of the axis lengths."""
        return len(self.observed_counts)

    @property
    def grand_total(self) -> int:
        """Paired observations. Both margins sum to this count."""
        return sum(self.left_totals)


@dataclass(frozen=True)
class CategoricalAssociationEstimate:
    """Classical Cramér's V for one categorical pair.

    ``value`` lies on ``[0, 1]`` when the denominator is positive and the
    ratio is finite. It is unsigned. It is never NaN. ``reason`` is set
    only when V is unavailable. Unavailable is not stored as zero.
    """

    method: CategoricalAssociationMethod
    availability: ResultAvailability
    value: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.method, CategoricalAssociationMethod, "method")
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_unit_interval(self.value, "Cramér's V")
            if self.reason is not None:
                raise ValueError(
                    "an available association has no unavailability reason"
                )
            return
        if self.value is not None:
            raise ValueError("an unavailable association has no value")
        _require_reason(self.reason, _ASSOCIATION_REASONS, "reason")


@dataclass(frozen=True)
class ExpectedCountDiagnostics:
    """Compact diagnostics for the chi-square approximation.

    Expected counts are ``row_total * column_total / n``. They are not
    retained cell by cell. ``minimum_expected_count`` is the smallest of
    those values. The two reference points, 5 and 1, are the conventional
    Cochran checkpoints. A cell below one is also below five. The fraction
    uses the full rectangle, including observed zeros, as its denominator.

    These facts do not decide whether Pearson's test is available. An
    expected count below 5 is not a failed test.
    """

    availability: ResultAvailability
    minimum_expected_count: Optional[float]
    n_cells_expected_below_5: Optional[int]
    fraction_cells_expected_below_5: Optional[float]
    n_cells_expected_below_1: Optional[int]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_positive_expected(self.minimum_expected_count)
            _require_cell_count(
                self.n_cells_expected_below_5, "n_cells_expected_below_5"
            )
            _require_cell_count(
                self.n_cells_expected_below_1, "n_cells_expected_below_1"
            )
            _require_unit_interval(
                self.fraction_cells_expected_below_5,
                "fraction_cells_expected_below_5",
            )
            if self.n_cells_expected_below_1 > self.n_cells_expected_below_5:  # type: ignore[operator]
                raise ValueError("cells below 1 are included in cells below 5")
            if self.reason is not None:
                raise ValueError("available diagnostics have no unavailability reason")
            return
        if (
            self.minimum_expected_count is not None
            or self.n_cells_expected_below_5 is not None
            or self.fraction_cells_expected_below_5 is not None
            or self.n_cells_expected_below_1 is not None
        ):
            raise ValueError("unavailable diagnostics have no values")
        _require_reason(self.reason, _DIAGNOSTIC_REASONS, "reason")


@dataclass(frozen=True)
class CategoricalIndependenceTest:
    """Pearson chi-square test of independence.

    ``statistic`` is the uncorrected Pearson statistic. ``degrees_of_freedom``
    is ``(r - 1) * (c - 1)`` for the observed levels when that statistic
    exists. Yates's correction is not used, including for a 2×2 table.
    ``frequentist`` holds the upper-tail chi-square p-value. The
    calculator stores that raw p-value. Dataset-level correction may
    later set the adjusted companion of the same test. The statistic
    and the p-value do not share one availability flag: a non-finite
    tail does not erase a finite statistic. The p-value is not a
    significance flag.
    """

    method: CategoricalIndependenceMethod
    statistic_availability: ResultAvailability
    statistic: Optional[float]
    degrees_of_freedom: Optional[int]
    statistic_reason: Optional[UnavailabilityReason]
    frequentist: FrequentistEvidence

    def __post_init__(self) -> None:
        _require_enum(self.method, CategoricalIndependenceMethod, "method")
        _require_enum(
            self.statistic_availability,
            ResultAvailability,
            "statistic_availability",
        )
        _require_type(self.frequentist, FrequentistEvidence, "frequentist")
        if (
            self.frequentist.reason is not None
            and self.frequentist.reason not in _ASSOCIATION_REASONS
        ):
            raise ValueError("chi-square p-value reason is not an independence reason")
        if self.statistic_availability is ResultAvailability.AVAILABLE:
            _require_nonnegative_float(self.statistic, "chi-square statistic")
            _require_degrees_of_freedom(self.degrees_of_freedom)
            if self.statistic_reason is not None:
                raise ValueError("an available chi-square has no unavailability reason")
            if self.frequentist.availability is ResultAvailability.UNAVAILABLE:
                if (
                    self.frequentist.reason
                    is not UnavailabilityReason.NON_FINITE_RESULT
                ):
                    raise ValueError(
                        "a defined chi-square loses its p-value only when that tail is not finite"
                    )
            return
        if self.statistic is not None or self.degrees_of_freedom is not None:
            raise ValueError(
                "an unavailable chi-square has no statistic or degrees of freedom"
            )
        _require_reason(self.statistic_reason, _ASSOCIATION_REASONS, "statistic_reason")
        if self.frequentist.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("an unavailable chi-square has no p-value")
        if self.frequentist.reason is not self.statistic_reason:
            raise ValueError("an unavailable chi-square and its p-value share a reason")


@dataclass(frozen=True)
class CategoricalCategoricalRelationship:
    """One selected Categorical × selected Categorical pair.

    ``left_position`` is less than ``right_position``. Both are physical
    positions. The left categorical axis is that left column and the
    right categorical axis is that right column. Neither is a predictor,
    an outcome, or a cause. Swapping the columns transposes the table.
    Cramér's V and Pearson's chi-square do not depend on that swap.

    ``n_paired`` counts rows where both categorical values are
    non-missing. ``n_excluded`` is every other row. Missing values are
    not imputed and are not a table level. ``table`` stores the observed
    positive cells and both margins. The paired codes are not stored.

    ``association`` is classical Cramér's V. ``expected_counts`` diagnoses
    the chi-square approximation without storing every expected cell.
    ``independence`` is Pearson's chi-square test. Those components do
    not share one availability flag. This record has no sign, no
    confidence interval, and no strength label.
    """

    left_position: int
    left_label: object
    right_position: int
    right_label: object
    n_total_rows: int
    n_paired: int
    table: CategoricalContingencyTable
    association: CategoricalAssociationEstimate
    expected_counts: ExpectedCountDiagnostics
    independence: CategoricalIndependenceTest

    def __post_init__(self) -> None:
        _require_canonical_positions(self.left_position, self.right_position)
        _require_population_counts(self.n_total_rows, self.n_paired)
        _require_type(self.table, CategoricalContingencyTable, "table")
        _require_type(self.association, CategoricalAssociationEstimate, "association")
        _require_type(self.expected_counts, ExpectedCountDiagnostics, "expected_counts")
        _require_type(self.independence, CategoricalIndependenceTest, "independence")
        if self.table.grand_total != self.n_paired:
            raise ValueError("contingency grand total must equal n_paired")
        _require_categorical_components(self)

    @property
    def family(self) -> RelationshipFamily:
        """The implemented family this record belongs to."""
        return RelationshipFamily.CATEGORICAL_CATEGORICAL

    @property
    def population(self) -> CategoricalCategoricalPopulation:
        """Rows in which both categorical values are non-missing."""
        return CategoricalCategoricalPopulation.PAIRWISE_NON_MISSING_CATEGORICAL

    @property
    def axis_order(self) -> CategoricalAxisOrder:
        """Vocabulary order of both observed axes. Not an ordinal score."""
        return CategoricalAxisOrder.PHYSICAL_CATEGORICAL_VOCABULARY

    @property
    def n_excluded(self) -> int:
        """Rows that are not in the pairwise non-missing categorical population.

        A row is excluded when either categorical value is missing.
        """
        return self.n_total_rows - self.n_paired


def _require_level_axis(
    levels: object,
    totals: object,
    side: str,
) -> None:
    if not isinstance(levels, tuple):
        raise TypeError(f"{side}_levels must be a tuple")
    if not isinstance(totals, tuple):
        raise TypeError(f"{side}_totals must be a tuple")
    if len(levels) != len(totals):
        raise ValueError(f"{side} totals must match the {side} levels")
    for level in levels:
        _require_category_scalar(level)
    for total in totals:
        if type(total) is not int or total < 1:
            raise ValueError(
                f"every retained {side} level has a positive marginal count"
            )


def _require_observed_cells(
    cells: Tuple[Tuple[int, int, int], ...],
    n_left: int,
    n_right: int,
    left_totals: Tuple[int, ...],
    right_totals: Tuple[int, ...],
) -> None:
    left_sums = [0] * n_left
    right_sums = [0] * n_right
    previous = (-1, -1)
    for cell in cells:
        if type(cell) is not tuple or len(cell) != 3:
            raise TypeError(
                "an observed cell must be a left index, right index, and count"
            )
        left_index, right_index, count = cell
        if (
            type(left_index) is not int
            or type(right_index) is not int
            or type(count) is not int
        ):
            raise TypeError("an observed cell must contain Python integers")
        if count < 1:
            raise ValueError("observed cells store positive counts only")
        if left_index < 0 or left_index >= n_left:
            raise ValueError("observed left index is outside the left axis")
        if right_index < 0 or right_index >= n_right:
            raise ValueError("observed right index is outside the right axis")
        key = (left_index, right_index)
        if key <= previous:
            raise ValueError("observed cells must be unique and in row-major order")
        previous = key
        left_sums[left_index] += count
        right_sums[right_index] += count
    if tuple(left_sums) != left_totals or tuple(right_sums) != right_totals:
        raise ValueError("marginal totals must equal the observed cells")


def _require_positive_expected(value: Optional[float]) -> None:
    if type(value) is not float or not math.isfinite(value) or value <= 0.0:
        raise ValueError("minimum expected count must be a positive finite float")


def _require_cell_count(value: Optional[int], field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_degrees_of_freedom(value: Optional[int]) -> None:
    if type(value) is not int or value < 1:
        raise ValueError("degrees of freedom must be a positive int")


def _require_categorical_components(
    relationship: CategoricalCategoricalRelationship,
) -> None:
    """Keep degenerate tables, V, and the chi-square tail distinct.

    No paired rows, and a paired margin with one observed level, have
    fixed reasons. A defined chi-square may still have an undefined V
    or an undefined p-value when that number is not finite. An undefined
    chi-square removes both.
    """
    table = relationship.table
    n_left = table.n_left_levels
    n_right = table.n_right_levels
    n_paired = relationship.n_paired
    association = relationship.association
    independence = relationship.independence
    diagnostics = relationship.expected_counts
    if n_paired == 0:
        _require_same_reason(
            association,
            independence,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        )
        _require_diagnostic_reason(
            diagnostics,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        )
        return
    if n_left < 2 or n_right < 2:
        _require_same_reason(
            association,
            independence,
            UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    else:
        _require_defined_chi_square(association, independence, n_left, n_right)
    _require_diagnostics_for_populated_table(diagnostics, n_left, n_right)


def _require_same_reason(
    association: CategoricalAssociationEstimate,
    independence: CategoricalIndependenceTest,
    reason: UnavailabilityReason,
) -> None:
    if (
        association.availability is not ResultAvailability.UNAVAILABLE
        or association.reason is not reason
    ):
        raise ValueError(f"association must be unavailable because {reason.value}")
    if (
        independence.statistic_availability is not ResultAvailability.UNAVAILABLE
        or independence.statistic_reason is not reason
    ):
        raise ValueError(f"chi-square must be unavailable because {reason.value}")


def _require_diagnostic_reason(
    diagnostics: ExpectedCountDiagnostics,
    reason: UnavailabilityReason,
) -> None:
    if (
        diagnostics.availability is not ResultAvailability.UNAVAILABLE
        or diagnostics.reason is not reason
    ):
        raise ValueError(
            f"expected-count diagnostics must be unavailable because {reason.value}"
        )


def _require_defined_chi_square(
    association: CategoricalAssociationEstimate,
    independence: CategoricalIndependenceTest,
    n_left: int,
    n_right: int,
) -> None:
    if independence.statistic_availability is ResultAvailability.UNAVAILABLE:
        if independence.statistic_reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError(
                "a non-degenerate table loses chi-square only when it is not finite"
            )
        if (
            association.availability is not ResultAvailability.UNAVAILABLE
            or association.reason is not UnavailabilityReason.NON_FINITE_RESULT
        ):
            raise ValueError("an undefined chi-square has no Cramér's V")
        return
    expected = (n_left - 1) * (n_right - 1)
    if independence.degrees_of_freedom != expected:
        raise ValueError("degrees of freedom must be (r - 1) * (c - 1)")
    if association.availability is ResultAvailability.UNAVAILABLE:
        if association.reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError(
                "a defined chi-square leaves V unavailable only when that value is not finite"
            )


def _require_diagnostics_for_populated_table(
    diagnostics: ExpectedCountDiagnostics,
    n_left: int,
    n_right: int,
) -> None:
    if diagnostics.availability is ResultAvailability.UNAVAILABLE:
        if diagnostics.reason is not UnavailabilityReason.NON_FINITE_RESULT:
            raise ValueError(
                "a populated table loses expected-count diagnostics only when they are not finite"
            )
        return
    n_cells = n_left * n_right
    below_5 = diagnostics.n_cells_expected_below_5
    if below_5 is None or below_5 > n_cells:
        raise ValueError("cells below 5 cannot exceed the contingency rectangle")
