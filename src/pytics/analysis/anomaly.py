"""Univariate numeric anomaly evidence for one DataFrame.

An anomaly is an observation that is unusual under a stated method and a
stated population. It is not an error, an invalid value, or a row to
delete. This module does not repair, cap, winsorize, impute, or label
values as wrong.

The only method is Tukey's inner fence on a column whose selected
semantic type is Numeric. For the finite population already described
by ``NumericDescriptiveAnalysis``:

    lower fence = Q1 - (3/2) * IQR
    upper fence = Q3 + (3/2) * IQR

Q1, Q3, and the interquartile range are the retained descriptive facts.
They are not recomputed. Integer and fractional landmarks keep exact
fence arithmetic. Float landmarks use float64 arithmetic, and a
non-finite fence is not applied. The coefficient ``3/2`` is Tukey's conventional
inner fence. It is a resistant rule of thumb, not a probability and not
a mild-versus-extreme scale. Values strictly outside the fences are
anomalies under this method. A value on the fence is not.

Missing values stay in the missingness result. Positive and negative
infinity are counted apart from the finite population and are not IQR
anomalies. A zero interquartile range does not classify the rows that
differ from the quartile. Boolean minority classes, rare categories,
identifiers, datetimes, durations, and text are not this method.

Row identity is the physical row position. The DataFrame index is not.
Every anomalous position is retained, in that order. There is no score
and no severity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import numpy as np
import pandas as pd

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus

# Tukey's inner fence. The outer fence at 3 IQR is not a second method.
_FENCE_COEFFICIENT = Fraction(3, 2)

# Integers in this closed interval survive a float64 cast unchanged.
_EXACT_INTEGER_LIMIT = 1 << 53

QuantileNumber = Union[int, float, Fraction]
ObservedNumber = Union[int, float]


class AnomalyDirection(Enum):
    """Which Tukey fence a finite observation lies strictly beyond.

    ``BELOW`` is less than the lower fence. ``ABOVE`` is greater than
    the upper fence. Neither name is a judgment about the value.
    """

    BELOW = "below"
    ABOVE = "above"


class NumericAnomalyMethod(Enum):
    """The univariate detector that produced a numeric anomaly record.

    ``TUKEY_IQR`` is the only member. Availability of that method is a
    status on the column record, not another method.
    """

    TUKEY_IQR = "tukey_iqr"


class NumericAnomalyStatus(Enum):
    """Whether Tukey fences were applied to one selected Numeric column.

    ``AVAILABLE`` means the fences were calculated. Zero anomalies is
    still available. The other members mean the method was not applied.
    A missing record is not one of these states: ineligible columns are
    coverage counts, not numeric records.
    """

    AVAILABLE = "available"
    INSUFFICIENT_FINITE_POPULATION = "insufficient_finite_population"
    ZERO_IQR = "zero_iqr"
    IQR_UNAVAILABLE = "iqr_unavailable"
    NUMERIC_PRECISION_UNSAFE = "numeric_precision_unsafe"


class AnomalyIneligibility(Enum):
    """Why a column is not a numeric anomaly candidate.

    The reason is the selected semantic type, or the absence of one.
    ``UNRESOLVED`` is insufficient evidence. ``AMBIGUOUS`` is a separate
    resolution state. Neither is a semantic type. Numeric is absent here
    because a selected Numeric column is eligible or, when its quartile
    profile was not retained, counted apart from this list.
    """

    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TIMEDELTA = "timedelta"
    IDENTIFIER = "identifier"
    TEXT = "text"
    EMPTY = "empty"
    CONSTANT = "constant"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"


_INELIGIBLE_TYPES = {
    SemanticType.BOOLEAN: AnomalyIneligibility.BOOLEAN,
    SemanticType.CATEGORICAL: AnomalyIneligibility.CATEGORICAL,
    SemanticType.DATETIME: AnomalyIneligibility.DATETIME,
    SemanticType.TIMEDELTA: AnomalyIneligibility.TIMEDELTA,
    SemanticType.IDENTIFIER: AnomalyIneligibility.IDENTIFIER,
    SemanticType.TEXT: AnomalyIneligibility.TEXT,
    SemanticType.EMPTY: AnomalyIneligibility.EMPTY,
    SemanticType.CONSTANT: AnomalyIneligibility.CONSTANT,
}

_UNAVAILABLE_ORDER = (
    NumericAnomalyStatus.INSUFFICIENT_FINITE_POPULATION,
    NumericAnomalyStatus.ZERO_IQR,
    NumericAnomalyStatus.IQR_UNAVAILABLE,
    NumericAnomalyStatus.NUMERIC_PRECISION_UNSAFE,
)


@dataclass(frozen=True)
class NumericAnomalyObservation:
    """One finite value strictly outside a Tukey fence.

    ``row_position`` is the physical row. It is not a DataFrame index
    label. ``value`` is that row's finite number. ``direction`` says
    which fence it crossed. The same value on another row is another
    observation.
    """

    row_position: int
    value: ObservedNumber
    direction: AnomalyDirection

    def __post_init__(self) -> None:
        if type(self.row_position) is not int or self.row_position < 0:
            raise ValueError("row position must be a non-negative int")
        _require_observed_number(self.value, "value")
        if not isinstance(self.direction, AnomalyDirection):
            raise TypeError("direction must be an AnomalyDirection")


@dataclass(frozen=True)
class NumericAnomalyColumn:
    """Tukey evidence for one selected Numeric column.

    Population counts reconcile with the retained numeric profile.
    ``n_missing`` is copied so the finite population can be checked. It
    does not make a missing value an anomaly. Infinity counts are the
    same kind of reconciliation. They are not IQR observations.

    ``method`` and ``fence_coefficient`` are present only when the fences
    were applied. ``below_count`` and ``above_count`` are present only
    then. Zero means the method ran and found nothing on that side.
    ``None`` means the method was not applied.
    """

    position: int
    label: object
    status: NumericAnomalyStatus
    n_rows: int
    n_missing: int
    finite_count: int
    positive_infinity_count: int
    negative_infinity_count: int
    method: Optional[NumericAnomalyMethod]
    fence_coefficient: Optional[Fraction]
    q1: Optional[QuantileNumber]
    q3: Optional[QuantileNumber]
    iqr: Optional[QuantileNumber]
    lower_fence: Optional[QuantileNumber]
    upper_fence: Optional[QuantileNumber]
    below_count: Optional[int]
    above_count: Optional[int]
    observations: Tuple[NumericAnomalyObservation, ...]

    def __post_init__(self) -> None:
        if type(self.position) is not int or self.position < 0:
            raise ValueError("position must be a non-negative int")
        if not isinstance(self.status, NumericAnomalyStatus):
            raise TypeError("status must be a NumericAnomalyStatus")
        _require_count(self.n_rows, "n_rows")
        _require_count(self.n_missing, "n_missing")
        _require_count(self.finite_count, "finite_count")
        _require_count(self.positive_infinity_count, "positive_infinity_count")
        _require_count(self.negative_infinity_count, "negative_infinity_count")
        accounted = (
            self.n_missing
            + self.finite_count
            + self.positive_infinity_count
            + self.negative_infinity_count
        )
        if accounted != self.n_rows:
            raise ValueError(
                "missing, finite, and infinite counts must account for every row"
            )
        if not isinstance(self.observations, tuple):
            raise TypeError("observations must be a tuple")
        _require_reference_fields(self)
        _require_observations(self)


@dataclass(frozen=True)
class AnomalyUnavailableCount:
    """How many eligible columns share one reason the method was not applied.

    ``n_columns`` is at least one. An unused status is omitted.
    """

    status: NumericAnomalyStatus
    n_columns: int

    def __post_init__(self) -> None:
        if self.status not in _UNAVAILABLE_ORDER:
            raise ValueError("an unavailable count names a status that blocks fences")
        if type(self.n_columns) is not int or self.n_columns < 1:
            raise ValueError("n_columns must be a positive int")


@dataclass(frozen=True)
class AnomalyIneligibleCount:
    """How many columns share one semantic reason they were not candidates.

    ``n_columns`` is at least one. A reason with no columns is omitted.
    """

    reason: AnomalyIneligibility
    n_columns: int

    def __post_init__(self) -> None:
        if not isinstance(self.reason, AnomalyIneligibility):
            raise TypeError("reason must be an AnomalyIneligibility")
        if type(self.n_columns) is not int or self.n_columns < 1:
            raise ValueError("n_columns must be a positive int")


@dataclass(frozen=True)
class AnomalyCoverage:
    """How numeric anomaly analysis covered one dataset.

    ``n_eligible`` columns are selected Numeric columns with a retained
    finite-population profile. ``n_analyzed`` is the subset whose Tukey
    fences were applied, including columns with no anomalies.
    ``n_unavailable`` is the eligible subset whose fences were not applied.
    ``n_ineligible`` columns are not numeric anomaly candidates.
    ``n_numeric_profile_absent`` counts selected Numeric columns that did
    not retain the quartile profile this method reads. ``analyze_series``
    retains that profile, so the count is zero on that path. It is not
    a claim that those columns had no anomalies.

    ``n_columns`` is the sum of eligible, ineligible, and profile-absent
    columns. A zero analyzed count is not a zero anomaly count.
    """

    n_columns: int
    n_eligible: int
    n_analyzed: int
    n_unavailable: int
    n_ineligible: int
    n_numeric_profile_absent: int
    unavailable: Tuple[AnomalyUnavailableCount, ...]
    ineligible: Tuple[AnomalyIneligibleCount, ...]

    def __post_init__(self) -> None:
        _require_count(self.n_columns, "n_columns")
        _require_count(self.n_eligible, "n_eligible")
        _require_count(self.n_analyzed, "n_analyzed")
        _require_count(self.n_unavailable, "n_unavailable")
        _require_count(self.n_ineligible, "n_ineligible")
        _require_count(self.n_numeric_profile_absent, "n_numeric_profile_absent")
        if self.n_analyzed + self.n_unavailable != self.n_eligible:
            raise ValueError("analyzed and unavailable columns must equal eligible")
        if (
            self.n_eligible + self.n_ineligible + self.n_numeric_profile_absent
            != self.n_columns
        ):
            raise ValueError(
                "eligible, ineligible, and profile-absent columns must equal n_columns"
            )
        _require_status_counts(self.unavailable, self.n_unavailable, "unavailable")
        _require_reason_counts(self.ineligible, self.n_ineligible)


@dataclass(frozen=True)
class AnomalyAnalysis:
    """Retained univariate numeric anomaly evidence for one dataset.

    ``numeric_univariate`` has one record per eligible column, in physical
    column order. There is no multivariate result. Ineligible columns
    appear only in ``coverage``.
    """

    coverage: AnomalyCoverage
    numeric_univariate: Tuple[NumericAnomalyColumn, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, AnomalyCoverage):
            raise TypeError("coverage must be an AnomalyCoverage")
        if not isinstance(self.numeric_univariate, tuple):
            raise TypeError("numeric_univariate must be a tuple")
        if len(self.numeric_univariate) != self.coverage.n_eligible:
            raise ValueError("numeric records must equal the eligible count")
        analyzed = 0
        unavailable: dict[NumericAnomalyStatus, int] = {}
        previous = -1
        for record in self.numeric_univariate:
            if not isinstance(record, NumericAnomalyColumn):
                raise TypeError("numeric_univariate must contain numeric records")
            if record.position <= previous:
                raise ValueError("numeric anomaly records must follow column order")
            previous = record.position
            if record.status is NumericAnomalyStatus.AVAILABLE:
                analyzed += 1
            else:
                unavailable[record.status] = unavailable.get(record.status, 0) + 1
        if analyzed != self.coverage.n_analyzed:
            raise ValueError("analyzed coverage must match available numeric records")
        expected = tuple(
            AnomalyUnavailableCount(status, unavailable[status])
            for status in _UNAVAILABLE_ORDER
            if unavailable.get(status, 0)
        )
        if self.coverage.unavailable != expected:
            raise ValueError("unavailable coverage must match numeric record statuses")


@dataclass(frozen=True)
class AnomalySummary:
    """Source-independent copy of retained numeric anomaly evidence.

    The copy is built from an existing ``DatasetAnalysis``. It does not
    read a DataFrame and does not classify rows again. It is not a
    finding and it has no severity.
    """

    coverage: AnomalyCoverage
    numeric_univariate: Tuple[NumericAnomalyColumn, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, AnomalyCoverage):
            raise TypeError("coverage must be an AnomalyCoverage")
        if not isinstance(self.numeric_univariate, tuple):
            raise TypeError("numeric_univariate must be a tuple")
        AnomalyAnalysis(
            coverage=self.coverage,
            numeric_univariate=self.numeric_univariate,
        )


def collect_anomaly_analysis(
    frame: pd.DataFrame,
    columns: Sequence[ColumnAnalysis],
) -> AnomalyAnalysis:
    """Locate finite numeric values that fall strictly outside Tukey fences.

    Quartiles come from the numeric descriptive result already stored on
    ``columns``. This function does not calculate them again. It reads a
    column only when that result can support fences. The DataFrame is not
    modified and is not retained. Index labels are not read.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("collect_anomaly_analysis expects a pandas DataFrame")
    column_tuple = _column_tuple(columns)
    n_rows = _require_aligned(frame, column_tuple)
    records = []
    for column in column_tuple:
        profile = _profile(column)
        if profile is None:
            continue
        _status, fences = _decision(profile[0])
        if fences is None:
            observations: Tuple[NumericAnomalyObservation, ...] = ()
        else:
            observations = _locate(
                frame.iloc[:, column.position],
                fences[0],
                fences[1],
            )
        records.append(_record_for(column, observations, n_rows))
    return anomaly_analysis_for_columns(
        column_tuple,
        n_rows=n_rows,
        records=tuple(records),
    )


def anomaly_analysis_for_columns(
    columns: Sequence[ColumnAnalysis],
    *,
    n_rows: int,
    records: Optional[Sequence[NumericAnomalyColumn]] = None,
) -> AnomalyAnalysis:
    """Attach numeric anomaly records to coverage taken from selected types.

    This does not read values. ``records`` must already be the eligible
    columns, in physical order. When ``records`` is omitted, eligible
    columns are recorded from their retained quartiles with no located
    observations. That shell is not a scan.
    """
    _require_count(n_rows, "n_rows")
    column_tuple = _column_tuple(columns)
    profiled = tuple(column for column in column_tuple if _profile(column) is not None)
    if records is None:
        built = tuple(_record_for(column, (), n_rows) for column in profiled)
    else:
        if not isinstance(records, tuple):
            raise TypeError("numeric anomaly records must be a tuple")
        if len(records) != len(profiled):
            raise ValueError(
                "numeric anomaly records must match the eligible Numeric columns"
            )
        built_list = []
        for column, record in zip(profiled, records):
            if not isinstance(record, NumericAnomalyColumn):
                raise TypeError("numeric anomaly records must be numeric records")
            expected = _record_for(column, record.observations, n_rows)
            if record != expected:
                raise ValueError(
                    "numeric anomaly record must match the retained numeric profile"
                )
            built_list.append(expected)
        built = tuple(built_list)
    return AnomalyAnalysis(
        coverage=_coverage(column_tuple, built),
        numeric_univariate=built,
    )


def build_anomaly_summary(analysis: object) -> AnomalySummary:
    """Copy retained numeric anomaly evidence into a summary.

    The argument must already be a ``DatasetAnalysis``. A DataFrame is
    not accepted. Rows are not classified again.
    """
    from pytics.analysis.dataset import DatasetAnalysis as DatasetAnalysisType

    if not isinstance(analysis, DatasetAnalysisType):
        raise TypeError("build_anomaly_summary expects a DatasetAnalysis")
    retained = analysis.anomaly_analysis
    return AnomalySummary(
        coverage=_copy_coverage(retained.coverage),
        numeric_univariate=tuple(
            _copy_column(record) for record in retained.numeric_univariate
        ),
    )


def _require_anomaly_attachment(
    analysis: AnomalyAnalysis,
    columns: Tuple[ColumnAnalysis, ...],
    *,
    n_rows: int,
) -> None:
    """Check retained anomaly evidence against the column analyses."""
    if not isinstance(analysis, AnomalyAnalysis):
        raise TypeError("anomaly_analysis must be an AnomalyAnalysis")
    expected = anomaly_analysis_for_columns(
        columns,
        n_rows=n_rows,
        records=analysis.numeric_univariate,
    )
    if analysis != expected:
        raise ValueError("anomaly analysis must match the retained numeric profiles")


def _record_for(
    column: ColumnAnalysis,
    observations: Tuple[NumericAnomalyObservation, ...],
    n_rows: int,
) -> NumericAnomalyColumn:
    """Build one numeric record from retained facts and located rows."""
    profile = _profile(column)
    if profile is None:
        raise ValueError("a numeric anomaly record requires a retained profile")
    descriptive, positive_infinity, negative_infinity = profile
    if column.evidence.basic.n_total != n_rows:
        raise ValueError("anomaly row count must equal the column row count")
    status, fences = _decision(descriptive)
    below_count: Optional[int] = None
    above_count: Optional[int] = None
    method = None
    coefficient = None
    lower = None
    upper = None
    if status is NumericAnomalyStatus.AVAILABLE:
        if fences is None:
            raise ValueError("available Tukey fences must be present")
        lower, upper = fences
        method = NumericAnomalyMethod.TUKEY_IQR
        coefficient = _FENCE_COEFFICIENT
        below_count, above_count = _count_directions(observations, lower, upper, n_rows)
    elif len(observations) != 0:
        raise ValueError("observations are recorded only when Tukey fences are applied")
    iqr = None
    if status is not NumericAnomalyStatus.INSUFFICIENT_FINITE_POPULATION:
        iqr = descriptive.interquartile_range
    return NumericAnomalyColumn(
        position=column.position,
        label=column.label,
        status=status,
        n_rows=n_rows,
        n_missing=column.evidence.basic.n_missing,
        finite_count=descriptive.finite_count,
        positive_infinity_count=positive_infinity,
        negative_infinity_count=negative_infinity,
        method=method,
        fence_coefficient=coefficient,
        q1=descriptive.q1,
        q3=descriptive.q3,
        iqr=iqr,
        lower_fence=lower,
        upper_fence=upper,
        below_count=below_count,
        above_count=above_count,
        observations=observations,
    )


def _decision(
    descriptive: NumericDescriptiveAnalysis,
) -> Tuple[NumericAnomalyStatus, Optional[Tuple[QuantileNumber, QuantileNumber]]]:
    """Choose the Tukey status from the retained descriptive profile.

    The finite count, Q1, Q3, and interquartile range are that profile's
    values. No second quantile is calculated. No minimum sample size is
    applied: one finite value has interquartile range zero, and two finite
    values are fenced when that range is positive.
    """
    if descriptive.finite_count == 0:
        return NumericAnomalyStatus.INSUFFICIENT_FINITE_POPULATION, None
    iqr = descriptive.interquartile_range
    if iqr is None:
        return NumericAnomalyStatus.IQR_UNAVAILABLE, None
    if iqr == 0:
        return NumericAnomalyStatus.ZERO_IQR, None
    if iqr < 0:
        raise ValueError("interquartile range cannot be negative")
    if descriptive.q1 is None or descriptive.q3 is None:
        raise ValueError("quartiles are required when the interquartile range exists")
    fences = _fences(descriptive.q1, descriptive.q3, iqr)
    if fences is None:
        return NumericAnomalyStatus.NUMERIC_PRECISION_UNSAFE, None
    return NumericAnomalyStatus.AVAILABLE, fences


def _fences(
    q1: QuantileNumber,
    q3: QuantileNumber,
    iqr: QuantileNumber,
) -> Optional[Tuple[QuantileNumber, QuantileNumber]]:
    """Return exact Tukey fences, or None when a float fence will not fit.

    Arithmetic uses the exact rational value of each retained landmark,
    including a float64 value's exact rational. Integer and fractional
    landmarks may produce an integer, an exact float, or a ``Fraction``.
    A float landmark whose fence is not a finite float is not stored as
    a rounded substitute.
    """
    if any(type(value) is float for value in (q1, q3, iqr)):
        return _float_fences(q1, q3, iqr)
    lower = _as_fraction(q1) - _FENCE_COEFFICIENT * _as_fraction(iqr)
    upper = _as_fraction(q3) + _FENCE_COEFFICIENT * _as_fraction(iqr)
    if not lower < upper:
        raise ValueError("Tukey fences must be strictly ordered when IQR is positive")
    return (_normalize_landmark(lower), _normalize_landmark(upper))


def _float_fences(
    q1: QuantileNumber,
    q3: QuantileNumber,
    iqr: QuantileNumber,
) -> Optional[Tuple[float, float]]:
    """Float64 fences for landmarks the descriptive profile already stored as floats.

    ``3/2`` is exact in float64. A non-finite fence is not a rounded
    substitute and is not applied. Integer landmarks do not use this path.
    """
    lower = float(q1) - float(_FENCE_COEFFICIENT) * float(iqr)
    upper = float(q3) + float(_FENCE_COEFFICIENT) * float(iqr)
    if not (math.isfinite(lower) and math.isfinite(upper) and lower < upper):
        return None
    return (_signed_float(lower), _signed_float(upper))


def _locate(
    series: pd.Series,
    lower: QuantileNumber,
    upper: QuantileNumber,
) -> Tuple[NumericAnomalyObservation, ...]:
    """Return anomalous physical rows of one numeric Series.

    The Series must use integer or floating storage. Missing values and
    non-finite floats are skipped. Comparison does not cast an integer
    outside the exact float64 range through float64.
    """
    values, mask, integer = _finite_population(series)
    below = _less_than(values, mask, lower, integer)
    above = _greater_than(values, mask, upper, integer)
    if np.any(below & above):
        raise ValueError("a value cannot fall beyond both Tukey fences")
    observations = []
    for position in np.flatnonzero(below | above):
        index = int(position)
        direction = (
            AnomalyDirection.BELOW if bool(below[index]) else AnomalyDirection.ABOVE
        )
        observations.append(
            NumericAnomalyObservation(
                row_position=index,
                value=_python_number(values[index], integer),
                direction=direction,
            )
        )
    return tuple(observations)


def _finite_population(series: pd.Series) -> Tuple[np.ndarray, np.ndarray, bool]:
    """Return storage values, a finite mask, and whether the values are integers."""
    if not isinstance(series, pd.Series):
        raise TypeError("numeric anomaly location expects a pandas Series")
    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype) or pd.api.types.is_complex_dtype(dtype):
        raise TypeError(
            "numeric anomaly location does not coerce boolean or complex values"
        )
    if pd.api.types.is_float_dtype(dtype):
        return _float_population(series)
    if pd.api.types.is_integer_dtype(dtype):
        return _integer_population(series)
    raise TypeError(
        "numeric anomaly location applies only to integer and floating values"
    )


def _float_population(series: pd.Series) -> Tuple[np.ndarray, np.ndarray, bool]:
    if isinstance(series.dtype, pd.api.extensions.ExtensionDtype):
        values = series.to_numpy(dtype=np.float64, na_value=np.nan, copy=True)
    else:
        values = series.to_numpy(dtype=np.float64, copy=True)
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("numeric anomaly values must be one-dimensional")
    return values, np.isfinite(values), False


def _integer_population(series: pd.Series) -> Tuple[np.ndarray, np.ndarray, bool]:
    mask = np.asarray(series.notna().to_numpy(dtype=bool, copy=True))
    if isinstance(series.dtype, pd.api.extensions.ExtensionDtype):
        numpy_dtype = np.dtype(series.dtype.numpy_dtype)
        values = series.to_numpy(dtype=numpy_dtype, na_value=0, copy=True)
    else:
        values = series.to_numpy(copy=True)
    values = np.asarray(values)
    if values.ndim != 1 or values.shape != mask.shape:
        raise ValueError("numeric anomaly values must contain one entry per row")
    if values.dtype.kind not in {"i", "u"}:
        raise TypeError("integer anomaly values must stay integers")
    return values, mask, True


def _less_than(
    values: np.ndarray,
    mask: np.ndarray,
    fence: QuantileNumber,
    integer: bool,
) -> np.ndarray:
    return _compare(values, mask, fence, integer, below=True)


def _greater_than(
    values: np.ndarray,
    mask: np.ndarray,
    fence: QuantileNumber,
    integer: bool,
) -> np.ndarray:
    return _compare(values, mask, fence, integer, below=False)


def _compare(
    values: np.ndarray,
    mask: np.ndarray,
    fence: QuantileNumber,
    integer: bool,
    *,
    below: bool,
) -> np.ndarray:
    """Compare finite values with one fence without collapsing integers."""
    if not integer and type(fence) is float:
        compared = values < fence if below else values > fence
        return mask & compared
    if not integer and type(fence) is int and abs(fence) <= _EXACT_INTEGER_LIMIT:
        compared = values < fence if below else values > fence
        return mask & compared
    if integer and type(fence) is int and values.dtype.kind in {"i", "u"}:
        direct = _integer_compare(values, fence, below)
        if direct is not None:
            return mask & direct
    out = np.zeros(values.shape[0], dtype=bool)
    limit = _as_fraction(fence)
    for position in np.flatnonzero(mask):
        index = int(position)
        number = int(values[index]) if integer else float(values[index])
        exact = _as_fraction(number)
        out[index] = exact < limit if below else exact > limit
    return out


def _integer_compare(
    values: np.ndarray,
    fence: int,
    below: bool,
) -> Optional[np.ndarray]:
    """Return a dtype-native comparison, or None when the fence does not fit.

    An unsigned value is never less than a non-positive fence. It is
    always greater than a negative fence. Those cases do not cast.
    """
    info = np.iinfo(values.dtype)
    if values.dtype.kind == "u":
        if below and fence <= 0:
            return np.zeros(values.shape[0], dtype=bool)
        if not below and fence < 0:
            return np.ones(values.shape[0], dtype=bool)
        if fence > int(info.max):
            return (
                np.ones(values.shape[0], dtype=bool)
                if below
                else np.zeros(values.shape[0], dtype=bool)
            )
    elif fence < int(info.min):
        return (
            np.zeros(values.shape[0], dtype=bool)
            if below
            else np.ones(values.shape[0], dtype=bool)
        )
    elif fence > int(info.max):
        return (
            np.ones(values.shape[0], dtype=bool)
            if below
            else np.zeros(values.shape[0], dtype=bool)
        )
    if int(info.min) <= fence <= int(info.max):
        native = np.array(fence, dtype=values.dtype)
        return values < native if below else values > native
    return None


def _count_directions(
    observations: Tuple[NumericAnomalyObservation, ...],
    lower: QuantileNumber,
    upper: QuantileNumber,
    n_rows: int,
) -> Tuple[int, int]:
    """Count fence crossings and reject an observation the fences do not support."""
    below = 0
    above = 0
    previous = -1
    for observation in observations:
        if observation.row_position <= previous or observation.row_position >= n_rows:
            raise ValueError("anomaly row positions must be increasing and in range")
        previous = observation.row_position
        exact = _as_fraction(observation.value)
        if observation.direction is AnomalyDirection.BELOW:
            if not exact < _as_fraction(lower):
                raise ValueError(
                    "a below observation must be strictly under the lower fence"
                )
            below += 1
        elif observation.direction is AnomalyDirection.ABOVE:
            if not exact > _as_fraction(upper):
                raise ValueError(
                    "an above observation must be strictly over the upper fence"
                )
            above += 1
        else:
            raise TypeError("direction must be an AnomalyDirection")
    return below, above


def _profile(
    column: ColumnAnalysis,
) -> Optional[Tuple[NumericDescriptiveAnalysis, int, int]]:
    """Return the retained profile and infinity counts, when both exist.

    Infinity counts come from numeric-structure evidence. When that
    evidence is absent and every non-missing value is finite, both
    infinity counts are zero. Otherwise the profile cannot support this
    method.
    """
    if column.inferred.selected_type is not SemanticType.NUMERIC:
        return None
    descriptive = column.numeric_analysis
    if descriptive is None:
        return None
    structure = column.evidence.numeric_structure
    if structure is not None:
        return (
            descriptive,
            structure.positive_infinity_count,
            structure.negative_infinity_count,
        )
    if descriptive.finite_count == column.evidence.basic.n_non_missing:
        return descriptive, 0, 0
    return None


def _coverage(
    columns: Tuple[ColumnAnalysis, ...],
    records: Tuple[NumericAnomalyColumn, ...],
) -> AnomalyCoverage:
    ineligible: dict[AnomalyIneligibility, int] = {}
    profile_absent = 0
    for column in columns:
        if _profile(column) is not None:
            continue
        if column.inferred.selected_type is SemanticType.NUMERIC:
            profile_absent += 1
            continue
        reason = _ineligibility(column)
        ineligible[reason] = ineligible.get(reason, 0) + 1
    unavailable: dict[NumericAnomalyStatus, int] = {}
    analyzed = 0
    for record in records:
        if record.status is NumericAnomalyStatus.AVAILABLE:
            analyzed += 1
        else:
            unavailable[record.status] = unavailable.get(record.status, 0) + 1
    return AnomalyCoverage(
        n_columns=len(columns),
        n_eligible=len(records),
        n_analyzed=analyzed,
        n_unavailable=len(records) - analyzed,
        n_ineligible=len(columns) - len(records) - profile_absent,
        n_numeric_profile_absent=profile_absent,
        unavailable=tuple(
            AnomalyUnavailableCount(status, unavailable[status])
            for status in _UNAVAILABLE_ORDER
            if unavailable.get(status, 0)
        ),
        ineligible=tuple(
            AnomalyIneligibleCount(reason, ineligible[reason])
            for reason in AnomalyIneligibility
            if ineligible.get(reason, 0)
        ),
    )


def _ineligibility(column: ColumnAnalysis) -> AnomalyIneligibility:
    selected = column.inferred.selected_type
    if selected is None:
        status = column.inferred.resolution.status
        if status is ResolutionStatus.INSUFFICIENT_EVIDENCE:
            return AnomalyIneligibility.UNRESOLVED
        if status is ResolutionStatus.AMBIGUOUS:
            return AnomalyIneligibility.AMBIGUOUS
        raise ValueError(
            "a column without a selected type must be unresolved or ambiguous"
        )
    if selected is SemanticType.NUMERIC:
        raise ValueError("a profiled Numeric column is not ineligible")
    try:
        return _INELIGIBLE_TYPES[selected]
    except KeyError as exc:
        raise TypeError("selected semantic type has no anomaly eligibility") from exc


def _column_tuple(columns: Sequence[ColumnAnalysis]) -> Tuple[ColumnAnalysis, ...]:
    if isinstance(columns, list):
        raise TypeError("anomaly columns must be a tuple")
    if not isinstance(columns, tuple):
        raise TypeError("anomaly columns must be a tuple")
    for position, column in enumerate(columns):
        if not isinstance(column, ColumnAnalysis):
            raise TypeError("anomaly columns must contain ColumnAnalysis records")
        if column.position != position:
            raise ValueError("anomaly column position must match column order")
    return columns


def _require_aligned(
    frame: pd.DataFrame,
    columns: Tuple[ColumnAnalysis, ...],
) -> int:
    n_rows = int(frame.shape[0])
    if len(columns) != int(frame.shape[1]):
        raise ValueError("anomaly columns must match the DataFrame width")
    for column in columns:
        if column.evidence.basic.n_total != n_rows:
            raise ValueError("anomaly row count must equal the DataFrame length")
    return n_rows


def _copy_coverage(coverage: AnomalyCoverage) -> AnomalyCoverage:
    return AnomalyCoverage(
        n_columns=coverage.n_columns,
        n_eligible=coverage.n_eligible,
        n_analyzed=coverage.n_analyzed,
        n_unavailable=coverage.n_unavailable,
        n_ineligible=coverage.n_ineligible,
        n_numeric_profile_absent=coverage.n_numeric_profile_absent,
        unavailable=tuple(
            AnomalyUnavailableCount(item.status, item.n_columns)
            for item in coverage.unavailable
        ),
        ineligible=tuple(
            AnomalyIneligibleCount(item.reason, item.n_columns)
            for item in coverage.ineligible
        ),
    )


def _copy_column(record: NumericAnomalyColumn) -> NumericAnomalyColumn:
    return NumericAnomalyColumn(
        position=record.position,
        label=record.label,
        status=record.status,
        n_rows=record.n_rows,
        n_missing=record.n_missing,
        finite_count=record.finite_count,
        positive_infinity_count=record.positive_infinity_count,
        negative_infinity_count=record.negative_infinity_count,
        method=record.method,
        fence_coefficient=record.fence_coefficient,
        q1=record.q1,
        q3=record.q3,
        iqr=record.iqr,
        lower_fence=record.lower_fence,
        upper_fence=record.upper_fence,
        below_count=record.below_count,
        above_count=record.above_count,
        observations=tuple(
            NumericAnomalyObservation(
                row_position=observation.row_position,
                value=observation.value,
                direction=observation.direction,
            )
            for observation in record.observations
        ),
    )


def _as_fraction(value: QuantileNumber) -> Fraction:
    if type(value) is int:
        return Fraction(value)
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("a fence landmark must be finite")
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    raise TypeError("a fence landmark must be an int, a float, or a Fraction")


def _signed_float(value: float) -> float:
    if value == 0.0:
        return 0.0
    return value


def _normalize_landmark(exact: Fraction) -> QuantileNumber:
    if exact.denominator == 1:
        return int(exact.numerator)
    as_float = float(exact)
    if math.isfinite(as_float) and as_float == exact:
        if as_float == 0.0:
            return 0.0
        return as_float
    return exact


def _python_number(value: object, integer: bool) -> ObservedNumber:
    if integer:
        if isinstance(value, (bool, np.bool_)):
            raise TypeError("an anomaly value cannot be boolean")
        return int(value)  # type: ignore[arg-type]
    number = float(value)  # type: ignore[arg-type]
    if not math.isfinite(number):
        raise ValueError("an anomaly value must be finite")
    if number == 0.0:
        return 0.0
    return number


def _require_reference_fields(record: NumericAnomalyColumn) -> None:
    available = record.status is NumericAnomalyStatus.AVAILABLE
    if available:
        if record.method is not NumericAnomalyMethod.TUKEY_IQR:
            raise ValueError("an available record names the Tukey IQR method")
        if record.fence_coefficient != _FENCE_COEFFICIENT:
            raise ValueError("the Tukey fence coefficient is 3/2")
        if type(record.fence_coefficient) is not Fraction:
            raise TypeError("fence coefficient must be a Fraction")
        _require_quantile(record.lower_fence, "lower_fence")
        _require_quantile(record.upper_fence, "upper_fence")
        if _as_fraction(record.lower_fence) >= _as_fraction(record.upper_fence):  # type: ignore[arg-type]
            raise ValueError("the lower fence must be below the upper fence")
        if type(record.below_count) is not int or type(record.above_count) is not int:
            raise ValueError("fence counts are required when fences are applied")
        if record.below_count < 0 or record.above_count < 0:  # type: ignore[operator]
            raise ValueError("fence counts cannot be negative")
    else:
        if record.method is not None or record.fence_coefficient is not None:
            raise ValueError("an unavailable record does not name an applied method")
        if record.lower_fence is not None or record.upper_fence is not None:
            raise ValueError("fences are present only when the method is applied")
        if record.below_count is not None or record.above_count is not None:
            raise ValueError("fence counts are present only when the method is applied")
        if len(record.observations) != 0:
            raise ValueError("observations are present only when the method is applied")
    if record.status is NumericAnomalyStatus.INSUFFICIENT_FINITE_POPULATION:
        if record.finite_count != 0:
            raise ValueError("an empty finite population has finite_count zero")
        if record.q1 is not None or record.q3 is not None or record.iqr is not None:
            raise ValueError("quartiles are undefined for an empty finite population")
        return
    if record.finite_count < 1:
        raise ValueError("a retained quartile profile has at least one finite value")
    _require_quantile(record.q1, "q1")
    _require_quantile(record.q3, "q3")
    if record.status is NumericAnomalyStatus.IQR_UNAVAILABLE:
        if record.iqr is not None:
            raise ValueError("an unavailable interquartile range is not stored as zero")
        return
    _require_quantile(record.iqr, "iqr")
    if record.status is NumericAnomalyStatus.ZERO_IQR:
        if record.iqr != 0:
            raise ValueError("zero IQR must be zero")
        return
    if record.iqr == 0 or record.iqr < 0:  # type: ignore[operator]
        raise ValueError("applied fences require a positive interquartile range")


def _require_observations(record: NumericAnomalyColumn) -> None:
    previous = -1
    below = 0
    above = 0
    for observation in record.observations:
        if not isinstance(observation, NumericAnomalyObservation):
            raise TypeError(
                "observations must contain NumericAnomalyObservation values"
            )
        if (
            observation.row_position <= previous
            or observation.row_position >= record.n_rows
        ):
            raise ValueError("anomaly row positions must be increasing and in range")
        previous = observation.row_position
        if observation.direction is AnomalyDirection.BELOW:
            below += 1
        else:
            above += 1
        if record.lower_fence is None or record.upper_fence is None:
            raise ValueError("observations require fences")
        exact = _as_fraction(observation.value)
        if observation.direction is AnomalyDirection.BELOW:
            if not exact < _as_fraction(record.lower_fence):
                raise ValueError(
                    "a below observation must be strictly under the lower fence"
                )
        elif not exact > _as_fraction(record.upper_fence):
            raise ValueError(
                "an above observation must be strictly over the upper fence"
            )
    if record.status is not NumericAnomalyStatus.AVAILABLE:
        return
    if below != record.below_count or above != record.above_count:
        raise ValueError("fence counts must equal the observation counts")


def _require_status_counts(
    counts: Tuple[AnomalyUnavailableCount, ...],
    total: int,
    field: str,
) -> None:
    if not isinstance(counts, tuple):
        raise TypeError(f"{field} must be a tuple")
    seen = []
    summed = 0
    for item in counts:
        if not isinstance(item, AnomalyUnavailableCount):
            raise TypeError(f"{field} must contain AnomalyUnavailableCount values")
        seen.append(item.status)
        summed += item.n_columns
    if seen != sorted(seen, key=_UNAVAILABLE_ORDER.index):
        raise ValueError(f"{field} counts must follow status order without duplicates")
    if summed != total:
        raise ValueError(f"{field} counts must sum to the {field} total")


def _require_reason_counts(
    counts: Tuple[AnomalyIneligibleCount, ...],
    total: int,
) -> None:
    if not isinstance(counts, tuple):
        raise TypeError("ineligible must be a tuple")
    order = tuple(AnomalyIneligibility)
    seen = []
    summed = 0
    for item in counts:
        if not isinstance(item, AnomalyIneligibleCount):
            raise TypeError("ineligible must contain AnomalyIneligibleCount values")
        seen.append(item.reason)
        summed += item.n_columns
    if seen != sorted(seen, key=order.index):
        raise ValueError(
            "ineligible counts must follow reason order without duplicates"
        )
    if summed != total:
        raise ValueError("ineligible counts must sum to n_ineligible")


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:  # type: ignore[operator]
        raise ValueError(f"{field} must be a non-negative int")


def _require_quantile(value: object, field: str) -> None:
    if value is None:
        raise ValueError(f"{field} is required")
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
    raise TypeError(f"{field} must be an int, a float, or a Fraction")


def _require_observed_number(value: object, field: str) -> None:
    if isinstance(value, bool) or isinstance(value, np.generic):
        raise TypeError(f"{field} must be a Python int or float")
    if type(value) is int:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError(f"{field} must not be negative zero")
        return
    raise TypeError(f"{field} must be a Python int or float")
