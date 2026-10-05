"""Findings over one finished dataset comparison.

Rules read the column alignment, the semantic snapshots, the
relationship-drift pair statuses, and the target-drift branches. No rule
reads a source value, a drift distance, an effect change, or a p-value.

A column on one side only and a matched column whose selected semantic
type differs are column findings. Relationship family and eligibility
transitions are counted on the semantic-change finding of each column
they involve, because those transitions follow from the change.

Target codes are evaluated only when a requested target is aligned,
because only then does the comparison hold the diagnostic and leakage
branches they read. A semantic-type change of the target, or of a
predictor, owns the task, class-vocabulary, and exact-duplicate
transition candidates that involve that column. A repeated-mapping
transition is not a finding: the comparison keeps the two statuses and
not the singleton counts a mapping finding needs.
"""

from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.models import DatasetComparison
from pytics.analysis.compare.relationship_models import RelationshipPairStatus
from pytics.analysis.compare.target_models import DiagnosticComparisonStatus
from pytics.analysis.compare.target_models import TargetAlignmentStatus
from pytics.analysis.compare.target_models import TargetDriftAnalysis
from pytics.analysis.findings.models import ComparedTargetPredictorSubject
from pytics.analysis.findings.models import Finding
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.findings.models import FindingIdentity
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.models import SemanticTransitionEvidence
from pytics.analysis.findings.models import SuppressedFinding
from pytics.analysis.findings.models import SuppressionRule
from pytics.analysis.findings.policy import assemble_findings
from pytics.analysis.findings.policy import finding
from pytics.analysis.findings.result import FindingsAnalysis
from pytics.analysis.target_leakage import ExactDuplicateStatus

_ONE_SIDED_CODES = {
    ColumnMatchStatus.REFERENCE_ONLY: FindingCode.COLUMN_REFERENCE_ONLY,
    ColumnMatchStatus.COMPARISON_ONLY: FindingCode.COLUMN_COMPARISON_ONLY,
}
_DIAGNOSTIC_CODES = {
    DiagnosticComparisonStatus.TASK_TRANSITION: FindingCode.TARGET_TASK_CHANGED,
    DiagnosticComparisonStatus.CLASS_VOCABULARY_CHANGED: (
        FindingCode.TARGET_CLASS_VOCABULARY_CHANGED
    ),
}
_TARGET_CODES = (
    FindingCode.TARGET_TASK_CHANGED,
    FindingCode.TARGET_CLASS_VOCABULARY_CHANGED,
    FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED,
)
_TRANSITION_STATUSES = frozenset(
    {
        RelationshipPairStatus.FAMILY_TRANSITION,
        RelationshipPairStatus.ELIGIBILITY_TRANSITION,
    }
)


def collect_compare_findings(comparison: DatasetComparison) -> FindingsAnalysis:
    """Select findings from one dataset comparison.

    The argument must already be a ``DatasetComparison``. Neither
    DataFrame is accepted.
    """
    if not isinstance(comparison, DatasetComparison):
        raise TypeError("collect_compare_findings expects a DatasetComparison")
    found, changed = _schema_findings(comparison)
    evaluated = [
        FindingCode.COLUMN_REFERENCE_ONLY,
        FindingCode.COLUMN_COMPARISON_ONLY,
        FindingCode.SEMANTIC_TYPE_CHANGED,
    ]
    suppressed: List[SuppressedFinding] = []
    target = comparison.target
    if target is not None and target.alignment.status is TargetAlignmentStatus.ALIGNED:
        evaluated.extend(_TARGET_CODES)
        for candidate, root in _target_candidates(comparison, target, changed):
            if root is None:
                found.append(candidate)
                continue
            suppressed.append(
                SuppressedFinding(
                    finding=candidate,
                    root=root,
                    rule=SuppressionRule.SEMANTIC_CHANGE_OWNS_TARGET_COMPARISON,
                )
            )
    return assemble_findings(FindingsSource.COMPARE, evaluated, found, suppressed)


def _schema_findings(
    comparison: DatasetComparison,
) -> Tuple[List[Finding], Dict[int, FindingIdentity]]:
    """One-sided and semantic-change findings.

    Semantic-change identities are also returned by reference position,
    so target candidates can name them as their root.
    """
    transitions = _relationship_transitions(comparison)
    found: List[Finding] = []
    changed: Dict[int, FindingIdentity] = {}
    for column in comparison.columns:
        alignment = column.alignment
        code = _ONE_SIDED_CODES.get(alignment.status)
        if code is not None:
            found.append(finding(code, alignment, column.semantic))
            continue
        if column.semantic.selected_type_changed is not True:
            continue
        position = alignment.reference_position
        evidence = SemanticTransitionEvidence(
            semantic=column.semantic,
            n_relationship_transitions=transitions.get(position, 0),  # type: ignore[arg-type]
        )
        changed_finding = finding(FindingCode.SEMANTIC_TYPE_CHANGED, alignment, evidence)
        found.append(changed_finding)
        changed[position] = changed_finding.identity  # type: ignore[index]
    return found, changed


def _relationship_transitions(comparison: DatasetComparison) -> Dict[int, int]:
    """Family or eligibility transitions per reference column position."""
    counts: Dict[int, int] = {}
    for record in comparison.relationships:
        if record.status not in _TRANSITION_STATUSES:
            continue
        for column in (record.alignment.first, record.alignment.second):
            position = column.reference_position
            counts[position] = counts.get(position, 0) + 1
    return counts


def _target_candidates(
    comparison: DatasetComparison,
    target: TargetDriftAnalysis,
    changed: Dict[int, FindingIdentity],
) -> Tuple[Tuple[Finding, Optional[FindingIdentity]], ...]:
    """Target candidates of an aligned target, each with its semantic root.

    The root is the target's semantic change, else the predictor's, else
    ``None``.
    """
    index = target.distribution.column_index  # type: ignore[union-attr]
    alignment = comparison.columns[index].alignment
    target_root = changed.get(alignment.reference_position)  # type: ignore[arg-type]
    candidates = []
    diagnostic = target.diagnostic
    code = _DIAGNOSTIC_CODES.get(diagnostic.status)  # type: ignore[union-attr]
    if code is not None:
        candidates.append((finding(code, alignment, diagnostic), target_root))  # type: ignore[arg-type]
    matched = {
        column.alignment.reference_position: column.alignment
        for column in comparison.columns
        if column.alignment.status is ColumnMatchStatus.MATCHED
    }
    promoted = ExactDuplicateStatus.EXACT_DUPLICATE
    for transition in target.leakage.transitions:  # type: ignore[union-attr]
        if (transition.reference_exact is promoted) is (
            transition.comparison_exact is promoted
        ):
            continue
        subject = ComparedTargetPredictorSubject(
            target=alignment,
            predictor=matched[transition.reference_position],
        )
        candidate = finding(
            FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED,
            subject,
            transition,
        )
        candidates.append(
            (candidate, target_root or changed.get(transition.reference_position))
        )
    return tuple(candidates)
