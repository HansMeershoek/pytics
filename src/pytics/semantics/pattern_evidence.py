"""Exact full-value pattern observations for one string-valued column.

A pattern count records that an observed string satisfies an explicit
syntax. It does not decide what the value or the column semantically
represents. UUID syntax is not an Identifier reading. IPv4 syntax is not
a network role. A fixed-width hexadecimal token is not a hash algorithm.

The population is the non-missing strings already accepted by
``StringStructureEvidence``. This module does not decide that eligibility
again and does not recollect string structure, basic counts, or
frequencies. Missing values stay missing. ``""``, whitespace, and literals
such as ``"NA"`` stay ordinary strings and simply fail these patterns.

Each pattern is a full-value match against the original string. Nothing is
stripped, case-folded, Unicode-normalized, stringified, or decoded.
Surrounding text does not match. The hexadecimal token alphabet is ASCII,
``0123456789abcdefABCDEF``. That is narrower than the Unicode character
classes used by string-structure evidence.

Counts may overlap. A compact UUID is also 32 hexadecimal characters, and
both counts increment. There is no best pattern and no winner.

Collection is exact, full-column, and unsampled. It runs only when
requested. The Empty, Constant, and physical-type precedence chain does
not collect it, and collecting string structure does not collect it either.
"""

from __future__ import annotations

import ipaddress
import uuid
from dataclasses import dataclass
from typing import Any
from typing import Optional

import pandas as pd

from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.string_structure_evidence import StringStructureEvidence

_APPLICABILITY_ERROR = (
    "pattern evidence applies only to non-missing Python strings from a "
    "population already accepted by string-structure evidence"
)

_ASCII_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_HEX_TOKEN_WIDTHS = (32, 40, 64, 128)
_COUNT_FIELDS = (
    "uuid_count",
    "ipv4_count",
    "ipv6_count",
    "hex_32_count",
    "hex_40_count",
    "hex_64_count",
    "hex_128_count",
)


@dataclass(frozen=True)
class PatternEvidence:
    """Immutable full-value pattern counts for one string Series.

    ``string_structure`` is the string-structure evidence these counts were
    collected with. Basic counts stay on that object. They are not copied.

    The seven counts are stored. A count is never ``None``. The same string
    may increment more than one count. Ratios are read from those counts
    and from ``string_structure.basic.n_non_missing``. An undefined ratio
    is ``None``.

    No matched strings are retained. A ratio is an observed proportion,
    not a semantic conclusion.
    """

    string_structure: StringStructureEvidence
    uuid_count: int
    ipv4_count: int
    ipv6_count: int
    hex_32_count: int
    hex_40_count: int
    hex_64_count: int
    hex_128_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.string_structure, StringStructureEvidence):
            raise TypeError("string_structure must be StringStructureEvidence")
        for field in _COUNT_FIELDS:
            _require_count(getattr(self, field), field)
        _require_counts_within_population(self)

    @property
    def uuid_ratio(self) -> Optional[float]:
        """UUID syntax matches divided by non-missing strings.

        The denominator is ``StringStructureEvidence.basic.n_non_missing``.
        ``None`` when that count is zero. This is not an Identifier rule.
        """
        return _ratio(self.uuid_count, self.string_structure.basic.n_non_missing)

    @property
    def ipv4_ratio(self) -> Optional[float]:
        """IPv4 syntax matches divided by non-missing strings.

        ``None`` when ``n_non_missing`` is zero.
        """
        return _ratio(self.ipv4_count, self.string_structure.basic.n_non_missing)

    @property
    def ipv6_ratio(self) -> Optional[float]:
        """IPv6 syntax matches divided by non-missing strings.

        ``None`` when ``n_non_missing`` is zero.
        """
        return _ratio(self.ipv6_count, self.string_structure.basic.n_non_missing)

    @property
    def hex_32_ratio(self) -> Optional[float]:
        """32-character ASCII hexadecimal tokens over non-missing strings.

        ``None`` when ``n_non_missing`` is zero. The width is not an MD5
        reading, and the ratio is not an Identifier rule.
        """
        return _ratio(self.hex_32_count, self.string_structure.basic.n_non_missing)

    @property
    def hex_40_ratio(self) -> Optional[float]:
        """40-character ASCII hexadecimal tokens over non-missing strings.

        ``None`` when ``n_non_missing`` is zero.
        """
        return _ratio(self.hex_40_count, self.string_structure.basic.n_non_missing)

    @property
    def hex_64_ratio(self) -> Optional[float]:
        """64-character ASCII hexadecimal tokens over non-missing strings.

        ``None`` when ``n_non_missing`` is zero.
        """
        return _ratio(self.hex_64_count, self.string_structure.basic.n_non_missing)

    @property
    def hex_128_ratio(self) -> Optional[float]:
        """128-character ASCII hexadecimal tokens over non-missing strings.

        ``None`` when ``n_non_missing`` is zero.
        """
        return _ratio(self.hex_128_count, self.string_structure.basic.n_non_missing)


def collect_pattern_evidence(
    series: pd.Series,
    string_structure: StringStructureEvidence,
    physical: PhysicalDtype,
) -> PatternEvidence:
    """Collect exact pattern counts from evidence already in hand.

    ``string_structure`` supplies the string population's basic evidence.
    This function does not collect string structure, basic counts, or
    frequencies, and it does not classify the physical dtype again.
    ``physical`` must already describe this Series. The Series is not
    modified.

    One drop of pandas-missing values produces the non-missing population.
    Each remaining value must be a Python ``str``, including subclasses.
    ``bytes`` are not strings and are not decoded. An ineligible population
    raises ``TypeError``. Counts that disagree with the composed basic
    evidence raise ``ValueError``.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_pattern_evidence expects a pandas Series")
    if not isinstance(string_structure, StringStructureEvidence):
        raise TypeError("string_structure must be StringStructureEvidence")
    if not isinstance(physical, PhysicalDtype):
        raise TypeError("physical must be a PhysicalDtype")
    _require_pattern_family(physical)
    if str(series.dtype) != physical.dtype_name:
        raise ValueError("physical dtype does not match the Series")
    observed = _non_missing_values(series, string_structure)
    if physical.family is PhysicalDtypeFamily.OBJECT and len(observed) == 0:
        # No non-missing value means string-structure evidence cannot
        # describe this object column. Do not treat that absence as a
        # string population.
        raise TypeError(_APPLICABILITY_ERROR)
    return _evidence_from_values(string_structure, observed)


def _require_pattern_family(physical: PhysicalDtype) -> None:
    """Reject storage that string-structure evidence cannot describe.

    This is a consistency guard for the supplied physical dtype. It does
    not classify the Series and does not recompute string structure.
    """
    if physical.family not in (
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    ):
        raise TypeError(_APPLICABILITY_ERROR)


def _non_missing_values(
    series: pd.Series,
    string_structure: StringStructureEvidence,
) -> pd.Series:
    """Return non-missing values in row order, without changing the source.

    The length check ties this population to the composed basic counts.
    It does not recompute distinct counts or string-structure facts.
    """
    basic = string_structure.basic
    observed = series.dropna()
    if len(series) != basic.n_total or len(observed) != basic.n_non_missing:
        raise ValueError(
            "pattern observations do not match BasicColumnEvidence "
            "n_total and n_non_missing"
        )
    return observed


def _evidence_from_values(
    string_structure: StringStructureEvidence,
    observed: pd.Series,
) -> PatternEvidence:
    """Count every pattern from the non-missing strings.

    Each value must already be a Python ``str``. The original string is
    tested once. Patterns are not exclusive: one string may increment
    more than one count. No match list is retained.

    When the known distinct count is at most half the non-missing
    count, each exact string is classified once and weighted by its
    occurrences. That table is not retained. Otherwise each value is read.
    """
    basic = string_structure.basic
    if _repeated_enough(basic.n_unique_non_missing, basic.n_non_missing):
        return _weighted_pattern(string_structure, observed)
    uuid_count = 0
    ipv4_count = 0
    ipv6_count = 0
    hex_32_count = 0
    hex_40_count = 0
    hex_64_count = 0
    hex_128_count = 0
    for value in observed:
        if not isinstance(value, str):
            raise TypeError(_APPLICABILITY_ERROR)
        if _is_uuid_syntax(value):
            uuid_count += 1
        if _is_ipv4_syntax(value):
            ipv4_count += 1
        if _is_ipv6_syntax(value):
            ipv6_count += 1
        width = _fixed_hex_width(value)
        if width == 32:
            hex_32_count += 1
        elif width == 40:
            hex_40_count += 1
        elif width == 64:
            hex_64_count += 1
        elif width == 128:
            hex_128_count += 1
    return PatternEvidence(
        string_structure=string_structure,
        uuid_count=uuid_count,
        ipv4_count=ipv4_count,
        ipv6_count=ipv6_count,
        hex_32_count=hex_32_count,
        hex_40_count=hex_40_count,
        hex_64_count=hex_64_count,
        hex_128_count=hex_128_count,
    )


def _repeated_enough(n_unique: Optional[int], n_non_missing: int) -> bool:
    """Internal performance gate. Not a semantic threshold."""
    if type(n_unique) is not int:
        return False
    return n_unique * 2 <= n_non_missing


def _exact_string_counts(observed: pd.Series) -> dict[str, int]:
    """Count strings after ``isinstance``. A non-string is not hashed."""
    counts: dict[str, int] = {}
    for value in observed:
        if not isinstance(value, str):
            raise TypeError(_APPLICABILITY_ERROR)
        seen = counts.get(value)
        if seen is None:
            counts[value] = 1
        else:
            counts[value] = seen + 1
    return counts


def _weighted_pattern(
    string_structure: StringStructureEvidence,
    observed: pd.Series,
) -> PatternEvidence:
    """Classify each exact string once and weight each pattern by its count."""
    counts = _exact_string_counts(observed)
    uuid_count = 0
    ipv4_count = 0
    ipv6_count = 0
    hex_32_count = 0
    hex_40_count = 0
    hex_64_count = 0
    hex_128_count = 0
    for value, weight in counts.items():
        if _is_uuid_syntax(value):
            uuid_count += weight
        if _is_ipv4_syntax(value):
            ipv4_count += weight
        if _is_ipv6_syntax(value):
            ipv6_count += weight
        width = _fixed_hex_width(value)
        if width == 32:
            hex_32_count += weight
        elif width == 40:
            hex_40_count += weight
        elif width == 64:
            hex_64_count += weight
        elif width == 128:
            hex_128_count += weight
    return PatternEvidence(
        string_structure=string_structure,
        uuid_count=uuid_count,
        ipv4_count=ipv4_count,
        ipv6_count=ipv6_count,
        hex_32_count=hex_32_count,
        hex_40_count=hex_40_count,
        hex_64_count=hex_64_count,
        hex_128_count=hex_128_count,
    )


def _is_uuid_syntax(value: str) -> bool:
    """Return whether ``value`` has the explicit UUID textual shape.

    The accepted forms are 36-character hyphenated hexadecimal text and
    32-character hexadecimal text. ``uuid.UUID`` also accepts braces, a
    ``urn:uuid:`` prefix, and misplaced hyphens. Those forms are not this
    contract, so the shape is required first. The parser then confirms the
    hexadecimal body. It is not asked for a version or a variant, and it
    is not allowed to widen the shape.
    """
    if not _has_explicit_uuid_shape(value):
        return False
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def _has_explicit_uuid_shape(value: str) -> bool:
    """Return whether ``value`` is exactly one of the two UUID spellings.

    Hexadecimal characters are the ASCII set used by the token patterns.
    Hyphens are required only in the canonical positions.
    """
    if len(value) == 32:
        return _is_ascii_hex(value)
    if len(value) != 36:
        return False
    if value[8] != "-" or value[13] != "-" or value[18] != "-" or value[23] != "-":
        return False
    return (
        _is_ascii_hex(value[0:8])
        and _is_ascii_hex(value[9:13])
        and _is_ascii_hex(value[14:18])
        and _is_ascii_hex(value[19:23])
        and _is_ascii_hex(value[24:36])
    )


def _is_ipv4_syntax(value: str) -> bool:
    """Return whether the entire original string is an IPv4 address.

    ``ipaddress.IPv4Address`` is the validator. A string without exactly
    three dots cannot be that syntax, so it is not submitted to the
    parser. The string is not stripped or rewritten first. Network
    syntax, including a CIDR suffix, is not an address match. Address
    properties are not classified.
    """
    if value.count(".") != 3:
        return False
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        return False
    return True


def _is_ipv6_syntax(value: str) -> bool:
    """Return whether the entire original string is an IPv6 address.

    ``ipaddress.IPv6Address`` is the validator, including the compressed
    and expanded spellings it accepts. A string with fewer than two
    colons cannot be that syntax, so it is not submitted to the parser.
    The string is not canonicalized, and a successful parse is not
    compared back to a normalized form. Network syntax is not an address
    match. Address properties are not classified.
    """
    if value.count(":") < 2:
        return False
    try:
        ipaddress.IPv6Address(value)
    except ValueError:
        return False
    return True


def matches_identifier_syntax(value: str) -> bool:
    """Return whether ``value`` is UUID syntax or one hexadecimal width.

    This is the same full-value test the Identifier counts use. It does
    not decide that a column is an Identifier, and it does not retain
    ``value``.
    """
    return _is_uuid_syntax(value) or _fixed_hex_width(value) is not None


def _fixed_hex_width(value: str) -> Optional[int]:
    """Return 32, 40, 64, or 128 when ``value`` is ASCII hexadecimal.

    Any other length returns ``None`` without inspecting characters. A
    character outside ``0123456789abcdefABCDEF`` returns ``None``. Unicode
    digits are not hexadecimal here. The returned width is not a hash
    algorithm name.
    """
    if len(value) not in _HEX_TOKEN_WIDTHS:
        return None
    if not _is_ascii_hex(value):
        return None
    return len(value)


def _is_ascii_hex(value: str) -> bool:
    """Return whether every character is an ASCII hexadecimal digit.

    An empty string has no failing character. Callers still require one of
    the explicit UUID or token lengths, so an empty string does not match.
    """
    for character in value:
        if character not in _ASCII_HEX_DIGITS:
            return False
    return True


def _ratio(count: int, denominator: int) -> Optional[float]:
    """Divide by the non-missing string population, or return ``None``.

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


def _require_counts_within_population(evidence: PatternEvidence) -> None:
    """Keep each count inside the non-missing string population.

    Patterns may overlap, so the counts are not a partition and their sum
    may exceed ``n_non_missing``. A compact UUID is also a 32-character
    hexadecimal token. That overlap is not rejected.
    """
    non_missing = evidence.string_structure.basic.n_non_missing
    for field in _COUNT_FIELDS:
        if getattr(evidence, field) > non_missing:
            raise ValueError(f"{field} cannot exceed n_non_missing")
