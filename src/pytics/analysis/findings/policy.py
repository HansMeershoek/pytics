"""The v0.1 findings policy and the assembly of a findings result.

Severity is set per code. No severity comes from a p-value, an effect
size, or a count crossing a cutoff. Codes that need such a cutoff are
not in this catalog.

Within one severity the rank follows this table. Mechanical leakage
evidence comes first. Target-level comparability comes before column
schema, because it qualifies a whole branch of the comparison. Column
conditions follow, and the dataset-level duplicate count is last.
"""

from __future__ import annotations

from typing import Iterable
from typing import Tuple

from pytics.analysis.findings.models import Evidence
from pytics.analysis.findings.models import Finding
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.findings.models import FindingSeverity
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.models import Subject
from pytics.analysis.findings.models import SuppressedFinding
from pytics.analysis.findings.result import FindingRule
from pytics.analysis.findings.result import FindingsAnalysis
from pytics.analysis.findings.result import FindingsPolicy
from pytics.analysis.findings.result import coverage_for

FINDINGS_POLICY = FindingsPolicy(
    identifier="pytics.findings/0.1",
    rules=(
        FindingRule(
            FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
            FindingSeverity.WARNING,
        ),
        FindingRule(
            FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE,
            FindingSeverity.WARNING,
        ),
        FindingRule(
            FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED,
            FindingSeverity.WARNING,
        ),
        FindingRule(FindingCode.TARGET_TASK_CHANGED, FindingSeverity.NOTABLE),
        FindingRule(
            FindingCode.TARGET_CLASS_VOCABULARY_CHANGED,
            FindingSeverity.NOTABLE,
        ),
        FindingRule(FindingCode.SEMANTIC_TYPE_CHANGED, FindingSeverity.NOTABLE),
        FindingRule(FindingCode.COLUMN_REFERENCE_ONLY, FindingSeverity.NOTABLE),
        FindingRule(FindingCode.COLUMN_COMPARISON_ONLY, FindingSeverity.NOTABLE),
        FindingRule(FindingCode.EMPTY_COLUMN, FindingSeverity.NOTABLE),
        FindingRule(FindingCode.CONSTANT_COLUMN, FindingSeverity.NOTABLE),
        FindingRule(FindingCode.DUPLICATE_ROWS, FindingSeverity.INFO),
    ),
)


def finding(code: FindingCode, subject: Subject, evidence: Evidence) -> Finding:
    """A finding with the policy's severity for its code."""
    return Finding(
        code=code,
        severity=FINDINGS_POLICY.severity(code),
        subject=subject,
        evidence=evidence,
    )


def assemble_findings(
    source: FindingsSource,
    evaluated: Iterable[FindingCode],
    findings: Iterable[Finding],
    suppressed: Iterable[SuppressedFinding] = (),
) -> FindingsAnalysis:
    """Order the findings and suppressed candidates, then count them."""
    policy = FINDINGS_POLICY
    ordered = tuple(sorted(findings, key=policy.order_key))
    owned = tuple(
        sorted(suppressed, key=lambda item: policy.order_key(item.finding))
    )
    codes: Tuple[FindingCode, ...] = tuple(evaluated)
    return FindingsAnalysis(
        source=source,
        policy=policy,
        coverage=coverage_for(source, policy, codes, ordered, owned),
        findings=ordered,
        suppressed=owned,
    )
