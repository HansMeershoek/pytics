"""Exact frequency observations for one column.

The distribution covers non-missing values only. It is exact, full-column,
and unsampled. Collection runs only when requested. The Empty, Constant, and
physical-type precedence chain does not collect it.

``most_frequent_count`` and ``singleton_count`` are stored. Ratios are read
from those counts and from the composed ``BasicColumnEvidence`` denominators.
Missing counts stay on that basic evidence. The exact distinct values are
retained only while their number stays within
``EXACT_DISTINCT_VALUE_RETENTION_LIMIT``. That limit is a storage bound, not
a semantic threshold.

These facts do not select a semantic type. Equal values under Python
equality, including ``True`` and ``1``, stay one frequency key. This module
does not replace the representative pandas already chose.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional

import pandas as pd

from pytics.semantics.column_evidence import BasicColumnEvidence

# How many distinct non-missing values may be stored exactly. This is an
# internal retention bound for the evidence object, not a cardinality class.
EXACT_DISTINCT_VALUE_RETENTION_LIMIT = 32


@dataclass(frozen=True)
class FrequencyEvidence:
    """Immutable frequency facts for one Series.

    ``basic`` is the universal evidence these facts were collected with.
    Its counts are not copied into new fields. ``most_frequent_count`` is
    the largest occurrence count among non-missing values, or ``0`` when
    that population is empty. ``singleton_count`` is how many of those
    distinct values occur once, or ``0`` when none do.

    ``exact_distinct_non_missing_values`` is a ``frozenset`` when every
    distinct non-missing value is retained, including an empty ``frozenset``
    when the population is empty. It is ``None`` when the distinct count
    exceeds the retention limit. ``None`` means the set was not stored. It
    does not mean the column had no values.

    ``most_frequent_ratio`` and ``singleton_ratio`` are read from the stored
    counts and from ``basic``. They are not fields.
    """

    basic: BasicColumnEvidence
    most_frequent_count: int
    singleton_count: int
    exact_distinct_non_missing_values: Optional[frozenset[Any]]

    def __post_init__(self) -> None:
        if not isinstance(self.basic, BasicColumnEvidence):
            raise TypeError("basic must be BasicColumnEvidence")
        _require_count(self.most_frequent_count, "most_frequent_count")
        _require_count(self.singleton_count, "singleton_count")
        _require_frequency_counts(
            self.basic,
            self.most_frequent_count,
            self.singleton_count,
        )
        _require_exact_values(
            self.basic.n_unique_non_missing,
            self.exact_distinct_non_missing_values,
        )

    @property
    def most_frequent_ratio(self) -> Optional[float]:
        """Largest non-missing count divided by non-missing observations.

        The denominator is ``BasicColumnEvidence.n_non_missing``. ``None``
        when that count is zero. This is not a categorical threshold.
        """
        if self.basic.n_non_missing == 0:
            return None
        return self.most_frequent_count / self.basic.n_non_missing

    @property
    def singleton_ratio(self) -> Optional[float]:
        """Share of distinct non-missing values that occur once.

        The denominator is ``BasicColumnEvidence.n_unique_non_missing``,
        not the number of rows and not ``n_non_missing``. ``None`` when
        there is no distinct non-missing value. This is not an identifier
        threshold.
        """
        if self.basic.n_unique_non_missing == 0:
            return None
        return self.singleton_count / self.basic.n_unique_non_missing


def collect_frequency_evidence(
    series: pd.Series,
    basic: BasicColumnEvidence,
) -> FrequencyEvidence:
    """Collect exact frequency facts using basic evidence already collected.

    The Series is not copied and is not modified. ``basic`` supplies
    ``n_non_missing`` and ``n_unique_non_missing``. This function does not
    call ``nunique`` or ``isna``, and it does not build a second basic
    evidence value. One ``value_counts`` pass, with missing values excluded,
    produces the mode count, the singleton count, and, when the distinct
    count is within the retention limit, the exact value set.

    The temporary count mapping is not stored. There is no sampling and no
    approximate cardinality. ``value_counts`` can group some unhashable
    values that ``nunique`` rejects. Those keys still raise ``TypeError``.
    They are not stringified, frozen, or omitted. A count table that
    disagrees with ``basic`` raises ``ValueError`` instead of replacing
    those counts.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_frequency_evidence expects a pandas Series")
    if not isinstance(basic, BasicColumnEvidence):
        raise TypeError("basic must be BasicColumnEvidence")
    counts = _non_missing_frequency_counts(series)
    observed_non_missing = int(counts.sum())
    observed_unique = len(counts)
    if (
        observed_non_missing != basic.n_non_missing
        or observed_unique != basic.n_unique_non_missing
    ):
        raise ValueError(
            "frequency observations do not match BasicColumnEvidence "
            "n_non_missing and n_unique_non_missing"
        )
    if basic.n_unique_non_missing == 0:
        most_frequent_count = 0
        singleton_count = 0
    else:
        most_frequent_count = int(counts.max())
        singleton_count = int((counts == 1).sum())
    if basic.n_unique_non_missing <= EXACT_DISTINCT_VALUE_RETENTION_LIMIT:
        exact_values: Optional[frozenset[Any]] = frozenset(counts.index)
    else:
        exact_values = None
    return FrequencyEvidence(
        basic=basic,
        most_frequent_count=most_frequent_count,
        singleton_count=singleton_count,
        exact_distinct_non_missing_values=exact_values,
    )


def _non_missing_frequency_counts(series: pd.Series) -> pd.Series:
    """Return one count per observed non-missing value.

    ``sort`` is false so the pass does not require values to be ordered.
    A categorical dtype can list unobserved categories at count zero. Those
    zeros are not observations, so they are removed before the facts are
    read. That removal uses this count table. It does not scan the Series
    again.
    """
    counts = series.value_counts(dropna=True, sort=False)
    if len(counts) > 0 and bool((counts == 0).any()):
        counts = counts[counts > 0]
    _require_hashable_frequency_keys(counts)
    return counts


def _require_hashable_frequency_keys(counts: pd.Series) -> None:
    """Raise when a frequency key cannot be stored as itself.

    ``value_counts`` may group an unhashable value. Retaining that key would
    require stringifying it or freezing it, and dropping it above the
    retention limit would hide it. Either choice would contradict basic
    evidence, which fails on the same values. ``hash`` is only a gate. It
    does not replace the value.
    """
    for value in counts.index:
        try:
            hash(value)
        except TypeError as exc:
            raise TypeError(
                "frequency evidence is unavailable when non-missing values "
                "are unhashable"
            ) from exc


def _require_count(value: Any, field: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be an int")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")


def _require_frequency_counts(
    basic: BasicColumnEvidence,
    most_frequent_count: int,
    singleton_count: int,
) -> None:
    n_non_missing = basic.n_non_missing
    n_unique = basic.n_unique_non_missing
    if n_non_missing == 0:
        if most_frequent_count != 0 or singleton_count != 0:
            raise ValueError(
                "an empty frequency population has most_frequent_count 0 "
                "and singleton_count 0"
            )
        return
    if n_unique < 1:
        raise ValueError(
            "n_unique_non_missing must be positive when non-missing "
            "observations exist"
        )
    if most_frequent_count < 1:
        raise ValueError(
            "most_frequent_count must be >= 1 when non-missing observations exist"
        )
    if most_frequent_count > n_non_missing:
        raise ValueError("most_frequent_count cannot exceed n_non_missing")
    if singleton_count > n_unique:
        raise ValueError("singleton_count cannot exceed n_unique_non_missing")
    if n_unique == 1:
        _require_single_value_counts(
            n_non_missing,
            most_frequent_count,
            singleton_count,
        )
        return
    if most_frequent_count == 1:
        if singleton_count != n_unique or n_non_missing != n_unique:
            raise ValueError(
                "when every non-missing value occurs once, singleton_count "
                "equals n_unique_non_missing"
            )
        return
    non_singletons = n_unique - singleton_count
    if non_singletons < 1:
        raise ValueError(
            "a repeated value means at least one distinct value is not a singleton"
        )
    lower = singleton_count + 2 * (non_singletons - 1) + most_frequent_count
    upper = singleton_count + non_singletons * most_frequent_count
    if not lower <= n_non_missing <= upper:
        raise ValueError(
            "frequency counts are inconsistent with n_non_missing and "
            "n_unique_non_missing"
        )


def _require_single_value_counts(
    n_non_missing: int,
    most_frequent_count: int,
    singleton_count: int,
) -> None:
    if most_frequent_count != n_non_missing:
        raise ValueError(
            "the only distinct non-missing value occurs n_non_missing times"
        )
    expected_singletons = 1 if n_non_missing == 1 else 0
    if singleton_count != expected_singletons:
        raise ValueError(
            "singleton_count is 1 only when the single distinct value occurs once"
        )


def _require_exact_values(
    n_unique: int,
    exact: Optional[frozenset[Any]],
) -> None:
    if n_unique <= EXACT_DISTINCT_VALUE_RETENTION_LIMIT:
        if type(exact) is not frozenset:
            raise TypeError(
                "exact_distinct_non_missing_values must be a frozenset when "
                "the distinct count is within the retention limit"
            )
        if len(exact) != n_unique:
            raise ValueError(
                "exact_distinct_non_missing_values must contain each "
                "retained distinct non-missing value once"
            )
        return
    if exact is not None:
        raise ValueError(
            "exact_distinct_non_missing_values must be None when the "
            "distinct count exceeds the retention limit"
        )
