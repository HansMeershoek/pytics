"""Numeric relationship analysis for one DataFrame.

Relationships are dataset-level facts. They are not semantic evidence.
The semantic engine has already selected a type for each physical column.
This module asks whether two selected types are a supported pair and, for
the one implemented family, describes that pair.

The implemented family is selected Numeric × selected Numeric. Spearman
rank correlation is the primary descriptive association. Pearson
product-moment correlation is a complementary linear association. Neither
method is chosen by a normality test. No other pair family is calculated.

Pair identity is the physical column positions, ordered so the left
position is smaller. Labels are not identity. Self-pairs are not pairs.
Each eligible pair uses the rows in which both values are finite. Missing
values and positive or negative infinity are excluded. Rows are not
imputed, and one column's missingness does not drop the whole dataset.

Estimates are calculated from a float64 image of those paired values so
the result can use SciPy. Integers above the float64 exact-integer range,
``2**53``, are not exact in that image. When the image removes all
variation that the original paired values had, the methods are unavailable.
A fabricated zero correlation is not stored. The source arrays and the
SciPy result objects are not retained.

An estimate, its frequentist p-value, and a confidence interval can each
be unavailable on their own. Unavailability is a state of that component.
It does not fail the dataset analysis. Raw p-values are stored when the
test exists. Adjusted p-values are not calculated: the test family for
multiple-testing correction is not defined. There is no significance flag,
no strength label, and no Finding.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.stats import pearsonr
from scipy.stats import spearmanr

from pytics.analysis.column import ColumnAnalysis
from pytics.semantics.interpretation import SemanticType

# Two finite paired observations can define a correlation of exactly ±1.
# A two-sided test needs a positive degrees-of-freedom count, ``n - 2``.
# The classical Fisher z interval needs a positive variance, ``1 / (n - 3)``.
_MIN_ESTIMATE_N = 2
_MIN_TEST_N = 3
_MIN_PEARSON_INTERVAL_N = 4

# Two-sided 95% interval. The level is not configurable in this slice.
_CONFIDENCE_LEVEL = 0.95

# Float64 can sit slightly outside [-1, 1] after a correlation product.
# A larger departure is not a correlation.
_CORRELATION_CLAMP = 1e-8


class AssociationMethod(Enum):
    """Machine-readable association method.

    Display names are not this identity.
    """

    SPEARMAN = "spearman"
    PEARSON = "pearson"


class RelationshipFamily(Enum):
    """Implemented relationship family.

    Further families are not members of this enum until a method exists.
    """

    NUMERIC_NUMERIC = "numeric_numeric"


class UnimplementedRelationshipFamily(Enum):
    """Accepted pair direction that this slice does not calculate.

    A count of these pairs is not a claim that the family was analyzed.
    """

    NUMERIC_BOOLEAN = "numeric_boolean"
    NUMERIC_CATEGORICAL = "numeric_categorical"
    BOOLEAN_BOOLEAN = "boolean_boolean"
    CATEGORICAL_CATEGORICAL = "categorical_categorical"
    DATETIME_NUMERIC = "datetime_numeric"
    DATETIME_CATEGORICAL = "datetime_categorical"


class _Eligibility(Enum):
    """Classifier outcome other than an unimplemented recognized family."""

    SUPPORTED = "supported"
    INELIGIBLE = "ineligible"


class ResultAvailability(Enum):
    """Whether one statistical component has a value."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class UnavailabilityReason(Enum):
    """Why a component has no value.

    These are analytical states, not user-facing prose.
    """

    INSUFFICIENT_PAIRED_OBSERVATIONS = "insufficient_paired_observations"
    CONSTANT_PAIRED_VALUES = "constant_paired_values"
    PRECISION_COLLAPSED = "precision_collapsed"
    NON_FINITE_RESULT = "non_finite_result"
    BOUNDARY_CORRELATION = "boundary_correlation"
    INTERVAL_NOT_DEFINED_FOR_METHOD = "interval_not_defined_for_method"


class EffectDirection(Enum):
    """Sign of a correlation estimate.

    A nonzero floating-point value keeps its sign. Strength is not a
    direction.
    """

    NEGATIVE = "negative"
    ZERO = "zero"
    POSITIVE = "positive"


class CorrelationIntervalMethod(Enum):
    """How a correlation interval was obtained."""

    FISHER_Z = "fisher_z"


class MultipleTestingAdjustment(Enum):
    """Multiple-testing status of a stored p-value.

    ``NOT_APPLIED`` means the raw p-value has no adjusted companion yet.
    """

    NOT_APPLIED = "not_applied"


class PairPopulation(Enum):
    """Which rows enter a Numeric × Numeric correlation."""

    PAIRWISE_FINITE = "pairwise_finite"


class NumericComputation(Enum):
    """Computational representation passed to the correlation routines.

    ``FLOAT64`` does not claim exact integer correlation above ``2**53``.
    """

    FLOAT64 = "float64"


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


@dataclass(frozen=True)
class CorrelationEstimate:
    """Effect estimate for one association method.

    ``value`` is a Python float in ``[-1, 1]`` when available. It is never
    NaN. ``direction`` is the sign of that value. ``reason`` is set only
    when the estimate is unavailable.
    """

    availability: ResultAvailability
    value: Optional[float]
    direction: Optional[EffectDirection]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_correlation(self.value, "estimate")
            _require_enum(self.direction, EffectDirection, "direction")
            if self.reason is not None:
                raise ValueError("an available estimate has no unavailability reason")
            if _direction(self.value) is not self.direction:  # type: ignore[arg-type]
                raise ValueError("direction must match the estimate sign")
            return
        if self.value is not None or self.direction is not None:
            raise ValueError("an unavailable estimate has no value or direction")
        _require_enum(self.reason, UnavailabilityReason, "reason")


@dataclass(frozen=True)
class FrequentistEvidence:
    """Raw frequentist evidence attached to one estimate.

    ``p_value`` is the two-sided SciPy p-value when the test is available.
    ``adjusted_p_value`` stays ``None`` while adjustment is not applied.
    The p-value is not a significance flag.
    """

    availability: ResultAvailability
    p_value: Optional[float]
    adjusted_p_value: Optional[float]
    adjustment: MultipleTestingAdjustment
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        _require_enum(self.adjustment, MultipleTestingAdjustment, "adjustment")
        if self.adjusted_p_value is not None:
            raise ValueError("an unadjusted test has no adjusted p-value")
        if self.availability is ResultAvailability.AVAILABLE:
            _require_p_value(self.p_value)
            if self.reason is not None:
                raise ValueError("an available test has no unavailability reason")
            return
        if self.p_value is not None:
            raise ValueError("an unavailable test has no p-value")
        _require_enum(self.reason, UnavailabilityReason, "reason")


@dataclass(frozen=True)
class CorrelationInterval:
    """Uncertainty interval for one correlation estimate.

    An available interval records its level and method. Spearman has no
    interval in this slice, so its interval stays unavailable even when
    the estimate exists.
    """

    availability: ResultAvailability
    level: Optional[float]
    method: Optional[CorrelationIntervalMethod]
    lower: Optional[float]
    upper: Optional[float]
    reason: Optional[UnavailabilityReason]

    def __post_init__(self) -> None:
        _require_enum(self.availability, ResultAvailability, "availability")
        if self.availability is ResultAvailability.AVAILABLE:
            if self.level != _CONFIDENCE_LEVEL:
                raise ValueError("confidence level must be 0.95")
            if self.method is not CorrelationIntervalMethod.FISHER_Z:
                raise ValueError("confidence interval method must be Fisher z")
            _require_correlation(self.lower, "lower")
            _require_correlation(self.upper, "upper")
            if self.lower > self.upper:  # type: ignore[operator]
                raise ValueError("interval bounds are out of order")
            if self.reason is not None:
                raise ValueError("an available interval has no unavailability reason")
            return
        if (
            self.level is not None
            or self.method is not None
            or self.lower is not None
            or self.upper is not None
        ):
            raise ValueError("an unavailable interval has no bounds")
        _require_enum(self.reason, UnavailabilityReason, "reason")


@dataclass(frozen=True)
class AssociationResult:
    """One association method on one numeric pair.

    ``n_observations`` is the pairwise finite count the method considered.
    The estimate, the test, and the interval do not share one availability
    flag. Spearman does not carry a confidence interval in this slice.
    """

    method: AssociationMethod
    n_observations: int
    estimate: CorrelationEstimate
    frequentist: FrequentistEvidence
    confidence_interval: CorrelationInterval

    def __post_init__(self) -> None:
        _require_enum(self.method, AssociationMethod, "method")
        if type(self.n_observations) is not int or self.n_observations < 0:
            raise ValueError("n_observations must be a non-negative int")
        _require_type(self.estimate, CorrelationEstimate, "estimate")
        _require_type(self.frequentist, FrequentistEvidence, "frequentist")
        _require_type(
            self.confidence_interval,
            CorrelationInterval,
            "confidence_interval",
        )
        _require_component_consistency(self)


@dataclass(frozen=True)
class NumericNumericRelationship:
    """One selected Numeric × selected Numeric pair.

    ``left_position`` is less than ``right_position``. Both are physical
    positions. ``n_paired`` counts rows where both source values are
    finite. ``n_excluded`` is every other row, including rows where either
    value is missing or infinite. The paired arrays are not stored.

    ``methods`` is Spearman, then Pearson. Both records exist when a
    method is unavailable.
    """

    left_position: int
    left_label: object
    right_position: int
    right_label: object
    n_total_rows: int
    n_paired: int
    methods: Tuple[AssociationResult, ...]

    def __post_init__(self) -> None:
        _require_position(self.left_position, "left_position")
        _require_position(self.right_position, "right_position")
        if self.left_position >= self.right_position:
            raise ValueError("left_position must be less than right_position")
        if type(self.n_total_rows) is not int or self.n_total_rows < 0:
            raise ValueError("n_total_rows must be a non-negative int")
        if type(self.n_paired) is not int or self.n_paired < 0:
            raise ValueError("n_paired must be a non-negative int")
        if self.n_paired > self.n_total_rows:
            raise ValueError("n_paired cannot exceed n_total_rows")
        if not isinstance(self.methods, tuple):
            raise TypeError("methods must be a tuple")
        if len(self.methods) != 2:
            raise ValueError("a numeric pair records Spearman and Pearson")
        spearman, pearson = self.methods
        _require_type(spearman, AssociationResult, "methods")
        _require_type(pearson, AssociationResult, "methods")
        if spearman.method is not AssociationMethod.SPEARMAN:
            raise ValueError("the first method must be Spearman")
        if pearson.method is not AssociationMethod.PEARSON:
            raise ValueError("the second method must be Pearson")
        if (
            spearman.n_observations != self.n_paired
            or pearson.n_observations != self.n_paired
        ):
            raise ValueError("method observations must equal n_paired")

    @property
    def family(self) -> RelationshipFamily:
        """The implemented family this record belongs to."""
        return RelationshipFamily.NUMERIC_NUMERIC

    @property
    def population(self) -> PairPopulation:
        """Rows in which both source values are finite."""
        return PairPopulation.PAIRWISE_FINITE

    @property
    def n_excluded(self) -> int:
        """Rows that are not in the pairwise finite population.

        A row is excluded when either value is missing or not finite.
        """
        return self.n_total_rows - self.n_paired

    @property
    def spearman(self) -> AssociationResult:
        """Spearman result. This is the primary descriptive association."""
        return self.methods[0]

    @property
    def pearson(self) -> AssociationResult:
        """Pearson result. This does not replace Spearman."""
        return self.methods[1]


@dataclass(frozen=True)
class _Classification:
    """Pair counts derived from selected semantic types."""

    supported_pairs: Tuple[Tuple[int, int], ...]
    unimplemented: Tuple[UnimplementedFamilyCount, ...]
    n_ineligible_pairs: int


@dataclass(frozen=True)
class RelationshipAnalysis:
    """Retained relationship facts for one dataset.

    Only supported Numeric × Numeric pairs are stored as records.
    Unimplemented recognized families and ineligible pairs are counts.
    ``n_analyzed_pairs`` is the number of retained records, including
    records whose methods are unavailable. It is not a count of
    significant tests.

    ``primary_method`` is Spearman. ``computation`` is float64. Those
    conventions are properties of this implementation, not a second copy
    of the estimates.
    """

    n_rows: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[NumericNumericRelationship, ...]

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

    @property
    def primary_method(self) -> AssociationMethod:
        """Spearman is the primary descriptive association."""
        return AssociationMethod.SPEARMAN

    @property
    def population(self) -> PairPopulation:
        """Pairwise finite source values."""
        return PairPopulation.PAIRWISE_FINITE

    @property
    def computation(self) -> NumericComputation:
        """Float64 image used for SciPy. Not an exact integer claim."""
        return NumericComputation.FLOAT64

    @property
    def confidence_level(self) -> float:
        """Level used when a Pearson interval is available."""
        return _CONFIDENCE_LEVEL

    @property
    def multiple_testing(self) -> MultipleTestingAdjustment:
        """Adjustment is not applied. Raw p-values stay raw."""
        return MultipleTestingAdjustment.NOT_APPLIED

    @property
    def implemented_family(self) -> RelationshipFamily:
        """The only family this analysis calculates."""
        return RelationshipFamily.NUMERIC_NUMERIC


@dataclass(frozen=True)
class RelationshipsSummary:
    """Product projection of a retained relationship analysis.

    The builder copies counts and relationship records. It does not read
    a DataFrame and does not calculate a correlation.
    """

    n_rows: int
    n_columns: int
    n_total_pairs: int
    n_supported_pairs: int
    n_analyzed_pairs: int
    n_unimplemented_family_pairs: int
    n_ineligible_pairs: int
    unimplemented_family_counts: Tuple[UnimplementedFamilyCount, ...]
    relationships: Tuple[NumericNumericRelationship, ...]

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

    @property
    def primary_method(self) -> AssociationMethod:
        """Spearman is the primary descriptive association."""
        return AssociationMethod.SPEARMAN

    @property
    def population(self) -> PairPopulation:
        """Pairwise finite source values."""
        return PairPopulation.PAIRWISE_FINITE

    @property
    def computation(self) -> NumericComputation:
        """Float64 image used for SciPy. Not an exact integer claim."""
        return NumericComputation.FLOAT64

    @property
    def confidence_level(self) -> float:
        """Level used when a Pearson interval is available."""
        return _CONFIDENCE_LEVEL

    @property
    def multiple_testing(self) -> MultipleTestingAdjustment:
        """Adjustment is not applied. Raw p-values stay raw."""
        return MultipleTestingAdjustment.NOT_APPLIED

    @property
    def implemented_family(self) -> RelationshipFamily:
        """The only family this summary projects."""
        return RelationshipFamily.NUMERIC_NUMERIC


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


def _read_numeric_column(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Return source values and a finite mask for one selected Numeric column.

    The mask is false for missing values and for non-finite floats.
    Integer storage has no infinities. Boolean and complex values are not
    coerced. The returned arrays are copies.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("numeric relationship values must be a pandas Series")
    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype) or pd.api.types.is_complex_dtype(dtype):
        raise TypeError(
            "relationship analysis does not coerce boolean or complex values"
        )
    if pd.api.types.is_float_dtype(dtype):
        return _read_float_column(series)
    if pd.api.types.is_integer_dtype(dtype):
        return _read_integer_column(series)
    raise TypeError(
        "numeric relationship analysis applies only to integer and floating values"
    )


def _read_float_column(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    if isinstance(series.dtype, pd.api.extensions.ExtensionDtype):
        values = series.to_numpy(dtype=np.float64, na_value=np.nan, copy=True)
    else:
        values = series.to_numpy(dtype=np.float64, copy=True)
    values = np.asarray(values, dtype=np.float64)
    return values, np.isfinite(values)


def _read_integer_column(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    finite = np.asarray(series.notna().to_numpy(dtype=bool, copy=True))
    if isinstance(series.dtype, pd.api.extensions.ExtensionDtype):
        numpy_dtype = np.dtype(series.dtype.numpy_dtype)
        values = series.to_numpy(dtype=numpy_dtype, na_value=0, copy=True)
    else:
        values = series.to_numpy(copy=True)
    values = np.asarray(values)
    if values.shape != finite.shape:
        raise ValueError("numeric values must contain one entry per row")
    if values.dtype.kind not in {"i", "u", "O"}:
        raise TypeError("integer relationship values must stay integers")
    return values, finite


def _association_methods(
    left: np.ndarray,
    right: np.ndarray,
) -> Tuple[AssociationResult, AssociationResult]:
    """Return Spearman and Pearson for one paired finite population."""
    if left.ndim != 1 or left.shape != right.shape:
        raise ValueError("paired values must be one-dimensional and aligned")
    n_paired = int(left.size)
    if n_paired < _MIN_ESTIMATE_N:
        reason = UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        return _both_unavailable(n_paired, reason)
    if not _has_variation(left) or not _has_variation(right):
        return _both_unavailable(n_paired, UnavailabilityReason.CONSTANT_PAIRED_VALUES)
    left_float = _to_float64(left)
    right_float = _to_float64(right)
    if (
        left_float is None
        or right_float is None
        or not (_all_finite(left_float) and _all_finite(right_float))
    ):
        return _both_unavailable(n_paired, UnavailabilityReason.NON_FINITE_RESULT)
    if not _has_variation(left_float) or not _has_variation(right_float):
        return _both_unavailable(n_paired, UnavailabilityReason.PRECISION_COLLAPSED)
    if n_paired == _MIN_ESTIMATE_N:
        estimate = _two_point_correlation(left, right)
        return (
            _estimate_only(AssociationMethod.SPEARMAN, n_paired, estimate),
            _estimate_only(AssociationMethod.PEARSON, n_paired, estimate),
        )
    return (
        _spearman_result(left_float, right_float, n_paired),
        _pearson_result(left_float, right_float, n_paired),
    )


def _spearman_result(
    left: np.ndarray,
    right: np.ndarray,
    n_paired: int,
) -> AssociationResult:
    """Spearman rho from ``scipy.stats.spearmanr``.

    The returned statistic is rho. No second test statistic is created.
    Ties use SciPy's rank convention. There is no Spearman interval.
    """
    correlation, p_value = _call_scipy(spearmanr, left, right)
    estimate = _estimate_from_library(correlation)
    return _method_result(
        AssociationMethod.SPEARMAN,
        n_paired,
        estimate,
        _frequentist_from_library(estimate, p_value, n_paired),
        _spearman_interval(estimate),
    )


def _pearson_result(
    left: np.ndarray,
    right: np.ndarray,
    n_paired: int,
) -> AssociationResult:
    """Pearson r from ``scipy.stats.pearsonr`` and a classical Fisher z interval.

    The library call is ``pearsonr(x, y)`` with no newer keyword arguments.
    The returned statistic is r. The interval uses ``atanh``, standard
    error ``1 / sqrt(n - 3)``, and the two-sided 95% normal quantile from
    ``scipy.stats.norm.ppf``. No bias correction is applied.
    """
    correlation, p_value = _call_scipy(pearsonr, left, right)
    estimate = _estimate_from_library(correlation)
    return _method_result(
        AssociationMethod.PEARSON,
        n_paired,
        estimate,
        _frequentist_from_library(estimate, p_value, n_paired),
        _pearson_interval(estimate, n_paired),
    )


def _call_scipy(
    function: object,
    left: np.ndarray,
    right: np.ndarray,
) -> Tuple[object, object]:
    """Call one SciPy correlation and return its coefficient and p-value.

    Runtime warnings from the call are ignored here. A non-finite result
    is handled by the caller. Programmer errors are not caught.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            result = function(left, right)  # type: ignore[operator]
    except (ValueError, FloatingPointError):
        return None, None
    correlation = getattr(result, "correlation", None)
    if correlation is None:
        correlation = getattr(result, "statistic", None)
    p_value = getattr(result, "pvalue", None)
    if correlation is None or p_value is None:
        try:
            correlation = result[0]  # type: ignore[index]
            p_value = result[1]  # type: ignore[index]
        except (TypeError, IndexError, KeyError):
            return None, None
    return correlation, p_value


def _estimate_from_library(correlation: object) -> CorrelationEstimate:
    value = _correlation_value(correlation)
    if value is None:
        return _unavailable_estimate(UnavailabilityReason.NON_FINITE_RESULT)
    return CorrelationEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=value,
        direction=_direction(value),
        reason=None,
    )


def _frequentist_from_library(
    estimate: CorrelationEstimate,
    p_value: object,
    n_paired: int,
) -> FrequentistEvidence:
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        return _unavailable_test(estimate.reason)  # type: ignore[arg-type]
    if n_paired < _MIN_TEST_N:
        return _unavailable_test(UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS)
    value = _p_value(p_value)
    if value is None:
        return _unavailable_test(UnavailabilityReason.NON_FINITE_RESULT)
    return FrequentistEvidence(
        availability=ResultAvailability.AVAILABLE,
        p_value=value,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=None,
    )


def _spearman_interval(estimate: CorrelationEstimate) -> CorrelationInterval:
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        return _unavailable_interval(estimate.reason)  # type: ignore[arg-type]
    return _unavailable_interval(UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD)


def _pearson_interval(
    estimate: CorrelationEstimate,
    n_paired: int,
) -> CorrelationInterval:
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        return _unavailable_interval(estimate.reason)  # type: ignore[arg-type]
    if n_paired < _MIN_PEARSON_INTERVAL_N:
        return _unavailable_interval(
            UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
        )
    if estimate.value == 1.0 or estimate.value == -1.0:
        return _unavailable_interval(UnavailabilityReason.BOUNDARY_CORRELATION)
    bounds = _fisher_z_bounds(estimate.value, n_paired)
    if bounds is None:
        return _unavailable_interval(UnavailabilityReason.NON_FINITE_RESULT)
    lower, upper = bounds
    return CorrelationInterval(
        availability=ResultAvailability.AVAILABLE,
        level=_CONFIDENCE_LEVEL,
        method=CorrelationIntervalMethod.FISHER_Z,
        lower=lower,
        upper=upper,
        reason=None,
    )


def _fisher_z_bounds(estimate: float, n_paired: int) -> Optional[Tuple[float, float]]:
    """Classical Fisher z interval, without a bias correction.

    ``z = atanh(r)`` and the standard error is ``1 / sqrt(n - 3)``.
    The critical value is the two-sided 95% standard-normal quantile.
    """
    try:
        transformed = math.atanh(estimate)
    except ValueError:
        return None
    if not math.isfinite(transformed):
        return None
    scale = math.sqrt(n_paired - 3)
    if scale == 0.0:
        return None
    critical = float(norm.ppf(1.0 - (1.0 - _CONFIDENCE_LEVEL) / 2.0))
    if not math.isfinite(critical):
        return None
    half_width = critical / scale
    lower = math.tanh(transformed - half_width)
    upper = math.tanh(transformed + half_width)
    lower = _bound_endpoint(lower)
    upper = _bound_endpoint(upper)
    if lower is None or upper is None or lower > upper:
        return None
    return lower, upper


def _bound_endpoint(value: float) -> Optional[float]:
    if not math.isfinite(value):
        return None
    if value == 0.0:
        return 0.0
    if value < -1.0 or value > 1.0:
        if abs(value) - 1.0 <= _CORRELATION_CLAMP:
            return -1.0 if value < 0.0 else 1.0
        return None
    return value


def _estimate_only(
    method: AssociationMethod,
    n_paired: int,
    estimate: float,
) -> AssociationResult:
    """Store an exact ±1 estimate without a test or a Pearson interval.

    Two varying points determine the sign. ``n - 2`` is zero, so the
    p-value is not taken from SciPy. The Pearson interval also needs
    ``n - 3 > 0``.
    """
    estimate_result = CorrelationEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=estimate,
        direction=_direction(estimate),
        reason=None,
    )
    return _method_result(
        method,
        n_paired,
        estimate_result,
        _unavailable_test(UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS),
        (
            _spearman_interval(estimate_result)
            if method is AssociationMethod.SPEARMAN
            else _unavailable_interval(
                UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
            )
        ),
    )


def _both_unavailable(
    n_paired: int,
    reason: UnavailabilityReason,
) -> Tuple[AssociationResult, AssociationResult]:
    return (
        _unavailable_method(AssociationMethod.SPEARMAN, n_paired, reason),
        _unavailable_method(AssociationMethod.PEARSON, n_paired, reason),
    )


def _unavailable_method(
    method: AssociationMethod,
    n_paired: int,
    reason: UnavailabilityReason,
) -> AssociationResult:
    return _method_result(
        method,
        n_paired,
        _unavailable_estimate(reason),
        _unavailable_test(reason),
        _unavailable_interval(reason),
    )


def _method_result(
    method: AssociationMethod,
    n_paired: int,
    estimate: CorrelationEstimate,
    frequentist: FrequentistEvidence,
    interval: CorrelationInterval,
) -> AssociationResult:
    return AssociationResult(
        method=method,
        n_observations=n_paired,
        estimate=estimate,
        frequentist=frequentist,
        confidence_interval=interval,
    )


def _unavailable_estimate(reason: UnavailabilityReason) -> CorrelationEstimate:
    return CorrelationEstimate(
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        direction=None,
        reason=reason,
    )


def _unavailable_test(reason: UnavailabilityReason) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=ResultAvailability.UNAVAILABLE,
        p_value=None,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=reason,
    )


def _unavailable_interval(reason: UnavailabilityReason) -> CorrelationInterval:
    return CorrelationInterval(
        availability=ResultAvailability.UNAVAILABLE,
        level=None,
        method=None,
        lower=None,
        upper=None,
        reason=reason,
    )


def _two_point_correlation(left: np.ndarray, right: np.ndarray) -> float:
    """Return ±1 from whether the two source values move together.

    Comparison uses the original values, so an integer above ``2**53``
    keeps its order. SciPy is not called.
    """
    left_increases = bool(left[1] > left[0])
    right_increases = bool(right[1] > right[0])
    if left_increases == right_increases:
        return 1.0
    return -1.0


def _to_float64(values: np.ndarray) -> Optional[np.ndarray]:
    """Return a float64 copy, or ``None`` when conversion cannot be finite."""
    try:
        if values.dtype.kind == "f":
            converted = np.asarray(values, dtype=np.float64)
        elif values.dtype.kind in {"i", "u"}:
            converted = values.astype(np.float64, copy=False)
        else:
            converted = np.array(
                [float(value) for value in values.tolist()],
                dtype=np.float64,
            )
    except (TypeError, ValueError, OverflowError):
        return None
    return np.asarray(converted, dtype=np.float64)


def _has_variation(values: np.ndarray) -> bool:
    if values.size < 2:
        return False
    return bool(np.any(values != values[0]))


def _all_finite(values: np.ndarray) -> bool:
    return bool(np.isfinite(values).all())


def _correlation_value(value: object) -> Optional[float]:
    number = _plain_unit_float(value)
    if number is None:
        return None
    if number < -1.0 or number > 1.0:
        if abs(number) - 1.0 <= _CORRELATION_CLAMP:
            return -1.0 if number < 0.0 else 1.0
        return None
    if number == 0.0:
        return 0.0
    return number


def _p_value(value: object) -> Optional[float]:
    number = _plain_unit_float(value)
    if number is None or number < 0.0 or number > 1.0:
        return None
    if number == 0.0:
        return 0.0
    return number


def _plain_unit_float(value: object) -> Optional[float]:
    if isinstance(value, (bool, np.bool_)):
        return None
    if isinstance(value, np.ndarray):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _direction(value: float) -> EffectDirection:
    if value < 0.0:
        return EffectDirection.NEGATIVE
    if value > 0.0:
        return EffectDirection.POSITIVE
    return EffectDirection.ZERO


def _require_component_consistency(result: AssociationResult) -> None:
    estimate = result.estimate
    interval = result.confidence_interval
    if estimate.availability is ResultAvailability.UNAVAILABLE:
        if result.frequentist.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("a test requires an estimate")
        if result.frequentist.reason is not estimate.reason:
            raise ValueError("an unavailable estimate and its test share a reason")
        if interval.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("an interval requires an estimate")
        if interval.reason is not estimate.reason:
            raise ValueError("an unavailable estimate and its interval share a reason")
        return
    if result.method is AssociationMethod.SPEARMAN:
        if interval.availability is not ResultAvailability.UNAVAILABLE:
            raise ValueError("Spearman has no confidence interval in this slice")
        if interval.reason is not UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD:
            raise ValueError("Spearman interval is not defined for this method")


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


def _require_relationships(
    relationships: Tuple[NumericNumericRelationship, ...],
    n_rows: int,
    n_analyzed: int,
) -> None:
    if not isinstance(relationships, tuple):
        raise TypeError("relationships must be a tuple")
    if len(relationships) != n_analyzed:
        raise ValueError("n_analyzed_pairs must equal the relationship records")
    previous = (-1, -1)
    for relationship in relationships:
        if not isinstance(relationship, NumericNumericRelationship):
            raise TypeError(
                "relationships must contain NumericNumericRelationship values"
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


def _require_correlation(value: Optional[float], field: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite float")
    if value < -1.0 or value > 1.0:
        raise ValueError(f"{field} must lie on [-1, 1]")


def _require_p_value(value: Optional[float]) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("p_value must be a finite float")
    if value < 0.0 or value > 1.0:
        raise ValueError("p_value must lie on [0, 1]")


def _require_enum(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _require_type(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")


def _require_position(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_nonnegative(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")
