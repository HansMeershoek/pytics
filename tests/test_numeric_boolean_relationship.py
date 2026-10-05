"""TSK-029: Numeric × Boolean relationship foundation."""

from __future__ import annotations

import dataclasses
import math
import warnings
from decimal import Decimal
from decimal import localcontext
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.relationships.boolean_boolean as boolean_boolean_module
import pytics.analysis.relationships.collector as collector_module
import pytics.analysis.relationships.numeric_boolean as numeric_boolean_module
import pytics.analysis.relationships.numeric_categorical as numeric_categorical_module
import pytics.analysis.relationships.numeric_numeric as numeric_numeric_module
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.numeric import collect_numeric_descriptive_analysis
from pytics.analysis.relationship import BooleanBooleanRelationship
from pytics.analysis.relationship import BooleanGroupContrast
from pytics.analysis.relationship import BooleanGroupSummary
from pytics.analysis.relationship import BooleanLevel
from pytics.analysis.relationship import FrequentistEvidence
from pytics.analysis.relationship import MeanDifferenceEstimate
from pytics.analysis.relationship import MeanDifferenceInterval
from pytics.analysis.relationship import MeanDifferenceIntervalMethod
from pytics.analysis.relationship import MeanDifferenceTest
from pytics.analysis.relationship import MeanDifferenceTestMethod
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericBooleanPopulation
from pytics.analysis.relationship import NumericBooleanRelationship
from pytics.analysis.relationship import NumericCategoricalRelationship
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import RelationshipFamily
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import StandardizedDifferenceMethod
from pytics.analysis.relationship import StandardizedMeanDifference
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.relationship import UnimplementedFamilyCount
from pytics.analysis.relationship import UnimplementedRelationshipFamily
from pytics.analysis.relationship import build_relationships_summary
from pytics.analysis.relationship import relationship_analysis_for_columns
from pytics.analysis.relationships.numeric_boolean import _hedges_correction
from pytics.semantics.interpretation import SemanticType

AVAILABLE = ResultAvailability.AVAILABLE
UNAVAILABLE = ResultAvailability.UNAVAILABLE
Reason = UnavailabilityReason

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
    "6ba7b814-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b815-9dad-11d1-80b4-00c04fd430c8",
)
_FALSE = [1.0, 2.0, 3.0, 4.0]
_TRUE = [2.0, 8.0, 14.0, 20.0, 26.0]
_PI = Decimal("3.14159265358979323846264338327950288419716939937510582097494459")
_REPRESENTATIVE_SIZES = (
    (2, 2),
    (2, 3),
    (3, 3),
    (5, 8),
    (20, 20),
    (100, 150),
    (1000, 1000),
)


def _frame(
    false_values: list[object],
    true_values: list[object],
    **columns: object,
) -> pd.DataFrame:
    data: dict[str, object] = {
        "y": [*false_values, *true_values],
        "flag": [False] * len(false_values) + [True] * len(true_values),
    }
    data.update(columns)
    return pd.DataFrame(data)


def _only(frame: pd.DataFrame) -> NumericBooleanRelationship:
    summary = build_relationships_summary(analyze_dataframe(frame))
    records = [
        item
        for item in summary.relationships
        if isinstance(item, NumericBooleanRelationship)
    ]
    assert len(records) == 1
    return records[0]


def _scaled(values: list[object]) -> tuple[list[Fraction], Fraction]:
    """Exact values divided by their largest magnitude."""
    exact = [Fraction(value) for value in values]  # type: ignore[arg-type]
    scale = max(abs(value) for value in exact) or Fraction(1)
    return [value / scale for value in exact], scale


def _exact_moments(values: list[Fraction]) -> tuple[Fraction, Fraction]:
    mean = sum(values, Fraction(0)) / len(values)
    if len(values) == 1:
        return mean, Fraction(0)
    variance = sum(((value - mean) ** 2 for value in values), Fraction(0)) / (
        len(values) - 1
    )
    return mean, variance


def _independent_welch(
    true_values: list[object],
    false_values: list[object],
) -> dict[str, float]:
    """Welch–Satterthwaite quantities in exact rational arithmetic."""
    scaled, scale = _scaled([*true_values, *false_values])
    true_mean, true_variance = _exact_moments(scaled[: len(true_values)])
    false_mean, false_variance = _exact_moments(scaled[len(true_values) :])
    a = true_variance / len(true_values)
    b = false_variance / len(false_values)
    degrees_of_freedom = float(
        (a + b) ** 2 / (a**2 / (len(true_values) - 1) + b**2 / (len(false_values) - 1))
    )
    scaled_error = math.sqrt(float(a + b))
    scaled_difference = float(true_mean - false_mean)
    statistic = scaled_difference / scaled_error
    critical = float(stats.t.ppf(0.975, degrees_of_freedom))
    difference = scaled_difference * float(scale)
    half_width = critical * scaled_error * float(scale)
    return {
        "difference": difference,
        "statistic": statistic,
        "df": degrees_of_freedom,
        "p_value": 2.0 * float(stats.t.sf(abs(statistic), degrees_of_freedom)),
        "lower": difference - half_width,
        "upper": difference + half_width,
    }


def _independent_cohen(true_values: list[object], false_values: list[object]) -> float:
    """Mean difference over the pooled sample deviation, before correction."""
    scaled, _scale = _scaled([*true_values, *false_values])
    true_mean, true_variance = _exact_moments(scaled[: len(true_values)])
    false_mean, false_variance = _exact_moments(scaled[len(true_values) :])
    degrees_of_freedom = len(true_values) + len(false_values) - 2
    pooled = (
        (len(true_values) - 1) * true_variance
        + (len(false_values) - 1) * false_variance
    ) / degrees_of_freedom
    return float(true_mean - false_mean) / math.sqrt(float(pooled))


def _exact_correction(degrees_of_freedom: int) -> float:
    """Hedges' J(v) from the gamma recurrence alone, at sixty digits.

    R(v) = Γ(v/2) / Γ((v - 1)/2) satisfies R(v) = R(v - 2) (v - 2) / (v - 3)
    because Γ(x + 1) = x Γ(x). R(2) = Γ(1) / Γ(1/2) = 1/√π and
    R(3) = Γ(3/2) / Γ(1) = √π/2. J(v) = R(v) / √(v/2). Neither
    ``math.gamma`` nor an asymptotic series is used.
    """
    with localcontext() as context:
        context.prec = 60
        root_pi = _PI.sqrt()
        ratio = 1 / root_pi if degrees_of_freedom % 2 == 0 else root_pi / 2
        for step in range(4 + degrees_of_freedom % 2, degrees_of_freedom + 1, 2):
            ratio = ratio * (step - 2) / (step - 3)
        return float(ratio / (Decimal(degrees_of_freedom) / 2).sqrt())


def _independent_hedges(true_values: list[object], false_values: list[object]) -> float:
    degrees_of_freedom = len(true_values) + len(false_values) - 2
    return _exact_correction(degrees_of_freedom) * _independent_cohen(
        true_values, false_values
    )


def _scipy_welch(
    true_values: list[float],
    false_values: list[float],
) -> tuple[float, float]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = stats.ttest_ind(true_values, false_values, equal_var=False)
    return float(result.statistic), float(result.pvalue)


def _assert_plain_record(value: object, seen: set[int] | None = None) -> None:
    """No source object, no library result, and no non-finite float."""
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _RETAINED)
    assert not type(value).__module__.startswith(("scipy", "pandas.core", "numpy"))
    if isinstance(value, float):
        assert math.isfinite(value)
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_plain_record(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_plain_record(item, seen)


def _reasons(relationship: NumericBooleanRelationship) -> tuple[object, ...]:
    test = relationship.mean_difference_test
    return (
        relationship.standardized_mean_difference.reason,
        relationship.mean_difference_interval.reason,
        test.statistic_reason,
        test.frequentist.reason,
    )


def test_pair_is_calculated_in_either_physical_order() -> None:
    numeric_first = _frame(_FALSE, _TRUE)
    before = numeric_first.copy(deep=True)
    first = _only(numeric_first)
    second = _only(numeric_first[["flag", "y"]])
    pd.testing.assert_frame_equal(numeric_first, before)
    assert (first.left_position, first.right_position) == (0, 1)
    assert (first.numeric_position, first.boolean_position) == (0, 1)
    assert (first.left_label, first.right_label) == ("y", "flag")
    assert (second.left_position, second.right_position) == (0, 1)
    assert (second.numeric_position, second.boolean_position) == (1, 0)
    assert (second.left_label, second.right_label) == ("flag", "y")
    for relationship in (first, second):
        assert relationship.family is RelationshipFamily.NUMERIC_BOOLEAN
        assert relationship.population is (
            NumericBooleanPopulation.FINITE_NUMERIC_NON_MISSING_BOOLEAN
        )
        assert relationship.contrast is BooleanGroupContrast.TRUE_MINUS_FALSE
        assert relationship.false_group.level is BooleanLevel.FALSE
        assert relationship.true_group.level is BooleanLevel.TRUE
        assert relationship.n_total_rows == relationship.n_paired == 9
        assert relationship.mean_difference.value == 11.5
        _assert_plain_record(relationship)
    for field in (
        "false_group",
        "true_group",
        "mean_difference",
        "standardized_mean_difference",
        "mean_difference_interval",
        "mean_difference_test",
    ):
        assert getattr(first, field) == getattr(second, field)


def test_selected_types_decide_the_family() -> None:
    frame = pd.DataFrame(
        {
            "amount": pd.Series([1, 2, pd.NA, 4, 5, 6], dtype="Int64"),
            "flag": pd.Series(
                [True, False, True, pd.NA, False, True],
                dtype="boolean",
            ),
            "binary": [0, 1, 0, 1, 1, 0],
            "group": pd.Categorical([True, False, True, False, True, False]),
            "text": pd.Series(
                ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"],
                dtype="string",
            ),
            "fixed": pd.Series([True] * 6, dtype="boolean"),
            "code": pd.Series(_UUIDS, dtype="string"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_relationships_summary(analysis)
    assert [column.inferred.selected_type for column in analysis.columns] == [
        SemanticType.NUMERIC,
        SemanticType.BOOLEAN,
        SemanticType.NUMERIC,
        SemanticType.CATEGORICAL,
        None,
        SemanticType.CONSTANT,
        SemanticType.IDENTIFIER,
    ]
    kinds = [
        (type(item).__name__, item.left_position, item.right_position)
        for item in summary.relationships
    ]
    assert kinds == [
        ("NumericBooleanRelationship", 0, 1),
        ("NumericNumericRelationship", 0, 2),
        ("NumericCategoricalRelationship", 0, 3),
        ("NumericBooleanRelationship", 1, 2),
        ("NumericCategoricalRelationship", 2, 3),
    ]
    assert summary.unimplemented_family_counts == (
        UnimplementedFamilyCount(
            UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN, 1
        ),
    )
    assert summary.n_unimplemented_family_pairs == 1
    assert summary.n_ineligible_pairs == 15
    nullable, binary = (
        item
        for item in summary.relationships
        if isinstance(item, NumericBooleanRelationship)
    )
    assert nullable.n_paired == 4
    assert nullable.mean_difference.value == 0.0
    assert nullable.standardized_mean_difference.value == 0.0
    assert (binary.numeric_position, binary.boolean_position) == (2, 1)
    assert binary.true_group.descriptive.minimum == 0
    assert type(binary.true_group.descriptive.minimum) is int
    assert binary.false_group.descriptive.minimum == 1
    assert binary.mean_difference.value == -1.0
    assert binary.standardized_mean_difference.reason is (
        Reason.MATHEMATICALLY_UNBOUNDED
    )


def test_population_excludes_missing_and_infinite_rows_once() -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, np.nan, 3.0, np.inf, -np.inf, 6.0, 7.0, np.nan, 9.0, 10.0],
            "flag": pd.Series(
                [False, True, pd.NA, True, False, pd.NA, True, pd.NA, False, True],
                dtype="boolean",
            ),
        }
    )
    before = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    relationship = build_relationships_summary(analysis).relationships[0]
    pd.testing.assert_frame_equal(frame, before)
    assert isinstance(relationship, NumericBooleanRelationship)
    assert relationship.n_total_rows == 10
    assert relationship.n_paired == 4
    assert relationship.n_excluded == 6
    assert relationship.false_group.n + relationship.true_group.n == 4
    assert relationship.false_group.descriptive.minimum == 1.0
    assert relationship.false_group.descriptive.maximum == 9.0
    assert relationship.true_group.descriptive.minimum == 7.0
    assert relationship.true_group.descriptive.maximum == 10.0
    assert relationship.mean_difference.value == 3.5
    assert analysis.columns[0].numeric_analysis.finite_count == 6
    assert analysis.columns[1].boolean_analysis.true_count == 4
    assert analysis.columns[1].boolean_analysis.false_count == 3
    _assert_plain_record(relationship)


def test_group_descriptions_reuse_numeric_definitions() -> None:
    false_values = [5, 1, 4, 2, 3]
    true_values = [10, 30, 20, 40]
    relationship = _only(_frame(false_values, true_values))
    for group, values in (
        (relationship.false_group, false_values),
        (relationship.true_group, true_values),
    ):
        expected = collect_numeric_descriptive_analysis(pd.Series(values))
        assert group.availability is AVAILABLE
        assert group.reason is None
        assert group.descriptive == expected
        assert group.n == len(values)
        assert type(group.descriptive.minimum) is int
        assert group.descriptive.standard_deviation == pytest.approx(
            float(np.std(values, ddof=1))
        )
        quartiles = np.quantile(values, [0.25, 0.5, 0.75], method="linear")
        assert [
            group.descriptive.q1,
            group.descriptive.median,
            group.descriptive.q3,
        ] == pytest.approx(quartiles.tolist())
    singleton = _only(_frame([7.5], [1.0, 2.0, 4.0]))
    described = singleton.false_group.descriptive
    assert singleton.false_group.n == 1
    assert described.standard_deviation is None
    assert described.minimum == described.median == described.maximum == 7.5


def test_absent_level_is_an_explicit_unavailable_group() -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, np.nan, np.inf],
            "flag": [False, False, False, True, True],
        }
    )
    analysis = analyze_dataframe(frame)
    relationship = build_relationships_summary(analysis).relationships[0]
    assert isinstance(relationship, NumericBooleanRelationship)
    assert analysis.columns[1].inferred.selected_type is SemanticType.BOOLEAN
    assert analysis.columns[1].boolean_analysis.true_count == 2
    absent = relationship.true_group
    assert absent.availability is UNAVAILABLE
    assert absent.reason is Reason.CONDITIONING_LEVEL_ABSENT
    assert absent.descriptive is None
    assert absent.n == 0
    assert relationship.false_group.n == 3
    assert relationship.mean_difference.value is None
    assert relationship.mean_difference.reason is Reason.CONDITIONING_LEVEL_ABSENT
    assert set(_reasons(relationship)) == {Reason.CONDITIONING_LEVEL_ABSENT}
    assert relationship.mean_difference_test.frequentist.p_value is None
    mirrored = _only(
        pd.DataFrame({"y": [np.nan, 2.0, 3.0], "flag": [False, True, True]})
    )
    assert mirrored.false_group.reason is Reason.CONDITIONING_LEVEL_ABSENT
    assert mirrored.true_group.n == 2
    assert set(_reasons(mirrored)) == {Reason.CONDITIONING_LEVEL_ABSENT}


def test_no_paired_rows_keep_the_record() -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, np.nan, np.nan],
            "flag": pd.Series([pd.NA, pd.NA, True, False], dtype="boolean"),
        }
    )
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert summary.n_supported_pairs == summary.n_analyzed_pairs == 1
    relationship = summary.relationships[0]
    assert isinstance(relationship, NumericBooleanRelationship)
    assert relationship.n_paired == 0
    assert relationship.n_excluded == 4
    for group in (relationship.false_group, relationship.true_group):
        assert group.reason is Reason.INSUFFICIENT_PAIRED_OBSERVATIONS
        assert group.descriptive is None
    assert relationship.mean_difference.reason is (
        Reason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert set(_reasons(relationship)) == {Reason.INSUFFICIENT_PAIRED_OBSERVATIONS}


def test_mean_difference_is_true_minus_false() -> None:
    positive = _only(_frame([1.0, 2.0, 3.0], [4.0, 6.0, 8.0]))
    negative = _only(_frame([4.0, 6.0, 8.0], [1.0, 2.0, 3.0]))
    zero = _only(_frame([1.0, 2.0, 3.0], [0.0, 2.0, 4.0]))
    assert positive.mean_difference.value == 4.0
    assert negative.mean_difference.value == -4.0
    assert zero.mean_difference.value == 0.0
    assert math.copysign(1.0, zero.mean_difference.value) == 1.0
    assert zero.standardized_mean_difference.value == 0.0
    assert zero.mean_difference_test.statistic == 0.0
    assert zero.mean_difference_test.frequentist.p_value == pytest.approx(
        1.0, abs=1e-12
    )
    for relationship, sign in ((positive, 1.0), (negative, -1.0)):
        assert sign * relationship.standardized_mean_difference.value > 0.0
        assert sign * relationship.mean_difference_test.statistic > 0.0
        interval = relationship.mean_difference_interval
        assert interval.lower <= relationship.mean_difference.value <= interval.upper
    identical = _only(_frame([0.1, 0.2, 0.7], [0.7, 0.1, 0.2]))
    assert identical.mean_difference.value == 0.0


def test_flipping_the_boolean_negates_every_signed_component() -> None:
    values = [1.5, 2.0, 7.25, 3.0, 9.5, 4.0, 0.5]
    flags = [False, True, True, False, True, False, False]
    original = _only(pd.DataFrame({"y": values, "flag": flags}))
    flipped = _only(pd.DataFrame({"y": values, "flag": [not flag for flag in flags]}))
    assert flipped.false_group.descriptive == original.true_group.descriptive
    assert flipped.true_group.descriptive == original.false_group.descriptive
    assert flipped.mean_difference.value == -original.mean_difference.value
    assert flipped.standardized_mean_difference.value == (
        -original.standardized_mean_difference.value
    )
    original_test = original.mean_difference_test
    flipped_test = flipped.mean_difference_test
    assert flipped_test.statistic == -original_test.statistic
    assert flipped_test.degrees_of_freedom == original_test.degrees_of_freedom
    assert flipped_test.frequentist.p_value == original_test.frequentist.p_value
    assert flipped.mean_difference_interval.lower == (
        -original.mean_difference_interval.upper
    )
    assert flipped.mean_difference_interval.upper == (
        -original.mean_difference_interval.lower
    )


def test_large_integer_offsets_keep_the_difference_and_the_spread() -> None:
    base = 2**60
    false_values = [base, base + 1]
    true_values = [base + 10, base + 11]
    relationship = _only(_frame(false_values, true_values))
    collapsed = np.array([*false_values, *true_values], dtype=np.float64)
    assert len(set(collapsed.tolist())) == 1
    false_summary = relationship.false_group.descriptive
    true_summary = relationship.true_group.descriptive
    assert false_summary.mean == true_summary.mean
    assert false_summary.minimum == base
    assert type(false_summary.minimum) is int
    assert relationship.mean_difference.value == 10.0
    assert false_summary.standard_deviation == pytest.approx(math.sqrt(0.5))
    reference = _independent_welch(true_values, false_values)
    test = relationship.mean_difference_test
    assert test.statistic == pytest.approx(reference["statistic"], rel=1e-12)
    assert test.degrees_of_freedom == pytest.approx(2.0, rel=1e-12)
    assert test.frequentist.p_value == pytest.approx(reference["p_value"], rel=1e-10)
    interval = relationship.mean_difference_interval
    assert interval.lower == pytest.approx(reference["lower"], rel=1e-12)
    assert interval.upper == pytest.approx(reference["upper"], rel=1e-12)
    assert relationship.standardized_mean_difference.value == pytest.approx(
        _independent_hedges(true_values, false_values), rel=1e-12
    )

    low = -(2**63)
    high = 2**63 - 1
    extreme = _only(_frame([high - 1, high], [low, low + 1]))
    assert extreme.mean_difference.value == float(low - high + 1)
    assert extreme.mean_difference_test.statistic == pytest.approx(
        _independent_welch([low, low + 1], [high - 1, high])["statistic"],
        rel=1e-12,
    )
    assert extreme.standardized_mean_difference.value == pytest.approx(
        _independent_hedges([low, low + 1], [high - 1, high]), rel=1e-12
    )

    top = 2**64 - 1
    unsigned = _only(
        pd.DataFrame(
            {
                "y": np.array([top - 3, top - 2, top - 1, top], dtype=np.uint64),
                "flag": [False, False, True, True],
            }
        )
    )
    assert unsigned.mean_difference.value == 2.0
    assert unsigned.mean_difference_test.statistic == pytest.approx(
        2.0 / math.sqrt(0.5)
    )

    far = _only(_frame([0, 1], [2**60, 2**60 + 1]))
    assert far.mean_difference.value == float(2**60)
    assert far.true_group.descriptive.standard_deviation == pytest.approx(
        math.sqrt(0.5)
    )
    assert far.mean_difference_test.statistic == pytest.approx(
        2**60 / math.sqrt(0.5), rel=1e-12
    )
    assert far.standardized_mean_difference.availability is AVAILABLE

    span = 2**54 + 1
    constant_span = _only(_frame([0, 0], [span, span]))
    assert constant_span.mean_difference.value == float(span)
    assert constant_span.standardized_mean_difference.reason is (
        Reason.MATHEMATICALLY_UNBOUNDED
    )
    assert constant_span.mean_difference_test.statistic_reason is (
        Reason.ZERO_WITHIN_GROUP_VARIATION
    )
    for record in (relationship, extreme, unsigned, far, constant_span):
        _assert_plain_record(record)


def test_extreme_finite_floats_are_unavailable_rather_than_infinite() -> None:
    wide = _only(_frame([-1.7e308, 1.7e308], [1e308, 1.5e308]))
    assert wide.mean_difference.value == 1.25e308
    assert wide.false_group.descriptive.minimum == -1.7e308
    assert wide.false_group.descriptive.standard_deviation is None
    assert set(_reasons(wide)) == {Reason.NON_FINITE_RESULT}

    beyond = _only(_frame([-1.7e308, -1.6e308], [1.6e308, 1.7e308]))
    assert beyond.mean_difference.reason is Reason.NON_FINITE_RESULT
    assert beyond.false_group.availability is AVAILABLE
    assert beyond.true_group.availability is AVAILABLE
    assert set(_reasons(beyond)) == {Reason.NON_FINITE_RESULT}

    false_values = [1e300, 2e300, 3e300]
    true_values = [4e300, 6e300, 8e300]
    scaled = _only(_frame(false_values, true_values))
    reference = _independent_welch(true_values, false_values)
    assert scaled.mean_difference.value == pytest.approx(4e300, rel=1e-15)
    assert scaled.mean_difference_test.statistic == pytest.approx(
        reference["statistic"], rel=1e-12
    )
    assert scaled.mean_difference_interval.upper == pytest.approx(
        reference["upper"], rel=1e-12
    )
    assert scaled.standardized_mean_difference.value == pytest.approx(
        _independent_hedges(true_values, false_values), rel=1e-12
    )

    unbounded_interval = _only(_frame([-1e308, 1e308], [0.0, 1.0]))
    assert unbounded_interval.mean_difference.value == 0.5
    assert unbounded_interval.mean_difference_test.statistic_availability is AVAILABLE
    assert unbounded_interval.mean_difference_test.frequentist.p_value == (
        pytest.approx(1.0)
    )
    assert unbounded_interval.mean_difference_interval.reason is (
        Reason.NON_FINITE_RESULT
    )
    assert unbounded_interval.standardized_mean_difference.availability is AVAILABLE

    overflowing_ratio = _only(_frame([0.0, 1e-300], [1e300, 1e300]))
    assert overflowing_ratio.mean_difference.value == 1e300
    assert overflowing_ratio.mean_difference_test.statistic_reason is (
        Reason.NON_FINITE_RESULT
    )
    assert overflowing_ratio.mean_difference_test.frequentist.reason is (
        Reason.NON_FINITE_RESULT
    )
    assert overflowing_ratio.standardized_mean_difference.reason is (
        Reason.NON_FINITE_RESULT
    )
    assert overflowing_ratio.mean_difference_interval.availability is AVAILABLE
    for record in (wide, beyond, scaled, unbounded_interval, overflowing_ratio):
        _assert_plain_record(record)


@pytest.mark.parametrize(("n_false", "n_true"), _REPRESENTATIVE_SIZES)
def test_hedges_g_matches_an_independent_formula(n_false: int, n_true: int) -> None:
    rng = np.random.default_rng(1000 * n_false + n_true)
    shift = 0.6 if (n_false + n_true) % 2 == 0 else -0.6
    false_values = rng.normal(0.0, 1.0, n_false).tolist()
    true_values = rng.normal(shift, 1.7, n_true).tolist()
    standardized = _only(_frame(false_values, true_values)).standardized_mean_difference
    degrees_of_freedom = n_false + n_true - 2
    correction = _exact_correction(degrees_of_freedom)
    cohen = _independent_cohen(true_values, false_values)
    assert _hedges_correction(degrees_of_freedom) == pytest.approx(
        correction, rel=2e-15
    )
    assert standardized.method is StandardizedDifferenceMethod.HEDGES_G
    assert standardized.availability is AVAILABLE
    assert standardized.value == pytest.approx(correction * cohen, rel=1e-13)
    assert abs(standardized.value) < abs(cohen)


def test_hedges_g_matches_its_closed_form() -> None:
    """False [1, 2, 3, 4] and True [2, 8, 14, 20, 26].

    The mean difference is 23/2 and the pooled variance is 365/7 on seven
    degrees of freedom. J(7) = Γ(7/2) / (√(7/2) Γ(3)) = 15√π / (16√(7/2)),
    so g = (345/32) √(2π/365).
    """
    relationship = _only(_frame(_FALSE, _TRUE))
    assert relationship.standardized_mean_difference.value == pytest.approx(
        345.0 / 32.0 * math.sqrt(2.0 * math.pi / 365.0), rel=2e-15
    )


def test_hedges_correction_matches_an_independent_gamma_recurrence() -> None:
    assert _hedges_correction(2) == pytest.approx(1.0 / math.sqrt(math.pi), rel=2e-15)
    assert _hedges_correction(3) == pytest.approx(math.sqrt(math.pi / 6.0), rel=2e-15)
    assert _hedges_correction(4) == pytest.approx(math.sqrt(2.0 / math.pi), rel=2e-15)
    for degrees_of_freedom in (*range(2, 401), 10**4, 10**5):
        assert _hedges_correction(degrees_of_freedom) == pytest.approx(
            _exact_correction(degrees_of_freedom), rel=2e-15
        )
    previous = _hedges_correction(2)
    for degrees_of_freedom in (3, 10, 100, 340, 341, 1_000, 10**6, 10**9):
        current = _hedges_correction(degrees_of_freedom)
        assert previous < current < 1.0
        assert current == pytest.approx(
            1.0 - 3.0 / (4.0 * degrees_of_freedom - 1.0),
            abs=1.0 / degrees_of_freedom**2 + 1e-15,
        )
        previous = current


def test_hedges_correction_is_not_evaluated_below_two_degrees_of_freedom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _undefined(degrees_of_freedom: int) -> float:
        raise AssertionError(f"J({degrees_of_freedom}) was evaluated")

    monkeypatch.setattr(numeric_boolean_module, "_hedges_correction", _undefined)
    for false_values, true_values in (([1.0], [3.0]), ([1.0], [3.0, 4.0])):
        relationship = _only(_frame(false_values, true_values))
        assert relationship.n_paired - 2 in (0, 1)
        assert relationship.mean_difference.availability is AVAILABLE
        assert relationship.standardized_mean_difference.value is None
        assert relationship.standardized_mean_difference.reason is (
            Reason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
        )
    with pytest.raises(AssertionError, match=r"J\(2\) was evaluated"):
        _only(_frame([1.0], [3.0, 4.0, 8.0]))


def test_zero_within_group_variation_is_never_a_finite_ratio() -> None:
    flags = pd.Series([False, False, True, True, pd.NA], dtype="boolean")
    equal = _only(pd.DataFrame({"y": [2.5, 2.5, 2.5, 2.5, 9.0], "flag": flags}))
    assert equal.mean_difference.value == 0.0
    assert set(_reasons(equal)) == {Reason.CONSTANT_PAIRED_VALUES}

    different = _only(_frame([2.0, 2.0, 2.0], [5.0, 5.0]))
    assert different.mean_difference.value == 3.0
    assert different.standardized_mean_difference.value is None
    assert different.standardized_mean_difference.reason is (
        Reason.MATHEMATICALLY_UNBOUNDED
    )
    test = different.mean_difference_test
    assert test.statistic is None
    assert test.degrees_of_freedom is None
    assert test.frequentist.p_value is None
    assert test.statistic_reason is Reason.ZERO_WITHIN_GROUP_VARIATION
    assert test.frequentist.reason is Reason.ZERO_WITHIN_GROUP_VARIATION
    interval = different.mean_difference_interval
    assert (interval.lower, interval.upper) == (None, None)
    assert interval.reason is Reason.ZERO_WITHIN_GROUP_VARIATION

    singleton = _only(_frame([5.0], [3.0, 3.0, 3.0]))
    assert singleton.mean_difference.value == -2.0
    assert singleton.standardized_mean_difference.reason is (
        Reason.MATHEMATICALLY_UNBOUNDED
    )
    assert singleton.mean_difference_test.statistic_reason is (
        Reason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    )

    true_values = [4.0, 5.0, 7.0]
    false_values = [2.0, 2.0, 2.0]
    one_constant = _only(_frame(false_values, true_values))
    statistic, p_value = _scipy_welch(true_values, false_values)
    assert one_constant.mean_difference_test.statistic == pytest.approx(
        statistic, rel=1e-12
    )
    assert one_constant.mean_difference_test.frequentist.p_value == pytest.approx(
        p_value, rel=1e-10
    )
    assert one_constant.mean_difference_test.degrees_of_freedom == 2.0
    assert one_constant.standardized_mean_difference.value == pytest.approx(
        _independent_hedges(true_values, false_values), rel=1e-12
    )


def test_subnormal_spread_is_precision_collapse_not_zero_variation() -> None:
    relationship = _only(_frame([0.0] * 999 + [5e-324], [0.0] * 1000))
    assert relationship.false_group.descriptive.minimum == 0.0
    assert relationship.false_group.descriptive.maximum == 5e-324
    assert relationship.mean_difference.availability is AVAILABLE
    assert set(_reasons(relationship)) == {Reason.PRECISION_COLLAPSED}


def test_singleton_groups_keep_the_raw_difference() -> None:
    pair = _only(_frame([1.0], [3.0]))
    assert pair.mean_difference.value == 2.0
    assert set(_reasons(pair)) == {Reason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM}

    one_degree = _only(_frame([1.0], [3.0, 4.0]))
    assert one_degree.mean_difference.value == 2.5
    assert set(_reasons(one_degree)) == {
        Reason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    }

    single_false = _only(_frame([1.0], [3.0, 4.0, 8.0]))
    assert single_false.standardized_mean_difference.value == pytest.approx(
        _independent_hedges([3.0, 4.0, 8.0], [1.0]), rel=1e-12
    )
    assert single_false.mean_difference_test.statistic_reason is (
        Reason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    )
    assert single_false.mean_difference_interval.reason is (
        Reason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    )
    single_true = _only(_frame([3.0, 4.0, 8.0], [1.0]))
    assert single_true.standardized_mean_difference.value == (
        -single_false.standardized_mean_difference.value
    )


def test_welch_matches_scipy_for_ordinary_samples() -> None:
    rng = np.random.default_rng(29)
    cases = [
        (rng.normal(0.0, 1.0, 12), rng.normal(0.0, 1.0, 15)),
        (rng.normal(0.0, 1.0, 20), rng.normal(1.5, 1.0, 20)),
        (rng.normal(0.0, 0.2, 8), rng.normal(0.4, 3.0, 30)),
        (rng.normal(5.0, 2.0, 3), rng.normal(4.0, 1.0, 200)),
    ]
    for false_array, true_array in cases:
        false_values = false_array.tolist()
        true_values = true_array.tolist()
        relationship = _only(_frame(false_values, true_values))
        test = relationship.mean_difference_test
        statistic, p_value = _scipy_welch(true_values, false_values)
        independent = _independent_welch(true_values, false_values)
        assert test.method is MeanDifferenceTestMethod.WELCH_T
        assert test.statistic_availability is AVAILABLE
        assert test.statistic == pytest.approx(statistic, rel=1e-12)
        assert test.frequentist.p_value == pytest.approx(p_value, rel=1e-10)
        assert test.degrees_of_freedom == pytest.approx(independent["df"], rel=1e-12)
        assert relationship.mean_difference.value == pytest.approx(
            independent["difference"], rel=1e-12
        )
        assert 0.0 <= test.frequentist.p_value <= 1.0
        assert (test.statistic > 0.0) == (relationship.mean_difference.value > 0.0)
        assert test.frequentist.adjustment is (
            MultipleTestingAdjustment.BENJAMINI_HOCHBERG
        )
        assert test.frequentist.adjusted_p_value == test.frequentist.p_value
        smaller = min(len(true_values), len(false_values)) - 1
        assert smaller <= test.degrees_of_freedom <= relationship.n_paired - 2


@pytest.mark.parametrize(
    ("false_values", "true_values"),
    [
        (_FALSE, _TRUE),
        ([1.0, 1.5, 2.0, 2.5, 3.0], [8.0, 9.5, 11.0]),
        ([10.0, 30.0, 20.0, 40.0], [21.0, 19.0, 22.0, 18.0, 20.0, 23.0]),
        ([5.0, 6.0, 7.0], [1.0, 2.0, 3.0]),
    ],
)
def test_welch_interval_matches_an_independent_formula(
    false_values: list[float],
    true_values: list[float],
) -> None:
    relationship = _only(_frame(false_values, true_values))
    interval = relationship.mean_difference_interval
    reference = _independent_welch(true_values, false_values)
    assert interval.availability is AVAILABLE
    assert interval.level == 0.95
    assert interval.method is MeanDifferenceIntervalMethod.WELCH_SATTERTHWAITE
    assert interval.lower == pytest.approx(reference["lower"], rel=1e-12, abs=1e-12)
    assert interval.upper == pytest.approx(reference["upper"], rel=1e-12, abs=1e-12)
    assert interval.lower <= relationship.mean_difference.value <= interval.upper
    excludes_zero = interval.lower > 0.0 or interval.upper < 0.0
    p_value = relationship.mean_difference_test.frequentist.p_value
    assert excludes_zero == (p_value < 0.05)


def test_mixed_frame_counts_each_family_once() -> None:
    frame = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "b": [2, 1, 4, 3, 6, 5],
            "c": [0.5, 0.1, 0.9, 0.3, 0.7, 0.2],
            "g": pd.Categorical(["x", "y", "x", "y", "x", "y"]),
            "h": pd.Categorical(["u", "u", "v", "v", "w", "w"]),
            "p": [True, False, True, False, True, False],
            "q": pd.Series([True, True, False, pd.NA, False, True], dtype="boolean"),
            "code": pd.Series(_UUIDS, dtype="string"),
            "when": pd.to_datetime(
                [
                    "2020-01-01",
                    "2020-01-02",
                    "2020-01-03",
                    "2020-01-04",
                    "2020-01-05",
                    "2020-01-06",
                ]
            ),
            "fixed": [7, 7, 7, 7, 7, 7],
        }
    )
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert summary.n_total_pairs == 45
    assert summary.n_supported_pairs == summary.n_analyzed_pairs == 17
    assert len(summary.relationships) == 17
    assert summary.n_unimplemented_family_pairs == 9
    assert summary.n_ineligible_pairs == 19
    by_family: dict[RelationshipFamily, int] = {}
    for item in summary.relationships:
        by_family[item.family] = by_family.get(item.family, 0) + 1
    assert by_family == {
        RelationshipFamily.NUMERIC_NUMERIC: 3,
        RelationshipFamily.NUMERIC_CATEGORICAL: 6,
        RelationshipFamily.BOOLEAN_BOOLEAN: 1,
        RelationshipFamily.NUMERIC_BOOLEAN: 6,
        RelationshipFamily.CATEGORICAL_CATEGORICAL: 1,
    }
    assert {
        item.family: item.n_pairs for item in summary.unimplemented_family_counts
    } == {
        UnimplementedRelationshipFamily.DATETIME_NUMERIC: 3,
        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL: 2,
        UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN: 4,
    }
    roles = sorted(
        (item.numeric_position, item.boolean_position)
        for item in summary.relationships
        if isinstance(item, NumericBooleanRelationship)
    )
    assert roles == [(0, 5), (0, 6), (1, 5), (1, 6), (2, 5), (2, 6)]
    positions = [
        (item.left_position, item.right_position) for item in summary.relationships
    ]
    assert positions == sorted(set(positions))


def test_each_source_column_is_prepared_once(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "y": [6, 1, 5, 2, 4, 3],
            "z": [0.1, 0.4, 0.2, 0.8, 0.3, 0.9],
            "p": [True, False, True, False, True, False],
            "q": [True, True, False, False, True, False],
            "r": pd.Series([False, True, pd.NA, True, False, True], dtype="boolean"),
        }
    )
    numeric_reads: list[str] = []
    boolean_reads: list[str] = []
    original_numeric = collector_module._read_numeric_column
    original_boolean = collector_module._read_boolean_column

    def _spy_numeric(series: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        numeric_reads.append(str(series.name))
        return original_numeric(series)

    def _spy_boolean(series: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        boolean_reads.append(str(series.name))
        return original_boolean(series)

    monkeypatch.setattr(collector_module, "_read_numeric_column", _spy_numeric)
    monkeypatch.setattr(collector_module, "_read_boolean_column", _spy_boolean)
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert numeric_reads == ["x", "y", "z"]
    assert boolean_reads == ["p", "q", "r"]
    assert summary.n_supported_pairs == 15
    assert (
        sum(
            isinstance(item, NumericBooleanRelationship)
            for item in summary.relationships
        )
        == 9
    )


def test_summary_copies_numeric_boolean_records_without_recomputing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, 2.0, 3.0, 4.0, 5.0, np.nan],
            "flag": [False, False, True, True, True, False],
            "other": [False, False, False, False, False, True],
            "group": pd.Categorical(["a", "b", "a", "b", "a", "b"]),
        }
    )
    analysis = analyze_dataframe(frame)

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("summary builder used a source-dependent operation")

    monkeypatch.setattr(collector_module, "_analyze_numeric_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_categorical_categorical", _fail)
    monkeypatch.setattr(collector_module, "_read_numeric_column", _fail)
    monkeypatch.setattr(collector_module, "_read_boolean_column", _fail)
    monkeypatch.setattr(collector_module, "_read_categorical_column", _fail)
    monkeypatch.setattr(collector_module, "_association_methods", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_categorical", _fail)
    monkeypatch.setattr(collector_module, "_analyze_boolean", _fail)
    monkeypatch.setattr(numeric_boolean_module, "student_t", _fail)
    monkeypatch.setattr(numeric_boolean_module, "_from_finite", _fail)
    monkeypatch.setattr(numeric_boolean_module, "_moments", _fail)
    monkeypatch.setattr(numeric_numeric_module, "spearmanr", _fail)
    monkeypatch.setattr(numeric_numeric_module, "pearsonr", _fail)
    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _fail)
    monkeypatch.setattr(boolean_boolean_module, "fisher_exact", _fail)
    monkeypatch.setattr(column_module, "analyze_series", _fail)
    monkeypatch.setattr(column_module, "resolve_semantics", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    summary = build_relationships_summary(analysis)
    retained = analysis.relationship_analysis.relationships
    assert summary.relationships == retained
    copies = [
        (copied, original)
        for copied, original in zip(summary.relationships, retained)
        if isinstance(copied, NumericBooleanRelationship)
    ]
    assert len(copies) == 2
    absent_seen = False
    for copied, original in copies:
        assert copied is not original
        assert copied.false_group is not original.false_group
        assert copied.mean_difference is not original.mean_difference
        assert copied.mean_difference_test is not original.mean_difference_test
        assert copied.mean_difference_test.frequentist is not (
            original.mean_difference_test.frequentist
        )
        for copied_group, original_group in (
            (copied.false_group, original.false_group),
            (copied.true_group, original.true_group),
        ):
            if original_group.descriptive is None:
                absent_seen = True
                assert copied_group.descriptive is None
            else:
                assert copied_group.descriptive is not original_group.descriptive
    assert absent_seen
    _assert_plain_record(summary)
    _assert_plain_record(analysis.relationship_analysis)


def test_repeated_and_reordered_analysis_is_equal() -> None:
    rng = np.random.default_rng(2029)
    frame = pd.DataFrame(
        {
            "y": rng.normal(10.0, 3.0, 400),
            "flag": rng.random(400) < 0.35,
        }
    )
    first = _only(frame)
    assert _only(frame) == first
    shuffled = frame.iloc[rng.permutation(400)].reset_index(drop=True)
    assert _only(shuffled) == first
    _assert_plain_record(first)


def test_adding_numeric_boolean_pairs_leaves_other_families_unchanged() -> None:
    x = [1.0, 4.0, 2.0, 8.0, 5.0, 7.0]
    y = [2, 3, 1, 9, 4, 6]
    group = pd.Categorical(["a", "b", "a", "b", "c", "c"])
    p = [True, False, True, False, False, True]
    q = [False, False, True, True, False, True]
    together = build_relationships_summary(
        analyze_dataframe(pd.DataFrame({"x": x, "y": y, "g": group, "p": p, "q": q}))
    ).relationships
    numeric = _single(pd.DataFrame({"x": x, "y": y}), NumericNumericRelationship)
    categorical = _single(
        pd.DataFrame({"x": x, "g": group}),
        NumericCategoricalRelationship,
    )
    boolean = _single(pd.DataFrame({"p": p, "q": q}), BooleanBooleanRelationship)
    numeric_together = _pick(together, NumericNumericRelationship, 0, 1)
    categorical_together = _pick(together, NumericCategoricalRelationship, 0, 2)
    boolean_together = _pick(together, BooleanBooleanRelationship, 3, 4)
    assert numeric_together.spearman.estimate == numeric.spearman.estimate
    assert numeric_together.spearman.frequentist.p_value == (
        numeric.spearman.frequentist.p_value
    )
    assert numeric_together.pearson == numeric.pearson
    assert numeric_together.spearman.frequentist.adjusted_p_value != (
        numeric.spearman.frequentist.adjusted_p_value
    )
    assert categorical_together.groups == categorical.groups
    assert categorical_together.effect == categorical.effect
    assert categorical_together.omnibus.statistic == categorical.omnibus.statistic
    assert categorical_together.omnibus.frequentist.p_value == (
        categorical.omnibus.frequentist.p_value
    )
    assert boolean_together.table == boolean.table
    assert boolean_together.phi == boolean.phi
    assert boolean_together.independence.frequentist.p_value == (
        boolean.independence.frequentist.p_value
    )


def _single(frame: pd.DataFrame, kind: type) -> object:
    records = build_relationships_summary(analyze_dataframe(frame)).relationships
    assert len(records) == 1
    assert isinstance(records[0], kind)
    return records[0]


def _pick(records: tuple[object, ...], kind: type, left: int, right: int) -> object:
    for record in records:
        if (record.left_position, record.right_position) == (left, right):  # type: ignore[attr-defined]
            assert isinstance(record, kind)
            return record
    raise AssertionError("pair not found")


def test_attachment_requires_the_numeric_boolean_record() -> None:
    analysis = analyze_dataframe(_frame([1.0, 2.0], [3.0, 5.0]))
    columns = analysis.columns
    record = analysis.relationship_analysis.relationships[0]
    numeric_record = _single(
        pd.DataFrame({"y": [1.0, 2.0, 3.0, 5.0], "flag": [1.0, 4.0, 2.0, 3.0]}),
        NumericNumericRelationship,
    )
    assert relationship_analysis_for_columns(
        columns, n_rows=4, relationships=(record,)
    ) == (analysis.relationship_analysis)
    with pytest.raises(TypeError, match="numeric-boolean pair requires"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=(numeric_record,),
        )
    with pytest.raises(ValueError, match="numeric role must follow"):
        relationship_analysis_for_columns(
            columns,
            n_rows=4,
            relationships=(
                dataclasses.replace(record, numeric_position=1, boolean_position=0),
            ),
        )


def test_record_has_no_strength_significance_or_target_vocabulary() -> None:
    relationship = _only(_frame(_FALSE, _TRUE))
    names = {field.name for field in dataclasses.fields(relationship)} | {
        name for name in dir(relationship) if not name.startswith("_")
    }
    for forbidden in (
        "is_significant",
        "significant",
        "strength",
        "magnitude",
        "target",
        "predictor",
        "feature",
        "importance",
        "leakage",
        "treatment",
        "control",
        "primary_method",
        "confidence_level",
    ):
        assert forbidden not in names
    vocabulary = {
        member.value
        for enum_type in (
            NumericBooleanPopulation,
            BooleanGroupContrast,
            StandardizedDifferenceMethod,
            MeanDifferenceIntervalMethod,
            MeanDifferenceTestMethod,
        )
        for member in enum_type
    }
    assert vocabulary.isdisjoint({"small", "medium", "large", "weak", "strong"})


def test_calculator_rejects_misaligned_or_non_numeric_images() -> None:
    finite = np.array([True, True])
    observed = np.array([True, True])
    is_true = np.array([False, True])
    positions = dict(
        left_position=0,
        left_label="y",
        right_position=1,
        right_label="flag",
        numeric_position=0,
        boolean_position=1,
    )
    with pytest.raises(ValueError, match="one entry per row"):
        numeric_boolean_module.analyze(
            np.array([1.0, 2.0]),
            finite,
            observed,
            is_true,
            n_total_rows=3,
            **positions,
        )
    with pytest.raises(TypeError, match="integer or floating"):
        numeric_boolean_module.analyze(
            np.array(["a", "b"], dtype=object),
            finite,
            observed,
            is_true,
            n_total_rows=2,
            **positions,
        )


def test_defensive_numerical_states_stay_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _frame(_FALSE, _TRUE)

    class _NoTail:
        sf = staticmethod(lambda value, df: math.nan)
        ppf = staticmethod(stats.t.ppf)

    monkeypatch.setattr(numeric_boolean_module, "student_t", _NoTail)
    no_tail = _only(frame)
    assert no_tail.mean_difference_test.statistic_availability is AVAILABLE
    assert no_tail.mean_difference_test.frequentist.reason is Reason.NON_FINITE_RESULT
    assert no_tail.mean_difference_interval.availability is AVAILABLE

    class _NoQuantile:
        sf = staticmethod(stats.t.sf)
        ppf = staticmethod(lambda quantile, df: math.nan)

    monkeypatch.setattr(numeric_boolean_module, "student_t", _NoQuantile)
    no_quantile = _only(frame)
    assert no_quantile.mean_difference_interval.reason is Reason.NON_FINITE_RESULT
    assert no_quantile.mean_difference_test.frequentist.availability is AVAILABLE
    monkeypatch.undo()

    monkeypatch.setattr(numeric_boolean_module, "_float_mean", lambda values: None)
    no_mean = _only(frame)
    assert no_mean.mean_difference.reason is Reason.NON_FINITE_RESULT
    assert set(_reasons(no_mean)) == {Reason.NON_FINITE_RESULT}
    monkeypatch.undo()

    monkeypatch.setattr(
        numeric_boolean_module,
        "_scaled_sample_std",
        lambda values: math.inf,
    )
    no_scale = _only(frame)
    assert no_scale.mean_difference.availability is AVAILABLE
    assert set(_reasons(no_scale)) == {Reason.NON_FINITE_RESULT}


def test_numeric_boolean_components_reject_inconsistent_states() -> None:
    def frequentist(reason: UnavailabilityReason | None) -> FrequentistEvidence:
        if reason is None:
            return FrequentistEvidence(
                availability=AVAILABLE,
                p_value=0.5,
                adjusted_p_value=None,
                adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                reason=None,
            )
        return FrequentistEvidence(
            availability=UNAVAILABLE,
            p_value=None,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=reason,
        )

    hedges = StandardizedDifferenceMethod.HEDGES_G
    welch = MeanDifferenceIntervalMethod.WELCH_SATTERTHWAITE
    welch_t = MeanDifferenceTestMethod.WELCH_T
    described = collect_numeric_descriptive_analysis(pd.Series([1.0, 2.0]))
    empty = collect_numeric_descriptive_analysis(pd.Series([], dtype="float64"))
    with pytest.raises(TypeError, match="BooleanLevel"):
        BooleanGroupSummary("false", UNAVAILABLE, None, Reason.CONDITIONING_LEVEL_ABSENT)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="NumericDescriptiveAnalysis"):
        BooleanGroupSummary(BooleanLevel.FALSE, AVAILABLE, None, None)
    with pytest.raises(ValueError, match="at least one paired value"):
        BooleanGroupSummary(BooleanLevel.FALSE, AVAILABLE, empty, None)
    with pytest.raises(ValueError, match="observed group has no unavailability"):
        BooleanGroupSummary(
            BooleanLevel.FALSE, AVAILABLE, described, Reason.CONDITIONING_LEVEL_ABSENT
        )
    with pytest.raises(ValueError, match="absent group has no description"):
        BooleanGroupSummary(
            BooleanLevel.FALSE, UNAVAILABLE, described, Reason.CONDITIONING_LEVEL_ABSENT
        )
    with pytest.raises(ValueError, match="not a reason for this component"):
        BooleanGroupSummary(
            BooleanLevel.FALSE, UNAVAILABLE, None, Reason.NON_FINITE_RESULT
        )

    with pytest.raises(ValueError, match="finite float"):
        MeanDifferenceEstimate(AVAILABLE, math.inf, None)
    with pytest.raises(ValueError, match="finite float"):
        MeanDifferenceEstimate(AVAILABLE, 1, None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="negative zero"):
        MeanDifferenceEstimate(AVAILABLE, -0.0, None)
    with pytest.raises(ValueError, match="no unavailability reason"):
        MeanDifferenceEstimate(AVAILABLE, 1.0, Reason.NON_FINITE_RESULT)
    with pytest.raises(ValueError, match="has no value"):
        MeanDifferenceEstimate(UNAVAILABLE, 1.0, Reason.NON_FINITE_RESULT)
    with pytest.raises(ValueError, match="not a reason for this component"):
        MeanDifferenceEstimate(UNAVAILABLE, None, Reason.ZERO_WITHIN_GROUP_VARIATION)

    with pytest.raises(TypeError, match="StandardizedDifferenceMethod"):
        StandardizedMeanDifference("hedges_g", AVAILABLE, 1.0, None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no unavailability reason"):
        StandardizedMeanDifference(hedges, AVAILABLE, 1.0, Reason.NON_FINITE_RESULT)
    with pytest.raises(ValueError, match="has no value"):
        StandardizedMeanDifference(hedges, UNAVAILABLE, 1.0, Reason.NON_FINITE_RESULT)
    with pytest.raises(ValueError, match="not a reason for this component"):
        StandardizedMeanDifference(
            hedges, UNAVAILABLE, None, Reason.ZERO_WITHIN_GROUP_VARIATION
        )

    with pytest.raises(ValueError, match="0.95"):
        MeanDifferenceInterval(AVAILABLE, 0.9, welch, -1.0, 1.0, None)
    with pytest.raises(ValueError, match="Welch–Satterthwaite"):
        MeanDifferenceInterval(AVAILABLE, 0.95, None, -1.0, 1.0, None)
    with pytest.raises(ValueError, match="finite float"):
        MeanDifferenceInterval(AVAILABLE, 0.95, welch, -math.inf, 1.0, None)
    with pytest.raises(ValueError, match="out of order"):
        MeanDifferenceInterval(AVAILABLE, 0.95, welch, 2.0, 1.0, None)
    with pytest.raises(ValueError, match="no unavailability reason"):
        MeanDifferenceInterval(
            AVAILABLE, 0.95, welch, -1.0, 1.0, Reason.NON_FINITE_RESULT
        )
    with pytest.raises(ValueError, match="has no bounds"):
        MeanDifferenceInterval(
            UNAVAILABLE, 0.95, None, None, None, Reason.NON_FINITE_RESULT
        )
    with pytest.raises(ValueError, match="not a reason for this component"):
        MeanDifferenceInterval(
            UNAVAILABLE, None, None, None, None, Reason.MATHEMATICALLY_UNBOUNDED
        )

    with pytest.raises(TypeError, match="FrequentistEvidence"):
        MeanDifferenceTest(welch_t, AVAILABLE, 1.0, 3.0, None, None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not a Welch reason"):
        MeanDifferenceTest(
            welch_t, AVAILABLE, 1.0, 3.0, None, frequentist(Reason.BOUNDARY_CORRELATION)
        )
    with pytest.raises(ValueError, match="t statistic must be a finite float"):
        MeanDifferenceTest(welch_t, AVAILABLE, math.nan, 3.0, None, frequentist(None))
    with pytest.raises(ValueError, match="at least 1"):
        MeanDifferenceTest(welch_t, AVAILABLE, 1.0, 0.5, None, frequentist(None))
    with pytest.raises(ValueError, match="no unavailability reason"):
        MeanDifferenceTest(
            welch_t, AVAILABLE, 1.0, 3.0, Reason.NON_FINITE_RESULT, frequentist(None)
        )
    with pytest.raises(ValueError, match="only when it is non-finite"):
        MeanDifferenceTest(
            welch_t,
            AVAILABLE,
            1.0,
            3.0,
            None,
            frequentist(Reason.ZERO_WITHIN_GROUP_VARIATION),
        )
    with pytest.raises(ValueError, match="has no value"):
        MeanDifferenceTest(
            welch_t,
            UNAVAILABLE,
            1.0,
            None,
            Reason.NON_FINITE_RESULT,
            frequentist(Reason.NON_FINITE_RESULT),
        )
    with pytest.raises(ValueError, match="not a reason for this component"):
        MeanDifferenceTest(
            welch_t,
            UNAVAILABLE,
            None,
            None,
            Reason.MATHEMATICALLY_UNBOUNDED,
            frequentist(Reason.NON_FINITE_RESULT),
        )
    with pytest.raises(ValueError, match="Welch p-value must be unavailable"):
        MeanDifferenceTest(
            welch_t,
            UNAVAILABLE,
            None,
            None,
            Reason.ZERO_WITHIN_GROUP_VARIATION,
            frequentist(None),
        )


def test_relationship_record_rejects_inconsistent_components() -> None:
    replace = dataclasses.replace
    base = _only(_frame(_FALSE, _TRUE))
    absent = _only(
        pd.DataFrame(
            {"y": [1.0, 2.0, 3.0, np.nan], "flag": [False, False, False, True]}
        )
    )
    flags = pd.Series([False, False, True, True, pd.NA], dtype="boolean")
    equal = _only(pd.DataFrame({"y": [2.5, 2.5, 2.5, 2.5, 9.0], "flag": flags}))
    different = _only(_frame([2.0, 2.0, 2.0], [5.0, 5.0]))
    singletons = _only(_frame([1.0], [3.0]))
    single_false = _only(_frame([1.0], [3.0, 4.0, 8.0]))
    zero = _only(_frame([1.0, 2.0, 3.0], [0.0, 2.0, 4.0]))
    non_finite_difference = MeanDifferenceEstimate(
        UNAVAILABLE, None, Reason.NON_FINITE_RESULT
    )
    non_finite_standardized = StandardizedMeanDifference(
        StandardizedDifferenceMethod.HEDGES_G,
        UNAVAILABLE,
        None,
        Reason.NON_FINITE_RESULT,
    )
    non_finite_test = numeric_boolean_module._unavailable_test(Reason.NON_FINITE_RESULT)

    with pytest.raises(ValueError, match="roles must be the two physical"):
        replace(base, numeric_position=1, boolean_position=1)
    with pytest.raises(ValueError, match="false_group describes the False level"):
        replace(base, false_group=base.true_group, true_group=base.false_group)
    with pytest.raises(ValueError, match="true_group describes the True level"):
        replace(
            base,
            true_group=BooleanGroupSummary(
                BooleanLevel.FALSE, AVAILABLE, base.true_group.descriptive, None
            ),
        )
    with pytest.raises(ValueError, match="group sizes must sum"):
        replace(base, n_paired=8)
    for field in (
        "false_group",
        "mean_difference",
        "standardized_mean_difference",
        "mean_difference_interval",
        "mean_difference_test",
    ):
        with pytest.raises(TypeError, match=field):
            replace(base, **{field: None})
    with pytest.raises(ValueError, match="an absent group must be unavailable"):
        replace(
            absent,
            true_group=BooleanGroupSummary(
                BooleanLevel.TRUE,
                UNAVAILABLE,
                None,
                Reason.INSUFFICIENT_PAIRED_OBSERVATIONS,
            ),
        )
    with pytest.raises(ValueError, match="mean difference must be unavailable"):
        replace(absent, mean_difference=base.mean_difference)
    with pytest.raises(ValueError, match="equal paired values have mean difference 0"):
        replace(equal, mean_difference=MeanDifferenceEstimate(AVAILABLE, 1.0, None))
    with pytest.raises(
        ValueError, match="insufficient_within_group_degrees_of_freedom"
    ):
        replace(
            singletons,
            standardized_mean_difference=base.standardized_mean_difference,
        )
    with pytest.raises(ValueError, match="because mathematically_unbounded"):
        replace(
            different,
            standardized_mean_difference=equal.standardized_mean_difference,
        )
    with pytest.raises(ValueError, match="because non_finite_result"):
        replace(base, mean_difference=non_finite_difference)
    with pytest.raises(ValueError, match="unavailable only numerically"):
        replace(
            base,
            standardized_mean_difference=equal.standardized_mean_difference,
        )
    with pytest.raises(ValueError, match="zero mean difference has standardized"):
        replace(
            zero,
            standardized_mean_difference=base.standardized_mean_difference,
        )
    with pytest.raises(ValueError, match="carry the sign"):
        replace(
            base,
            standardized_mean_difference=StandardizedMeanDifference(
                StandardizedDifferenceMethod.HEDGES_G, AVAILABLE, -1.0, None
            ),
        )
    with pytest.raises(ValueError, match="Welch statistic must be unavailable"):
        replace(single_false, mean_difference_test=base.mean_difference_test)
    with pytest.raises(ValueError, match="because zero_within_group_variation"):
        replace(different, mean_difference_test=equal.mean_difference_test)
    with pytest.raises(ValueError, match="degrees of freedom lie between"):
        replace(
            base,
            mean_difference_test=replace(
                base.mean_difference_test, degrees_of_freedom=100.0
            ),
        )
    with pytest.raises(ValueError, match="interval with a defined scale"):
        replace(
            base,
            mean_difference_interval=different.mean_difference_interval,
        )
    with pytest.raises(
        ValueError, match="mean-difference interval must be unavailable"
    ):
        replace(
            singletons,
            mean_difference_interval=numeric_boolean_module._unavailable_interval(
                Reason.NON_FINITE_RESULT
            ),
        )
    with pytest.raises(ValueError, match="an interval requires a mean difference"):
        replace(
            base,
            mean_difference=non_finite_difference,
            standardized_mean_difference=non_finite_standardized,
            mean_difference_test=non_finite_test,
        )
    with pytest.raises(ValueError, match="must contain the mean difference"):
        replace(
            base,
            mean_difference_interval=replace(
                base.mean_difference_interval, lower=20.0, upper=30.0
            ),
        )
