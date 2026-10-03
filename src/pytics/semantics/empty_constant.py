"""Empty and Constant interpretations from basic column evidence.

Empty is ``BasicColumnEvidence.is_empty``. Constant is
``BasicColumnEvidence.is_constant``. Empty is tested first. Any other column
gets no interpretation from these rules: absence is not an unknown type.

Confidence is ``Confidence.HIGH`` because both rules are exact definitions
applied to exact full-column counts. That is the existing three-level scale,
not a numeric score. No alternative semantic type is attached.
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
from pytics.semantics.physical import classify_physical_dtype


def interpret_empty_or_constant(
    series: pd.Series,
) -> Optional[SemanticInterpretation]:
    """Infer Empty or Constant, or return None when neither rule applies.

    Physical dtype comes from the Slice 001 classifier. Basic counts are
    collected once and then interpreted. ``None`` means these rules produced
    no semantic interpretation.
    """
    evidence = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    return interpret_empty_or_constant_from_evidence(evidence, physical)


def interpret_empty_or_constant_from_evidence(
    evidence: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Optional[SemanticInterpretation]:
    """Apply Empty, then Constant, to evidence that was already collected."""
    if not isinstance(evidence, BasicColumnEvidence):
        raise TypeError("evidence must be BasicColumnEvidence")
    if not isinstance(physical, PhysicalDtype):
        raise TypeError("physical must be a PhysicalDtype")
    if evidence.is_empty:
        semantic_type = SemanticType.EMPTY
        statement = f"0 non-missing observations out of {evidence.n_total}"
    elif evidence.is_constant:
        semantic_type = SemanticType.CONSTANT
        statement = (
            "1 distinct non-missing value among "
            f"{evidence.n_non_missing} non-missing observations "
            f"out of {evidence.n_total}"
        )
    else:
        return None
    return SemanticInterpretation(
        semantic_type=semantic_type,
        confidence=Confidence.HIGH,
        source=InferenceSource.INFERRED,
        physical=physical,
        evidence=(SemanticEvidence(statement),),
    )
