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
for descriptively compared columns, then one Benjamini–Hochberg
adjustment of the available primary drift tests before the result is
frozen. Neither analysis and neither frame is modified or retained.
"""

from __future__ import annotations

from typing import Optional

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
from pytics.analysis.compare.schema import physical_comparison
from pytics.analysis.compare.schema import semantic_comparison
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationships.collector import _labels_match

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
) -> DatasetComparison:
    """Compare two finished dataset analyses.

    The analyses are not modified. Target, leakage, diagnostic,
    relationship, and anomaly results are not read. No row index is
    available on either analysis, and none is inferred.

    The source frames are optional and go together. When given, each
    must be the frame its analysis was built from: same shape, same
    labels by position, and the same finite Numeric counts. Only Numeric
    distribution drift reads them.
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
    return DatasetComparison(
        overview=overview,
        columns=columns,
        coverage=coverage_from_columns(columns),
    )


def compare_dataframes(
    reference: pd.DataFrame,
    comparison: pd.DataFrame,
) -> DatasetComparison:
    """Analyze two DataFrames independently, then compare those analyses.

    Neither frame is modified. No target is requested. Distribution drift
    is collected. This function is not the public ``pytics.compare``
    entry point, and its result is not passed to the legacy renderer.
    """
    if not isinstance(reference, pd.DataFrame) or not isinstance(
        comparison, pd.DataFrame
    ):
        raise TypeError("compare_dataframes expects two pandas DataFrames")
    reference_analysis = analyze_dataframe(reference)
    comparison_analysis = analyze_dataframe(comparison)
    return compare_dataset_analyses(
        reference_analysis,
        comparison_analysis,
        reference_frame=reference,
        comparison_frame=comparison,
    )


def _require_source_frame(frame: pd.DataFrame, analysis: DatasetAnalysis) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("source frames must be pandas DataFrames")
    if frame.shape != (analysis.n_rows, analysis.n_columns):
        raise ValueError("source frame shape does not match its analysis")
    for column in analysis.columns:
        if not _labels_match(column.label, frame.columns[column.position]):
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
