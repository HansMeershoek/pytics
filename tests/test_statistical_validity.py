"""TSK-047: high-cardinality bias and chi-square inferential validity.

These tests keep the naive effect beside its correction and keep a
computed chi-square tail out of Benjamini–Hochberg when Cochran's
expected-count convention fails. They do not add a cardinality cutoff.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.stats import chi2

from pytics.analysis.compare.distribution import adjust_drift_tests
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationships.adjustment import adjust_primary_p_values
from pytics.analysis.relationships.adjustment import benjamini_hochberg
from pytics.analysis.relationships.models import CategoricalCategoricalRelationship
from pytics.analysis.relationships.models import InferentialInvalidityReason
from pytics.analysis.relationships.models import InferentialValidity
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import NumericCategoricalRelationship
from pytics.analysis.relationships.models import NumericNumericRelationship
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import UnavailabilityReason
from pytics.analysis.relationships.models import cochran_expected_counts_hold
from pytics import compare
from pytics import profile

_NOT_APPLIED = MultipleTestingAdjustment.NOT_APPLIED
_BH = MultipleTestingAdjustment.BENJAMINI_HOCHBERG
_INVALID = InferentialValidity.INVALID
_VALID = InferentialValidity.VALID
_CHI_SQUARE_COUNTS = InferentialInvalidityReason.CHI_SQUARE_EXPECTED_COUNTS


def test_cochran_boundaries_use_the_integer_fifth() -> None:
    assert cochran_expected_counts_hold(
        minimum_expected_count=1.0,
        n_cells_expected_below_5=2,
        n_cells=10,
    )
    assert not cochran_expected_counts_hold(
        minimum_expected_count=1.0,
        n_cells_expected_below_5=3,
        n_cells=10,
    )
    assert not cochran_expected_counts_hold(
        minimum_expected_count=0.999999999999,
        n_cells_expected_below_5=0,
        n_cells=4,
    )
    assert cochran_expected_counts_hold(
        minimum_expected_count=5.0,
        n_cells_expected_below_5=0,
        n_cells=4,
    )


def test_noise_eta_squared_keeps_the_naive_value_and_a_smaller_epsilon() -> None:
    frame = _noise_numeric_frame(n=1000, k=240, seed=0)
    original = frame.copy(deep=True)
    relationship = _only_numeric(analyze_dataframe(frame))
    pd.testing.assert_frame_equal(frame, original)
    assert relationship.n_groups == frame["g"].nunique()
    assert relationship.n_groups > 200
    eta = relationship.effect.value
    epsilon = relationship.corrected_effect.value
    assert eta is not None and epsilon is not None
    assert eta > 0.15
    assert epsilon < 0.05
    assert epsilon < eta - 0.10
    assert math.isfinite(epsilon)
    assert epsilon <= 1.0
    manual = _epsilon_from_eta(eta, relationship.n_paired, relationship.n_groups)
    assert epsilon == pytest.approx(manual, abs=1e-8)


def test_noise_cramers_v_keeps_the_naive_value_and_a_smaller_correction() -> None:
    frame = _noise_categorical_frame(n=1000, k=240, seed=0)
    original = frame.copy(deep=True)
    relationship = _only_categorical(analyze_dataframe(frame))
    pd.testing.assert_frame_equal(frame, original)
    assert relationship.table.n_left_levels == frame["a"].nunique()
    assert relationship.table.n_right_levels == frame["b"].nunique()
    naive = relationship.association.value
    corrected = relationship.corrected_association.value
    assert naive is not None and corrected is not None
    assert naive > 0.40
    assert corrected < naive / 2
    assert 0.0 <= corrected <= 1.0
    assert corrected == pytest.approx(
        _bergsma_v(
            relationship.independence.statistic,
            relationship.n_paired,
            relationship.table.n_left_levels,
            relationship.table.n_right_levels,
        )
    )
    evidence = relationship.independence.frequentist
    assert evidence.availability is ResultAvailability.AVAILABLE
    assert evidence.p_value is not None and evidence.p_value < 0.01
    assert evidence.p_value == pytest.approx(
        float(
            chi2.sf(
                relationship.independence.statistic,
                relationship.independence.degrees_of_freedom,
            )
        )
    )
    assert relationship.expected_counts.minimum_expected_count < 1.0
    assert evidence.inferential_validity is _INVALID
    assert evidence.invalidity_reason is _CHI_SQUARE_COUNTS
    assert evidence.adjustment is _NOT_APPLIED
    assert evidence.adjusted_p_value is None


def test_corrected_effects_match_hand_calculations() -> None:
    numeric = _only_numeric(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "y": [0.0, 1.0, 2.0, 0.0, 1.0, 2.0],
                    "g": pd.Categorical(list("aaabbb")),
                }
            )
        )
    )
    # Equal groups: SS_between = 0, MS_within = 1, so epsilon squared is -1/4.
    assert numeric.effect.value == 0.0
    assert numeric.corrected_effect.value == pytest.approx(-0.25)

    categorical = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a"] * 30 + ["b"] * 30),
                    "right": pd.Categorical(
                        ["x"] * 20 + ["y"] * 10 + ["x"] * 10 + ["y"] * 20
                    ),
                }
            )
        )
    )
    # Cells 20, 10, 10, 20. chi2 = 20/3 and corrected V = sqrt(25/261).
    assert categorical.association.value == pytest.approx(1 / 3)
    assert categorical.corrected_association.numerator_floored is False
    assert categorical.corrected_association.value == pytest.approx(math.sqrt(25 / 261))


def test_chi_square_validity_follows_each_cochran_clause() -> None:
    below_one = _only_categorical(
        analyze_dataframe(
            _counts_frame(
                (
                    (1, 11, 11, 11, 11, 5, 0, 0, 0, 0),
                    (0, 0, 0, 0, 0, 6, 11, 11, 11, 11),
                )
            )
        )
    )
    assert below_one.expected_counts.minimum_expected_count == pytest.approx(0.5)
    assert below_one.expected_counts.n_cells_expected_below_5 * 5 <= 20
    _assert_invalid(below_one)

    sparse_share = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a"] * 4 + ["b"] * 4),
                    "right": pd.Categorical(["x", "y"] * 4),
                }
            )
        )
    )
    assert sparse_share.expected_counts.minimum_expected_count == pytest.approx(2.0)
    assert sparse_share.expected_counts.fraction_cells_expected_below_5 == 1.0
    _assert_invalid(sparse_share)

    dense = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a"] * 10 + ["b"] * 10),
                    "right": pd.Categorical((["x"] * 5 + ["y"] * 5) * 2),
                }
            )
        )
    )
    assert dense.expected_counts.minimum_expected_count == 5.0
    assert dense.expected_counts.n_cells_expected_below_5 == 0
    evidence = dense.independence.frequentist
    assert evidence.inferential_validity is _VALID
    assert evidence.invalidity_reason is None
    assert evidence.adjustment is _BH
    assert evidence.adjusted_p_value == evidence.p_value

    boundary = _only_categorical(
        analyze_dataframe(
            _counts_frame(
                (
                    (3, 7, 5, 5, 5),
                    (3, 7, 5, 5, 5),
                )
            )
        )
    )
    assert boundary.expected_counts.minimum_expected_count == pytest.approx(3.0)
    assert boundary.expected_counts.n_cells_expected_below_5 == 2
    assert boundary.table.n_left_levels * boundary.table.n_right_levels == 10
    assert boundary.independence.frequentist.inferential_validity is _VALID


def test_invalid_chi_square_is_excluded_from_the_reduced_bh_family() -> None:
    numeric = _only_numeric_pair(
        analyze_dataframe(
            pd.DataFrame({"x": [1, 2, 3, 4, 5, 6], "y": [1, 3, 2, 6, 4, 5]})
        )
    )
    dense = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a"] * 10 + ["b"] * 10),
                    "right": pd.Categorical((["x"] * 5 + ["y"] * 5) * 2),
                }
            )
        )
    )
    sparse = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a"] * 5 + ["b"]),
                    "right": pd.Categorical(["x"] * 5 + ["y"]),
                }
            )
        )
    )
    numeric = _with_primary_p(replace(numeric, left_position=0, right_position=1), 0.01)
    dense = _with_primary_p(replace(dense, left_position=2, right_position=3), 0.20)
    sparse = _with_primary_p(replace(sparse, left_position=4, right_position=5), 0.40)
    adjusted = adjust_primary_p_values((numeric, dense, sparse))
    numeric_p, dense_p, sparse_p = (
        (
            item.spearman.frequentist
            if isinstance(item, NumericNumericRelationship)
            else item.independence.frequentist
        )
        for item in adjusted
    )
    assert (numeric_p.adjusted_p_value, dense_p.adjusted_p_value) == pytest.approx(
        benjamini_hochberg((0.01, 0.20))
    )
    assert numeric_p.adjusted_p_value == pytest.approx(0.02)
    assert benjamini_hochberg((0.01, 0.20, 0.40))[0] == pytest.approx(0.03)
    assert sparse_p.p_value == pytest.approx(0.40)
    assert sparse_p.inferential_validity is _INVALID
    assert sparse_p.invalidity_reason is _CHI_SQUARE_COUNTS
    assert sparse_p.adjustment is _NOT_APPLIED
    assert sparse_p.adjusted_p_value is None
    tied = adjust_primary_p_values(
        (_with_primary_p(numeric, 0.20), _with_primary_p(dense, 0.20), sparse)
    )
    assert tied[0].spearman.frequentist.adjusted_p_value == (
        tied[1].independence.frequentist.adjusted_p_value
    )


def test_target_reuse_does_not_restore_an_excluded_p_value() -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, 4.0],
            "left": pd.Categorical(["a"] * 3 + ["b"]),
            "right": pd.Categorical(["x"] * 3 + ["y"]),
        }
    )
    analysis = analyze_dataframe(frame, target="left")
    dataset_record = next(
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    )
    link = next(
        item
        for item in analysis.target_analysis.relationships
        if item.relationship is dataset_record
    )
    evidence = link.relationship.independence.frequentist
    assert evidence is dataset_record.independence.frequentist
    assert evidence.inferential_validity is _INVALID
    assert evidence.adjusted_p_value is None
    assert evidence.adjustment is _NOT_APPLIED


def test_sparse_and_dense_categorical_drift_keep_separate_validity() -> None:
    sparse = (
        compare(
            pd.DataFrame({"c": pd.Categorical([f"r{i}" for i in range(30)])}),
            pd.DataFrame(
                {"c": pd.Categorical([f"c{i}" for i in range(20)] + ["r0"] * 10)}
            ),
        )
        .columns[0]
        .distribution
    )
    assert sparse.total_variation_distance.availability is ResultAvailability.AVAILABLE
    assert sparse.test.availability is ResultAvailability.AVAILABLE
    assert sparse.test.p_value is not None
    assert sparse.expected_counts.minimum_expected_count < 1.0
    assert sparse.test.inferential_validity is _INVALID
    assert sparse.test.invalidity_reason is _CHI_SQUARE_COUNTS
    assert sparse.test.adjustment is _NOT_APPLIED
    assert sparse.test.adjusted_p_value is None

    dense = (
        compare(
            pd.DataFrame({"c": pd.Categorical(["a"] * 40 + ["b"] * 40)}),
            pd.DataFrame({"c": pd.Categorical(["a"] * 30 + ["b"] * 50)}),
        )
        .columns[0]
        .distribution
    )
    assert dense.expected_counts.minimum_expected_count > 5.0
    assert dense.test.inferential_validity is _VALID
    assert dense.test.adjustment is _BH
    assert dense.test.adjusted_p_value == dense.test.p_value

    numeric = (
        compare(
            pd.DataFrame({"n": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]}),
            pd.DataFrame({"n": [2.0, 3.0, 4.0, 5.0, 6.0, 8.0]}),
        )
        .columns[0]
        .distribution
    )
    mixed = adjust_drift_tests(
        (
            _with_drift_p(numeric, 0.01),
            _with_drift_p(dense, 0.20),
            _with_drift_p(sparse, 0.40),
        )
    )
    assert mixed[0].test.adjusted_p_value == pytest.approx(0.02)
    assert mixed[1].test.adjusted_p_value == pytest.approx(0.20)
    assert mixed[2].test.p_value == pytest.approx(0.40)
    assert mixed[2].test.adjusted_p_value is None
    assert mixed[2].test.inferential_validity is _INVALID


def test_relationship_drift_keeps_corrected_effects_beside_the_naive_ones() -> None:
    reference = pd.DataFrame(
        {
            "y": [0, 1, 2, 0, 1, 2],
            "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            "left": pd.Categorical(["a", "a", "b", "b", "a", "b"]),
            "right": pd.Categorical(["x", "x", "y", "y", "x", "y"]),
        }
    )
    comparison = pd.DataFrame(
        {
            "y": [0, 0, 0, 3, 3, 3],
            "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            "left": pd.Categorical(["a", "a", "b", "b", "a", "b"]),
            "right": pd.Categorical(["x", "y", "x", "y", "x", "y"]),
        }
    )
    result = compare(reference, comparison)
    numeric = next(
        item
        for item in result.relationships
        if item.primary is not None and item.primary.measure.value == "eta_squared"
    )
    categorical = next(
        item
        for item in result.relationships
        if item.primary is not None and item.primary.measure.value == "cramers_v"
    )
    assert numeric.primary.measure.value == "eta_squared"
    assert numeric.complementary[0].measure.value == "epsilon_squared"
    assert numeric.complementary[0].availability is ResultAvailability.AVAILABLE
    assert categorical.primary.measure.value == "cramers_v"
    assert categorical.complementary[0].measure.value == "bias_corrected_cramers_v"
    assert (
        categorical.reference.categorical_categorical.bias_corrected_cramers_v
        is not None
    )


def test_degenerate_numeric_categorical_effects_stay_explicit() -> None:
    one_group = _only_numeric(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "y": [1.0, 2.0, math.inf],
                    "g": pd.Categorical(["a", "a", "b"]),
                }
            )
        )
    )
    assert one_group.effect.reason is UnavailabilityReason.INSUFFICIENT_GROUPS
    assert one_group.corrected_effect.reason is UnavailabilityReason.INSUFFICIENT_GROUPS
    assert one_group.effect.value is None
    assert one_group.corrected_effect.value is None

    singletons = _only_numeric(
        analyze_dataframe(
            pd.DataFrame({"y": [1.0, 4.0, 9.0], "g": pd.Categorical(["a", "b", "c"])})
        )
    )
    assert singletons.effect.value == 1.0
    assert singletons.corrected_effect.value is None
    assert singletons.corrected_effect.reason is (
        UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    )

    constant = _only_numeric(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "y": [2.0, 2.0, 2.0, 2.0, math.inf],
                    "g": pd.Categorical(list("ababa")),
                }
            )
        )
    )
    assert constant.effect.reason is UnavailabilityReason.ZERO_TOTAL_VARIATION
    assert constant.corrected_effect.reason is UnavailabilityReason.ZERO_TOTAL_VARIATION
    assert constant.effect.value is None

    empty = _only_numeric(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "y": [1.0, 2.0, np.nan, np.nan],
                    "g": pd.Categorical([pd.NA, pd.NA, "a", "b"]),
                }
            )
        )
    )
    assert empty.effect.reason is UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    assert empty.corrected_effect.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )

    infinities = _only_numeric(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "y": [math.inf, -math.inf, math.inf],
                    "g": pd.Categorical(["a", "b", "a"]),
                }
            )
        )
    )
    assert infinities.n_paired == 0
    assert infinities.effect.value is None
    assert infinities.corrected_effect.value is None

    wide = _only_numeric(analyze_dataframe(_explicit_wide_frame()))
    assert wide.n_groups == 25
    assert wide.n_paired == 30
    assert wide.effect.availability is ResultAvailability.AVAILABLE
    assert wide.corrected_effect.availability is ResultAvailability.AVAILABLE
    assert wide.corrected_effect.value < wide.effect.value


def test_degenerate_categorical_associations_stay_explicit() -> None:
    one_margin = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a", "a", "b"]),
                    "right": pd.Categorical(["x", "y", pd.NA]),
                }
            )
        )
    )
    assert one_margin.association.reason is UnavailabilityReason.CONSTANT_PAIRED_VALUES
    assert one_margin.corrected_association.reason is (
        UnavailabilityReason.CONSTANT_PAIRED_VALUES
    )
    assert one_margin.association.value is None
    assert one_margin.corrected_association.value is None

    empty = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a", "b", pd.NA, pd.NA]),
                    "right": pd.Categorical([pd.NA, pd.NA, "x", "y"]),
                }
            )
        )
    )
    assert empty.n_paired == 0
    assert (
        empty.association.reason
        is UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert empty.corrected_association.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )

    permutation = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a", "b"]),
                    "right": pd.Categorical(["x", "y"]),
                }
            )
        )
    )
    assert permutation.association.value == 1.0
    assert permutation.corrected_association.value is None
    assert permutation.corrected_association.reason is (
        UnavailabilityReason.BIAS_CORRECTION_UNDEFINED
    )

    independent = _only_categorical(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": pd.Categorical(["a", "a", "b", "b"]),
                    "right": pd.Categorical(["x", "y", "x", "y"]),
                }
            )
        )
    )
    assert independent.association.value == 0.0
    assert independent.corrected_association.value == 0.0
    assert independent.corrected_association.numerator_floored is True

    profiled = profile(
        pd.DataFrame(
            {
                "y": np.arange(40, dtype=float),
                "g": pd.Categorical([f"g{index % 30}" for index in range(40)]),
            }
        )
    )
    assert profiled.relationships.analysis.n_analyzed_pairs == 1


def _assert_invalid(relationship: CategoricalCategoricalRelationship) -> None:
    evidence = relationship.independence.frequentist
    assert evidence.availability is ResultAvailability.AVAILABLE
    assert evidence.p_value is not None
    assert evidence.inferential_validity is _INVALID
    assert evidence.invalidity_reason is _CHI_SQUARE_COUNTS
    assert evidence.adjustment is _NOT_APPLIED
    assert evidence.adjusted_p_value is None


def _with_primary_p(record, p_value: float):
    if isinstance(record, NumericNumericRelationship):
        spearman, pearson = record.methods
        return replace(
            record,
            methods=(
                replace(spearman, frequentist=_reset_p(spearman.frequentist, p_value)),
                pearson,
            ),
        )
    return replace(
        record,
        independence=replace(
            record.independence,
            frequentist=_reset_p(record.independence.frequentist, p_value),
        ),
    )


def _with_drift_p(record, p_value: float):
    return replace(record, test=replace(record.test, **_p_fields(record.test, p_value)))


def _reset_p(evidence, p_value: float):
    return replace(evidence, **_p_fields(evidence, p_value))


def _p_fields(evidence, p_value: float) -> dict:
    return {
        "p_value": p_value,
        "adjusted_p_value": None,
        "adjustment": _NOT_APPLIED,
    }


def _only_numeric(analysis) -> NumericCategoricalRelationship:
    found = [
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, NumericCategoricalRelationship)
    ]
    assert len(found) == 1
    return found[0]


def _only_numeric_pair(analysis) -> NumericNumericRelationship:
    found = [
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, NumericNumericRelationship)
    ]
    assert len(found) == 1
    return found[0]


def _only_categorical(analysis) -> CategoricalCategoricalRelationship:
    found = [
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    ]
    assert len(found) == 1
    return found[0]


def _noise_numeric_frame(*, n: int, k: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "y": rng.normal(size=n),
            "g": pd.Categorical(rng.integers(0, k, size=n).astype(str)),
        }
    )


def _noise_categorical_frame(*, n: int, k: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "a": pd.Categorical(rng.integers(0, k, size=n).astype(str)),
            "b": pd.Categorical(rng.integers(0, k, size=n).astype(str)),
        }
    )


def _explicit_wide_frame() -> pd.DataFrame:
    labels = [f"g{index}" for index in range(25)]
    values = [float(index) for index in range(25)] + [10.0, 11.0, 12.0, 13.0, 14.0]
    groups = labels + labels[:5]
    return pd.DataFrame({"y": values, "g": pd.Categorical(groups)})


def _epsilon_from_eta(eta: float, n_paired: int, n_groups: int) -> float:
    return (eta * (n_paired - 1) - (n_groups - 1)) / (n_paired - n_groups)


def _bergsma_v(statistic: float, n_paired: int, n_left: int, n_right: int) -> float:
    phi_squared = statistic / n_paired
    bias = ((n_left - 1) * (n_right - 1)) / (n_paired - 1)
    adjusted = max(0.0, phi_squared - bias)
    denominator = min(
        (n_left - 1) * (n_paired - n_left),
        (n_right - 1) * (n_paired - n_right),
    )
    return math.sqrt(adjusted * (n_paired - 1) / denominator)


def _counts_frame(counts: tuple[tuple[int, ...], ...]) -> pd.DataFrame:
    left_values = []
    right_values = []
    for row, row_counts in enumerate(counts):
        for column, count in enumerate(row_counts):
            left_values.extend([f"r{row}"] * count)
            right_values.extend([f"c{column}"] * count)
    return pd.DataFrame(
        {
            "left": pd.Categorical(left_values),
            "right": pd.Categorical(right_values),
        }
    )
