"""TSK-028: Boolean × Boolean relationship foundation."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import fisher_exact

import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.relationships.boolean_boolean as boolean_module
import pytics.analysis.relationships.collector as collector_module
import pytics.analysis.relationships.numeric_categorical as numeric_categorical_module
import pytics.analysis.relationships.numeric_numeric as numeric_numeric_module
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationship import BooleanAssociationMethod
from pytics.analysis.relationship import CategoricalCategoricalRelationship
from pytics.analysis.relationship import BooleanBooleanPopulation
from pytics.analysis.relationship import BooleanBooleanRelationship
from pytics.analysis.relationship import BooleanDirectionalEstimate
from pytics.analysis.relationship import BooleanDirectionalMethod
from pytics.analysis.relationship import BooleanIndependenceMethod
from pytics.analysis.relationship import BooleanLevel
from pytics.analysis.relationship import CorrelationEstimate
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericBooleanRelationship
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import RelationshipFamily
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.relationship import UnimplementedFamilyCount
from pytics.analysis.relationship import UnimplementedRelationshipFamily
from pytics.analysis.relationship import build_relationships_summary
from pytics.analysis.relationships.boolean_boolean import relationship_from_counts
from pytics.semantics.interpretation import SemanticType

_RETAINED = (
    pd.DataFrame,
    pd.Series,
    pd.Index,
    np.ndarray,
    pd.arrays.BooleanArray,
)
_UUIDS = (
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
)


def _boolean_frame(
    left: list[object],
    right: list[object],
    **columns: object,
) -> pd.DataFrame:
    data = {
        "left": pd.Series(left, dtype="boolean"),
        "right": pd.Series(right, dtype="boolean"),
    }
    data.update(columns)
    return pd.DataFrame(data)


def _only(frame: pd.DataFrame) -> BooleanBooleanRelationship:
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert summary.n_supported_pairs == 1
    relationship = summary.relationships[0]
    assert isinstance(relationship, BooleanBooleanRelationship)
    return relationship


def _from_cells(
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
) -> BooleanBooleanRelationship:
    return relationship_from_counts(
        n_ff,
        n_ft,
        n_tf,
        n_tt,
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=n_ff + n_ft + n_tf + n_tt,
    )


def _rows_from_cells(
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
) -> tuple[list[bool], list[bool]]:
    left = [False] * n_ff + [False] * n_ft + [True] * n_tf + [True] * n_tt
    right = [False] * n_ff + [True] * n_ft + [False] * n_tf + [True] * n_tt
    return left, right


def _independent_difference(n_ff: int, n_ft: int, n_tf: int, n_tt: int) -> float:
    p_true = n_tt / (n_tf + n_tt)
    p_false = n_ft / (n_ff + n_ft)
    return p_true - p_false


def _independent_ratio(n_ff: int, n_ft: int, n_tf: int, n_tt: int) -> float:
    p_true = n_tt / (n_tf + n_tt)
    p_false = n_ft / (n_ff + n_ft)
    return p_true / p_false


def _independent_phi(n_ff: int, n_ft: int, n_tf: int, n_tt: int) -> float:
    numerator = n_tt * n_ff - n_tf * n_ft
    n_conditioning_false = n_ff + n_ft
    n_conditioning_true = n_tf + n_tt
    n_outcome_false = n_ff + n_tf
    n_outcome_true = n_ft + n_tt
    denominator = (
        math.sqrt(n_conditioning_false)
        * math.sqrt(n_conditioning_true)
        * math.sqrt(n_outcome_false)
        * math.sqrt(n_outcome_true)
    )
    return numerator / denominator


def _independent_fisher_p(n_ff: int, n_ft: int, n_tf: int, n_tt: int) -> float:
    _odds_ratio, p_value = fisher_exact(
        [[n_ff, n_ft], [n_tf, n_tt]],
        alternative="two-sided",
    )
    return float(p_value)


def _assert_no_retained_source(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _RETAINED)
    assert not type(value).__module__.startswith(("scipy", "pandas.core", "numpy"))
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_no_retained_source(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_retained_source(item, seen)


def _assert_available_effects(
    relationship: BooleanBooleanRelationship,
    n_ff: int,
    n_ft: int,
    n_tf: int,
    n_tt: int,
) -> None:
    assert relationship.probability_difference.value == pytest.approx(
        _independent_difference(n_ff, n_ft, n_tf, n_tt)
    )
    assert relationship.probability_ratio.value == pytest.approx(
        _independent_ratio(n_ff, n_ft, n_tf, n_tt)
    )
    assert relationship.phi.value == pytest.approx(
        _independent_phi(n_ff, n_ft, n_tf, n_tt)
    )
    assert relationship.independence.frequentist.p_value == pytest.approx(
        _independent_fisher_p(n_ff, n_ft, n_tf, n_tt)
    )


def test_physical_boolean_pair_is_calculated() -> None:
    frame = pd.DataFrame(
        {
            "left": [False, False, True, True],
            "right": [False, True, False, True],
        }
    )
    before = frame.copy(deep=True)
    relationship = _only(frame)
    pd.testing.assert_frame_equal(frame, before)
    assert relationship.family is RelationshipFamily.BOOLEAN_BOOLEAN
    assert relationship.population is (
        BooleanBooleanPopulation.PAIRWISE_NON_MISSING_BOOLEAN
    )
    assert relationship.conditioning_position == 0
    assert relationship.outcome_position == 1
    assert relationship.n_total_rows == 4
    assert relationship.n_paired == 4
    assert relationship.n_excluded == 0
    assert relationship.table.conditioning_false_outcome_false == 1
    assert relationship.table.conditioning_false_outcome_true == 1
    assert relationship.table.conditioning_true_outcome_false == 1
    assert relationship.table.conditioning_true_outcome_true == 1
    assert not hasattr(relationship, "confidence_interval")
    assert not hasattr(relationship, "is_significant")


def test_nullable_boolean_pair_excludes_missing_without_imputing() -> None:
    frame = _boolean_frame(
        [True, False, pd.NA, True, pd.NA],
        [True, pd.NA, False, False, pd.NA],
    )
    before = frame.copy(deep=True)
    relationship = _only(frame)
    pd.testing.assert_frame_equal(frame, before)
    assert relationship.n_total_rows == 5
    assert relationship.n_paired == 2
    assert relationship.n_excluded == 3
    assert relationship.table.conditioning_false_outcome_false == 0
    assert relationship.table.conditioning_false_outcome_true == 0
    assert relationship.table.conditioning_true_outcome_false == 1
    assert relationship.table.conditioning_true_outcome_true == 1
    assert (
        relationship.table.conditioning_false_outcome_false
        + relationship.table.conditioning_false_outcome_true
        + relationship.table.conditioning_true_outcome_false
        + relationship.table.conditioning_true_outcome_true
        == relationship.n_paired
    )


def test_pairwise_population_is_not_the_column_boolean_profile() -> None:
    frame = _boolean_frame(
        [True, False, pd.NA],
        [True, pd.NA, False],
    )
    analysis = analyze_dataframe(frame)
    relationship = analysis.relationship_analysis.relationships[0]
    assert isinstance(relationship, BooleanBooleanRelationship)
    assert analysis.columns[0].boolean_analysis is not None
    assert analysis.columns[0].boolean_analysis.n_non_missing == 2
    assert relationship.n_paired == 1
    assert relationship.table.conditioning_true_outcome_true == 1


def test_boolean_with_numeric_or_categorical_is_not_this_family() -> None:
    frame = pd.DataFrame(
        {
            "amount": [1, 2, 3, 4],
            "flag": [True, False, True, False],
            "group": pd.Categorical(["a", "b", "a", "b"]),
        }
    )
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert not any(
        isinstance(item, BooleanBooleanRelationship) for item in summary.relationships
    )
    flagged = [
        item
        for item in summary.relationships
        if isinstance(item, NumericBooleanRelationship)
    ]
    assert [(item.numeric_position, item.boolean_position) for item in flagged] == [
        (0, 1)
    ]
    assert summary.unimplemented_family_counts == (
        UnimplementedFamilyCount(
            UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN, 1
        ),
    )
    assert summary.n_unimplemented_family_pairs == 1
    assert summary.n_ineligible_pairs == 0


def test_binary_integers_and_boolean_strings_are_not_boolean_pairs() -> None:
    integers = analyze_dataframe(pd.DataFrame({"a": [0, 1, 0, 1], "b": [1, 0, 1, 0]}))
    assert integers.columns[0].inferred.selected_type is SemanticType.NUMERIC
    assert isinstance(
        integers.relationship_analysis.relationships[0],
        NumericNumericRelationship,
    )
    strings = analyze_dataframe(
        pd.DataFrame(
            {
                "a": pd.Series(["true", "false", "true", "false"], dtype="string"),
                "b": pd.Series(["yes", "no", "yes", "no"], dtype="string"),
            }
        )
    )
    assert strings.columns[0].inferred.selected_type is not SemanticType.BOOLEAN
    assert strings.columns[1].inferred.selected_type is not SemanticType.BOOLEAN
    assert not any(
        isinstance(item, BooleanBooleanRelationship)
        for item in strings.relationship_analysis.relationships
    )


def test_categorical_boolean_values_follow_the_selected_type() -> None:
    frame = pd.DataFrame(
        {
            "a": pd.Categorical([True, False, True, False]),
            "b": pd.Categorical([False, True, False, True]),
        }
    )
    analysis = analyze_dataframe(frame)
    assert analysis.columns[0].inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.columns[1].inferred.selected_type is SemanticType.CATEGORICAL
    assert len(analysis.relationship_analysis.relationships) == 1
    relationship = analysis.relationship_analysis.relationships[0]
    assert isinstance(relationship, CategoricalCategoricalRelationship)
    assert not isinstance(relationship, BooleanBooleanRelationship)
    assert analysis.relationship_analysis.n_supported_pairs == 1
    assert analysis.relationship_analysis.unimplemented_family_counts == ()


def test_constant_and_empty_boolean_columns_are_not_boolean_pairs() -> None:
    frame = _boolean_frame(
        [True, True, True, True],
        [pd.NA, pd.NA, pd.NA, pd.NA],
    )
    frame["varied"] = pd.Series([True, False, True, False], dtype="boolean")
    analysis = analyze_dataframe(frame)
    assert analysis.columns[0].inferred.selected_type is SemanticType.CONSTANT
    assert analysis.columns[1].inferred.selected_type is SemanticType.EMPTY
    assert analysis.columns[2].inferred.selected_type is SemanticType.BOOLEAN
    assert analysis.relationship_analysis.relationships == ()
    assert analysis.relationship_analysis.n_supported_pairs == 0


def test_object_boolean_values_are_not_read_as_boolean_storage() -> None:
    frame = pd.DataFrame(
        {
            "a": pd.Series([True, False, True, False], dtype=object),
            "b": pd.Series([False, True, False, True], dtype=object),
        }
    )
    analysis = analyze_dataframe(frame)
    assert analysis.columns[0].inferred.selected_type is not SemanticType.BOOLEAN
    assert not any(
        isinstance(item, BooleanBooleanRelationship)
        for item in analysis.relationship_analysis.relationships
    )


def test_contingency_cells_ignore_row_order_and_keep_logical_axes() -> None:
    left, right = _rows_from_cells(2, 3, 4, 5)
    forward = _only(_boolean_frame(left, right))
    reverse = _only(_boolean_frame(list(reversed(left)), list(reversed(right))))
    assert forward.table == reverse.table
    assert forward.table.conditioning_false_outcome_false == 2
    assert forward.table.conditioning_false_outcome_true == 3
    assert forward.table.conditioning_true_outcome_false == 4
    assert forward.table.conditioning_true_outcome_true == 5
    assert forward.table.n_conditioning_false == 5
    assert forward.table.n_conditioning_true == 9
    assert forward.table.n_outcome_false == 6
    assert forward.table.n_outcome_true == 8
    assert forward == reverse


def test_sparse_boolean_storage_is_a_boolean_pair() -> None:
    frame = pd.DataFrame(
        {
            "left": pd.Series(pd.arrays.SparseArray([False, False, True, True])),
            "right": pd.Series(pd.arrays.SparseArray([False, True, False, True])),
        }
    )
    relationship = _only(frame)
    assert relationship.n_paired == 4
    assert relationship.table.conditioning_true_outcome_true == 1


def test_ordinary_positive_table_matches_independent_formulas() -> None:
    relationship = _from_cells(2, 3, 4, 5)
    assert relationship.outcome_true_given_conditioning_false.value == pytest.approx(
        3 / 5
    )
    assert relationship.outcome_true_given_conditioning_true.value == pytest.approx(
        5 / 9
    )
    _assert_available_effects(relationship, 2, 3, 4, 5)
    assert relationship.probability_difference.method is (
        BooleanDirectionalMethod.PROBABILITY_DIFFERENCE
    )
    assert relationship.probability_ratio.method is (
        BooleanDirectionalMethod.PROBABILITY_RATIO
    )
    assert relationship.phi.method is BooleanAssociationMethod.PHI
    assert relationship.independence.method is BooleanIndependenceMethod.FISHER_EXACT
    assert (
        relationship.independence.frequentist.adjustment
        is MultipleTestingAdjustment.NOT_APPLIED
    )
    assert relationship.independence.frequentist.adjusted_p_value is None
    assert type(relationship.probability_difference.value) is float
    assert type(relationship.phi.value) is float
    assert type(relationship.independence.frequentist.p_value) is float


def test_balanced_table_has_zero_effects_and_raw_fisher_p() -> None:
    relationship = _from_cells(10, 10, 10, 10)
    assert relationship.probability_difference.value == 0.0
    assert relationship.probability_ratio.value == 1.0
    assert relationship.phi.value == 0.0
    assert relationship.independence.frequentist.p_value == pytest.approx(
        _independent_fisher_p(10, 10, 10, 10)
    )
    assert relationship.independence.frequentist.p_value == pytest.approx(1.0)
    assert not hasattr(relationship, "association_label")


def test_perfect_agreement_and_disagreement() -> None:
    agreement = _only(
        _boolean_frame([False, False, True, True], [False, False, True, True])
    )
    disagreement = _only(
        _boolean_frame([False, False, True, True], [True, True, False, False])
    )
    assert agreement.phi.value == 1.0
    assert agreement.probability_difference.value == 1.0
    assert agreement.probability_ratio.reason is (
        UnavailabilityReason.MATHEMATICALLY_UNBOUNDED
    )
    assert agreement.probability_ratio.value is None
    assert disagreement.phi.value == -1.0
    assert disagreement.probability_difference.value == -1.0
    assert disagreement.probability_ratio.value == 0.0
    assert agreement.independence.frequentist.p_value == pytest.approx(
        _independent_fisher_p(2, 0, 0, 2)
    )
    assert disagreement.independence.frequentist.p_value == pytest.approx(
        _independent_fisher_p(0, 2, 2, 0)
    )


def test_zero_event_probability_is_distinct_from_an_absent_level() -> None:
    zero_events = _from_cells(4, 0, 6, 0)
    assert zero_events.outcome_true_given_conditioning_false.value == 0.0
    assert zero_events.outcome_true_given_conditioning_true.value == 0.0
    assert zero_events.probability_difference.value == 0.0
    assert zero_events.probability_ratio.reason is UnavailabilityReason.UNDEFINED_RATIO
    assert zero_events.phi.reason is UnavailabilityReason.CONSTANT_PAIRED_VALUES
    absent = _from_cells(3, 2, 0, 0)
    assert absent.outcome_true_given_conditioning_false.value == pytest.approx(2 / 5)
    assert absent.outcome_true_given_conditioning_true.reason is (
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    )
    assert absent.outcome_true_given_conditioning_true.value is None
    assert absent.probability_difference.reason is (
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    )
    assert absent.probability_ratio.reason is (
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    )
    assert absent.phi.reason is UnavailabilityReason.CONSTANT_PAIRED_VALUES


def test_positive_ratio_with_a_zero_baseline_is_unbounded() -> None:
    relationship = _from_cells(5, 0, 3, 4)
    assert relationship.outcome_true_given_conditioning_false.value == 0.0
    assert relationship.outcome_true_given_conditioning_true.value == pytest.approx(
        4 / 7
    )
    assert relationship.probability_difference.value == pytest.approx(4 / 7)
    assert relationship.probability_ratio.reason is (
        UnavailabilityReason.MATHEMATICALLY_UNBOUNDED
    )
    assert relationship.phi.value == pytest.approx(_independent_phi(5, 0, 3, 4))
    assert relationship.independence.frequentist.p_value == pytest.approx(
        _independent_fisher_p(5, 0, 3, 4)
    )


def test_one_zero_off_diagonal_keeps_a_finite_probability_ratio() -> None:
    relationship = _from_cells(4, 2, 0, 6)
    assert relationship.probability_ratio.value == pytest.approx(
        _independent_ratio(4, 2, 0, 6)
    )
    assert math.isfinite(relationship.probability_ratio.value)  # type: ignore[arg-type]
    assert relationship.probability_difference.value == pytest.approx(
        _independent_difference(4, 2, 0, 6)
    )


def test_no_paired_rows_keep_a_zero_table_and_no_fisher_p() -> None:
    frame = _boolean_frame(
        [True, False, pd.NA, pd.NA],
        [pd.NA, pd.NA, True, False],
    )
    relationship = _only(frame)
    library_odds, library_p = fisher_exact([[0, 0], [0, 0]], alternative="two-sided")
    assert math.isnan(library_odds)
    assert library_p == 1.0
    assert relationship.n_paired == 0
    assert relationship.n_excluded == 4
    assert relationship.table.conditioning_false_outcome_false == 0
    assert relationship.table.conditioning_true_outcome_true == 0
    assert relationship.outcome_true_given_conditioning_false.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert relationship.probability_difference.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert relationship.probability_ratio.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert relationship.phi.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert relationship.independence.frequentist.availability is (
        ResultAvailability.UNAVAILABLE
    )
    assert relationship.independence.frequentist.p_value is None
    assert relationship.independence.frequentist.reason is (
        UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )


def test_degenerate_margin_does_not_store_the_library_p_value() -> None:
    frame = _boolean_frame(
        [False, False, True, pd.NA],
        [False, True, pd.NA, False],
    )
    relationship = _only(frame)
    library_odds, library_p = fisher_exact([[1, 1], [0, 0]], alternative="two-sided")
    assert math.isnan(library_odds)
    assert library_p == 1.0
    assert relationship.n_paired == 2
    assert relationship.table.n_conditioning_true == 0
    assert relationship.outcome_true_given_conditioning_false.value == 0.5
    assert relationship.probability_difference.reason is (
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    )
    assert relationship.phi.reason is UnavailabilityReason.CONSTANT_PAIRED_VALUES
    assert relationship.independence.frequentist.p_value is None
    assert relationship.independence.frequentist.reason is (
        UnavailabilityReason.CONSTANT_PAIRED_VALUES
    )


def test_outcome_constant_after_pairing_keeps_a_zero_difference() -> None:
    always_false = _only(
        _boolean_frame(
            [False, True, pd.NA, pd.NA],
            [False, False, True, False],
        )
    )
    assert always_false.table.n_outcome_true == 0
    assert always_false.probability_difference.value == 0.0
    assert always_false.probability_ratio.reason is UnavailabilityReason.UNDEFINED_RATIO
    assert always_false.phi.reason is UnavailabilityReason.CONSTANT_PAIRED_VALUES
    always_true = _only(
        _boolean_frame(
            [False, True, pd.NA, pd.NA],
            [True, True, False, True],
        )
    )
    assert always_true.probability_difference.value == 0.0
    assert always_true.probability_ratio.value == 1.0
    assert always_true.phi.reason is UnavailabilityReason.CONSTANT_PAIRED_VALUES
    assert always_true.independence.frequentist.reason is (
        UnavailabilityReason.CONSTANT_PAIRED_VALUES
    )


def test_both_variables_constant_in_the_paired_population() -> None:
    both_false = _only(
        _boolean_frame(
            [False, pd.NA, True],
            [False, True, pd.NA],
        )
    )
    assert both_false.n_paired == 1
    assert both_false.table.conditioning_false_outcome_false == 1
    assert both_false.outcome_true_given_conditioning_false.value == 0.0
    assert both_false.outcome_true_given_conditioning_true.reason is (
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    )
    assert both_false.phi.reason is UnavailabilityReason.CONSTANT_PAIRED_VALUES
    both_true = _only(
        _boolean_frame(
            [True, pd.NA, False],
            [True, False, pd.NA],
        )
    )
    assert both_true.table.conditioning_true_outcome_true == 1
    assert both_true.outcome_true_given_conditioning_true.value == 1.0
    assert both_true.probability_difference.reason is (
        UnavailabilityReason.CONDITIONING_LEVEL_ABSENT
    )


def test_sparse_agreement_stores_fisher_p_separately_from_phi() -> None:
    relationship = _from_cells(1, 0, 0, 1)
    assert relationship.phi.value == 1.0
    assert relationship.independence.frequentist.p_value == pytest.approx(1.0)
    assert relationship.phi is not relationship.independence.frequentist


def test_large_balanced_counts_do_not_use_fixed_width_products() -> None:
    count = 2**80
    relationship = _from_cells(count, count, count, count)
    assert relationship.probability_difference.value == 0.0
    assert relationship.probability_ratio.value == 1.0
    assert relationship.phi.value == 0.0
    assert relationship.independence.frequentist.reason is (
        UnavailabilityReason.NON_FINITE_RESULT
    )
    shifted = _from_cells(count, count, count, count + 2**40)
    assert shifted.phi.value == pytest.approx(
        _independent_phi(count, count, count, count + 2**40)
    )
    assert shifted.probability_difference.value == pytest.approx(
        _independent_difference(count, count, count, count + 2**40)
    )
    assert shifted.independence.frequentist.p_value is None


def test_huge_exact_agreement_stays_finite_without_calling_fisher() -> None:
    count = 2**80
    relationship = relationship_from_counts(
        count + 1,
        0,
        0,
        count + 3,
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=(count + 1) + (count + 3),
    )
    assert relationship.phi.value == 1.0
    assert relationship.probability_difference.value == 1.0
    assert relationship.probability_ratio.reason is (
        UnavailabilityReason.MATHEMATICALLY_UNBOUNDED
    )
    assert relationship.independence.frequentist.reason is (
        UnavailabilityReason.NON_FINITE_RESULT
    )
    assert relationship.independence.frequentist.p_value is None


def test_a_finite_ratio_that_overflows_float_is_not_stored_as_infinity() -> None:
    huge = 10**400
    relationship = relationship_from_counts(
        huge - 1,
        1,
        0,
        huge,
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=(huge - 1) + 1 + huge,
    )
    assert relationship.probability_ratio.reason is (
        UnavailabilityReason.NON_FINITE_RESULT
    )
    assert relationship.probability_ratio.value is None
    assert relationship.probability_difference.availability is (
        ResultAvailability.AVAILABLE
    )
    assert relationship.table.conditioning_false_outcome_true == 1


def test_direction_changes_with_column_order_and_phi_does_not() -> None:
    conditioning = [False, False, False, True, True]
    outcome = [False, False, True, True, True]
    forward = _only(_boolean_frame(conditioning, outcome))
    reversed_frame = pd.DataFrame(
        {
            "outcome": pd.Series(outcome, dtype="boolean"),
            "conditioning": pd.Series(conditioning, dtype="boolean"),
        }
    )
    backward = _only(reversed_frame)
    assert (forward.left_position, forward.right_position) == (0, 1)
    assert forward.left_label == "left"
    assert forward.conditioning_position == forward.left_position
    assert backward.left_label == "outcome"
    assert backward.conditioning_position == 0
    assert forward.probability_difference.value == pytest.approx(2 / 3)
    assert forward.probability_ratio.value == pytest.approx(3.0)
    assert backward.probability_difference.value == pytest.approx(2 / 3)
    assert backward.probability_ratio.reason is (
        UnavailabilityReason.MATHEMATICALLY_UNBOUNDED
    )
    assert forward.phi.value == pytest.approx(backward.phi.value)
    assert forward.phi.value == pytest.approx(2 / 3)
    assert forward.independence.frequentist.p_value == pytest.approx(
        backward.independence.frequentist.p_value
    )
    summary = build_relationships_summary(
        analyze_dataframe(
            _boolean_frame(
                conditioning,
                outcome,
                third=pd.Series([True, False, True, False, True], dtype="boolean"),
            )
        )
    )
    assert summary.n_supported_pairs == 3
    assert [
        (item.left_position, item.right_position) for item in summary.relationships
    ] == [(0, 1), (0, 2), (1, 2)]


def test_three_boolean_columns_are_prepared_once() -> None:
    frame = _boolean_frame(
        [True, False, True, False],
        [False, True, False, True],
        third=pd.Series([True, True, False, False], dtype="boolean"),
        amount=[1, 2, 3, 4],
    )
    boolean_reads: list[int] = []
    original = collector_module._read_boolean_column

    def _spy(series: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        boolean_reads.append(int(series.shape[0]))
        return original(series)

    collector_module._read_boolean_column = _spy
    try:
        summary = build_relationships_summary(analyze_dataframe(frame))
    finally:
        collector_module._read_boolean_column = original
    assert boolean_reads == [4, 4, 4]
    assert summary.n_supported_pairs == 6
    assert (
        sum(
            isinstance(item, BooleanBooleanRelationship)
            for item in summary.relationships
        )
        == 3
    )
    assert (
        sum(
            isinstance(item, NumericBooleanRelationship)
            for item in summary.relationships
        )
        == 3
    )


def test_mixed_coverage_reconciles() -> None:
    frame = pd.DataFrame(
        {
            "x": [1, 2, 3, 4],
            "y": [2, 3, 4, 5],
            "group": pd.Categorical(["a", "b", "a", "b"]),
            "left": [True, False, True, False],
            "right": [False, True, False, True],
            "code": pd.Series(_UUIDS, dtype="string"),
        }
    )
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert summary.n_total_pairs == 15
    assert summary.n_supported_pairs == 8
    assert summary.n_analyzed_pairs == 8
    assert summary.n_unimplemented_family_pairs == 2
    assert summary.n_ineligible_pairs == 5
    assert (
        summary.n_supported_pairs
        + summary.n_unimplemented_family_pairs
        + summary.n_ineligible_pairs
        == summary.n_total_pairs
    )
    assert summary.unimplemented_family_counts == (
        UnimplementedFamilyCount(
            UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN, 2
        ),
    )
    assert (
        sum(
            isinstance(item, NumericBooleanRelationship)
            for item in summary.relationships
        )
        == 4
    )
    boolean_pairs = [
        item
        for item in summary.relationships
        if isinstance(item, BooleanBooleanRelationship)
    ]
    assert len(boolean_pairs) == 1
    assert (boolean_pairs[0].left_position, boolean_pairs[0].right_position) == (3, 4)


def test_summary_copies_boolean_records_without_recomputing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = analyze_dataframe(
        _boolean_frame([False, False, True, True], [False, True, False, True])
    )

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("summary builder used a source-dependent operation")

    monkeypatch.setattr(collector_module, "_read_boolean_column", _fail)
    monkeypatch.setattr(collector_module, "_analyze_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_categorical_categorical", _fail)
    monkeypatch.setattr(boolean_module, "fisher_exact", _fail)
    monkeypatch.setattr(boolean_module, "relationship_from_counts", _fail)
    monkeypatch.setattr(collector_module, "_read_numeric_column", _fail)
    monkeypatch.setattr(collector_module, "_read_categorical_column", _fail)
    monkeypatch.setattr(collector_module, "_association_methods", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_categorical", _fail)
    monkeypatch.setattr(numeric_numeric_module, "spearmanr", _fail)
    monkeypatch.setattr(numeric_numeric_module, "pearsonr", _fail)
    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _fail)
    monkeypatch.setattr(column_module, "analyze_series", _fail)
    monkeypatch.setattr(column_module, "resolve_semantics", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    summary = build_relationships_summary(analysis)
    retained = analysis.relationship_analysis.relationships[0]
    copied = summary.relationships[0]
    assert copied == retained
    assert copied is not retained
    assert isinstance(copied, BooleanBooleanRelationship)
    assert copied.table is not retained.table
    assert copied.phi is not retained.phi
    assert copied.independence is not retained.independence
    assert copied.independence.frequentist is not retained.independence.frequentist
    _assert_no_retained_source(summary)
    _assert_no_retained_source(analysis.relationship_analysis)


def test_repeated_analysis_is_equal_and_row_order_is_not_retained() -> None:
    frame = _boolean_frame(
        [False, True, False, True, pd.NA],
        [True, False, False, True, False],
    )
    first = _only(frame)
    second = _only(frame)
    assert first == second
    reordered = frame.iloc[::-1].reset_index(drop=True)
    assert _only(reordered) == first
    _assert_no_retained_source(first)


def test_boolean_components_reject_other_family_reasons() -> None:
    with pytest.raises(ValueError, match="not a reason for this component"):
        CorrelationEstimate(
            availability=ResultAvailability.UNAVAILABLE,
            value=None,
            direction=None,
            reason=UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
        )
    with pytest.raises(ValueError, match="not a Boolean margin reason"):
        from pytics.analysis.relationship import BooleanIndependenceTest
        from pytics.analysis.relationship import FrequentistEvidence

        BooleanIndependenceTest(
            method=BooleanIndependenceMethod.FISHER_EXACT,
            frequentist=FrequentistEvidence(
                availability=ResultAvailability.UNAVAILABLE,
                p_value=None,
                adjusted_p_value=None,
                adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                reason=UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
            ),
        )
    with pytest.raises(ValueError, match="finite float"):
        BooleanDirectionalEstimate(
            method=BooleanDirectionalMethod.PROBABILITY_RATIO,
            availability=ResultAvailability.AVAILABLE,
            value=float("inf"),
            reason=None,
        )
    with pytest.raises(ValueError, match="not a reason for this component"):
        BooleanDirectionalEstimate(
            method=BooleanDirectionalMethod.PROBABILITY_DIFFERENCE,
            availability=ResultAvailability.UNAVAILABLE,
            value=None,
            reason=UnavailabilityReason.MATHEMATICALLY_UNBOUNDED,
        )


def test_boolean_record_rejects_a_non_canonical_role() -> None:
    base = _from_cells(1, 1, 1, 1)
    with pytest.raises(ValueError, match="conditioning role"):
        BooleanBooleanRelationship(
            left_position=base.left_position,
            left_label=base.left_label,
            right_position=base.right_position,
            right_label=base.right_label,
            conditioning_position=base.right_position,
            outcome_position=base.left_position,
            n_total_rows=base.n_total_rows,
            n_paired=base.n_paired,
            table=base.table,
            outcome_true_given_conditioning_false=(
                base.outcome_true_given_conditioning_false
            ),
            outcome_true_given_conditioning_true=(
                base.outcome_true_given_conditioning_true
            ),
            probability_difference=base.probability_difference,
            probability_ratio=base.probability_ratio,
            phi=base.phi,
            independence=base.independence,
        )
    with pytest.raises(ValueError, match="non-negative int"):
        relationship_from_counts(
            -1,
            0,
            0,
            0,
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=0,
        )


def test_boolean_reader_rejects_non_boolean_storage() -> None:
    with pytest.raises(TypeError, match="pandas Series"):
        boolean_module._read_boolean_column([True, False])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="boolean storage"):
        boolean_module._read_boolean_column(pd.Series([0, 1, 0, 1]))
    categorical = pd.Series(pd.Categorical([True, False, True, False]))
    with pytest.raises(TypeError, match="boolean storage"):
        boolean_module._read_boolean_column(categorical)


def test_non_finite_fisher_result_does_not_replace_the_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _nan_result(table: object, alternative: str) -> tuple[float, float]:
        assert alternative == "two-sided"
        return (float("nan"), float("nan"))

    monkeypatch.setattr(boolean_module, "fisher_exact", _nan_result)
    relationship = _from_cells(2, 2, 2, 2)
    assert relationship.phi.value == 0.0
    assert relationship.probability_difference.value == 0.0
    assert relationship.independence.frequentist.reason is (
        UnavailabilityReason.NON_FINITE_RESULT
    )
    assert relationship.independence.frequentist.p_value is None

    def _raise(table: object, alternative: str) -> tuple[float, float]:
        raise ValueError("table")

    monkeypatch.setattr(boolean_module, "fisher_exact", _raise)
    failed = _from_cells(3, 1, 1, 3)
    assert failed.probability_ratio.availability is ResultAvailability.AVAILABLE
    assert failed.independence.frequentist.reason is (
        UnavailabilityReason.NON_FINITE_RESULT
    )


def test_boolean_invariants_reject_inconsistent_components() -> None:
    balanced = _from_cells(10, 10, 10, 10)
    ordinary = _from_cells(2, 3, 4, 5)
    agreement = _from_cells(2, 0, 0, 2)
    disagreement = _from_cells(0, 2, 2, 0)
    zero_numerator = _from_cells(4, 2, 3, 0)
    with pytest.raises(ValueError, match="probability difference 0"):
        dataclasses.replace(
            balanced,
            probability_difference=BooleanDirectionalEstimate(
                method=BooleanDirectionalMethod.PROBABILITY_DIFFERENCE,
                availability=ResultAvailability.AVAILABLE,
                value=0.5,
                reason=None,
            ),
        )
    with pytest.raises(ValueError, match="only when non-finite"):
        dataclasses.replace(
            ordinary,
            probability_difference=BooleanDirectionalEstimate(
                method=BooleanDirectionalMethod.PROBABILITY_DIFFERENCE,
                availability=ResultAvailability.UNAVAILABLE,
                value=None,
                reason=UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
            ),
        )
    with pytest.raises(ValueError, match="conditional probability must match"):
        dataclasses.replace(
            ordinary,
            outcome_true_given_conditioning_false=dataclasses.replace(
                ordinary.outcome_true_given_conditioning_false,
                value=0.1,
            ),
        )
    with pytest.raises(ValueError, match="observed conditioning level"):
        dataclasses.replace(
            ordinary,
            outcome_true_given_conditioning_true=dataclasses.replace(
                ordinary.outcome_true_given_conditioning_true,
                availability=ResultAvailability.UNAVAILABLE,
                value=None,
                reason=UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
            ),
        )
    with pytest.raises(ValueError, match="probability ratio 0"):
        dataclasses.replace(
            zero_numerator,
            probability_ratio=BooleanDirectionalEstimate(
                method=BooleanDirectionalMethod.PROBABILITY_RATIO,
                availability=ResultAvailability.AVAILABLE,
                value=0.5,
                reason=None,
            ),
        )
    with pytest.raises(ValueError, match="probability ratio 1"):
        dataclasses.replace(
            balanced,
            probability_ratio=BooleanDirectionalEstimate(
                method=BooleanDirectionalMethod.PROBABILITY_RATIO,
                availability=ResultAvailability.AVAILABLE,
                value=2.0,
                reason=None,
            ),
        )
    with pytest.raises(ValueError, match="phi 0"):
        dataclasses.replace(
            balanced,
            phi=dataclasses.replace(balanced.phi, value=0.2),
        )
    with pytest.raises(ValueError, match="phi 1"):
        dataclasses.replace(
            agreement, phi=dataclasses.replace(agreement.phi, value=0.0)
        )
    with pytest.raises(ValueError, match="phi -1"):
        dataclasses.replace(
            disagreement,
            phi=dataclasses.replace(disagreement.phi, value=0.0),
        )
    with pytest.raises(ValueError, match="negative zero"):
        BooleanDirectionalEstimate(
            method=BooleanDirectionalMethod.PROBABILITY_DIFFERENCE,
            availability=ResultAvailability.AVAILABLE,
            value=-0.0,
            reason=None,
        )
    with pytest.raises(ValueError, match="lie on"):
        BooleanDirectionalEstimate(
            method=BooleanDirectionalMethod.PROBABILITY_DIFFERENCE,
            availability=ResultAvailability.AVAILABLE,
            value=2.0,
            reason=None,
        )
    with pytest.raises(ValueError, match="cannot be negative"):
        BooleanDirectionalEstimate(
            method=BooleanDirectionalMethod.PROBABILITY_RATIO,
            availability=ResultAvailability.AVAILABLE,
            value=-0.2,
            reason=None,
        )
    assert boolean_module._normalize_signed_unit(1.0 + 1e-12) == 1.0
    assert boolean_module._normalize_signed_unit(-1.0 - 1e-12) == -1.0
    assert boolean_module._normalize_signed_unit(0.0) == 0.0
    assert boolean_module._normalize_signed_unit(2.0) is None
    assert boolean_module._normalize_signed_unit(float("nan")) is None
    assert boolean_module._as_p_value(True) is None
    assert boolean_module._as_p_value(np.array([0.2])) is None
    assert boolean_module._as_p_value("no") is None
    assert boolean_module._as_p_value(1.5) is None
    assert boolean_module._as_p_value(0.0) == 0.0
    assert boolean_module._normalize_signed_unit(-2.0) is None
    empty = _from_cells(0, 0, 0, 0)
    with pytest.raises(ValueError, match="insufficient_paired_observations"):
        dataclasses.replace(
            empty,
            outcome_true_given_conditioning_false=dataclasses.replace(
                empty.outcome_true_given_conditioning_false,
                reason=UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
            ),
        )
    with pytest.raises(ValueError, match="only when non-finite"):
        dataclasses.replace(
            ordinary,
            probability_ratio=BooleanDirectionalEstimate(
                method=BooleanDirectionalMethod.PROBABILITY_RATIO,
                availability=ResultAvailability.UNAVAILABLE,
                value=None,
                reason=UnavailabilityReason.CONDITIONING_LEVEL_ABSENT,
            ),
        )
    with pytest.raises(ValueError, match="only when non-finite"):
        dataclasses.replace(
            ordinary,
            phi=dataclasses.replace(
                ordinary.phi,
                availability=ResultAvailability.UNAVAILABLE,
                value=None,
                reason=UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            ),
        )
    with pytest.raises(ValueError, match="only when non-finite"):
        dataclasses.replace(
            ordinary,
            independence=dataclasses.replace(
                ordinary.independence,
                frequentist=dataclasses.replace(
                    ordinary.independence.frequentist,
                    availability=ResultAvailability.UNAVAILABLE,
                    p_value=None,
                    reason=UnavailabilityReason.CONSTANT_PAIRED_VALUES,
                ),
            ),
        )
    with pytest.raises(ValueError, match="contingency counts must sum"):
        dataclasses.replace(ordinary, n_paired=ordinary.n_paired - 1)
    with pytest.raises(ValueError, match="finite float"):
        BooleanDirectionalEstimate(
            method=BooleanDirectionalMethod.PROBABILITY_DIFFERENCE,
            availability=ResultAvailability.AVAILABLE,
            value=None,
            reason=None,
        )
    from pytics.analysis.relationship import ConditionalOutcomeProbability

    with pytest.raises(ValueError, match="finite float"):
        ConditionalOutcomeProbability(
            conditioning_value=BooleanLevel.FALSE,
            availability=ResultAvailability.AVAILABLE,
            value=None,
            reason=None,
        )
    with pytest.raises(ValueError, match="negative zero"):
        BooleanDirectionalEstimate(
            method=BooleanDirectionalMethod.PROBABILITY_RATIO,
            availability=ResultAvailability.AVAILABLE,
            value=-0.0,
            reason=None,
        )
    with pytest.raises(ValueError, match="n_paired cannot exceed"):
        relationship_from_counts(
            1,
            0,
            0,
            0,
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=0,
        )
    with pytest.raises(TypeError, match="NumPy arrays"):
        boolean_module.analyze(
            [True, False],  # type: ignore[arg-type]
            np.array([True, False]),
            np.array([True, False]),
            np.array([False, True]),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )
    with pytest.raises(TypeError, match="boolean arrays"):
        boolean_module.analyze(
            np.array([1, 0]),
            np.array([1, 0]),
            np.array([1, 0]),
            np.array([0, 1]),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )
    with pytest.raises(ValueError, match="cover every dataset row"):
        boolean_module.analyze(
            np.array([True]),
            np.array([True]),
            np.array([False]),
            np.array([False]),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )

    class _NoPValue:
        def __getitem__(self, index: int) -> float:
            raise TypeError

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        boolean_module,
        "fisher_exact",
        lambda table, alternative: _NoPValue(),
    )
    try:
        missing_p = _from_cells(2, 1, 1, 2)
    finally:
        monkeypatch.undo()
    assert missing_p.independence.frequentist.reason is (
        UnavailabilityReason.NON_FINITE_RESULT
    )


def test_defensive_boolean_branches_stay_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(boolean_module, "_normalize_signed_unit", lambda value: None)
    assert (
        boolean_module._probability_difference(1, 1, 1, 2, 5).reason
        is UnavailabilityReason.NON_FINITE_RESULT
    )
    assert (
        boolean_module._phi(2, 3, 4, 5, 14).reason
        is UnavailabilityReason.NON_FINITE_RESULT
    )
    monkeypatch.undo()
    monkeypatch.setattr(boolean_module.math, "isfinite", lambda value: False)
    assert (
        boolean_module._probability_ratio(49, 1, 0, 1, 51).reason
        is UnavailabilityReason.NON_FINITE_RESULT
    )
    monkeypatch.undo()
    columns = analyze_dataframe(
        pd.DataFrame({"a": [True, False, True], "b": [False, True, False]})
    ).columns
    numeric = analyze_dataframe(
        pd.DataFrame({"a": [1, 2, 3], "b": [2, 3, 4]})
    ).relationship_analysis.relationships[0]
    with pytest.raises(TypeError, match="BooleanBooleanRelationship"):
        collector_module._require_record_family(numeric, columns, 0, 1)
    with pytest.raises(TypeError, match="calculated relationship"):
        collector_module._copy_relationship(numeric.methods[0])  # type: ignore[attr-defined]


def test_outcome_true_level_names_are_explicit() -> None:
    relationship = _from_cells(1, 0, 0, 1)
    assert (
        relationship.outcome_true_given_conditioning_false.conditioning_value
        is BooleanLevel.FALSE
    )
    assert (
        relationship.outcome_true_given_conditioning_true.conditioning_value
        is BooleanLevel.TRUE
    )
    assert relationship.outcome_true_given_conditioning_false.value == 0.0
    assert relationship.outcome_true_given_conditioning_true.value == 1.0
