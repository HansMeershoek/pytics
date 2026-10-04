"""Exact duplicate rows for one DataFrame.

A duplicate group is one complete row value that occurs more than once.
Row equality is physical cell equality across physical column positions.
Column labels and the index are not part of that value. ``collect_duplicate_analysis``
reads the DataFrame, keeps the physical positions of repeated rows, and
drops the values. ``build_duplicate_summary`` reads that retained analysis
only.

The result records exact repetition. It does not decide that a repeated
row is an error, and it does not normalize near-duplicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from pytics.analysis.dataset import DatasetAnalysis


@dataclass(frozen=True)
class DuplicateGroup:
    """One repeated row value.

    ``row_positions`` are the physical source rows that carry that value.
    They are strictly increasing, and there are at least two. Position is
    the row identity. The DataFrame index is not. The row value itself is
    not stored.

    ``size`` is the number of those rows. ``excess_count`` is ``size - 1``.
    Neither count treats one occurrence as an original row.
    """

    row_positions: Tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.row_positions, tuple):
            raise TypeError("row_positions must be a tuple")
        if len(self.row_positions) < 2:
            raise ValueError("a duplicate group must contain at least two rows")
        previous = -1
        for position in self.row_positions:
            if type(position) is not int or position < 0:
                raise ValueError("row position must be a non-negative int")
            if position <= previous:
                raise ValueError("row positions must be strictly increasing")
            previous = position

    @property
    def size(self) -> int:
        """Rows that carry this repeated value."""
        return len(self.row_positions)

    @property
    def excess_count(self) -> int:
        """Rows in this group beyond the first occurrence.

        This is ``size - 1``. It does not identify an original row.
        """
        return self.size - 1


@dataclass(frozen=True)
class DuplicateAnalysis:
    """Retained exact duplicate groups for one dataset.

    Groups are ordered by descending size, then by ascending first
    physical row position, then by the position tuple. That order does
    not follow hash randomization, pandas group order, or index labels.
    Equal-sized groups already have distinct first positions when the
    positions are disjoint, so the tuple is a final tie-break.

    Singleton row values are not stored. ``n_rows`` is not stored: the
    dataset analysis checks these groups against its own row count.
    Counts that do not need that row count are derived here.
    """

    duplicate_groups: Tuple[DuplicateGroup, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.duplicate_groups, tuple):
            raise TypeError("duplicate_groups must be a tuple")
        seen: set[int] = set()
        keys = []
        for group in self.duplicate_groups:
            if not isinstance(group, DuplicateGroup):
                raise TypeError("duplicate_groups must contain DuplicateGroup values")
            for position in group.row_positions:
                if position in seen:
                    raise ValueError(
                        "a row position belongs to more than one duplicate group"
                    )
                seen.add(position)
            keys.append(_group_sort_key(group))
        if keys != sorted(keys):
            raise ValueError(
                "duplicate groups must be ordered by descending size, "
                "then ascending first row position"
            )

    @property
    def n_duplicate_groups(self) -> int:
        """How many row values occur more than once."""
        return len(self.duplicate_groups)

    @property
    def n_rows_in_duplicate_groups(self) -> int:
        """Rows that belong to some duplicate group."""
        return _rows_in_duplicate_groups(self.duplicate_groups)

    @property
    def n_excess_duplicate_rows(self) -> int:
        """Rows beyond one occurrence of each distinct row value.

        This equals ``n_rows - n_unique_rows`` once the dataset row count
        is supplied. It is not a count of groups.
        """
        return _excess_duplicate_rows(self.duplicate_groups)

    def n_unique_rows(self, n_rows: int) -> int:
        """Distinct row values in a dataset of ``n_rows`` rows.

        ``None`` is not used. Zero rows have zero distinct values. A
        dataset with rows has at least one.
        """
        return _unique_row_count(n_rows, self.n_excess_duplicate_rows)


@dataclass(frozen=True)
class DuplicateSummary:
    """Product duplicate-row facts for one dataset analysis.

    ``n_rows`` is copied from the dataset analysis. Groups are copies of
    the retained duplicate groups. This summary does not keep that
    analysis, a DataFrame, or the row values.

    Row ratios divide by ``n_rows`` and are ``None`` when there are no
    rows. They are not a quality score.
    """

    n_rows: int
    duplicate_groups: Tuple[DuplicateGroup, ...]

    def __post_init__(self) -> None:
        _require_count(self.n_rows, "n_rows")
        analysis = DuplicateAnalysis(duplicate_groups=self.duplicate_groups)
        _require_positions_within_rows(analysis, self.n_rows)
        _unique_row_count(self.n_rows, analysis.n_excess_duplicate_rows)

    @property
    def n_duplicate_groups(self) -> int:
        """How many row values occur more than once."""
        return len(self.duplicate_groups)

    @property
    def n_rows_in_duplicate_groups(self) -> int:
        """Rows that belong to some duplicate group."""
        return _rows_in_duplicate_groups(self.duplicate_groups)

    @property
    def n_excess_duplicate_rows(self) -> int:
        """Rows beyond one occurrence of each distinct row value."""
        return _excess_duplicate_rows(self.duplicate_groups)

    @property
    def n_unique_rows(self) -> int:
        """Distinct complete row values.

        Zero when there are no rows. Otherwise at least one.
        """
        return _unique_row_count(self.n_rows, self.n_excess_duplicate_rows)

    @property
    def unique_row_ratio(self) -> Optional[float]:
        """Distinct row values divided by all rows.

        ``None`` when there are no rows.
        """
        return _row_ratio(self.n_unique_rows, self.n_rows)

    @property
    def rows_in_duplicate_groups_ratio(self) -> Optional[float]:
        """Rows that belong to a duplicate group, divided by all rows.

        ``None`` when there are no rows.
        """
        return _row_ratio(self.n_rows_in_duplicate_groups, self.n_rows)

    @property
    def excess_duplicate_row_ratio(self) -> Optional[float]:
        """Excess duplicate rows divided by all rows.

        ``None`` when there are no rows.
        """
        return _row_ratio(self.n_excess_duplicate_rows, self.n_rows)


def collect_duplicate_analysis(frame: pd.DataFrame) -> DuplicateAnalysis:
    """Group rows that are exactly equal.

    The argument must already be a pandas DataFrame. Each physical column
    is factorized with pandas, so equal values, including pandas-missing
    values in that column, share one integer code. A row's identity is
    the exact code tuple. Codes are not a lossy row hash, and they are
    discarded before this function returns.

    Column labels are not part of the row. The index is not part of the
    row. Duplicate labels stay separate physical columns. A frame with
    fewer than two rows has no duplicate group, including a frame whose
    cells are unhashable. A frame with two or more rows and no columns
    has one group containing every physical position, because every row
    is the same empty value. Unhashable cell values in a compared column
    raise ``TypeError``. The DataFrame is not modified.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("collect_duplicate_analysis expects a pandas DataFrame")
    n_rows, n_columns = frame.shape
    if n_rows < 2:
        return DuplicateAnalysis(duplicate_groups=())
    if n_columns == 0:
        return DuplicateAnalysis(
            duplicate_groups=(DuplicateGroup(row_positions=tuple(range(n_rows))),)
        )
    codes = _row_codes(frame, n_rows, n_columns)
    return DuplicateAnalysis(duplicate_groups=_groups_from_codes(codes))


def build_duplicate_summary(analysis: DatasetAnalysis) -> DuplicateSummary:
    """Summarize exact duplicate rows from one dataset analysis.

    The argument must already be a ``DatasetAnalysis``. A DataFrame is
    not accepted and is not analyzed. Groups are copied from the retained
    duplicate analysis. They are not recomputed from raw values.
    """
    # Local import: dataset analysis retains DuplicateAnalysis, so this
    # module cannot import DatasetAnalysis at load time.
    from pytics.analysis.dataset import DatasetAnalysis as DatasetAnalysisType

    if not isinstance(analysis, DatasetAnalysisType):
        raise TypeError("build_duplicate_summary expects a DatasetAnalysis")
    groups = tuple(
        DuplicateGroup(row_positions=tuple(group.row_positions))
        for group in analysis.duplicate_analysis.duplicate_groups
    )
    return DuplicateSummary(n_rows=analysis.n_rows, duplicate_groups=groups)


def _require_duplicate_attachment(
    analysis: DuplicateAnalysis,
    *,
    n_rows: int,
    n_columns: int,
) -> None:
    """Check retained groups against the dataset shape."""
    if not isinstance(analysis, DuplicateAnalysis):
        raise TypeError("duplicate_analysis must be a DuplicateAnalysis")
    _require_count(n_rows, "n_rows")
    _require_count(n_columns, "n_columns")
    _require_positions_within_rows(analysis, n_rows)
    if n_columns == 0:
        _require_zero_column_groups(analysis, n_rows)
        return
    _unique_row_count(n_rows, analysis.n_excess_duplicate_rows)


def _row_codes(frame: pd.DataFrame, n_rows: int, n_columns: int) -> np.ndarray:
    """Return one int64 code per cell.

    Pandas ``factorize`` assigns one code to equal values. With its
    default missing sentinel, pandas-missing values in a column share
    that column's missing code. The codes are temporary.
    """
    codes = np.empty((n_rows, n_columns), dtype=np.int64)
    for position in range(n_columns):
        column = frame.iloc[:, position]
        try:
            encoded, _uniques = pd.factorize(column, sort=False)
        except TypeError as exc:
            message = str(exc).lower()
            if "unhashable" not in message and "not hashable" not in message:
                raise
            raise TypeError(
                "exact duplicate analysis cannot group unhashable values "
                f"in column {position}"
            ) from exc
        values = np.asarray(encoded)
        if values.shape != (n_rows,):
            raise ValueError("factorize codes must contain one code per row")
        if not np.issubdtype(values.dtype, np.integer):
            raise TypeError("factorize codes must be integers")
        codes[:, position] = values
    return codes


def _groups_from_codes(codes: np.ndarray) -> Tuple[DuplicateGroup, ...]:
    """Turn exact code rows into ordered duplicate groups.

    Identical code rows are the same row value. The comparison is byte
    equality of the codes, not a hash of the original frame. Groups of
    size one are omitted.
    """
    n_rows, n_columns = codes.shape
    contiguous = np.ascontiguousarray(codes)
    itemsize = n_columns * contiguous.dtype.itemsize
    keys = contiguous.view(np.dtype((np.void, itemsize))).reshape(n_rows)
    _unique_keys, inverse, counts = np.unique(
        keys,
        return_inverse=True,
        return_counts=True,
    )
    if int(counts.max()) < 2:
        return ()
    order = np.argsort(inverse, kind="mergesort")
    sorted_inverse = inverse[order]
    changes = np.flatnonzero(sorted_inverse[1:] != sorted_inverse[:-1]) + 1
    starts = np.concatenate((np.array([0], dtype=np.intp), changes))
    ends = np.concatenate((changes, np.array([n_rows], dtype=np.intp)))
    groups = []
    for index in np.flatnonzero((ends - starts) >= 2).tolist():
        positions = tuple(
            sorted(int(value) for value in order[int(starts[index]) : int(ends[index])])
        )
        groups.append(DuplicateGroup(row_positions=positions))
    groups.sort(key=_group_sort_key)
    return tuple(groups)


def _require_zero_column_groups(analysis: DuplicateAnalysis, n_rows: int) -> None:
    """A zero-column row is one empty value shared by every row."""
    if n_rows < 2:
        return
    expected = (DuplicateGroup(row_positions=tuple(range(n_rows))),)
    if analysis.duplicate_groups != expected:
        raise ValueError(
            "a zero-column dataset with two or more rows has one duplicate group "
            "containing every row"
        )


def _require_positions_within_rows(analysis: DuplicateAnalysis, n_rows: int) -> None:
    for group in analysis.duplicate_groups:
        for position in group.row_positions:
            if position >= n_rows:
                raise ValueError("duplicate row position must be less than n_rows")


def _rows_in_duplicate_groups(groups: Tuple[DuplicateGroup, ...]) -> int:
    return sum(group.size for group in groups)


def _excess_duplicate_rows(groups: Tuple[DuplicateGroup, ...]) -> int:
    return sum(group.excess_count for group in groups)


def _unique_row_count(n_rows: int, n_excess_duplicate_rows: int) -> int:
    _require_count(n_rows, "n_rows")
    _require_count(n_excess_duplicate_rows, "n_excess_duplicate_rows")
    if n_excess_duplicate_rows > n_rows:
        raise ValueError("n_excess_duplicate_rows cannot exceed n_rows")
    unique = n_rows - n_excess_duplicate_rows
    if n_rows > 0 and unique < 1:
        raise ValueError("a dataset with rows has at least one unique row")
    return unique


def _row_ratio(count: int, n_rows: int) -> Optional[float]:
    """``count / n_rows``, or ``None`` when there are no rows."""
    if n_rows == 0:
        return None
    return count / n_rows


def _group_sort_key(
    group: DuplicateGroup,
) -> Tuple[int, int, Tuple[int, ...]]:
    """Descending size, then ascending first position, then the tuple."""
    return (-group.size, group.row_positions[0], group.row_positions)


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")
