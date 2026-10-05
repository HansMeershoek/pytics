"""Notebook landing view of one comparison result.

The view reads retained comparison counts. It does not compare the
datasets again and it does not rank drift.
"""

from __future__ import annotations

from typing import List
from typing import Sequence
from typing import Tuple

from pytics.analysis.compare.models import ComparisonCoverage
from pytics.analysis.compare.overview import DatasetOverviewComparison
from pytics.analysis.compare.relationship_models import RelationshipDriftCoverage
from pytics.analysis.compare.target_models import TargetDriftAlignment
from pytics.analysis.compare.values import CountComparison
from pytics.presentation.notebook.document import facts
from pytics.presentation.notebook.document import findings_block
from pytics.presentation.notebook.document import notes
from pytics.presentation.notebook.document import section
from pytics.presentation.notebook.document import shell
from pytics.presentation.notebook.document import sides
from pytics.presentation.notebook.document import subhead
from pytics.presentation.notebook.text import ALIGNMENT_LABEL
from pytics.presentation.notebook.text import DIAGNOSTIC_COMPARISON_LABEL
from pytics.presentation.notebook.text import TYPE_LABEL
from pytics.presentation.notebook.text import deferred_finding_sentence
from pytics.presentation.notebook.text import english_list
from pytics.presentation.notebook.text import evaluated_sentence
from pytics.presentation.notebook.text import format_count
from pytics.presentation.notebook.text import landing_findings
from pytics.presentation.notebook.text import more_findings
from pytics.presentation.notebook.text import paired_label
from pytics.presentation.notebook.text import present_counts
from pytics.presentation.notebook.text import severity_summary
from pytics.presentation.notebook.text import type_name
from pytics.results.common import TargetRequest
from pytics.results.comparison import ComparisonResult
from pytics.semantics.interpretation import SemanticType


def render_comparison(result: ComparisonResult) -> str:
    """Return the notebook HTML for one comparison. Does not modify it."""
    if type(result) is not ComparisonResult:
        raise TypeError("notebook comparison rendering expects a ComparisonResult")
    parts = [
        _dataset(result.overview),
        _findings(result),
        _schema(result),
        _distribution(result.coverage.columns),
        _relationships(result.coverage.relationships),
    ]
    if result.target.request is TargetRequest.REQUESTED:
        parts.append(_target(result))
    parts.append(_coverage(result))
    return shell(
        "comparison",
        "Dataset Comparison",
        result.metadata.findings_policy,
        "".join(parts),
    )


def _findings(result: ComparisonResult) -> str:
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


def _dataset(overview: DatasetOverviewComparison) -> str:
    rows = [
        _count_row("Rows", overview.n_rows),
        _count_row("Columns", overview.n_columns),
        _count_row("Cells", overview.n_cells),
        _count_row("Missing cells", overview.n_missing_cells),
        _count_row("Exact duplicate groups", overview.n_duplicate_groups),
        _count_row("Empty columns", overview.empty_column_count),
        _count_row("Constant columns", overview.constant_column_count),
    ]
    table = sides(("Measure", "Reference", "Comparison"), rows)
    return section("dataset", "Dataset", table)


def _count_row(label: str, counts: CountComparison) -> Tuple[str, str, str]:
    return (label, format_count(counts.reference), format_count(counts.comparison))


def _schema(result: ComparisonResult) -> str:
    coverage = result.coverage.columns
    rows = [
        (
            "Columns",
            _join(
                (
                    f"{format_count(coverage.n_matched_columns)} matched",
                    f"{format_count(coverage.n_reference_only_columns)} reference only",
                    f"{format_count(coverage.n_comparison_only_columns)} comparison only",
                    f"{format_count(coverage.n_reordered_matched_columns)} reordered",
                )
            ),
        ),
        (
            "Selected type",
            _join(
                (
                    f"{format_count(coverage.n_same_selected_type_columns)} same",
                    f"{format_count(coverage.n_selected_type_changed_columns)} changed",
                    f"{format_count(coverage.n_both_unresolved_columns)} both unresolved",
                )
            ),
        ),
    ]
    body = facts(rows) + _semantic_types(result.overview)
    return section("schema", "Schema", body)


def _semantic_types(overview: DatasetOverviewComparison) -> str:
    counts = overview.semantic_type_counts
    if not counts:
        return subhead("No selected semantic type on either side.")
    rows = [
        (
            TYPE_LABEL[item.semantic_type],
            format_count(item.reference_count),
            format_count(item.comparison_count),
        )
        for item in counts
    ]
    return subhead("Selected types") + sides(
        ("Semantic type", "Reference", "Comparison"),
        rows,
    )


def _distribution(coverage: ComparisonCoverage) -> str:
    rows = [
        (
            "Records",
            _join(
                (
                    f"Numeric {format_count(coverage.n_numeric_distribution_drift)}",
                    f"categorical {format_count(coverage.n_categorical_distribution_drift)}",
                    f"boolean {format_count(coverage.n_boolean_distribution_drift)}",
                )
            ),
        ),
        (
            "Tests",
            (
                f"{format_count(coverage.n_distribution_tests)} available · "
                f"{format_count(coverage.n_distribution_tests_unavailable)} unavailable · "
                f"{format_count(coverage.n_distribution_not_eligible)} not eligible"
            ),
        ),
    ]
    extra = present_counts(
        (
            ("Source values not supplied", coverage.n_distribution_source_not_supplied),
            (
                "Primary effects unavailable",
                coverage.n_distribution_primary_effects_unavailable,
            ),
            (
                "Wasserstein distances unavailable",
                coverage.n_wasserstein_distances_unavailable,
            ),
        )
    )
    if extra:
        rows.append(("Not collected", extra))
    return section("distribution", "Distribution", facts(rows))


def _relationships(coverage: RelationshipDriftCoverage) -> str:
    rows = [
        (
            "Pairs",
            _join(
                (
                    f"{format_count(coverage.n_aligned_pairs)} aligned",
                    f"{format_count(coverage.n_same_family)} same family",
                    f"{format_count(coverage.n_family_transition)} family transition",
                    f"{format_count(coverage.n_unimplemented)} unimplemented",
                    (
                        f"{format_count(coverage.n_eligibility_transition)} "
                        "eligibility transition"
                    ),
                )
            ),
        ),
        (
            "Effect change",
            (
                f"{format_count(coverage.n_effect_change_available)} available · "
                f"{format_count(coverage.n_effect_change_unavailable)} unavailable"
            ),
        ),
    ]
    return section("relationships", "Relationships", facts(rows))


def _target(result: ComparisonResult) -> str:
    analysis = result.target.analysis
    if analysis is None:
        raise ValueError("a requested target has no target drift")
    alignment = analysis.alignment
    rows: List[Tuple[str, str]] = []
    label = paired_label(alignment)
    if label:
        rows.append(("Column", label))
    rows.append(("Alignment", ALIGNMENT_LABEL[alignment.status]))
    types = _target_types(alignment)
    if types:
        rows.append(("Selected type", types))
    diagnostic = analysis.diagnostic
    if diagnostic is not None:
        rows.append(("Diagnostic", DIAGNOSTIC_COMPARISON_LABEL[diagnostic.status]))
    return section("target", "Target", facts(rows))


def _target_types(alignment: TargetDriftAlignment) -> str:
    reference = alignment.reference_selected_type
    comparison = alignment.comparison_selected_type
    if reference == comparison:
        if reference is None:
            return ""
        return TYPE_LABEL[reference]
    return f"Reference {type_name(reference)} · comparison {type_name(comparison)}"


def _coverage(result: ComparisonResult) -> str:
    families = result.coverage.columns.deferred_families
    phrases = [family.value.replace("_", " ") for family in families]
    footer = [
        deferred_finding_sentence(result.findings.coverage),
        f"Not compared: {english_list(phrases)}.",
        "Columns, relationship changes, findings, and coverage are on this result.",
        (
            f"Pytics {result.metadata.pytics_version} · "
            f"{result.metadata.findings_policy}"
        ),
    ]
    if result.target.request is TargetRequest.NOT_REQUESTED:
        footer.insert(0, "Target: not requested.")
    return section("coverage", "Analysis coverage", notes(footer))


def _join(parts: Sequence[str]) -> str:
    return " · ".join(parts)
