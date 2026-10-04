"""Selected Boolean × Boolean association.

The conditioning variable is the left physical column. The outcome
variable is the right physical column. Directional effects compare
observed outcome-True probabilities. They do not identify a cause.
Phi is the signed symmetric association under False = 0 and True = 1.
The inferential result is a two-sided Fisher exact p-value. SciPy's
odds-ratio statistic is not the stored effect.

A zero cell is not replaced by a continuity correction. An exact
infinite ratio is unavailable. A constant paired margin leaves phi and
the exact test unavailable and keeps the contingency table.
"""

from __future__ import annotations

import math
import warnings
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from pytics.analysis.relationships.models import BooleanAssociationEstimate
from pytics.analysis.relationships.models import BooleanAssociationMethod
from pytics.analysis.relationships.models import BooleanBooleanRelationship
from pytics.analysis.relationships.models import BooleanContingencyTable
from pytics.analysis.relationships.models import BooleanDirectionalEstimate
from pytics.analysis.relationships.models import BooleanDirectionalMethod
from pytics.analysis.relationships.models import BooleanIndependenceMethod
from pytics.analysis.relationships.models import BooleanIndependenceTest
from pytics.analysis.relationships.models import BooleanLevel
from pytics.analysis.relationships.models import ConditionalOutcomeProbability
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import UnavailabilityReason

# A floating evaluation of a unit-interval quantity may sit slightly
# outside the closed interval. A larger departure is not that quantity.
_UNIT_OVERSHOOT = 1e-8

# ``scipy.stats.fisher_exact`` receives a numeric table. Counts above
# signed 64-bit are not passed into that conversion.
_INT64_MAX = 2**63 - 1


def _read_boolean_column(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Return an observed mask and a True-image for one Boolean column.

    ``observed`` is true where the source value is non-missing.
    ``is_true`` is true only where the source value is True. A missing
    value is false in both arrays. A False value is false in ``is_true``
    and true in ``observed``. The arrays are copies. Python ``bool()``
    is not applied. A categorical dtype is rejected even when its
    categories are boolean.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("boolean relationship values must be a pandas Series")
    if not _is_boolean_storage(series.dtype):
        raise TypeError("boolean relationship analysis applies only to boolean storage")
    observed = np.asarray(series.notna().to_numpy(copy=True), dtype=np.bool_)
    true_values = series.eq(True).fillna(False)
    is_true = np.asarray(true_values.to_numpy(copy=True), dtype=np.bool_)
    if observed.shape != (series.shape[0],) or is_true.shape != observed.shape:
        raise ValueError("boolean images must be one-dimensional")
    if np.any(is_true & ~observed):
        raise ValueError("a true boolean value cannot be missing")
    return observed, is_true


def analyze(
    left_observed: np.ndarray,
    left_is_true: np.ndarray,
    right_observed: np.ndarray,
    right_is_true: np.ndarray,
    *,
    left_position: int,
    left_label: object,
    right_position: int,
    right_label: object,
    n_total_rows: int,
) -> BooleanBooleanRelationship:
    """Describe one canonical Boolean pair from prepared column images.

    The left image is the conditioning variable. The right image is the
    outcome variable. Both images cover every dataset row. Pairwise
    missing rows stay in ``n_total_rows`` and out of the table.
    """
    _require_boolean_image("left", left_observed, left_is_true, n_total_rows)
    _require_boolean_image("right", right_observed, right_is_true, n_total_rows)
    n_ff, n_ft, n_tf, n_tt = _contingency_counts(
        left_observed,
        left_is_true,
        right_observed,
        right_is_true,
    )
    return relationship_from_counts(
        n_ff,
        n_ft,
        n_tf,
        n_tt,
        left_position=left_position,
        left_label=left_label,
        right_position=right_position,
        right_label=right_label,
        n_total_rows=n_total_rows,
    )


def relationship_from_counts(
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
    *,
    left_position: int,
    left_label: object,
    right_position: int,
    right_label: object,
    n_total_rows: int,
) -> BooleanBooleanRelationship:
    """Build one Boolean pair from the four logical cell counts.

    ``n_ff`` is conditioning False and outcome False. ``n_ft`` is
    conditioning False and outcome True. ``n_tf`` is conditioning True
    and outcome False. ``n_tt`` is conditioning True and outcome True.
    Products use Python integers. No continuity correction is added.
    """
    for name, count in (
        ("n_ff", n_ff),
        ("n_ft", n_ft),
        ("n_tf", n_tf),
        ("n_tt", n_tt),
    ):
        if type(count) is not int or count < 0:
            raise ValueError(f"{name} must be a non-negative int")
    n_paired = n_ff + n_ft + n_tf + n_tt
    if type(n_total_rows) is not int or n_paired > n_total_rows:
        raise ValueError("n_paired cannot exceed n_total_rows")
    table = BooleanContingencyTable(
        conditioning_false_outcome_false=n_ff,
        conditioning_false_outcome_true=n_ft,
        conditioning_true_outcome_false=n_tf,
        conditioning_true_outcome_true=n_tt,
    )
    return BooleanBooleanRelationship(
        left_position=left_position,
        left_label=left_label,
        right_position=right_position,
        right_label=right_label,
        conditioning_position=left_position,
        outcome_position=right_position,
        n_total_rows=n_total_rows,
        n_paired=n_paired,
        table=table,
        outcome_true_given_conditioning_false=_conditional(
            BooleanLevel.FALSE,
            events=n_ft,
            group=n_ff + n_ft,
            n_paired=n_paired,
        ),
        outcome_true_given_conditioning_true=_conditional(
            BooleanLevel.TRUE,
            events=n_tt,
            group=n_tf + n_tt,
            n_paired=n_paired,
        ),
        probability_difference=_probability_difference(
            n_ff,
            n_ft,
            n_tf,
            n_tt,
            n_paired,
        ),
        probability_ratio=_probability_ratio(n_ff, n_ft, n_tf, n_tt, n_paired),
        phi=_phi(n_ff, n_ft, n_tf, n_tt, n_paired),
        independence=_independence(n_ff, n_ft, n_tf, n_tt, n_paired),
    )


def _is_boolean_storage(dtype: object) -> bool:
    """Return whether this dtype is boolean storage.

    ``is_bool_dtype`` is also true for a categorical whose categories are
    booleans. Those values stay categorical and are not boolean storage.
    """
    if isinstance(dtype, pd.CategoricalDtype):
        return False
    return bool(pd.api.types.is_bool_dtype(dtype))


def _require_boolean_image(
    side: str,
    observed: np.ndarray,
    is_true: np.ndarray,
    n_total_rows: int,
) -> None:
    if not isinstance(observed, np.ndarray) or not isinstance(is_true, np.ndarray):
        raise TypeError(f"{side} boolean images must be NumPy arrays")
    if observed.dtype != np.bool_ or is_true.dtype != np.bool_:
        raise TypeError(f"{side} boolean images must be boolean arrays")
    if observed.shape != (n_total_rows,) or is_true.shape != (n_total_rows,):
        raise ValueError(f"{side} boolean images must cover every dataset row")


def _contingency_counts(
    left_observed: np.ndarray,
    left_is_true: np.ndarray,
    right_observed: np.ndarray,
    right_is_true: np.ndarray,
) -> Tuple[int, int, int, int]:
    """Count the four logical cells from prepared Boolean images.

    Code 0 is False/False, 1 is False/True, 2 is True/False, and 3 is
    True/True. The code uses the conditioning variable as the high bit.
    """
    paired = left_observed & right_observed
    codes = (left_is_true[paired].astype(np.uint8, copy=False) << 1) | right_is_true[
        paired
    ].astype(np.uint8, copy=False)
    counts = np.bincount(codes, minlength=4)
    return int(counts[0]), int(counts[1]), int(counts[2]), int(counts[3])


def _conditional(
    level: BooleanLevel,
    *,
    events: int,
    group: int,
    n_paired: int,
) -> ConditionalOutcomeProbability:
    if n_paired == 0:
        return _unavailable_conditional(
            level,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        )
    if group == 0:
        return _unavailable_conditional(
            level,
            UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
        )
    if events == 0:
        value = 0.0
    elif events == group:
        value = 1.0
    else:
        value = events / group
    return ConditionalOutcomeProbability(
        conditioning_value=level,
        availability=ResultAvailability.AVAILABLE,
        value=value,
        reason=None,
    )


def _probability_difference(
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
    n_paired: int,
) -> BooleanDirectionalEstimate:
    """Return ``P(outcome True | conditioning True) - P(outcome True | False)``."""
    method = BooleanDirectionalMethod.PROBABILITY_DIFFERENCE
    n_conditioning_false = n_ff + n_ft
    n_conditioning_true = n_tf + n_tt
    if n_paired == 0:
        return _unavailable_effect(
            method,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        )
    if n_conditioning_false == 0 or n_conditioning_true == 0:
        return _unavailable_effect(
            method,
            UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
        )
    if n_tt * n_conditioning_false == n_ft * n_conditioning_true:
        return _available_effect(method, 0.0)
    value = _normalize_signed_unit(
        (n_tt / n_conditioning_true) - (n_ft / n_conditioning_false)
    )
    if value is None:
        return _unavailable_effect(method, UnavailabilityReason.NON_FINITE_RESULT)
    return _available_effect(method, value)


def _probability_ratio(
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
    n_paired: int,
) -> BooleanDirectionalEstimate:
    """Return ``P(outcome True | conditioning True) / P(outcome True | False)``."""
    method = BooleanDirectionalMethod.PROBABILITY_RATIO
    n_conditioning_false = n_ff + n_ft
    n_conditioning_true = n_tf + n_tt
    if n_paired == 0:
        return _unavailable_effect(
            method,
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        )
    if n_conditioning_false == 0 or n_conditioning_true == 0:
        return _unavailable_effect(
            method,
            UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
        )
    if n_ft == 0 and n_tt == 0:
        return _unavailable_effect(method, UnavailabilityReason.UNDEFINED_RATIO)
    if n_ft == 0:
        return _unavailable_effect(
            method,
            UnavailabilityReason.MATHEMATICALLY_UNBOUNDED,
        )
    if n_tt == 0:
        return _available_effect(method, 0.0)
    if n_tt * n_conditioning_false == n_ft * n_conditioning_true:
        return _available_effect(method, 1.0)
    try:
        value = (n_tt * n_conditioning_false) / (n_ft * n_conditioning_true)
    except OverflowError:
        return _unavailable_effect(method, UnavailabilityReason.NON_FINITE_RESULT)
    if type(value) is not float or not math.isfinite(value) or value <= 0.0:
        return _unavailable_effect(method, UnavailabilityReason.NON_FINITE_RESULT)
    return _available_effect(method, value)


def _phi(
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
    n_paired: int,
) -> BooleanAssociationEstimate:
    """Return the signed phi coefficient from the 2×2 counts.

    ``(n_tt * n_ff - n_tf * n_ft) / sqrt(marginal product)``. The
    numerator is a Python integer. A zero numerator is ``0.0`` before
    any floating division. The denominator uses logarithms so the four
    marginals are not multiplied in fixed-width arithmetic.
    """
    n_conditioning_false = n_ff + n_ft
    n_conditioning_true = n_tf + n_tt
    n_outcome_false = n_ff + n_tf
    n_outcome_true = n_ft + n_tt
    if n_paired == 0:
        return _unavailable_phi(UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS)
    if (
        n_conditioning_false == 0
        or n_conditioning_true == 0
        or n_outcome_false == 0
        or n_outcome_true == 0
    ):
        return _unavailable_phi(UnavailabilityReason.CONSTANT_PAIRED_VALUES)
    if n_ft == 0 and n_tf == 0:
        return _available_phi(1.0)
    if n_ff == 0 and n_tt == 0:
        return _available_phi(-1.0)
    numerator = n_tt * n_ff - n_tf * n_ft
    if numerator == 0:
        return _available_phi(0.0)
    magnitude = math.exp(
        math.log(abs(numerator))
        - 0.5
        * (
            math.log(n_conditioning_false)
            + math.log(n_conditioning_true)
            + math.log(n_outcome_false)
            + math.log(n_outcome_true)
        )
    )
    value = _normalize_signed_unit(-magnitude if numerator < 0 else magnitude)
    if value is None:
        return _unavailable_phi(UnavailabilityReason.NON_FINITE_RESULT)
    return _available_phi(value)


def _independence(
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
    n_paired: int,
) -> BooleanIndependenceTest:
    """Return a two-sided Fisher exact p-value when every margin is positive.

    The null hypothesis is that the odds ratio is 1, conditional on the
    observed margins. The stored result is only that p-value. The call is
    ``scipy.stats.fisher_exact(table, alternative="two-sided")``.
    """
    n_conditioning_false = n_ff + n_ft
    n_conditioning_true = n_tf + n_tt
    n_outcome_false = n_ff + n_tf
    n_outcome_true = n_ft + n_tt
    if n_paired == 0:
        return _unavailable_test(UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS)
    if (
        n_conditioning_false == 0
        or n_conditioning_true == 0
        or n_outcome_false == 0
        or n_outcome_true == 0
    ):
        return _unavailable_test(UnavailabilityReason.CONSTANT_PAIRED_VALUES)
    if max(n_ff, n_ft, n_tf, n_tt) > _INT64_MAX:
        return _unavailable_test(UnavailabilityReason.NON_FINITE_RESULT)
    p_value = _fisher_p_value(n_ff, n_ft, n_tf, n_tt)
    if p_value is None:
        return _unavailable_test(UnavailabilityReason.NON_FINITE_RESULT)
    return BooleanIndependenceTest(
        method=BooleanIndependenceMethod.FISHER_EXACT,
        frequentist=FrequentistEvidence(
            availability=ResultAvailability.AVAILABLE,
            p_value=p_value,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=None,
        ),
    )


def _fisher_p_value(n_ff: int, n_ft: int, n_tf: int, n_tt: int) -> Optional[float]:
    """Two-sided Fisher p-value. The returned odds ratio is discarded."""
    table = [[n_ff, n_ft], [n_tf, n_tt]]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = fisher_exact(table, alternative="two-sided")
    except (ValueError, FloatingPointError, OverflowError):
        return None
    p_value = getattr(result, "pvalue", None)
    if p_value is None:
        try:
            p_value = result[1]  # type: ignore[index]
        except (TypeError, IndexError, KeyError):
            return None
    return _as_p_value(p_value)


def _as_p_value(value: object) -> Optional[float]:
    if isinstance(value, (bool, np.bool_)):
        return None
    if isinstance(value, np.ndarray):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0.0 or number > 1.0:
        return None
    if number == 0.0:
        return 0.0
    return number


def _normalize_signed_unit(value: float) -> Optional[float]:
    if not math.isfinite(value):
        return None
    if value > 1.0:
        if value - 1.0 <= _UNIT_OVERSHOOT:
            return 1.0
        return None
    if value < -1.0:
        if -1.0 - value <= _UNIT_OVERSHOOT:
            return -1.0
        return None
    if value == 0.0:
        return 0.0
    return float(value)


def _unavailable_conditional(
    level: BooleanLevel,
    reason: UnavailabilityReason,
) -> ConditionalOutcomeProbability:
    return ConditionalOutcomeProbability(
        conditioning_value=level,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _available_effect(
    method: BooleanDirectionalMethod,
    value: float,
) -> BooleanDirectionalEstimate:
    return BooleanDirectionalEstimate(
        method=method,
        availability=ResultAvailability.AVAILABLE,
        value=value,
        reason=None,
    )


def _unavailable_effect(
    method: BooleanDirectionalMethod,
    reason: UnavailabilityReason,
) -> BooleanDirectionalEstimate:
    return BooleanDirectionalEstimate(
        method=method,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _available_phi(value: float) -> BooleanAssociationEstimate:
    return BooleanAssociationEstimate(
        method=BooleanAssociationMethod.PHI,
        availability=ResultAvailability.AVAILABLE,
        value=value,
        reason=None,
    )


def _unavailable_phi(reason: UnavailabilityReason) -> BooleanAssociationEstimate:
    return BooleanAssociationEstimate(
        method=BooleanAssociationMethod.PHI,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=reason,
    )


def _unavailable_test(reason: UnavailabilityReason) -> BooleanIndependenceTest:
    return BooleanIndependenceTest(
        method=BooleanIndependenceMethod.FISHER_EXACT,
        frequentist=FrequentistEvidence(
            availability=ResultAvailability.UNAVAILABLE,
            p_value=None,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=reason,
        ),
    )
