"""TSK-042: public profile and comparison results."""

from __future__ import annotations

import dataclasses

import pandas as pd
import pytest

from pytics import __version__
from pytics.analysis.column_label import _COLUMN_LABEL_FIELDS
from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.target_models import TargetAlignmentStatus
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.target import TargetStatus
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.results import AmbiguousColumnLabel
from pytics.results import ResultKind
from pytics.results import TargetRequest
from pytics.results import comparison_result
from pytics.results import profile_result
from pytics.results.equality import LABEL_FIELDS
from pytics.semantics.interpretation import SemanticType
from tests.findings_support import assert_source_free
from tests.findings_support import with_labels


def test_label_fields_follow_the_column_identity_contract() -> None:
    assert LABEL_FIELDS == _COLUMN_LABEL_FIELDS


def test_profile_without_target_exposes_views_and_not_a_renderer() -> None:
    frame = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 5.0]})
    result = profile_result(frame)
    assert type(result).__name__ == "ProfileResult"
    assert result.metadata.kind is ResultKind.PROFILE
    assert result.metadata.pytics_version == __version__
    assert result.metadata.target_request is TargetRequest.NOT_REQUESTED
    assert result.metadata.findings_policy == "pytics.findings/0.1"
    assert result.n_rows == 4
    assert result.n_columns == 2
    assert result.target.request is TargetRequest.NOT_REQUESTED
    assert result.target.analysis is None
    assert result.target.status is None
    assert result.target.diagnostic_status is None
    assert result.variables[0].label == "x"
    assert result.variables[0].selected_type is SemanticType.NUMERIC
    assert len(result.relationships) == 1
    assert result.relationships.between(0, 1) is result.relationships[0]
    assert result.relationships.between_labels("y", "x") is result.relationships[0]
    assert result.missing is result._analysis.missing_analysis
    assert result.duplicates is result._analysis.duplicate_analysis
    assert result.anomalies is result._analysis.anomaly_analysis
    assert result.coverage.relationships is result._analysis.relationship_analysis
    assert result.coverage.relationships.n_analyzed_pairs == 1
    assert result.coverage.findings.n_findings == len(result.findings)
    assert not hasattr(result, "to_html")
    assert not hasattr(result, "to_markdown")
    assert not hasattr(result, "to_pdf")
    assert not hasattr(result, "to_json")
    assert not hasattr(result, "to_dict")
    assert not hasattr(result, "_repr_html_")
    assert not hasattr(result, "show")
    assert not hasattr(result, "score")
    assert "quality" not in result.__dict__


def test_profile_with_target_is_distinct_from_an_unsupported_target() -> None:
    rows = 40
    supported = pd.DataFrame(
        {
            "x": list(range(rows)),
            "y": [index % 2 == 0 for index in range(rows)],
        }
    )
    result = profile_result(supported, target="y")
    assert result.target.request is TargetRequest.REQUESTED
    assert result.target.status is TargetStatus.SUPPORTED
    assert result.target.analysis is result._analysis.target_analysis
    assert result.target.leakage is result._analysis.target_leakage
    assert result.target.diagnostic is result._analysis.target_diagnostic
    assert result.target.diagnostic_status is DiagnosticStatus.AVAILABLE
    assert result.metadata.target_request is TargetRequest.REQUESTED

    unsupported = pd.DataFrame(
        {
            "when": pd.date_range("2020-01-01", periods=5),
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    unavailable = profile_result(unsupported, target="when")
    assert unavailable.target.request is TargetRequest.REQUESTED
    assert unavailable.target.status is TargetStatus.UNSUPPORTED
    assert unavailable.target.diagnostic_status is (
        DiagnosticStatus.TARGET_TYPE_UNSUPPORTED
    )
    omitted = profile_result(unsupported)
    assert omitted.target.request is TargetRequest.NOT_REQUESTED
    assert omitted.target.status is None
    assert omitted.target.diagnostic_status is None


def test_ambiguous_target_does_not_return_a_disabled_target() -> None:
    frame = with_labels([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], ["a", "a"])
    with pytest.raises(ValueError, match="more than one column"):
        profile_result(frame, target="a")


def test_variables_keep_duplicate_nan_and_numeric_labels_distinct() -> None:
    frame = with_labels(
        [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0], [1.0, 1.0, 1.0]],
        [1, 1.0, True, float("nan")],
    )
    result = profile_result(frame)
    assert [variable.position for variable in result.variables] == [0, 1, 2, 3]
    assert result.variables[0].label == 1
    assert result.variables[1].label == 1.0
    assert (
        result.variables[0].identity.match_key == result.variables[1].identity.match_key
    )
    assert result.variables[0].identity.occurrence == 1
    assert result.variables[1].identity.occurrence == 2
    assert (
        result.variables[2].identity.match_key != result.variables[0].identity.match_key
    )
    assert result.variables.by_label(True).position == 2
    assert result.variables.by_label(True).position != result.variables[0].position
    nan = result.variables.by_label(float("nan"))
    assert nan.position == 3
    assert nan.identity.occurrence == 1
    with pytest.raises(AmbiguousColumnLabel) as caught:
        result.variables.by_label(1)
    assert caught.value.positions == (0, 1)
    with pytest.raises(KeyError):
        result.variables.by_label("missing")
    with pytest.raises(TypeError):
        result.variables[True]  # type: ignore[index]
    assert result.variables[1].position == 1
    assert result.variables[-1].position == 3


def test_duplicate_labels_and_adversarial_labels_round_trip() -> None:
    labels = ["a", "a", "", ("a", True), ("a", 1)]
    columns = [[float(index), float(index + 1), float(index + 2)] for index in range(5)]
    frame = with_labels(columns, labels)
    result = profile_result(frame)
    assert len(result.variables.matching("a")) == 2
    with pytest.raises(AmbiguousColumnLabel):
        result.variables.by_label("a")
    assert result.variables.by_label("").position == 2
    assert result.variables.by_label(("a", True)).position == 3
    assert result.variables.by_label(("a", 1)).position == 4
    assert (
        result.variables[3].identity.match_key != result.variables[4].identity.match_key
    )
    again = profile_result(with_labels(columns, labels))
    assert result == again
    assert result is not again


def test_nan_labels_compare_equal_on_the_public_result() -> None:
    columns = [[1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 5.0]]
    labels = [float("nan"), "b"]
    left = profile_result(with_labels(columns, labels))
    right = profile_result(with_labels(columns, labels))
    assert left == right
    assert left._analysis is not right._analysis
    with pytest.raises(TypeError):
        hash(left)


def test_true_does_not_compare_equal_to_one_and_one_matches_one_point_zero() -> None:
    values = [[1.0, 2.0, 3.0, 4.0]]
    as_bool = profile_result(with_labels(values, [True]))
    as_int = profile_result(with_labels(values, [1]))
    as_float = profile_result(with_labels(values, [1.0]))
    assert as_bool != as_int
    assert as_int == as_float


def test_findings_keep_identity_evidence_policy_and_order() -> None:
    frame = pd.DataFrame({"a": [None, None], "b": [1.0, 1.0]})
    result = profile_result(frame)
    codes = [finding.code for finding in result.findings]
    assert codes == [finding.code for finding in result.findings.records]
    assert codes[0] is FindingCode.EMPTY_COLUMN
    assert result.findings[0] is result._findings_analysis.findings[0]
    assert result.findings[0].evidence is not None
    assert result.findings[0].severity is result.findings.policy.severity(codes[0])
    assert result.findings.policy.identifier == "pytics.findings/0.1"
    assert result.findings.coverage.evaluated_codes
    assert FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE in (
        result.findings.coverage.not_evaluated_codes
    )
    duplicated = profile_result(pd.DataFrame({"a": [1, 1], "b": [2, 2]}))
    duplicate_finding = next(
        finding
        for finding in duplicated.findings
        if finding.code is FindingCode.DUPLICATE_ROWS
    )
    assert duplicate_finding.evidence.n_duplicate_groups == 1
    assert duplicated.findings.suppressed is duplicated._findings_analysis.suppressed


def test_inspection_does_not_recompute_or_require_the_frame(monkeypatch) -> None:
    frame = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 5.0]})
    result = profile_result(frame)
    minimum = result.variables[0].record.numeric_analysis.minimum
    frame.iloc[0, 0] = 100.0
    del frame

    def boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("analysis ran during inspection")

    monkeypatch.setattr("pytics.results.profile.analyze_dataframe", boom)
    monkeypatch.setattr(
        "pytics.analysis.relationships.numeric_numeric.spearmanr",
        boom,
    )
    assert result.n_rows == 4
    assert result.variables[0].record.numeric_analysis.minimum == minimum
    assert result.relationships[0] is (
        result._analysis.relationship_analysis.relationships[0]
    )
    assert result.variables[0].record is result._analysis.columns[0]
    assert_source_free(result)


def test_public_result_is_frozen() -> None:
    result = profile_result(pd.DataFrame({"x": [None, None], "y": [1.0, 2.0]}))
    with pytest.raises(dataclasses.FrozenInstanceError):
        result._analysis = None  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.variables._columns = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.variables = ()  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.findings[0].code = FindingCode.CONSTANT_COLUMN  # type: ignore[misc]


def test_profile_result_rejects_a_non_frame() -> None:
    with pytest.raises(TypeError):
        profile_result([1, 2, 3])  # type: ignore[arg-type]


def test_comparison_without_target_keeps_alignment_and_drift() -> None:
    reference = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [1.0, 2.0, 3.0, 4.0]})
    comparison = pd.DataFrame(
        {
            "b": [1.0, 2.0, 3.0, 9.0],
            "a": [1.0, 2.0, 3.0, 8.0],
            "c": [1.0, 1.0, 1.0, 1.0],
        }
    )
    result = comparison_result(reference, comparison)
    assert result.metadata.kind is ResultKind.COMPARISON
    assert result.target.request is TargetRequest.NOT_REQUESTED
    assert result.target.analysis is None
    assert result.target.alignment_status is None
    assert result.coverage.target is None
    matched = result.columns.by_label("a")
    assert matched.alignment.status is ColumnMatchStatus.MATCHED
    assert matched.alignment.reordered is True
    assert matched.distribution is not None
    added = result.columns.by_label("c")
    assert added.alignment.status is ColumnMatchStatus.COMPARISON_ONLY
    assert result.relationships.between(0, 1) is result.relationships[0]
    assert result.relationships.between_labels("b", "a") is result.relationships[0]
    assert result.coverage.columns.n_comparison_only_columns == 1
    assert result.coverage.relationships.n_aligned_pairs == 1
    assert "anomaly_comparison" in {
        family.value for family in result.coverage.columns.deferred_families
    }
    assert_source_free(result)
    assert result == comparison_result(reference, comparison)


def test_comparison_target_request_is_distinct_from_a_missing_target() -> None:
    reference = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [True, False, True, False, True],
        }
    )
    comparison = pd.DataFrame(
        {
            "y": [False, True, False, True, False],
            "a": [1.0, 2.0, 3.0, 4.0, 9.0],
        }
    )
    omitted = comparison_result(reference, comparison)
    assert omitted.target.request is TargetRequest.NOT_REQUESTED
    requested = comparison_result(reference, comparison, target="y")
    assert requested.target.request is TargetRequest.REQUESTED
    assert requested.target.alignment_status is TargetAlignmentStatus.ALIGNED
    assert requested.target.analysis is requested._comparison.target
    assert requested.coverage.target is requested.target.analysis.coverage
    missing = comparison_result(reference, comparison, target="absent")
    assert missing.target.request is TargetRequest.REQUESTED
    assert missing.target.alignment_status is TargetAlignmentStatus.NOT_IN_EITHER
    assert missing.target.analysis is not None
    assert missing != omitted
    assert missing != requested


def test_comparison_identity_for_duplicate_nan_and_bool_labels() -> None:
    reference = with_labels(
        [[1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0]],
        ["a", "a"],
    )
    comparison = with_labels(
        [[1.0, 2.0, 3.0, 4.0], [9.0, 3.0, 2.0, 1.0]],
        ["a", "a"],
    )
    result = comparison_result(reference, comparison)
    matched = result.columns.matching("a")
    assert len(matched) == 2
    assert matched[0].alignment.occurrence == 1
    assert matched[1].alignment.occurrence == 2
    assert matched[0].alignment.status is ColumnMatchStatus.MATCHED
    with pytest.raises(AmbiguousColumnLabel) as caught:
        result.columns.by_label("a")
    assert caught.value.positions == (0, 1)

    nan_reference = with_labels(
        [[1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0]],
        [float("nan"), "b"],
    )
    nan_comparison = with_labels(
        [[9.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0]],
        ["b", float("nan")],
    )
    nan_result = comparison_result(nan_reference, nan_comparison)
    nan_column = nan_result.columns.by_label(float("nan"))
    assert nan_column.alignment.status is ColumnMatchStatus.MATCHED
    assert nan_column.alignment.reordered is True
    assert nan_result == comparison_result(nan_reference, nan_comparison)

    bool_reference = with_labels([[1.0, 2.0, 3.0, 4.0]], [True])
    int_comparison = with_labels([[1.0, 2.0, 3.0, 4.0]], [1])
    separated = comparison_result(bool_reference, int_comparison)
    assert separated.columns[0].alignment.status is ColumnMatchStatus.REFERENCE_ONLY
    assert separated.columns[1].alignment.status is ColumnMatchStatus.COMPARISON_ONLY

    int_reference = with_labels([[1.0, 2.0, 3.0, 4.0]], [1])
    float_comparison = with_labels([[1.0, 2.0, 3.0, 4.0]], [1.0])
    aligned = comparison_result(int_reference, float_comparison)
    assert len(aligned.columns) == 1
    assert aligned.columns[0].alignment.status is ColumnMatchStatus.MATCHED


def test_comparison_schema_transition_is_on_the_column() -> None:
    reference = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]})
    comparison = pd.DataFrame({"a": ["x", "y", "x", "y"]})
    result = comparison_result(reference, comparison)
    column = result.columns.by_label("a")
    assert column.semantic.selected_type_changed is True
    assert any(
        finding.code is FindingCode.SEMANTIC_TYPE_CHANGED for finding in result.findings
    )
    changed = next(
        finding
        for finding in result.findings
        if finding.code is FindingCode.SEMANTIC_TYPE_CHANGED
    )
    assert changed.evidence is not None
    assert changed.subject.reference_position == 0


def test_comparison_result_rejects_a_non_frame_and_is_frozen() -> None:
    frame = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    with pytest.raises(TypeError):
        comparison_result(frame, [1, 2, 3])  # type: ignore[arg-type]
    result = comparison_result(frame, frame)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result._comparison = None  # type: ignore[misc]
    with pytest.raises(TypeError):
        result.relationships.between(True, 0)


def test_content_equality_covers_labels_numbers_and_shape() -> None:
    import numpy as np

    from pytics.results.equality import content_equal

    assert content_equal(1, 1.0) is False
    assert content_equal(float("nan"), float("nan")) is True
    assert content_equal(np.float64("nan"), np.float64("nan")) is True
    assert content_equal(np.float64(1.0), np.float64(1.0)) is True
    assert content_equal(np.float64(1.0), np.float64(2.0)) is False
    assert content_equal((1,), (1, 2)) is False
    assert content_equal((1, 2), (1, 2)) is True


def test_construction_guards_and_lookup_edges() -> None:
    from pytics.analysis.column_label import retain_column_label
    from pytics.analysis.findings.models import FindingsSource
    from pytics.results import ComparisonColumnIndex
    from pytics.results import ComparisonCoverageView
    from pytics.results import ComparisonRelationshipIndex
    from pytics.results import ComparisonResult
    from pytics.results import ComparisonTargetView
    from pytics.results import FindingsView
    from pytics.results import ProfileCoverage
    from pytics.results import ProfileResult
    from pytics.results import RelationshipIndex
    from pytics.results import ResultMetadata
    from pytics.results import TargetView
    from pytics.results import Variable
    from pytics.results import VariableIndex
    from pytics.results.common import retained_label_matches

    frame = pd.DataFrame({"a": [1, 1, 1], "b": [2, 2, 2]})
    result = profile_result(frame)
    assert result.n_cells == 6
    assert result.variables[0].resolution_status.value == "resolved"
    assert len(result.variables) == 2
    assert list(result.relationships) == []
    assert result.findings.source is FindingsSource.PROFILE
    assert result.relationships.records == ()
    assert result.relationships.analysis.n_ineligible_pairs == 1
    assert "ProfileResult" in repr(result)
    assert "Variable" in repr(result.variables[0])
    assert "VariableIndex" in repr(result.variables)
    assert "RelationshipIndex" in repr(result.relationships)
    assert "TargetView" in repr(result.target)
    assert "FindingsView" in repr(result.findings)
    assert "ProfileCoverage" in repr(result.coverage)
    assert "ResultMetadata" in repr(result.metadata)
    with pytest.raises(KeyError):
        result.relationships.between(0, 1)
    with pytest.raises(ValueError):
        result.relationships.between(0, 0)
    with pytest.raises(TypeError):
        result.relationships.between(-1, 0)
    with pytest.raises(TypeError):
        result.relationships[True]  # type: ignore[index]
    with pytest.raises(IndexError):
        result.variables[5]
    with pytest.raises(IndexError):
        result.variables[-5]
    assert result.__eq__("no") is NotImplemented
    assert result != "no"

    reference = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0]})
    other = pd.DataFrame({"a": [1.0, 2.0, 3.0, 9.0], "c": [1.0, 1.0, 1.0, 1.0]})
    compared = comparison_result(reference, other)
    assert "ComparisonResult" in repr(compared)
    assert "ComparisonCoverageView" in repr(compared.coverage)
    assert compared.columns.records[0].alignment.reference_position == 0
    assert list(compared.columns)
    assert "ComparisonColumnIndex" in repr(compared.columns)
    assert compared.overview.n_rows.reference == 4
    with pytest.raises(KeyError):
        compared.columns.by_label("missing")
    with pytest.raises(ValueError):
        compared.relationships.between(0, 0)
    assert list(compared.relationships) == []
    assert len(compared.relationships) == 0
    assert compared.relationships.records == ()
    with pytest.raises(ValueError):
        compared.relationships.between_labels("a", "c")
    with pytest.raises(KeyError):
        compared.relationships.between(0, 5)
    with pytest.raises(TypeError):
        compared.columns["a"]  # type: ignore[index]
    assert compared.__eq__(result) is NotImplemented

    assert retained_label_matches(None, "a") is False
    assert retained_label_matches(retain_column_label(object()), "a") is False
    assert retained_label_matches(retain_column_label("a"), object()) is False

    with pytest.raises(ValueError):
        ResultMetadata(" ", ResultKind.PROFILE, TargetRequest.NOT_REQUESTED, "x")
    with pytest.raises(TypeError):
        ResultMetadata("1", "profile", TargetRequest.NOT_REQUESTED, "x")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ResultMetadata("1", ResultKind.PROFILE, "no", "x")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ResultMetadata("1", ResultKind.PROFILE, TargetRequest.NOT_REQUESTED, " ")
    with pytest.raises(TypeError):
        FindingsView(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Variable(object(), object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        VariableIndex.from_columns([])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        VariableIndex("no", ())  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        VariableIndex((), (object(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        VariableIndex((object(),), (object(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        RelationshipIndex(object(), result.variables)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        RelationshipIndex(result.relationships.analysis, object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        VariableIndex((), "no")  # type: ignore[arg-type]
    one = profile_result(pd.DataFrame({"a": [1.0, 2.0, 3.0]}))
    with pytest.raises(TypeError):
        Variable(one.variables[0].record, object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        VariableIndex(one.variables._columns, (object(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        TargetView("no", None, None, None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        TargetView(TargetRequest.NOT_REQUESTED, object(), None, None)
    with pytest.raises(ValueError):
        TargetView(TargetRequest.REQUESTED, None, None, None)
    with pytest.raises(TypeError):
        TargetView(TargetRequest.REQUESTED, object(), object(), object())
    with pytest.raises(TypeError):
        ProfileCoverage(object(), object(), object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ProfileCoverage(
            result.coverage.relationships,
            object(),  # type: ignore[arg-type]
            result.coverage.findings,
        )
    with pytest.raises(TypeError):
        ProfileCoverage(
            result.coverage.relationships,
            result.coverage.anomalies,
            object(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        ProfileResult.from_analysis(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ProfileResult(
            object(),  # type: ignore[arg-type]
            result._findings_analysis,
            result.metadata,
            result.variables,
            result.relationships,
            result.findings,
            result.target,
            result.coverage,
        )
    with pytest.raises(TypeError):
        ProfileResult(
            result._analysis,
            object(),  # type: ignore[arg-type]
            result.metadata,
            result.variables,
            result.relationships,
            result.findings,
            result.target,
            result.coverage,
        )
    with pytest.raises(ValueError):
        ProfileResult(
            result._analysis,
            compared._findings_analysis,
            result.metadata,
            result.variables,
            result.relationships,
            result.findings,
            result.target,
            result.coverage,
        )
    bad_metadata = ResultMetadata(
        pytics_version="1.1.5",
        kind=ResultKind.COMPARISON,
        target_request=TargetRequest.NOT_REQUESTED,
        findings_policy="pytics.findings/0.1",
    )
    with pytest.raises(ValueError):
        ProfileResult(
            result._analysis,
            result._findings_analysis,
            bad_metadata,
            result.variables,
            result.relationships,
            result.findings,
            result.target,
            result.coverage,
        )
    with pytest.raises(TypeError):
        ComparisonResult.from_comparison(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonColumnIndex(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonColumnIndex((object(),))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonTargetView(object(), None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ComparisonTargetView(TargetRequest.NOT_REQUESTED, object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonTargetView(TargetRequest.REQUESTED, object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonCoverageView(object(), object(), object(), None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonCoverageView(
            compared.coverage.columns,
            object(),  # type: ignore[arg-type]
            compared.findings.coverage,
            None,
        )
    with pytest.raises(TypeError):
        ComparisonCoverageView(
            compared.coverage.columns,
            compared.coverage.relationships,
            object(),  # type: ignore[arg-type]
            None,
        )
    with pytest.raises(TypeError):
        ComparisonCoverageView(
            compared.coverage.columns,
            compared.coverage.relationships,
            compared.findings.coverage,
            object(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        ComparisonRelationshipIndex(object(), compared.relationships.coverage, compared.columns)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonRelationshipIndex((object(),), compared.relationships.coverage, compared.columns)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonRelationshipIndex((), object(), compared.columns)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ComparisonRelationshipIndex((), compared.relationships.coverage, object())  # type: ignore[arg-type]
    assert "ComparisonRelationshipIndex" in repr(compared.relationships)
    assert "ComparisonTargetView" in repr(compared.target)
    with pytest.raises(TypeError):
        ProfileResult(
            result._analysis,
            result._findings_analysis,
            object(),  # type: ignore[arg-type]
            result.variables,
            result.relationships,
            result.findings,
            result.target,
            result.coverage,
        )
    with pytest.raises(TypeError):
        ComparisonResult(
            object(),  # type: ignore[arg-type]
            compared._findings_analysis,
            compared.metadata,
            compared.columns,
            compared.relationships,
            compared.findings,
            compared.target,
            compared.coverage,
        )
    with pytest.raises(TypeError):
        ComparisonResult(
            compared._comparison,
            object(),  # type: ignore[arg-type]
            compared.metadata,
            compared.columns,
            compared.relationships,
            compared.findings,
            compared.target,
            compared.coverage,
        )
    with pytest.raises(TypeError):
        ComparisonResult(
            compared._comparison,
            compared._findings_analysis,
            object(),  # type: ignore[arg-type]
            compared.columns,
            compared.relationships,
            compared.findings,
            compared.target,
            compared.coverage,
        )
    with pytest.raises(ValueError):
        ComparisonResult(
            compared._comparison,
            result._findings_analysis,
            compared.metadata,
            compared.columns,
            compared.relationships,
            compared.findings,
            compared.target,
            compared.coverage,
        )
    with pytest.raises(ValueError):
        ComparisonResult(
            compared._comparison,
            compared._findings_analysis,
            result.metadata,
            compared.columns,
            compared.relationships,
            compared.findings,
            compared.target,
            compared.coverage,
        )

    dated = profile_result(
        pd.DataFrame(
            {
                "when": pd.date_range("2020-01-01", periods=3),
                "x": [1.0, 2.0, 3.0],
            }
        ),
        target="when",
    )
    with pytest.raises(TypeError):
        TargetView(
            TargetRequest.REQUESTED,
            dated.target.analysis,
            object(),
            dated.target.diagnostic,
        )
    with pytest.raises(TypeError):
        TargetView(
            TargetRequest.REQUESTED,
            dated.target.analysis,
            dated.target.leakage,
            object(),
        )


def test_legacy_entry_points_are_not_the_public_result() -> None:
    import pytics
    from pytics.profiler import compare as legacy_compare
    from pytics.profiler import profile as legacy_profile

    assert pytics.profile is legacy_profile
    assert pytics.compare is legacy_compare
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "profile_result")
    assert not hasattr(pytics, "plugin")
