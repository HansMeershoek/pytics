"""TSK-035: target leakage evidence for an explicit target."""

from __future__ import annotations

import dataclasses
import inspect
import pickle
import uuid

import numpy as np
import pandas as pd
import pytest

import pytics.analysis.dataset as dataset_module
import pytics.analysis.target_leakage as leakage_module
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.target import project_target_analysis
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import PredictorDecision
from pytics.analysis.target_leakage import ExactDuplicateEvidence
from pytics.analysis.target_leakage import ExactDuplicateStatus
from pytics.analysis.target_leakage import LeakageApplicability
from pytics.analysis.target_leakage import LeakagePopulation
from pytics.analysis.target_leakage import MappingEvidence
from pytics.analysis.target_leakage import MappingStatus
from pytics.analysis.target_leakage import TargetLeakageAnalysis
from pytics.analysis.target_leakage import analyze_target_leakage
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.resolution import ResolutionStatus

_SOURCE_TYPES = (
    pd.DataFrame,
    pd.Series,
    pd.Index,
    np.ndarray,
    dict,
    list,
    set,
)


def _fail(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("source access")


def _leakage(frame: pd.DataFrame, target: object) -> TargetLeakageAnalysis:
    analysis = analyze_dataframe(frame, target=target)
    assert analysis.target_leakage is not None
    return analysis.target_leakage


def _predictor(leakage: TargetLeakageAnalysis, label: object) -> object:
    return next(item for item in leakage.predictors if item.label == label)


def _strings(value: object) -> list:
    found: list = []
    if isinstance(value, str):
        found.append(value)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            found.extend(_strings(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            found.extend(_strings(item))
    return found


def _assert_plain(value: object) -> None:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            _assert_plain(getattr(value, field.name))
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_plain(item)
        return
    assert not isinstance(value, _SOURCE_TYPES)
    assert not callable(value)


def _audit_groups(
    predictor: pd.Series,
    target: pd.Series,
    *,
    numeric: bool = False,
) -> dict:
    """Count functional-dependency facts without the production collector."""
    target_observed = target.notna().to_numpy()
    if numeric:
        values = np.asarray(predictor.to_numpy(dtype=np.float64, na_value=np.nan))
        observed = np.isfinite(values) & target_observed
        keys = values[observed]
    else:
        observed = predictor.notna().to_numpy() & target_observed
        keys = predictor.to_numpy()[observed]
    classes = target.to_numpy()[observed]
    audited = pd.DataFrame({"x": keys, "y": classes})
    if isinstance(audited["x"].dtype, pd.CategoricalDtype):
        audited["x"] = audited["x"].cat.remove_unused_categories()
    if isinstance(audited["y"].dtype, pd.CategoricalDtype):
        audited["y"] = audited["y"].cat.remove_unused_categories()
    n_applicable = int(np.count_nonzero(target_observed))
    n_joint = int(observed.sum())
    if n_joint == 0:
        return {
            "n_applicable_rows": n_applicable,
            "n_joint_rows": 0,
            "n_predictor_unobserved": n_applicable,
            "n_distinct_groups": 0,
            "n_repeated_groups": 0,
            "n_singleton_groups": 0,
            "n_conflicting_groups": 0,
            "n_consistent_repeated_groups": 0,
            "n_rows_in_repeated_groups": 0,
            "n_rows_in_conflicting_groups": 0,
            "n_target_classes": 0,
        }
    grouped = audited.groupby("x", dropna=True, observed=True)["y"]
    sizes = grouped.size()
    class_counts = grouped.nunique(dropna=True)
    repeated = sizes >= 2
    conflicting = class_counts > 1
    n_repeated = int(repeated.sum())
    n_conflicting = int(conflicting.sum())
    return {
        "n_applicable_rows": n_applicable,
        "n_joint_rows": n_joint,
        "n_predictor_unobserved": n_applicable - n_joint,
        "n_distinct_groups": int(sizes.size),
        "n_repeated_groups": n_repeated,
        "n_singleton_groups": int((~repeated).sum()),
        "n_conflicting_groups": n_conflicting,
        "n_consistent_repeated_groups": n_repeated - n_conflicting,
        "n_rows_in_repeated_groups": int(sizes[repeated].sum()) if n_repeated else 0,
        "n_rows_in_conflicting_groups": (
            int(sizes[conflicting].sum()) if n_conflicting else 0
        ),
        "n_target_classes": int(pd.Series(classes).nunique(dropna=True)),
    }


def _assert_mapping_audit(evidence: MappingEvidence, audit: dict) -> None:
    for name, expected in audit.items():
        assert getattr(evidence, name) == expected


def _categories(values: list, categories: list) -> pd.Series:
    return pd.Series(pd.Categorical(values, categories=categories))


def test_no_target_does_not_collect_leakage(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 4.0]})
    monkeypatch.setattr(dataset_module, "analyze_target_leakage", _fail)
    analysis = analyze_dataframe(frame)
    assert analysis.target_analysis is None
    assert analysis.target_leakage is None
    assert analysis.target_diagnostic is None


def test_unsupported_ineligible_and_unresolved_targets_do_not_read_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "when": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "code": pd.Series(
                [str(uuid.UUID(int=index + 1)) for index in range(3)],
                dtype="string",
            ),
            "words": pd.Series(
                ["alpha bravo", "charlie delta", "echo foxtrot"], dtype="string"
            ),
            "x": [1.0, 2.0, 3.0],
        }
    )
    expected = {
        "when": LeakageApplicability.TARGET_UNSUPPORTED,
        "code": LeakageApplicability.TARGET_INELIGIBLE,
        "words": LeakageApplicability.TARGET_UNRESOLVED,
    }
    for label, applicability in expected.items():
        analysis = analyze_dataframe(frame, target=label)
        leakage = analysis.target_leakage
        assert leakage is not None
        assert leakage.applicability is applicability
        assert leakage.predictors == ()
        assert leakage.population.n_applicable == 0
        assert leakage.n_exact_duplicates == 0
        assert leakage.n_repeated_deterministic_mappings == 0
        monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
        again = analyze_target_leakage(
            frame, analysis.columns, analysis.target_analysis
        )
        assert again == leakage
        monkeypatch.undo()


def test_exact_copies_use_the_semantic_equality_contract() -> None:
    boolean = pd.DataFrame(
        {
            "y": pd.Series([index % 2 == 0 for index in range(30)], dtype="boolean"),
            "copy": pd.Series([index % 2 == 0 for index in range(30)], dtype="boolean"),
            "gap": pd.Series(
                [pd.NA if index == 3 else index % 2 == 0 for index in range(30)],
                dtype="boolean",
            ),
            "other": pd.Series(
                [index % 3 == 0 for index in range(30)], dtype="boolean"
            ),
        }
    )
    boolean_leakage = _leakage(boolean, "y")
    copy = _predictor(boolean_leakage, "copy")
    assert copy.exact_duplicate.status is ExactDuplicateStatus.EXACT_DUPLICATE
    assert copy.exact_duplicate.n_joint_rows == 30
    assert copy.exact_duplicate.n_unequal_rows == 0
    gap = _predictor(boolean_leakage, "gap")
    assert gap.exact_duplicate.status is (
        ExactDuplicateStatus.MISSINGNESS_BLOCKS_EQUALITY
    )
    assert gap.exact_duplicate.n_equal_rows == 29
    assert gap.exact_duplicate.n_predictor_unobserved == 1
    assert _predictor(boolean_leakage, "other").exact_duplicate.status is (
        ExactDuplicateStatus.NOT_EQUAL
    )
    boolean_analysis = analyze_dataframe(boolean, target="y")
    decisions = {
        item.label: item.decision
        for item in boolean_analysis.target_diagnostic.predictors
    }
    assert decisions["copy"] is PredictorDecision.IDENTICAL_TO_TARGET
    assert decisions["gap"] is not PredictorDecision.IDENTICAL_TO_TARGET
    assert "copy" not in {
        item.label for item in boolean_analysis.target_diagnostic.included_predictors
    }

    numeric = pd.DataFrame(
        {
            "y": np.arange(30, dtype=np.int64),
            "copy": np.arange(30, dtype=np.float64),
            "gap": np.arange(30, dtype=np.float64),
            "affine": np.arange(30, dtype=np.float64) * 2.0 + 1.0,
        }
    )
    numeric.loc[4, "gap"] = np.nan
    numeric_leakage = _leakage(numeric, "y")
    assert _predictor(numeric_leakage, "copy").exact_duplicate.status is (
        ExactDuplicateStatus.EXACT_DUPLICATE
    )
    assert _predictor(numeric_leakage, "gap").exact_duplicate.status is (
        ExactDuplicateStatus.MISSINGNESS_BLOCKS_EQUALITY
    )
    affine = _predictor(numeric_leakage, "affine")
    assert affine.exact_duplicate.status is ExactDuplicateStatus.NOT_EQUAL
    assert affine.exact_duplicate.n_unequal_rows == 30
    assert affine.deterministic_mapping.status is MappingStatus.NOT_APPLICABLE
    numeric_decisions = {
        item.label: item.decision
        for item in analyze_dataframe(numeric, target="y").target_diagnostic.predictors
    }
    assert numeric_decisions["copy"] is PredictorDecision.IDENTICAL_TO_TARGET
    assert numeric_decisions["affine"] is PredictorDecision.INCLUDED

    labels = ["low", "mid", "high"]
    repeated = [labels[index % 3] for index in range(30)]
    categorical = pd.DataFrame(
        {
            "y": _categories(repeated, labels),
            "copy": pd.Series(
                pd.Categorical(repeated, categories=["high", "low", "mid", "spare"])
            ),
            "relabeled": _categories(
                [{"low": "L", "mid": "M", "high": "H"}[value] for value in repeated],
                ["L", "M", "H"],
            ),
        }
    )
    categorical_leakage = _leakage(categorical, "y")
    assert _predictor(categorical_leakage, "copy").exact_duplicate.status is (
        ExactDuplicateStatus.EXACT_DUPLICATE
    )
    relabeled = _predictor(categorical_leakage, "relabeled")
    assert relabeled.exact_duplicate.status is ExactDuplicateStatus.NOT_EQUAL
    assert relabeled.deterministic_mapping.status is (
        MappingStatus.DETERMINISTIC_REPEATED
    )
    categorical_decisions = {
        item.label: item.decision
        for item in analyze_dataframe(
            categorical, target="y"
        ).target_diagnostic.predictors
    }
    assert categorical_decisions["copy"] is PredictorDecision.IDENTICAL_TO_TARGET
    assert categorical_decisions["relabeled"] is PredictorDecision.INCLUDED


def test_exact_duplicate_population_distinguishes_missingness() -> None:
    target = [1.0, 2.0, 3.0, np.nan, np.nan]
    frame = pd.DataFrame(
        {
            "y": target,
            "matched_outside": [1.0, 2.0, 3.0, 9.0, 8.0],
            "blank": [np.nan, np.nan, np.nan, 7.0, 8.0],
            "disagree": [1.0, 2.0, 0.0, np.nan, np.nan],
            "codes": pd.Series([1, 0, 1, 0, 1], dtype="category"),
        }
    )
    original = frame.copy(deep=True)
    leakage = _leakage(frame, "y")
    pd.testing.assert_frame_equal(frame, original)
    matched = _predictor(leakage, "matched_outside").exact_duplicate
    assert matched.status is ExactDuplicateStatus.EXACT_DUPLICATE
    assert matched.n_applicable_rows == 3
    assert matched.n_joint_rows == 3
    blank = _predictor(leakage, "blank").exact_duplicate
    assert blank.status is ExactDuplicateStatus.INSUFFICIENT_POPULATION
    assert blank.n_joint_rows == 0
    assert blank.n_predictor_unobserved == 3
    disagree = _predictor(leakage, "disagree").exact_duplicate
    assert disagree.status is ExactDuplicateStatus.NOT_EQUAL
    assert disagree.n_equal_rows == 2
    assert disagree.n_unequal_rows == 1
    codes = _predictor(leakage, "codes")
    assert codes.exact_duplicate.status is (
        ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    )
    assert codes.exact_duplicate.n_joint_rows == 0
    assert leakage.population.n_target_missing == 2
    assert leakage.population.n_applicable == 3


def test_cross_type_values_are_not_exact_duplicates() -> None:
    flag = [index % 2 == 0 for index in range(24)]
    frame = pd.DataFrame(
        {
            "y": pd.Series(flag, dtype="boolean"),
            "number": np.array([1.0 if value else 0.0 for value in flag]),
            "labels": pd.Series(
                pd.Categorical(["yes" if value else "no" for value in flag])
            ),
        }
    )
    leakage = _leakage(frame, "y")
    number = _predictor(leakage, "number")
    assert number.exact_duplicate.status is (
        ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    )
    assert number.deterministic_mapping.status is MappingStatus.DETERMINISTIC_REPEATED
    assert number.deterministic_mapping.n_repeated_groups == 2
    assert number.deterministic_mapping.n_target_classes == 2
    labels = _predictor(leakage, "labels")
    assert labels.exact_duplicate.status is (
        ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    )
    assert labels.deterministic_mapping.status is MappingStatus.DETERMINISTIC_REPEATED
    analysis = analyze_dataframe(frame, target="y")
    decisions = {
        item.label: item.decision for item in analysis.target_diagnostic.predictors
    }
    assert decisions["number"] is PredictorDecision.INCLUDED
    assert decisions["labels"] is PredictorDecision.INCLUDED

    ones = pd.DataFrame(
        {
            "y": _categories([1, 1, 0, 0] * 6, [1, 0]),
            "as_bool": _categories([True, True, False, False] * 6, [True, False]),
        }
    )
    boolean_categories = _predictor(_leakage(ones, "y"), "as_bool")
    assert boolean_categories.exact_duplicate.status is (
        ExactDuplicateStatus.EXACT_DUPLICATE
    )


def test_repeated_deterministic_mapping_is_audited_independently() -> None:
    predictor = ["A", "A", "B", "B", "C", "C"]
    target = ["0", "0", "1", "1", "0", "0"]
    frame = pd.DataFrame(
        {
            "group": _categories(predictor, ["A", "B", "C", "spare"]),
            "y": _categories(target, ["0", "1"]),
        }
    )
    evidence = _predictor(_leakage(frame, "y"), "group")
    assert evidence.deterministic_mapping.status is MappingStatus.DETERMINISTIC_REPEATED
    assert evidence.exact_duplicate.status is ExactDuplicateStatus.NOT_EQUAL
    _assert_mapping_audit(
        evidence.deterministic_mapping,
        _audit_groups(frame["group"], frame["y"]),
    )
    assert evidence.deterministic_mapping.n_repeated_groups == 3
    assert evidence.deterministic_mapping.n_conflicting_groups == 0
    assert evidence.deterministic_mapping.n_target_classes == 2
    assert evidence.deterministic_mapping.n_singleton_groups == 0


def test_conflicting_mapping_is_not_promoted() -> None:
    frame = pd.DataFrame(
        {
            "group": _categories(["A", "A", "B", "B"], ["A", "B"]),
            "y": _categories(["0", "1", "1", "1"], ["0", "1"]),
        }
    )
    evidence = _predictor(_leakage(frame, "y"), "group").deterministic_mapping
    assert evidence.status is MappingStatus.CONFLICTING
    _assert_mapping_audit(evidence, _audit_groups(frame["group"], frame["y"]))
    assert evidence.n_conflicting_groups == 1
    assert evidence.n_consistent_repeated_groups == 1


def test_pure_uniqueness_is_not_repeated_target_encoding() -> None:
    identifiers = [f"id{index}" for index in range(4)]
    target = ["0", "1", "0", "1"]
    frame = pd.DataFrame(
        {
            "row": _categories(identifiers, identifiers),
            "y": _categories(target, ["0", "1"]),
        }
    )
    evidence = _predictor(_leakage(frame, "y"), "row").deterministic_mapping
    assert evidence.status is MappingStatus.TRIVIAL_UNIQUENESS
    _assert_mapping_audit(evidence, _audit_groups(frame["row"], frame["y"]))
    assert evidence.n_distinct_groups == 4
    assert evidence.n_repeated_groups == 0
    assert evidence.n_rows_in_repeated_groups == 0
    assert evidence.n_target_classes == 2


def test_multiclass_repeated_mapping_keeps_every_class() -> None:
    predictor = ["A", "A", "B", "B", "C", "C"]
    target = ["low", "low", "mid", "mid", "high", "high"]
    frame = pd.DataFrame(
        {
            "group": _categories(predictor, ["A", "B", "C"]),
            "y": _categories(target, ["low", "mid", "high"]),
        }
    )
    evidence = _predictor(_leakage(frame, "y"), "group").deterministic_mapping
    assert evidence.status is MappingStatus.DETERMINISTIC_REPEATED
    _assert_mapping_audit(evidence, _audit_groups(frame["group"], frame["y"]))
    assert evidence.n_target_classes == 3
    assert evidence.n_repeated_groups == 3
    assert evidence.n_rows_in_repeated_groups == 6


def test_missing_predictor_values_are_not_a_group_or_a_class() -> None:
    frame = pd.DataFrame(
        {
            "group": _categories(
                ["A", "A", "B", "B", np.nan, np.nan],
                ["A", "B"],
            ),
            "y": _categories(["0", "0", "1", "1", "0", "1"], ["0", "1"]),
        }
    )
    evidence = _predictor(_leakage(frame, "y"), "group").deterministic_mapping
    assert evidence.status is MappingStatus.DETERMINISTIC_REPEATED
    _assert_mapping_audit(evidence, _audit_groups(frame["group"], frame["y"]))
    assert evidence.n_predictor_unobserved == 2
    assert evidence.n_joint_rows == 4
    assert evidence.n_distinct_groups == 2
    assert evidence.n_target_classes == 2

    conflict = pd.DataFrame(
        {
            "group": _categories(["A", "A", "B", np.nan], ["A", "B"]),
            "y": _categories(["0", "1", "1", "0"], ["0", "1"]),
        }
    )
    conflicted = _predictor(_leakage(conflict, "y"), "group").deterministic_mapping
    assert conflicted.status is MappingStatus.CONFLICTING
    _assert_mapping_audit(conflicted, _audit_groups(conflict["group"], conflict["y"]))
    assert conflicted.n_predictor_unobserved == 1

    blank = pd.DataFrame(
        {
            "group": pd.Series([pd.NA, pd.NA, pd.NA], dtype="category"),
            "y": _categories(["0", "1", "0"], ["0", "1"]),
        }
    )
    # An all-missing categorical column resolves before Categorical.
    blank_leakage = _leakage(blank, "y")
    blank_predictor = _predictor(blank_leakage, "group")
    assert blank_predictor.selected_type is SemanticType.EMPTY
    assert blank_predictor.deterministic_mapping.status is MappingStatus.NOT_APPLICABLE

    observed_blank = pd.DataFrame(
        {
            "group": _categories(["A", "A", "B", np.nan], ["A", "B"]),
            "y": _categories(["0", "0", "0", "1"], ["0", "1"]),
        }
    )
    partial = _predictor(_leakage(observed_blank, "y"), "group").deterministic_mapping
    assert partial.status is MappingStatus.TARGET_CONSTANT_ON_JOINT
    _assert_mapping_audit(
        partial, _audit_groups(observed_blank["group"], observed_blank["y"])
    )
    assert partial.n_joint_rows == 3
    assert partial.n_target_classes == 1
    assert partial.n_predictor_unobserved == 1


def test_missing_target_is_not_a_class() -> None:
    frame = pd.DataFrame(
        {
            "group": _categories(["A", "A", "B", "B", "A"], ["A", "B"]),
            "y": _categories(["0", "0", "1", "1", np.nan], ["0", "1"]),
        }
    )
    evidence = _predictor(_leakage(frame, "y"), "group").deterministic_mapping
    assert evidence.status is MappingStatus.DETERMINISTIC_REPEATED
    _assert_mapping_audit(evidence, _audit_groups(frame["group"], frame["y"]))
    assert evidence.n_applicable_rows == 4
    assert evidence.n_joint_rows == 4
    assert evidence.n_target_classes == 2
    assert evidence.n_conflicting_groups == 0


def test_numeric_target_does_not_treat_grouped_values_as_leakage() -> None:
    frame = pd.DataFrame(
        {
            "group": _categories(["A", "A", "B", "B"], ["A", "B"]),
            "y": [1.0, 1.0, 2.0, 2.0],
            "double": [2.0, 2.0, 4.0, 4.0],
        }
    )
    leakage = _leakage(frame, "y")
    group = _predictor(leakage, "group")
    assert group.exact_duplicate.status is (
        ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    )
    assert group.deterministic_mapping.status is MappingStatus.NOT_APPLICABLE
    assert _predictor(leakage, "double").exact_duplicate.status is (
        ExactDuplicateStatus.NOT_EQUAL
    )
    assert leakage.n_repeated_deterministic_mappings == 0
    assert leakage.n_exact_duplicates == 0


def test_strong_nondeterministic_association_is_not_leakage_evidence() -> None:
    rng = np.random.default_rng(11)
    n = 240
    group = rng.choice(["a", "b", "c"], size=n)
    base = np.where(group == "a", "yes", np.where(group == "b", "no", "maybe"))
    flipped = rng.random(n) < 0.2
    target = np.where(flipped, rng.choice(["yes", "no", "maybe"], size=n), base)
    frame = pd.DataFrame(
        {
            "group": pd.Series(group, dtype="category"),
            "noise": rng.normal(size=n),
            "y": pd.Series(target, dtype="category"),
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    leakage = analysis.target_leakage
    assert leakage is not None
    group_evidence = _predictor(leakage, "group")
    assert group_evidence.deterministic_mapping.status is MappingStatus.CONFLICTING
    assert group_evidence.exact_duplicate.status is ExactDuplicateStatus.NOT_EQUAL
    assert leakage.n_repeated_deterministic_mappings == 0
    assert leakage.n_exact_duplicates == 0
    _assert_mapping_audit(
        group_evidence.deterministic_mapping,
        _audit_groups(frame["group"], frame["y"]),
    )
    link = next(
        item
        for item in analysis.target_analysis.relationships
        if item.other_label == "group"
    )
    assert link.relationship.association.value > 0.4
    assert link.relationship.independence.frequentist.p_value < 1e-6
    by_label = {
        item.label: item for item in analysis.target_diagnostic.importance.predictors
    }
    assert by_label["group"].mean > by_label["noise"].mean
    assert by_label["group"].mean > 0.0
    noise = _predictor(leakage, "noise")
    assert (
        noise.deterministic_mapping.status is not MappingStatus.DETERMINISTIC_REPEATED
    )
    assert noise.exact_duplicate.status is (
        ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    )

    covariate = rng.normal(size=80)
    correlated = pd.DataFrame(
        {"x": covariate, "y": 3.0 * covariate + rng.normal(scale=0.05, size=80)}
    )
    correlated_analysis = analyze_dataframe(correlated, target="y")
    numeric = _predictor(correlated_analysis.target_leakage, "x")
    assert numeric.exact_duplicate.status is ExactDuplicateStatus.NOT_EQUAL
    assert numeric.deterministic_mapping.status is MappingStatus.NOT_APPLICABLE
    pair = correlated_analysis.target_analysis.relationships[0].relationship
    assert pair.pearson.estimate.value > 0.9
    assert pair.pearson.frequentist.p_value < 1e-6


def test_identifier_uniqueness_is_not_target_encoding() -> None:
    n = 40
    identifiers = [str(uuid.UUID(int=index + 1)) for index in range(n)]
    frame = pd.DataFrame(
        {
            "code": pd.Series(identifiers, dtype="string"),
            "y": pd.Series([index % 2 == 0 for index in range(n)], dtype="boolean"),
            "signal": np.linspace(-1.0, 1.0, n),
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    evidence = _predictor(analysis.target_leakage, "code")
    assert evidence.selected_type is SemanticType.IDENTIFIER
    assert evidence.exact_duplicate.status is (
        ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
    )
    assert evidence.deterministic_mapping.status is MappingStatus.TRIVIAL_UNIQUENESS
    _assert_mapping_audit(
        evidence.deterministic_mapping,
        _audit_groups(frame["code"], frame["y"]),
    )
    assert evidence.deterministic_mapping.n_repeated_groups == 0
    assert evidence.deterministic_mapping.n_distinct_groups == n
    retained_strings = _strings(analysis.target_leakage)
    assert not any(value in retained_strings for value in identifiers)
    decisions = {
        item.label: item.decision for item in analysis.target_diagnostic.predictors
    }
    assert decisions["code"] is PredictorDecision.IDENTIFIER
    assert "code" not in {
        item.label for item in analysis.target_diagnostic.included_predictors
    }
    assert len(pickle.dumps(analysis.target_leakage)) < 20_000


def test_repeated_identifier_groups_keep_mapping_evidence() -> None:
    n = 40
    identifiers = [str(uuid.UUID(int=(index // 2) + 1)) for index in range(n)]
    frame = pd.DataFrame(
        {
            "code": pd.Series(identifiers, dtype="string"),
            "y": pd.Series([index % 4 < 2 for index in range(n)], dtype="boolean"),
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    evidence = _predictor(analysis.target_leakage, "code")
    assert evidence.selected_type is SemanticType.IDENTIFIER
    assert evidence.deterministic_mapping.status is MappingStatus.DETERMINISTIC_REPEATED
    _assert_mapping_audit(
        evidence.deterministic_mapping,
        _audit_groups(frame["code"], frame["y"]),
    )
    assert evidence.deterministic_mapping.n_repeated_groups == 20
    decisions = {
        item.label: item.decision for item in analysis.target_diagnostic.predictors
    }
    assert decisions["code"] is PredictorDecision.IDENTIFIER


def test_datetime_text_and_constant_predictors_are_not_mapping_candidates() -> None:
    frame = pd.DataFrame(
        {
            "when": pd.date_range("2020-01-01", periods=12),
            "words": pd.Series(
                [f"alpha bravo {index}" for index in range(12)], dtype="string"
            ),
            "same": np.ones(12),
            "y": pd.Series([index % 2 == 0 for index in range(12)], dtype="boolean"),
        }
    )
    leakage = _leakage(frame, "y")
    for label in ("when", "words", "same"):
        evidence = _predictor(leakage, label)
        assert evidence.deterministic_mapping.status is MappingStatus.NOT_APPLICABLE
        assert evidence.exact_duplicate.status is (
            ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION
        )


def test_numeric_groups_of_a_classification_target_are_audited() -> None:
    values = np.array([1.0, 1.0, 2.0, 2.0, 3.0, np.nan])
    frame = pd.DataFrame(
        {
            "code": values,
            "y": _categories(["a", "a", "b", "b", "c", "a"], ["a", "b", "c"]),
        }
    )
    evidence = _predictor(_leakage(frame, "y"), "code").deterministic_mapping
    assert evidence.status is MappingStatus.DETERMINISTIC_REPEATED
    _assert_mapping_audit(
        evidence, _audit_groups(frame["code"], frame["y"], numeric=True)
    )
    assert evidence.n_predictor_unobserved == 1
    assert evidence.n_repeated_groups == 2
    assert evidence.n_singleton_groups == 1
    assert evidence.n_target_classes == 3


def test_small_exact_copy_is_retained_before_diagnostic_screening() -> None:
    frame = pd.DataFrame(
        {
            "y": pd.Series([index % 2 == 0 for index in range(8)], dtype="boolean"),
            "copy": pd.Series([index % 2 == 0 for index in range(8)], dtype="boolean"),
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    assert analysis.target_diagnostic.status is (
        DiagnosticStatus.INSUFFICIENT_TARGET_POPULATION
    )
    assert analysis.target_diagnostic.predictors == ()
    assert _predictor(analysis.target_leakage, "copy").exact_duplicate.status is (
        ExactDuplicateStatus.EXACT_DUPLICATE
    )


def test_results_drop_source_objects() -> None:
    frame = pd.DataFrame(
        {
            "group": _categories(["A", "A", "B", "B"] * 10, ["A", "B"]),
            "y": _categories(["0", "0", "1", "1"] * 10, ["0", "1"]),
            "noise": np.arange(40, dtype=np.float64),
        }
    )
    original = frame.copy(deep=True)
    analysis = analyze_dataframe(frame, target="y")
    pd.testing.assert_frame_equal(frame, original)
    leakage = analysis.target_leakage
    _assert_plain(leakage)
    plain = analyze_dataframe(frame)
    assert analysis.relationship_analysis == plain.relationship_analysis
    assert analysis.columns == plain.columns
    projected = project_target_analysis(
        analysis.columns,
        analysis.relationship_analysis.relationships,
        position=analysis.target_analysis.position,
        n_rows=analysis.n_rows,
    )
    assert projected == analysis.target_analysis
    adjusted = [
        link.relationship.independence.frequentist.adjusted_p_value
        for link in analysis.target_analysis.relationships
        if link.relationship is not None
        and link.relationship.family.value == "categorical_categorical"
    ]
    plain_adjusted = [
        record.independence.frequentist.adjusted_p_value
        for record in plain.relationship_analysis.relationships
        if record.family.value == "categorical_categorical"
    ]
    assert adjusted == plain_adjusted
    _assert_plain(leakage)


def test_leakage_has_no_score_and_does_not_name_association_methods() -> None:
    source = inspect.getsource(leakage_module)
    for word in ("pearson", "spearman", "cramer", "hedges", "p_value", "importance"):
        assert word not in source.lower()
    for cls in (
        TargetLeakageAnalysis,
        leakage_module.PredictorLeakage,
        ExactDuplicateEvidence,
        MappingEvidence,
    ):
        names = {field.name for field in dataclasses.fields(cls)}
        assert not any(
            token in name
            for name in names
            for token in ("score", "probability", "severity")
        )


def test_records_and_attachment_reject_inconsistent_evidence() -> None:
    with pytest.raises(ValueError, match="not compared"):
        ExactDuplicateEvidence(
            ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION, 1, 0, 0, 0, 0
        )
    with pytest.raises(ValueError, match="every applicable"):
        ExactDuplicateEvidence(ExactDuplicateStatus.EXACT_DUPLICATE, 2, 2, 0, 1, 1)
    with pytest.raises(ValueError, match="not counted"):
        MappingEvidence(MappingStatus.NOT_APPLICABLE, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError, match="no repeated group"):
        MappingEvidence(
            MappingStatus.TRIVIAL_UNIQUENESS, 2, 2, 0, 1, 1, 0, 0, 1, 2, 0, 2
        )
    population = LeakagePopulation(4, 1, 3, 0, 3)
    column_resolution = ResolutionStatus.RESOLVED
    predictor = leakage_module.PredictorLeakage(
        position=1,
        label="x",
        selected_type=SemanticType.NUMERIC,
        resolution_status=column_resolution,
        exact_duplicate=ExactDuplicateEvidence(
            ExactDuplicateStatus.NOT_EQUAL, 3, 3, 0, 1, 2
        ),
        deterministic_mapping=MappingEvidence(
            MappingStatus.NOT_APPLICABLE, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ),
    )
    with pytest.raises(ValueError, match="ascending"):
        TargetLeakageAnalysis(
            target_position=1,
            target_label="y",
            target_selected_type=SemanticType.NUMERIC,
            target_resolution_status=column_resolution,
            applicability=LeakageApplicability.APPLICABLE,
            population=population,
            predictors=(predictor,),
        )
    with pytest.raises(ValueError, match="only an applicable"):
        TargetLeakageAnalysis(
            target_position=0,
            target_label="y",
            target_selected_type=SemanticType.DATETIME,
            target_resolution_status=column_resolution,
            applicability=LeakageApplicability.TARGET_UNSUPPORTED,
            population=LeakagePopulation(4, 0, 4, 0, 0),
            predictors=(predictor,),
        )
    from pytics.analysis.target_diagnostic import PredictorEncoding
    from pytics.analysis.target_diagnostic import PredictorImportance

    frame = pd.DataFrame(
        {
            "y": np.arange(40, dtype=np.float64),
            "copy": np.arange(40, dtype=np.float64),
            "x": np.linspace(0.0, 1.0, 40),
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    fields = {
        field.name: getattr(analysis, field.name)
        for field in dataclasses.fields(DatasetAnalysis)
    }
    with pytest.raises(ValueError, match="requires its leakage"):
        DatasetAnalysis(**{**fields, "target_leakage": None})
    with pytest.raises(ValueError, match="requires target analysis"):
        DatasetAnalysis(**{**fields, "target_analysis": None, "target_leakage": None})
    leaked = analysis.target_leakage
    with pytest.raises(ValueError, match="name the analyzed target"):
        DatasetAnalysis(
            **{
                **fields,
                "target_leakage": dataclasses.replace(leaked, target_position=3),
            }
        )
    diagnostic = analysis.target_diagnostic
    copy = next(item for item in diagnostic.predictors if item.label == "copy")
    assert copy.decision is PredictorDecision.IDENTICAL_TO_TARGET
    included = dataclasses.replace(
        copy,
        decision=PredictorDecision.INCLUDED,
        encoding=PredictorEncoding.STANDARDIZED,
    )
    predictors = tuple(
        included if item.position == copy.position else item
        for item in diagnostic.predictors
    )
    decreases = diagnostic.importance.predictors[0].decreases
    ranked = tuple(
        sorted(
            (
                *diagnostic.importance.predictors,
                PredictorImportance(
                    position=copy.position, label=copy.label, decreases=decreases
                ),
            ),
            key=lambda item: item.position,
        )
    )
    with pytest.raises(ValueError, match="excluded from the diagnostic"):
        DatasetAnalysis(
            **{
                **fields,
                "target_diagnostic": dataclasses.replace(
                    diagnostic,
                    predictors=predictors,
                    importance=dataclasses.replace(
                        diagnostic.importance, predictors=ranked
                    ),
                ),
            }
        )
    with pytest.raises(TypeError, match="DataFrame"):
        analyze_target_leakage(frame.to_dict(), analysis.columns, analysis.target_analysis)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TargetAnalysis"):
        analyze_target_leakage(frame, analysis.columns, "y")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="frame shape"):
        analyze_target_leakage(
            frame.iloc[:-1], analysis.columns, analysis.target_analysis
        )
    with pytest.raises(TypeError, match="ColumnAnalysis"):
        analyze_target_leakage(frame, ("column",), analysis.target_analysis)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="column position"):
        analyze_target_leakage(
            frame,
            (analysis.columns[1], analysis.columns[0], analysis.columns[2]),
            analysis.target_analysis,
        )
    narrow = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 4.0, 5.0]})
    narrow_analysis = analyze_dataframe(narrow, target="b")
    with pytest.raises(ValueError, match="outside the column axis"):
        analyze_target_leakage(
            narrow.iloc[:, :1],
            narrow_analysis.columns[:1],
            narrow_analysis.target_analysis,
        )
    with pytest.raises(TypeError, match="TargetLeakageAnalysis"):
        leakage_module.exact_duplicate_positions(analysis)  # type: ignore[arg-type]
    assert leakage_module._same_value(True, 1) is False
    assert leakage_module._same_value(float("1.5"), float("1.5")) is True
    with pytest.raises(ValueError, match="no leakage applicability"):
        leakage_module._applicability_for("supported")


def test_non_finite_targets_and_empty_joint_rows_are_explicit() -> None:
    numeric = pd.DataFrame(
        {
            "y": [1.0, 2.0, np.inf, np.nan],
            "copy": [1.0, 2.0, 9.0, 8.0],
        }
    )
    leakage = _leakage(numeric, "y")
    assert leakage.population.n_target_non_finite == 1
    assert leakage.population.n_target_missing == 1
    assert leakage.population.n_applicable == 2
    assert _predictor(leakage, "copy").exact_duplicate.status is (
        ExactDuplicateStatus.EXACT_DUPLICATE
    )

    hidden = pd.DataFrame(
        {
            "y": _categories(["a", "a", "b", "b", np.nan, np.nan], ["a", "b"]),
            "code": [np.nan, np.nan, np.nan, np.nan, 1.0, 2.0],
            "label": _categories(
                [np.nan, np.nan, np.nan, np.nan, "p", "q"],
                ["p", "q"],
            ),
        }
    )
    hidden_leakage = _leakage(hidden, "y")
    code = _predictor(hidden_leakage, "code").deterministic_mapping
    assert code.status is MappingStatus.INSUFFICIENT_POPULATION
    assert code.n_joint_rows == 0
    assert code.n_predictor_unobserved == 4
    label = _predictor(hidden_leakage, "label")
    assert label.exact_duplicate.status is ExactDuplicateStatus.INSUFFICIENT_POPULATION
    assert label.exact_duplicate.n_joint_rows == 0
    assert label.deterministic_mapping.status is MappingStatus.INSUFFICIENT_POPULATION


def test_retained_records_reject_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="must reconcile"):
        LeakagePopulation(3, 1, 1, 0, 1)
    with pytest.raises(ValueError, match="observed target rows"):
        LeakagePopulation(4, 1, 3, 4, 0)
    with pytest.raises(ValueError, match="finite observed"):
        LeakagePopulation(2, 0, 2, 0, 3)
    with pytest.raises(ValueError, match="only after a match"):
        ExactDuplicateEvidence(
            ExactDuplicateStatus.MISSINGNESS_BLOCKS_EQUALITY, 2, 2, 0, 2, 0
        )
    with pytest.raises(ValueError, match="disagreeing row"):
        ExactDuplicateEvidence(ExactDuplicateStatus.NOT_EQUAL, 2, 2, 0, 2, 0)
    with pytest.raises(ValueError, match="no joint row"):
        ExactDuplicateEvidence(
            ExactDuplicateStatus.INSUFFICIENT_POPULATION, 2, 1, 1, 1, 0
        )
    with pytest.raises(ValueError, match="must reconcile"):
        ExactDuplicateEvidence(ExactDuplicateStatus.NOT_EQUAL, 3, 1, 1, 1, 0)
    with pytest.raises(ValueError, match="no joint row"):
        MappingEvidence(
            MappingStatus.INSUFFICIENT_POPULATION, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1
        )
    with pytest.raises(ValueError, match="conflicting group"):
        MappingEvidence(MappingStatus.CONFLICTING, 2, 2, 0, 1, 1, 0, 0, 1, 2, 0, 2)
    with pytest.raises(ValueError, match="one class"):
        MappingEvidence(
            MappingStatus.TARGET_CONSTANT_ON_JOINT, 2, 2, 0, 1, 1, 0, 0, 1, 2, 0, 2
        )
    with pytest.raises(ValueError, match="more than one class"):
        MappingEvidence(
            MappingStatus.TRIVIAL_UNIQUENESS, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1
        )
    with pytest.raises(ValueError, match="no conflicting group"):
        MappingEvidence(
            MappingStatus.DETERMINISTIC_REPEATED, 2, 2, 0, 1, 1, 0, 1, 0, 2, 2, 2
        )
    with pytest.raises(ValueError, match="more than one class"):
        MappingEvidence(
            MappingStatus.DETERMINISTIC_REPEATED, 2, 2, 0, 1, 1, 0, 0, 1, 2, 0, 1
        )
    with pytest.raises(ValueError, match="rows must reconcile"):
        MappingEvidence(
            MappingStatus.TRIVIAL_UNIQUENESS, 3, 2, 0, 2, 0, 2, 0, 0, 0, 0, 2
        )
    with pytest.raises(ValueError, match="groups must reconcile"):
        MappingEvidence(
            MappingStatus.TRIVIAL_UNIQUENESS, 2, 2, 0, 2, 0, 1, 0, 0, 0, 0, 2
        )
    with pytest.raises(ValueError, match="repeated groups must reconcile"):
        MappingEvidence(
            MappingStatus.DETERMINISTIC_REPEATED, 4, 4, 0, 2, 2, 0, 0, 1, 4, 0, 2
        )
    with pytest.raises(ValueError, match="cover the joint"):
        MappingEvidence(
            MappingStatus.TRIVIAL_UNIQUENESS, 2, 2, 0, 2, 0, 2, 0, 0, 1, 0, 2
        )
    with pytest.raises(ValueError, match="conflicting rows require"):
        MappingEvidence(
            MappingStatus.TRIVIAL_UNIQUENESS, 2, 2, 0, 2, 0, 2, 0, 0, 0, 2, 2
        )
    with pytest.raises(ValueError, match="at least two rows"):
        MappingEvidence(MappingStatus.CONFLICTING, 2, 2, 0, 1, 1, 0, 1, 0, 2, 1, 2)
    with pytest.raises(ValueError, match="are repeated rows"):
        MappingEvidence(MappingStatus.CONFLICTING, 3, 3, 0, 2, 1, 1, 1, 0, 2, 3, 2)
    with pytest.raises(ValueError, match="no target class"):
        MappingEvidence(
            MappingStatus.INSUFFICIENT_POPULATION, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1
        )
    with pytest.raises(ValueError, match="resolution selected one"):
        leakage_module.PredictorLeakage(
            position=1,
            label="x",
            selected_type=None,
            resolution_status=ResolutionStatus.RESOLVED,
            exact_duplicate=ExactDuplicateEvidence(
                ExactDuplicateStatus.INCOMPATIBLE_REPRESENTATION, 0, 0, 0, 0, 0
            ),
            deterministic_mapping=MappingEvidence(
                MappingStatus.NOT_APPLICABLE, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            ),
        )
    with pytest.raises(TypeError, match="tuple"):
        TargetLeakageAnalysis(
            target_position=0,
            target_label="y",
            target_selected_type=SemanticType.NUMERIC,
            target_resolution_status=ResolutionStatus.RESOLVED,
            applicability=LeakageApplicability.APPLICABLE,
            population=LeakagePopulation(2, 0, 2, 0, 2),
            predictors=[],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="no comparison rows"):
        TargetLeakageAnalysis(
            target_position=0,
            target_label="y",
            target_selected_type=SemanticType.DATETIME,
            target_resolution_status=ResolutionStatus.RESOLVED,
            applicability=LeakageApplicability.TARGET_UNSUPPORTED,
            population=LeakagePopulation(2, 0, 2, 0, 1),
        )
    with pytest.raises(ValueError, match="finite observed target rows"):
        TargetLeakageAnalysis(
            target_position=0,
            target_label="y",
            target_selected_type=SemanticType.NUMERIC,
            target_resolution_status=ResolutionStatus.RESOLVED,
            applicability=LeakageApplicability.APPLICABLE,
            population=LeakagePopulation(4, 0, 4, 1, 2),
        )
    with pytest.raises(ValueError, match="only after a match"):
        ExactDuplicateEvidence(
            ExactDuplicateStatus.MISSINGNESS_BLOCKS_EQUALITY, 2, 0, 2, 0, 0
        )
    with pytest.raises(ValueError, match="resolution selected one"):
        TargetLeakageAnalysis(
            target_position=0,
            target_label="y",
            target_selected_type=None,
            target_resolution_status=ResolutionStatus.RESOLVED,
            applicability=LeakageApplicability.TARGET_UNRESOLVED,
            population=LeakagePopulation(2, 0, 2, 0, 0),
        )


def test_attachment_rejects_a_leakage_result_that_is_not_the_target() -> None:
    frame = pd.DataFrame(
        {
            "y": np.arange(30, dtype=np.float64),
            "x": np.arange(30, dtype=np.float64) + 1.0,
        }
    )
    analysis = analyze_dataframe(frame, target="y")
    fields = {
        field.name: getattr(analysis, field.name)
        for field in dataclasses.fields(DatasetAnalysis)
    }
    leaked = analysis.target_leakage
    population = leaked.population
    shifted = LeakagePopulation(
        population.n_total_rows + 1,
        population.n_target_missing + 1,
        population.n_target_observed,
        population.n_target_non_finite,
        population.n_applicable,
    )
    with pytest.raises(ValueError, match="leakage rows"):
        DatasetAnalysis(
            **{
                **fields,
                "target_leakage": dataclasses.replace(leaked, population=shifted),
            }
        )
    relabeled = dataclasses.replace(leaked, target_label="other")
    with pytest.raises(ValueError, match="name the analyzed target"):
        DatasetAnalysis(**{**fields, "target_leakage": relabeled})
    retyped = dataclasses.replace(leaked, target_selected_type=SemanticType.BOOLEAN)
    with pytest.raises(ValueError, match="selected type"):
        DatasetAnalysis(**{**fields, "target_leakage": retyped})
    renamed = dataclasses.replace(
        leaked.predictors[0],
        label="other",
    )
    with pytest.raises(ValueError, match="must be its column"):
        DatasetAnalysis(
            **{
                **fields,
                "target_leakage": dataclasses.replace(leaked, predictors=(renamed,)),
            }
        )
    with pytest.raises(ValueError, match="every other column"):
        DatasetAnalysis(
            **{**fields, "target_leakage": dataclasses.replace(leaked, predictors=())}
        )
    finite_gap = LeakagePopulation(
        population.n_total_rows,
        population.n_target_missing,
        population.n_target_observed,
        1,
        population.n_applicable - 1,
    )
    with pytest.raises(ValueError, match="finite target rows"):
        DatasetAnalysis(
            **{
                **fields,
                "target_leakage": dataclasses.replace(leaked, population=finite_gap),
            }
        )
