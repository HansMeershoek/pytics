"""Empty, Constant, physical Boolean, then physical Datetime.

The earlier Boolean chain stays as it is. This module calls that chain and
then applies one further rule. A column that survives Empty, Constant, and
physical Boolean is semantic Datetime only when its physical family is
native datetime or timezone-aware datetime. Both families use
``SemanticType.DATETIME``. The timezone-aware family stays visible on the
physical dtype and in the evidence statement.

Timedelta and period storage are not Datetime. Strings, objects, integers,
and categoricals are not parsed or coerced into datetime. There is no rule
class or registry.
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
from pytics.semantics.physical_boolean import (
    interpret_empty_constant_or_physical_boolean_from_evidence,
)


def interpret_series_precedence(
    series: pd.Series,
) -> Optional[SemanticInterpretation]:
    """Apply Empty, Constant, physical Boolean, then physical Datetime.

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
    does not classify the physical dtype again.
    """
    reading = interpret_empty_constant_or_physical_boolean_from_evidence(
        evidence,
        physical,
    )
    if reading is not None:
        return reading
    return _interpret_physical_datetime(physical)


def _interpret_physical_datetime(
    physical: PhysicalDtype,
) -> Optional[SemanticInterpretation]:
    """Read Datetime from a physical datetime family, or return None.

    Native datetime and timezone-aware datetime are the same semantic type.
    The evidence statement keeps the storage distinction. No other family
    matches, including timedelta and period.
    """
    if physical.family is PhysicalDtypeFamily.DATETIME:
        statement = "physical dtype is datetime"
    elif physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE:
        statement = "physical dtype is timezone-aware datetime"
    else:
        return None
    return SemanticInterpretation(
        semantic_type=SemanticType.DATETIME,
        confidence=Confidence.HIGH,
        source=InferenceSource.PHYSICAL_DTYPE,
        physical=physical,
        evidence=(SemanticEvidence(statement),),
    )
