"""Identifier candidate assessment from observations already collected.

Identifier is a semantic role: values primarily function to distinguish,
reference, or key entities or records, rather than measure a quantity or
represent a classification vocabulary. It is not a primary-key definition.
Uniqueness is not that role. Zero missingness is not that role. A duplicate
does not by itself remove the role.

This assessor does not collect observations and does not classify a
physical dtype. It does not read the Series, the column name, or a regular
step. It does not resolve the candidate, assign High, Medium, or Low
confidence, or enter the Empty, Constant, and physical-type precedence
chain.

The positive rules are deliberately narrow. Empty and Constant are not
supported, because those readings already have stronger precedence; they
are not recorded as contradictions. Otherwise the candidate is supported
only when one explicit signal covers every non-missing value: UUID syntax,
or one supported fixed-width ASCII hexadecimal token width. A compact UUID
may record both of those facts. That is still one disposition, not a
stronger score. A partial ratio, a mixture of different patterns, an IP
address pattern, and every numeric sequence stay unsupported. No Identifier
contradiction is emitted.

The full-population requirement is the conservative initial candidate rule
for the current evidence foundation. It is not a universal threshold.
"""

from __future__ import annotations

from typing import Optional
from typing import Tuple

from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.frequency_evidence import FrequencyEvidence
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
_STRING_FAMILIES = frozenset(
    {
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    }
)
_HEX_WIDTHS = (32, 40, 64, 128)


def assess_identifier_candidate(
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
    frequency: Optional[FrequencyEvidence] = None,
    numeric_structure: Optional[NumericStructureEvidence] = None,
    string_structure: Optional[StringStructureEvidence] = None,
    pattern: Optional[PatternEvidence] = None,
) -> CandidateAssessment:
    """Assess Identifier from one consistent evidence bundle.

    ``basic`` is the universal evidence. ``physical`` is the dtype already
    classified for that column. Frequency, numeric-structure, string-structure,
    and pattern evidence are optional. When one is supplied, it must be the
    object collected with this ``basic`` evidence, and pattern evidence must
    be the object collected with the supplied string-structure evidence.
    Counts that merely match are not the same bundle.

    The return value is always an Identifier candidate assessment. It is
    not a semantic interpretation.
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
        return _not_supported()
    support = _full_population_support(basic, pattern)
    if support:
        return CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.SUPPORTED,
            supporting_evidence=support,
        )
    return _not_supported()


def _not_supported() -> CandidateAssessment:
    return CandidateAssessment(
        semantic_type=SemanticType.IDENTIFIER,
        disposition=CandidateDisposition.NOT_SUPPORTED,
    )


def _full_population_support(
    basic: BasicColumnEvidence,
    pattern: Optional[PatternEvidence],
) -> Tuple[SemanticEvidence, ...]:
    """Return syntax facts that cover every non-missing value.

    A pattern count equal to ``n_non_missing`` is the full population.
    That is the same fact as an observed ratio of 1.0, compared on the
    integers so a partial count cannot round to that ratio. A ratio below
    the full population is not support. Different patterns are not added
    together. IP syntax is not an Identifier signal.
    """
    if pattern is None:
        return ()
    population = basic.n_non_missing
    statements = []
    if pattern.uuid_count == population:
        statements.append(
            SemanticEvidence(
                f"All {population} non-missing values match the UUID syntax."
            )
        )
    for width in _HEX_WIDTHS:
        if getattr(pattern, f"hex_{width}_count") == population:
            statements.append(
                SemanticEvidence(
                    f"All {population} non-missing values are "
                    f"{width}-character ASCII hexadecimal tokens."
                )
            )
    return tuple(statements)


def _require_bundle(
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
    frequency: Optional[FrequencyEvidence],
    numeric_structure: Optional[NumericStructureEvidence],
    string_structure: Optional[StringStructureEvidence],
    pattern: Optional[PatternEvidence],
) -> None:
    """Reject a bundle that mixes columns or inapplicable evidence."""
    if not isinstance(basic, BasicColumnEvidence):
        raise TypeError("basic must be BasicColumnEvidence")
    if not isinstance(physical, PhysicalDtype):
        raise TypeError("physical must be a PhysicalDtype")
    if frequency is not None:
        if not isinstance(frequency, FrequencyEvidence):
            raise TypeError("frequency must be FrequencyEvidence")
        _require_same_basic(frequency.basic, basic, "frequency evidence")
    if numeric_structure is not None:
        if not isinstance(numeric_structure, NumericStructureEvidence):
            raise TypeError("numeric_structure must be NumericStructureEvidence")
        _require_same_basic(
            numeric_structure.basic,
            basic,
            "numeric structure evidence",
        )
        if physical.family not in _NUMERIC_FAMILIES:
            raise ValueError(
                "numeric structure evidence does not apply to this physical dtype"
            )
    if string_structure is not None:
        if not isinstance(string_structure, StringStructureEvidence):
            raise TypeError("string_structure must be StringStructureEvidence")
        _require_same_basic(
            string_structure.basic,
            basic,
            "string structure evidence",
        )
        if physical.family not in _STRING_FAMILIES:
            raise ValueError(
                "string structure evidence does not apply to this physical dtype"
            )
    if pattern is not None:
        if not isinstance(pattern, PatternEvidence):
            raise TypeError("pattern must be PatternEvidence")
        if string_structure is None or pattern.string_structure is not string_structure:
            raise ValueError(
                "pattern evidence was not collected from the supplied "
                "StringStructureEvidence"
            )


def _require_same_basic(
    evidence_basic: BasicColumnEvidence,
    basic: BasicColumnEvidence,
    label: str,
) -> None:
    if evidence_basic is not basic:
        raise ValueError(
            f"{label} was not collected from the supplied BasicColumnEvidence"
        )
