"""Exact numeric-structure observations for one physically numeric column.

The observations apply only when the physical family is integer or floating.
Boolean storage is not numeric, even where a numeric predicate would accept
it. Strings are not parsed. Datetime, timedelta, and the other non-numeric
families are not coerced.

Counts use non-missing values only. Missing values stay on
``BasicColumnEvidence``. Finite sign counts and integer-like counts ignore
positive and negative infinity. Integer-like means exact integrality of a
finite value, with no tolerance. Monotonicity is defined only when every
non-missing value is finite. Zero non-missing values, one finite value, and
a finite constant series are both non-decreasing and non-increasing. That
is a vacuous structural fact. It is not an Identifier reading.

Collection is exact, full-column, and unsampled. It runs only when
requested. The Empty, Constant, and physical-type precedence chain does not
collect it. These facts do not select a semantic type, and they do not
carry descriptive statistics such as a mean or a quantile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional

import numpy as np
import pandas as pd

from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily

# Real numeric storage only. Boolean is its own physical family and is
# excluded here even though arithmetic on ``bool`` is defined.
_NUMERIC_STRUCTURE_FAMILIES = frozenset(
    {
        PhysicalDtypeFamily.INTEGER,
        PhysicalDtypeFamily.FLOATING,
    }
)


@dataclass(frozen=True)
class NumericStructureEvidence:
    """Immutable numeric-structure facts for one Series.

    ``basic`` is the universal evidence these facts were collected with.
    ``n_total``, ``n_missing``, and ``n_non_missing`` stay on that object.
    They are not copied into new fields.

    The eight counts are stored. A count is never ``None``. Ratios are
    read from those counts and from ``basic``. An undefined ratio is
    ``None``.

    ``is_non_decreasing`` and ``is_non_increasing`` are ``bool`` when every
    non-missing value is finite, including the vacuous cases of no
    non-missing values and one finite value. Both are ``None`` when any
    non-missing value is infinite. Missing values are not positions in
    that sequence. A finite constant series is both. These flags do not
    record a step size or a sequence role.
    """

    basic: BasicColumnEvidence
    finite_count: int
    positive_count: int
    negative_count: int
    zero_count: int
    positive_infinity_count: int
    negative_infinity_count: int
    integer_like_count: int
    non_integer_like_count: int
    is_non_decreasing: Optional[bool]
    is_non_increasing: Optional[bool]

    def __post_init__(self) -> None:
        if not isinstance(self.basic, BasicColumnEvidence):
            raise TypeError("basic must be BasicColumnEvidence")
        _require_count(self.finite_count, "finite_count")
        _require_count(self.positive_count, "positive_count")
        _require_count(self.negative_count, "negative_count")
        _require_count(self.zero_count, "zero_count")
        _require_count(self.positive_infinity_count, "positive_infinity_count")
        _require_count(self.negative_infinity_count, "negative_infinity_count")
        _require_count(self.integer_like_count, "integer_like_count")
        _require_count(self.non_integer_like_count, "non_integer_like_count")
        _require_population_counts(self)
        _require_monotonicity(self)

    @property
    def finite_ratio(self) -> Optional[float]:
        """Finite observations divided by non-missing observations.

        The denominator is ``BasicColumnEvidence.n_non_missing``. ``None``
        when that count is zero. Infinities are non-missing and are not
        finite, so this ratio can be ``0.0`` when every non-missing value
        is infinite.
        """
        if self.basic.n_non_missing == 0:
            return None
        return self.finite_count / self.basic.n_non_missing

    @property
    def positive_ratio(self) -> Optional[float]:
        """Finite values greater than zero, divided by finite values.

        ``None`` when ``finite_count`` is zero. The denominator is not
        ``n_non_missing`` and not ``n_total``.
        """
        if self.finite_count == 0:
            return None
        return self.positive_count / self.finite_count

    @property
    def negative_ratio(self) -> Optional[float]:
        """Finite values less than zero, divided by finite values.

        ``None`` when ``finite_count`` is zero.
        """
        if self.finite_count == 0:
            return None
        return self.negative_count / self.finite_count

    @property
    def zero_ratio(self) -> Optional[float]:
        """Finite zeros divided by finite values.

        ``None`` when ``finite_count`` is zero. ``0`` and ``-0.0`` are both
        zeros. This is not a missingness ratio.
        """
        if self.finite_count == 0:
            return None
        return self.zero_count / self.finite_count

    @property
    def integer_like_ratio(self) -> Optional[float]:
        """Finite integer-like values divided by finite values.

        ``None`` when ``finite_count`` is zero. This is not a discrete,
        identifier, or binary threshold.
        """
        if self.finite_count == 0:
            return None
        return self.integer_like_count / self.finite_count


def collect_numeric_structure_evidence(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> NumericStructureEvidence:
    """Collect exact numeric-structure facts from evidence already in hand.

    ``basic`` supplies the universal counts. This function does not collect
    them again and does not classify the physical dtype again. ``physical``
    must already describe this Series. The Series is not copied as a
    replacement and is not modified.

    One drop of missing values, using pandas missingness, produces the
    non-missing population in its original order. Counts and monotonicity
    are then read from that array. There is no second scan for frequencies,
    no sampling, and no ``pd.to_numeric`` coercion. A physical family other
    than integer or floating raises ``TypeError``. Boolean storage raises
    ``TypeError`` as well. Counts that disagree with ``basic`` raise
    ``ValueError``.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_numeric_structure_evidence expects a pandas Series")
    if not isinstance(basic, BasicColumnEvidence):
        raise TypeError("basic must be BasicColumnEvidence")
    if not isinstance(physical, PhysicalDtype):
        raise TypeError("physical must be a PhysicalDtype")
    _require_applicable_family(series, physical)
    if str(series.dtype) != physical.dtype_name:
        raise ValueError("physical dtype does not match the Series")
    values = _non_missing_numeric_values(series, basic)
    return _evidence_from_values(basic, values)


def _require_applicable_family(series: pd.Series, physical: PhysicalDtype) -> None:
    """Reject storage that is not a real integer or floating family.

    The boolean check stands even when ``physical.family`` has been labeled
    integer. Pandas and NumPy can treat ``bool`` as numeric. This evidence
    does not.
    """
    if (
        physical.family not in _NUMERIC_STRUCTURE_FAMILIES
        or pd.api.types.is_bool_dtype(series.dtype)
    ):
        raise TypeError(
            "numeric structure evidence applies only to integer and floating "
            "physical dtypes"
        )


def _non_missing_numeric_values(
    series: pd.Series,
    basic: BasicColumnEvidence,
) -> np.ndarray:
    """Return non-missing values in row order, without changing storage.

    The array keeps its integer or floating dtype. Casting integers through
    float64 would round values above ``2**53`` and could change order.
    """
    observed = series.dropna()
    if len(series) != basic.n_total or len(observed) != basic.n_non_missing:
        raise ValueError(
            "numeric observations do not match BasicColumnEvidence "
            "n_total and n_non_missing"
        )
    values = observed.to_numpy(copy=False)
    if not isinstance(values, np.ndarray) or values.dtype.kind not in {"i", "u", "f"}:
        raise TypeError(
            "numeric structure evidence applies only to real integer and "
            "floating values"
        )
    return values


def _evidence_from_values(
    basic: BasicColumnEvidence,
    values: np.ndarray,
) -> NumericStructureEvidence:
    """Derive every stored fact from one non-missing numeric array.

    ``np.trunc(np.inf)`` equals ``np.inf``, so integer-like comparison is
    masked to finite values. Infinity is neither integer-like nor a finite
    sign. Monotonicity stays undefined when any infinity remains, including
    a constant infinity. It is not evaluated on the finite subset alone.
    """
    finite = np.isfinite(values)
    positive_infinity_count = int(np.count_nonzero(np.isposinf(values)))
    negative_infinity_count = int(np.count_nonzero(np.isneginf(values)))
    finite_count = int(np.count_nonzero(finite))
    if finite_count + positive_infinity_count + negative_infinity_count != len(values):
        raise ValueError("a non-missing numeric value is neither finite nor infinite")
    positive_count = int(np.count_nonzero(finite & (values > 0)))
    negative_count = int(np.count_nonzero(finite & (values < 0)))
    zero_count = int(np.count_nonzero(finite & (values == 0)))
    # Exact equality with truncation. No tolerance and no rounding.
    integer_like_count = int(np.count_nonzero(finite & (values == np.trunc(values))))
    non_integer_like_count = finite_count - integer_like_count
    if positive_infinity_count or negative_infinity_count:
        is_non_decreasing: Optional[bool] = None
        is_non_increasing: Optional[bool] = None
    else:
        is_non_decreasing = bool(np.all(values[1:] >= values[:-1]))
        is_non_increasing = bool(np.all(values[1:] <= values[:-1]))
    return NumericStructureEvidence(
        basic=basic,
        finite_count=finite_count,
        positive_count=positive_count,
        negative_count=negative_count,
        zero_count=zero_count,
        positive_infinity_count=positive_infinity_count,
        negative_infinity_count=negative_infinity_count,
        integer_like_count=integer_like_count,
        non_integer_like_count=non_integer_like_count,
        is_non_decreasing=is_non_decreasing,
        is_non_increasing=is_non_increasing,
    )


def _require_count(value: Any, field: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be an int")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")


def _require_population_counts(evidence: NumericStructureEvidence) -> None:
    """Check the population identities.

    Non-negative counts plus these identities also keep each count inside
    the population it describes. Finite signs partition finite values.
    Integer-like and non-integer-like partition those same finite values.
    Finite values and the two infinities partition non-missing values.
    """
    non_missing = evidence.basic.n_non_missing
    if (
        evidence.finite_count
        + evidence.positive_infinity_count
        + evidence.negative_infinity_count
        != non_missing
    ):
        raise ValueError("finite and infinite counts must equal n_non_missing")
    if (
        evidence.positive_count + evidence.negative_count + evidence.zero_count
        != evidence.finite_count
    ):
        raise ValueError("positive, negative, and zero counts must equal finite_count")
    if (
        evidence.integer_like_count + evidence.non_integer_like_count
        != evidence.finite_count
    ):
        raise ValueError(
            "integer-like and non-integer-like counts must equal finite_count"
        )


def _require_monotonicity(evidence: NumericStructureEvidence) -> None:
    defined = evidence.finite_count == evidence.basic.n_non_missing
    flags = (evidence.is_non_decreasing, evidence.is_non_increasing)
    if not defined:
        if flags != (None, None):
            raise ValueError(
                "monotonicity is undefined when a non-missing value is infinite"
            )
        return
    if (
        type(evidence.is_non_decreasing) is not bool
        or type(evidence.is_non_increasing) is not bool
    ):
        raise TypeError("monotonicity is a bool when every non-missing value is finite")
    if evidence.basic.n_non_missing <= 1 and flags != (True, True):
        raise ValueError(
            "zero or one finite non-missing observation is both "
            "non-decreasing and non-increasing"
        )
    if evidence.basic.is_constant and flags != (True, True):
        raise ValueError(
            "a finite constant series is both non-decreasing and non-increasing"
        )
