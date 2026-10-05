"""Column-label equivalence and occurrence identity.

Physical position identifies a column inside one DataFrame. A label's
match key is the equivalence used when two labels should be treated as
the same label: across datasets, and wherever a stored label is compared
again. Occurrence counts labels that share a match key, from 1, in the
order of one column axis. Alignment pairs those occurrences across two
datasets. This module owns the key and the occurrence count. It does not
align datasets, and it does not rewrite a label.

The comparison result may keep only the retained form defined below.

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

import dataclasses
import datetime as datetime_module
import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict
from typing import Optional
from typing import Sequence
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


def retained_column_label_match_key(
    label: RetainedColumnLabel,
) -> Tuple[object, ...]:
    """Return the match key of a label that was already retained.

    A raw label uses :func:`column_label_match_key`. An unsupported
    label has no key.
    """
    if not isinstance(label, RetainedColumnLabel):
        raise TypeError("label must be a RetainedColumnLabel")
    if label.kind is ColumnLabelKind.UNSUPPORTED:
        raise TypeError("an unsupported label has no match key")
    return _match_key(label)


def observed_labels_equal(left: object, right: object) -> bool:
    """Whether two observed labels are the same label.

    The same object matches, including an unsupported label compared
    with itself. Otherwise two supported labels match by match key, so
    every float ``NaN`` matches, ``True`` does not match ``1``, and
    ``1`` matches ``1.0`` when the float is that integer exactly. An
    unsupported label does not match a different object through the
    match key. It can still match through guarded Python equality, which
    is how an incomparable object stays unequal and how a NumPy array
    stays unequal. Nothing is stringified.
    """
    if left is right:
        return True
    left_key = column_label_match_key(left)
    right_key = column_label_match_key(right)
    if left_key is not None or right_key is not None:
        return left_key is not None and left_key == right_key
    return _guarded_python_equal(left, right)


def labels_are_float_nan(left: object, right: object) -> bool:
    """Whether both values are float NaN, including a NumPy floating NaN.

    ``None``, ``pd.NA``, and ``pd.NaT`` are not float NaN. This is the
    NaN case used by checks that otherwise require the same Python type.
    """
    return _is_float_nan(left) and _is_float_nan(right)


@dataclass(frozen=True)
class ColumnLabelIdentity:
    """One label's retained form, match key, and occurrence in one order.

    ``occurrence`` counts labels that share ``match_key``, starting at 1.
    Both are ``None`` exactly when the label is unsupported.
    """

    retained: RetainedColumnLabel
    match_key: Optional[Tuple[object, ...]]
    occurrence: Optional[int]

    def __post_init__(self) -> None:
        if not isinstance(self.retained, RetainedColumnLabel):
            raise TypeError("retained must be a RetainedColumnLabel")
        if self.match_key is None:
            if self.occurrence is not None:
                raise ValueError("an unsupported label has no occurrence")
            if self.retained.kind is not ColumnLabelKind.UNSUPPORTED:
                raise ValueError("a retained label has a match key")
            return
        if type(self.match_key) is not tuple or len(self.match_key) < 1:
            raise TypeError("match_key must be a non-empty tuple")
        if type(self.occurrence) is not int or self.occurrence < 1:
            raise ValueError("occurrence must be a positive int")
        if self.retained.kind is ColumnLabelKind.UNSUPPORTED:
            raise ValueError("an unsupported label has no match key")


def identify_column_labels(
    labels: Sequence[object],
) -> Tuple[ColumnLabelIdentity, ...]:
    """Identify each label once, in the order given.

    One pass and a dict of match keys. Expected linear in the number of
    labels. Column values are not read, and the labels are not reordered
    or rewritten.
    """
    if isinstance(labels, (str, bytes)):
        raise TypeError("identify_column_labels expects a sequence of labels")
    counts: Dict[Tuple[object, ...], int] = {}
    identified = []
    for label in labels:
        retained = retain_column_label(label)
        if retained.kind is ColumnLabelKind.UNSUPPORTED:
            identified.append(
                ColumnLabelIdentity(
                    retained=retained,
                    match_key=None,
                    occurrence=None,
                )
            )
            continue
        key = _match_key(retained)
        counts[key] = counts.get(key, 0) + 1
        identified.append(
            ColumnLabelIdentity(
                retained=retained,
                match_key=key,
                occurrence=counts[key],
            )
        )
    return tuple(identified)


_COLUMN_LABEL_FIELDS = frozenset(
    {
        "label",
        "left_label",
        "right_label",
        "other_label",
        "target_label",
    }
)


def records_equal(left: object, right: object) -> bool:
    """Field equality, with column-label fields on the match key.

    Non-label fields use ordinary equality. A column-label field uses
    :func:`observed_labels_equal`, so a rebuilt record whose label is
    float ``NaN`` still matches. This does not compare different types.
    """
    if left is right:
        return True
    if type(left) is not type(right):
        return False
    if not dataclasses.is_dataclass(left) or isinstance(left, type):
        return False
    for field in dataclasses.fields(left):
        if not _field_equal(
            getattr(left, field.name),
            getattr(right, field.name),
            field.name,
        ):
            return False
    return True


def records_hash(record: object) -> int:
    """Hash consistent with :func:`records_equal` for column-label fields.

    A supported label is hashed by its match key, so every float ``NaN``
    shares one hash and ``1`` shares the hash of ``1.0``. Other fields
    use their ordinary hash.
    """
    if not dataclasses.is_dataclass(record) or isinstance(record, type):
        raise TypeError("records_hash expects a dataclass instance")
    hashed = []
    for field in dataclasses.fields(record):
        value = getattr(record, field.name)
        if field.name in _COLUMN_LABEL_FIELDS:
            hashed.append(_label_hash(value))
        else:
            hashed.append(value)
    return hash(tuple(hashed))


def install_column_label_equality(cls: type) -> type:
    """Use match-key equality for one frozen record's column-label fields.

    The generated equality compares a raw label with ``==``. Float
    ``NaN`` is not equal to itself under that test, so a rebuilt record
    does not match. The replacement keeps ordinary equality for every
    other field.
    """

    def __eq__(self: object, other: object) -> bool:
        if other.__class__ is not self.__class__:
            return NotImplemented  # type: ignore[return-value]
        return records_equal(self, other)

    def __hash__(self: object) -> int:
        return records_hash(self)

    setattr(cls, "__eq__", __eq__)
    setattr(cls, "__hash__", __hash__)
    return cls


def _guarded_python_equal(left: object, right: object) -> bool:
    try:
        equal = left == right
    except TypeError:
        return False
    if equal is True or equal is False:
        return equal
    if isinstance(equal, np.bool_):
        return bool(equal)
    return False


def _is_float_nan(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (float, np.floating)):
        return False
    return math.isnan(float(value))


def _field_equal(left: object, right: object, name: str) -> bool:
    if name in _COLUMN_LABEL_FIELDS:
        return observed_labels_equal(left, right)
    return _guarded_python_equal(left, right)


def _label_hash(label: object) -> int:
    key = column_label_match_key(label)
    if key is not None:
        return hash(key)
    return hash(label)


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
