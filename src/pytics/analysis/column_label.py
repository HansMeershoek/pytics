"""Cross-dataset identity for one column label.

Physical position identifies a column inside one DataFrame. Across two
DataFrames the label has to be matched as well. This module defines that
match and the value the comparison result may keep.

Boolean labels stay distinct from integers. ``True == 1`` is true in
Python, and that comparison must not align those labels. The same rule
applies to each element of a tuple label. ``1`` and ``1.0`` do align when
the float is that integer exactly, which is the same top-level numeric
equality target resolution already uses for a non-boolean label.

Float ``NaN`` labels align with each other. Python's ``==`` would not.
``None``, ``pd.NA``, and ``pd.NaT`` are three further labels, and none of
them aligns with float ``NaN``. Pandas may already have collapsed a label
before analysis sees it. A ``MultiIndex`` can store ``True`` as ``1``.
This module does not recover a value pandas did not keep.

A label is retained only as ``None``, a bool, an int, a finite float, a
string, bytes, a date or time, a timezone-aware or naive ``datetime``, a
``timedelta`` that survives an exact round trip, or a tuple of those. Any
other object, including a pandas interval or a user instance, is an
unsupported label. Unsupported labels are not matched and their objects
are not stored.
"""

from __future__ import annotations

import datetime as datetime_module
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd


class ColumnLabelKind(Enum):
    """What a retained column label is.

    ``UNSUPPORTED`` means the original object is not kept. It is not a
    stringified stand-in, and it does not match another unsupported label.
    """

    NONE = "none"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    FLOAT_NAN = "float_nan"
    PANDAS_NA = "pandas_na"
    PANDAS_NAT = "pandas_nat"
    STRING = "string"
    BYTES = "bytes"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    TIMEDELTA = "timedelta"
    TUPLE = "tuple"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class RetainedColumnLabel:
    """Source-independent form of one column label.

    ``value`` is ``None`` for missing-like kinds and for an unsupported
    label. A tuple value contains retained labels, not the original
    objects. ``-0.0`` is stored as ``0.0``.
    """

    kind: ColumnLabelKind
    value: object = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ColumnLabelKind):
            raise TypeError("kind must be a ColumnLabelKind")
        _require_value(self.kind, self.value)


def retain_column_label(label: object) -> RetainedColumnLabel:
    """Return the retained form of one column label.

    The original object is not returned when it is a pandas or NumPy
    container, a callable, or any other unsupported value.
    """
    retained = _retain(label)
    if retained is None:
        return RetainedColumnLabel(kind=ColumnLabelKind.UNSUPPORTED, value=None)
    return retained


def column_label_match_key(label: object) -> Optional[Tuple[object, ...]]:
    """Return the hashable identity used to align one label.

    ``None`` means the label is unsupported and must not be matched.
    Integer ``1`` and float ``1.0`` share a key. ``True`` does not.
    Every float ``NaN`` shares one key.
    """
    retained = retain_column_label(label)
    if retained.kind is ColumnLabelKind.UNSUPPORTED:
        return None
    return _match_key(retained)


def column_labels_equal(left: object, right: object) -> bool:
    """Return whether two labels align under the column-label contract.

    Unsupported labels are not equal, including a label compared with
    itself. Supported equality is the match key, not Python ``==``.
    """
    left_key = column_label_match_key(left)
    right_key = column_label_match_key(right)
    if left_key is None or right_key is None:
        return False
    return left_key == right_key


def _retain(label: object) -> Optional[RetainedColumnLabel]:
    if label is None:
        return RetainedColumnLabel(kind=ColumnLabelKind.NONE, value=None)
    if type(label) is tuple:
        elements = []
        for item in label:
            retained = _retain(item)
            if retained is None or retained.kind is ColumnLabelKind.UNSUPPORTED:
                return None
            elements.append(retained)
        return RetainedColumnLabel(
            kind=ColumnLabelKind.TUPLE,
            value=tuple(elements),
        )
    if type(label) is bool or isinstance(label, np.bool_):
        return RetainedColumnLabel(kind=ColumnLabelKind.BOOL, value=bool(label))
    if label is pd.NA:
        return RetainedColumnLabel(kind=ColumnLabelKind.PANDAS_NA, value=None)
    if label is pd.NaT:
        return RetainedColumnLabel(kind=ColumnLabelKind.PANDAS_NAT, value=None)
    if isinstance(label, pd.Timestamp):
        return _retain_timestamp(label)
    if isinstance(label, pd.Timedelta):
        return _retain_timedelta(label)
    if type(label) is datetime_module.datetime:
        return RetainedColumnLabel(kind=ColumnLabelKind.DATETIME, value=label)
    if type(label) is datetime_module.date:
        return RetainedColumnLabel(kind=ColumnLabelKind.DATE, value=label)
    if type(label) is datetime_module.time:
        return RetainedColumnLabel(kind=ColumnLabelKind.TIME, value=label)
    if isinstance(label, np.integer):
        return RetainedColumnLabel(kind=ColumnLabelKind.INT, value=int(label))
    if type(label) is int:
        return RetainedColumnLabel(kind=ColumnLabelKind.INT, value=label)
    if isinstance(label, np.floating):
        return _retain_float(float(label))
    if type(label) is float:
        return _retain_float(label)
    if type(label) is str:
        return RetainedColumnLabel(kind=ColumnLabelKind.STRING, value=label)
    if type(label) is bytes:
        return RetainedColumnLabel(kind=ColumnLabelKind.BYTES, value=label)
    return None


def _retain_float(value: float) -> RetainedColumnLabel:
    if math.isnan(value):
        return RetainedColumnLabel(kind=ColumnLabelKind.FLOAT_NAN, value=None)
    if not math.isfinite(value):
        return RetainedColumnLabel(kind=ColumnLabelKind.UNSUPPORTED, value=None)
    if value == 0.0:
        value = 0.0
    return RetainedColumnLabel(kind=ColumnLabelKind.FLOAT, value=value)


def _retain_timestamp(value: pd.Timestamp) -> Optional[RetainedColumnLabel]:
    if pd.isna(value):
        return RetainedColumnLabel(kind=ColumnLabelKind.PANDAS_NAT, value=None)
    try:
        converted = value.to_pydatetime()
    except (ValueError, OverflowError):
        return None
    if type(converted) is not datetime_module.datetime:
        return None
    try:
        round_trip = pd.Timestamp(converted)
    except (ValueError, OverflowError):
        return None
    if round_trip != value:
        return None
    return RetainedColumnLabel(kind=ColumnLabelKind.DATETIME, value=converted)


def _retain_timedelta(value: pd.Timedelta) -> Optional[RetainedColumnLabel]:
    if pd.isna(value):
        return RetainedColumnLabel(kind=ColumnLabelKind.PANDAS_NAT, value=None)
    try:
        converted = value.to_pytimedelta()
    except (ValueError, OverflowError):
        return None
    if type(converted) is not datetime_module.timedelta:
        return None
    try:
        round_trip = pd.Timedelta(converted)
    except (ValueError, OverflowError):
        return None
    if round_trip != value:
        return None
    return RetainedColumnLabel(kind=ColumnLabelKind.TIMEDELTA, value=converted)


def _match_key(retained: RetainedColumnLabel) -> Tuple[object, ...]:
    kind = retained.kind
    if kind is ColumnLabelKind.NONE:
        return ("none",)
    if kind is ColumnLabelKind.FLOAT_NAN:
        return ("float_nan",)
    if kind is ColumnLabelKind.PANDAS_NA:
        return ("pandas_na",)
    if kind is ColumnLabelKind.PANDAS_NAT:
        return ("pandas_nat",)
    if kind is ColumnLabelKind.BOOL:
        return ("bool", retained.value)
    if kind is ColumnLabelKind.INT:
        return ("number", retained.value)
    if kind is ColumnLabelKind.FLOAT:
        as_int = _exact_int(retained.value)
        if as_int is not None:
            return ("number", as_int)
        return ("float", retained.value)
    if kind is ColumnLabelKind.STRING:
        return ("str", retained.value)
    if kind is ColumnLabelKind.BYTES:
        return ("bytes", retained.value)
    if kind is ColumnLabelKind.DATE:
        return ("date", retained.value)
    if kind is ColumnLabelKind.TIME:
        return ("time", retained.value)
    if kind is ColumnLabelKind.DATETIME:
        return ("datetime", retained.value)
    if kind is ColumnLabelKind.TIMEDELTA:
        return ("timedelta", retained.value)
    if kind is ColumnLabelKind.TUPLE:
        return ("tuple", tuple(_match_key(item) for item in retained.value))
    raise TypeError("an unsupported label has no match key")


def _exact_int(value: object) -> Optional[int]:
    """Return the integer a finite float is, when that integer is exact."""
    if type(value) is not float or not math.isfinite(value):
        return None
    if not value.is_integer():
        return None
    as_int = int(value)
    if float(as_int) != value:
        return None
    return as_int


def _require_value(kind: ColumnLabelKind, value: object) -> None:
    empty = (
        ColumnLabelKind.NONE,
        ColumnLabelKind.FLOAT_NAN,
        ColumnLabelKind.PANDAS_NA,
        ColumnLabelKind.PANDAS_NAT,
        ColumnLabelKind.UNSUPPORTED,
    )
    if kind in empty:
        if value is not None:
            raise ValueError(f"{kind.value} label does not store a value")
        return
    if kind is ColumnLabelKind.BOOL:
        if type(value) is not bool:
            raise TypeError("bool label value must be a bool")
        return
    if kind is ColumnLabelKind.INT:
        if type(value) is not int:
            raise TypeError("int label value must be an int")
        return
    if kind is ColumnLabelKind.FLOAT:
        if type(value) is not float or not math.isfinite(value):
            raise TypeError("float label value must be a finite float")
        if value == 0.0 and math.copysign(1.0, value) < 0.0:
            raise ValueError("float label value must not be negative zero")
        return
    if kind is ColumnLabelKind.STRING:
        if type(value) is not str:
            raise TypeError("string label value must be a str")
        return
    if kind is ColumnLabelKind.BYTES:
        if type(value) is not bytes:
            raise TypeError("bytes label value must be bytes")
        return
    if kind is ColumnLabelKind.DATE:
        if type(value) is not datetime_module.date:
            raise TypeError("date label value must be a date")
        return
    if kind is ColumnLabelKind.TIME:
        if type(value) is not datetime_module.time:
            raise TypeError("time label value must be a time")
        return
    if kind is ColumnLabelKind.DATETIME:
        if type(value) is not datetime_module.datetime:
            raise TypeError("datetime label value must be a datetime")
        return
    if kind is ColumnLabelKind.TIMEDELTA:
        if type(value) is not datetime_module.timedelta:
            raise TypeError("timedelta label value must be a timedelta")
        return
    if kind is ColumnLabelKind.TUPLE:
        if type(value) is not tuple:
            raise TypeError("tuple label value must be a tuple")
        for item in value:
            if not isinstance(item, RetainedColumnLabel):
                raise TypeError("tuple label elements must be retained labels")
            if item.kind is ColumnLabelKind.UNSUPPORTED:
                raise ValueError("a tuple label cannot contain an unsupported element")
        return
    raise TypeError("column label kind is not recognized")
