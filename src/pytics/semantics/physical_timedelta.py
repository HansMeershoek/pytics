"""Empty, Constant, physical Boolean, physical Datetime, then physical Timedelta.

The earlier precedence chain stays as it is. This module calls that chain
and then applies one further rule. A column that survives Empty, Constant,
physical Boolean, and physical Datetime is semantic Timedelta only when its
physical family is timedelta.

Datetime remains a point in time. Timedelta remains a duration. Strings,
objects, numbers, categoricals, and periods are not parsed or coerced into
a duration. There is no rule class or registry.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_datetime import (
    interpret_precedence_from_evidence as datetime_precedence_from_evidence,
)


def interpret_series_precedence(
    series: pd.Series,
) -> Optional[SemanticInterpretation]:
    """Apply the existing precedence, then physical Timedelta.

    Physical dtype is classified once. Basic counts are collected once and
    reused. ``None`` means this chain produced no semantic interpretation.
    The Series is not copied and is not modified.
    """
    physical = classify_physical_dtype(series)
    evidence = collect_basic_column_evidence(series)
    return interpret_precedence_from_evidence(evidence, physical)


def interpret_precedence_from_evidence(
    evidence: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Optional[SemanticInterpretation]:
    """Apply the chain to counts and a physical dtype already collected.

    This function does not recompute missingness or distinct counts, and it
    does not classify the physical dtype again. The Timedelta rule sees only
    the physical family.
    """
    reading = datetime_precedence_from_evidence(evidence, physical)
    if reading is not None:
        return reading
    return _interpret_physical_timedelta(physical)


def _interpret_physical_timedelta(
    physical: PhysicalDtype,
) -> Optional[SemanticInterpretation]:
    """Read Timedelta from a physical timedelta family, or return None.

    No other family matches. Duration-like strings, numbers, objects, and
    categoricals are not inspected. Units are not guessed.
    """
    if physical.family is not PhysicalDtypeFamily.TIMEDELTA:
        return None
    return SemanticInterpretation(
        semantic_type=SemanticType.TIMEDELTA,
        confidence=Confidence.HIGH,
        source=InferenceSource.PHYSICAL_DTYPE,
        physical=physical,
        evidence=(SemanticEvidence("physical dtype is timedelta"),),
    )
