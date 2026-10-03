"""Numeric, Categorical, and Text candidate assessments.

These assessors consume observations already collected. They do not
collect observations, classify a physical dtype, or read a Series or a
column name. They do not resolve a candidate, assign High, Medium, or
Low confidence, or enter the Empty, Constant, and physical-type
precedence chain.

A candidate is supported only by an explicit positive rule. The
assessors do not force one reading to exclude another. Absence of
support is not contradiction. No candidate in this module emits a
contradiction.

Numeric means values primarily function as quantities on which magnitude
and arithmetic relationships are analytically meaningful. Non-empty,
non-constant physical integer or floating storage is that positive
evidence. Numeric-structure observations may be supplied with the
bundle. They are context, and support does not depend on a distribution
of those facts. Complex storage is outside this rule. Numeric-looking
strings are not parsed.

Categorical means values primarily function as a classification
vocabulary. Non-empty, non-constant physical categorical storage is that
positive evidence. Ordered categorical metadata stays on the physical
dtype. Repetition and low cardinality are not a vocabulary rule.

Text means values primarily function as textual content. Current
observations do not contain an approved positive rule for that reading,
so the Text candidate stays unsupported.
"""

from __future__ import annotations

from typing import Optional

from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.frequency_evidence import FrequencyEvidence
from pytics.semantics.identifier_candidate import _require_bundle
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.numeric_structure_evidence import NumericStructureEvidence
from pytics.semantics.pattern_evidence import PatternEvidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.string_structure_evidence import StringStructureEvidence

_NUMERIC_FAMILIES = frozenset(
    {
        PhysicalDtypeFamily.INTEGER,
        PhysicalDtypeFamily.FLOATING,
    }
)


def assess_numeric_candidate(
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
    frequency: Optional[FrequencyEvidence] = None,
    numeric_structure: Optional[NumericStructureEvidence] = None,
    string_structure: Optional[StringStructureEvidence] = None,
    pattern: Optional[PatternEvidence] = None,
) -> CandidateAssessment:
    """Assess Numeric from one consistent evidence bundle.

    The return value is always a Numeric candidate assessment. It is not
    a semantic interpretation. Empty and Constant stay unsupported
    because those readings already have stronger precedence.
    """
    _require_bundle(
        basic,
        physical,
        frequency,
        numeric_structure,
        string_structure,
        pattern,
    )
    if basic.is_empty or basic.is_constant:
        return _not_supported(SemanticType.NUMERIC)
    if physical.family in _NUMERIC_FAMILIES:
        statement = (
            f"Physical dtype family {physical.family.name} "
            "supports a Numeric reading."
        )
        return CandidateAssessment(
            semantic_type=SemanticType.NUMERIC,
            disposition=CandidateDisposition.SUPPORTED,
            supporting_evidence=(SemanticEvidence(statement),),
        )
    return _not_supported(SemanticType.NUMERIC)


def assess_categorical_candidate(
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
    frequency: Optional[FrequencyEvidence] = None,
    numeric_structure: Optional[NumericStructureEvidence] = None,
    string_structure: Optional[StringStructureEvidence] = None,
    pattern: Optional[PatternEvidence] = None,
) -> CandidateAssessment:
    """Assess Categorical from one consistent evidence bundle.

    The return value is always a Categorical candidate assessment. It is
    not a semantic interpretation. Physical categorical storage is the
    positive rule. Empty and Constant stay unsupported.
    """
    _require_bundle(
        basic,
        physical,
        frequency,
        numeric_structure,
        string_structure,
        pattern,
    )
    if basic.is_empty or basic.is_constant:
        return _not_supported(SemanticType.CATEGORICAL)
    if physical.family is PhysicalDtypeFamily.CATEGORICAL:
        return CandidateAssessment(
            semantic_type=SemanticType.CATEGORICAL,
            disposition=CandidateDisposition.SUPPORTED,
            supporting_evidence=(
                SemanticEvidence(
                    "Physical categorical storage supports a Categorical reading."
                ),
            ),
        )
    return _not_supported(SemanticType.CATEGORICAL)


def assess_text_candidate(
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
    frequency: Optional[FrequencyEvidence] = None,
    numeric_structure: Optional[NumericStructureEvidence] = None,
    string_structure: Optional[StringStructureEvidence] = None,
    pattern: Optional[PatternEvidence] = None,
) -> CandidateAssessment:
    """Assess Text from one consistent evidence bundle.

    The return value is always a Text candidate assessment. It is not a
    semantic interpretation. Empty and Constant stay unsupported. No
    other current observation is an approved positive Text rule, so the
    candidate stays unsupported there as well.
    """
    _require_bundle(
        basic,
        physical,
        frequency,
        numeric_structure,
        string_structure,
        pattern,
    )
    if basic.is_empty or basic.is_constant:
        return _not_supported(SemanticType.TEXT)
    # No approved positive rule uses the observations collected so far.
    return _not_supported(SemanticType.TEXT)


def _not_supported(semantic_type: SemanticType) -> CandidateAssessment:
    return CandidateAssessment(
        semantic_type=semantic_type,
        disposition=CandidateDisposition.NOT_SUPPORTED,
    )
