"""Relationship coverage and the heterogeneous record container.

This module names which families this version calculates and retains
the records a dataset actually produced. It does not name one method,
one population rule, or one confidence level for every pair.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple
from typing import Union

from pytics.analysis.relationships.models.boolean_boolean import (
    BooleanBooleanRelationship,
)
from pytics.analysis.relationships.models.common import _require_nonnegative
from pytics.analysis.relationships.models.numeric_categorical import (
    NumericCategoricalRelationship,
)
from pytics.analysis.relationships.models.numeric_numeric import (
    NumericNumericRelationship,
)


class UnimplementedRelationshipFamily(Enum):
    """Accepted pair direction that this slice does not calculate.

    A count of these pairs is not a claim that the family was analyzed.
    """

    NUMERIC_BOOLEAN = "numeric_boolean"
    CATEGORICAL_CATEGORICAL = "categorical_categorical"
    DATETIME_NUMERIC = "datetime_numeric"
    DATETIME_CATEGORICAL = "datetime_categorical"


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
    dataset. Unimplemented recognized families and ineligible pairs are
    counts, because those pairs have no record. ``n_analyzed_pairs`` is
    the number of retained records, including records whose statistical
    components are unavailable. It is not a count of significant tests.
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


@dataclass(frozen=True)
class RelationshipsSummary:
    """Product projection of a retained relationship analysis.

    The summary is not a second statistical analysis. It copies coverage
    counts and family records so a later Relationships view can read them
    without the rest of ``DatasetAnalysis``. ``n_columns`` is copied so
    the unordered-pair total can be checked against the schema.

    The builder does not read a DataFrame, infer a family, or calculate
    a statistic. It does not restate a method, a population rule, a
    computational image, or a confidence level that is not already on
    the copied record.
    """

    n_rows: int
    n_columns: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[RelationshipRecord, ...]

    def __post_init__(self) -> None:
        _require_nonnegative(self.n_rows, "n_rows")
        _require_nonnegative(self.n_columns, "n_columns")
        expected = self.n_columns * (self.n_columns - 1) // 2
        if self.n_total_pairs != expected:
            raise ValueError("n_total_pairs must equal the unordered column pairs")
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
        """Pairs that were not analyzed."""
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
