"""Dataset-level relationship correction and coverage consolidation."""

from __future__ import annotations

import dataclasses
import math
import time
import tracemalloc

import numpy as np
import pandas as pd
import pytest

import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.relationships.adjustment as adjustment_module
import pytics.analysis.relationships.boolean_boolean as boolean_module
import pytics.analysis.relationships.categorical_categorical as categorical_module
import pytics.analysis.relationships.collector as collector_module
import pytics.analysis.relationships.numeric_boolean as numeric_boolean_module
import pytics.analysis.relationships.numeric_categorical as numeric_categorical_module
import pytics.analysis.relationships.numeric_numeric as numeric_numeric_module
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationship import BooleanBooleanRelationship
from pytics.analysis.relationship import CategoricalCategoricalRelationship
from pytics.analysis.relationship import FrequentistEvidence
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericBooleanRelationship
from pytics.analysis.relationship import NumericCategoricalRelationship
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import RelationshipFamily
from pytics.analysis.relationship import RelationshipRecord
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.relationship import UnimplementedRelationshipFamily
from pytics.analysis.relationship import build_relationships_summary
from pytics.analysis.relationships.adjustment import adjust_primary_p_values
from pytics.analysis.relationships.models import InferentialValidity
from pytics.analysis.relationships.adjustment import benjamini_hochberg
from pytics.analysis.relationships.collector import _Eligibility
from pytics.analysis.relationships.collector import _pair_class
from pytics.semantics.interpretation import SemanticType

try:
    from statsmodels.stats.multitest import multipletests
except ImportError:  # pragma: no cover - optional development reference
    multipletests = None

BH = MultipleTestingAdjustment.BENJAMINI_HOCHBERG
NOT_APPLIED = MultipleTestingAdjustment.NOT_APPLIED
AVAILABLE = ResultAvailability.AVAILABLE
UNAVAILABLE = ResultAvailability.UNAVAILABLE
_HAND_RAW = (0.001, 0.01, 0.02, 0.2, 0.8)
_HAND_ADJUSTED = (0.005, 0.025, 1 / 30, 0.25, 0.8)
_UUIDS = (
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b814-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b815-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b816-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b817-9dad-11d1-80b4-00c04fd430c8",
)


def _independent_bh(p_values: tuple[float, ...]) -> tuple[float, ...]:
    """NumPy Benjamini–Hochberg. This is not the production helper."""
    if not p_values:
        return ()
    values = np.asarray(p_values, dtype=np.float64)
    order = np.argsort(values, kind="mergesort")
    ranked = values[order]
    factors = np.arange(1, values.size + 1, dtype=np.float64)
    corrected = ranked * values.size / factors
    np.minimum(corrected, 1.0, out=corrected)
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    restored = np.empty(values.size, dtype=np.float64)
    restored[order] = corrected
    return tuple(float(0.0 if item == 0.0 else item) for item in restored)


def _assert_matches_reference(raw: tuple[float, ...]) -> tuple[float, ...]:
    produced = benjamini_hochberg(raw)
    reference = _independent_bh(raw)
    assert produced == pytest.approx(reference, abs=1e-12)
    if multipletests is not None and raw:
        _reject, corrected, _alphac, _alphac_sidak = multipletests(
            raw,
            method="fdr_bh",
        )
        assert produced == pytest.approx(
            [float(item) for item in corrected],
            abs=1e-12,
        )
    ordered = sorted(range(len(raw)), key=lambda index: (raw[index], index))
    previous = 0.0
    for index in ordered:
        assert 0.0 <= produced[index] <= 1.0
        assert produced[index] + 1e-12 >= raw[index]
        assert produced[index] + 1e-12 >= previous
        previous = produced[index]
    return produced


def _parts(
    record: RelationshipRecord,
) -> tuple[tuple[str, FrequentistEvidence], ...]:
    if isinstance(record, NumericNumericRelationship):
        return (
            ("spearman", record.spearman.frequentist),
            ("pearson", record.pearson.frequentist),
        )
    if isinstance(record, NumericCategoricalRelationship):
        return (("anova", record.omnibus.frequentist),)
    if isinstance(record, NumericBooleanRelationship):
        return (("welch", record.mean_difference_test.frequentist),)
    if isinstance(record, BooleanBooleanRelationship):
        return (("fisher", record.independence.frequentist),)
    if isinstance(record, CategoricalCategoricalRelationship):
        return (("chi_square", record.independence.frequentist),)
    raise AssertionError(type(record))


def _mixed_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "n1": [1, 2, 3, 4, 5, 6, 7, 8],
            "n2": [1, 2, 4, 3, 6, 5, 8, 7],
            "c1": pd.Categorical(["a", "a", "a", "a", "b", "b", "b", "b"]),
            "b1": [False, False, False, False, True, True, True, True],
            "b2": [False, True, False, True, False, True, False, True],
            "c2": pd.Categorical(["x", "y", "x", "y", "x", "y", "x", "y"]),
        }
    )


def _analysis(frame: pd.DataFrame):
    return analyze_dataframe(frame).relationship_analysis


def test_benjamini_hochberg_matches_the_hand_vector_and_an_independent_reference() -> (
    None
):
    produced = _assert_matches_reference(_HAND_RAW)
    assert produced == pytest.approx(_HAND_ADJUSTED, abs=1e-12)
    reversed_values = benjamini_hochberg(tuple(reversed(_HAND_RAW)))
    assert reversed_values == pytest.approx(tuple(reversed(_HAND_ADJUSTED)), abs=1e-12)


@pytest.mark.parametrize(
    "raw",
    [
        (),
        (0.2,),
        (0.01, 0.04),
        (0.2, 0.2, 0.2),
        (1.0, 1.0, 1.0),
        (0.0, 0.0, 0.2),
        (0.0,),
        (1e-320, 1e-300, 0.5),
        (0.01, 0.04, 0.01),
        (0.5, 0.01, 0.5, 0.01),
    ],
)
def test_benjamini_hochberg_edges_are_deterministic(raw: tuple[float, ...]) -> None:
    produced = _assert_matches_reference(raw)
    if not raw:
        assert produced == ()
        return
    if len(raw) == 1:
        assert produced == raw
    if len(set(raw)) == 1:
        assert produced == pytest.approx(tuple(value for value in raw))
    order = list(range(len(raw) - 1, -1, -1))
    permuted = tuple(raw[index] for index in order)
    restored = [0.0] * len(raw)
    adjusted = benjamini_hochberg(permuted)
    for position, index in enumerate(order):
        restored[index] = adjusted[position]
    assert tuple(restored) == pytest.approx(produced, abs=1e-12)


def test_equal_raw_p_values_do_not_depend_on_traversal_order() -> None:
    left = benjamini_hochberg((0.01, 0.2, 0.01, 0.4))
    right = benjamini_hochberg((0.01, 0.01, 0.4, 0.2))
    assert left[0] == pytest.approx(left[2])
    assert right[0] == pytest.approx(right[1])
    assert left[0] == pytest.approx(right[0])
    assert left[1] == pytest.approx(right[3])


def test_non_finite_p_values_do_not_enter_correction() -> None:
    with pytest.raises(ValueError, match="finite float"):
        benjamini_hochberg((0.1, float("nan")))
    with pytest.raises(ValueError, match="finite float"):
        benjamini_hochberg((float("inf"),))
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        benjamini_hochberg((-0.1,))
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        benjamini_hochberg((1.1,))


def test_large_correction_family_stays_linear() -> None:
    values = tuple((index % 1000) / 999 for index in range(100_000))
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    started = time.perf_counter()
    produced = benjamini_hochberg(values)
    elapsed = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(produced) == 100_000
    assert elapsed < 15.0
    assert peak - before < 64 * 1024 * 1024
    assert produced[0] == 0.0
    assert produced[-1] <= 1.0
    sample = tuple(values[index] for index in range(0, 100_000, 1000))
    assert benjamini_hochberg(sample) == pytest.approx(
        _independent_bh(sample),
        abs=1e-12,
    )


def test_correction_family_contains_each_primary_test_once() -> None:
    retained = _analysis(_mixed_frame())
    adjusted: dict[RelationshipFamily, int] = {}
    pearson_raw = 0
    pearson_adjusted = 0
    for record in retained.relationships:
        for name, evidence in _parts(record):
            if name == "pearson":
                assert evidence.availability is AVAILABLE
                assert evidence.inferential_validity is InferentialValidity.VALID
                assert evidence.adjustment is NOT_APPLIED
                assert evidence.adjusted_p_value is None
                pearson_raw += 1
                if evidence.adjustment is BH:
                    pearson_adjusted += 1
                continue
            assert evidence.availability is AVAILABLE
            if evidence.inferential_validity is not InferentialValidity.VALID:
                assert name == "chi_square"
                assert evidence.inferential_validity is InferentialValidity.INVALID
                assert evidence.adjustment is NOT_APPLIED
                assert evidence.adjusted_p_value is None
                continue
            assert evidence.adjustment is BH
            assert evidence.adjusted_p_value is not None
            assert evidence.adjusted_p_value + 1e-12 >= evidence.p_value
            adjusted[record.family] = adjusted.get(record.family, 0) + 1
    assert adjusted == {
        RelationshipFamily.NUMERIC_NUMERIC: 1,
        RelationshipFamily.NUMERIC_CATEGORICAL: 4,
        RelationshipFamily.NUMERIC_BOOLEAN: 4,
        RelationshipFamily.BOOLEAN_BOOLEAN: 1,
    }
    assert sum(adjusted.values()) == 10
    assert pearson_raw == 1
    assert pearson_adjusted == 0
    assert retained.n_supported_pairs == 11
    assert retained.n_unimplemented_family_pairs == 4


def test_calculators_emit_raw_evidence_and_replacement_is_shallow() -> None:
    seen: list[tuple[RelationshipRecord, ...]] = []
    original = collector_module.adjust_primary_p_values

    def _spy(
        relationships: tuple[RelationshipRecord, ...],
    ) -> tuple[RelationshipRecord, ...]:
        seen.append(relationships)
        return original(relationships)

    collector_module.adjust_primary_p_values = _spy
    try:
        retained = _analysis(_mixed_frame())
    finally:
        collector_module.adjust_primary_p_values = original
    assert len(seen) == 1
    before = seen[0]
    assert len(before) == len(retained.relationships)
    for raw, adjusted in zip(before, retained.relationships):
        for (_raw_name, raw_evidence), (name, adjusted_evidence) in zip(
            _parts(raw),
            _parts(adjusted),
        ):
            assert raw_evidence.adjustment is NOT_APPLIED
            assert raw_evidence.adjusted_p_value is None
            assert adjusted_evidence.p_value == raw_evidence.p_value
            if name == "pearson" or raw_evidence.availability is UNAVAILABLE:
                assert adjusted_evidence is raw_evidence
        if isinstance(raw, NumericNumericRelationship):
            assert isinstance(adjusted, NumericNumericRelationship)
            assert adjusted.pearson is raw.pearson
            assert adjusted.spearman.estimate is raw.spearman.estimate
            assert adjusted.spearman.confidence_interval is (
                raw.spearman.confidence_interval
            )
        elif isinstance(raw, NumericCategoricalRelationship):
            assert isinstance(adjusted, NumericCategoricalRelationship)
            assert adjusted.groups is raw.groups
            assert adjusted.effect is raw.effect
        elif isinstance(raw, NumericBooleanRelationship):
            assert isinstance(adjusted, NumericBooleanRelationship)
            assert adjusted.mean_difference is raw.mean_difference
            assert adjusted.standardized_mean_difference is (
                raw.standardized_mean_difference
            )
            assert adjusted.mean_difference_interval is raw.mean_difference_interval
        elif isinstance(raw, BooleanBooleanRelationship):
            assert isinstance(adjusted, BooleanBooleanRelationship)
            assert adjusted.table is raw.table
            assert adjusted.phi is raw.phi
        else:
            assert isinstance(raw, CategoricalCategoricalRelationship)
            assert isinstance(adjusted, CategoricalCategoricalRelationship)
            assert adjusted.table is raw.table
            assert adjusted.association is raw.association
            assert adjusted.expected_counts is raw.expected_counts


def test_adding_a_hypothesis_changes_adjusted_p_values_only() -> None:
    base = pd.DataFrame(
        {"n1": [1, 2, 3, 4, 5, 6, 7, 8], "n2": [1, 2, 4, 3, 6, 5, 8, 7]}
    )
    wider = base.copy()
    wider["n3"] = [8, 1, 7, 2, 6, 3, 5, 4]
    first = _analysis(base).relationships[0]
    second = next(
        item
        for item in _analysis(wider).relationships
        if isinstance(item, NumericNumericRelationship)
        and (item.left_position, item.right_position) == (0, 1)
    )
    assert isinstance(first, NumericNumericRelationship)
    assert second.spearman.frequentist.p_value == first.spearman.frequentist.p_value
    assert second.spearman.estimate == first.spearman.estimate
    assert second.pearson == first.pearson
    assert second.spearman.frequentist.adjusted_p_value != (
        first.spearman.frequentist.adjusted_p_value
    )
    assert second.spearman.frequentist.adjusted_p_value > (
        first.spearman.frequentist.adjusted_p_value
    )


def test_an_ineligible_column_does_not_change_the_correction_family() -> None:
    base = pd.DataFrame({"n1": [1, 2, 3, 4, 5, 6], "n2": [2, 1, 4, 3, 6, 5]})
    extra = base.copy()
    extra["code"] = list(_UUIDS[:6])
    first = _analysis(base).relationships[0]
    second = _analysis(extra).relationships[0]
    assert isinstance(first, NumericNumericRelationship)
    assert isinstance(second, NumericNumericRelationship)
    assert second.spearman.frequentist == first.spearman.frequentist
    assert second.pearson == first.pearson
    assert _analysis(extra).n_ineligible_pairs == 2


def test_unavailable_primary_p_values_do_not_enter_m() -> None:
    base = pd.DataFrame(
        {
            "n1": [1.0, 2, 3, 4, 5, 6, 7, 8],
            "n2": [2.0, 1, 4, 3, 6, 5, 8, 7],
        }
    )
    wider = base.copy()
    wider["a"] = [1.0, 3.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    wider["b"] = [4.0, 2.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    alone = _analysis(base).relationships[0]
    retained = _analysis(wider)
    paired = next(
        item
        for item in retained.relationships
        if isinstance(item, NumericNumericRelationship)
        and (item.left_position, item.right_position) == (0, 1)
    )
    short = next(
        item
        for item in retained.relationships
        if isinstance(item, NumericNumericRelationship)
        and (item.left_position, item.right_position) == (2, 3)
    )
    assert isinstance(alone, NumericNumericRelationship)
    assert paired.spearman.frequentist == alone.spearman.frequentist
    assert paired.spearman.estimate == alone.spearman.estimate
    assert short.spearman.estimate.availability is AVAILABLE
    assert short.spearman.frequentist.availability is UNAVAILABLE
    assert short.spearman.frequentist.adjustment is NOT_APPLIED
    assert short.spearman.frequentist.adjusted_p_value is None
    assert short.n_paired == 2


def test_sparse_chi_square_does_not_enter_the_correction_family() -> None:
    frame = pd.DataFrame(
        {
            "left": pd.Categorical(["a"] * 5 + ["b"]),
            "right": pd.Categorical(["x"] * 5 + ["y"]),
        }
    )
    relationship = _analysis(frame).relationships[0]
    assert isinstance(relationship, CategoricalCategoricalRelationship)
    assert relationship.expected_counts.minimum_expected_count < 1.0
    evidence = relationship.independence.frequentist
    assert evidence.availability is AVAILABLE
    assert evidence.p_value is not None
    assert evidence.inferential_validity is InferentialValidity.INVALID
    assert evidence.adjustment is NOT_APPLIED
    assert evidence.adjusted_p_value is None


def test_perfect_and_null_p_values_stay_inside_the_unit_interval() -> None:
    values = list(range(1, 31))
    perfect = _analysis(
        pd.DataFrame({"x": values, "y": [2 * value for value in values]})
    ).relationships[0]
    assert isinstance(perfect, NumericNumericRelationship)
    assert perfect.spearman.frequentist.p_value == 0.0
    assert perfect.spearman.frequentist.adjusted_p_value == 0.0
    assert perfect.spearman.frequentist.adjustment is BH
    assert perfect.pearson.frequentist.adjustment is NOT_APPLIED
    assert perfect.pearson.frequentist.p_value is not None
    balanced = _analysis(
        pd.DataFrame(
            {
                "left": [False, False, True, True],
                "right": [False, True, False, True],
            }
        )
    ).relationships[0]
    assert isinstance(balanced, BooleanBooleanRelationship)
    assert balanced.independence.frequentist.p_value == pytest.approx(1.0)
    assert balanced.independence.frequentist.adjusted_p_value == pytest.approx(1.0)


def test_row_and_column_order_preserve_adjusted_evidence() -> None:
    frame = _mixed_frame()
    forward = _analysis(frame)
    backward = _analysis(frame.iloc[::-1].reset_index(drop=True))
    assert backward.relationships == forward.relationships
    order = ["c2", "b2", "n2", "c1", "b1", "n1"]
    reordered = _analysis(frame.loc[:, order])
    by_forward = _by_column_names(frame, forward.relationships)
    by_reordered = _by_column_names(frame.loc[:, order], reordered.relationships)
    assert set(by_forward) == set(by_reordered)
    for key, record in by_forward.items():
        other = by_reordered[key]
        for (_name, left), (_other_name, right) in zip(_parts(record), _parts(other)):
            assert right.p_value == left.p_value
            assert right.adjusted_p_value == left.adjusted_p_value
            assert right.adjustment is left.adjustment


def _by_column_names(
    frame: pd.DataFrame,
    relationships: tuple[RelationshipRecord, ...],
) -> dict[tuple[str, str], RelationshipRecord]:
    found = {}
    for record in relationships:
        left = str(frame.columns[record.left_position])
        right = str(frame.columns[record.right_position])
        found[tuple(sorted((left, right)))] = record
    return found


def test_two_group_numeric_families_share_descriptive_facts() -> None:
    values = [1.0, 10.0, 2.0, 30.0, 3.0, 11.0, 4.0, 40.0]
    flag = [True, False, True, False, True, False, True, False]
    labels = ["true" if item else "false" for item in flag]
    boolean = _analysis(pd.DataFrame({"y": values, "flag": flag})).relationships[0]
    categorical = _analysis(
        pd.DataFrame(
            {
                "y": values,
                "group": pd.Categorical(labels, categories=["false", "true"]),
            }
        )
    ).relationships[0]
    assert isinstance(boolean, NumericBooleanRelationship)
    assert isinstance(categorical, NumericCategoricalRelationship)
    false_group, true_group = categorical.groups
    assert false_group.category == "false"
    assert true_group.category == "true"
    assert false_group.n == boolean.false_group.n == 4
    assert true_group.n == boolean.true_group.n == 4
    assert false_group.descriptive.mean == pytest.approx(
        boolean.false_group.descriptive.mean
    )
    assert true_group.descriptive.mean == pytest.approx(
        boolean.true_group.descriptive.mean
    )
    assert boolean.mean_difference.value == pytest.approx(
        true_group.descriptive.mean - false_group.descriptive.mean
    )
    assert boolean.mean_difference_test.frequentist.p_value != pytest.approx(
        categorical.omnibus.frequentist.p_value
    )


def test_two_by_two_cramers_v_matches_absolute_boolean_phi() -> None:
    counts = (2, 3, 4, 5)
    conditioning = [False] * (counts[0] + counts[1]) + [True] * (counts[2] + counts[3])
    outcome = (
        [False] * counts[0]
        + [True] * counts[1]
        + [False] * counts[2]
        + [True] * counts[3]
    )
    boolean = _analysis(
        pd.DataFrame({"left": conditioning, "right": outcome})
    ).relationships[0]
    categorical = _analysis(
        pd.DataFrame(
            {
                "left": pd.Categorical(
                    ["f"] * (counts[0] + counts[1]) + ["t"] * (counts[2] + counts[3]),
                    categories=["f", "t"],
                ),
                "right": pd.Categorical(
                    ["f"] * counts[0]
                    + ["t"] * counts[1]
                    + ["f"] * counts[2]
                    + ["t"] * counts[3],
                    categories=["f", "t"],
                ),
            }
        )
    ).relationships[0]
    assert isinstance(boolean, BooleanBooleanRelationship)
    assert isinstance(categorical, CategoricalCategoricalRelationship)
    assert categorical.association.value == pytest.approx(abs(boolean.phi.value))
    assert boolean.phi.value < 0.0
    assert boolean.independence.method.value == "fisher_exact"
    assert categorical.independence.method.value == "pearson_chi_square"


def test_coverage_categories_classify_a_mixed_semantic_frame() -> None:
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3, 4],
            "group": pd.Categorical(["a", "b", "a", "b"]),
            "flag": [True, False, True, False],
            "when": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
            ),
            "code": pd.Series(_UUIDS[:4], dtype="string"),
            "fixed": [7, 7, 7, 7],
            "blank": pd.Series([pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64"),
            "duration": pd.to_timedelta(["1 day", "2 days", "3 days", "4 days"]),
            "note": pd.Series(["alpha", "beta", "gamma", "delta"], dtype="string"),
        }
    )
    analysis = analyze_dataframe(frame)
    assert [column.inferred.selected_type for column in analysis.columns] == [
        SemanticType.NUMERIC,
        SemanticType.CATEGORICAL,
        SemanticType.BOOLEAN,
        SemanticType.DATETIME,
        SemanticType.IDENTIFIER,
        SemanticType.CONSTANT,
        SemanticType.EMPTY,
        SemanticType.TIMEDELTA,
        None,
    ]
    summary = build_relationships_summary(analysis)
    assert summary.n_total_pairs == 36
    assert summary.n_supported_pairs == summary.n_analyzed_pairs == 2
    assert summary.n_unimplemented_family_pairs == 3
    assert summary.n_ineligible_pairs == 31
    assert {
        item.family: item.n_pairs for item in summary.unimplemented_family_counts
    } == {
        UnimplementedRelationshipFamily.DATETIME_NUMERIC: 1,
        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL: 1,
        UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN: 1,
    }
    assert _pair_class(SemanticType.CATEGORICAL, SemanticType.BOOLEAN) is (
        UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN
    )
    assert _pair_class(SemanticType.BOOLEAN, SemanticType.CATEGORICAL) is (
        UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN
    )
    assert _pair_class(SemanticType.DATETIME, SemanticType.NUMERIC) is (
        UnimplementedRelationshipFamily.DATETIME_NUMERIC
    )
    assert _pair_class(SemanticType.NUMERIC, SemanticType.DATETIME) is (
        UnimplementedRelationshipFamily.DATETIME_NUMERIC
    )
    assert _pair_class(SemanticType.DATETIME, SemanticType.CATEGORICAL) is (
        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL
    )
    for left, right in (
        (SemanticType.DATETIME, SemanticType.BOOLEAN),
        (SemanticType.DATETIME, SemanticType.DATETIME),
        (SemanticType.IDENTIFIER, SemanticType.NUMERIC),
        (SemanticType.TEXT, SemanticType.CATEGORICAL),
        (SemanticType.TIMEDELTA, SemanticType.NUMERIC),
        (SemanticType.EMPTY, SemanticType.BOOLEAN),
        (SemanticType.CONSTANT, SemanticType.CATEGORICAL),
        (None, SemanticType.NUMERIC),
    ):
        assert _pair_class(left, right) is _Eligibility.INELIGIBLE


def _assert_plain(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, (pd.DataFrame, pd.Series, pd.Index, np.ndarray))
    assert not callable(value)
    assert not type(value).__module__.startswith(("scipy", "pandas.core", "numpy"))
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_plain(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_plain(item, seen)


def test_summary_keeps_adjusted_evidence_without_recomputing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = analyze_dataframe(_mixed_frame())
    original = next(
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, NumericNumericRelationship)
    )
    raw_p = original.spearman.frequentist.p_value
    adjusted_p = original.spearman.frequentist.adjusted_p_value

    def _fail(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("summary builder recomputed a relationship")

    monkeypatch.setattr(adjustment_module, "benjamini_hochberg", _fail)
    monkeypatch.setattr(adjustment_module, "adjust_primary_p_values", _fail)
    monkeypatch.setattr(collector_module, "adjust_primary_p_values", _fail)
    monkeypatch.setattr(collector_module, "_association_methods", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_categorical", _fail)
    monkeypatch.setattr(collector_module, "_analyze_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_categorical_categorical", _fail)
    monkeypatch.setattr(collector_module, "_read_numeric_column", _fail)
    monkeypatch.setattr(collector_module, "_read_categorical_column", _fail)
    monkeypatch.setattr(collector_module, "_read_boolean_column", _fail)
    monkeypatch.setattr(numeric_numeric_module, "spearmanr", _fail)
    monkeypatch.setattr(numeric_numeric_module, "pearsonr", _fail)
    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _fail)
    monkeypatch.setattr(boolean_module, "fisher_exact", _fail)
    monkeypatch.setattr(numeric_boolean_module, "student_t", _fail)
    monkeypatch.setattr(categorical_module, "chi2", _fail)
    monkeypatch.setattr(column_module, "analyze_series", _fail)
    monkeypatch.setattr(column_module, "resolve_semantics", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    summary = build_relationships_summary(analysis)
    copied = next(
        item
        for item in summary.relationships
        if isinstance(item, NumericNumericRelationship)
        and (item.left_position, item.right_position) == (0, 1)
    )
    assert copied.spearman.frequentist.p_value == raw_p
    assert copied.spearman.frequentist.adjusted_p_value == adjusted_p
    assert copied.spearman.frequentist.adjustment is BH
    assert copied.pearson.frequentist.adjustment is NOT_APPLIED
    _assert_plain(summary)
    _assert_plain(analysis.relationship_analysis)


def test_adjusted_evidence_rejects_inconsistent_states() -> None:
    with pytest.raises(ValueError, match="adjusted p-value"):
        FrequentistEvidence(
            availability=AVAILABLE,
            p_value=0.2,
            adjusted_p_value=0.2,
            adjustment=NOT_APPLIED,
            reason=None,
        )
    with pytest.raises(ValueError, match="adjusted p-value"):
        FrequentistEvidence(
            availability=AVAILABLE,
            p_value=0.2,
            adjusted_p_value=None,
            adjustment=BH,
            reason=None,
        )
    with pytest.raises(ValueError, match="not adjusted"):
        FrequentistEvidence(
            availability=UNAVAILABLE,
            p_value=None,
            adjusted_p_value=None,
            adjustment=BH,
            reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(ValueError, match="less than"):
        FrequentistEvidence(
            availability=AVAILABLE,
            p_value=0.2,
            adjusted_p_value=0.1,
            adjustment=BH,
            reason=None,
        )
    relationship = _analysis(
        pd.DataFrame({"x": [1, 2, 3, 4, 5, 6], "y": [1, 2, 4, 3, 6, 5]})
    ).relationships[0]
    assert isinstance(relationship, NumericNumericRelationship)
    pearson = relationship.pearson.frequentist
    with pytest.raises(ValueError, match="Pearson evidence"):
        dataclasses.replace(
            relationship,
            methods=(
                relationship.spearman,
                dataclasses.replace(
                    relationship.pearson,
                    frequentist=dataclasses.replace(
                        pearson,
                        adjusted_p_value=pearson.p_value,
                        adjustment=BH,
                    ),
                ),
            ),
        )
    with pytest.raises(dataclasses.FrozenInstanceError):
        relationship.spearman.frequentist.p_value = 0.5  # type: ignore[misc]


def test_correction_rejects_a_non_tuple_and_a_repeated_hypothesis() -> None:
    retained = _analysis(
        pd.DataFrame({"x": [1, 2, 3, 4, 5, 6], "y": [1, 2, 4, 3, 6, 5]})
    )
    record = retained.relationships[0]
    with pytest.raises(TypeError, match="tuple"):
        adjust_primary_p_values([record])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="sequence of floats"):
        benjamini_hochberg("0.2")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="recorded twice"):
        adjust_primary_p_values((record, record))


def test_direct_adjustment_is_idempotent_for_the_same_raw_family() -> None:
    retained = _analysis(_mixed_frame())
    again = adjust_primary_p_values(retained.relationships)
    assert again == retained.relationships
    assert math.isfinite(
        next(
            item.spearman.frequentist.adjusted_p_value
            for item in again
            if isinstance(item, NumericNumericRelationship)
        )
    )
