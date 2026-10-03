"""Contract tests for the Slice 001 semantic foundation."""

from __future__ import annotations

import warnings
from dataclasses import FrozenInstanceError
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

import pytics
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticAlternative
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype


class _UnrecognizedDtype(pd.api.extensions.ExtensionDtype):
    name = "pytics_unrecognized"
    type = object

    @classmethod
    def construct_array_type(cls):
        raise NotImplementedError


def _aware_datetime_dtype():
    return pd.Series(pd.date_range("2024-01-01", periods=2, tz="UTC")).dtype


@pytest.mark.parametrize(
    ("dtype", "family"),
    [
        (np.dtype("int64"), PhysicalDtypeFamily.INTEGER),
        (pd.Int64Dtype(), PhysicalDtypeFamily.INTEGER),
        (np.dtype("float64"), PhysicalDtypeFamily.FLOATING),
        (pd.Float64Dtype(), PhysicalDtypeFamily.FLOATING),
        (np.dtype("bool"), PhysicalDtypeFamily.BOOLEAN),
        (pd.BooleanDtype(), PhysicalDtypeFamily.BOOLEAN),
        (pd.StringDtype(), PhysicalDtypeFamily.STRING),
        (np.dtype("O"), PhysicalDtypeFamily.OBJECT),
        (pd.CategoricalDtype(), PhysicalDtypeFamily.CATEGORICAL),
        (np.dtype("datetime64[ns]"), PhysicalDtypeFamily.DATETIME),
        (_aware_datetime_dtype(), PhysicalDtypeFamily.DATETIME_TZ_AWARE),
        (np.dtype("timedelta64[ns]"), PhysicalDtypeFamily.TIMEDELTA),
        (pd.PeriodDtype(freq="D"), PhysicalDtypeFamily.PERIOD),
        (pd.IntervalDtype(subtype="int64"), PhysicalDtypeFamily.INTERVAL),
        (np.dtype("complex128"), PhysicalDtypeFamily.COMPLEX),
        (np.dtype("U10"), PhysicalDtypeFamily.STRING),
        (pd.SparseDtype("float64"), PhysicalDtypeFamily.FLOATING),
        (_UnrecognizedDtype(), PhysicalDtypeFamily.OTHER),
    ],
)
def test_physical_family_and_dtype_name(dtype, family):
    result = classify_physical_dtype(dtype)

    assert result.family is family
    assert result.dtype_name == str(dtype)
    if family is PhysicalDtypeFamily.CATEGORICAL:
        assert result.categorical_ordered is False
    else:
        assert result.categorical_ordered is None


def test_dtype_alias_uses_pandas_resolution():
    assert classify_physical_dtype("int64") == classify_physical_dtype(
        np.dtype("int64")
    )
    assert classify_physical_dtype("Int64").family is PhysicalDtypeFamily.INTEGER
    assert classify_physical_dtype("Int64").dtype_name == "Int64"


def test_series_and_its_dtype_classify_the_same_way():
    series = pd.Series([1, 2, 3], dtype="int64")

    assert classify_physical_dtype(series) == classify_physical_dtype(series.dtype)


def test_integer_family_ignores_uniqueness_and_constancy():
    unique = pd.Series([1, 2, 3, 4], dtype="int64")
    repeated = pd.Series([7, 7, 7, 7], dtype="int64")

    assert classify_physical_dtype(unique) == classify_physical_dtype(unique.dtype)
    assert classify_physical_dtype(unique) == classify_physical_dtype(repeated)
    assert classify_physical_dtype(unique).family is PhysicalDtypeFamily.INTEGER


def test_all_missing_nullable_integer_stays_integer():
    series = pd.Series([pd.NA, pd.NA], dtype="Int64")

    result = classify_physical_dtype(series)

    assert result.family is PhysicalDtypeFamily.INTEGER
    assert isinstance(result, PhysicalDtype)


def test_object_strings_stay_object():
    series = pd.Series(["true", "false", "maybe"], dtype=object)

    result = classify_physical_dtype(series)

    assert result.family is PhysicalDtypeFamily.OBJECT
    assert result.dtype_name == "object"


def test_string_dtype_stays_string_when_values_look_boolean():
    series = pd.Series(["true", "false"], dtype="string")

    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.STRING


def test_ordered_categorical_remains_a_physical_categorical():
    dtype = pd.CategoricalDtype(categories=["low", "medium", "high"], ordered=True)

    result = classify_physical_dtype(dtype)

    assert result.family is PhysicalDtypeFamily.CATEGORICAL
    assert result.categorical_ordered is True
    assert isinstance(result, PhysicalDtype)


def test_timezone_name_stays_visible():
    result = classify_physical_dtype(_aware_datetime_dtype())

    assert result.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert "UTC" in result.dtype_name


def test_classification_does_not_mutate_the_series():
    series = pd.Series([1, None, 3], dtype="Int64")
    original = series.copy(deep=True)

    classify_physical_dtype(series)

    pd.testing.assert_series_equal(series, original)


def test_classification_does_not_emit_deprecated_dtype_warnings():
    sources = [
        np.dtype("int64"),
        pd.CategoricalDtype(ordered=True),
        pd.PeriodDtype(freq="D"),
        pd.IntervalDtype(subtype="int64"),
        _aware_datetime_dtype(),
        np.dtype("timedelta64[ns]"),
    ]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for source in sources:
            classify_physical_dtype(source)

    deprecated = [item for item in caught if "deprecated" in str(item.message).lower()]
    assert deprecated == []


def test_rejected_classification_inputs():
    with pytest.raises(TypeError):
        classify_physical_dtype(pd.DataFrame({"a": [1]}))
    with pytest.raises(TypeError):
        classify_physical_dtype(np.array([1, 2, 3]))
    with pytest.raises(TypeError):
        classify_physical_dtype(object())
    with pytest.raises(TypeError):
        classify_physical_dtype("not_a_dtype")


def test_physical_dtype_is_frozen_and_equal_by_value():
    left = classify_physical_dtype(np.dtype("float64"))
    right = classify_physical_dtype(np.dtype("float64"))

    assert left == right
    with pytest.raises(FrozenInstanceError):
        left.family = PhysicalDtypeFamily.INTEGER  # type: ignore[misc]


def test_categorical_ordered_is_rejected_on_other_families():
    with pytest.raises(ValueError):
        PhysicalDtype(
            family=PhysicalDtypeFamily.INTEGER,
            dtype_name="int64",
            categorical_ordered=True,
        )


def test_physical_dtype_rejects_invalid_parts():
    with pytest.raises(TypeError):
        PhysicalDtype(family="integer", dtype_name="int64")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        PhysicalDtype(family=PhysicalDtypeFamily.INTEGER, dtype_name=" ")
    with pytest.raises(TypeError):
        PhysicalDtype(family=PhysicalDtypeFamily.CATEGORICAL, dtype_name="category")


def test_semantic_vocabulary_is_the_minimum_list_without_ordinal():
    assert {member.name for member in SemanticType} == {
        "NUMERIC",
        "CATEGORICAL",
        "BOOLEAN",
        "TEXT",
        "DATETIME",
        "TIMEDELTA",
        "IDENTIFIER",
        "CONSTANT",
        "EMPTY",
    }
    assert not any(member.name == "ORDINAL" for member in SemanticType)


def test_confidence_is_only_high_medium_low():
    assert [member.value for member in Confidence] == ["high", "medium", "low"]
    assert all(isinstance(member.value, str) for member in Confidence)


def test_inference_source_vocabulary():
    assert {member.value for member in InferenceSource} == {
        "inferred",
        "physical_dtype",
        "user_configured",
    }


def test_interpretation_stores_evidence_alternatives_and_subtype():
    physical = classify_physical_dtype(pd.BooleanDtype())
    supplied_evidence = [SemanticEvidence("physical dtype is boolean")]
    reading = SemanticInterpretation(
        semantic_type=SemanticType.BOOLEAN,
        confidence=Confidence.HIGH,
        source=InferenceSource.PHYSICAL_DTYPE,
        physical=physical,
        evidence=supplied_evidence,
        alternatives=(
            SemanticAlternative(
                semantic_type=SemanticType.CATEGORICAL,
                confidence=Confidence.LOW,
            ),
        ),
    )
    supplied_evidence.append(SemanticEvidence("this must not leak into the reading"))

    assert reading.evidence == (SemanticEvidence("physical dtype is boolean"),)
    assert reading.alternatives[0].semantic_type is SemanticType.CATEGORICAL
    assert reading.alternatives[0].confidence is Confidence.LOW
    assert reading.subtype is None
    assert reading.physical.family is PhysicalDtypeFamily.BOOLEAN


def test_interpretations_are_equal_and_frozen():
    physical = classify_physical_dtype(np.dtype("int64"))
    kwargs = {
        "semantic_type": SemanticType.NUMERIC,
        "confidence": Confidence.MEDIUM,
        "source": InferenceSource.INFERRED,
        "physical": physical,
        "subtype": "discrete",
        "evidence": (SemanticEvidence("stored as an integer dtype"),),
        "alternatives": (
            SemanticAlternative(
                semantic_type=SemanticType.CATEGORICAL,
                subtype="ordinal",
                confidence=Confidence.LOW,
            ),
        ),
    }
    left = SemanticInterpretation(**kwargs)
    right = SemanticInterpretation(**kwargs)

    assert left == right
    assert left != replace(left, confidence=Confidence.HIGH)
    assert left.alternatives[0].subtype == "ordinal"
    with pytest.raises(FrozenInstanceError):
        left.confidence = Confidence.LOW  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        left.evidence[0].statement = "changed"  # type: ignore[misc]


def test_subtype_label_does_not_define_a_taxonomy():
    reading = SemanticInterpretation(
        semantic_type=SemanticType.CATEGORICAL,
        confidence=Confidence.LOW,
        source=InferenceSource.USER_CONFIGURED,
        physical=classify_physical_dtype(pd.CategoricalDtype()),
        subtype="ordinal",
    )

    assert reading.subtype == "ordinal"
    assert "ORDINAL" not in SemanticType.__members__


def test_numeric_confidence_and_loose_strings_are_rejected():
    physical = classify_physical_dtype(np.dtype("float64"))
    with pytest.raises(TypeError):
        SemanticInterpretation(
            semantic_type=SemanticType.NUMERIC,
            confidence=0.87,  # type: ignore[arg-type]
            source=InferenceSource.INFERRED,
            physical=physical,
        )
    with pytest.raises(TypeError):
        SemanticInterpretation(
            semantic_type="numeric",  # type: ignore[arg-type]
            confidence=Confidence.HIGH,
            source=InferenceSource.INFERRED,
            physical=physical,
        )
    with pytest.raises(TypeError):
        SemanticInterpretation(
            semantic_type=SemanticType.NUMERIC,
            confidence=Confidence.HIGH,
            source="inferred",  # type: ignore[arg-type]
            physical=physical,
        )


def test_evidence_must_be_a_non_empty_statement_sequence():
    with pytest.raises(ValueError):
        SemanticEvidence("  ")
    physical = classify_physical_dtype(np.dtype("int64"))
    with pytest.raises(TypeError):
        SemanticInterpretation(
            semantic_type=SemanticType.IDENTIFIER,
            confidence=Confidence.LOW,
            source=InferenceSource.INFERRED,
            physical=physical,
            evidence=SemanticEvidence("100% unique among non-missing values"),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError):
        SemanticInterpretation(
            semantic_type=SemanticType.CATEGORICAL,
            confidence=Confidence.LOW,
            source=InferenceSource.USER_CONFIGURED,
            physical=physical,
            subtype="  ",
        )


def test_interpretation_rejects_malformed_subtype_and_evidence():
    physical = classify_physical_dtype(np.dtype("int64"))
    base = {
        "semantic_type": SemanticType.NUMERIC,
        "confidence": Confidence.LOW,
        "source": InferenceSource.INFERRED,
        "physical": physical,
    }
    with pytest.raises(TypeError):
        SemanticInterpretation(**base, subtype=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        SemanticInterpretation(**base, evidence=123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        SemanticInterpretation(**base, evidence=("not evidence",))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        SemanticAlternative(
            semantic_type=SemanticType.TEXT,
            confidence="low",  # type: ignore[arg-type]
        )


def test_value_objects_do_not_grow_speculative_fields():
    assert set(SemanticEvidence.__dataclass_fields__) == {"statement"}
    assert set(SemanticAlternative.__dataclass_fields__) == {
        "semantic_type",
        "subtype",
        "confidence",
    }
    assert set(SemanticInterpretation.__dataclass_fields__) == {
        "semantic_type",
        "confidence",
        "source",
        "physical",
        "subtype",
        "evidence",
        "alternatives",
    }
    assert set(PhysicalDtype.__dataclass_fields__) == {
        "family",
        "dtype_name",
        "categorical_ordered",
    }


def test_top_level_public_api_is_unchanged():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "classify_physical_dtype")
    assert not hasattr(pytics, "SemanticInterpretation")
    assert not hasattr(pytics, "SemanticType")
