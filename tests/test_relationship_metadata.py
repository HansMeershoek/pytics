"""TSK-027: heterogeneous relationship metadata ownership."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import f as f_distribution
from scipy.stats import pearsonr
from scipy.stats import spearmanr

import pytics.analysis.column as column_module
import pytics.analysis.dataset as dataset_module
import pytics.analysis.relationships.boolean_boolean as boolean_boolean_module
import pytics.analysis.relationships.collector as collector_module
import pytics.analysis.relationships.numeric_boolean as numeric_boolean_module
import pytics.analysis.relationships.numeric_categorical as numeric_categorical_module
import pytics.analysis.relationships.numeric_numeric as numeric_numeric_module
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationship import AssociationMethod
from pytics.analysis.relationship import BooleanBooleanPopulation
from pytics.analysis.relationship import BooleanBooleanRelationship
from pytics.analysis.relationship import CorrelationEstimate
from pytics.analysis.relationship import CorrelationInterval
from pytics.analysis.relationship import CorrelationIntervalMethod
from pytics.analysis.relationship import EffectDirection
from pytics.analysis.relationship import FrequentistEvidence
from pytics.analysis.relationship import GroupEffectEstimate
from pytics.analysis.relationship import GroupEffectMethod
from pytics.analysis.relationship import MultipleTestingAdjustment
from pytics.analysis.relationship import NumericBooleanPopulation
from pytics.analysis.relationship import NumericBooleanRelationship
from pytics.analysis.relationship import NumericCategoricalPopulation
from pytics.analysis.relationship import NumericCategoricalRelationship
from pytics.analysis.relationship import NumericComputation
from pytics.analysis.relationship import NumericNumericRelationship
from pytics.analysis.relationship import OmnibusAnovaResult
from pytics.analysis.relationship import OmnibusTestMethod
from pytics.analysis.relationship import PairPopulation
from pytics.analysis.relationship import RelationshipAnalysis
from pytics.analysis.relationship import RelationshipFamily
from pytics.analysis.relationship import RelationshipsSummary
from pytics.analysis.relationship import ResultAvailability
from pytics.analysis.relationship import UnavailabilityReason
from pytics.analysis.relationship import UnimplementedRelationshipFamily
from pytics.analysis.relationship import build_relationships_summary
from pytics.semantics.interpretation import SemanticType

_RETAINED = (pd.DataFrame, pd.Series, pd.Index, np.ndarray)
_DATASET_FIELDS = (
    "n_rows",
    "n_total_pairs",
    "n_supported_pairs",
    "n_analyzed_pairs",
    "n_unimplemented_family_pairs",
    "n_ineligible_pairs",
    "unimplemented_family_counts",
    "relationships",
)
_SUMMARY_FIELDS = ("n_rows", "n_columns", *_DATASET_FIELDS[1:])
_ABSENT_DATASET_CLAIMS = (
    "primary_method",
    "population",
    "computation",
    "confidence_level",
    "multiple_testing",
    "implemented_families",
)
_UUIDS = (
    "550e8400-e29b-41d4-a716-446655440000",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b814-9dad-11d1-80b4-00c04fd430c8",
    "6ba7b815-9dad-11d1-80b4-00c04fd430c8",
)


def _mixed_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5, 6],
            "y": [2, 1, 4, 3, 6, 5],
            "group": pd.Categorical(["a", "a", "b", "b", "c", "c"]),
            "flag": [True, False, True, False, True, False],
            "code": pd.Series(_UUIDS, dtype="string"),
        }
    )


def _assert_no_dataset_claims(value: object) -> None:
    for name in _ABSENT_DATASET_CLAIMS:
        assert not hasattr(value, name)


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


def _eta_squared(values: list[float], groups: list[str]) -> tuple[float, float]:
    """Independent eta squared and classical F from group means."""
    buckets: dict[str, list[float]] = {}
    for value, group in zip(values, groups):
        buckets.setdefault(group, []).append(value)
    observations = [value for bucket in buckets.values() for value in bucket]
    grand = sum(observations) / len(observations)
    ss_within = 0.0
    ss_between = 0.0
    for bucket in buckets.values():
        mean = sum(bucket) / len(bucket)
        ss_within += sum((value - mean) ** 2 for value in bucket)
        ss_between += len(bucket) * (mean - grand) ** 2
    ss_total = ss_within + ss_between
    df_between = len(buckets) - 1
    df_within = len(observations) - len(buckets)
    statistic = (ss_between / df_between) / (ss_within / df_within)
    return ss_between / ss_total, statistic


def test_dataset_container_keeps_coverage_and_not_one_method() -> None:
    analysis = analyze_dataframe(_mixed_frame())
    retained = analysis.relationship_analysis
    summary = build_relationships_summary(analysis)
    assert [field.name for field in dataclasses.fields(RelationshipAnalysis)] == list(
        _DATASET_FIELDS
    )
    assert [field.name for field in dataclasses.fields(RelationshipsSummary)] == list(
        _SUMMARY_FIELDS
    )
    assert [field.name for field in dataclasses.fields(DatasetAnalysis)] == [
        "n_rows",
        "n_columns",
        "n_cells",
        "columns",
        "missing_analysis",
        "duplicate_analysis",
        "relationship_analysis",
    ]
    _assert_no_dataset_claims(retained)
    _assert_no_dataset_claims(summary)
    assert tuple(RelationshipFamily) == (
        RelationshipFamily.NUMERIC_NUMERIC,
        RelationshipFamily.NUMERIC_CATEGORICAL,
        RelationshipFamily.BOOLEAN_BOOLEAN,
        RelationshipFamily.NUMERIC_BOOLEAN,
        RelationshipFamily.CATEGORICAL_CATEGORICAL,
    )
    assert (
        retained.n_supported_pairs
        + retained.n_unimplemented_family_pairs
        + retained.n_ineligible_pairs
        == retained.n_total_pairs
    )
    assert retained.n_analyzed_pairs == len(retained.relationships)
    assert retained.n_analyzed_pairs == retained.n_supported_pairs


def test_mixed_dataset_records_are_self_describing() -> None:
    frame = _mixed_frame()
    analysis = analyze_dataframe(frame)
    summary = build_relationships_summary(analysis)
    assert [column.inferred.selected_type for column in analysis.columns] == [
        SemanticType.NUMERIC,
        SemanticType.NUMERIC,
        SemanticType.CATEGORICAL,
        SemanticType.BOOLEAN,
        SemanticType.IDENTIFIER,
    ]
    assert summary.n_total_pairs == 10
    assert summary.n_supported_pairs == 5
    assert summary.n_analyzed_pairs == 5
    assert summary.n_unimplemented_family_pairs == 0
    assert summary.n_ineligible_pairs == 5
    assert summary.unimplemented_family_counts == ()
    numeric, left_group, left_flag, right_group, right_flag = summary.relationships
    assert isinstance(numeric, NumericNumericRelationship)
    assert isinstance(left_group, NumericCategoricalRelationship)
    assert isinstance(right_group, NumericCategoricalRelationship)
    for flagged, numeric_position in ((left_flag, 0), (right_flag, 1)):
        assert isinstance(flagged, NumericBooleanRelationship)
        assert flagged.family is RelationshipFamily.NUMERIC_BOOLEAN
        assert flagged.population is (
            NumericBooleanPopulation.FINITE_NUMERIC_NON_MISSING_BOOLEAN
        )
        assert (flagged.numeric_position, flagged.boolean_position) == (
            numeric_position,
            3,
        )
        assert flagged.mean_difference_interval.level == 0.95
        assert not hasattr(flagged, "primary_method")
        assert not hasattr(flagged, "computation")
        assert not hasattr(flagged, "confidence_level")
    assert (numeric.left_position, numeric.right_position) == (0, 1)
    assert numeric.family is RelationshipFamily.NUMERIC_NUMERIC
    assert numeric.population is PairPopulation.PAIRWISE_FINITE
    assert numeric.computation is NumericComputation.FLOAT64
    assert numeric.n_total_rows == 6
    assert numeric.n_paired == 6
    assert numeric.n_excluded == 0
    assert numeric.spearman.method is AssociationMethod.SPEARMAN
    assert numeric.pearson.method is AssociationMethod.PEARSON
    assert not hasattr(numeric, "primary_method")
    assert not hasattr(left_group, "confidence_level")
    assert not hasattr(left_group, "confidence_interval")
    assert not hasattr(left_group, "computation")
    assert not hasattr(left_group, "primary_method")
    assert left_group.family is RelationshipFamily.NUMERIC_CATEGORICAL
    assert left_group.population is (
        NumericCategoricalPopulation.FINITE_NUMERIC_OBSERVED_CATEGORY
    )
    assert (left_group.numeric_position, left_group.categorical_position) == (0, 2)
    assert (right_group.numeric_position, right_group.categorical_position) == (1, 2)
    assert left_group.effect.method is GroupEffectMethod.ETA_SQUARED
    assert left_group.omnibus.method is OmnibusTestMethod.ONE_WAY_ANOVA
    assert [group.category for group in left_group.groups] == ["a", "b", "c"]
    repeated = analyze_dataframe(frame).relationship_analysis
    assert repeated == analysis.relationship_analysis
    positions = [
        (item.left_position, item.right_position) for item in summary.relationships
    ]
    assert positions == sorted(positions)


def test_numeric_numeric_statistics_stay_on_the_pair() -> None:
    relationship = build_relationships_summary(
        analyze_dataframe(_mixed_frame())
    ).relationships[0]
    assert isinstance(relationship, NumericNumericRelationship)
    x = [1, 2, 3, 4, 5, 6]
    y = [2, 1, 4, 3, 6, 5]
    spearman = spearmanr(x, y)
    pearson = pearsonr(x, y)
    assert relationship.spearman.estimate.value == pytest.approx(spearman.correlation)
    assert relationship.spearman.frequentist.p_value == pytest.approx(spearman.pvalue)
    assert relationship.pearson.estimate.value == pytest.approx(pearson.correlation)
    assert relationship.pearson.frequentist.p_value == pytest.approx(pearson.pvalue)
    assert relationship.spearman.frequentist.adjustment is (
        MultipleTestingAdjustment.NOT_APPLIED
    )
    assert relationship.spearman.frequentist.adjusted_p_value is None
    assert relationship.pearson.frequentist.adjusted_p_value is None
    interval = relationship.pearson.confidence_interval
    assert interval.availability is ResultAvailability.AVAILABLE
    assert interval.level == 0.95
    assert interval.method is CorrelationIntervalMethod.FISHER_Z
    assert relationship.spearman.confidence_interval.availability is (
        ResultAvailability.UNAVAILABLE
    )
    assert relationship.spearman.confidence_interval.level is None
    assert relationship.spearman.confidence_interval.reason is (
        UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD
    )
    transformed = math.atanh(relationship.pearson.estimate.value)
    half_width = 1.959963984540054 / math.sqrt(relationship.n_paired - 3)
    assert interval.lower == pytest.approx(math.tanh(transformed - half_width))
    assert interval.upper == pytest.approx(math.tanh(transformed + half_width))


def test_numeric_categorical_statistics_stay_on_the_pair() -> None:
    summary = build_relationships_summary(analyze_dataframe(_mixed_frame()))
    pair = summary.relationships[1]
    assert isinstance(pair, NumericCategoricalRelationship)
    eta, statistic = _eta_squared(
        [1, 2, 3, 4, 5, 6],
        ["a", "a", "b", "b", "c", "c"],
    )
    assert pair.effect.value == pytest.approx(eta)
    assert pair.omnibus.statistic == pytest.approx(statistic)
    assert pair.omnibus.frequentist.p_value == pytest.approx(
        float(f_distribution.sf(statistic, 2, 3))
    )
    assert pair.omnibus.frequentist.adjustment is MultipleTestingAdjustment.NOT_APPLIED
    assert pair.omnibus.frequentist.adjusted_p_value is None
    assert pair.groups[0].descriptive.mean == pytest.approx(1.5)
    assert pair.groups[1].n == 2

    degenerate = build_relationships_summary(
        analyze_dataframe(
            pd.DataFrame(
                {
                    "y": [1, 1, 2, 2],
                    "g": pd.Categorical(["a", "a", "b", "b"]),
                }
            )
        )
    ).relationships[0]
    assert isinstance(degenerate, NumericCategoricalRelationship)
    assert degenerate.effect.value == 1.0
    assert degenerate.omnibus.statistic is None
    assert degenerate.omnibus.statistic_reason is (
        UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION
    )
    assert degenerate.omnibus.frequentist.availability is ResultAvailability.UNAVAILABLE
    assert degenerate.omnibus.frequentist.p_value is None
    assert degenerate.omnibus.frequentist.reason is (
        UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION
    )


def test_population_rules_stay_on_the_family_record() -> None:
    frame = pd.DataFrame(
        {
            "x": [1.0, 2.0, np.nan, 4.0, 5.0],
            "y": [1.0, np.inf, 3.0, 4.0, 5.0],
            "g": pd.Categorical(["a", "b", "a", None, "b"]),
        }
    )
    numeric, by_x, by_y = build_relationships_summary(
        analyze_dataframe(frame)
    ).relationships
    assert isinstance(numeric, NumericNumericRelationship)
    assert isinstance(by_x, NumericCategoricalRelationship)
    assert isinstance(by_y, NumericCategoricalRelationship)
    assert numeric.population is PairPopulation.PAIRWISE_FINITE
    assert numeric.n_paired == 3
    assert numeric.n_excluded == 2
    assert by_x.population is (
        NumericCategoricalPopulation.FINITE_NUMERIC_OBSERVED_CATEGORY
    )
    assert by_y.population is by_x.population
    assert by_x.n_paired == 3
    assert by_x.n_excluded == 2
    assert by_y.n_paired == 3
    assert [group.category for group in by_x.groups] == ["a", "b"]
    assert [group.n for group in by_x.groups] == [1, 2]
    assert by_x.population is not numeric.population


def test_version_capability_is_not_a_dataset_field() -> None:
    flags = pd.DataFrame(
        {
            "left": [True, False, True, False],
            "right": [False, True, False, True],
        }
    )
    retained = analyze_dataframe(flags).relationship_analysis
    assert len(retained.relationships) == 1
    assert retained.n_analyzed_pairs == 1
    assert retained.n_supported_pairs == 1
    assert retained.n_unimplemented_family_pairs == 0
    relationship = retained.relationships[0]
    assert isinstance(relationship, BooleanBooleanRelationship)
    assert relationship.family is RelationshipFamily.BOOLEAN_BOOLEAN
    assert relationship.population is (
        BooleanBooleanPopulation.PAIRWISE_NON_MISSING_BOOLEAN
    )
    _assert_no_dataset_claims(retained)
    assert RelationshipFamily.BOOLEAN_BOOLEAN in RelationshipFamily
    assert "boolean_boolean" not in {
        family.value for family in UnimplementedRelationshipFamily
    }


def test_summary_copies_records_without_source_or_recalculation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = analyze_dataframe(_mixed_frame())

    def _fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("summary builder used a source-dependent operation")

    monkeypatch.setattr(collector_module, "_read_numeric_column", _fail)
    monkeypatch.setattr(collector_module, "_read_categorical_column", _fail)
    monkeypatch.setattr(collector_module, "_read_boolean_column", _fail)
    monkeypatch.setattr(collector_module, "_association_methods", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_categorical", _fail)
    monkeypatch.setattr(collector_module, "_analyze_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_numeric_boolean", _fail)
    monkeypatch.setattr(collector_module, "_analyze_categorical_categorical", _fail)
    monkeypatch.setattr(boolean_boolean_module, "fisher_exact", _fail)
    monkeypatch.setattr(numeric_boolean_module, "student_t", _fail)
    monkeypatch.setattr(collector_module, "collect_relationship_analysis", _fail)
    monkeypatch.setattr(numeric_numeric_module, "spearmanr", _fail)
    monkeypatch.setattr(numeric_numeric_module, "pearsonr", _fail)
    monkeypatch.setattr(numeric_numeric_module, "norm", _fail)
    monkeypatch.setattr(numeric_categorical_module, "f_oneway", _fail)
    monkeypatch.setattr(column_module, "analyze_series", _fail)
    monkeypatch.setattr(column_module, "resolve_semantics", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    summary = build_relationships_summary(analysis)
    assert summary == RelationshipsSummary(
        n_rows=analysis.n_rows,
        n_columns=analysis.n_columns,
        n_total_pairs=analysis.relationship_analysis.n_total_pairs,
        n_supported_pairs=analysis.relationship_analysis.n_supported_pairs,
        n_analyzed_pairs=analysis.relationship_analysis.n_analyzed_pairs,
        n_unimplemented_family_pairs=(
            analysis.relationship_analysis.n_unimplemented_family_pairs
        ),
        n_ineligible_pairs=analysis.relationship_analysis.n_ineligible_pairs,
        unimplemented_family_counts=(
            analysis.relationship_analysis.unimplemented_family_counts
        ),
        relationships=summary.relationships,
    )
    retained_relationships = analysis.relationship_analysis.relationships
    assert summary.relationships[0] == retained_relationships[0]
    assert summary.relationships[0] is not retained_relationships[0]
    assert summary.relationships[1] is not retained_relationships[1]
    _assert_no_dataset_claims(summary)
    _assert_no_retained_source(summary)
    _assert_no_retained_source(analysis.relationship_analysis)


def test_components_reject_another_familys_reason() -> None:
    with pytest.raises(ValueError, match="not a reason for this component"):
        CorrelationEstimate(
            availability=ResultAvailability.UNAVAILABLE,
            value=None,
            direction=None,
            reason=UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
        )
    with pytest.raises(ValueError, match="not an ANOVA reason"):
        OmnibusAnovaResult(
            method=OmnibusTestMethod.ONE_WAY_ANOVA,
            statistic_availability=ResultAvailability.UNAVAILABLE,
            statistic=None,
            statistic_reason=UnavailabilityReason.INSUFFICIENT_GROUPS,
            frequentist=FrequentistEvidence(
                availability=ResultAvailability.UNAVAILABLE,
                p_value=None,
                adjusted_p_value=None,
                adjustment=MultipleTestingAdjustment.NOT_APPLIED,
                reason=UnavailabilityReason.BOUNDARY_CORRELATION,
            ),
        )
    with pytest.raises(ValueError, match="not a reason for this component"):
        GroupEffectEstimate(
            method=GroupEffectMethod.ETA_SQUARED,
            availability=ResultAvailability.UNAVAILABLE,
            value=None,
            reason=UnavailabilityReason.BOUNDARY_CORRELATION,
        )
    with pytest.raises(ValueError, match="p_value must lie on"):
        FrequentistEvidence(
            availability=ResultAvailability.AVAILABLE,
            p_value=1.5,
            adjusted_p_value=None,
            adjustment=MultipleTestingAdjustment.NOT_APPLIED,
            reason=None,
        )
    estimate = CorrelationEstimate(
        availability=ResultAvailability.AVAILABLE,
        value=0.5,
        direction=EffectDirection.POSITIVE,
        reason=None,
    )
    interval = CorrelationInterval(
        availability=ResultAvailability.UNAVAILABLE,
        level=None,
        method=None,
        lower=None,
        upper=None,
        reason=UnavailabilityReason.INTERVAL_NOT_DEFINED_FOR_METHOD,
    )
    wrong_test = FrequentistEvidence(
        availability=ResultAvailability.UNAVAILABLE,
        p_value=None,
        adjusted_p_value=None,
        adjustment=MultipleTestingAdjustment.NOT_APPLIED,
        reason=UnavailabilityReason.ZERO_WITHIN_GROUP_VARIATION,
    )
    with pytest.raises(ValueError, match="correlation-test reason"):
        from pytics.analysis.relationship import AssociationResult

        AssociationResult(
            method=AssociationMethod.SPEARMAN,
            n_observations=4,
            estimate=estimate,
            frequentist=wrong_test,
            confidence_interval=interval,
        )

    analysis = analyze_dataframe(
        pd.DataFrame(
            {
                "y": [1, 2, 3, 4],
                "g": pd.Categorical(["a", "a", "b", "b"]),
            }
        )
    )
    pair = analysis.relationship_analysis.relationships[0]
    assert isinstance(pair, NumericCategoricalRelationship)
    with pytest.raises(ValueError, match="roles must be the two physical"):
        NumericCategoricalRelationship(
            left_position=pair.left_position,
            left_label=pair.left_label,
            right_position=pair.right_position,
            right_label=pair.right_label,
            numeric_position=pair.left_position,
            categorical_position=pair.left_position,
            n_total_rows=pair.n_total_rows,
            n_paired=pair.n_paired,
            groups=pair.groups,
            effect=pair.effect,
            omnibus=pair.omnibus,
        )
    with pytest.raises(ValueError, match="less than right_position"):
        NumericNumericRelationship(
            left_position=2,
            left_label="b",
            right_position=1,
            right_label="a",
            n_total_rows=4,
            n_paired=4,
            methods=build_relationships_summary(
                analyze_dataframe(pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 3, 2, 5]}))
            )
            .relationships[0]
            .methods,  # type: ignore[attr-defined]
        )
