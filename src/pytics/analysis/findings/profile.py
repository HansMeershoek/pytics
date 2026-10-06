"""Findings over one finished dataset analysis.

Each rule reads a retained result and returns the findings it supports.
No rule reads a DataFrame, a relationship statistic, or a p-value.

``EMPTY_COLUMN`` and ``CONSTANT_COLUMN`` read the selected semantic type.
Semantic precedence already makes them exclusive, so an all-missing
column is Empty and never also Constant. ``DUPLICATE_ROWS`` reads the
exact duplicate groups and keeps their counts. Target rules run only
when the analysis holds leakage evidence for an explicit target. A
mapping finding needs every observed predictor value to repeat, so a
nearly unique column that repeats only on duplicate rows is not
selected. An exact copy of a classification target is also such a
mapping, so the mapping candidate for that predictor is suppressed.
"""

from __future__ import annotations

from typing import List
from typing import Tuple

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column_label import identify_column_labels
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.findings.models import ColumnSubject
from pytics.analysis.findings.models import DuplicateRowsEvidence
from pytics.analysis.findings.models import Finding
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.models import SuppressedFinding
from pytics.analysis.findings.models import SuppressionRule
from pytics.analysis.findings.models import TargetPredictorSubject
from pytics.analysis.findings.models import is_complete_repeated_mapping
from pytics.analysis.findings.policy import assemble_findings
from pytics.analysis.findings.policy import finding
from pytics.analysis.findings.result import FindingsAnalysis
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import TargetLeakageAnalysis
from pytics.semantics.interpretation import SemanticType

_STRUCTURAL_CODES = {
    SemanticType.EMPTY: FindingCode.EMPTY_COLUMN,
    SemanticType.CONSTANT: FindingCode.CONSTANT_COLUMN,
}


def collect_profile_findings(analysis: DatasetAnalysis) -> FindingsAnalysis:
    """Select findings from one dataset analysis.

    The argument must already be a ``DatasetAnalysis``. A DataFrame is
    not accepted. Target codes are evaluated only when the analysis has
    leakage evidence, which exists exactly when a target was requested.
    """
    if not isinstance(analysis, DatasetAnalysis):
        raise TypeError("collect_profile_findings expects a DatasetAnalysis")
    subjects = column_subjects(analysis.columns)
    evaluated = [
        FindingCode.EMPTY_COLUMN,
        FindingCode.CONSTANT_COLUMN,
        FindingCode.DUPLICATE_ROWS,
    ]
    found: List[Finding] = list(_structural_columns(analysis.columns, subjects))
    found.extend(_duplicate_rows(analysis))
    suppressed: Tuple[SuppressedFinding, ...] = ()
    if analysis.target_leakage is not None:
        evaluated.extend(
            (
                FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
                FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE,
            )
        )
        target_found, suppressed = _target_leakage(analysis.target_leakage, subjects)
        found.extend(target_found)
    return assemble_findings(FindingsSource.PROFILE, evaluated, found, suppressed)


def column_subjects(columns: Tuple[ColumnAnalysis, ...]) -> Tuple[ColumnSubject, ...]:
    """One subject per physical column, with the shared label identity."""
    identities = identify_column_labels(tuple(column.label for column in columns))
    return tuple(
        ColumnSubject(
            position=column.position,
            label=identity.retained,
            occurrence=identity.occurrence,
        )
        for column, identity in zip(columns, identities)
    )


def _structural_columns(
    columns: Tuple[ColumnAnalysis, ...],
    subjects: Tuple[ColumnSubject, ...],
) -> Tuple[Finding, ...]:
    found = []
    for column, subject in zip(columns, subjects):
        code = _STRUCTURAL_CODES.get(column.inferred.selected_type)  # type: ignore[arg-type]
        if code is not None:
            found.append(finding(code, subject, column.evidence.basic))
    return tuple(found)


def _duplicate_rows(analysis: DatasetAnalysis) -> Tuple[Finding, ...]:
    duplicates = analysis.duplicate_analysis
    n_groups = duplicates.n_duplicate_groups
    n_in_groups = duplicates.n_rows_in_duplicate_groups
    if n_groups is None or n_in_groups is None or n_groups == 0:
        return ()
    evidence = DuplicateRowsEvidence(
        n_rows=analysis.n_rows,
        n_duplicate_groups=n_groups,
        n_rows_in_duplicate_groups=n_in_groups,
    )
    return (finding(FindingCode.DUPLICATE_ROWS, None, evidence),)


def _target_leakage(
    leakage: TargetLeakageAnalysis,
    subjects: Tuple[ColumnSubject, ...],
) -> Tuple[Tuple[Finding, ...], Tuple[SuppressedFinding, ...]]:
    target = subjects[leakage.target_position]
    found = []
    suppressed = []
    for predictor in leakage.predictors:
        subject = TargetPredictorSubject(
            target=target,
            predictor=subjects[predictor.position],
        )
        exact = None
        if predictor.exact_duplicate.status is ExactDuplicateStatus.EXACT_DUPLICATE:
            exact = finding(
                FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
                subject,
                predictor.exact_duplicate,
            )
            found.append(exact)
        if not is_complete_repeated_mapping(predictor.deterministic_mapping):
            continue
        mapping = finding(
            FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE,
            subject,
            predictor.deterministic_mapping,
        )
        if exact is None:
            found.append(mapping)
            continue
        suppressed.append(
            SuppressedFinding(
                finding=mapping,
                root=exact.identity,
                rule=SuppressionRule.EXACT_DUPLICATE_OWNS_MAPPING,
            )
        )
    return tuple(found), tuple(suppressed)
