"""Objective physical dtype classification.

This module names the pandas storage family of a dtype. It does not infer
semantic types, and it does not inspect Series values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import numpy as np
import pandas as pd


class PhysicalDtypeFamily(Enum):
    """Physical pandas dtype families.

    These are storage families, not semantic types. ``DATETIME_TZ_AWARE``
    records timezone-aware datetime storage. ``OTHER`` is the fallback for a
    dtype that does not belong to a named family.
    """

    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOATING = "floating"
    COMPLEX = "complex"
    STRING = "string"
    OBJECT = "object"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    DATETIME_TZ_AWARE = "datetime_tz_aware"
    TIMEDELTA = "timedelta"
    PERIOD = "period"
    INTERVAL = "interval"
    OTHER = "other"


@dataclass(frozen=True)
class PhysicalDtype:
    """Inspectable physical dtype of one column.

    ``dtype_name`` is the pandas display string captured at classification.
    ``categorical_ordered`` preserves ``CategoricalDtype.ordered`` because
    that flag is physical metadata and ``str(dtype)`` collapses it to
    ``category``. It is not an ordinal semantic inference.
    """

    family: PhysicalDtypeFamily
    dtype_name: str
    categorical_ordered: Optional[bool] = None

    def __post_init__(self) -> None:
        if not isinstance(self.family, PhysicalDtypeFamily):
            raise TypeError("family must be a PhysicalDtypeFamily")
        if not isinstance(self.dtype_name, str) or not self.dtype_name.strip():
            raise ValueError("dtype_name must be a non-empty string")
        if self.family is PhysicalDtypeFamily.CATEGORICAL:
            if not isinstance(self.categorical_ordered, bool):
                raise TypeError(
                    "categorical_ordered must be a bool for a categorical dtype"
                )
        elif self.categorical_ordered is not None:
            raise ValueError(
                "categorical_ordered is only set for a categorical dtype"
            )


def classify_physical_dtype(source: Any) -> PhysicalDtype:
    """Classify the physical dtype of a Series, a dtype, or a dtype alias.

    A Series is read only through ``.dtype``. Values, uniqueness, and
    missingness are not inspected. Extension dtypes that pandas identifies
    as a named family, such as nullable integers, use that family.
    Unrecognized extension dtypes fall back to ``PhysicalDtypeFamily.OTHER``.
    """
    dtype = _coerce_dtype(source)
    return PhysicalDtype(
        family=_family_of(dtype),
        dtype_name=str(dtype),
        categorical_ordered=_categorical_ordered(dtype),
    )


def _coerce_dtype(source: Any) -> Any:
    if isinstance(source, pd.Series):
        return source.dtype
    if isinstance(source, pd.DataFrame):
        raise TypeError(
            "classify_physical_dtype expects a dtype or a Series, not a DataFrame"
        )
    if isinstance(source, np.ndarray):
        raise TypeError(
            "classify_physical_dtype expects a dtype or a Series, not an ndarray"
        )
    if isinstance(source, (np.dtype, pd.api.extensions.ExtensionDtype)):
        return source
    if isinstance(source, str):
        try:
            return pd.api.types.pandas_dtype(source)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"unknown dtype alias: {source!r}") from exc
    raise TypeError(
        "classify_physical_dtype expects a pandas or NumPy dtype, a dtype "
        "alias, or a Series"
    )


def _family_of(dtype: Any) -> PhysicalDtypeFamily:
    # Categorical, period, and interval are identified before numeric
    # predicates so their contents are not classified as the value family.
    if isinstance(dtype, pd.CategoricalDtype):
        return PhysicalDtypeFamily.CATEGORICAL
    if isinstance(dtype, pd.PeriodDtype):
        return PhysicalDtypeFamily.PERIOD
    if isinstance(dtype, pd.IntervalDtype):
        return PhysicalDtypeFamily.INTERVAL
    if isinstance(dtype, pd.DatetimeTZDtype):
        return PhysicalDtypeFamily.DATETIME_TZ_AWARE
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return PhysicalDtypeFamily.DATETIME
    if pd.api.types.is_timedelta64_dtype(dtype):
        return PhysicalDtypeFamily.TIMEDELTA
    if pd.api.types.is_bool_dtype(dtype):
        return PhysicalDtypeFamily.BOOLEAN
    if pd.api.types.is_complex_dtype(dtype):
        return PhysicalDtypeFamily.COMPLEX
    if pd.api.types.is_integer_dtype(dtype):
        return PhysicalDtypeFamily.INTEGER
    if pd.api.types.is_float_dtype(dtype):
        return PhysicalDtypeFamily.FLOATING
    if isinstance(dtype, pd.StringDtype):
        return PhysicalDtypeFamily.STRING
    # pandas 3 reports object dtype as a string dtype. Object storage is
    # still object, including when the values happen to be strings.
    if pd.api.types.is_object_dtype(dtype):
        return PhysicalDtypeFamily.OBJECT
    if pd.api.types.is_string_dtype(dtype):
        return PhysicalDtypeFamily.STRING
    return PhysicalDtypeFamily.OTHER


def _categorical_ordered(dtype: Any) -> Optional[bool]:
    if isinstance(dtype, pd.CategoricalDtype):
        return bool(dtype.ordered)
    return None
