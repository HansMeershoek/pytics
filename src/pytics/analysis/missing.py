"""Observed missingness structure for one DataFrame.

Column missing counts already live on basic evidence. A missingness
pattern is which physical columns are missing together in a row, so it
cannot be rebuilt from those independent counts. ``collect_missing_analysis``
reads the DataFrame once, keeps exact aggregate counts, and drops the
mask.

The result records where values are missing. It does not say why, and it
does not classify a missingness mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RowMissingnessBucket:
    """How many rows share one missing-column count.

    ``missing_columns_count`` is how many physical columns are missing in
    each of those rows. ``row_count`` is how many rows have that count.
    Zero-count buckets are omitted. Source row indices are not stored.

    ``row_ratio`` divides ``row_count`` by the dataset row count. That
    denominator is not stored here.
    """

    missing_columns_count: int
    row_count: int

    def __post_init__(self) -> None:
        _require_count(self.missing_columns_count, "missing_columns_count")
        _require_positive(self.row_count, "row_count")

    def row_ratio(self, n_rows: int) -> Optional[float]:
        """Rows in this bucket divided by ``n_rows``.

        ``None`` when ``n_rows`` is zero. The denominator is the dataset
        row count, not a count stored on this bucket.
        """
        _require_count(n_rows, "n_rows")
        return _ratio(self.row_count, n_rows)


@dataclass(frozen=True)
class MissingnessPattern:
    """One exact recurring missingness pattern.

    ``positions`` are the physical column positions missing together.
    They are strictly increasing, so they are unique. Position is the
    identity. A label is not. The empty tuple is the complete-row
    pattern: no column is missing.

    ``row_count`` is how many rows have this pattern. ``row_ratio``
    divides that count by the dataset row count. The denominator is not
    stored on the pattern.
    """

    positions: Tuple[int, ...]
    row_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.positions, tuple):
            raise TypeError("positions must be a tuple")
        previous = -1
        for position in self.positions:
            if type(position) is not int or position < 0:
                raise ValueError("position must be a non-negative int")
            if position <= previous:
                raise ValueError("positions must be strictly increasing")
            previous = position
        _require_positive(self.row_count, "row_count")

    def row_ratio(self, n_rows: int) -> Optional[float]:
        """Rows with this pattern divided by ``n_rows``.

        ``None`` when ``n_rows`` is zero. The denominator is the dataset
        row count, not a count stored on this pattern.
        """
        _require_count(n_rows, "n_rows")
        return _ratio(self.row_count, n_rows)


@dataclass(frozen=True)
class MissingAnalysis:
    """Retained cross-column missingness for one dataset.

    ``row_distribution`` is ordered by increasing
    ``missing_columns_count``. ``patterns`` is ordered by descending
    ``row_count``, then by ascending ``positions`` under ordinary tuple
    order. That order does not follow first-seen row order or pandas
    groupby order. A shorter position tuple that is a prefix of a longer
    one sorts first when the counts are equal. The empty pattern sorts
    before every non-empty pattern of the same count.

    These aggregates are exact. There is no pattern cutoff. The boolean
    mask used to count them is not stored. ``n_rows`` is not stored:
    the dataset analysis checks these aggregates against its own row count.
    """

    row_distribution: Tuple[RowMissingnessBucket, ...]
    patterns: Tuple[MissingnessPattern, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.row_distribution, tuple):
            raise TypeError("row_distribution must be a tuple")
        if not isinstance(self.patterns, tuple):
            raise TypeError("patterns must be a tuple")
        previous_count = -1
        distribution: dict[int, int] = {}
        for bucket in self.row_distribution:
            if not isinstance(bucket, RowMissingnessBucket):
                raise TypeError(
                    "row_distribution must contain RowMissingnessBucket values"
                )
            if bucket.missing_columns_count <= previous_count:
                raise ValueError(
                    "row distribution must follow increasing missing_columns_count"
                )
            previous_count = bucket.missing_columns_count
            distribution[bucket.missing_columns_count] = bucket.row_count
        seen: set[Tuple[int, ...]] = set()
        keys = []
        from_patterns: dict[int, int] = {}
        for pattern in self.patterns:
            if not isinstance(pattern, MissingnessPattern):
                raise TypeError("patterns must contain MissingnessPattern values")
            if pattern.positions in seen:
                raise ValueError("pattern positions must be unique")
            seen.add(pattern.positions)
            keys.append(_pattern_sort_key(pattern))
            width = len(pattern.positions)
            from_patterns[width] = from_patterns.get(width, 0) + pattern.row_count
        if keys != sorted(keys):
            raise ValueError(
                "patterns must be ordered by descending row count, then positions"
            )
        if from_patterns != distribution:
            raise ValueError("pattern row counts must match the row distribution")

    @property
    def n_patterns(self) -> int:
        """How many distinct missingness patterns were observed."""
        return len(self.patterns)

    @property
    def n_complete_rows(self) -> int:
        """Rows whose missingness pattern is empty.

        Zero when no row is complete, including when there are no rows.
        """
        for bucket in self.row_distribution:
            if bucket.missing_columns_count == 0:
                return bucket.row_count
        return 0


def collect_missing_analysis(frame: pd.DataFrame) -> MissingAnalysis:
    """Count exact row missingness and missingness patterns.

    The argument must already be a pandas DataFrame. Missingness is
    pandas ``DataFrame.isna``. Ordinary literals such as an empty
    string, whitespace, or ``"NA"`` stay observed unless pandas already
    treats that value as missing. The DataFrame is not modified.

    A frame with no rows has no buckets and no patterns. A frame with
    rows and no columns has one complete-row pattern, because those
    rows contain no missing cell. Otherwise one boolean mask is built
    and copied into contiguous row order so identical rows can be
    counted. Both arrays are discarded before this function returns.
    Observed patterns are kept. Their number cannot exceed the row count.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("collect_missing_analysis expects a pandas DataFrame")
    n_rows, n_columns = frame.shape
    if n_rows == 0:
        return MissingAnalysis(row_distribution=(), patterns=())
    if n_columns == 0:
        return MissingAnalysis(
            row_distribution=(
                RowMissingnessBucket(missing_columns_count=0, row_count=n_rows),
            ),
            patterns=(MissingnessPattern(positions=(), row_count=n_rows),),
        )
    values = _boolean_missingness(frame, n_rows, n_columns)
    return _analysis_from_mask(values)


def _require_missing_attachment(
    analysis: MissingAnalysis,
    *,
    n_rows: int,
    n_columns: int,
    n_missing_cells: int,
    missing_counts: Tuple[int, ...],
) -> None:
    """Check retained patterns against dataset and column counts."""
    if not isinstance(analysis, MissingAnalysis):
        raise TypeError("missing_analysis must be a MissingAnalysis")
    if sum(pattern.row_count for pattern in analysis.patterns) != n_rows:
        raise ValueError("pattern row counts must sum to n_rows")
    observed = [0] * n_columns
    weighted = 0
    for pattern in analysis.patterns:
        weighted += len(pattern.positions) * pattern.row_count
        for position in pattern.positions:
            if position >= n_columns:
                raise ValueError("pattern position must be less than n_columns")
            observed[position] += pattern.row_count
    if weighted != n_missing_cells:
        raise ValueError("weighted pattern cells must equal n_missing_cells")
    for position, expected in enumerate(missing_counts):
        if observed[position] != expected:
            raise ValueError("pattern margins must equal column n_missing")


def _boolean_missingness(
    frame: pd.DataFrame,
    n_rows: int,
    n_columns: int,
) -> np.ndarray:
    """Return one C-contiguous boolean mask.

    Pandas may store ``DataFrame.isna`` column-major. Counting identical
    rows needs each row in one contiguous byte string, so this copies
    when the mask is not already C-contiguous. The result is temporary.
    """
    mask = frame.isna()
    if not isinstance(mask, pd.DataFrame):
        raise TypeError("pandas missingness mask must be a DataFrame")
    if mask.shape != (n_rows, n_columns):
        raise ValueError("missingness mask shape must match the DataFrame")
    values = mask.to_numpy(copy=False)
    if values.dtype != np.bool_:
        raise TypeError("pandas missingness mask must be boolean")
    return np.ascontiguousarray(values)


def _analysis_from_mask(values: np.ndarray) -> MissingAnalysis:
    """Aggregate a boolean mask into buckets and exact patterns."""
    n_rows, n_columns = values.shape
    row_missing = values.sum(axis=1)
    counts = np.bincount(row_missing.astype(np.intp, copy=False))
    buckets = tuple(
        RowMissingnessBucket(missing_columns_count=index, row_count=int(count))
        for index, count in enumerate(counts.tolist())
        if count
    )
    keys = values.view(np.dtype((np.void, n_columns))).reshape(n_rows)
    unique_keys, unique_counts = np.unique(keys, return_counts=True)
    patterns = []
    for key, count in zip(unique_keys.tolist(), unique_counts.tolist()):
        row = np.frombuffer(key, dtype=np.uint8)
        positions = tuple(int(index) for index in np.flatnonzero(row))
        patterns.append(MissingnessPattern(positions=positions, row_count=int(count)))
    patterns.sort(key=_pattern_sort_key)
    return MissingAnalysis(row_distribution=buckets, patterns=tuple(patterns))


def _pattern_sort_key(pattern: MissingnessPattern) -> Tuple[int, Tuple[int, ...]]:
    """Descending row count, then ascending positions."""
    return (-pattern.row_count, pattern.positions)


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_positive(value: object, field: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field} must be a positive int")


def _ratio(count: int, denominator: int) -> Optional[float]:
    if denominator == 0:
        return None
    return count / denominator
