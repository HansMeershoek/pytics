"""Compare two dataset analyses.

The question is what changed between a reference dataset and a comparison
dataset. A difference is not drift, drift is not degradation, and this
result does not score either one. It also does not say that the comparison
dataset is worse, invalid, or the result of a particular event.

``compare_dataframes`` analyzes each DataFrame on its own, then compares
those results. ``compare_dataset_analyses`` only reads the results. It
does not scan either frame again, and it does not mutate them. Column
profiles, missingness, and duplicate counts are the facts those analyses
already retained.

Rows are not paired. The DataFrame index is not an entity key. Duplicate
groups are not matched across datasets. Distribution tests, relationship
drift, target drift, and anomaly-count comparison are not this result.

A directional number, where the arithmetic is defined, is
``comparison - reference``. There is no percent change. A missing
descriptive record is an explicit status, not a claim that the column
was unchanged.

Nothing here is ``pytics.compare``. The legacy public function is unchanged.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Optional
from typing import Tuple
from typing import Union

import pandas as pd

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.column_label import column_label_match_key
from pytics.analysis.column_label import retain_column_label
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.overview import build_dataset_overview
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus


class ColumnMatchStatus(Enum):
    """How one column sits relative to the other dataset.

    A reordered column is ``MATCHED``. It is not removed and added.
    """

    MATCHED = "matched"
    REFERENCE_ONLY = "reference_only"
    COMPARISON_ONLY = "comparison_only"


class DescriptiveComparisonStatus(Enum):
    """Whether a matched column received a typed descriptive comparison.

    ``INAPPLICABLE`` and ``UNAVAILABLE`` are results. They do not mean
    the column was unchanged.
    """

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    INAPPLICABLE = "inapplicable"
    UNAVAILABLE = "unavailable"


class DescriptiveComparisonReason(Enum):
    """Why a typed descriptive comparison was not produced.

    A compared Numeric, Categorical, or Boolean column has no reason.
    """

    UNMATCHED_COLUMN = "unmatched_column"
    SEMANTIC_MISMATCH = "semantic_mismatch"
    PROFILE_ABSENT = "profile_absent"
    IDENTIFIER = "identifier"
    DATETIME = "datetime"
    TIMEDELTA = "timedelta"
    TEXT = "text"
    EMPTY = "empty"
    CONSTANT = "constant"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"


class DeferredComparisonFamily(Enum):
    """Comparison families this result deliberately does not contain.

    Their absence is not evidence that those aspects were unchanged.
    """

    STATISTICAL_DISTRIBUTION_DRIFT = "statistical_distribution_drift"
    RELATIONSHIP_DRIFT = "relationship_drift"
    TARGET_DRIFT = "target_drift"
    ANOMALY_COMPARISON = "anomaly_comparison"
    MISSINGNESS_PATTERN_DRIFT = "missingness_pattern_drift"
    DUPLICATE_GROUP_MATCHING = "duplicate_group_matching"
    ROW_ALIGNMENT = "row_alignment"


DEFERRED_COMPARISON_FAMILIES: Tuple[DeferredComparisonFamily, ...] = (
    DeferredComparisonFamily.STATISTICAL_DISTRIBUTION_DRIFT,
    DeferredComparisonFamily.RELATIONSHIP_DRIFT,
    DeferredComparisonFamily.TARGET_DRIFT,
    DeferredComparisonFamily.ANOMALY_COMPARISON,
    DeferredComparisonFamily.MISSINGNESS_PATTERN_DRIFT,
    DeferredComparisonFamily.DUPLICATE_GROUP_MATCHING,
    DeferredComparisonFamily.ROW_ALIGNMENT,
)

_NO_SPECIALIZED_COMPARATOR = {
    SemanticType.IDENTIFIER: DescriptiveComparisonReason.IDENTIFIER,
    SemanticType.DATETIME: DescriptiveComparisonReason.DATETIME,
    SemanticType.TIMEDELTA: DescriptiveComparisonReason.TIMEDELTA,
    SemanticType.TEXT: DescriptiveComparisonReason.TEXT,
    SemanticType.EMPTY: DescriptiveComparisonReason.EMPTY,
    SemanticType.CONSTANT: DescriptiveComparisonReason.CONSTANT,
}

MetricNumber = Union[int, float, Fraction]


@dataclass(frozen=True)
class CountComparison:
    """One non-negative integer on each side.

    ``change`` is ``comparison - reference``. It is exact.
    """

    reference: int
    comparison: int

    def __post_init__(self) -> None:
        _require_count(self.reference, "reference")
        _require_count(self.comparison, "comparison")

    @property
    def change(self) -> int:
        """``comparison - reference``."""
        return self.comparison - self.reference


@dataclass(frozen=True)
class OptionalCountComparison:
    """One integer that may be absent on either side.

    ``change`` is ``None`` when either side is absent. ``None`` is not
    zero.
    """

    reference: Optional[int]
    comparison: Optional[int]

    def __post_init__(self) -> None:
        if self.reference is not None:
            _require_count(self.reference, "reference")
        if self.comparison is not None:
            _require_count(self.comparison, "comparison")

    @property
    def change(self) -> Optional[int]:
        """``comparison - reference``, or ``None`` when either side is absent."""
        if self.reference is None or self.comparison is None:
            return None
        return self.comparison - self.reference


@dataclass(frozen=True)
class ProportionDifference:
    """One proportion on each side.

    ``change`` is the float difference ``comparison - reference`` when
    both proportions exist and that difference is finite. There is no
    percent change and no tolerance. ``None`` is not zero.
    """

    reference: Optional[float]
    comparison: Optional[float]

    def __post_init__(self) -> None:
        _require_optional_proportion(self.reference, "reference")
        _require_optional_proportion(self.comparison, "comparison")

    @property
    def change(self) -> Optional[float]:
        """``comparison - reference`` when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return _finite_float_difference(self.comparison, self.reference)


@dataclass(frozen=True)
class NumericDifference:
    """One retained numeric fact on each side.

    ``change`` is ``comparison - reference`` when that difference can be
    represented without rounding a float subtraction to infinity and
    without collapsing an exact integer or fraction. Otherwise ``change``
    is ``None``. Both side values stay stored either way. ``None`` is not
    zero and not NaN.
    """

    reference: Optional[MetricNumber]
    comparison: Optional[MetricNumber]

    def __post_init__(self) -> None:
        _require_metric(self.reference, "reference")
        _require_metric(self.comparison, "comparison")

    @property
    def change(self) -> Optional[MetricNumber]:
        """``comparison - reference`` under the numeric-change contract."""
        return directional_difference(self.comparison, self.reference)


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


@dataclass(frozen=True)
class PhysicalDtypeSnapshot:
    """Physical storage of one column, without the source dtype object."""

    family: PhysicalDtypeFamily
    dtype_name: str
    categorical_ordered: Optional[bool] = None

    def __post_init__(self) -> None:
        if not isinstance(self.family, PhysicalDtypeFamily):
            raise TypeError("family must be a PhysicalDtypeFamily")
        if type(self.dtype_name) is not str or not self.dtype_name.strip():
            raise ValueError("dtype_name must be a non-empty string")
        if (
            self.categorical_ordered is not None
            and type(self.categorical_ordered) is not bool
        ):
            raise TypeError("categorical_ordered must be a bool or None")


@dataclass(frozen=True)
class PhysicalDtypeComparison:
    """Physical dtype on each side that has the column.

    ``family_changed`` is ``None`` when the column exists on only one
    side. A dtype-name change is not a semantic-type change.
    """

    reference: Optional[PhysicalDtypeSnapshot]
    comparison: Optional[PhysicalDtypeSnapshot]

    def __post_init__(self) -> None:
        _require_optional(self.reference, PhysicalDtypeSnapshot, "reference")
        _require_optional(self.comparison, PhysicalDtypeSnapshot, "comparison")
        if self.reference is None and self.comparison is None:
            raise ValueError("a physical comparison needs at least one side")

    @property
    def family_changed(self) -> Optional[bool]:
        """Whether the physical families differ, when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.family is not self.comparison.family

    @property
    def dtype_name_changed(self) -> Optional[bool]:
        """Whether the dtype display names differ, when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.dtype_name != self.comparison.dtype_name

    @property
    def categorical_ordered_changed(self) -> Optional[bool]:
        """Whether ordered-categorical metadata differs, when both sides exist.

        ``None`` on a snapshot means that side is not categorical. ``False``
        to ``True`` is a change. Both ``None`` is not a change.
        """
        if self.reference is None or self.comparison is None:
            return None
        return (
            self.reference.categorical_ordered
            is not self.comparison.categorical_ordered
        )


@dataclass(frozen=True)
class SemanticSnapshot:
    """Inferred semantic state of one column.

    ``confidence`` is the structural interpretation's confidence. It is
    ``None`` when resolution did not keep an interpretation, including a
    candidate-derived selection. There is no effective-interpretation
    override to compare yet.
    """

    resolution_status: ResolutionStatus
    selected_type: Optional[SemanticType]
    confidence: Optional[Confidence]

    def __post_init__(self) -> None:
        if not isinstance(self.resolution_status, ResolutionStatus):
            raise TypeError("resolution_status must be a ResolutionStatus")
        if self.selected_type is not None and not isinstance(
            self.selected_type, SemanticType
        ):
            raise TypeError("selected_type must be a SemanticType or None")
        if self.confidence is not None and not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence or None")
        if self.resolution_status is ResolutionStatus.RESOLVED:
            if self.selected_type is None:
                raise ValueError("a resolved column has a selected semantic type")
        elif self.selected_type is not None:
            raise ValueError("an unresolved column has no selected semantic type")


@dataclass(frozen=True)
class SemanticComparison:
    """Inferred semantic state on each side that has the column.

    Confidence is compared as a category. Levels are not subtracted.
    Both sides are the inferred state. An effective override is not
    represented, because overrides are not implemented.
    """

    reference: Optional[SemanticSnapshot]
    comparison: Optional[SemanticSnapshot]

    def __post_init__(self) -> None:
        _require_optional(self.reference, SemanticSnapshot, "reference")
        _require_optional(self.comparison, SemanticSnapshot, "comparison")
        if self.reference is None and self.comparison is None:
            raise ValueError("a semantic comparison needs at least one side")

    @property
    def selected_type_changed(self) -> Optional[bool]:
        """Whether the selected types differ, when both sides exist.

        ``None`` and a selected type differ. Two ``None`` values do not.
        """
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.selected_type is not self.comparison.selected_type

    @property
    def resolution_status_changed(self) -> Optional[bool]:
        """Whether the resolution statuses differ, when both sides exist."""
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.resolution_status is not self.comparison.resolution_status

    @property
    def confidence_changed(self) -> Optional[bool]:
        """Whether the confidence categories differ, when both sides exist.

        ``None`` is its own category. This is not a numeric step.
        """
        if self.reference is None or self.comparison is None:
            return None
        return self.reference.confidence is not self.comparison.confidence


@dataclass(frozen=True)
class ColumnAlignment:
    """Where one aligned column sits in each dataset.

    ``occurrence`` counts labels that share a match key, starting at 1,
    in physical order on that side. Matched columns share one occurrence.
    An unsupported label has no occurrence and is never matched.
    ``reordered`` is ``None`` unless both physical positions exist.
    """

    status: ColumnMatchStatus
    reference_label: Optional[RetainedColumnLabel]
    comparison_label: Optional[RetainedColumnLabel]
    occurrence: Optional[int]
    reference_position: Optional[int]
    comparison_position: Optional[int]

    def __post_init__(self) -> None:
        if not isinstance(self.status, ColumnMatchStatus):
            raise TypeError("status must be a ColumnMatchStatus")
        _require_optional(self.reference_label, RetainedColumnLabel, "reference_label")
        _require_optional(
            self.comparison_label, RetainedColumnLabel, "comparison_label"
        )
        _require_optional_position(self.reference_position, "reference_position")
        _require_optional_position(self.comparison_position, "comparison_position")
        if self.occurrence is not None and (
            type(self.occurrence) is not int or self.occurrence < 1
        ):
            raise ValueError("occurrence must be a positive int or None")
        if self.status is ColumnMatchStatus.MATCHED:
            if self.reference_position is None or self.comparison_position is None:
                raise ValueError("a matched column has two physical positions")
            if self.reference_label is None or self.comparison_label is None:
                raise ValueError("a matched column has two labels")
            if self.occurrence is None:
                raise ValueError("a matched column has an occurrence")
        elif self.status is ColumnMatchStatus.REFERENCE_ONLY:
            if self.reference_position is None or self.comparison_position is not None:
                raise ValueError(
                    "a reference-only column has only a reference position"
                )
            if self.reference_label is None or self.comparison_label is not None:
                raise ValueError("a reference-only column has only a reference label")
        else:
            if self.comparison_position is None or self.reference_position is not None:
                raise ValueError(
                    "a comparison-only column has only a comparison position"
                )
            if self.comparison_label is None or self.reference_label is not None:
                raise ValueError("a comparison-only column has only a comparison label")

    @property
    def reordered(self) -> Optional[bool]:
        """Whether the two physical positions differ.

        ``None`` when the column is missing from either side. Equal
        positions are not reordered.
        """
        if self.reference_position is None or self.comparison_position is None:
            return None
        return self.reference_position != self.comparison_position


@dataclass(frozen=True)
class ColumnMissingnessComparison:
    """Missing counts for one matched column.

    The counts are the basic evidence already retained. This is not a
    missingness-pattern comparison.
    """

    missing_count: CountComparison
    missing_proportion: ProportionDifference

    def __post_init__(self) -> None:
        if not isinstance(self.missing_count, CountComparison):
            raise TypeError("missing_count must be a CountComparison")
        if not isinstance(self.missing_proportion, ProportionDifference):
            raise TypeError("missing_proportion must be a ProportionDifference")


@dataclass(frozen=True)
class NumericDescriptiveComparison:
    """Descriptive numeric facts for one Numeric-to-Numeric column.

    Infinity counts are ``None`` on a side whose numeric-structure
    evidence was not retained. Quartiles and the mean stay as they were
    retained, including ``None`` when that statistic was unavailable.
    """

    finite_count: CountComparison
    missing_count: CountComparison
    positive_infinity_count: OptionalCountComparison
    negative_infinity_count: OptionalCountComparison
    minimum: NumericDifference
    maximum: NumericDifference
    mean: NumericDifference
    median: NumericDifference
    standard_deviation: NumericDifference
    q1: NumericDifference
    q3: NumericDifference
    interquartile_range: NumericDifference
    range: NumericDifference

    def __post_init__(self) -> None:
        _require_type(self.finite_count, CountComparison, "finite_count")
        _require_type(self.missing_count, CountComparison, "missing_count")
        _require_type(
            self.positive_infinity_count,
            OptionalCountComparison,
            "positive_infinity_count",
        )
        _require_type(
            self.negative_infinity_count,
            OptionalCountComparison,
            "negative_infinity_count",
        )
        for field in (
            "minimum",
            "maximum",
            "mean",
            "median",
            "standard_deviation",
            "q1",
            "q3",
            "interquartile_range",
            "range",
        ):
            _require_type(getattr(self, field), NumericDifference, field)


@dataclass(frozen=True)
class ComparedCategoryLevel:
    """One observed category in the reference, the comparison, or both.

    ``value`` is the category scalar from the retained distribution. It
    is not a display string. A count is ``None`` when that side did not
    observe the value. ``None`` is not a zero count.
    """

    value: object
    reference_count: Optional[int]
    comparison_count: Optional[int]
    reference_proportion: Optional[float]
    comparison_proportion: Optional[float]

    def __post_init__(self) -> None:
        if self.reference_count is not None:
            _require_positive(self.reference_count, "reference_count")
        if self.comparison_count is not None:
            _require_positive(self.comparison_count, "comparison_count")
        if self.reference_count is None and self.comparison_count is None:
            raise ValueError("a compared category level must be observed on one side")
        _require_optional_proportion(self.reference_proportion, "reference_proportion")
        _require_optional_proportion(
            self.comparison_proportion, "comparison_proportion"
        )
        if (self.reference_count is None) is not (self.reference_proportion is None):
            raise ValueError("a reference category count and proportion disagree")
        if (self.comparison_count is None) is not (self.comparison_proportion is None):
            raise ValueError("a comparison category count and proportion disagree")

    @property
    def count_change(self) -> Optional[int]:
        """``comparison_count - reference_count`` when the level is shared."""
        if self.reference_count is None or self.comparison_count is None:
            return None
        return self.comparison_count - self.reference_count


@dataclass(frozen=True)
class CategoricalDescriptiveComparison:
    """Observed categorical facts for one Categorical-to-Categorical column.

    Shared, reference-only, and comparison-only levels partition the
    observed values under the categorical equality contract. Declared
    categories that were not observed are not levels. ``ordered`` is the
    physical flag already stored on each descriptive result.
    """

    n_non_missing: CountComparison
    missing_count: CountComparison
    n_observed: CountComparison
    most_frequent_count: CountComparison
    least_frequent_count: CountComparison
    most_frequent_proportion: ProportionDifference
    least_frequent_proportion: ProportionDifference
    reference_most_frequent_values: Tuple[object, ...]
    comparison_most_frequent_values: Tuple[object, ...]
    reference_least_frequent_values: Tuple[object, ...]
    comparison_least_frequent_values: Tuple[object, ...]
    shared_levels: Tuple[ComparedCategoryLevel, ...]
    reference_only_levels: Tuple[ComparedCategoryLevel, ...]
    comparison_only_levels: Tuple[ComparedCategoryLevel, ...]
    observed_sequences_equal: bool
    reference_ordered: Optional[bool]
    comparison_ordered: Optional[bool]

    def __post_init__(self) -> None:
        _require_type(self.n_non_missing, CountComparison, "n_non_missing")
        _require_type(self.missing_count, CountComparison, "missing_count")
        _require_type(self.n_observed, CountComparison, "n_observed")
        _require_type(self.most_frequent_count, CountComparison, "most_frequent_count")
        _require_type(
            self.least_frequent_count, CountComparison, "least_frequent_count"
        )
        _require_type(
            self.most_frequent_proportion,
            ProportionDifference,
            "most_frequent_proportion",
        )
        _require_type(
            self.least_frequent_proportion,
            ProportionDifference,
            "least_frequent_proportion",
        )
        _require_object_tuple(
            self.reference_most_frequent_values, "reference_most_frequent_values"
        )
        _require_object_tuple(
            self.comparison_most_frequent_values, "comparison_most_frequent_values"
        )
        _require_object_tuple(
            self.reference_least_frequent_values, "reference_least_frequent_values"
        )
        _require_object_tuple(
            self.comparison_least_frequent_values, "comparison_least_frequent_values"
        )
        _require_level_tuple(self.shared_levels, "shared_levels", shared=True)
        _require_level_tuple(
            self.reference_only_levels, "reference_only_levels", shared=False
        )
        _require_level_tuple(
            self.comparison_only_levels, "comparison_only_levels", shared=False
        )
        if type(self.observed_sequences_equal) is not bool:
            raise TypeError("observed_sequences_equal must be a bool")
        if (
            self.reference_ordered is not None
            and type(self.reference_ordered) is not bool
        ):
            raise TypeError("reference_ordered must be a bool or None")
        if (
            self.comparison_ordered is not None
            and type(self.comparison_ordered) is not bool
        ):
            raise TypeError("comparison_ordered must be a bool or None")
        if (
            len(self.shared_levels) + len(self.reference_only_levels)
            != self.n_observed.reference
        ):
            raise ValueError("reference observed levels must match n_observed")
        if (
            len(self.shared_levels) + len(self.comparison_only_levels)
            != self.n_observed.comparison
        ):
            raise ValueError("comparison observed levels must match n_observed")

    @property
    def ordered_flag_changed(self) -> bool:
        """Whether the retained ordered flags differ."""
        return self.reference_ordered is not self.comparison_ordered


@dataclass(frozen=True)
class BooleanDescriptiveComparison:
    """True and false counts for one Boolean-to-Boolean column.

    A change in class share is a descriptive change. It is not a drift
    test and not a degradation.
    """

    true_count: CountComparison
    false_count: CountComparison
    missing_count: CountComparison
    true_proportion: ProportionDifference
    false_proportion: ProportionDifference

    def __post_init__(self) -> None:
        _require_type(self.true_count, CountComparison, "true_count")
        _require_type(self.false_count, CountComparison, "false_count")
        _require_type(self.missing_count, CountComparison, "missing_count")
        _require_type(self.true_proportion, ProportionDifference, "true_proportion")
        _require_type(self.false_proportion, ProportionDifference, "false_proportion")


@dataclass(frozen=True)
class ColumnComparison:
    """Alignment, schema, missingness, and one descriptive comparison.

    The descriptive payload matches ``descriptive_status``. An inapplicable
    or unavailable status has no payload.
    """

    alignment: ColumnAlignment
    physical: PhysicalDtypeComparison
    semantic: SemanticComparison
    missingness: Optional[ColumnMissingnessComparison]
    descriptive_status: DescriptiveComparisonStatus
    descriptive_reason: Optional[DescriptiveComparisonReason]
    numeric: Optional[NumericDescriptiveComparison] = None
    categorical: Optional[CategoricalDescriptiveComparison] = None
    boolean: Optional[BooleanDescriptiveComparison] = None

    def __post_init__(self) -> None:
        _require_type(self.alignment, ColumnAlignment, "alignment")
        _require_type(self.physical, PhysicalDtypeComparison, "physical")
        _require_type(self.semantic, SemanticComparison, "semantic")
        _require_optional(self.missingness, ColumnMissingnessComparison, "missingness")
        if not isinstance(self.descriptive_status, DescriptiveComparisonStatus):
            raise TypeError("descriptive_status must be a DescriptiveComparisonStatus")
        if self.descriptive_reason is not None and not isinstance(
            self.descriptive_reason, DescriptiveComparisonReason
        ):
            raise TypeError("descriptive_reason must be a DescriptiveComparisonReason")
        _require_optional(self.numeric, NumericDescriptiveComparison, "numeric")
        _require_optional(
            self.categorical, CategoricalDescriptiveComparison, "categorical"
        )
        _require_optional(self.boolean, BooleanDescriptiveComparison, "boolean")
        _require_descriptive_payload(self)
        matched = self.alignment.status is ColumnMatchStatus.MATCHED
        if matched and self.missingness is None:
            raise ValueError("a matched column has a missingness comparison")
        if not matched and self.missingness is not None:
            raise ValueError("an unmatched column has no missingness comparison")
        if matched is not (
            self.physical.reference is not None and self.physical.comparison is not None
        ):
            raise ValueError("physical snapshots must follow the column match")
        if matched is not (
            self.semantic.reference is not None and self.semantic.comparison is not None
        ):
            raise ValueError("semantic snapshots must follow the column match")


@dataclass(frozen=True)
class ComparisonCoverage:
    """How many columns received each kind of comparison.

    These counts describe the result. They are not a score. Deferred
    families are named so their absence is not read as "unchanged".
    """

    n_columns: int
    n_matched_columns: int
    n_reference_only_columns: int
    n_comparison_only_columns: int
    n_reordered_matched_columns: int
    n_same_selected_type_columns: int
    n_selected_type_changed_columns: int
    n_both_unresolved_columns: int
    n_numeric_descriptive_comparisons: int
    n_categorical_descriptive_comparisons: int
    n_boolean_descriptive_comparisons: int
    n_inapplicable_descriptive_comparisons: int
    n_unavailable_descriptive_comparisons: int
    deferred_families: Tuple[DeferredComparisonFamily, ...]

    def __post_init__(self) -> None:
        for field in (
            "n_columns",
            "n_matched_columns",
            "n_reference_only_columns",
            "n_comparison_only_columns",
            "n_reordered_matched_columns",
            "n_same_selected_type_columns",
            "n_selected_type_changed_columns",
            "n_both_unresolved_columns",
            "n_numeric_descriptive_comparisons",
            "n_categorical_descriptive_comparisons",
            "n_boolean_descriptive_comparisons",
            "n_inapplicable_descriptive_comparisons",
            "n_unavailable_descriptive_comparisons",
        ):
            _require_count(getattr(self, field), field)
        if not isinstance(self.deferred_families, tuple):
            raise TypeError("deferred_families must be a tuple")
        if self.deferred_families != DEFERRED_COMPARISON_FAMILIES:
            raise ValueError("deferred comparison families are fixed for this result")
        matched = (
            self.n_matched_columns
            + self.n_reference_only_columns
            + self.n_comparison_only_columns
        )
        if matched != self.n_columns:
            raise ValueError("matched and unmatched columns must sum to n_columns")
        semantic = (
            self.n_same_selected_type_columns
            + self.n_selected_type_changed_columns
            + self.n_both_unresolved_columns
        )
        if semantic != self.n_matched_columns:
            raise ValueError("semantic coverage must sum to matched columns")
        described = (
            self.n_numeric_descriptive_comparisons
            + self.n_categorical_descriptive_comparisons
            + self.n_boolean_descriptive_comparisons
            + self.n_inapplicable_descriptive_comparisons
            + self.n_unavailable_descriptive_comparisons
        )
        if described != self.n_columns:
            raise ValueError("descriptive coverage must sum to n_columns")


@dataclass(frozen=True)
class DatasetComparison:
    """Structured comparison of two dataset analyses.

    ``columns`` follows the reference physical order, then comparison-only
    columns in comparison physical order. The result does not keep either
    analysis or either DataFrame.
    """

    overview: DatasetOverviewComparison
    columns: Tuple[ColumnComparison, ...]
    coverage: ComparisonCoverage

    def __post_init__(self) -> None:
        _require_type(self.overview, DatasetOverviewComparison, "overview")
        if not isinstance(self.columns, tuple):
            raise TypeError("columns must be a tuple")
        for column in self.columns:
            if not isinstance(column, ColumnComparison):
                raise TypeError("columns must contain ColumnComparison records")
        _require_type(self.coverage, ComparisonCoverage, "coverage")
        if self.coverage != _coverage_from_columns(self.columns):
            raise ValueError("coverage does not match the column comparisons")
        _require_column_order(self.columns)


def compare_dataset_analyses(
    reference: DatasetAnalysis,
    comparison: DatasetAnalysis,
) -> DatasetComparison:
    """Compare two finished dataset analyses.

    The analyses are not modified. Target, leakage, diagnostic,
    relationship, and anomaly results are not read. No row index is
    available on either analysis, and none is inferred.
    """
    if not isinstance(reference, DatasetAnalysis) or not isinstance(
        comparison, DatasetAnalysis
    ):
        raise TypeError("compare_dataset_analyses expects two DatasetAnalysis values")
    overview = _overview_comparison(reference, comparison)
    columns = _align_columns(reference.columns, comparison.columns)
    return DatasetComparison(
        overview=overview,
        columns=columns,
        coverage=_coverage_from_columns(columns),
    )


def compare_dataframes(
    reference: pd.DataFrame,
    comparison: pd.DataFrame,
) -> DatasetComparison:
    """Analyze two DataFrames independently, then compare those analyses.

    Neither frame is modified. No target is requested. This function is
    not the public ``pytics.compare`` entry point, and its result is not
    passed to the legacy renderer.
    """
    if not isinstance(reference, pd.DataFrame) or not isinstance(
        comparison, pd.DataFrame
    ):
        raise TypeError("compare_dataframes expects two pandas DataFrames")
    reference_analysis = analyze_dataframe(reference)
    comparison_analysis = analyze_dataframe(comparison)
    return compare_dataset_analyses(reference_analysis, comparison_analysis)


def directional_difference(
    comparison: Optional[MetricNumber],
    reference: Optional[MetricNumber],
) -> Optional[MetricNumber]:
    """Return ``comparison - reference`` when the difference is safe.

    Two integers, or an integer and a fraction, stay exact. Two finite
    floats use float subtraction, and a non-finite result is ``None``.
    A mix of a float and an exact number keeps the exact rational
    difference instead of rounding through float64. Either side ``None``
    yields ``None``.
    """
    if comparison is None or reference is None:
        return None
    _require_metric(comparison, "comparison")
    _require_metric(reference, "reference")
    comparison_exact = _is_exact_metric(comparison)
    reference_exact = _is_exact_metric(reference)
    if comparison_exact and reference_exact:
        difference = comparison - reference
        if isinstance(difference, Fraction):
            if difference.denominator == 1:
                return difference.numerator
            return difference
        if type(difference) is int:
            return difference
        raise TypeError("an exact numeric difference must be an int or a Fraction")
    if type(comparison) is float and type(reference) is float:
        return _finite_float_difference(comparison, reference)
    exact = Fraction(comparison) - Fraction(reference)
    if exact.denominator == 1:
        return exact.numerator
    return exact


@dataclass(frozen=True)
class _IndexedColumn:
    column: ColumnAnalysis
    label: RetainedColumnLabel
    occurrence: Optional[int]
    key: Optional[Tuple[object, ...]]


def _align_columns(
    reference_columns: Tuple[ColumnAnalysis, ...],
    comparison_columns: Tuple[ColumnAnalysis, ...],
) -> Tuple[ColumnComparison, ...]:
    reference_index = _index_columns(reference_columns)
    comparison_index = _index_columns(comparison_columns)
    comparison_by_key = {}
    for indexed in comparison_index:
        if indexed.key is None:
            continue
        comparison_by_key[(indexed.key, indexed.occurrence)] = indexed
    matched_ids = set()
    aligned = []
    for indexed in reference_index:
        partner = None
        if indexed.key is not None:
            partner = comparison_by_key.get((indexed.key, indexed.occurrence))
        if partner is None:
            aligned.append(_unmatched_column(indexed, reference_side=True))
            continue
        matched_ids.add(id(partner))
        aligned.append(_matched_column(indexed, partner))
    for indexed in comparison_index:
        if id(indexed) in matched_ids:
            continue
        aligned.append(_unmatched_column(indexed, reference_side=False))
    return tuple(aligned)


def _index_columns(
    columns: Tuple[ColumnAnalysis, ...],
) -> Tuple[_IndexedColumn, ...]:
    counts = {}
    indexed = []
    for column in columns:
        label = retain_column_label(column.label)
        key = column_label_match_key(column.label)
        occurrence = None
        if key is not None:
            counts[key] = counts.get(key, 0) + 1
            occurrence = counts[key]
        indexed.append(
            _IndexedColumn(
                column=column,
                label=label,
                occurrence=occurrence,
                key=key,
            )
        )
    return tuple(indexed)


def _matched_column(
    reference: _IndexedColumn,
    comparison: _IndexedColumn,
) -> ColumnComparison:
    status, reason, numeric, categorical, boolean = _descriptive_comparison(
        reference.column,
        comparison.column,
    )
    return ColumnComparison(
        alignment=ColumnAlignment(
            status=ColumnMatchStatus.MATCHED,
            reference_label=reference.label,
            comparison_label=comparison.label,
            occurrence=reference.occurrence,
            reference_position=reference.column.position,
            comparison_position=comparison.column.position,
        ),
        physical=PhysicalDtypeComparison(
            reference=_physical_snapshot(reference.column),
            comparison=_physical_snapshot(comparison.column),
        ),
        semantic=SemanticComparison(
            reference=_semantic_snapshot(reference.column),
            comparison=_semantic_snapshot(comparison.column),
        ),
        missingness=_missingness_comparison(reference.column, comparison.column),
        descriptive_status=status,
        descriptive_reason=reason,
        numeric=numeric,
        categorical=categorical,
        boolean=boolean,
    )


def _unmatched_column(
    indexed: _IndexedColumn,
    *,
    reference_side: bool,
) -> ColumnComparison:
    if reference_side:
        alignment = ColumnAlignment(
            status=ColumnMatchStatus.REFERENCE_ONLY,
            reference_label=indexed.label,
            comparison_label=None,
            occurrence=indexed.occurrence,
            reference_position=indexed.column.position,
            comparison_position=None,
        )
        physical = PhysicalDtypeComparison(
            reference=_physical_snapshot(indexed.column),
            comparison=None,
        )
        semantic = SemanticComparison(
            reference=_semantic_snapshot(indexed.column),
            comparison=None,
        )
    else:
        alignment = ColumnAlignment(
            status=ColumnMatchStatus.COMPARISON_ONLY,
            reference_label=None,
            comparison_label=indexed.label,
            occurrence=indexed.occurrence,
            reference_position=None,
            comparison_position=indexed.column.position,
        )
        physical = PhysicalDtypeComparison(
            reference=None,
            comparison=_physical_snapshot(indexed.column),
        )
        semantic = SemanticComparison(
            reference=None,
            comparison=_semantic_snapshot(indexed.column),
        )
    return ColumnComparison(
        alignment=alignment,
        physical=physical,
        semantic=semantic,
        missingness=None,
        descriptive_status=DescriptiveComparisonStatus.INAPPLICABLE,
        descriptive_reason=DescriptiveComparisonReason.UNMATCHED_COLUMN,
    )


def _descriptive_comparison(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
):
    reference_type = reference.inferred.selected_type
    comparison_type = comparison.inferred.selected_type
    if reference_type is not comparison_type:
        return (
            DescriptiveComparisonStatus.INAPPLICABLE,
            DescriptiveComparisonReason.SEMANTIC_MISMATCH,
            None,
            None,
            None,
        )
    if reference_type is None:
        reference_status = reference.inferred.resolution.status
        comparison_status = comparison.inferred.resolution.status
        if reference_status is not comparison_status:
            reason = DescriptiveComparisonReason.SEMANTIC_MISMATCH
        elif reference_status is ResolutionStatus.AMBIGUOUS:
            reason = DescriptiveComparisonReason.AMBIGUOUS
        else:
            reason = DescriptiveComparisonReason.UNRESOLVED
        return (DescriptiveComparisonStatus.INAPPLICABLE, reason, None, None, None)
    if reference_type is SemanticType.NUMERIC:
        if reference.numeric_analysis is None or comparison.numeric_analysis is None:
            return (
                DescriptiveComparisonStatus.UNAVAILABLE,
                DescriptiveComparisonReason.PROFILE_ABSENT,
                None,
                None,
                None,
            )
        return (
            DescriptiveComparisonStatus.NUMERIC,
            None,
            _numeric_comparison(reference, comparison),
            None,
            None,
        )
    if reference_type is SemanticType.CATEGORICAL:
        if (
            reference.categorical_analysis is None
            or comparison.categorical_analysis is None
        ):
            return (
                DescriptiveComparisonStatus.UNAVAILABLE,
                DescriptiveComparisonReason.PROFILE_ABSENT,
                None,
                None,
                None,
            )
        return (
            DescriptiveComparisonStatus.CATEGORICAL,
            None,
            None,
            _categorical_comparison(reference, comparison),
            None,
        )
    if reference_type is SemanticType.BOOLEAN:
        if reference.boolean_analysis is None or comparison.boolean_analysis is None:
            return (
                DescriptiveComparisonStatus.UNAVAILABLE,
                DescriptiveComparisonReason.PROFILE_ABSENT,
                None,
                None,
                None,
            )
        return (
            DescriptiveComparisonStatus.BOOLEAN,
            None,
            None,
            None,
            _boolean_comparison(reference, comparison),
        )
    reason = _NO_SPECIALIZED_COMPARATOR.get(reference_type)
    if reason is None:
        raise ValueError("selected semantic type has no comparison rule")
    return (DescriptiveComparisonStatus.INAPPLICABLE, reason, None, None, None)


def _numeric_comparison(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
) -> NumericDescriptiveComparison:
    reference_profile = reference.numeric_analysis
    comparison_profile = comparison.numeric_analysis
    if reference_profile is None or comparison_profile is None:
        raise ValueError("numeric comparison requires two numeric profiles")
    return NumericDescriptiveComparison(
        finite_count=CountComparison(
            reference_profile.finite_count,
            comparison_profile.finite_count,
        ),
        missing_count=CountComparison(
            reference.evidence.basic.n_missing,
            comparison.evidence.basic.n_missing,
        ),
        positive_infinity_count=_infinity_count(
            reference, comparison, "positive_infinity_count"
        ),
        negative_infinity_count=_infinity_count(
            reference, comparison, "negative_infinity_count"
        ),
        minimum=NumericDifference(
            reference_profile.minimum, comparison_profile.minimum
        ),
        maximum=NumericDifference(
            reference_profile.maximum, comparison_profile.maximum
        ),
        mean=NumericDifference(reference_profile.mean, comparison_profile.mean),
        median=NumericDifference(reference_profile.median, comparison_profile.median),
        standard_deviation=NumericDifference(
            reference_profile.standard_deviation,
            comparison_profile.standard_deviation,
        ),
        q1=NumericDifference(reference_profile.q1, comparison_profile.q1),
        q3=NumericDifference(reference_profile.q3, comparison_profile.q3),
        interquartile_range=NumericDifference(
            reference_profile.interquartile_range,
            comparison_profile.interquartile_range,
        ),
        range=NumericDifference(reference_profile.range, comparison_profile.range),
    )


def _infinity_count(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
    field: str,
) -> OptionalCountComparison:
    return OptionalCountComparison(
        _structure_count(reference, field),
        _structure_count(comparison, field),
    )


def _structure_count(column: ColumnAnalysis, field: str) -> Optional[int]:
    structure = column.evidence.numeric_structure
    if structure is None:
        return None
    return getattr(structure, field)


def _categorical_comparison(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
) -> CategoricalDescriptiveComparison:
    reference_profile = reference.categorical_analysis
    comparison_profile = comparison.categorical_analysis
    if reference_profile is None or comparison_profile is None:
        raise ValueError("categorical comparison requires two categorical profiles")
    comparison_counts = {
        level.value: level.count for level in comparison_profile.levels
    }
    reference_counts = {level.value: level.count for level in reference_profile.levels}
    shared = []
    reference_only = []
    for level in reference_profile.levels:
        if level.value in comparison_counts:
            shared.append(
                _category_level(
                    level.value,
                    level.count,
                    comparison_counts[level.value],
                    reference_profile.n_non_missing,
                    comparison_profile.n_non_missing,
                )
            )
        else:
            reference_only.append(
                _category_level(
                    level.value,
                    level.count,
                    None,
                    reference_profile.n_non_missing,
                    comparison_profile.n_non_missing,
                )
            )
    comparison_only = [
        _category_level(
            level.value,
            None,
            level.count,
            reference_profile.n_non_missing,
            comparison_profile.n_non_missing,
        )
        for level in comparison_profile.levels
        if level.value not in reference_counts
    ]
    reference_values = tuple(level.value for level in reference_profile.levels)
    comparison_values = tuple(level.value for level in comparison_profile.levels)
    return CategoricalDescriptiveComparison(
        n_non_missing=CountComparison(
            reference_profile.n_non_missing,
            comparison_profile.n_non_missing,
        ),
        missing_count=CountComparison(
            reference.evidence.basic.n_missing,
            comparison.evidence.basic.n_missing,
        ),
        n_observed=CountComparison(
            reference_profile.n_observed,
            comparison_profile.n_observed,
        ),
        most_frequent_count=CountComparison(
            reference_profile.most_frequent_count,
            comparison_profile.most_frequent_count,
        ),
        least_frequent_count=CountComparison(
            reference_profile.least_frequent_count,
            comparison_profile.least_frequent_count,
        ),
        most_frequent_proportion=ProportionDifference(
            reference_profile.most_frequent_proportion,
            comparison_profile.most_frequent_proportion,
        ),
        least_frequent_proportion=ProportionDifference(
            reference_profile.least_frequent_proportion,
            comparison_profile.least_frequent_proportion,
        ),
        reference_most_frequent_values=reference_profile.most_frequent_values,
        comparison_most_frequent_values=comparison_profile.most_frequent_values,
        reference_least_frequent_values=reference_profile.least_frequent_values,
        comparison_least_frequent_values=comparison_profile.least_frequent_values,
        shared_levels=tuple(shared),
        reference_only_levels=tuple(reference_only),
        comparison_only_levels=tuple(comparison_only),
        observed_sequences_equal=reference_values == comparison_values,
        reference_ordered=reference_profile.ordered,
        comparison_ordered=comparison_profile.ordered,
    )


def _category_level(
    value: object,
    reference_count: Optional[int],
    comparison_count: Optional[int],
    reference_population: int,
    comparison_population: int,
) -> ComparedCategoryLevel:
    return ComparedCategoryLevel(
        value=value,
        reference_count=reference_count,
        comparison_count=comparison_count,
        reference_proportion=_category_proportion(
            reference_count, reference_population
        ),
        comparison_proportion=_category_proportion(
            comparison_count, comparison_population
        ),
    )


def _category_proportion(count: Optional[int], population: int) -> Optional[float]:
    if count is None or population == 0:
        return None
    proportion = count / population
    if not math.isfinite(proportion) or proportion <= 0.0 or proportion > 1.0:
        raise ValueError("a category proportion must be finite and within (0, 1]")
    return proportion


def _boolean_comparison(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
) -> BooleanDescriptiveComparison:
    reference_profile = reference.boolean_analysis
    comparison_profile = comparison.boolean_analysis
    if reference_profile is None or comparison_profile is None:
        raise ValueError("boolean comparison requires two boolean profiles")
    return BooleanDescriptiveComparison(
        true_count=CountComparison(
            reference_profile.true_count,
            comparison_profile.true_count,
        ),
        false_count=CountComparison(
            reference_profile.false_count,
            comparison_profile.false_count,
        ),
        missing_count=CountComparison(
            reference.evidence.basic.n_missing,
            comparison.evidence.basic.n_missing,
        ),
        true_proportion=ProportionDifference(
            reference_profile.true_ratio,
            comparison_profile.true_ratio,
        ),
        false_proportion=ProportionDifference(
            reference_profile.false_ratio,
            comparison_profile.false_ratio,
        ),
    )


def _missingness_comparison(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
) -> ColumnMissingnessComparison:
    return ColumnMissingnessComparison(
        missing_count=CountComparison(
            reference.evidence.basic.n_missing,
            comparison.evidence.basic.n_missing,
        ),
        missing_proportion=ProportionDifference(
            reference.evidence.basic.missing_ratio,
            comparison.evidence.basic.missing_ratio,
        ),
    )


def _overview_comparison(
    reference: DatasetAnalysis,
    comparison: DatasetAnalysis,
) -> DatasetOverviewComparison:
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


def _physical_snapshot(column: ColumnAnalysis) -> PhysicalDtypeSnapshot:
    physical = column.physical
    return PhysicalDtypeSnapshot(
        family=physical.family,
        dtype_name=physical.dtype_name,
        categorical_ordered=physical.categorical_ordered,
    )


def _semantic_snapshot(column: ColumnAnalysis) -> SemanticSnapshot:
    interpretation = column.inferred.interpretation
    confidence = None if interpretation is None else interpretation.confidence
    return SemanticSnapshot(
        resolution_status=column.inferred.resolution.status,
        selected_type=column.inferred.selected_type,
        confidence=confidence,
    )


def _coverage_from_columns(
    columns: Tuple[ColumnComparison, ...],
) -> ComparisonCoverage:
    n_matched = 0
    n_reference_only = 0
    n_comparison_only = 0
    n_reordered = 0
    n_same = 0
    n_changed = 0
    n_unresolved = 0
    n_numeric = 0
    n_categorical = 0
    n_boolean = 0
    n_inapplicable = 0
    n_unavailable = 0
    for column in columns:
        status = column.alignment.status
        if status is ColumnMatchStatus.MATCHED:
            n_matched += 1
            if column.alignment.reordered:
                n_reordered += 1
            semantic = column.semantic
            reference_snapshot = semantic.reference
            comparison_snapshot = semantic.comparison
            if reference_snapshot is None or comparison_snapshot is None:
                raise ValueError("a matched column has two semantic snapshots")
            reference_type = reference_snapshot.selected_type
            comparison_type = comparison_snapshot.selected_type
            if reference_type is None and comparison_type is None:
                if (
                    reference_snapshot.resolution_status
                    is comparison_snapshot.resolution_status
                ):
                    n_unresolved += 1
                else:
                    n_changed += 1
            elif reference_type is comparison_type:
                n_same += 1
            else:
                n_changed += 1
        elif status is ColumnMatchStatus.REFERENCE_ONLY:
            n_reference_only += 1
        else:
            n_comparison_only += 1
        described = column.descriptive_status
        if described is DescriptiveComparisonStatus.NUMERIC:
            n_numeric += 1
        elif described is DescriptiveComparisonStatus.CATEGORICAL:
            n_categorical += 1
        elif described is DescriptiveComparisonStatus.BOOLEAN:
            n_boolean += 1
        elif described is DescriptiveComparisonStatus.INAPPLICABLE:
            n_inapplicable += 1
        else:
            n_unavailable += 1
    return ComparisonCoverage(
        n_columns=len(columns),
        n_matched_columns=n_matched,
        n_reference_only_columns=n_reference_only,
        n_comparison_only_columns=n_comparison_only,
        n_reordered_matched_columns=n_reordered,
        n_same_selected_type_columns=n_same,
        n_selected_type_changed_columns=n_changed,
        n_both_unresolved_columns=n_unresolved,
        n_numeric_descriptive_comparisons=n_numeric,
        n_categorical_descriptive_comparisons=n_categorical,
        n_boolean_descriptive_comparisons=n_boolean,
        n_inapplicable_descriptive_comparisons=n_inapplicable,
        n_unavailable_descriptive_comparisons=n_unavailable,
        deferred_families=DEFERRED_COMPARISON_FAMILIES,
    )


def _require_column_order(columns: Tuple[ColumnComparison, ...]) -> None:
    seen_comparison_only = False
    previous_reference = -1
    previous_comparison_only = -1
    for column in columns:
        status = column.alignment.status
        if status is ColumnMatchStatus.COMPARISON_ONLY:
            seen_comparison_only = True
            position = column.alignment.comparison_position
            if position is None or position <= previous_comparison_only:
                raise ValueError("comparison-only columns must follow physical order")
            previous_comparison_only = position
            continue
        if seen_comparison_only:
            raise ValueError("comparison-only columns must follow reference columns")
        position = column.alignment.reference_position
        if position is None or position <= previous_reference:
            raise ValueError("reference columns must follow physical order")
        previous_reference = position


def _require_descriptive_payload(column: ColumnComparison) -> None:
    status = column.descriptive_status
    payloads = (column.numeric, column.categorical, column.boolean)
    if status is DescriptiveComparisonStatus.NUMERIC:
        if (
            column.numeric is None
            or column.categorical is not None
            or column.boolean is not None
        ):
            raise ValueError("a numeric comparison keeps only the numeric payload")
        if column.descriptive_reason is not None:
            raise ValueError("a numeric comparison has no inapplicable reason")
        return
    if status is DescriptiveComparisonStatus.CATEGORICAL:
        if (
            column.categorical is None
            or column.numeric is not None
            or column.boolean is not None
        ):
            raise ValueError(
                "a categorical comparison keeps only the categorical payload"
            )
        if column.descriptive_reason is not None:
            raise ValueError("a categorical comparison has no inapplicable reason")
        return
    if status is DescriptiveComparisonStatus.BOOLEAN:
        if (
            column.boolean is None
            or column.numeric is not None
            or column.categorical is not None
        ):
            raise ValueError("a boolean comparison keeps only the boolean payload")
        if column.descriptive_reason is not None:
            raise ValueError("a boolean comparison has no inapplicable reason")
        return
    if any(payload is not None for payload in payloads):
        raise ValueError("an undescribed column has no descriptive payload")
    if column.descriptive_reason is None:
        raise ValueError("an undescribed column names why")
    if status is DescriptiveComparisonStatus.UNAVAILABLE:
        if column.descriptive_reason is not DescriptiveComparisonReason.PROFILE_ABSENT:
            raise ValueError("an unavailable comparison is a missing profile")
        return
    if status is not DescriptiveComparisonStatus.INAPPLICABLE:
        raise ValueError("descriptive status is not recognized")


def _finite_float_difference(comparison: float, reference: float) -> Optional[float]:
    difference = comparison - reference
    if not math.isfinite(difference):
        return None
    if difference == 0.0:
        return 0.0
    return difference


def _is_exact_metric(value: MetricNumber) -> bool:
    return type(value) is int or isinstance(value, Fraction)


def _require_metric(value: object, field: str) -> None:
    if value is None:
        return
    if type(value) is bool:
        raise TypeError(f"{field} must not be a bool")
    if type(value) is int:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{field} must be finite")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError(f"{field} must not be negative zero")
        return
    if isinstance(value, Fraction):
        return
    raise TypeError(f"{field} must be an int, float, Fraction, or None")


def _require_optional_proportion(value: object, field: str) -> None:
    if value is None:
        return
    if type(value) is not float or not math.isfinite(value):
        raise TypeError(f"{field} must be a finite float or None")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field} must be within [0, 1]")
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise ValueError(f"{field} must not be negative zero")


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_positive(value: object, field: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field} must be a positive int")


def _require_optional_position(value: object, field: str) -> None:
    if value is None:
        return
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int or None")


def _require_type(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _require_optional(value: object, expected: type, field: str) -> None:
    if value is not None and not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__} or None")


def _require_object_tuple(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be a tuple")


def _require_level_tuple(
    value: object,
    field: str,
    *,
    shared: bool,
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be a tuple")
    for level in value:
        if not isinstance(level, ComparedCategoryLevel):
            raise TypeError(f"{field} must contain compared category levels")
        if shared:
            if level.reference_count is None or level.comparison_count is None:
                raise ValueError("a shared category level is observed on both sides")
        elif field == "reference_only_levels":
            if level.reference_count is None or level.comparison_count is not None:
                raise ValueError("a reference-only level is observed on the reference")
        elif level.comparison_count is None or level.reference_count is not None:
            raise ValueError("a comparison-only level is observed on the comparison")
