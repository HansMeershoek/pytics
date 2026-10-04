"""Selected Numeric × Numeric association.

Spearman rank correlation is the primary descriptive association.
Pearson product-moment correlation is complementary. Neither method is
chosen by a normality test. The computational image is float64 because
that is what the SciPy calls accept. Integers above ``2**53`` are not
exact in that image. When the image removes variation that the original
paired values had, the methods are unavailable. A fabricated zero
correlation is not stored.

An estimate, its frequentist p-value, and a confidence interval can each
be unavailable on their own. Raw p-values are stored when the test
exists. This module does not adjust them. Dataset-level correction may
later adjust the Spearman p-value and leaves the Pearson p-value raw.
"""

from __future__ import annotations

import math
import warnings
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.stats import pearsonr
from scipy.stats import spearmanr

from pytics.analysis.relationships.models import AssociationMethod
from pytics.analysis.relationships.models import AssociationResult
from pytics.analysis.relationships.models import CorrelationEstimate
from pytics.analysis.relationships.models import CorrelationInterval
from pytics.analysis.relationships.models import CorrelationIntervalMethod
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import UnavailabilityReason
from pytics.analysis.relationships.models import _CONFIDENCE_LEVEL
from pytics.analysis.relationships.models import _direction

# Two finite paired observations can define a correlation of exactly ±1.
# A two-sided test needs a positive degrees-of-freedom count, ``n - 2``.
# The classical Fisher z interval needs a positive variance, ``1 / (n - 3)``.
_MIN_ESTIMATE_N = 2


_MIN_TEST_N = 3


_MIN_PEARSON_INTERVAL_N = 4


# Float64 can sit slightly outside [-1, 1] after a correlation product.
# A larger departure is not a correlation.
_CORRELATION_CLAMP = 1e-8


def _read_numeric_column(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Return source values and a finite mask for one selected Numeric column.

    The mask is false for missing values and for non-finite floats.
    Integer storage has no infinities. Boolean and complex values are not
    coerced. The returned arrays are copies.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("numeric relationship values must be a pandas Series")
    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype) or pd.api.types.is_complex_dtype(dtype):
        raise TypeError(
            "relationship analysis does not coerce boolean or complex values"
        )
    if pd.api.types.is_float_dtype(dtype):
        return _read_float_column(series)
    if pd.api.types.is_integer_dtype(dtype):
        return _read_integer_column(series)
    raise TypeError(
        "numeric relationship analysis applies only to integer and floating values"
    )


def _read_float_column(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    if isinstance(series.dtype, pd.api.extensions.ExtensionDtype):
        values = series.to_numpy(dtype=np.float64, na_value=np.nan, copy=True)
    else:
        values = series.to_numpy(dtype=np.float64, copy=True)
    values = np.asarray(values, dtype=np.float64)
    return values, np.isfinite(values)


def _read_integer_column(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    finite = np.asarray(series.notna().to_numpy(dtype=bool, copy=True))
    if isinstance(series.dtype, pd.api.extensions.ExtensionDtype):
        numpy_dtype = np.dtype(series.dtype.numpy_dtype)
        values = series.to_numpy(dtype=numpy_dtype, na_value=0, copy=True)
    else:
        values = series.to_numpy(copy=True)
    values = np.asarray(values)
    if values.shape != finite.shape:
        raise ValueError("numeric values must contain one entry per row")
    if values.dtype.kind not in {"i", "u", "O"}:
        raise TypeError("integer relationship values must stay integers")
    return values, finite


def _association_methods(
    left: np.ndarray,
    right: np.ndarray,
) -> Tuple[AssociationResult, AssociationResult]:
    """Return Spearman and Pearson for one paired finite population."""
    if left.ndim != 1 or left.shape != right.shape:
        raise ValueError("paired values must be one-dimensional and aligned")
    n_paired = int(left.size)
    if n_paired < _MIN_ESTIMATE_N:
        reason = UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        return _both_unavailable(n_paired, reason)
    if not _has_variation(left) or not _has_variation(right):
        return _both_unavailable(n_paired, UnavailabilityReason.CONSTANT_PAIRED_VALUES)
    left_float = _to_float64(left)
    right_float = _to_float64(right)
    if (
        left_float is None
        or right_float is None
        or not (_all_finite(left_float) and _all_finite(right_float))
    ):
        return _both_unavailable(n_paired, UnavailabilityReason.NON_FINITE_RESULT)
    if not _has_variation(left_float) or not _has_variation(right_float):
        return _both_unavailable(n_paired, UnavailabilityReason.PRECISION_COLLAPSED)
    if n_paired == _MIN_ESTIMATE_N:
        estimate = _two_point_correlation(left, right)
        return (
            _estimate_only(AssociationMethod.SPEARMAN, n_paired, estimate),
            _estimate_only(AssociationMethod.PEARSON, n_paired, estimate),
        )
    return (
        _spearman_result(left_float, right_float, n_paired),
        _pearson_result(left_float, right_float, n_paired),
    )


def _spearman_result(
    left: np.ndarray,
    right: np.ndarray,
    n_paired: int,
) -> AssociationResult:
    """Spearman rho from ``scipy.stats.spearmanr``.

    The returned statistic is rho. No second test statistic is created.
    Ties use SciPy's rank convention. There is no Spearman interval.
    """
    correlation, p_value = _call_scipy(spearmanr, left, right)
    estimate = _estimate_from_library(correlation)
    return _method_result(
        AssociationMethod.SPEARMAN,
        n_paired,
        estimate,
        _frequentist_from_library(estimate, p_value, n_paired),
        _spearman_interval(estimate),
    )


def _pearson_result(
    left: np.ndarray,
    right: np.ndarray,
    n_paired: int,
) -> AssociationResult:
    """Pearson r from ``scipy.stats.pearsonr`` and a classical Fisher z interval.

    The library call is ``pearsonr(x, y)`` with no newer keyword arguments.
    The returned statistic is r. The interval uses ``atanh``, standard
    error ``1 / sqrt(n - 3)``, and the two-sided 95% normal quantile from
    ``scipy.stats.norm.ppf``. No bias correction is applied.
    """
    correlation, p_value = _call_scipy(pearsonr, left, right)
    estimate = _estimate_from_library(correlation)
    return _method_result(
        AssociationMethod.PEARSON,
        n_paired,
        estimate,
        _frequentist_from_library(estimate, p_value, n_paired),
        _pearson_interval(estimate, n_paired),
    )


def _call_scipy(
    function: object,
    left: np.ndarray,
    right: np.ndarray,
) -> Tuple[object, object]:
    """Call one SciPy correlation and return its coefficient and p-value.

    Runtime warnings from the call are ignored here. A non-finite result
    is handled by the caller. Programmer errors are not caught.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = function(left, right)  # type: ignore[operator]
    except (ValueError, FloatingPointError):
        return None, None
    correlation = getattr(result, "correlation", None)
    if correlation is None:
        correlation = getattr(result, "statistic", None)
    p_value = getattr(result, "pvalue", None)
    if correlation is None or p_value is None:
        try:
            correlation = result[0]  # type: ignore[index]
            p_value = result[1]  # type: ignore[index]
        except (TypeError, IndexError, KeyError):
            return None, None
    return correlation, p_value


def _estimate_from_library(correlation: object) -> CorrelationEstimate:
    value = _correlation_value(correlation)
    if value is None:
        return _unavailable_estimate(UnavailabilityReason.NON_FINITE_RESULT)
    return CorrelationEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=value,
        direction=_direction(value),
        reason=None,
    )


def _frequentist_from_library(
    estimate: CorrelationEstimate,
    p_value: object,
    n_paired: int,
) -> FrequentistEvidence:
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        return _unavailable_test(estimate.reason)  # type: ignore[arg-type]
    if n_paired < _MIN_TEST_N:
        return _unavailable_test(UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS)
    value = _p_value(p_value)
    if value is None:
        return _unavailable_test(UnavailabilityReason.NON_FINITE_RESULT)
    return FrequentistEvidence(
        availability=ResultAvailability.AVAILABLE,
        p_value=value,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )


def _spearman_interval(estimate: CorrelationEstimate) -> CorrelationInterval:
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        return _unavailable_interval(estimate.reason)  # type: ignore[arg-type]
    return _unavailable_interval(UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD)


def _pearson_interval(
    estimate: CorrelationEstimate,
    n_paired: int,
) -> CorrelationInterval:
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        return _unavailable_interval(estimate.reason)  # type: ignore[arg-type]
    if n_paired < _MIN_PEARSON_INTERVAL_N:
        return _unavailable_interval(
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        )
    if estimate.value == 1.0 or estimate.value == -1.0:
        return _unavailable_interval(UnavailabilityReason.BOUNDARY_CORRELATION)
    bounds = _fisher_z_bounds(estimate.value, n_paired)
    if bounds is None:
        return _unavailable_interval(UnavailabilityReason.NON_FINITE_RESULT)
    lower, upper = bounds
    return CorrelationInterval(
        availability=ResultAvailability.AVAILABLE,
        level=_CONFIDENCE_LEVEL,
        method=CorrelationIntervalMethod.FISHER_Z,
        lower=lower,
        upper=upper,
        reason=None,
    )


def _fisher_z_bounds(estimate: float, n_paired: int) -> Optional[Tuple[float, float]]:
    """Classical Fisher z interval, without a bias correction.

    ``z = atanh(r)`` and the standard error is ``1 / sqrt(n - 3)``.
    The critical value is the two-sided 95% standard-normal quantile.
    """
    try:
        transformed = math.atanh(estimate)
    except ValueError:
        return None
    if not math.isfinite(transformed):
        return None
    scale = math.sqrt(n_paired - 3)
    if scale == 0.0:
        return None
    critical = float(norm.ppf(1.0 - (1.0 - _CONFIDENCE_LEVEL) / 2.0))
    if not math.isfinite(critical):
        return None
    half_width = critical / scale
    lower = math.tanh(transformed - half_width)
    upper = math.tanh(transformed + half_width)
    lower = _bound_endpoint(lower)
    upper = _bound_endpoint(upper)
    if lower is None or upper is None or lower > upper:
        return None
    return lower, upper


def _bound_endpoint(value: float) -> Optional[float]:
    if not math.isfinite(value):
        return None
    if value == 0.0:
        return 0.0
    if value < -1.0 or value > 1.0:
        if abs(value) - 1.0 <= _CORRELATION_CLAMP:
            return -1.0 if value < 0.0 else 1.0
        return None
    return value


def _estimate_only(
    method: AssociationMethod,
    n_paired: int,
    estimate: float,
) -> AssociationResult:
    """Store an exact ±1 estimate without a test or a Pearson interval.

    Two varying points determine the sign. ``n - 2`` is zero, so the
    p-value is not taken from SciPy. The Pearson interval also needs
    ``n - 3 > 0``.
    """
    estimate_result = CorrelationEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=estimate,
        direction=_direction(estimate),
        reason=None,
    )
    return _method_result(
        method,
        n_paired,
        estimate_result,
        _unavailable_test(UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS),
        (
            _spearman_interval(estimate_result)
            if method is AssociationMethod.SPEARMAN
            else _unavailable_interval(
                UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
            )
        ),
    )


def _both_unavailable(
    n_paired: int,
    reason: UnavailabilityReason,
) -> Tuple[AssociationResult, AssociationResult]:
    return (
        _unavailable_method(AssociationMethod.SPEARMAN, n_paired, reason),
        _unavailable_method(AssociationMethod.PEARSON, n_paired, reason),
    )


def _unavailable_method(
    method: AssociationMethod,
    n_paired: int,
    reason: UnavailabilityReason,
) -> AssociationResult:
    return _method_result(
        method,
        n_paired,
        _unavailable_estimate(reason),
        _unavailable_test(reason),
        _unavailable_interval(reason),
    )


def _method_result(
    method: AssociationMethod,
    n_paired: int,
    estimate: CorrelationEstimate,
    frequentist: FrequentistEvidence,
    interval: CorrelationInterval,
) -> AssociationResult:
    return AssociationResult(
        method=method,
        n_observations=n_paired,
        estimate=estimate,
        frequentist=frequentist,
        confidence_interval=interval,
    )


def _unavailable_estimate(reason: UnavailabilityReason) -> CorrelationEstimate:
    return CorrelationEstimate(
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        direction=None,
        reason=reason,
    )


def _unavailable_test(reason: UnavailabilityReason) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=ResultAvailability.UNAVAILABLE,
        p_value=None,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=reason,
    )


def _unavailable_interval(reason: UnavailabilityReason) -> CorrelationInterval:
    return CorrelationInterval(
        availability=ResultAvailability.UNAVAILABLE,
        level=None,
        method=None,
        lower=None,
        upper=None,
        reason=reason,
    )


def _two_point_correlation(left: np.ndarray, right: np.ndarray) -> float:
    """Return ±1 from whether the two source values move together.

    Comparison uses the original values, so an integer above ``2**53``
    keeps its order. SciPy is not called.
    """
    left_increases = bool(left[1] > left[0])
    right_increases = bool(right[1] > right[0])
    if left_increases == right_increases:
        return 1.0
    return -1.0


def _to_float64(values: np.ndarray) -> Optional[np.ndarray]:
    """Return a float64 copy, or ``None`` when conversion cannot be finite."""
    try:
        if values.dtype.kind == "f":
            converted = np.asarray(values, dtype=np.float64)
        elif values.dtype.kind in {"i", "u"}:
            converted = values.astype(np.float64, copy=False)
        else:
            converted = np.array(
                [float(value) for value in values.tolist()],
                dtype=np.float64,
            )
    except (TypeError, ValueError, OverflowError):
        return None
    return np.asarray(converted, dtype=np.float64)


def _has_variation(values: np.ndarray) -> bool:
    if values.size < 2:
        return False
    return bool(np.any(values != values[0]))


def _all_finite(values: np.ndarray) -> bool:
    return bool(np.isfinite(values).all())


def _correlation_value(value: object) -> Optional[float]:
    number = _plain_unit_float(value)
    if number is None:
        return None
    if number < -1.0 or number > 1.0:
        if abs(number) - 1.0 <= _CORRELATION_CLAMP:
            return -1.0 if number < 0.0 else 1.0
        return None
    if number == 0.0:
        return 0.0
    return number


def _p_value(value: object) -> Optional[float]:
    number = _plain_unit_float(value)
    if number is None or number < 0.0 or number > 1.0:
        return None
    if number == 0.0:
        return 0.0
    return number


def _plain_unit_float(value: object) -> Optional[float]:
    if isinstance(value, (bool, np.bool_)):
        return None
    if isinstance(value, np.ndarray):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number
