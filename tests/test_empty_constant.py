"""Slice 002: basic column evidence and Empty/Constant inference."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

import pytics
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.empty_constant import interpret_empty_or_constant
from pytics.semantics.empty_constant import interpret_empty_or_constant_from_evidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype


def _empty_statement(n_total: int) -> str:
    return f"0 non-missing observations out of {n_total}"


def _constant_statement(n_non_missing: int, n_total: int) -> str:
    return (
        "1 distinct non-missing value among "
        f"{n_non_missing} non-missing observations out of {n_total}"
    )


def _assert_invariants(evidence: BasicColumnEvidence) -> None:
    assert evidence.n_total >= 0
    assert 0 <= evidence.n_missing <= evidence.n_total
    assert evidence.n_non_missing == evidence.n_total - evidence.n_missing
    assert 0 <= evidence.n_unique_non_missing <= evidence.n_non_missing
    assert type(evidence.n_total) is int
    assert type(evidence.n_missing) is int
    assert type(evidence.n_non_missing) is int
    assert type(evidence.n_unique_non_missing) is int


def _assert_interpretation(series: pd.Series, semantic_type: SemanticType) -> None:
    evidence = collect_basic_column_evidence(series)
    result = interpret_empty_or_constant(series)

    _assert_invariants(evidence)
    assert result is not None
    assert result.semantic_type is semantic_type
    assert result.physical == classify_physical_dtype(series)
    assert result.source is InferenceSource.INFERRED
    assert result.confidence is Confidence.HIGH
    assert result.subtype is None
    assert result.alternatives == ()
    assert len(result.evidence) == 1
    assert isinstance(result.evidence[0], SemanticEvidence)
    if semantic_type is SemanticType.EMPTY:
        assert evidence.n_non_missing == 0
        assert result.evidence[0].statement == _empty_statement(evidence.n_total)
    else:
        assert evidence.n_non_missing > 0
        assert evidence.n_unique_non_missing == 1
        assert result.evidence[0].statement == _constant_statement(
            evidence.n_non_missing, evidence.n_total
        )
    assert result.semantic_type not in {
        SemanticType.BOOLEAN,
        SemanticType.NUMERIC,
        SemanticType.CATEGORICAL,
        SemanticType.TEXT,
        SemanticType.IDENTIFIER,
    }


def _assert_no_interpretation(series: pd.Series) -> None:
    evidence = collect_basic_column_evidence(series)
    result = interpret_empty_or_constant(series)

    _assert_invariants(evidence)
    assert evidence.n_non_missing > 0
    assert evidence.n_unique_non_missing != 1
    assert result is None


def test_basic_evidence_stores_only_the_four_counts():
    evidence = BasicColumnEvidence(
        n_total=4,
        n_missing=1,
        n_non_missing=3,
        n_unique_non_missing=2,
    )

    assert set(BasicColumnEvidence.__dataclass_fields__) == {
        "n_total",
        "n_missing",
        "n_non_missing",
        "n_unique_non_missing",
    }
    _assert_invariants(evidence)
    with pytest.raises(FrozenInstanceError):
        evidence.n_total = 0  # type: ignore[misc]


def test_basic_evidence_rejects_broken_counts():
    with pytest.raises(TypeError):
        BasicColumnEvidence(True, 0, 1, 0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        BasicColumnEvidence(1, np.int64(0), 1, 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        BasicColumnEvidence(-1, 0, -1, 0)
    with pytest.raises(ValueError):
        BasicColumnEvidence(2, 3, 0, 0)
    with pytest.raises(ValueError):
        BasicColumnEvidence(3, 1, 1, 1)
    with pytest.raises(ValueError):
        BasicColumnEvidence(3, 0, 3, 4)


def test_collected_counts_match_pandas_missingness_without_sampling():
    series = pd.Series([1, None, 1, 2, None], dtype="Int64")

    evidence = collect_basic_column_evidence(series)

    assert evidence == BasicColumnEvidence(
        n_total=5,
        n_missing=2,
        n_non_missing=3,
        n_unique_non_missing=2,
    )
    _assert_invariants(evidence)


def test_pandas_missing_sentinels_are_missing_and_literals_are_values():
    sentinels = pd.Series([None, np.nan, pd.NA, pd.NaT], dtype=object)
    sentinel_evidence = collect_basic_column_evidence(sentinels)

    assert sentinel_evidence.n_missing == 4
    assert sentinel_evidence.n_non_missing == 0
    assert interpret_empty_or_constant(sentinels).semantic_type is SemanticType.EMPTY

    literals = pd.Series(["?", "N/A", "", "null", "NA"])
    literal_evidence = collect_basic_column_evidence(literals)

    assert literal_evidence.n_missing == 0
    assert literal_evidence.n_unique_non_missing == 5
    assert interpret_empty_or_constant(literals) is None


def test_collect_and_interpret_reject_non_series():
    frame = pd.DataFrame({"a": [1, 1]})

    with pytest.raises(TypeError):
        collect_basic_column_evidence(frame)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        interpret_empty_or_constant(frame)  # type: ignore[arg-type]


def test_unhashable_values_are_not_empty_or_constant():
    series = pd.Series([[1], [2]])
    original = series.copy(deep=True)

    evidence = collect_basic_column_evidence(series)

    assert evidence.n_unique_non_missing is None
    assert evidence.is_constant is False
    assert interpret_empty_or_constant(series) is None
    pd.testing.assert_series_equal(series, original)


def test_empty_series_is_empty():
    series = pd.Series([], dtype="float64")

    evidence = collect_basic_column_evidence(series)

    assert evidence == BasicColumnEvidence(0, 0, 0, 0)
    _assert_interpretation(series, SemanticType.EMPTY)


def test_all_missing_float_is_empty():
    _assert_interpretation(pd.Series([np.nan, np.nan]), SemanticType.EMPTY)


def test_all_missing_nullable_integer_is_empty_integer():
    series = pd.Series([pd.NA, pd.NA], dtype="Int64")
    result = interpret_empty_or_constant(series)

    _assert_interpretation(series, SemanticType.EMPTY)
    assert result.physical.family is PhysicalDtypeFamily.INTEGER
    assert result.physical.dtype_name == "Int64"


def test_all_missing_boolean_is_empty():
    series = pd.Series([pd.NA, pd.NA], dtype="boolean")

    _assert_interpretation(series, SemanticType.EMPTY)
    assert interpret_empty_or_constant(series).physical.family is (
        PhysicalDtypeFamily.BOOLEAN
    )


def test_all_missing_string_is_empty():
    series = pd.Series([pd.NA, pd.NA], dtype="string")

    _assert_interpretation(series, SemanticType.EMPTY)
    assert interpret_empty_or_constant(series).physical.family is (
        PhysicalDtypeFamily.STRING
    )


def test_all_missing_categorical_is_empty():
    series = pd.Series(pd.Categorical([pd.NA, pd.NA], categories=["A", "B"]))

    _assert_interpretation(series, SemanticType.EMPTY)
    assert interpret_empty_or_constant(series).physical.family is (
        PhysicalDtypeFamily.CATEGORICAL
    )


def test_all_missing_datetime_is_empty_datetime():
    series = pd.Series([pd.NaT, pd.NaT], dtype="datetime64[ns]")
    result = interpret_empty_or_constant(series)

    _assert_interpretation(series, SemanticType.EMPTY)
    assert result.physical.family is PhysicalDtypeFamily.DATETIME
    assert result.physical.dtype_name == "datetime64[ns]"


def test_constant_numeric():
    series = pd.Series([5, 5, 5])
    result = interpret_empty_or_constant(series)

    _assert_interpretation(series, SemanticType.CONSTANT)
    assert "5" not in result.evidence[0].statement


def test_constant_numeric_plus_missing():
    series = pd.Series([5, np.nan, 5])
    evidence = collect_basic_column_evidence(series)

    assert evidence.n_missing == 1
    assert evidence.n_non_missing == 2
    assert evidence.n_unique_non_missing == 1
    _assert_interpretation(series, SemanticType.CONSTANT)


def test_constant_nullable_integer_plus_missing_stays_integer():
    series = pd.Series([5, pd.NA, 5], dtype="Int64")
    result = interpret_empty_or_constant(series)

    _assert_interpretation(series, SemanticType.CONSTANT)
    assert result.physical.family is PhysicalDtypeFamily.INTEGER


def test_constant_string():
    _assert_interpretation(pd.Series(["A", "A"]), SemanticType.CONSTANT)


def test_constant_string_plus_missing():
    series = pd.Series(["A", None, "A"])

    assert collect_basic_column_evidence(series).n_missing == 1
    _assert_interpretation(series, SemanticType.CONSTANT)


def test_constant_boolean_is_not_boolean_semantics():
    series = pd.Series([True, True, True])
    result = interpret_empty_or_constant(series)

    _assert_interpretation(series, SemanticType.CONSTANT)
    assert result.semantic_type is SemanticType.CONSTANT
    assert result.physical.family is PhysicalDtypeFamily.BOOLEAN


def test_binary_boolean_has_no_interpretation():
    _assert_no_interpretation(pd.Series([True, False]))


def test_multi_value_numeric_has_no_interpretation():
    _assert_no_interpretation(pd.Series([1, 2, 3]))


def test_multi_value_string_has_no_interpretation():
    _assert_no_interpretation(pd.Series(["A", "B"]))


def test_repeated_missing_like_literal_is_constant():
    series = pd.Series(["?", "?"])
    result = interpret_empty_or_constant(series)

    _assert_interpretation(series, SemanticType.CONSTANT)
    assert result.semantic_type is not SemanticType.EMPTY
    assert list(series) == ["?", "?"]


def test_missing_like_literal_plus_missing_is_constant():
    series = pd.Series(["?", None, "?"])

    assert collect_basic_column_evidence(series).n_missing == 1
    _assert_interpretation(series, SemanticType.CONSTANT)


def test_categorical_with_one_observed_value_is_constant():
    series = pd.Series(pd.Categorical(["A", "A"], categories=["A", "B"]))
    evidence = collect_basic_column_evidence(series)

    assert evidence.n_unique_non_missing == 1
    _assert_interpretation(series, SemanticType.CONSTANT)
    assert interpret_empty_or_constant(series).physical.categorical_ordered is False


def test_ordered_categorical_keeps_physical_order_and_is_not_ordinal():
    ordered = pd.CategoricalDtype(categories=["low", "medium", "high"], ordered=True)
    constant = pd.Series(["low", "low"], dtype=ordered)
    varied = pd.Series(["low", "high"], dtype=ordered)
    empty = pd.Series([pd.NA, pd.NA], dtype=ordered)

    constant_reading = interpret_empty_or_constant(constant)
    empty_reading = interpret_empty_or_constant(empty)

    _assert_interpretation(constant, SemanticType.CONSTANT)
    _assert_interpretation(empty, SemanticType.EMPTY)
    assert constant_reading.physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert constant_reading.physical.categorical_ordered is True
    assert empty_reading.physical.categorical_ordered is True
    assert constant_reading.subtype is None
    assert "ORDINAL" not in SemanticType.__members__
    _assert_no_interpretation(varied)


def test_precedence_on_evidence_checks_empty_before_constant():
    physical = classify_physical_dtype("float64")
    empty = BasicColumnEvidence(2, 2, 0, 0)
    constant = BasicColumnEvidence(3, 1, 2, 1)
    ordinary = BasicColumnEvidence(3, 0, 3, 2)

    assert (
        interpret_empty_or_constant_from_evidence(empty, physical).semantic_type
        is SemanticType.EMPTY
    )
    assert (
        interpret_empty_or_constant_from_evidence(constant, physical).semantic_type
        is SemanticType.CONSTANT
    )
    assert interpret_empty_or_constant_from_evidence(ordinary, physical) is None
    with pytest.raises(TypeError):
        interpret_empty_or_constant_from_evidence(ordinary, "float64")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        interpret_empty_or_constant_from_evidence(object(), physical)  # type: ignore[arg-type]


def test_series_is_unchanged_after_evidence_and_inference():
    constant = pd.Series(
        ["?", None, "?"],
        index=[3, 1, 2],
        name="token",
    )
    ordinary = pd.Series([1, None, 3], dtype="Int64", name="measure")
    constant_original = constant.copy(deep=True)
    ordinary_original = ordinary.copy(deep=True)

    collect_basic_column_evidence(constant)
    interpret_empty_or_constant(constant)
    collect_basic_column_evidence(ordinary)
    interpret_empty_or_constant(ordinary)

    pd.testing.assert_series_equal(constant, constant_original)
    pd.testing.assert_series_equal(ordinary, ordinary_original)


def test_slice_002_names_are_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "BasicColumnEvidence")
    assert not hasattr(pytics, "collect_basic_column_evidence")
    assert not hasattr(pytics, "interpret_empty_or_constant")
