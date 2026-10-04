"""Retained result of the lightweight diagnostic model for an explicit target.

The diagnostic asks one question: does a single simple, untuned model
recover held-out predictive signal for the target from the other columns,
compared with a naive baseline on the same split? It is not a search for
the best model, and its numbers are not a predictability verdict.

This module holds the frozen result and its consistency rules. It does
not import scikit-learn, read a DataFrame, or fit anything. Fitting lives
in ``target_diagnostic_fit``. A retained result holds no estimator,
pipeline, array, frame, random generator, or row index.

The semantic target type is not the predictive task. Boolean is binary
classification. Categorical is binary or multiclass classification by
its observed class count. Numeric is regression, including numeric
``{0, 1}``. A target that is not supported by target analysis has no
task.

Permutation importance is the drop in held-out performance when one
input column is permuted on the validation rows. It is not a causal
effect, a statistical test, or a relationship strength. Correlated
inputs can share or hide that drop. Negative values are kept.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple
from typing import Union

from pytics.analysis.column import ColumnAnalysis
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


class DiagnosticStatus(Enum):
    """Whether the diagnostic model was fitted and evaluated.

    ``AVAILABLE`` means a model and its baseline were scored on held-out
    rows. Every other member is an analytical reason the model was not
    evaluated. ``TARGET_TYPE_UNSUPPORTED`` follows target analysis: the
    target is unsupported, ineligible, or unresolved there.
    ``NUMERICAL_FAILURE`` means predictions or validation scores were
    not finite float64 values.
    """

    AVAILABLE = "available"
    TARGET_TYPE_UNSUPPORTED = "target_type_unsupported"
    INSUFFICIENT_TARGET_CLASSES = "insufficient_target_classes"
    TOO_MANY_TARGET_CLASSES = "too_many_target_classes"
    INSUFFICIENT_TARGET_POPULATION = "insufficient_target_population"
    INSUFFICIENT_TARGET_VARIATION = "insufficient_target_variation"
    VALIDATION_SPLIT_IMPOSSIBLE = "validation_split_impossible"
    NO_ELIGIBLE_PREDICTORS = "no_eligible_predictors"
    NUMERICAL_FAILURE = "numerical_failure"


class PredictiveTask(Enum):
    """Predictive task of the diagnostic model. Not a semantic type."""

    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"

    @property
    def is_classification(self) -> bool:
        return self is not PredictiveTask.REGRESSION


class ValidationStrategy(Enum):
    """How the modeling rows are split into training and validation rows.

    ``STRATIFIED_HOLDOUT`` draws ``ceil(fraction * n_class)`` validation
    rows from each class, at least one and at most ``n_class - 1``, so
    every class is in both parts. ``RANDOM_HOLDOUT`` draws
    ``ceil(fraction * n)`` validation rows from all modeling rows.
    """

    STRATIFIED_HOLDOUT = "stratified_holdout"
    RANDOM_HOLDOUT = "random_holdout"


class DiagnosticEstimator(Enum):
    """Estimator identity. The value is the scikit-learn class path."""

    LOGISTIC_REGRESSION = "sklearn.linear_model.LogisticRegression"
    RIDGE = "sklearn.linear_model.Ridge"
    PRIOR_CLASSIFIER = "sklearn.dummy.DummyClassifier"
    MEAN_REGRESSOR = "sklearn.dummy.DummyRegressor"


class PredictorDecision(Enum):
    """Whether one non-target column entered the diagnostic model.

    ``IDENTIFIER``, ``EMPTY``, ``CONSTANT``, ``UNRESOLVED``, and
    ``UNSUPPORTED_TYPE`` follow the selected semantic state. Datetime,
    Timedelta, and Text are ``UNSUPPORTED_TYPE``. ``IDENTICAL_TO_TARGET``
    means leakage evidence recorded an exact duplicate on every
    applicable target row. The diagnostic excludes that column and does
    not compare it again. The decision is not itself a leakage verdict.
    The remaining exclusions are read from the training rows only.
    """

    INCLUDED = "included"
    IDENTIFIER = "identifier"
    EMPTY = "empty"
    CONSTANT = "constant"
    UNRESOLVED = "unresolved"
    UNSUPPORTED_TYPE = "unsupported_type"
    IDENTICAL_TO_TARGET = "identical_to_target"
    NO_TRAINING_VARIATION = "no_training_variation"
    TOO_MANY_LEVELS = "too_many_levels"
    SCALE_NOT_FINITE = "scale_not_finite"


class PredictorEncoding(Enum):
    """Internal preprocessing of an included column, fitted on training rows.

    ``STANDARDIZED`` is a Numeric column. Missing and non-finite values
    are imputed with the training median, a missing indicator is added
    when the training rows have such values, and the result is scaled to
    the training mean and standard deviation. ``ONE_HOT`` is a Boolean or
    Categorical column. Each training level becomes one indicator,
    missing is its own level, and a level absent from the training rows
    encodes as all zeros. Neither is a recommendation for the data.
    """

    STANDARDIZED = "standardized"
    ONE_HOT = "one_hot"


class DiagnosticMetric(Enum):
    """Held-out metric identity.

    ``ROC_AUC`` is binary. ``MACRO_OVR_ROC_AUC`` is the unweighted mean of
    one-versus-rest areas over the classes. ``LOG_LOSS`` uses natural logs
    and clips probabilities to ``[1e-15, 1]``. ``R2`` uses the validation
    mean and is not clamped. ``MAE`` and ``RMSE`` are in target units.
    """

    ROC_AUC = "roc_auc"
    MACRO_OVR_ROC_AUC = "macro_ovr_roc_auc"
    BALANCED_ACCURACY = "balanced_accuracy"
    LOG_LOSS = "log_loss"
    R2 = "r2"
    MAE = "mae"
    RMSE = "rmse"

    @property
    def higher_is_better(self) -> bool:
        return self not in _LOWER_IS_BETTER


_LOWER_IS_BETTER = frozenset(
    {DiagnosticMetric.LOG_LOSS, DiagnosticMetric.MAE, DiagnosticMetric.RMSE}
)
_UNIT_INTERVAL_METRICS = frozenset(
    {
        DiagnosticMetric.ROC_AUC,
        DiagnosticMetric.MACRO_OVR_ROC_AUC,
        DiagnosticMetric.BALANCED_ACCURACY,
    }
)
_MODELED_TYPES = frozenset(
    {SemanticType.NUMERIC, SemanticType.BOOLEAN, SemanticType.CATEGORICAL}
)
_SEMANTIC_DECISIONS = {
    SemanticType.IDENTIFIER: PredictorDecision.IDENTIFIER,
    SemanticType.EMPTY: PredictorDecision.EMPTY,
    SemanticType.CONSTANT: PredictorDecision.CONSTANT,
    SemanticType.DATETIME: PredictorDecision.UNSUPPORTED_TYPE,
    SemanticType.TIMEDELTA: PredictorDecision.UNSUPPORTED_TYPE,
    SemanticType.TEXT: PredictorDecision.UNSUPPORTED_TYPE,
}
# Statuses decided from the target alone. No predictor is screened.
_TARGET_STATUSES = frozenset(
    {
        DiagnosticStatus.TOO_MANY_TARGET_CLASSES,
        DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION,
        DiagnosticStatus.INSUFFICIENT_TARGET_VARIATION,
        DiagnosticStatus.VALIDATION_SPLIT_IMPOSSIBLE,
    }
)
_SCREENED_STATUSES = frozenset(
    {
        DiagnosticStatus.AVAILABLE,
        DiagnosticStatus.NO_ELIGIBLE_PREDICTORS,
        DiagnosticStatus.NUMERICAL_FAILURE,
    }
)


@dataclass(frozen=True)
class DiagnosticDesign:
    """Fixed design of the diagnostic, retained for reproduction.

    The design follows the task. Classification uses a stratified holdout,
    logistic regression, a prior-probability baseline, and log loss for
    permutation importance. Regression uses a random holdout, ridge
    regression, a training-mean baseline, and R² for permutation
    importance. ``estimator_parameters`` are the arguments passed to the
    estimator. Every other argument is the library default of
    ``library_version``. Nothing is tuned.
    """

    validation: ValidationStrategy
    validation_fraction: float
    random_seed: int
    estimator: DiagnosticEstimator
    estimator_parameters: Tuple[Tuple[str, object], ...]
    baseline: DiagnosticEstimator
    importance_metric: DiagnosticMetric
    permutation_repeats: int
    library_version: str

    def __post_init__(self) -> None:
        _require_type(self.validation, ValidationStrategy, "validation")
        _require_type(self.estimator, DiagnosticEstimator, "estimator")
        _require_type(self.baseline, DiagnosticEstimator, "baseline")
        _require_type(self.importance_metric, DiagnosticMetric, "importance_metric")
        fraction = self.validation_fraction
        if type(fraction) is not float or not 0.0 < fraction < 1.0:
            raise ValueError("validation_fraction must be a float in (0, 1)")
        _require_count(self.random_seed, "random_seed")
        _require_count(self.permutation_repeats, "permutation_repeats")
        if self.permutation_repeats < 1:
            raise ValueError("permutation_repeats must be positive")
        if not isinstance(self.estimator_parameters, tuple):
            raise TypeError("estimator_parameters must be a tuple")
        for item in self.estimator_parameters:
            if not (isinstance(item, tuple) and len(item) == 2):
                raise TypeError("estimator_parameters must hold name-value pairs")
            if not isinstance(item[0], str):
                raise TypeError("an estimator parameter name must be a str")
        if not isinstance(self.library_version, str) or not self.library_version:
            raise TypeError("library_version must be a non-empty str")


@dataclass(frozen=True)
class DiagnosticClassCount:
    """One observed target class and its split counts."""

    value: object
    n_training: int
    n_validation: int

    def __post_init__(self) -> None:
        _require_count(self.n_training, "n_training")
        _require_count(self.n_validation, "n_validation")
        if self.n_training < 1 or self.n_validation < 1:
            raise ValueError("every class is in both training and validation rows")

    @property
    def n_modeling(self) -> int:
        return self.n_training + self.n_validation


@dataclass(frozen=True)
class DiagnosticPopulation:
    """Rows of the target that the diagnostic could use.

    ``n_target_missing`` is the target's own missingness from target
    analysis. ``n_target_non_finite`` is a non-missing Numeric target
    value that is not finite, and is zero for a classification target.
    The modeling rows are the rest. Those three reconcile with
    ``n_total_rows``. Training and validation counts exist only after a
    split and reconcile with the modeling rows. ``classes`` lists each
    observed class with its split counts, for classification only.
    """

    n_total_rows: int
    n_target_missing: int
    n_target_non_finite: int
    n_modeling: int
    n_training: Optional[int] = None
    n_validation: Optional[int] = None
    classes: Tuple[DiagnosticClassCount, ...] = ()

    def __post_init__(self) -> None:
        _require_count(self.n_total_rows, "n_total_rows")
        _require_count(self.n_target_missing, "n_target_missing")
        _require_count(self.n_target_non_finite, "n_target_non_finite")
        _require_count(self.n_modeling, "n_modeling")
        total = self.n_target_missing + self.n_target_non_finite + self.n_modeling
        if total != self.n_total_rows:
            raise ValueError("diagnostic population counts must reconcile")
        if (self.n_training is None) != (self.n_validation is None):
            raise ValueError("training and validation counts are recorded together")
        if self.n_training is not None:
            _require_count(self.n_training, "n_training")
            _require_count(self.n_validation, "n_validation")
            if self.n_training + self.n_validation != self.n_modeling:
                raise ValueError(
                    "training and validation rows must be the modeling rows"
                )
        if not isinstance(self.classes, tuple):
            raise TypeError("classes must be a tuple")
        if not self.classes:
            return
        if self.n_training is None:
            raise ValueError("class split counts require a split")
        for item in self.classes:
            _require_type(item, DiagnosticClassCount, "classes")
        if sum(item.n_training for item in self.classes) != self.n_training:
            raise ValueError("class training counts must sum to n_training")
        if sum(item.n_validation for item in self.classes) != self.n_validation:
            raise ValueError("class validation counts must sum to n_validation")

    @property
    def n_target_non_missing(self) -> int:
        return self.n_total_rows - self.n_target_missing

    @property
    def is_split(self) -> bool:
        return self.n_training is not None


@dataclass(frozen=True)
class DiagnosticPredictor:
    """One non-target column and whether it entered the model.

    ``encoding`` is set only for an included column. ``n_training_levels``
    is the number of one-hot levels in the training rows, including a
    missing level. It is set for an included one-hot column and for a
    column excluded because it had too many levels.
    """

    position: int
    label: object
    selected_type: Optional[SemanticType]
    resolution_status: ResolutionStatus
    decision: PredictorDecision
    encoding: Optional[PredictorEncoding] = None
    n_training_levels: Optional[int] = None

    def __post_init__(self) -> None:
        _require_count(self.position, "position")
        if self.selected_type is not None:
            _require_type(self.selected_type, SemanticType, "selected_type")
        _require_type(self.resolution_status, ResolutionStatus, "resolution_status")
        _require_type(self.decision, PredictorDecision, "decision")
        if (self.resolution_status is ResolutionStatus.RESOLVED) != (
            self.selected_type is not None
        ):
            raise ValueError(
                "a selected type exists exactly when resolution selected one"
            )
        forced = _expected_semantic_decision(self.selected_type)
        if forced is not None:
            if self.decision is not forced:
                raise ValueError("predictor decision must follow the selected type")
        elif self.decision not in _CANDIDATE_DECISIONS:
            raise ValueError("predictor decision must follow the selected type")
        _require_encoding(self)
        _require_levels(self)


_CANDIDATE_DECISIONS = frozenset(
    {
        PredictorDecision.INCLUDED,
        PredictorDecision.IDENTICAL_TO_TARGET,
        PredictorDecision.NO_TRAINING_VARIATION,
        PredictorDecision.TOO_MANY_LEVELS,
        PredictorDecision.SCALE_NOT_FINITE,
    }
)


@dataclass(frozen=True)
class MetricComparison:
    """One held-out metric for the model and for the baseline.

    Both values use the same validation rows. ``None`` for both means the
    metric is undefined there. That happens only for R² when the
    validation target has no variation. ``improvement`` is positive when
    the model is better than the baseline under that metric's direction.
    It is not a predictability score.
    """

    metric: DiagnosticMetric
    model: Optional[float]
    baseline: Optional[float]

    def __post_init__(self) -> None:
        _require_type(self.metric, DiagnosticMetric, "metric")
        if (self.model is None) != (self.baseline is None):
            raise ValueError("model and baseline metrics are defined together")
        if self.model is None:
            if self.metric is not DiagnosticMetric.R2:
                raise ValueError("only R² can be undefined on validation rows")
            return
        _require_metric_value(self.metric, self.model)
        _require_metric_value(self.metric, self.baseline)

    @property
    def improvement(self) -> Optional[float]:
        if self.model is None or self.baseline is None:
            return None
        if self.metric.higher_is_better:
            return self.model - self.baseline
        return self.baseline - self.model


@dataclass(frozen=True)
class ClassificationEvaluation:
    """Held-out classification metrics and solver convergence."""

    roc_auc: MetricComparison
    balanced_accuracy: MetricComparison
    log_loss: MetricComparison
    solver_converged: bool

    def __post_init__(self) -> None:
        _require_type(self.roc_auc, MetricComparison, "roc_auc")
        if self.roc_auc.metric not in (
            DiagnosticMetric.ROC_AUC,
            DiagnosticMetric.MACRO_OVR_ROC_AUC,
        ):
            raise ValueError("roc_auc must be a ROC AUC metric")
        _require_metric(self.balanced_accuracy, DiagnosticMetric.BALANCED_ACCURACY)
        _require_metric(self.log_loss, DiagnosticMetric.LOG_LOSS)
        if type(self.solver_converged) is not bool:
            raise TypeError("solver_converged must be a bool")


@dataclass(frozen=True)
class RegressionEvaluation:
    """Held-out regression metrics."""

    r2: MetricComparison
    mae: MetricComparison
    rmse: MetricComparison

    def __post_init__(self) -> None:
        _require_metric(self.r2, DiagnosticMetric.R2)
        _require_metric(self.mae, DiagnosticMetric.MAE)
        _require_metric(self.rmse, DiagnosticMetric.RMSE)


DiagnosticEvaluation = Union[ClassificationEvaluation, RegressionEvaluation]


@dataclass(frozen=True)
class PredictorImportance:
    """Held-out permutation importance of one included column.

    ``decreases`` has one value per repeat: the model's validation score
    minus its score after that column is permuted on the validation rows.
    For log loss that is permuted loss minus original loss. Positive means
    permuting the column hurt held-out performance. Negative values are
    kept. ``mean`` and ``standard_deviation`` are read from those values.
    The deviation divides by the repeat count.
    """

    position: int
    label: object
    decreases: Tuple[float, ...]

    def __post_init__(self) -> None:
        _require_count(self.position, "position")
        if not isinstance(self.decreases, tuple) or not self.decreases:
            raise ValueError("decreases must be a non-empty tuple")
        for value in self.decreases:
            if type(value) is not float or not math.isfinite(value):
                raise ValueError("a permutation decrease must be a finite float")

    @property
    def mean(self) -> float:
        return math.fsum(self.decreases) / len(self.decreases)

    @property
    def standard_deviation(self) -> float:
        mean = self.mean
        squares = math.fsum((value - mean) ** 2 for value in self.decreases)
        return math.sqrt(squares / len(self.decreases))


@dataclass(frozen=True)
class PermutationImportance:
    """Held-out permutation importance for every included column.

    ``predictors`` follows physical column order. It is not sorted by
    importance and is not a ranking of relationships.
    """

    metric: DiagnosticMetric
    n_repeats: int
    predictors: Tuple[PredictorImportance, ...]

    def __post_init__(self) -> None:
        if self.metric not in (DiagnosticMetric.LOG_LOSS, DiagnosticMetric.R2):
            raise ValueError("permutation importance uses log loss or R²")
        _require_count(self.n_repeats, "n_repeats")
        if not isinstance(self.predictors, tuple) or not self.predictors:
            raise ValueError("predictors must be a non-empty tuple")
        previous = -1
        for item in self.predictors:
            _require_type(item, PredictorImportance, "predictors")
            if item.position <= previous:
                raise ValueError("importance follows ascending physical positions")
            previous = item.position
            if len(item.decreases) != self.n_repeats:
                raise ValueError("each predictor has one decrease per repeat")


@dataclass(frozen=True)
class TargetDiagnosticAnalysis:
    """Lightweight diagnostic model of one explicit target.

    ``target_position`` links this result to ``TargetAnalysis``. ``task``
    is ``None`` when the target is unsupported or has fewer than two
    observed classes. ``design`` exists exactly when ``task`` does.
    ``population`` exists for every supported target. ``predictors``
    lists every other column, in physical order, once predictor screening
    was reached, and is empty before that. ``evaluation`` exists only when
    the status is ``AVAILABLE``. ``importance`` exists with it, except
    when the importance metric is undefined on the validation rows.
    """

    target_position: int
    status: DiagnosticStatus
    task: Optional[PredictiveTask] = None
    design: Optional[DiagnosticDesign] = None
    population: Optional[DiagnosticPopulation] = None
    predictors: Tuple[DiagnosticPredictor, ...] = ()
    evaluation: Optional[DiagnosticEvaluation] = None
    importance: Optional[PermutationImportance] = None

    def __post_init__(self) -> None:
        _require_count(self.target_position, "target_position")
        _require_type(self.status, DiagnosticStatus, "status")
        if self.task is not None:
            _require_type(self.task, PredictiveTask, "task")
        _require_task_shape(self)
        _require_predictors(self)
        _require_evaluation(self)

    @property
    def included_predictors(self) -> Tuple[DiagnosticPredictor, ...]:
        return tuple(
            item
            for item in self.predictors
            if item.decision is PredictorDecision.INCLUDED
        )


def predictive_task_for(
    selected_type: Optional[SemanticType],
    n_observed_classes: Optional[int],
) -> Optional[PredictiveTask]:
    """Return the diagnostic task for a supported target's semantic type.

    Numeric is regression, whatever its values. Boolean and Categorical
    are classification only with at least two observed classes: two is
    binary and more is multiclass. Any other type has no task.
    """
    if selected_type is SemanticType.NUMERIC:
        return PredictiveTask.REGRESSION
    if selected_type not in (SemanticType.BOOLEAN, SemanticType.CATEGORICAL):
        return None
    _require_count(n_observed_classes, "n_observed_classes")
    if n_observed_classes < 2:
        return None
    if n_observed_classes == 2:
        return PredictiveTask.BINARY_CLASSIFICATION
    return PredictiveTask.MULTICLASS_CLASSIFICATION


def semantic_predictor_decision(
    selected_type: Optional[SemanticType],
) -> Optional[PredictorDecision]:
    """Return the exclusion a semantic state forces, or ``None``.

    ``None`` means Numeric, Boolean, or Categorical: the column is a
    candidate and later checks decide.
    """
    return _expected_semantic_decision(selected_type)


def copy_target_diagnostic(
    analysis: TargetDiagnosticAnalysis,
) -> TargetDiagnosticAnalysis:
    """Return new frozen records with the same values.

    Every nested record is rebuilt and revalidated. Labels, class values,
    enums, and numbers are kept as they are. Nothing is recomputed.
    """
    _require_type(analysis, TargetDiagnosticAnalysis, "analysis")
    return _copy_record(analysis)


def _require_diagnostic_attachment(
    diagnostic: Optional[TargetDiagnosticAnalysis],
    target: object,
    columns: Tuple[ColumnAnalysis, ...],
) -> None:
    """Check a retained diagnostic against the target and column records.

    This does not refit. It checks what the retained facts already fix:
    the link, the task, the target-side population and classes, and each
    predictor's identity and semantic state.
    """
    from pytics.analysis.target import TargetAnalysis
    from pytics.analysis.target import TargetStatus

    if target is None:
        if diagnostic is not None:
            raise ValueError("a target diagnostic requires target analysis")
        return
    _require_type(target, TargetAnalysis, "target_analysis")
    if diagnostic is None:
        raise ValueError("target analysis requires its diagnostic result")
    _require_type(diagnostic, TargetDiagnosticAnalysis, "target_diagnostic")
    if diagnostic.target_position != target.position:
        raise ValueError("the diagnostic must name the analyzed target")
    if target.status is not TargetStatus.SUPPORTED:
        if diagnostic.status is not DiagnosticStatus.TARGET_TYPE_UNSUPPORTED:
            raise ValueError("an unsupported target has no diagnostic model")
        return
    if diagnostic.status is DiagnosticStatus.TARGET_TYPE_UNSUPPORTED:
        raise ValueError("a supported target is not an unsupported diagnostic")
    expected_task = predictive_task_for(
        target.selected_type, _observed_class_count(target)
    )
    if diagnostic.task is not expected_task:
        raise ValueError("the diagnostic task must follow the target's semantic type")
    _require_population_attachment(diagnostic.population, target)
    if diagnostic.predictors:
        others = tuple(
            column for column in columns if column.position != target.position
        )
        if len(diagnostic.predictors) != len(others):
            raise ValueError("diagnostic predictors must list every other column")
        for item, column in zip(diagnostic.predictors, others):
            if item.position != column.position or not _same_value(
                item.label, column.label
            ):
                raise ValueError("a diagnostic predictor must be its column")
            if item.selected_type is not column.inferred.selected_type:
                raise ValueError("a diagnostic predictor keeps its selected type")
            if item.resolution_status is not column.inferred.resolution.status:
                raise ValueError("a diagnostic predictor keeps its resolution status")


def _observed_class_count(target: object) -> Optional[int]:
    if target.boolean_facts is not None:
        return target.boolean_facts.n_observed_classes
    if target.categorical_facts is not None:
        return target.categorical_facts.n_observed
    return None


def _require_population_attachment(
    population: DiagnosticPopulation,
    target: object,
) -> None:
    if population.n_total_rows != target.population.n_total_rows:
        raise ValueError("diagnostic rows must be the target rows")
    if population.n_target_missing != target.population.n_target_missing:
        raise ValueError("diagnostic missing rows must be the target's missing rows")
    if target.numeric_facts is not None:
        expected_modeling = target.numeric_facts.finite_count
    else:
        expected_modeling = target.population.n_target_non_missing
    if population.n_modeling != expected_modeling:
        raise ValueError("modeling rows must be the finite non-missing target rows")
    if not population.classes:
        return
    expected = _target_class_counts(target)
    if len(population.classes) != len(expected):
        raise ValueError("diagnostic classes must be the observed target classes")
    for item, (value, count) in zip(population.classes, expected):
        if not _same_value(item.value, value):
            raise ValueError("diagnostic classes must be the observed target classes")
        if item.n_modeling != count:
            raise ValueError(
                "diagnostic class counts must be the observed class counts"
            )


def _target_class_counts(target: object) -> Tuple[Tuple[object, int], ...]:
    if target.boolean_facts is not None:
        facts = target.boolean_facts
        pairs = ((False, facts.false_count), (True, facts.true_count))
        return tuple(pair for pair in pairs if pair[1] > 0)
    levels = target.categorical_facts.levels
    return tuple((level.value, level.count) for level in levels)


def _expected_semantic_decision(
    selected_type: Optional[SemanticType],
) -> Optional[PredictorDecision]:
    if selected_type is None:
        return PredictorDecision.UNRESOLVED
    if selected_type in _MODELED_TYPES:
        return None
    return _SEMANTIC_DECISIONS[selected_type]


def _require_encoding(item: DiagnosticPredictor) -> None:
    if item.decision is not PredictorDecision.INCLUDED:
        if item.encoding is not None:
            raise ValueError("only an included predictor has an encoding")
        return
    _require_type(item.encoding, PredictorEncoding, "encoding")
    expected = (
        PredictorEncoding.STANDARDIZED
        if item.selected_type is SemanticType.NUMERIC
        else PredictorEncoding.ONE_HOT
    )
    if item.encoding is not expected:
        raise ValueError("predictor encoding must follow the selected type")


def _require_levels(item: DiagnosticPredictor) -> None:
    counted = item.encoding is PredictorEncoding.ONE_HOT or (
        item.decision is PredictorDecision.TOO_MANY_LEVELS
    )
    if item.decision is PredictorDecision.TOO_MANY_LEVELS:
        if item.selected_type is not SemanticType.CATEGORICAL:
            raise ValueError("only a Categorical predictor has too many levels")
    if item.decision is PredictorDecision.SCALE_NOT_FINITE:
        if item.selected_type is not SemanticType.NUMERIC:
            raise ValueError("only a Numeric predictor has a scale")
    if not counted:
        if item.n_training_levels is not None:
            raise ValueError("training levels are counted for one-hot predictors only")
        return
    _require_count(item.n_training_levels, "n_training_levels")
    if item.n_training_levels < 2:
        raise ValueError("a counted one-hot predictor has at least two levels")


def _require_task_shape(analysis: TargetDiagnosticAnalysis) -> None:
    status = analysis.status
    if status is DiagnosticStatus.TARGET_TYPE_UNSUPPORTED:
        if (
            analysis.task is not None
            or analysis.design is not None
            or analysis.population is not None
        ):
            raise ValueError("an unsupported target has no task, design, or population")
        return
    if analysis.population is None:
        raise ValueError("a supported target keeps its diagnostic population")
    _require_type(analysis.population, DiagnosticPopulation, "population")
    if status is DiagnosticStatus.INSUFFICIENT_TARGET_CLASSES:
        if analysis.task is not None or analysis.design is not None:
            raise ValueError("fewer than two classes have no task or design")
        return
    if analysis.task is None:
        raise ValueError("this diagnostic status requires a predictive task")
    _require_type(analysis.design, DiagnosticDesign, "design")
    _require_design_for_task(analysis.design, analysis.task)
    task = analysis.task
    if status is DiagnosticStatus.INSUFFICIENT_TARGET_VARIATION and (
        task is not PredictiveTask.REGRESSION
    ):
        raise ValueError("target variation is checked for regression")
    if status is DiagnosticStatus.TOO_MANY_TARGET_CLASSES and (
        task is not PredictiveTask.MULTICLASS_CLASSIFICATION
    ):
        raise ValueError("a class limit applies to multiclass classification")
    if status is DiagnosticStatus.VALIDATION_SPLIT_IMPOSSIBLE and (
        not task.is_classification
    ):
        raise ValueError("a stratified split applies to classification")
    population = analysis.population
    if status in _TARGET_STATUSES and population.is_split:
        raise ValueError("a target-side status is decided before the split")
    if status in (DiagnosticStatus.AVAILABLE, DiagnosticStatus.NUMERICAL_FAILURE):
        if not population.is_split:
            raise ValueError("a fitted diagnostic has training and validation rows")
    if population.is_split and task.is_classification:
        n_classes = len(population.classes)
        binary = task is PredictiveTask.BINARY_CLASSIFICATION
        if (binary and n_classes != 2) or (not binary and n_classes < 3):
            raise ValueError("class counts must follow the classification task")
    elif population.classes:
        raise ValueError("class counts belong to a split classification target")


def _require_design_for_task(design: DiagnosticDesign, task: PredictiveTask) -> None:
    if task.is_classification:
        expected = (
            ValidationStrategy.STRATIFIED_HOLDOUT,
            DiagnosticEstimator.LOGISTIC_REGRESSION,
            DiagnosticEstimator.PRIOR_CLASSIFIER,
            DiagnosticMetric.LOG_LOSS,
        )
    else:
        expected = (
            ValidationStrategy.RANDOM_HOLDOUT,
            DiagnosticEstimator.RIDGE,
            DiagnosticEstimator.MEAN_REGRESSOR,
            DiagnosticMetric.R2,
        )
    actual = (
        design.validation,
        design.estimator,
        design.baseline,
        design.importance_metric,
    )
    if actual != expected:
        raise ValueError("the diagnostic design must follow the predictive task")


def _require_predictors(analysis: TargetDiagnosticAnalysis) -> None:
    if not isinstance(analysis.predictors, tuple):
        raise TypeError("predictors must be a tuple")
    previous = -1
    for item in analysis.predictors:
        _require_type(item, DiagnosticPredictor, "predictors")
        if item.position == analysis.target_position:
            raise ValueError("the target is not its own predictor")
        if item.position <= previous:
            raise ValueError("predictors follow ascending physical positions")
        previous = item.position
    if analysis.predictors and analysis.status not in _SCREENED_STATUSES:
        raise ValueError("predictors are screened only after the target checks")
    population = analysis.population
    split = population is not None and population.is_split
    for item in analysis.predictors:
        if item.decision in _TRAINING_DECISIONS and not split:
            raise ValueError("training-row decisions require a split")
    included = analysis.included_predictors
    if analysis.status is DiagnosticStatus.NO_ELIGIBLE_PREDICTORS:
        if included:
            raise ValueError("no eligible predictors means none was included")
        return
    if analysis.status in _SCREENED_STATUSES and not included:
        raise ValueError("a fitted diagnostic includes at least one predictor")


_TRAINING_DECISIONS = frozenset(
    {
        PredictorDecision.INCLUDED,
        PredictorDecision.NO_TRAINING_VARIATION,
        PredictorDecision.TOO_MANY_LEVELS,
        PredictorDecision.SCALE_NOT_FINITE,
    }
)


def _require_evaluation(analysis: TargetDiagnosticAnalysis) -> None:
    evaluation = analysis.evaluation
    importance = analysis.importance
    if analysis.status is not DiagnosticStatus.AVAILABLE:
        if evaluation is not None or importance is not None:
            raise ValueError("only an available diagnostic is evaluated")
        return
    task = analysis.task
    if task.is_classification:
        _require_type(evaluation, ClassificationEvaluation, "evaluation")
        expected_auc = (
            DiagnosticMetric.ROC_AUC
            if task is PredictiveTask.BINARY_CLASSIFICATION
            else DiagnosticMetric.MACRO_OVR_ROC_AUC
        )
        if evaluation.roc_auc.metric is not expected_auc:
            raise ValueError("the ROC AUC metric must follow the task")
        importance_defined = True
    else:
        _require_type(evaluation, RegressionEvaluation, "evaluation")
        importance_defined = evaluation.r2.model is not None
    if not importance_defined:
        if importance is not None:
            raise ValueError("importance needs a defined importance metric")
        return
    _require_type(importance, PermutationImportance, "importance")
    if importance.metric is not analysis.design.importance_metric:
        raise ValueError("importance must use the design's metric")
    if importance.n_repeats != analysis.design.permutation_repeats:
        raise ValueError("importance must use the design's repeat count")
    included = analysis.included_predictors
    if tuple(item.position for item in importance.predictors) != tuple(
        item.position for item in included
    ):
        raise ValueError("importance covers exactly the included predictors")
    for scored, item in zip(importance.predictors, included):
        if not _same_value(scored.label, item.label):
            raise ValueError("importance keeps the predictor label")


def _require_metric(comparison: object, metric: DiagnosticMetric) -> None:
    _require_type(comparison, MetricComparison, metric.value)
    if comparison.metric is not metric:
        raise ValueError(f"{metric.value} must hold the {metric.value} metric")


def _require_metric_value(metric: DiagnosticMetric, value: object) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError("a metric value must be a finite float")
    if metric in _UNIT_INTERVAL_METRICS and not 0.0 <= value <= 1.0:
        raise ValueError(f"{metric.value} lies on [0, 1]")
    if metric is DiagnosticMetric.R2 and value > 1.0:
        raise ValueError("R² cannot exceed 1")
    if not metric.higher_is_better and value < 0.0:
        raise ValueError(f"{metric.value} cannot be negative")


def _same_value(left: object, right: object) -> bool:
    """Return whether two retained labels or class values are the same value.

    ``True == 1`` in Python, so the types must also match.
    """
    if left is right:
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
