"""TSK-030: Categorical × Categorical relationship foundation."""

from __future__ import annotations

import dataclasses
import math
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from scipy.stats import chi2_contingency

import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.relationships.boolean_boolean as boolean_boolean_module
import pytics.analysis.relationships.categorical_categorical as categorical_module
import pytics.analysis.relationships.collector as collector_module
import pytics.analysis.relationships.numeric_boolean as numeric_boolean_module
import pytics.analysis.relationships.numeric_categorical as numeric_categorical_module
import pytics.analysis.relationships.numeric_numeric as numeric_numeric_module
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationship import BooleanBooleanRelationship
from pytics.analysis.relationship import CategoricalAssociationEstimate
from pytics.analysis.relationship import CategoricalAssociationMethod
from pytics.analysis.relationship import CategoricalAxisOrder
from pytics.analysis.relationship import CategoricalCategoricalPopulation
from pytics.analysis.relationship import CategoricalCategoricalRelationship
from pytics.analysis.relationship import CategoricalContingencyTable
from pytics.analysis.relationship import CategoricalIndependenceMethod
from pytics.analysis.relationship import CategoricalIndependenceTest
from pytics.analysis.relationship import ExpectedCountDiagnostics
from pytics.analysis.relationship import FrequentistEvidence
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericBooleanRelationship
from pytics.analysis.relationship import NumericCategoricalRelationship
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import RelationshipFamily
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.relationship import UnimplementedRelationshipFamily
from pytics.analysis.relationship import build_relationships_summary
from pytics.analysis.relationships.categorical_categorical import _assemble
from pytics.analysis.relationships.categorical_categorical import _as_p_value
from pytics.analysis.relationships.categorical_categorical import _cramers_v
from pytics.analysis.relationships.categorical_categorical import _finite_chi_square
from pytics.analysis.relationships.categorical_categorical import _fraction
from pytics.analysis.relationships.categorical_categorical import _minimum_expected
from pytics.analysis.relationships.categorical_categorical import _normalize_unit
from pytics.analysis.relationships.categorical_categorical import _pearson_p_value
from pytics.semantics.interpretation import SemanticType

AVAILABLE = ResultAvailability.AVAILABLE
UNAVAILABLE = ResultAvailability.UNAVAILABLE
NOT_APPLIED = MultipleTestingAdjustment.NOT_APPLIED
Reason = UnavailabilityReason
_RETAINED = (
    pd.DataFrame,
    pd.Series,
    pd.Index,
    pd.Categorical,
    np.ndarray,
)
_UUIDS = (
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
)


def _frame(
    pairs: list[tuple[object, object]],
    *,
    left_categories: list[object] | tuple[object, ...] | None = None,
    right_categories: list[object] | tuple[object, ...] | None = None,
    **columns: object,
) -> pd.DataFrame:
    left_values = [pair[0] for pair in pairs]
    right_values = [pair[1] for pair in pairs]
    frame = pd.DataFrame(
        {
            "left": pd.Categorical(left_values, categories=left_categories),
            "right": pd.Categorical(right_values, categories=right_categories),
        }
    )
    for name, values in columns.items():
        frame[name] = values
    return frame


def _only(frame: pd.DataFrame) -> CategoricalCategoricalRelationship:
    records = [
        item
        for item in build_relationships_summary(analyze_dataframe(frame)).relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    ]
    assert len(records) == 1
    return records[0]


def _dense(table: CategoricalContingencyTable) -> list[list[int]]:
    rows = [
        [0 for _column in range(table.n_right_levels)]
        for _row in range(table.n_left_levels)
    ]
    for left_index, right_index, count in table.observed_counts:
        rows[left_index][right_index] = count
    return rows


def _abs_phi(
    top_left: int, top_right: int, bottom_left: int, bottom_right: int
) -> float:
    """Unsigned 2×2 phi from the Pearson counts. Not the Boolean calculator."""
    numerator = top_left * bottom_right - top_right * bottom_left
    if numerator == 0:
        return 0.0
    denominator = math.sqrt(
        (top_left + top_right)
        * (bottom_left + bottom_right)
        * (top_left + bottom_left)
        * (top_right + bottom_right)
    )
    return abs(numerator) / denominator


def _expected_reference(
    table: CategoricalContingencyTable,
) -> tuple[float, int, int, float]:
    """Independent expected-count diagnostics. Strictly less than 5 and 1."""
    n_paired = table.grand_total
    minimum = None
    below_5 = 0
    below_1 = 0
    n_cells = table.n_left_levels * table.n_right_levels
    for left_total in table.left_totals:
        for right_total in table.right_totals:
            expected = Fraction(left_total * right_total, n_paired)
            if minimum is None or expected < minimum:
                minimum = expected
            if expected < 5:
                below_5 += 1
            if expected < 1:
                below_1 += 1
    assert minimum is not None
    return float(minimum), below_5, below_1, below_5 / n_cells


def _assert_plain(value: object, seen: set[int] | None = None) -> None:
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
            _assert_plain(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_plain(item, seen)


def _assert_pearson(relationship: CategoricalCategoricalRelationship) -> None:
    table = relationship.table
    reference = chi2_contingency(_dense(table), correction=False)
    yates = chi2_contingency(_dense(table), correction=True)
    test = relationship.independence
    assert test.method is CategoricalIndependenceMethod.PEARSON_CHI_SQUARE
    assert test.statistic == pytest.approx(
        float(reference.statistic), rel=1e-12, abs=1e-12
    )
    assert test.degrees_of_freedom == int(reference.dof)
    assert test.degrees_of_freedom == (table.n_left_levels - 1) * (
        table.n_right_levels - 1
    )
    assert test.frequentist.p_value == pytest.approx(
        float(reference.pvalue), rel=1e-12, abs=1e-12
    )
    assert test.frequentist.adjustment is NOT_APPLIED
    assert test.frequentist.adjusted_p_value is None
    if int(reference.dof) == 1:
        assert test.statistic != pytest.approx(float(yates.statistic))
    assert relationship.association.method is CategoricalAssociationMethod.CRAMERS_V
    scale = relationship.n_paired * min(
        table.n_left_levels - 1, table.n_right_levels - 1
    )
    assert relationship.association.value == pytest.approx(
        math.sqrt(float(reference.statistic) / scale)
    )
    minimum, below_5, below_1, fraction = _expected_reference(table)
    diagnostics = relationship.expected_counts
    assert diagnostics.availability is AVAILABLE
    assert diagnostics.minimum_expected_count == pytest.approx(minimum)
    assert diagnostics.n_cells_expected_below_5 == below_5
    assert diagnostics.n_cells_expected_below_1 == below_1
    assert diagnostics.fraction_cells_expected_below_5 == pytest.approx(fraction)
    assert diagnostics.reason is None


def test_selected_categorical_pairs_are_calculated_and_other_types_are_not() -> None:
    frame = pd.DataFrame(
        {
            "stored": pd.Categorical(["a", "b", "a", "b"]),
            "ordered": pd.Categorical(
                ["b", "a", "b", "a"],
                categories=["b", "a"],
                ordered=True,
            ),
            "y": [1, 2, 3, 4],
            "flag": [True, False, True, False],
            "bits": [0, 1, 0, 1],
            "fixed": ["a", "a", "a", "a"],
            "blank": pd.Series([pd.NA, pd.NA, pd.NA, pd.NA], dtype="string"),
            "code": pd.Series(_UUIDS, dtype="string"),
            "note": pd.Series(["alpha", "beta", "gamma", "delta"], dtype="string"),
            "labels": pd.Series(["yes", "no", "yes", "no"], dtype="string"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = build_relationships_summary(analysis)
    assert analysis.columns[0].inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.columns[1].inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.columns[1].inferred.selected_type is not SemanticType.BOOLEAN
    assert analysis.columns[4].inferred.selected_type is SemanticType.NUMERIC
    assert analysis.columns[5].inferred.selected_type is SemanticType.CONSTANT
    assert analysis.columns[6].inferred.selected_type is SemanticType.EMPTY
    assert analysis.columns[7].inferred.selected_type is SemanticType.IDENTIFIER
    assert analysis.columns[8].inferred.selected_type is None
    assert analysis.columns[9].inferred.selected_type is None
    categorical = [
        item
        for item in summary.relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    ]
    assert len(categorical) == 1
    pair = categorical[0]
    assert (pair.left_position, pair.right_position) == (0, 1)
    assert pair.family is RelationshipFamily.CATEGORICAL_CATEGORICAL
    assert (
        pair.population
        is CategoricalCategoricalPopulation.PAIRWISE_NON_MISSING_CATEGORICAL
    )
    assert pair.axis_order is CategoricalAxisOrder.PHYSICAL_CATEGORICAL_VOCABULARY
    assert pair.table.left_levels == ("a", "b")
    assert pair.table.right_levels == ("b", "a")
    assert not any(
        isinstance(item, BooleanBooleanRelationship) and item.left_position == 0
        for item in summary.relationships
    )
    numeric_categorical = [
        item
        for item in summary.relationships
        if isinstance(item, NumericCategoricalRelationship)
    ]
    assert {
        (item.numeric_position, item.categorical_position)
        for item in numeric_categorical
    } == {
        (2, 0),
        (2, 1),
        (4, 0),
        (4, 1),
    }
    numeric_boolean = [
        item
        for item in summary.relationships
        if isinstance(item, NumericBooleanRelationship)
    ]
    assert {
        (item.numeric_position, item.boolean_position) for item in numeric_boolean
    } == {
        (2, 3),
        (4, 3),
    }
    assert "categorical_categorical" not in {
        family.value for family in UnimplementedRelationshipFamily
    }
    assert RelationshipFamily.CATEGORICAL_CATEGORICAL in RelationshipFamily
    assert summary.unimplemented_family_counts == ()


def test_boolean_and_numeric_pairs_stay_in_their_families() -> None:
    frame = pd.DataFrame(
        {
            "group": pd.Categorical(["a", "b", "a", "b"]),
            "flag": [True, False, True, False],
            "other": [False, True, False, True],
            "y": [1.0, 2.0, 3.0, 4.0],
        }
    )
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert not any(
        isinstance(item, CategoricalCategoricalRelationship)
        for item in summary.relationships
    )
    assert [type(item) for item in summary.relationships] == [
        NumericCategoricalRelationship,
        BooleanBooleanRelationship,
        NumericBooleanRelationship,
        NumericBooleanRelationship,
    ]


def test_population_excludes_each_missing_side_once() -> None:
    frame = _frame(
        [
            ("a", "x"),
            ("a", pd.NA),
            (pd.NA, "y"),
            ("b", "y"),
            (pd.NA, pd.NA),
        ],
        left_categories=["a", "b"],
        right_categories=["x", "y"],
    )
    before = frame.copy(deep=True)
    relationship = _only(frame)
    pd.testing.assert_frame_equal(frame, before)
    assert relationship.n_total_rows == 5
    assert relationship.n_paired == 2
    assert relationship.n_excluded == 3
    assert relationship.table.left_levels == ("a", "b")
    assert relationship.table.right_levels == ("x", "y")
    assert relationship.table.observed_counts == ((0, 0, 1), (1, 1, 1))
    assert relationship.table.left_totals == (1, 1)
    assert relationship.table.right_totals == (1, 1)
    assert relationship.table.grand_total == 2
    assert (
        sum(count for _left, _right, count in relationship.table.observed_counts) == 2
    )


def test_observed_tables_keep_vocabulary_order_and_drop_unused_levels() -> None:
    square = _only(
        _frame(
            [("a", "x"), ("a", "x"), ("a", "y"), ("b", "y"), ("b", "y")],
            left_categories=["a", "b", "z"],
            right_categories=["y", "x", "w"],
        )
    )
    assert square.table.left_levels == ("a", "b")
    assert square.table.right_levels == ("y", "x")
    assert square.table.observed_counts == ((0, 0, 1), (0, 1, 2), (1, 0, 2))
    assert square.table.left_totals == (3, 2)
    assert square.table.right_totals == (3, 2)
    assert "z" not in square.table.left_levels
    assert "w" not in square.table.right_levels

    rectangular = _only(
        _frame(
            [
                ("a", "x"),
                ("a", "x"),
                ("a", "y"),
                ("b", "y"),
                ("b", "y"),
                ("b", "y"),
                ("b", "z"),
                ("b", "z"),
                ("b", "z"),
                ("b", "z"),
            ],
            left_categories=["b", "a"],
            right_categories=["z", "x", "y", "unused"],
        )
    )
    assert rectangular.table.left_levels == ("b", "a")
    assert rectangular.table.right_levels == ("z", "x", "y")
    assert rectangular.table.observed_counts == (
        (0, 0, 4),
        (0, 2, 3),
        (1, 1, 2),
        (1, 2, 1),
    )
    assert rectangular.table.left_totals == (7, 3)
    assert rectangular.table.right_totals == (4, 2, 4)
    assert rectangular.n_paired == 10

    wide = _only(
        _frame(
            [
                ("a", "w"),
                ("a", "x"),
                ("b", "y"),
                ("b", "z"),
                ("c", "w"),
                ("c", "z"),
            ],
            left_categories=["c", "a", "b"],
            right_categories=["z", "y", "x", "w"],
        )
    )
    assert wide.table.n_left_levels == 3
    assert wide.table.n_right_levels == 4
    assert wide.table.left_totals == (2, 2, 2)
    assert wide.table.right_totals == (2, 1, 1, 2)
    assert sum(wide.table.left_totals) == sum(wide.table.right_totals) == 6


def test_row_reorder_preserves_declared_axes_and_column_swap_transposes() -> None:
    pairs = [("b", "y"), ("a", 1), (("b",), "y"), ("a", "x"), (("b",), 1)]
    categories = [("b",), "a", "b"]
    right_categories = ["y", 1, "x"]
    frame = _frame(pairs, left_categories=categories, right_categories=right_categories)
    original = _only(frame)
    assert original.table.left_levels == (("b",), "a", "b")
    assert original.table.right_levels == ("y", 1, "x")
    assert [type(level) for level in original.table.right_levels] == [str, int, str]
    shuffled = frame.iloc[[4, 1, 3, 0, 2]].reset_index(drop=True)
    assert _only(shuffled) == original
    assert list(shuffled["left"].cat.categories) == list(categories)

    reversed_frame = frame[["right", "left"]]
    transposed = _only(reversed_frame)
    assert transposed.table.left_levels == original.table.right_levels
    assert transposed.table.right_levels == original.table.left_levels
    assert transposed.association == original.association
    assert transposed.independence == original.independence
    assert transposed.expected_counts == original.expected_counts
    assert transposed.table.observed_counts != original.table.observed_counts


def test_category_identity_follows_the_pandas_vocabulary() -> None:
    collapsed = _only(
        _frame(
            [(1, "a"), (True, "a"), (1.0, "b"), (2, "b")],
            right_categories=["a", "b"],
        )
    )
    assert collapsed.table.left_levels == (1, 2)
    assert [type(level) for level in collapsed.table.left_levels] == [int, int]
    assert collapsed.table.left_totals == (3, 1)

    distinct = _only(
        _frame(
            [("1", "a"), (1, "a"), ("1", "b"), (1, "b")],
            left_categories=["1", 1],
            right_categories=["a", "b"],
        )
    )
    assert distinct.table.left_levels == ("1", 1)
    assert [type(level) for level in distinct.table.left_levels] == [str, int]

    stamped = _only(
        pd.DataFrame(
            {
                "left": pd.Categorical(
                    pd.to_datetime(["2020-01-02", "2020-01-01", "2020-01-02"])
                ),
                "right": pd.Categorical(["a", "b", "a"]),
            }
        )
    )
    assert all(isinstance(level, pd.Timestamp) for level in stamped.table.left_levels)
    assert not isinstance(stamped.table.left_levels[0], str)


def test_cramers_v_matches_the_classical_formula() -> None:
    independent = _only(
        _frame(
            [("a", "x")] * 1 + [("a", "y")] * 2 + [("b", "x")] * 3 + [("b", "y")] * 6,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert independent.association.value == 0.0
    assert independent.independence.statistic == 0.0
    assert independent.independence.frequentist.p_value == 1.0

    perfect = _only(
        _frame(
            [("a", "x")] * 5 + [("b", "y")] * 5,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert perfect.association.value == 1.0
    assert perfect.independence.statistic == 10.0
    assert perfect.independence.degrees_of_freedom == 1

    off_diagonal = _only(
        _frame(
            [("a", "y")] * 5 + [("b", "x")] * 5,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert off_diagonal.association.value == 1.0
    assert off_diagonal.table.observed_counts == ((0, 1, 5), (1, 0, 5))

    ordinary = _only(
        _frame(
            [("a", "x")] * 20
            + [("a", "y")] * 10
            + [("b", "x")] * 10
            + [("b", "y")] * 20,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert ordinary.association.value == pytest.approx(1 / 3)
    assert ordinary.association.value == pytest.approx(_abs_phi(20, 10, 10, 20))
    assert off_diagonal.association.value == pytest.approx(_abs_phi(0, 5, 5, 0))

    rectangular = _only(
        _frame(
            [("a", "x")] * 4 + [("b", "y")] * 3 + [("b", "z")] * 1 + [("c", "z")] * 6,
            left_categories=["a", "b", "c"],
            right_categories=["x", "y", "z"],
        )
    )
    _assert_pearson(rectangular)
    assert rectangular.association.value == pytest.approx(
        math.sqrt(
            float(
                chi2_contingency(_dense(rectangular.table), correction=False).statistic
            )
            / (14 * 2)
        )
    )


def test_two_by_two_v_is_unsigned_phi_and_boolean_phi_keeps_its_sign() -> None:
    categorical = _only(
        _frame(
            [("a", "y")] * 4 + [("b", "x")] * 6,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert categorical.association.value == pytest.approx(_abs_phi(0, 4, 6, 0))
    assert categorical.association.value == 1.0
    boolean = build_relationships_summary(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "left": [False] * 4 + [True] * 6,
                    "right": [True] * 4 + [False] * 6,
                }
            )
        )
    ).relationships[0]
    assert isinstance(boolean, BooleanBooleanRelationship)
    assert boolean.phi.value == pytest.approx(-1.0)
    assert categorical.association.value == pytest.approx(abs(boolean.phi.value))
    assert boolean.independence.method.value == "fisher_exact"
    assert (
        categorical.independence.method
        is CategoricalIndependenceMethod.PEARSON_CHI_SQUARE
    )


def test_pearson_chi_square_disables_yates_and_keeps_sparse_evidence() -> None:
    ordinary = _only(
        _frame(
            [("a", "x")] * 5 + [("a", "y")] * 1 + [("b", "y")] * 4,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    _assert_pearson(ordinary)
    assert ordinary.table.n_observed_cells == 3
    assert ordinary.independence.degrees_of_freedom == 1
    assert ordinary.independence.degrees_of_freedom != ordinary.table.n_observed_cells

    wide = _only(
        _frame(
            [
                ("a", "x"),
                ("a", "y"),
                ("a", "y"),
                ("b", "y"),
                ("b", "z"),
                ("b", "z"),
                ("b", "z"),
            ],
            left_categories=["a", "b"],
            right_categories=["x", "y", "z"],
        )
    )
    _assert_pearson(wide)
    assert wide.independence.degrees_of_freedom == 2

    grid = _only(
        _frame(
            [
                ("a", "w"),
                ("a", "x"),
                ("a", "y"),
                ("b", "x"),
                ("b", "z"),
                ("c", "w"),
                ("c", "y"),
                ("c", "z"),
            ],
            left_categories=["a", "b", "c"],
            right_categories=["w", "x", "y", "z"],
        )
    )
    _assert_pearson(grid)
    assert grid.independence.degrees_of_freedom == 6
    assert grid.table.n_observed_cells == 8

    sparse = _only(
        _frame(
            [("a", "x"), ("b", "y")],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert sparse.association.availability is AVAILABLE
    assert sparse.association.value == 1.0
    assert sparse.independence.statistic_availability is AVAILABLE
    assert sparse.independence.frequentist.availability is AVAILABLE
    assert sparse.expected_counts.n_cells_expected_below_5 == 4
    assert sparse.expected_counts.n_cells_expected_below_1 == 4
    assert (
        sparse.independence.method is CategoricalIndependenceMethod.PEARSON_CHI_SQUARE
    )
    assert not hasattr(sparse, "is_significant")
    assert not hasattr(sparse.association, "strength")
    p_value = sparse.independence.frequentist.p_value
    assert p_value is not None
    assert 0.0 <= p_value <= 1.0


def test_expected_count_of_five_is_not_below_five_and_zero_cells_still_count() -> None:
    balanced = _only(
        _frame(
            [("a", "x")] * 5 + [("a", "y")] * 5 + [("b", "x")] * 5 + [("b", "y")] * 5,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert balanced.expected_counts.minimum_expected_count == 5.0
    assert balanced.expected_counts.n_cells_expected_below_5 == 0
    assert balanced.expected_counts.fraction_cells_expected_below_5 == 0.0
    assert balanced.expected_counts.n_cells_expected_below_1 == 0
    assert balanced.association.value == 0.0

    skewed = _only(
        _frame(
            [("a", "x")] + [("b", "y")] * 100,
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert skewed.table.n_observed_cells == 2
    assert skewed.expected_counts.n_cells_expected_below_1 == 3
    assert skewed.expected_counts.minimum_expected_count == pytest.approx(1 / 101)
    _assert_pearson(skewed)


def test_degenerate_margins_keep_the_table_and_drop_association() -> None:
    empty = _only(
        _frame(
            [("a", pd.NA), ("b", pd.NA), (pd.NA, "x"), (pd.NA, "y")],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert empty.n_paired == 0
    assert empty.table.left_levels == ()
    assert empty.table.observed_counts == ()
    assert empty.association.reason is Reason.INSUFFICIENT_PAIRED_OBSERVATIONS
    assert (
        empty.independence.statistic_reason is Reason.INSUFFICIENT_PAIRED_OBSERVATIONS
    )
    assert empty.independence.degrees_of_freedom is None
    assert empty.expected_counts.reason is Reason.INSUFFICIENT_PAIRED_OBSERVATIONS

    left_constant = _only(
        _frame(
            [("a", "x"), ("a", "y"), ("b", pd.NA)],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert left_constant.table.n_left_levels == 1
    assert left_constant.table.n_right_levels == 2
    assert left_constant.table.left_totals == (2,)
    assert left_constant.association.reason is Reason.CONSTANT_PAIRED_VALUES
    assert left_constant.independence.statistic_reason is Reason.CONSTANT_PAIRED_VALUES
    assert left_constant.expected_counts.availability is AVAILABLE
    assert left_constant.association.value is None

    right_constant = _only(
        _frame(
            [("a", "x"), ("b", "x"), (pd.NA, "y")],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert right_constant.table.n_left_levels == 2
    assert right_constant.table.n_right_levels == 1
    assert right_constant.association.reason is Reason.CONSTANT_PAIRED_VALUES
    assert right_constant.expected_counts.availability is AVAILABLE

    both_constant = _only(
        _frame(
            [("a", "x"), ("a", "x"), ("b", pd.NA), (pd.NA, "y")],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    assert both_constant.table.n_left_levels == 1
    assert both_constant.table.n_right_levels == 1
    assert both_constant.table.observed_counts == ((0, 0, 2),)
    assert both_constant.association.reason is Reason.CONSTANT_PAIRED_VALUES
    assert both_constant.independence.frequentist.p_value is None


def test_large_counts_stay_finite_until_the_float_range_is_exceeded() -> None:
    huge = 2**60
    perfect = CategoricalContingencyTable(
        left_levels=("a", "b"),
        right_levels=("x", "y"),
        observed_counts=((0, 0, huge), (1, 1, huge)),
        left_totals=(huge, huge),
        right_totals=(huge, huge),
    )
    relationship = _assemble(
        perfect,
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=2 * huge,
    )
    reference = chi2_contingency([[huge, 0], [0, huge]], correction=False)
    assert relationship.association.value == 1.0
    assert relationship.independence.statistic == pytest.approx(
        float(reference.statistic)
    )
    assert relationship.independence.frequentist.p_value == 0.0
    assert relationship.independence.degrees_of_freedom == 1

    balanced = 2**40
    independent = _assemble(
        CategoricalContingencyTable(
            left_levels=("a", "b"),
            right_levels=("x", "y"),
            observed_counts=(
                (0, 0, balanced),
                (0, 1, balanced),
                (1, 0, balanced),
                (1, 1, balanced),
            ),
            left_totals=(2 * balanced, 2 * balanced),
            right_totals=(2 * balanced, 2 * balanced),
        ),
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=4 * balanced,
    )
    assert independent.association.value == 0.0
    assert independent.independence.statistic == 0.0
    assert independent.independence.frequentist.p_value == 1.0

    overflow_count = 10**310
    overflow = _assemble(
        CategoricalContingencyTable(
            left_levels=("a", "b"),
            right_levels=("x", "y"),
            observed_counts=((0, 0, overflow_count), (1, 1, overflow_count)),
            left_totals=(overflow_count, overflow_count),
            right_totals=(overflow_count, overflow_count),
        ),
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=2 * overflow_count,
    )
    assert overflow.table.observed_counts[0][2] == overflow_count
    assert overflow.association.reason is Reason.NON_FINITE_RESULT
    assert overflow.association.value is None
    assert overflow.independence.statistic is None
    assert overflow.independence.frequentist.p_value is None
    assert overflow.expected_counts.reason is Reason.NON_FINITE_RESULT
    assert overflow.expected_counts.minimum_expected_count is None


def test_unit_boundary_and_tail_failures_stay_component_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _finite_chi_square(-1e-12) == 0.0
    assert _finite_chi_square(-1e-6) is None
    assert _finite_chi_square(float("nan")) is None
    assert _finite_chi_square(float("inf")) is None
    assert _normalize_unit(1.0 + 1e-10) == 1.0
    assert _normalize_unit(1.0 + 1e-6) is None
    assert _normalize_unit(-1e-12) == 0.0
    assert _normalize_unit(-1e-6) is None
    assert _fraction(1, 0) is None
    assert _fraction(10**400, 1) is None
    assert _cramers_v(1.0, 10, 1, 2) is None
    assert _cramers_v(-1.0, 10, 2, 2) is None
    assert _cramers_v(1.0, 10**400, 2, 2) is None
    assert _cramers_v(1e-320, 10**20, 2, 2) == 0.0
    assert _normalize_unit(float("nan")) is None
    assert _normalize_unit(0.0) == 0.0
    assert _as_p_value("not-a-probability") is None
    assert _minimum_expected((1,), (1,), 10**400) is None
    assert _pearson_p_value(1e6, 1) == 0.0
    assert _pearson_p_value(0.0, 4) == 1.0

    frame = _frame(
        [("a", "x"), ("a", "y"), ("b", "x"), ("b", "y")],
        left_categories=["a", "b"],
        right_categories=["x", "y"],
    )

    def _nan(*_args: object, **_kwargs: object) -> float:
        return float("nan")

    monkeypatch.setattr(categorical_module, "_survival_function", _nan)
    failed_tail = _only(frame)
    assert failed_tail.association.availability is AVAILABLE
    assert failed_tail.independence.statistic_availability is AVAILABLE
    assert failed_tail.independence.frequentist.reason is Reason.NON_FINITE_RESULT
    assert failed_tail.independence.statistic is not None

    def _raise(*_args: object, **_kwargs: object) -> float:
        raise ValueError("tail")

    monkeypatch.setattr(categorical_module, "_survival_function", _raise)
    assert categorical_module._pearson_p_value(1.0, 1) is None
    monkeypatch.setattr(
        categorical_module, "_survival_function", lambda *_args, **_kwargs: True
    )
    assert categorical_module._pearson_p_value(1.0, 1) is None
    monkeypatch.setattr(
        categorical_module,
        "_survival_function",
        lambda *_args, **_kwargs: np.array([0.2]),
    )
    assert categorical_module._pearson_p_value(1.0, 1) is None

    monkeypatch.setattr(
        categorical_module, "_cramers_v", lambda *_args, **_kwargs: None
    )
    undefined_v = categorical_module.analyze(
        np.array([0, 0, 1, 1]),
        ("a", "b"),
        np.array([0, 1, 0, 1]),
        ("x", "y"),
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=4,
    )
    assert undefined_v.independence.statistic_availability is AVAILABLE
    assert undefined_v.association.reason is Reason.NON_FINITE_RESULT

    monkeypatch.setattr(categorical_module, "_cramers_v", _cramers_v)
    monkeypatch.setattr(categorical_module, "_fraction", lambda *_args, **_kwargs: None)
    undefined_fraction = categorical_module.analyze(
        np.array([0, 0, 1, 1]),
        ("a", "b"),
        np.array([0, 1, 0, 1]),
        ("x", "y"),
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=4,
    )
    assert undefined_fraction.association.availability is AVAILABLE
    assert undefined_fraction.expected_counts.reason is Reason.NON_FINITE_RESULT


def test_histogram_and_sorted_counters_match() -> None:
    rng = np.random.default_rng(7)
    left = rng.integers(0, 6, size=50)
    right = rng.integers(0, 4, size=50)
    assert categorical_module._cells_from_histogram(left, right, 6, 4) == (
        categorical_module._cells_from_sorted_pairs(left, right)
    )


def test_high_cardinality_does_not_allocate_a_dense_rectangle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    n_rows = 400
    vocabulary = 20_000
    levels = tuple(f"c{index}" for index in range(vocabulary))
    codes = np.arange(n_rows, dtype=np.int64)
    original_bincount = np.bincount
    lengths: list[int] = []

    def _guard(original: object) -> object:
        def _wrapped(shape: object, *args: object, **kwargs: object) -> np.ndarray:
            dims = shape if isinstance(shape, tuple) else (shape,)
            if len(dims) >= 2 and all(int(dim) >= 100 for dim in dims[:2]):
                raise AssertionError(f"dense rectangular allocation {dims}")
            size = 1
            for dim in dims:
                size *= int(dim)  # type: ignore[arg-type]
            if size > categorical_module._DENSE_HISTOGRAM_LIMIT:
                raise AssertionError(f"large allocation of {size}")
            return original(shape, *args, **kwargs)  # type: ignore[operator, no-any-return]

        return _wrapped

    def _guard_bincount(
        values: np.ndarray,
        weights: object = None,
        minlength: int = 0,
    ) -> np.ndarray:
        required = int(minlength)
        if np.size(values):
            required = max(required, int(np.max(values)) + 1)
        if required > categorical_module._DENSE_HISTOGRAM_LIMIT:
            raise AssertionError(f"bincount length {required}")
        lengths.append(required)
        return original_bincount(values, weights, minlength)

    monkeypatch.setattr(np, "empty", _guard(np.empty))
    monkeypatch.setattr(np, "zeros", _guard(np.zeros))
    monkeypatch.setattr(np, "ones", _guard(np.ones))
    monkeypatch.setattr(np, "full", _guard(np.full))
    monkeypatch.setattr(np, "bincount", _guard_bincount)
    relationship = categorical_module.analyze(
        codes,
        levels,
        codes,
        levels,
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=n_rows,
    )
    assert relationship.table.n_left_levels == n_rows
    assert relationship.table.n_right_levels == n_rows
    assert relationship.table.n_observed_cells == n_rows
    assert (
        relationship.table.n_left_levels * relationship.table.n_right_levels == 160_000
    )
    assert relationship.association.value == 1.0
    assert relationship.independence.degrees_of_freedom == (n_rows - 1) * (n_rows - 1)
    assert max(lengths) == n_rows * n_rows
    assert max(lengths) < vocabulary * vocabulary

    lengths.clear()
    wide = 1_100
    wide_codes = np.arange(wide, dtype=np.int64)
    wide_levels = tuple(range(wide))
    sorted_path = categorical_module.analyze(
        wide_codes,
        wide_levels,
        wide_codes,
        wide_levels,
        left_position=0,
        left_label="left",
        right_position=1,
        right_label="right",
        n_total_rows=wide,
    )
    assert wide * wide > categorical_module._DENSE_HISTOGRAM_LIMIT
    assert sorted_path.table.n_observed_cells == wide
    assert sorted_path.association.value == 1.0
    assert lengths
    assert max(lengths) == wide
    assert max(lengths) < wide * wide

    labels = [f"c{index}" for index in range(3_000)]
    observed = labels[:80]
    public = _only(
        pd.DataFrame(
            {
                "left": pd.Categorical(observed, categories=labels),
                "right": pd.Categorical(observed, categories=labels),
            }
        )
    )
    assert public.table.n_left_levels == 80
    assert public.table.n_observed_cells == 80
    assert public.n_paired == 80


def test_each_categorical_column_is_prepared_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "g": pd.Categorical(["a", "b", "a", "b"]),
            "h": pd.Categorical(["b", "a", "b", "a"]),
            "i": pd.Categorical(["a", "a", "b", "b"]),
            "y": [1, 2, 3, 4],
        }
    )
    reads: list[str] = []
    original = collector_module._read_categorical_column

    def _spy(series: pd.Series) -> tuple[np.ndarray, tuple[object, ...]]:
        reads.append(str(series.name))
        return original(series)

    monkeypatch.setattr(collector_module, "_read_categorical_column", _spy)
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert reads == ["g", "h", "i"]
    assert (
        sum(
            isinstance(item, CategoricalCategoricalRelationship)
            for item in summary.relationships
        )
        == 3
    )
    assert (
        sum(
            isinstance(item, NumericCategoricalRelationship)
            for item in summary.relationships
        )
        == 3
    )


def test_mixed_frame_counts_each_family_once() -> None:
    frame = pd.DataFrame(
        {
            "n1": [1.0, 2.0, 3.0, 4.0],
            "n2": [4, 3, 2, 1],
            "c1": pd.Categorical(["a", "b", "a", "b"]),
            "c2": pd.Categorical(["u", "u", "v", "v"]),
            "c3": pd.Categorical(["x", "y", "z", "x"]),
            "b1": [True, False, True, False],
            "b2": [False, False, True, True],
            "code": pd.Series(_UUIDS, dtype="string"),
            "when": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
            ),
            "fixed": [7, 7, 7, 7],
        }
    )
    summary = build_relationships_summary(analyze_dataframe(frame))
    assert summary.n_total_pairs == 45
    assert summary.n_supported_pairs == summary.n_analyzed_pairs == 15
    assert summary.n_unimplemented_family_pairs == 5
    assert summary.n_ineligible_pairs == 25
    assert (
        summary.n_supported_pairs
        + summary.n_unimplemented_family_pairs
        + summary.n_ineligible_pairs
        == summary.n_total_pairs
    )
    by_family: dict[RelationshipFamily, int] = {}
    positions = []
    for item in summary.relationships:
        by_family[item.family] = by_family.get(item.family, 0) + 1
        positions.append((item.left_position, item.right_position))
    assert by_family == {
        RelationshipFamily.NUMERIC_NUMERIC: 1,
        RelationshipFamily.NUMERIC_CATEGORICAL: 6,
        RelationshipFamily.NUMERIC_BOOLEAN: 4,
        RelationshipFamily.BOOLEAN_BOOLEAN: 1,
        RelationshipFamily.CATEGORICAL_CATEGORICAL: 3,
    }
    assert {
        item.family: item.n_pairs for item in summary.unimplemented_family_counts
    } == {
        UnimplementedRelationshipFamily.DATETIME_NUMERIC: 2,
        UnimplementedRelationshipFamily.DATETIME_CATEGORICAL: 3,
    }
    assert positions == sorted(set(positions))
    assert len(positions) == 15


def test_summary_copies_records_without_recomputing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0],
            "y": [4, 1, 2, 3],
            "g": pd.Categorical(["a", "b", "a", "b"]),
            "h": pd.Categorical(["u", "v", "u", "v"], categories=["v", "u", "missing"]),
            "p": [True, False, True, False],
            "q": [False, True, False, True],
        }
    )
    before = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    pd.testing.assert_frame_equal(frame, before)

    def _fail(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("summary builder used a source-dependent operation")

    monkeypatch.setattr(collector_module, "_analyze_categorical_categorical", _fail)
    monkeypatch.setattr(collector_module, "_read_categorical_column", _fail)
    monkeypatch.setattr(categorical_module, "_pearson_chi_square", _fail)
    monkeypatch.setattr(categorical_module, "_survival_function", _fail)
    monkeypatch.setattr(categorical_module, "chi2", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_categorical", _fail)
    monkeypatch.setattr(collector_module, "_analyze_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_boolean", _fail)
    monkeypatch.setattr(collector_module, "_association_methods", _fail)
    monkeypatch.setattr(collector_module, "_read_numeric_column", _fail)
    monkeypatch.setattr(collector_module, "_read_boolean_column", _fail)
    monkeypatch.setattr(numeric_numeric_module, "spearmanr", _fail)
    monkeypatch.setattr(numeric_numeric_module, "pearsonr", _fail)
    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _fail)
    monkeypatch.setattr(boolean_boolean_module, "fisher_exact", _fail)
    monkeypatch.setattr(numeric_boolean_module, "student_t", _fail)
    monkeypatch.setattr(column_module, "analyze_series", _fail)
    monkeypatch.setattr(column_module, "resolve_semantics", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    original = next(
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    )
    summary = build_relationships_summary(analysis)
    assert summary.relationships == analysis.relationship_analysis.relationships
    copied = next(
        item
        for item in summary.relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    )
    assert isinstance(copied, CategoricalCategoricalRelationship)
    assert copied is not original
    assert copied.table is not original.table
    assert copied.table.observed_counts is not original.table.observed_counts
    assert copied.association is not original.association
    assert copied.expected_counts is not original.expected_counts
    assert copied.independence is not original.independence
    assert copied.independence.frequentist is not original.independence.frequentist
    assert copied.table.right_levels == ("v", "u")
    _assert_plain(summary)
    _assert_plain(analysis.relationship_analysis)
    cells = original.table.observed_counts
    monkeypatch.undo()
    frame.iloc[0, 2] = "b"
    retained = next(
        item
        for item in analysis.relationship_analysis.relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    )
    assert retained.table.observed_counts == cells


def test_adding_categorical_pairs_leaves_other_families_unchanged() -> None:
    x = [1.0, 4.0, 2.0, 8.0, 5.0, 7.0]
    y = [2, 3, 1, 9, 4, 6]
    group = pd.Categorical(["a", "b", "a", "b", "c", "c"])
    other = pd.Categorical(["u", "v", "u", "v", "u", "v"])
    p = [True, False, True, False, False, True]
    q = [False, False, True, True, False, True]
    together = build_relationships_summary(
        analyze_dataframe(
            pd.DataFrame({"x": x, "y": y, "g": group, "h": other, "p": p, "q": q})
        )
    ).relationships
    numeric = build_relationships_summary(
        analyze_dataframe(pd.DataFrame({"x": x, "y": y}))
    ).relationships[0]
    categorical = build_relationships_summary(
        analyze_dataframe(pd.DataFrame({"x": x, "g": group}))
    ).relationships[0]
    boolean = build_relationships_summary(
        analyze_dataframe(pd.DataFrame({"p": p, "q": q}))
    ).relationships[0]
    flagged = build_relationships_summary(
        analyze_dataframe(pd.DataFrame({"x": x, "p": p}))
    ).relationships[0]
    assert isinstance(together[0], NumericNumericRelationship)
    assert isinstance(numeric, NumericNumericRelationship)
    assert together[0].methods == numeric.methods
    numeric_categorical = next(
        item
        for item in together
        if isinstance(item, NumericCategoricalRelationship)
        and (item.left_position, item.right_position) == (0, 2)
    )
    assert isinstance(categorical, NumericCategoricalRelationship)
    assert numeric_categorical.groups == categorical.groups
    assert numeric_categorical.effect == categorical.effect
    assert numeric_categorical.omnibus == categorical.omnibus
    boolean_together = next(
        item for item in together if isinstance(item, BooleanBooleanRelationship)
    )
    assert isinstance(boolean, BooleanBooleanRelationship)
    assert boolean_together.table == boolean.table
    assert boolean_together.phi == boolean.phi
    assert boolean_together.independence == boolean.independence
    numeric_boolean = next(
        item
        for item in together
        if isinstance(item, NumericBooleanRelationship)
        and (item.left_position, item.right_position) == (0, 4)
    )
    assert isinstance(flagged, NumericBooleanRelationship)
    assert numeric_boolean.mean_difference == flagged.mean_difference
    assert (
        numeric_boolean.standardized_mean_difference
        == flagged.standardized_mean_difference
    )
    assert numeric_boolean.mean_difference_test == flagged.mean_difference_test


def test_models_reject_inconsistent_categorical_tables() -> None:
    relationship = _only(
        _frame(
            [("a", "x"), ("a", "x"), ("a", "y"), ("b", "y"), ("b", "y")],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    with pytest.raises(ValueError, match="positive counts"):
        CategoricalContingencyTable(
            left_levels=("a", "b"),
            right_levels=("x", "y"),
            observed_counts=((0, 0, -1), (1, 1, 1)),
            left_totals=(1, 1),
            right_totals=(1, 1),
        )
    with pytest.raises(ValueError, match="match the left levels"):
        dataclasses.replace(relationship.table, left_totals=(5,))
    with pytest.raises(ValueError, match="marginal totals"):
        dataclasses.replace(
            relationship.table,
            observed_counts=((0, 0, 1), (0, 1, 1), (1, 1, 2)),
        )
    with pytest.raises(ValueError, match="grand total"):
        dataclasses.replace(relationship, n_paired=4)
    with pytest.raises(ValueError, match="row-major"):
        dataclasses.replace(
            relationship.table,
            observed_counts=((0, 0, 2), (0, 0, 1), (1, 1, 2)),
            left_totals=(3, 2),
        )
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        CategoricalAssociationEstimate(
            method=CategoricalAssociationMethod.CRAMERS_V,
            availability=AVAILABLE,
            value=1.1,
            reason=None,
        )
    with pytest.raises(ValueError, match="negative zero"):
        CategoricalAssociationEstimate(
            method=CategoricalAssociationMethod.CRAMERS_V,
            availability=AVAILABLE,
            value=-0.0,
            reason=None,
        )
    with pytest.raises(ValueError, match="p_value"):
        FrequentistEvidence(
            availability=AVAILABLE,
            p_value=1.5,
            adjusted_p_value=None,
            adjustment=NOT_APPLIED,
            reason=None,
        )
    with pytest.raises(ValueError, match="degrees of freedom"):
        dataclasses.replace(
            relationship.independence,
            degrees_of_freedom=0,
        )
    with pytest.raises(ValueError, match="degrees of freedom must be \\(r - 1\\)"):
        dataclasses.replace(
            relationship,
            independence=dataclasses.replace(
                relationship.independence,
                degrees_of_freedom=2,
            ),
        )
    with pytest.raises(ValueError, match="available association has no"):
        dataclasses.replace(
            relationship.association,
            reason=Reason.NON_FINITE_RESULT,
        )
    with pytest.raises(ValueError, match="unavailable association has no value"):
        CategoricalAssociationEstimate(
            method=CategoricalAssociationMethod.CRAMERS_V,
            availability=UNAVAILABLE,
            value=0.2,
            reason=Reason.CONSTANT_PAIRED_VALUES,
        )
    with pytest.raises(ValueError, match="positive int"):
        CategoricalIndependenceTest(
            method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            statistic_availability=AVAILABLE,
            statistic=1.0,
            degrees_of_freedom=True,  # type: ignore[arg-type]
            statistic_reason=None,
            frequentist=relationship.independence.frequentist,
        )
    with pytest.raises(TypeError, match="Python integers"):
        CategoricalContingencyTable(
            left_levels=("a", "b"),
            right_levels=("x", "y"),
            observed_counts=((0, 0, True), (1, 1, 1)),  # type: ignore[arg-type]
            left_totals=(1, 1),
            right_totals=(1, 1),
        )
    with pytest.raises(ValueError, match="positive marginal"):
        CategoricalContingencyTable(
            left_levels=("a",),
            right_levels=("x",),
            observed_counts=(),
            left_totals=(0,),
            right_totals=(0,),
        )
    with pytest.raises(TypeError, match="NumPy array"):
        categorical_module.analyze(
            [0, 1],  # type: ignore[arg-type]
            ("a", "b"),
            np.array([0, 1]),
            ("x", "y"),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )
    with pytest.raises(TypeError, match="integers"):
        categorical_module.analyze(
            np.array([0.0, 1.0]),
            ("a", "b"),
            np.array([0, 1]),
            ("x", "y"),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )
    with pytest.raises(ValueError, match="one entry per row"):
        categorical_module.analyze(
            np.array([0, 1]),
            ("a", "b"),
            np.array([0]),
            ("x",),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )
    with pytest.raises(ValueError, match="outside the categorical vocabulary"):
        categorical_module.analyze(
            np.array([0, 3]),
            ("a", "b"),
            np.array([0, 0]),
            ("x",),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )
    with pytest.raises(TypeError, match="tuple"):
        categorical_module.analyze(
            np.array([0, 1]),
            ["a", "b"],  # type: ignore[arg-type]
            np.array([0, 1]),
            ("x", "y"),
            left_position=0,
            left_label="left",
            right_position=1,
            right_label="right",
            n_total_rows=2,
        )


def _unavailable_frequentist(reason: Reason) -> FrequentistEvidence:
    return FrequentistEvidence(
        availability=UNAVAILABLE,
        p_value=None,
        adjusted_p_value=None,
        adjustment=NOT_APPLIED,
        reason=reason,
    )


def test_invalid_component_states_are_rejected() -> None:
    ordinary = _only(
        _frame(
            [("a", "x"), ("a", "y"), ("b", "x"), ("b", "y")],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    empty = _only(
        _frame(
            [("a", pd.NA), ("b", pd.NA), (pd.NA, "x"), (pd.NA, "y")],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    constant = _only(
        _frame(
            [("a", "x"), ("a", "y"), ("b", pd.NA)],
            left_categories=["a", "b"],
            right_categories=["x", "y"],
        )
    )
    available_p = ordinary.independence.frequentist
    with pytest.raises(TypeError, match="observed_counts must be a tuple"):
        dataclasses.replace(ordinary.table, observed_counts=[(0, 0, 1)])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot be empty on its own"):
        CategoricalContingencyTable(
            left_levels=(),
            right_levels=("x",),
            observed_counts=(),
            left_totals=(),
            right_totals=(1,),
        )
    with pytest.raises(TypeError, match="left_levels must be a tuple"):
        CategoricalContingencyTable(
            left_levels=["a"],  # type: ignore[arg-type]
            right_levels=("x",),
            observed_counts=((0, 0, 1),),
            left_totals=(1,),
            right_totals=(1,),
        )
    with pytest.raises(TypeError, match="left_totals must be a tuple"):
        CategoricalContingencyTable(
            left_levels=("a",),
            right_levels=("x",),
            observed_counts=((0, 0, 1),),
            left_totals=[1],  # type: ignore[arg-type]
            right_totals=(1,),
        )
    with pytest.raises(TypeError, match="left index, right index, and count"):
        CategoricalContingencyTable(
            left_levels=("a",),
            right_levels=("x",),
            observed_counts=((0, 0),),  # type: ignore[arg-type]
            left_totals=(1,),
            right_totals=(1,),
        )
    with pytest.raises(ValueError, match="outside the left axis"):
        CategoricalContingencyTable(
            left_levels=("a",),
            right_levels=("x",),
            observed_counts=((1, 0, 1),),
            left_totals=(1,),
            right_totals=(1,),
        )
    with pytest.raises(ValueError, match="outside the right axis"):
        CategoricalContingencyTable(
            left_levels=("a",),
            right_levels=("x",),
            observed_counts=((0, 1, 1),),
            left_totals=(1,),
            right_totals=(1,),
        )
    with pytest.raises(ValueError, match="included in cells below 5"):
        ExpectedCountDiagnostics(
            availability=AVAILABLE,
            minimum_expected_count=0.5,
            n_cells_expected_below_5=1,
            fraction_cells_expected_below_5=0.25,
            n_cells_expected_below_1=2,
            reason=None,
        )
    with pytest.raises(ValueError, match="available diagnostics have no"):
        ExpectedCountDiagnostics(
            availability=AVAILABLE,
            minimum_expected_count=0.5,
            n_cells_expected_below_5=0,
            fraction_cells_expected_below_5=0.0,
            n_cells_expected_below_1=0,
            reason=Reason.NON_FINITE_RESULT,
        )
    with pytest.raises(ValueError, match="unavailable diagnostics have no values"):
        ExpectedCountDiagnostics(
            availability=UNAVAILABLE,
            minimum_expected_count=0.5,
            n_cells_expected_below_5=None,
            fraction_cells_expected_below_5=None,
            n_cells_expected_below_1=None,
            reason=Reason.INSUFFICIENT_PAIRED_OBSERVATIONS,
        )
    with pytest.raises(ValueError, match="positive finite float"):
        ExpectedCountDiagnostics(
            availability=AVAILABLE,
            minimum_expected_count=0.0,
            n_cells_expected_below_5=0,
            fraction_cells_expected_below_5=0.0,
            n_cells_expected_below_1=0,
            reason=None,
        )
    with pytest.raises(ValueError, match="non-negative int"):
        ExpectedCountDiagnostics(
            availability=AVAILABLE,
            minimum_expected_count=0.5,
            n_cells_expected_below_5=-1,
            fraction_cells_expected_below_5=0.0,
            n_cells_expected_below_1=0,
            reason=None,
        )
    with pytest.raises(ValueError, match="not an independence reason"):
        CategoricalIndependenceTest(
            method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            statistic_availability=UNAVAILABLE,
            statistic=None,
            degrees_of_freedom=None,
            statistic_reason=Reason.CONSTANT_PAIRED_VALUES,
            frequentist=_unavailable_frequentist(Reason.PRECISION_COLLAPSED),
        )
    with pytest.raises(ValueError, match="available chi-square has no"):
        CategoricalIndependenceTest(
            method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            statistic_availability=AVAILABLE,
            statistic=1.0,
            degrees_of_freedom=1,
            statistic_reason=Reason.NON_FINITE_RESULT,
            frequentist=available_p,
        )
    with pytest.raises(ValueError, match="only when that tail is not finite"):
        CategoricalIndependenceTest(
            method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            statistic_availability=AVAILABLE,
            statistic=1.0,
            degrees_of_freedom=1,
            statistic_reason=None,
            frequentist=_unavailable_frequentist(Reason.CONSTANT_PAIRED_VALUES),
        )
    with pytest.raises(ValueError, match="has no statistic or degrees"):
        CategoricalIndependenceTest(
            method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            statistic_availability=UNAVAILABLE,
            statistic=1.0,
            degrees_of_freedom=None,
            statistic_reason=Reason.CONSTANT_PAIRED_VALUES,
            frequentist=_unavailable_frequentist(Reason.CONSTANT_PAIRED_VALUES),
        )
    with pytest.raises(ValueError, match="unavailable chi-square has no p-value"):
        CategoricalIndependenceTest(
            method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            statistic_availability=UNAVAILABLE,
            statistic=None,
            degrees_of_freedom=None,
            statistic_reason=Reason.CONSTANT_PAIRED_VALUES,
            frequentist=available_p,
        )
    with pytest.raises(ValueError, match="share a reason"):
        CategoricalIndependenceTest(
            method=CategoricalIndependenceMethod.PEARSON_CHI_SQUARE,
            statistic_availability=UNAVAILABLE,
            statistic=None,
            degrees_of_freedom=None,
            statistic_reason=Reason.CONSTANT_PAIRED_VALUES,
            frequentist=_unavailable_frequentist(
                Reason.INSUFFICIENT_PAIRED_OBSERVATIONS
            ),
        )
    with pytest.raises(ValueError, match="association must be unavailable"):
        dataclasses.replace(constant, association=ordinary.association)
    with pytest.raises(ValueError, match="chi-square must be unavailable"):
        dataclasses.replace(constant, independence=ordinary.independence)
    with pytest.raises(ValueError, match="diagnostics must be unavailable"):
        dataclasses.replace(empty, expected_counts=ordinary.expected_counts)
    with pytest.raises(ValueError, match="only when it is not finite"):
        dataclasses.replace(
            ordinary,
            independence=empty.independence,
        )
    with pytest.raises(ValueError, match="has no Cramér"):
        dataclasses.replace(
            ordinary,
            independence=dataclasses.replace(
                ordinary.independence,
                statistic_availability=UNAVAILABLE,
                statistic=None,
                degrees_of_freedom=None,
                statistic_reason=Reason.NON_FINITE_RESULT,
                frequentist=_unavailable_frequentist(Reason.NON_FINITE_RESULT),
            ),
        )
    with pytest.raises(ValueError, match="only when that value is not finite"):
        dataclasses.replace(ordinary, association=constant.association)
    with pytest.raises(ValueError, match="only when they are not finite"):
        dataclasses.replace(ordinary, expected_counts=empty.expected_counts)
    with pytest.raises(ValueError, match="cannot exceed the contingency rectangle"):
        dataclasses.replace(
            ordinary,
            expected_counts=dataclasses.replace(
                ordinary.expected_counts,
                n_cells_expected_below_5=100,
                fraction_cells_expected_below_5=1.0,
            ),
        )


def test_repeated_analysis_is_equal() -> None:
    frame = _frame(
        [("a", "x"), ("b", "y"), ("a", "y"), ("c", "x"), ("b", "z")],
        left_categories=["c", "a", "b"],
        right_categories=["z", "x", "y"],
    )
    assert _only(frame) == _only(frame)
