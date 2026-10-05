"""Data profiling for pandas DataFrames.

``profile`` and ``compare`` are the top-level entry points. They return
the structured results from :mod:`pytics.results`. Analysis modules load
when those functions are called.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from pytics.results.comparison import ComparisonResult
    from pytics.results.profile import ProfileResult

__version__ = "1.1.5"
__all__ = ["profile", "compare"]


def profile(frame: pd.DataFrame, *, target: object = None) -> ProfileResult:
    """Profile one DataFrame and return its structured result.

    Delegates to :func:`pytics.results.profile_result`. ``target`` is
    keyword-only and is passed through. ``None`` requests no target.
    """
    from pytics.results import profile_result

    return profile_result(frame, target=target)


def compare(
    reference: pd.DataFrame,
    comparison: pd.DataFrame,
    *,
    target: object = None,
) -> ComparisonResult:
    """Compare two DataFrames and return the structured result.

    Delegates to :func:`pytics.results.comparison_result`. ``target`` is
    keyword-only and is passed through. ``None`` requests no target drift.
    """
    from pytics.results import comparison_result

    return comparison_result(reference, comparison, target=target)
