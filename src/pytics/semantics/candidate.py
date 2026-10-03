"""Candidate assessments for one possible semantic reading.

An assessment records whether already collected observations support or
contradict one semantic candidate. It is not the reading selected for the
column. Resolution, final confidence, and material alternatives are later
stages. This module does not resolve anything.

There is no score. Supporting and contradicting statements stay separate.
A fact that does not bear on the candidate is omitted. Absence of support
is not contradiction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Tuple

from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType


class CandidateDisposition(Enum):
    """Whether current rules treat one candidate as plausible.

    ``SUPPORTED`` means those rules found enough positive evidence to keep
    the reading available for later resolution. It does not mean the
    candidate wins. ``NOT_SUPPORTED`` means that positive evidence is
    absent or insufficient. It is not a contradiction. ``CONTRADICTED``
    means an explicit fact is incompatible with the candidate under a
    stated rule.
    """

    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    CONTRADICTED = "contradicted"


@dataclass(frozen=True)
class CandidateAssessment:
    """Evidence for and against one semantic candidate.

    ``semantic_type`` names the candidate. ``supporting_evidence`` and
    ``contradicting_evidence`` are tuples of the same statement value used
    on a semantic interpretation. They are not a second evidence type, and
    they are not a score. Final confidence is not stored here.

    ``SUPPORTED`` requires at least one supporting statement.
    ``CONTRADICTED`` requires at least one contradicting statement. Both
    sequences may be non-empty together. ``NOT_SUPPORTED`` does not require
    either sequence.
    """

    semantic_type: SemanticType
    disposition: CandidateDisposition
    supporting_evidence: Tuple[SemanticEvidence, ...] = ()
    contradicting_evidence: Tuple[SemanticEvidence, ...] = ()

    def __post_init__(self) -> None:
        _require(self.semantic_type, SemanticType, "semantic_type")
        _require(self.disposition, CandidateDisposition, "disposition")
        support = _as_tuple(
            self.supporting_evidence,
            SemanticEvidence,
            "supporting_evidence",
        )
        contradiction = _as_tuple(
            self.contradicting_evidence,
            SemanticEvidence,
            "contradicting_evidence",
        )
        if self.disposition is CandidateDisposition.SUPPORTED and not support:
            raise ValueError("SUPPORTED requires supporting evidence")
        if self.disposition is CandidateDisposition.CONTRADICTED and not contradiction:
            raise ValueError("CONTRADICTED requires contradicting evidence")
        object.__setattr__(self, "supporting_evidence", support)
        object.__setattr__(self, "contradicting_evidence", contradiction)


def _require(value: Any, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _as_tuple(value: Any, item_type: type, field: str) -> Tuple[Any, ...]:
    if isinstance(value, (str, bytes, dict)) or isinstance(value, item_type):
        raise TypeError(f"{field} must be a sequence of {item_type.__name__}")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise TypeError(f"{field} must be a sequence of {item_type.__name__}") from exc
    for item in items:
        if not isinstance(item, item_type):
            raise TypeError(f"{field} must contain only {item_type.__name__} values")
    return items
