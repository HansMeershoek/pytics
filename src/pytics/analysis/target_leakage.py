"""Evidence of possible target duplication for one explicit target.

Leakage is contextual. A DataFrame does not say whether a column was
available at prediction time, whether it was built from the outcome, or
whether a business process leaked future information. This module
records facts that can be checked from the observed values. It does not
decide that a column is leakage, and it does not assign a score,
probability, or severity.

Two facts are recorded.

Exact duplication: a predictor of the target's semantic type equals the
target on every applicable target row, under the comparison below.
Applicable rows are the finite rows of a Numeric target and the
non-missing rows of a Boolean or Categorical target. A missing or
non-finite predictor value on any of those rows blocks equality. Rows
where the target itself is missing are not compared, so matching
missingness is not required. Numeric equality is the finite float64
image, the same image the diagnostic model uses. Boolean equality is
the observed False/True code. Categorical equality is Python equality of
the category values, not equality of codes or vocabularies, so ``1``,
``True``, and ``1.0`` compare equal when both columns are Categorical.
Different semantic types are not compared. ``1`` and ``True`` are not
duplicates when one column is Numeric and the other is Boolean.

Deterministic mapping: for a Boolean or Categorical target, whether
observed predictor values functionally determine the observed target
classes on the jointly observed rows. Missing predictor values are
excluded from the groups. Missing target values are not a class.
Numeric targets do not receive this fact. A dependency that holds only
because every predictor value occurs once is trivial uniqueness, not
repeated target encoding. A dependency that holds only because the
joint target has one class is a constant image. The only mapping status
that asks for inspection is a conflict-free dependency with at least one
repeated predictor value and at least two target classes. That status
is still evidence, not a claim that the column leaks.

Nothing here treats a correlation, an effect size, a p-value, or a
model coefficient as leakage. No percentage cutoff is used. Datetime
columns are not read as temporal leakage. No rule engine is implemented.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column_label import labels_are_float_nan
from pytics.analysis.relationships.boolean_boolean import _read_boolean_column
from pytics.analysis.relationships.numeric_categorical import _read_categorical_column
from pytics.analysis.relationships.numeric_numeric import _read_numeric_column
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus

if TYPE_CHECKING:
    from pytics.analysis.target import TargetAnalysis


class LeakageApplicability(Enum):
    """Whether leakage evidence is defined for the selected target.

    ``APPLICABLE`` is a supported Numeric, Boolean, or Categorical
    target. The other members follow target analysis and do not read
    predictor values.
    """

    APPLICABLE = "applicable"
    TARGET_UNSUPPORTED = "target_unsupported"
    TARGET_INELIGIBLE = "target_ineligible"
    TARGET_UNRESOLVED = "target_unresolved"


class ExactDuplicateStatus(Enum):
    """Whether one predictor is an exact copy of the target.

    ``EXACT_DUPLICATE`` means the comparison contract holds on every
    applicable target row. It is mechanical sameness, not a leakage
    verdict. ``MISSINGNESS_BLOCKS_EQUALITY`` means the jointly observed
    values match and at least one applicable row has no comparable
    predictor value. ``INCOMPATIBLE_REPRESENTATION`` means the semantic
    types are not compared. ``INSUFFICIENT_POPULATION`` means there is
    no jointly observed row.
    """

    EXACT_DUPLICATE = "exact_duplicate"
    NOT_EQUAL = "not_equal"
    MISSINGNESS_BLOCKS_EQUALITY = "missingness_blocks_equality"
    INCOMPATIBLE_REPRESENTATION = "incompatible_representation"
    INSUFFICIENT_POPULATION = "insufficient_population"


class MappingStatus(Enum):
    """How observed predictor values relate to classification classes.

    ``DETERMINISTIC_REPEATED`` means the jointly observed predictor
    values functionally determine the target, at least one value
    repeats, no group conflicts, and the joint target has at least two
    classes. It is evidence an analyst can inspect. It is not a
    determination that the column leaks the target. ``TRIVIAL_UNIQUENESS``
    means that dependency holds only because every predictor value
    occurs once. ``TARGET_CONSTANT_ON_JOINT`` means the joint target has
    one class, so every predictor determines it. ``NOT_APPLICABLE`` means
    this fact is not defined for the target or the predictor.
    """

    NOT_APPLICABLE = "not_applicable"
    INSUFFICIENT_POPULATION = "insufficient_population"
    CONFLICTING = "conflicting"
    TARGET_CONSTANT_ON_JOINT = "target_constant_on_joint"
    TRIVIAL_UNIQUENESS = "trivial_uniqueness"
    DETERMINISTIC_REPEATED = "deterministic_repeated"


_EXACT_TYPES = frozenset(
    {
        SemanticType.NUMERIC,
        SemanticType.BOOLEAN,
        SemanticType.CATEGORICAL,
    }
)
_CLASSIFICATION_TYPES = frozenset({SemanticType.BOOLEAN, SemanticType.CATEGORICAL})
_MAPPING_TYPES = frozenset(
    {
        SemanticType.BOOLEAN,
        SemanticType.CATEGORICAL,
        SemanticType.NUMERIC,
        SemanticType.IDENTIFIER,
    }
)


@dataclass(frozen=True)
class LeakagePopulation:
    """Rows on which leakage evidence may be compared.

    ``n_target_missing + n_target_observed`` equals ``n_total_rows``.
    ``n_target_non_finite`` counts non-missing Numeric values that are
    not finite, and is zero otherwise. ``n_applicable`` is the rows
    actually compared: finite Numeric rows, or non-missing Boolean or
    Categorical rows. It is zero when the target is not applicable.
    """

    n_total_rows: int
    n_target_missing: int
    n_target_observed: int
    n_target_non_finite: int
    n_applicable: int

    def __post_init__(self) -> None:
        _require_count(self.n_total_rows, "n_total_rows")
        _require_count(self.n_target_missing, "n_target_missing")
        _require_count(self.n_target_observed, "n_target_observed")
        _require_count(self.n_target_non_finite, "n_target_non_finite")
        _require_count(self.n_applicable, "n_applicable")
        if self.n_target_missing + self.n_target_observed != self.n_total_rows:
            raise ValueError("leakage population counts must reconcile")
        if self.n_target_non_finite > self.n_target_observed:
            raise ValueError("non-finite target rows are observed target rows")
        if self.n_applicable > self.n_target_observed - self.n_target_non_finite:
            raise ValueError("applicable rows are finite observed target rows")


@dataclass(frozen=True)
class ExactDuplicateEvidence:
    """Comparison of one predictor with the target. Counts, not values."""

    status: ExactDuplicateStatus
    n_applicable_rows: int
    n_joint_rows: int
    n_predictor_unobserved: int
    n_equal_rows: int
    n_unequal_rows: int

    def __post_init__(self) -> None:
        _require_type(self.status, ExactDuplicateStatus, "status")
        _require_count(self.n_applicable_rows, "n_applicable_rows")
        _require_count(self.n_joint_rows, "n_joint_rows")
        _require_count(self.n_predictor_unobserved, "n_predictor_unobserved")
        _require_count(self.n_equal_rows, "n_equal_rows")
        _require_count(self.n_unequal_rows, "n_unequal_rows")
        if self.status is ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION:
            if _exact_measured(self):
                raise ValueError("an incompatible representation is not compared")
            return
        _require_exact_reconciliation(self)
        if self.status is ExactDuplicateStatus.EXACT_DUPLICATE:
            if (
                self.n_unequal_rows
                or self.n_predictor_unobserved
                or self.n_joint_rows < 1
            ):
                raise ValueError("an exact duplicate matches every applicable row")
        elif self.status is ExactDuplicateStatus.MISSINGNESS_BLOCKS_EQUALITY:
            if self.n_unequal_rows or self.n_predictor_unobserved < 1:
                raise ValueError("missingness blocks equality only after a match")
            if self.n_joint_rows < 1:
                raise ValueError("missingness blocks equality only after a match")
        elif self.status is ExactDuplicateStatus.NOT_EQUAL:
            if self.n_unequal_rows < 1:
                raise ValueError("an unequal predictor has a disagreeing row")
        elif self.n_joint_rows != 0:
            raise ValueError("an insufficient population has no joint row")


@dataclass(frozen=True)
class MappingEvidence:
    """Functional dependency of target classes on predictor values.

    Groups are observed predictor values on rows where the target class
    is also observed. A repeated group occurs at least twice. A
    conflicting group contains more than one target class. No predictor
    value and no target class is stored.
    """

    status: MappingStatus
    n_applicable_rows: int
    n_joint_rows: int
    n_predictor_unobserved: int
    n_distinct_groups: int
    n_repeated_groups: int
    n_singleton_groups: int
    n_conflicting_groups: int
    n_consistent_repeated_groups: int
    n_rows_in_repeated_groups: int
    n_rows_in_conflicting_groups: int
    n_target_classes: int

    def __post_init__(self) -> None:
        _require_type(self.status, MappingStatus, "status")
        for name in (
            "n_applicable_rows",
            "n_joint_rows",
            "n_predictor_unobserved",
            "n_distinct_groups",
            "n_repeated_groups",
            "n_singleton_groups",
            "n_conflicting_groups",
            "n_consistent_repeated_groups",
            "n_rows_in_repeated_groups",
            "n_rows_in_conflicting_groups",
            "n_target_classes",
        ):
            _require_count(getattr(self, name), name)
        if self.status is MappingStatus.NOT_APPLICABLE:
            if _mapping_measured(self):
                raise ValueError("an inapplicable mapping is not counted")
            return
        _require_mapping_reconciliation(self)
        if self.status is MappingStatus.INSUFFICIENT_POPULATION:
            if self.n_joint_rows != 0:
                raise ValueError("an insufficient mapping has no joint row")
        elif self.status is MappingStatus.CONFLICTING:
            if self.n_conflicting_groups < 1:
                raise ValueError("a conflicting mapping has a conflicting group")
        elif self.status is MappingStatus.TARGET_CONSTANT_ON_JOINT:
            if self.n_target_classes != 1 or self.n_conflicting_groups:
                raise ValueError("a constant joint target has one class")
        elif self.status is MappingStatus.TRIVIAL_UNIQUENESS:
            if self.n_repeated_groups or self.n_conflicting_groups:
                raise ValueError("trivial uniqueness has no repeated group")
            if self.n_target_classes < 2:
                raise ValueError("trivial uniqueness has more than one class")
        elif self.n_repeated_groups < 1 or self.n_conflicting_groups:
            raise ValueError("a repeated mapping has no conflicting group")
        elif self.n_target_classes < 2:
            raise ValueError("a repeated mapping has more than one class")


@dataclass(frozen=True)
class PredictorLeakage:
    """Leakage evidence for one column other than the target."""

    position: int
    label: object
    selected_type: Optional[SemanticType]
    resolution_status: ResolutionStatus
    exact_duplicate: ExactDuplicateEvidence
    deterministic_mapping: MappingEvidence

    def __post_init__(self) -> None:
        _require_count(self.position, "position")
        if self.selected_type is not None:
            _require_type(self.selected_type, SemanticType, "selected_type")
        _require_type(self.resolution_status, ResolutionStatus, "resolution_status")
        _require_type(self.exact_duplicate, ExactDuplicateEvidence, "exact_duplicate")
        _require_type(
            self.deterministic_mapping,
            MappingEvidence,
            "deterministic_mapping",
        )
        if (self.resolution_status is ResolutionStatus.RESOLVED) != (
            self.selected_type is not None
        ):
            raise ValueError(
                "a selected type exists exactly when resolution selected one"
            )


@dataclass(frozen=True)
class TargetLeakageAnalysis:
    """Retained leakage evidence for one explicit target.

    ``predictors`` follows physical column order and omits the target.
    It is empty when the target is not applicable, including when the
    frame has no other column. No source values are stored.
    """

    target_position: int
    target_label: object
    target_selected_type: Optional[SemanticType]
    target_resolution_status: ResolutionStatus
    applicability: LeakageApplicability
    population: LeakagePopulation
    predictors: Tuple[PredictorLeakage, ...] = ()

    def __post_init__(self) -> None:
        _require_count(self.target_position, "target_position")
        if self.target_selected_type is not None:
            _require_type(
                self.target_selected_type, SemanticType, "target_selected_type"
            )
        _require_type(
            self.target_resolution_status,
            ResolutionStatus,
            "target_resolution_status",
        )
        _require_type(self.applicability, LeakageApplicability, "applicability")
        _require_type(self.population, LeakagePopulation, "population")
        if (self.target_resolution_status is ResolutionStatus.RESOLVED) != (
            self.target_selected_type is not None
        ):
            raise ValueError(
                "a selected type exists exactly when resolution selected one"
            )
        if not isinstance(self.predictors, tuple):
            raise TypeError("predictors must be a tuple")
        if self.applicability is not LeakageApplicability.APPLICABLE:
            if self.predictors:
                raise ValueError("only an applicable target lists predictors")
            if self.population.n_applicable or self.population.n_target_non_finite:
                raise ValueError("an inapplicable target has no comparison rows")
        elif self.population.n_applicable != (
            self.population.n_target_observed - self.population.n_target_non_finite
        ):
            raise ValueError("applicable rows are the finite observed target rows")
        previous = -1
        for item in self.predictors:
            _require_type(item, PredictorLeakage, "predictors")
            if item.position == self.target_position or item.position <= previous:
                raise ValueError(
                    "predictors follow ascending positions other than the target"
                )
            previous = item.position

    @property
    def n_exact_duplicates(self) -> int:
        """Predictors whose exact-duplicate status is ``EXACT_DUPLICATE``.

        This is a count of retained evidence. It is not a leakage score.
        """
        return sum(
            item.exact_duplicate.status is ExactDuplicateStatus.EXACT_DUPLICATE
            for item in self.predictors
        )

    @property
    def n_repeated_deterministic_mappings(self) -> int:
        """Predictors whose mapping status is ``DETERMINISTIC_REPEATED``.

        This is a count of retained evidence. It is not a leakage score.
        """
        return sum(
            item.deterministic_mapping.status is MappingStatus.DETERMINISTIC_REPEATED
            for item in self.predictors
        )


@dataclass(frozen=True)
class _DependencyCounts:
    n_distinct_groups: int
    n_repeated_groups: int
    n_singleton_groups: int
    n_conflicting_groups: int
    n_consistent_repeated_groups: int
    n_rows_in_repeated_groups: int
    n_rows_in_conflicting_groups: int
    n_target_classes: int


def analyze_target_leakage(
    frame: pd.DataFrame,
    columns: Tuple[ColumnAnalysis, ...],
    target: TargetAnalysis,
) -> TargetLeakageAnalysis:
    """Collect leakage evidence for an analyzed target.

    ``columns`` and ``target`` are the analysis of ``frame``. The frame
    is read, not modified, and not retained. An unsupported, ineligible,
    or unresolved target returns that applicability and does not read
    predictor values. Relationship records are not read.
    """
    from pytics.analysis.target import TargetAnalysis

    _require_frame(frame, columns, target, TargetAnalysis)
    column = columns[target.position]
    applicability = _applicability_for(target.status)
    population = _population_for(target, applicability)
    if applicability is not LeakageApplicability.APPLICABLE:
        return _analysis(column, applicability, population, ())
    applicable, target_float, target_codes, target_categories = _read_target(
        frame.iloc[:, target.position],
        target.selected_type,
    )
    if int(np.count_nonzero(applicable)) != population.n_applicable:
        raise ValueError("frame target values do not match the target analysis")
    predictors = tuple(
        _diagnose_predictor(
            frame.iloc[:, item.position],
            item,
            target_type=target.selected_type,
            applicable=applicable,
            n_applicable=population.n_applicable,
            target_float=target_float,
            target_codes=target_codes,
            target_categories=target_categories,
        )
        for item in columns
        if item.position != target.position
    )
    return _analysis(column, applicability, population, predictors)


def exact_duplicate_positions(analysis: TargetLeakageAnalysis) -> FrozenSet[int]:
    """Return positions whose retained status is an exact duplicate.

    The diagnostic model excludes these columns. It does not compare the
    values again.
    """
    _require_type(analysis, TargetLeakageAnalysis, "analysis")
    return frozenset(
        item.position
        for item in analysis.predictors
        if item.exact_duplicate.status is ExactDuplicateStatus.EXACT_DUPLICATE
    )


def copy_target_leakage(analysis: TargetLeakageAnalysis) -> TargetLeakageAnalysis:
    """Return new frozen records with the same values.

    Every nested record is rebuilt and revalidated. Nothing is recomputed
    and no source value is read.
    """
    _require_type(analysis, TargetLeakageAnalysis, "analysis")
    copied = _copy_record(analysis)
    if not isinstance(copied, TargetLeakageAnalysis):
        raise TypeError("analysis must be a TargetLeakageAnalysis")
    return copied


def _require_leakage_attachment(
    leakage: Optional[TargetLeakageAnalysis],
    target: object,
    columns: Tuple[ColumnAnalysis, ...],
) -> None:
    """Check retained leakage evidence against the target and columns.

    This does not reread the frame. Predictor identity and semantic state
    must be the column's. Measured populations must be the target's.
    """
    from pytics.analysis.target import TargetAnalysis

    if target is None:
        if leakage is not None:
            raise ValueError("target leakage analysis requires target analysis")
        return
    _require_type(target, TargetAnalysis, "target_analysis")
    if leakage is None:
        raise ValueError("target analysis requires its leakage result")
    _require_type(leakage, TargetLeakageAnalysis, "target_leakage")
    if leakage.target_position != target.position:
        raise ValueError("the leakage result must name the analyzed target")
    if not _same_value(leakage.target_label, target.label):
        raise ValueError("the leakage result must name the analyzed target")
    if leakage.target_selected_type is not target.selected_type:
        raise ValueError("leakage keeps the target's selected type")
    if leakage.target_resolution_status is not target.resolution_status:
        raise ValueError("leakage keeps the target's resolution status")
    expected = _applicability_for(target.status)
    if leakage.applicability is not expected:
        raise ValueError("leakage applicability must follow the target status")
    _require_population_attachment(leakage, target)
    if leakage.applicability is not LeakageApplicability.APPLICABLE:
        return
    others = tuple(column for column in columns if column.position != target.position)
    if len(leakage.predictors) != len(others):
        raise ValueError("leakage predictors must list every other column")
    for item, column in zip(leakage.predictors, others):
        if item.position != column.position or not _same_value(
            item.label, column.label
        ):
            raise ValueError("a leakage predictor must be its column")
        if item.selected_type is not column.inferred.selected_type:
            raise ValueError("a leakage predictor keeps its selected type")
        if item.resolution_status is not column.inferred.resolution.status:
            raise ValueError("a leakage predictor keeps its resolution status")
        _require_predictor_population(item, leakage.population.n_applicable)


def _require_exact_duplicate_consumption(
    leakage: Optional[TargetLeakageAnalysis],
    diagnostic: object,
) -> None:
    """Require the diagnostic exclusion to follow exact-duplicate evidence.

    The check runs only after predictor screening. An exact duplicate is
    excluded, and no other column receives that exclusion.
    """
    from pytics.analysis.target_diagnostic import PredictorDecision
    from pytics.analysis.target_diagnostic import TargetDiagnosticAnalysis

    if leakage is None or diagnostic is None:
        return
    if not isinstance(diagnostic, TargetDiagnosticAnalysis):
        return
    if not diagnostic.predictors:
        return
    if len(leakage.predictors) != len(diagnostic.predictors):
        raise ValueError("leakage and diagnostic predictors must be the same columns")
    for evidence, screened in zip(leakage.predictors, diagnostic.predictors):
        if evidence.position != screened.position:
            raise ValueError(
                "leakage and diagnostic predictors must be the same columns"
            )
        duplicate = (
            evidence.exact_duplicate.status is ExactDuplicateStatus.EXACT_DUPLICATE
        )
        excluded = screened.decision is PredictorDecision.IDENTICAL_TO_TARGET
        if duplicate != excluded:
            raise ValueError(
                "an exact target duplicate is excluded from the diagnostic model"
            )


def _applicability_for(status: object) -> LeakageApplicability:
    from pytics.analysis.target import TargetStatus

    if status is TargetStatus.SUPPORTED:
        return LeakageApplicability.APPLICABLE
    if status is TargetStatus.UNSUPPORTED:
        return LeakageApplicability.TARGET_UNSUPPORTED
    if status is TargetStatus.INELIGIBLE:
        return LeakageApplicability.TARGET_INELIGIBLE
    if status is TargetStatus.UNRESOLVED:
        return LeakageApplicability.TARGET_UNRESOLVED
    raise ValueError("target status has no leakage applicability")


def _population_for(
    target: TargetAnalysis,
    applicability: LeakageApplicability,
) -> LeakagePopulation:
    observed = target.population.n_target_non_missing
    if applicability is not LeakageApplicability.APPLICABLE:
        return LeakagePopulation(
            n_total_rows=target.population.n_total_rows,
            n_target_missing=target.population.n_target_missing,
            n_target_observed=observed,
            n_target_non_finite=0,
            n_applicable=0,
        )
    if target.numeric_facts is not None:
        applicable = target.numeric_facts.finite_count
        non_finite = observed - applicable
    else:
        applicable = observed
        non_finite = 0
    return LeakagePopulation(
        n_total_rows=target.population.n_total_rows,
        n_target_missing=target.population.n_target_missing,
        n_target_observed=observed,
        n_target_non_finite=non_finite,
        n_applicable=applicable,
    )


def _analysis(
    column: ColumnAnalysis,
    applicability: LeakageApplicability,
    population: LeakagePopulation,
    predictors: Tuple[PredictorLeakage, ...],
) -> TargetLeakageAnalysis:
    return TargetLeakageAnalysis(
        target_position=column.position,
        target_label=column.label,
        target_selected_type=column.inferred.selected_type,
        target_resolution_status=column.inferred.resolution.status,
        applicability=applicability,
        population=population,
        predictors=predictors,
    )


def _read_target(
    series: pd.Series,
    selected: Optional[SemanticType],
) -> Tuple[
    np.ndarray, Optional[np.ndarray], Optional[np.ndarray], Optional[Tuple[object, ...]]
]:
    """Return the applicable mask and the target's comparison image.

    The float image is set for Numeric. Codes and categories are set for
    Boolean and Categorical. Boolean codes are 0 and 1. Categorical codes
    are the physical category codes. Missing and non-finite rows are not
    applicable.
    """
    if selected is SemanticType.NUMERIC:
        image = _numeric_float_image(series)
        return np.isfinite(image), image, None, None
    if selected is SemanticType.BOOLEAN:
        codes = _boolean_codes(series)
        return codes >= 0, None, codes, None
    codes, categories = _read_categorical_column(series)
    codes = np.asarray(codes, dtype=np.int64)
    return codes >= 0, None, codes, categories


def _diagnose_predictor(
    series: pd.Series,
    column: ColumnAnalysis,
    *,
    target_type: Optional[SemanticType],
    applicable: np.ndarray,
    n_applicable: int,
    target_float: Optional[np.ndarray],
    target_codes: Optional[np.ndarray],
    target_categories: Optional[Tuple[object, ...]],
) -> PredictorLeakage:
    selected = column.inferred.selected_type
    need_exact = selected in _EXACT_TYPES and selected is target_type
    need_mapping = target_type in _CLASSIFICATION_TYPES and selected in _MAPPING_TYPES
    if n_applicable == 0 or (not need_exact and not need_mapping):
        return _predictor(
            column,
            _exact_without_values(need_exact, n_applicable),
            _mapping_without_values(need_mapping, n_applicable),
        )
    if selected is SemanticType.NUMERIC:
        image = _numeric_float_image(series)
        observed = np.isfinite(image)
        exact = (
            _exact_from_float(image, target_float, applicable, n_applicable)
            if need_exact
            else _incompatible_exact()
        )
        mapping = (
            _mapping_from_float(image, observed, target_codes, applicable, n_applicable)
            if need_mapping
            else _mapping_not_applicable()
        )
        return _predictor(column, exact, mapping)
    if selected is SemanticType.BOOLEAN:
        codes = _boolean_codes(series)
        categories: Optional[Tuple[object, ...]] = None
    elif selected is SemanticType.CATEGORICAL:
        codes, categories = _read_categorical_column(series)
        codes = np.asarray(codes, dtype=np.int64)
    else:
        codes = _identifier_codes(series)
        categories = None
    observed = codes >= 0
    if need_exact and selected is SemanticType.BOOLEAN:
        exact = _exact_from_codes(codes, target_codes, applicable, n_applicable)
    elif need_exact:
        exact = _exact_from_categories(
            codes,
            categories,
            target_codes,
            target_categories,
            applicable,
            n_applicable,
        )
    else:
        exact = _incompatible_exact()
    mapping = (
        _mapping_from_codes(codes, observed, target_codes, applicable, n_applicable)
        if need_mapping
        else _mapping_not_applicable()
    )
    return _predictor(column, exact, mapping)


def _numeric_float_image(series: pd.Series) -> np.ndarray:
    """Return the finite float64 image used for numeric equality.

    Missing values and non-finite values stay NaN. Integer values are
    cast, matching the diagnostic model's numeric image. A cast that is
    not finite is not a comparable value.
    """
    values, present = _read_numeric_column(series)
    image = np.full(values.shape[0], np.nan, dtype=np.float64)
    if np.any(present):
        image[present] = np.asarray(values[present], dtype=np.float64)
    return image


def _boolean_codes(series: pd.Series) -> np.ndarray:
    observed, is_true = _read_boolean_column(series)
    return np.where(observed, is_true.astype(np.int64), np.int64(-1))


def _identifier_codes(series: pd.Series) -> np.ndarray:
    """Return factorize codes. Missing stays the sentinel and is not a group.

    The uniques are discarded. They are not part of the retained result.
    """
    codes, uniques = pd.factorize(series, sort=False)
    del uniques
    return np.asarray(codes, dtype=np.int64)


def _exact_from_float(
    predictor: np.ndarray,
    target: Optional[np.ndarray],
    applicable: np.ndarray,
    n_applicable: int,
) -> ExactDuplicateEvidence:
    if target is None:
        raise ValueError("numeric equality requires a numeric target image")
    joint = applicable & np.isfinite(predictor)
    return _exact_counts(
        n_applicable,
        joint,
        predictor[joint] == target[joint],
    )


def _exact_from_codes(
    predictor: np.ndarray,
    target: Optional[np.ndarray],
    applicable: np.ndarray,
    n_applicable: int,
) -> ExactDuplicateEvidence:
    if target is None:
        raise ValueError("boolean equality requires boolean target codes")
    joint = applicable & (predictor >= 0)
    return _exact_counts(
        n_applicable,
        joint,
        predictor[joint] == target[joint],
    )


def _exact_from_categories(
    predictor_codes: np.ndarray,
    predictor_categories: Optional[Tuple[object, ...]],
    target_codes: Optional[np.ndarray],
    target_categories: Optional[Tuple[object, ...]],
    applicable: np.ndarray,
    n_applicable: int,
) -> ExactDuplicateEvidence:
    if (
        predictor_categories is None
        or target_codes is None
        or target_categories is None
    ):
        raise ValueError("categorical equality requires both vocabularies")
    joint = applicable & (predictor_codes >= 0)
    if not np.any(joint):
        return _exact_counts(n_applicable, joint, np.zeros(0, dtype=np.bool_))
    left = predictor_codes[joint]
    right = target_codes[joint]
    if predictor_categories == target_categories:
        equal = left == right
    else:
        equal = _category_values(predictor_categories, left) == _category_values(
            target_categories, right
        )
        equal = np.asarray(equal, dtype=np.bool_)
    return _exact_counts(n_applicable, joint, equal)


def _category_values(categories: Tuple[object, ...], codes: np.ndarray) -> np.ndarray:
    values = np.empty(len(categories), dtype=object)
    values[:] = list(categories)
    if codes.size and (int(np.min(codes)) < 0 or int(np.max(codes)) >= len(values)):
        raise ValueError("category codes must index the vocabulary")
    return values[codes]


def _exact_counts(
    n_applicable: int,
    joint: np.ndarray,
    equal: np.ndarray,
) -> ExactDuplicateEvidence:
    n_joint = int(np.count_nonzero(joint))
    n_unobserved = n_applicable - n_joint
    n_equal = int(np.count_nonzero(equal)) if n_joint else 0
    n_unequal = n_joint - n_equal
    return ExactDuplicateEvidence(
        status=_exact_status(n_joint, n_unobserved, n_unequal),
        n_applicable_rows=n_applicable,
        n_joint_rows=n_joint,
        n_predictor_unobserved=n_unobserved,
        n_equal_rows=n_equal,
        n_unequal_rows=n_unequal,
    )


def _exact_status(
    n_joint: int,
    n_unobserved: int,
    n_unequal: int,
) -> ExactDuplicateStatus:
    if n_joint == 0:
        return ExactDuplicateStatus.INSUFFICIENT_POPULATION
    if n_unequal:
        return ExactDuplicateStatus.NOT_EQUAL
    if n_unobserved:
        return ExactDuplicateStatus.MISSINGNESS_BLOCKS_EQUALITY
    return ExactDuplicateStatus.EXACT_DUPLICATE


def _mapping_from_float(
    image: np.ndarray,
    observed: np.ndarray,
    class_codes: Optional[np.ndarray],
    applicable: np.ndarray,
    n_applicable: int,
) -> MappingEvidence:
    joint = applicable & observed
    if not np.any(joint):
        groups = np.empty(0, dtype=np.int64)
    else:
        inverse = np.unique(image[joint], return_inverse=True)[1]
        groups = np.asarray(inverse, dtype=np.int64)
    return _mapping_evidence(groups, class_codes, joint, n_applicable)


def _mapping_from_codes(
    codes: np.ndarray,
    observed: np.ndarray,
    class_codes: Optional[np.ndarray],
    applicable: np.ndarray,
    n_applicable: int,
) -> MappingEvidence:
    joint = applicable & observed
    groups = codes[joint] if np.any(joint) else np.empty(0, dtype=np.int64)
    return _mapping_evidence(groups, class_codes, joint, n_applicable)


def _mapping_evidence(
    groups: np.ndarray,
    class_codes: Optional[np.ndarray],
    joint: np.ndarray,
    n_applicable: int,
) -> MappingEvidence:
    if class_codes is None:
        raise ValueError("a classification mapping requires target classes")
    classes = class_codes[joint] if groups.size else np.empty(0, dtype=np.int64)
    if classes.size and int(np.min(classes)) < 0:
        raise ValueError("a missing target value is not a leakage class")
    counts = _functional_dependency(groups, classes)
    n_joint = int(groups.size)
    return MappingEvidence(
        status=_mapping_status(n_joint, counts),
        n_applicable_rows=n_applicable,
        n_joint_rows=n_joint,
        n_predictor_unobserved=n_applicable - n_joint,
        n_distinct_groups=counts.n_distinct_groups,
        n_repeated_groups=counts.n_repeated_groups,
        n_singleton_groups=counts.n_singleton_groups,
        n_conflicting_groups=counts.n_conflicting_groups,
        n_consistent_repeated_groups=counts.n_consistent_repeated_groups,
        n_rows_in_repeated_groups=counts.n_rows_in_repeated_groups,
        n_rows_in_conflicting_groups=counts.n_rows_in_conflicting_groups,
        n_target_classes=counts.n_target_classes,
    )


def _functional_dependency(
    groups: np.ndarray,
    classes: np.ndarray,
) -> _DependencyCounts:
    """Count repeated, singleton, and conflicting predictor groups.

    ``groups`` and ``classes`` are aligned joint rows. Missing values are
    already excluded. A group conflicts when its class codes are not all
    equal. Sorting by group code makes each group one contiguous run.
    """
    n_joint = int(groups.size)
    if n_joint == 0:
        return _DependencyCounts(0, 0, 0, 0, 0, 0, 0, 0)
    order = np.argsort(groups, kind="mergesort")
    ordered_groups = groups[order]
    ordered_classes = classes[order]
    starts = np.empty(n_joint, dtype=np.bool_)
    starts[0] = True
    if n_joint > 1:
        starts[1:] = ordered_groups[1:] != ordered_groups[:-1]
    boundaries = np.flatnonzero(starts)
    ends = np.empty(boundaries.size, dtype=np.intp)
    ends[:-1] = boundaries[1:]
    ends[-1] = n_joint
    sizes = ends - boundaries
    within = np.zeros(n_joint, dtype=np.intp)
    if n_joint > 1:
        within[1:] = ordered_classes[1:] != ordered_classes[:-1]
    within[boundaries] = 0
    conflicting = np.add.reduceat(within, boundaries) > 0
    repeated = sizes >= 2
    n_distinct = int(boundaries.size)
    n_repeated = int(np.count_nonzero(repeated))
    n_conflicting = int(np.count_nonzero(conflicting))
    n_rows_repeated = int(sizes[repeated].sum()) if n_repeated else 0
    n_rows_conflicting = int(sizes[conflicting].sum()) if n_conflicting else 0
    return _DependencyCounts(
        n_distinct_groups=n_distinct,
        n_repeated_groups=n_repeated,
        n_singleton_groups=n_distinct - n_repeated,
        n_conflicting_groups=n_conflicting,
        n_consistent_repeated_groups=n_repeated - n_conflicting,
        n_rows_in_repeated_groups=n_rows_repeated,
        n_rows_in_conflicting_groups=n_rows_conflicting,
        n_target_classes=int(np.unique(ordered_classes).size),
    )


def _mapping_status(n_joint: int, counts: _DependencyCounts) -> MappingStatus:
    if n_joint == 0:
        return MappingStatus.INSUFFICIENT_POPULATION
    if counts.n_conflicting_groups:
        return MappingStatus.CONFLICTING
    if counts.n_target_classes < 2:
        return MappingStatus.TARGET_CONSTANT_ON_JOINT
    if counts.n_repeated_groups == 0:
        return MappingStatus.TRIVIAL_UNIQUENESS
    return MappingStatus.DETERMINISTIC_REPEATED


def _exact_without_values(
    need_exact: bool, n_applicable: int
) -> ExactDuplicateEvidence:
    if not need_exact:
        return _incompatible_exact()
    return ExactDuplicateEvidence(
        status=ExactDuplicateStatus.INSUFFICIENT_POPULATION,
        n_applicable_rows=n_applicable,
        n_joint_rows=0,
        n_predictor_unobserved=n_applicable,
        n_equal_rows=0,
        n_unequal_rows=0,
    )


def _mapping_without_values(need_mapping: bool, n_applicable: int) -> MappingEvidence:
    if not need_mapping:
        return _mapping_not_applicable()
    return MappingEvidence(
        status=MappingStatus.INSUFFICIENT_POPULATION,
        n_applicable_rows=n_applicable,
        n_joint_rows=0,
        n_predictor_unobserved=n_applicable,
        n_distinct_groups=0,
        n_repeated_groups=0,
        n_singleton_groups=0,
        n_conflicting_groups=0,
        n_consistent_repeated_groups=0,
        n_rows_in_repeated_groups=0,
        n_rows_in_conflicting_groups=0,
        n_target_classes=0,
    )


def _incompatible_exact() -> ExactDuplicateEvidence:
    return ExactDuplicateEvidence(
        status=ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION,
        n_applicable_rows=0,
        n_joint_rows=0,
        n_predictor_unobserved=0,
        n_equal_rows=0,
        n_unequal_rows=0,
    )


def _mapping_not_applicable() -> MappingEvidence:
    return MappingEvidence(
        status=MappingStatus.NOT_APPLICABLE,
        n_applicable_rows=0,
        n_joint_rows=0,
        n_predictor_unobserved=0,
        n_distinct_groups=0,
        n_repeated_groups=0,
        n_singleton_groups=0,
        n_conflicting_groups=0,
        n_consistent_repeated_groups=0,
        n_rows_in_repeated_groups=0,
        n_rows_in_conflicting_groups=0,
        n_target_classes=0,
    )


def _predictor(
    column: ColumnAnalysis,
    exact: ExactDuplicateEvidence,
    mapping: MappingEvidence,
) -> PredictorLeakage:
    return PredictorLeakage(
        position=column.position,
        label=column.label,
        selected_type=column.inferred.selected_type,
        resolution_status=column.inferred.resolution.status,
        exact_duplicate=exact,
        deterministic_mapping=mapping,
    )


def _require_frame(
    frame: object,
    columns: object,
    target: object,
    target_type: type,
) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("target leakage analysis reads a pandas DataFrame")
    if not isinstance(columns, tuple):
        raise TypeError("columns must be a tuple")
    for index, column in enumerate(columns):
        if not isinstance(column, ColumnAnalysis):
            raise TypeError("columns must contain ColumnAnalysis records")
        if column.position != index:
            raise ValueError("column position must match column order")
    if not isinstance(target, target_type):
        raise TypeError("target must be a TargetAnalysis")
    if frame.shape != (target.population.n_total_rows, len(columns)):
        raise ValueError("frame shape must match the analyzed columns")
    if target.position >= len(columns):
        raise ValueError("target position is outside the column axis")


def _require_population_attachment(
    leakage: TargetLeakageAnalysis,
    target: TargetAnalysis,
) -> None:
    population = leakage.population
    if population.n_total_rows != target.population.n_total_rows:
        raise ValueError("leakage rows must be the target rows")
    if population.n_target_missing != target.population.n_target_missing:
        raise ValueError("leakage missing rows must be the target's missing rows")
    if population.n_target_observed != target.population.n_target_non_missing:
        raise ValueError("leakage observed rows must be the target's observed rows")
    if target.numeric_facts is not None and (
        leakage.applicability is LeakageApplicability.APPLICABLE
    ):
        if population.n_applicable != target.numeric_facts.finite_count:
            raise ValueError("applicable rows must be the finite target rows")
        non_finite = target.population.n_target_non_missing - population.n_applicable
        if population.n_target_non_finite != non_finite:
            raise ValueError("non-finite rows must be the target's non-finite rows")
    elif population.n_target_non_finite != 0:
        raise ValueError("only a numeric target has non-finite rows")


def _require_predictor_population(item: PredictorLeakage, n_applicable: int) -> None:
    exact = item.exact_duplicate
    if exact.status is not ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION:
        if exact.n_applicable_rows != n_applicable:
            raise ValueError("exact-duplicate rows must be the applicable target rows")
    mapping = item.deterministic_mapping
    if mapping.status is not MappingStatus.NOT_APPLICABLE:
        if mapping.n_applicable_rows != n_applicable:
            raise ValueError("mapping rows must be the applicable target rows")


def _exact_measured(evidence: ExactDuplicateEvidence) -> bool:
    return any(
        (
            evidence.n_applicable_rows,
            evidence.n_joint_rows,
            evidence.n_predictor_unobserved,
            evidence.n_equal_rows,
            evidence.n_unequal_rows,
        )
    )


def _require_exact_reconciliation(evidence: ExactDuplicateEvidence) -> None:
    joint = evidence.n_joint_rows
    if joint + evidence.n_predictor_unobserved != evidence.n_applicable_rows:
        raise ValueError("exact-duplicate rows must reconcile")
    if evidence.n_equal_rows + evidence.n_unequal_rows != joint:
        raise ValueError("equal and unequal rows must cover the joint rows")


def _mapping_measured(evidence: MappingEvidence) -> bool:
    return any(
        (
            evidence.n_applicable_rows,
            evidence.n_joint_rows,
            evidence.n_predictor_unobserved,
            evidence.n_distinct_groups,
            evidence.n_repeated_groups,
            evidence.n_singleton_groups,
            evidence.n_conflicting_groups,
            evidence.n_consistent_repeated_groups,
            evidence.n_rows_in_repeated_groups,
            evidence.n_rows_in_conflicting_groups,
            evidence.n_target_classes,
        )
    )


def _require_mapping_reconciliation(evidence: MappingEvidence) -> None:
    if (
        evidence.n_joint_rows + evidence.n_predictor_unobserved
        != evidence.n_applicable_rows
    ):
        raise ValueError("mapping rows must reconcile")
    if (
        evidence.n_repeated_groups + evidence.n_singleton_groups
        != evidence.n_distinct_groups
    ):
        raise ValueError("mapping groups must reconcile")
    if (
        evidence.n_consistent_repeated_groups + evidence.n_conflicting_groups
        != evidence.n_repeated_groups
    ):
        raise ValueError("repeated groups must reconcile")
    if (
        evidence.n_rows_in_repeated_groups + evidence.n_singleton_groups
        != evidence.n_joint_rows
    ):
        raise ValueError("mapping group rows must cover the joint rows")
    if evidence.n_conflicting_groups == 0:
        if evidence.n_rows_in_conflicting_groups != 0:
            raise ValueError("conflicting rows require a conflicting group")
    elif evidence.n_rows_in_conflicting_groups < 2:
        raise ValueError("a conflicting group covers at least two rows")
    if evidence.n_rows_in_conflicting_groups > evidence.n_rows_in_repeated_groups:
        raise ValueError("conflicting rows are repeated rows")
    if evidence.n_joint_rows == 0:
        if evidence.n_target_classes != 0:
            raise ValueError("an empty joint population has no target class")
    elif evidence.n_target_classes < 1:
        raise ValueError("a joint population has a target class")


def _same_value(left: object, right: object) -> bool:
    """Return whether two retained labels are the same value.

    ``True == 1`` in Python, so the types must also match. Float ``NaN``
    matches float ``NaN``, including a NumPy floating NaN, because those
    values are not equal under ``==``.
    """
    if left is right or labels_are_float_nan(left, right):
        return True
    if type(left) is not type(right):
        return False
    return bool(left == right)


def _copy_record(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return type(value)(
            **{
                field.name: _copy_record(getattr(value, field.name))
                for field in dataclasses.fields(value)
            }
        )
    if isinstance(value, tuple):
        return tuple(_copy_record(item) for item in value)
    return value


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _require_type(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")
