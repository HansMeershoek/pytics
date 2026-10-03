"""One column analysis, including the evidence that semantic inference uses.

``analyze_series`` is the only column collection path. It classifies the
physical dtype once, collects basic evidence once, and keeps every evidence
object that this path actually produces. ``None`` means that family was not
collected. It does not mean the underlying count was zero.

Frequency evidence and string-content evidence are not collected. No current
candidate rule reads them, and this dataset slice has no consumer that needs
them. Structural precedence still returns before candidate-family collection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Tuple

import pandas as pd

from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.core_candidates import assess_categorical_candidate
from pytics.semantics.core_candidates import assess_numeric_candidate
from pytics.semantics.core_candidates import assess_text_candidate
from pytics.semantics.identifier_candidate import assess_identifier_candidate
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.inferred import build_inferred_semantic_result
from pytics.semantics.numeric_structure_evidence import NumericStructureEvidence
from pytics.semantics.numeric_structure_evidence import (
    collect_numeric_structure_evidence,
)
from pytics.semantics.pattern_evidence import PatternEvidence
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_precedence_from_evidence
from pytics.semantics.resolution import resolve_semantics
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import (
    collect_string_structure_evidence,
)

# These families are the collector contracts already implemented. The
# analysis uses them only to avoid calling a collector that would reject
# the dtype. It does not reinterpret the families.
_NUMERIC_FAMILIES = frozenset(
    {
        PhysicalDtypeFamily.INTEGER,
        PhysicalDtypeFamily.FLOATING,
    }
)
_STRING_FAMILIES = frozenset(
    {
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    }
)
# The string-structure collector uses this phrase for a population that is
# not a Python string population. That rejection is applicability, not an
# invalid Series.
_INELIGIBLE_STRING_POPULATION = "every non-missing value is a Python str"


@dataclass(frozen=True)
class ColumnEvidence:
    """Evidence retained for one column.

    ``basic`` is always present. The other families are present only when
    this observation path collected them. A missing family is ``None``.
    A collected family keeps the object the collector returned, including
    its composition with ``basic`` or with string structure.
    """

    basic: BasicColumnEvidence
    numeric_structure: Optional[NumericStructureEvidence] = None
    string_structure: Optional[StringStructureEvidence] = None
    pattern: Optional[PatternEvidence] = None

    def __post_init__(self) -> None:
        _require(self.basic, BasicColumnEvidence, "basic")
        if self.numeric_structure is not None:
            _require(
                self.numeric_structure,
                NumericStructureEvidence,
                "numeric_structure",
            )
            if self.numeric_structure.basic is not self.basic:
                raise ValueError(
                    "numeric_structure.basic must be this evidence's basic"
                )
        if self.string_structure is not None:
            _require(
                self.string_structure,
                StringStructureEvidence,
                "string_structure",
            )
            if self.string_structure.basic is not self.basic:
                raise ValueError("string_structure.basic must be this evidence's basic")
        if self.pattern is not None:
            _require(self.pattern, PatternEvidence, "pattern")
            if self.string_structure is None:
                raise ValueError("pattern evidence requires string-structure evidence")
            if self.pattern.string_structure is not self.string_structure:
                raise ValueError(
                    "pattern.string_structure must be this evidence's "
                    "string_structure"
                )
        if self.numeric_structure is not None and self.string_structure is not None:
            raise ValueError(
                "numeric-structure evidence and string-structure evidence "
                "do not apply to the same column"
            )


@dataclass(frozen=True)
class ColumnAnalysis:
    """Internal analysis of one physical column.

    ``position`` is the column's place in the source column axis.
    ``label`` is the original column label. It is not a display string,
    and it is not semantic evidence. ``physical``, ``evidence``, and
    ``inferred`` are the facts this path already produced. The Series
    itself is not stored.
    """

    position: int
    label: object
    physical: PhysicalDtype
    evidence: ColumnEvidence
    inferred: InferredSemanticResult

    def __post_init__(self) -> None:
        if type(self.position) is not int or self.position < 0:
            raise ValueError("position must be a non-negative int")
        _require(self.physical, PhysicalDtype, "physical")
        _require(self.evidence, ColumnEvidence, "evidence")
        _require(self.inferred, InferredSemanticResult, "inferred")
        if self.inferred.physical is not self.physical:
            raise ValueError("inferred.physical must be this column's physical")


def analyze_series(
    series: pd.Series,
    *,
    position: int = 0,
    label: object = None,
) -> ColumnAnalysis:
    """Analyze one Series and retain the evidence used to infer it.

    ``position`` and ``label`` are stored as column identity. They are not
    read by physical classification, evidence collection, candidate
    assessment, or resolution. The Series name and index are not read.
    The Series is not copied and is not modified.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("analyze_series expects a pandas Series")
    if type(position) is not int or position < 0:
        raise ValueError("position must be a non-negative int")
    physical = classify_physical_dtype(series)
    basic = collect_basic_column_evidence(series)
    structural = interpret_precedence_from_evidence(basic, physical)
    if structural is not None:
        resolution = resolve_semantics(structural_interpretation=structural)
        numeric_structure = None
        string_structure = None
        pattern = None
    else:
        numeric_structure, string_structure, pattern = _evidence_for_candidates(
            series,
            basic,
            physical,
        )
        candidates = _assess_candidates(
            basic,
            physical,
            numeric_structure,
            string_structure,
            pattern,
        )
        resolution = resolve_semantics(candidates=candidates)
    inferred = build_inferred_semantic_result(physical, resolution)
    evidence = ColumnEvidence(
        basic=basic,
        numeric_structure=numeric_structure,
        string_structure=string_structure,
        pattern=pattern,
    )
    return ColumnAnalysis(
        position=position,
        label=label,
        physical=physical,
        evidence=evidence,
        inferred=inferred,
    )


def _evidence_for_candidates(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Tuple[
    Optional[NumericStructureEvidence],
    Optional[StringStructureEvidence],
    Optional[PatternEvidence],
]:
    """Collect the evidence the current assessors can consume.

    Frequency evidence is not collected. Numeric-structure evidence is
    collected only for integer and floating storage. String structure and
    pattern evidence are collected only when the string-structure collector
    accepts the population. String-content evidence is not collected.
    Other families are assessed from the basic evidence and the physical
    dtype alone.
    """
    if physical.family in _NUMERIC_FAMILIES:
        numeric = collect_numeric_structure_evidence(series, basic, physical)
        return numeric, None, None
    if physical.family in _STRING_FAMILIES:
        structure, pattern = _string_evidence(series, basic, physical)
        return None, structure, pattern
    return None, None, None


def _string_evidence(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Tuple[Optional[StringStructureEvidence], Optional[PatternEvidence]]:
    """Collect string structure, then pattern evidence from that same object.

    An ineligible population collects neither. Pattern evidence is not
    rebuilt from a second string-structure pass.
    """
    structure = _collect_applicable_string_structure(series, basic, physical)
    if structure is None:
        return None, None
    pattern = collect_pattern_evidence(series, structure, physical)
    return structure, pattern


def _collect_applicable_string_structure(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Optional[StringStructureEvidence]:
    """Return string structure, or None when the collector rejects it.

    An applicability ``TypeError`` means this population is not string
    evidence. Mixed object values and ``bytes`` are that case. They are
    not coerced, and they are not an inference failure. Any other error
    still propagates.
    """
    try:
        return collect_string_structure_evidence(series, basic, physical)
    except TypeError as exc:
        if _INELIGIBLE_STRING_POPULATION not in str(exc):
            raise
        return None


def _assess_candidates(
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
    numeric_structure: Optional[NumericStructureEvidence],
    string_structure: Optional[StringStructureEvidence],
    pattern: Optional[PatternEvidence],
) -> Tuple[CandidateAssessment, ...]:
    """Assess every current candidate from one evidence bundle.

    The assessors do not receive the Series. Omitted evidence stays
    ``None``. A zero-filled stand-in is not created for a family that
    does not apply.
    """
    return (
        assess_identifier_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
        ),
        assess_numeric_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
        ),
        assess_categorical_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
        ),
        assess_text_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
        ),
    )


def _require(value: Any, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")
