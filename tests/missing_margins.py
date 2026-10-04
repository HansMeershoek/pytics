"""Build a MissingAnalysis whose column margins match given counts.

Manual dataset analyses do not have a joint row pattern. This helper
places each column's missing values in its first rows and counts that
frame with the production collector. It is a fixture, not a second
definition of missingness.
"""

from __future__ import annotations

from typing import Sequence

import pandas as pd

from pytics.analysis.missing import MissingAnalysis
from pytics.analysis.missing import collect_missing_analysis


def missing_analysis_for_margins(
    n_rows: int,
    missing_counts: Sequence[int],
) -> MissingAnalysis:
    """Return patterns consistent with ``missing_counts`` over ``n_rows``."""
    n_columns = len(missing_counts)
    if n_rows == 0 or n_columns == 0:
        if n_columns == 0:
            frame = pd.DataFrame(index=range(n_rows))
        else:
            frame = pd.DataFrame(
                {position: pd.Series(dtype="float64") for position in range(n_columns)}
            )
        return collect_missing_analysis(frame)
    columns = {}
    for position, count in enumerate(missing_counts):
        columns[position] = [pd.NA if row < count else 0 for row in range(n_rows)]
    return collect_missing_analysis(pd.DataFrame(columns))
