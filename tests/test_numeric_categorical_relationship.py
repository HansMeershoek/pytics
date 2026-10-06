"""TSK-026: Numeric × Categorical relationship analysis."""

from __future__ import annotations

import dataclasses
import inspect
import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import f_oneway

import pytics.analysis.relationships.collector as collector_module
import pytics.analysis.relationships.numeric_categorical as numeric_categorical_module
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.numeric import collect_numeric_descriptive_analysis
from pytics.analysis.relationship import CategoricalCategoricalRelationship
from pytics.analysis.relationship import CategoricalGroupSummary
from pytics.analysis.relationship import CategoryGroupOrder
from pytics.analysis.relationship import FrequentistEvidence
from pytics.analysis.relationship import GroupEffectEstimate
from pytics.analysis.relationship import GroupEffectMethod
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericBooleanRelationship
from pytics.analysis.relationship import NumericCategoricalPopulation
from pytics.analysis.relationship import NumericCategoricalRelationship
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import OmnibusAnovaResult
from pytics.analysis.relationship import OmnibusTestMethod
from pytics.analysis.relationship import RelationshipFamily
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.relationship import UnimplementedFamilyCount
from pytics.analysis.relationship import UnimplementedRelationshipFamily
from pytics.analysis.relationship import relationship_analysis_for_columns
from pytics.semantics.interpretation import SemanticType

_RETAINED = (pd.DataFrame, pd.Series, pd.Index, np.ndarray)


def _relationship(frame: pd.DataFrame) -> NumericCategoricalRelationship:
    summary = analyze_dataframe(frame).relationship_analysis
    assert summary.n_analyzed_pairs == 1
    relationship = summary.relationships[0]
    assert isinstance(relationship, NumericCategoricalRelationship)
    return relationship


def _hand_eta(groups: list[np.ndarray]) -> float:
    """Independent eta squared for a tiny, well-scaled example."""
    arrays = [np.asarray(group, dtype=float) for group in groups]
    values = np.concatenate(arrays)
    grand = float(values.mean())
    ss_between = sum(
        len(group) * (float(group.mean()) - grand) ** 2 for group in arrays
    )
    ss_total = float(np.sum((values - grand) ** 2))
    return ss_between / ss_total


def _assert_no_retained_source(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _RETAINED)
    assert "GroupBy" not in type(value).__name__
    module = type(value).__module__
    assert not module.startswith(("scipy", "pandas.core", "numpy"))
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_no_retained_source(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_retained_source(item, seen)


def test_orientation_does_not_follow_physical_side() -> None:
    numeric = [1, 2, 3, 4, 5, 6]
    categorical = pd.Categorical(["a", "a", "a", "b", "b", "b"])
    left_numeric = _relationship(pd.DataFrame({"y": numeric, "g": categorical}))
    left_categorical = _relationship(pd.DataFrame({"g": categorical, "y": numeric}))
    assert left_numeric.numeric_position == 0
    assert left_numeric.categorical_position == 1
    assert left_categorical.numeric_position == 1
    assert left_categorical.categorical_position == 0
    assert left_numeric.left_position == 0
    assert left_numeric.right_position == 1
    assert left_categorical.left_position == 0
    assert left_categorical.right_position == 1
    assert left_numeric.effect.value == left_categorical.effect.value
    assert left_numeric.omnibus.statistic == left_categorical.omnibus.statistic
    assert left_numeric.omnibus.frequentist.p_value == (
        left_categorical.omnibus.frequentist.p_value
    )
    assert [group.category for group in left_numeric.groups] == ["a", "b"]

    wide = pd.DataFrame(
        {
            "g": pd.Categorical(["a", "a", "b", "b"]),
            "flag": [True, False, True, False],
            "y": [1, 2, 10, 11],
        }
    )
    summary = analyze_dataframe(wide).relationship_analysis
    pair = summary.relationships[0]
    assert isinstance(pair, NumericCategoricalRelationship)
    assert (pair.left_position, pair.right_position) == (0, 2)
    assert pair.categorical_position == 0
    assert pair.numeric_position == 2
    assert pair.family is RelationshipFamily.NUMERIC_CATEGORICAL
    assert pair.population is (
        NumericCategoricalPopulation.FINITE_NUMERIC_OBSERVED_CATEGORY
    )
    assert pair.group_order is CategoryGroupOrder.PHYSICAL_CATEGORICAL_VOCABULARY


def test_physical_categorical_is_eligible_and_other_types_are_not() -> None:
    frame = pd.DataFrame(
        {
            "y": [1, 2, 3, 4],
            "stored": pd.Categorical(["a", "b", "a", "b"]),
            "ordered": pd.Categorical(
                ["a", "b", "a", "b"],
                categories=["a", "b"],
                ordered=True,
            ),
            "flag": [True, False, True, False],
            "fixed": [5, 5, 5, 5],
            "blank": pd.Series([pd.NA, pd.NA, pd.NA, pd.NA], dtype="Int64"),
            "code": pd.Series(
                [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                    "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
                    "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
                ],
                dtype="string",
            ),
            "note": pd.Series(["alpha", "beta", "gamma", "delta"], dtype="string"),
        }
    )
    analysis = analyze_dataframe(frame)
    summary = analysis.relationship_analysis
    categorical_pairs = [
        item
        for item in summary.relationships
        if isinstance(item, NumericCategoricalRelationship)
    ]
    assert [item.categorical_position for item in categorical_pairs] == [1, 2]
    assert analysis.columns[1].inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.columns[2].inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.columns[3].inferred.selected_type is SemanticType.BOOLEAN
    assert analysis.columns[4].inferred.selected_type is SemanticType.CONSTANT
    assert analysis.columns[5].inferred.selected_type is SemanticType.EMPTY
    assert analysis.columns[6].inferred.selected_type is SemanticType.IDENTIFIER
    assert analysis.columns[7].inferred.selected_type is None
    assert summary.n_supported_pairs == 4
    assert summary.n_analyzed_pairs == 4
    flagged = [
        item
        for item in summary.relationships
        if isinstance(item, NumericBooleanRelationship)
    ]
    assert [(item.numeric_position, item.boolean_position) for item in flagged] == [
        (0, 3)
    ]
    categorical_pairs_only = [
        item
        for item in summary.relationships
        if isinstance(item, CategoricalCategoricalRelationship)
    ]
    assert len(categorical_pairs_only) == 1
    assert (
        categorical_pairs_only[0].left_position,
        categorical_pairs_only[0].right_position,
    ) == (
        1,
        2,
    )
    assert summary.unimplemented_family_counts == (
        UnimplementedFamilyCount(
            UnimplementedRelationshipFamily.CATEGORICAL_BOOLEAN, 2
        ),
    )
    assert "numeric_categorical" not in {
        item.family.value for item in summary.unimplemented_family_counts
    }
    assert (
        summary.n_supported_pairs
        + summary.n_unimplemented_family_pairs
        + summary.n_ineligible_pairs
        == summary.n_total_pairs
    )
    ordered = categorical_pairs[1]
    unordered = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4],
                "g": pd.Categorical(["a", "b", "a", "b"], categories=["a", "b"]),
            }
        )
    )
    assert ordered.effect.value == unordered.effect.value
    assert ordered.omnibus.statistic == unordered.omnibus.statistic


def test_labels_keep_physical_identity() -> None:
    frame = pd.concat(
        [
            pd.Series([1, 2, 3, 4], name="x"),
            pd.Series(pd.Categorical(["a", "b", "a", "b"]), name="x"),
        ],
        axis=1,
    )
    relationship = _relationship(frame)
    assert relationship.left_label == "x"
    assert relationship.right_label == "x"
    assert (relationship.left_position, relationship.right_position) == (0, 1)
    assert relationship.numeric_position == 0

    numbered = pd.DataFrame({1: [1, 2, 3, 4]})
    numbered[7] = pd.Categorical(["a", "b", "a", "b"])
    numbered = numbered.loc[:, [7, 1]]
    numbered_relationship = _relationship(numbered)
    assert numbered_relationship.left_label == 7
    assert numbered_relationship.right_label == 1
    assert numbered_relationship.categorical_position == 0
    assert numbered_relationship.numeric_position == 1

    nested = pd.DataFrame(
        {
            ("left", "y"): [1, 2, 3, 4],
            ("left", "g"): pd.Categorical(["a", "b", "a", "b"]),
        }
    )
    nested.columns = pd.MultiIndex.from_tuples([("left", "y"), ("left", "g")])
    nested_relationship = _relationship(nested)
    assert nested_relationship.left_label == ("left", "y")
    assert nested_relationship.right_label == ("left", "g")


def test_population_keeps_finite_numeric_and_observed_categories() -> None:
    frame = pd.DataFrame(
        {
            "y": [1.0, np.nan, np.inf, -np.inf, 5.0, 6.0, 7.0],
            "g": pd.Categorical(
                ["a", "b", "a", "c", "a", None, "d"],
                categories=["a", "b", "c", "d", "unused"],
            ),
        }
    )
    relationship = _relationship(frame)
    assert relationship.n_total_rows == 7
    assert relationship.n_paired == 3
    assert relationship.n_excluded == 4
    assert [(group.category, group.n) for group in relationship.groups] == [
        ("a", 2),
        ("d", 1),
    ]
    assert "unused" not in [group.category for group in relationship.groups]
    assert "b" not in [group.category for group in relationship.groups]
    assert "c" not in [group.category for group in relationship.groups]

    disappeared = _relationship(
        pd.DataFrame(
            {
                "y": [1.0, 2.0, np.nan],
                "g": pd.Categorical(["a", "a", "b"], categories=["a", "b", "c"]),
            }
        )
    )
    assert disappeared.n_paired == 2
    assert [group.category for group in disappeared.groups] == ["a"]
    assert disappeared.effect.reason is UnavailabilityReason.INSUFFICIENT_GROUPS


def test_group_descriptions_reuse_numeric_definitions() -> None:
    values = [1, 2, 4, 8]
    relationship = _relationship(
        pd.DataFrame(
            {
                "y": values + [100],
                "g": pd.Categorical(["a", "a", "a", "a", "b"]),
            }
        )
    )
    expected = collect_numeric_descriptive_analysis(pd.Series(values, dtype="int64"))
    assert relationship.groups[0].descriptive == expected
    assert relationship.groups[0].n == 4
    assert relationship.groups[1].n == 1
    assert relationship.groups[1].descriptive.standard_deviation is None
    assert relationship.groups[1].descriptive.minimum == 100
    assert (
        relationship.groups[1].descriptive.minimum
        == relationship.groups[1].descriptive.maximum
        == relationship.groups[1].descriptive.mean
    )

    base = 2**60
    large = _relationship(
        pd.DataFrame(
            {
                "y": [base, base + 1, base + 10, base + 11],
                "g": pd.Categorical(["a", "a", "b", "b"]),
            }
        )
    )
    large_expected = collect_numeric_descriptive_analysis(
        pd.Series([base, base + 1], dtype="int64")
    )
    assert large.groups[0].descriptive == large_expected
    assert large.groups[0].descriptive.minimum == base
    assert type(large.groups[0].descriptive.minimum) is int
    assert large.groups[0].descriptive.standard_deviation == pytest.approx(
        math.sqrt(0.5)
    )
    assert large.groups[0].descriptive.standard_deviation != 0.0


def test_effect_matches_an_independent_sum_of_squares() -> None:
    groups = [np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0])]
    relationship = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4, 5, 6],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    expected = _hand_eta(groups)
    assert relationship.effect.method is GroupEffectMethod.ETA_SQUARED
    assert relationship.effect.value == pytest.approx(expected)
    assert relationship.effect.value == pytest.approx(13.5 / 17.5)
    assert 0.0 <= relationship.effect.value <= 1.0
    library = f_oneway(*groups)
    assert relationship.omnibus.method is OmnibusTestMethod.ONE_WAY_ANOVA
    assert relationship.omnibus.statistic == pytest.approx(float(library.statistic))
    assert relationship.omnibus.statistic == 13.5
    assert relationship.omnibus.frequentist.p_value == pytest.approx(
        float(library.pvalue)
    )
    assert relationship.omnibus.frequentist.adjustment is (
        MultipleTestingAdjustment.BENJAMINI_HOCHBERG
    )
    assert relationship.omnibus.frequentist.adjusted_p_value == (
        relationship.omnibus.frequentist.p_value
    )
    assert not hasattr(relationship, "is_significant")
    assert not hasattr(relationship.effect, "strength")

    equal_means = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 1, 2, 3],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    assert equal_means.effect.value == 0.0
    assert equal_means.omnibus.statistic == 0.0
    assert equal_means.omnibus.frequentist.p_value == pytest.approx(1.0)

    separated = _relationship(
        pd.DataFrame(
            {
                "y": [1, 1, 1, 4, 4, 4],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    assert separated.effect.value == 1.0


def test_two_groups_stay_on_the_omnibus_anova() -> None:
    relationship = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4, 6, 8],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    library = f_oneway([1, 2, 3], [4, 6, 8])
    assert relationship.n_groups == 2
    assert relationship.omnibus.method is OmnibusTestMethod.ONE_WAY_ANOVA
    assert relationship.omnibus.statistic == pytest.approx(float(library.statistic))
    assert relationship.effect.value == pytest.approx(
        _hand_eta([np.array([1, 2, 3]), np.array([4, 6, 8])])
    )
    source = inspect.getsource(numeric_categorical_module)
    assert "ttest" not in source
    assert "tukey" not in source.lower()
    assert "kruskal" not in source.lower()
    assert "levene" not in source.lower()
    assert "shapiro" not in source.lower()


def test_degenerate_effect_and_test_states_stay_explicit() -> None:
    empty = _relationship(
        pd.DataFrame(
            {
                "y": [np.nan, np.inf, -np.inf],
                "g": pd.Categorical(["a", "b", None]),
            }
        )
    )
    assert empty.n_paired == 0
    assert empty.groups == ()
    assert empty.effect.reason is UnavailabilityReason.INSUFFICIENT_PAIRED_OBSERVATIONS
    assert empty.effect.value is None

    one_group = _relationship(
        pd.DataFrame(
            {
                "y": [1.0, 2.0, 3.0, np.nan],
                "g": pd.Categorical(["a", "a", "a", "b"], categories=["a", "b", "c"]),
            }
        )
    )
    assert one_group.n_groups == 1
    assert one_group.groups[0].descriptive.standard_deviation == pytest.approx(1.0)
    assert one_group.effect.reason is UnavailabilityReason.INSUFFICIENT_GROUPS

    unequal = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4, 9],
                "g": pd.Categorical(["a", "b", "b", "b", "c"]),
            }
        )
    )
    assert unequal.groups[0].n == 1
    assert unequal.groups[0].descriptive.standard_deviation is None
    assert unequal.omnibus.statistic == pytest.approx(
        float(f_oneway([1], [2, 3, 4], [9]).statistic)
    )
    assert unequal.omnibus.frequentist.p_value == pytest.approx(
        float(f_oneway([1], [2, 3, 4], [9]).pvalue)
    )

    singletons = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 4],
                "g": pd.Categorical(["a", "b", "c"]),
            }
        )
    )
    assert singletons.effect.value == 1.0
    assert singletons.omnibus.statistic is None
    assert singletons.omnibus.statistic_reason is (
        UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    )
    assert singletons.omnibus.frequentist.availability is ResultAvailability.UNAVAILABLE
    assert singletons.omnibus.frequentist.p_value is None
    assert singletons.omnibus.frequentist.reason is (
        UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    )
    assert all(
        group.descriptive.standard_deviation is None for group in singletons.groups
    )

    constant_groups = _relationship(
        pd.DataFrame(
            {
                "y": [1, 1, 5, 5, 9, 9],
                "g": pd.Categorical(["a", "a", "b", "b", "c", "c"]),
            }
        )
    )
    assert constant_groups.effect.value == 1.0
    assert constant_groups.n_paired > constant_groups.n_groups
    assert constant_groups.omnibus.statistic is None
    assert constant_groups.omnibus.statistic_reason is (
        UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION
    )
    assert constant_groups.omnibus.frequentist.availability is (
        ResultAvailability.UNAVAILABLE
    )
    assert constant_groups.omnibus.frequentist.p_value is None
    assert constant_groups.omnibus.frequentist.reason is (
        UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION
    )

    zero_total = _relationship(
        pd.DataFrame(
            {
                "y": [5.0, 5.0, 5.0, 5.0, np.inf],
                "g": pd.Categorical(["a", "a", "b", "b", "a"]),
            }
        )
    )
    assert zero_total.n_groups == 2
    assert zero_total.effect.value is None
    assert zero_total.effect.reason is UnavailabilityReason.ZERO_TOTAL_VARIATION
    assert zero_total.omnibus.statistic_reason is (
        UnavailabilityReason.ZERO_TOTAL_VARIATION
    )
    assert zero_total.groups[0].descriptive.standard_deviation == 0.0


def test_large_integer_offsets_do_not_collapse_the_group_effect() -> None:
    base = 2**60
    relationship = _relationship(
        pd.DataFrame(
            {
                "y": [base, base + 1, base + 10, base + 11],
                "g": pd.Categorical(["a", "a", "b", "b"]),
            }
        )
    )
    centered = [np.array([0.0, 1.0]), np.array([10.0, 11.0])]
    assert relationship.effect.value == pytest.approx(_hand_eta(centered))
    assert relationship.effect.value == pytest.approx(100 / 101)
    assert relationship.omnibus.statistic == 200.0
    assert relationship.effect.value != 0.0
    collapsed = np.array([base, base + 1, base + 10, base + 11], dtype=np.float64)
    assert len(set(collapsed.tolist())) == 1

    span = 2**54 + 1
    imprecise = _relationship(
        pd.DataFrame(
            {
                "y": [0, 0, span, span],
                "g": pd.Categorical(["a", "a", "b", "b"]),
            }
        )
    )
    assert imprecise.effect.reason is UnavailabilityReason.PRECISION_COLLAPSED
    assert imprecise.effect.value is None
    assert imprecise.omnibus.statistic is None
    assert imprecise.groups[1].descriptive.minimum == span
    assert type(imprecise.groups[1].descriptive.minimum) is int


def test_extreme_floats_do_not_fail_dataset_analysis() -> None:
    relationship = _relationship(
        pd.DataFrame(
            {
                "y": [1e308, 1e308, -1e308, -1e308],
                "g": pd.Categorical(["a", "a", "b", "b"]),
            }
        )
    )
    assert relationship.effect.reason is UnavailabilityReason.NON_FINITE_RESULT
    assert relationship.effect.value is None
    assert relationship.groups[0].descriptive.minimum == 1e308
    assert relationship.omnibus.statistic is None

    scaled = _relationship(
        pd.DataFrame(
            {
                "y": [1e200, 1e200, 2e200, 2e200],
                "g": pd.Categorical(["a", "a", "b", "b"]),
            }
        )
    )
    assert scaled.effect.value == 1.0
    assert scaled.omnibus.statistic is None
    assert scaled.omnibus.statistic_reason is (
        UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION
    )
    assert scaled.omnibus.frequentist.p_value is None


def test_category_identity_and_vocabulary_order() -> None:
    relationship = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4],
                "g": pd.Categorical(
                    ["b", "a", "b", "c"],
                    categories=["c", "a", "b", "d"],
                ),
            }
        )
    )
    assert [group.category for group in relationship.groups] == ["c", "a", "b"]
    assert "d" not in [group.category for group in relationship.groups]

    ordered = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4],
                "g": pd.Categorical(
                    ["b", "a", "b", "c"],
                    categories=["c", "a", "b", "d"],
                    ordered=True,
                ),
            }
        )
    )
    assert [group.category for group in ordered.groups] == ["c", "a", "b"]
    assert ordered.omnibus.statistic == relationship.omnibus.statistic

    mixed = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3],
                "g": pd.Categorical(
                    ["1", 1, ("a", 1)],
                    categories=["1", 1, ("a", 1)],
                ),
            }
        )
    )
    assert [group.category for group in mixed.groups] == ["1", 1, ("a", 1)]
    assert [type(group.category) for group in mixed.groups] == [str, int, tuple]

    flags = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4],
                "g": pd.Categorical([True, False, True, False]),
            }
        )
    )
    assert [group.category for group in flags.groups] == [False, True]
    assert [type(group.category) for group in flags.groups] == [bool, bool]

    stamped = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4],
                "g": pd.Categorical(pd.to_datetime(["2020-01-02", "2020-01-01"] * 2)),
            }
        )
    )
    assert all(isinstance(group.category, pd.Timestamp) for group in stamped.groups)
    assert not isinstance(stamped.groups[0].category, pd.Index)


def test_high_cardinality_and_singletons_are_not_truncated() -> None:
    n_groups = 40
    labels = [f"g{index}" for index in range(n_groups)]
    frame = pd.DataFrame(
        {
            "y": np.arange(n_groups, dtype=np.int64),
            "g": pd.Categorical(labels, categories=labels),
        }
    )
    analysis = analyze_dataframe(frame)
    relationship = _relationship(frame)
    assert relationship.n_groups == n_groups
    assert [group.category for group in relationship.groups] == labels
    assert relationship.effect.value == 1.0
    assert analysis.columns[1].inferred.selected_type is SemanticType.CATEGORICAL
    assert relationship.omnibus.statistic_reason is (
        UnavailabilityReason.INSUFFICIENT_WITHIN_GROUP_DEGREES_OF_FREEDOM
    )


def test_mixed_frame_coverage_counts_each_pair_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    numeric = {
        "a": [1, 2, 3, 4],
        "b": [4, 3, 2, 1],
        "c": [1, 1, 2, 2],
    }
    only_numeric = (analyze_dataframe(pd.DataFrame(numeric))).relationship_analysis
    frame = pd.DataFrame(
        {
            **numeric,
            "g": pd.Categorical(["a", "b", "a", "b"]),
            "h": pd.Categorical(["b", "a", "b", "a"]),
            "flag": [True, False, True, False],
        }
    )
    numeric_reads: list[int] = []
    categorical_reads: list[int] = []
    original_numeric = collector_module._read_numeric_column
    original_categorical = collector_module._read_categorical_column

    def _spy_numeric(series: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        numeric_reads.append(1)
        return original_numeric(series)

    def _spy_categorical(
        series: pd.Series,
    ) -> tuple[np.ndarray, tuple[object, ...]]:
        categorical_reads.append(1)
        return original_categorical(series)

    monkeypatch.setattr(collector_module, "_read_numeric_column", _spy_numeric)
    monkeypatch.setattr(collector_module, "_read_categorical_column", _spy_categorical)
    summary = analyze_dataframe(frame).relationship_analysis
    assert summary.n_total_pairs == 15
    assert summary.n_supported_pairs == 13
    assert summary.n_analyzed_pairs == len(summary.relationships) == 13
    assert summary.n_unimplemented_family_pairs == 2
    assert summary.n_ineligible_pairs == 0
    assert (
        summary.n_supported_pairs
        + summary.n_unimplemented_family_pairs
        + summary.n_ineligible_pairs
        == summary.n_total_pairs
    )
    numeric_pairs = [
        item
        for item in summary.relationships
        if isinstance(item, NumericNumericRelationship)
    ]
    categorical_pairs = [
        item
        for item in summary.relationships
        if isinstance(item, NumericCategoricalRelationship)
    ]
    assert len(numeric_pairs) == 3
    assert len(categorical_pairs) == 6
    assert (
        sum(
            isinstance(item, CategoricalCategoricalRelationship)
            for item in summary.relationships
        )
        == 1
    )
    assert (
        sum(
            isinstance(item, NumericBooleanRelationship)
            for item in summary.relationships
        )
        == 3
    )
    assert numeric_pairs[0].methods == only_numeric.relationships[0].methods
    assert len(numeric_reads) == 3
    assert len(categorical_reads) == 2
    positions = [
        (item.left_position, item.right_position) for item in summary.relationships
    ]
    assert positions == sorted(positions)


def test_retained_numeric_categorical_record_holds_no_source() -> None:
    frame = pd.DataFrame(
        {
            "y": [1, 2, 3, 4, 5, 6],
            "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
        }
    )
    before = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    pd.testing.assert_frame_equal(frame, before)
    _assert_no_retained_source(analysis.relationship_analysis)


def test_source_frame_mutation_does_not_change_retained_groups() -> None:
    frame = pd.DataFrame(
        {
            "y": [1, 2, 3, 4],
            "g": pd.Categorical(["a", "b", "a", "b"]),
        }
    )
    analysis = analyze_dataframe(frame)
    retained = analysis.relationship_analysis.relationships[0]
    frame.iloc[0, 0] = 100
    frame["g"] = pd.Categorical(["b", "b", "b", "b"])
    assert retained.groups[0].category == "a"
    assert retained.groups[0].n == 2
    _assert_no_retained_source(retained)


def test_category_scalars_have_an_explicit_boundary() -> None:
    complex_relationship = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4],
                "g": pd.Categorical([1 + 2j, 3 + 4j, 1 + 2j, 3 + 4j]),
            }
        )
    )
    assert type(complex_relationship.groups[0].category) is complex
    assert complex_relationship.groups[0].category == 1 + 2j

    with pytest.raises(TypeError, match="cannot be retained"):
        numeric_categorical_module._retain_category(object())
    with pytest.raises(TypeError, match="container"):
        numeric_categorical_module._retain_category(np.array([1, 2]))
    with pytest.raises(TypeError, match="physical categorical"):
        numeric_categorical_module._read_categorical_column(pd.Series([1, 2, 3]))


def test_library_non_finite_p_value_does_not_erase_a_finite_f(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "y": [1, 2, 3, 4, 5, 6],
            "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
        }
    )

    def _nan(*args: object, **kwargs: object) -> tuple[float, float]:
        return 13.5, float("nan")

    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _nan)
    relationship = _relationship(frame)
    assert relationship.omnibus.statistic == 13.5
    assert relationship.omnibus.frequentist.reason is (
        UnavailabilityReason.NON_FINITE_RESULT
    )
    assert relationship.omnibus.frequentist.p_value is None

    def _raise(*args: object, **kwargs: object) -> None:
        raise ValueError("library rejected the samples")

    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _raise)
    raised = _relationship(frame)
    assert raised.omnibus.statistic == 13.5
    assert raised.omnibus.frequentist.p_value is None


def test_models_reject_inconsistent_numeric_categorical_records() -> None:
    relationship = _relationship(
        pd.DataFrame(
            {
                "y": [1, 1, 5, 5],
                "g": pd.Categorical(["a", "a", "b", "b"]),
            }
        )
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        relationship.n_paired = 0  # type: ignore[misc]
    with pytest.raises(ValueError, match="less than right_position"):
        dataclasses.replace(relationship, left_position=1, right_position=1)
    with pytest.raises(ValueError, match="roles must be"):
        dataclasses.replace(relationship, numeric_position=4)
    with pytest.raises(ValueError, match="group sizes"):
        dataclasses.replace(relationship, n_paired=3)
    with pytest.raises(ValueError, match="at least one paired"):
        CategoricalGroupSummary(
            category="a",
            descriptive=collect_numeric_descriptive_analysis(
                pd.Series([np.nan], dtype="float64")
            ),
        )
    with pytest.raises(TypeError, match="NumPy"):
        CategoricalGroupSummary(
            category=np.array([1]),
            descriptive=relationship.groups[0].descriptive,
        )
    zero_within = OmnibusAnovaResult(
        method=OmnibusTestMethod.ONE_WAY_ANOVA,
        statistic_availability=ResultAvailability.UNAVAILABLE,
        statistic=None,
        statistic_reason=UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
        frequentist=FrequentistEvidence(
            availability=ResultAvailability.UNAVAILABLE,
            p_value=None,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
        ),
    )
    singletons = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 4],
                "g": pd.Categorical(["a", "b", "c"]),
            }
        )
    )
    with pytest.raises(ValueError, match="degrees of freedom"):
        dataclasses.replace(singletons, omnibus=zero_within)
    with pytest.raises(ValueError, match="eta squared 1"):
        dataclasses.replace(
            relationship,
            effect=GroupEffectEstimate(
                method=GroupEffectMethod.ETA_SQUARED,
                availability=ResultAvailability.AVAILABLE,
                value=0.5,
                reason=None,
            ),
            omnibus=zero_within,
        )
    with pytest.raises(ValueError, match="no ANOVA p-value"):
        dataclasses.replace(
            relationship,
            omnibus=OmnibusAnovaResult(
                method=OmnibusTestMethod.ONE_WAY_ANOVA,
                statistic_availability=ResultAvailability.UNAVAILABLE,
                statistic=None,
                statistic_reason=UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
                frequentist=FrequentistEvidence(
                    availability=ResultAvailability.AVAILABLE,
                    p_value=0.0,
                    adjusted_p_value=None,
                    adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                    reason=None,
                ),
            ),
        )
    with pytest.raises(ValueError, match="F statistic's reason"):
        dataclasses.replace(
            relationship,
            omnibus=OmnibusAnovaResult(
                method=OmnibusTestMethod.ONE_WAY_ANOVA,
                statistic_availability=ResultAvailability.UNAVAILABLE,
                statistic=None,
                statistic_reason=UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
                frequentist=FrequentistEvidence(
                    availability=ResultAvailability.UNAVAILABLE,
                    p_value=None,
                    adjusted_p_value=None,
                    adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                    reason=UnavailabilityReason.NON_FINITE_RESULT,
                ),
            ),
        )
    with pytest.raises(ValueError, match="unavailable F statistic has no p-value"):
        dataclasses.replace(
            relationship,
            omnibus=OmnibusAnovaResult(
                method=OmnibusTestMethod.ONE_WAY_ANOVA,
                statistic_availability=ResultAvailability.UNAVAILABLE,
                statistic=None,
                statistic_reason=UnavailabilityReason.NON_FINITE_RESULT,
                frequentist=FrequentistEvidence(
                    availability=ResultAvailability.AVAILABLE,
                    p_value=0.2,
                    adjusted_p_value=None,
                    adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                    reason=None,
                ),
            ),
        )
    numeric = analyze_series(pd.Series([1, 2, 3, 4]), position=0, label="y")
    categorical = analyze_series(
        pd.Series(pd.Categorical(["a", "b", "a", "b"])),
        position=1,
        label="g",
    )
    swapped = dataclasses.replace(
        relationship,
        numeric_position=1,
        categorical_position=0,
    )
    with pytest.raises(ValueError, match="numeric role"):
        relationship_analysis_for_columns(
            (numeric, categorical),
            n_rows=4,
            relationships=(swapped,),
        )
    numeric_pair = analyze_series(pd.Series([1, 2, 3, 4]), position=1, label="z")
    with pytest.raises(TypeError, match="NumericNumericRelationship"):
        relationship_analysis_for_columns(
            (numeric, numeric_pair),
            n_rows=4,
            relationships=(dataclasses.replace(relationship, right_label="z"),),
        )
    numeric_numeric = (analyze_dataframe(pd.DataFrame({"y": [1, 2, 3, 4], "g": [2, 3, 4, 5]}))).relationship_analysis.relationships[0]
    with pytest.raises(TypeError, match="numeric-categorical pair"):
        relationship_analysis_for_columns(
            (numeric, categorical),
            n_rows=4,
            relationships=(numeric_numeric,),
        )
    with pytest.raises(ValueError, match="negative zero"):
        GroupEffectEstimate(
            method=GroupEffectMethod.ETA_SQUARED,
            availability=ResultAvailability.AVAILABLE,
            value=-0.0,
            reason=None,
        )
    with pytest.raises(TypeError, match="retained scalar"):
        CategoricalGroupSummary(
            category=["a"],
            descriptive=relationship.groups[0].descriptive,
        )


def test_retained_category_boundary_and_defensive_inputs() -> None:
    assert numeric_categorical_module._retain_category(np.int64(3)) == 3
    assert numeric_categorical_module._retain_category((np.int64(1), "a")) == (1, "a")
    assert numeric_categorical_module._retain_category(1.5) == 1.5
    assert numeric_categorical_module._retain_category(-0.0) == 0.0
    assert math.copysign(1.0, numeric_categorical_module._retain_category(-0.0)) > 0
    assert numeric_categorical_module._retain_category(b"ab") == b"ab"
    assert isinstance(
        numeric_categorical_module._retain_category(pd.Timedelta(days=1)),
        pd.Timedelta,
    )
    assert isinstance(
        numeric_categorical_module._retain_category(pd.Period("2020-01", freq="M")),
        pd.Period,
    )
    assert isinstance(
        numeric_categorical_module._retain_category(pd.Interval(0, 1)),
        pd.Interval,
    )
    with pytest.raises(TypeError, match="finite"):
        numeric_categorical_module._retain_category(float("nan"))
    with pytest.raises(TypeError, match="finite"):
        numeric_categorical_module._retain_category(complex(float("nan"), 1.0))
    with pytest.raises(TypeError, match="container"):
        numeric_categorical_module._retain_category(pd.Index([1, 2]))
    with pytest.raises(TypeError, match="pandas Series"):
        numeric_categorical_module._read_categorical_column([1, 2, 3])  # type: ignore[arg-type]


def _positions() -> dict[str, object]:
    return {
        "left_position": 0,
        "left_label": "y",
        "right_position": 1,
        "right_label": "g",
        "numeric_position": 0,
        "categorical_position": 1,
    }


def test_direct_inputs_cover_unavailable_images_and_p_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="one entry per row"):
        numeric_categorical_module.analyze(
            np.array([1.0, 2.0]),
            np.array([True, True]),
            np.array([0, 0]),
            ("a",),
            n_total_rows=3,
            **_positions(),
        )
    with pytest.raises(ValueError, match="outside the categorical vocabulary"):
        numeric_categorical_module.analyze(
            np.array([1.0, 2.0, 3.0, 4.0]),
            np.array([True, True, True, True]),
            np.array([0, 0, 5, 5]),
            ("a",),
            n_total_rows=4,
            **_positions(),
        )
    with pytest.raises(TypeError, match="integer or floating"):
        numeric_categorical_module.analyze(
            np.array([1, 2, 3, 4], dtype=object),
            np.array([True, True, True, True]),
            np.array([0, 0, 1, 1]),
            ("a", "b"),
            n_total_rows=4,
            **_positions(),
        )
    image, image_reason = numeric_categorical_module._working_image(
        np.array([1.0, np.inf])
    )
    assert image is None
    assert image_reason is UnavailabilityReason.NON_FINITE_RESULT
    shifted, shift_reason = numeric_categorical_module._shift(np.array([np.inf]))
    assert shifted is None
    assert shift_reason is UnavailabilityReason.NON_FINITE_RESULT
    scaled, scale_reason = numeric_categorical_module._scale(np.array([np.inf]))
    assert scaled is None
    assert scale_reason is UnavailabilityReason.NON_FINITE_RESULT

    def _tuple_result(*args: object, **kwargs: object) -> tuple[float, float]:
        return (13.5, 0.25)

    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _tuple_result)
    tuple_result = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4, 5, 6],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    assert tuple_result.omnibus.frequentist.p_value == 0.25

    def _bool_result(*args: object, **kwargs: object) -> object:
        return type("Result", (), {"pvalue": True})()

    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _bool_result)
    bool_result = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4, 5, 6],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    assert bool_result.omnibus.frequentist.p_value is None

    def _high_result(*args: object, **kwargs: object) -> object:
        return type("Result", (), {"pvalue": 1.0 + 1e-12})()

    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _high_result)
    high_result = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4, 5, 6],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    assert high_result.omnibus.frequentist.p_value == 1.0

    def _junk_result(*args: object, **kwargs: object) -> object:
        return object()

    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _junk_result)
    junk_result = _relationship(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4, 5, 6],
                "g": pd.Categorical(["a", "a", "a", "b", "b", "b"]),
            }
        )
    )
    assert junk_result.omnibus.frequentist.p_value is None
    assert numeric_categorical_module._eta_squared(1.0, 1.0 - 1e-12) == 1.0
    assert numeric_categorical_module._eta_squared(-1e-12, 1.0) == 0.0
    assert numeric_categorical_module._bounds(np.array([], dtype=int))[0].size == 0
    shifted, reason = numeric_categorical_module._shift(np.array([], dtype=float))
    assert reason is None
    assert shifted.size == 0
    scaled, scale_reason = numeric_categorical_module._scale(np.array([0.0, 0.0]))
    assert scale_reason is None
    assert scaled.tolist() == [0.0, 0.0]
    empty_image, empty_reason = numeric_categorical_module._working_image(
        np.array([], dtype=np.int64)
    )
    assert empty_reason is None
    assert empty_image.size == 0
    assert numeric_categorical_module._as_p_value(np.array([0.2])) is None
    assert numeric_categorical_module._as_p_value("no") is None
    assert numeric_categorical_module._as_p_value(float("nan")) is None
    assert numeric_categorical_module._as_p_value(-1e-12) == 0.0
    assert numeric_categorical_module._as_p_value(-0.2) is None
    assert numeric_categorical_module._as_p_value(1.5) is None
    assert numeric_categorical_module._as_p_value(0.2) == 0.2
    assert numeric_categorical_module._eta_squared(float("nan"), 1.0) is None
    assert numeric_categorical_module._eta_squared(-1.0, 1.0) is None
    assert numeric_categorical_module._eta_squared(2.0, 1.0) is None


def test_effect_estimate_rejects_a_strength_label() -> None:
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        GroupEffectEstimate(
            method=GroupEffectMethod.ETA_SQUARED,
            availability=ResultAvailability.AVAILABLE,
            value=1.5,
            reason=None,
        )
    unavailable = GroupEffectEstimate(
        method=GroupEffectMethod.ETA_SQUARED,
        availability=ResultAvailability.UNAVAILABLE,
        value=None,
        reason=UnavailabilityReason.ZERO_TOTAL_VARIATION,
    )
    assert unavailable.value is None
    assert not hasattr(unavailable, "is_significant")
