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


class MultipleTestingAdjustment(Enum):
    """What happened to one stored p-value.

    ``NOT_APPLIED`` means this p-value was not adjusted. That covers an
    unavailable p-value, which never enters a correction family, and an
    available complementary p-value that the correction policy leaves
    raw. It does not mean a correction was attempted and failed.

    ``BENJAMINI_HOCHBERG`` means this p-value was one available primary
    test in the exploratory family of the result that stores it, and it
    received that family's Benjamini–Hochberg adjustment. A relationship
    record belongs to the dataset-level relationship family. A
    distribution-drift record belongs to the univariate drift family of
    one dataset comparison. The two families are never pooled. The
    adjusted value is evidence about that same raw test. It is not a
    significance flag.
    """

    NOT_APPLIED = "not_applied"
    BENJAMINI_HOCHBERG = "benjamini_hochberg"


@dataclass(frozen=True)
class FrequentistEvidence:
    """Frequentist evidence for one inferential result.

    A correlation test, a one-way ANOVA p-value, a Boolean exact
    test, and a Pearson chi-square p-value all use this record.
    ``adjustment`` belongs to this result. It is not a dataset-wide
    correction status. ``NOT_APPLIED`` keeps ``adjusted_p_value`` empty.
    ``BENJAMINI_HOCHBERG`` stores the adjusted companion of this same
    raw p-value. An unavailable test is not adjusted. The p-value is
    not a significance flag.
    """

    availability: ResultAvailability
    p_value: Optional[float]
    adjusted_p_value: Optional[float]
    adjustment: MultipleTestingAdjustment
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        _require_enum(self.adjustment, MultipleTestingAdjustment, "adjustment")
        if self.availability is ResultAvailability.UNAVAILABLE:
            if self.p_value is not None:
                raise ValueError("an unavailable test has no p-value")
            if self.adjusted_p_value is not None:
                raise ValueError("an unavailable test has no adjusted p-value")
            if self.adjustment is not MultipleTestingAdjustment.NOT_APPLIED:
                raise ValueError("an unavailable test is not adjusted")
            _require_enum(self.reason, UnavailabilityReason, "reason")
            return
        _require_p_value(self.p_value)
        if self.reason is not None:
            raise ValueError("an available test has no unavailability reason")
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
