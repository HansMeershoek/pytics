"""Selected Categorical × Categorical association.

The question is which category combinations are observed, how strong the
symmetric association is, and what frequentist evidence supports
departure from independence. Chi-square significance is not the
relationship.

The effect is classical Cramér's V,

    V = sqrt(chi2 / (n * min(r - 1, c - 1)))

with ``n`` the paired count and ``r``, ``c`` the observed levels. It is
not the Bergsma finite-sample correction. It is unsigned. For a 2×2
table it equals the absolute value of the phi coefficient of the same
Pearson counts. Boolean × Boolean keeps signed phi because False and
True have a fixed coding. Arbitrary category levels do not.

The test is Pearson's chi-square of independence, without Yates's
correction for any shape, including 2×2. The null is independence of
the two categorical variables in the paired population. Degrees of
freedom are ``(r - 1) * (c - 1)``. The p-value is the upper tail
``scipy.stats.chi2.sf(statistic, df)``. ``chi2_contingency`` is not
called: its default applies Yates's correction when the degrees of
freedom are 1, and its array input is a dense rectangle.

One Pearson statistic produces V, the chi-square, and the tail. Expected
counts are not stored. The retained diagnostics are the minimum expected
count and the Cochran checkpoints of cells below 5 and below 1. Those
checkpoints do not turn the test on or off. A sparse table keeps its
table, its V when the formula is defined, its statistic, and its raw
p-value, and it does not switch to Fisher's exact test. This module
does not apply dataset-level correction.

The retained table stores positive cells only. Pair counts use a
temporary one-dimensional histogram when the observed rectangle has at
most ``2**20`` cells, and a sort of the paired codes otherwise. That
histogram is not retained. Marginal totals use ``bincount`` on each
compact axis. Zero cells still contribute to chi-square through the
identity

    chi2 = sum((O*n - R*C)^2 / (n*R*C)) + (n*n - sum(R*C)) / n

taken over observed cells. Products are Python integers until one float
division. A float that overflows, and a V outside ``[0, 1]`` by more
than the shared ``1e-8`` tolerance, are unavailable. A p-value that
underflows to ``0.0`` is kept.

Category identity is the scalar already stored on the physical
categorical vocabulary. Pandas may already have collapsed values that
compare equal, such as ``1``, ``True``, and ``1.0``, before this module
sees the codes. This module does not split them and does not stringify
them. Axis order is that vocabulary with unused levels removed. Category
values are not sorted.
"""

from __future__ import annotations

import math
import warnings
from typing import Optional
from typing import Tuple

import numpy as np
from scipy.stats import chi2

from pytics.analysis.relationships.models import CategoricalAssociationEstimate
from pytics.analysis.relationships.models import CategoricalAssociationMethod
from pytics.analysis.relationships.models import CategoricalCategoricalRelationship
from pytics.analysis.relationships.models import CategoricalContingencyTable
from pytics.analysis.relationships.models import CategoricalIndependenceMethod
from pytics.analysis.relationships.models import CategoricalIndependenceTest
from pytics.analysis.relationships.models import ExpectedCountDiagnostics
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import UnavailabilityReason

# The same absolute tolerance eta squared and phi use for a float that
# lands just outside its closed interval.
_UNIT_OVERSHOOT = 1e-8

# Temporary int64 histogram used only while counting pairs. 2**20 bins
# are 8 MiB. A larger observed rectangle is counted by sorting the
# paired codes, which stays proportional to the paired rows. The switch
# does not change the retained table and it does not make a pair
# unavailable.
_DENSE_HISTOGRAM_LIMIT = 2**20

_Effects = Tuple[CategoricalAssociationEstimate, CategoricalIndependenceTest]


def analyze(
    left_codes: np.ndarray,
    left_categories: Tuple[object, ...],
    right_codes: np.ndarray,
    right_categories: Tuple[object, ...],
    *,
    left_position: int,
    left_label: object,
    right_position: int,
    right_label: object,
    n_total_rows: int,
) -> CategoricalCategoricalRelationship:
    """Describe one canonical Categorical × Categorical pair.

    Each code array uses ``-1`` for a missing category, the pandas
    categorical sentinel. A non-missing code selects that column's
    vocabulary by index. A row survives only when both codes are
    non-missing. The arrays are not retained. The left axis is the left
    physical column.
    """
    _require_codes(left_codes, left_categories, n_total_rows, "left")
    _require_codes(right_codes, right_categories, n_total_rows, "right")
    mask = (left_codes >= 0) & (right_codes >= 0)
    n_paired = int(np.count_nonzero(mask))
    if n_paired == 0:
        table = _empty_table()
    else:
        table = _contingency_table(
            left_codes[mask],
            left_categories,
            right_codes[mask],
            right_categories,
        )
    return _assemble(
        table,
        left_position=left_position,
        left_label=left_label,
        right_position=right_position,
        right_label=right_label,
        n_total_rows=n_total_rows,
    )


def _require_codes(
    codes: object,
    categories: object,
    n_total_rows: int,
    side: str,
) -> None:
    if not isinstance(codes, np.ndarray):
        raise TypeError(f"{side} category codes must be a NumPy array")
    if codes.shape != (n_total_rows,):
        raise ValueError("relationship inputs must contain one entry per row")
    if codes.dtype.kind not in {"i", "u"}:
        raise TypeError(f"{side} category codes must be integers")
    if not isinstance(categories, tuple):
        raise TypeError(f"{side} categories must be a tuple")


def _empty_table() -> CategoricalContingencyTable:
    return CategoricalContingencyTable(
        left_levels=(),
        right_levels=(),
        observed_counts=(),
        left_totals=(),
        right_totals=(),
    )


def _assemble(
    table: CategoricalContingencyTable,
    *,
    left_position: int,
    left_label: object,
    right_position: int,
    right_label: object,
    n_total_rows: int,
) -> CategoricalCategoricalRelationship:
    association, independence = _effects(table)
    return CategoricalCategoricalRelationship(
        left_position=left_position,
        left_label=left_label,
        right_position=right_position,
        right_label=right_label,
        n_total_rows=n_total_rows,
        n_paired=table.grand_total,
        table=table,
        association=association,
        expected_counts=_diagnostics(table),
        independence=independence,
    )


def _contingency_table(
    left_codes: np.ndarray,
    left_categories: Tuple[object, ...],
    right_codes: np.ndarray,
    right_categories: Tuple[object, ...],
) -> CategoricalContingencyTable:
    """Build the observed table from vocabulary indexes.

    ``numpy.unique`` sorts those indexes, so axis order is the physical
    vocabulary. It does not compare category values. The temporary
    histogram, when used, is discarded with the compact codes.
    """
    left_levels, left_compact = _compact_axis(left_codes, left_categories)
    right_levels, right_compact = _compact_axis(right_codes, right_categories)
    observed = _observed_counts(
        left_compact,
        right_compact,
        len(left_levels),
        len(right_levels),
    )
    return CategoricalContingencyTable(
        left_levels=left_levels,
        right_levels=right_levels,
        observed_counts=observed,
        left_totals=_margin(left_compact),
        right_totals=_margin(right_compact),
    )


def _compact_axis(
    codes: np.ndarray,
    vocabulary: Tuple[object, ...],
) -> Tuple[Tuple[object, ...], np.ndarray]:
    observed = np.unique(codes)
    levels = []
    for code in observed.tolist():
        index = int(code)
        if index < 0 or index >= len(vocabulary):
            raise ValueError("category code is outside the categorical vocabulary")
        levels.append(vocabulary[index])
    compact = np.searchsorted(observed, codes)
    return tuple(levels), compact


def _observed_counts(
    left_compact: np.ndarray,
    right_compact: np.ndarray,
    n_left: int,
    n_right: int,
) -> Tuple[Tuple[int, int, int], ...]:
    """Positive cells in row-major order, without an ``r`` by ``c`` matrix."""
    if n_left * n_right <= _DENSE_HISTOGRAM_LIMIT:
        return _cells_from_histogram(left_compact, right_compact, n_left, n_right)
    return _cells_from_sorted_pairs(left_compact, right_compact)


def _cells_from_histogram(
    left_compact: np.ndarray,
    right_compact: np.ndarray,
    n_left: int,
    n_right: int,
) -> Tuple[Tuple[int, int, int], ...]:
    keys = left_compact.astype(np.int64, copy=False) * np.int64(n_right)
    keys += right_compact.astype(np.int64, copy=False)
    histogram = np.bincount(keys, minlength=n_left * n_right)
    occupied = np.flatnonzero(histogram)
    left_index = occupied // np.int64(n_right)
    right_index = occupied - left_index * np.int64(n_right)
    counts = histogram[occupied]
    return tuple(
        (int(row), int(column), int(count))
        for row, column, count in zip(left_index, right_index, counts)
    )


def _cells_from_sorted_pairs(
    left_compact: np.ndarray,
    right_compact: np.ndarray,
) -> Tuple[Tuple[int, int, int], ...]:
    order = np.lexsort((right_compact, left_compact))
    left_sorted = left_compact[order]
    right_sorted = right_compact[order]
    n_pairs = int(left_sorted.size)
    change = np.empty(n_pairs, dtype=bool)
    change[0] = True
    if n_pairs > 1:
        change[1:] = (left_sorted[1:] != left_sorted[:-1]) | (
            right_sorted[1:] != right_sorted[:-1]
        )
    starts = np.flatnonzero(change)
    counts = np.diff(np.append(starts, n_pairs))
    return tuple(
        (int(left_sorted[start]), int(right_sorted[start]), int(count))
        for start, count in zip(starts, counts)
    )


def _margin(compact: np.ndarray) -> Tuple[int, ...]:
    """Positive marginal counts. The bin length is the observed axis, not ``r * c``."""
    return tuple(int(count) for count in np.bincount(compact).tolist())


def _effects(table: CategoricalContingencyTable) -> _Effects:
    n_paired = table.grand_total
    n_left = table.n_left_levels
    n_right = table.n_right_levels
    if n_paired == 0:
        reason = UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        return _unavailable_association(reason), _unavailable_test(reason)
    if n_left < 2 or n_right < 2:
        reason = UnavailabilityReason.CONSTANT_PAIRED_VALUES
        return _unavailable_association(reason), _unavailable_test(reason)
    statistic = _pearson_chi_square(table)
    if statistic is None:
        reason = UnavailabilityReason.NON_FINITE_RESULT
        return _unavailable_association(reason), _unavailable_test(reason)
    cramers_v = _cramers_v(statistic, n_paired, n_left, n_right)
    if cramers_v is None:
        association = _unavailable_association(UnavailabilityReason.NON_FINITE_RESULT)
    else:
        association = _available_association(cramers_v)
    degrees_of_freedom = (n_left - 1) * (n_right - 1)
    return association, _test_from_statistic(statistic, degrees_of_freedom)


def _pearson_chi_square(table: CategoricalContingencyTable) -> Optional[float]:
    """Uncorrected Pearson statistic of one retained contingency table."""
    return _pearson_chi_square_from_counts(
        table.observed_counts,
        table.left_totals,
        table.right_totals,
        table.grand_total,
    )


def _pearson_chi_square_from_counts(
    observed_counts: Tuple[Tuple[int, int, int], ...],
    left_totals: Tuple[int, ...],
    right_totals: Tuple[int, ...],
    n_paired: int,
) -> Optional[float]:
    """Uncorrected Pearson statistic from the observed positive cells.

    ``observed_counts`` holds ``(left_index, right_index, count)`` for
    positive cells. The margins are positive and each sums to
    ``n_paired``. ``(O*n - R*C)^2 / (n*R*C)`` is ``(O - E)^2 / E`` with
    the products kept as Python integers. Unobserved cells contribute
    their expected counts in one exact remainder,
    ``(n*n - sum(R*C)) / n``, so a zero cell does not need its own visit
    and does not need a dense matrix. Distribution drift reuses this
    statistic for its two-sample homogeneity table.
    """
    terms = []
    observed_product = 0
    try:
        for left_index, right_index, count in observed_counts:
            row_total = left_totals[left_index]
            column_total = right_totals[right_index]
            residual = count * n_paired - row_total * column_total
            denominator = n_paired * row_total * column_total
            terms.append((residual * residual) / denominator)
            observed_product += row_total * column_total
        deficit = n_paired * n_paired - observed_product
        if deficit < 0:
            return None
        quotient, remainder = divmod(deficit, n_paired)
        zero_mass = float(quotient) + remainder / n_paired
        statistic = math.fsum(terms) + zero_mass
    except (OverflowError, ZeroDivisionError, ValueError):
        return None
    return _finite_chi_square(statistic)


def _finite_chi_square(statistic: float) -> Optional[float]:
    if not math.isfinite(statistic):
        return None
    if statistic == 0.0:
        return 0.0
    if statistic < 0.0:
        if statistic >= -_UNIT_OVERSHOOT:
            return 0.0
        return None
    return float(statistic)


def _cramers_v(
    statistic: float,
    n_paired: int,
    n_left: int,
    n_right: int,
) -> Optional[float]:
    """Classical ``sqrt(chi2 / (n * min(r - 1, c - 1)))``."""
    scale = n_paired * min(n_left - 1, n_right - 1)
    if scale <= 0:
        return None
    if statistic == 0.0:
        return 0.0
    try:
        ratio = statistic / scale
    except OverflowError:
        return None
    if not math.isfinite(ratio) or ratio < 0.0:
        return None
    if ratio == 0.0:
        return 0.0
    return _normalize_unit(math.sqrt(ratio))


def _normalize_unit(value: float) -> Optional[float]:
    if not math.isfinite(value):
        return None
    if value > 1.0:
        if value - 1.0 <= _UNIT_OVERSHOOT:
            return 1.0
        return None
    if value < 0.0:
        if -value <= _UNIT_OVERSHOOT:
            return 0.0
        return None
    if value == 0.0:
        return 0.0
    return float(value)


def _test_from_statistic(
    statistic: float,
    degrees_of_freedom: int,
) -> CategoricalIndependenceTest:
    p_value = _pearson_p_value(statistic, degrees_of_freedom)
    if p_value is None:
        frequentist = _unavailable_frequentist(UnavailabilityReason.NON_FINITE_RESULT)
    else:
        frequentist = _available_frequentist(p_value)
    return CategoricalIndependenceTest(
        method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
        statistic_availability=ResultAvailability.AVAILABLE,
        statistic=statistic,
        degrees_of_freedom=degrees_of_freedom,
        statistic_reason=None,
        frequentist=frequentist,
    )


def _pearson_p_value(statistic: float, degrees_of_freedom: int) -> Optional[float]:
    """Raw upper tail of the chi-square distribution. ``0.0`` is a real tail."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            raw = _survival_function(statistic, degrees_of_freedom)
    except (ValueError, OverflowError, FloatingPointError):
        return None
    return _as_p_value(raw)


def _survival_function(statistic: float, degrees_of_freedom: int) -> object:
    return chi2.sf(statistic, degrees_of_freedom)


def _as_p_value(value: object) -> Optional[float]:
    if isinstance(value, (bool, np.bool_)):
        return None
    if isinstance(value, np.ndarray):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0.0 or number > 1.0:
        return None
    if number == 0.0:
        return 0.0
    return number


def _diagnostics(table: CategoricalContingencyTable) -> ExpectedCountDiagnostics:
    return _expected_count_diagnostics(
        table.left_totals,
        table.right_totals,
        table.grand_total,
    )


def _expected_count_diagnostics(
    left_totals: Tuple[int, ...],
    right_totals: Tuple[int, ...],
    n_paired: int,
) -> ExpectedCountDiagnostics:
    """Cochran checkpoints for the rectangle spanned by two positive margins.

    Every cell of that rectangle counts, including observed zeros.
    Distribution drift reuses these checkpoints for its two-sample
    homogeneity table.
    """
    if n_paired == 0:
        return _unavailable_diagnostics(
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        )
    minimum = _minimum_expected(left_totals, right_totals, n_paired)
    if minimum is None:
        return _unavailable_diagnostics(UnavailabilityReason.NON_FINITE_RESULT)
    ordered = tuple(sorted(right_totals))
    below_5 = _count_products_below(left_totals, ordered, 5 * n_paired)
    below_1 = _count_products_below(left_totals, ordered, n_paired)
    n_cells = len(left_totals) * len(right_totals)
    fraction = _fraction(below_5, n_cells)
    if fraction is None:
        return _unavailable_diagnostics(UnavailabilityReason.NON_FINITE_RESULT)
    return ExpectedCountDiagnostics(
        availability=ResultAvailability.AVAILABLE,
        minimum_expected_count=minimum,
        n_cells_expected_below_5=below_5,
        fraction_cells_expected_below_5=fraction,
        n_cells_expected_below_1=below_1,
        reason=None,
    )


def _minimum_expected(
    left_totals: Tuple[int, ...],
    right_totals: Tuple[int, ...],
    n_paired: int,
) -> Optional[float]:
    """``min(R) * min(C) / n``. Both margins are positive, so this is the minimum."""
    try:
        value = (min(left_totals) * min(right_totals)) / n_paired
    except (OverflowError, ZeroDivisionError, ValueError):
        return None
    if type(value) is not float or not math.isfinite(value) or value <= 0.0:
        return None
    return value


def _count_products_below(
    left_totals: Tuple[int, ...],
    ordered_right_totals: Tuple[int, ...],
    limit: int,
) -> int:
    """Count cells with ``row * column < limit``.

    ``limit`` is ``threshold * n``. The comparison stays in Python
    integers, so an expected count of exactly 5 is not counted as below 5.
    """
    count = 0
    last = len(ordered_right_totals)
    for left_total in left_totals:
        lower = 0
        upper = last
        while lower < upper:
            middle = (lower + upper) // 2
            if left_total * ordered_right_totals[middle] < limit:
                lower = middle + 1
            else:
                upper = middle
        count += lower
    return count


def _fraction(count: int, n_cells: int) -> Optional[float]:
    if n_cells <= 0:
        return None
    if count == 0:
        return 0.0
    if count == n_cells:
        return 1.0
    try:
        value = count / n_cells
    except OverflowError:
        return None
    return _normalize_unit(value)


def _available_association(value: float) -> CategoricalAssociationEstimate:
    return CategoricalAssociationEstimate(
        method=CategoricalAssociationMethod.CRAMERS_V,
        availability=ResultAvailability.AVAILABLE,
        value=value,
        reason=None,
    )


def _unavailable_association(
    reason: UnavailabilityReason,
) -> CategoricalAssociationEstimate:
    return CategoricalAssociationEstimate(
        method=CategoricalAssociationMethod.CRAMERS_V,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _unavailable_test(reason: UnavailabilityReason) -> CategoricalIndependenceTest:
    return CategoricalIndependenceTest(
        method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
        statistic_availability=ResultAvailability.UNAVAILABLE,
        statistic=None,
        degrees_of_freedom=None,
        statistic_reason=reason,
        frequentist=_unavailable_frequentist(reason),
    )


def _available_frequentist(p_value: float) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=ResultAvailability.AVAILABLE,
        p_value=p_value,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )


def _unavailable_frequentist(reason: UnavailabilityReason) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=ResultAvailability.UNAVAILABLE,
        p_value=None,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=reason,
    )


def _unavailable_diagnostics(reason: UnavailabilityReason) -> ExpectedCountDiagnostics:
    return ExpectedCountDiagnostics(
        availability=ResultAvailability.UNAVAILABLE,
        minimum_expected_count=None,
        n_cells_expected_below_5=None,
        fraction_cells_expected_below_5=None,
        n_cells_expected_below_1=None,
        reason=reason,
    )
