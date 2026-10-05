"""The findings result: policy, coverage, and the ordered findings.

A policy assigns each code one severity and one rank. Findings are
ordered by severity, then rank, then the subject's dataset order. There
is no score. Coverage counts what a pass evaluated and produced, and it
is re-derived when a result is built.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from pytics.analysis.compare.values import _require_count
from pytics.analysis.compare.values import _require_type
from pytics.analysis.findings.models import DEFERRED_FINDING_FAMILIES
from pytics.analysis.findings.models import DeferredFindingFamily
from pytics.analysis.findings.models import Finding
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.findings.models import FindingSeverity
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.models import SuppressedFinding
from pytics.analysis.findings.models import codes_for
from pytics.analysis.findings.models import subject_order

SEVERITY_ORDER: Tuple[FindingSeverity, ...] = (
    FindingSeverity.WARNING,
    FindingSeverity.NOTABLE,
    FindingSeverity.INFO,
)


@dataclass(frozen=True)
class FindingRule:
    """The policy's severity for one code."""

    code: FindingCode
    severity: FindingSeverity

    def __post_init__(self) -> None:
        _require_type(self.code, FindingCode, "code")
        _require_type(self.severity, FindingSeverity, "severity")


@dataclass(frozen=True)
class FindingsPolicy:
    """Severity and catalog order for every code.

    ``rules`` lists each code once. Its order is the code rank used after
    severity. ``identifier`` names this policy so results from different
    policies can be told apart.
    """

    identifier: str
    rules: Tuple[FindingRule, ...]

    def __post_init__(self) -> None:
        if type(self.identifier) is not str or not self.identifier.strip():
            raise ValueError("identifier must be a non-empty string")
        if not isinstance(self.rules, tuple):
            raise TypeError("rules must be a tuple")
        for rule in self.rules:
            _require_type(rule, FindingRule, "rules")
        if sorted(rule.code.value for rule in self.rules) != sorted(
            code.value for code in FindingCode
        ):
            raise ValueError("a policy names every finding code exactly once")

    def severity(self, code: FindingCode) -> FindingSeverity:
        for rule in self.rules:
            if rule.code is code:
                return rule.severity
        raise KeyError(code)

    def rank(self, code: FindingCode) -> int:
        for index, rule in enumerate(self.rules):
            if rule.code is code:
                return index
        raise KeyError(code)

    def order_key(self, finding: Finding) -> Tuple[int, int, Tuple[int, ...]]:
        """Severity, then code rank, then the subject's dataset order."""
        return (
            SEVERITY_ORDER.index(finding.severity),
            self.rank(finding.code),
            subject_order(finding.subject),
        )


@dataclass(frozen=True)
class FindingsCoverage:
    """What one findings pass evaluated and produced. Not a score.

    ``evaluated_codes`` and ``not_evaluated_codes`` partition the codes
    of the source, in policy order. A target code is not evaluated when
    the result has no target branch for it. That differs from evaluated
    with nothing found.
    """

    evaluated_codes: Tuple[FindingCode, ...]
    not_evaluated_codes: Tuple[FindingCode, ...]
    n_findings: int
    n_suppressed: int
    n_warning: int
    n_notable: int
    n_info: int
    deferred_families: Tuple[DeferredFindingFamily, ...]

    def __post_init__(self) -> None:
        for field in ("evaluated_codes", "not_evaluated_codes"):
            codes = getattr(self, field)
            if not isinstance(codes, tuple):
                raise TypeError(f"{field} must be a tuple")
            for code in codes:
                _require_type(code, FindingCode, field)
        if set(self.evaluated_codes) & set(self.not_evaluated_codes):
            raise ValueError("a code is evaluated or not evaluated, not both")
        for field in ("n_findings", "n_suppressed", "n_warning", "n_notable", "n_info"):
            _require_count(getattr(self, field), field)
        if self.n_warning + self.n_notable + self.n_info != self.n_findings:
            raise ValueError("severity counts must sum to n_findings")
        if self.deferred_families != DEFERRED_FINDING_FAMILIES:
            raise ValueError("deferred finding families are fixed for v0.1")

    @property
    def n_candidates(self) -> int:
        """Findings that a rule produced, before suppression."""
        return self.n_findings + self.n_suppressed


@dataclass(frozen=True)
class FindingsAnalysis:
    """Ordered findings over one canonical result.

    Findings follow the policy order and have distinct identities. Each
    suppressed candidate names an emitted root. Every finding's severity
    is the policy's severity for its code. The coverage is re-derived
    and must match. Nothing here keeps a DataFrame or rendered text.
    """

    source: FindingsSource
    policy: FindingsPolicy
    coverage: FindingsCoverage
    findings: Tuple[Finding, ...]
    suppressed: Tuple[SuppressedFinding, ...] = ()

    def __post_init__(self) -> None:
        _require_type(self.source, FindingsSource, "source")
        _require_type(self.policy, FindingsPolicy, "policy")
        _require_type(self.coverage, FindingsCoverage, "coverage")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if not isinstance(self.suppressed, tuple):
            raise TypeError("suppressed must be a tuple")
        evaluated = set(self.coverage.evaluated_codes)
        emitted = set()
        for finding in self.findings:
            _require_type(finding, Finding, "findings")
            _require_member(finding, self.source, self.policy, evaluated)
            identity = finding.identity
            if identity in emitted:
                raise ValueError("findings have distinct identities")
            emitted.add(identity)
        _require_policy_order(tuple(self.findings), self.policy, "findings")
        candidates = set(emitted)
        for item in self.suppressed:
            _require_type(item, SuppressedFinding, "suppressed")
            _require_member(item.finding, self.source, self.policy, evaluated)
            identity = item.finding.identity
            if identity in candidates:
                raise ValueError("a candidate is emitted or suppressed once")
            candidates.add(identity)
            if item.root not in emitted:
                raise ValueError("a suppressed finding names an emitted root")
        _require_policy_order(
            tuple(item.finding for item in self.suppressed),
            self.policy,
            "suppressed",
        )
        expected = coverage_for(
            self.source,
            self.policy,
            self.coverage.evaluated_codes,
            self.findings,
            self.suppressed,
        )
        if self.coverage != expected:
            raise ValueError("coverage does not match the findings")


def coverage_for(
    source: FindingsSource,
    policy: FindingsPolicy,
    evaluated: Tuple[FindingCode, ...],
    findings: Tuple[Finding, ...],
    suppressed: Tuple[SuppressedFinding, ...],
) -> FindingsCoverage:
    """Count one findings result. Nothing is re-evaluated."""
    available = codes_for(source)
    for code in evaluated:
        if code not in available:
            raise ValueError(f"{code.name} is not a {source.value} finding")
    ordered = tuple(sorted(available, key=policy.rank))
    counts = {severity: 0 for severity in FindingSeverity}
    for finding in findings:
        counts[finding.severity] += 1
    return FindingsCoverage(
        evaluated_codes=tuple(code for code in ordered if code in evaluated),
        not_evaluated_codes=tuple(code for code in ordered if code not in evaluated),
        n_findings=len(findings),
        n_suppressed=len(suppressed),
        n_warning=counts[FindingSeverity.WARNING],
        n_notable=counts[FindingSeverity.NOTABLE],
        n_info=counts[FindingSeverity.INFO],
        deferred_families=DEFERRED_FINDING_FAMILIES,
    )


def _require_member(
    finding: Finding,
    source: FindingsSource,
    policy: FindingsPolicy,
    evaluated: set,
) -> None:
    if finding.source is not source:
        raise ValueError(f"{finding.code.name} is not a {source.value} finding")
    if finding.code not in evaluated:
        raise ValueError(f"{finding.code.name} was not evaluated")
    if finding.severity is not policy.severity(finding.code):
        raise ValueError(f"{finding.code.name} severity must follow the policy")


def _require_policy_order(
    findings: Tuple[Finding, ...], policy: FindingsPolicy, field: str
) -> None:
    keys = [policy.order_key(finding) for finding in findings]
    for previous, current in zip(keys, keys[1:]):
        if current <= previous:
            raise ValueError(f"{field} must follow the policy order")
