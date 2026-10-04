"""TSK-036: univariate numeric anomaly evidence."""

from __future__ import annotations

import ast
import dataclasses
import math
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.analysis.anomaly as anomaly_module
import pytics.analysis.dataset as dataset_module
from pytics.analysis.anomaly import AnomalyAnalysis
from pytics.analysis.anomaly import AnomalyIneligibleCount
from pytics.analysis.anomaly import AnomalyUnavailableCount
from pytics.analysis.anomaly import AnomalyCoverage
from pytics.analysis.anomaly import AnomalyDirection
from pytics.analysis.anomaly import AnomalyIneligibility
from pytics.analysis.anomaly import AnomalySummary
from pytics.analysis.anomaly import NumericAnomalyColumn
from pytics.analysis.anomaly import NumericAnomalyMethod
from pytics.analysis.anomaly import NumericAnomalyObservation
from pytics.analysis.anomaly import NumericAnomalyStatus
from pytics.analysis.anomaly import anomaly_analysis_for_columns
from pytics.analysis.anomaly import build_anomaly_summary
from pytics.analysis.anomaly import collect_anomaly_analysis
from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.column import ColumnEvidence
from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.dataset import analyze_dataframe
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.resolution import SemanticResolution

_UUID_A = "550e8400-e29b-41d4-a716-446655440000"
_UUID_B = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
_UUID_C = "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
_FORBIDDEN = (pd.DataFrame, pd.Series, pd.Index, np.ndarray, np.generic)
_COEFFICIENT = Fraction(3, 2)


def _analysis(frame: pd.DataFrame, **kwargs: object):
    return analyze_dataframe(frame, **kwargs)


def _numeric(frame: pd.DataFrame, label: object = None):
    analysis = _analysis(frame)
    records = analysis.anomaly_analysis.numeric_univariate
    if label is None:
        assert len(records) == 1
        return analysis, records[0]
    match = [record for record in records if record.label == label]
    assert len(match) == 1
    return analysis, match[0]


def _assert_no_source(value: object, seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if id(value) in seen:
        return
    seen.add(id(value))
    assert not isinstance(value, _FORBIDDEN)
    assert not callable(value)
    if dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            _assert_no_source(getattr(value, field.name), seen)
    elif isinstance(value, tuple):
        for item in value:
            _assert_no_source(item, seen)


def _type7(values: list[int], numerator: int, denominator: int) -> Fraction:
    """Hyndman-Fan type 7 quantile, independent of the production collector."""
    ordered = sorted(values)
    scaled = (len(ordered) - 1) * numerator
    lower = scaled // denominator
    remainder = scaled % denominator
    left = ordered[lower]
    if remainder == 0:
        return Fraction(left)
    right = ordered[lower + 1]
    return Fraction(left * denominator + (right - left) * remainder, denominator)


def _expected_fences(q1: object, q3: object, iqr: object):
    if any(type(value) is float for value in (q1, q3, iqr)):
        lower = float(q1) - 1.5 * float(iqr)  # type: ignore[arg-type]
        upper = float(q3) + 1.5 * float(iqr)  # type: ignore[arg-type]
        return lower, upper
    lower = Fraction(q1) - _COEFFICIENT * Fraction(iqr)  # type: ignore[arg-type]
    upper = Fraction(q3) + _COEFFICIENT * Fraction(iqr)  # type: ignore[arg-type]
    return lower, upper


def _exact_value(value: object) -> Fraction | None:
    if isinstance(value, np.generic):
        value = value.item()
    if (
        value is None
        or value is pd.NA
        or (isinstance(value, float) and not math.isfinite(value))
    ):
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(value)
    return None


def _finite_rows(values: list[object]) -> list[tuple[int, Fraction]]:
    rows = []
    for position, value in enumerate(values):
        exact = _exact_value(value)
        if exact is None:
            continue
        rows.append((position, exact))
    return rows


def _assert_matches_retained_profile(frame: pd.DataFrame, label: object) -> None:
    """Check fences and positions against retained quartiles, not a second collector."""
    analysis, record = _numeric(frame, label)
    column = next(item for item in analysis.columns if item.label == label)
    descriptive = column.numeric_analysis
    assert descriptive is not None
    assert record.q1 == descriptive.q1
    assert record.q3 == descriptive.q3
    assert record.iqr == descriptive.interquartile_range
    assert record.finite_count == descriptive.finite_count
    if record.status is not NumericAnomalyStatus.AVAILABLE:
        assert record.observations == ()
        assert record.below_count is None
        assert record.above_count is None
        assert record.method is None
        return
    assert descriptive.q1 is not None
    assert descriptive.q3 is not None
    assert descriptive.interquartile_range is not None
    lower, upper = _expected_fences(
        descriptive.q1,
        descriptive.q3,
        descriptive.interquartile_range,
    )
    if isinstance(lower, float):
        assert record.lower_fence == (0.0 if lower == 0.0 else lower)
        assert record.upper_fence == (0.0 if upper == 0.0 else upper)
    else:
        assert Fraction(record.lower_fence) == lower  # type: ignore[arg-type]
        assert Fraction(record.upper_fence) == upper  # type: ignore[arg-type]
    assert record.fence_coefficient == _COEFFICIENT
    assert type(record.fence_coefficient) is Fraction
    assert record.method is NumericAnomalyMethod.TUKEY_IQR
    observed = _finite_rows(frame[label].tolist())
    below = [position for position, value in observed if value < lower]
    above = [position for position, value in observed if value > upper]
    assert [
        item.row_position
        for item in record.observations
        if item.direction is AnomalyDirection.BELOW
    ] == below
    assert [
        item.row_position
        for item in record.observations
        if item.direction is AnomalyDirection.ABOVE
    ] == above
    assert record.below_count == len(below)
    assert record.above_count == len(above)
    assert [item.row_position for item in record.observations] == sorted(
        item.row_position for item in record.observations
    )


def test_compact_numeric_values_are_inside_the_fences() -> None:
    frame = pd.DataFrame({"amount": [-1, 2, 3, 4, 7]})
    analysis, record = _numeric(frame, "amount")
    assert record.status is NumericAnomalyStatus.AVAILABLE
    assert record.lower_fence == -1
    assert record.upper_fence == 7
    assert record.below_count == 0
    assert record.above_count == 0
    assert record.observations == ()
    assert analysis.anomaly_analysis.coverage.n_analyzed == 1
    _assert_matches_retained_profile(frame, "amount")


def test_low_and_high_values_keep_direction_and_physical_position() -> None:
    frame = pd.DataFrame({"amount": [-2, 2, 3, 4, 8]})
    _assert_matches_retained_profile(frame, "amount")
    _, record = _numeric(frame, "amount")
    assert [
        (item.row_position, item.value, item.direction) for item in record.observations
    ] == [
        (0, -2, AnomalyDirection.BELOW),
        (4, 8, AnomalyDirection.ABOVE),
    ]
    assert record.below_count == 1
    assert record.above_count == 1


def test_repeated_anomalous_values_stay_distinct_rows() -> None:
    frame = pd.DataFrame({"amount": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1000, 1000]})
    _assert_matches_retained_profile(frame, "amount")
    _, record = _numeric(frame, "amount")
    high = [
        item for item in record.observations if item.direction is AnomalyDirection.ABOVE
    ]
    assert [item.row_position for item in high] == [10, 11]
    assert [item.value for item in high] == [1000, 1000]


def test_duplicate_nonmonotonic_index_labels_are_not_row_identity() -> None:
    frame = pd.DataFrame(
        {"amount": [-2, 2, 3, 4, 8]},
        index=[7, 7, 0, 3, 7],
    )
    _assert_matches_retained_profile(frame, "amount")
    _, record = _numeric(frame, "amount")
    assert [item.row_position for item in record.observations] == [0, 4]
    assert 7 not in [item.row_position for item in record.observations]
    assert frame.index.tolist() == [7, 7, 0, 3, 7]


def test_missing_values_are_counted_and_not_anomalies() -> None:
    frame = pd.DataFrame({"amount": [-2, 2, None, 4, 8]})
    analysis, record = _numeric(frame, "amount")
    _assert_matches_retained_profile(frame, "amount")
    assert record.n_missing == 1
    assert 2 not in [item.row_position for item in record.observations]
    assert analysis.columns[0].evidence.basic.n_missing == record.n_missing


def test_infinities_are_not_iqr_observations() -> None:
    frame = pd.DataFrame(
        {"amount": [1.0, 2.0, 3.0, 4.0, 100.0, np.inf, -np.inf, np.nan]}
    )
    _, record = _numeric(frame, "amount")
    _assert_matches_retained_profile(frame, "amount")
    assert record.positive_infinity_count == 1
    assert record.negative_infinity_count == 1
    assert record.n_missing == 1
    assert record.finite_count == 5
    assert all(math.isfinite(item.value) for item in record.observations)
    assert [item.row_position for item in record.observations] == [4]
    assert record.observations[0].value == 100.0
    assert record.observations[0].direction is AnomalyDirection.ABOVE


def test_infinite_only_population_does_not_apply_fences() -> None:
    frame = pd.DataFrame({"amount": [np.inf, -np.inf, np.inf]})
    analysis, record = _numeric(frame, "amount")
    assert analysis.columns[0].inferred.selected_type is SemanticType.NUMERIC
    assert record.status is NumericAnomalyStatus.INSUFFICIENT_FINITE_POPULATION
    assert record.finite_count == 0
    assert record.q1 is None
    assert record.iqr is None
    assert record.observations == ()
    assert record.positive_infinity_count == 2
    assert record.negative_infinity_count == 1
    assert analysis.anomaly_analysis.coverage.n_analyzed == 0
    assert analysis.anomaly_analysis.coverage.n_unavailable == 1


def test_zero_iqr_does_not_classify_a_different_value() -> None:
    frame = pd.DataFrame({"amount": [0, 0, 0, 0, 0, 1]})
    analysis, record = _numeric(frame, "amount")
    descriptive = analysis.columns[0].numeric_analysis
    assert descriptive is not None
    assert descriptive.interquartile_range == 0
    assert record.status is NumericAnomalyStatus.ZERO_IQR
    assert record.q1 == descriptive.q1 == 0
    assert record.q3 == descriptive.q3 == 0
    assert record.iqr == 0
    assert record.lower_fence is None
    assert record.observations == ()
    assert record.method is None


def test_one_finite_value_beside_infinity_is_zero_iqr() -> None:
    frame = pd.DataFrame({"amount": [5.0, np.inf]})
    _, record = _numeric(frame, "amount")
    assert record.status is NumericAnomalyStatus.ZERO_IQR
    assert record.finite_count == 1
    assert record.positive_infinity_count == 1
    assert record.observations == ()


def test_two_finite_values_are_fenced_without_a_minimum_sample_size() -> None:
    frame = pd.DataFrame({"amount": [1, 5]})
    _, record = _numeric(frame, "amount")
    assert record.status is NumericAnomalyStatus.AVAILABLE
    assert record.finite_count == 2
    assert record.observations == ()
    _assert_matches_retained_profile(frame, "amount")


def test_quartiles_agree_with_an_independent_type7_calculation() -> None:
    values = [0, 1, 2, 3, 4, 5, 6, 1000]
    frame = pd.DataFrame({"amount": values})
    analysis, record = _numeric(frame, "amount")
    descriptive = analysis.columns[0].numeric_analysis
    assert descriptive is not None
    assert Fraction(descriptive.q1) == _type7(values, 1, 4)  # type: ignore[arg-type]
    assert Fraction(descriptive.q3) == _type7(values, 3, 4)  # type: ignore[arg-type]
    assert Fraction(record.q1) == Fraction(descriptive.q1)  # type: ignore[arg-type]
    assert Fraction(record.q3) == Fraction(descriptive.q3)  # type: ignore[arg-type]
    assert Fraction(record.iqr) == Fraction(descriptive.q3) - Fraction(descriptive.q1)  # type: ignore[arg-type]
    _assert_matches_retained_profile(frame, "amount")
    assert record.observations[-1].value == 1000
    assert record.observations[-1].row_position == 7


def test_huge_integers_are_not_classified_through_float64() -> None:
    base = 2**63
    offsets = (0, 1, 2, 3, 4, 5, 6, 1000)
    values = [base + offset for offset in offsets]
    frame = pd.DataFrame({"amount": np.array(values, dtype=np.uint64)})
    analysis, record = _numeric(frame, "amount")
    descriptive = analysis.columns[0].numeric_analysis
    assert descriptive is not None
    assert Fraction(descriptive.q1) == _type7(values, 1, 4)  # type: ignore[arg-type]
    assert Fraction(descriptive.q3) == _type7(values, 3, 4)  # type: ignore[arg-type]
    assert float(base + 1000) == float(base)
    _assert_matches_retained_profile(frame, "amount")
    assert record.status is NumericAnomalyStatus.AVAILABLE
    assert record.observations == (
        NumericAnomalyObservation(7, base + 1000, AnomalyDirection.ABOVE),
    )
    assert type(record.observations[0].value) is int


def test_signed_integers_above_the_exact_float_limit_keep_exact_positions() -> None:
    base = 2**62
    values = [base + offset for offset in (0, 1, 2, 3, 4, 5, 6, 1000)]
    frame = pd.DataFrame({"amount": pd.Series(values, dtype="int64")})
    _, record = _numeric(frame, "amount")
    _assert_matches_retained_profile(frame, "amount")
    assert record.observations[-1].value == base + 1000
    assert type(record.observations[-1].value) is int
    assert float(base + 1) == float(base)


def test_uint64_extreme_is_an_exact_python_int() -> None:
    top = 2**64 - 1
    values = [top - offset for offset in (1000, 6, 5, 4, 3, 2, 1, 0)]
    frame = pd.DataFrame({"amount": np.array(values, dtype=np.uint64)})
    _, record = _numeric(frame, "amount")
    _assert_matches_retained_profile(frame, "amount")
    assert record.observations[0].value == top - 1000
    assert record.observations[0].direction is AnomalyDirection.BELOW
    assert type(record.observations[0].value) is int


def test_wide_float_range_leaves_iqr_unavailable() -> None:
    limit = float(np.finfo(float).max)
    frame = pd.DataFrame({"amount": [-limit] * 50 + [limit] * 50})
    analysis, record = _numeric(frame, "amount")
    descriptive = analysis.columns[0].numeric_analysis
    assert descriptive is not None
    assert descriptive.interquartile_range is None
    assert record.status is NumericAnomalyStatus.IQR_UNAVAILABLE
    assert record.q1 == descriptive.q1
    assert record.q3 == descriptive.q3
    assert record.iqr is None
    assert record.observations == ()


def test_float_fence_that_is_not_a_finite_float_is_not_applied() -> None:
    limit = float(np.finfo(float).max)
    frame = pd.DataFrame({"amount": [limit * 0.5] * 50 + [limit] * 50})
    analysis, record = _numeric(frame, "amount")
    descriptive = analysis.columns[0].numeric_analysis
    assert descriptive is not None
    assert descriptive.interquartile_range is not None
    assert descriptive.interquartile_range > 0
    assert record.status is NumericAnomalyStatus.NUMERIC_PRECISION_UNSAFE
    assert record.iqr == descriptive.interquartile_range
    assert record.lower_fence is None
    assert record.upper_fence is None
    assert record.observations == ()
    assert (
        analysis.anomaly_analysis.coverage.unavailable[0].status
        is NumericAnomalyStatus.NUMERIC_PRECISION_UNSAFE
    )


def test_subnormal_values_remain_finite_observations() -> None:
    tiny = float(np.nextafter(0.0, 1.0))
    frame = pd.DataFrame({"amount": [tiny, 1.0, 2.0, 3.0, 4.0]})
    _, record = _numeric(frame, "amount")
    _assert_matches_retained_profile(frame, "amount")
    assert record.status is NumericAnomalyStatus.AVAILABLE
    assert all(item.value != tiny for item in record.observations)


def test_empty_and_constant_columns_are_ineligible() -> None:
    empty = _analysis(
        pd.DataFrame({"amount": pd.Series([pd.NA, pd.NA], dtype="Float64")})
    )
    assert empty.columns[0].inferred.selected_type is SemanticType.EMPTY
    assert empty.anomaly_analysis.coverage.n_eligible == 0
    assert (
        empty.anomaly_analysis.coverage.ineligible[0].reason
        is AnomalyIneligibility.EMPTY
    )
    constant = _analysis(pd.DataFrame({"amount": [4, 4, 4, 4]}))
    assert constant.columns[0].inferred.selected_type is SemanticType.CONSTANT
    assert constant.anomaly_analysis.numeric_univariate == ()
    assert (
        constant.anomaly_analysis.coverage.ineligible[0].reason
        is AnomalyIneligibility.CONSTANT
    )


def test_non_numeric_semantic_types_are_not_tukey_candidates() -> None:
    frame = pd.DataFrame(
        {
            "amount": [-2, 2, 3, 4, 8],
            "flag": pd.Series([True, True, True, True, False]),
            "city": pd.Series(["a", "a", "a", "b", "c"], dtype="category"),
            "when": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-08"]
            ),
            "span": pd.to_timedelta(["1 day", "2 days", "1 day", "3 days", "1 day"]),
            "code": pd.Series(
                [_UUID_A, _UUID_B, _UUID_A, _UUID_C, _UUID_B],
                dtype="string",
            ),
            "note": pd.Series(
                ["Amsterdam", "Berlin", "a longer note", "x", "y"],
                dtype="string",
            ),
            "empty": pd.Series([pd.NA] * 5, dtype="Float64"),
            "same": [4, 4, 4, 4, 4],
        }
    )
    analysis = _analysis(frame)
    coverage = analysis.anomaly_analysis.coverage
    assert [
        record.label for record in analysis.anomaly_analysis.numeric_univariate
    ] == ["amount"]
    reasons = {item.reason: item.n_columns for item in coverage.ineligible}
    assert reasons[AnomalyIneligibility.BOOLEAN] == 1
    assert reasons[AnomalyIneligibility.CATEGORICAL] == 1
    assert reasons[AnomalyIneligibility.DATETIME] == 1
    assert reasons[AnomalyIneligibility.TIMEDELTA] == 1
    assert reasons[AnomalyIneligibility.IDENTIFIER] == 1
    assert reasons[AnomalyIneligibility.UNRESOLVED] == 1
    assert reasons[AnomalyIneligibility.EMPTY] == 1
    assert reasons[AnomalyIneligibility.CONSTANT] == 1
    assert coverage.n_eligible == 1
    assert coverage.n_analyzed == 1
    assert coverage.n_ineligible == 8
    assert coverage.n_columns == 9
    assert analysis.columns[1].boolean_analysis is not None
    assert analysis.columns[1].boolean_analysis.false_count == 1
    assert analysis.columns[2].categorical_analysis is not None
    assert analysis.anomaly_analysis.numeric_univariate[0].label == "amount"


def test_integer_zero_one_stays_numeric_and_boolean_storage_does_not() -> None:
    frame = pd.DataFrame(
        {
            "code": [0, 0, 0, 1],
            "flag": pd.Series([True, True, True, False]),
        }
    )
    analysis = _analysis(frame)
    assert analysis.columns[0].inferred.selected_type is SemanticType.NUMERIC
    assert analysis.columns[1].inferred.selected_type is SemanticType.BOOLEAN
    assert [
        record.label for record in analysis.anomaly_analysis.numeric_univariate
    ] == ["code"]
    assert (
        analysis.anomaly_analysis.coverage.ineligible[0].reason
        is AnomalyIneligibility.BOOLEAN
    )


def test_physical_numeric_identifier_is_not_scanned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    series = pd.Series([1, 2, 100], dtype="int64")
    base = analyze_series(series, position=0, label="id")
    column = ColumnAnalysis(
        position=0,
        label="id",
        physical=base.physical,
        evidence=base.evidence,
        inferred=InferredSemanticResult(
            physical=base.physical,
            resolution=SemanticResolution(
                status=ResolutionStatus.RESOLVED,
                reason="Exactly one candidate is supported: Identifier.",
                candidates=(
                    CandidateAssessment(
                        semantic_type=SemanticType.IDENTIFIER,
                        disposition=CandidateDisposition.SUPPORTED,
                        supporting_evidence=(
                            SemanticEvidence(statement="synthetic identifier"),
                        ),
                    ),
                ),
                selected_type=SemanticType.IDENTIFIER,
            ),
        ),
    )
    assert column.numeric_analysis is None
    assert base.physical.family is PhysicalDtypeFamily.INTEGER

    def _fail(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("identifier column was scanned for Tukey fences")

    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    anomaly = collect_anomaly_analysis(pd.DataFrame({"id": series}), (column,))
    assert anomaly.numeric_univariate == ()
    assert anomaly.coverage.n_ineligible == 1
    assert anomaly.coverage.ineligible[0].reason is AnomalyIneligibility.IDENTIFIER


def test_text_and_ambiguous_columns_are_ineligible_without_a_detector() -> None:
    text = analyze_series(
        pd.Series(["alpha", "beta sentence", "gamma"], dtype="string"),
        label="note",
    )
    text_column = ColumnAnalysis(
        position=0,
        label="note",
        physical=text.physical,
        evidence=text.evidence,
        inferred=InferredSemanticResult(
            physical=text.physical,
            resolution=SemanticResolution(
                status=ResolutionStatus.RESOLVED,
                reason="Exactly one candidate is supported: Text.",
                candidates=(
                    CandidateAssessment(
                        semantic_type=SemanticType.TEXT,
                        disposition=CandidateDisposition.SUPPORTED,
                        supporting_evidence=(
                            SemanticEvidence(statement="synthetic text"),
                        ),
                    ),
                ),
                selected_type=SemanticType.TEXT,
            ),
        ),
    )
    physical = PhysicalDtype(family=PhysicalDtypeFamily.INTEGER, dtype_name="int64")
    basic = BasicColumnEvidence(
        n_total=3,
        n_missing=0,
        n_non_missing=3,
        n_unique_non_missing=3,
    )
    ambiguous = ColumnAnalysis(
        position=1,
        label="mixed",
        physical=physical,
        evidence=ColumnEvidence(basic=basic),
        inferred=InferredSemanticResult(
            physical=physical,
            resolution=SemanticResolution(
                status=ResolutionStatus.AMBIGUOUS,
                reason="Multiple candidates are supported: Identifier, Numeric.",
                candidates=(
                    CandidateAssessment(
                        semantic_type=SemanticType.IDENTIFIER,
                        disposition=CandidateDisposition.SUPPORTED,
                        supporting_evidence=(
                            SemanticEvidence(statement="synthetic identifier"),
                        ),
                    ),
                    CandidateAssessment(
                        semantic_type=SemanticType.NUMERIC,
                        disposition=CandidateDisposition.SUPPORTED,
                        supporting_evidence=(
                            SemanticEvidence(statement="synthetic numeric"),
                        ),
                    ),
                ),
            ),
        ),
    )
    frame = pd.DataFrame(
        {
            "note": ["alpha", "beta sentence", "gamma"],
            "mixed": [1, 2, 3],
        }
    )
    anomaly = collect_anomaly_analysis(frame, (text_column, ambiguous))
    reasons = {item.reason for item in anomaly.coverage.ineligible}
    assert reasons == {AnomalyIneligibility.TEXT, AnomalyIneligibility.AMBIGUOUS}
    assert anomaly.numeric_univariate == ()
    assert anomaly.coverage.n_analyzed == 0


def test_numeric_column_without_a_retained_profile_is_not_a_zero_anomaly_result() -> (
    None
):
    physical = PhysicalDtype(family=PhysicalDtypeFamily.INTEGER, dtype_name="int64")
    basic = BasicColumnEvidence(
        n_total=3,
        n_missing=0,
        n_non_missing=3,
        n_unique_non_missing=3,
    )
    column = ColumnAnalysis(
        position=0,
        label="amount",
        physical=physical,
        evidence=ColumnEvidence(basic=basic),
        inferred=InferredSemanticResult(
            physical=physical,
            resolution=SemanticResolution(
                status=ResolutionStatus.RESOLVED,
                reason="Exactly one candidate is supported: Numeric.",
                candidates=(
                    CandidateAssessment(
                        semantic_type=SemanticType.NUMERIC,
                        disposition=CandidateDisposition.SUPPORTED,
                        supporting_evidence=(
                            SemanticEvidence(statement="synthetic numeric"),
                        ),
                    ),
                ),
                selected_type=SemanticType.NUMERIC,
            ),
        ),
    )
    anomaly = anomaly_analysis_for_columns((column,), n_rows=3)
    assert anomaly.numeric_univariate == ()
    assert anomaly.coverage.n_eligible == 0
    assert anomaly.coverage.n_analyzed == 0
    assert anomaly.coverage.n_numeric_profile_absent == 1


def test_target_presence_does_not_change_anomaly_evidence() -> None:
    frame = pd.DataFrame(
        {
            "amount": [-2, 2, 3, 4, 8, 8],
            "flag": [True, False, True, False, True, False],
            "other": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )
    plain = _analysis(frame)
    targeted = _analysis(frame, target="flag")
    other_target = _analysis(frame, target="amount")
    assert plain.anomaly_analysis == targeted.anomaly_analysis
    assert plain.anomaly_analysis == other_target.anomaly_analysis
    assert targeted.target_analysis is not None
    assert plain.target_analysis is None


def test_summary_copies_retained_evidence_without_reading_the_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {"amount": [-2, 2, 3, 4, 8], "flag": [True, False, True, False, True]}
    )
    original = frame.copy()
    analysis = _analysis(frame)
    pd.testing.assert_frame_equal(frame, original)

    def _fail(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("anomaly summary reread the source")

    monkeypatch.setattr(pd.DataFrame, "iloc", _fail)
    monkeypatch.setattr(pd.Series, "to_numpy", _fail)
    monkeypatch.setattr(anomaly_module, "collect_anomaly_analysis", _fail)
    monkeypatch.setattr(dataset_module, "collect_anomaly_analysis", _fail)
    monkeypatch.setattr(dataset_module, "analyze_dataframe", _fail)
    summary = build_anomaly_summary(analysis)
    assert isinstance(summary, AnomalySummary)
    assert summary.coverage == analysis.anomaly_analysis.coverage
    assert summary.numeric_univariate == analysis.anomaly_analysis.numeric_univariate
    assert (
        summary.numeric_univariate is not analysis.anomaly_analysis.numeric_univariate
    )
    assert (
        summary.numeric_univariate[0]
        is not analysis.anomaly_analysis.numeric_univariate[0]
    )
    _assert_no_source(summary)
    _assert_no_source(analysis.anomaly_analysis)


def test_results_are_frozen_and_have_no_score_or_severity() -> None:
    frame = pd.DataFrame({"amount": [-2, 2, 3, 4, 8]})
    analysis, record = _numeric(frame, "amount")
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.status = NumericAnomalyStatus.ZERO_IQR  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.observations[0].value = 0  # type: ignore[misc]
    assert not hasattr(record, "score")
    assert not hasattr(record, "severity")
    assert not hasattr(record, "anomaly_score")
    assert dataclasses.fields(record.observations[0])[0].name == "row_position"
    names = {field.name for field in dataclasses.fields(record.observations[0])}
    assert names == {"row_position", "value", "direction"}
    assert "bad_rows" not in names
    assert analysis.anomaly_analysis.coverage.n_analyzed == 1
    assert not hasattr(analysis.anomaly_analysis, "multivariate")


def test_every_anomalous_position_is_retained() -> None:
    body = [0, 1, 2, 3, 4] * 16
    tail = [1000] * 20
    frame = pd.DataFrame({"amount": body + tail})
    _, record = _numeric(frame, "amount")
    _assert_matches_retained_profile(frame, "amount")
    assert record.above_count == len(record.observations)
    assert record.above_count == 20
    assert not hasattr(record, "truncated")
    assert not hasattr(record, "omitted_count")


def test_dataset_attachment_rejects_a_record_that_disagrees_with_the_profile() -> None:
    frame = pd.DataFrame({"amount": [-2, 2, 3, 4, 8]})
    analysis = _analysis(frame)
    record = analysis.anomaly_analysis.numeric_univariate[0]
    with pytest.raises(ValueError, match="retained numeric profile"):
        DatasetAnalysis(
            n_rows=analysis.n_rows,
            n_columns=analysis.n_columns,
            n_cells=analysis.n_cells,
            columns=analysis.columns,
            missing_analysis=analysis.missing_analysis,
            duplicate_analysis=analysis.duplicate_analysis,
            relationship_analysis=analysis.relationship_analysis,
            anomaly_analysis=AnomalyAnalysis(
                coverage=analysis.anomaly_analysis.coverage,
                numeric_univariate=(dataclasses.replace(record, q1=0),),
            ),
            target_analysis=analysis.target_analysis,
            target_leakage=analysis.target_leakage,
            target_diagnostic=analysis.target_diagnostic,
        )


def test_models_reject_inconsistent_anomaly_facts() -> None:
    with pytest.raises(TypeError, match="Python int or float"):
        NumericAnomalyObservation(0, np.int64(3), AnomalyDirection.ABOVE)
    with pytest.raises(ValueError, match="negative zero"):
        NumericAnomalyObservation(0, -0.0, AnomalyDirection.ABOVE)
    with pytest.raises(ValueError, match="strictly over"):
        NumericAnomalyColumn(
            position=0,
            label="amount",
            status=NumericAnomalyStatus.AVAILABLE,
            n_rows=1,
            n_missing=0,
            finite_count=1,
            positive_infinity_count=0,
            negative_infinity_count=0,
            method=NumericAnomalyMethod.TUKEY_IQR,
            fence_coefficient=Fraction(3, 2),
            q1=1,
            q3=2,
            iqr=1,
            lower_fence=0,
            upper_fence=3,
            below_count=0,
            above_count=1,
            observations=(NumericAnomalyObservation(0, 3, AnomalyDirection.ABOVE),),
        )
    with pytest.raises(ValueError, match="3/2"):
        NumericAnomalyColumn(
            position=0,
            label="amount",
            status=NumericAnomalyStatus.AVAILABLE,
            n_rows=1,
            n_missing=0,
            finite_count=1,
            positive_infinity_count=0,
            negative_infinity_count=0,
            method=NumericAnomalyMethod.TUKEY_IQR,
            fence_coefficient=Fraction(3, 1),
            q1=1,
            q3=2,
            iqr=1,
            lower_fence=0,
            upper_fence=4,
            below_count=0,
            above_count=0,
            observations=(),
        )
    with pytest.raises(ValueError, match="eligible"):
        AnomalyAnalysis(
            coverage=AnomalyCoverage(
                n_columns=0,
                n_eligible=1,
                n_analyzed=0,
                n_unavailable=1,
                n_ineligible=0,
                n_numeric_profile_absent=0,
                unavailable=(),
                ineligible=(),
            ),
            numeric_univariate=(),
        )
    with pytest.raises(TypeError, match="DatasetAnalysis"):
        build_anomaly_summary(pd.DataFrame({"amount": [1, 2, 3]}))
    with pytest.raises(TypeError, match="DataFrame"):
        collect_anomaly_analysis(pd.Series([1, 2, 3]), ())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="tuple"):
        anomaly_analysis_for_columns([], n_rows=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-negative"):
        NumericAnomalyObservation(-1, 1, AnomalyDirection.ABOVE)
    with pytest.raises(TypeError, match="AnomalyDirection"):
        NumericAnomalyObservation(0, 1, "above")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Python int or float"):
        NumericAnomalyObservation(0, True, AnomalyDirection.ABOVE)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocks fences"):
        AnomalyUnavailableCount(NumericAnomalyStatus.AVAILABLE, 1)
    with pytest.raises(ValueError, match="positive"):
        AnomalyUnavailableCount(NumericAnomalyStatus.ZERO_IQR, 0)
    with pytest.raises(TypeError, match="AnomalyIneligibility"):
        AnomalyIneligibleCount("boolean", 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="eligible"):
        AnomalyCoverage(
            n_columns=1,
            n_eligible=1,
            n_analyzed=1,
            n_unavailable=1,
            n_ineligible=0,
            n_numeric_profile_absent=0,
            unavailable=(),
            ineligible=(),
        )
    with pytest.raises(ValueError, match="account"):
        NumericAnomalyColumn(
            position=0,
            label="amount",
            status=NumericAnomalyStatus.INSUFFICIENT_FINITE_POPULATION,
            n_rows=2,
            n_missing=0,
            finite_count=0,
            positive_infinity_count=0,
            negative_infinity_count=0,
            method=None,
            fence_coefficient=None,
            q1=None,
            q3=None,
            iqr=None,
            lower_fence=None,
            upper_fence=None,
            below_count=None,
            above_count=None,
            observations=(),
        )
    with pytest.raises(ValueError, match="does not name an applied method"):
        NumericAnomalyColumn(
            position=0,
            label="amount",
            status=NumericAnomalyStatus.ZERO_IQR,
            n_rows=1,
            n_missing=0,
            finite_count=1,
            positive_infinity_count=0,
            negative_infinity_count=0,
            method=NumericAnomalyMethod.TUKEY_IQR,
            fence_coefficient=None,
            q1=0,
            q3=0,
            iqr=0,
            lower_fence=None,
            upper_fence=None,
            below_count=None,
            above_count=None,
            observations=(),
        )
    with pytest.raises(ValueError, match="increasing"):
        NumericAnomalyColumn(
            position=0,
            label="amount",
            status=NumericAnomalyStatus.AVAILABLE,
            n_rows=1,
            n_missing=0,
            finite_count=1,
            positive_infinity_count=0,
            negative_infinity_count=0,
            method=NumericAnomalyMethod.TUKEY_IQR,
            fence_coefficient=Fraction(3, 2),
            q1=1,
            q3=2,
            iqr=1,
            lower_fence=-1,
            upper_fence=4,
            below_count=0,
            above_count=1,
            observations=(NumericAnomalyObservation(3, 9, AnomalyDirection.ABOVE),),
        )
    with pytest.raises(ValueError, match="status order"):
        AnomalyCoverage(
            n_columns=2,
            n_eligible=2,
            n_analyzed=0,
            n_unavailable=2,
            n_ineligible=0,
            n_numeric_profile_absent=0,
            unavailable=(
                AnomalyUnavailableCount(NumericAnomalyStatus.ZERO_IQR, 1),
                AnomalyUnavailableCount(
                    NumericAnomalyStatus.INSUFFICIENT_FINITE_POPULATION,
                    1,
                ),
            ),
            ineligible=(),
        )
    with pytest.raises(ValueError, match="reason order"):
        AnomalyCoverage(
            n_columns=2,
            n_eligible=0,
            n_analyzed=0,
            n_unavailable=0,
            n_ineligible=2,
            n_numeric_profile_absent=0,
            unavailable=(),
            ineligible=(
                AnomalyIneligibleCount(AnomalyIneligibility.CATEGORICAL, 1),
                AnomalyIneligibleCount(AnomalyIneligibility.BOOLEAN, 1),
            ),
        )


def test_anomaly_module_is_not_a_detector_registry() -> None:
    text = open(anomaly_module.__file__, encoding="utf-8").read()
    source = ast.parse(text)
    imported = [
        alias.name
        for node in ast.walk(source)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    imported.extend(
        node.module
        for node in ast.walk(source)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert not any(name.split(".")[0] in {"sklearn", "scipy"} for name in imported)
    assert "IsolationForest" not in text
    assert "registry" not in text
    assert not hasattr(pytics, "analyze_dataframe")
    assert [member.name for member in NumericAnomalyMethod] == ["TUKEY_IQR"]


def test_nullable_numeric_storage_keeps_physical_positions() -> None:
    frame = pd.DataFrame(
        {
            "amount": pd.Series([-2, 2, pd.NA, 4, 8], dtype="Int64"),
            "reading": pd.Series([1.5, 2.5, pd.NA, 3.5, 40.0], dtype="Float64"),
        }
    )
    _assert_matches_retained_profile(frame, "amount")
    _assert_matches_retained_profile(frame, "reading")
    analysis = _analysis(frame)
    assert [
        record.n_missing for record in analysis.anomaly_analysis.numeric_univariate
    ] == [
        1,
        1,
    ]


def test_unsigned_values_compare_with_a_negative_lower_fence() -> None:
    frame = pd.DataFrame({"amount": np.array([0, 1, 2, 3, 4, 100], dtype=np.uint64)})
    _, record = _numeric(frame, "amount")
    _assert_matches_retained_profile(frame, "amount")
    assert record.lower_fence < 0
    assert record.observations[-1].value == 100
    assert type(record.observations[-1].value) is int


def test_collector_rejects_a_frame_that_does_not_match_the_columns() -> None:
    column = analyze_series(pd.Series([1, 2, 3]), position=0, label="amount")
    with pytest.raises(ValueError, match="width"):
        collect_anomaly_analysis(
            pd.DataFrame({"amount": [1, 2], "other": [3, 4]}), (column,)
        )
    with pytest.raises(ValueError, match="row count"):
        collect_anomaly_analysis(pd.DataFrame({"amount": [1, 2]}), (column,))
    with pytest.raises(TypeError, match="tuple"):
        collect_anomaly_analysis(
            pd.DataFrame({"amount": [1, 2, 3]}),
            [column],  # type: ignore[arg-type]
        )


def test_public_package_does_not_export_anomaly_analysis() -> None:
    assert not hasattr(pytics, "AnomalyAnalysis")
    assert not hasattr(pytics, "collect_anomaly_analysis")
