"""Empty, Constant, then physical Boolean.

Empty and Constant come from Slice 002 and keep precedence. A column that
survives those rules is semantic Boolean only when its physical dtype
family is Boolean. That reading is directly supported by the physical
dtype, so its source is ``InferenceSource.PHYSICAL_DTYPE`` and its
confidence is ``Confidence.HIGH``. Cardinality, token strings, object
values, and categorical values are not Boolean evidence in this module.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.empty_constant import interpret_empty_or_constant_from_evidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype


def interpret_empty_constant_or_physical_boolean(
    series: pd.Series,
) -> Optional[SemanticInterpretation]:
    """Apply Empty, then Constant, then physical Boolean.

    Physical dtype is classified once. Basic counts are collected once and
    reused. ``None`` means this chain produced no semantic interpretation.
    The Series is not copied and is not modified.
    """
    physical = classify_physical_dtype(series)
    evidence = collect_basic_column_evidence(series)
    return interpret_empty_constant_or_physical_boolean_from_evidence(
        evidence,
        physical,
    )


def interpret_empty_constant_or_physical_boolean_from_evidence(
    evidence: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Optional[SemanticInterpretation]:
    """Apply the chain to counts and a physical dtype already collected.

    This function does not recompute missingness or distinct counts.
    """
    reading = interpret_empty_or_constant_from_evidence(evidence, physical)
    if reading is not None:
        return reading
    if physical.family is PhysicalDtypeFamily.BOOLEAN:
        return SemanticInterpretation(
            semantic_type=SemanticType.BOOLEAN,
            confidence=Confidence.HIGH,
            source=InferenceSource.PHYSICAL_DTYPE,
            physical=physical,
            evidence=(SemanticEvidence("physical dtype is boolean"),),
        )
    return None
