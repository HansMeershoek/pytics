"""TSK-034: lightweight diagnostic model for an explicit target."""

from __future__ import annotations

import dataclasses
import math
import uuid
from enum import Enum

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import log_loss
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.compose import ColumnTransformer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from scipy import sparse

import pytics.analysis.dataset as dataset_module
import pytics.analysis.target_diagnostic_fit as fit_module
from pytics.analysis.boolean import BooleanDescriptiveAnalysis
from pytics.analysis.categorical import CategoricalDescriptiveAnalysis
from pytics.analysis.categorical import ObservedCategoryCount
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.target import TargetStatus
from pytics.analysis.target import build_target_summary
from pytics.analysis.target import project_target_analysis
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
from pytics.analysis.target_diagnostic import TargetDiagnosticAnalysis
from pytics.analysis.target_diagnostic import ValidationStrategy
from pytics.analysis.target_diagnostic import copy_target_diagnostic
from pytics.analysis.target_diagnostic import predictive_task_for
from pytics.analysis.target_diagnostic import semantic_predictor_decision
from pytics.analysis.target_diagnostic_fit import analyze_target_diagnostic
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus


def _binary_frame(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    signal = rng.normal(size=n)
    return pd.DataFrame(
        {
            "y": pd.Series(signal + 0.5 * rng.normal(size=n) > 0, dtype="boolean"),
            "signal": signal,
            "noise": rng.normal(size=n),
            "group": pd.Series(rng.choice(["a", "b", "c"], size=n), dtype="category"),
            "flag": pd.Series(rng.random(n) < 0.4, dtype="boolean"),
        }
    )


def _multiclass_frame(n: int = 300, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    signal = rng.normal(size=n)
    label = np.where(signal > 0.5, "high", np.where(signal < -0.5, "low", "mid"))
    return pd.DataFrame(
        {
            "signal": signal + 0.3 * rng.normal(size=n),
            "noise": rng.normal(size=n),
            "y": pd.Series(label, dtype="category"),
        }
    )


def _regression_frame(n: int = 300, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    signal = rng.normal(size=n)
    group = rng.choice(["a", "b"], size=n)
    return pd.DataFrame(
        {
            "signal": signal,
            "group": pd.Series(group, dtype="category"),
            "y": 3.0 * signal + np.where(group == "a", 1.0, -1.0) + rng.normal(size=n),
        }
    )


def _diagnostic(frame: pd.DataFrame, target: object) -> TargetDiagnosticAnalysis:
    diagnostic = analyze_dataframe(frame, target=target).target_diagnostic
    assert diagnostic is not None
    return diagnostic


def _decisions(diagnostic: TargetDiagnosticAnalysis) -> dict:
    return {item.label: item.decision for item in diagnostic.predictors}


class _Spy:
    """Record what the diagnostic pipeline was fitted on and asked to predict."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.fit_index: list = []
        self.fit_y: list = []
        self.pipelines: list = []
        self.predict_index: list = []
        original_fit = Pipeline.fit
        original_proba = Pipeline.predict_proba
        original_predict = Pipeline.predict
        spy = self

        def fit(self, X, y=None, **params):  # type: ignore[no-untyped-def]
            if "model" in self.named_steps:
                spy.fit_index.append(X.index.to_numpy().copy())
                spy.fit_y.append(np.asarray(y).copy())
                spy.pipelines.append(self)
            return original_fit(self, X, y, **params)

        def predict_proba(self, X, **params):  # type: ignore[no-untyped-def]
            spy.predict_index.append(X.index.to_numpy().copy())
            return original_proba(self, X, **params)

        def predict(self, X, **params):  # type: ignore[no-untyped-def]
            spy.predict_index.append(X.index.to_numpy().copy())
            return original_predict(self, X, **params)

        monkeypatch.setattr(Pipeline, "fit", fit)
        monkeypatch.setattr(Pipeline, "predict_proba", predict_proba)
        monkeypatch.setattr(Pipeline, "predict", predict)


def test_semantic_type_and_predictive_task_are_separate_mappings() -> None:
    assert predictive_task_for(SemanticType.NUMERIC, None) is PredictiveTask.REGRESSION
    for semantic_type in (SemanticType.BOOLEAN, SemanticType.CATEGORICAL):
        assert predictive_task_for(semantic_type, 2) is (
            PredictiveTask.BINARY_CLASSIFICATION
        )
        assert predictive_task_for(semantic_type, 1) is None
        assert predictive_task_for(semantic_type, 0) is None
    assert predictive_task_for(SemanticType.CATEGORICAL, 3) is (
        PredictiveTask.MULTICLASS_CLASSIFICATION
    )
    for semantic_type in set(SemanticType) - {
        SemanticType.NUMERIC,
        SemanticType.BOOLEAN,
        SemanticType.CATEGORICAL,
    }:
        assert predictive_task_for(semantic_type, 2) is None
    assert predictive_task_for(None, None) is None
    with pytest.raises(ValueError, match="n_observed_classes"):
        predictive_task_for(SemanticType.BOOLEAN, None)


def test_boolean_target_is_binary_classification() -> None:
    frame = _binary_frame()
    analysis = analyze_dataframe(frame, target="y")
    diagnostic = analysis.target_diagnostic
    assert analysis.target_analysis.selected_type is SemanticType.BOOLEAN
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    assert diagnostic.task is PredictiveTask.BINARY_CLASSIFICATION
    design = diagnostic.design
    assert design.validation is ValidationStrategy.STRATIFIED_HOLDOUT
    assert design.estimator is DiagnosticEstimator.LOGISTIC_REGRESSION
    assert design.baseline is DiagnosticEstimator.PRIOR_CLASSIFIER
    assert design.importance_metric is DiagnosticMetric.LOG_LOSS
    assert dict(design.estimator_parameters) == {
        "C": 1.0,
        "solver": "lbfgs",
        "max_iter": 1000,
    }
    assert design.validation_fraction == 0.25
    assert design.random_seed == 0
    assert design.permutation_repeats == 5
    assert design.library_version
    assert [item.value for item in diagnostic.population.classes] == [False, True]
    assert isinstance(diagnostic.evaluation, ClassificationEvaluation)
    assert diagnostic.evaluation.roc_auc.metric is DiagnosticMetric.ROC_AUC
    assert diagnostic.evaluation.solver_converged is True


def test_categorical_targets_map_by_observed_class_count() -> None:
    rng = np.random.default_rng(4)
    n = 200
    signal = rng.normal(size=n)
    two = pd.Categorical(
        np.where(signal > 0, "yes", "no"), categories=["yes", "unused", "no"]
    )
    frame = pd.DataFrame({"signal": signal, "y": two})
    binary = _diagnostic(frame, "y")
    assert binary.task is PredictiveTask.BINARY_CLASSIFICATION
    assert binary.evaluation.roc_auc.metric is DiagnosticMetric.ROC_AUC
    assert [item.value for item in binary.population.classes] == ["yes", "no"]
    multiclass = _diagnostic(_multiclass_frame(), "y")
    assert multiclass.task is PredictiveTask.MULTICLASS_CLASSIFICATION
    assert multiclass.evaluation.roc_auc.metric is DiagnosticMetric.MACRO_OVR_ROC_AUC
    assert [item.value for item in multiclass.population.classes] == [
        "high",
        "low",
        "mid",
    ]


def test_numeric_targets_are_regression_including_zero_one() -> None:
    regression = _diagnostic(_regression_frame(), "y")
    assert regression.task is PredictiveTask.REGRESSION
    assert regression.design.validation is ValidationStrategy.RANDOM_HOLDOUT
    assert regression.design.estimator is DiagnosticEstimator.RIDGE
    assert regression.design.baseline is DiagnosticEstimator.MEAN_REGRESSOR
    assert regression.design.importance_metric is DiagnosticMetric.R2
    assert dict(regression.design.estimator_parameters) == {
        "alpha": 1.0,
        "solver": "auto",
    }
    assert regression.population.classes == ()
    rng = np.random.default_rng(5)
    signal = rng.normal(size=120)
    frame = pd.DataFrame({"signal": signal, "y": (signal > 0).astype(np.int64)})
    analysis = analyze_dataframe(frame, target="y")
    assert analysis.target_analysis.selected_type is SemanticType.NUMERIC
    zero_one = analysis.target_diagnostic
    assert zero_one.status is DiagnosticStatus.AVAILABLE
    assert zero_one.task is PredictiveTask.REGRESSION
    assert zero_one.design.estimator is DiagnosticEstimator.RIDGE
    assert analysis.columns[1].boolean_analysis is None


def test_unsupported_and_ineligible_targets_have_no_task() -> None:
    n = 40
    frame = pd.DataFrame(
        {
            "when": pd.date_range("2020-01-01", periods=n),
            "code": pd.Series(
                [str(uuid.UUID(int=index + 1)) for index in range(n)], dtype="string"
            ),
            "words": pd.Series(["red", "blue"] * (n // 2), dtype="string"),
            "amount": np.arange(n, dtype=np.float64),
        }
    )
    expected = {
        "when": TargetStatus.UNSUPPORTED,
        "code": TargetStatus.INELIGIBLE,
        "words": TargetStatus.UNRESOLVED,
    }
    for label, target_status in expected.items():
        analysis = analyze_dataframe(frame, target=label)
        assert analysis.target_analysis.status is target_status
        diagnostic = analysis.target_diagnostic
        assert diagnostic.status is DiagnosticStatus.TARGET_TYPE_UNSUPPORTED
        assert diagnostic.task is None
        assert diagnostic.design is None
        assert diagnostic.population is None
        assert diagnostic.predictors == ()
        assert analysis.target_analysis.relationships


def test_repeated_runs_are_identical_and_seed_is_retained() -> None:
    frame = _binary_frame()
    first = analyze_dataframe(frame, target="y")
    second = analyze_dataframe(frame, target="y")
    assert first.target_diagnostic == second.target_diagnostic
    reseeded = analyze_target_diagnostic(
        frame, first.columns, first.target_analysis, first.target_leakage, seed=7
    )
    assert reseeded.design.random_seed == 7
    assert (
        reseeded.population.classes != first.target_diagnostic.population.classes
        or (reseeded.evaluation != first.target_diagnostic.evaluation)
    )
    with pytest.raises(ValueError, match="seed"):
        analyze_target_diagnostic(
            frame, first.columns, first.target_analysis, first.target_leakage, seed=-1
        )
    with pytest.raises(ValueError, match="seed"):
        analyze_target_diagnostic(
            frame,
            first.columns,
            first.target_analysis,
            first.target_leakage,
            seed=True,  # type: ignore[arg-type]
        )


def test_validation_rows_are_never_fitted(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = _binary_frame()
    frame.loc[[3, 17, 40], "y"] = pd.NA
    spy = _Spy(monkeypatch)
    diagnostic = _diagnostic(frame, "y")
    assert len(spy.fit_index) == 1
    fitted = set(spy.fit_index[0].tolist())
    predicted = set(np.concatenate(spy.predict_index).tolist())
    modeling = set(np.flatnonzero(frame["y"].notna().to_numpy()).tolist())
    assert fitted.isdisjoint(predicted)
    assert fitted | predicted == modeling
    assert {3, 17, 40}.isdisjoint(fitted | predicted)
    population = diagnostic.population
    assert population.n_target_missing == 3
    assert population.n_target_non_missing == 297
    assert population.n_modeling == 297
    assert population.n_training == len(fitted)
    assert population.n_validation == len(predicted)


def test_split_sizes_follow_an_independent_rule() -> None:
    rng = np.random.default_rng(6)
    counts = {"a": 2, "b": 3, "c": 5, "d": 9, "e": 21}
    labels = np.repeat(list(counts), list(counts.values()))
    rng.shuffle(labels)
    frame = pd.DataFrame(
        {
            "x": rng.normal(size=labels.size),
            "y": pd.Series(labels, dtype="category"),
        }
    )
    diagnostic = _diagnostic(frame, "y")
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    for item in diagnostic.population.classes:
        n_class = counts[item.value]
        expected = min(max(math.ceil(n_class / 4), 1), n_class - 1)
        assert item.n_validation == expected
        assert item.n_training == n_class - expected
        assert item.n_training >= 1 and item.n_validation >= 1
    regression = _diagnostic(_regression_frame(n=101), "y")
    assert regression.population.n_validation == math.ceil(101 / 4)
    assert regression.population.n_training == 101 - math.ceil(101 / 4)


def test_target_side_statuses_are_decided_before_any_split() -> None:
    small = _binary_frame(n=19)
    diagnostic = _diagnostic(small, "y")
    assert diagnostic.status is DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION
    assert diagnostic.task is PredictiveTask.BINARY_CLASSIFICATION
    assert diagnostic.design is not None
    assert not diagnostic.population.is_split
    assert diagnostic.predictors == ()
    assert _diagnostic(_binary_frame(n=20), "y").status is DiagnosticStatus.AVAILABLE

    singleton = pd.DataFrame(
        {
            "x": np.arange(30, dtype=np.float64),
            "y": pd.Series(["a"] * 15 + ["b"] * 14 + ["c"], dtype="category"),
        }
    )
    split = _diagnostic(singleton, "y")
    assert split.status is DiagnosticStatus.VALIDATION_SPLIT_IMPOSSIBLE
    assert split.task is PredictiveTask.MULTICLASS_CLASSIFICATION

    many = pd.DataFrame(
        {
            "x": np.arange(202, dtype=np.float64),
            "y": pd.Series(
                [f"k{index // 2}" for index in range(202)], dtype="category"
            ),
        }
    )
    assert _diagnostic(many, "y").status is DiagnosticStatus.TOO_MANY_TARGET_CLASSES

    flat = pd.DataFrame(
        {
            "x": np.arange(25, dtype=np.float64),
            "y": [5.0] * 24 + [np.inf],
        }
    )
    flat_diagnostic = _diagnostic(flat, "y")
    assert flat_diagnostic.status is DiagnosticStatus.INSUFFICIENT_TARGET_VARIATION
    assert flat_diagnostic.population.n_target_non_finite == 1
    assert flat_diagnostic.population.n_modeling == 24


def test_one_observed_class_declines_without_fitting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _binary_frame()
    analysis = analyze_dataframe(frame, target="y")
    target = analysis.target_analysis
    one_class = dataclasses.replace(
        target,
        boolean_facts=BooleanDescriptiveAnalysis(true_count=300, false_count=0),
    )
    categorical = analyze_dataframe(_multiclass_frame(), target="y")
    single_level = dataclasses.replace(
        categorical.target_analysis,
        categorical_facts=CategoricalDescriptiveAnalysis(
            n_non_missing=300,
            ordered=False,
            levels=(ObservedCategoryCount(value="high", count=300),),
        ),
    )
    monkeypatch.setattr(Pipeline, "fit", _fail)
    diagnostic = analyze_target_diagnostic(
        frame, analysis.columns, one_class, analysis.target_leakage
    )
    assert diagnostic.status is DiagnosticStatus.INSUFFICIENT_TARGET_CLASSES
    assert diagnostic.task is None and diagnostic.design is None
    assert diagnostic.population.n_modeling == 300
    declined = analyze_target_diagnostic(
        _multiclass_frame(),
        categorical.columns,
        single_level,
        categorical.target_leakage,
    )
    assert declined.status is DiagnosticStatus.INSUFFICIENT_TARGET_CLASSES


def test_missing_and_non_finite_predictor_values_are_internal_preprocessing() -> None:
    frame = _regression_frame()
    frame.loc[::7, "signal"] = np.nan
    frame.loc[5, "signal"] = np.inf
    frame.loc[::11, "group"] = np.nan
    original = frame.copy(deep=True)
    diagnostic = _diagnostic(frame, "y")
    pd.testing.assert_frame_equal(frame, original)
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    by_label = {item.label: item for item in diagnostic.predictors}
    assert by_label["signal"].decision is PredictorDecision.INCLUDED
    assert by_label["signal"].encoding is PredictorEncoding.STANDARDIZED
    assert by_label["signal"].n_training_levels is None
    assert by_label["group"].encoding is PredictorEncoding.ONE_HOT
    assert by_label["group"].n_training_levels == 3


def test_boolean_predictor_keeps_true_false_and_missing_levels() -> None:
    frame = _binary_frame()
    frame.loc[::5, "flag"] = pd.NA
    diagnostic = _diagnostic(frame, "y")
    flag = next(item for item in diagnostic.predictors if item.label == "flag")
    assert flag.selected_type is SemanticType.BOOLEAN
    assert flag.encoding is PredictorEncoding.ONE_HOT
    assert flag.n_training_levels == 3


def test_learned_preprocessing_is_fitted_on_training_rows_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rng = np.random.default_rng(8)
    n = 240
    amount = rng.lognormal(size=n)
    amount[::6] = np.nan
    levels = [f"rare{index}" for index in range(80)] + ["common"] * (n - 80)
    rng.shuffle(levels)
    frame = pd.DataFrame(
        {
            "y": pd.Series(rng.random(n) < 0.4, dtype="boolean"),
            "amount": amount,
            "code": pd.Series(levels, dtype="category"),
        }
    )
    spy = _Spy(monkeypatch)
    diagnostic = _diagnostic(frame, "y")
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    training = spy.fit_index[0]
    validation = np.setdiff1d(np.arange(n), training)
    preprocess = spy.pipelines[0].named_steps["preprocess"]
    numeric = preprocess.named_transformers_["numeric"]
    encoder = preprocess.named_transformers_["levels"]

    training_amount = amount[training]
    training_median = np.nanmedian(training_amount)
    assert training_median != np.nanmedian(amount)
    assert numeric.named_steps["impute"].statistics_[0] == training_median
    imputed = np.where(np.isnan(training_amount), training_median, training_amount)
    assert numeric.named_steps["scale"].mean_[0] == pytest.approx(np.mean(imputed))
    assert numeric.named_steps["scale"].mean_[0] != pytest.approx(
        np.mean(np.where(np.isnan(amount), np.nanmedian(amount), amount))
    )

    codes = frame["code"].cat.codes.to_numpy()
    training_codes = set(codes[training].tolist())
    validation_only = set(codes[validation].tolist()) - training_codes
    assert validation_only
    assert set(encoder.categories_[0].tolist()) == training_codes
    code = next(item for item in diagnostic.predictors if item.label == "code")
    assert code.n_training_levels == len(training_codes)


def test_semantic_predictor_exclusions_are_recorded() -> None:
    n = 60
    rng = np.random.default_rng(9)
    signal = rng.normal(size=n)
    frame = pd.DataFrame(
        {
            "id": pd.Series(
                [str(uuid.UUID(int=index + 1)) for index in range(n)], dtype="string"
            ),
            "empty": np.full(n, np.nan),
            "constant": np.ones(n),
            "when": pd.date_range("2020-01-01", periods=n),
            "span": pd.to_timedelta(np.arange(n), unit="h"),
            "words": pd.Series(rng.choice(["red", "blue"], size=n), dtype="string"),
            "y": signal + rng.normal(size=n),
            "signal": signal,
        }
    )
    diagnostic = _diagnostic(frame, "y")
    assert _decisions(diagnostic) == {
        "id": PredictorDecision.IDENTIFIER,
        "empty": PredictorDecision.EMPTY,
        "constant": PredictorDecision.CONSTANT,
        "when": PredictorDecision.UNSUPPORTED_TYPE,
        "span": PredictorDecision.UNSUPPORTED_TYPE,
        "words": PredictorDecision.UNRESOLVED,
        "signal": PredictorDecision.INCLUDED,
    }
    assert [item.position for item in diagnostic.predictors] == [0, 1, 2, 3, 4, 5, 7]
    assert all(item.position != 6 for item in diagnostic.predictors)
    assert semantic_predictor_decision(SemanticType.TEXT) is (
        PredictorDecision.UNSUPPORTED_TYPE
    )
    for semantic_type in (
        SemanticType.NUMERIC,
        SemanticType.BOOLEAN,
        SemanticType.CATEGORICAL,
    ):
        assert semantic_predictor_decision(semantic_type) is None
    assert [item.position for item in diagnostic.importance.predictors] == [7]


def test_exact_copies_of_the_target_are_excluded() -> None:
    frame = _regression_frame()
    frame["copy"] = frame["y"]
    frame["almost"] = frame["y"]
    frame.loc[0, "almost"] = np.nan
    numeric = _decisions(_diagnostic(frame, "y"))
    assert numeric["copy"] is PredictorDecision.IDENTICAL_TO_TARGET
    assert numeric["almost"] is PredictorDecision.INCLUDED

    boolean = _binary_frame()
    boolean["copy"] = boolean["y"].copy()
    assert _decisions(_diagnostic(boolean, "y"))["copy"] is (
        PredictorDecision.IDENTICAL_TO_TARGET
    )

    categorical = _multiclass_frame()
    categorical["copy"] = pd.Categorical(
        categorical["y"].astype(str), categories=["mid", "low", "high", "spare"]
    )
    categorical["relabeled"] = categorical["y"].cat.rename_categories(["H", "L", "M"])
    decisions = _decisions(_diagnostic(categorical, "y"))
    assert decisions["copy"] is PredictorDecision.IDENTICAL_TO_TARGET
    assert decisions["relabeled"] is PredictorDecision.INCLUDED


def test_no_eligible_predictors_before_and_after_the_split() -> None:
    n = 40
    frame = pd.DataFrame(
        {
            "id": pd.Series(
                [str(uuid.UUID(int=index + 1)) for index in range(n)], dtype="string"
            ),
            "y": np.arange(n, dtype=np.float64),
        }
    )
    before = _diagnostic(frame, "y")
    assert before.status is DiagnosticStatus.NO_ELIGIBLE_PREDICTORS
    assert not before.population.is_split
    assert _decisions(before) == {"id": PredictorDecision.IDENTIFIER}

    rng = np.random.default_rng(10)
    target = rng.normal(size=n + 10)
    target[n:] = np.nan
    sparse = np.full(n + 10, np.nan)
    sparse[n:] = rng.normal(size=10)
    after = _diagnostic(pd.DataFrame({"y": target, "sparse": sparse}), "y")
    assert after.status is DiagnosticStatus.NO_ELIGIBLE_PREDICTORS
    assert after.population.is_split
    assert _decisions(after) == {"sparse": PredictorDecision.NO_TRAINING_VARIATION}
    assert after.evaluation is None and after.importance is None

    alone = _diagnostic(pd.DataFrame({"y": rng.normal(size=n)}), "y")
    assert alone.status is DiagnosticStatus.NO_ELIGIBLE_PREDICTORS
    assert alone.predictors == ()


def test_wide_and_unscalable_predictors_are_excluded_with_a_reason() -> None:
    rng = np.random.default_rng(11)
    n = 2800
    signal = rng.normal(size=n)
    frame = pd.DataFrame(
        {
            "y": signal + rng.normal(size=n),
            "signal": signal,
            "wide": pd.Series(
                [f"k{index // 2}" for index in range(n)], dtype="category"
            ),
            "huge": np.where(rng.random(n) < 0.5, -1e300, 1e300),
        }
    )
    diagnostic = _diagnostic(frame, "y")
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    by_label = {item.label: item for item in diagnostic.predictors}
    assert by_label["wide"].decision is PredictorDecision.TOO_MANY_LEVELS
    assert by_label["wide"].n_training_levels > 1000
    assert by_label["huge"].decision is PredictorDecision.SCALE_NOT_FINITE
    assert by_label["signal"].decision is PredictorDecision.INCLUDED


def test_classification_metrics_match_an_independent_calculation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for frame, labels in (
        (_binary_frame(), None),
        (_multiclass_frame(), ["high", "low", "mid"]),
    ):
        spy = _Spy(monkeypatch)
        diagnostic = _diagnostic(frame, "y")
        pipeline = spy.pipelines[-1]
        training = spy.fit_index[-1]
        validation = np.setdiff1d(np.arange(len(frame)), training)
        if labels is None:
            y_all = frame["y"].astype(bool).to_numpy().astype(int)
        else:
            y_all = pd.Categorical(frame["y"], categories=labels).codes
        y_valid = y_all[validation]
        y_train = y_all[training]
        probabilities = _validation_probabilities(pipeline, frame, validation)
        evaluation = diagnostic.evaluation
        if labels is None:
            expected_auc = roc_auc_score(y_valid, probabilities[:, 1])
        else:
            expected_auc = roc_auc_score(
                y_valid, probabilities, multi_class="ovr", average="macro"
            )
        assert evaluation.roc_auc.model == pytest.approx(expected_auc, abs=1e-12)
        assert evaluation.balanced_accuracy.model == pytest.approx(
            balanced_accuracy_score(y_valid, probabilities.argmax(axis=1)), abs=1e-12
        )
        assert evaluation.log_loss.model == pytest.approx(
            log_loss(y_valid, probabilities), rel=1e-9
        )
        n_classes = probabilities.shape[1]
        prior = np.bincount(y_train, minlength=n_classes) / y_train.size
        assert evaluation.roc_auc.baseline == 0.5
        assert evaluation.balanced_accuracy.baseline == pytest.approx(1 / n_classes)
        assert evaluation.log_loss.baseline == pytest.approx(
            -np.mean(np.log(prior[y_valid]))
        )
        assert evaluation.log_loss.improvement == pytest.approx(
            evaluation.log_loss.baseline - evaluation.log_loss.model
        )
        assert evaluation.roc_auc.improvement == pytest.approx(
            evaluation.roc_auc.model - 0.5
        )


def _validation_probabilities(
    pipeline: Pipeline, frame: pd.DataFrame, validation: np.ndarray
) -> np.ndarray:
    design = _design_frame(pipeline, frame, validation)
    return pipeline.predict_proba(design)


def _design_frame(
    pipeline: Pipeline, frame: pd.DataFrame, rows: np.ndarray
) -> pd.DataFrame:
    """Rebuild the model input for ``rows`` from the source frame."""
    columns = {}
    for name in pipeline.named_steps["preprocess"].feature_names_in_:
        position = int(name.split("_")[1])
        series = frame.iloc[:, position]
        if isinstance(series.dtype, pd.CategoricalDtype):
            values = series.cat.codes.to_numpy().astype(np.int64)
        elif pd.api.types.is_bool_dtype(series.dtype):
            values = np.where(
                series.notna().to_numpy(),
                series.fillna(False).to_numpy().astype(int),
                -1,
            ).astype(np.int64)
        else:
            values = series.to_numpy(dtype=np.float64, na_value=np.nan)
            values = np.where(np.isfinite(values), values, np.nan)
        columns[name] = values[rows]
    return pd.DataFrame(columns, index=rows)


def test_regression_metrics_match_an_independent_calculation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _regression_frame()
    spy = _Spy(monkeypatch)
    diagnostic = _diagnostic(frame, "y")
    pipeline = spy.pipelines[0]
    training = spy.fit_index[0]
    validation = np.setdiff1d(np.arange(len(frame)), training)
    y = frame["y"].to_numpy()
    predicted = pipeline.predict(_design_frame(pipeline, frame, validation))
    mean = np.full(validation.size, np.mean(y[training]))
    evaluation = diagnostic.evaluation
    assert evaluation.r2.model == pytest.approx(r2_score(y[validation], predicted))
    assert evaluation.mae.model == pytest.approx(
        mean_absolute_error(y[validation], predicted)
    )
    assert evaluation.rmse.model == pytest.approx(
        math.sqrt(mean_squared_error(y[validation], predicted))
    )
    assert evaluation.r2.baseline == pytest.approx(r2_score(y[validation], mean))
    assert evaluation.mae.baseline == pytest.approx(
        mean_absolute_error(y[validation], mean)
    )
    assert evaluation.rmse.baseline == pytest.approx(
        math.sqrt(mean_squared_error(y[validation], mean))
    )
    assert evaluation.mae.improvement == pytest.approx(
        evaluation.mae.baseline - evaluation.mae.model
    )


def test_negative_r2_is_retained() -> None:
    rng = np.random.default_rng(0)
    frame = pd.DataFrame({"y": rng.normal(size=24), "x": rng.normal(size=24)})
    evaluation = _diagnostic(frame, "y").evaluation
    assert evaluation.r2.model < 0.0
    assert evaluation.r2.baseline < 0.0
    assert evaluation.r2.improvement == pytest.approx(
        evaluation.r2.model - evaluation.r2.baseline
    )


def test_r2_and_importance_are_undefined_for_a_constant_validation_target() -> None:
    frame = pd.DataFrame(
        {"y": [0.0] * 23 + [1.0], "x": np.arange(24, dtype=np.float64) % 5}
    )
    diagnostic = _diagnostic(frame, "y")
    assert diagnostic.status is DiagnosticStatus.AVAILABLE
    assert diagnostic.evaluation.r2.model is None
    assert diagnostic.evaluation.r2.baseline is None
    assert diagnostic.evaluation.r2.improvement is None
    assert diagnostic.evaluation.mae.model is not None
    assert diagnostic.importance is None


def test_unrepresentable_scores_are_a_numerical_failure() -> None:
    rng = np.random.default_rng(12)
    n = 80
    frame = pd.DataFrame(
        {
            "x": rng.normal(size=n),
            "y": np.where(rng.random(n) < 0.5, -1e200, 1e200),
        }
    )
    diagnostic = _diagnostic(frame, "y")
    assert diagnostic.status is DiagnosticStatus.NUMERICAL_FAILURE
    assert diagnostic.population.is_split
    assert diagnostic.included_predictors
    assert diagnostic.evaluation is None and diagnostic.importance is None


def test_permutation_importance_is_held_out_and_column_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _binary_frame()
    spy = _Spy(monkeypatch)
    encoded_index: list = []
    scored_rows: list = []
    original_transform = ColumnTransformer.transform
    original_proba = LogisticRegression.predict_proba

    def transform(self, X, **params):  # type: ignore[no-untyped-def]
        encoded_index.append(X.index.to_numpy().copy())
        return original_transform(self, X, **params)

    def predict_proba(self, X):  # type: ignore[no-untyped-def]
        scored_rows.append(X.shape[0])
        return original_proba(self, X)

    monkeypatch.setattr(ColumnTransformer, "transform", transform)
    monkeypatch.setattr(LogisticRegression, "predict_proba", predict_proba)
    diagnostic = _diagnostic(frame, "y")
    training = set(spy.fit_index[0].tolist())
    assert len(scored_rows) == 1 + 1 + 4 * 5
    assert set(scored_rows) == {diagnostic.population.n_validation}
    assert encoded_index
    for index in encoded_index:
        assert training.isdisjoint(index.tolist())
        assert len(index) == diagnostic.population.n_validation
    importance = diagnostic.importance
    assert importance.metric is DiagnosticMetric.LOG_LOSS
    assert importance.n_repeats == 5
    assert [item.label for item in importance.predictors] == [
        "signal",
        "noise",
        "group",
        "flag",
    ]
    by_label = {item.label: item for item in importance.predictors}
    assert len(by_label["group"].decreases) == 5
    assert by_label["signal"].mean > 0.5
    assert by_label["signal"].mean > 20 * abs(by_label["noise"].mean)
    assert by_label["noise"].mean < 0.0
    assert any(value < 0.0 for value in by_label["noise"].decreases)
    values = by_label["signal"].decreases
    assert by_label["signal"].mean == pytest.approx(np.mean(values))
    assert by_label["signal"].standard_deviation == pytest.approx(np.std(values))


def test_regression_importance_uses_r2_and_finds_the_signal() -> None:
    importance = _diagnostic(_regression_frame(), "y").importance
    assert importance.metric is DiagnosticMetric.R2
    by_label = {item.label: item for item in importance.predictors}
    assert by_label["signal"].mean > by_label["group"].mean > 0.0


def test_diagnostic_does_not_change_target_or_relationship_truth() -> None:
    frame = _binary_frame()
    plain = analyze_dataframe(frame)
    targeted = analyze_dataframe(frame, target="y")
    assert targeted.columns == plain.columns
    assert targeted.relationship_analysis == plain.relationship_analysis
    for before, after in zip(
        plain.relationship_analysis.relationships,
        targeted.relationship_analysis.relationships,
    ):
        assert before == after
    projected = project_target_analysis(
        targeted.columns,
        targeted.relationship_analysis.relationships,
        position=0,
        n_rows=targeted.n_rows,
    )
    assert projected == targeted.target_analysis
    positions = [link.other_position for link in targeted.target_analysis.relationships]
    assert positions == sorted(positions)

    small = analyze_dataframe(_binary_frame(n=10), target="group")
    assert small.target_diagnostic.status is (
        DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION
    )
    assert small.target_analysis.status is TargetStatus.SUPPORTED
    assert (
        small.target_analysis.categorical_facts is small.columns[3].categorical_analysis
    )


def test_dataset_attachment_rejects_an_inconsistent_diagnostic() -> None:
    analysis = analyze_dataframe(_binary_frame(n=12), target="y")
    diagnostic = analysis.target_diagnostic
    fields = {
        field.name: getattr(analysis, field.name)
        for field in dataclasses.fields(DatasetAnalysis)
    }
    with pytest.raises(ValueError, match="requires its diagnostic"):
        DatasetAnalysis(**{**fields, "target_diagnostic": None})
    with pytest.raises(ValueError, match="requires target analysis"):
        DatasetAnalysis(**{**fields, "target_analysis": None})
    with pytest.raises(TypeError, match="target_diagnostic"):
        DatasetAnalysis(**{**fields, "target_diagnostic": "model"})
    with pytest.raises(ValueError, match="name the analyzed target"):
        DatasetAnalysis(
            **{
                **fields,
                "target_diagnostic": dataclasses.replace(diagnostic, target_position=2),
            }
        )
    with pytest.raises(ValueError, match="task must follow"):
        DatasetAnalysis(
            **{
                **fields,
                "target_diagnostic": dataclasses.replace(
                    diagnostic, task=PredictiveTask.MULTICLASS_CLASSIFICATION
                ),
            }
        )
    population = diagnostic.population
    with pytest.raises(ValueError, match="missing rows"):
        DatasetAnalysis(
            **{
                **fields,
                "target_diagnostic": dataclasses.replace(
                    diagnostic,
                    population=dataclasses.replace(
                        population,
                        n_target_missing=1,
                        n_modeling=population.n_modeling - 1,
                    ),
                ),
            }
        )
    with pytest.raises(ValueError, match="supported target is not"):
        DatasetAnalysis(
            **{
                **fields,
                "target_diagnostic": TargetDiagnosticAnalysis(
                    target_position=0,
                    status=DiagnosticStatus.TARGET_TYPE_UNSUPPORTED,
                ),
            }
        )
    full = analyze_dataframe(_binary_frame(), target="y")
    full_fields = {
        field.name: getattr(full, field.name)
        for field in dataclasses.fields(DatasetAnalysis)
    }
    retained = full.target_diagnostic
    renamed = dataclasses.replace(retained.predictors[0], label="other")
    with pytest.raises(ValueError, match="must be its column"):
        DatasetAnalysis(
            **{
                **full_fields,
                "target_diagnostic": dataclasses.replace(
                    retained,
                    predictors=(renamed,) + retained.predictors[1:],
                    importance=dataclasses.replace(
                        retained.importance,
                        predictors=(
                            dataclasses.replace(
                                retained.importance.predictors[0], label="other"
                            ),
                        )
                        + retained.importance.predictors[1:],
                    ),
                ),
            }
        )
    with pytest.raises(ValueError, match="every other column"):
        DatasetAnalysis(
            **{
                **full_fields,
                "target_diagnostic": dataclasses.replace(
                    retained,
                    predictors=retained.predictors[:-1],
                    importance=dataclasses.replace(
                        retained.importance,
                        predictors=retained.importance.predictors[:-1],
                    ),
                ),
            }
        )
    population = retained.population
    swapped = (
        dataclasses.replace(population.classes[0], value=True),
        dataclasses.replace(population.classes[1], value=False),
    )
    with pytest.raises(ValueError, match="observed target classes"):
        DatasetAnalysis(
            **{
                **full_fields,
                "target_diagnostic": dataclasses.replace(
                    retained,
                    population=dataclasses.replace(population, classes=swapped),
                ),
            }
        )


def test_result_records_reject_inconsistent_values() -> None:
    with pytest.raises(ValueError, match="only R²"):
        MetricComparison(DiagnosticMetric.LOG_LOSS, None, None)
    with pytest.raises(ValueError, match="defined together"):
        MetricComparison(DiagnosticMetric.R2, 0.5, None)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        MetricComparison(DiagnosticMetric.ROC_AUC, 1.5, 0.5)
    with pytest.raises(ValueError, match="cannot exceed 1"):
        MetricComparison(DiagnosticMetric.R2, 1.5, 0.0)
    with pytest.raises(ValueError, match="cannot be negative"):
        MetricComparison(DiagnosticMetric.RMSE, -1.0, 1.0)
    with pytest.raises(ValueError, match="finite float"):
        MetricComparison(DiagnosticMetric.MAE, math.nan, 1.0)
    assert MetricComparison(DiagnosticMetric.R2, -3.0, -0.1).improvement == (
        pytest.approx(-2.9)
    )
    with pytest.raises(ValueError, match="finite float"):
        PredictorImportance(position=0, label="x", decreases=(math.inf,))
    with pytest.raises(ValueError, match="non-empty"):
        PredictorImportance(position=0, label="x", decreases=())
    negative = PredictorImportance(position=0, label="x", decreases=(-0.25, -0.75))
    assert negative.mean == -0.5
    assert negative.standard_deviation == 0.25
    with pytest.raises(ValueError, match="log loss or R²"):
        PermutationImportance(DiagnosticMetric.MAE, 2, (negative,))
    with pytest.raises(ValueError, match="one decrease per repeat"):
        PermutationImportance(DiagnosticMetric.R2, 3, (negative,))
    with pytest.raises(ValueError, match="must reconcile"):
        DiagnosticPopulation(10, 1, 0, 8)
    with pytest.raises(ValueError, match="recorded together"):
        DiagnosticPopulation(10, 0, 0, 10, n_training=8)
    with pytest.raises(ValueError, match="modeling rows"):
        DiagnosticPopulation(10, 0, 0, 10, n_training=8, n_validation=1)
    with pytest.raises(ValueError, match="both training and validation"):
        DiagnosticClassCount(value="a", n_training=3, n_validation=0)
    with pytest.raises(ValueError, match="sum to n_training"):
        DiagnosticPopulation(
            10,
            0,
            0,
            10,
            n_training=8,
            n_validation=2,
            classes=(DiagnosticClassCount("a", 7, 2),),
        )
    with pytest.raises(ValueError, match="follow the selected type"):
        DiagnosticPredictor(
            position=1,
            label="id",
            selected_type=SemanticType.IDENTIFIER,
            resolution_status=ResolutionStatus.RESOLVED,
            decision=PredictorDecision.INCLUDED,
        )
    with pytest.raises(ValueError, match="follow the selected type"):
        DiagnosticPredictor(
            position=1,
            label="x",
            selected_type=SemanticType.NUMERIC,
            resolution_status=ResolutionStatus.RESOLVED,
            decision=PredictorDecision.CONSTANT,
        )
    with pytest.raises(ValueError, match="only a Categorical"):
        DiagnosticPredictor(
            position=1,
            label="x",
            selected_type=SemanticType.NUMERIC,
            resolution_status=ResolutionStatus.RESOLVED,
            decision=PredictorDecision.TOO_MANY_LEVELS,
            n_training_levels=2000,
        )
    with pytest.raises(ValueError, match="encoding must follow"):
        DiagnosticPredictor(
            position=1,
            label="x",
            selected_type=SemanticType.NUMERIC,
            resolution_status=ResolutionStatus.RESOLVED,
            decision=PredictorDecision.INCLUDED,
            encoding=PredictorEncoding.ONE_HOT,
            n_training_levels=3,
        )
    with pytest.raises(ValueError, match="one-hot predictors only"):
        DiagnosticPredictor(
            position=1,
            label="x",
            selected_type=SemanticType.NUMERIC,
            resolution_status=ResolutionStatus.RESOLVED,
            decision=PredictorDecision.INCLUDED,
            encoding=PredictorEncoding.STANDARDIZED,
            n_training_levels=3,
        )
    retained = _diagnostic(_binary_frame(), "y")
    with pytest.raises(ValueError, match="only an available"):
        dataclasses.replace(retained, status=DiagnosticStatus.NUMERICAL_FAILURE)
    with pytest.raises(ValueError, match="design must follow"):
        dataclasses.replace(retained, task=PredictiveTask.REGRESSION)
    with pytest.raises(ValueError, match="included predictors"):
        dataclasses.replace(
            retained,
            importance=dataclasses.replace(
                retained.importance, predictors=retained.importance.predictors[:1]
            ),
        )
    with pytest.raises(ValueError, match="no task, design, or population"):
        TargetDiagnosticAnalysis(
            target_position=0,
            status=DiagnosticStatus.TARGET_TYPE_UNSUPPORTED,
            population=retained.population,
        )
    with pytest.raises(ValueError, match="decided before the split"):
        dataclasses.replace(
            retained,
            status=DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION,
            predictors=(),
            evaluation=None,
            importance=None,
        )
    with pytest.raises(ValueError, match="validation_fraction"):
        dataclasses.replace(retained.design, validation_fraction=1.0)


def test_retained_result_holds_no_model_or_source_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = analyze_dataframe(_multiclass_frame(), target="y")
    retained = analysis.target_diagnostic
    _assert_plain(retained)
    monkeypatch.setattr(fit_module, "analyze_target_diagnostic", _fail)
    monkeypatch.setattr(fit_module, "_permutation_importance", _fail)
    monkeypatch.setattr(fit_module, "_block_mover", _fail)
    monkeypatch.setattr(fit_module, "_validation_permutations", _fail)
    monkeypatch.setattr(dataset_module, "analyze_target_diagnostic", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(Pipeline, "fit", _fail)
    monkeypatch.setattr(Pipeline, "predict", _fail)
    monkeypatch.setattr(Pipeline, "predict_proba", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    summary = build_target_summary(analysis)
    assert summary.diagnostic == retained
    assert summary.diagnostic is not retained
    assert summary.diagnostic.evaluation is not retained.evaluation
    _assert_plain(summary.diagnostic)
    copied = copy_target_diagnostic(retained)
    assert copied == retained
    for item in copied.importance.predictors:
        assert math.isfinite(item.mean) and math.isfinite(item.standard_deviation)
    assert copied.evaluation.log_loss.improvement > 0.0
    with pytest.raises(TypeError, match="TargetDiagnosticAnalysis"):
        copy_target_diagnostic(analysis)  # type: ignore[arg-type]


def test_inputs_must_be_the_analysis_of_the_frame() -> None:
    frame = _binary_frame()
    analysis = analyze_dataframe(frame, target="y")
    with pytest.raises(TypeError, match="DataFrame"):
        analyze_target_diagnostic(
            frame.to_dict(),  # type: ignore[arg-type]
            analysis.columns,
            analysis.target_analysis,
            analysis.target_leakage,
        )
    with pytest.raises(ValueError, match="frame shape"):
        analyze_target_diagnostic(
            frame.iloc[:-1],
            analysis.columns,
            analysis.target_analysis,
            analysis.target_leakage,
        )
    with pytest.raises(TypeError, match="TargetAnalysis"):
        analyze_target_diagnostic(
            frame, analysis.columns, "y", analysis.target_leakage  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="tuple"):
        analyze_target_diagnostic(
            frame,
            list(analysis.columns),  # type: ignore[arg-type]
            analysis.target_analysis,
            analysis.target_leakage,
        )
    edited = frame.copy()
    edited.loc[:5, "y"] = pd.NA
    with pytest.raises(ValueError, match="do not match the target analysis"):
        analyze_target_diagnostic(
            edited, analysis.columns, analysis.target_analysis, analysis.target_leakage
        )


def test_training_rows_decide_variation_for_numeric_and_one_hot_columns() -> None:
    rng = np.random.default_rng(13)
    n = 60
    target = rng.normal(size=n)
    target[-6:] = np.nan
    flat_number = np.ones(n)
    flat_number[-6:] = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    flat_level = np.array(["a"] * (n - 6) + ["b"] * 6)
    frame = pd.DataFrame(
        {
            "y": target,
            "signal": rng.normal(size=n),
            "flat_number": flat_number,
            "flat_level": pd.Series(flat_level, dtype="category"),
        }
    )
    decisions = _decisions(_diagnostic(frame, "y"))
    assert decisions == {
        "signal": PredictorDecision.INCLUDED,
        "flat_number": PredictorDecision.NO_TRAINING_VARIATION,
        "flat_level": PredictorDecision.NO_TRAINING_VARIATION,
    }


def test_non_finite_probabilities_or_importance_are_numerical_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _binary_frame()

    def nan_probabilities(self, X):  # type: ignore[no-untyped-def]
        return np.full((X.shape[0], 2), np.nan)

    with monkeypatch.context() as patched:
        patched.setattr(
            fit_module.LogisticRegression, "predict_proba", nan_probabilities
        )
        failed = _diagnostic(frame, "y")
    assert failed.status is DiagnosticStatus.NUMERICAL_FAILURE
    assert failed.evaluation is None

    monkeypatch.setattr(fit_module, "_negative_log_loss", lambda *a, **k: math.nan)
    assert _diagnostic(frame, "y").status is DiagnosticStatus.NUMERICAL_FAILURE


def test_summary_requires_the_target_diagnostic() -> None:
    analysis = analyze_dataframe(_binary_frame(n=12), target="y")
    summary = build_target_summary(analysis)
    with pytest.raises(TypeError, match="diagnostic"):
        dataclasses.replace(summary, diagnostic="model")
    with pytest.raises(ValueError, match="summarized target"):
        dataclasses.replace(
            summary,
            diagnostic=TargetDiagnosticAnalysis(
                target_position=1, status=DiagnosticStatus.TARGET_TYPE_UNSUPPORTED
            ),
        )


def test_fit_inputs_are_checked_before_reading_values() -> None:
    frame = _binary_frame()
    analysis = analyze_dataframe(frame, target="flag")
    columns = analysis.columns
    target = analysis.target_analysis
    with pytest.raises(TypeError, match="ColumnAnalysis"):
        analyze_target_diagnostic(
            frame, ("column",), target, analysis.target_leakage  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="column position"):
        analyze_target_diagnostic(
            frame,
            (columns[1], columns[0]) + columns[2:],
            target,
            analysis.target_leakage,
        )
    with pytest.raises(ValueError, match="outside the column axis"):
        analyze_target_diagnostic(
            frame.iloc[:, :2], columns[:2], target, analysis.target_leakage
        )


def test_diagnostic_records_reject_every_inconsistent_shape() -> None:
    available = _diagnostic(_binary_frame(), "y")
    multiclass = _diagnostic(_multiclass_frame(), "y")
    regression = _diagnostic(_regression_frame(), "y")
    small = _diagnostic(_binary_frame(n=12), "y")
    small_regression = _diagnostic(_regression_frame(n=10), "y")
    undefined = _diagnostic(
        pd.DataFrame(
            {"y": [0.0] * 23 + [1.0], "x": np.arange(24, dtype=np.float64) % 5}
        ),
        "y",
    )
    design = available.design
    population = available.population
    evaluation = available.evaluation
    numeric = DiagnosticPredictor(
        position=1,
        label="signal",
        selected_type=SemanticType.NUMERIC,
        resolution_status=ResolutionStatus.RESOLVED,
        decision=PredictorDecision.NO_TRAINING_VARIATION,
    )
    unsplit = DiagnosticPopulation(
        population.n_total_rows,
        population.n_target_missing,
        population.n_target_non_finite,
        population.n_modeling,
    )
    excluded = tuple(
        dataclasses.replace(
            item,
            decision=PredictorDecision.IDENTICAL_TO_TARGET,
            encoding=None,
            n_training_levels=None,
        )
        for item in available.predictors
    )
    cases = [
        (lambda: dataclasses.replace(design, permutation_repeats=0), "positive"),
        (lambda: dataclasses.replace(design, estimator_parameters=[]), "a tuple"),
        (
            lambda: dataclasses.replace(design, estimator_parameters=(("C",),)),
            "name-value",
        ),
        (
            lambda: dataclasses.replace(design, estimator_parameters=((1, 2),)),
            "name must be a str",
        ),
        (lambda: dataclasses.replace(design, library_version=""), "non-empty"),
        (lambda: dataclasses.replace(population, classes=[]), "classes must be"),
        (
            lambda: DiagnosticPopulation(
                10, 0, 0, 10, classes=(DiagnosticClassCount("a", 1, 1),)
            ),
            "require a split",
        ),
        (
            lambda: DiagnosticPopulation(
                10,
                0,
                0,
                10,
                n_training=8,
                n_validation=2,
                classes=(DiagnosticClassCount("a", 8, 1),),
            ),
            "n_validation",
        ),
        (
            lambda: dataclasses.replace(numeric, selected_type=None),
            "exactly when resolution",
        ),
        (
            lambda: dataclasses.replace(
                numeric, encoding=PredictorEncoding.STANDARDIZED
            ),
            "only an included",
        ),
        (
            lambda: dataclasses.replace(
                numeric,
                selected_type=SemanticType.CATEGORICAL,
                decision=PredictorDecision.SCALE_NOT_FINITE,
            ),
            "only a Numeric",
        ),
        (
            lambda: DiagnosticPredictor(
                position=1,
                label="g",
                selected_type=SemanticType.CATEGORICAL,
                resolution_status=ResolutionStatus.RESOLVED,
                decision=PredictorDecision.INCLUDED,
                encoding=PredictorEncoding.ONE_HOT,
                n_training_levels=1,
            ),
            "at least two levels",
        ),
        (
            lambda: dataclasses.replace(evaluation, roc_auc=evaluation.log_loss),
            "ROC AUC metric",
        ),
        (lambda: dataclasses.replace(evaluation, solver_converged=1), "bool"),
        (
            lambda: dataclasses.replace(
                evaluation, balanced_accuracy=evaluation.log_loss
            ),
            "must hold",
        ),
        (lambda: PermutationImportance(DiagnosticMetric.R2, 5, ()), "non-empty"),
        (
            lambda: dataclasses.replace(
                available.importance,
                predictors=available.importance.predictors[::-1],
            ),
            "ascending",
        ),
        (
            lambda: TargetDiagnosticAnalysis(
                0, DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION
            ),
            "keeps its diagnostic population",
        ),
        (
            lambda: TargetDiagnosticAnalysis(
                0,
                DiagnosticStatus.INSUFFICIENT_TARGET_CLASSES,
                task=PredictiveTask.BINARY_CLASSIFICATION,
                design=design,
                population=small.population,
            ),
            "fewer than two classes",
        ),
        (
            lambda: dataclasses.replace(small, task=None, design=None),
            "requires a predictive task",
        ),
        (
            lambda: dataclasses.replace(
                small, status=DiagnosticStatus.INSUFFICIENT_TARGET_VARIATION
            ),
            "for regression",
        ),
        (
            lambda: dataclasses.replace(
                small, status=DiagnosticStatus.TOO_MANY_TARGET_CLASSES
            ),
            "class limit",
        ),
        (
            lambda: dataclasses.replace(
                small_regression, status=DiagnosticStatus.VALIDATION_SPLIT_IMPOSSIBLE
            ),
            "stratified split",
        ),
        (
            lambda: dataclasses.replace(available, population=unsplit),
            "training and validation rows",
        ),
        (
            lambda: dataclasses.replace(
                available, task=PredictiveTask.MULTICLASS_CLASSIFICATION
            ),
            "follow the classification task",
        ),
        (
            lambda: dataclasses.replace(
                regression,
                population=dataclasses.replace(
                    regression.population,
                    classes=(
                        DiagnosticClassCount(
                            "a",
                            regression.population.n_training,
                            regression.population.n_validation,
                        ),
                    ),
                ),
            ),
            "belong to a split classification",
        ),
        (
            lambda: dataclasses.replace(
                available, predictors=list(available.predictors)
            ),
            "predictors must be a tuple",
        ),
        (
            lambda: dataclasses.replace(
                available,
                predictors=(dataclasses.replace(available.predictors[0], position=0),)
                + available.predictors[1:],
            ),
            "not its own predictor",
        ),
        (
            lambda: dataclasses.replace(
                available, predictors=available.predictors[::-1]
            ),
            "ascending physical positions",
        ),
        (
            lambda: dataclasses.replace(small, predictors=available.predictors),
            "only after the target checks",
        ),
        (
            lambda: dataclasses.replace(
                available,
                status=DiagnosticStatus.NO_ELIGIBLE_PREDICTORS,
                evaluation=None,
                importance=None,
            ),
            "none was included",
        ),
        (
            lambda: dataclasses.replace(available, predictors=excluded),
            "at least one predictor",
        ),
        (
            lambda: TargetDiagnosticAnalysis(
                0,
                DiagnosticStatus.NO_ELIGIBLE_PREDICTORS,
                task=PredictiveTask.BINARY_CLASSIFICATION,
                design=design,
                population=unsplit,
                predictors=(numeric,),
            ),
            "require a split",
        ),
        (
            lambda: dataclasses.replace(
                multiclass,
                evaluation=dataclasses.replace(
                    multiclass.evaluation,
                    roc_auc=MetricComparison(DiagnosticMetric.ROC_AUC, 0.9, 0.5),
                ),
            ),
            "must follow the task",
        ),
        (
            lambda: dataclasses.replace(undefined, importance=regression.importance),
            "defined importance metric",
        ),
        (
            lambda: dataclasses.replace(
                available,
                importance=dataclasses.replace(
                    available.importance, metric=DiagnosticMetric.R2
                ),
            ),
            "design's metric",
        ),
        (
            lambda: dataclasses.replace(
                available,
                importance=PermutationImportance(
                    DiagnosticMetric.LOG_LOSS,
                    1,
                    tuple(
                        PredictorImportance(item.position, item.label, (0.0,))
                        for item in available.importance.predictors
                    ),
                ),
            ),
            "repeat count",
        ),
        (
            lambda: dataclasses.replace(
                available,
                importance=dataclasses.replace(
                    available.importance,
                    predictors=(
                        dataclasses.replace(
                            available.importance.predictors[0], label="other"
                        ),
                    )
                    + available.importance.predictors[1:],
                ),
            ),
            "keeps the predictor label",
        ),
    ]
    for build, message in cases:
        with pytest.raises((TypeError, ValueError), match=message):
            build()
            pytest.fail(f"no rejection for: {message}")


def test_dataset_attachment_checks_population_classes_and_predictor_state() -> None:
    def rebuild(analysis: DatasetAnalysis, diagnostic: object) -> DatasetAnalysis:
        fields = {
            field.name: getattr(analysis, field.name)
            for field in dataclasses.fields(DatasetAnalysis)
        }
        return DatasetAnalysis(**{**fields, "target_diagnostic": diagnostic})

    dated = analyze_dataframe(
        pd.DataFrame(
            {"when": pd.date_range("2020-01-01", periods=30), "x": np.arange(30.0)}
        ),
        target="when",
    )
    with pytest.raises(ValueError, match="no diagnostic model"):
        rebuild(
            dated,
            TargetDiagnosticAnalysis(
                0,
                DiagnosticStatus.INSUFFICIENT_TARGET_CLASSES,
                population=DiagnosticPopulation(30, 0, 0, 30),
            ),
        )

    regression = analyze_dataframe(_regression_frame(), target="y")
    diagnostic = regression.target_diagnostic
    population = diagnostic.population
    with pytest.raises(ValueError, match="must be the target rows"):
        rebuild(
            regression,
            dataclasses.replace(
                diagnostic,
                population=dataclasses.replace(
                    population,
                    n_total_rows=population.n_total_rows + 1,
                    n_modeling=population.n_modeling + 1,
                    n_training=population.n_training + 1,
                ),
            ),
        )
    with pytest.raises(ValueError, match="finite non-missing"):
        rebuild(
            regression,
            dataclasses.replace(
                diagnostic,
                population=dataclasses.replace(
                    population,
                    n_target_non_finite=1,
                    n_modeling=population.n_modeling - 1,
                    n_training=population.n_training - 1,
                ),
            ),
        )

    multiclass = analyze_dataframe(_multiclass_frame(), target="y")
    retained = multiclass.target_diagnostic
    classes = retained.population.classes
    first = classes[0]
    split_first = (
        DiagnosticClassCount("high", first.n_training - 1, first.n_validation - 1),
        DiagnosticClassCount("extra", 1, 1),
    ) + classes[1:]
    moved = (
        dataclasses.replace(classes[0], n_training=classes[0].n_training + 1),
        dataclasses.replace(classes[1], n_training=classes[1].n_training - 1),
    ) + classes[2:]
    retyped = analyze_dataframe(_binary_frame(), target="y")
    boolean_classes = retyped.target_diagnostic.population.classes
    for target_analysis, replaced, message in (
        (multiclass, split_first, "observed target classes"),
        (multiclass, moved, "observed class counts"),
        (
            retyped,
            (dataclasses.replace(boolean_classes[0], value=0),) + boolean_classes[1:],
            "observed target classes",
        ),
    ):
        kept = target_analysis.target_diagnostic
        with pytest.raises(ValueError, match=message):
            rebuild(
                target_analysis,
                dataclasses.replace(
                    kept,
                    population=dataclasses.replace(kept.population, classes=replaced),
                ),
            )

    rng = np.random.default_rng(14)
    n = 60
    target = rng.normal(size=n)
    target[-6:] = np.nan
    flat = np.ones(n)
    flat[-6:] = rng.normal(size=6)
    mixed = analyze_dataframe(
        pd.DataFrame(
            {
                "y": target,
                "flat": flat,
                "words": pd.Series(rng.choice(["red", "blue"], size=n), dtype="string"),
                "signal": rng.normal(size=n),
            }
        ),
        target="y",
    )
    kept = mixed.target_diagnostic
    flat_record, words_record = kept.predictors[0], kept.predictors[1]
    assert flat_record.decision is PredictorDecision.NO_TRAINING_VARIATION
    assert words_record.decision is PredictorDecision.UNRESOLVED
    with pytest.raises(ValueError, match="keeps its selected type"):
        rebuild(
            mixed,
            dataclasses.replace(
                kept,
                predictors=(
                    dataclasses.replace(
                        flat_record, selected_type=SemanticType.CATEGORICAL
                    ),
                )
                + kept.predictors[1:],
            ),
        )
    with pytest.raises(ValueError, match="keeps its resolution status"):
        rebuild(
            mixed,
            dataclasses.replace(
                kept,
                predictors=(
                    flat_record,
                    dataclasses.replace(
                        words_record, resolution_status=ResolutionStatus.AMBIGUOUS
                    ),
                )
                + kept.predictors[2:],
            ),
        )


def _equivalence_frame(name: str) -> pd.DataFrame:
    rng = np.random.default_rng(21)
    n = 240
    signal = rng.normal(size=n)
    amount = rng.normal(size=n)
    amount[::9] = np.nan
    amount[5::17] = np.inf
    flag = pd.Series(rng.random(n) < 0.5, dtype="boolean")
    flag[::7] = pd.NA
    levels = rng.choice(["a", "b", "c", "d"], size=n).astype(object)
    levels[::11] = None
    levels[3::12] = [f"rare{index}" for index in range(len(levels[3::12]))]
    columns = {
        "plain": rng.normal(size=n) + 0.5 * signal,
        "amount": amount + signal,
        "flag": flag,
        "group": pd.Series(levels, dtype="category"),
    }
    binary = pd.Series(signal + rng.normal(size=n) > 0, dtype="boolean")
    if name == "numeric":
        return pd.DataFrame({"y": binary, "plain": columns["plain"]})
    if name == "numeric_missing":
        return pd.DataFrame({"y": binary, "amount": columns["amount"]})
    if name == "boolean":
        return pd.DataFrame({"y": binary, "flag": columns["flag"]})
    if name == "categorical":
        return pd.DataFrame({"y": binary, "group": columns["group"]})
    if name == "mixed_binary":
        return pd.DataFrame({"y": binary, **columns})
    if name == "mixed_multiclass":
        label = np.where(signal > 0.5, "high", np.where(signal < -0.5, "low", "mid"))
        return pd.DataFrame({"y": pd.Series(label, dtype="category"), **columns})
    return pd.DataFrame({"y": 2.0 * signal + rng.normal(size=n), **columns})


class _ImportanceSpy:
    """Keep the arguments and result of the diagnostic's importance call."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list = []
        original = fit_module._permutation_importance
        spy = self

        def wrapped(*args):  # type: ignore[no-untyped-def]
            result = original(*args)
            spy.calls.append((args, result))
            return result

        monkeypatch.setattr(fit_module, "_permutation_importance", wrapped)


def _source_permuted(
    x_valid: pd.DataFrame, key: str, order: np.ndarray
) -> pd.DataFrame:
    permuted = x_valid.copy()
    permuted[key] = x_valid[key].to_numpy()[order]
    return permuted


@pytest.mark.parametrize(
    "name",
    [
        "numeric",
        "numeric_missing",
        "boolean",
        "categorical",
        "mixed_binary",
        "mixed_multiclass",
        "mixed_regression",
    ],
)
def test_block_permutation_equals_source_column_permutation(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    frame = _equivalence_frame(name)
    spy = _ImportanceSpy(monkeypatch)
    diagnostic = _diagnostic(frame, "y")
    (pipeline, included, x_valid, y_valid, scorer, _task, seed), result = spy.calls[0]
    assert result == diagnostic.importance
    preprocess = pipeline.named_steps["preprocess"]
    encoded = preprocess.transform(x_valid)
    if name == "numeric":
        assert not sparse.issparse(encoded)
    if name in ("numeric_missing", "mixed_binary"):
        imputer = preprocess.named_transformers_["numeric"].named_steps["impute"]
        assert imputer.indicator_.features_.size
        assert not np.all(np.isfinite(frame["amount"]))
    if name in ("categorical", "mixed_binary"):
        position = list(frame.columns).index("group")
        index = [
            item.position
            for item in included
            if item.encoding is (PredictorEncoding.ONE_HOT)
        ].index(position)
        vocabulary = set(preprocess.named_transformers_["levels"].categories_[index])
        observed = set(x_valid[f"column_{position}"].tolist())
        assert -1 in vocabulary
        assert observed - vocabulary
    orders = fit_module._validation_permutations(len(x_valid), seed)
    reference = scorer(pipeline, x_valid, y_valid)
    for item, scored in zip(included, result.predictors):
        key = f"column_{item.position}"
        expected = [
            reference - scorer(pipeline, _source_permuted(x_valid, key, order), y_valid)
            for order in orders
        ]
        np.testing.assert_allclose(scored.decreases, expected, rtol=0.0, atol=1e-12)
        assert scored.mean == pytest.approx(np.mean(expected), rel=0.0, abs=1e-12)
        assert scored.standard_deviation == pytest.approx(
            np.std(expected), rel=0.0, abs=1e-12
        )
    legacy = permutation_importance(
        pipeline, x_valid, y_valid, scoring=scorer, n_repeats=5, random_state=seed
    )
    np.testing.assert_allclose(
        [scored.decreases for scored in result.predictors],
        legacy.importances,
        rtol=0.0,
        atol=1e-12,
    )


def test_controlled_order_moves_every_owned_column_with_its_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def orders(n_rows: int, _seed: int) -> tuple:
        base = np.arange(n_rows)
        return (
            base[::-1].copy(),
            np.roll(base, 1),
            np.roll(base, 7),
            np.concatenate([base[1::2], base[::2]]),
            base[::-1].copy(),
        )

    scored: list = []
    original_proba = LogisticRegression.predict_proba

    def predict_proba(self, X):  # type: ignore[no-untyped-def]
        scored.append(X.copy())
        return original_proba(self, X)

    monkeypatch.setattr(fit_module, "_validation_permutations", orders)
    monkeypatch.setattr(LogisticRegression, "predict_proba", predict_proba)
    spy = _ImportanceSpy(monkeypatch)
    _diagnostic(_equivalence_frame("mixed_binary"), "y")
    (pipeline, included, x_valid, *_rest), _result = spy.calls[0]
    preprocess = pipeline.named_steps["preprocess"]
    encoded = preprocess.transform(x_valid)
    calls = scored[-(1 + len(included) * 5) :]
    assert (calls[0] != encoded).nnz == 0
    block_sizes = {}
    for index, item in enumerate(included):
        key = f"column_{item.position}"
        for repeat, order in enumerate(orders(len(x_valid), 0)):
            matrix = calls[1 + index * 5 + repeat]
            expected = preprocess.transform(_source_permuted(x_valid, key, order))
            assert (matrix != expected).nnz == 0
            moved = np.unique((expected != encoded).nonzero()[1])
            others = np.setdiff1d(np.arange(encoded.shape[1]), moved)
            assert (matrix[:, moved] != encoded[order][:, moved]).nnz == 0
            assert (matrix[:, others] != encoded[:, others]).nnz == 0
            block_sizes[item.label] = max(block_sizes.get(item.label, 0), moved.size)
    assert block_sizes["amount"] == 2
    assert block_sizes["flag"] == 3
    assert block_sizes["group"] == 5
    assert block_sizes["plain"] == 1


def test_validation_permutations_are_fixed_full_orders() -> None:
    first = fit_module._validation_permutations(50, 0)
    assert len(first) == 5
    for order in first:
        assert np.array_equal(np.sort(order), np.arange(50))
    assert all(
        np.array_equal(left, right)
        for left, right in zip(first, fit_module._validation_permutations(50, 0))
    )
    assert len({tuple(order.tolist()) for order in first}) == 5
    other = fit_module._validation_permutations(50, 1)
    assert not all(np.array_equal(a, b) for a, b in zip(first, other))


_PLAIN = (type(None), bool, int, float, str)


def _assert_plain(value: object, seen: set | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    module = type(value).__module__
    assert not module.startswith(("sklearn", "numpy", "pandas", "scipy"))
    assert not callable(value) or isinstance(value, Enum)
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_plain(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_plain(item, seen)
    else:
        assert isinstance(value, _PLAIN + (Enum,))


def _fail(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("the retained diagnostic used a fitting or source operation")
