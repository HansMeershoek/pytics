"""Validation guards for the comparison records."""

from __future__ import annotations

import datetime as datetime_module
import warnings
from dataclasses import replace

import pandas as pd
import pytest

from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.column_label import retain_column_label
from pytics.analysis.compare import ColumnAlignment
from pytics.analysis.compare import ColumnMatchStatus
from pytics.analysis.compare import CountComparison
from pytics.analysis.compare import DatasetComparison
from pytics.analysis.compare import DescriptiveComparisonReason
from pytics.analysis.compare import DescriptiveComparisonStatus
from pytics.analysis.compare import OptionalCountComparison
from pytics.analysis.compare import PhysicalDtypeComparison
from pytics.analysis.compare import PhysicalDtypeSnapshot
from pytics.analysis.compare import ProportionDifference
from pytics.analysis.compare import SemanticSnapshot
from pytics.analysis.compare import SemanticTypeCountComparison
from pytics.analysis.compare import compare_dataframes
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus


def test_one_sided_changes_are_absent_rather_than_false() -> None:
    result = compare_dataframes(
        pd.DataFrame({"age": [1, 2, 3], "income": [4, 5, 6]}),
        pd.DataFrame({"age": [1, 2, 8]}),
    )
    removed = result.columns[1]
    assert removed.physical.family_changed is None
    assert removed.physical.dtype_name_changed is None
    assert removed.physical.categorical_ordered_changed is None
    assert removed.semantic.selected_type_changed is None
    assert removed.semantic.resolution_status_changed is None
    assert removed.semantic.confidence_changed is None
    assert removed.alignment.reordered is None
    assert OptionalCountComparison(None, 2).change is None
    assert OptionalCountComparison(1, 4).change == 3


def test_label_records_reject_values_that_do_not_match_the_kind() -> None:
    with pytest.raises(TypeError):
        RetainedColumnLabel(kind="none")  # type: ignore[arg-type]
    invalid = (
        (ColumnLabelKind.NONE, 1, ValueError),
        (ColumnLabelKind.BOOL, 1, TypeError),
        (ColumnLabelKind.INT, True, TypeError),
        (ColumnLabelKind.FLOAT, 1, TypeError),
        (ColumnLabelKind.FLOAT, float("nan"), TypeError),
        (ColumnLabelKind.FLOAT, -0.0, ValueError),
        (ColumnLabelKind.STRING, b"a", TypeError),
        (ColumnLabelKind.BYTES, "a", TypeError),
        (ColumnLabelKind.DATE, "2020-01-01", TypeError),
        (ColumnLabelKind.TIME, "00:00", TypeError),
        (ColumnLabelKind.DATETIME, "2020-01-01", TypeError),
        (ColumnLabelKind.TIMEDELTA, 1, TypeError),
        (ColumnLabelKind.TUPLE, ("a",), TypeError),
        (
            ColumnLabelKind.TUPLE,
            (RetainedColumnLabel(ColumnLabelKind.UNSUPPORTED),),
            ValueError,
        ),
    )
    for kind, value, error in invalid:
        with pytest.raises(error):
            RetainedColumnLabel(kind=kind, value=value)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        assert retain_column_label(pd.Timestamp(1)).kind is ColumnLabelKind.UNSUPPORTED
    assert retain_column_label(pd.Timedelta(days=1)).kind is ColumnLabelKind.TIMEDELTA


def test_direct_records_reject_inconsistent_fields() -> None:
    label = RetainedColumnLabel(ColumnLabelKind.STRING, "age")
    with pytest.raises(TypeError):
        ColumnAlignment(
            status="matched",  # type: ignore[arg-type]
            reference_label=label,
            comparison_label=label,
            occurrence=1,
            reference_position=0,
            comparison_position=0,
        )
    with pytest.raises(ValueError):
        ColumnAlignment(
            status=ColumnMatchStatus.MATCHED,
            reference_label=label,
            comparison_label=label,
            occurrence=0,
            reference_position=0,
            comparison_position=1,
        )
    with pytest.raises(ValueError):
        ColumnAlignment(
            status=ColumnMatchStatus.MATCHED,
            reference_label=label,
            comparison_label=None,
            occurrence=1,
            reference_position=0,
            comparison_position=1,
        )
    with pytest.raises(ValueError):
        ColumnAlignment(
            status=ColumnMatchStatus.REFERENCE_ONLY,
            reference_label=label,
            comparison_label=label,
            occurrence=1,
            reference_position=0,
            comparison_position=None,
        )
    with pytest.raises(ValueError):
        ColumnAlignment(
            status=ColumnMatchStatus.COMPARISON_ONLY,
            reference_label=None,
            comparison_label=None,
            occurrence=1,
            reference_position=None,
            comparison_position=0,
        )
    with pytest.raises(TypeError):
        PhysicalDtypeSnapshot(family="integer", dtype_name="int64")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        PhysicalDtypeSnapshot(family=PhysicalDtypeFamily.INTEGER, dtype_name=" ")
    with pytest.raises(TypeError):
        PhysicalDtypeSnapshot(
            family=PhysicalDtypeFamily.INTEGER,
            dtype_name="int64",
            categorical_ordered=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError):
        PhysicalDtypeComparison(reference=None, comparison=None)
    with pytest.raises(ValueError):
        SemanticTypeCountComparison(SemanticType.NUMERIC, 0, 0)
    with pytest.raises(TypeError):
        SemanticSnapshot(
            resolution_status="resolved",  # type: ignore[arg-type]
            selected_type=SemanticType.NUMERIC,
            confidence=None,
        )
    with pytest.raises(ValueError):
        SemanticSnapshot(
            resolution_status=ResolutionStatus.RESOLVED,
            selected_type=None,
            confidence=None,
        )
    with pytest.raises(ValueError):
        SemanticSnapshot(
            resolution_status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
            selected_type=SemanticType.NUMERIC,
            confidence=None,
        )
    with pytest.raises(ValueError):
        ProportionDifference(reference=1.5, comparison=0.0)
    with pytest.raises(ValueError):
        CountComparison(reference=1.0, comparison=1)  # type: ignore[arg-type]
    result = compare_dataframes(
        pd.DataFrame({"age": [1, 2], "income": [3, 4]}),
        pd.DataFrame({"age": [1, 2], "income": [3, 9]}),
    )
    swapped = (result.columns[1], result.columns[0])
    with pytest.raises(ValueError, match="physical order"):
        DatasetComparison(
            overview=result.overview,
            columns=swapped,
            coverage=result.coverage,
        )
    with pytest.raises(ValueError, match="SemanticType order"):
        type(result.overview)(
            **{
                **{
                    field.name: getattr(result.overview, field.name)
                    for field in result.overview.__dataclass_fields__.values()
                },
                "semantic_type_counts": (
                    SemanticTypeCountComparison(SemanticType.BOOLEAN, 0, 1),
                    SemanticTypeCountComparison(SemanticType.NUMERIC, 1, 1),
                ),
            }
        )


def test_descriptive_payload_must_match_its_status() -> None:
    column = compare_dataframes(
        pd.DataFrame({"amount": [1, 2, 3]}),
        pd.DataFrame({"amount": [1, 2, 4]}),
    ).columns[0]
    with pytest.raises(ValueError, match="numeric payload"):
        replace(column, numeric=None)
    with pytest.raises(ValueError, match="no inapplicable reason"):
        replace(column, descriptive_reason=DescriptiveComparisonReason.EMPTY)
    with pytest.raises(ValueError, match="no descriptive payload"):
        replace(
            column,
            descriptive_status=DescriptiveComparisonStatus.INAPPLICABLE,
            descriptive_reason=DescriptiveComparisonReason.EMPTY,
        )
    with pytest.raises(ValueError, match="names why"):
        replace(
            column,
            descriptive_status=DescriptiveComparisonStatus.INAPPLICABLE,
            numeric=None,
            descriptive_reason=None,
        )
    with pytest.raises(ValueError, match="missing profile"):
        replace(
            column,
            descriptive_status=DescriptiveComparisonStatus.UNAVAILABLE,
            numeric=None,
            descriptive_reason=DescriptiveComparisonReason.EMPTY,
        )
    with pytest.raises(ValueError, match="missingness"):
        replace(column, missingness=None)


def test_datetime_label_value_is_a_datetime() -> None:
    moment = datetime_module.datetime(2020, 1, 1)
    retained = RetainedColumnLabel(ColumnLabelKind.DATETIME, moment)
    assert retained.value == moment
