"""Exact basic facts about one column.

These counts are observed characteristics. They are not a semantic type,
a confidence, or a threshold. Missing-like strings are left as observed
values; only values pandas already treats as missing are counted as missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class BasicColumnEvidence:
    """Immutable basic counts for one Series.

    ``n_non_missing`` is stored, rather than recomputed by callers, and must
    equal ``n_total - n_missing``. ``n_unique_non_missing`` counts distinct
    non-missing values only. The constant value itself is not stored.
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


def collect_basic_column_evidence(series: pd.Series) -> BasicColumnEvidence:
    """Collect exact basic counts from a Series.

    The Series is not copied and is not modified. Counts use the full column.
    There is no sampling. ``n_unique_non_missing`` uses
    ``Series.nunique(dropna=True)``. Unhashable non-missing values have no
    pandas distinct-count and raise ``TypeError``; this function does not
    stringify or otherwise normalize them.
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
