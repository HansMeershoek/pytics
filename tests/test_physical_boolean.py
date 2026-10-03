"""Slice 003: physical Boolean inference after Empty and Constant."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import pytics
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.empty_constant import interpret_empty_or_constant
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_boolean import (
    interpret_empty_constant_or_physical_boolean,
)
from pytics.semantics.physical_boolean import (
    interpret_empty_constant_or_physical_boolean_from_evidence,
)


def _interpret(series: pd.Series):
    return interpret_empty_constant_or_physical_boolean(series)


def _assert_boolean(series: pd.Series) -> None:
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is SemanticType.BOOLEAN
    assert result.confidence is Confidence.HIGH
    assert type(result.confidence) is Confidence
    assert result.source is InferenceSource.PHYSICAL_DTYPE
    assert result.source is not InferenceSource.INFERRED
    assert result.physical == classify_physical_dtype(series)
    assert result.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert result.subtype is None
    assert result.alternatives == ()
    assert result.evidence == (SemanticEvidence("physical dtype is boolean"),)


def _assert_precedence(series: pd.Series, semantic_type: SemanticType) -> None:
    result = _interpret(series)

    assert result is not None
    assert result.semantic_type is semantic_type
    assert result.semantic_type is not SemanticType.BOOLEAN
    assert result.confidence is Confidence.HIGH
    assert result.source is InferenceSource.INFERRED
    assert result.physical == classify_physical_dtype(series)
    assert result.physical.family is PhysicalDtypeFamily.BOOLEAN
    assert result.subtype is None
    assert result.alternatives == ()
    assert len(result.evidence) == 1
    assert isinstance(result.evidence[0], SemanticEvidence)


def test_native_bool_is_boolean():
    series = pd.Series([True, False], dtype=bool)

    _assert_boolean(series)
    assert series.dtype == bool


def test_nullable_boolean_with_missing_is_boolean():
    series = pd.Series([True, False, pd.NA], dtype="boolean")

    _assert_boolean(series)
    assert str(series.dtype) == "boolean"


def test_constant_bool_stays_constant():
    series = pd.Series([True, True], dtype=bool)

    _assert_precedence(series, SemanticType.CONSTANT)


def test_constant_nullable_bool_stays_constant():
    series = pd.Series([True, pd.NA, True], dtype="boolean")

    _assert_precedence(series, SemanticType.CONSTANT)


def test_empty_nullable_bool_stays_empty():
    series = pd.Series([pd.NA, pd.NA], dtype="boolean")

    _assert_precedence(series, SemanticType.EMPTY)
    assert _interpret(series).evidence[0].statement == (
        "0 non-missing observations out of 2"
    )


def test_empty_zero_length_bool_stays_empty():
    series = pd.Series([], dtype=bool)

    _assert_precedence(series, SemanticType.EMPTY)
    assert _interpret(series).evidence[0].statement == (
        "0 non-missing observations out of 0"
    )


def test_numeric_zero_one_has_no_interpretation():
    series = pd.Series([0, 1])
    result = _interpret(series)

    assert result is None
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.INTEGER


def test_repeated_numeric_zero_one_has_no_interpretation():
    series = pd.Series([0, 1, 0, 1])

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is not PhysicalDtypeFamily.BOOLEAN


def test_yes_no_strings_have_no_interpretation():
    series = pd.Series(["yes", "no"])

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is not PhysicalDtypeFamily.BOOLEAN


def test_true_false_strings_have_no_interpretation():
    series = pd.Series(["true", "false"])

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is not PhysicalDtypeFamily.BOOLEAN


def test_object_python_booleans_have_no_interpretation():
    series = pd.Series([True, False], dtype=object)

    assert _interpret(series) is None
    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.OBJECT
    assert str(series.dtype) == "object"


def test_categorical_booleans_have_no_interpretation():
    series = pd.Series(pd.Categorical([True, False]))

    assert _interpret(series) is None
    physical = classify_physical_dtype(series)
    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert physical.categorical_ordered is False


def test_ordered_categorical_booleans_have_no_interpretation():
    ordered = pd.CategoricalDtype(categories=[False, True], ordered=True)
    series = pd.Series([True, False], dtype=ordered)

    assert _interpret(series) is None
    physical = classify_physical_dtype(series)
    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    assert physical.categorical_ordered is True
    assert series.dtype.ordered is True
    assert list(series.dtype.categories) == [False, True]
    assert "ORDINAL" not in SemanticType.__members__


def test_multi_value_numeric_and_string_have_no_interpretation():
    assert _interpret(pd.Series([1, 2, 3])) is None
    assert _interpret(pd.Series(["A", "B"])) is None


def test_empty_and_constant_still_apply_outside_boolean_dtype():
    empty = _interpret(pd.Series([np.nan, np.nan]))
    constant = _interpret(pd.Series([5, 5, 5]))

    assert empty is not None and empty.semantic_type is SemanticType.EMPTY
    assert empty.source is InferenceSource.INFERRED
    assert constant is not None and constant.semantic_type is SemanticType.CONSTANT
    assert constant.source is InferenceSource.INFERRED
    assert constant.alternatives == ()


def test_slice_002_boolean_pair_still_has_no_interpretation():
    series = pd.Series([True, False], dtype=bool)

    assert interpret_empty_or_constant(series) is None
    assert _interpret(series).semantic_type is SemanticType.BOOLEAN


def test_from_evidence_reuses_counts_and_keeps_precedence():
    boolean = classify_physical_dtype("boolean")
    integer = classify_physical_dtype("int64")
    both_values = BasicColumnEvidence(4, 1, 3, 2)
    constant = BasicColumnEvidence(3, 1, 2, 1)
    empty = BasicColumnEvidence(2, 2, 0, 0)
    binary_numbers = BasicColumnEvidence(4, 0, 4, 2)

    boolean_reading = interpret_empty_constant_or_physical_boolean_from_evidence(
        both_values,
        boolean,
    )
    assert boolean_reading.semantic_type is SemanticType.BOOLEAN
    assert boolean_reading.source is InferenceSource.PHYSICAL_DTYPE
    assert boolean_reading.physical is boolean
    assert (
        interpret_empty_constant_or_physical_boolean_from_evidence(
            constant,
            boolean,
        ).semantic_type
        is SemanticType.CONSTANT
    )
    assert (
        interpret_empty_constant_or_physical_boolean_from_evidence(
            empty,
            boolean,
        ).semantic_type
        is SemanticType.EMPTY
    )
    assert (
        interpret_empty_constant_or_physical_boolean_from_evidence(
            binary_numbers,
            integer,
        )
        is None
    )


def test_from_evidence_rejects_bad_inputs():
    evidence = BasicColumnEvidence(2, 0, 2, 2)
    physical = classify_physical_dtype("bool")

    with pytest.raises(TypeError):
        interpret_empty_constant_or_physical_boolean_from_evidence(
            evidence,
            "bool",  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        interpret_empty_constant_or_physical_boolean_from_evidence(
            object(),  # type: ignore[arg-type]
            physical,
        )


def test_non_series_is_rejected():
    frame = pd.DataFrame({"flag": [True, False]})

    with pytest.raises(TypeError):
        interpret_empty_constant_or_physical_boolean(frame)  # type: ignore[arg-type]


def test_column_name_does_not_create_a_boolean_reading():
    named_numbers = pd.Series([0, 1], name="is_active")
    named_bool = pd.Series([True, False], dtype=bool, name="measurement")

    assert _interpret(named_numbers) is None
    assert _interpret(named_bool).semantic_type is SemanticType.BOOLEAN


def test_series_is_unchanged_after_inference():
    native = pd.Series([True, False, True], dtype=bool, index=[2, 0, 1], name="flag")
    nullable = pd.Series([True, pd.NA, False], dtype="boolean", name="flag")
    objects = pd.Series([True, False], dtype=object, index=["a", "b"], name="flag")
    ordered = pd.CategoricalDtype(categories=[False, True], ordered=True)
    categorical = pd.Series([True, False, True], dtype=ordered, name="flag")
    numbers = pd.Series([0, 1, 0, 1], index=[3, 1, 4, 2], name="code")
    words = pd.Series(["yes", "no"], name="answer")
    originals = [
        series.copy(deep=True)
        for series in (native, nullable, objects, categorical, numbers, words)
    ]

    for series in (native, nullable, objects, categorical, numbers, words):
        _interpret(series)

    for series, original in zip(
        (native, nullable, objects, categorical, numbers, words),
        originals,
    ):
        pd.testing.assert_series_equal(series, original)


def test_slice_003_names_are_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "interpret_empty_constant_or_physical_boolean")
    assert not hasattr(
        pytics,
        "interpret_empty_constant_or_physical_boolean_from_evidence",
    )
