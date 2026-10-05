"""TSK-041: canonical column identity, including float NaN labels."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd
import pytest

from pytics.analysis.anomaly import build_anomaly_summary
from pytics.analysis.column_label import ColumnLabelIdentity
from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import identify_column_labels
from pytics.analysis.column_label import labels_are_float_nan
from pytics.analysis.column_label import observed_labels_equal
from pytics.analysis.column_label import records_equal
from pytics.analysis.column_label import records_hash
from pytics.analysis.column_label import retain_column_label
from pytics.analysis.column_label import retained_column_label_match_key
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.findings import FindingCode
from pytics.analysis.findings import collect_profile_findings
from pytics.analysis.findings.profile import column_subjects
from pytics.analysis.relationships.collector import build_relationships_summary
from pytics.analysis.target import TargetPosition
from pytics.analysis.target import resolve_target_position
from pytics.semantics.interpretation import SemanticType
from tests.findings_support import with_labels


def _nan_numeric_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0],
            [4.0, 4.0],
            [5.0, 5.0],
            [100.0, 6.0],
        ],
        columns=[float("nan"), "other"],
    )


def test_float_nan_labels_use_one_match_key() -> None:
    identities = identify_column_labels(
        [float("nan"), np.float64("nan"), None, pd.NA, pd.NaT]
    )
    assert identities[0].match_key == identities[1].match_key == ("float_nan",)
    assert identities[0].occurrence == 1
    assert identities[1].occurrence == 2
    assert identities[2].match_key == ("none",)
    assert identities[2].match_key != identities[0].match_key
    assert identities[3].match_key != identities[4].match_key
    assert labels_are_float_nan(float("nan"), np.float64("nan")) is True
    assert labels_are_float_nan(None, float("nan")) is False
    assert labels_are_float_nan(True, float("nan")) is False
    assert observed_labels_equal(float("nan"), np.float64("nan")) is True
    assert observed_labels_equal(None, float("nan")) is False
    assert observed_labels_equal(True, 1) is False
    assert observed_labels_equal(1, 1.0) is True
    assert observed_labels_equal(2**53 + 1, float(2**53 + 1)) is False


def test_unsupported_labels_stay_outside_the_match_key() -> None:
    sentinel = object()

    class _Same:
        def __eq__(self, other: object) -> bool:
            return isinstance(other, _Same)

    class _Incomparable:
        def __eq__(self, other: object) -> bool:
            raise TypeError("incomparable")

    assert observed_labels_equal(sentinel, sentinel) is True
    assert observed_labels_equal(_Same(), _Same()) is True
    assert observed_labels_equal(_Incomparable(), _Incomparable()) is False
    assert observed_labels_equal(np.array([1]), np.array([1])) is False
    unsupported = retain_column_label(sentinel)
    assert unsupported.kind is ColumnLabelKind.UNSUPPORTED
    with pytest.raises(TypeError, match="no match key"):
        retained_column_label_match_key(unsupported)
    with pytest.raises(TypeError, match="RetainedColumnLabel"):
        retained_column_label_match_key("a")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="sequence of labels"):
        identify_column_labels("ab")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no occurrence"):
        ColumnLabelIdentity(retained=unsupported, match_key=None, occurrence=1)
    with pytest.raises(ValueError, match="has a match key"):
        ColumnLabelIdentity(
            retained=retain_column_label("a"),
            match_key=None,
            occurrence=None,
        )
    with pytest.raises(TypeError, match="RetainedColumnLabel"):
        ColumnLabelIdentity(retained=sentinel, match_key=None, occurrence=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="non-empty tuple"):
        ColumnLabelIdentity(
            retained=retain_column_label("a"),
            match_key=(),
            occurrence=1,
        )
    with pytest.raises(ValueError, match="positive int"):
        ColumnLabelIdentity(
            retained=retain_column_label("a"),
            match_key=("str", "a"),
            occurrence=0,
        )
    with pytest.raises(ValueError, match="no match key"):
        ColumnLabelIdentity(retained=unsupported, match_key=("str", "a"), occurrence=1)

    class _NumpyBool:
        def __eq__(self, other: object) -> np.bool_:
            return np.True_

    assert observed_labels_equal(_NumpyBool(), _NumpyBool()) is True
    assert observed_labels_equal(sentinel, "a") is False
    assert records_equal(sentinel, "a") is False
    assert records_equal("a", "b") is False
    with pytest.raises(TypeError, match="dataclass"):
        records_hash(sentinel)


def test_numeric_nan_label_completes_anomaly_and_relationship_analysis() -> None:
    frame = _nan_numeric_frame()
    original = tuple(frame.columns)
    analysis = analyze_dataframe(frame)
    assert tuple(frame.columns) == original
    assert all(left is right for left, right in zip(original, frame.columns))

    nan_column, other = analysis.columns
    assert nan_column.inferred.selected_type is SemanticType.NUMERIC
    assert other.inferred.selected_type is SemanticType.NUMERIC
    assert type(nan_column.label) is float
    assert math.isnan(nan_column.label)
    assert nan_column.label is original[0]

    anomaly = analysis.anomaly_analysis.numeric_univariate
    assert [record.position for record in anomaly] == [0, 1]
    assert observed_labels_equal(anomaly[0].label, float("nan"))
    assert anomaly[0].label is nan_column.label
    assert anomaly[0].observations[0].row_position == 5
    summary = build_anomaly_summary(analysis)
    assert summary.numeric_univariate == anomaly
    assert summary.numeric_univariate[0] is not anomaly[0]

    relationships = analysis.relationship_analysis.relationships
    assert len(relationships) == 1
    assert (relationships[0].left_position, relationships[0].right_position) == (0, 1)
    assert observed_labels_equal(relationships[0].left_label, float("nan"))
    assert relationships[0].right_label == "other"
    assert build_relationships_summary(analysis).relationships == relationships

    again = analyze_dataframe(_nan_numeric_frame())
    assert {anomaly[0], again.anomaly_analysis.numeric_univariate[0]} == {anomaly[0]}
    assert anomaly[0] != "amount"
    unsupported_label = dataclasses.replace(anomaly[0], label=object())
    assert hash(unsupported_label) == hash(unsupported_label)
    assert unsupported_label != anomaly[0]


def test_nan_label_can_be_the_requested_target() -> None:
    frame = _nan_numeric_frame()
    by_python = analyze_dataframe(frame, target=float("nan"))
    by_numpy = analyze_dataframe(frame, target=np.float64("nan"))
    by_lookup = analyze_dataframe(frame, target=frame.columns[0])
    assert by_python.target_analysis is not None
    assert by_numpy.target_analysis is not None
    assert by_lookup.target_analysis is not None
    assert by_python.target_analysis.position == 0
    assert by_numpy.target_analysis.position == 0
    assert by_lookup.target_analysis.position == 0
    assert observed_labels_equal(by_python.target_analysis.label, float("nan"))
    assert by_python.target_leakage is not None
    assert observed_labels_equal(by_python.target_leakage.target_label, float("nan"))
    with pytest.raises(ValueError, match="not found"):
        resolve_target_position(frame.columns, None)
    with pytest.raises(ValueError, match="not found"):
        resolve_target_position(frame.columns, pd.NA)

    duplicated = pd.DataFrame(
        [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]],
        columns=[float("nan"), np.float64("nan")],
    )
    with pytest.raises(ValueError, match="more than one column"):
        analyze_dataframe(duplicated, target=float("nan"))
    selected = analyze_dataframe(duplicated, target=TargetPosition(1))
    assert selected.target_analysis is not None
    assert selected.target_analysis.position == 1


def test_duplicate_labels_stay_distinct_through_analysis() -> None:
    frame = pd.DataFrame(
        [
            [1.0, 10.0, 100.0, 2.0],
            [2.0, 20.0, 110.0, 3.0],
            [3.0, 30.0, 120.0, 4.0],
            [4.0, 40.0, 130.0, 50.0],
        ],
        columns=["a", "a", "b", "a"],
    )
    analysis = analyze_dataframe(frame)
    subjects = column_subjects(analysis.columns)
    assert [subject.occurrence for subject in subjects] == [1, 2, 1, 3]
    assert subjects[0].key[1] == subjects[1].key[1] == subjects[3].key[1]
    assert len({subject.key for subject in subjects if subject.label.value == "a"}) == 3
    pairs = {
        (item.left_position, item.right_position)
        for item in analysis.relationship_analysis.relationships
    }
    assert pairs == {(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)}

    empty = pd.DataFrame([[None, None, None, None]], columns=["a", "a", "b", "a"])
    findings = collect_profile_findings(analyze_dataframe(empty))
    assert [finding.code for finding in findings.findings] == [
        FindingCode.EMPTY_COLUMN,
        FindingCode.EMPTY_COLUMN,
        FindingCode.EMPTY_COLUMN,
        FindingCode.EMPTY_COLUMN,
    ]
    assert [finding.subject.occurrence for finding in findings.findings] == [1, 2, 1, 3]
    assert len({finding.identity for finding in findings.findings}) == 4
    assert findings.policy.identifier == "pytics.findings/0.1"


def test_adversarial_labels_keep_the_match_key_contract() -> None:
    labels = [True, 1, 1.0, float("nan"), None, 2**53 + 1, float(2**53), "1"]
    rows = [
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        [9.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 11.0],
    ]
    frame = pd.DataFrame(rows, columns=labels)
    analysis = analyze_dataframe(frame)
    assert len(analysis.columns) == len(labels)
    subjects = column_subjects(analysis.columns)
    keys = [subject.key for subject in subjects]
    assert keys[0][1] == ("bool", True)
    assert keys[1][1] == keys[2][1] == ("number", 1)
    assert (keys[1][2], keys[2][2]) == (1, 2)
    assert keys[3][1] == ("float_nan",)
    assert keys[4][1] == ("none",)
    assert keys[5][1] == ("number", 2**53 + 1)
    assert keys[6][1] == ("number", 2**53)
    assert keys[5][1] != keys[6][1]
    assert keys[7][1] == ("str", "1")
    assert len(set(keys)) == len(labels)

    mixed = pd.DataFrame([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], columns=[1, True])
    selected = analyze_dataframe(mixed, target=1)
    assert selected.target_analysis is not None
    assert selected.target_analysis.position == 0
    assert analyze_dataframe(mixed, target=True).target_analysis.position == 1
    wide = with_labels(
        [[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]],
        [2**53 + 1, float(2**53 + 1)],
    )
    assert analyze_dataframe(wide, target=2**53 + 1).target_analysis.position == 0
    assert (
        analyze_dataframe(wide, target=float(2**53 + 1)).target_analysis.position == 1
    )


def test_reordered_compare_keeps_occurrence_identity() -> None:
    reference = pd.DataFrame(
        [
            [1.0, 10.0, 2.0, 7.0],
            [2.0, 11.0, 3.0, 8.0],
            [3.0, 12.0, 4.0, 9.0],
            [8.0, 13.0, 5.0, 14.0],
        ],
        columns=["a", "b", "a", float("nan")],
    )
    comparison = pd.DataFrame(
        [
            [7.0, 1.0, 2.0, 10.0],
            [8.0, 2.0, 3.0, 11.0],
            [9.0, 3.0, 4.0, 12.0],
            [14.0, 8.0, 5.0, 13.0],
        ],
        columns=[float("nan"), "a", "a", "b"],
    )
    result = compare_dataframes(reference, comparison)
    assert [column.alignment.status for column in result.columns] == [
        ColumnMatchStatus.MATCHED
    ] * 4
    assert [column.alignment.reference_position for column in result.columns] == [
        0,
        1,
        2,
        3,
    ]
    assert [column.alignment.comparison_position for column in result.columns] == [
        1,
        3,
        2,
        0,
    ]
    assert [column.alignment.occurrence for column in result.columns] == [1, 1, 2, 1]
    assert result.columns[3].alignment.reordered is True

    collapsed = pd.DataFrame([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], columns=[1, 1.0])
    assert [type(label) for label in collapsed.columns] == [float, float]
    numbers = with_labels([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]], [1, 1.0])
    swapped = with_labels([[2.0, 4.0, 6.0], [1.0, 3.0, 5.0]], [1.0, 1])
    aligned = compare_dataframes(numbers, swapped)
    assert [column.alignment.occurrence for column in aligned.columns] == [1, 2]
    assert [column.alignment.comparison_position for column in aligned.columns] == [
        0,
        1,
    ]
    assert aligned.columns[0].alignment.reference_label.kind.name == "INT"
    assert aligned.columns[0].alignment.comparison_label.kind.name == "FLOAT"

    separated = compare_dataframes(
        pd.DataFrame([[1.0], [2.0], [3.0]], columns=[True]),
        pd.DataFrame([[4.0], [5.0], [6.0]], columns=[1]),
    )
    assert [column.alignment.status for column in separated.columns] == [
        ColumnMatchStatus.REFERENCE_ONLY,
        ColumnMatchStatus.COMPARISON_ONLY,
    ]
    large = compare_dataframes(
        pd.DataFrame([[1.0], [2.0], [3.0]], columns=[2**53 + 1]),
        pd.DataFrame([[4.0], [5.0], [6.0]], columns=[float(2**53 + 1)]),
    )
    assert [column.alignment.status for column in large.columns] == [
        ColumnMatchStatus.REFERENCE_ONLY,
        ColumnMatchStatus.COMPARISON_ONLY,
    ]
    missing = compare_dataframes(
        pd.DataFrame([[1.0], [2.0], [3.0]], columns=[None]),
        pd.DataFrame([[4.0], [5.0], [6.0]], columns=[float("nan")]),
    )
    assert [column.alignment.status for column in missing.columns] == [
        ColumnMatchStatus.REFERENCE_ONLY,
        ColumnMatchStatus.COMPARISON_ONLY,
    ]
