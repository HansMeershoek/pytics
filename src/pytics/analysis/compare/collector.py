"""Comparison entry points and the order of the comparison pass.

``compare_dataframes`` analyzes each DataFrame on its own and then
compares those results with both source frames. ``compare_dataset_analyses``
compares two finished analyses. Without source frames it does not read
any value, and every eligible column's distribution drift is recorded as
not collected. With both frames it also runs the distribution-drift
pass. Univariate drift is one pass with one correction family, so the
family never depends on which entry point was used.

The pass is: dataset counts, column alignment, schema and semantic
snapshots, missingness and descriptive comparison, distribution drift
for descriptively compared columns, one Benjamini–Hochberg adjustment
of the available primary drift tests, relationship drift from the
retained relationship records, then target drift when a target was
requested. Relationship drift does not read source values. Target drift
does not calculate a second distribution test or a second relationship.
Neither analysis and neither frame is modified or retained.

A target argument is optional. Omitting it leaves target drift unset.
Passing one resolves that column on each frame. A label that matches
more than one column still fails. A label that matches neither column
is an explicit missing target, not a guessed column.
"""

from __future__ import annotations

from typing import Optional
from typing import Sequence

import pandas as pd

from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.alignment import _AlignedColumn
from pytics.analysis.compare.alignment import align_columns
from pytics.analysis.compare.descriptive import DescriptiveComparisonReason
from pytics.analysis.compare.descriptive import DescriptiveComparisonStatus
from pytics.analysis.compare.descriptive import _Descriptive
from pytics.analysis.compare.descriptive import descriptive_comparison
from pytics.analysis.compare.descriptive import missingness_comparison
from pytics.analysis.compare.distribution import adjust_drift_tests
from pytics.analysis.compare.distribution import boolean_distribution_drift
from pytics.analysis.compare.distribution import categorical_distribution_drift
from pytics.analysis.compare.distribution import numeric_distribution_drift
from pytics.analysis.compare.distribution import read_numeric_population
from pytics.analysis.compare.distribution_models import DistributionDrift
from pytics.analysis.compare.distribution_models import DistributionDriftStatus
from pytics.analysis.compare.models import ColumnComparison
from pytics.analysis.compare.models import DatasetComparison
from pytics.analysis.compare.models import coverage_from_columns
from pytics.analysis.compare.overview import overview_comparison
from pytics.analysis.compare.relationship_models import coverage_from_relationships
from pytics.analysis.compare.relationships import compare_relationships
from pytics.analysis.compare.schema import physical_comparison
from pytics.analysis.compare.schema import semantic_comparison
from pytics.analysis.compare.target import compare_target
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.column_label import observed_labels_equal
from pytics.analysis.target import TargetPosition
from pytics.analysis.target import _labels_equal

_DRIFT_STATUS = {
    DescriptiveComparisonStatus.NUMERIC: DistributionDriftStatus.NUMERIC,
    DescriptiveComparisonStatus.CATEGORICAL: DistributionDriftStatus.CATEGORICAL,
    DescriptiveComparisonStatus.BOOLEAN: DistributionDriftStatus.BOOLEAN,
}


def compare_dataset_analyses(
    reference: DatasetAnalysis,
    comparison: DatasetAnalysis,
    *,
    reference_frame: Optional[pd.DataFrame] = None,
    comparison_frame: Optional[pd.DataFrame] = None,
    target_reference_position: Optional[int] = None,
    target_comparison_position: Optional[int] = None,
    target_requested: bool = False,
) -> DatasetComparison:
    """Compare two finished dataset analyses.

    The analyses are not modified. Anomaly results are not read.
    Relationship drift reads the retained relationship records only.
    No row index is available on either analysis, and none is inferred.

    The source frames are optional and go together. When given, each
    must be the frame its analysis was built from: same shape, same
    labels by position, and the same finite Numeric counts. Only Numeric
    distribution drift reads them.

    ``target_requested`` is the only switch for target drift. Positions
    are the columns already resolved on each side. A target stored on an
    analysis is not used unless this switch is set, and a stored target
    at a different position is rejected when the switch is set.
    """
    if not isinstance(reference, DatasetAnalysis) or not isinstance(
        comparison, DatasetAnalysis
    ):
        raise TypeError("compare_dataset_analyses expects two DatasetAnalysis values")
    if (reference_frame is None) is not (comparison_frame is None):
        raise ValueError("supply both source frames or neither")
    if reference_frame is not None:
        _require_source_frame(reference_frame, reference)
        _require_source_frame(comparison_frame, comparison)  # type: ignore[arg-type]
    if type(target_requested) is not bool:
        raise TypeError("target_requested must be a bool")
    if not target_requested and (
        target_reference_position is not None or target_comparison_position is not None
    ):
        raise ValueError("target positions require a target request")
    overview = overview_comparison(reference, comparison)
    aligned = align_columns(reference.columns, comparison.columns)
    descriptive = tuple(_descriptive_part(item) for item in aligned)
    drift = adjust_drift_tests(
        tuple(
            _drift_record(item, part, reference_frame, comparison_frame)
            for item, part in zip(aligned, descriptive)
        )
    )
    columns = tuple(
        _column_comparison(item, part, record, sourced=reference_frame is not None)
        for item, part, record in zip(aligned, descriptive, drift)
    )
    relationships = compare_relationships(reference, comparison, aligned)
    target = None
    if target_requested:
        target = compare_target(
            reference_position=target_reference_position,
            comparison_position=target_comparison_position,
            columns=columns,
            relationships=relationships,
            reference=reference,
            comparison=comparison,
        )
    return DatasetComparison(
        overview=overview,
        columns=columns,
        coverage=coverage_from_columns(columns),
        relationships=relationships,
        relationship_coverage=coverage_from_relationships(relationships),
        target=target,
    )


def compare_dataframes(
    reference: pd.DataFrame,
    comparison: pd.DataFrame,
    *,
    target: object = None,
) -> DatasetComparison:
    """Analyze two DataFrames independently, then compare those analyses.

    Neither frame is modified. ``target`` requests target drift for one
    column. ``None`` requests none. Distribution drift is collected.
    This function is not the public ``pytics.compare`` entry point, and
    its result is not passed to the legacy renderer.
    """
    if not isinstance(reference, pd.DataFrame) or not isinstance(
        comparison, pd.DataFrame
    ):
        raise TypeError("compare_dataframes expects two pandas DataFrames")
    reference_position = None
    comparison_position = None
    if target is not None:
        reference_position = _target_position(reference.columns, target)
        comparison_position = _target_position(comparison.columns, target)
    reference_analysis = analyze_dataframe(
        reference,
        target=(
            None if reference_position is None else TargetPosition(reference_position)
        ),
    )
    comparison_analysis = analyze_dataframe(
        comparison,
        target=(
            None if comparison_position is None else TargetPosition(comparison_position)
        ),
    )
    return compare_dataset_analyses(
        reference_analysis,
        comparison_analysis,
        reference_frame=reference,
        comparison_frame=comparison,
        target_reference_position=reference_position,
        target_comparison_position=comparison_position,
        target_requested=target is not None,
    )


def _target_position(labels: Sequence[object], target: object) -> Optional[int]:
    """Resolve one requested target, or return None when it is absent.

    A label that matches more than one column fails. A position outside
    the axis is absence, not a guessed neighbor.
    """
    if isinstance(labels, (str, bytes)):
        raise TypeError("target resolution expects a column axis")
    count = len(labels)
    if isinstance(target, TargetPosition):
        if target.position >= count:
            return None
        return target.position
    matches = [index for index in range(count) if _labels_equal(labels[index], target)]
    if len(matches) > 1:
        raise ValueError("target label matches more than one column")
    if not matches:
        return None
    return matches[0]


def _require_source_frame(frame: pd.DataFrame, analysis: DatasetAnalysis) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("source frames must be pandas DataFrames")
    if frame.shape != (analysis.n_rows, analysis.n_columns):
        raise ValueError("source frame shape does not match its analysis")
    for column in analysis.columns:
        if not observed_labels_equal(column.label, frame.columns[column.position]):
            raise ValueError("source frame labels do not match its analysis")


def _descriptive_part(item: _AlignedColumn) -> Optional[_Descriptive]:
    if item.reference is None or item.comparison is None:
        return None
    return descriptive_comparison(item.reference, item.comparison)


def _drift_record(
    item: _AlignedColumn,
    descriptive: Optional[_Descriptive],
    reference_frame: Optional[pd.DataFrame],
    comparison_frame: Optional[pd.DataFrame],
) -> Optional[DistributionDrift]:
    if descriptive is None or reference_frame is None or comparison_frame is None:
        return None
    if descriptive.categorical is not None:
        return categorical_distribution_drift(descriptive.categorical)
    if descriptive.boolean is not None:
        return boolean_distribution_drift(descriptive.boolean)
    if descriptive.numeric is None:
        return None
    counts = descriptive.numeric.finite_count
    reference_values = read_numeric_population(
        reference_frame.iloc[:, item.reference.position],  # type: ignore[union-attr]
        counts.reference,
    )
    comparison_values = read_numeric_population(
        comparison_frame.iloc[:, item.comparison.position],  # type: ignore[union-attr]
        counts.comparison,
    )
    return numeric_distribution_drift(reference_values, comparison_values)


def _column_comparison(
    item: _AlignedColumn,
    descriptive: Optional[_Descriptive],
    drift: Optional[DistributionDrift],
    *,
    sourced: bool,
) -> ColumnComparison:
    if descriptive is None:
        if item.alignment.status is ColumnMatchStatus.MATCHED:
            raise ValueError("a matched column has a descriptive comparison")
        return ColumnComparison(
            alignment=item.alignment,
            physical=physical_comparison(item.reference, item.comparison),
            semantic=semantic_comparison(item.reference, item.comparison),
            missingness=None,
            descriptive_status=DescriptiveComparisonStatus.INAPPLICABLE,
            descriptive_reason=DescriptiveComparisonReason.UNMATCHED_COLUMN,
            distribution_status=DistributionDriftStatus.NOT_ELIGIBLE,
        )
    status = _DRIFT_STATUS.get(descriptive.status, DistributionDriftStatus.NOT_ELIGIBLE)
    if status is not DistributionDriftStatus.NOT_ELIGIBLE and not sourced:
        status = DistributionDriftStatus.SOURCE_VALUES_NOT_SUPPLIED
    return ColumnComparison(
        alignment=item.alignment,
        physical=physical_comparison(item.reference, item.comparison),
        semantic=semantic_comparison(item.reference, item.comparison),
        missingness=missingness_comparison(
            item.reference, item.comparison  # type: ignore[arg-type]
        ),
        descriptive_status=descriptive.status,
        descriptive_reason=descriptive.reason,
        distribution_status=status,
        numeric=descriptive.numeric,
        categorical=descriptive.categorical,
        boolean=descriptive.boolean,
        distribution=drift,
    )
