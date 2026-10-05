"""The comparison result: per-column records, coverage, and the dataset record.

``ColumnComparison`` joins one aligned column's schema, missingness,
descriptive, and distribution-drift records. ``ComparisonCoverage``
counts what each column received. ``DatasetComparison`` checks that the
coverage, the column order, and the drift correction family agree with
the column records. These checks re-derive; they do not compute a
statistic that is not already stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

from pytics.analysis.compare.alignment import ColumnAlignment
from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.descriptive import BooleanDescriptiveComparison
from pytics.analysis.compare.descriptive import CategoricalDescriptiveComparison
from pytics.analysis.compare.descriptive import ColumnMissingnessComparison
from pytics.analysis.compare.descriptive import DescriptiveComparisonReason
from pytics.analysis.compare.descriptive import DescriptiveComparisonStatus
from pytics.analysis.compare.descriptive import NumericDescriptiveComparison
from pytics.analysis.compare.distribution_models import BooleanDistributionDrift
from pytics.analysis.compare.distribution_models import CategoricalDistributionDrift
from pytics.analysis.compare.distribution_models import DistributionDrift
from pytics.analysis.compare.distribution_models import DistributionDriftStatus
from pytics.analysis.compare.distribution_models import NumericDistributionDrift
from pytics.analysis.compare.overview import DatasetOverviewComparison
from pytics.analysis.compare.relationship_models import RelationshipDrift
from pytics.analysis.compare.relationship_models import RelationshipDriftCoverage
from pytics.analysis.compare.relationship_models import coverage_from_relationships
from pytics.analysis.compare.schema import PhysicalDtypeComparison
from pytics.analysis.compare.schema import SemanticComparison
from pytics.analysis.compare.values import _require_count
from pytics.analysis.compare.values import _require_optional
from pytics.analysis.compare.values import _require_type
from pytics.analysis.relationships.adjustment import benjamini_hochberg
from pytics.analysis.relationships.models import InferentialValidity
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import inferential_p_value_eligible

_DRIFT_PAYLOAD = {
    DistributionDriftStatus.NUMERIC: (
        NumericDistributionDrift,
        DescriptiveComparisonStatus.NUMERIC,
    ),
    DistributionDriftStatus.CATEGORICAL: (
        CategoricalDistributionDrift,
        DescriptiveComparisonStatus.CATEGORICAL,
    ),
    DistributionDriftStatus.BOOLEAN: (
        BooleanDistributionDrift,
        DescriptiveComparisonStatus.BOOLEAN,
    ),
}

_DESCRIBED = frozenset(
    {
        DescriptiveComparisonStatus.NUMERIC,
        DescriptiveComparisonStatus.CATEGORICAL,
        DescriptiveComparisonStatus.BOOLEAN,
    }
)


class DeferredComparisonFamily(Enum):
    """Comparison families this result deliberately does not contain.

    Their absence is not evidence that those aspects were unchanged.
    Relationship change and target change are separate records on the
    comparison. They are not members of this list.
    """

    ANOMALY_COMPARISON = "anomaly_comparison"
    MISSINGNESS_PATTERN_DRIFT = "missingness_pattern_drift"
    DUPLICATE_GROUP_MATCHING = "duplicate_group_matching"
    ROW_ALIGNMENT = "row_alignment"


DEFERRED_COMPARISON_FAMILIES: Tuple[DeferredComparisonFamily, ...] = (
    DeferredComparisonFamily.ANOMALY_COMPARISON,
    DeferredComparisonFamily.MISSINGNESS_PATTERN_DRIFT,
    DeferredComparisonFamily.DUPLICATE_GROUP_MATCHING,
    DeferredComparisonFamily.ROW_ALIGNMENT,
)


@dataclass(frozen=True)
class ColumnComparison:
    """Alignment, schema, missingness, descriptive change, and distribution drift.

    The descriptive payload matches ``descriptive_status``. An inapplicable
    or unavailable status has no payload. ``distribution`` matches
    ``distribution_status``. A column has distribution drift only when it
    has the matching typed descriptive comparison, and the drift record's
    population agrees with that comparison.
    """

    alignment: ColumnAlignment
    physical: PhysicalDtypeComparison
    semantic: SemanticComparison
    missingness: Optional[ColumnMissingnessComparison]
    descriptive_status: DescriptiveComparisonStatus
    descriptive_reason: Optional[DescriptiveComparisonReason]
    distribution_status: DistributionDriftStatus
    numeric: Optional[NumericDescriptiveComparison] = None
    categorical: Optional[CategoricalDescriptiveComparison] = None
    boolean: Optional[BooleanDescriptiveComparison] = None
    distribution: Optional[DistributionDrift] = None

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
        _require_type(
            self.distribution_status, DistributionDriftStatus, "distribution_status"
        )
        _require_optional(self.numeric, NumericDescriptiveComparison, "numeric")
        _require_optional(
            self.categorical, CategoricalDescriptiveComparison, "categorical"
        )
        _require_optional(self.boolean, BooleanDescriptiveComparison, "boolean")
        _require_descriptive_payload(self)
        _require_distribution_payload(self)
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

    Distribution-drift columns, not-eligible columns, and columns whose
    source values were not supplied sum to ``n_columns``. Among the drift
    records, an unavailable primary effect or test is counted, not
    hidden. ``n_distribution_tests`` counts computationally available
    primary p-values, including an asymptotic chi-square tail whose
    Cochran convention failed. The drift correction family is the
    inferentially valid subset of those p-values, which can be smaller.
    No p-value does not mean no drift. An invalid p-value does not mean
    the distance is absent.
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
    n_numeric_distribution_drift: int
    n_categorical_distribution_drift: int
    n_boolean_distribution_drift: int
    n_distribution_not_eligible: int
    n_distribution_source_not_supplied: int
    n_distribution_primary_effects_unavailable: int
    n_distribution_tests: int
    n_distribution_tests_unavailable: int
    n_wasserstein_distances_unavailable: int
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
            "n_numeric_distribution_drift",
            "n_categorical_distribution_drift",
            "n_boolean_distribution_drift",
            "n_distribution_not_eligible",
            "n_distribution_source_not_supplied",
            "n_distribution_primary_effects_unavailable",
            "n_distribution_tests",
            "n_distribution_tests_unavailable",
            "n_wasserstein_distances_unavailable",
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
        drifted = self.n_distribution_drift_records
        if (
            drifted
            + self.n_distribution_not_eligible
            + self.n_distribution_source_not_supplied
            != self.n_columns
        ):
            raise ValueError("distribution coverage must sum to n_columns")
        if self.n_distribution_tests + self.n_distribution_tests_unavailable != drifted:
            raise ValueError("drift tests must account for every drift record")
        if self.n_distribution_primary_effects_unavailable > drifted:
            raise ValueError("unavailable effects cannot exceed drift records")
        if self.n_wasserstein_distances_unavailable > self.n_numeric_distribution_drift:
            raise ValueError("unavailable Wasserstein distances need numeric records")

    @property
    def n_distribution_drift_records(self) -> int:
        """Columns that received a distribution-drift record."""
        return (
            self.n_numeric_distribution_drift
            + self.n_categorical_distribution_drift
            + self.n_boolean_distribution_drift
        )


@dataclass(frozen=True)
class DatasetComparison:
    """Structured comparison of two dataset analyses.

    ``columns`` follows the reference physical order, then comparison-only
    columns in comparison physical order. ``relationships`` follows
    ascending reference positions of aligned pairs. ``target`` is present
    only when the caller requested a target. The result does not keep
    either analysis or either DataFrame.

    The available primary drift tests form one Benjamini–Hochberg family,
    in column order. Relationship-change tests are not members of that
    family. Every distribution-drift member stores that family's adjusted
    value.
    """

    overview: DatasetOverviewComparison
    columns: Tuple[ColumnComparison, ...]
    coverage: ComparisonCoverage
    relationships: Tuple[RelationshipDrift, ...]
    relationship_coverage: RelationshipDriftCoverage
    target: Optional["TargetDriftAnalysis"] = None

    def __post_init__(self) -> None:
        _require_type(self.overview, DatasetOverviewComparison, "overview")
        if not isinstance(self.columns, tuple):
            raise TypeError("columns must be a tuple")
        for column in self.columns:
            if not isinstance(column, ColumnComparison):
                raise TypeError("columns must contain ColumnComparison records")
        _require_type(self.coverage, ComparisonCoverage, "coverage")
        if self.coverage != coverage_from_columns(self.columns):
            raise ValueError("coverage does not match the column comparisons")
        _require_column_order(self.columns)
        _require_drift_family(self.columns)
        if not isinstance(self.relationships, tuple):
            raise TypeError("relationships must be a tuple")
        _require_type(
            self.relationship_coverage,
            RelationshipDriftCoverage,
            "relationship_coverage",
        )
        if self.relationship_coverage != coverage_from_relationships(
            self.relationships
        ):
            raise ValueError("relationship coverage does not match the records")
        _require_relationship_order(self.relationships)
        if self.target is not None:
            from pytics.analysis.compare.target import require_target_links
            from pytics.analysis.compare.target_models import TargetDriftAnalysis

            if not isinstance(self.target, TargetDriftAnalysis):
                raise TypeError("target must be a TargetDriftAnalysis")
            require_target_links(self.target, self.columns, self.relationships)


def coverage_from_columns(
    columns: Tuple[ColumnComparison, ...],
) -> ComparisonCoverage:
    """Count what each column received. Nothing is recalculated."""
    n_matched = 0
    n_reference_only = 0
    n_comparison_only = 0
    n_reordered = 0
    n_same = 0
    n_changed = 0
    n_unresolved = 0
    described = {status: 0 for status in DescriptiveComparisonStatus}
    drifted = {status: 0 for status in DistributionDriftStatus}
    n_effects_unavailable = 0
    n_tests = 0
    n_tests_unavailable = 0
    n_wasserstein_unavailable = 0
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
        described[column.descriptive_status] += 1
        drifted[column.distribution_status] += 1
        record = column.distribution
        if record is None:
            continue
        if record.primary_effect.availability is ResultAvailability.UNAVAILABLE:
            n_effects_unavailable += 1
        if record.test.availability is ResultAvailability.AVAILABLE:
            n_tests += 1
        else:
            n_tests_unavailable += 1
        if (
            isinstance(record, NumericDistributionDrift)
            and record.wasserstein_distance.availability
            is ResultAvailability.UNAVAILABLE
        ):
            n_wasserstein_unavailable += 1
    return ComparisonCoverage(
        n_columns=len(columns),
        n_matched_columns=n_matched,
        n_reference_only_columns=n_reference_only,
        n_comparison_only_columns=n_comparison_only,
        n_reordered_matched_columns=n_reordered,
        n_same_selected_type_columns=n_same,
        n_selected_type_changed_columns=n_changed,
        n_both_unresolved_columns=n_unresolved,
        n_numeric_descriptive_comparisons=described[
            DescriptiveComparisonStatus.NUMERIC
        ],
        n_categorical_descriptive_comparisons=described[
            DescriptiveComparisonStatus.CATEGORICAL
        ],
        n_boolean_descriptive_comparisons=described[
            DescriptiveComparisonStatus.BOOLEAN
        ],
        n_inapplicable_descriptive_comparisons=described[
            DescriptiveComparisonStatus.INAPPLICABLE
        ],
        n_unavailable_descriptive_comparisons=described[
            DescriptiveComparisonStatus.UNAVAILABLE
        ],
        n_numeric_distribution_drift=drifted[DistributionDriftStatus.NUMERIC],
        n_categorical_distribution_drift=drifted[DistributionDriftStatus.CATEGORICAL],
        n_boolean_distribution_drift=drifted[DistributionDriftStatus.BOOLEAN],
        n_distribution_not_eligible=drifted[DistributionDriftStatus.NOT_ELIGIBLE],
        n_distribution_source_not_supplied=drifted[
            DistributionDriftStatus.SOURCE_VALUES_NOT_SUPPLIED
        ],
        n_distribution_primary_effects_unavailable=n_effects_unavailable,
        n_distribution_tests=n_tests,
        n_distribution_tests_unavailable=n_tests_unavailable,
        n_wasserstein_distances_unavailable=n_wasserstein_unavailable,
        deferred_families=DEFERRED_COMPARISON_FAMILIES,
    )


def _require_relationship_order(relationships: Tuple[RelationshipDrift, ...]) -> None:
    previous = (-1, -1)
    for record in relationships:
        if not isinstance(record, RelationshipDrift):
            raise TypeError("relationships must contain RelationshipDrift records")
        key = (
            record.alignment.first.reference_position,
            record.alignment.second.reference_position,
        )
        if key <= previous:
            raise ValueError("relationship drift follows ascending reference positions")
        previous = key


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


def _require_drift_family(columns: Tuple[ColumnComparison, ...]) -> None:
    """Every inferentially valid primary drift test holds this family's BH value."""
    eligible = []
    for column in columns:
        record = column.distribution
        if record is None:
            continue
        test = record.test
        if test.availability is not ResultAvailability.AVAILABLE:
            continue
        if inferential_p_value_eligible(
            test.availability,
            test.inferential_validity,  # type: ignore[arg-type]
        ):
            eligible.append(test)
            continue
        if test.inferential_validity is not InferentialValidity.INVALID:
            raise ValueError("a computed drift p-value is valid or invalid")
        if (
            test.adjustment is not MultipleTestingAdjustment.NOT_APPLIED
            or test.adjusted_p_value is not None
        ):
            raise ValueError("an inferentially invalid drift test is not adjusted")
    adjusted = benjamini_hochberg(tuple(test.p_value for test in eligible))
    for test, expected in zip(eligible, adjusted):
        if test.adjustment is not MultipleTestingAdjustment.BENJAMINI_HOCHBERG:
            raise ValueError("a valid drift test belongs to the drift family")
        if test.adjusted_p_value != expected:
            raise ValueError("adjusted drift p-values must match the drift family")


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


def _require_distribution_payload(column: ColumnComparison) -> None:
    status = column.distribution_status
    record = column.distribution
    expected = _DRIFT_PAYLOAD.get(status)
    if expected is None:
        if record is not None:
            raise ValueError("a column without drift has no drift payload")
        eligible = column.descriptive_status in _DESCRIBED
        if status is DistributionDriftStatus.NOT_ELIGIBLE and eligible:
            raise ValueError("a described column is eligible for distribution drift")
        if (
            status is DistributionDriftStatus.SOURCE_VALUES_NOT_SUPPLIED
            and not eligible
        ):
            raise ValueError("only an eligible column waits for source values")
        return
    record_type, descriptive_status = expected
    if not isinstance(record, record_type):
        raise ValueError("the drift payload must match the drift status")
    if column.descriptive_status is not descriptive_status:
        raise ValueError("drift follows the matching descriptive comparison")
    population = record.population
    if isinstance(record, NumericDistributionDrift):
        counts = column.numeric.finite_count  # type: ignore[union-attr]
    elif isinstance(record, CategoricalDistributionDrift):
        counts = column.categorical.n_non_missing  # type: ignore[union-attr]
        _require_categorical_support(record, column.categorical)  # type: ignore[arg-type]
    else:
        boolean = column.boolean
        counts = None
        if (
            population.n_reference
            != boolean.true_count.reference + boolean.false_count.reference  # type: ignore[union-attr]
            or population.n_comparison
            != boolean.true_count.comparison + boolean.false_count.comparison  # type: ignore[union-attr]
        ):
            raise ValueError(
                "boolean drift population must match the descriptive counts"
            )
        effect = record.true_proportion_difference
        if (
            effect.availability is ResultAvailability.AVAILABLE
            and effect.value != boolean.true_proportion.change  # type: ignore[union-attr]
        ):
            raise ValueError("boolean drift reuses the descriptive proportion change")
    if counts is not None and (
        population.n_reference != counts.reference
        or population.n_comparison != counts.comparison
    ):
        raise ValueError("drift population must match the descriptive comparison")


def _require_categorical_support(
    record: CategoricalDistributionDrift,
    descriptive: CategoricalDescriptiveComparison,
) -> None:
    n_levels = (
        len(descriptive.shared_levels)
        + len(descriptive.reference_only_levels)
        + len(descriptive.comparison_only_levels)
    )
    if record.n_levels != n_levels:
        raise ValueError("categorical drift levels must match the partition")
    reference_only = sum(
        level.reference_count for level in descriptive.reference_only_levels
    )
    comparison_only = sum(
        level.comparison_count for level in descriptive.comparison_only_levels
    )
    if (
        record.n_reference_only_observations != reference_only
        or record.n_comparison_only_observations != comparison_only
    ):
        raise ValueError("one-sided observations must match the partition")
