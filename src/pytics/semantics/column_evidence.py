"""Exact basic facts about one column.

These counts are observed characteristics. They are not a semantic type,
a confidence, or a threshold. Missing-like strings are left as observed
values; only values pandas already treats as missing are counted as missing.

The four stored counts are exact, full-column, and unsampled. Ratios and
boolean facts are computed from those counts. They are not stored, and they
are not collected by a second pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class BasicColumnEvidence:
    """Immutable basic counts for one Series.

    ``n_total``, ``n_missing``, ``n_non_missing``, and
    ``n_unique_non_missing`` are the stored primary observations. They are
    exact, full-column, and unsampled. ``n_non_missing`` is stored, rather
    than recomputed by callers, and must equal ``n_total - n_missing``.
    ``n_unique_non_missing`` counts distinct non-missing values only.

    ``missing_ratio``, ``unique_ratio_non_missing``, ``has_missing``,
    ``is_empty``, and ``is_constant`` are read from those counts. They are
    not fields. A ratio is ``None`` when its denominator is zero. The
    constant value itself is not stored.
    """

    n_total: int
    n_missing: int
    n_non_missing: int
    n_unique_non_missing: int

    def __post_init__(self) -> None:
        _require_count(self.n_total, "n_total")
        _require_count(self.n_missing, "n_missing")
        _require_count(self.n_non_missing, "n_non_missing")
        _require_count(self.n_unique_non_missing, "n_unique_non_missing")
        if self.n_missing > self.n_total:
            raise ValueError("n_missing cannot exceed n_total")
        if self.n_non_missing != self.n_total - self.n_missing:
            raise ValueError("n_non_missing must equal n_total - n_missing")
        if self.n_unique_non_missing > self.n_non_missing:
            raise ValueError("n_unique_non_missing cannot exceed n_non_missing")

    @property
    def missing_ratio(self) -> Optional[float]:
        """Missing observations divided by all observations.

        ``None`` when the Series has no rows.
        """
        if self.n_total == 0:
            return None
        return self.n_missing / self.n_total

    @property
    def unique_ratio_non_missing(self) -> Optional[float]:
        """Distinct non-missing values divided by non-missing observations.

        ``None`` when there is no non-missing observation. This is not an
        identifier threshold.
        """
        if self.n_non_missing == 0:
            return None
        return self.n_unique_non_missing / self.n_non_missing

    @property
    def has_missing(self) -> bool:
        """True when at least one observation is missing."""
        return self.n_missing > 0

    @property
    def is_empty(self) -> bool:
        """True when there is no non-missing observation.

        A zero-length Series and an all-missing Series are both empty.
        """
        return self.n_non_missing == 0

    @property
    def is_constant(self) -> bool:
        """True when one distinct non-missing value is present.

        A zero-length Series and an all-missing Series are empty, not
        constant. Missing observations beside that one value do not remove
        the constant fact.
        """
        return self.n_non_missing > 0 and self.n_unique_non_missing == 1


def collect_basic_column_evidence(series: pd.Series) -> BasicColumnEvidence:
    """Collect exact basic counts from a Series.

    The Series is not copied and is not modified. The four counts use the
    full column. There is no sampling. ``n_unique_non_missing`` uses
    ``Series.nunique(dropna=True)``. Unhashable non-missing values have no
    pandas distinct-count and raise ``TypeError``; this function does not
    stringify or otherwise normalize them. Derived facts are computed from
    the stored counts and do not scan the Series again.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_basic_column_evidence expects a pandas Series")
    n_total = len(series)
    n_missing = int(series.isna().sum())
    n_non_missing = n_total - n_missing
    try:
        n_unique_non_missing = int(series.nunique(dropna=True))
    except TypeError as exc:
        raise TypeError(
            "n_unique_non_missing is unavailable when non-missing values "
            "are unhashable"
        ) from exc
    return BasicColumnEvidence(
        n_total=n_total,
        n_missing=n_missing,
        n_non_missing=n_non_missing,
        n_unique_non_missing=n_unique_non_missing,
    )


def _require_count(value: Any, field: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be an int")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")
