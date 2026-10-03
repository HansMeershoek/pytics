"""Column-level semantic inference for one Series.

One Series enters and one inferred result leaves. Physical dtype is
classified once. Basic evidence is collected once. Structural precedence
is the existing evidence-level helper, not a second copy of those rules.
Candidate assessors then see only evidence that already applies to the
observed family. This module does not add a semantic rule, a confidence,
or a configuration.
"""

from __future__ import annotations

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
from pytics.semantics.string_content_evidence import collect_string_content_evidence
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import (
    collect_string_structure_evidence,
)

# These families are the collector contracts already implemented. The
# pipeline uses them only to avoid calling a collector that would reject
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


def infer_series_semantics(series: pd.Series) -> InferredSemanticResult:
    """Infer the semantic result of one Series.

    The Series is not copied and is not modified. There is no sampling,
    no user configuration, and no use of the Series name or index. A
    column with no supported candidate still returns an inferred result.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("infer_series_semantics expects a pandas Series")
    physical = classify_physical_dtype(series)
    basic = collect_basic_column_evidence(series)
    structural = interpret_precedence_from_evidence(basic, physical)
    if structural is not None:
        resolution = resolve_semantics(structural_interpretation=structural)
        return build_inferred_semantic_result(physical, resolution)
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
    return build_inferred_semantic_result(physical, resolution)


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

    Frequency evidence is not collected. No current candidate rule reads
    it. Numeric-structure evidence is collected only for integer and
    floating storage. String evidence is collected only when the
    string-structure collector accepts the population. Other families
    are assessed from the basic evidence and the physical dtype alone.
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
    """Collect string evidence in dependency order, or nothing if ineligible.

    Pattern evidence and string-content evidence both receive the same
    string-structure object. String content is part of that string
    observation. No current assessor accepts it, so it is not passed on.
    """
    structure = _collect_applicable_string_structure(series, basic, physical)
    if structure is None:
        return None, None
    pattern = collect_pattern_evidence(series, structure, physical)
    collect_string_content_evidence(series, structure, physical)
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
