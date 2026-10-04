"""Target analysis projected from an existing dataset analysis.

A target is analyzed only when the caller names one. This module does
not infer a target, and it does not calculate a relationship, a
descriptive statistic, or a multiple-testing correction. It reads the
selected column's inferred semantic state, the descriptive facts that
column analysis already retained, and the relationship records that
already involve that column.

The target population is the target column's own missingness. It is not
the pairwise population of any feature-target relationship. Adjusted
p-values on those records are the dataset-level relationship screen.
They are not recomputed for the target.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import numpy as np

from pytics.analysis.boolean import BooleanDescriptiveAnalysis
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.relationships.models.boolean_boolean import (
    BooleanBooleanRelationship,
)
from pytics.analysis.relationships.models.categorical_categorical import (
    CategoricalCategoricalRelationship,
)
from pytics.analysis.relationships.models.coverage import RelationshipRecord
from pytics.analysis.relationships.models.coverage import SelectedPairClass
from pytics.analysis.relationships.models.coverage import SelectedPairCoverage
from pytics.analysis.relationships.models.coverage import UnimplementedRelationshipFamily
from pytics.analysis.relationships.models.coverage import classify_selected_pair
from pytics.analysis.relationships.models.numeric_boolean import (
    NumericBooleanRelationship,
)
from pytics.analysis.relationships.models.numeric_categorical import (
    NumericCategoricalRelationship,
)
from pytics.analysis.relationships.models.numeric_numeric import (
    NumericNumericRelationship,
)
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


class TargetStatus(Enum):
    """Whether the selected column can be a target in this version.

    ``SUPPORTED`` is Numeric, Categorical, or Boolean. Those types already
    have descriptive facts and calculated relationship families.
    ``UNSUPPORTED`` is a resolved type this version recognizes and does
    not analyze as a target: Datetime, Timedelta, and Text. ``INELIGIBLE``
    is a resolved type the contract does not treat as a target: Empty,
    Constant, and Identifier. ``UNRESOLVED`` means resolution did not
    select a semantic type. The selected type, when there is one, keeps
    these states distinct.
    """

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    INELIGIBLE = "ineligible"
    UNRESOLVED = "unresolved"


class TargetPhysicalSide(Enum):
    """Which physical side of the canonical pair is the target.

    ``LEFT`` is the smaller physical position. This is not a cause, a
    treatment, or a model input.
    """

    LEFT = "left"
    RIGHT = "right"


class TargetRecordRole(Enum):
    """How the target sits inside a retained relationship record.

    Symmetric pairs record only which physical side the target is.
    Numeric × Categorical and Numeric × Boolean record the analytical
    role already stored on that record. Boolean × Boolean records
    whether the target is the conditioning column or the outcome
    column of that record. None of these roles reverses a stored
    statistic.
    """

    SYMMETRIC_LEFT = "symmetric_left"
    SYMMETRIC_RIGHT = "symmetric_right"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BOOLEAN_GROUP = "boolean_group"
    CONDITIONING = "conditioning"
    OUTCOME = "outcome"


_SUPPORTED_TARGET_TYPES = frozenset(
    {
        SemanticType.NUMERIC,
        SemanticType.CATEGORICAL,
        SemanticType.BOOLEAN,
    }
)
_UNSUPPORTED_TARGET_TYPES = frozenset(
    {
        SemanticType.DATETIME,
        SemanticType.TIMEDELTA,
        SemanticType.TEXT,
    }
)
_INELIGIBLE_TARGET_TYPES = frozenset(
    {
        SemanticType.EMPTY,
        SemanticType.CONSTANT,
        SemanticType.IDENTIFIER,
    }
)
_STRUCTURAL_TARGET_TYPES = frozenset(
    {
        SemanticType.EMPTY,
        SemanticType.CONSTANT,
        SemanticType.BOOLEAN,
        SemanticType.DATETIME,
        SemanticType.TIMEDELTA,
    }
)


@dataclass(frozen=True)
class TargetPosition:
    """Physical column position of an explicit target.

    The position is the column axis index. It is not a column label.
    An integer label is selected by passing that label, not by passing
    this position.
    """

    position: int

    def __post_init__(self) -> None:
        if type(self.position) is not int or self.position < 0:
            raise ValueError("position must be a non-negative int")


@dataclass(frozen=True)
class TargetPopulation:
    """Rows of the target column, split by the target's own missingness.

    ``n_target_non_missing + n_target_missing`` equals ``n_total_rows``.
    Missing target rows stay in the dataset. They are not dropped.
    A relationship population can be smaller, because a pair also drops
    rows that are missing on the other column, and a numeric pair also
    drops non-finite numbers.
    """

    n_total_rows: int
    n_target_non_missing: int
    n_target_missing: int

    def __post_init__(self) -> None:
        _require_count(self.n_total_rows, "n_total_rows")
        _require_count(self.n_target_non_missing, "n_target_non_missing")
        _require_count(self.n_target_missing, "n_target_missing")
        if (
            self.n_target_non_missing + self.n_target_missing
            != self.n_total_rows
        ):
            raise ValueError("target population counts must reconcile")


@dataclass(frozen=True)
class CategoricalTargetFacts:
    """Categorical frequency facts already retained for the target.

    These are the same counts as a categorical variable detail. They are
    not a second frequency table. The mode value and the per-level
    counts are not retained by that evidence, and this record does not
    collect them. There is no balanced or imbalanced verdict.
    """

    n_non_missing: int
    n_unique_non_missing: int
    most_frequent_count: int
    singleton_count: int

    def __post_init__(self) -> None:
        _require_count(self.n_non_missing, "n_non_missing")
        _require_count(self.n_unique_non_missing, "n_unique_non_missing")
        _require_count(self.most_frequent_count, "most_frequent_count")
        _require_count(self.singleton_count, "singleton_count")
        if self.n_non_missing == 0:
            if (
                self.n_unique_non_missing != 0
                or self.most_frequent_count != 0
                or self.singleton_count != 0
            ):
                raise ValueError("an empty categorical target has no frequency counts")
            return
        if self.n_unique_non_missing > self.n_non_missing:
            raise ValueError("n_unique_non_missing cannot exceed n_non_missing")
        if self.most_frequent_count > self.n_non_missing:
            raise ValueError("most_frequent_count cannot exceed n_non_missing")
        if self.singleton_count > self.n_unique_non_missing:
            raise ValueError("singleton_count cannot exceed n_unique_non_missing")
        if self.n_unique_non_missing < 1 or self.most_frequent_count < 1:
            raise ValueError("a non-empty categorical target has a frequency")

    @property
    def most_frequent_ratio(self) -> Optional[float]:
        """Largest non-missing count divided by non-missing target values.

        ``None`` when the target has no non-missing value. This is not
        an imbalance threshold.
        """
        if self.n_non_missing == 0:
            return None
        return self.most_frequent_count / self.n_non_missing

    @property
    def singleton_ratio(self) -> Optional[float]:
        """Share of distinct non-missing values that occur once.

        ``None`` when there is no distinct non-missing value.
        """
        if self.n_unique_non_missing == 0:
            return None
        return self.singleton_count / self.n_unique_non_missing


@dataclass(frozen=True)
class TargetRelationship:
    """One other column, as seen from the selected target.

    ``coverage`` uses the relationship coverage already frozen for the
    dataset. A calculated link holds the existing relationship record.
    An unimplemented or ineligible link is still present, with no record.
    ``target_side`` is the target's physical side of the canonical pair.
    ``record_role`` says how that record already orients the target.
    Adjusted p-values inside a calculated record belong to the full
    dataset relationship screen.
    """

    other_position: int
    other_label: object
    other_selected_type: Optional[SemanticType]
    other_resolution_status: ResolutionStatus
    coverage: SelectedPairCoverage
    unimplemented_family: Optional[UnimplementedRelationshipFamily]
    target_side: TargetPhysicalSide
    record_role: Optional[TargetRecordRole]
    relationship: Optional[RelationshipRecord]

    def __post_init__(self) -> None:
        _require_count(self.other_position, "other_position")
        if self.other_selected_type is not None:
            _require_type(self.other_selected_type, SemanticType, "other_selected_type")
        _require_type(
            self.other_resolution_status,
            ResolutionStatus,
            "other_resolution_status",
        )
        if self.other_resolution_status is ResolutionStatus.RESOLVED:
            if self.other_selected_type is None:
                raise ValueError("a resolved column has a selected semantic type")
        elif self.other_selected_type is not None:
            raise ValueError("an unresolved column has no selected semantic type")
        _require_type(self.coverage, SelectedPairCoverage, "coverage")
        _require_type(self.target_side, TargetPhysicalSide, "target_side")
        if self.record_role is not None:
            _require_type(self.record_role, TargetRecordRole, "record_role")
        classified = SelectedPairClass(
            coverage=self.coverage,
            unimplemented_family=self.unimplemented_family,
        )
        if classified.coverage is SelectedPairCoverage.CALCULATED:
            if self.relationship is None or self.record_role is None:
                raise ValueError("a calculated target link keeps its relationship")
            _require_relationship_record(self.relationship)
            return
        if self.relationship is not None or self.record_role is not None:
            raise ValueError("only a calculated target link keeps a relationship")


@dataclass(frozen=True)
class TargetAnalysis:
    """Analytical target facts for one explicitly selected column.

    ``position`` is the target's identity. ``label`` is the source label
    stored beside it. Selecting the target does not change the inferred
    semantic result. ``confidence`` and ``inference_source`` are present
    only when that result already has a structural interpretation.
    A candidate-derived Numeric, Categorical, or Identifier selection
    keeps those two fields empty. This record does not assign a
    classification or regression problem type.

    ``numeric_facts``, ``boolean_facts``, and ``categorical_facts`` are
    set only for a supported target of that type. Numeric and Boolean
    facts are the objects column analysis already stored. Categorical
    facts copy the retained frequency counts. ``relationships`` follows
    physical column order, skipping the target. It is not sorted by an
    effect or a p-value.
    """

    position: int
    label: object
    selected_type: Optional[SemanticType]
    resolution_status: ResolutionStatus
    confidence: Optional[Confidence]
    inference_source: Optional[InferenceSource]
    status: TargetStatus
    population: TargetPopulation
    numeric_facts: Optional[NumericDescriptiveAnalysis]
    boolean_facts: Optional[BooleanDescriptiveAnalysis]
    categorical_facts: Optional[CategoricalTargetFacts]
    relationships: Tuple[TargetRelationship, ...]

    def __post_init__(self) -> None:
        _require_target_contents(self)

    @property
    def n_other_columns(self) -> int:
        """Columns other than the target. One link each."""
        return len(self.relationships)

    @property
    def n_calculated_relationships(self) -> int:
        """Links that hold an existing relationship record."""
        return _count_coverage(self.relationships, SelectedPairCoverage.CALCULATED)

    @property
    def n_unimplemented_relationships(self) -> int:
        """Links whose recognized family is not calculated."""
        return _count_coverage(
            self.relationships,
            SelectedPairCoverage.UNIMPLEMENTED,
        )

    @property
    def n_ineligible_relationships(self) -> int:
        """Links the relationship contract does not treat as candidates."""
        return _count_coverage(self.relationships, SelectedPairCoverage.INELIGIBLE)


@dataclass(frozen=True)
class TargetSummary:
    """Product projection of a retained target analysis.

    The summary copies identity, semantic state, population, descriptive
    facts, and relationship links. It does not read a DataFrame, infer a
    semantic type, calculate a statistic, or adjust a p-value. Copied
    relationship records are new frozen objects with the same values.
    """

    position: int
    label: object
    selected_type: Optional[SemanticType]
    resolution_status: ResolutionStatus
    confidence: Optional[Confidence]
    inference_source: Optional[InferenceSource]
    status: TargetStatus
    population: TargetPopulation
    numeric_facts: Optional[NumericDescriptiveAnalysis]
    boolean_facts: Optional[BooleanDescriptiveAnalysis]
    categorical_facts: Optional[CategoricalTargetFacts]
    relationships: Tuple[TargetRelationship, ...]

    def __post_init__(self) -> None:
        _require_target_contents(self)

    @property
    def n_other_columns(self) -> int:
        """Columns other than the target. One link each."""
        return len(self.relationships)

    @property
    def n_calculated_relationships(self) -> int:
        """Links that hold a copied relationship record."""
        return _count_coverage(self.relationships, SelectedPairCoverage.CALCULATED)

    @property
    def n_unimplemented_relationships(self) -> int:
        """Links whose recognized family is not calculated."""
        return _count_coverage(
            self.relationships,
            SelectedPairCoverage.UNIMPLEMENTED,
        )

    @property
    def n_ineligible_relationships(self) -> int:
        """Links the relationship contract does not treat as candidates."""
        return _count_coverage(self.relationships, SelectedPairCoverage.INELIGIBLE)


def status_for_target(
    selected_type: Optional[SemanticType],
    resolution_status: ResolutionStatus,
) -> TargetStatus:
    """Return the target status of one already resolved semantic state.

    This does not infer a semantic type. Numeric ``{0, 1}`` stays
    Numeric, and therefore supported, rather than Boolean.
    """
    if not isinstance(resolution_status, ResolutionStatus):
        raise TypeError("resolution_status must be a ResolutionStatus")
    if selected_type is not None and not isinstance(selected_type, SemanticType):
        raise TypeError("selected_type must be a SemanticType or None")
    if resolution_status is not ResolutionStatus.RESOLVED:
        if selected_type is not None:
            raise ValueError("an unresolved target has no selected semantic type")
        return TargetStatus.UNRESOLVED
    if selected_type is None:
        raise ValueError("a resolved target has a selected semantic type")
    if selected_type in _SUPPORTED_TARGET_TYPES:
        return TargetStatus.SUPPORTED
    if selected_type in _UNSUPPORTED_TARGET_TYPES:
        return TargetStatus.UNSUPPORTED
    if selected_type in _INELIGIBLE_TARGET_TYPES:
        return TargetStatus.INELIGIBLE
    raise ValueError("semantic type has no target status")


def resolve_target_position(labels: Sequence[object], target: object) -> int:
    """Resolve an explicit target to one physical column position.

    ``TargetPosition`` selects that index. Any other value is a label.
    The label must equal exactly one column. Boolean labels do not match
    integer labels. A missing label and a duplicated label both raise.
    This function does not choose a column by position, by the name
    ``target``, or by cardinality.
    """
    if isinstance(labels, (str, bytes)):
        raise TypeError("target resolution expects a column axis")
    try:
        count = len(labels)
    except TypeError as error:
        raise TypeError("target resolution expects a column axis") from error
    if isinstance(target, TargetPosition):
        if target.position >= count:
            raise ValueError("target position is outside the column axis")
        return target.position
    matches = [
        index
        for index in range(count)
        if _labels_equal(labels[index], target)
    ]
    if not matches:
        raise ValueError("target column was not found")
    if len(matches) > 1:
        raise ValueError("target label matches more than one column")
    return matches[0]


def project_target_analysis(
    columns: Tuple[ColumnAnalysis, ...],
    relationships: Tuple[RelationshipRecord, ...],
    *,
    position: int,
    n_rows: int,
) -> TargetAnalysis:
    """Project one target from column analyses and relationship records.

    ``position`` is a physical column that was already analyzed.
    Relationship records are attached by identity. No pair is
    recalculated, and no column is reread.
    """
    _require_count(n_rows, "n_rows")
    _require_column_tuple(columns, n_rows)
    if type(position) is not int or position < 0 or position >= len(columns):
        raise ValueError("target position is outside the column axis")
    column = columns[position]
    selected_type = column.inferred.selected_type
    resolution_status = column.inferred.resolution.status
    status = status_for_target(selected_type, resolution_status)
    interpretation = column.inferred.interpretation
    if interpretation is None:
        confidence = None
        inference_source = None
    else:
        confidence = interpretation.confidence
        inference_source = interpretation.source
    basic = column.evidence.basic
    population = TargetPopulation(
        n_total_rows=n_rows,
        n_target_non_missing=basic.n_non_missing,
        n_target_missing=basic.n_missing,
    )
    numeric_facts, boolean_facts, categorical_facts = _target_facts(column, status)
    retained = _relationship_index(relationships)
    links = tuple(
        _link_for_column(column_item, position, selected_type, retained)
        for column_item in columns
        if column_item.position != position
    )
    return TargetAnalysis(
        position=position,
        label=column.label,
        selected_type=selected_type,
        resolution_status=resolution_status,
        confidence=confidence,
        inference_source=inference_source,
        status=status,
        population=population,
        numeric_facts=numeric_facts,
        boolean_facts=boolean_facts,
        categorical_facts=categorical_facts,
        relationships=links,
    )


def build_target_summary(analysis: object) -> Optional[TargetSummary]:
    """Project retained target facts into a product summary.

    The argument must already be a ``DatasetAnalysis``. ``None`` means
    the caller did not request a target. A DataFrame is not accepted
    and is not analyzed. Statistics are not recomputed.
    """
    from pytics.analysis.dataset import DatasetAnalysis as DatasetAnalysisType
    from pytics.analysis.relationships.collector import (
        _copy_relationship as copy_relationship,
    )

    if not isinstance(analysis, DatasetAnalysisType):
        raise TypeError("build_target_summary expects a DatasetAnalysis")
    retained = analysis.target_analysis
    if retained is None:
        return None
    return TargetSummary(
        position=retained.position,
        label=retained.label,
        selected_type=retained.selected_type,
        resolution_status=retained.resolution_status,
        confidence=retained.confidence,
        inference_source=retained.inference_source,
        status=retained.status,
        population=TargetPopulation(
            n_total_rows=retained.population.n_total_rows,
            n_target_non_missing=retained.population.n_target_non_missing,
            n_target_missing=retained.population.n_target_missing,
        ),
        numeric_facts=_copy_numeric_facts(retained.numeric_facts),
        boolean_facts=_copy_boolean_facts(retained.boolean_facts),
        categorical_facts=_copy_categorical_facts(retained.categorical_facts),
        relationships=tuple(
            _copy_link(link, copy_relationship) for link in retained.relationships
        ),
    )


def _require_target_attachment(
    target: Optional[TargetAnalysis],
    columns: Tuple[ColumnAnalysis, ...],
    relationships: Tuple[RelationshipRecord, ...],
    *,
    n_rows: int,
) -> None:
    """Check a retained target against the column and relationship records.

    Descriptive facts and calculated relationships must be the same
    objects those passes already stored. A value-equal copy is not
    another statistical result, but it is not this attachment.
    """
    if target is None:
        return
    if not isinstance(target, TargetAnalysis):
        raise TypeError("target_analysis must be a TargetAnalysis")
    expected = project_target_analysis(
        columns,
        relationships,
        position=target.position,
        n_rows=n_rows,
    )
    if target != expected:
        raise ValueError(
            "target analysis must match the selected column and retained relationships"
        )
    column = columns[target.position]
    if target.numeric_facts is not column.numeric_analysis:
        raise ValueError(
            "numeric target facts must be the retained descriptive analysis"
        )
    if target.boolean_facts is not column.boolean_analysis:
        raise ValueError(
            "boolean target facts must be the retained descriptive analysis"
        )
    for link, expected_link in zip(target.relationships, expected.relationships):
        if link.relationship is not expected_link.relationship:
            raise ValueError(
                "a target relationship must be the retained relationship record"
            )


def _require_target_contents(
    target: Union[TargetAnalysis, TargetSummary],
) -> None:
    _require_count(target.position, "position")
    if target.selected_type is not None:
        _require_type(target.selected_type, SemanticType, "selected_type")
    _require_type(target.resolution_status, ResolutionStatus, "resolution_status")
    if target.confidence is not None:
        _require_type(target.confidence, Confidence, "confidence")
    if target.inference_source is not None:
        _require_type(target.inference_source, InferenceSource, "inference_source")
    if (target.confidence is None) != (target.inference_source is None):
        raise ValueError("confidence and inference source are recorded together")
    _require_type(target.status, TargetStatus, "status")
    expected_status = status_for_target(
        target.selected_type,
        target.resolution_status,
    )
    if target.status is not expected_status:
        raise ValueError("target status must follow the selected semantic state")
    _require_confidence_boundary(target.selected_type, target.confidence)
    _require_type(target.population, TargetPopulation, "population")
    _require_facts(target)
    if not isinstance(target.relationships, tuple):
        raise TypeError("relationships must be a tuple")
    previous = -1
    for link in target.relationships:
        if not isinstance(link, TargetRelationship):
            raise TypeError("relationships must contain TargetRelationship records")
        if link.other_position == target.position:
            raise ValueError("a target relationship cannot name the target")
        if link.other_position <= previous:
            raise ValueError(
                "target relationships must follow ascending physical positions"
            )
        previous = link.other_position
        _require_link(link, target.position, target.selected_type)


def _require_confidence_boundary(
    selected_type: Optional[SemanticType],
    confidence: Optional[Confidence],
) -> None:
    if selected_type in _STRUCTURAL_TARGET_TYPES:
        if confidence is None:
            raise ValueError("a structural target keeps its confidence")
        return
    if confidence is not None:
        raise ValueError("a candidate-derived or unresolved target has no confidence")


def _require_facts(target: Union[TargetAnalysis, TargetSummary]) -> None:
    numeric = target.numeric_facts
    boolean = target.boolean_facts
    categorical = target.categorical_facts
    if numeric is not None:
        _require_type(numeric, NumericDescriptiveAnalysis, "numeric_facts")
    if boolean is not None:
        _require_type(boolean, BooleanDescriptiveAnalysis, "boolean_facts")
    if categorical is not None:
        _require_type(categorical, CategoricalTargetFacts, "categorical_facts")
    if target.status is not TargetStatus.SUPPORTED:
        if numeric is not None or boolean is not None or categorical is not None:
            raise ValueError("only a supported target keeps descriptive facts")
        return
    if target.selected_type is SemanticType.NUMERIC:
        if numeric is None or boolean is not None or categorical is not None:
            raise ValueError("a numeric target keeps numeric facts only")
        if numeric.finite_count > target.population.n_target_non_missing:
            raise ValueError(
                "numeric finite_count cannot exceed non-missing target rows"
            )
        return
    if target.selected_type is SemanticType.BOOLEAN:
        if boolean is None or numeric is not None or categorical is not None:
            raise ValueError("a boolean target keeps boolean facts only")
        if boolean.n_non_missing != target.population.n_target_non_missing:
            raise ValueError("boolean counts must equal non-missing target rows")
        return
    if target.selected_type is SemanticType.CATEGORICAL:
        if categorical is None or numeric is not None or boolean is not None:
            raise ValueError("a categorical target keeps categorical facts only")
        if categorical.n_non_missing != target.population.n_target_non_missing:
            raise ValueError(
                "categorical non-missing count must equal the target population"
            )
        return
    raise ValueError("a supported target is numeric, categorical, or boolean")


def _require_link(
    link: TargetRelationship,
    target_position: int,
    target_type: Optional[SemanticType],
) -> None:
    classified = classify_selected_pair(target_type, link.other_selected_type)
    if link.coverage is not classified.coverage:
        raise ValueError("target coverage must follow the selected semantic pair")
    if link.unimplemented_family is not classified.unimplemented_family:
        raise ValueError("target coverage must name the recognized family")
    expected_side = (
        TargetPhysicalSide.LEFT
        if target_position < link.other_position
        else TargetPhysicalSide.RIGHT
    )
    if link.target_side is not expected_side:
        raise ValueError("target side must follow the physical positions")
    if link.coverage is not SelectedPairCoverage.CALCULATED:
        return
    relationship = link.relationship
    if relationship is None or link.record_role is None:
        raise ValueError("a calculated target link keeps its relationship")
    positions = {relationship.left_position, relationship.right_position}
    if positions != {target_position, link.other_position}:
        raise ValueError("relationship positions must be the target pair")
    if link.record_role is not _record_role(relationship, target_position):
        raise ValueError("target role must follow the retained relationship")


def _target_facts(
    column: ColumnAnalysis,
    status: TargetStatus,
) -> Tuple[
    Optional[NumericDescriptiveAnalysis],
    Optional[BooleanDescriptiveAnalysis],
    Optional[CategoricalTargetFacts],
]:
    if status is not TargetStatus.SUPPORTED:
        return None, None, None
    selected = column.inferred.selected_type
    if selected is SemanticType.NUMERIC:
        if column.numeric_analysis is None:
            raise ValueError(
                "a numeric target requires the retained numeric description"
            )
        return column.numeric_analysis, None, None
    if selected is SemanticType.BOOLEAN:
        if column.boolean_analysis is None:
            raise ValueError(
                "a boolean target requires the retained boolean description"
            )
        return None, column.boolean_analysis, None
    if selected is SemanticType.CATEGORICAL:
        frequency = column.evidence.frequency
        if frequency is None:
            raise ValueError(
                "a categorical target requires the retained frequency evidence"
            )
        basic = frequency.basic
        return (
            None,
            None,
            CategoricalTargetFacts(
                n_non_missing=basic.n_non_missing,
                n_unique_non_missing=basic.n_unique_non_missing,
                most_frequent_count=frequency.most_frequent_count,
                singleton_count=frequency.singleton_count,
            ),
        )
    raise ValueError("a supported target is numeric, categorical, or boolean")


def _link_for_column(
    other: ColumnAnalysis,
    target_position: int,
    target_type: Optional[SemanticType],
    retained: dict[Tuple[int, int], RelationshipRecord],
) -> TargetRelationship:
    selected = other.inferred.selected_type
    classified = classify_selected_pair(target_type, selected)
    relationship = None
    role = None
    if classified.coverage is SelectedPairCoverage.CALCULATED:
        left, right = sorted((target_position, other.position))
        relationship = retained.get((left, right))
        if relationship is None:
            raise ValueError("a calculated target pair requires its relationship record")
        role = _record_role(relationship, target_position)
    side = (
        TargetPhysicalSide.LEFT
        if target_position < other.position
        else TargetPhysicalSide.RIGHT
    )
    return TargetRelationship(
        other_position=other.position,
        other_label=other.label,
        other_selected_type=selected,
        other_resolution_status=other.inferred.resolution.status,
        coverage=classified.coverage,
        unimplemented_family=classified.unimplemented_family,
        target_side=side,
        record_role=role,
        relationship=relationship,
    )


def _record_role(
    relationship: RelationshipRecord,
    target_position: int,
) -> TargetRecordRole:
    if isinstance(
        relationship,
        (NumericNumericRelationship, CategoricalCategoricalRelationship),
    ):
        if relationship.left_position == target_position:
            return TargetRecordRole.SYMMETRIC_LEFT
        return TargetRecordRole.SYMMETRIC_RIGHT
    if isinstance(relationship, NumericBooleanRelationship):
        if relationship.boolean_position == target_position:
            return TargetRecordRole.BOOLEAN_GROUP
        return TargetRecordRole.NUMERIC
    if isinstance(relationship, NumericCategoricalRelationship):
        if relationship.numeric_position == target_position:
            return TargetRecordRole.NUMERIC
        return TargetRecordRole.CATEGORICAL
    if isinstance(relationship, BooleanBooleanRelationship):
        if relationship.conditioning_position == target_position:
            return TargetRecordRole.CONDITIONING
        return TargetRecordRole.OUTCOME
    raise TypeError("relationship records must be calculated relationship values")


def _relationship_index(
    relationships: Tuple[RelationshipRecord, ...],
) -> dict[Tuple[int, int], RelationshipRecord]:
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    indexed: dict[Tuple[int, int], RelationshipRecord] = {}
    for relationship in relationships:
        _require_relationship_record(relationship)
        key = (relationship.left_position, relationship.right_position)
        if key in indexed:
            raise ValueError("relationship positions must be unique")
        indexed[key] = relationship
    return indexed


def _require_relationship_record(relationship: object) -> None:
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
        raise TypeError("relationships must contain calculated relationship records")


def _copy_link(link: TargetRelationship, copy_relationship: object) -> TargetRelationship:
    relationship = link.relationship
    copied = None if relationship is None else copy_relationship(relationship)
    return TargetRelationship(
        other_position=link.other_position,
        other_label=link.other_label,
        other_selected_type=link.other_selected_type,
        other_resolution_status=link.other_resolution_status,
        coverage=link.coverage,
        unimplemented_family=link.unimplemented_family,
        target_side=link.target_side,
        record_role=link.record_role,
        relationship=copied,
    )


def _copy_numeric_facts(
    facts: Optional[NumericDescriptiveAnalysis],
) -> Optional[NumericDescriptiveAnalysis]:
    if facts is None:
        return None
    return NumericDescriptiveAnalysis(
        finite_count=facts.finite_count,
        minimum=facts.minimum,
        maximum=facts.maximum,
        mean=facts.mean,
        median=facts.median,
        standard_deviation=facts.standard_deviation,
        q1=facts.q1,
        q3=facts.q3,
    )


def _copy_boolean_facts(
    facts: Optional[BooleanDescriptiveAnalysis],
) -> Optional[BooleanDescriptiveAnalysis]:
    if facts is None:
        return None
    return BooleanDescriptiveAnalysis(
        true_count=facts.true_count,
        false_count=facts.false_count,
    )


def _copy_categorical_facts(
    facts: Optional[CategoricalTargetFacts],
) -> Optional[CategoricalTargetFacts]:
    if facts is None:
        return None
    return CategoricalTargetFacts(
        n_non_missing=facts.n_non_missing,
        n_unique_non_missing=facts.n_unique_non_missing,
        most_frequent_count=facts.most_frequent_count,
        singleton_count=facts.singleton_count,
    )


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


def _count_coverage(
    relationships: Tuple[TargetRelationship, ...],
    coverage: SelectedPairCoverage,
) -> int:
    return sum(1 for link in relationships if link.coverage is coverage)


def _labels_equal(label: object, target: object) -> bool:
    """Return whether a stored label is the requested target label.

    Boolean and integer labels stay distinct. ``True == 1`` is true in
    Python, and that comparison must not select one of those labels as
    the other. A NumPy integer label still matches a Python integer of
    the same value.
    """
    if label is target:
        return True
    label_is_bool = _is_boolean_label(label)
    target_is_bool = _is_boolean_label(target)
    if label_is_bool or target_is_bool:
        if label_is_bool and target_is_bool:
            return bool(label) is bool(target)
        return False
    try:
        equal = label == target
    except TypeError:
        return False
    if isinstance(equal, np.ndarray):
        return False
    if equal is True or equal is False:
        return equal
    if isinstance(equal, np.bool_):
        return bool(equal)
    return False


def _is_boolean_label(value: object) -> bool:
    return type(value) is bool or isinstance(value, np.bool_)


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_type(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")
