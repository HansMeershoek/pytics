"""Relationship drift from two retained relationship analyses.

Pairs align by the column identities already built for the comparison.
The pass reads those identities and the retained effects. It does not
read a DataFrame, and it does not calculate Spearman, eta squared,
epsilon squared, Hedges' g, phi, or Cramér's V again.

A same-family numeric pair also receives a complementary Fisher z test
of Pearson equality. That test uses the retained correlations and pair
counts only. It is not a test of Spearman rho, and its p-value is not
adjusted.
"""

from __future__ import annotations

from typing import Dict
from typing import Optional
from typing import Tuple

from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.alignment import _AlignedColumn
from pytics.analysis.compare.relationship_models import BooleanBooleanState
from pytics.analysis.compare.relationship_models import CategoricalCategoricalState
from pytics.analysis.compare.relationship_models import ContingencyVocabulary
from pytics.analysis.compare.relationship_models import EffectChange
from pytics.analysis.compare.relationship_models import EffectChangeReason
from pytics.analysis.compare.relationship_models import GroupingVocabulary
from pytics.analysis.compare.relationship_models import NumericBooleanState
from pytics.analysis.compare.relationship_models import NumericCategoricalState
from pytics.analysis.compare.relationship_models import NumericNumericState
from pytics.analysis.compare.relationship_models import PearsonChangeNull
from pytics.analysis.compare.relationship_models import PearsonChangeReason
from pytics.analysis.compare.relationship_models import PearsonCorrelationChangeTest
from pytics.analysis.compare.relationship_models import PEARSON_CHANGE_ASSUMPTIONS
from pytics.analysis.compare.relationship_models import RelationshipChangeMeasure
from pytics.analysis.compare.relationship_models import RelationshipColumnIdentity
from pytics.analysis.compare.relationship_models import RelationshipDrift
from pytics.analysis.compare.relationship_models import RelationshipPairAlignment
from pytics.analysis.compare.relationship_models import RelationshipSide
from pytics.analysis.compare.relationship_models import RelationshipSideKind
from pytics.analysis.compare.relationship_models import VocabularyStatus
from pytics.analysis.compare.relationship_models import pair_status
from pytics.analysis.compare.relationship_models import _SIGNED_MEASURES
from pytics.analysis.compare.relationship_models import _finite_difference
from pytics.analysis.compare.relationship_models import _sign_reversal
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.relationships.models import RelationshipFamily
from pytics.analysis.relationships.models import RelationshipRecord
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models.coverage import SelectedPairCoverage
from pytics.analysis.relationships.models.coverage import classify_selected_pair
from pytics.analysis.relationships.numeric_numeric import independent_pearson_equality
from pytics.semantics.interpretation import SemanticType

_MIN_PEARSON_CHANGE_N = 4
_FAMILY_BY_TYPES = {
    frozenset((SemanticType.NUMERIC,)): RelationshipFamily.NUMERIC_NUMERIC,
    frozenset((SemanticType.NUMERIC, SemanticType.CATEGORICAL)): (
        RelationshipFamily.NUMERIC_CATEGORICAL
    ),
    frozenset((SemanticType.NUMERIC, SemanticType.BOOLEAN)): (
        RelationshipFamily.NUMERIC_BOOLEAN
    ),
    frozenset((SemanticType.BOOLEAN,)): RelationshipFamily.BOOLEAN_BOOLEAN,
    frozenset((SemanticType.CATEGORICAL,)): RelationshipFamily.CATEGORICAL_CATEGORICAL,
}


def compare_relationships(
    reference: DatasetAnalysis,
    comparison: DatasetAnalysis,
    aligned: Tuple[_AlignedColumn, ...],
) -> Tuple[RelationshipDrift, ...]:
    """Align retained relationship records and compare their effects.

    ``aligned`` is the column alignment already produced for this
    comparison. Only pairs of matched columns are candidates. A pair
    that is ineligible on both sides is omitted. Alignment is one index
    of retained records, then one pass over matched column pairs.
    """
    matched = tuple(
        item for item in aligned if item.alignment.status is ColumnMatchStatus.MATCHED
    )
    by_reference = {
        item.alignment.reference_position: item
        for item in matched
        if item.alignment.reference_position is not None
    }
    comparison_to_reference = {
        item.alignment.comparison_position: item.alignment.reference_position
        for item in matched
        if item.alignment.comparison_position is not None
        and item.alignment.reference_position is not None
    }
    reference_map = {
        position: position for position in by_reference if position is not None
    }
    reference_index = _index_relationships(
        reference.relationship_analysis.relationships,
        reference_map,
    )
    comparison_index = _index_relationships(
        comparison.relationship_analysis.relationships,
        comparison_to_reference,
    )
    records = []
    positions = sorted(position for position in by_reference if position is not None)
    for index, first in enumerate(positions):
        for second in positions[index + 1 :]:
            record = _pair_record(
                by_reference[first],
                by_reference[second],
                reference_index.get((first, second)),
                comparison_index.get((first, second)),
                reference_map,
                comparison_to_reference,
            )
            if record is not None:
                records.append(record)
    return tuple(records)


def _index_relationships(
    relationships: Tuple[RelationshipRecord, ...],
    position_map: Dict[int, int],
) -> Dict[Tuple[int, int], RelationshipRecord]:
    indexed: Dict[Tuple[int, int], RelationshipRecord] = {}
    for relationship in relationships:
        left = position_map.get(relationship.left_position)
        right = position_map.get(relationship.right_position)
        if left is None or right is None:
            continue
        key = (left, right) if left < right else (right, left)
        if key in indexed:
            raise ValueError("two relationship records share one aligned pair")
        indexed[key] = relationship
    return indexed


def _pair_record(
    first: _AlignedColumn,
    second: _AlignedColumn,
    reference_record: Optional[RelationshipRecord],
    comparison_record: Optional[RelationshipRecord],
    reference_map: Dict[int, int],
    comparison_map: Dict[int, int],
) -> Optional[RelationshipDrift]:
    if first.reference is None or first.comparison is None:
        raise ValueError("a matched column has two analyses")
    if second.reference is None or second.comparison is None:
        raise ValueError("a matched column has two analyses")
    reference_class = classify_selected_pair(
        first.reference.inferred.selected_type,
        second.reference.inferred.selected_type,
    )
    comparison_class = classify_selected_pair(
        first.comparison.inferred.selected_type,
        second.comparison.inferred.selected_type,
    )
    if (
        reference_class.coverage is SelectedPairCoverage.INELIGIBLE
        and comparison_class.coverage is SelectedPairCoverage.INELIGIBLE
    ):
        return None
    first_position = first.alignment.reference_position
    second_position = second.alignment.reference_position
    if first_position is None or second_position is None:
        raise ValueError("a matched column has a reference position")
    reference_side = _side(
        reference_class.coverage,
        reference_class.unimplemented_family,
        reference_record,
        first.reference.inferred.selected_type,
        second.reference.inferred.selected_type,
        first_position,
        reference_map,
    )
    comparison_side = _side(
        comparison_class.coverage,
        comparison_class.unimplemented_family,
        comparison_record,
        first.comparison.inferred.selected_type,
        second.comparison.inferred.selected_type,
        first_position,
        comparison_map,
    )
    return _drift(
        RelationshipPairAlignment(
            first=_column_identity(first),
            second=_column_identity(second),
        ),
        reference_side,
        comparison_side,
    )


def _side(
    coverage: SelectedPairCoverage,
    unimplemented: object,
    record: Optional[RelationshipRecord],
    left_type: Optional[SemanticType],
    right_type: Optional[SemanticType],
    first_reference: int,
    position_map: Dict[int, int],
) -> RelationshipSide:
    if coverage is SelectedPairCoverage.INELIGIBLE:
        if record is not None:
            raise ValueError("an ineligible pair has a relationship record")
        return RelationshipSide(kind=RelationshipSideKind.INELIGIBLE)
    if coverage is SelectedPairCoverage.UNIMPLEMENTED:
        if record is not None:
            raise ValueError("an unimplemented pair has a relationship record")
        return RelationshipSide(
            kind=RelationshipSideKind.UNIMPLEMENTED,
            unimplemented_family=unimplemented,  # type: ignore[arg-type]
        )
    if record is None:
        raise ValueError("a calculated pair is missing its relationship record")
    expected = _FAMILY_BY_TYPES.get(
        frozenset(item for item in (left_type, right_type) if item is not None)
    )
    if record.family is not expected:
        raise ValueError("relationship family does not match the selected types")
    return RelationshipSide(
        kind=RelationshipSideKind.CALCULATED,
        family=record.family,
        **_payload(record, first_reference, position_map),
    )


def _payload(
    record: RelationshipRecord,
    first_reference: int,
    position_map: Dict[int, int],
) -> dict:
    if record.family is RelationshipFamily.NUMERIC_NUMERIC:
        spearman, pearson = record.methods
        return {
            "numeric_numeric": NumericNumericState(
                n_paired=record.n_paired,
                spearman=_component_value(spearman.estimate),
                spearman_reason=_component_reason(spearman.estimate),
                pearson=_component_value(pearson.estimate),
                pearson_reason=_component_reason(pearson.estimate),
            )
        }
    if record.family is RelationshipFamily.NUMERIC_CATEGORICAL:
        return {
            "numeric_categorical": NumericCategoricalState(
                n_paired=record.n_paired,
                numeric_is_first=_is_first(
                    record.numeric_position, position_map, first_reference
                ),
                categories=tuple(group.category for group in record.groups),
                eta_squared=_component_value(record.effect),
                eta_squared_reason=_component_reason(record.effect),
                epsilon_squared=_component_value(record.corrected_effect),
                epsilon_squared_reason=_component_reason(record.corrected_effect),
            )
        }
    if record.family is RelationshipFamily.NUMERIC_BOOLEAN:
        return {
            "numeric_boolean": NumericBooleanState(
                n_paired=record.n_paired,
                numeric_is_first=_is_first(
                    record.numeric_position, position_map, first_reference
                ),
                hedges_g=_component_value(record.standardized_mean_difference),
                hedges_g_reason=_component_reason(record.standardized_mean_difference),
                mean_difference=_component_value(record.mean_difference),
                mean_difference_reason=_component_reason(record.mean_difference),
            )
        }
    if record.family is RelationshipFamily.BOOLEAN_BOOLEAN:
        return {
            "boolean_boolean": BooleanBooleanState(
                n_paired=record.n_paired,
                conditioning_is_first=_is_first(
                    record.conditioning_position, position_map, first_reference
                ),
                phi=_component_value(record.phi),
                phi_reason=_component_reason(record.phi),
                probability_difference=_component_value(record.probability_difference),
                probability_difference_reason=_component_reason(
                    record.probability_difference
                ),
            )
        }
    left_is_first = _is_first(record.left_position, position_map, first_reference)
    table = record.table
    if left_is_first:
        first_levels = table.left_levels
        second_levels = table.right_levels
    else:
        first_levels = table.right_levels
        second_levels = table.left_levels
    return {
        "categorical_categorical": CategoricalCategoricalState(
            n_paired=record.n_paired,
            first_levels=first_levels,
            second_levels=second_levels,
            n_positive_cells=table.n_observed_cells,
            cramers_v=_component_value(record.association),
            cramers_v_reason=_component_reason(record.association),
            bias_corrected_cramers_v=_component_value(record.corrected_association),
            bias_corrected_cramers_v_reason=_component_reason(
                record.corrected_association
            ),
            bias_correction_numerator_floored=(
                record.corrected_association.numerator_floored
            ),
        )
    }


def _drift(
    alignment: RelationshipPairAlignment,
    reference: RelationshipSide,
    comparison: RelationshipSide,
) -> RelationshipDrift:
    same_family = (
        reference.kind is RelationshipSideKind.CALCULATED
        and comparison.kind is RelationshipSideKind.CALCULATED
        and reference.family is comparison.family
    )
    primary = None
    complementary: Tuple[EffectChange, ...] = ()
    grouping = None
    contingency = None
    pearson_test = None
    if same_family:
        family = reference.family
        reference_payload = reference.payload()
        comparison_payload = comparison.payload()
        primary = _effect_change(
            _primary_measure(family),
            _primary_value(reference_payload),
            _primary_value(comparison_payload),
        )
        complementary = _complementary_changes(reference_payload, comparison_payload)
        if family is RelationshipFamily.NUMERIC_CATEGORICAL:
            grouping = _grouping(
                reference_payload.categories,  # type: ignore[attr-defined]
                comparison_payload.categories,  # type: ignore[attr-defined]
            )
        elif family is RelationshipFamily.CATEGORICAL_CATEGORICAL:
            contingency = _contingency(reference_payload, comparison_payload)
        elif family is RelationshipFamily.NUMERIC_NUMERIC:
            pearson_test = _pearson_test(reference_payload, comparison_payload)
    return RelationshipDrift(
        alignment=alignment,
        status=pair_status(reference, comparison),
        reference=reference,
        comparison=comparison,
        primary=primary,
        complementary=complementary,
        grouping_vocabulary=grouping,
        contingency_vocabulary=contingency,
        pearson_change_test=pearson_test,
    )


def _primary_measure(family: Optional[RelationshipFamily]) -> RelationshipChangeMeasure:
    if family is RelationshipFamily.NUMERIC_NUMERIC:
        return RelationshipChangeMeasure.SPEARMAN_RHO
    if family is RelationshipFamily.NUMERIC_CATEGORICAL:
        return RelationshipChangeMeasure.ETA_SQUARED
    if family is RelationshipFamily.NUMERIC_BOOLEAN:
        return RelationshipChangeMeasure.HEDGES_G
    if family is RelationshipFamily.BOOLEAN_BOOLEAN:
        return RelationshipChangeMeasure.PHI
    return RelationshipChangeMeasure.CRAMERS_V


def _primary_value(payload: object) -> Optional[float]:
    if isinstance(payload, NumericNumericState):
        return payload.spearman
    if isinstance(payload, NumericCategoricalState):
        return payload.eta_squared
    if isinstance(payload, NumericBooleanState):
        return payload.hedges_g
    if isinstance(payload, BooleanBooleanState):
        return payload.phi
    if isinstance(payload, CategoricalCategoricalState):
        return payload.cramers_v
    raise TypeError("a calculated side has a family payload")


def _complementary_changes(
    reference: object,
    comparison: object,
) -> Tuple[EffectChange, ...]:
    if isinstance(reference, NumericNumericState):
        return (
            _effect_change(
                RelationshipChangeMeasure.PEARSON_R,
                reference.pearson,
                comparison.pearson,  # type: ignore[attr-defined]
            ),
        )
    if isinstance(reference, NumericCategoricalState):
        return (
            _effect_change(
                RelationshipChangeMeasure.EPSILON_SQUARED,
                reference.epsilon_squared,
                comparison.epsilon_squared,  # type: ignore[attr-defined]
            ),
        )
    if isinstance(reference, NumericBooleanState):
        return (
            _effect_change(
                RelationshipChangeMeasure.MEAN_DIFFERENCE,
                reference.mean_difference,
                comparison.mean_difference,  # type: ignore[attr-defined]
            ),
        )
    if isinstance(reference, CategoricalCategoricalState):
        return (
            _effect_change(
                RelationshipChangeMeasure.BIAS_CORRECTED_CRAMERS_V,
                reference.bias_corrected_cramers_v,
                comparison.bias_corrected_cramers_v,  # type: ignore[attr-defined]
            ),
        )
    if isinstance(reference, BooleanBooleanState):
        shared = (
            reference.conditioning_is_first is comparison.conditioning_is_first  # type: ignore[attr-defined]
        )
        return (
            _effect_change(
                RelationshipChangeMeasure.PROBABILITY_DIFFERENCE,
                None if not shared else reference.probability_difference,
                None if not shared else comparison.probability_difference,  # type: ignore[attr-defined]
                orientation_shared=shared,
            ),
        )
    return ()


def _effect_change(
    measure: RelationshipChangeMeasure,
    reference: Optional[float],
    comparison: Optional[float],
    *,
    orientation_shared: bool = True,
) -> EffectChange:
    signed = measure in _SIGNED_MEASURES
    if not orientation_shared:
        return _unavailable_change(
            measure,
            None,
            None,
            EffectChangeReason.ORIENTATION_NOT_SHARED,
        )
    if reference is None and comparison is None:
        return _unavailable_change(
            measure,
            None,
            None,
            EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE,
        )
    if reference is None:
        return _unavailable_change(
            measure,
            None,
            comparison,
            EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE,
        )
    if comparison is None:
        return _unavailable_change(
            measure,
            reference,
            None,
            EffectChangeReason.COMPARISON_EFFECT_UNAVAILABLE,
        )
    change = _finite_difference(comparison, reference)
    magnitude = None
    reversal = None
    if signed:
        magnitude = _finite_difference(abs(comparison), abs(reference))
        reversal = _sign_reversal(reference, comparison)
    if change is None:
        return EffectChange(
            measure=measure,
            availability=ResultAvailability.UNAVAILABLE,
            reference=reference,
            comparison=comparison,
            change=None,
            magnitude_change=magnitude,
            sign_reversal=reversal,
            reason=EffectChangeReason.NON_FINITE_DIFFERENCE,
        )
    return EffectChange(
        measure=measure,
        availability=ResultAvailability.AVAILABLE,
        reference=reference,
        comparison=comparison,
        change=change,
        magnitude_change=magnitude,
        sign_reversal=reversal,
        reason=None,
    )


def _unavailable_change(
    measure: RelationshipChangeMeasure,
    reference: Optional[float],
    comparison: Optional[float],
    reason: EffectChangeReason,
) -> EffectChange:
    return EffectChange(
        measure=measure,
        availability=ResultAvailability.UNAVAILABLE,
        reference=reference,
        comparison=comparison,
        change=None,
        magnitude_change=None,
        sign_reversal=None,
        reason=reason,
    )


def _pearson_test(
    reference: object, comparison: object
) -> PearsonCorrelationChangeTest:
    if not isinstance(reference, NumericNumericState) or not isinstance(
        comparison, NumericNumericState
    ):
        raise TypeError("the Pearson change test reads two numeric states")
    if reference.pearson is None or comparison.pearson is None:
        return _unavailable_pearson(PearsonChangeReason.PEARSON_UNAVAILABLE)
    if (
        reference.n_paired < _MIN_PEARSON_CHANGE_N
        or comparison.n_paired < _MIN_PEARSON_CHANGE_N
    ):
        return _unavailable_pearson(
            PearsonChangeReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        )
    if abs(reference.pearson) == 1.0 or abs(comparison.pearson) == 1.0:
        return _unavailable_pearson(PearsonChangeReason.BOUNDARY_CORRELATION)
    found = independent_pearson_equality(
        reference.pearson,
        reference.n_paired,
        comparison.pearson,
        comparison.n_paired,
    )
    if found is None:
        return _unavailable_pearson(PearsonChangeReason.NON_FINITE_RESULT)
    statistic, probability = found
    return PearsonCorrelationChangeTest(
        availability=ResultAvailability.AVAILABLE,
        statistic=statistic,
        p_value=probability,
        null=PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS,
        assumptions=PEARSON_CHANGE_ASSUMPTIONS,
        reason=None,
    )


def _unavailable_pearson(reason: PearsonChangeReason) -> PearsonCorrelationChangeTest:
    return PearsonCorrelationChangeTest(
        availability=ResultAvailability.UNAVAILABLE,
        statistic=None,
        p_value=None,
        null=None,
        assumptions=(),
        reason=reason,
    )


def _grouping(
    reference_levels: Tuple[object, ...],
    comparison_levels: Tuple[object, ...],
) -> GroupingVocabulary:
    status = (
        VocabularyStatus.SAME
        if _same_levels(reference_levels, comparison_levels)
        else VocabularyStatus.CHANGED
    )
    return GroupingVocabulary(
        status=status,
        reference_n_levels=len(reference_levels),
        comparison_n_levels=len(comparison_levels),
    )


def _contingency(reference: object, comparison: object) -> ContingencyVocabulary:
    if not isinstance(reference, CategoricalCategoricalState) or not isinstance(
        comparison, CategoricalCategoricalState
    ):
        raise TypeError("contingency vocabulary reads two categorical states")
    first = _grouping(reference.first_levels, comparison.first_levels)
    second = _grouping(reference.second_levels, comparison.second_levels)
    status = (
        VocabularyStatus.CHANGED
        if first.status is VocabularyStatus.CHANGED
        or second.status is VocabularyStatus.CHANGED
        else VocabularyStatus.SAME
    )
    return ContingencyVocabulary(
        first=first,
        second=second,
        reference_shape=(len(reference.first_levels), len(reference.second_levels)),
        comparison_shape=(
            len(comparison.first_levels),
            len(comparison.second_levels),
        ),
        status=status,
    )


def _same_levels(reference: Tuple[object, ...], comparison: Tuple[object, ...]) -> bool:
    if len(reference) != len(comparison):
        return False
    pending = list(comparison)
    for value in reference:
        found = None
        for index, other in enumerate(pending):
            if other == value:
                found = index
                break
        if found is None:
            return False
        del pending[found]
    return True


def _column_identity(item: _AlignedColumn) -> RelationshipColumnIdentity:
    alignment = item.alignment
    if (
        alignment.occurrence is None
        or alignment.reference_position is None
        or alignment.comparison_position is None
        or alignment.reference_label is None
        or alignment.comparison_label is None
    ):
        raise ValueError("a matched column has a cross-dataset identity")
    return RelationshipColumnIdentity(
        occurrence=alignment.occurrence,
        reference_position=alignment.reference_position,
        comparison_position=alignment.comparison_position,
        reference_label=alignment.reference_label,
        comparison_label=alignment.comparison_label,
    )


def _is_first(
    position: int, position_map: Dict[int, int], first_reference: int
) -> bool:
    mapped = position_map.get(position)
    if mapped is None:
        raise ValueError("a relationship column is not in the aligned pair")
    return mapped == first_reference


def _component_value(component: object) -> Optional[float]:
    availability = getattr(component, "availability")
    if availability is ResultAvailability.AVAILABLE:
        return getattr(component, "value")
    return None


def _component_reason(component: object):
    availability = getattr(component, "availability")
    if availability is ResultAvailability.AVAILABLE:
        return None
    return getattr(component, "reason")
