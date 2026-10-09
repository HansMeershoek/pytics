"""Shared relationship result vocabulary.

Availability, unavailability reasons, frequentist evidence, Boolean
levels, and the calculated-family names are used by more than one
family. Coverage counts live beside the heterogeneous container. These
models do not calculate a statistic and they do not import a
statistical library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet
from typing import Optional
from typing import Tuple


class RelationshipFamily(Enum):
    """Relationship family this version calculates.

    A member means the family is implemented. It does not mean one
    dataset contains a pair of that family. Families present in a
    dataset are the retained relationship records. Further families are
    not members until a calculation exists.
    """

    NUMERIC_NUMERIC = "numeric_numeric"
    NUMERIC_CATEGORICAL = "numeric_categorical"
    BOOLEAN_BOOLEAN = "boolean_boolean"
    NUMERIC_BOOLEAN = "numeric_boolean"
    CATEGORICAL_CATEGORICAL = "categorical_categorical"


class BooleanLevel(Enum):
    """One logical Boolean value.

    False precedes True. This is not a display label and not source order.
    """

    FALSE = "false"
    TRUE = "true"


class ResultAvailability(Enum):
    """Whether one statistical component has a value."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class UnavailabilityReason(Enum):
    """Why a component has no value.

    These are analytical states, not user-facing prose.
    ``CATEGORY_VOCABULARY_NOT_RETAINABLE`` means the physical category
    vocabulary could not be stored as itself. That pair keeps no category
    labels, and every statistical component of the pair uses this reason.
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
    CONDITIONING_LEVEL_ABSENT = "conditioning_level_absent"
    MATHEMATICALLY_UNBOUNDED = "mathematically_unbounded"
    UNDEFINED_RATIO = "undefined_ratio"
    BIAS_CORRECTION_UNDEFINED = "bias_correction_undefined"
    CATEGORY_VOCABULARY_NOT_RETAINABLE = "category_vocabulary_not_retainable"


class MultipleTestingAdjustment(Enum):
    """What happened to one stored p-value.

    ``NOT_APPLIED`` means this p-value was not adjusted. That covers an
    unavailable p-value, a computed p-value whose inferential validity
    failed, and an available complementary p-value that the correction
    policy leaves raw. It does not mean a correction was attempted and
    failed.

    ``BENJAMINI_HOCHBERG`` means this p-value was one inferentially valid
    primary test in the exploratory family of the result that stores it,
    and it received that family's Benjamini–Hochberg adjustment. A
    relationship record belongs to the dataset-level relationship family.
    A distribution-drift record belongs to the univariate drift family of
    one dataset comparison. The two families are never pooled. A
    complementary test that two Pearson correlations are equal is not a
    member of either family. The adjusted value is evidence about that
    same raw test. It is not a significance flag.
    """

    NOT_APPLIED = "not_applied"
    BENJAMINI_HOCHBERG = "benjamini_hochberg"


class InferentialValidity(Enum):
    """Whether a stored p-value may be read as inferential evidence.

    ``NOT_APPLICABLE`` means no p-value was computed.
    ``VALID`` means a p-value was computed and every validity gate
    required for its method passed. A method with no separate gate in
    this version is valid whenever its p-value is available.
    ``INVALID`` means a p-value was computed and a required gate failed.
    The raw number remains. It is not an ordinary inferential p-value,
    it does not enter a correction family, and it has no adjusted value.
    """

    NOT_APPLICABLE = "not_applicable"
    VALID = "valid"
    INVALID = "invalid"


class InferentialInvalidityReason(Enum):
    """Why a computed p-value is not inferentially valid.

    ``CHI_SQUARE_EXPECTED_COUNTS`` means Cochran's expected-count
    convention failed, or the expected-count diagnostics needed to
    apply that convention were not available. The computed chi-square
    tail is still stored on the p-value.
    """

    CHI_SQUARE_EXPECTED_COUNTS = "chi_square_expected_counts"


# Cochran (1954): no expected count below 1, and no more than 20% of
# expected counts below 5. The share is an exact integer comparison,
# ``5 * n_below_5 <= n_cells``, so one fifth of the cells passes.
_CHI_SQUARE_MINIMUM_EXPECTED_COUNT = 1.0
_CHI_SQUARE_LOW_EXPECTED_CELL_FACTOR = 5


def cochran_expected_counts_hold(
    *,
    minimum_expected_count: Optional[float],
    n_cells_expected_below_5: Optional[int],
    n_cells: int,
) -> bool:
    """Whether retained expected counts meet Cochran's chi-square convention."""
    if type(n_cells) is not int or n_cells < 1:
        return False
    if (
        type(minimum_expected_count) is not float
        or not math.isfinite(minimum_expected_count)
        or minimum_expected_count < _CHI_SQUARE_MINIMUM_EXPECTED_COUNT
    ):
        return False
    if type(n_cells_expected_below_5) is not int or n_cells_expected_below_5 < 0:
        return False
    return n_cells_expected_below_5 * _CHI_SQUARE_LOW_EXPECTED_CELL_FACTOR <= n_cells


def chi_square_inferential_status(
    *,
    diagnostics_available: bool,
    minimum_expected_count: Optional[float],
    n_cells_expected_below_5: Optional[int],
    n_cells: int,
) -> Tuple[InferentialValidity, Optional[InferentialInvalidityReason]]:
    """Validity of one computed asymptotic chi-square p-value.

    A missing diagnostic is not treated as valid. The returned reason
    is set only when the status is ``INVALID``.
    """
    if diagnostics_available and cochran_expected_counts_hold(
        minimum_expected_count=minimum_expected_count,
        n_cells_expected_below_5=n_cells_expected_below_5,
        n_cells=n_cells,
    ):
        return InferentialValidity.VALID, None
    return (
        InferentialValidity.INVALID,
        InferentialInvalidityReason.CHI_SQUARE_EXPECTED_COUNTS,
    )


def inferential_p_value_eligible(
    availability: ResultAvailability,
    inferential_validity: InferentialValidity,
) -> bool:
    """Whether one p-value may enter its correction family.

    The p-value must have been computed and its method's validity gates
    must have passed. A computed value whose assumptions failed is not
    eligible. An absent p-value is not eligible.
    """
    return (
        availability is ResultAvailability.AVAILABLE
        and inferential_validity is InferentialValidity.VALID
    )


@dataclass(frozen=True)
class FrequentistEvidence:
    """Frequentist evidence for one inferential result.

    A correlation test, a one-way ANOVA p-value, a Boolean exact
    test, and a Pearson chi-square p-value all use this record.
    ``availability`` says whether a raw p-value was computed. It does
    not say that the number is an inferential probability.
    ``inferential_validity`` makes that second distinction.
    ``adjustment`` belongs to this result. It is not a dataset-wide
    correction status. ``NOT_APPLIED`` keeps ``adjusted_p_value`` empty.
    ``BENJAMINI_HOCHBERG`` stores the adjusted companion of this same
    raw p-value and is allowed only when the p-value is inferentially
    valid. An unavailable test is not adjusted. The p-value is not a
    significance flag.

    Omitting ``inferential_validity`` means ``NOT_APPLICABLE`` when no
    p-value was computed and ``VALID`` when one was. Chi-square callers
    pass ``INVALID`` explicitly when Cochran's convention fails.
    """

    availability: ResultAvailability
    p_value: Optional[float]
    adjusted_p_value: Optional[float]
    adjustment: MultipleTestingAdjustment
    reason: Optional[UnavailabilityReason]
    inferential_validity: Optional[InferentialValidity] = None
    invalidity_reason: Optional[InferentialInvalidityReason] = None

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        _require_enum(self.adjustment, MultipleTestingAdjustment, "adjustment")
        _resolve_inferential_validity(self)
        if self.availability is ResultAvailability.UNAVAILABLE:
            if self.p_value is not None:
                raise ValueError("an unavailable test has no p-value")
            if self.adjusted_p_value is not None:
                raise ValueError("an unavailable test has no adjusted p-value")
            if self.adjustment is not MultipleTestingAdjustment.NOT_APPLIED:
                raise ValueError("an unavailable test is not adjusted")
            if self.inferential_validity is not InferentialValidity.NOT_APPLICABLE:
                raise ValueError("an unavailable test has no inferential p-value")
            if self.invalidity_reason is not None:
                raise ValueError("an unavailable test has no invalidity reason")
            _require_enum(self.reason, UnavailabilityReason, "reason")
            return
        _require_p_value(self.p_value)
        if self.reason is not None:
            raise ValueError("an available test has no unavailability reason")
        if self.inferential_validity is InferentialValidity.NOT_APPLICABLE:
            raise ValueError("a computed p-value has an inferential status")
        if self.inferential_validity is InferentialValidity.INVALID:
            _require_enum(
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
            return
        if self.inferential_validity is not InferentialValidity.VALID:
            raise ValueError("inferential validity is not recognized")
        if self.invalidity_reason is not None:
            raise ValueError("a valid p-value has no invalidity reason")
        if self.adjustment is MultipleTestingAdjustment.NOT_APPLIED:
            if self.adjusted_p_value is not None:
                raise ValueError("an unadjusted test has no adjusted p-value")
            return
        if self.adjustment is not MultipleTestingAdjustment.BENJAMINI_HOCHBERG:
            raise ValueError("adjustment is not a known correction")
        if self.adjusted_p_value is None:
            raise ValueError("an adjusted test has an adjusted p-value")
        _require_p_value(self.adjusted_p_value)
        if self.adjusted_p_value + 1e-12 < self.p_value:  # type: ignore[operator]
            raise ValueError("an adjusted p-value cannot be less than its raw p-value")


def _resolve_inferential_validity(evidence: FrequentistEvidence) -> None:
    """Fill an omitted status. An explicit status is left unchanged."""
    if evidence.inferential_validity is not None:
        _require_enum(
            evidence.inferential_validity,
            InferentialValidity,
            "inferential_validity",
        )
        return
    if evidence.invalidity_reason is not None:
        raise ValueError("an unspecified inferential status has no invalidity reason")
    validity = (
        InferentialValidity.NOT_APPLICABLE
        if evidence.availability is ResultAvailability.UNAVAILABLE
        else InferentialValidity.VALID
    )
    object.__setattr__(evidence, "inferential_validity", validity)


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


def _require_unavailable_component(
    availability: ResultAvailability,
    reason: Optional[UnavailabilityReason],
    expected: UnavailabilityReason,
    field: str,
) -> None:
    if availability is not ResultAvailability.UNAVAILABLE or reason is not expected:
        raise ValueError(f"{field} must be unavailable because {expected.value}")


def _require_nonnegative(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_closed_interval(
    value: Optional[float],
    lower: float,
    upper: float,
    field: str,
) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value < lower or value > upper:
        raise ValueError(f"{field} must lie on [{lower:g}, {upper:g}]")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


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
