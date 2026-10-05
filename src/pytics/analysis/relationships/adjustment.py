"""Dataset-level Benjamini–Hochberg adjustment for relationship tests.

Pair calculators store raw p-values. This module runs after those
records exist and before ``RelationshipAnalysis`` is frozen. It adjusts
one primary p-value per calculated pair when that p-value was computed
and is inferentially valid. Complementary p-values stay raw. An
unavailable p-value is not counted. A computed chi-square p-value whose
Cochran convention failed is not counted. The summary builder does not
call this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from dataclasses import replace
from typing import Dict
from typing import Sequence
from typing import Tuple
from typing import Union

from pytics.analysis.relationships.models import AssociationMethod
from pytics.analysis.relationships.models import BooleanBooleanRelationship
from pytics.analysis.relationships.models import BooleanIndependenceMethod
from pytics.analysis.relationships.models import CategoricalCategoricalRelationship
from pytics.analysis.relationships.models import CategoricalIndependenceMethod
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import MeanDifferenceTestMethod
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import NumericBooleanRelationship
from pytics.analysis.relationships.models import NumericCategoricalRelationship
from pytics.analysis.relationships.models import NumericNumericRelationship
from pytics.analysis.relationships.models import OmnibusTestMethod
from pytics.analysis.relationships.models import RelationshipFamily
from pytics.analysis.relationships.models import RelationshipRecord
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import inferential_p_value_eligible

_PrimaryTestMethod = Union[
    AssociationMethod,
    OmnibusTestMethod,
    MeanDifferenceTestMethod,
    BooleanIndependenceMethod,
    CategoricalIndependenceMethod,
]


@dataclass(frozen=True)
class _PrimaryHypothesis:
    """Identity of one p-value in the exploratory correction family.

    Positions are the canonical physical pair. ``family`` is the
    calculated relationship family. ``method`` is that family's primary
    test. Column labels are not part of the identity.
    """

    left_position: int
    right_position: int
    family: RelationshipFamily
    method: _PrimaryTestMethod


def benjamini_hochberg(p_values: Sequence[float]) -> Tuple[float, ...]:
    """Return Benjamini–Hochberg adjusted p-values in input order.

    ``m`` is the number of values passed in, which is the number of
    available p-values in one correction family. For ascending
    ``p_(1) <= ... <= p_(m)``, rank ``i`` starts at
    ``min(1, p_(i) * m / i)``. Each rank is then replaced by the minimum
    of that value and every later rank. Equal raw p-values are adjacent
    after the sort, so they receive one adjusted value. Ties break by
    original position only to keep the sort deterministic; that order
    does not change the adjusted value. A raw zero stays zero. No
    significance threshold is applied.
    """
    validated = _require_correction_p_values(p_values)
    m = len(validated)
    if m == 0:
        return ()
    order = sorted(range(m), key=lambda index: (validated[index], index))
    adjusted = [0.0] * m
    limit = 1.0
    for rank in range(m, 0, -1):
        index = order[rank - 1]
        raw = validated[index]
        candidate = raw * m / rank
        if candidate > 1.0 or not math.isfinite(candidate):
            candidate = 1.0
        if candidate > limit:
            candidate = limit
        else:
            limit = candidate
        if candidate == 0.0:
            candidate = 0.0
        adjusted[index] = candidate
    return tuple(adjusted)


def adjust_primary_p_values(
    relationships: Tuple[RelationshipRecord, ...],
) -> Tuple[RelationshipRecord, ...]:
    """Attach Benjamini–Hochberg results to primary relationship tests.

    Each calculated pair contributes at most one hypothesis: Spearman,
    one-way ANOVA, Welch, Fisher exact, or Pearson chi-square, and only
    when that raw p-value is available and inferentially valid. Pearson
    correlation is complementary and stays raw. A chi-square p-value
    that was computed but failed Cochran's expected-count convention
    stays on its record and is not a member. ``m`` is the number of
    eligible primary p-values, not the number of physical pairs and not
    the number of computed tails. Records outside the family are
    returned unchanged. The replacement is a new frozen record; nested
    tables and group summaries are not rebuilt.
    """
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    included: Dict[_PrimaryHypothesis, int] = {}
    p_values = []
    for record in relationships:
        hypothesis, evidence = _primary_hypothesis(record)
        if not inferential_p_value_eligible(
            evidence.availability,
            evidence.inferential_validity,  # type: ignore[arg-type]
        ):
            continue
        if hypothesis in included:
            raise ValueError("a primary hypothesis was recorded twice")
        if evidence.p_value is None:
            raise ValueError("an available primary test has no raw p-value")
        included[hypothesis] = len(p_values)
        p_values.append(evidence.p_value)
    if not p_values:
        return relationships
    adjusted = benjamini_hochberg(tuple(p_values))
    by_hypothesis = {
        hypothesis: adjusted[index] for hypothesis, index in included.items()
    }
    return tuple(
        _with_primary_adjustment(record, by_hypothesis) for record in relationships
    )


def _require_correction_p_values(p_values: Sequence[float]) -> Tuple[float, ...]:
    if isinstance(p_values, (str, bytes)):
        raise TypeError("p-values must be a sequence of floats")
    validated = []
    for value in p_values:
        if type(value) is not float or not math.isfinite(value):
            raise ValueError("a correction p-value must be a finite float")
        if value < 0.0 or value > 1.0:
            raise ValueError("a correction p-value must lie on [0, 1]")
        validated.append(0.0 if value == 0.0 else value)
    return tuple(validated)


def _primary_hypothesis(
    record: RelationshipRecord,
) -> Tuple[_PrimaryHypothesis, FrequentistEvidence]:
    if isinstance(record, NumericNumericRelationship):
        return (
            _PrimaryHypothesis(
                record.left_position,
                record.right_position,
                RelationshipFamily.NUMERIC_NUMERIC,
                AssociationMethod.SPEARMAN,
            ),
            record.spearman.frequentist,
        )
    if isinstance(record, NumericCategoricalRelationship):
        return (
            _PrimaryHypothesis(
                record.left_position,
                record.right_position,
                RelationshipFamily.NUMERIC_CATEGORICAL,
                OmnibusTestMethod.ONE_WAY_ANOVA,
            ),
            record.omnibus.frequentist,
        )
    if isinstance(record, NumericBooleanRelationship):
        return (
            _PrimaryHypothesis(
                record.left_position,
                record.right_position,
                RelationshipFamily.NUMERIC_BOOLEAN,
                MeanDifferenceTestMethod.WELCH_T,
            ),
            record.mean_difference_test.frequentist,
        )
    if isinstance(record, BooleanBooleanRelationship):
        return (
            _PrimaryHypothesis(
                record.left_position,
                record.right_position,
                RelationshipFamily.BOOLEAN_BOOLEAN,
                BooleanIndependenceMethod.FISHER_EXACT,
            ),
            record.independence.frequentist,
        )
    if isinstance(record, CategoricalCategoricalRelationship):
        return (
            _PrimaryHypothesis(
                record.left_position,
                record.right_position,
                RelationshipFamily.CATEGORICAL_CATEGORICAL,
                CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            ),
            record.independence.frequentist,
        )
    raise TypeError("relationship record has no primary test")


def _with_primary_adjustment(
    record: RelationshipRecord,
    adjusted_by_hypothesis: Dict[_PrimaryHypothesis, float],
) -> RelationshipRecord:
    hypothesis, evidence = _primary_hypothesis(record)
    adjusted = adjusted_by_hypothesis.get(hypothesis)
    if adjusted is None:
        return record
    if evidence.availability is not ResultAvailability.AVAILABLE:
        return record
    updated = replace(
        evidence,
        adjusted_p_value=adjusted,
        adjustment=MultipleTestingAdjustment.BENJAMINI_HOCHBERG,
    )
    if isinstance(record, NumericNumericRelationship):
        return _adjust_numeric_numeric(record, updated)
    if isinstance(record, NumericCategoricalRelationship):
        return _adjust_numeric_categorical(record, updated)
    if isinstance(record, NumericBooleanRelationship):
        return _adjust_numeric_boolean(record, updated)
    if isinstance(record, BooleanBooleanRelationship):
        return _adjust_boolean_boolean(record, updated)
    if isinstance(record, CategoricalCategoricalRelationship):
        return _adjust_categorical_categorical(record, updated)
    raise TypeError("relationship record has no primary test")


def _adjust_numeric_numeric(
    record: NumericNumericRelationship,
    frequentist: FrequentistEvidence,
) -> NumericNumericRelationship:
    spearman = replace(record.spearman, frequentist=frequentist)
    return replace(record, methods=(spearman, record.pearson))


def _adjust_numeric_categorical(
    record: NumericCategoricalRelationship,
    frequentist: FrequentistEvidence,
) -> NumericCategoricalRelationship:
    return replace(record, omnibus=replace(record.omnibus, frequentist=frequentist))


def _adjust_numeric_boolean(
    record: NumericBooleanRelationship,
    frequentist: FrequentistEvidence,
) -> NumericBooleanRelationship:
    return replace(
        record,
        mean_difference_test=replace(
            record.mean_difference_test,
            frequentist=frequentist,
        ),
    )


def _adjust_boolean_boolean(
    record: BooleanBooleanRelationship,
    frequentist: FrequentistEvidence,
) -> BooleanBooleanRelationship:
    return replace(
        record,
        independence=replace(record.independence, frequentist=frequentist),
    )


def _adjust_categorical_categorical(
    record: CategoricalCategoricalRelationship,
    frequentist: FrequentistEvidence,
) -> CategoricalCategoricalRelationship:
    return replace(
        record,
        independence=replace(record.independence, frequentist=frequentist),
    )
