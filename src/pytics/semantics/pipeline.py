"""Series convenience wrapper for column analysis.

Collection, candidate assessment, and resolution live in
``pytics.analysis.column``. This wrapper returns only the inferred result
of that same analysis.
"""

from __future__ import annotations

import pandas as pd

from pytics.analysis.column import analyze_series
from pytics.semantics.inferred import InferredSemanticResult


def infer_series_semantics(series: pd.Series) -> InferredSemanticResult:
    """Infer the semantic result of one Series.

    The Series is not copied and is not modified. There is no sampling,
    no user configuration, and no use of the Series name or index. Evidence
    collected for the inference is retained by ``analyze_series`` and is
    not part of this return value. A column with no supported candidate
    still returns an inferred result.
    """
    return analyze_series(series).inferred
