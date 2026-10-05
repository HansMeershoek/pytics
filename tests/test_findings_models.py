"""TSK-040: the findings model, policy, identity, and result invariants."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pandas as pd
import pytest

import pytics.analysis.findings as findings_package
from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.column_label import retain_column_label
from pytics.analysis.compare import ColumnAlignment
from pytics.analysis.compare import ColumnMatchStatus
from pytics.analysis.compare import DiagnosticComparisonStatus
from pytics.analysis.compare import DiagnosticPredictabilityComparison
from pytics.analysis.compare import SemanticComparison
from pytics.analysis.compare import SemanticSnapshot
from pytics.analysis.compare.target_models import PredictorLeakageTransition
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.findings import DEFERRED_FINDING_FAMILIES
from pytics.analysis.findings import FINDINGS_POLICY
from pytics.analysis.findings import ColumnSubject
from pytics.analysis.findings import ComparedTargetPredictorSubject
from pytics.analysis.findings import DuplicateRowsEvidence
from pytics.analysis.findings import Finding
from pytics.analysis.findings import FindingCode
from pytics.analysis.findings import FindingIdentity
from pytics.analysis.findings import FindingRule
from pytics.analysis.findings import FindingScope
from pytics.analysis.findings import FindingSeverity
from pytics.analysis.findings import FindingsAnalysis
from pytics.analysis.findings import FindingsCoverage
from pytics.analysis.findings import FindingsPolicy
from pytics.analysis.findings import FindingsSource
from pytics.analysis.findings import SemanticTransitionEvidence
from pytics.analysis.findings import SuppressedFinding
from pytics.analysis.findings import SuppressionRule
from pytics.analysis.findings import TargetPredictorSubject
from pytics.analysis.findings import collect_profile_findings
from pytics.analysis.findings.models import subject_key
from pytics.analysis.findings.models import subject_order
from pytics.analysis.findings.result import coverage_for
from pytics.analysis.target_diagnostic import PredictiveTask
from pytics.analysis.target_leakage import ExactDuplicateEvidence
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import MappingEvidence
from pytics.analysis.target_leakage import MappingStatus
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus

_PACKAGE = Path(findings_package.__file__).parent

_EMPTY = BasicColumnEvidence(
    n_total=3, n_missing=3, n_non_missing=0, n_unique_non_missing=0
)
_CONSTANT = BasicColumnEvidence(
    n_total=3, n_missing=0, n_non_missing=3, n_unique_non_missing=1
)
_VARIED = BasicColumnEvidence(
    n_total=3, n_missing=0, n_non_missing=3, n_unique_non_missing=3
)


def _column(position: int, label: object = "a", occurrence: int = 1) -> ColumnSubject:
    return ColumnSubject(
        position=position,
        label=retain_column_label(label),
        occurrence=occurrence,
    )


def _alignment(
    status: ColumnMatchStatus = ColumnMatchStatus.MATCHED,
    label: object = "a",
    reference_position: int = 0,
    comparison_position: int = 0,
) -> ColumnAlignment:
    retained = retain_column_label(label)
    return ColumnAlignment(
        status=status,
        reference_label=(
            None if status is ColumnMatchStatus.COMPARISON_ONLY else retained
        ),
        comparison_label=(
            None if status is ColumnMatchStatus.REFERENCE_ONLY else retained
        ),
        occurrence=1,
        reference_position=(
            None if status is ColumnMatchStatus.COMPARISON_ONLY else reference_position
        ),
        comparison_position=(
            None if status is ColumnMatchStatus.REFERENCE_ONLY else comparison_position
        ),
    )


def _snapshot(selected: SemanticType = SemanticType.NUMERIC) -> SemanticSnapshot:
    return SemanticSnapshot(
        resolution_status=ResolutionStatus.RESOLVED,
        selected_type=selected,
        confidence=None,
    )


def _exact(status: ExactDuplicateStatus) -> ExactDuplicateEvidence:
    unequal = 1 if status is ExactDuplicateStatus.NOT_EQUAL else 0
    return ExactDuplicateEvidence(
        status=status,
        n_applicable_rows=4,
        n_joint_rows=4,
        n_predictor_unobserved=0,
        n_equal_rows=4 - unequal,
        n_unequal_rows=unequal,
    )


def _mapping(n_singleton_groups: int) -> MappingEvidence:
    return MappingEvidence(
        status=MappingStatus.DETERMINISTIC_REPEATED,
        n_applicable_rows=4 + n_singleton_groups,
        n_joint_rows=4 + n_singleton_groups,
        n_predictor_unobserved=0,
        n_distinct_groups=2 + n_singleton_groups,
        n_repeated_groups=2,
        n_singleton_groups=n_singleton_groups,
        n_conflicting_groups=0,
        n_consistent_repeated_groups=2,
        n_rows_in_repeated_groups=4,
        n_rows_in_conflicting_groups=0,
        n_target_classes=2,
    )


def _finding(code: FindingCode, subject, evidence) -> Finding:
    return Finding(
        code=code,
        severity=FINDINGS_POLICY.severity(code),
        subject=subject,
        evidence=evidence,
    )


def _profile(findings, suppressed=(), evaluated=None) -> FindingsAnalysis:
    codes = tuple(FindingCode) if evaluated is None else evaluated
    codes = tuple(
        code
        for code in codes
        if code
        in (
            FindingCode.EMPTY_COLUMN,
            FindingCode.CONSTANT_COLUMN,
            FindingCode.DUPLICATE_ROWS,
            FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
            FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE,
        )
    )
    return FindingsAnalysis(
        source=FindingsSource.PROFILE,
        policy=FINDINGS_POLICY,
        coverage=coverage_for(
            FindingsSource.PROFILE, FINDINGS_POLICY, codes, findings, suppressed
        ),
        findings=findings,
        suppressed=suppressed,
    )


def test_policy_names_every_code_once_with_the_v01_severities() -> None:
    assert FINDINGS_POLICY.identifier == "pytics.findings/0.1"
    assert sorted(rule.code.value for rule in FINDINGS_POLICY.rules) == sorted(
        code.value for code in FindingCode
    )
    expected = {
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE: FindingSeverity.WARNING,
        FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE: FindingSeverity.WARNING,
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED: FindingSeverity.WARNING,
        FindingCode.TARGET_TASK_CHANGED: FindingSeverity.NOTABLE,
        FindingCode.TARGET_CLASS_VOCABULARY_CHANGED: FindingSeverity.NOTABLE,
        FindingCode.SEMANTIC_TYPE_CHANGED: FindingSeverity.NOTABLE,
        FindingCode.COLUMN_REFERENCE_ONLY: FindingSeverity.NOTABLE,
        FindingCode.COLUMN_COMPARISON_ONLY: FindingSeverity.NOTABLE,
        FindingCode.EMPTY_COLUMN: FindingSeverity.NOTABLE,
        FindingCode.CONSTANT_COLUMN: FindingSeverity.NOTABLE,
        FindingCode.DUPLICATE_ROWS: FindingSeverity.INFO,
    }
    assert {code: FINDINGS_POLICY.severity(code) for code in FindingCode} == expected
    assert FINDINGS_POLICY.severity(FindingCode.COLUMN_REFERENCE_ONLY) is (
        FINDINGS_POLICY.severity(FindingCode.COLUMN_COMPARISON_ONLY)
    )


def test_policy_rejects_an_incomplete_or_repeated_table() -> None:
    rules = FINDINGS_POLICY.rules
    with pytest.raises(ValueError, match="every finding code"):
        FindingsPolicy(identifier="x", rules=rules[1:])
    with pytest.raises(ValueError, match="every finding code"):
        FindingsPolicy(identifier="x", rules=rules + rules[:1])
    with pytest.raises(ValueError, match="identifier"):
        FindingsPolicy(identifier=" ", rules=rules)
    with pytest.raises(TypeError):
        FindingsPolicy(identifier="x", rules=list(rules))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        FindingRule(code="empty_column", severity=FindingSeverity.INFO)  # type: ignore[arg-type]
    with pytest.raises(KeyError):
        FINDINGS_POLICY.severity("empty_column")  # type: ignore[arg-type]
    with pytest.raises(KeyError):
        FINDINGS_POLICY.rank("empty_column")  # type: ignore[arg-type]


def test_each_code_has_one_scope() -> None:
    scopes = {
        FindingCode.EMPTY_COLUMN: FindingScope.COLUMN,
        FindingCode.DUPLICATE_ROWS: FindingScope.DATASET,
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE: FindingScope.TARGET_PREDICTOR,
        FindingCode.SEMANTIC_TYPE_CHANGED: FindingScope.COMPARISON_COLUMN,
        FindingCode.TARGET_TASK_CHANGED: FindingScope.COMPARISON_TARGET,
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED: (
            FindingScope.COMPARISON_TARGET_PREDICTOR
        ),
    }
    empty = _finding(FindingCode.EMPTY_COLUMN, _column(0), _EMPTY)
    assert empty.scope is scopes[FindingCode.EMPTY_COLUMN]
    assert empty.source is FindingsSource.PROFILE
    used = {scope for scope in scopes.values()}
    assert used == set(FindingScope)


def test_identity_is_the_condition_and_not_the_severity() -> None:
    notable = _finding(FindingCode.EMPTY_COLUMN, _column(0), _EMPTY)
    escalated = dataclasses.replace(notable, severity=FindingSeverity.WARNING)
    other_counts = dataclasses.replace(
        notable,
        evidence=BasicColumnEvidence(
            n_total=9, n_missing=9, n_non_missing=0, n_unique_non_missing=0
        ),
    )
    moved = dataclasses.replace(notable, subject=_column(7))
    assert escalated.identity == notable.identity
    assert other_counts.identity == notable.identity
    assert moved.identity == notable.identity
    assert hash(escalated.identity) == hash(notable.identity)
    assert notable.identity == FindingIdentity(
        code=FindingCode.EMPTY_COLUMN,
        subject=(("label", ("str", "a"), 1),),
    )
    with pytest.raises(ValueError, match="severity must follow the policy"):
        _profile((escalated,))


def test_column_subject_keys_use_label_identity_and_fall_back_to_position() -> None:
    unsupported = RetainedColumnLabel(kind=ColumnLabelKind.UNSUPPORTED)
    fallback = ColumnSubject(position=4, label=unsupported, occurrence=None)
    assert fallback.key == ("position", 4)
    assert _column(0, True).key != _column(0, 1).key
    assert _column(0, 1).key[1] == _column(0, 1.0).key[1]
    assert _column(0, float("nan")).key != _column(0, None).key
    with pytest.raises(ValueError, match="retained label has an occurrence"):
        ColumnSubject(position=0, label=retain_column_label("a"), occurrence=None)
    with pytest.raises(ValueError, match="unsupported label has no occurrence"):
        ColumnSubject(position=0, label=unsupported, occurrence=1)
    with pytest.raises(ValueError, match="positive"):
        ColumnSubject(position=0, label=retain_column_label("a"), occurrence=0)
    with pytest.raises(ValueError, match="other than the target"):
        TargetPredictorSubject(target=_column(1), predictor=_column(1, "b"))
    with pytest.raises(ValueError, match="matched column"):
        ComparedTargetPredictorSubject(
            target=_alignment(),
            predictor=_alignment(ColumnMatchStatus.REFERENCE_ONLY, "b", 1),
        )
    with pytest.raises(ValueError, match="other than the target"):
        ComparedTargetPredictorSubject(target=_alignment(), predictor=_alignment())
    with pytest.raises(TypeError):
        subject_key("a")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        subject_order("a")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="subject must be a tuple"):
        FindingIdentity(code=FindingCode.EMPTY_COLUMN, subject=["a"])  # type: ignore[arg-type]


def test_comparison_keys_follow_alignment_and_unsupported_sides() -> None:
    unsupported = RetainedColumnLabel(kind=ColumnLabelKind.UNSUPPORTED)
    reference_side = ColumnAlignment(
        status=ColumnMatchStatus.REFERENCE_ONLY,
        reference_label=unsupported,
        comparison_label=None,
        occurrence=None,
        reference_position=3,
        comparison_position=None,
    )
    comparison_side = ColumnAlignment(
        status=ColumnMatchStatus.COMPARISON_ONLY,
        reference_label=None,
        comparison_label=unsupported,
        occurrence=None,
        reference_position=None,
        comparison_position=3,
    )
    assert subject_key(reference_side) != subject_key(comparison_side)
    assert subject_key(_alignment(reference_position=0, comparison_position=5)) == (
        subject_key(_alignment(reference_position=2, comparison_position=0))
    )


def test_findings_reject_mismatched_subjects_and_evidence() -> None:
    with pytest.raises(TypeError, match="subject must be a ColumnSubject"):
        _finding(FindingCode.EMPTY_COLUMN, _alignment(), _EMPTY)
    with pytest.raises(TypeError, match="evidence must be a BasicColumnEvidence"):
        _finding(
            FindingCode.EMPTY_COLUMN,
            _column(0),
            DuplicateRowsEvidence(
                n_rows=4, n_duplicate_groups=1, n_rows_in_duplicate_groups=2
            ),
        )
    with pytest.raises(ValueError, match="about the dataset"):
        _finding(
            FindingCode.DUPLICATE_ROWS,
            _column(0),
            DuplicateRowsEvidence(
                n_rows=4, n_duplicate_groups=1, n_rows_in_duplicate_groups=2
            ),
        )
    with pytest.raises(ValueError, match="empty column"):
        _finding(FindingCode.EMPTY_COLUMN, _column(0), _CONSTANT)
    with pytest.raises(ValueError, match="constant column"):
        _finding(FindingCode.CONSTANT_COLUMN, _column(0), _VARIED)
    with pytest.raises(TypeError):
        Finding(
            code="empty_column",  # type: ignore[arg-type]
            severity=FindingSeverity.NOTABLE,
            subject=_column(0),
            evidence=_EMPTY,
        )


def test_target_findings_require_their_mechanical_status() -> None:
    pair = TargetPredictorSubject(target=_column(0, "y"), predictor=_column(1, "x"))
    _finding(
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
        pair,
        _exact(ExactDuplicateStatus.EXACT_DUPLICATE),
    )
    with pytest.raises(ValueError, match="exact duplicate evidence"):
        _finding(
            FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
            pair,
            _exact(ExactDuplicateStatus.NOT_EQUAL),
        )
    _finding(FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE, pair, _mapping(0))
    with pytest.raises(ValueError, match="no singleton value"):
        _finding(FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE, pair, _mapping(1))


def test_comparison_findings_require_their_condition() -> None:
    reference_only = SemanticComparison(reference=_snapshot(), comparison=None)
    _finding(
        FindingCode.COLUMN_REFERENCE_ONLY,
        _alignment(ColumnMatchStatus.REFERENCE_ONLY),
        reference_only,
    )
    with pytest.raises(ValueError, match="alignment is reference_only"):
        _finding(FindingCode.COLUMN_REFERENCE_ONLY, _alignment(), reference_only)
    with pytest.raises(ValueError, match="side that has the column"):
        _finding(
            FindingCode.COLUMN_COMPARISON_ONLY,
            _alignment(ColumnMatchStatus.COMPARISON_ONLY),
            reference_only,
        )
    changed = SemanticTransitionEvidence(
        semantic=SemanticComparison(
            reference=_snapshot(SemanticType.NUMERIC),
            comparison=_snapshot(SemanticType.CATEGORICAL),
        ),
        n_relationship_transitions=0,
    )
    with pytest.raises(ValueError, match="matched column"):
        _finding(
            FindingCode.SEMANTIC_TYPE_CHANGED,
            _alignment(ColumnMatchStatus.REFERENCE_ONLY),
            changed,
        )
    with pytest.raises(ValueError, match="two different selected types"):
        SemanticTransitionEvidence(
            semantic=SemanticComparison(reference=_snapshot(), comparison=_snapshot()),
            n_relationship_transitions=0,
        )
    vocabulary = DiagnosticPredictabilityComparison(
        status=DiagnosticComparisonStatus.NOT_COLLECTED
    )
    with pytest.raises(ValueError, match="task_transition"):
        _finding(FindingCode.TARGET_TASK_CHANGED, _alignment(), vocabulary)
    with pytest.raises(ValueError, match="aligned target"):
        _finding(
            FindingCode.TARGET_CLASS_VOCABULARY_CHANGED,
            _alignment(ColumnMatchStatus.REFERENCE_ONLY),
            vocabulary,
        )
    subject = ComparedTargetPredictorSubject(
        target=_alignment(label="y"),
        predictor=_alignment(label="x", reference_position=1, comparison_position=1),
    )

    def transition(reference, comparison, position=1):
        return PredictorLeakageTransition(
            reference_position=position,
            comparison_position=1,
            occurrence=1,
            reference_exact=reference,
            comparison_exact=comparison,
            reference_mapping=MappingStatus.NOT_APPLICABLE,
            comparison_mapping=MappingStatus.NOT_APPLICABLE,
        )

    exact = ExactDuplicateStatus.EXACT_DUPLICATE
    unequal = ExactDuplicateStatus.NOT_EQUAL
    code = FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED
    _finding(code, subject, transition(exact, unequal))
    with pytest.raises(ValueError, match="exactly one side"):
        _finding(code, subject, transition(exact, exact))
    with pytest.raises(ValueError, match="exactly one side"):
        _finding(code, subject, transition(unequal, unequal))
    with pytest.raises(ValueError, match="predictor's"):
        _finding(code, subject, transition(exact, unequal, position=2))


def test_snapshot_evidence_keeps_exact_counts() -> None:
    evidence = DuplicateRowsEvidence(
        n_rows=10, n_duplicate_groups=2, n_rows_in_duplicate_groups=5
    )
    assert evidence.n_excess_duplicate_rows == 3
    with pytest.raises(ValueError, match="at least one group"):
        DuplicateRowsEvidence(
            n_rows=10, n_duplicate_groups=0, n_rows_in_duplicate_groups=0
        )
    with pytest.raises(ValueError, match="at least two rows"):
        DuplicateRowsEvidence(
            n_rows=10, n_duplicate_groups=2, n_rows_in_duplicate_groups=3
        )
    with pytest.raises(ValueError, match="cannot exceed"):
        DuplicateRowsEvidence(
            n_rows=3, n_duplicate_groups=2, n_rows_in_duplicate_groups=4
        )
    with pytest.raises(ValueError, match="non-negative"):
        DuplicateRowsEvidence(
            n_rows=-1, n_duplicate_groups=1, n_rows_in_duplicate_groups=2
        )


def test_result_rejects_unordered_repeated_or_unevaluated_findings() -> None:
    first = _finding(FindingCode.EMPTY_COLUMN, _column(0, "a"), _EMPTY)
    second = _finding(FindingCode.EMPTY_COLUMN, _column(1, "b"), _EMPTY)
    constant = _finding(FindingCode.CONSTANT_COLUMN, _column(2, "c"), _CONSTANT)
    result = _profile((first, second, constant))
    assert result.coverage.n_findings == 3
    with pytest.raises(ValueError, match="policy order"):
        _profile((second, first))
    with pytest.raises(ValueError, match="policy order"):
        _profile((constant, first))
    with pytest.raises(ValueError, match="distinct identities"):
        _profile((first, dataclasses.replace(first, subject=_column(1, "a"))))
    with pytest.raises(ValueError, match="was not evaluated"):
        _profile((first,), evaluated=(FindingCode.CONSTANT_COLUMN,))
    compare_only = _finding(
        FindingCode.COLUMN_REFERENCE_ONLY,
        _alignment(ColumnMatchStatus.REFERENCE_ONLY),
        SemanticComparison(reference=_snapshot(), comparison=None),
    )
    with pytest.raises(ValueError, match="not a profile finding"):
        _profile((compare_only,))
    with pytest.raises(ValueError, match="not a profile finding"):
        coverage_for(
            FindingsSource.PROFILE,
            FINDINGS_POLICY,
            (FindingCode.SEMANTIC_TYPE_CHANGED,),
            (),
            (),
        )
    with pytest.raises(ValueError, match="coverage does not match"):
        FindingsAnalysis(
            source=FindingsSource.PROFILE,
            policy=FINDINGS_POLICY,
            coverage=result.coverage,
            findings=(first,),
        )
    with pytest.raises(TypeError):
        FindingsAnalysis(
            source=FindingsSource.PROFILE,
            policy=FINDINGS_POLICY,
            coverage=result.coverage,
            findings=[first, second, constant],  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="suppressed must be a tuple"):
        FindingsAnalysis(
            source=FindingsSource.PROFILE,
            policy=FINDINGS_POLICY,
            coverage=result.coverage,
            findings=(first, second, constant),
            suppressed=[],  # type: ignore[arg-type]
        )


def test_suppression_names_an_emitted_root_of_the_right_kind() -> None:
    pair = TargetPredictorSubject(target=_column(0, "y"), predictor=_column(1, "x"))
    exact = _finding(
        FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE,
        pair,
        _exact(ExactDuplicateStatus.EXACT_DUPLICATE),
    )
    mapping = _finding(
        FindingCode.TARGET_DETERMINISTIC_MAPPING_EVIDENCE, pair, _mapping(0)
    )
    owned = SuppressedFinding(
        finding=mapping,
        root=exact.identity,
        rule=SuppressionRule.EXACT_DUPLICATE_OWNS_MAPPING,
    )
    result = _profile((exact,), (owned,))
    assert result.coverage.n_suppressed == 1
    assert result.coverage.n_candidates == 2
    with pytest.raises(ValueError, match="emitted root"):
        _profile((), (owned,))
    with pytest.raises(ValueError, match="emitted or suppressed once"):
        _profile((exact, mapping), (owned,))
    with pytest.raises(ValueError, match="does not suppress itself"):
        SuppressedFinding(
            finding=exact,
            root=exact.identity,
            rule=SuppressionRule.EXACT_DUPLICATE_OWNS_MAPPING,
        )
    with pytest.raises(ValueError, match="owned by the exact duplicate"):
        SuppressedFinding(
            finding=exact,
            root=mapping.identity,
            rule=SuppressionRule.EXACT_DUPLICATE_OWNS_MAPPING,
        )
    other = TargetPredictorSubject(target=_column(0, "y"), predictor=_column(2, "z"))
    with pytest.raises(ValueError, match="same predictor"):
        SuppressedFinding(
            finding=mapping,
            root=dataclasses.replace(exact, subject=other).identity,
            rule=SuppressionRule.EXACT_DUPLICATE_OWNS_MAPPING,
        )
    with pytest.raises(ValueError, match="target comparison findings"):
        SuppressedFinding(
            finding=mapping,
            root=exact.identity,
            rule=SuppressionRule.SEMANTIC_CHANGE_OWNS_TARGET_COMPARISON,
        )
    task = _finding(
        FindingCode.TARGET_TASK_CHANGED,
        _alignment(label="y"),
        DiagnosticPredictabilityComparison(
            status=DiagnosticComparisonStatus.TASK_TRANSITION,
            reference_task=PredictiveTask.REGRESSION,
            comparison_task=PredictiveTask.BINARY_CLASSIFICATION,
        ),
    )
    with pytest.raises(ValueError, match="root of a target comparison"):
        SuppressedFinding(
            finding=task,
            root=exact.identity,
            rule=SuppressionRule.SEMANTIC_CHANGE_OWNS_TARGET_COMPARISON,
        )
    elsewhere = FindingIdentity(
        code=FindingCode.SEMANTIC_TYPE_CHANGED,
        subject=(("label", ("str", "other"), 1),),
    )
    with pytest.raises(ValueError, match="about a column of the finding"):
        SuppressedFinding(
            finding=task,
            root=elsewhere,
            rule=SuppressionRule.SEMANTIC_CHANGE_OWNS_TARGET_COMPARISON,
        )


def test_coverage_is_arithmetic_and_not_a_score() -> None:
    result = collect_profile_findings(
        analyze_dataframe(pd.DataFrame({"e": [None, None]}))
    )
    coverage = result.coverage
    assert coverage.deferred_families == DEFERRED_FINDING_FAMILIES
    assert (
        coverage.n_findings == coverage.n_warning + coverage.n_notable + coverage.n_info
    )
    assert set(coverage.evaluated_codes).isdisjoint(coverage.not_evaluated_codes)
    with pytest.raises(ValueError, match="sum to n_findings"):
        dataclasses.replace(coverage, n_info=coverage.n_info + 1)
    with pytest.raises(ValueError, match="not both"):
        dataclasses.replace(coverage, not_evaluated_codes=coverage.evaluated_codes[:1])
    with pytest.raises(ValueError, match="fixed for v0.1"):
        dataclasses.replace(coverage, deferred_families=())
    with pytest.raises(TypeError):
        dataclasses.replace(coverage, evaluated_codes=["empty_column"])
    fields = {field.name for field in dataclasses.fields(FindingsCoverage)}
    assert not any("score" in name for name in fields)


def test_the_package_reads_no_source_values_and_no_significance() -> None:
    sources = {
        path.name: path.read_text(encoding="utf-8") for path in _PACKAGE.glob("*.py")
    }
    assert set(sources) == {
        "__init__.py",
        "models.py",
        "result.py",
        "policy.py",
        "profile.py",
        "compare.py",
    }
    forbidden_imports = re.compile(
        r"^\s*(import|from)\s+(pandas|numpy|scipy|sklearn)\b", re.M
    )
    for name, text in sources.items():
        assert not forbidden_imports.search(text), name
        assert "p_value" not in text, name
        assert "adjusted" not in text, name
    finding_fields = {field.name for field in dataclasses.fields(Finding)}
    assert finding_fields == {"code", "severity", "subject", "evidence"}
    prose = re.compile(r"message|text|title|label_text|recommend|score|summary")
    modules = (findings_package.models, findings_package.result)
    for value in [item for module in modules for item in vars(module).values()]:
        if isinstance(value, type) and dataclasses.is_dataclass(value):
            assert value.__dataclass_params__.frozen, value
            for field in dataclasses.fields(value):
                assert not prose.search(field.name), (value, field.name)
