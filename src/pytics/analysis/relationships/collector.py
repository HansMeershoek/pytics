"""Dataset relationship collection and product projection.

Eligibility uses the selected semantic type. The calculated families are
selected Numeric × Numeric, selected Numeric × Categorical, selected
Boolean × Boolean, selected Numeric × Boolean, and selected Categorical
× Categorical. Recognized families that are not calculated are counted,
including Categorical × Boolean and the datetime directions. Ineligible
pairs are semantic pairs the contract does not treat as relationship
candidates. They are counted and not read. Each needed source column is
prepared once. Those temporary arrays are discarded before the collector
returns. After the pair records exist, one dataset-level correction
adjusts the available primary p-values. The summary builder copies the
retained records and does not calculate a statistic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
import pandas as pd

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column_label import observed_labels_equal
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.relationships.adjustment import adjust_primary_p_values
from pytics.analysis.relationships.boolean_boolean import _read_boolean_column
from pytics.analysis.relationships.boolean_boolean import analyze as _analyze_boolean
from pytics.analysis.relationships.categorical_categorical import (
    analyze as _analyze_categorical_categorical,
)
from pytics.analysis.relationships.models import AssociationResult
from pytics.analysis.relationships.models import CategoricalAssociationEstimate
from pytics.analysis.relationships.models import CategoricalCategoricalRelationship
from pytics.analysis.relationships.models import CategoricalContingencyTable
from pytics.analysis.relationships.models import CategoricalIndependenceTest
from pytics.analysis.relationships.models import ExpectedCountDiagnostics
from pytics.analysis.relationships.models import BooleanAssociationEstimate
from pytics.analysis.relationships.models import BooleanBooleanRelationship
from pytics.analysis.relationships.models import BooleanContingencyTable
from pytics.analysis.relationships.models import BooleanDirectionalEstimate
from pytics.analysis.relationships.models import BooleanGroupSummary
from pytics.analysis.relationships.models import BooleanIndependenceTest
from pytics.analysis.relationships.models import CategoricalGroupSummary
from pytics.analysis.relationships.models import ConditionalOutcomeProbability
from pytics.analysis.relationships.models import CorrelationEstimate
from pytics.analysis.relationships.models import CorrelationInterval
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import GroupEffectEstimate
from pytics.analysis.relationships.models import MeanDifferenceEstimate
from pytics.analysis.relationships.models import MeanDifferenceInterval
from pytics.analysis.relationships.models import MeanDifferenceTest
from pytics.analysis.relationships.models import NumericBooleanRelationship
from pytics.analysis.relationships.models import NumericCategoricalRelationship
from pytics.analysis.relationships.models import NumericNumericRelationship
from pytics.analysis.relationships.models import OmnibusAnovaResult
from pytics.analysis.relationships.models import RelationshipAnalysis
from pytics.analysis.relationships.models import RelationshipRecord
from pytics.analysis.relationships.models import RelationshipsSummary
from pytics.analysis.relationships.models import StandardizedMeanDifference
from pytics.analysis.relationships.models import UnimplementedFamilyCount
from pytics.analysis.relationships.models import UnimplementedRelationshipFamily
from pytics.analysis.relationships.models.coverage import SelectedPairCoverage
from pytics.analysis.relationships.models.coverage import classify_selected_pair
from pytics.analysis.relationships.models import _require_nonnegative
from pytics.analysis.relationships.numeric_boolean import (
    analyze as _analyze_numeric_boolean,
)
from pytics.analysis.relationships.numeric_categorical import _read_categorical_column
from pytics.analysis.relationships.numeric_categorical import (
    analyze as _analyze_numeric_categorical,
)
from pytics.analysis.relationships.numeric_numeric import _association_methods
from pytics.analysis.relationships.numeric_numeric import _read_numeric_column
from pytics.semantics.interpretation import SemanticType


class _Eligibility(Enum):
    """Classifier outcome other than an unimplemented recognized family."""

    SUPPORTED = "supported"
    INELIGIBLE = "ineligible"


_PairClass = Union[UnimplementedRelationshipFamily, _Eligibility]


@dataclass(frozen=True)
class _Classification:
    """Pair counts derived from selected semantic types."""

    supported_pairs: Tuple[Tuple[int, int], ...]
    unimplemented: Tuple[UnimplementedFamilyCount, ...]
    n_ineligible_pairs: int


def collect_relationship_analysis(
    frame: pd.DataFrame,
    columns: Tuple[ColumnAnalysis, ...],
) -> RelationshipAnalysis:
    """Describe eligible relationship pairs in one DataFrame.

    ``columns`` are the column analyses already produced for ``frame``.
    Selected semantic types decide eligibility before any pair is read.
    Each Numeric column that belongs to a supported pair is converted
    once. Each Categorical column that belongs to a supported pair is
    read once. Each Boolean column that belongs to a Boolean × Boolean or
    Numeric × Boolean pair is read once. Unsupported pairs do not read
    raw values. Temporary arrays are discarded before return.
    The DataFrame is not modified.

    A component that cannot produce a finite result is recorded as
    unavailable. That state does not raise, and it does not discard the
    pair or the other component. Available primary p-values are then
    adjusted together. Complementary and unavailable p-values are not.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("collect_relationship_analysis expects a pandas DataFrame")
    _require_aligned_columns(frame, columns)
    n_rows = int(frame.shape[0])
    relationships = adjust_primary_p_values(
        _relationships_for_frame(frame, columns, n_rows)
    )
    return relationship_analysis_for_columns(
        columns,
        n_rows=n_rows,
        relationships=relationships,
    )


def relationship_analysis_for_columns(
    columns: Tuple[ColumnAnalysis, ...],
    *,
    n_rows: int,
    relationships: Tuple[
        RelationshipRecord,
        ...,
    ] = (),
) -> RelationshipAnalysis:
    """Attach relationship records to the selected-type pair counts.

    This does not read values and does not calculate statistics.
    ``relationships`` must already be the supported pairs, in ascending
    position order. A supported pair with no record is invalid.
    """
    _require_nonnegative(n_rows, "n_rows")
    _require_column_tuple(columns, n_rows)
    classification = _classify_columns(columns)
    _require_recorded_pairs(classification, relationships, columns, n_rows)
    unimplemented_total = sum(item.n_pairs for item in classification.unimplemented)
    return RelationshipAnalysis(
        n_rows=n_rows,
        n_total_pairs=len(columns) * (len(columns) - 1) // 2,
        n_supported_pairs=len(classification.supported_pairs),
        n_analyzed_pairs=len(relationships),
        n_unimplemented_family_pairs=unimplemented_total,
        n_ineligible_pairs=classification.n_ineligible_pairs,
        unimplemented_family_counts=classification.unimplemented,
        relationships=relationships,
    )


def build_relationships_summary(analysis: object) -> RelationshipsSummary:
    """Project retained relationship facts into a product summary.

    The argument must already be a ``DatasetAnalysis``. A DataFrame is
    not accepted and is not analyzed. Statistics are not recomputed.
    """
    # Local import: dataset analysis retains RelationshipAnalysis, so this
    # module cannot import DatasetAnalysis at load time.
    from pytics.analysis.dataset import DatasetAnalysis as DatasetAnalysisType

    if not isinstance(analysis, DatasetAnalysisType):
        raise TypeError("build_relationships_summary expects a DatasetAnalysis")
    retained = analysis.relationship_analysis
    return RelationshipsSummary(
        n_rows=analysis.n_rows,
        n_columns=analysis.n_columns,
        n_total_pairs=retained.n_total_pairs,
        n_supported_pairs=retained.n_supported_pairs,
        n_analyzed_pairs=retained.n_analyzed_pairs,
        n_unimplemented_family_pairs=retained.n_unimplemented_family_pairs,
        n_ineligible_pairs=retained.n_ineligible_pairs,
        unimplemented_family_counts=tuple(
            UnimplementedFamilyCount(family=item.family, n_pairs=item.n_pairs)
            for item in retained.unimplemented_family_counts
        ),
        relationships=tuple(
            _copy_relationship(item) for item in retained.relationships
        ),
    )


def _require_relationship_attachment(
    analysis: RelationshipAnalysis,
    columns: Tuple[ColumnAnalysis, ...],
    *,
    n_rows: int,
) -> None:
    """Check retained relationships against the selected semantic types."""
    if not isinstance(analysis, RelationshipAnalysis):
        raise TypeError("relationship_analysis must be a RelationshipAnalysis")
    expected = relationship_analysis_for_columns(
        columns,
        n_rows=n_rows,
        relationships=analysis.relationships,
    )
    if analysis != expected:
        raise ValueError(
            "relationship analysis must match the selected semantic pair counts"
        )


def _relationships_for_frame(
    frame: pd.DataFrame,
    columns: Tuple[ColumnAnalysis, ...],
    n_rows: int,
) -> Tuple[RelationshipRecord, ...]:
    """Calculate one record per supported pair.

    A Numeric column is read once even when it pairs with several other
    columns. A Categorical column is read once even when it pairs with
    several Numeric or Categorical columns. A Boolean column is read once
    even when it pairs with several Boolean or Numeric columns. Those
    preparations are local to this function.
    """
    classification = _classify_columns(columns)
    if not classification.supported_pairs:
        return ()
    numeric_positions, categorical_positions, boolean_positions = (
        _preparation_positions(
            columns,
            classification.supported_pairs,
        )
    )
    numeric_columns = {
        position: _read_numeric_column(frame.iloc[:, position])
        for position in numeric_positions
    }
    categorical_columns = {
        position: _read_categorical_column(frame.iloc[:, position])
        for position in categorical_positions
    }
    boolean_columns = {
        position: _read_boolean_column(frame.iloc[:, position])
        for position in boolean_positions
    }
    records: List[RelationshipRecord] = []
    for left, right in classification.supported_pairs:
        left_type = columns[left].inferred.selected_type
        right_type = columns[right].inferred.selected_type
        if left_type is SemanticType.NUMERIC and right_type is SemanticType.NUMERIC:
            records.append(
                _numeric_numeric_record(
                    columns,
                    numeric_columns,
                    left,
                    right,
                    n_rows,
                )
            )
        elif left_type is SemanticType.BOOLEAN and right_type is SemanticType.BOOLEAN:
            records.append(
                _boolean_boolean_record(
                    columns,
                    boolean_columns,
                    left,
                    right,
                    n_rows,
                )
            )
        elif {left_type, right_type} == {SemanticType.NUMERIC, SemanticType.BOOLEAN}:
            records.append(
                _numeric_boolean_record(
                    columns,
                    numeric_columns,
                    boolean_columns,
                    left,
                    right,
                    n_rows,
                )
            )
        elif {left_type, right_type} == {
            SemanticType.NUMERIC,
            SemanticType.CATEGORICAL,
        }:
            records.append(
                _numeric_categorical_record(
                    columns,
                    numeric_columns,
                    categorical_columns,
                    left,
                    right,
                    n_rows,
                )
            )
        elif (
            left_type is SemanticType.CATEGORICAL
            and right_type is SemanticType.CATEGORICAL
        ):
            records.append(
                _categorical_categorical_record(
                    columns,
                    categorical_columns,
                    left,
                    right,
                    n_rows,
                )
            )
        else:
            raise TypeError("supported pair has no relationship calculator")
    return tuple(records)


def _preparation_positions(
    columns: Tuple[ColumnAnalysis, ...],
    pairs: Tuple[Tuple[int, int], ...],
) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    """Columns that a supported pair actually reads, in pair order."""
    numeric: List[int] = []
    categorical: List[int] = []
    boolean: List[int] = []
    seen_numeric = set()
    seen_categorical = set()
    seen_boolean = set()
    for left, right in pairs:
        for position in (left, right):
            semantic = columns[position].inferred.selected_type
            if semantic is SemanticType.NUMERIC and position not in seen_numeric:
                seen_numeric.add(position)
                numeric.append(position)
            elif (
                semantic is SemanticType.CATEGORICAL
                and position not in seen_categorical
            ):
                seen_categorical.add(position)
                categorical.append(position)
            elif semantic is SemanticType.BOOLEAN and position not in seen_boolean:
                seen_boolean.add(position)
                boolean.append(position)
    return tuple(numeric), tuple(categorical), tuple(boolean)


def _numeric_numeric_record(
    columns: Tuple[ColumnAnalysis, ...],
    numeric_columns: dict,
    left: int,
    right: int,
    n_rows: int,
) -> NumericNumericRelationship:
    left_values, left_finite = numeric_columns[left]
    right_values, right_finite = numeric_columns[right]
    paired_rows = np.flatnonzero(left_finite & right_finite)
    methods = _association_methods(
        left_values[paired_rows],
        right_values[paired_rows],
    )
    return NumericNumericRelationship(
        left_position=left,
        left_label=columns[left].label,
        right_position=right,
        right_label=columns[right].label,
        n_total_rows=n_rows,
        n_paired=int(paired_rows.size),
        methods=methods,
    )


def _numeric_categorical_record(
    columns: Tuple[ColumnAnalysis, ...],
    numeric_columns: dict,
    categorical_columns: dict,
    left: int,
    right: int,
    n_rows: int,
) -> NumericCategoricalRelationship:
    numeric_position, categorical_position = _role_positions(
        left,
        right,
        columns[left].inferred.selected_type,
    )
    numeric_values, numeric_finite = numeric_columns[numeric_position]
    category_codes, categories = categorical_columns[categorical_position]
    return _analyze_numeric_categorical(
        numeric_values,
        numeric_finite,
        category_codes,
        categories,
        left_position=left,
        left_label=columns[left].label,
        right_position=right,
        right_label=columns[right].label,
        numeric_position=numeric_position,
        categorical_position=categorical_position,
        n_total_rows=n_rows,
    )


def _boolean_boolean_record(
    columns: Tuple[ColumnAnalysis, ...],
    boolean_columns: dict,
    left: int,
    right: int,
    n_rows: int,
) -> BooleanBooleanRelationship:
    left_observed, left_is_true = boolean_columns[left]
    right_observed, right_is_true = boolean_columns[right]
    return _analyze_boolean(
        left_observed,
        left_is_true,
        right_observed,
        right_is_true,
        left_position=left,
        left_label=columns[left].label,
        right_position=right,
        right_label=columns[right].label,
        n_total_rows=n_rows,
    )


def _numeric_boolean_record(
    columns: Tuple[ColumnAnalysis, ...],
    numeric_columns: dict,
    boolean_columns: dict,
    left: int,
    right: int,
    n_rows: int,
) -> NumericBooleanRelationship:
    numeric_position, boolean_position = _role_positions(
        left,
        right,
        columns[left].inferred.selected_type,
    )
    numeric_values, numeric_finite = numeric_columns[numeric_position]
    boolean_observed, boolean_is_true = boolean_columns[boolean_position]
    return _analyze_numeric_boolean(
        numeric_values,
        numeric_finite,
        boolean_observed,
        boolean_is_true,
        left_position=left,
        left_label=columns[left].label,
        right_position=right,
        right_label=columns[right].label,
        numeric_position=numeric_position,
        boolean_position=boolean_position,
        n_total_rows=n_rows,
    )


def _categorical_categorical_record(
    columns: Tuple[ColumnAnalysis, ...],
    categorical_columns: dict,
    left: int,
    right: int,
    n_rows: int,
) -> CategoricalCategoricalRelationship:
    left_codes, left_categories = categorical_columns[left]
    right_codes, right_categories = categorical_columns[right]
    return _analyze_categorical_categorical(
        left_codes,
        left_categories,
        right_codes,
        right_categories,
        left_position=left,
        left_label=columns[left].label,
        right_position=right,
        right_label=columns[right].label,
        n_total_rows=n_rows,
    )


def _role_positions(
    left: int,
    right: int,
    left_type: object,
) -> Tuple[int, int]:
    """Return the Numeric position, then the other role's position."""
    if left_type is SemanticType.NUMERIC:
        return left, right
    return right, left


def _classify_columns(columns: Tuple[ColumnAnalysis, ...]) -> _Classification:
    """Count canonical pairs from selected types, without reading values."""
    supported: List[Tuple[int, int]] = []
    unimplemented_counts: Dict[UnimplementedRelationshipFamily, int] = {}
    ineligible = 0
    for left in range(len(columns)):
        left_type = columns[left].inferred.selected_type
        for right in range(left + 1, len(columns)):
            kind = _pair_class(left_type, columns[right].inferred.selected_type)
            if kind is _Eligibility.SUPPORTED:
                supported.append((left, right))
            elif isinstance(kind, UnimplementedRelationshipFamily):
                unimplemented_counts[kind] = unimplemented_counts.get(kind, 0) + 1
            else:
                ineligible += 1
    unimplemented = tuple(
        UnimplementedFamilyCount(family=family, n_pairs=unimplemented_counts[family])
        for family in UnimplementedRelationshipFamily
        if family in unimplemented_counts
    )
    return _Classification(
        supported_pairs=tuple(supported),
        unimplemented=unimplemented,
        n_ineligible_pairs=ineligible,
    )


def _pair_class(
    left: Optional[SemanticType],
    right: Optional[SemanticType],
) -> _PairClass:
    """Classify one unordered pair of selected types.

    The coverage decision is ``classify_selected_pair``. This adapter
    keeps the collector's supported-pair list on that same decision.
    """
    classified = classify_selected_pair(left, right)
    if classified.coverage is SelectedPairCoverage.CALCULATED:
        return _Eligibility.SUPPORTED
    if classified.coverage is SelectedPairCoverage.UNIMPLEMENTED:
        family = classified.unimplemented_family
        if family is None:
            raise ValueError("an unimplemented pair names its recognized family")
        return family
    return _Eligibility.INELIGIBLE


def _require_recorded_pairs(
    classification: _Classification,
    relationships: Tuple[
        RelationshipRecord,
        ...,
    ],
    columns: Tuple[ColumnAnalysis, ...],
    n_rows: int,
) -> None:
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    if len(relationships) != len(classification.supported_pairs):
        raise ValueError("relationship records must be the selected supported pairs")
    for relationship, pair in zip(relationships, classification.supported_pairs):
        if not isinstance(
            relationship,
            (
                NumericNumericRelationship,
                NumericCategoricalRelationship,
                BooleanBooleanRelationship,
                NumericBooleanRelationship,
                CategoricalCategoricalRelationship,
            ),
        ):
            raise TypeError(
                "relationships must contain calculated relationship records"
            )
        left, right = pair
        if (relationship.left_position, relationship.right_position) != (left, right):
            raise ValueError(
                "relationship positions must follow selected supported pairs"
            )
        if relationship.n_total_rows != n_rows:
            raise ValueError("n_total_rows must equal the dataset row count")
        if not _labels_match(relationship.left_label, columns[left].label):
            raise ValueError("relationship label must be the source column label")
        if not _labels_match(relationship.right_label, columns[right].label):
            raise ValueError("relationship label must be the source column label")
        _require_record_family(relationship, columns, left, right)


def _require_aligned_columns(
    frame: pd.DataFrame,
    columns: Tuple[ColumnAnalysis, ...],
) -> None:
    _require_column_tuple(columns, frame.shape[0])
    if len(columns) != frame.shape[1]:
        raise ValueError("columns must contain one record per DataFrame column")
    for position, column in enumerate(columns):
        if not _labels_match(column.label, frame.columns[position]):
            raise ValueError("column label must match the DataFrame label")


def _require_column_tuple(columns: Tuple[ColumnAnalysis, ...], n_rows: int) -> None:
    if not isinstance(columns, tuple):
        raise TypeError("columns must be a tuple")
    for position, column in enumerate(columns):
        if not isinstance(column, ColumnAnalysis):
            raise TypeError("columns must contain ColumnAnalysis records")
        if column.position != position:
            raise ValueError("column position must match column order")
        if column.evidence.basic.n_total != n_rows:
            raise ValueError("column n_total must equal n_rows")


def _require_record_family(
    relationship: object,
    columns: Tuple[ColumnAnalysis, ...],
    left: int,
    right: int,
) -> None:
    left_type = columns[left].inferred.selected_type
    right_type = columns[right].inferred.selected_type
    if left_type is SemanticType.NUMERIC and right_type is SemanticType.NUMERIC:
        if not isinstance(relationship, NumericNumericRelationship):
            raise TypeError("a numeric pair requires a NumericNumericRelationship")
        return
    if left_type is SemanticType.BOOLEAN and right_type is SemanticType.BOOLEAN:
        if not isinstance(relationship, BooleanBooleanRelationship):
            raise TypeError("a boolean pair requires a BooleanBooleanRelationship")
        return
    if {left_type, right_type} == {SemanticType.NUMERIC, SemanticType.BOOLEAN}:
        if not isinstance(relationship, NumericBooleanRelationship):
            raise TypeError("a numeric-boolean pair requires that relationship record")
        numeric_position, _other_position = _role_positions(left, right, left_type)
        if relationship.numeric_position != numeric_position:
            raise ValueError("numeric role must follow the selected numeric column")
        return
    if {left_type, right_type} == {SemanticType.NUMERIC, SemanticType.CATEGORICAL}:
        if not isinstance(relationship, NumericCategoricalRelationship):
            raise TypeError(
                "a numeric-categorical pair requires that relationship record"
            )
        numeric_position, _other_position = _role_positions(left, right, left_type)
        if relationship.numeric_position != numeric_position:
            raise ValueError("numeric role must follow the selected numeric column")
        return
    if left_type is SemanticType.CATEGORICAL and right_type is SemanticType.CATEGORICAL:
        if not isinstance(relationship, CategoricalCategoricalRelationship):
            raise TypeError(
                "a categorical pair requires a CategoricalCategoricalRelationship"
            )
        return
    raise TypeError("supported pair has no relationship family")


def _copy_relationship(
    relationship: RelationshipRecord,
) -> RelationshipRecord:
    if isinstance(relationship, NumericNumericRelationship):
        return _copy_numeric_numeric(relationship)
    if isinstance(relationship, NumericCategoricalRelationship):
        return _copy_numeric_categorical(relationship)
    if isinstance(relationship, BooleanBooleanRelationship):
        return _copy_boolean_boolean(relationship)
    if isinstance(relationship, NumericBooleanRelationship):
        return _copy_numeric_boolean(relationship)
    if isinstance(relationship, CategoricalCategoricalRelationship):
        return _copy_categorical_categorical(relationship)
    raise TypeError("relationship records must be calculated relationship values")


def _copy_numeric_numeric(
    relationship: NumericNumericRelationship,
) -> NumericNumericRelationship:
    return NumericNumericRelationship(
        left_position=relationship.left_position,
        left_label=relationship.left_label,
        right_position=relationship.right_position,
        right_label=relationship.right_label,
        n_total_rows=relationship.n_total_rows,
        n_paired=relationship.n_paired,
        methods=tuple(_copy_method(method) for method in relationship.methods),
    )


def _copy_method(method: AssociationResult) -> AssociationResult:
    estimate = method.estimate
    frequentist = method.frequentist
    interval = method.confidence_interval
    return AssociationResult(
        method=method.method,
        n_observations=method.n_observations,
        estimate=CorrelationEstimate(
            availability=estimate.availability,
            value=estimate.value,
            direction=estimate.direction,
            reason=estimate.reason,
        ),
        frequentist=_copy_frequentist(frequentist),
        confidence_interval=CorrelationInterval(
            availability=interval.availability,
            level=interval.level,
            method=interval.method,
            lower=interval.lower,
            upper=interval.upper,
            reason=interval.reason,
        ),
    )


def _copy_numeric_categorical(
    relationship: NumericCategoricalRelationship,
) -> NumericCategoricalRelationship:
    return NumericCategoricalRelationship(
        left_position=relationship.left_position,
        left_label=relationship.left_label,
        right_position=relationship.right_position,
        right_label=relationship.right_label,
        numeric_position=relationship.numeric_position,
        categorical_position=relationship.categorical_position,
        n_total_rows=relationship.n_total_rows,
        n_paired=relationship.n_paired,
        groups=tuple(_copy_group(group) for group in relationship.groups),
        effect=_copy_effect(relationship.effect),
        corrected_effect=_copy_effect(relationship.corrected_effect),
        omnibus=_copy_omnibus(relationship.omnibus),
    )


def _copy_group(group: CategoricalGroupSummary) -> CategoricalGroupSummary:
    return CategoricalGroupSummary(
        category=group.category,
        descriptive=_copy_descriptive(group.descriptive),
    )


def _copy_descriptive(
    descriptive: NumericDescriptiveAnalysis,
) -> NumericDescriptiveAnalysis:
    return NumericDescriptiveAnalysis(
        finite_count=descriptive.finite_count,
        minimum=descriptive.minimum,
        maximum=descriptive.maximum,
        mean=descriptive.mean,
        median=descriptive.median,
        standard_deviation=descriptive.standard_deviation,
        q1=descriptive.q1,
        q3=descriptive.q3,
    )


def _copy_effect(effect: GroupEffectEstimate) -> GroupEffectEstimate:
    return GroupEffectEstimate(
        method=effect.method,
        availability=effect.availability,
        value=effect.value,
        reason=effect.reason,
    )


def _copy_omnibus(omnibus: OmnibusAnovaResult) -> OmnibusAnovaResult:
    return OmnibusAnovaResult(
        method=omnibus.method,
        statistic_availability=omnibus.statistic_availability,
        statistic=omnibus.statistic,
        statistic_reason=omnibus.statistic_reason,
        frequentist=_copy_frequentist(omnibus.frequentist),
    )


def _copy_frequentist(frequentist: FrequentistEvidence) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=frequentist.availability,
        p_value=frequentist.p_value,
        adjusted_p_value=frequentist.adjusted_p_value,
        adjustment=frequentist.adjustment,
        reason=frequentist.reason,
        inferential_validity=frequentist.inferential_validity,
        invalidity_reason=frequentist.invalidity_reason,
    )


def _copy_boolean_boolean(
    relationship: BooleanBooleanRelationship,
) -> BooleanBooleanRelationship:
    return BooleanBooleanRelationship(
        left_position=relationship.left_position,
        left_label=relationship.left_label,
        right_position=relationship.right_position,
        right_label=relationship.right_label,
        conditioning_position=relationship.conditioning_position,
        outcome_position=relationship.outcome_position,
        n_total_rows=relationship.n_total_rows,
        n_paired=relationship.n_paired,
        table=BooleanContingencyTable(
            conditioning_false_outcome_false=(
                relationship.table.conditioning_false_outcome_false
            ),
            conditioning_false_outcome_true=(
                relationship.table.conditioning_false_outcome_true
            ),
            conditioning_true_outcome_false=(
                relationship.table.conditioning_true_outcome_false
            ),
            conditioning_true_outcome_true=(
                relationship.table.conditioning_true_outcome_true
            ),
        ),
        outcome_true_given_conditioning_false=_copy_conditional(
            relationship.outcome_true_given_conditioning_false
        ),
        outcome_true_given_conditioning_true=_copy_conditional(
            relationship.outcome_true_given_conditioning_true
        ),
        probability_difference=_copy_directional(relationship.probability_difference),
        probability_ratio=_copy_directional(relationship.probability_ratio),
        phi=_copy_phi(relationship.phi),
        independence=_copy_independence(relationship.independence),
    )


def _copy_conditional(
    probability: ConditionalOutcomeProbability,
) -> ConditionalOutcomeProbability:
    return ConditionalOutcomeProbability(
        conditioning_value=probability.conditioning_value,
        availability=probability.availability,
        value=probability.value,
        reason=probability.reason,
    )


def _copy_directional(
    estimate: BooleanDirectionalEstimate,
) -> BooleanDirectionalEstimate:
    return BooleanDirectionalEstimate(
        method=estimate.method,
        availability=estimate.availability,
        value=estimate.value,
        reason=estimate.reason,
    )


def _copy_phi(estimate: BooleanAssociationEstimate) -> BooleanAssociationEstimate:
    return BooleanAssociationEstimate(
        method=estimate.method,
        availability=estimate.availability,
        value=estimate.value,
        reason=estimate.reason,
    )


def _copy_independence(test: BooleanIndependenceTest) -> BooleanIndependenceTest:
    frequentist = test.frequentist
    return BooleanIndependenceTest(
        method=test.method,
        frequentist=_copy_frequentist(frequentist),
    )


def _copy_numeric_boolean(
    relationship: NumericBooleanRelationship,
) -> NumericBooleanRelationship:
    difference = relationship.mean_difference
    standardized = relationship.standardized_mean_difference
    interval = relationship.mean_difference_interval
    return NumericBooleanRelationship(
        left_position=relationship.left_position,
        left_label=relationship.left_label,
        right_position=relationship.right_position,
        right_label=relationship.right_label,
        numeric_position=relationship.numeric_position,
        boolean_position=relationship.boolean_position,
        n_total_rows=relationship.n_total_rows,
        n_paired=relationship.n_paired,
        false_group=_copy_boolean_group(relationship.false_group),
        true_group=_copy_boolean_group(relationship.true_group),
        mean_difference=MeanDifferenceEstimate(
            availability=difference.availability,
            value=difference.value,
            reason=difference.reason,
        ),
        standardized_mean_difference=StandardizedMeanDifference(
            method=standardized.method,
            availability=standardized.availability,
            value=standardized.value,
            reason=standardized.reason,
        ),
        mean_difference_interval=MeanDifferenceInterval(
            availability=interval.availability,
            level=interval.level,
            method=interval.method,
            lower=interval.lower,
            upper=interval.upper,
            reason=interval.reason,
        ),
        mean_difference_test=_copy_mean_difference_test(
            relationship.mean_difference_test
        ),
    )


def _copy_boolean_group(group: BooleanGroupSummary) -> BooleanGroupSummary:
    return BooleanGroupSummary(
        level=group.level,
        availability=group.availability,
        descriptive=(
            None if group.descriptive is None else _copy_descriptive(group.descriptive)
        ),
        reason=group.reason,
    )


def _copy_mean_difference_test(test: MeanDifferenceTest) -> MeanDifferenceTest:
    frequentist = test.frequentist
    return MeanDifferenceTest(
        method=test.method,
        statistic_availability=test.statistic_availability,
        statistic=test.statistic,
        degrees_of_freedom=test.degrees_of_freedom,
        statistic_reason=test.statistic_reason,
        frequentist=_copy_frequentist(frequentist),
    )


def _copy_categorical_categorical(
    relationship: CategoricalCategoricalRelationship,
) -> CategoricalCategoricalRelationship:
    return CategoricalCategoricalRelationship(
        left_position=relationship.left_position,
        left_label=relationship.left_label,
        right_position=relationship.right_position,
        right_label=relationship.right_label,
        n_total_rows=relationship.n_total_rows,
        n_paired=relationship.n_paired,
        table=_copy_contingency(relationship.table),
        association=_copy_cramers_v(relationship.association),
        corrected_association=_copy_cramers_v(relationship.corrected_association),
        expected_counts=_copy_expected_counts(relationship.expected_counts),
        independence=_copy_chi_square(relationship.independence),
    )


def _copy_contingency(
    table: CategoricalContingencyTable,
) -> CategoricalContingencyTable:
    return CategoricalContingencyTable(
        left_levels=tuple(table.left_levels),
        right_levels=tuple(table.right_levels),
        observed_counts=tuple(
            (left_index, right_index, count)
            for left_index, right_index, count in table.observed_counts
        ),
        left_totals=tuple(table.left_totals),
        right_totals=tuple(table.right_totals),
    )


def _copy_cramers_v(
    estimate: CategoricalAssociationEstimate,
) -> CategoricalAssociationEstimate:
    return CategoricalAssociationEstimate(
        method=estimate.method,
        availability=estimate.availability,
        value=estimate.value,
        reason=estimate.reason,
        numerator_floored=estimate.numerator_floored,
    )


def _copy_expected_counts(
    diagnostics: ExpectedCountDiagnostics,
) -> ExpectedCountDiagnostics:
    return ExpectedCountDiagnostics(
        availability=diagnostics.availability,
        minimum_expected_count=diagnostics.minimum_expected_count,
        n_cells_expected_below_5=diagnostics.n_cells_expected_below_5,
        fraction_cells_expected_below_5=diagnostics.fraction_cells_expected_below_5,
        n_cells_expected_below_1=diagnostics.n_cells_expected_below_1,
        reason=diagnostics.reason,
    )


def _copy_chi_square(test: CategoricalIndependenceTest) -> CategoricalIndependenceTest:
    frequentist = test.frequentist
    return CategoricalIndependenceTest(
        method=test.method,
        statistic_availability=test.statistic_availability,
        statistic=test.statistic,
        degrees_of_freedom=test.degrees_of_freedom,
        statistic_reason=test.statistic_reason,
        frequentist=_copy_frequentist(frequentist),
    )


def _labels_match(left: object, right: object) -> bool:
    """Whether two stored column labels are the same label.

    This is :func:`observed_labels_equal`. Float ``NaN`` matches float
    ``NaN``. ``True`` does not match ``1``.
    """
    return observed_labels_equal(left, right)
