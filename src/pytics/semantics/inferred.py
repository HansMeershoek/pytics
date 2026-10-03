"""Record the inferred semantic state after resolution.

The result keeps the physical dtype that was already observed and the
resolution that was already produced. It does not collect observations,
assess candidates, or choose a reading again.

When resolution selected a structural interpretation, that same object
is the inferred interpretation. Its confidence, source, and physical
dtype stay as they are. The supplied physical dtype must match it.

When resolution selected a semantic type from exactly one supported
candidate, the inferred state keeps that selection and does not build
a ``SemanticInterpretation``. Candidate assessments do not justify
High, Medium, or Low confidence, and this module does not invent one.

Insufficient evidence and ambiguity are complete inferred states. They
have no interpretation and no selected semantic type. They are not
errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional

from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.resolution import SemanticResolution


@dataclass(frozen=True)
class InferredSemanticResult:
    """Inferred semantic state for one column after resolution.

    ``physical`` is the observed storage supplied by the caller. It is
    not inferred from a semantic type. ``resolution`` is the resolution
    result already produced. Status, the selected type, candidate
    assessments, and a structural interpretation stay on that object.

    ``interpretation`` reads the structural interpretation when
    resolution has one. It is ``None`` for a candidate-derived
    selection, for insufficient evidence, and for ambiguity.
    ``selected_type`` reads the resolution's selected type. Neither
    value is stored a second time.
    """

    physical: PhysicalDtype
    resolution: SemanticResolution

    def __post_init__(self) -> None:
        _require(self.physical, PhysicalDtype, "physical")
        _require(self.resolution, SemanticResolution, "resolution")
        structural = self.resolution.structural_interpretation
        if structural is not None and self.physical != structural.physical:
            supplied = _describe_physical(self.physical)
            expected = _describe_physical(structural.physical)
            raise ValueError(
                "physical dtype must match the structural interpretation: "
                f"supplied ({supplied}) != structural ({expected})"
            )

    @property
    def interpretation(self) -> Optional[SemanticInterpretation]:
        """Structural interpretation already held by the resolution."""
        return self.resolution.structural_interpretation

    @property
    def selected_type(self) -> Optional[SemanticType]:
        """Semantic type selected by the resolution, if it selected one."""
        return self.resolution.selected_type


def build_inferred_semantic_result(
    physical: PhysicalDtype,
    resolution: SemanticResolution,
) -> InferredSemanticResult:
    """Combine an observed physical dtype with a finished resolution.

    Both arguments are facts already known. A physical dtype that
    disagrees with a structural interpretation is invalid. This
    function does not collect observations or assess candidates.
    """
    return InferredSemanticResult(physical=physical, resolution=resolution)


def _describe_physical(physical: PhysicalDtype) -> str:
    return (
        f"{physical.family.name}, {physical.dtype_name!r}, "
        f"categorical_ordered={physical.categorical_ordered!r}"
    )


def _require(value: Any, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")
