"""Typed semantic interpretation values.

These objects can carry a semantic reading. Nothing in this module infers
one. Subtype is an optional label because the subtype taxonomy is not
decided, and ordinal storage is not decided. Ordinal is not a member of
``SemanticType``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple

from pytics.semantics.physical import PhysicalDtype


class SemanticType(Enum):
    """Minimum semantic-type vocabulary.

    ``BOOLEAN`` is the Boolean/Binary family. It does not split strict
    boolean from binary. ``TEXT`` is the Text/String family. Ordinal is
    omitted on purpose: it is not in this minimum list, and its storage is
    unresolved.
    """

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TEXT = "text"
    DATETIME = "datetime"
    TIMEDELTA = "timedelta"
    IDENTIFIER = "identifier"
    CONSTANT = "constant"
    EMPTY = "empty"


class Confidence(Enum):
    """User-facing confidence. There is no numeric score."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InferenceSource(Enum):
    """Where a semantic interpretation came from.

    ``PHYSICAL_DTYPE`` means the reading is directly supported by the
    physical or source dtype. ``USER_CONFIGURED`` means the user configured
    it explicitly. ``INFERRED`` means it was inferred from evidence.
    """

    INFERRED = "inferred"
    PHYSICAL_DTYPE = "physical_dtype"
    USER_CONFIGURED = "user_configured"


@dataclass(frozen=True)
class SemanticEvidence:
    """One inspectable statement supporting a semantic reading.

    The statement is prose such as ``physical dtype is boolean``. This
    slice does not generate those statements.
    """

    statement: str

    def __post_init__(self) -> None:
        if not isinstance(self.statement, str) or not self.statement.strip():
            raise ValueError("evidence statement must be a non-empty string")


@dataclass(frozen=True)
class SemanticAlternative:
    """A relevant alternative reading. It does not repeat column evidence."""

    semantic_type: SemanticType
    subtype: Optional[str] = None
    confidence: Optional[Confidence] = None

    def __post_init__(self) -> None:
        _require(self.semantic_type, SemanticType, "semantic_type")
        object.__setattr__(self, "subtype", _optional_subtype(self.subtype))
        if self.confidence is not None:
            _require_confidence(self.confidence, "confidence")


@dataclass(frozen=True)
class SemanticInterpretation:
    """Selected semantic reading for one column.

    ``subtype`` is an open label, not a closed taxonomy. ``evidence`` and
    ``alternatives`` are stored as tuples. This object does not decide
    which reading is correct.
    """

    semantic_type: SemanticType
    confidence: Confidence
    source: InferenceSource
    physical: PhysicalDtype
    subtype: Optional[str] = None
    evidence: Tuple[SemanticEvidence, ...] = ()
    alternatives: Tuple[SemanticAlternative, ...] = ()

    def __post_init__(self) -> None:
        _require(self.semantic_type, SemanticType, "semantic_type")
        _require_confidence(self.confidence, "confidence")
        _require(self.source, InferenceSource, "source")
        _require(self.physical, PhysicalDtype, "physical")
        object.__setattr__(self, "subtype", _optional_subtype(self.subtype))
        object.__setattr__(self, "evidence", _as_tuple(self.evidence, SemanticEvidence, "evidence"))
        object.__setattr__(
            self,
            "alternatives",
            _as_tuple(self.alternatives, SemanticAlternative, "alternatives"),
        )


def _require(value: Any, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _require_confidence(value: Any, field: str) -> None:
    if not isinstance(value, Confidence):
        raise TypeError(
            f"{field} must be Confidence.HIGH, Confidence.MEDIUM, or Confidence.LOW"
        )


def _optional_subtype(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("subtype must be a string or None")
    if not value.strip():
        raise ValueError("subtype must be a non-empty string when provided")
    return value


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
