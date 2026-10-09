"""Relationship drift compares retained effects, not source p-values."""

from __future__ import annotations

import dataclasses
import decimal
import math
from typing import Iterable
from typing import Sequence
from typing import Tuple

import pandas as pd
import pytest

from pytics.analysis.compare import EffectChangeReason
from pytics.analysis.compare import PearsonChangeNull
from pytics.analysis.compare import PearsonChangeReason
from pytics.analysis.compare import RelationshipChangeMeasure
from pytics.analysis.compare import RelationshipDrift
from pytics.analysis.compare import RelationshipPairStatus
from pytics.analysis.compare import VocabularyStatus
from pytics.analysis.compare import compare_dataframes
from pytics.analysis.compare import compare_dataset_analyses
from pytics.analysis.compare.distribution_models import DistributionDriftStatus
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationships.models import RelationshipFamily
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.numeric_numeric import independent_pearson_equality
from pytics.analysis.relationships.models import UnimplementedRelationshipFamily


def _rho(x: Sequence[int], y: Sequence[int]) -> float:
    """Spearman rho for two permutations of distinct ranks."""
    n = len(x)
    squared = sum((left - right) ** 2 for left, right in zip(x, y))
    return 1.0 - 6.0 * squared / (n * (n * n - 1))


def _pearson(x: Sequence[float], y: Sequence[float]) -> float:
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    numerator = sum((left - mean_x) * (right - mean_y) for left, right in zip(x, y))
    left_scale = math.sqrt(sum((value - mean_x) ** 2 for value in x))
    right_scale = math.sqrt(sum((value - mean_y) ** 2 for value in y))
    return numerator / (left_scale * right_scale)


def _fisher_z(
    reference: float,
    reference_n: int,
    comparison: float,
    comparison_n: int,
) -> Tuple[float, float]:
    statistic = (math.atanh(comparison) - math.atanh(reference)) / math.sqrt(
        1.0 / (comparison_n - 3) + 1.0 / (reference_n - 3)
    )
    probability = math.erfc(abs(statistic) / math.sqrt(2.0))
    return statistic, probability


def _eta(groups: Sequence[Sequence[float]]) -> float:
    values = [value for group in groups for value in group]
    grand = sum(values) / len(values)
    total = sum((value - grand) ** 2 for value in values)
    between = sum(
        len(group) * (sum(group) / len(group) - grand) ** 2 for group in groups
    )
    return between / total


def _hedges_g(false_group: Sequence[float], true_group: Sequence[float]) -> float:
    false_mean = sum(false_group) / len(false_group)
    true_mean = sum(true_group) / len(true_group)
    false_scale = sum((value - false_mean) ** 2 for value in false_group)
    true_scale = sum((value - true_mean) ** 2 for value in true_group)
    degrees = len(false_group) + len(true_group) - 2
    pooled = math.sqrt((false_scale + true_scale) / degrees)
    half = degrees / 2.0
    correction = math.gamma(half) / (math.sqrt(half) * math.gamma(half - 0.5))
    return correction * (true_mean - false_mean) / pooled


def _phi(n_ff: int, n_ft: int, n_tf: int, n_tt: int) -> float:
    false_conditioning = n_ff + n_ft
    true_conditioning = n_tf + n_tt
    false_outcome = n_ff + n_tf
    true_outcome = n_ft + n_tt
    numerator = n_tt * n_ff - n_tf * n_ft
    denominator = math.sqrt(
        false_conditioning * true_conditioning * false_outcome * true_outcome
    )
    return numerator / denominator


def _cramers_v(table: Sequence[Sequence[int]]) -> float:
    rows = len(table)
    columns = len(table[0])
    total = sum(sum(row) for row in table)
    row_totals = [sum(row) for row in table]
    column_totals = [
        sum(table[row][column] for row in range(rows)) for column in range(columns)
    ]
    chi_square = 0.0
    for row in range(rows):
        for column in range(columns):
            expected = row_totals[row] * column_totals[column] / total
            chi_square += (table[row][column] - expected) ** 2 / expected
    return math.sqrt(chi_square / (total * min(rows - 1, columns - 1)))


def _frame(x: Sequence[int], y: Sequence[int]) -> pd.DataFrame:
    return pd.DataFrame({"x": list(x), "y": list(y)})


def _pair(result) -> RelationshipDrift:
    assert len(result.relationships) == 1
    return result.relationships[0]


def _spearman_p(frame: pd.DataFrame) -> float:
    relationship = analyze_dataframe(frame).relationship_analysis.relationships[0]
    evidence = relationship.methods[0].frequentist
    assert evidence.availability is ResultAvailability.AVAILABLE
    assert evidence.p_value is not None
    return evidence.p_value


def _walk(value: object) -> Iterable[object]:
    if isinstance(value, (str, bytes)):
        yield value
        return
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        yield value
        for item in dataclasses.astuple(value):
            yield from _walk(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _walk(item)
        return
    yield value


def test_spearman_change_keeps_direction_and_reversal() -> None:
    strong = (1, 2, 3, 4, 5)
    weak = (1, 2, 4, 3, 5)
    negative = (5, 4, 3, 2, 1)
    zero = (1, 5, 4, 3, 2)
    positive = (1, 2, 3, 4, 5)
    mild_positive = (1, 2, 4, 5, 3)
    mild_negative = (5, 4, 2, 1, 3)

    weakened = _pair(compare_dataframes(_frame(strong, strong), _frame(strong, weak)))
    assert weakened.primary is not None
    assert weakened.primary.measure is RelationshipChangeMeasure.SPEARMAN_RHO
    assert weakened.primary.reference == pytest.approx(_rho(strong, strong))
    assert weakened.primary.comparison == pytest.approx(_rho(strong, weak))
    assert weakened.primary.change == pytest.approx(
        _rho(strong, weak) - _rho(strong, strong)
    )
    assert weakened.primary.change == pytest.approx(-0.1)
    assert weakened.primary.sign_reversal is False
    assert weakened.primary.magnitude_change == pytest.approx(-0.1)

    reversed_pair = _pair(
        compare_dataframes(_frame(strong, strong), _frame(strong, negative))
    )
    assert reversed_pair.primary is not None
    assert reversed_pair.primary.reference == pytest.approx(1.0)
    assert reversed_pair.primary.comparison == pytest.approx(-1.0)
    assert reversed_pair.primary.change == pytest.approx(-2.0)
    assert reversed_pair.primary.sign_reversal is True
    assert reversed_pair.primary.magnitude_change == pytest.approx(0.0)
    assert reversed_pair.pearson_change_test is not None
    assert reversed_pair.pearson_change_test.reason is (
        PearsonChangeReason.BOUNDARY_CORRELATION
    )

    emerged = _pair(compare_dataframes(_frame(strong, zero), _frame(strong, positive)))
    assert emerged.primary is not None
    assert emerged.primary.reference == pytest.approx(0.0)
    assert emerged.primary.comparison == pytest.approx(1.0)
    assert emerged.primary.sign_reversal is False
    assert emerged.primary.change == pytest.approx(1.0)

    flipped = _pair(
        compare_dataframes(_frame(strong, mild_positive), _frame(strong, mild_negative))
    )
    assert flipped.primary is not None
    assert flipped.primary.reference == pytest.approx(0.7)
    assert flipped.primary.comparison == pytest.approx(-0.7)
    assert flipped.primary.change == pytest.approx(-1.4)
    assert flipped.primary.magnitude_change == pytest.approx(0.0)
    assert flipped.primary.sign_reversal is True
    pearson_reference = _pearson(strong, mild_positive)
    pearson_comparison = _pearson(strong, mild_negative)
    complementary = flipped.complementary[0]
    assert complementary.measure is RelationshipChangeMeasure.PEARSON_R
    assert complementary.reference == pytest.approx(pearson_reference)
    assert complementary.comparison == pytest.approx(pearson_comparison)
    assert complementary.change == pytest.approx(pearson_comparison - pearson_reference)
    assert complementary.sign_reversal is True
    test = flipped.pearson_change_test
    assert test is not None and test.p_value is not None and test.statistic is not None
    statistic, probability = _fisher_z(pearson_reference, 5, pearson_comparison, 5)
    assert test.statistic == pytest.approx(statistic)
    assert test.p_value == pytest.approx(probability)
    assert test.null is PearsonChangeNull.EQUAL_PEARSON_CORRELATIONS
    assert test.availability is ResultAvailability.AVAILABLE


def test_reorder_and_duplicate_labels_keep_one_logical_pair() -> None:
    reference = pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 2, 4, 3]})
    comparison = pd.DataFrame({"b": [1, 2, 4, 7], "a": [1, 3, 5, 7]})
    result = compare_dataframes(reference, comparison)
    record = _pair(result)
    assert record.alignment.first.reference_position == 0
    assert record.alignment.first.comparison_position == 1
    assert record.alignment.second.reference_position == 1
    assert record.alignment.second.comparison_position == 0
    assert record.alignment.first.reordered is True
    assert record.status is RelationshipPairStatus.SAME_FAMILY
    assert len(result.columns) == 2

    reference_duplicates = pd.DataFrame(
        [[1, 2, 1], [2, 3, 2], [3, 4, 4], [4, 5, 3]],
        columns=pd.Index(["a", "a", "b"]),
    )
    comparison_duplicates = pd.DataFrame(
        [[1, 1, 2], [2, 2, 3], [4, 4, 4], [3, 3, 5]],
        columns=pd.Index(["b", "a", "a"]),
    )
    duplicated = compare_dataframes(reference_duplicates, comparison_duplicates)
    assert duplicated.relationship_coverage.n_aligned_pairs == 3
    occurrences = {
        (
            record.alignment.first.occurrence,
            record.alignment.second.occurrence,
        )
        for record in duplicated.relationships
    }
    assert (1, 2) in occurrences
    paired = next(
        record
        for record in duplicated.relationships
        if record.alignment.first.reference_label.value == "a"
        and record.alignment.second.reference_label.value == "a"
    )
    assert paired.alignment.first.reference_position == 0
    assert paired.alignment.first.comparison_position == 1
    assert paired.alignment.second.reference_position == 1
    assert paired.alignment.second.comparison_position == 2


def test_true_does_not_align_with_integer_one() -> None:
    reference = pd.DataFrame({True: [1, 2, 3, 4], "x": [1, 2, 3, 4]})
    comparison = pd.DataFrame({1: [1, 2, 3, 4], "x": [4, 3, 2, 1]})
    result = compare_dataframes(reference, comparison)
    assert result.relationships == ()


def test_significance_transition_is_not_the_effect_change() -> None:
    reference_x = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    reference_y = (2, 3, 4, 5, 6, 1, 7, 8, 9, 10)
    comparison_x = (1, 2, 3, 4, 5)
    comparison_y = (1, 3, 2, 5, 4)
    reference_rho = _rho(reference_x, reference_y)
    comparison_rho = _rho(comparison_x, comparison_y)
    reference = _frame(reference_x, reference_y)
    comparison = _frame(comparison_x, comparison_y)
    reference_p = _spearman_p(reference)
    comparison_p = _spearman_p(comparison)
    assert reference_p < 0.05
    assert comparison_p > 0.05
    record = _pair(compare_dataframes(reference, comparison))
    assert record.primary is not None
    assert record.primary.change == pytest.approx(comparison_rho - reference_rho)
    assert abs(record.primary.change) < 0.03
    assert record.primary.sign_reversal is False
    assert not hasattr(record.primary, "p_value")
    assert not hasattr(record.primary, "adjusted_p_value")
    assert record.pearson_change_test is not None
    assert record.pearson_change_test.p_value != pytest.approx(reference_p)
    assert record.pearson_change_test.p_value != pytest.approx(comparison_p)


def test_effect_change_is_kept_when_source_p_values_agree() -> None:
    quiet_x = (1, 2, 3, 4, 5)
    quiet_reference = (1, 5, 4, 3, 2)
    quiet_comparison = (1, 2, 4, 5, 3)
    quiet = _pair(
        compare_dataframes(
            _frame(quiet_x, quiet_reference),
            _frame(quiet_x, quiet_comparison),
        )
    )
    assert _spearman_p(_frame(quiet_x, quiet_reference)) > 0.05
    assert _spearman_p(_frame(quiet_x, quiet_comparison)) > 0.05
    assert quiet.primary is not None
    assert quiet.primary.change == pytest.approx(0.7)
    assert quiet.primary.reference == pytest.approx(0.0)

    loud_x = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    loud_positive = (2, 3, 4, 5, 6, 1, 7, 8, 9, 10)
    loud_negative = tuple(11 - value for value in loud_positive)
    loud = _pair(
        compare_dataframes(_frame(loud_x, loud_positive), _frame(loud_x, loud_negative))
    )
    assert _spearman_p(_frame(loud_x, loud_positive)) < 0.05
    assert _spearman_p(_frame(loud_x, loud_negative)) < 0.05
    assert loud.primary is not None
    assert loud.primary.change == pytest.approx(
        _rho(loud_x, loud_negative) - _rho(loud_x, loud_positive)
    )
    assert loud.primary.change < -1.0
    assert loud.primary.sign_reversal is True


def test_eta_squared_change_records_vocabulary_without_blocking_subtraction() -> None:
    same_reference = pd.DataFrame(
        {"y": [0, 1, 2, 0, 1, 2], "g": pd.Categorical(["a", "a", "a", "b", "b", "b"])}
    )
    same_comparison = pd.DataFrame(
        {"y": [0, 0, 0, 3, 3, 3], "g": pd.Categorical(["a", "a", "a", "b", "b", "b"])}
    )
    same = _pair(compare_dataframes(same_reference, same_comparison))
    assert same.primary is not None
    assert same.primary.measure is RelationshipChangeMeasure.ETA_SQUARED
    assert same.primary.reference == pytest.approx(_eta(((0, 1, 2), (0, 1, 2))))
    assert same.primary.comparison == pytest.approx(_eta(((0, 0, 0), (3, 3, 3))))
    assert same.primary.change == pytest.approx(1.0)
    assert same.primary.sign_reversal is None
    assert same.primary.magnitude_change is None
    assert same.grouping_vocabulary is not None
    assert same.grouping_vocabulary.status is VocabularyStatus.SAME
    assert len(same.complementary) == 1
    assert same.complementary[0].measure is RelationshipChangeMeasure.EPSILON_SQUARED
    assert same.pearson_change_test is None

    added = _pair(
        compare_dataframes(
            same_comparison,
            pd.DataFrame(
                {
                    "y": [0, 0, 0, 3, 3, 3, 9, 9],
                    "g": pd.Categorical(["a", "a", "a", "b", "b", "b", "c", "c"]),
                }
            ),
        )
    )
    assert added.grouping_vocabulary is not None
    assert added.grouping_vocabulary.status is VocabularyStatus.CHANGED
    assert added.grouping_vocabulary.reference_n_levels == 2
    assert added.grouping_vocabulary.comparison_n_levels == 3
    assert added.primary is not None
    assert added.primary.availability is ResultAvailability.AVAILABLE
    assert added.primary.change == pytest.approx(0.0)

    removed = _pair(
        compare_dataframes(
            pd.DataFrame(
                {
                    "y": [0, 0, 1, 1, 5, 5],
                    "g": pd.Categorical(["a", "a", "b", "b", "c", "c"]),
                }
            ),
            pd.DataFrame(
                {"y": [0, 0, 1, 1], "g": pd.Categorical(["a", "a", "b", "b"])}
            ),
        )
    )
    assert removed.grouping_vocabulary is not None
    assert removed.grouping_vocabulary.status is VocabularyStatus.CHANGED
    assert removed.primary is not None and removed.primary.change is not None

    separated = _pair(
        compare_dataframes(
            pd.DataFrame(
                {
                    "y": [1, 1, 1, 4, 4, 4],
                    "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
                }
            ),
            pd.DataFrame(
                {
                    "y": [1, 1, 1, 4, 4, 4],
                    "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
                }
            ),
        )
    )
    assert separated.primary is not None
    assert separated.primary.reference == pytest.approx(1.0)
    assert separated.primary.change == pytest.approx(0.0)
    reference_anova = (
        analyze_dataframe(
            pd.DataFrame(
                {
                    "y": [1, 1, 1, 4, 4, 4],
                    "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
                }
            )
        )
        .relationship_analysis.relationships[0]
        .omnibus.frequentist
    )
    assert reference_anova.availability is ResultAvailability.UNAVAILABLE

    missing = _pair(
        compare_dataframes(
            pd.DataFrame(
                {"y": [1, 1, 1, 5], "g": pd.Categorical(["a", "a", "b", None])}
            ),
            same_comparison,
        )
    )
    assert missing.primary is not None
    assert missing.primary.availability is ResultAvailability.UNAVAILABLE
    assert missing.primary.reason is EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE
    assert missing.primary.reference is None
    assert missing.primary.comparison == pytest.approx(1.0)
    assert missing.primary.change is None


def test_hedges_g_keeps_true_minus_false_after_reorder() -> None:
    false_group = (1, 2, 3)
    true_group = (4, 5, 6)
    expected = _hedges_g(false_group, true_group)
    reference = pd.DataFrame(
        {
            "flag": [False, False, False, True, True, True],
            "amount": [1, 2, 3, 4, 5, 6],
        }
    )
    reordered = pd.DataFrame(
        {
            "amount": [1, 2, 3, 4, 5, 6],
            "flag": [False, False, False, True, True, True],
        }
    )
    stable = _pair(compare_dataframes(reference, reordered))
    assert stable.alignment.first.comparison_position == 1
    assert stable.primary is not None
    assert stable.primary.measure is RelationshipChangeMeasure.HEDGES_G
    assert stable.primary.reference == pytest.approx(expected)
    assert stable.primary.comparison == pytest.approx(expected)
    assert stable.primary.change == pytest.approx(0.0)
    assert stable.reference.numeric_boolean is not None
    assert stable.comparison.numeric_boolean is not None
    assert stable.reference.numeric_boolean.numeric_is_first is False
    assert stable.comparison.numeric_boolean.numeric_is_first is False

    flipped = pd.DataFrame(
        {
            "amount": [4, 5, 6, 1, 2, 3],
            "flag": [False, False, False, True, True, True],
        }
    )
    changed = _pair(compare_dataframes(reference, flipped))
    flipped_g = _hedges_g((4, 5, 6), (1, 2, 3))
    assert changed.primary is not None
    assert changed.primary.comparison == pytest.approx(flipped_g)
    assert changed.primary.change == pytest.approx(flipped_g - expected)
    assert changed.primary.sign_reversal is True
    mean_change = changed.complementary[0]
    assert mean_change.measure is RelationshipChangeMeasure.MEAN_DIFFERENCE
    assert mean_change.reference == pytest.approx(3.0)
    assert mean_change.comparison == pytest.approx(-3.0)
    assert mean_change.change == pytest.approx(-6.0)
    assert mean_change.sign_reversal is True


def test_phi_is_the_primary_boolean_change_and_orientation_is_explicit() -> None:
    reference_rows = (
        [(False, False)] * 8
        + [(False, True)] * 2
        + [(True, False)] * 1
        + [(True, True)] * 9
    )
    comparison_rows = (
        [(False, False)] * 2
        + [(False, True)] * 8
        + [(True, False)] * 7
        + [(True, True)] * 3
    )
    reference = pd.DataFrame(reference_rows, columns=["a", "b"])
    comparison = pd.DataFrame(comparison_rows, columns=["a", "b"])
    strengthened = _pair(compare_dataframes(reference, comparison))
    reference_phi = _phi(8, 2, 1, 9)
    comparison_phi = _phi(2, 8, 7, 3)
    assert strengthened.primary is not None
    assert strengthened.primary.measure is RelationshipChangeMeasure.PHI
    assert strengthened.primary.reference == pytest.approx(reference_phi)
    assert strengthened.primary.comparison == pytest.approx(comparison_phi)
    assert strengthened.primary.change == pytest.approx(comparison_phi - reference_phi)
    assert strengthened.primary.sign_reversal is True
    directional = strengthened.complementary[0]
    assert directional.availability is ResultAvailability.AVAILABLE
    assert directional.measure is RelationshipChangeMeasure.PROBABILITY_DIFFERENCE

    reordered = pd.DataFrame(
        {
            "b": [row[1] for row in comparison_rows],
            "a": [row[0] for row in comparison_rows],
        }
    )
    swapped = _pair(compare_dataframes(reference, reordered))
    assert swapped.primary is not None
    assert swapped.primary.comparison == pytest.approx(comparison_phi)
    assert swapped.complementary[0].reason is EffectChangeReason.ORIENTATION_NOT_SHARED
    assert swapped.complementary[0].change is None
    assert swapped.comparison.boolean_boolean is not None
    assert swapped.comparison.boolean_boolean.conditioning_is_first is False

    degenerate = pd.DataFrame(
        {
            "a": pd.Series([True, False, pd.NA, pd.NA], dtype="boolean"),
            "b": pd.Series([True, True, False, False], dtype="boolean"),
        }
    )
    varied = pd.DataFrame(
        {
            "a": [True, True, False, False],
            "b": [True, False, True, False],
        }
    )
    gap = _pair(compare_dataframes(degenerate, varied))
    assert gap.primary is not None
    assert gap.primary.reason is EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE
    assert gap.primary.change is None
    assert gap.primary.comparison == pytest.approx(_phi(1, 1, 1, 1))


def test_cramers_v_change_keeps_vocabulary_and_shape_diagnostics() -> None:
    reference = pd.DataFrame(
        {
            "left": pd.Categorical(["a", "a", "b", "b"]),
            "right": pd.Categorical(["x", "x", "y", "y"]),
        }
    )
    comparison = pd.DataFrame(
        {
            "right": pd.Categorical(["y", "x", "y", "x"]),
            "left": pd.Categorical(["a", "a", "b", "b"]),
        }
    )
    stable = _pair(compare_dataframes(reference, comparison))
    expected = _cramers_v(((2, 0), (0, 2)))
    assert stable.primary is not None
    assert stable.primary.measure is RelationshipChangeMeasure.CRAMERS_V
    assert stable.primary.reference == pytest.approx(expected)
    assert stable.primary.comparison == pytest.approx(_cramers_v(((1, 1), (1, 1))))
    assert stable.primary.change == pytest.approx(0.0 - expected)
    assert stable.contingency_vocabulary is not None
    assert stable.contingency_vocabulary.status is VocabularyStatus.SAME
    assert stable.reference.categorical_categorical is not None
    assert stable.comparison.categorical_categorical is not None
    assert stable.reference.categorical_categorical.first_levels == ("a", "b")
    assert stable.comparison.categorical_categorical.first_levels == ("a", "b")

    wider = pd.DataFrame(
        {
            "left": pd.Categorical(["a", "a", "b", "b", "a", "b"]),
            "right": pd.Categorical(["x", "y", "y", "z", "z", "x"]),
        }
    )
    changed = _pair(compare_dataframes(reference, wider))
    assert changed.contingency_vocabulary is not None
    assert changed.contingency_vocabulary.status is VocabularyStatus.CHANGED
    assert changed.contingency_vocabulary.reference_shape == (2, 2)
    assert changed.contingency_vocabulary.comparison_shape == (2, 3)
    assert changed.primary is not None
    assert changed.primary.change is not None
    assert changed.comparison.categorical_categorical is not None
    assert changed.comparison.categorical_categorical.n_positive_cells == 6

    sparse = pd.DataFrame(
        {
            "left": pd.Categorical(["a", "b", "c", "a"]),
            "right": pd.Categorical(["x", "y", "z", "x"]),
        }
    )
    sparse_record = _pair(compare_dataframes(reference, sparse))
    assert sparse_record.comparison.categorical_categorical is not None
    assert sparse_record.comparison.categorical_categorical.n_positive_cells == 3
    assert sparse_record.primary is not None
    assert sparse_record.primary.comparison == pytest.approx(
        _cramers_v(((2, 0, 0), (0, 1, 0), (0, 0, 1)))
    )
    assert sparse_record.contingency_vocabulary is not None
    assert sparse_record.contingency_vocabulary.status is VocabularyStatus.CHANGED


def test_family_and_availability_transitions_are_explicit() -> None:
    numeric = pd.DataFrame({"x": [1, 2, 3, 4], "y": [1, 2, 3, 4]})
    categorical = pd.DataFrame(
        {"x": [1, 2, 3, 4], "y": pd.Categorical(["a", "a", "b", "b"])}
    )
    transition = _pair(compare_dataframes(numeric, categorical))
    assert transition.status is RelationshipPairStatus.FAMILY_TRANSITION
    assert transition.primary is None
    assert transition.complementary == ()
    assert transition.reference.numeric_numeric is not None
    assert transition.comparison.numeric_categorical is not None

    unimplemented = compare_dataframes(
        pd.DataFrame(
            {
                "group": pd.Categorical(["a", "a", "b", "b"]),
                "flag": [True, False, True, False],
            }
        ),
        pd.DataFrame(
            {
                "flag": [False, True, False, True],
                "group": pd.Categorical(["a", "b", "a", "b"]),
            }
        ),
    )
    record = _pair(unimplemented)
    assert record.status is RelationshipPairStatus.UNIMPLEMENTED
    assert record.reference.unimplemented_family is (
        UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN
    )
    assert record.primary is None
    assert unimplemented.relationship_coverage.n_unimplemented == 1

    dated = compare_dataframes(
        pd.DataFrame(
            {"when": pd.date_range("2020-01-01", periods=4), "x": [1, 2, 3, 4]}
        ),
        pd.DataFrame(
            {"x": [1, 2, 3, 9], "when": pd.date_range("2021-01-01", periods=4)}
        ),
    )
    dated_record = _pair(dated)
    assert dated_record.status is RelationshipPairStatus.UNIMPLEMENTED
    assert dated_record.reference.unimplemented_family is (
        UnimplementedRelationshipFamily.DATETIME_NUMERIC
    )

    constant = pd.DataFrame({"x": [1, 1, 1, 1], "y": [1, 2, 3, 4]})
    emerged = _pair(compare_dataframes(constant, numeric))
    assert emerged.status is RelationshipPairStatus.ELIGIBILITY_TRANSITION
    assert emerged.primary is None


def test_unavailable_correlation_does_not_become_zero_change() -> None:
    reference = pd.DataFrame(
        {"x": [1.0, 2.0, 3.0, math.inf], "y": [1.0, 1.0, 1.0, 2.0]}
    )
    comparison = pd.DataFrame({"x": [1, 2, 3, 4], "y": [1, 2, 3, 5]})
    record = _pair(compare_dataframes(reference, comparison))
    assert record.status is RelationshipPairStatus.SAME_FAMILY
    assert record.primary is not None
    assert record.primary.availability is ResultAvailability.UNAVAILABLE
    assert record.primary.reason is EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE
    assert record.primary.change is None
    assert record.primary.comparison == pytest.approx(1.0)


def test_relationship_drift_does_not_read_source_values() -> None:
    reference = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [1, 2, 4, 3, 5]})
    comparison = pd.DataFrame({"y": [5, 4, 3, 2, 1], "x": [1, 2, 3, 4, 5]})
    result = compare_dataset_analyses(
        analyze_dataframe(reference),
        analyze_dataframe(comparison),
    )
    record = _pair(result)
    assert record.primary is not None
    assert record.primary.change == pytest.approx(-1.9)
    assert result.columns[0].distribution_status is (
        DistributionDriftStatus.SOURCE_VALUES_NOT_SUPPLIED
    )
    assert result.relationship_coverage.n_formal_change_tests_unavailable == 1
    names = {type(item).__name__ for item in _walk(result.relationships)}
    assert "DataFrame" not in names
    assert "Series" not in names
    assert "ndarray" not in names
    for record in result.relationships:
        assert "p_value" not in {field.name for field in dataclasses.fields(record.primary)}  # type: ignore[arg-type]
        score_names = {field.name for field in dataclasses.fields(record)}
        assert "score" not in score_names
        assert "severity" not in score_names


def test_coverage_counts_match_the_records() -> None:
    reference = pd.DataFrame(
        {
            "x": [1, 2, 3, 4],
            "y": [1, 2, 3, 5],
            "g": pd.Categorical(["a", "a", "b", "b"]),
            "flag": [True, False, True, False],
            "when": pd.date_range("2020-01-01", periods=4),
        }
    )
    comparison = reference.copy()
    comparison["y"] = [1, 3, 2, 4]
    result = compare_dataframes(reference, comparison)
    coverage = result.relationship_coverage
    assert coverage.n_aligned_pairs == len(result.relationships)
    assert (
        coverage.n_same_family
        + coverage.n_family_transition
        + coverage.n_unimplemented
        + coverage.n_eligibility_transition
        == coverage.n_aligned_pairs
    )
    assert coverage.n_unimplemented >= 1
    assert (
        coverage.n_effect_change_available + coverage.n_effect_change_unavailable
        == coverage.n_same_family
    )
    assert (
        coverage.n_formal_change_tests + coverage.n_formal_change_tests_unavailable
        == coverage.n_numeric_numeric
    )


def test_pearson_equality_is_undefined_without_degrees_of_freedom() -> None:
    assert independent_pearson_equality(0.2, 3, 0.4, 30) is None
    assert independent_pearson_equality(1.0, 30, 0.2, 30) is None
    statistic, probability = independent_pearson_equality(0.0, 12, 0.0, 12)
    assert statistic == 0.0
    assert probability == pytest.approx(1.0)


def test_effect_change_rejects_a_missing_side_and_a_false_reversal() -> None:
    with pytest.raises(ValueError, match="both effects"):
        from pytics.analysis.compare.relationship_models import EffectChange

        EffectChange(
            measure=RelationshipChangeMeasure.SPEARMAN_RHO,
            availability=ResultAvailability.AVAILABLE,
            reference=0.2,
            comparison=None,
            change=0.0,
            magnitude_change=None,
            sign_reversal=False,
            reason=None,
        )
    with pytest.raises(ValueError, match="sign reversal"):
        from pytics.analysis.compare.relationship_models import EffectChange

        EffectChange(
            measure=RelationshipChangeMeasure.SPEARMAN_RHO,
            availability=ResultAvailability.AVAILABLE,
            reference=0.0,
            comparison=0.4,
            change=0.4,
            magnitude_change=0.4,
            sign_reversal=True,
            reason=None,
        )


def _decimal_categories(*values: str) -> pd.Categorical:
    return pd.Categorical([decimal.Decimal(value) for value in values])


def _numeric_groups(categories: object, values: Sequence[float]) -> pd.DataFrame:
    return pd.DataFrame({"y": list(values), "g": categories})


def _category_pair(left: object, right: object) -> pd.DataFrame:
    return pd.DataFrame({"left": left, "right": right})


def test_unretained_numeric_vocabulary_is_not_same_or_changed() -> None:
    withheld = _numeric_groups(
        _decimal_categories("1", "1", "2", "2"),
        [1.0, 2.0, 3.0, 4.0],
    )
    other = _numeric_groups(
        _decimal_categories("3", "4", "3", "4"),
        [4.0, 3.0, 2.0, 1.0],
    )
    both = _pair(compare_dataframes(withheld, other))
    assert both.grouping_vocabulary is not None
    assert both.grouping_vocabulary.status is VocabularyStatus.NOT_RETAINABLE
    assert both.grouping_vocabulary.reference_n_levels == 0
    assert both.grouping_vocabulary.comparison_n_levels == 0
    assert both.primary is not None
    assert both.primary.reason is EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE
    assert both.primary.change is None
    assert both.complementary[0].reason is EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE
    assert both == _pair(compare_dataframes(withheld, other))

    observed = _numeric_groups(
        pd.Categorical(["a", "a", "b", "b"]),
        [1.0, 1.0, 2.0, 2.0],
    )
    one_side = _pair(compare_dataframes(withheld, observed))
    assert one_side.grouping_vocabulary is not None
    assert one_side.grouping_vocabulary.status is VocabularyStatus.NOT_RETAINABLE
    assert one_side.grouping_vocabulary.reference_n_levels == 0
    assert one_side.grouping_vocabulary.comparison_n_levels == 2
    assert one_side.primary is not None
    assert one_side.primary.reason is EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE
    assert one_side.primary.reference is None
    assert one_side.primary.comparison == pytest.approx(1.0)
    assert one_side.primary.change is None
    assert one_side == _pair(compare_dataframes(withheld, observed))


def test_observed_numeric_vocabularies_keep_same_and_changed() -> None:
    shared = _numeric_groups(
        pd.Categorical(["a", "a", "b", "b"]),
        [0.0, 1.0, 2.0, 3.0],
    )
    same = _pair(compare_dataframes(shared, shared.copy()))
    assert same.grouping_vocabulary is not None
    assert same.grouping_vocabulary.status is VocabularyStatus.SAME
    assert same.primary is not None
    assert same.primary.availability is ResultAvailability.AVAILABLE
    assert same.primary.change == pytest.approx(0.0)

    added = _numeric_groups(
        pd.Categorical(["a", "a", "b", "b", "c", "c"]),
        [0.0, 1.0, 2.0, 3.0, 9.0, 9.0],
    )
    changed = _pair(compare_dataframes(shared, added))
    assert changed.grouping_vocabulary is not None
    assert changed.grouping_vocabulary.status is VocabularyStatus.CHANGED
    assert changed.grouping_vocabulary.reference_n_levels == 2
    assert changed.grouping_vocabulary.comparison_n_levels == 3
    assert changed.primary is not None
    assert changed.primary.availability is ResultAvailability.AVAILABLE


def test_empty_paired_numeric_vocabulary_stays_an_observed_empty_set() -> None:
    empty = _numeric_groups(
        pd.Categorical(["a", "b", "a"]),
        [float("inf"), float("-inf"), float("nan")],
    )
    record = _pair(compare_dataframes(empty, empty))
    assert record.grouping_vocabulary is not None
    assert record.grouping_vocabulary.status is VocabularyStatus.SAME
    assert record.grouping_vocabulary.reference_n_levels == 0
    assert record.grouping_vocabulary.comparison_n_levels == 0
    assert record.primary is not None
    assert record.primary.reason is EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE

    populated = _numeric_groups(
        pd.Categorical(["a", "b", "a"]),
        [1.0, 1.0, 2.0],
    )
    changed = _pair(compare_dataframes(empty, populated))
    assert changed.grouping_vocabulary is not None
    assert changed.grouping_vocabulary.status is VocabularyStatus.CHANGED


def test_unretained_contingency_vocabulary_is_not_same_or_changed() -> None:
    withheld = _category_pair(
        _decimal_categories("1", "1", "2", "2"),
        _decimal_categories("3", "3", "4", "4"),
    )
    other = _category_pair(
        _decimal_categories("5", "6", "5", "6"),
        _decimal_categories("7", "7", "8", "8"),
    )
    both = _pair(compare_dataframes(withheld, other))
    vocabulary = both.contingency_vocabulary
    assert vocabulary is not None
    assert vocabulary.status is VocabularyStatus.NOT_RETAINABLE
    assert vocabulary.first.status is VocabularyStatus.NOT_RETAINABLE
    assert vocabulary.second.status is VocabularyStatus.NOT_RETAINABLE
    assert vocabulary.reference_shape == (0, 0)
    assert vocabulary.comparison_shape == (0, 0)
    assert both.primary is not None
    assert both.primary.reason is EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE
    assert both.complementary[0].reason is EffectChangeReason.BOTH_EFFECTS_UNAVAILABLE
    assert both == _pair(compare_dataframes(withheld, other))

    observed = _category_pair(
        pd.Categorical(["a", "a", "b", "b"]),
        pd.Categorical(["x", "x", "y", "y"]),
    )
    one_side = _pair(compare_dataframes(withheld, observed))
    vocabulary = one_side.contingency_vocabulary
    assert vocabulary is not None
    assert vocabulary.status is VocabularyStatus.NOT_RETAINABLE
    assert vocabulary.first.status is VocabularyStatus.NOT_RETAINABLE
    assert vocabulary.second.status is VocabularyStatus.NOT_RETAINABLE
    assert vocabulary.reference_shape == (0, 0)
    assert vocabulary.comparison_shape == (2, 2)
    assert one_side.primary is not None
    assert one_side.primary.reason is EffectChangeReason.REFERENCE_EFFECT_UNAVAILABLE
    assert one_side.primary.comparison == pytest.approx(1.0)
    assert one_side.primary.change is None
    assert one_side == _pair(compare_dataframes(withheld, observed))


def test_observed_contingency_vocabularies_keep_same_and_changed() -> None:
    reference = _category_pair(
        pd.Categorical(["a", "a", "b", "b"]),
        pd.Categorical(["x", "x", "y", "y"]),
    )
    same = _pair(compare_dataframes(reference, reference.copy()))
    assert same.contingency_vocabulary is not None
    assert same.contingency_vocabulary.status is VocabularyStatus.SAME
    assert same.primary is not None
    assert same.primary.availability is ResultAvailability.AVAILABLE
    assert same.primary.change == pytest.approx(0.0)

    changed_frame = _category_pair(
        pd.Categorical(["a", "a", "b", "b"]),
        pd.Categorical(["x", "x", "z", "z"]),
    )
    changed = _pair(compare_dataframes(reference, changed_frame))
    assert changed.contingency_vocabulary is not None
    assert changed.contingency_vocabulary.status is VocabularyStatus.CHANGED
    assert changed.primary is not None
    assert changed.primary.availability is ResultAvailability.AVAILABLE


def test_unretained_vocabulary_leaves_a_numeric_pair_unchanged() -> None:
    def frame(second: Sequence[float]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "n1": [1.0, 2.0, 3.0, 4.0],
                "n2": list(second),
                "g": _decimal_categories("1", "1", "2", "2"),
            }
        )

    values = [1.0, 2.0, 3.0, 5.0]
    result = compare_dataframes(frame(values), frame(values))
    records = list(result.relationships)
    assert len(records) == 3
    numeric = [
        record
        for record in records
        if record.reference.family is RelationshipFamily.NUMERIC_NUMERIC
    ]
    assert len(numeric) == 1
    assert numeric[0].grouping_vocabulary is None
    assert numeric[0].pearson_change_test is not None
    assert numeric[0].primary is not None
    assert numeric[0].primary.availability is ResultAvailability.AVAILABLE
    grouped = [record for record in records if record.grouping_vocabulary is not None]
    assert len(grouped) == 2
    assert all(
        record.grouping_vocabulary is not None
        and record.grouping_vocabulary.status is VocabularyStatus.NOT_RETAINABLE
        for record in grouped
    )
    assert (
        result.relationships
        == compare_dataframes(frame(values), frame(values)).relationships
    )
