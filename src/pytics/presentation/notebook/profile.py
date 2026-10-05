"""Notebook landing view of one profile result.

Counts in this module add up retained fields for display. They do not
classify a column again, and they do not calculate a statistic.
"""

from __future__ import annotations

from typing import List
from typing import Tuple

from pytics.analysis.relationships.models import RelationshipAnalysis
from pytics.presentation.notebook.document import facts
from pytics.presentation.notebook.document import findings_block
from pytics.presentation.notebook.document import metrics
from pytics.presentation.notebook.document import notes
from pytics.presentation.notebook.document import section
from pytics.presentation.notebook.document import shell
from pytics.presentation.notebook.text import DIAGNOSTIC_STATUS_LABEL
from pytics.presentation.notebook.text import RESOLUTION_LABEL
from pytics.presentation.notebook.text import TARGET_STATUS_LABEL
from pytics.presentation.notebook.text import TASK_LABEL
from pytics.presentation.notebook.text import TYPE_LABEL
from pytics.presentation.notebook.text import deferred_finding_sentence
from pytics.presentation.notebook.text import evaluated_sentence
from pytics.presentation.notebook.text import format_count
from pytics.presentation.notebook.text import landing_findings
from pytics.presentation.notebook.text import missing_text
from pytics.presentation.notebook.text import more_findings
from pytics.presentation.notebook.text import present_counts
from pytics.presentation.notebook.text import retained_display
from pytics.presentation.notebook.text import severity_summary
from pytics.results.common import TargetRequest
from pytics.results.profile import ProfileResult
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


def render_profile(result: ProfileResult) -> str:
    """Return the notebook HTML for one profile. Does not modify it."""
    if type(result) is not ProfileResult:
        raise TypeError("notebook profile rendering expects a ProfileResult")
    parts = [
        metrics(
            (
                ("Rows", format_count(result.n_rows)),
                ("Columns", format_count(result.n_columns)),
                ("Cells", format_count(result.n_cells)),
            )
        ),
        _findings(result),
        _structure(result),
    ]
    if result.target.request is TargetRequest.REQUESTED:
        parts.append(_target(result))
    parts.append(_coverage(result))
    return shell(
        "profile",
        "Data Profile",
        result.metadata.findings_policy,
        "".join(parts),
    )


def _findings(result: ProfileResult) -> str:
    lines, remainder = landing_findings(result.findings)
    coverage = result.findings.coverage
    footer: List[str] = []
    if remainder:
        footer.append(more_findings(remainder))
    footer.append(evaluated_sentence(coverage))
    if result.target.request is TargetRequest.NOT_REQUESTED:
        footer.append("Target findings were not evaluated.")
    if coverage.n_findings == 0:
        summary = "No findings."
    else:
        summary = severity_summary(coverage)
    return section("findings", "Findings", findings_block(summary, lines, footer))


def _structure(result: ProfileResult) -> str:
    counts = {semantic_type: 0 for semantic_type in SemanticType}
    insufficient = 0
    ambiguous = 0
    n_missing = 0
    columns_with_missing = 0
    for variable in result.variables:
        basic = variable.record.evidence.basic
        n_missing += basic.n_missing
        if basic.n_missing:
            columns_with_missing += 1
        status = variable.resolution_status
        if status is ResolutionStatus.INSUFFICIENT_EVIDENCE:
            insufficient += 1
        elif status is ResolutionStatus.AMBIGUOUS:
            ambiguous += 1
        selected = variable.selected_type
        if selected is not None:
            counts[selected] += 1
    type_counts = [
        (semantic_type, counts[semantic_type]) for semantic_type in SemanticType
    ]
    rows: List[Tuple[str, str]] = [
        ("Semantic types", _semantic_types(type_counts)),
    ]
    unresolved = present_counts(
        (
            (
                RESOLUTION_LABEL[ResolutionStatus.INSUFFICIENT_EVIDENCE],
                insufficient,
            ),
            (RESOLUTION_LABEL[ResolutionStatus.AMBIGUOUS], ambiguous),
        )
    )
    if unresolved:
        rows.append(("Unresolved", unresolved))
    rows.append(("Missing cells", missing_text(n_missing, result.n_cells)))
    rows.append(("Missing columns", format_count(columns_with_missing)))
    groups = result.duplicates.n_duplicate_groups
    rows.append(("Exact duplicate groups", format_count(groups)))
    if groups:
        rows.append(
            (
                "Excess duplicate rows",
                format_count(result.duplicates.n_excess_duplicate_rows),
            )
        )
    return section("structure", "Structure", facts(rows))


def _semantic_types(counts: List[Tuple[SemanticType, int]]) -> str:
    text = present_counts(
        [(TYPE_LABEL[semantic_type], count) for semantic_type, count in counts]
    )
    if text:
        return text
    return "No selected semantic type"


def _target(result: ProfileResult) -> str:
    analysis = result.target.analysis
    diagnostic = result.target.diagnostic
    if analysis is None or diagnostic is None:
        raise ValueError("a requested target has no target records")
    variable = result.variables[analysis.position]
    rows = [
        (
            "Column",
            retained_display(
                variable.identity.retained,
                variable.identity.occurrence,
                variable.position,
            ),
        ),
        ("Status", TARGET_STATUS_LABEL[analysis.status]),
    ]
    if analysis.selected_type is not None:
        rows.append(("Selected type", TYPE_LABEL[analysis.selected_type]))
    rows.append(("Diagnostic", DIAGNOSTIC_STATUS_LABEL[diagnostic.status]))
    if diagnostic.task is not None:
        rows.append(("Task", TASK_LABEL[diagnostic.task]))
    return section("target", "Target", facts(rows))


def _coverage(result: ProfileResult) -> str:
    relationships = result.coverage.relationships
    anomalies = result.coverage.anomalies
    lines = [
        ("Relationships", _relationships(relationships)),
        (
            "Numeric anomalies",
            _anomalies(
                anomalies.n_columns,
                anomalies.n_eligible,
                anomalies.n_analyzed,
                anomalies.n_unavailable,
            ),
        ),
    ]
    body = facts(lines)
    footer = [
        deferred_finding_sentence(result.findings.coverage),
        "Variables, relationships, findings, and coverage are on this result.",
        (
            f"Pytics {result.metadata.pytics_version} · "
            f"{result.metadata.findings_policy}"
        ),
    ]
    if result.target.request is TargetRequest.NOT_REQUESTED:
        footer.insert(0, "Target: not requested.")
    return section("coverage", "Analysis coverage", body + notes(footer))


def _relationships(analysis: RelationshipAnalysis) -> str:
    calculated = analysis.n_analyzed_pairs
    unimplemented = analysis.n_unimplemented_family_pairs
    ineligible = analysis.n_ineligible_pairs
    return (
        f"{format_count(calculated)} calculated · "
        f"{format_count(unimplemented)} unimplemented · "
        f"{format_count(ineligible)} ineligible"
    )


def _anomalies(
    n_columns: int,
    n_eligible: int,
    n_analyzed: int,
    n_unavailable: int,
) -> str:
    if n_columns == 0:
        return "No column"
    if n_eligible == 0:
        return "No eligible numeric column"
    return (
        f"{format_count(n_analyzed)} analyzed · "
        f"{format_count(n_unavailable)} unavailable"
    )
