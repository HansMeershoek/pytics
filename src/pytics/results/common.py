"""Shared public-result vocabulary.

A result is a read-only view of one finished canonical analysis plus the
findings pass over that analysis. It does not render, serialize, or
score. Profile and comparison use the same finding view, the same
metadata fields, and the same label-lookup failure. They do not share a
single object.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator
from typing import Optional
from typing import Tuple
from typing import TypeVar

from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.column_label import column_label_match_key
from pytics.analysis.column_label import retained_column_label_match_key
from pytics.analysis.findings.result import FindingsAnalysis
from pytics.analysis.findings.result import FindingsCoverage
from pytics.analysis.findings.result import FindingsPolicy
from pytics.analysis.findings.models import Finding
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.models import SuppressedFinding


class ResultKind(Enum):
    """Which public result this is.

    The value is the machine-readable code. It is not a sentence.
    """

    PROFILE = "profile"
    COMPARISON = "comparison"


class TargetRequest(Enum):
    """Whether the caller named a target.

    ``NOT_REQUESTED`` means the result has no target branch.
    ``REQUESTED`` means a target branch exists. The branch's own status
    says whether that target is supported, unavailable, or unaligned.
    Request and failure are different codes.
    """

    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"


class AmbiguousColumnLabel(LookupError):
    """A label matches more than one column.

    ``positions`` locates those columns. For a profile they are physical
    positions. For a comparison they are indexes in the alignment
    sequence. Lookup does not choose one of them.
    """

    def __init__(self, label: object, positions: Tuple[int, ...]) -> None:
        self.label = label
        self.positions = positions
        super().__init__(f"label matches {len(positions)} columns at {positions}")


@dataclass(frozen=True, repr=False)
class ResultMetadata:
    """Provenance that belongs on the result itself.

    There is no generation timestamp and no random identifier. Both would
    make two equivalent analyses compare unequal. Package version and
    findings-policy identifier are recorded because a later reader needs
    them to know which definitions produced the result. They are not a
    serialized file header. An artifact schema version, when one exists,
    is a property of that file, not of this object.
    """

    pytics_version: str
    kind: ResultKind
    target_request: TargetRequest
    findings_policy: str

    def __post_init__(self) -> None:
        if type(self.pytics_version) is not str or not self.pytics_version.strip():
            raise ValueError("pytics_version must be a non-empty string")
        if not isinstance(self.kind, ResultKind):
            raise TypeError("kind must be a ResultKind")
        if not isinstance(self.target_request, TargetRequest):
            raise TypeError("target_request must be a TargetRequest")
        if type(self.findings_policy) is not str or not self.findings_policy.strip():
            raise ValueError("findings_policy must be a non-empty string")

    def __repr__(self) -> str:
        return (
            f"ResultMetadata(kind={self.kind.value}, "
            f"target={self.target_request.value}, "
            f"policy={self.findings_policy!r})"
        )


@dataclass(frozen=True, eq=False, repr=False)
class FindingsView:
    """Ordered findings, their policy, and their coverage.

    The finding objects are the canonical findings. This view does not
    copy them and does not sort them again. Suppressed candidates stay
    visible so a missing finding can be told from a finding a rule owned.
    """

    _findings: FindingsAnalysis

    def __post_init__(self) -> None:
        if not isinstance(self._findings, FindingsAnalysis):
            raise TypeError("findings must be a FindingsAnalysis")

    def __iter__(self) -> Iterator[Finding]:
        return iter(self._findings.findings)

    def __len__(self) -> int:
        return len(self._findings.findings)

    def __getitem__(self, index: object) -> Finding:
        return _index(self._findings.findings, index, "findings")

    @property
    def records(self) -> Tuple[Finding, ...]:
        """Findings in policy order. The canonical tuple, not a copy."""
        return self._findings.findings

    @property
    def suppressed(self) -> Tuple[SuppressedFinding, ...]:
        """Candidates a root finding owns, in policy order."""
        return self._findings.suppressed

    @property
    def coverage(self) -> FindingsCoverage:
        """What this findings pass evaluated. Not a score."""
        return self._findings.coverage

    @property
    def policy(self) -> FindingsPolicy:
        """The severity and order table that produced this result."""
        return self._findings.policy

    @property
    def source(self) -> FindingsSource:
        """Whether these findings were read from a profile or a comparison."""
        return self._findings.source

    def __repr__(self) -> str:
        return f"FindingsView(n={len(self._findings.findings)})"


def pytics_version() -> str:
    """Return the installed Pytics package version."""
    from pytics import __version__

    return __version__


def retained_label_matches(
    retained: Optional[RetainedColumnLabel],
    label: object,
) -> bool:
    """Whether a retained label is the same label as ``label``.

    Comparison uses the match key. An unsupported label has no key and
    does not match, including against another unsupported label.
    """
    if retained is None or retained.kind is ColumnLabelKind.UNSUPPORTED:
        return False
    key = column_label_match_key(label)
    if key is None:
        return False
    return retained_column_label_match_key(retained) == key


_T = TypeVar("_T")


def _index(items: Tuple[_T, ...], index: object, kind: str) -> _T:
    """Return one item by int position.

    ``True`` is not a position. A label is not a position either. Negative
    positions count from the end, as they do for a tuple.
    """
    if type(index) is not int:
        raise TypeError(f"{kind} is indexed by an int position, not by a label")
    return items[index]
