"""Exact string-structure observations for one string-valued column.

The observations describe non-missing Python strings. They do not decide
whether those strings are Text, Categorical, Identifier, or any other
semantic role, and they do not recognize patterns such as UUID, email, or
URL.

A physical string dtype is eligible, including an all-missing string
column: the dtype itself is positive evidence that the values are strings.
An object column is eligible only when every non-missing value is a
Python ``str``. An empty or all-missing object column has no such value,
so it is not eligible. Physical categorical storage is not eligible, even
when its labels are strings.

Missingness is pandas missingness. ``""``, whitespace, and literals such
as ``"NA"`` stay ordinary strings. Character classes use Python's Unicode
string methods. Length is ``len`` of the original string. Nothing is
normalized, stripped, or coerced.

Collection is exact, full-column, and unsampled. It runs only when
requested. The Empty, Constant, and physical-type precedence chain does
not collect it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional

import pandas as pd

from pytics.semantics.column_evidence import AnalyticalInapplicability
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily

_APPLICABILITY_ERROR = (
    "string structure evidence applies only to a physical string dtype "
    "or to an object Series whose every non-missing value is a Python str"
)

_COUNT_FIELDS = (
    "empty_string_count",
    "whitespace_only_count",
    "contains_whitespace_count",
    "contains_alpha_count",
    "contains_digit_count",
    "contains_other_count",
)


@dataclass(frozen=True)
class StringStructureEvidence:
    """Immutable string-structure facts for one Series.

    ``basic`` is the universal evidence these facts were collected with.
    ``n_total``, ``n_missing``, ``n_non_missing``, and
    ``n_unique_non_missing`` stay on that object. They are not copied.

    The six counts are stored. A count is never ``None``. Ratios are read
    from those counts and from ``basic.n_non_missing``. An undefined ratio
    is ``None``.

    ``min_length`` and ``max_length`` are ``None`` when there is no
    non-missing string. They are integers when there is at least one. An
    observed empty string has length 0, so a defined ``min_length`` may be
    0. That is not the same as an undefined bound.

    A string may contribute to more than one content count. Those counts
    are not a partition of ``n_non_missing``.
    """

    basic: BasicColumnEvidence
    empty_string_count: int
    whitespace_only_count: int
    contains_whitespace_count: int
    contains_alpha_count: int
    contains_digit_count: int
    contains_other_count: int
    min_length: Optional[int]
    max_length: Optional[int]

    def __post_init__(self) -> None:
        if not isinstance(self.basic, BasicColumnEvidence):
            raise TypeError("basic must be BasicColumnEvidence")
        for field in _COUNT_FIELDS:
            _require_count(getattr(self, field), field)
        _require_counts_within_population(self)
        _require_lengths(self)

    @property
    def empty_string_ratio(self) -> Optional[float]:
        """Empty strings divided by non-missing observations.

        The denominator is ``BasicColumnEvidence.n_non_missing``. ``None``
        when that count is zero.
        """
        return _ratio(self.empty_string_count, self.basic.n_non_missing)

    @property
    def whitespace_only_ratio(self) -> Optional[float]:
        """Whitespace-only strings divided by non-missing observations.

        ``None`` when ``n_non_missing`` is zero. The empty string is not
        whitespace-only.
        """
        return _ratio(self.whitespace_only_count, self.basic.n_non_missing)

    @property
    def contains_whitespace_ratio(self) -> Optional[float]:
        """Strings containing whitespace, divided by non-missing observations.

        ``None`` when ``n_non_missing`` is zero. A whitespace-only string
        also contains whitespace.
        """
        return _ratio(self.contains_whitespace_count, self.basic.n_non_missing)

    @property
    def contains_alpha_ratio(self) -> Optional[float]:
        """Strings containing an alphabetic character, over non-missing ones.

        ``None`` when ``n_non_missing`` is zero. Alphabetic uses
        ``str.isalpha``, including non-ASCII letters.
        """
        return _ratio(self.contains_alpha_count, self.basic.n_non_missing)

    @property
    def contains_digit_ratio(self) -> Optional[float]:
        """Strings containing a digit, divided by non-missing observations.

        ``None`` when ``n_non_missing`` is zero. Digit uses ``str.isdigit``,
        including non-ASCII digits.
        """
        return _ratio(self.contains_digit_count, self.basic.n_non_missing)

    @property
    def contains_other_ratio(self) -> Optional[float]:
        """Strings containing another character, over non-missing observations.

        ``None`` when ``n_non_missing`` is zero. Other means a character
        that is not alphabetic, not a digit, and not whitespace.
        """
        return _ratio(self.contains_other_count, self.basic.n_non_missing)


def collect_string_structure_evidence(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> StringStructureEvidence:
    """Collect exact string-structure facts from evidence already in hand.

    ``basic`` supplies the universal counts. This function does not collect
    them again and does not classify the physical dtype again. ``physical``
    must already describe this Series. The Series is not modified.

    One drop of pandas-missing values produces the non-missing population.
    Object eligibility then requires every remaining value to be a Python
    ``str``, including subclasses such as ``numpy.str_``. ``bytes`` are not
    strings and are not decoded. There is no second scan for frequencies,
    no sampling, and no string coercion. An ineligible Series raises
    ``AnalyticalInapplicability``. Counts that disagree with ``basic``
    raise ``ValueError``. An unexpected ``TypeError`` still propagates.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_string_structure_evidence expects a pandas Series")
    if not isinstance(basic, BasicColumnEvidence):
        raise TypeError("basic must be BasicColumnEvidence")
    if not isinstance(physical, PhysicalDtype):
        raise TypeError("physical must be a PhysicalDtype")
    _require_applicable_family(physical)
    if str(series.dtype) != physical.dtype_name:
        raise ValueError("physical dtype does not match the Series")
    observed = _non_missing_values(series, basic)
    if physical.family is PhysicalDtypeFamily.OBJECT and len(observed) == 0:
        # No non-missing value means there is no positive evidence that the
        # object column holds strings. Absence of a contradiction is not
        # enough.
        raise AnalyticalInapplicability(_APPLICABILITY_ERROR)
    return _evidence_from_values(basic, observed)


def _require_applicable_family(physical: PhysicalDtype) -> None:
    """Reject storage that is not a string dtype or an object dtype.

    Categorical labels are not inspected. Boolean, numeric, datetime,
    timedelta, period, and the other families are not coerced into strings.
    """
    if physical.family not in (
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    ):
        raise AnalyticalInapplicability(_APPLICABILITY_ERROR)


def _non_missing_values(
    series: pd.Series,
    basic: BasicColumnEvidence,
) -> pd.Series:
    """Return non-missing values in row order, without changing the source.

    The length check ties this population to the supplied basic counts.
    It does not recompute distinct counts.
    """
    observed = series.dropna()
    if len(series) != basic.n_total or len(observed) != basic.n_non_missing:
        raise ValueError(
            "string observations do not match BasicColumnEvidence "
            "n_total and n_non_missing"
        )
    return observed


def _evidence_from_values(
    basic: BasicColumnEvidence,
    observed: pd.Series,
) -> StringStructureEvidence:
    """Derive every stored fact from one pass over non-missing values.

    Each value must already be a Python ``str``. ``isinstance(value, str)``
    accepts subclasses. It does not accept ``bytes``. The original string
    is not stripped, case-folded, or Unicode-normalized. Empty, whitespace,
    alphabetic, digit, and other are recorded together so the same string
    can contribute to several counts.
    """
    empty_string_count = 0
    whitespace_only_count = 0
    contains_whitespace_count = 0
    contains_alpha_count = 0
    contains_digit_count = 0
    contains_other_count = 0
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    for value in observed:
        if not isinstance(value, str):
            raise AnalyticalInapplicability(_APPLICABILITY_ERROR)
        (
            is_empty,
            is_whitespace_only,
            contains_whitespace,
            contains_alpha,
            contains_digit,
            contains_other,
            length,
        ) = _observe_string(value)
        empty_string_count += is_empty
        whitespace_only_count += is_whitespace_only
        contains_whitespace_count += contains_whitespace
        contains_alpha_count += contains_alpha
        contains_digit_count += contains_digit
        contains_other_count += contains_other
        if min_length is None or length < min_length:
            min_length = length
        if max_length is None or length > max_length:
            max_length = length
    return StringStructureEvidence(
        basic=basic,
        empty_string_count=empty_string_count,
        whitespace_only_count=whitespace_only_count,
        contains_whitespace_count=contains_whitespace_count,
        contains_alpha_count=contains_alpha_count,
        contains_digit_count=contains_digit_count,
        contains_other_count=contains_other_count,
        min_length=min_length,
        max_length=max_length,
    )


def _observe_string(
    value: str,
) -> tuple[int, int, int, int, int, int, int]:
    """Return six 0/1 flags and ``len(value)`` for one original string.

    The flags are empty, whitespace-only, contains whitespace, contains
    alphabetic, contains digit, and contains other. ``""`` is empty.
    ``str.isspace`` decides whitespace-only, so the empty string is not
    included. A character is other when it is not alphabetic, not a digit,
    and not whitespace. Classes are not treated as exclusive: one character
    that satisfied more than one positive class would count for each.
    """
    contains_whitespace = False
    contains_alpha = False
    contains_digit = False
    contains_other = False
    for character in value:
        if character.isspace():
            contains_whitespace = True
        if character.isalpha():
            contains_alpha = True
        if character.isdigit():
            contains_digit = True
        if (
            not character.isalpha()
            and not character.isdigit()
            and not character.isspace()
        ):
            contains_other = True
    return (
        1 if value == "" else 0,
        1 if value.isspace() else 0,
        1 if contains_whitespace else 0,
        1 if contains_alpha else 0,
        1 if contains_digit else 0,
        1 if contains_other else 0,
        len(value),
    )


def _ratio(count: int, denominator: int) -> Optional[float]:
    """Divide by the non-missing population, or return ``None`` when it is 0.

    A zero numerator with a positive denominator is ``0.0``. An undefined
    ratio is not ``0.0``, ``1.0``, NaN, or infinity.
    """
    if denominator == 0:
        return None
    return count / denominator


def _require_count(value: Any, field: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be an int")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")


def _require_counts_within_population(evidence: StringStructureEvidence) -> None:
    """Keep each count inside the non-missing population.

    Content counts may overlap, so their sum may exceed ``n_non_missing``.
    A whitespace-only string also contains whitespace, and the empty string
    is not whitespace-only.
    """
    non_missing = evidence.basic.n_non_missing
    for field in _COUNT_FIELDS:
        if getattr(evidence, field) > non_missing:
            raise ValueError(f"{field} cannot exceed n_non_missing")
    if evidence.whitespace_only_count > evidence.contains_whitespace_count:
        raise ValueError("whitespace-only strings also contain whitespace")
    if evidence.empty_string_count + evidence.whitespace_only_count > non_missing:
        raise ValueError("empty and whitespace-only strings cannot overlap")


def _require_lengths(evidence: StringStructureEvidence) -> None:
    """Check length bounds against the non-missing population.

    No non-missing string leaves both bounds undefined. A stored 0 would
    claim that an empty string was observed. An observed empty string
    forces the minimum to 0, and a minimum of 0 requires one.
    """
    minimum = evidence.min_length
    maximum = evidence.max_length
    if evidence.basic.n_non_missing == 0:
        if minimum is not None or maximum is not None:
            raise ValueError(
                "min_length and max_length are undefined when n_non_missing is 0"
            )
        return
    if type(minimum) is not int or type(maximum) is not int:
        raise TypeError("min_length and max_length must be ints when n_non_missing > 0")
    if minimum < 0 or maximum < 0:
        raise ValueError("string lengths must be >= 0")
    if minimum > maximum:
        raise ValueError("min_length cannot exceed max_length")
    if evidence.empty_string_count > 0 and minimum != 0:
        raise ValueError("an empty string requires min_length == 0")
    if minimum == 0 and evidence.empty_string_count == 0:
        raise ValueError("min_length 0 requires an empty string")
