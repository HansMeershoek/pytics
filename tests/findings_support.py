"""Shared helpers for the TSK-040 findings tests."""

from __future__ import annotations

import dataclasses
import datetime as datetime_module
from enum import Enum
from fractions import Fraction
from typing import Sequence

import numpy as np
import pandas as pd

_ALLOWED_SCALARS = (
    type(None),
    bool,
    int,
    float,
    str,
    bytes,
    Fraction,
    datetime_module.date,
    datetime_module.time,
    datetime_module.timedelta,
)


def with_labels(columns: Sequence[object], labels: Sequence[object]) -> pd.DataFrame:
    """Build a frame whose column labels are exactly the objects passed."""
    stored = np.empty(len(labels), dtype=object)
    for index, label in enumerate(labels):
        stored[index] = label
    frame = pd.DataFrame({index: values for index, values in enumerate(columns)})
    frame.columns = stored
    return frame


def assert_source_free(value: object) -> None:
    """Only frozen dataclasses, tuples, enums, and plain scalars are retained."""
    seen = set()

    def walk(item: object) -> None:
        if id(item) in seen:
            return
        seen.add(id(item))
        if isinstance(
            item, (pd.DataFrame, pd.Series, pd.Index, np.ndarray, np.generic)
        ):
            raise AssertionError(f"retained a pandas or NumPy object: {type(item)}")
        if isinstance(item, (pd.Timestamp, pd.Timedelta, pd.Categorical)):
            raise AssertionError(f"retained a pandas scalar: {type(item)}")
        if item is pd.NA or item is pd.NaT:
            raise AssertionError("retained a pandas missing singleton")
        if isinstance(item, (dict, list, set)):
            raise AssertionError(f"retained a mutable container: {type(item)}")
        if isinstance(item, Enum):
            return
        if isinstance(item, tuple):
            for child in item:
                walk(child)
            return
        if dataclasses.is_dataclass(item) and not isinstance(item, type):
            if not type(item).__dataclass_params__.frozen:
                raise AssertionError(f"retained a mutable dataclass: {type(item)}")
            for field in dataclasses.fields(item):
                walk(getattr(item, field.name))
            return
        if callable(item):
            raise AssertionError(f"retained a callable: {type(item)}")
        if type(item) in _ALLOWED_SCALARS or isinstance(item, datetime_module.date):
            return
        raise AssertionError(f"unexpected retained object: {type(item)!r}")

    walk(value)
