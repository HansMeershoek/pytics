"""Descriptive counts for a column selected as Boolean.

These facts profile a Boolean population. They are not semantic-inference
evidence. They do not select Boolean, and they do not read a semantic type.
``{0, 1}``, ``{0.0, 1.0}``, and two-valued strings are not counted here.

``True`` and ``False`` are the only non-missing values. Missing values
are excluded. The ratios use that non-missing count as the denominator.
A zero count is not an observed class. Missing values are not a class.
The largest and smallest class facts are read from these two counts.
A tie keeps both ``False`` and ``True``. There is no balanced or
imbalanced label. The source Series is not retained.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BooleanDescriptiveAnalysis:
    """True and false counts for one Boolean column.

    ``n_non_missing`` is ``true_count + false_count``. It is not stored.
    ``true_ratio`` and ``false_ratio`` divide by that count. Both are
    ``None`` when it is zero. A selected Boolean column does not have an
    empty population: Empty and Constant take precedence. A directly
    constructed result may still use zero for both counts.

    Missing counts are not stored. They stay on the universal column facts.
    """

    true_count: int
    false_count: int

    def __post_init__(self) -> None:
        _require_count(self.true_count, "true_count")
        _require_count(self.false_count, "false_count")

    @property
    def n_non_missing(self) -> int:
        """Non-missing Boolean observations, ``true_count + false_count``."""
        return self.true_count + self.false_count

    @property
    def true_ratio(self) -> Optional[float]:
        """``True`` values divided by non-missing values.

        ``None`` when there is no non-missing value. The denominator is
        not the row count.
        """
        return _ratio(self.true_count, self.n_non_missing)

    @property
    def false_ratio(self) -> Optional[float]:
        """``False`` values divided by non-missing values.

        ``None`` when there is no non-missing value. The denominator is
        not the row count.
        """
        return _ratio(self.false_count, self.n_non_missing)

    @property
    def n_observed_classes(self) -> int:
        """How many of ``False`` and ``True`` occur at least once."""
        return int(self.false_count > 0) + int(self.true_count > 0)

    @property
    def largest_class_count(self) -> Optional[int]:
        """Larger of the two class counts.

        ``None`` when both counts are zero. This is not an imbalance
        threshold. A tie is the shared count.
        """
        if self.n_non_missing == 0:
            return None
        return max(self.false_count, self.true_count)

    @property
    def smallest_class_count(self) -> Optional[int]:
        """Smaller count among classes that occur at least once.

        ``None`` when both counts are zero. A class with count zero is
        not observed, so it is not the smallest class.
        """
        observed = [count for count in (self.false_count, self.true_count) if count > 0]
        if not observed:
            return None
        return min(observed)

    @property
    def largest_class_proportion(self) -> Optional[float]:
        """Largest class count divided by non-missing values.

        ``None`` when there is no non-missing value. The denominator is
        not the row count.
        """
        count = self.largest_class_count
        if count is None:
            return None
        return _ratio(count, self.n_non_missing)

    @property
    def smallest_class_proportion(self) -> Optional[float]:
        """Smallest observed class count divided by non-missing values.

        ``None`` when there is no non-missing value. The denominator is
        not the row count.
        """
        count = self.smallest_class_count
        if count is None:
            return None
        return _ratio(count, self.n_non_missing)

    @property
    def largest_class_values(self) -> Tuple[bool, ...]:
        """``False`` and ``True`` values that share the largest count.

        ``False`` precedes ``True`` when both share that count. The
        sequence is empty when both counts are zero.
        """
        return _class_values(self, self.largest_class_count)

    @property
    def smallest_class_values(self) -> Tuple[bool, ...]:
        """``False`` and ``True`` values that share the smallest observed count.

        ``False`` precedes ``True`` when both share that count. The
        sequence is empty when both counts are zero.
        """
        return _class_values(self, self.smallest_class_count)


def _class_values(
    analysis: BooleanDescriptiveAnalysis,
    count: Optional[int],
) -> Tuple[bool, ...]:
    if count is None:
        return ()
    values = []
    if analysis.false_count == count:
        values.append(False)
    if analysis.true_count == count:
        values.append(True)
    return tuple(values)


def collect_boolean_descriptive_analysis(
    series: pd.Series,
) -> BooleanDescriptiveAnalysis:
    """Count ``True`` and ``False`` in one boolean Series.

    The Series must already use boolean storage. That is NumPy ``bool``,
    pandas nullable ``boolean``, or another dtype the physical classifier
    already calls boolean, including sparse boolean storage. A categorical
    dtype is rejected even when its values are boolean. Integer, floating,
    string, and object storage are rejected. ``1`` is not read as ``True``.
    ``0`` is not read as ``False``. Strings are not parsed.

    Missing values are dropped with pandas missingness and contribute to
    neither count. The Series is not modified, and its dtype is not changed.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_boolean_descriptive_analysis expects a pandas Series")
    if not _is_boolean_storage(series.dtype):
        raise TypeError("boolean descriptive analysis applies only to boolean storage")
    values = _boolean_values(series)
    true_count = int(np.count_nonzero(values))
    false_count = int(values.size) - true_count
    return BooleanDescriptiveAnalysis(
        true_count=true_count,
        false_count=false_count,
    )


def _is_boolean_storage(dtype: object) -> bool:
    """Return whether this dtype is boolean storage.

    ``is_bool_dtype`` is also true for a categorical whose categories are
    booleans. Those values stay categorical and are not boolean storage.
    """
    if isinstance(dtype, pd.CategoricalDtype):
        return False
    return bool(pd.api.types.is_bool_dtype(dtype))


def _boolean_values(series: pd.Series) -> np.ndarray:
    """Return non-missing values as a NumPy boolean array.

    The array contains only ``True`` and ``False``. ``count_nonzero`` then
    counts ``True`` inside that boolean array. It is not applied to
    integers, strings, or objects, and it does not call ``bool()`` on them.
    """
    observed = series.dropna()
    values = observed.to_numpy(copy=False)
    if isinstance(values, np.ndarray) and values.dtype.kind == "b":
        return values
    raise TypeError("boolean descriptive analysis applies only to boolean values")


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _ratio(count: int, denominator: int) -> Optional[float]:
    if denominator == 0:
        return None
    return count / denominator
