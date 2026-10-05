"""Directional value records shared by every comparison layer.

A directional number is ``comparison - reference`` when that difference
is defined. There is no percent change and no tolerance. ``None`` is not
zero. These records hold Python scalars only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional
from typing import Union

MetricNumber = Union[int, float, Fraction]


@dataclass(frozen=True)
class CountComparison:
    """One non-negative integer on each side.

    ``change`` is ``comparison - reference``. It is exact.
    """

    reference: int
    comparison: int

    def __post_init__(self) -> None:
        _require_count(self.reference, "reference")
        _require_count(self.comparison, "comparison")

    @property
    def change(self) -> int:
        """``comparison - reference``."""
        return self.comparison - self.reference


@dataclass(frozen=True)
class OptionalCountComparison:
    """One integer that may be absent on either side.

    ``change`` is ``None`` when either side is absent. ``None`` is not
    zero.
    """

    reference: Optional[int]
    comparison: Optional[int]

    def __post_init__(self) -> None:
        if self.reference is not None:
            _require_count(self.reference, "reference")
        if self.comparison is not None:
            _require_count(self.comparison, "comparison")

    @property
    def change(self) -> Optional[int]:
        """``comparison - reference``, or ``None`` when either side is absent."""
        if self.reference is None or self.comparison is None:
            return None
        return self.comparison - self.reference


@dataclass(frozen=True)
class ProportionDifference:
    """One proportion on each side.

    ``change`` is the float difference ``comparison - reference`` when
    both proportions exist and that difference is finite. There is no
    percent change and no tolerance. ``None`` is not zero.
    """

    reference: Optional[float]
    comparison: Optional[float]

    def __post_init__(self) -> None:
        _require_optional_proportion(self.reference, "reference")
        _require_optional_proportion(self.comparison, "comparison")

    @property
    def change(self) -> Optional[float]:
        """``comparison - reference`` when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return _finite_float_difference(self.comparison, self.reference)


@dataclass(frozen=True)
class NumericDifference:
    """One retained numeric fact on each side.

    ``change`` is ``comparison - reference`` when that difference can be
    represented without rounding a float subtraction to infinity and
    without collapsing an exact integer or fraction. Otherwise ``change``
    is ``None``. Both side values stay stored either way. ``None`` is not
    zero and not NaN.
    """

    reference: Optional[MetricNumber]
    comparison: Optional[MetricNumber]

    def __post_init__(self) -> None:
        _require_metric(self.reference, "reference")
        _require_metric(self.comparison, "comparison")

    @property
    def change(self) -> Optional[MetricNumber]:
        """``comparison - reference`` under the numeric-change contract."""
        return directional_difference(self.comparison, self.reference)


def directional_difference(
    comparison: Optional[MetricNumber],
    reference: Optional[MetricNumber],
) -> Optional[MetricNumber]:
    """Return ``comparison - reference`` when the difference is safe.

    Two integers, or an integer and a fraction, stay exact. Two finite
    floats use float subtraction, and a non-finite result is ``None``.
    A mix of a float and an exact number keeps the exact rational
    difference instead of rounding through float64. Either side ``None``
    yields ``None``.
    """
    if comparison is None or reference is None:
        return None
    _require_metric(comparison, "comparison")
    _require_metric(reference, "reference")
    comparison_exact = _is_exact_metric(comparison)
    reference_exact = _is_exact_metric(reference)
    if comparison_exact and reference_exact:
        difference = comparison - reference
        if isinstance(difference, Fraction):
            if difference.denominator == 1:
                return difference.numerator
            return difference
        if type(difference) is int:
            return difference
        raise TypeError("an exact numeric difference must be an int or a Fraction")
    if type(comparison) is float and type(reference) is float:
        return _finite_float_difference(comparison, reference)
    exact = Fraction(comparison) - Fraction(reference)
    if exact.denominator == 1:
        return exact.numerator
    return exact


def _finite_float_difference(comparison: float, reference: float) -> Optional[float]:
    difference = comparison - reference
    if not math.isfinite(difference):
        return None
    if difference == 0.0:
        return 0.0
    return difference


def _is_exact_metric(value: MetricNumber) -> bool:
    return type(value) is int or isinstance(value, Fraction)


def _require_metric(value: object, field: str) -> None:
    if value is None:
        return
    if type(value) is bool:
        raise TypeError(f"{field} must not be a bool")
    if type(value) is int:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError(f"{field} must not be negative zero")
        return
    if isinstance(value, Fraction):
        return
    raise TypeError(f"{field} must be an int, float, Fraction, or None")


def _require_optional_proportion(value: object, field: str) -> None:
    if value is None:
        return
    if type(value) is not float or not math.isfinite(value):
        raise TypeError(f"{field} must be a finite float or None")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field} must be within [0, 1]")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_positive(value: object, field: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field} must be a positive int")


def _require_optional_position(value: object, field: str) -> None:
    if value is None:
        return
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int or None")


def _require_type(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _require_optional(value: object, expected: type, field: str) -> None:
    if value is not None and not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__} or None")
