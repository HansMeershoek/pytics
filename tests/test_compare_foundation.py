"""TSK-037: descriptive comparison of two dataset analyses."""

from __future__ import annotations

import dataclasses
import datetime as datetime_module
import math
import re
from fractions import Fraction
from pathlib import Path
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.compare as compare_module
import pytics.analysis.compare.collector as compare_collector
from pytics.analysis.anomaly import anomaly_analysis_for_columns
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import ColumnEvidence
from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import column_labels_equal
from pytics.analysis.column_label import retain_column_label
from pytics.analysis.compare import ColumnMatchStatus
from pytics.analysis.compare import CountComparison
from pytics.analysis.compare import DeferredComparisonFamily
from pytics.analysis.compare import DescriptiveComparisonReason
from pytics.analysis.compare import DescriptiveComparisonStatus
from pytics.analysis.compare import NumericDifference
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare import compare_dataset_analyses
from pytics.analysis.compare import directional_difference
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.duplicate import DuplicateAnalysis
from pytics.analysis.relationship import relationship_analysis_for_columns
from pytics.profiler import compare as legacy_compare
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.resolution import SemanticResolution
from tests.missing_margins import missing_analysis_for_margins

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_UUID_C = "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
_UUID_D = "6ba7b812-9dad-11d1-80b4-00c04fd430c8"

_ALLOWED_SCALARS = (
    type(None),
    bool,
    int,
    float,
    str,
    bytes,
    Fraction,
    datetime_module.date,
    datetime_module.datetime,
    datetime_module.time,
    datetime_module.timedelta,
)


class _Box:
    def __init__(self, name: str) -> None:
        self.name = name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Box) and self.name == other.name


def _with_labels(rows, labels) -> pd.DataFrame:
    """Build a frame without letting pandas coerce label scalars together.

    ``Index(..., dtype=object)`` can still rewrite ``True`` as ``1`` inside
    a tuple, and a float ``NaN`` constructed twice may not stay one object.
    Assigning an object array keeps the label values that were passed.
    """
    stored = np.empty(len(labels), dtype=object)
    for index, label in enumerate(labels):
        stored[index] = label
    frame = pd.DataFrame(rows)
    frame.columns = stored
    return frame


def _at(result, position: int, *, reference: bool = True):
    for column in result.columns:
        current = (
            column.alignment.reference_position
            if reference
            else column.alignment.comparison_position
        )
        if current == position:
            return column
    raise AssertionError(f"position {position} was not retained")


def _assert_source_free(value: object) -> None:
    seen = set()

    def walk(item: object) -> None:
        marker = id(item)
        if marker in seen:
            return
        seen.add(marker)
        if isinstance(item, (pd.DataFrame, pd.Series, pd.Index, np.ndarray)):
            raise AssertionError(f"retained a pandas or NumPy container: {type(item)}")
        if isinstance(item, np.generic):
            raise AssertionError(f"retained a NumPy scalar: {type(item)}")
        if isinstance(
            item,
            (pd.Timestamp, pd.Timedelta, pd.Interval, pd.Categorical),
        ):
            raise AssertionError(f"retained a pandas scalar: {type(item)}")
        if item is pd.NA or item is pd.NaT:
            raise AssertionError("retained a pandas missing singleton")
        if callable(item) and not isinstance(item, type):
            raise AssertionError("retained a callable")
        if isinstance(item, (dict, list, set)):
            raise AssertionError(
                f"retained a mutable mapping or sequence: {type(item)}"
            )
        if isinstance(item, tuple):
            for child in item:
                walk(child)
            return
        if dataclasses.is_dataclass(item):
            for field in dataclasses.fields(item):
                walk(getattr(item, field.name))
            return
        if isinstance(item, _ALLOWED_SCALARS) or isinstance(item, type) and False:
            return
        if isinstance(item, (int, float, str, bytes, Fraction)):
            return
        if type(item) in _ALLOWED_SCALARS or isinstance(item, datetime_module.date):
            return
        if isinstance(
            getattr(item, "__class__", None), type
        ) and item.__class__.__bases__ == (object,):
            pass
        module = type(item).__module__
        if module.startswith("enum") or isinstance(item, tuple):
            return
        if type(item).__module__ == "enum":
            return
        # Enum members report their enum module.
        if isinstance(item, (SemanticType, Confidence, PhysicalDtypeFamily)):
            return
        if type(item).__mro__[1].__name__ == "Enum":
            return
        raise AssertionError(f"unexpected retained object: {type(item)!r}")

    walk(value)


def _manual(
    columns: Tuple[ColumnAnalysis, ...],
    n_rows: int,
) -> DatasetAnalysis:
    return DatasetAnalysis(
        n_rows=n_rows,
        n_columns=len(columns),
        n_cells=n_rows * len(columns),
        columns=columns,
        missing_analysis=missing_analysis_for_margins(
            n_rows,
            tuple(column.evidence.basic.n_missing for column in columns),
        ),
        duplicate_analysis=DuplicateAnalysis(duplicate_groups=()),
        relationship_analysis=relationship_analysis_for_columns(columns, n_rows=n_rows),
        anomaly_analysis=anomaly_analysis_for_columns(columns, n_rows=n_rows),
    )


def _synthetic_column(
    position: int,
    label: object,
    *,
    n_rows: int,
    semantic_type: Optional[SemanticType],
    status: ResolutionStatus = ResolutionStatus.RESOLVED,
) -> ColumnAnalysis:
    physical = PhysicalDtype(family=PhysicalDtypeFamily.OBJECT, dtype_name="object")
    if status is ResolutionStatus.RESOLVED and semantic_type in (
        SemanticType.EMPTY,
        SemanticType.CONSTANT,
        SemanticType.BOOLEAN,
        SemanticType.DATETIME,
        SemanticType.TIMEDELTA,
    ):
        interpretation = SemanticInterpretation(
            semantic_type=semantic_type,
            confidence=Confidence.HIGH,
            source=InferenceSource.INFERRED,
            physical=physical,
            evidence=(SemanticEvidence(statement="synthetic structural"),),
        )
        resolution = SemanticResolution(
            status=status,
            reason="synthetic structural",
            selected_type=semantic_type,
            structural_interpretation=interpretation,
        )
    elif status is ResolutionStatus.RESOLVED:
        resolution = SemanticResolution(
            status=status,
            reason="synthetic candidate",
            candidates=(
                CandidateAssessment(
                    semantic_type=semantic_type,
                    disposition=CandidateDisposition.SUPPORTED,
                    supporting_evidence=(
                        SemanticEvidence(statement="synthetic support"),
                    ),
                ),
            ),
            selected_type=semantic_type,
        )
    elif status is ResolutionStatus.AMBIGUOUS:
        resolution = SemanticResolution(
            status=status,
            reason="synthetic ambiguity",
            candidates=(
                CandidateAssessment(
                    semantic_type=SemanticType.IDENTIFIER,
                    disposition=CandidateDisposition.SUPPORTED,
                    supporting_evidence=(
                        SemanticEvidence(statement="synthetic support"),
                    ),
                ),
                CandidateAssessment(
                    semantic_type=SemanticType.NUMERIC,
                    disposition=CandidateDisposition.SUPPORTED,
                    supporting_evidence=(
                        SemanticEvidence(statement="synthetic support"),
                    ),
                ),
            ),
        )
    else:
        resolution = SemanticResolution(status=status, reason="synthetic abstention")
    n_unique = 0 if semantic_type is SemanticType.EMPTY else 2
    n_missing = n_rows if semantic_type is SemanticType.EMPTY else 0
    return ColumnAnalysis(
        position=position,
        label=label,
        physical=physical,
        evidence=ColumnEvidence(
            basic=BasicColumnEvidence(
                n_total=n_rows,
                n_missing=n_missing,
                n_non_missing=n_rows - n_missing,
                n_unique_non_missing=n_unique,
            )
        ),
        inferred=InferredSemanticResult(physical=physical, resolution=resolution),
    )


def test_label_equality_separates_bool_from_int_and_aligns_exact_floats() -> None:
    assert column_labels_equal(1, True) is False
    assert column_labels_equal(True, np.bool_(True)) is True
    assert column_labels_equal(1, np.int64(1)) is True
    assert column_labels_equal(1, 1.0) is True
    assert column_labels_equal(1, "1") is False
    assert column_labels_equal(("group", 1), ("group", True)) is False
    assert column_labels_equal(("group", 1), ("group", 1.0)) is True
    assert column_labels_equal(float("nan"), np.nan) is True
    assert column_labels_equal(None, float("nan")) is False
    assert column_labels_equal(pd.NA, float("nan")) is False
    assert column_labels_equal(pd.NA, pd.NaT) is False
    assert column_labels_equal(pd.NA, None) is False
    assert column_labels_equal(float("-0.0"), 0) is True
    assert column_labels_equal(2**53 + 1, float(2**53 + 1)) is False
    assert retain_column_label(float("inf")).kind is ColumnLabelKind.UNSUPPORTED
    assert retain_column_label(_Box("a")).kind is ColumnLabelKind.UNSUPPORTED
    assert retain_column_label(_Box("a")).value is None
    retained_time = retain_column_label(pd.Timestamp("2020-01-01"))
    assert retained_time.kind is ColumnLabelKind.DATETIME
    assert retained_time.value == datetime_module.datetime(2020, 1, 1)
    assert (
        retain_column_label(pd.Timedelta(nanoseconds=1)).kind
        is ColumnLabelKind.UNSUPPORTED
    )


def test_same_columns_in_the_same_order_match_without_reordering() -> None:
    frame = pd.DataFrame({"age": [1, 2, 3], "city": ["a", "b", "a"]})
    result = compare_dataframes(frame, frame.copy())
    assert result.coverage.n_matched_columns == 2
    assert result.coverage.n_reference_only_columns == 0
    assert result.coverage.n_comparison_only_columns == 0
    assert result.coverage.n_reordered_matched_columns == 0
    age = _at(result, 0)
    assert age.alignment.status is ColumnMatchStatus.MATCHED
    assert age.alignment.reordered is False
    assert age.alignment.reference_position == 0
    assert age.alignment.comparison_position == 0
    assert age.alignment.reference_label.value == "age"
    assert age.descriptive_status is DescriptiveComparisonStatus.NUMERIC
    assert age.numeric is not None
    assert age.numeric.mean.change == 0.0
    _assert_source_free(result)


def test_reordered_columns_stay_matched() -> None:
    reference = pd.DataFrame(
        {"age": [1, 2, 4], "income": [10, 20, 30], "city": list("aba")}
    )
    comparison = pd.DataFrame(
        {"city": list("abc"), "age": [1, 2, 9], "income": [10, 20, 40]}
    )
    result = compare_dataframes(reference, comparison)
    age = _at(result, 0)
    income = _at(result, 1)
    city = _at(result, 2)
    assert (age.alignment.reference_position, age.alignment.comparison_position) == (
        0,
        1,
    )
    assert age.alignment.reordered is True
    assert (
        income.alignment.reference_position,
        income.alignment.comparison_position,
    ) == (
        1,
        2,
    )
    assert (city.alignment.reference_position, city.alignment.comparison_position) == (
        2,
        0,
    )
    assert result.coverage.n_matched_columns == 3
    assert result.coverage.n_reordered_matched_columns == 3
    assert result.coverage.n_reference_only_columns == 0
    # Independent positions from the column lists, not from the aligner.
    assert list(comparison.columns).index("age") == 1
    assert list(reference.columns).index("income") == 1


def test_added_and_removed_columns_are_explicit() -> None:
    reference = pd.DataFrame({"age": [1, 2, 3], "income": [4, 5, 6]})
    comparison = pd.DataFrame({"age": [1, 2, 8], "city": ["a", "b", "c"]})
    result = compare_dataframes(reference, comparison)
    removed = _at(result, 1)
    added = _at(result, 1, reference=False)
    assert removed.alignment.status is ColumnMatchStatus.REFERENCE_ONLY
    assert removed.alignment.reference_label.value == "income"
    assert removed.alignment.comparison_position is None
    assert removed.descriptive_status is DescriptiveComparisonStatus.INAPPLICABLE
    assert removed.descriptive_reason is DescriptiveComparisonReason.UNMATCHED_COLUMN
    assert removed.numeric is None
    assert added.alignment.status is ColumnMatchStatus.COMPARISON_ONLY
    assert added.alignment.comparison_label.value == "city"
    assert added.alignment.reference_position is None
    assert result.coverage.n_reference_only_columns == 1
    assert result.coverage.n_comparison_only_columns == 1
    assert [column.alignment.status for column in result.columns] == [
        ColumnMatchStatus.MATCHED,
        ColumnMatchStatus.REFERENCE_ONLY,
        ColumnMatchStatus.COMPARISON_ONLY,
    ]


def test_add_remove_and_reorder_together() -> None:
    reference = pd.DataFrame(
        {"age": [1, 2, 3], "income": [4, 5, 6], "city": list("abc")}
    )
    comparison = pd.DataFrame(
        {"city": list("abd"), "score": [1.0, 2.0, 3.0], "age": [3, 2, 1]}
    )
    result = compare_dataframes(reference, comparison)
    expected = {
        "age": (0, 2),
        "income": (1, None),
        "city": (2, 0),
        "score": (None, 1),
    }
    found = {}
    for column in result.columns:
        label = column.alignment.reference_label or column.alignment.comparison_label
        found[label.value] = (
            column.alignment.reference_position,
            column.alignment.comparison_position,
        )
    assert found == expected
    assert _at(result, 0).alignment.reordered is True
    assert _at(result, 2).alignment.reordered is True


def test_duplicate_labels_match_by_occurrence_not_by_first_hit() -> None:
    reference = pd.DataFrame([[1, 10, 7], [2, 20, 8]], columns=["x", "x", "y"])
    comparison = pd.DataFrame([[3, 9, 11], [4, 8, 21]], columns=["x", "y", "x"])
    result = compare_dataframes(reference, comparison)
    first = _at(result, 0)
    second = _at(result, 1)
    third = _at(result, 2)
    assert first.alignment.occurrence == 1
    assert (
        first.alignment.reference_position,
        first.alignment.comparison_position,
    ) == (
        0,
        0,
    )
    assert first.alignment.reordered is False
    assert second.alignment.occurrence == 2
    assert (
        second.alignment.reference_position,
        second.alignment.comparison_position,
    ) == (
        1,
        2,
    )
    assert second.alignment.reordered is True
    assert third.alignment.reference_label.value == "y"
    assert (
        third.alignment.reference_position,
        third.alignment.comparison_position,
    ) == (
        2,
        1,
    )
    # The second x is not treated as removed and added.
    assert result.coverage.n_reference_only_columns == 0
    assert result.coverage.n_comparison_only_columns == 0
    assert compare_dataframes(reference, comparison) == result


def test_duplicate_labels_reordered_on_the_comparison_only() -> None:
    reference = pd.DataFrame([[1, 2]], columns=["x", "x"])
    comparison = pd.DataFrame([[9, 8]], columns=["x", "x"])
    result = compare_dataframes(reference, comparison)
    assert [column.alignment.occurrence for column in result.columns] == [1, 2]
    assert [column.alignment.comparison_position for column in result.columns] == [0, 1]


def test_non_string_and_tuple_labels_are_not_stringified() -> None:
    reference = pd.DataFrame([[1, 2, 3]], columns=[42, ("group", "value"), b"raw"])
    comparison = pd.DataFrame(
        [[4, 5, 6]],
        columns=[("group", "value"), b"raw", 42],
    )
    result = compare_dataframes(reference, comparison)
    number = _at(result, 0)
    pair = _at(result, 1)
    raw = _at(result, 2)
    assert number.alignment.reference_label.kind is ColumnLabelKind.INT
    assert number.alignment.reference_label.value == 42
    assert not isinstance(number.alignment.reference_label.value, str)
    assert pair.alignment.reference_label.kind is ColumnLabelKind.TUPLE
    assert pair.alignment.reference_label.value[0].value == "group"
    assert pair.alignment.reference_label.value[1].value == "value"
    assert raw.alignment.reference_label.kind is ColumnLabelKind.BYTES
    assert raw.alignment.reference_label.value == b"raw"
    assert number.alignment.comparison_position == 2
    assert pair.alignment.comparison_position == 0
    assert raw.alignment.comparison_position == 1
    _assert_source_free(result)


def test_bool_int_and_float_labels_do_not_collapse_together() -> None:
    reference = pd.DataFrame([[1, 2]], columns=[1, True])
    comparison = pd.DataFrame([[4, 3]], columns=[True, 1])
    result = compare_dataframes(reference, comparison)
    integer = _at(result, 0)
    boolean = _at(result, 1)
    assert integer.alignment.comparison_position == 1
    assert integer.alignment.reference_label.kind is ColumnLabelKind.INT
    assert boolean.alignment.comparison_position == 0
    assert boolean.alignment.reference_label.kind is ColumnLabelKind.BOOL
    assert result.coverage.n_matched_columns == 2

    exact = compare_dataframes(
        _with_labels([[1], [2], [3]], [1]),
        _with_labels([[4], [5], [6]], [1.0]),
    )
    matched = exact.columns[0]
    assert matched.alignment.status is ColumnMatchStatus.MATCHED
    assert matched.alignment.reference_label.kind is ColumnLabelKind.INT
    assert matched.alignment.comparison_label.kind is ColumnLabelKind.FLOAT
    assert matched.alignment.comparison_label.value == 1.0

    both = compare_dataframes(
        _with_labels([[1, 2]], [1, 1.0]),
        _with_labels([[3, 4]], [1.0, 1]),
    )
    # 1 and 1.0 share one numeric identity, so they are two occurrences.
    assert [column.alignment.occurrence for column in both.columns] == [1, 2]
    assert both.columns[0].alignment.reference_label.kind is ColumnLabelKind.INT
    assert both.columns[0].alignment.comparison_label.kind is ColumnLabelKind.FLOAT
    assert both.columns[1].alignment.reference_label.kind is ColumnLabelKind.FLOAT
    assert both.columns[1].alignment.comparison_label.kind is ColumnLabelKind.INT
    assert both.columns[1].alignment.comparison_position == 1


def test_tuple_element_bool_does_not_match_int() -> None:
    reference = _with_labels([[1, 2]], [("a", 1), ("a", True)])
    comparison = _with_labels([[3, 4]], [("a", True), ("a", 1)])
    result = compare_dataframes(reference, comparison)
    assert _at(result, 0).alignment.comparison_position == 1
    assert _at(result, 1).alignment.comparison_position == 0
    assert result.coverage.n_matched_columns == 2


def test_missing_like_labels_stay_distinct_and_nan_occurrences_match() -> None:
    reference = _with_labels([[1, 2, 3, 4]], [None, np.nan, pd.NA, pd.NaT])
    comparison = _with_labels([[5, 6, 7, 8]], [np.nan, None, pd.NaT, pd.NA])
    result = compare_dataframes(reference, comparison)
    kinds = [
        column.alignment.reference_label.kind
        for column in result.columns
        if column.alignment.reference_label is not None
    ]
    assert kinds == [
        ColumnLabelKind.NONE,
        ColumnLabelKind.FLOAT_NAN,
        ColumnLabelKind.PANDAS_NA,
        ColumnLabelKind.PANDAS_NAT,
    ]
    assert _at(result, 0).alignment.comparison_position == 1
    assert _at(result, 1).alignment.comparison_position == 0
    assert _at(result, 2).alignment.comparison_position == 3
    assert _at(result, 3).alignment.comparison_position == 2
    repeated = compare_dataframes(
        _with_labels([[1, 2]], [np.nan, np.nan]),
        _with_labels([[3]], [np.nan]),
    )
    assert repeated.columns[0].alignment.status is ColumnMatchStatus.MATCHED
    assert repeated.columns[0].alignment.occurrence == 1
    assert repeated.columns[1].alignment.status is ColumnMatchStatus.REFERENCE_ONLY
    assert repeated.columns[1].alignment.occurrence == 2
    _assert_source_free(result)


def test_unsupported_labels_are_not_matched_or_stored() -> None:
    reference = pd.DataFrame([[1]], columns=[_Box("same")])
    comparison = pd.DataFrame([[2]], columns=[_Box("same")])
    result = compare_dataframes(reference, comparison)
    assert result.coverage.n_matched_columns == 0
    assert result.columns[0].alignment.status is ColumnMatchStatus.REFERENCE_ONLY
    assert result.columns[0].alignment.occurrence is None
    assert (
        result.columns[0].alignment.reference_label.kind is ColumnLabelKind.UNSUPPORTED
    )
    assert result.columns[1].alignment.status is ColumnMatchStatus.COMPARISON_ONLY
    _assert_source_free(result)
    assert not any(isinstance(item, _Box) for item in _walk_objects(result))


def test_schema_transitions_keep_dtype_and_semantics_apart() -> None:
    reference = pd.DataFrame(
        {
            "measure": pd.Series([1, 2, 4], dtype="int64"),
            "flag": pd.Series([True, False, True]),
            "steady": pd.Series([5, 5, 5], dtype="int64"),
            "group": pd.Series(
                pd.Categorical(["a", "b", "a"], categories=["a", "b"], ordered=False)
            ),
        }
    )
    comparison = pd.DataFrame(
        {
            "measure": pd.Series([1.0, 2.0, 8.0], dtype="float64"),
            "flag": pd.Series([1, 0, 1], dtype="int64"),
            "steady": pd.Series([5, 6, 7], dtype="int64"),
            "group": pd.Series(
                pd.Categorical(["a", "b", "a"], categories=["a", "b"], ordered=True)
            ),
        }
    )
    result = compare_dataframes(reference, comparison)
    measure = _at(result, 0)
    flag = _at(result, 1)
    steady = _at(result, 2)
    group = _at(result, 3)

    assert measure.physical.family_changed is True
    assert measure.physical.reference.family is PhysicalDtypeFamily.INTEGER
    assert measure.physical.comparison.family is PhysicalDtypeFamily.FLOATING
    assert measure.semantic.selected_type_changed is False
    assert measure.semantic.reference.selected_type is SemanticType.NUMERIC
    assert measure.descriptive_status is DescriptiveComparisonStatus.NUMERIC

    assert flag.physical.family_changed is True
    assert flag.semantic.selected_type_changed is True
    assert flag.semantic.reference.selected_type is SemanticType.BOOLEAN
    assert flag.semantic.comparison.selected_type is SemanticType.NUMERIC
    assert flag.semantic.reference.confidence is Confidence.HIGH
    assert flag.semantic.comparison.confidence is None
    assert flag.semantic.confidence_changed is True
    assert flag.descriptive_reason is DescriptiveComparisonReason.SEMANTIC_MISMATCH
    assert flag.numeric is None
    assert flag.boolean is None

    assert steady.physical.family_changed is False
    assert steady.physical.dtype_name_changed is False
    assert steady.semantic.selected_type_changed is True
    assert steady.semantic.reference.selected_type is SemanticType.CONSTANT
    assert steady.semantic.comparison.selected_type is SemanticType.NUMERIC
    assert steady.descriptive_reason is DescriptiveComparisonReason.SEMANTIC_MISMATCH

    assert group.physical.family_changed is False
    assert group.physical.categorical_ordered_changed is True
    assert group.semantic.selected_type_changed is False
    assert group.semantic.reference.selected_type is SemanticType.CATEGORICAL
    assert group.descriptive_status is DescriptiveComparisonStatus.CATEGORICAL
    assert group.categorical.ordered_flag_changed is True
    assert group.semantic.confidence_changed is False
    assert result.coverage.n_selected_type_changed_columns == 2
    assert result.coverage.n_same_selected_type_columns == 2


def test_confidence_transition_is_not_a_number() -> None:
    reference = pd.DataFrame({"flag": [True, False, True, False]})
    comparison = pd.DataFrame({"flag": [True, False, True, True]})
    result = compare_dataframes(reference, comparison)
    semantic = result.columns[0].semantic
    assert semantic.reference.confidence is Confidence.HIGH
    assert semantic.comparison.confidence is Confidence.HIGH
    assert semantic.confidence_changed is False
    assert not hasattr(semantic, "confidence_delta")


def test_numeric_descriptive_changes_are_directional_and_reused() -> None:
    reference = pd.DataFrame(
        {
            "amount": [1.0, 2.0, 3.0, 4.0],
            "spread": [1.0, 1.0, 1.0, np.inf],
        }
    )
    comparison = pd.DataFrame(
        {
            "amount": [1.0, 2.0, np.nan, 10.0],
            "spread": [5.0, -np.inf, np.inf, np.inf],
        }
    )
    reference_analysis = analyze_dataframe(reference)
    comparison_analysis = analyze_dataframe(comparison)
    result = compare_dataset_analyses(reference_analysis, comparison_analysis)
    amount = result.columns[0].numeric
    reference_profile = reference_analysis.columns[0].numeric_analysis
    comparison_profile = comparison_analysis.columns[0].numeric_analysis
    assert amount.mean.reference == reference_profile.mean
    assert amount.mean.comparison == comparison_profile.mean
    assert amount.mean.change == comparison_profile.mean - reference_profile.mean
    assert amount.mean.change > 0
    assert amount.median.change == comparison_profile.median - reference_profile.median
    assert (
        amount.minimum.change == comparison_profile.minimum - reference_profile.minimum
    )
    assert amount.finite_count.reference == 4
    assert amount.finite_count.comparison == 3
    assert amount.finite_count.change == -1
    assert amount.missing_count.change == 1
    assert (
        amount.missing_count.change
        == result.columns[0].missingness.missing_count.change
    )
    assert amount.standard_deviation.change == (
        comparison_profile.standard_deviation - reference_profile.standard_deviation
    )
    spread = result.columns[1].numeric
    assert spread.positive_infinity_count.reference == 1
    assert spread.positive_infinity_count.comparison == 2
    assert spread.positive_infinity_count.change == 1
    assert spread.negative_infinity_count.change == 1 - 0
    assert spread.finite_count.change == 1 - 3


def test_numeric_unavailable_statistics_stay_distinct_from_zero() -> None:
    reference = pd.DataFrame({"amount": [10.0, np.inf]})
    comparison = pd.DataFrame({"amount": [12.0, 14.0]})
    result = compare_dataframes(reference, comparison)
    deviation = result.columns[0].numeric.standard_deviation
    assert deviation.reference is None
    assert deviation.comparison is not None
    assert deviation.change is None
    assert deviation.change != 0

    empty = compare_dataframes(
        pd.DataFrame({"amount": [np.inf, -np.inf]}),
        pd.DataFrame({"amount": [np.inf, -np.inf]}),
    )
    mean = empty.columns[0].numeric.mean
    assert mean.reference is None
    assert mean.comparison is None
    assert mean.change is None
    assert empty.columns[0].numeric.finite_count.change == 0


def test_numeric_integer_differences_stay_exact() -> None:
    huge = 2**62
    reference = pd.DataFrame({"amount": pd.Series([huge, huge + 2], dtype="int64")})
    comparison = pd.DataFrame(
        {"amount": pd.Series([huge + 5, huge + 9], dtype="int64")}
    )
    result = compare_dataframes(reference, comparison)
    minimum = result.columns[0].numeric.minimum
    assert minimum.reference == huge
    assert minimum.comparison == huge + 5
    assert type(minimum.change) is int
    assert minimum.change == 5
    maximum = result.columns[0].numeric.maximum
    assert type(maximum.change) is int
    assert maximum.change == (huge + 9) - (huge + 2)

    lower_left = np.uint64(2**64 - 9)
    lower_right = np.uint64(2**64 - 8)
    upper_left = np.uint64(2**64 - 2)
    upper_right = np.uint64(2**64 - 1)
    unsigned = compare_dataframes(
        pd.DataFrame({"amount": pd.Series([lower_left, lower_right], dtype="uint64")}),
        pd.DataFrame({"amount": pd.Series([upper_left, upper_right], dtype="uint64")}),
    )
    unsigned_min = unsigned.columns[0].numeric.minimum
    assert unsigned_min.reference == int(lower_left)
    assert unsigned_min.comparison == int(upper_left)
    assert type(unsigned_min.change) is int
    assert unsigned_min.change == int(upper_left) - int(lower_left)
    unsigned_max = unsigned.columns[0].numeric.maximum
    assert type(unsigned_max.change) is int
    assert unsigned_max.change == int(upper_right) - int(lower_right)


def test_numeric_float_overflow_does_not_become_infinity() -> None:
    reference = pd.DataFrame({"amount": [1.5e308, 1.6e308]})
    comparison = pd.DataFrame({"amount": [-1.5e308, -1.6e308]})
    reference_mean = analyze_dataframe(reference).columns[0].numeric_analysis.mean
    comparison_mean = analyze_dataframe(comparison).columns[0].numeric_analysis.mean
    assert math.isinf(comparison_mean - reference_mean)
    result = compare_dataframes(reference, comparison)
    mean = result.columns[0].numeric.mean
    assert mean.reference == reference_mean
    assert mean.comparison == comparison_mean
    assert mean.change is None


def test_mixed_int_and_float_difference_stays_exact() -> None:
    result = compare_dataframes(
        pd.DataFrame({"amount": [1, 3, 5]}),
        pd.DataFrame({"amount": [1.5, 3.5, 5.5]}),
    )
    minimum = result.columns[0].numeric.minimum
    assert minimum.reference == 1
    assert minimum.comparison == 1.5
    assert minimum.change == Fraction(1, 2)
    assert directional_difference(1.5, 1) == Fraction(1, 2)
    assert directional_difference(2**100, 2**100 - 3) == 3
    assert directional_difference(1e308, -1e308) is None
    assert directional_difference(None, 1.0) is None


def test_categorical_level_partition_is_typed_and_exact() -> None:
    reference = pd.DataFrame(
        {
            "group": pd.Categorical(
                ["a", "a", "b", "c"],
                categories=["a", "b", "c", "unused"],
                ordered=True,
            )
        }
    )
    comparison = pd.DataFrame(
        {
            "group": pd.Categorical(
                ["b", "b", "b", "d"],
                categories=["b", "a", "d", "unused"],
                ordered=True,
            )
        }
    )
    result = compare_dataframes(reference, comparison)
    categorical = result.columns[0].categorical
    assert categorical.n_observed.reference == 3
    assert categorical.n_observed.comparison == 2
    assert categorical.n_observed.change == -1
    shared = {level.value: level for level in categorical.shared_levels}
    assert set(shared) == {"b"}
    assert shared["b"].reference_count == 1
    assert shared["b"].comparison_count == 3
    assert shared["b"].count_change == 2
    reference_only = categorical.reference_only_levels
    comparison_only = categorical.comparison_only_levels
    assert [level.value for level in reference_only] == ["a", "c"]
    assert reference_only[0].reference_count == 2
    assert reference_only[0].comparison_count is None
    assert reference_only[0].count_change is None
    assert [level.value for level in comparison_only] == ["d"]
    assert comparison_only[0].comparison_count == 1
    assert "unused" not in shared
    assert all(level.value != "unused" for level in reference_only + comparison_only)
    assert categorical.observed_sequences_equal is False
    assert [level.value for level in categorical.shared_levels] == ["b"]
    reference_counts = {"a": 2, "b": 1, "c": 1}
    comparison_counts = {"b": 3, "d": 1}
    assert set(reference_counts) & set(comparison_counts) == set(shared)
    assert set(reference_counts) - set(comparison_counts) == {"a", "c"}
    assert set(comparison_counts) - set(reference_counts) == {"d"}
    assert type(categorical.shared_levels[0].value) is str
    _assert_source_free(result)


def test_reordered_declared_categories_do_not_invent_unused_levels() -> None:
    reference = pd.DataFrame(
        {
            "group": pd.Categorical(
                ["a", "b", "a"],
                categories=["a", "b", "c"],
                ordered=True,
            )
        }
    )
    comparison = pd.DataFrame(
        {
            "group": pd.Categorical(
                ["a", "b", "a"],
                categories=["b", "a", "c"],
                ordered=True,
            )
        }
    )
    result = compare_dataframes(reference, comparison)
    categorical = result.columns[0].categorical
    assert categorical.reference_only_levels == ()
    assert categorical.comparison_only_levels == ()
    assert [level.value for level in categorical.shared_levels] == ["a", "b"]
    assert categorical.observed_sequences_equal is False
    assert categorical.ordered_flag_changed is False
    assert all(
        level.value != "c"
        for level in categorical.shared_levels
        + categorical.reference_only_levels
        + categorical.comparison_only_levels
    )


def test_high_cardinality_partition_matches_an_independent_set() -> None:
    reference_levels = [f"L{index}" for index in range(1000)]
    comparison_levels = reference_levels[1:] + ["new"]
    reference = pd.DataFrame(
        {"group": pd.Categorical(reference_levels, categories=reference_levels)}
    )
    comparison = pd.DataFrame(
        {"group": pd.Categorical(comparison_levels, categories=comparison_levels)}
    )
    result = compare_dataframes(reference, comparison)
    categorical = result.columns[0].categorical
    shared = {level.value for level in categorical.shared_levels}
    reference_only = {level.value for level in categorical.reference_only_levels}
    comparison_only = {level.value for level in categorical.comparison_only_levels}
    assert shared == set(reference_levels[1:])
    assert reference_only == {"L0"}
    assert comparison_only == {"new"}
    assert len(shared) + len(reference_only) == 1000
    assert len(shared) + len(comparison_only) == 1000


def test_boolean_comparison_is_descriptive_only() -> None:
    reference = pd.DataFrame({"flag": [True, True, False, False, False]})
    comparison = pd.DataFrame(
        {"flag": pd.Series([True, True, True, False, False, pd.NA], dtype="boolean")}
    )
    result = compare_dataframes(reference, comparison)
    boolean = result.columns[0].boolean
    assert result.columns[0].descriptive_status is DescriptiveComparisonStatus.BOOLEAN
    assert boolean.true_count.reference == 2
    assert boolean.true_count.comparison == 3
    assert boolean.true_count.change == 1
    assert boolean.false_count.change == 2 - 3
    assert boolean.missing_count.change == 1
    expected_true = (3 / 5) - (2 / 5)
    assert boolean.true_proportion.change == expected_true
    assert boolean.true_proportion.reference == 2 / 5
    assert boolean.true_proportion.comparison == 3 / 5
    assert not hasattr(boolean, "p_value")
    assert not hasattr(boolean, "drift")
    unchanged = compare_dataframes(reference, reference.copy())
    assert unchanged.columns[0].boolean.true_proportion.change == 0.0


def test_specialized_comparison_is_withheld_for_unsupported_semantics() -> None:
    reference = pd.DataFrame(
        {
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C, _UUID_D], dtype="string"),
            "when": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
            ),
            "span": pd.to_timedelta(["1 days", "2 days", "3 days", "4 days"]),
            "blank": pd.Series([None, None, None, None], dtype="object"),
            "steady": pd.Series([4, 4, 4, 4], dtype="int64"),
            "note": pd.Series(["alpha", "beta", "gamma", "delta"], dtype="string"),
            "amount": [1, 2, 3, 4],
        }
    )
    comparison = pd.DataFrame(
        {
            "code": pd.Series([_UUID_A, _UUID_A, _UUID_B, _UUID_D], dtype="string"),
            "when": pd.to_datetime(
                ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"]
            ),
            "span": pd.to_timedelta(["4 days", "5 days", "6 days", "7 days"]),
            "blank": pd.Series([None, None, None, None], dtype="object"),
            "steady": pd.Series([4, 4, 4, 4], dtype="int64"),
            "note": pd.Series(["alpha", "beta", "delta", "epsilon"], dtype="string"),
            "amount": pd.Series(pd.Categorical(["a", "b", "a", "b"])),
        }
    )
    result = compare_dataframes(reference, comparison)
    expected = {
        0: DescriptiveComparisonReason.IDENTIFIER,
        1: DescriptiveComparisonReason.DATETIME,
        2: DescriptiveComparisonReason.TIMEDELTA,
        3: DescriptiveComparisonReason.EMPTY,
        4: DescriptiveComparisonReason.CONSTANT,
        5: DescriptiveComparisonReason.UNRESOLVED,
        6: DescriptiveComparisonReason.SEMANTIC_MISMATCH,
    }
    for position, reason in expected.items():
        column = _at(result, position)
        assert column.descriptive_status is DescriptiveComparisonStatus.INAPPLICABLE
        assert column.descriptive_reason is reason
        assert column.numeric is None
        assert column.categorical is None
        assert column.boolean is None
    assert result.coverage.n_numeric_descriptive_comparisons == 0
    assert result.coverage.n_inapplicable_descriptive_comparisons == 7


def test_text_ambiguous_and_missing_profile_are_explicit() -> None:
    text_reference = _manual(
        (_synthetic_column(0, "body", n_rows=3, semantic_type=SemanticType.TEXT),),
        3,
    )
    text_comparison = _manual(
        (_synthetic_column(0, "body", n_rows=3, semantic_type=SemanticType.TEXT),),
        3,
    )
    text = compare_dataset_analyses(text_reference, text_comparison)
    assert text.columns[0].descriptive_reason is DescriptiveComparisonReason.TEXT
    assert text.columns[0].numeric is None

    ambiguous = compare_dataset_analyses(
        _manual(
            (
                _synthetic_column(
                    0,
                    "mixed",
                    n_rows=3,
                    semantic_type=None,
                    status=ResolutionStatus.AMBIGUOUS,
                ),
            ),
            3,
        ),
        _manual(
            (
                _synthetic_column(
                    0,
                    "mixed",
                    n_rows=3,
                    semantic_type=None,
                    status=ResolutionStatus.AMBIGUOUS,
                ),
            ),
            3,
        ),
    )
    assert (
        ambiguous.columns[0].descriptive_reason is DescriptiveComparisonReason.AMBIGUOUS
    )
    assert ambiguous.coverage.n_both_unresolved_columns == 1

    mismatched_status = compare_dataset_analyses(
        _manual(
            (
                _synthetic_column(
                    0,
                    "mixed",
                    n_rows=3,
                    semantic_type=None,
                    status=ResolutionStatus.AMBIGUOUS,
                ),
            ),
            3,
        ),
        _manual(
            (
                _synthetic_column(
                    0,
                    "mixed",
                    n_rows=3,
                    semantic_type=None,
                    status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
                ),
            ),
            3,
        ),
    )
    assert (
        mismatched_status.columns[0].descriptive_reason
        is DescriptiveComparisonReason.SEMANTIC_MISMATCH
    )
    assert mismatched_status.coverage.n_selected_type_changed_columns == 1

    absent = compare_dataset_analyses(
        _manual(
            (
                _synthetic_column(
                    0, "amount", n_rows=3, semantic_type=SemanticType.NUMERIC
                ),
            ),
            3,
        ),
        _manual(
            (
                _synthetic_column(
                    0, "amount", n_rows=3, semantic_type=SemanticType.NUMERIC
                ),
            ),
            3,
        ),
    )
    assert (
        absent.columns[0].descriptive_status is DescriptiveComparisonStatus.UNAVAILABLE
    )
    assert (
        absent.columns[0].descriptive_reason
        is DescriptiveComparisonReason.PROFILE_ABSENT
    )
    assert absent.columns[0].numeric is None
    assert absent.coverage.n_unavailable_descriptive_comparisons == 1


def test_overview_counts_missingness_and_duplicates_without_matching_rows() -> None:
    reference = pd.DataFrame(
        {
            "amount": [1, 2, None, 1],
            "flag": [True, False, True, True],
            "code": pd.Series([_UUID_A, _UUID_B, _UUID_C, _UUID_A], dtype="string"),
        }
    )
    comparison = pd.DataFrame(
        {
            "amount": [1, 2, 3, 4, 5],
            "flag": [True, True, False, False, True],
            "code": pd.Series(
                [_UUID_A, _UUID_B, _UUID_C, _UUID_D, _UUID_A],
                dtype="string",
            ),
            "note": ["a", "a", "a", "a", "a"],
        }
    )
    result = compare_dataframes(reference, comparison)
    overview = result.overview
    assert overview.n_rows.reference == 4
    assert overview.n_rows.comparison == 5
    assert overview.n_rows.change == 1
    assert overview.n_columns.change == 1
    assert overview.n_cells.change == 5 * 4 - 4 * 3
    assert overview.n_missing_cells.reference == 1
    assert overview.n_missing_cells.comparison == 0
    assert overview.n_missing_cells.change == -1
    assert overview.n_non_missing_cells.change == overview.n_cells.change - (
        overview.n_missing_cells.change
    )
    assert overview.n_complete_rows.reference == 3
    assert overview.n_rows_with_missing.reference == 1
    assert overview.n_rows_with_missing.comparison == 0
    assert overview.n_unique_rows.reference == 3
    assert overview.n_excess_duplicate_rows.reference == 1
    assert overview.n_duplicate_groups.reference == 1
    assert overview.n_duplicate_groups.comparison == 0
    assert overview.n_duplicate_groups.change == -1
    assert overview.empty_column_count.change == 0
    assert overview.constant_column_count.comparison == 1
    assert overview.constant_column_count.change == 1
    assert overview.identifier_column_count.reference == 1
    assert overview.identifier_column_count.comparison == 1
    counts = {
        item.semantic_type: (item.reference_count, item.comparison_count, item.change)
        for item in overview.semantic_type_counts
    }
    assert (
        counts[SemanticType.NUMERIC][2]
        == counts[SemanticType.NUMERIC][1] - counts[SemanticType.NUMERIC][0]
    )
    assert counts[SemanticType.CONSTANT] == (0, 1, 1)
    assert not any(isinstance(item, tuple) and False for item in ())
    assert not hasattr(result, "duplicate_groups")
    _assert_source_free(result)


def test_row_indexes_do_not_pair_observations() -> None:
    values = pd.DataFrame({"amount": [1, 2, 3], "flag": [True, False, True]})
    same = values.copy()
    shifted = values.copy()
    shifted.index = [10, 20, 30]
    duplicated = values.copy()
    duplicated.index = [1, 1, 1]
    overlapping = values.copy()
    overlapping.index = [0, 5, 2]
    baseline = compare_dataframes(values, same)
    assert compare_dataframes(values, shifted) == baseline
    assert compare_dataframes(values, duplicated) == baseline
    assert compare_dataframes(values, overlapping) == baseline
    longer = pd.concat([values, values.iloc[[0]]], ignore_index=True)
    changed = compare_dataframes(values, longer)
    assert changed.overview.n_rows.change == 1
    assert changed is not baseline
    retained_ints = [
        item
        for item in _walk_objects(baseline)
        if type(item) is int and item in (10, 20, 30)
    ]
    assert retained_ints == []


def test_naming_a_target_does_not_change_the_comparison(monkeypatch) -> None:
    frame = pd.DataFrame({"amount": [1, 2, 3, 4], "flag": [True, False, True, False]})
    plain_reference = analyze_dataframe(frame)
    plain_comparison = analyze_dataframe(frame.iloc[:, ::-1])
    targeted_reference = analyze_dataframe(frame, target="amount")
    targeted_comparison = analyze_dataframe(frame.iloc[:, ::-1], target="flag")
    assert plain_reference.target_analysis is None
    assert targeted_reference.target_analysis is not None

    def fail(*args, **kwargs):
        raise AssertionError("compare reanalyzed a frame")

    monkeypatch.setattr(compare_collector, "analyze_dataframe", fail)
    plain = compare_dataset_analyses(plain_reference, plain_comparison)
    targeted = compare_dataset_analyses(targeted_reference, targeted_comparison)
    assert plain == targeted
    assert plain.target is None
    assert (
        DeferredComparisonFamily.ANOMALY_COMPARISON in plain.coverage.deferred_families
    )


def test_source_frames_and_analyses_are_unchanged() -> None:
    reference = pd.DataFrame({"amount": [1, None, 3], "city": ["a", "b", "a"]})
    comparison = pd.DataFrame({"city": ["a", "c", "a"], "amount": [1, 2, 4]})
    reference_before = reference.copy(deep=True)
    comparison_before = comparison.copy(deep=True)
    reference_analysis = analyze_dataframe(reference)
    comparison_analysis = analyze_dataframe(comparison)
    columns_id = reference_analysis.columns
    compare_dataset_analyses(reference_analysis, comparison_analysis)
    compare_dataframes(reference, comparison)
    pd.testing.assert_frame_equal(reference, reference_before)
    pd.testing.assert_frame_equal(comparison, comparison_before)
    assert reference_analysis.columns is columns_id


def test_result_has_no_score_severity_or_unselected_drift_method() -> None:
    result = compare_dataframes(
        pd.DataFrame({"amount": [1, 2, 3]}),
        pd.DataFrame({"amount": [1, 2, 9]}),
    )
    names = {field.name for field in dataclasses.fields(result)}
    assert "score" not in names
    assert "severity" not in names
    package = Path(compare_module.__file__).parent
    lowered = "".join(
        path.read_text(encoding="utf-8").lower() for path in package.glob("*.py")
    )
    for banned in (
        "jensen",
        "hellinger",
        "mannwhitney",
        "population_stability",
        "severity =",
        "significant",
    ):
        assert banned not in lowered
    assert re.search(r"\bpsi\b", lowered) is None
    assert result.coverage.deferred_families[0] is (
        DeferredComparisonFamily.ANOMALY_COMPARISON
    )
    assert "statistical_distribution_drift" not in {
        family.value for family in DeferredComparisonFamily
    }


def test_legacy_public_compare_is_not_replaced() -> None:
    assert pytics.compare is legacy_compare
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "compare_dataframes")


def test_wide_unique_labels_align_after_reorder_add_and_remove() -> None:
    labels = [f"c{index}" for index in range(60)]
    reference = pd.DataFrame({label: ["a", "b"] for label in labels})
    kept = labels[5:] + labels[:5]
    kept = [label for label in kept if label not in {"c1", "c2"}]
    comparison = pd.DataFrame({label: ["a", "c"] for label in kept})
    comparison["added"] = ["z", "z"]
    result = compare_dataframes(reference, comparison)
    positions = {label: index for index, label in enumerate(reference.columns)}
    comparison_positions = {
        label: index for index, label in enumerate(comparison.columns)
    }
    for column in result.columns:
        if column.alignment.status is ColumnMatchStatus.MATCHED:
            label = column.alignment.reference_label.value
            assert column.alignment.reference_position == positions[label]
            assert column.alignment.comparison_position == comparison_positions[label]
        elif column.alignment.status is ColumnMatchStatus.REFERENCE_ONLY:
            assert column.alignment.reference_label.value in {"c1", "c2"}
        else:
            assert column.alignment.comparison_label.value == "added"
    assert result.coverage.n_matched_columns == 58
    assert result.coverage.n_reference_only_columns == 2
    assert result.coverage.n_comparison_only_columns == 1


def test_zero_row_missing_proportion_is_not_zero() -> None:
    frame = pd.DataFrame({"amount": pd.Series(dtype="float64")})
    result = compare_dataframes(frame, frame.copy())
    proportion = result.columns[0].missingness.missing_proportion
    assert proportion.reference is None
    assert proportion.comparison is None
    assert proportion.change is None
    assert result.columns[0].descriptive_reason is DescriptiveComparisonReason.EMPTY


def test_temporal_and_float_labels_keep_their_kinds() -> None:
    day = datetime_module.date(2020, 1, 2)
    clock = datetime_module.time(3, 4, 5)
    moment = datetime_module.datetime(2020, 1, 2, 3, 4, 5)
    duration = pd.Timedelta(days=1, seconds=2)
    reference = _with_labels([[1, 2, 3, 4]], [day, clock, moment, duration])
    comparison = _with_labels([[5, 6, 7, 8]], [duration, moment, clock, day])
    result = compare_dataframes(reference, comparison)
    assert _at(result, 0).alignment.reference_label.kind is ColumnLabelKind.DATE
    assert _at(result, 0).alignment.comparison_position == 3
    assert _at(result, 1).alignment.reference_label.kind is ColumnLabelKind.TIME
    assert _at(result, 1).alignment.comparison_position == 2
    assert _at(result, 2).alignment.reference_label.kind is ColumnLabelKind.DATETIME
    assert _at(result, 2).alignment.reference_label.value == moment
    assert _at(result, 3).alignment.reference_label.kind is ColumnLabelKind.TIMEDELTA
    assert _at(result, 3).alignment.comparison_position == 0
    assert retain_column_label(np.float64(1.5)).value == 1.5
    assert column_labels_equal(_Box("a"), _Box("a")) is False
    assert retain_column_label((1, float("inf"))).kind is ColumnLabelKind.UNSUPPORTED
    assert directional_difference(Fraction(1, 3), Fraction(1, 6)) == Fraction(1, 6)
    assert directional_difference(Fraction(2, 1), Fraction(1, 1)) == 1
    assert directional_difference(1.0, 1.0) == 0.0
    _assert_source_free(result)


def test_missing_specialized_profiles_are_unavailable() -> None:
    categorical = compare_dataset_analyses(
        _manual(
            (
                _synthetic_column(
                    0, "group", n_rows=3, semantic_type=SemanticType.CATEGORICAL
                ),
            ),
            3,
        ),
        _manual(
            (
                _synthetic_column(
                    0, "group", n_rows=3, semantic_type=SemanticType.CATEGORICAL
                ),
            ),
            3,
        ),
    )
    boolean = compare_dataset_analyses(
        _manual(
            (
                _synthetic_column(
                    0, "flag", n_rows=3, semantic_type=SemanticType.BOOLEAN
                ),
            ),
            3,
        ),
        _manual(
            (
                _synthetic_column(
                    0, "flag", n_rows=3, semantic_type=SemanticType.BOOLEAN
                ),
            ),
            3,
        ),
    )
    assert categorical.columns[0].descriptive_reason is (
        DescriptiveComparisonReason.PROFILE_ABSENT
    )
    assert boolean.columns[0].descriptive_reason is (
        DescriptiveComparisonReason.PROFILE_ABSENT
    )
    assert categorical.columns[0].categorical is None
    assert boolean.columns[0].boolean is None


def test_record_guards_reject_inconsistent_comparisons() -> None:
    with pytest.raises(TypeError):
        compare_dataframes([1, 2], pd.DataFrame({"a": [1]}))
    with pytest.raises(TypeError):
        compare_dataset_analyses(pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [1]}))
    with pytest.raises(ValueError):
        CountComparison(True, 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        NumericDifference(True, 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        NumericDifference(float("nan"), 1.0)


def _walk_objects(value: object):
    seen = set()

    def walk(item: object):
        marker = id(item)
        if marker in seen:
            return
        seen.add(marker)
        yield item
        if isinstance(item, tuple):
            for child in item:
                yield from walk(child)
        elif dataclasses.is_dataclass(item):
            for field in dataclasses.fields(item):
                yield from walk(getattr(item, field.name))

    yield from walk(value)
