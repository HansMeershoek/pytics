"""Retained descriptive facts compared for one matched column.

A matched Numeric pair compares the retained finite profile, the basic
missing count, and the numeric-structure infinity counts. A matched
Categorical pair partitions the retained observed levels into shared,
reference-only, and comparison-only levels under the Python equality the
categorical profile already uses. A matched Boolean pair compares true,
false, and missing counts. Missingness counts are compared for every
matched column.

Eligibility lives here. A semantic mismatch, Identifier, Datetime,
Timedelta, Text, Empty, Constant, an unresolved or ambiguous reading,
and a missing profile are explicit statuses. They are not equality.
Distribution drift reads these records and does not decide eligibility
again. Nothing here reads a frame.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.compare.values import CountComparison
from pytics.analysis.compare.values import NumericDifference
from pytics.analysis.compare.values import OptionalCountComparison
from pytics.analysis.compare.values import ProportionDifference
from pytics.analysis.compare.values import _require_optional_proportion
from pytics.analysis.compare.values import _require_positive
from pytics.analysis.compare.values import _require_type
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


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


_NO_SPECIALIZED_COMPARATOR = {
    SemanticType.IDENTIFIER: DescriptiveComparisonReason.IDENTIFIER,
    SemanticType.DATETIME: DescriptiveComparisonReason.DATETIME,
    SemanticType.TIMEDELTA: DescriptiveComparisonReason.TIMEDELTA,
    SemanticType.TEXT: DescriptiveComparisonReason.TEXT,
    SemanticType.EMPTY: DescriptiveComparisonReason.EMPTY,
    SemanticType.CONSTANT: DescriptiveComparisonReason.CONSTANT,
}


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

    A change in class share is a descriptive change. It is not a
    degradation. The inferential evidence for it is the column's
    distribution-drift record.
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
class _Descriptive:
    """Descriptive status and payload for one matched column. Temporary."""

    status: DescriptiveComparisonStatus
    reason: Optional[DescriptiveComparisonReason]
    numeric: Optional[NumericDescriptiveComparison] = None
    categorical: Optional[CategoricalDescriptiveComparison] = None
    boolean: Optional[BooleanDescriptiveComparison] = None


def descriptive_comparison(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
) -> _Descriptive:
    """Choose and build the typed descriptive comparison of a matched pair."""
    reference_type = reference.inferred.selected_type
    comparison_type = comparison.inferred.selected_type
    if reference_type is not comparison_type:
        return _inapplicable(DescriptiveComparisonReason.SEMANTIC_MISMATCH)
    if reference_type is None:
        reference_status = reference.inferred.resolution.status
        comparison_status = comparison.inferred.resolution.status
        if reference_status is not comparison_status:
            reason = DescriptiveComparisonReason.SEMANTIC_MISMATCH
        elif reference_status is ResolutionStatus.AMBIGUOUS:
            reason = DescriptiveComparisonReason.AMBIGUOUS
        else:
            reason = DescriptiveComparisonReason.UNRESOLVED
        return _inapplicable(reason)
    if reference_type is SemanticType.NUMERIC:
        if reference.numeric_analysis is None or comparison.numeric_analysis is None:
            return _profile_absent()
        return _Descriptive(
            status=DescriptiveComparisonStatus.NUMERIC,
            reason=None,
            numeric=_numeric_comparison(reference, comparison),
        )
    if reference_type is SemanticType.CATEGORICAL:
        if (
            reference.categorical_analysis is None
            or comparison.categorical_analysis is None
        ):
            return _profile_absent()
        return _Descriptive(
            status=DescriptiveComparisonStatus.CATEGORICAL,
            reason=None,
            categorical=_categorical_comparison(reference, comparison),
        )
    if reference_type is SemanticType.BOOLEAN:
        if reference.boolean_analysis is None or comparison.boolean_analysis is None:
            return _profile_absent()
        return _Descriptive(
            status=DescriptiveComparisonStatus.BOOLEAN,
            reason=None,
            boolean=_boolean_comparison(reference, comparison),
        )
    reason = _NO_SPECIALIZED_COMPARATOR.get(reference_type)
    if reason is None:
        raise ValueError("selected semantic type has no comparison rule")
    return _inapplicable(reason)


def missingness_comparison(
    reference: ColumnAnalysis,
    comparison: ColumnAnalysis,
) -> ColumnMissingnessComparison:
    """Basic missing counts of one matched column."""
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


def _inapplicable(reason: DescriptiveComparisonReason) -> _Descriptive:
    return _Descriptive(status=DescriptiveComparisonStatus.INAPPLICABLE, reason=reason)


def _profile_absent() -> _Descriptive:
    return _Descriptive(
        status=DescriptiveComparisonStatus.UNAVAILABLE,
        reason=DescriptiveComparisonReason.PROFILE_ABSENT,
    )


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
