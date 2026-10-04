"""Exact observed distribution for a column selected as Categorical.

These facts profile a categorical vocabulary. They are not semantic-inference
evidence. ``FrequencyEvidence`` still owns the aggregate most-frequent and
singleton counts, and it still drops the count table above its retention
limit. This module keeps the observed level table. It does not select a
semantic type, and it does not read one.

The descriptive population is the non-missing observations. Missing values
are not levels. Unused physical categorical levels are not levels. Counts
sum to that non-missing population. Proportions divide by it, not by the
row count.

Level order is the physical categorical vocabulary with unused levels
removed. ``ordered`` is that dtype's ``ordered`` flag. ``True`` does not
create an Ordinal semantic type. ``False`` means the vocabulary order is
storage order, not a ranking. This collector does not invent an order for
a representation that is not a pandas categorical.

Category identity is the identity pandas already used to build the
vocabulary. Pandas category uniqueness uses equality, so values such as
``1``, ``True``, and ``1.0`` can already be one level. This module does
not build a separate equality universe that would split them, and it does
not stringify a level to keep it.

The source Series is not retained. There is no cardinality cutoff.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ObservedCategoryCount:
    """One observed non-missing category and how often it occurs.

    ``value`` is the category scalar. It is not a display string.
    ``count`` is that value's occurrences in the non-missing population.
    A count of zero is an unused level and is not an observed category.
    """

    value: object
    count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _retain_category(self.value))
        if type(self.count) is not int or self.count < 1:
            raise ValueError("an observed category count must be a positive int")


@dataclass(frozen=True)
class CategoricalDescriptiveAnalysis:
    """Exact observed distribution of one Categorical column.

    ``n_non_missing`` is the non-missing population. It equals the sum of
    the level counts. ``levels`` lists each observed value once. When the
    source is a pandas categorical, that sequence is the physical
    vocabulary with unused levels removed. ``ordered`` is the dtype flag
    for that vocabulary. It is ``None`` only when a directly constructed
    result was not given a source order flag. The collector does not
    produce ``None``.

    Proportions, the most frequent count, the least frequent count, and
    the singleton count are read from ``levels``. They are not stored, so
    they cannot disagree with the counts. A tie keeps every tied level,
    in retained level order. There is no single mode when the count is
    shared, and there is no balanced or imbalanced label.

    A proportion is ``None`` when the population is empty. A stored
    proportion is never NaN or infinite, because proportions are not
    stored.
    """

    n_non_missing: int
    ordered: Optional[bool]
    levels: Tuple[ObservedCategoryCount, ...]

    def __post_init__(self) -> None:
        if type(self.n_non_missing) is not int or self.n_non_missing < 0:
            raise ValueError("n_non_missing must be a non-negative int")
        if self.ordered is not None and type(self.ordered) is not bool:
            raise TypeError("ordered must be a bool or None")
        if not isinstance(self.levels, tuple):
            raise TypeError("levels must be a tuple")
        if self.n_non_missing == 0:
            if self.levels:
                raise ValueError(
                    "an empty categorical population has no observed levels"
                )
            return
        if not self.levels:
            raise ValueError("a non-empty categorical population has observed levels")
        seen: dict[object, None] = {}
        total = 0
        for level in self.levels:
            if not isinstance(level, ObservedCategoryCount):
                raise TypeError("levels must contain observed category counts")
            if level.value in seen:
                raise ValueError(
                    "observed category values must be unique under Python equality"
                )
            seen[level.value] = None
            total += level.count
        if total != self.n_non_missing:
            raise ValueError("category counts must sum to n_non_missing")

    @property
    def n_observed(self) -> int:
        """How many distinct non-missing values were observed."""
        return len(self.levels)

    @property
    def proportions(self) -> Tuple[float, ...]:
        """Each level count divided by the non-missing population.

        The tuple follows ``levels``. It is empty when that population is
        empty. The denominator is not the row count.
        """
        if self.n_non_missing == 0:
            return ()
        return tuple(
            _proportion(level.count, self.n_non_missing) for level in self.levels
        )

    @property
    def singleton_count(self) -> int:
        """How many observed levels occur once."""
        return sum(1 for level in self.levels if level.count == 1)

    @property
    def most_frequent_count(self) -> int:
        """Largest observed count, or ``0`` when no level was observed."""
        if not self.levels:
            return 0
        return max(level.count for level in self.levels)

    @property
    def least_frequent_count(self) -> int:
        """Smallest observed count, or ``0`` when no level was observed.

        Unused levels are already absent, so this is not zero merely
        because the physical vocabulary had an unused level.
        """
        if not self.levels:
            return 0
        return min(level.count for level in self.levels)

    @property
    def most_frequent_proportion(self) -> Optional[float]:
        """Largest observed count divided by the non-missing population.

        ``None`` when that population is empty. This is not an imbalance
        threshold.
        """
        if self.n_non_missing == 0:
            return None
        return _proportion(self.most_frequent_count, self.n_non_missing)

    @property
    def least_frequent_proportion(self) -> Optional[float]:
        """Smallest observed count divided by the non-missing population.

        ``None`` when that population is empty. This is not a rare-class
        threshold.
        """
        if self.n_non_missing == 0:
            return None
        return _proportion(self.least_frequent_count, self.n_non_missing)

    @property
    def most_frequent_values(self) -> Tuple[object, ...]:
        """Observed values that share the largest count, in level order.

        A tie keeps every tied value. The sequence is empty when no
        level was observed.
        """
        return _values_at_count(self.levels, self.most_frequent_count)

    @property
    def least_frequent_values(self) -> Tuple[object, ...]:
        """Observed values that share the smallest count, in level order.

        A tie keeps every tied value. The sequence is empty when no
        level was observed.
        """
        return _values_at_count(self.levels, self.least_frequent_count)


def collect_categorical_descriptive_analysis(
    series: pd.Series,
) -> CategoricalDescriptiveAnalysis:
    """Describe the observed non-missing levels of one categorical Series.

    The Series must already use pandas categorical storage. String,
    object, integer, floating, and boolean storage are rejected even
    when the values look like labels. A categorical whose values are
    boolean stays categorical. The Series is not modified, and its dtype
    is not changed.

    Counts come from category codes. Missing codes are excluded. A code
    that never occurs is an unused level and is omitted. The remaining
    levels follow the physical vocabulary. ``ordered`` is copied from
    the dtype. Values are not stringified. There is no sampling and no
    cardinality cutoff.
    """
    if not isinstance(series, pd.Series):
        raise TypeError(
            "collect_categorical_descriptive_analysis expects a pandas Series"
        )
    if not isinstance(series.dtype, pd.CategoricalDtype):
        raise TypeError(
            "categorical descriptive analysis applies only to categorical storage"
        )
    counts = _observed_code_counts(series)
    categories = series.cat.categories
    levels = []
    for index, count in enumerate(counts.tolist()):
        if count == 0:
            continue
        levels.append(
            ObservedCategoryCount(
                value=categories[index],
                count=int(count),
            )
        )
    return CategoricalDescriptiveAnalysis(
        n_non_missing=int(counts.sum()),
        ordered=bool(series.dtype.ordered),
        levels=tuple(levels),
    )


def copy_categorical_descriptive_analysis(
    analysis: CategoricalDescriptiveAnalysis,
) -> CategoricalDescriptiveAnalysis:
    """Return a new frozen distribution with the same levels.

    The copy does not read a Series and does not recount values.
    """
    if not isinstance(analysis, CategoricalDescriptiveAnalysis):
        raise TypeError("analysis must be a CategoricalDescriptiveAnalysis")
    return CategoricalDescriptiveAnalysis(
        n_non_missing=analysis.n_non_missing,
        ordered=analysis.ordered,
        levels=tuple(
            ObservedCategoryCount(value=level.value, count=level.count)
            for level in analysis.levels
        ),
    )


def _observed_code_counts(series: pd.Series) -> np.ndarray:
    """Return one count per physical category, including zeros.

    The array is temporary. Only positive counts are retained. A code
    below zero is pandas' missing sentinel and is not a category.
    """
    codes = np.asarray(series.cat.codes.to_numpy(copy=False))
    n_categories = len(series.cat.categories)
    if codes.ndim != 1:
        raise ValueError("category codes must be one-dimensional")
    if codes.size == 0:
        return np.zeros(n_categories, dtype=np.int64)
    if codes.dtype.kind not in {"i", "u"}:
        raise TypeError("category codes must be integers")
    if int(codes.min()) < -1:
        raise ValueError("category codes must be missing or a vocabulary index")
    observed = codes[codes >= 0]
    if observed.size and int(observed.max()) >= n_categories:
        raise ValueError("category code is outside the categorical vocabulary")
    counts = np.bincount(observed.astype(np.intp, copy=False), minlength=n_categories)
    if int(counts.sum()) != int(observed.size):
        raise ValueError("category counts do not match the non-missing codes")
    return counts


def _retain_category(value: object) -> object:
    """Return a category scalar that can be stored without its container.

    NumPy scalars become Python scalars. Tuples are retained element by
    element. The value is not stringified. Pandas and NumPy containers
    are rejected so the result does not keep a Series, an Index, or an
    array. Identity is still the value pandas stored: this function does
    not split values that compare equal.
    """
    if isinstance(value, tuple):
        return tuple(_retain_category(item) for item in value)
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(
        value,
        (np.ndarray, pd.Index, pd.Series, pd.DataFrame, pd.Categorical),
    ):
        raise TypeError("a category value cannot be a pandas or NumPy container")
    if callable(value):
        raise TypeError("a category value cannot be callable")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("a category value must be finite")
        if value == 0.0:
            return 0.0
        return value
    if isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise TypeError("a category value must be finite")
        return value
    try:
        hash(value)
    except TypeError as exc:
        raise TypeError(
            "a category value must be hashable so it can be retained as itself"
        ) from exc
    return value


def _values_at_count(
    levels: Tuple[ObservedCategoryCount, ...],
    count: int,
) -> Tuple[object, ...]:
    if count == 0:
        return ()
    return tuple(level.value for level in levels if level.count == count)


def _proportion(count: int, denominator: int) -> float:
    value = count / denominator
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError("a category proportion must be finite and within [0, 1]")
    return value
