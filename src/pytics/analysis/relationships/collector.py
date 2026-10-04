"""Dataset relationship collection and product projection.

Eligibility uses the selected semantic type. The only calculated family
is selected Numeric × Numeric. Other recognized directions are counted.
Ineligible pairs are counted and not read. Temporary numeric arrays are
discarded before the collector returns. The summary builder copies the
retained records and does not calculate a correlation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

import numpy as np
import pandas as pd

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.relationships.models import AssociationResult
from pytics.analysis.relationships.models import CorrelationEstimate
from pytics.analysis.relationships.models import CorrelationInterval
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import NumericNumericRelationship
from pytics.analysis.relationships.models import RelationshipAnalysis
from pytics.analysis.relationships.models import RelationshipsSummary
from pytics.analysis.relationships.models import UnimplementedFamilyCount
from pytics.analysis.relationships.models import UnimplementedRelationshipFamily
from pytics.analysis.relationships.models import _require_nonnegative
from pytics.analysis.relationships.numeric_numeric import _association_methods
from pytics.analysis.relationships.numeric_numeric import _read_numeric_column
from pytics.semantics.interpretation import SemanticType


class _Eligibility(Enum):
    """Classifier outcome other than an unimplemented recognized family."""

    SUPPORTED = "supported"
    INELIGIBLE = "ineligible"


_PairClass = Union[UnimplementedRelationshipFamily, _Eligibility]


# Recognized directions that are not implemented. Lookup ignores order.
_UNIMPLEMENTED_FAMILIES = {
    frozenset((SemanticType.NUMERIC, SemanticType.BOOLEAN)): (
        UnimplementedRelationshipFamily.NUMERIC_BOOLEAN
    ),
    frozenset((SemanticType.NUMERIC, SemanticType.CATEGORICAL)): (
        UnimplementedRelationshipFamily.NUMERIC_CATEGORICAL
    ),
    frozenset((SemanticType.BOOLEAN,)): UnimplementedRelationshipFamily.BOOLEAN_BOOLEAN,
    frozenset((SemanticType.CATEGORICAL,)): (
        UnimplementedRelationshipFamily.CATEGORICAL_CATEGORICAL
    ),
    frozenset((SemanticType.DATETIME, SemanticType.NUMERIC)): (
        UnimplementedRelationshipFamily.DATETIME_NUMERIC
    ),
    frozenset((SemanticType.DATETIME, SemanticType.CATEGORICAL)): (
        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL
    ),
}


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
    """Describe eligible Numeric × Numeric pairs in one DataFrame.

    ``columns`` are the column analyses already produced for ``frame``.
    Selected semantic types decide eligibility before any pair is read.
    Each selected Numeric column is converted once. Unsupported pairs do
    not read raw values. Temporary arrays are discarded before return.
    The DataFrame is not modified.

    A method that cannot produce a finite estimate is recorded as
    unavailable. That state does not raise, and it does not discard the
    other method on the same pair.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("collect_relationship_analysis expects a pandas DataFrame")
    _require_aligned_columns(frame, columns)
    n_rows = int(frame.shape[0])
    relationships = _relationships_for_frame(frame, columns, n_rows)
    return relationship_analysis_for_columns(
        columns,
        n_rows=n_rows,
        relationships=relationships,
    )


def relationship_analysis_for_columns(
    columns: Tuple[ColumnAnalysis, ...],
    *,
    n_rows: int,
    relationships: Tuple[NumericNumericRelationship, ...] = (),
) -> RelationshipAnalysis:
    """Attach relationship records to the selected-type pair counts.

    This does not read values and does not calculate correlations.
    ``relationships`` must already be the selected Numeric pairs, in
    ascending position order. A supported pair with no record is invalid.
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
    not accepted and is not analyzed. Correlations are not recomputed.
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
) -> Tuple[NumericNumericRelationship, ...]:
    """Calculate one record per selected Numeric pair.

    Numeric columns are read once. The reads are local to this function.
    """
    classification = _classify_columns(columns)
    if not classification.supported_pairs:
        return ()
    populations = {
        position: _read_numeric_column(frame.iloc[:, position])
        for position in _numeric_positions(columns)
    }
    records: List[NumericNumericRelationship] = []
    for left, right in classification.supported_pairs:
        left_values, left_finite = populations[left]
        right_values, right_finite = populations[right]
        paired_rows = np.flatnonzero(left_finite & right_finite)
        methods = _association_methods(
            left_values[paired_rows],
            right_values[paired_rows],
        )
        records.append(
            NumericNumericRelationship(
                left_position=left,
                left_label=columns[left].label,
                right_position=right,
                right_label=columns[right].label,
                n_total_rows=n_rows,
                n_paired=int(paired_rows.size),
                methods=methods,
            )
        )
    return tuple(records)


def _numeric_positions(columns: Tuple[ColumnAnalysis, ...]) -> Tuple[int, ...]:
    return tuple(
        column.position
        for column in columns
        if column.inferred.selected_type is SemanticType.NUMERIC
    )


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

    ``None`` is an unresolved column. It is ineligible, as are identifiers,
    constants, empty columns, and pair types with no accepted direction.
    """
    if left is None or right is None:
        return _Eligibility.INELIGIBLE
    if left is SemanticType.NUMERIC and right is SemanticType.NUMERIC:
        return _Eligibility.SUPPORTED
    family = _UNIMPLEMENTED_FAMILIES.get(frozenset((left, right)))
    if family is None:
        return _Eligibility.INELIGIBLE
    return family


def _require_recorded_pairs(
    classification: _Classification,
    relationships: Tuple[NumericNumericRelationship, ...],
    columns: Tuple[ColumnAnalysis, ...],
    n_rows: int,
) -> None:
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    if len(relationships) != len(classification.supported_pairs):
        raise ValueError("relationship records must be the selected Numeric pairs")
    for relationship, pair in zip(relationships, classification.supported_pairs):
        if not isinstance(relationship, NumericNumericRelationship):
            raise TypeError(
                "relationships must contain NumericNumericRelationship values"
            )
        left, right = pair
        if (relationship.left_position, relationship.right_position) != (left, right):
            raise ValueError(
                "relationship positions must follow selected Numeric pairs"
            )
        if relationship.n_total_rows != n_rows:
            raise ValueError("n_total_rows must equal the dataset row count")
        if not _labels_match(relationship.left_label, columns[left].label):
            raise ValueError("relationship label must be the source column label")
        if not _labels_match(relationship.right_label, columns[right].label):
            raise ValueError("relationship label must be the source column label")


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


def _copy_relationship(
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
        frequentist=FrequentistEvidence(
            availability=frequentist.availability,
            p_value=frequentist.p_value,
            adjusted_p_value=frequentist.adjusted_p_value,
            adjustment=frequentist.adjustment,
            reason=frequentist.reason,
        ),
        confidence_interval=CorrelationInterval(
            availability=interval.availability,
            level=interval.level,
            method=interval.method,
            lower=interval.lower,
            upper=interval.upper,
            reason=interval.reason,
        ),
    )


def _labels_match(left: object, right: object) -> bool:
    if left is right:
        return True
    try:
        equal = left == right
    except TypeError:
        return False
    if isinstance(equal, np.ndarray):
        return False
    return bool(equal)
