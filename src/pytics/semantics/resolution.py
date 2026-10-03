"""Resolve a semantic reading from structural and candidate facts.

Resolution chooses among readings that are already justified. It does not
manufacture a reading when those facts are insufficient, and it does not
choose between supported candidates when no reviewed rule says how.

A structural interpretation for Empty, Constant, Boolean, Datetime, or
Timedelta is kept as the resolved reading. Candidate assessments do not
replace it. The confidence already stored on that interpretation stays
as it is.

With no structural interpretation, exactly one supported candidate
selects that semantic type. No supported candidate yields insufficient
evidence. More than one supported candidate yields an ambiguous result
with no selected type. A contradicted candidate is not selected and does
not block a different supported candidate.

This module does not build the final confidence-bearing interpretation
for a candidate-derived selection. ``SemanticInterpretation`` requires a
confidence and a physical dtype that candidate assessments do not carry.
That later step is separate.

Candidate assessments are stored in semantic-type name order. The order
makes the result independent of input order. It does not choose a reading.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Optional
from typing import Sequence
from typing import Tuple

from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType


class ResolutionStatus(Enum):
    """Whether resolution selected one reading.

    ``RESOLVED`` means one justified reading was selected.
    ``INSUFFICIENT_EVIDENCE`` means no candidate is supported and no
    structural reading was supplied. ``AMBIGUOUS`` means more than one
    candidate is supported and no reviewed rule selects between them.
    These are resolution states, not semantic types.
    """

    RESOLVED = "resolved"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    AMBIGUOUS = "ambiguous"


_STRUCTURAL_TYPES = frozenset(
    {
        SemanticType.EMPTY,
        SemanticType.CONSTANT,
        SemanticType.BOOLEAN,
        SemanticType.DATETIME,
        SemanticType.TIMEDELTA,
    }
)


@dataclass(frozen=True)
class SemanticResolution:
    """Immutable result of resolving one column's semantic reading.

    ``selected_type`` is set only when ``status`` is ``RESOLVED``.
    ``structural_interpretation`` is set only when that resolved reading
    is a structural interpretation already produced elsewhere. A
    candidate-derived selection records the semantic type and leaves
    ``structural_interpretation`` unset. It does not carry confidence.

    ``candidates`` retains the assessments that were considered. It does
    not copy the observations those assessments already hold. Stored
    order is semantic-type name order.
    """

    status: ResolutionStatus
    reason: str
    candidates: Tuple[CandidateAssessment, ...] = ()
    selected_type: Optional[SemanticType] = None
    structural_interpretation: Optional[SemanticInterpretation] = None

    def __post_init__(self) -> None:
        _require(self.status, ResolutionStatus, "status")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        object.__setattr__(self, "candidates", _normalize_candidates(self.candidates))
        if self.selected_type is not None:
            _require(self.selected_type, SemanticType, "selected_type")
        if self.structural_interpretation is not None:
            _require(
                self.structural_interpretation,
                SemanticInterpretation,
                "structural_interpretation",
            )
            _require_structural_type(self.structural_interpretation)
        _require_coherent_state(
            self.status,
            self.selected_type,
            self.structural_interpretation,
            self.candidates,
        )


def resolve_semantics(
    structural_interpretation: Optional[SemanticInterpretation] = None,
    candidates: Sequence[CandidateAssessment] = (),
) -> SemanticResolution:
    """Resolve structural and candidate facts already produced.

    ``structural_interpretation`` is accepted only for Empty, Constant,
    Boolean, Datetime, or Timedelta. ``candidates`` must not contain two
    assessments for the same semantic type. Input order does not change
    the result. This function does not collect observations.
    """
    if structural_interpretation is not None and not isinstance(
        structural_interpretation,
        SemanticInterpretation,
    ):
        raise TypeError(
            "structural_interpretation must be a SemanticInterpretation or None"
        )
    assessed = _normalize_candidates(candidates)
    if structural_interpretation is not None:
        _require_structural_type(structural_interpretation)
        selected = structural_interpretation.semantic_type
        return SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            reason=(f"Structural interpretation {_label(selected)} takes precedence."),
            candidates=assessed,
            selected_type=selected,
            structural_interpretation=structural_interpretation,
        )
    supported = _supported_types(assessed)
    if len(supported) == 1:
        selected = supported[0]
        return SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            reason=f"Exactly one candidate is supported: {_label(selected)}.",
            candidates=assessed,
            selected_type=selected,
        )
    if not supported:
        return SemanticResolution(
            status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
            reason="No candidate is supported.",
            candidates=assessed,
        )
    listed = ", ".join(_label(semantic_type) for semantic_type in supported)
    return SemanticResolution(
        status=ResolutionStatus.AMBIGUOUS,
        reason=f"Multiple candidates are supported: {listed}.",
        candidates=assessed,
    )


def _require_coherent_state(
    status: ResolutionStatus,
    selected_type: Optional[SemanticType],
    structural_interpretation: Optional[SemanticInterpretation],
    candidates: Tuple[CandidateAssessment, ...],
) -> None:
    supported = _supported_types(candidates)
    if status is ResolutionStatus.RESOLVED:
        if selected_type is None:
            raise ValueError("RESOLVED requires a selected semantic type")
        if structural_interpretation is not None:
            if selected_type is not structural_interpretation.semantic_type:
                raise ValueError(
                    "selected semantic type must match the structural interpretation"
                )
            return
        if supported != (selected_type,):
            raise ValueError(
                "RESOLVED from candidates requires exactly one supported "
                "candidate of the selected semantic type"
            )
        return
    if selected_type is not None:
        raise ValueError("only a resolved result has a selected semantic type")
    if structural_interpretation is not None:
        raise ValueError("only a resolved result has a structural interpretation")
    if status is ResolutionStatus.INSUFFICIENT_EVIDENCE:
        if supported:
            raise ValueError(
                "INSUFFICIENT_EVIDENCE cannot include a supported candidate"
            )
        return
    if len(supported) < 2:
        raise ValueError("AMBIGUOUS requires at least two supported candidates")


def _require_structural_type(reading: SemanticInterpretation) -> None:
    semantic_type = reading.semantic_type
    if semantic_type not in _STRUCTURAL_TYPES:
        raise ValueError(
            "structural interpretation must be Empty, Constant, Boolean, "
            f"Datetime, or Timedelta, not {semantic_type.name}"
        )


def _supported_types(
    candidates: Tuple[CandidateAssessment, ...],
) -> Tuple[SemanticType, ...]:
    return tuple(
        item.semantic_type
        for item in candidates
        if item.disposition is CandidateDisposition.SUPPORTED
    )


def _label(semantic_type: SemanticType) -> str:
    return semantic_type.name.title()


def _normalize_candidates(value: Any) -> Tuple[CandidateAssessment, ...]:
    items = _as_tuple(value, CandidateAssessment, "candidates")
    seen = set()
    for item in items:
        if item.semantic_type in seen:
            name = item.semantic_type.name
            raise ValueError(f"duplicate candidate semantic type: {name}")
        seen.add(item.semantic_type)
    return tuple(sorted(items, key=lambda item: item.semantic_type.name))


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
