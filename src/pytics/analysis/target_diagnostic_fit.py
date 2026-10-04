"""Fit the lightweight diagnostic model for one explicit target.

This module is the only place that imports scikit-learn. It reads the
source frame because fitting needs values. It returns a frozen
``TargetDiagnosticAnalysis`` that keeps none of the estimator, the
pipeline, the arrays, the random generator, or the row split.

The design is fixed. There is one estimator per task, no search, no
tuning, no threshold choice, and no model comparison other than the
naive baseline on the same split:

- classification: stratified 25% holdout, ``LogisticRegression`` against
  ``DummyClassifier(strategy="prior")``;
- regression: random 25% holdout, ``Ridge`` against
  ``DummyRegressor(strategy="mean")``.

Target-side eligibility is read from the descriptive facts target
analysis already retained. The split depends only on the target. Every
learned transformation — median, mean, scale, and one-hot vocabulary —
is fitted inside one scikit-learn pipeline on the training rows only.
Validation rows are used only to score the model, the baseline, and
held-out permutation importance.
"""

from __future__ import annotations

import math
import warnings
from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd
import sklearn
from scipy import sparse
from scipy.stats import rankdata
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.dummy import DummyRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

from pytics.analysis.categorical import _retain_category
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.relationships.boolean_boolean import _read_boolean_column
from pytics.analysis.relationships.numeric_categorical import _read_categorical_column
from pytics.analysis.relationships.numeric_numeric import _read_numeric_column
from pytics.analysis.target import TargetAnalysis
from pytics.analysis.target import TargetStatus
from pytics.analysis.target_diagnostic import ClassificationEvaluation
from pytics.analysis.target_diagnostic import DiagnosticClassCount
from pytics.analysis.target_diagnostic import DiagnosticDesign
from pytics.analysis.target_diagnostic import DiagnosticEstimator
from pytics.analysis.target_diagnostic import DiagnosticMetric
from pytics.analysis.target_diagnostic import DiagnosticPopulation
from pytics.analysis.target_diagnostic import DiagnosticPredictor
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import MetricComparison
from pytics.analysis.target_diagnostic import PermutationImportance
from pytics.analysis.target_diagnostic import PredictiveTask
from pytics.analysis.target_diagnostic import PredictorDecision
from pytics.analysis.target_diagnostic import PredictorEncoding
from pytics.analysis.target_diagnostic import PredictorImportance
from pytics.analysis.target_diagnostic import RegressionEvaluation
from pytics.analysis.target_diagnostic import TargetDiagnosticAnalysis
from pytics.analysis.target_diagnostic import ValidationStrategy
from pytics.analysis.target_diagnostic import _target_class_counts
from pytics.analysis.target_diagnostic import predictive_task_for
from pytics.analysis.target_diagnostic import semantic_predictor_decision
from pytics.semantics.interpretation import SemanticType

DEFAULT_RANDOM_SEED = 0

_VALIDATION_FRACTION = 0.25
# Feasibility floors, not reliability thresholds: a 25% holdout of 20 rows
# leaves 15 training and 5 validation rows, and a class needs one row on
# each side of the split.
_MIN_MODELING_ROWS = 20
_MIN_ROWS_PER_CLASS = 2
# Computational bounds on one-hot width and on the multinomial probability
# matrix. They are not a high-cardinality definition.
_MAX_TARGET_CLASSES = 100
_MAX_ONE_HOT_LEVELS = 1000
_PERMUTATION_REPEATS = 5
_LOG_LOSS_FLOOR = 1e-15

_LOGISTIC_PARAMETERS: Tuple[Tuple[str, object], ...] = (
    ("C", 1.0),
    ("solver", "lbfgs"),
    ("max_iter", 1000),
)
_RIDGE_PARAMETERS: Tuple[Tuple[str, object], ...] = (
    ("alpha", 1.0),
    ("solver", "auto"),
)

# Encoded representation of one column on the modeling rows: float64 with
# NaN for missing and non-finite Numeric values, or int64 one-hot codes
# with -1 for a missing Boolean or Categorical value.
_Image = np.ndarray


def analyze_target_diagnostic(
    frame: pd.DataFrame,
    columns: Tuple[ColumnAnalysis, ...],
    target: TargetAnalysis,
    *,
    seed: int = DEFAULT_RANDOM_SEED,
) -> TargetDiagnosticAnalysis:
    """Fit and score the diagnostic model for an analyzed target.

    ``columns`` and ``target`` are the analysis of ``frame``. The frame is
    read, not modified, and not retained. A reason the model cannot be
    evaluated is returned as a status. Inconsistent arguments raise.
    """
    _require_inputs(frame, columns, target, seed)
    position = target.position
    if target.status is not TargetStatus.SUPPORTED:
        return TargetDiagnosticAnalysis(
            target_position=position,
            status=DiagnosticStatus.TARGET_TYPE_UNSUPPORTED,
        )
    population = _population_from_facts(target)
    class_counts = _target_class_counts_or_empty(target)
    task = predictive_task_for(target.selected_type, len(class_counts))
    if task is None:
        return TargetDiagnosticAnalysis(
            target_position=position,
            status=DiagnosticStatus.INSUFFICIENT_TARGET_CLASSES,
            population=population,
        )
    design = _design(task, seed)
    rejected = _target_side_status(task, target, population, class_counts)
    if rejected is not None:
        return TargetDiagnosticAnalysis(
            target_position=position,
            status=rejected,
            task=task,
            design=design,
            population=population,
        )
    rows, y, class_values = _read_target(frame.iloc[:, position], target.selected_type)
    if rows.size != population.n_modeling:
        raise ValueError("frame target values do not match the target analysis")
    screened, images = _screen_semantics(
        frame, columns, position, task, rows, y, class_values
    )
    if not images:
        return TargetDiagnosticAnalysis(
            target_position=position,
            status=DiagnosticStatus.NO_ELIGIBLE_PREDICTORS,
            task=task,
            design=design,
            population=population,
            predictors=tuple(
                _predictor_record(column, decision) for column, decision in screened
            ),
        )
    validation = _validation_mask(y, task, np.random.default_rng(seed))
    population = _split_population(population, y, validation, class_values)
    predictors = _screen_training(screened, images, validation)
    included = tuple(
        item for item in predictors if item.decision is PredictorDecision.INCLUDED
    )
    if not included:
        return TargetDiagnosticAnalysis(
            target_position=position,
            status=DiagnosticStatus.NO_ELIGIBLE_PREDICTORS,
            task=task,
            design=design,
            population=population,
            predictors=predictors,
        )
    fitted = _fit_and_score(
        task, len(class_values), included, images, rows, y, validation, seed
    )
    if fitted is None:
        return TargetDiagnosticAnalysis(
            target_position=position,
            status=DiagnosticStatus.NUMERICAL_FAILURE,
            task=task,
            design=design,
            population=population,
            predictors=predictors,
        )
    evaluation, importance = fitted
    return TargetDiagnosticAnalysis(
        target_position=position,
        status=DiagnosticStatus.AVAILABLE,
        task=task,
        design=design,
        population=population,
        predictors=predictors,
        evaluation=evaluation,
        importance=importance,
    )


def _require_inputs(
    frame: object,
    columns: object,
    target: object,
    seed: object,
) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("the diagnostic model reads a pandas DataFrame")
    if not isinstance(columns, tuple):
        raise TypeError("columns must be a tuple")
    for index, column in enumerate(columns):
        if not isinstance(column, ColumnAnalysis):
            raise TypeError("columns must contain ColumnAnalysis records")
        if column.position != index:
            raise ValueError("column position must match column order")
    if not isinstance(target, TargetAnalysis):
        raise TypeError("target must be a TargetAnalysis")
    if frame.shape != (target.population.n_total_rows, len(columns)):
        raise ValueError("frame shape must match the analyzed columns")
    if target.position >= len(columns):
        raise ValueError("target position is outside the column axis")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative int")


def _population_from_facts(target: TargetAnalysis) -> DiagnosticPopulation:
    retained = target.population
    if target.numeric_facts is not None:
        n_modeling = target.numeric_facts.finite_count
    else:
        n_modeling = retained.n_target_non_missing
    return DiagnosticPopulation(
        n_total_rows=retained.n_total_rows,
        n_target_missing=retained.n_target_missing,
        n_target_non_finite=retained.n_target_non_missing - n_modeling,
        n_modeling=n_modeling,
    )


def _target_class_counts_or_empty(
    target: TargetAnalysis,
) -> Tuple[Tuple[object, int], ...]:
    if target.selected_type is SemanticType.NUMERIC:
        return ()
    return _target_class_counts(target)


def _design(task: PredictiveTask, seed: int) -> DiagnosticDesign:
    if task.is_classification:
        return DiagnosticDesign(
            validation=ValidationStrategy.STRATIFIED_HOLDOUT,
            validation_fraction=_VALIDATION_FRACTION,
            random_seed=seed,
            estimator=DiagnosticEstimator.LOGISTIC_REGRESSION,
            estimator_parameters=_LOGISTIC_PARAMETERS,
            baseline=DiagnosticEstimator.PRIOR_CLASSIFIER,
            importance_metric=DiagnosticMetric.LOG_LOSS,
            permutation_repeats=_PERMUTATION_REPEATS,
            library_version=sklearn.__version__,
        )
    return DiagnosticDesign(
        validation=ValidationStrategy.RANDOM_HOLDOUT,
        validation_fraction=_VALIDATION_FRACTION,
        random_seed=seed,
        estimator=DiagnosticEstimator.RIDGE,
        estimator_parameters=_RIDGE_PARAMETERS,
        baseline=DiagnosticEstimator.MEAN_REGRESSOR,
        importance_metric=DiagnosticMetric.R2,
        permutation_repeats=_PERMUTATION_REPEATS,
        library_version=sklearn.__version__,
    )


def _target_side_status(
    task: PredictiveTask,
    target: TargetAnalysis,
    population: DiagnosticPopulation,
    class_counts: Tuple[Tuple[object, int], ...],
) -> Optional[DiagnosticStatus]:
    """Return a status decided from retained target facts, or ``None``."""
    if len(class_counts) > _MAX_TARGET_CLASSES:
        return DiagnosticStatus.TOO_MANY_TARGET_CLASSES
    if population.n_modeling < _MIN_MODELING_ROWS:
        return DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION
    if task is PredictiveTask.REGRESSION:
        facts = target.numeric_facts
        if facts.minimum == facts.maximum:
            return DiagnosticStatus.INSUFFICIENT_TARGET_VARIATION
        return None
    if min(count for _, count in class_counts) < _MIN_ROWS_PER_CLASS:
        return DiagnosticStatus.VALIDATION_SPLIT_IMPOSSIBLE
    return None


def _read_target(
    series: pd.Series,
    selected: SemanticType,
) -> Tuple[np.ndarray, np.ndarray, Tuple[object, ...]]:
    """Return modeling row positions, model labels, and class values.

    Regression labels are the finite float64 target values. Class labels
    index the observed classes: ``False`` then ``True``, or the observed
    categorical vocabulary in its physical order.
    """
    if selected is SemanticType.NUMERIC:
        values, finite = _read_numeric_column(series)
        rows = np.flatnonzero(finite)
        return rows, values[rows].astype(np.float64), ()
    if selected is SemanticType.CATEGORICAL:
        codes, categories = _read_categorical_column(series)
        rows = np.flatnonzero(codes >= 0)
        observed = np.unique(codes[rows])
        labels = np.searchsorted(observed, codes[rows]).astype(np.intp)
        values = tuple(_retain_category(categories[code]) for code in observed)
        return rows, labels, values
    observed_mask, is_true = _read_boolean_column(series)
    rows = np.flatnonzero(observed_mask)
    return rows, is_true[rows].astype(np.intp), (False, True)


def _screen_semantics(
    frame: pd.DataFrame,
    columns: Tuple[ColumnAnalysis, ...],
    target_position: int,
    task: PredictiveTask,
    rows: np.ndarray,
    y: np.ndarray,
    class_values: Tuple[object, ...],
) -> Tuple[Tuple[Tuple[ColumnAnalysis, Optional[PredictorDecision]], ...], dict]:
    """Apply the semantic and duplicate exclusions to every other column.

    Returns each other column with its exclusion, or ``None`` for a
    candidate, and the modeling-row image of each candidate. Candidates
    are decided later from the training rows.
    """
    target_type = columns[target_position].inferred.selected_type
    screened: List[Tuple[ColumnAnalysis, Optional[PredictorDecision]]] = []
    images: dict = {}
    for column in columns:
        if column.position == target_position:
            continue
        selected = column.inferred.selected_type
        decision = semantic_predictor_decision(selected)
        if decision is None:
            image, vocabulary = _read_predictor(frame.iloc[:, column.position], selected)
            image = image[rows]
            if selected is target_type and _identical_to_target(
                image, vocabulary, task, y, class_values
            ):
                decision = PredictorDecision.IDENTICAL_TO_TARGET
            else:
                images[column.position] = image
        screened.append((column, decision))
    return tuple(screened), images


def _read_predictor(
    series: pd.Series,
    selected: SemanticType,
) -> Tuple[_Image, Tuple[object, ...]]:
    if selected is SemanticType.NUMERIC:
        values, finite = _read_numeric_column(series)
        image = np.full(values.shape, np.nan, dtype=np.float64)
        image[finite] = values[finite].astype(np.float64)
        return image, ()
    if selected is SemanticType.CATEGORICAL:
        codes, categories = _read_categorical_column(series)
        return codes.astype(np.int64), categories
    observed, is_true = _read_boolean_column(series)
    return np.where(observed, is_true.astype(np.int64), np.int64(-1)), ()


def _identical_to_target(
    image: _Image,
    vocabulary: Tuple[object, ...],
    task: PredictiveTask,
    y: np.ndarray,
    class_values: Tuple[object, ...],
) -> bool:
    """Return whether a same-type column equals the target on every modeling row.

    A missing or non-finite predictor value on any modeling row means the
    column is not a copy. A relabeled or partial copy is not detected.
    """
    if task is PredictiveTask.REGRESSION:
        return bool(np.all(np.isfinite(image)) and np.array_equal(image, y))
    if np.any(image < 0):
        return False
    if not vocabulary:
        return bool(np.array_equal(image, y))
    predictor_values = np.empty(len(vocabulary), dtype=object)
    predictor_values[:] = list(vocabulary)
    target_values = np.empty(len(class_values), dtype=object)
    target_values[:] = list(class_values)
    return bool(np.all(predictor_values[image] == target_values[y]))


def _predictor_record(
    column: ColumnAnalysis,
    decision: PredictorDecision,
    *,
    n_training_levels: Optional[int] = None,
) -> DiagnosticPredictor:
    selected = column.inferred.selected_type
    encoding = None
    if decision is PredictorDecision.INCLUDED:
        encoding = (
            PredictorEncoding.STANDARDIZED
            if selected is SemanticType.NUMERIC
            else PredictorEncoding.ONE_HOT
        )
    return DiagnosticPredictor(
        position=column.position,
        label=column.label,
        selected_type=selected,
        resolution_status=column.inferred.resolution.status,
        decision=decision,
        encoding=encoding,
        n_training_levels=n_training_levels,
    )


def _validation_mask(
    y: np.ndarray,
    task: PredictiveTask,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return the validation rows of the modeling population.

    Classification draws ``ceil(fraction * n_class)`` rows from each class
    in class order, at least one and at most ``n_class - 1``. Regression
    draws ``ceil(fraction * n)`` rows from all modeling rows.
    """
    n_rows = int(y.shape[0])
    validation = np.zeros(n_rows, dtype=np.bool_)
    if not task.is_classification:
        size = math.ceil(_VALIDATION_FRACTION * n_rows)
        validation[rng.permutation(n_rows)[:size]] = True
        return validation
    for label in range(int(y.max()) + 1):
        members = np.flatnonzero(y == label)
        size = math.ceil(_VALIDATION_FRACTION * members.size)
        size = min(max(size, 1), members.size - 1)
        validation[rng.permutation(members)[:size]] = True
    return validation


def _split_population(
    population: DiagnosticPopulation,
    y: np.ndarray,
    validation: np.ndarray,
    class_values: Tuple[object, ...],
) -> DiagnosticPopulation:
    classes = tuple(
        DiagnosticClassCount(
            value=value,
            n_training=int(np.count_nonzero((y == label) & ~validation)),
            n_validation=int(np.count_nonzero((y == label) & validation)),
        )
        for label, value in enumerate(class_values)
    )
    n_validation = int(np.count_nonzero(validation))
    return DiagnosticPopulation(
        n_total_rows=population.n_total_rows,
        n_target_missing=population.n_target_missing,
        n_target_non_finite=population.n_target_non_finite,
        n_modeling=population.n_modeling,
        n_training=population.n_modeling - n_validation,
        n_validation=n_validation,
        classes=classes,
    )


def _screen_training(
    screened: Tuple[Tuple[ColumnAnalysis, Optional[PredictorDecision]], ...],
    images: dict,
    validation: np.ndarray,
) -> Tuple[DiagnosticPredictor, ...]:
    """Decide each candidate from its training rows only."""
    training = ~validation
    records = []
    for column, decision in screened:
        levels = None
        if decision is None:
            image = images[column.position][training]
            if column.inferred.selected_type is SemanticType.NUMERIC:
                decision = _numeric_training_decision(image)
            else:
                decision, levels = _one_hot_training_decision(image)
        records.append(_predictor_record(column, decision, n_training_levels=levels))
    return tuple(records)


def _numeric_training_decision(image: np.ndarray) -> PredictorDecision:
    """Include a Numeric column whose training image varies and can be scaled.

    A single finite value still varies when some training rows are
    missing, because the missing indicator differs.
    """
    finite = np.isfinite(image)
    if not finite.any():
        return PredictorDecision.NO_TRAINING_VARIATION
    observed = image[finite]
    if np.unique(observed).size < 2 and finite.all():
        return PredictorDecision.NO_TRAINING_VARIATION
    with np.errstate(over="ignore", invalid="ignore"):
        mean = float(np.mean(observed))
        deviation = float(np.std(observed))
    if not (math.isfinite(mean) and math.isfinite(deviation)):
        return PredictorDecision.SCALE_NOT_FINITE
    return PredictorDecision.INCLUDED


def _one_hot_training_decision(
    image: np.ndarray,
) -> Tuple[PredictorDecision, Optional[int]]:
    levels = int(np.unique(image).size)
    if levels < 2:
        return PredictorDecision.NO_TRAINING_VARIATION, None
    if levels > _MAX_ONE_HOT_LEVELS:
        return PredictorDecision.TOO_MANY_LEVELS, levels
    return PredictorDecision.INCLUDED, levels


def _fit_and_score(
    task: PredictiveTask,
    n_classes: int,
    included: Tuple[DiagnosticPredictor, ...],
    images: dict,
    rows: np.ndarray,
    y: np.ndarray,
    validation: np.ndarray,
    seed: int,
) -> Optional[Tuple[object, Optional[PermutationImportance]]]:
    """Fit the model and baseline on training rows and score validation rows.

    ``None`` means a prediction or score was not a finite float64.
    """
    design = pd.DataFrame(
        {_key(item.position): images[item.position] for item in included},
        index=rows,
    )
    training_rows = np.flatnonzero(~validation)
    validation_rows = np.flatnonzero(validation)
    x_train = design.iloc[training_rows]
    x_valid = design.iloc[validation_rows]
    y_train = y[training_rows]
    y_valid = y[validation_rows]
    pipeline = Pipeline(
        [("preprocess", _preprocessor(included)), ("model", _estimator(task))]
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        pipeline.fit(x_train, y_train)
    if task.is_classification:
        baseline = DummyClassifier(strategy="prior").fit(x_train, y_train)
        evaluation = _classification_evaluation(
            task, n_classes, pipeline, baseline, x_valid, y_valid
        )
        scorer = _negative_log_loss
    else:
        baseline = DummyRegressor(strategy="mean").fit(x_train, y_train)
        evaluation = _regression_evaluation(pipeline, baseline, x_valid, y_valid)
        scorer = _r2_scorer
    if evaluation is None:
        return None
    if isinstance(evaluation, RegressionEvaluation) and evaluation.r2.model is None:
        return evaluation, None
    importance = _permutation_importance(
        pipeline, included, x_valid, y_valid, scorer, task, seed
    )
    if importance is None:
        return None
    return evaluation, importance


def _key(position: int) -> str:
    return f"column_{position}"


def _preprocessor(included: Tuple[DiagnosticPredictor, ...]) -> ColumnTransformer:
    numeric = [
        _key(item.position)
        for item in included
        if item.encoding is PredictorEncoding.STANDARDIZED
    ]
    one_hot = [
        _key(item.position)
        for item in included
        if item.encoding is PredictorEncoding.ONE_HOT
    ]
    transformers = []
    if numeric:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        (
                            "impute",
                            SimpleImputer(strategy="median", add_indicator=True),
                        ),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            )
        )
    if one_hot:
        transformers.append(
            ("levels", OneHotEncoder(handle_unknown="ignore"), one_hot)
        )
    return ColumnTransformer(transformers, remainder="drop", sparse_threshold=1.0)


def _estimator(task: PredictiveTask) -> object:
    if task.is_classification:
        return LogisticRegression(**dict(_LOGISTIC_PARAMETERS))
    return Ridge(**dict(_RIDGE_PARAMETERS))


def _classification_evaluation(
    task: PredictiveTask,
    n_classes: int,
    pipeline: Pipeline,
    baseline: DummyClassifier,
    x_valid: pd.DataFrame,
    y_valid: np.ndarray,
) -> Optional[ClassificationEvaluation]:
    expected = np.arange(n_classes)
    if not (
        np.array_equal(pipeline.classes_, expected)
        and np.array_equal(baseline.classes_, expected)
    ):
        raise ValueError("every target class must be in the training rows")
    model = pipeline.predict_proba(x_valid)
    prior = baseline.predict_proba(x_valid)
    if not (np.all(np.isfinite(model)) and np.all(np.isfinite(prior))):
        return None
    auc = (
        DiagnosticMetric.ROC_AUC
        if task is PredictiveTask.BINARY_CLASSIFICATION
        else DiagnosticMetric.MACRO_OVR_ROC_AUC
    )
    iterations = int(np.max(pipeline.named_steps["model"].n_iter_))
    return ClassificationEvaluation(
        roc_auc=MetricComparison(
            auc, _roc_auc(y_valid, model), _roc_auc(y_valid, prior)
        ),
        balanced_accuracy=MetricComparison(
            DiagnosticMetric.BALANCED_ACCURACY,
            _balanced_accuracy(y_valid, model),
            _balanced_accuracy(y_valid, prior),
        ),
        log_loss=MetricComparison(
            DiagnosticMetric.LOG_LOSS,
            _log_loss(y_valid, model),
            _log_loss(y_valid, prior),
        ),
        solver_converged=iterations < dict(_LOGISTIC_PARAMETERS)["max_iter"],
    )


def _regression_evaluation(
    pipeline: Pipeline,
    baseline: DummyRegressor,
    x_valid: pd.DataFrame,
    y_valid: np.ndarray,
) -> Optional[RegressionEvaluation]:
    model = np.asarray(pipeline.predict(x_valid), dtype=np.float64)
    mean = np.asarray(baseline.predict(x_valid), dtype=np.float64)
    scores = []
    for metric in (_r2, _mae, _rmse):
        pair = (metric(y_valid, model), metric(y_valid, mean))
        if any(value is not None and not math.isfinite(value) for value in pair):
            return None
        scores.append(pair)
    (r2_model, r2_mean), (mae_model, mae_mean), (rmse_model, rmse_mean) = scores
    return RegressionEvaluation(
        r2=MetricComparison(DiagnosticMetric.R2, r2_model, r2_mean),
        mae=MetricComparison(DiagnosticMetric.MAE, mae_model, mae_mean),
        rmse=MetricComparison(DiagnosticMetric.RMSE, rmse_model, rmse_mean),
    )


def _permutation_importance(
    pipeline: Pipeline,
    included: Tuple[DiagnosticPredictor, ...],
    x_valid: pd.DataFrame,
    y_valid: np.ndarray,
    scorer: Callable[[object, object, np.ndarray], Optional[float]],
    task: PredictiveTask,
    seed: int,
) -> Optional[PermutationImportance]:
    """Permute each original input column on the validation rows.

    The validation rows are encoded once. Every fitted transformation is
    row-wise and column-local: each encoded column is computed from one
    input column of the same row, with parameters fitted on training rows.
    Permuting an input column and then encoding therefore gives the same
    matrix as encoding and then moving the rows of every encoded column
    that input owns by that one order. A Numeric input owns its scaled
    value and its missing indicator, and a Boolean or Categorical input
    owns all its one-hot columns. No other column moves.
    """
    preprocess = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    encoded = preprocess.transform(x_valid)
    owned = _owned_columns(preprocess, included, encoded.shape[1])
    reference = scorer(model, encoded, y_valid)
    orders = _validation_permutations(encoded.shape[0], seed)
    decreases = np.empty((len(included), _PERMUTATION_REPEATS), dtype=np.float64)
    for index, columns in enumerate(owned):
        move = _block_mover(encoded, columns)
        for repeat, order in enumerate(orders):
            decreases[index, repeat] = reference - scorer(model, move(order), y_valid)
    if not np.all(np.isfinite(decreases)):
        return None
    metric = (
        DiagnosticMetric.LOG_LOSS if task.is_classification else DiagnosticMetric.R2
    )
    return PermutationImportance(
        metric=metric,
        n_repeats=_PERMUTATION_REPEATS,
        predictors=tuple(
            PredictorImportance(
                position=item.position,
                label=item.label,
                decreases=tuple(float(value) for value in row),
            )
            for item, row in zip(included, decreases)
        ),
    )


def _owned_columns(
    preprocess: ColumnTransformer,
    included: Tuple[DiagnosticPredictor, ...],
    width: int,
) -> Tuple[np.ndarray, ...]:
    """Return the encoded columns of each included input, in physical order.

    This reads the fixed layout ``_preprocessor`` builds. The numeric block
    is each scaled value in input order, then one missing indicator for
    each input that had missing training values, in input order. The
    one-hot block is each input's training levels, in input order. Every
    encoded column must belong to exactly one input.
    """
    owned = {}
    numeric = [i for i in included if i.encoding is PredictorEncoding.STANDARDIZED]
    if numeric:
        start = preprocess.output_indices_["numeric"].start
        imputer = preprocess.named_transformers_["numeric"].named_steps["impute"]
        indicated = imputer.indicator_.features_.tolist()
        for offset, item in enumerate(numeric):
            columns = [start + offset]
            if offset in indicated:
                columns.append(start + len(numeric) + indicated.index(offset))
            owned[item.position] = columns
    one_hot = [i for i in included if i.encoding is PredictorEncoding.ONE_HOT]
    if one_hot:
        start = preprocess.output_indices_["levels"].start
        levels = preprocess.named_transformers_["levels"].categories_
        for item, vocabulary in zip(one_hot, levels):
            owned[item.position] = list(range(start, start + len(vocabulary)))
            start += len(vocabulary)
    every = sorted(column for columns in owned.values() for column in columns)
    if every != list(range(width)):
        raise ValueError("every encoded column must belong to exactly one input")
    return tuple(np.asarray(owned[item.position], dtype=np.intp) for item in included)


def _validation_permutations(n_rows: int, seed: int) -> Tuple[np.ndarray, ...]:
    """Return one validation row order per repeat, shared by every input.

    One column seed is drawn from ``numpy.random.RandomState(seed)``. A
    ``RandomState`` with that seed then shuffles ``arange(n_rows)`` in
    place once per repeat, and each repeat applies that shuffle to the
    previous repeat's order. These are the orders TSK-034 used.
    ``RandomState`` streams do not change between NumPy releases.
    """
    column_seed = np.random.RandomState(seed).randint(
        np.iinfo(np.int32).max + 1, dtype=np.int64
    )
    generator = np.random.RandomState(column_seed)
    shuffle = np.arange(n_rows)
    order = np.arange(n_rows)
    orders = []
    for _ in range(_PERMUTATION_REPEATS):
        generator.shuffle(shuffle)
        order = order[shuffle]
        orders.append(order)
    return tuple(orders)


def _block_mover(
    encoded: object,
    columns: np.ndarray,
) -> Callable[[np.ndarray], object]:
    """Return a function that moves the rows of ``columns`` by one order.

    The other encoded columns keep their rows. A sparse matrix stays
    sparse: the moved and kept parts have disjoint columns, so their sum
    holds each value exactly.
    """
    if sparse.issparse(encoded):
        selected = np.zeros(encoded.shape[1], dtype=np.float64)
        selected[columns] = 1.0
        moved = encoded @ sparse.diags(selected)
        kept = encoded @ sparse.diags(1.0 - selected)
        return lambda order: kept + moved[order]

    def move(order: np.ndarray) -> np.ndarray:
        permuted = encoded.copy()
        permuted[:, columns] = encoded[np.ix_(order, columns)]
        return permuted

    return move


def _negative_log_loss(
    estimator: object, x_valid: object, y_valid: np.ndarray
) -> float:
    return -_log_loss(y_valid, estimator.predict_proba(x_valid))


def _r2_scorer(
    estimator: object, x_valid: object, y_valid: np.ndarray
) -> Optional[float]:
    # Permuting an input does not change the validation target, and R² was
    # already defined on it, so this is never None.
    return _r2(y_valid, np.asarray(estimator.predict(x_valid), dtype=np.float64))


def _roc_auc(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    """Binary ROC AUC, or the macro mean of one-versus-rest areas."""
    n_classes = probabilities.shape[1]
    if n_classes == 2:
        return _binary_auc(y_true == 1, probabilities[:, 1])
    areas = [
        _binary_auc(y_true == label, probabilities[:, label])
        for label in range(n_classes)
    ]
    return math.fsum(areas) / n_classes


def _binary_auc(positive: np.ndarray, scores: np.ndarray) -> float:
    """Mann–Whitney area under the ROC curve, with tied scores sharing ranks."""
    n_positive = int(np.count_nonzero(positive))
    n_negative = int(positive.size) - n_positive
    ranks = rankdata(scores)
    rank_sum = math.fsum(ranks[positive].tolist())
    return (rank_sum - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative)


def _balanced_accuracy(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    """Mean per-class recall of the most probable class.

    A probability tie predicts the first class in class order.
    """
    predicted = np.argmax(probabilities, axis=1)
    recalls = [
        float(np.mean(predicted[y_true == label] == label))
        for label in range(probabilities.shape[1])
    ]
    return math.fsum(recalls) / len(recalls)


def _log_loss(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    chosen = probabilities[np.arange(y_true.size), y_true]
    clipped = np.clip(chosen, _LOG_LOSS_FLOOR, 1.0)
    return float(-np.mean(np.log(clipped)))


def _r2(y_true: np.ndarray, predicted: np.ndarray) -> Optional[float]:
    """R² against the validation mean. ``None`` when that target is constant."""
    with np.errstate(over="ignore", invalid="ignore"):
        total = float(np.sum((y_true - np.mean(y_true)) ** 2))
        residual = float(np.sum((y_true - predicted) ** 2))
    if total == 0.0:
        return None
    if not (math.isfinite(total) and math.isfinite(residual)):
        return math.nan
    return 1.0 - residual / total


def _mae(y_true: np.ndarray, predicted: np.ndarray) -> float:
    with np.errstate(over="ignore", invalid="ignore"):
        return float(np.mean(np.abs(y_true - predicted)))


def _rmse(y_true: np.ndarray, predicted: np.ndarray) -> float:
    with np.errstate(over="ignore", invalid="ignore"):
        return float(np.sqrt(np.mean((y_true - predicted) ** 2)))
