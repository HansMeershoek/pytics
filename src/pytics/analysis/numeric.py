"""Descriptive statistics for a column selected as Numeric.

These facts profile a numeric measurement. They are not semantic-inference
evidence. ``NumericStructureEvidence`` still owns finite, sign, infinity,
and integer-like counts. This module does not select a semantic type, and
it does not read one.

The descriptive population is the finite non-missing values. Missing values
are excluded. Positive and negative infinity are not finite observations, so
they are excluded from every statistic here. When that population is empty,
every statistic is undefined.

Minimum and maximum keep the finite population's own numbers: a Python
``int`` for integer storage, including values above the float64 exact-integer
range, and a Python ``float`` for floating storage. ``-0.0`` is stored as
``0.0``. Mean and sample standard deviation are float64. The deviation is scaled
before squaring so a finite population of large floats does not overflow.
Quantiles use one
linear-interpolation rule. Integer quantiles stay exact when float64 cannot
represent the interpolated value.

The source Series is not retained. Integer and floating storage are not
coerced into each other, numeric strings are not parsed, and complex values
are not accepted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional
from typing import Union

import numpy as np
import pandas as pd

# Sample standard deviation. NumPy's default ``ddof`` is 0, which is the
# population convention. This profiling layer describes an observed sample.
_SAMPLE_DDOF = 1

# Linear interpolation, Hyndman-Fan type 7: the position is ``(n - 1) * q``.
# Q1, the median, and Q3 are the same rule at 1/4, 1/2, and 3/4. The
# fractions stay in lowest integer terms so the index arithmetic is exact.
_Q1 = (1, 4)
_MEDIAN = (1, 2)
_Q3 = (3, 4)

ObservedNumber = Union[int, float]
QuantileNumber = Union[int, float, Fraction]


@dataclass(frozen=True)
class NumericDescriptiveAnalysis:
    """Finite-population descriptive statistics for one Numeric column.

    ``finite_count`` is the number of finite non-missing observations.
    It is not a copy of the zero, sign, or infinity counts.

    ``minimum`` and ``maximum`` are those finite observations. They are
    ``None`` when ``finite_count`` is zero. ``mean``, ``median``, ``q1``,
    and ``q3`` follow the same rule. ``standard_deviation`` is also
    ``None`` when fewer than two finite observations exist, because the
    sample convention divides by ``n - 1``.

    ``range`` and ``interquartile_range`` are derived. They are not stored.
    A non-integral quantile of integer data may be a ``Fraction`` when the
    float64 image of that exact value would leave the integer extrema.
    """

    finite_count: int
    minimum: Optional[ObservedNumber]
    maximum: Optional[ObservedNumber]
    mean: Optional[float]
    median: Optional[QuantileNumber]
    standard_deviation: Optional[float]
    q1: Optional[QuantileNumber]
    q3: Optional[QuantileNumber]

    def __post_init__(self) -> None:
        if type(self.finite_count) is not int or self.finite_count < 0:
            raise ValueError("finite_count must be a non-negative int")
        if self.finite_count == 0:
            _require_undefined(self)
            return
        _require_observed(self.minimum, "minimum")
        _require_observed(self.maximum, "maximum")
        _require_float_metric(self.mean, "mean")
        _require_quantile(self.median, "median")
        _require_quantile(self.q1, "q1")
        _require_quantile(self.q3, "q3")
        if self.finite_count == 1:
            if self.standard_deviation is not None:
                raise ValueError("standard deviation is undefined for one finite value")
            if not (self.minimum == self.q1 == self.median == self.q3 == self.maximum):
                raise ValueError("one finite value is every distribution landmark")
        else:
            if self.standard_deviation is None:
                raise ValueError(
                    "standard deviation is required when at least two finite "
                    "values exist"
                )
            _require_float_metric(self.standard_deviation, "standard_deviation")
            if self.standard_deviation < 0.0:
                raise ValueError("standard deviation cannot be negative")
        if not (self.minimum <= self.q1 <= self.median <= self.q3 <= self.maximum):
            raise ValueError("minimum, quartiles, median, and maximum are out of order")

    @property
    def range(self) -> Optional[QuantileNumber]:
        """Maximum minus minimum of the finite population.

        ``None`` when there is no finite observation. Zero when the finite
        population has one value.
        """
        if self.minimum is None or self.maximum is None:
            return None
        return _difference(self.maximum, self.minimum)

    @property
    def interquartile_range(self) -> Optional[QuantileNumber]:
        """Q3 minus Q1.

        ``None`` when those quartiles are undefined. Zero when the finite
        population has one value.
        """
        if self.q1 is None or self.q3 is None:
            return None
        return _difference(self.q3, self.q1)


def collect_numeric_descriptive_analysis(
    series: pd.Series,
) -> NumericDescriptiveAnalysis:
    """Describe the finite non-missing values of one numeric Series.

    The Series must already use integer or floating storage, including
    nullable integer and floating dtypes. Boolean storage is rejected even
    where a numeric predicate would accept it. Strings are not parsed.
    Complex values are not coerced. The Series is not modified, and its
    dtype is not changed.

    Missing values are dropped with pandas missingness. Infinities are then
    removed. Minimum, maximum, mean, sample standard deviation, and the
    three linear quantiles are read from that finite population only.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_numeric_descriptive_analysis expects a pandas Series")
    finite = _finite_values(series)
    return _from_finite(finite)


def _finite_values(series: pd.Series) -> np.ndarray:
    """Return finite non-missing values without changing the source Series.

    Integer storage has no infinities. Those values keep their integer
    dtype. Floating storage drops values that are not finite. The returned
    array is not written back to ``series``.
    """
    if pd.api.types.is_bool_dtype(series.dtype) or not (
        pd.api.types.is_integer_dtype(series.dtype)
        or pd.api.types.is_float_dtype(series.dtype)
    ):
        raise TypeError(
            "numeric descriptive analysis applies only to integer and "
            "floating values"
        )
    observed = series.dropna()
    values = observed.to_numpy(copy=False)
    if not isinstance(values, np.ndarray):
        raise TypeError(
            "numeric descriptive analysis applies only to real integer and "
            "floating values"
        )
    kind = values.dtype.kind
    if kind in {"i", "u"}:
        return values
    if kind == "f":
        return values[np.isfinite(values)]
    raise TypeError(
        "numeric descriptive analysis applies only to real integer and "
        "floating values"
    )


def _from_finite(values: np.ndarray) -> NumericDescriptiveAnalysis:
    """Calculate one descriptive result from finite values already isolated.

    The array is sorted into a new array. Quantiles share that order
    statistics. Mean and sample standard deviation use float64 even when
    the source values are integers, so integers above ``2**53`` are not
    exact in those two statistics.
    """
    finite_count = int(values.size)
    if finite_count == 0:
        return NumericDescriptiveAnalysis(
            finite_count=0,
            minimum=None,
            maximum=None,
            mean=None,
            median=None,
            standard_deviation=None,
            q1=None,
            q3=None,
        )
    integer = values.dtype.kind in {"i", "u"}
    ordered = np.sort(values)
    minimum = _endpoint(ordered[0], integer)
    maximum = _endpoint(ordered[-1], integer)
    mean = _plain_float(np.mean(ordered, dtype=np.float64))
    if finite_count == 1:
        standard_deviation = None
    else:
        standard_deviation = _sample_standard_deviation(ordered)
    q1 = _linear_quantile(ordered, _Q1[0], _Q1[1], integer)
    median = _linear_quantile(ordered, _MEDIAN[0], _MEDIAN[1], integer)
    q3 = _linear_quantile(ordered, _Q3[0], _Q3[1], integer)
    return NumericDescriptiveAnalysis(
        finite_count=finite_count,
        minimum=minimum,
        maximum=maximum,
        mean=mean,
        median=median,
        standard_deviation=standard_deviation,
        q1=q1,
        q3=q3,
    )


def _linear_quantile(
    ordered: np.ndarray,
    numerator: int,
    denominator: int,
    integer: bool,
) -> QuantileNumber:
    """Interpolate one quantile from a sorted finite population.

    The position is ``(n - 1) * numerator / denominator``. An exact index
    returns that order statistic. Otherwise the result lies on the segment
    between the surrounding order statistics. Integer segments use exact
    arithmetic. Floating segments use float64.
    """
    scaled = (ordered.size - 1) * numerator
    lower = int(scaled // denominator)
    remainder = int(scaled % denominator)
    left = ordered[lower]
    if remainder == 0:
        return _endpoint(left, integer)
    right = ordered[lower + 1]
    if integer:
        return _integer_interpolation(left, right, remainder, denominator)
    return _float_interpolation(left, right, remainder, denominator)


def _integer_interpolation(
    left: object,
    right: object,
    remainder: int,
    denominator: int,
) -> QuantileNumber:
    """Interpolate two integers without rounding them through float64.

    The exact value is ``left + (right - left) * remainder / denominator``.
    An integer result stays a Python ``int``. A non-integer result is a
    Python ``float`` when that float equals the exact value, and a
    ``Fraction`` when float64 would move it outside the exact endpoints.
    """
    left_int = int(left)  # type: ignore[arg-type]
    right_int = int(right)  # type: ignore[arg-type]
    exact_numerator = left_int * denominator + (right_int - left_int) * remainder
    if exact_numerator % denominator == 0:
        return exact_numerator // denominator
    exact = Fraction(exact_numerator, denominator)
    as_float = float(exact)
    if as_float == exact:
        return _plain_float(as_float)
    return exact


def _float_interpolation(
    left: object,
    right: object,
    remainder: int,
    denominator: int,
) -> float:
    """Interpolate two finite floats in float64.

    ``left * (1 - weight) + right * weight`` keeps a segment between large
    opposite-signed values finite. Float rounding that steps outside the
    two surrounding order statistics is pulled back onto that segment.
    """
    left_float = float(left)  # type: ignore[arg-type]
    right_float = float(right)  # type: ignore[arg-type]
    weight = remainder / denominator
    result = left_float * (1.0 - weight) + right_float * weight
    low = left_float if left_float <= right_float else right_float
    high = right_float if left_float <= right_float else left_float
    return _plain_float(_on_segment(result, low, high))


def _on_segment(result: float, low: float, high: float) -> float:
    """Keep a rounded interpolation on the segment between two order statistics."""
    if not math.isfinite(result) or result < low:
        return low
    if result > high:
        return high
    return result


def _sample_standard_deviation(ordered: np.ndarray) -> float:
    """Return the float64 sample standard deviation, divided by ``n - 1``.

    The values are scaled by their maximum absolute value before squaring.
    A finite population of very large floats then stays finite instead of
    overflowing. The result is still float64, so integers above ``2**53``
    are not exact. Zero is returned as ``0.0``, never as negative zero.
    """
    as_float = np.asarray(ordered, dtype=np.float64)
    scale = float(np.max(np.abs(as_float)))
    if scale == 0.0:
        return 0.0
    standardized = as_float / scale
    deviation = float(np.std(standardized, dtype=np.float64, ddof=_SAMPLE_DDOF))
    return _plain_float(deviation * scale)


def _endpoint(value: object, integer: bool) -> ObservedNumber:
    """Return one observed finite value as a Python int or float."""
    if integer:
        return int(value)  # type: ignore[arg-type]
    return _plain_float(value)


def _plain_float(value: object) -> float:
    """Return a finite Python float, with negative zero stored as zero."""
    number = float(value)  # type: ignore[arg-type]
    if not math.isfinite(number):
        raise ValueError("descriptive metric must be finite")
    if number == 0.0:
        return 0.0
    return number


def _difference(
    later: QuantileNumber,
    earlier: QuantileNumber,
) -> QuantileNumber:
    difference = later - earlier
    if type(difference) is float and difference == 0.0:
        return 0.0
    return difference


def _require_undefined(analysis: NumericDescriptiveAnalysis) -> None:
    metrics = (
        analysis.minimum,
        analysis.maximum,
        analysis.mean,
        analysis.median,
        analysis.standard_deviation,
        analysis.q1,
        analysis.q3,
    )
    if any(metric is not None for metric in metrics):
        raise ValueError("descriptive metrics are undefined when finite_count is 0")


def _require_observed(value: object, field: str) -> None:
    if value is None:
        raise ValueError(f"{field} is required when finite_count is positive")
    if type(value) is int:
        return
    if type(value) is float:
        _require_finite_float(value, field)
        return
    raise TypeError(f"{field} must be an int or a float")


def _require_quantile(value: object, field: str) -> None:
    if value is None:
        raise ValueError(f"{field} is required when finite_count is positive")
    if type(value) is int:
        return
    if type(value) is float:
        _require_finite_float(value, field)
        return
    if isinstance(value, Fraction):
        return
    raise TypeError(f"{field} must be an int, a float, or a Fraction")


def _require_float_metric(value: object, field: str) -> None:
    if value is None:
        raise ValueError(f"{field} is required when finite_count is positive")
    if type(value) is not float:
        raise TypeError(f"{field} must be a float")
    _require_finite_float(value, field)


def _require_finite_float(value: float, field: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")
