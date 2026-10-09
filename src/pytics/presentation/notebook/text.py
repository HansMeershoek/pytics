"""Display text for the notebook landing view.

Strings built here are presentation. They are not fields of a finding
or of any canonical record. Column identity stays the retained label,
match key, and occurrence; a suffix such as ``[2]`` is display only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from html import escape
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import cast

from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.compare.alignment import ColumnAlignment
from pytics.analysis.compare.target_models import DiagnosticComparisonStatus
from pytics.analysis.compare.target_models import DiagnosticPredictabilityComparison
from pytics.analysis.compare.target_models import TargetAlignmentStatus
from pytics.analysis.findings.models import ColumnSubject
from pytics.analysis.findings.models import ComparedTargetPredictorSubject
from pytics.analysis.findings.models import DuplicateRowsEvidence
from pytics.analysis.findings.models import Finding
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.findings.models import FindingSeverity
from pytics.analysis.findings.models import SemanticTransitionEvidence
from pytics.analysis.findings.models import TargetPredictorSubject
from pytics.analysis.findings.result import FindingsCoverage
from pytics.analysis.target import TargetStatus
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import PredictiveTask
from pytics.results.common import FindingsView
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus

FINDINGS_ON_LANDING = 5

TYPE_LABEL = {
    SemanticType.NUMERIC: "Numeric",
    SemanticType.CATEGORICAL: "Categorical",
    SemanticType.BOOLEAN: "Boolean",
    SemanticType.TEXT: "Text",
    SemanticType.DATETIME: "Datetime",
    SemanticType.TIMEDELTA: "Timedelta",
    SemanticType.IDENTIFIER: "Identifier",
    SemanticType.CONSTANT: "Constant",
    SemanticType.EMPTY: "Empty",
}

SEVERITY_LABEL = {
    FindingSeverity.WARNING: "Warning",
    FindingSeverity.NOTABLE: "Notable",
    FindingSeverity.INFO: "Info",
}

TITLE = {
    FindingCode.EMPTY_COLUMN: "Empty column",
    FindingCode.CONSTANT_COLUMN: "Constant column",
    FindingCode.DUPLICATE_ROWS: "Exact duplicate rows",
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE: "Exact copy of the target",
    FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE: (
        "Deterministic mapping onto the target"
    ),
    FindingCode.COLUMN_REFERENCE_ONLY: "Column only in the reference",
    FindingCode.COLUMN_COMPARISON_ONLY: "Column only in the comparison",
    FindingCode.SEMANTIC_TYPE_CHANGED: "Semantic type changed",
    FindingCode.TARGET_TASK_CHANGED: "Diagnostic task changed",
    FindingCode.TARGET_CLASS_VOCABULARY_CHANGED: "Target class vocabulary changed",
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED: (
        "Exact-copy evidence changed"
    ),
}

EVALUATED = {
    FindingCode.EMPTY_COLUMN: "empty columns",
    FindingCode.CONSTANT_COLUMN: "constant columns",
    FindingCode.DUPLICATE_ROWS: "duplicate rows",
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE: "exact copies of the target",
    FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE: (
        "deterministic mappings onto the target"
    ),
    FindingCode.COLUMN_REFERENCE_ONLY: "columns only in the reference",
    FindingCode.COLUMN_COMPARISON_ONLY: "columns only in the comparison",
    FindingCode.SEMANTIC_TYPE_CHANGED: "semantic type changes",
    FindingCode.TARGET_TASK_CHANGED: "diagnostic task changes",
    FindingCode.TARGET_CLASS_VOCABULARY_CHANGED: "target class vocabulary changes",
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED: "exact-copy evidence changes",
}

TARGET_STATUS_LABEL = {
    TargetStatus.SUPPORTED: "Supported",
    TargetStatus.UNSUPPORTED: "Unsupported",
    TargetStatus.INELIGIBLE: "Ineligible",
    TargetStatus.UNRESOLVED: "Unresolved",
}

DIAGNOSTIC_STATUS_LABEL = {
    DiagnosticStatus.AVAILABLE: "Available",
    DiagnosticStatus.TARGET_TYPE_UNSUPPORTED: (
        "Not collected — target type is not supported"
    ),
    DiagnosticStatus.INSUFFICIENT_TARGET_CLASSES: (
        "Not collected — fewer than two classes"
    ),
    DiagnosticStatus.TOO_MANY_TARGET_CLASSES: "Not collected — the class bound was met",
    DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION: (
        "Not collected — the population is below the bound"
    ),
    DiagnosticStatus.INSUFFICIENT_TARGET_VARIATION: (
        "Not collected — not enough variation"
    ),
    DiagnosticStatus.VALIDATION_SPLIT_IMPOSSIBLE: (
        "Not collected — a validation split was not possible"
    ),
    DiagnosticStatus.NO_ELIGIBLE_PREDICTORS: "Not collected — no eligible predictor",
    DiagnosticStatus.NUMERICAL_FAILURE: (
        "Not collected — the numerical result was not finite"
    ),
    DiagnosticStatus.TARGET_VOCABULARY_NOT_RETAINABLE: (
        "Not collected — the category vocabulary was not retained"
    ),
}

TASK_LABEL = {
    PredictiveTask.BINARY_CLASSIFICATION: "Binary classification",
    PredictiveTask.MULTICLASS_CLASSIFICATION: "Multiclass classification",
    PredictiveTask.REGRESSION: "Regression",
}

ALIGNMENT_LABEL = {
    TargetAlignmentStatus.ALIGNED: "Aligned",
    TargetAlignmentStatus.REFERENCE_ONLY: "Reference only",
    TargetAlignmentStatus.COMPARISON_ONLY: "Comparison only",
    TargetAlignmentStatus.IDENTITY_MISMATCH: "Different columns",
    TargetAlignmentStatus.NOT_IN_EITHER: "Not in either dataset",
}

DIAGNOSTIC_COMPARISON_LABEL = {
    DiagnosticComparisonStatus.COMPARED: "Compared",
    DiagnosticComparisonStatus.NOT_COLLECTED: "Not collected",
    DiagnosticComparisonStatus.TASK_TRANSITION: "Task differs",
    DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED: "Class vocabulary differs",
    DiagnosticComparisonStatus.EVALUATION_UNAVAILABLE: "Evaluation unavailable",
}

RESOLUTION_LABEL = {
    ResolutionStatus.RESOLVED: "Resolved",
    ResolutionStatus.INSUFFICIENT_EVIDENCE: "Insufficient evidence",
    ResolutionStatus.AMBIGUOUS: "Ambiguous",
}


@dataclass(frozen=True)
class FindingLine:
    """One landing-row of a finding. Plain text, escaped later."""

    index: int
    code: str
    severity: str
    severity_label: str
    title: str
    subject: str
    detail: str
    attributes: Tuple[Tuple[str, str], ...]


def html_text(value: str) -> str:
    """Escape text that will be placed in HTML body or attributes."""
    return escape(value, quote=True)


def format_count(value: Optional[int]) -> str:
    """Group digits for display. The canonical count is unchanged.

    ``None`` is an unavailable count. It is not shown as zero.
    """
    if value is None:
        return "Unavailable"
    return f"{value:,}"


def format_percent(part: int, whole: int) -> str:
    """Format a ratio of two retained counts. Not a stored statistic."""
    if whole <= 0:
        raise ValueError("a percent needs a positive whole")
    percent = (part / whole) * 100
    if percent == 0:
        return "0%"
    if percent == 100:
        return "100%"
    if percent < 0.01:
        return "<0.01%"
    if percent >= 10:
        text = f"{percent:.1f}"
    else:
        text = f"{percent:.2f}"
    text = text.rstrip("0").rstrip(".")
    return f"{text}%"


def missing_text(n_missing: int, n_cells: int) -> str:
    """Missing cells beside the cell count when that count exists."""
    count = format_count(n_missing)
    if n_cells <= 0:
        return count
    percent = format_percent(n_missing, n_cells)
    shown = f"{count} of {format_count(n_cells)}"
    if percent == "0%":
        return shown
    return f"{shown} ({percent})"


def english_list(items: Sequence[str]) -> str:
    """Join presentation phrases. Empty, one, two, and longer lists differ."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def present_counts(items: Sequence[Tuple[str, int]]) -> str:
    """Join label/count pairs, omitting zero counts."""
    parts = [f"{label} {format_count(count)}" for label, count in items if count]
    return " · ".join(parts)


def more_findings(count: int) -> str:
    """Say how many canonical findings the landing view left off."""
    if count == 1:
        return "1 more finding follows in the same order."
    return f"{format_count(count)} more findings follow in the same order."


def severity_summary(coverage: FindingsCoverage) -> str:
    """Attention counts in policy severity order, including zeros."""
    return " · ".join(
        (
            f"{format_count(coverage.n_warning)} Warning",
            f"{format_count(coverage.n_notable)} Notable",
            f"{format_count(coverage.n_info)} Info",
        )
    )


def type_name(selected: Optional[SemanticType]) -> str:
    """Presentation name of a selected type, or unresolved."""
    if selected is None:
        return "unresolved"
    return TYPE_LABEL[selected]


def task_name(task: Optional[PredictiveTask]) -> str:
    """Presentation name of a diagnostic task, or not collected."""
    if task is None:
        return "not collected"
    return TASK_LABEL[task]


def retained_text(label: RetainedColumnLabel) -> str:
    """Readable form of one retained label. Not a new label value."""
    kind = label.kind
    value = label.value
    if kind is ColumnLabelKind.NONE:
        return "None"
    if kind is ColumnLabelKind.BOOL:
        return "True" if value else "False"
    if kind is ColumnLabelKind.INT:
        return str(value)
    if kind is ColumnLabelKind.FLOAT:
        return str(value)
    if kind is ColumnLabelKind.FLOAT_NAN:
        return "NaN"
    if kind is ColumnLabelKind.PANDAS_NA:
        return "NA"
    if kind is ColumnLabelKind.PANDAS_NAT:
        return "NaT"
    if kind is ColumnLabelKind.STRING:
        return cast(str, value)
    if kind is ColumnLabelKind.BYTES:
        return repr(value)
    if kind is ColumnLabelKind.DATE:
        return cast(date, value).isoformat()
    if kind is ColumnLabelKind.TIME:
        return cast(time, value).isoformat()
    if kind is ColumnLabelKind.DATETIME:
        return cast(datetime, value).isoformat(sep=" ")
    if kind is ColumnLabelKind.TIMEDELTA:
        return str(cast(timedelta, value))
    if kind is ColumnLabelKind.TUPLE:
        elements = cast(Tuple[RetainedColumnLabel, ...], value)
        inner = ", ".join(retained_text(item) for item in elements)
        return f"({inner})"
    if kind is ColumnLabelKind.UNSUPPORTED:
        return "Unsupported label"
    raise TypeError("unrecognized column label kind")


def retained_display(
    label: RetainedColumnLabel,
    occurrence: Optional[int],
    position: Optional[int] = None,
) -> str:
    """Label text plus occurrence, when a later duplicate would collide.

    The first occurrence has no suffix. Later occurrences use ``[n]``,
    where ``n`` is the canonical 1-based occurrence. An unsupported label
    has no occurrence, so the physical position is shown instead.
    """
    text = retained_text(label)
    if occurrence is not None and occurrence > 1:
        return f"{text} [{occurrence}]"
    if label.kind is ColumnLabelKind.UNSUPPORTED and position is not None:
        return f"{text} · position {position}"
    return text


def paired_label(alignment: ColumnAlignment) -> str:
    """Reference and comparison labels, when their display text differs."""
    reference = alignment.reference_label
    comparison = alignment.comparison_label
    occurrence = alignment.occurrence
    if reference is not None and comparison is not None:
        left = retained_display(reference, occurrence, alignment.reference_position)
        right = retained_display(comparison, occurrence, alignment.comparison_position)
        if left == right:
            return left
        return f"{left} · {right}"
    label = reference if reference is not None else comparison
    if label is None:
        return ""
    position = alignment.reference_position
    if position is None:
        position = alignment.comparison_position
    return retained_display(label, occurrence, position)


def subject_text(finding: Finding) -> str:
    """Who the finding is about, in display text."""
    subject = finding.subject
    if subject is None:
        return "Dataset"
    if isinstance(subject, ColumnSubject):
        return retained_display(subject.label, subject.occurrence, subject.position)
    if isinstance(subject, TargetPredictorSubject):
        predictor = retained_display(
            subject.predictor.label,
            subject.predictor.occurrence,
            subject.predictor.position,
        )
        target = retained_display(
            subject.target.label,
            subject.target.occurrence,
            subject.target.position,
        )
        return f"{predictor} · target {target}"
    if isinstance(subject, ColumnAlignment):
        return paired_label(subject)
    if isinstance(subject, ComparedTargetPredictorSubject):
        predictor = paired_label(subject.predictor)
        target = paired_label(subject.target)
        return f"{predictor} · target {target}"
    raise TypeError("finding subject is not a known subject")


def finding_detail(finding: Finding) -> str:
    """A short factual gloss. Empty when the title and subject are enough."""
    code = finding.code
    evidence = finding.evidence
    if code is FindingCode.DUPLICATE_ROWS:
        rows = cast(DuplicateRowsEvidence, evidence)
        return (
            f"{format_count(rows.n_duplicate_groups)} groups, "
            f"{format_count(rows.n_rows_in_duplicate_groups)} rows in those groups"
        )
    if code is FindingCode.SEMANTIC_TYPE_CHANGED:
        changed = cast(SemanticTransitionEvidence, evidence)
        reference = type_name(changed.semantic.reference.selected_type)
        comparison = type_name(changed.semantic.comparison.selected_type)
        transitions = format_count(changed.n_relationship_transitions)
        return (
            f"Reference {reference} · comparison {comparison} · "
            f"relationship transitions {transitions}"
        )
    if code is FindingCode.TARGET_TASK_CHANGED:
        diagnostic = cast(DiagnosticPredictabilityComparison, evidence)
        return (
            f"Reference {task_name(diagnostic.reference_task)} · "
            f"comparison {task_name(diagnostic.comparison_task)}"
        )
    return ""


def _attributes(finding: Finding, index: int) -> Tuple[Tuple[str, str], ...]:
    """Canonical indexes for later navigation. Not display labels."""
    attributes = [
        ("data-finding-index", str(index)),
        ("data-finding-code", finding.code.value),
    ]
    subject = finding.subject
    if isinstance(subject, ColumnSubject):
        attributes.append(("data-column-position", str(subject.position)))
        attributes.extend(_occurrence_attribute(subject.occurrence))
    elif isinstance(subject, TargetPredictorSubject):
        attributes.append(("data-column-position", str(subject.predictor.position)))
        attributes.extend(_occurrence_attribute(subject.predictor.occurrence))
    elif isinstance(subject, ColumnAlignment):
        attributes.extend(_alignment_attributes(subject))
    elif isinstance(subject, ComparedTargetPredictorSubject):
        attributes.extend(_alignment_attributes(subject.predictor))
    return tuple(attributes)


def _occurrence_attribute(occurrence: Optional[int]) -> Tuple[Tuple[str, str], ...]:
    if occurrence is None:
        return ()
    return (("data-occurrence", str(occurrence)),)


def _alignment_attributes(
    alignment: ColumnAlignment,
) -> Tuple[Tuple[str, str], ...]:
    attributes = []
    if alignment.reference_position is not None:
        attributes.append(
            ("data-reference-position", str(alignment.reference_position))
        )
    if alignment.comparison_position is not None:
        attributes.append(
            ("data-comparison-position", str(alignment.comparison_position))
        )
    attributes.extend(_occurrence_attribute(alignment.occurrence))
    return tuple(attributes)


def finding_line(index: int, finding: Finding) -> FindingLine:
    """One finding in canonical order. ``index`` is that order's position."""
    return FindingLine(
        index=index,
        code=finding.code.value,
        severity=finding.severity.value,
        severity_label=SEVERITY_LABEL[finding.severity],
        title=TITLE[finding.code],
        subject=subject_text(finding),
        detail=finding_detail(finding),
        attributes=_attributes(finding, index),
    )


def landing_findings(
    findings: FindingsView,
) -> Tuple[Tuple[FindingLine, ...], int]:
    """The first landing findings and how many remain after them."""
    records = findings.records
    shown = records[:FINDINGS_ON_LANDING]
    lines = tuple(finding_line(index, finding) for index, finding in enumerate(shown))
    return lines, len(records) - len(lines)


def evaluated_sentence(coverage: FindingsCoverage) -> str:
    """Which finding codes this result evaluated, in policy order."""
    phrases = [EVALUATED[code] for code in coverage.evaluated_codes]
    return f"Evaluated: {english_list(phrases)}."


def deferred_finding_sentence(coverage: FindingsCoverage) -> str:
    """Conditions with no v0.1 finding rule. Not a claim they are absent."""
    phrases = [family.value.replace("_", " ") for family in coverage.deferred_families]
    return f"No finding rule in this version for {english_list(phrases)}."
