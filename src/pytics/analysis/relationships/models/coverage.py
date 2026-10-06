"""Relationship coverage and the heterogeneous record container.

This module names which families this version calculates and retains
the records a dataset actually produced. It does not name one method,
one population rule, or one confidence level for every pair.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple
from typing import Union

from pytics.semantics.interpretation import SemanticType

from pytics.analysis.relationships.models.boolean_boolean import (
    BooleanBooleanRelationship,
)
from pytics.analysis.relationships.models.categorical_categorical import (
    CategoricalCategoricalRelationship,
)
from pytics.analysis.relationships.models.common import _require_nonnegative
from pytics.analysis.relationships.models.numeric_boolean import (
    NumericBooleanRelationship,
)
from pytics.analysis.relationships.models.numeric_categorical import (
    NumericCategoricalRelationship,
)
from pytics.analysis.relationships.models.numeric_numeric import (
    NumericNumericRelationship,
)


class UnimplementedRelationshipFamily(Enum):
    """Recognized relationship family this version does not calculate.

    Unimplemented means the semantic pair has a meaningful analytical
    family under the current contract, and Pytics does not yet produce
    a record for it. It does not mean the pair is ineligible. Both
    physical orientations of one family share one member. A count of
    these pairs is not a claim that the family was analyzed.
    """

    DATETIME_NUMERIC = "datetime_numeric"
    DATETIME_CATEGORICAL = "datetime_categorical"
    CATEGORICAL_BOOLEAN = "categorical_boolean"


class SelectedPairCoverage(Enum):
    """Coverage of one unordered pair of selected semantic types.

    ``CALCULATED`` means this version produces a relationship record.
    ``UNIMPLEMENTED`` means a recognized family has no calculator yet.
    ``INELIGIBLE`` means the contract does not treat the pair as a
    relationship candidate. A missing selected type is ineligible.
    """

    CALCULATED = "calculated"
    UNIMPLEMENTED = "unimplemented"
    INELIGIBLE = "ineligible"


@dataclass(frozen=True)
class SelectedPairClass:
    """Classification of one unordered semantic pair.

    ``unimplemented_family`` is set only for ``UNIMPLEMENTED``. A
    calculated pair names its family by the record that is produced,
    not by this object.
    """

    coverage: SelectedPairCoverage
    unimplemented_family: Optional[UnimplementedRelationshipFamily] = None

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, SelectedPairCoverage):
            raise TypeError("coverage must be a SelectedPairCoverage")
        if self.coverage is SelectedPairCoverage.UNIMPLEMENTED:
            if not isinstance(
                self.unimplemented_family,
                UnimplementedRelationshipFamily,
            ):
                raise ValueError("an unimplemented pair names its recognized family")
            return
        if self.unimplemented_family is not None:
            raise ValueError("only an unimplemented pair names a family")


# Recognized directions that are not calculated. Lookup ignores order.
_UNIMPLEMENTED_FAMILIES = {
    frozenset((SemanticType.DATETIME, SemanticType.NUMERIC)): (
        UnimplementedRelationshipFamily.DATETIME_NUMERIC
    ),
    frozenset((SemanticType.DATETIME, SemanticType.CATEGORICAL)): (
        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL
    ),
    frozenset((SemanticType.CATEGORICAL, SemanticType.BOOLEAN)): (
        UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN
    ),
}


def classify_selected_pair(
    left: Optional[SemanticType],
    right: Optional[SemanticType],
) -> SelectedPairClass:
    """Classify one unordered pair of selected semantic types.

    ``None`` is an unresolved column. It is ineligible, as are Identifier,
    Constant, Empty, Text, Timedelta, and pair types with no recognized
    family. A recognized family that is not calculated is unimplemented.
    Categorical × Boolean is that family in either physical order.
    Datetime × Boolean is ineligible: no datetime-boolean family is
    recognized, and Boolean is not collapsed into Categorical.
    This function does not read values and does not calculate a statistic.
    """
    if left is not None and not isinstance(left, SemanticType):
        raise TypeError("left must be a SemanticType or None")
    if right is not None and not isinstance(right, SemanticType):
        raise TypeError("right must be a SemanticType or None")
    if left is None or right is None:
        return SelectedPairClass(coverage=SelectedPairCoverage.INELIGIBLE)
    if left is SemanticType.NUMERIC and right is SemanticType.NUMERIC:
        return SelectedPairClass(coverage=SelectedPairCoverage.CALCULATED)
    if {left, right} == {SemanticType.NUMERIC, SemanticType.CATEGORICAL}:
        return SelectedPairClass(coverage=SelectedPairCoverage.CALCULATED)
    if left is SemanticType.BOOLEAN and right is SemanticType.BOOLEAN:
        return SelectedPairClass(coverage=SelectedPairCoverage.CALCULATED)
    if {left, right} == {SemanticType.NUMERIC, SemanticType.BOOLEAN}:
        return SelectedPairClass(coverage=SelectedPairCoverage.CALCULATED)
    if left is SemanticType.CATEGORICAL and right is SemanticType.CATEGORICAL:
        return SelectedPairClass(coverage=SelectedPairCoverage.CALCULATED)
    family = _UNIMPLEMENTED_FAMILIES.get(frozenset((left, right)))
    if family is None:
        return SelectedPairClass(coverage=SelectedPairCoverage.INELIGIBLE)
    return SelectedPairClass(
        coverage=SelectedPairCoverage.UNIMPLEMENTED,
        unimplemented_family=family,
    )


@dataclass(frozen=True)
class UnimplementedFamilyCount:
    """How many physical pairs share one recognized, unimplemented family.

    ``n_pairs`` is at least one. A family with no pairs is omitted.
    """

    family: UnimplementedRelationshipFamily
    n_pairs: int

    def __post_init__(self) -> None:
        if not isinstance(self.family, UnimplementedRelationshipFamily):
            raise TypeError("family must be an UnimplementedRelationshipFamily")
        if type(self.n_pairs) is not int or self.n_pairs < 1:
            raise ValueError("n_pairs must be a positive int")


RelationshipRecord = Union[
    NumericNumericRelationship,
    NumericCategoricalRelationship,
    BooleanBooleanRelationship,
    NumericBooleanRelationship,
    CategoricalCategoricalRelationship,
]


@dataclass(frozen=True)
class RelationshipAnalysis:
    """Coverage and retained relationship records for one dataset.

    This container answers which relationship analyses were performed
    and how pair coverage was counted. It does not name one statistical
    method, one population rule, one computational image, or one
    confidence level for every record.

    Supported pairs are family-specific records, in ascending physical
    position order. ``RelationshipFamily`` names the families this
    version can calculate. Records name the families present in this
    dataset.

    Calculated, or supported, means Pytics computes a relationship
    record for that semantic pair family. Unimplemented means a
    recognized family has no calculator yet, so those pairs are counts.
    Ineligible means the current contract does not treat that semantic
    pair as a relationship candidate. Ineligible is not a placeholder
    for a recognized family that has not been implemented.
    ``n_analyzed_pairs`` is the number of retained records, including
    records whose statistical components are unavailable. It is not a
    count of significant tests.
    """

    n_rows: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[RelationshipRecord, ...]

    def __post_init__(self) -> None:
        _require_nonnegative(self.n_rows, "n_rows")
        _require_nonnegative(self.n_total_pairs, "n_total_pairs")
        _require_nonnegative(self.n_supported_pairs, "n_supported_pairs")
        _require_nonnegative(self.n_analyzed_pairs, "n_analyzed_pairs")
        _require_nonnegative(
            self.n_unimplemented_family_pairs,
            "n_unimplemented_family_pairs",
        )
        _require_nonnegative(self.n_ineligible_pairs, "n_ineligible_pairs")
        if (
            self.n_supported_pairs
            + self.n_unimplemented_family_pairs
            + self.n_ineligible_pairs
            != self.n_total_pairs
        ):
            raise ValueError("pair counts must sum to n_total_pairs")
        if self.n_analyzed_pairs != self.n_supported_pairs:
            raise ValueError("every supported pair is analyzed")
        _require_family_counts(
            self.unimplemented_family_counts,
            self.n_unimplemented_family_pairs,
        )
        _require_relationships(self.relationships, self.n_rows, self.n_analyzed_pairs)

    @property
    def n_unsupported_pairs(self) -> int:
        """Pairs that were not analyzed.

        This is the unimplemented recognized families plus the ineligible
        pairs. Unsupported does not mean the data are invalid.
        """
        return self.n_unimplemented_family_pairs + self.n_ineligible_pairs


def _require_relationships(
    relationships: Tuple[RelationshipRecord, ...],
    n_rows: int,
    n_analyzed: int,
) -> None:
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    if len(relationships) != n_analyzed:
        raise ValueError("n_analyzed_pairs must equal the relationship records")
    previous = (-1, -1)
    for relationship in relationships:
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
        if relationship.n_total_rows != n_rows:
            raise ValueError("relationship rows must equal the dataset row count")
        key = (relationship.left_position, relationship.right_position)
        if key <= previous:
            raise ValueError("relationships must be ordered by ascending positions")
        previous = key


def _require_family_counts(
    counts: Tuple[UnimplementedFamilyCount, ...],
    n_pairs: int,
) -> None:
    if not isinstance(counts, tuple):
        raise TypeError("unimplemented_family_counts must be a tuple")
    seen = []
    total = 0
    for item in counts:
        if not isinstance(item, UnimplementedFamilyCount):
            raise TypeError(
                "unimplemented_family_counts must contain UnimplementedFamilyCount values"
            )
        seen.append(item.family)
        total += item.n_pairs
    if len(seen) != len(set(seen)):
        raise ValueError("an unimplemented family is counted more than once")
    order = {
        family: index for index, family in enumerate(UnimplementedRelationshipFamily)
    }
    if seen != sorted(seen, key=lambda family: order[family]):
        raise ValueError("unimplemented families must follow definition order")
    if total != n_pairs:
        raise ValueError("unimplemented family counts must sum to the family total")
