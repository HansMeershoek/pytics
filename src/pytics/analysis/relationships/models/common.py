"""Shared relationship result vocabulary.

Availability, unavailability reasons, frequentist evidence, and the
calculated-family names are used by more than one family. Coverage
counts live beside the heterogeneous container. These models do not
calculate a statistic and they do not import a statistical library.
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
    """Multiple-testing status of a stored p-value.

    ``NOT_APPLIED`` means the raw p-value has no adjusted companion yet.
    """

    NOT_APPLIED = "not_applied"


@dataclass(frozen=True)
class FrequentistEvidence:
    """Raw frequentist evidence for one inferential result.

    A correlation test, a one-way ANOVA p-value, and a Boolean exact
    test all use this record.
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
