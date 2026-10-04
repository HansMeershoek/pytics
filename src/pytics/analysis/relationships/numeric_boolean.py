"""Selected Numeric × Boolean association.

The question is how the paired Numeric distribution differs between the
False and True groups of a Boolean variable, how large the mean
difference is, how uncertain it is, and what frequentist evidence
accompanies it.

Every signed component is the True group minus the False group, whichever
physical side is Boolean. That orientation is not a cause, an exposure,
or a treatment.

Each observed group is described by the Numeric descriptive calculator.
The mean difference, Hedges' g, the Welch interval, and Welch's t-test
share one set of group moments. Each group is offset from its own exact
minimum before the float64 cast, so a large common magnitude does not
erase a within-group spread or a between-group difference. The two group
means are subtracted in exact rational arithmetic and rounded once.

Hedges' g uses the pooled sample standard deviation and the exact
small-sample correction. Welch's t-test does not assume equal variances.
It is not chosen by a normality or variance test, and no rank or
permutation test replaces it. The interval and the p-value use the
Student t distribution on the Welch–Satterthwaite degrees of freedom,
through ``scipy.stats.t``.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
from scipy.stats import t as student_t

from pytics.analysis.numeric import _centered_integer_deltas
from pytics.analysis.numeric import _float_mean
from pytics.analysis.numeric import _from_finite
from pytics.analysis.numeric import _scaled_sample_std
from pytics.analysis.relationships.models import BooleanGroupSummary
from pytics.analysis.relationships.models import BooleanLevel
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import MeanDifferenceEstimate
from pytics.analysis.relationships.models import MeanDifferenceInterval
from pytics.analysis.relationships.models import MeanDifferenceIntervalMethod
from pytics.analysis.relationships.models import MeanDifferenceTest
from pytics.analysis.relationships.models import MeanDifferenceTestMethod
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import NumericBooleanRelationship
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import StandardizedDifferenceMethod
from pytics.analysis.relationships.models import StandardizedMeanDifference
from pytics.analysis.relationships.models import UnavailabilityReason
from pytics.analysis.relationships.models import _WELCH_INTERVAL_LEVEL

# Both gamma values of the Hedges correction stay finite in float64 up to
# this many degrees of freedom.
_DIRECT_GAMMA_LIMIT = 340

# Gamma(z + 1/2) / (sqrt(z) * Gamma(z)) as a series in 1/z. Above
# _DIRECT_GAMMA_LIMIT, z exceeds 169 and the omitted terms are below 1e-16.
_GAMMA_RATIO_SERIES = (
    1.0,
    -1.0 / 8.0,
    1.0 / 128.0,
    5.0 / 1024.0,
    -21.0 / 32768.0,
    -399.0 / 262144.0,
    869.0 / 4194304.0,
)

_Number = Union[int, float]
_Welch = Tuple[MeanDifferenceInterval, MeanDifferenceTest]


@dataclass(frozen=True)
class _GroupMoments:
    """Moments of one observed group, on offsets from its exact minimum.

    ``origin`` is that minimum: a Python ``int`` for integer storage and a
    float otherwise. ``offset_mean`` is the float64 mean of the offsets.
    ``standard_deviation`` is their sample deviation, ``None`` for one
    value or when it is not a finite float64. ``constant`` compares the
    exact extrema. These values are not retained.
    """

    n: int
    origin: _Number
    offset_mean: Optional[float]
    standard_deviation: Optional[float]
    constant: bool


def analyze(
    numeric_values: np.ndarray,
    numeric_finite: np.ndarray,
    boolean_observed: np.ndarray,
    boolean_is_true: np.ndarray,
    *,
    left_position: int,
    left_label: object,
    right_position: int,
    right_label: object,
    numeric_position: int,
    boolean_position: int,
    n_total_rows: int,
) -> NumericBooleanRelationship:
    """Describe one Numeric × Boolean pair from prepared column images.

    The numeric image is a value array and a finite mask. The Boolean
    image is an observed mask and a True mask. All four arrays cover every
    dataset row. A row survives only when the numeric value is finite and
    the Boolean value is observed. The arrays are not retained.
    """
    false_values, true_values = _group_values(
        numeric_values,
        numeric_finite,
        boolean_observed,
        boolean_is_true,
        n_total_rows,
    )
    n_paired = int(false_values.size + true_values.size)
    if n_paired == 0:
        absent: Optional[UnavailabilityReason] = (
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        )
    elif false_values.size == 0 or true_values.size == 0:
        absent = UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    else:
        absent = None
    if absent is not None:
        difference = _unavailable_difference(absent)
        standardized = _unavailable_standardized(absent)
        interval, test = _unavailable_welch(absent)
    else:
        false_moments = _moments(false_values)
        true_moments = _moments(true_values)
        difference = _mean_difference(false_moments, true_moments)
        standardized = _hedges_g(difference, false_moments, true_moments)
        interval, test = _welch(difference, false_moments, true_moments)
    return NumericBooleanRelationship(
        left_position=left_position,
        left_label=left_label,
        right_position=right_position,
        right_label=right_label,
        numeric_position=numeric_position,
        boolean_position=boolean_position,
        n_total_rows=n_total_rows,
        n_paired=n_paired,
        false_group=_group_summary(BooleanLevel.FALSE, false_values, n_paired),
        true_group=_group_summary(BooleanLevel.TRUE, true_values, n_paired),
        mean_difference=difference,
        standardized_mean_difference=standardized,
        mean_difference_interval=interval,
        mean_difference_test=test,
    )


def _group_values(
    numeric_values: np.ndarray,
    numeric_finite: np.ndarray,
    boolean_observed: np.ndarray,
    boolean_is_true: np.ndarray,
    n_total_rows: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Sorted paired values at False, then at True.

    Sorting fixes the order of every floating reduction, so the result
    does not depend on source row order.
    """
    for array in (numeric_values, numeric_finite, boolean_observed, boolean_is_true):
        if array.shape != (n_total_rows,):
            raise ValueError("relationship inputs must contain one entry per row")
    if numeric_values.dtype.kind not in {"i", "u", "f"}:
        raise TypeError("numeric-boolean analysis requires integer or floating values")
    paired = np.asarray(numeric_finite, dtype=bool) & np.asarray(
        boolean_observed, dtype=bool
    )
    is_true = np.asarray(boolean_is_true, dtype=bool)
    false_values = np.sort(numeric_values[paired & ~is_true])
    true_values = np.sort(numeric_values[paired & is_true])
    return false_values, true_values


def _group_summary(
    level: BooleanLevel,
    values: np.ndarray,
    n_paired: int,
) -> BooleanGroupSummary:
    if values.size == 0:
        reason = (
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
            if n_paired == 0
            else UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
        )
        return BooleanGroupSummary(
            level=level,
            availability=ResultAvailability.UNAVAILABLE,
            descriptive=None,
            reason=reason,
        )
    return BooleanGroupSummary(
        level=level,
        availability=ResultAvailability.AVAILABLE,
        descriptive=_from_finite(values),
        reason=None,
    )


def _moments(values: np.ndarray) -> _GroupMoments:
    """Moments of one sorted, non-empty group.

    Integer offsets use unsigned subtraction in the source width, the same
    centering as Numeric description, so they are exact before the
    float64 cast. A floating range wider than float64 keeps the values
    themselves, with origin zero.
    """
    origin: _Number
    if values.dtype.kind in {"i", "u"}:
        origin = int(values[0])
        offsets = _centered_integer_deltas(values)
    else:
        origin = float(values[0])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            offsets = np.subtract(values, origin)
        if not bool(np.isfinite(offsets).all()):
            origin = 0.0
            offsets = np.asarray(values, dtype=np.float64)
    n = int(values.size)
    return _GroupMoments(
        n=n,
        origin=origin,
        offset_mean=_float_mean(offsets),
        standard_deviation=_scaled_sample_std(offsets) if n >= 2 else None,
        constant=bool(values[0] == values[-1]),
    )


def _mean_difference(
    false_moments: _GroupMoments,
    true_moments: _GroupMoments,
) -> MeanDifferenceEstimate:
    """``mean(True) - mean(False)``, rounded once.

    Each mean is its exact origin plus its float64 offset mean. Those four
    numbers are combined as fractions. A difference beyond float64 is
    unavailable. It is not stored as infinity.
    """
    if false_moments.offset_mean is None or true_moments.offset_mean is None:
        return _unavailable_difference(UnavailabilityReason.NON_FINITE_RESULT)
    exact = (Fraction(true_moments.origin) + Fraction(true_moments.offset_mean)) - (
        Fraction(false_moments.origin) + Fraction(false_moments.offset_mean)
    )
    try:
        value = float(exact)
    except OverflowError:
        return _unavailable_difference(UnavailabilityReason.NON_FINITE_RESULT)
    return MeanDifferenceEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=_plain(value),
        reason=None,
    )


def _hedges_g(
    difference: MeanDifferenceEstimate,
    false_moments: _GroupMoments,
    true_moments: _GroupMoments,
) -> StandardizedMeanDifference:
    """Hedges' g: ``J(N - 2) * difference / pooled standard deviation``.

    The pooled variance is
    ``((n_true - 1) * s_true**2 + (n_false - 1) * s_false**2) / (N - 2)``,
    with sample deviations divided by ``n - 1``. A one-value group adds no
    term and no degree of freedom. The correction needs ``N - 2 >= 2``.
    When every group is constant the pooled scale is zero: equal values
    have no standardized difference, and different values have an
    unbounded one. Neither is stored as a number.
    """
    degrees_of_freedom = false_moments.n + true_moments.n - 2
    if degrees_of_freedom < 2:
        return _unavailable_standardized(
            UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
        )
    if false_moments.constant and true_moments.constant:
        if false_moments.origin == true_moments.origin:
            return _unavailable_standardized(
                UnavailabilityReason.CONSTANT_PAIRED_VALUES
            )
        return _unavailable_standardized(UnavailabilityReason.MATHEMATICALLY_UNBOUNDED)
    if difference.value is None:
        return _unavailable_standardized(UnavailabilityReason.NON_FINITE_RESULT)
    scale = _pooled_standard_deviation(
        false_moments,
        true_moments,
        degrees_of_freedom,
    )
    if scale is None:
        return _unavailable_standardized(UnavailabilityReason.NON_FINITE_RESULT)
    if scale == 0.0:
        return _unavailable_standardized(UnavailabilityReason.PRECISION_COLLAPSED)
    value = _hedges_correction(degrees_of_freedom) * (difference.value / scale)
    if not math.isfinite(value):
        return _unavailable_standardized(UnavailabilityReason.NON_FINITE_RESULT)
    return StandardizedMeanDifference(
        method=StandardizedDifferenceMethod.HEDGES_G,
        availability=ResultAvailability.AVAILABLE,
        value=_plain(value),
        reason=None,
    )


def _pooled_standard_deviation(
    false_moments: _GroupMoments,
    true_moments: _GroupMoments,
    degrees_of_freedom: int,
) -> Optional[float]:
    """Square root of the pooled variance, without squaring a deviation.

    ``hypot`` of the weighted deviations is that square root. ``None``
    means a deviation or the pooled value is not a finite float64.
    """
    weighted = []
    for moments in (false_moments, true_moments):
        if moments.n < 2:
            continue
        if moments.standard_deviation is None:
            return None
        weighted.append(
            moments.standard_deviation
            * math.sqrt((moments.n - 1) / degrees_of_freedom)
        )
    scale = math.hypot(*weighted)
    if not math.isfinite(scale):
        return None
    return scale


def _hedges_correction(degrees_of_freedom: int) -> float:
    """Exact small-sample correction ``J(v) = G(v/2) / (sqrt(v/2) G((v-1)/2))``.

    ``G`` is the gamma function and ``v`` the pooled degrees of freedom.
    Callers pass ``v >= 2``. At ``v = 1`` the expression has a pole in
    ``G(0)`` and only its limit is zero. The uncorrected ratio has no
    finite mean there, so no unbiased correction exists. The two gamma
    values are evaluated directly while they fit in float64. Beyond that,
    the ratio uses its asymptotic series, which agrees with the direct
    ratio to about 1e-16 at the switch.
    """
    half = degrees_of_freedom / 2.0
    if degrees_of_freedom <= _DIRECT_GAMMA_LIMIT:
        return math.gamma(half) / (math.sqrt(half) * math.gamma(half - 0.5))
    z = half - 0.5
    inverse = 1.0 / z
    series = 0.0
    for coefficient in reversed(_GAMMA_RATIO_SERIES):
        series = series * inverse + coefficient
    return math.sqrt(z / half) * series


def _welch(
    difference: MeanDifferenceEstimate,
    false_moments: _GroupMoments,
    true_moments: _GroupMoments,
) -> _Welch:
    """Welch–Satterthwaite interval and Welch's t-test from shared moments.

    Each group needs two values for a sample variance. When both groups
    are constant the standard error is zero: equal values have no test,
    and different values would have an infinite t. Neither state stores
    an infinite statistic, a p-value of zero, or a zero-width interval.
    """
    if false_moments.n < 2 or true_moments.n < 2:
        return _unavailable_welch(
            UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
        )
    if false_moments.constant and true_moments.constant:
        if false_moments.origin == true_moments.origin:
            return _unavailable_welch(UnavailabilityReason.CONSTANT_PAIRED_VALUES)
        return _unavailable_welch(UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION)
    if (
        difference.value is None
        or false_moments.standard_deviation is None
        or true_moments.standard_deviation is None
    ):
        return _unavailable_welch(UnavailabilityReason.NON_FINITE_RESULT)
    true_error = true_moments.standard_deviation / math.sqrt(true_moments.n)
    false_error = false_moments.standard_deviation / math.sqrt(false_moments.n)
    standard_error = math.hypot(true_error, false_error)
    if standard_error == 0.0:
        return _unavailable_welch(UnavailabilityReason.PRECISION_COLLAPSED)
    if not math.isfinite(standard_error):
        return _unavailable_welch(UnavailabilityReason.NON_FINITE_RESULT)
    degrees_of_freedom = _welch_degrees_of_freedom(
        true_error,
        false_error,
        true_moments.n,
        false_moments.n,
    )
    return (
        _welch_interval(difference.value, standard_error, degrees_of_freedom),
        _welch_test(difference.value, standard_error, degrees_of_freedom),
    )


def _welch_degrees_of_freedom(
    true_error: float,
    false_error: float,
    n_true: int,
    n_false: int,
) -> float:
    """Welch–Satterthwaite degrees of freedom.

    ``(a + b)**2 / (a**2 / (n_true - 1) + b**2 / (n_false - 1))``, where
    ``a`` and ``b`` are the squared standard errors of the two means.
    Both errors are divided by the larger one first. That leaves the ratio
    unchanged and keeps every square finite. The exact value lies between
    the smaller group's ``n - 1`` and ``n_true + n_false - 2``. A rounded
    value outside that range is returned to it.
    """
    largest = max(true_error, false_error)
    a = (true_error / largest) ** 2
    b = (false_error / largest) ** 2
    value = (a + b) ** 2 / (a * a / (n_true - 1) + b * b / (n_false - 1))
    lower = float(min(n_true, n_false) - 1)
    upper = float(n_true + n_false - 2)
    return min(max(value, lower), upper)


def _welch_interval(
    difference: float,
    standard_error: float,
    degrees_of_freedom: float,
) -> MeanDifferenceInterval:
    """``difference ± t(0.975, df) * standard_error``.

    The critical value is ``scipy.stats.t.ppf`` at the two-sided 95%
    level on the Welch–Satterthwaite degrees of freedom. A normal
    quantile is not substituted. Bounds that do not fit in float64 are
    unavailable.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        critical = float(
            student_t.ppf(1.0 - (1.0 - _WELCH_INTERVAL_LEVEL) / 2.0, degrees_of_freedom)
        )
    if not math.isfinite(critical) or critical <= 0.0:
        return _unavailable_interval(UnavailabilityReason.NON_FINITE_RESULT)
    half_width = critical * standard_error
    lower = difference - half_width
    upper = difference + half_width
    if not (
        math.isfinite(half_width) and math.isfinite(lower) and math.isfinite(upper)
    ):
        return _unavailable_interval(UnavailabilityReason.NON_FINITE_RESULT)
    return MeanDifferenceInterval(
        availability=ResultAvailability.AVAILABLE,
        level=_WELCH_INTERVAL_LEVEL,
        method=MeanDifferenceIntervalMethod.WELCH_SATTERTHWAITE,
        lower=_plain(lower),
        upper=_plain(upper),
        reason=None,
    )


def _welch_test(
    difference: float,
    standard_error: float,
    degrees_of_freedom: float,
) -> MeanDifferenceTest:
    """Welch's t ratio and its raw two-sided p-value.

    ``t = difference / standard_error``, so its sign is the sign of the
    True − False difference. The p-value is
    ``2 * scipy.stats.t.sf(abs(t), df)``, the tail SciPy's
    ``ttest_ind(..., equal_var=False)`` reports for the same moments. A
    ratio beyond float64 is unavailable together with its p-value.
    """
    statistic = difference / standard_error
    if not math.isfinite(statistic):
        return _unavailable_test(UnavailabilityReason.NON_FINITE_RESULT)
    p_value = _two_sided_p_value(statistic, degrees_of_freedom)
    if p_value is None:
        frequentist = _unavailable_frequentist(UnavailabilityReason.NON_FINITE_RESULT)
    else:
        frequentist = FrequentistEvidence(
            availability=ResultAvailability.AVAILABLE,
            p_value=p_value,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=None,
        )
    return MeanDifferenceTest(
        method=MeanDifferenceTestMethod.WELCH_T,
        statistic_availability=ResultAvailability.AVAILABLE,
        statistic=_plain(statistic),
        degrees_of_freedom=degrees_of_freedom,
        statistic_reason=None,
        frequentist=frequentist,
    )


def _two_sided_p_value(statistic: float, degrees_of_freedom: float) -> Optional[float]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        tail = float(student_t.sf(abs(statistic), degrees_of_freedom))
    p_value = 2.0 * tail
    if not math.isfinite(p_value) or p_value < 0.0 or p_value > 1.0:
        return None
    return _plain(p_value)


def _plain(value: float) -> float:
    """Store ``-0.0`` as ``0.0``."""
    if value == 0.0:
        return 0.0
    return value


def _unavailable_difference(reason: UnavailabilityReason) -> MeanDifferenceEstimate:
    return MeanDifferenceEstimate(
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _unavailable_standardized(
    reason: UnavailabilityReason,
) -> StandardizedMeanDifference:
    return StandardizedMeanDifference(
        method=StandardizedDifferenceMethod.HEDGES_G,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _unavailable_welch(reason: UnavailabilityReason) -> _Welch:
    return _unavailable_interval(reason), _unavailable_test(reason)


def _unavailable_interval(reason: UnavailabilityReason) -> MeanDifferenceInterval:
    return MeanDifferenceInterval(
        availability=ResultAvailability.UNAVAILABLE,
        level=None,
        method=None,
        lower=None,
        upper=None,
        reason=reason,
    )


def _unavailable_test(reason: UnavailabilityReason) -> MeanDifferenceTest:
    return MeanDifferenceTest(
        method=MeanDifferenceTestMethod.WELCH_T,
        statistic_availability=ResultAvailability.UNAVAILABLE,
        statistic=None,
        degrees_of_freedom=None,
        statistic_reason=reason,
        frequentist=_unavailable_frequentist(reason),
    )


def _unavailable_frequentist(reason: UnavailabilityReason) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=ResultAvailability.UNAVAILABLE,
        p_value=None,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=reason,
    )
