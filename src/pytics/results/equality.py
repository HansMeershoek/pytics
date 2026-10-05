"""Label-aware equality for a public result.

Generated dataclass equality uses ``==`` for a raw column label. Float
``NaN`` is not equal to itself under that test, so two analyses of the
same labeled frame can compare unequal. Public results do not use that
test. They walk the retained fields and compare column-label fields with
the match key from :mod:`pytics.analysis.column_label`.

This walk does not replace equality on the internal records. A public
result is not hashed: the graph is large, and a hash would have to
follow the same label rule for every nested field.
"""

from __future__ import annotations

import dataclasses
import math
from enum import Enum
from typing import Optional

from pytics.analysis.column_label import observed_labels_equal

# Field names that store a raw column label. Retained labels are a
# different type and compare by their own fields. Keep this set the same
# as the one column-label equality uses.
LABEL_FIELDS = frozenset(
    {
        "label",
        "left_label",
        "right_label",
        "other_label",
        "target_label",
    }
)


def content_equal(left: object, right: object) -> bool:
    """Whether two retained values are the same analytical content."""
    return _equal(left, right, None)


def _equal(left: object, right: object, field_name: Optional[str]) -> bool:
    if field_name in LABEL_FIELDS:
        return observed_labels_equal(left, right)
    if left is right:
        return True
    if type(left) is not type(right):
        return False
    if isinstance(left, float):
        if math.isnan(left) and math.isnan(right):
            return True
        return bool(left == right)
    if isinstance(left, Enum):
        return left is right
    if dataclasses.is_dataclass(left) and not isinstance(left, type):
        for field in dataclasses.fields(left):
            if not _equal(
                getattr(left, field.name),
                getattr(right, field.name),
                field.name,
            ):
                return False
        return True
    if isinstance(left, tuple):
        if len(left) != len(right):
            return False
        for left_item, right_item in zip(left, right):
            if not _equal(left_item, right_item, None):
                return False
        return True
    return left == right
