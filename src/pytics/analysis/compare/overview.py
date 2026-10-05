"""Dataset-level counts copied from the two retained analyses.

Duplicate groups are counted, not matched. Missingness patterns are not
compared. None of these changes is a quality score. The counts come
from the existing overview builder and the retained missingness and
duplicate results. No frame is read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from pytics.analysis.compare.values import CountComparison
from pytics.analysis.compare.values import _require_count
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.overview import build_dataset_overview
from pytics.semantics.interpretation import SemanticType


@dataclass(frozen=True)
class SemanticTypeCountComparison:
    """How many columns selected one semantic type on each side.

    A zero count means that side had no resolved column of this type.
    The type is omitted only when both counts are zero.
    """

    semantic_type: SemanticType
    reference_count: int
    comparison_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.semantic_type, SemanticType):
            raise TypeError("semantic_type must be a SemanticType")
        _require_count(self.reference_count, "reference_count")
        _require_count(self.comparison_count, "comparison_count")
        if self.reference_count == 0 and self.comparison_count == 0:
            raise ValueError("a semantic-type comparison requires a positive count")

    @property
    def change(self) -> int:
        """``comparison_count - reference_count``."""
        return self.comparison_count - self.reference_count


@dataclass(frozen=True)
class DatasetOverviewComparison:
    """Dataset-level counts copied from the two retained analyses.

    Duplicate groups are counted, not matched. Missingness patterns are
    not compared. None of these changes is a quality score.
    """

    n_rows: CountComparison
    n_columns: CountComparison
    n_cells: CountComparison
    n_missing_cells: CountComparison
    n_non_missing_cells: CountComparison
    n_complete_rows: CountComparison
    n_rows_with_missing: CountComparison
    n_unique_rows: CountComparison
    n_excess_duplicate_rows: CountComparison
    n_duplicate_groups: CountComparison
    n_rows_in_duplicate_groups: CountComparison
    empty_column_count: CountComparison
    constant_column_count: CountComparison
    identifier_column_count: CountComparison
    insufficient_evidence_column_count: CountComparison
    ambiguous_column_count: CountComparison
    semantic_type_counts: Tuple[SemanticTypeCountComparison, ...]

    def __post_init__(self) -> None:
        for field in (
            "n_rows",
            "n_columns",
            "n_cells",
            "n_missing_cells",
            "n_non_missing_cells",
            "n_complete_rows",
            "n_rows_with_missing",
            "n_unique_rows",
            "n_excess_duplicate_rows",
            "n_duplicate_groups",
            "n_rows_in_duplicate_groups",
            "empty_column_count",
            "constant_column_count",
            "identifier_column_count",
            "insufficient_evidence_column_count",
            "ambiguous_column_count",
        ):
            if not isinstance(getattr(self, field), CountComparison):
                raise TypeError(f"{field} must be a CountComparison")
        if not isinstance(self.semantic_type_counts, tuple):
            raise TypeError("semantic_type_counts must be a tuple")
        seen = []
        for item in self.semantic_type_counts:
            if not isinstance(item, SemanticTypeCountComparison):
                raise TypeError(
                    "semantic_type_counts must contain SemanticTypeCountComparison"
                )
            seen.append(item.semantic_type)
        if seen != sorted(seen, key=lambda item: list(SemanticType).index(item)):
            raise ValueError("semantic type counts must follow SemanticType order")
        if len(seen) != len(set(seen)):
            raise ValueError("semantic type counts must be unique")


def overview_comparison(
    reference: DatasetAnalysis,
    comparison: DatasetAnalysis,
) -> DatasetOverviewComparison:
    """Copy dataset-level counts from both retained analyses."""
    reference_overview = build_dataset_overview(reference)
    comparison_overview = build_dataset_overview(comparison)
    return DatasetOverviewComparison(
        n_rows=CountComparison(reference_overview.n_rows, comparison_overview.n_rows),
        n_columns=CountComparison(
            reference_overview.n_columns, comparison_overview.n_columns
        ),
        n_cells=CountComparison(
            reference_overview.n_cells, comparison_overview.n_cells
        ),
        n_missing_cells=CountComparison(
            reference_overview.n_missing_cells,
            comparison_overview.n_missing_cells,
        ),
        n_non_missing_cells=CountComparison(
            reference_overview.n_non_missing_cells,
            comparison_overview.n_non_missing_cells,
        ),
        n_complete_rows=CountComparison(
            reference.missing_analysis.n_complete_rows,
            comparison.missing_analysis.n_complete_rows,
        ),
        n_rows_with_missing=CountComparison(
            reference.n_rows - reference.missing_analysis.n_complete_rows,
            comparison.n_rows - comparison.missing_analysis.n_complete_rows,
        ),
        n_unique_rows=CountComparison(
            reference_overview.n_unique_rows,
            comparison_overview.n_unique_rows,
        ),
        n_excess_duplicate_rows=CountComparison(
            reference_overview.n_excess_duplicate_rows,
            comparison_overview.n_excess_duplicate_rows,
        ),
        n_duplicate_groups=CountComparison(
            reference.duplicate_analysis.n_duplicate_groups,
            comparison.duplicate_analysis.n_duplicate_groups,
        ),
        n_rows_in_duplicate_groups=CountComparison(
            reference.duplicate_analysis.n_rows_in_duplicate_groups,
            comparison.duplicate_analysis.n_rows_in_duplicate_groups,
        ),
        empty_column_count=CountComparison(
            reference_overview.empty_column_count,
            comparison_overview.empty_column_count,
        ),
        constant_column_count=CountComparison(
            reference_overview.constant_column_count,
            comparison_overview.constant_column_count,
        ),
        identifier_column_count=CountComparison(
            reference_overview.identifier_column_count,
            comparison_overview.identifier_column_count,
        ),
        insufficient_evidence_column_count=CountComparison(
            reference_overview.insufficient_evidence_column_count,
            comparison_overview.insufficient_evidence_column_count,
        ),
        ambiguous_column_count=CountComparison(
            reference_overview.ambiguous_column_count,
            comparison_overview.ambiguous_column_count,
        ),
        semantic_type_counts=_semantic_type_counts(
            reference_overview.semantic_type_counts,
            comparison_overview.semantic_type_counts,
        ),
    )


def _semantic_type_counts(reference_counts, comparison_counts):
    reference_map = {item.semantic_type: item.count for item in reference_counts}
    comparison_map = {item.semantic_type: item.count for item in comparison_counts}
    return tuple(
        SemanticTypeCountComparison(
            semantic_type=semantic_type,
            reference_count=reference_map.get(semantic_type, 0),
            comparison_count=comparison_map.get(semantic_type, 0),
        )
        for semantic_type in SemanticType
        if semantic_type in reference_map or semantic_type in comparison_map
    )
