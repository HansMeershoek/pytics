"""Selected Numeric × Categorical association.

The question is whether the location of a Numeric variable differs across
the observed groups of a Categorical variable, how large that overall
group effect is, and what omnibus evidence accompanies it. It does not
say which category pairs differ.

The descriptive effect is eta squared, the ratio of between-group sum of
squares to total sum of squares. The bias-corrected companion is
Kelley's epsilon squared,

    epsilon² = (SS_between - (k - 1) * MS_within) / SS_total

with ``MS_within = SS_within / (N - k)``. It estimates the same ratio
with the null expectation of the between-group sum removed. A negative
value is retained: the correction exceeded the observed between-group
sum, and that is not stored as zero. Epsilon squared is unavailable when
``N = k``, because the within-group mean square is then undefined.
Omega squared was not selected. It changes the denominator as well as
the numerator, so it is not a correction of the ratio eta squared
already stores, and it is slightly more biased for that ratio.

The omnibus test is classical one-way ANOVA from
``scipy.stats.f_oneway`` with no keyword arguments, so the call stays
within the declared SciPy 1.7 floor. Equal variances are an assumption
of that test. They are not tested, and the test is not replaced when
they might fail. Welch's ANOVA is not used: SciPy exposes it through
``equal_var=False``, which was added in SciPy 1.16.

Sums of squares use group deviations on a shifted float64 image.
When those squares overflow, the shifted values are scaled. Integer
values outside the exact float64 integer
range are translated by unsigned subtraction of their minimum before
that cast. A translated value that is not an exact float64 makes the
effect and the test unavailable. Group descriptions do not use that
image. They use the Numeric descriptive calculator, so the landmarks
match a Numeric column.

Category order is the physical categorical vocabulary with unused and
unpaired levels removed. The ANOVA calculation does not use that order.
Ordered categorical metadata does not become an ordinal score. This
module stores the raw ANOVA p-value. It does not apply dataset-level
correction.
"""

from __future__ import annotations

import math
import warnings
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd

from pytics.analysis.categorical import _label_storage_codes
from pytics.semantics.column_evidence import AnalyticalInapplicability
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from scipy.stats import f_oneway

from pytics.analysis.numeric import _FLOAT64_EXACT_INTEGER_LIMIT
from pytics.analysis.numeric import _from_finite
from pytics.analysis.relationships.models import CategoricalGroupSummary
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import GroupEffectEstimate
from pytics.analysis.relationships.models import GroupEffectMethod
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import NumericCategoricalRelationship
from pytics.analysis.relationships.models import OmnibusAnovaResult
from pytics.analysis.relationships.models import OmnibusTestMethod
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import UnavailabilityReason

# A float64 ratio can sit just outside [0, 1] after cancellation. A larger
# departure is not eta squared.
_ETA_TOLERANCE = 1e-8

_EffectAndTest = Tuple[GroupEffectEstimate, GroupEffectEstimate, OmnibusAnovaResult]


def analyze(
    numeric_values: np.ndarray,
    numeric_finite: np.ndarray,
    category_codes: np.ndarray,
    categories: Tuple[object, ...],
    *,
    left_position: int,
    left_label: object,
    right_position: int,
    right_label: object,
    numeric_position: int,
    categorical_position: int,
    n_total_rows: int,
) -> NumericCategoricalRelationship:
    """Describe one Numeric × Categorical pair.

    ``category_codes`` uses ``-1`` for a missing category, which is the
    pandas categorical sentinel. A code that is not missing selects
    ``categories`` by that vocabulary index. Rows survive only when the
    numeric value is finite and the code is not missing. The arrays are
    not retained.
    """
    paired_values, paired_codes = _paired_population(
        numeric_values,
        numeric_finite,
        category_codes,
        n_total_rows,
    )
    groups = _group_summaries(paired_values, paired_codes, categories)
    effect, corrected_effect, omnibus = _effect_and_test(
        paired_values, paired_codes, groups
    )
    return NumericCategoricalRelationship(
        left_position=left_position,
        left_label=left_label,
        right_position=right_position,
        right_label=right_label,
        numeric_position=numeric_position,
        categorical_position=categorical_position,
        n_total_rows=n_total_rows,
        n_paired=int(paired_values.size),
        groups=groups,
        effect=effect,
        corrected_effect=corrected_effect,
        omnibus=omnibus,
    )


def _read_categorical_column(
    series: pd.Series,
) -> Tuple[np.ndarray, Tuple[object, ...]]:
    """Return category codes and retained vocabulary scalars.

    The code array is a copy. The vocabulary tuple drops the pandas
    Index. Unused levels remain in that temporary tuple so codes keep
    their original indexes; relationship records later keep only levels
    that have paired observations. Values are not stringified.

    String and object storage is coded in first-appearance order. That
    coding does not replace the source dtype. Integer, floating, and
    boolean storage are not cast into categories.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("categorical relationship values must be a pandas Series")
    if not isinstance(series.dtype, pd.CategoricalDtype):
        family = classify_physical_dtype(series).family
        if family not in (PhysicalDtypeFamily.STRING, PhysicalDtypeFamily.OBJECT):
            raise TypeError(
                "numeric-categorical analysis reads a physical categorical column "
                "or string or object label storage"
            )
        return _label_storage_codes(series)
    codes = _physical_category_codes(series)
    categories = tuple(_retain_category(value) for value in series.cat.categories)
    return codes, categories


def _physical_category_codes(series: pd.Series) -> np.ndarray:
    """Return a copy of the physical category codes.

    Category scalars are not read and are not retained. ``-1`` remains
    the pandas missing sentinel.
    """
    if not isinstance(series.dtype, pd.CategoricalDtype):
        raise TypeError("physical category codes require a categorical dtype")
    codes = np.asarray(series.cat.codes.to_numpy(copy=True))
    if codes.ndim != 1:
        raise ValueError("category codes must be one-dimensional")
    if codes.dtype.kind not in {"i", "u"}:
        codes = codes.astype(np.intp, copy=False)
    return codes


def _withheld_category_vocabulary(
    *,
    left_position: int,
    left_label: object,
    right_position: int,
    right_label: object,
    numeric_position: int,
    categorical_position: int,
    n_total_rows: int,
    n_paired: int,
) -> NumericCategoricalRelationship:
    """Record one pair whose category vocabulary cannot be retained.

    No category scalar is stored. ``n_paired`` is the count already taken
    from the integer codes and the finite numeric mask. Every statistical
    component shares one reason.
    """
    effect, corrected_effect, omnibus = _unavailable_pair(
        UnavailabilityReason.CATEGORY_VOCABULARY_NOT_RETAINABLE
    )
    return NumericCategoricalRelationship(
        left_position=left_position,
        left_label=left_label,
        right_position=right_position,
        right_label=right_label,
        numeric_position=numeric_position,
        categorical_position=categorical_position,
        n_total_rows=n_total_rows,
        n_paired=n_paired,
        groups=(),
        effect=effect,
        corrected_effect=corrected_effect,
        omnibus=omnibus,
    )


def _retain_category(value: object) -> object:
    """Return a source category scalar that the relationship model can store.

    NumPy scalars become Python scalars. Tuples are retained element by
    element.     Pandas Timestamp, Timedelta, Period, and Interval values
    stay those scalars; they are not containers. A scalar outside this
    closed vocabulary raises ``AnalyticalInapplicability`` and is not
    serialized. Containers and non-finite accepted scalars still raise
    ``TypeError``.
    """
    if isinstance(value, tuple):
        return tuple(_retain_category(item) for item in value)
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(
        value, (np.ndarray, pd.Index, pd.Series, pd.DataFrame, pd.Categorical)
    ):
        raise TypeError("a category value cannot be a pandas or NumPy container")
    if (
        type(value) is bool
        or type(value) is int
        or type(value) is str
        or type(value) is bytes
    ):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise TypeError("a category value must be finite")
        if value == 0.0:
            return 0.0
        return value
    if type(value) is complex:
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise TypeError("a category value must be finite")
        return value
    if isinstance(value, (pd.Timestamp, pd.Timedelta, pd.Period, pd.Interval)):
        return value
    raise AnalyticalInapplicability(
        f"category value type {type(value).__name__} cannot be retained "
        "without stringifying it"
    )


def _paired_population(
    numeric_values: np.ndarray,
    numeric_finite: np.ndarray,
    category_codes: np.ndarray,
    n_total_rows: int,
) -> Tuple[np.ndarray, np.ndarray]:
    if (
        numeric_values.shape != (n_total_rows,)
        or numeric_finite.shape != (n_total_rows,)
        or category_codes.shape != (n_total_rows,)
    ):
        raise ValueError("relationship inputs must contain one entry per row")
    mask = np.asarray(numeric_finite, dtype=bool) & (category_codes >= 0)
    index = np.flatnonzero(mask)
    return numeric_values[index], category_codes[index]


def _group_summaries(
    values: np.ndarray,
    codes: np.ndarray,
    categories: Tuple[object, ...],
) -> Tuple[CategoricalGroupSummary, ...]:
    """One descriptive record per observed code, in vocabulary order.

    Sorting the codes follows the categorical vocabulary because those
    codes are vocabulary indexes. It does not compare category values
    with ``<``. A code that never survives pairing is omitted, so an
    unused level and a level whose numeric values are all excluded do
    not become groups.
    """
    if values.size == 0:
        return ()
    order = np.argsort(codes, kind="mergesort")
    sorted_codes = codes[order]
    sorted_values = values[order]
    starts, ends = _bounds(sorted_codes)
    groups = []
    for start, end in zip(starts.tolist(), ends.tolist()):
        code = int(sorted_codes[start])
        if code >= len(categories):
            raise ValueError("category code is outside the categorical vocabulary")
        groups.append(
            CategoricalGroupSummary(
                category=categories[code],
                descriptive=_from_finite(sorted_values[start:end]),
            )
        )
    return tuple(groups)


def _effect_and_test(
    values: np.ndarray,
    codes: np.ndarray,
    groups: Tuple[CategoricalGroupSummary, ...],
) -> _EffectAndTest:
    n_paired = int(values.size)
    n_groups = len(groups)
    if n_paired < 2:
        return _unavailable_pair(UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS)
    if n_groups < 2:
        return _unavailable_pair(UnavailabilityReason.INSUFFICIENT_GROUPS)
    image, image_reason = _working_image(values)
    if image_reason is not None:
        return _unavailable_pair(image_reason)
    shifted, shift_reason = _shift(image)
    if shift_reason is not None or shifted is None:
        return _unavailable_pair(shift_reason or UnavailabilityReason.NON_FINITE_RESULT)
    order = np.argsort(codes, kind="mergesort")
    sorted_codes = codes[order]
    sorted_shifted = shifted[order]
    starts, ends = _bounds(sorted_codes)
    sums = _sums_of_squares(sorted_shifted, starts)
    sorted_working = sorted_shifted
    if sums is None:
        scaled, scale_reason = _scale(shifted)
        if scale_reason is not None or scaled is None:
            return _unavailable_pair(
                scale_reason or UnavailabilityReason.NON_FINITE_RESULT
            )
        sorted_working = scaled[order]
        sums = _sums_of_squares(sorted_working, starts)
    if sums is None:
        return _unavailable_pair(UnavailabilityReason.NON_FINITE_RESULT)
    ss_within, ss_between = sums
    return _from_sums(
        ss_within,
        ss_between,
        n_groups=n_groups,
        n_paired=n_paired,
        sorted_scaled=sorted_working,
        starts=starts,
        ends=ends,
    )


def _working_image(
    values: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[UnavailabilityReason]]:
    """Return a float64 image that keeps observed numeric differences.

    Integers inside ``±2**53`` are already exact float64 values. Larger
    integers are replaced by exact unsigned offsets from their minimum
    when every offset round-trips through float64. A failed round-trip
    is precision collapse, not a zero effect.
    """
    kind = values.dtype.kind
    if kind == "f":
        image = np.asarray(values, dtype=np.float64)
        if image.size and not bool(np.isfinite(image).all()):
            return None, UnavailabilityReason.NON_FINITE_RESULT
        return image, None
    if kind not in {"i", "u"}:
        raise TypeError(
            "numeric-categorical analysis requires integer or floating values"
        )
    if values.size == 0:
        return np.asarray(values, dtype=np.float64), None
    minimum = int(values.min())
    maximum = int(values.max())
    if (
        -_FLOAT64_EXACT_INTEGER_LIMIT <= minimum
        and maximum <= _FLOAT64_EXACT_INTEGER_LIMIT
    ):
        return np.asarray(values, dtype=np.float64), None
    deltas = _unsigned_deltas(values)
    as_float = deltas.astype(np.float64, copy=False)
    if not bool(np.isfinite(as_float).all()):
        return None, UnavailabilityReason.PRECISION_COLLAPSED
    restored = as_float.astype(deltas.dtype, copy=False)
    if not np.array_equal(restored, deltas):
        return None, UnavailabilityReason.PRECISION_COLLAPSED
    return np.asarray(as_float, dtype=np.float64), None


def _unsigned_deltas(values: np.ndarray) -> np.ndarray:
    """Exact non-negative offsets from the signed minimum.

    This is the same unsigned subtraction as Numeric descriptive
    centering. The minimum does not have to sit at index 0. The
    difference fits in the unsigned width of the source dtype, so the
    subtraction does not overflow a signed integer.
    """
    contiguous = np.ascontiguousarray(values)
    unsigned_dtype = np.dtype(contiguous.dtype.str.replace("i", "u"))
    bits = contiguous.view(unsigned_dtype)
    minimum_bits = bits[int(np.argmin(contiguous))]
    return np.subtract(bits, minimum_bits, dtype=unsigned_dtype)


def _shift(
    image: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[UnavailabilityReason]]:
    """Subtract the first value. ANOVA is unchanged by that translation.

    A non-finite difference is not turned into a zero effect. Ordinary
    values stay unscaled. Scaling is a later fallback when squares of
    these shifted values overflow.
    """
    if image.size == 0:
        return image, None
    origin = float(image[0])
    if not math.isfinite(origin):
        return None, UnavailabilityReason.NON_FINITE_RESULT
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        shifted = np.subtract(image, origin)
    if not bool(np.isfinite(shifted).all()):
        return None, UnavailabilityReason.NON_FINITE_RESULT
    return shifted, None


def _scale(
    shifted: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[UnavailabilityReason]]:
    """Divide by the maximum absolute shifted value.

    Eta squared and the F ratio are unchanged by a positive scale.
    The scale is used only after unscaled squares fail to stay finite.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        scale = float(np.max(np.abs(shifted)))
        if scale == 0.0:
            return shifted, None
        if not math.isfinite(scale):
            return None, UnavailabilityReason.NON_FINITE_RESULT
        scaled = shifted / scale
    if not bool(np.isfinite(scaled).all()):
        return None, UnavailabilityReason.NON_FINITE_RESULT
    return scaled, None


def _bounds(codes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Half-open spans of a code array that is already sorted."""
    if codes.size == 0:
        empty = np.zeros(0, dtype=np.intp)
        return empty, empty
    changes = np.flatnonzero(codes[1:] != codes[:-1]) + 1
    change_index = changes.astype(np.intp, copy=False)
    starts = np.concatenate((np.zeros(1, dtype=np.intp), change_index))
    ends = np.concatenate((change_index, np.array([codes.size], dtype=np.intp)))
    return starts, ends


def _sums_of_squares(
    sorted_values: np.ndarray,
    starts: np.ndarray,
) -> Optional[Tuple[float, float]]:
    """Between-group and within-group sums of squares from sorted groups.

    ``SS_within`` is the sum of squared deviations from each group mean.
    ``SS_between`` is the weighted sum of squared deviations of those
    means from the grand mean. The two are not computed from
    ``sum(x**2) - n * mean**2``.
    """
    counts = np.diff(
        np.concatenate((starts, np.array([sorted_values.size], dtype=np.intp)))
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        sums = np.add.reduceat(sorted_values, starts)
        means = sums / counts
        grand = float(np.sum(sums, dtype=np.float64) / sorted_values.size)
        expanded = np.repeat(means, counts)
        deviations = sorted_values - expanded
        ss_within = float(np.dot(deviations, deviations))
        centered_means = means - grand
        ss_between = float(np.dot(counts, centered_means * centered_means))
    if not math.isfinite(ss_within) or not math.isfinite(ss_between):
        return None
    if ss_within < 0.0:
        if -ss_within <= _ETA_TOLERANCE:
            ss_within = 0.0
        else:
            return None
    if ss_between < 0.0:
        magnitude = max(abs(ss_within), abs(ss_between), 1.0)
        if -ss_between <= _ETA_TOLERANCE * magnitude:
            ss_between = 0.0
        else:
            return None
    return ss_within, ss_between


def _from_sums(
    ss_within: float,
    ss_between: float,
    *,
    n_groups: int,
    n_paired: int,
    sorted_scaled: np.ndarray,
    starts: np.ndarray,
    ends: np.ndarray,
) -> _EffectAndTest:
    """Turn sums of squares into eta squared and one-way ANOVA.

    Eta squared is ``SS_between / SS_total``. It is undefined when
    ``SS_total`` is zero. The F ratio is
    ``(SS_between / (k - 1)) / (SS_within / (N - k))`` when ``N > k``
    and ``SS_within`` is positive. ``k`` is the number of observed
    groups and ``N`` is the paired count.

    The null hypothesis is that every group has the same population
    mean. The p-value is the upper tail of the F distribution on
    ``(k - 1, N - k)`` degrees of freedom, taken from
    ``scipy.stats.f_oneway`` without keyword arguments. When within-group
    variation is zero and between-group variation is positive, eta
    squared is 1 and classical ANOVA inference is unavailable. The F
    ratio would be infinite when within-group degrees of freedom remain,
    and that infinite value is not stored. When every group has one
    observation, those degrees of freedom are zero and the F test is
    also undefined; eta squared remains 1 when the observations are not
    all equal.
    """
    ss_total = ss_within + ss_between
    if ss_total == 0.0:
        return _unavailable_pair(UnavailabilityReason.ZERO_TOTAL_VARIATION)
    if not math.isfinite(ss_total) or ss_total < 0.0:
        return _unavailable_pair(UnavailabilityReason.NON_FINITE_RESULT)
    df_between = n_groups - 1
    df_within = n_paired - n_groups
    if ss_within == 0.0:
        effect = _available_effect(1.0)
        if df_within == 0:
            return (
                effect,
                _unavailable_corrected(
                    UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
                ),
                _unavailable_anova(
                    UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
                ),
            )
        return (
            effect,
            _available_corrected(1.0),
            _unavailable_anova(UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION),
        )
    eta = _eta_squared(ss_between, ss_total)
    if eta is None:
        return _unavailable_pair(UnavailabilityReason.NON_FINITE_RESULT)
    if df_within <= 0:
        return _unavailable_pair(UnavailabilityReason.NON_FINITE_RESULT)
    corrected = _corrected_effect(
        ss_between, ss_within, ss_total, df_between, df_within
    )
    statistic = (ss_between / df_between) / (ss_within / df_within)
    if statistic < 0.0 and -statistic <= _ETA_TOLERANCE:
        statistic = 0.0
    if not math.isfinite(statistic) or statistic < 0.0:
        return (
            _available_effect(eta),
            corrected,
            _unavailable_anova(UnavailabilityReason.NON_FINITE_RESULT),
        )
    if statistic == 0.0:
        statistic = 0.0
    samples = tuple(
        sorted_scaled[start:end] for start, end in zip(starts.tolist(), ends.tolist())
    )
    p_value = _anova_p_value(samples)
    frequentist = (
        _available_p(p_value)
        if p_value is not None
        else _unavailable_frequentist(UnavailabilityReason.NON_FINITE_RESULT)
    )
    return (
        _available_effect(eta),
        corrected,
        OmnibusAnovaResult(
            method=OmnibusTestMethod.ONE_WAY_ANOVA,
            statistic_availability=ResultAvailability.AVAILABLE,
            statistic=statistic,
            statistic_reason=None,
            frequentist=frequentist,
        ),
    )


def _corrected_effect(
    ss_between: float,
    ss_within: float,
    ss_total: float,
    df_between: int,
    df_within: int,
) -> GroupEffectEstimate:
    """Epsilon squared from the same sums that produced eta squared."""
    value = _epsilon_squared(ss_between, ss_within, ss_total, df_between, df_within)
    if value is None:
        return _unavailable_corrected(UnavailabilityReason.NON_FINITE_RESULT)
    return _available_corrected(value)


def _epsilon_squared(
    ss_between: float,
    ss_within: float,
    ss_total: float,
    df_between: int,
    df_within: int,
) -> Optional[float]:
    """Kelley's epsilon squared. A negative result is a defined estimate."""
    if df_within <= 0 or ss_total <= 0.0 or not math.isfinite(ss_total):
        return None
    if ss_within == 0.0:
        return 1.0 if ss_between > 0.0 else None
    mean_square_within = ss_within / df_within
    if not math.isfinite(mean_square_within):
        return None
    numerator = ss_between - df_between * mean_square_within
    if not math.isfinite(numerator):
        return None
    value = numerator / ss_total
    if not math.isfinite(value):
        return None
    if value > 1.0:
        if value <= 1.0 + _ETA_TOLERANCE:
            return 1.0
        return None
    floor = -df_between / df_within
    if value < floor and floor - value > _ETA_TOLERANCE:
        return None
    if value < floor:
        value = floor
    if value == 0.0:
        return 0.0
    return float(value)


def _eta_squared(ss_between: float, ss_total: float) -> Optional[float]:
    if ss_between == 0.0:
        return 0.0
    ratio = ss_between / ss_total
    if not math.isfinite(ratio):
        return None
    if ratio < 0.0:
        if ratio >= -_ETA_TOLERANCE:
            return 0.0
        return None
    if ratio > 1.0:
        if ratio <= 1.0 + _ETA_TOLERANCE:
            return 1.0
        return None
    if ratio == 0.0:
        return 0.0
    return float(ratio)


def _anova_p_value(samples: Tuple[np.ndarray, ...]) -> Optional[float]:
    """Upper-tail p-value from ``scipy.stats.f_oneway(*samples)``.

    No keyword arguments are passed. Runtime warnings from a degenerate
    library call are ignored here; a non-finite p-value is unavailable.
    Programmer errors other than ``ValueError`` and ``FloatingPointError``
    are not caught.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = f_oneway(*samples)
    except (ValueError, FloatingPointError):
        return None
    p_value = getattr(result, "pvalue", None)
    if p_value is None:
        try:
            p_value = result[1]  # type: ignore[index]
        except (TypeError, IndexError, KeyError):
            return None
    return _as_p_value(p_value)


def _as_p_value(value: object) -> Optional[float]:
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
    if number < 0.0 or number > 1.0:
        if 0.0 > number >= -_ETA_TOLERANCE:
            return 0.0
        if 1.0 < number <= 1.0 + _ETA_TOLERANCE:
            return 1.0
        return None
    if number == 0.0:
        return 0.0
    return number


def _unavailable_pair(reason: UnavailabilityReason) -> _EffectAndTest:
    return (
        _unavailable_effect(reason),
        _unavailable_corrected(reason),
        _unavailable_anova(reason),
    )


def _unavailable_effect(reason: UnavailabilityReason) -> GroupEffectEstimate:
    return GroupEffectEstimate(
        method=GroupEffectMethod.ETA_SQUARED,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _available_effect(value: float) -> GroupEffectEstimate:
    return GroupEffectEstimate(
        method=GroupEffectMethod.ETA_SQUARED,
        availability=ResultAvailability.AVAILABLE,
        value=value,
        reason=None,
    )


def _unavailable_corrected(reason: UnavailabilityReason) -> GroupEffectEstimate:
    return GroupEffectEstimate(
        method=GroupEffectMethod.EPSILON_SQUARED,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _available_corrected(value: float) -> GroupEffectEstimate:
    return GroupEffectEstimate(
        method=GroupEffectMethod.EPSILON_SQUARED,
        availability=ResultAvailability.AVAILABLE,
        value=value,
        reason=None,
    )


def _unavailable_anova(reason: UnavailabilityReason) -> OmnibusAnovaResult:
    return OmnibusAnovaResult(
        method=OmnibusTestMethod.ONE_WAY_ANOVA,
        statistic_availability=ResultAvailability.UNAVAILABLE,
        statistic=None,
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


def _available_p(p_value: float) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=ResultAvailability.AVAILABLE,
        p_value=p_value,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )
