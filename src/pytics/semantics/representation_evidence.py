"""Exact representation-family counts for one string-valued column.

A count records that an original string has a shape. It does not convert
that string, and it does not select a semantic type. A date-shaped string
stays a string. A currency-shaped string is not a parsed amount. A
missing-like literal stays a literal and is not a pandas missing value.

The families are a partition of the non-missing strings. Each string
increments one count. Blank is the same population as the empty-string
count plus the whitespace-only count already stored on string structure.
Identity syntax is the same full-value test pattern evidence uses for
UUID text and the supported hexadecimal widths. This module does not
store a second UUID count or a second hexadecimal count.

Nothing is stripped, case-folded, or rewritten in the Series. A
case-folded copy is used only to recognize a closed literal list, a
month token, a quarter token, or a currency code. Derived evidence stays
on this object.

Collection is exact, full-column, and unsampled. It runs only when
requested. The precedence chain does not collect it. No raw value is
retained.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Optional
from typing import Tuple

import pandas as pd

from pytics.semantics.pattern_evidence import matches_identifier_syntax
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.string_structure_evidence import StringStructureEvidence

_APPLICABILITY_ERROR = (
    "representation evidence applies only to non-missing Python strings "
    "from a population already accepted by string-structure evidence"
)

# A short label may contain this many alphanumeric tokens. Four covers an
# ordinary multi-word label. It is not a general cardinality threshold.
MAX_LABEL_TOKENS = 4

# A short label may be this long, in characters of the original string.
# A longer string is not this shape. The bound is not a Text cutoff.
MAX_LABEL_LENGTH = 40

# Prose is a letter-bearing string with at least this many tokens. A
# single long token is not prose. The bound does not select Text.
PROSE_MIN_TOKENS = 6

# A conceptual group is material when it covers at least this many
# strings and at least 1/20 of the non-missing population. The pair
# describes mixture. It does not select a semantic type.
MATERIAL_MIN_COUNT = 2
MATERIAL_PROPORTION_DENOMINATOR = 20

_LABEL_PUNCTUATION = frozenset("&'.,()")
_CURRENCY_CHARS = frozenset("€£$¥")
_CURRENCY_CODES = frozenset({"usd", "eur", "gbp"})
_MISSING_LITERALS = frozenset(
    {"unknown", "n/a", "na", "none", "null", "missing"}
)
_MONTHS = frozenset(
    {
        "jan",
        "january",
        "feb",
        "february",
        "mar",
        "march",
        "apr",
        "april",
        "may",
        "jun",
        "june",
        "jul",
        "july",
        "aug",
        "august",
        "sep",
        "sept",
        "september",
        "oct",
        "october",
        "nov",
        "november",
        "dec",
        "december",
    }
)
_IDENTITY_LENGTHS = frozenset({32, 36, 40, 64, 128})
_MAGNITUDE_SUFFIXES = frozenset("kKmMbB")


class RepresentationFamily(Enum):
    """One mutually exclusive shape for an original string.

    The value is a stable token. It is not a semantic type, not a
    cleaned value, and not a column name.
    """

    BLANK = "blank"
    PADDED = "padded"
    MISSING_LIKE = "missing_like"
    EMAIL_LIKE = "email_like"
    URL_LIKE = "url_like"
    TEMPORAL_LIKE = "temporal_like"
    QUARTER_YEAR_LIKE = "quarter_year_like"
    CURRENCY_LIKE = "currency_like"
    RANGE_LIKE = "range_like"
    SCORE_LIKE = "score_like"
    UNIT_COUNT_LIKE = "unit_count_like"
    NUMERIC_LIKE = "numeric_like"
    IDENTITY_SYNTAX = "identity_syntax"
    LABEL_LIKE = "label_like"
    PROSE_LIKE = "prose_like"
    OTHER = "other"


class RepresentationMixture(Enum):
    """How the core representation families relate.

    ``NONE`` means no core family and no modifier was observed. Blank
    and other are that case. ``OBSERVED`` means a core family or a
    modifier was observed, and fewer than two core groups are material.
    ``CONFLICTING`` means at least two core groups are material.

    Padding and missing-like literals are modifiers. They are retained
    as counts and do not compete with a core family. This is not a
    resolution status and not a semantic type.
    """

    NONE = "none"
    OBSERVED = "observed"
    CONFLICTING = "conflicting"


_FAMILY_INDEX = {
    family: index for index, family in enumerate(RepresentationFamily)
}
_FAMILY_COUNT = len(RepresentationFamily)

# Core groups can compete for a semantic reading. Families inside one
# group are different spellings of that reading, so they do not conflict
# with each other. Padding and missing-like literals are not groups:
# they describe the recorded text and do not compete with a core family.
_CORE_GROUPS = (
    (RepresentationFamily.LABEL_LIKE,),
    (
        RepresentationFamily.TEMPORAL_LIKE,
        RepresentationFamily.QUARTER_YEAR_LIKE,
    ),
    (
        RepresentationFamily.CURRENCY_LIKE,
        RepresentationFamily.RANGE_LIKE,
        RepresentationFamily.SCORE_LIKE,
        RepresentationFamily.UNIT_COUNT_LIKE,
        RepresentationFamily.NUMERIC_LIKE,
    ),
    (RepresentationFamily.PROSE_LIKE,),
    (RepresentationFamily.EMAIL_LIKE, RepresentationFamily.URL_LIKE),
    (RepresentationFamily.IDENTITY_SYNTAX,),
)
_MODIFIER_FAMILIES = (
    RepresentationFamily.PADDED,
    RepresentationFamily.MISSING_LIKE,
)


@dataclass(frozen=True)
class RepresentationEvidence:
    """Immutable representation counts for one string Series.

    ``string_structure`` is the evidence these counts were collected
    with. Basic counts and character-class counts stay on that object.
    ``counts`` follows ``RepresentationFamily`` order. The counts sum to
    ``n_non_missing``. No matched string is stored.

    A ratio is an observed proportion, not a confidence and not a
    semantic conclusion.
    """

    string_structure: StringStructureEvidence
    counts: Tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.string_structure, StringStructureEvidence):
            raise TypeError("string_structure must be StringStructureEvidence")
        counts = _normalize_counts(self.counts)
        object.__setattr__(self, "counts", counts)
        population = self.string_structure.basic.n_non_missing
        if sum(counts) != population:
            raise ValueError("representation counts must sum to n_non_missing")
        blank = counts[_FAMILY_INDEX[RepresentationFamily.BLANK]]
        structure = self.string_structure
        expected_blank = structure.empty_string_count + structure.whitespace_only_count
        if blank != expected_blank:
            raise ValueError(
                "blank representation count must equal the empty-string "
                "and whitespace-only string-structure counts"
            )

    def count(self, family: RepresentationFamily) -> int:
        """How many non-missing strings were placed in ``family``."""
        if not isinstance(family, RepresentationFamily):
            raise TypeError("family must be a RepresentationFamily")
        return self.counts[_FAMILY_INDEX[family]]

    def ratio(self, family: RepresentationFamily) -> Optional[float]:
        """``count(family) / n_non_missing``, or ``None`` when that is 0.

        A zero numerator with a positive denominator is ``0.0``. An
        undefined ratio is not ``0.0``, ``1.0``, NaN, or infinity.
        """
        return _ratio(
            self.count(family),
            self.string_structure.basic.n_non_missing,
        )

    def positive_families(self) -> Tuple[RepresentationFamily, ...]:
        """Families with a positive count, in enum order.

        The result is at most one entry per family. It contains no raw
        values.
        """
        return tuple(
            family
            for family in RepresentationFamily
            if self.counts[_FAMILY_INDEX[family]] > 0
        )

    @property
    def mixture(self) -> RepresentationMixture:
        """Whether core families are absent, observed, or conflicting.

        A core group is material at ``MATERIAL_MIN_COUNT`` strings and
        at least one twentieth of the non-missing population. Two
        material core groups conflict. Padding and missing-like counts
        can make the result observed, and they do not create a conflict.
        Blank and other do not. The result is not a semantic type.
        """
        population = self.string_structure.basic.n_non_missing
        if population == 0:
            return RepresentationMixture.NONE
        core_count = 0
        material_groups = 0
        for group in _CORE_GROUPS:
            total = 0
            for family in group:
                total += self.counts[_FAMILY_INDEX[family]]
            core_count += total
            if _is_material(total, population):
                material_groups += 1
        if material_groups >= 2:
            return RepresentationMixture.CONFLICTING
        modifier_count = 0
        for family in _MODIFIER_FAMILIES:
            modifier_count += self.counts[_FAMILY_INDEX[family]]
        if core_count + modifier_count == 0:
            return RepresentationMixture.NONE
        return RepresentationMixture.OBSERVED


def collect_representation_evidence(
    series: pd.Series,
    string_structure: StringStructureEvidence,
    physical: PhysicalDtype,
) -> RepresentationEvidence:
    """Collect exact representation counts from evidence already in hand.

    ``string_structure`` supplies the string population. This function
    does not collect string structure, pattern evidence, or basic counts,
    and it does not classify the physical dtype again. ``physical`` must
    already describe this Series. The Series is not modified.

    One drop of pandas-missing values produces the non-missing population.
    Each remaining value must be a Python ``str``. An ineligible
    population raises ``TypeError``. Counts that disagree with the
    composed evidence raise ``ValueError``.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_representation_evidence expects a pandas Series")
    if not isinstance(string_structure, StringStructureEvidence):
        raise TypeError("string_structure must be StringStructureEvidence")
    if not isinstance(physical, PhysicalDtype):
        raise TypeError("physical must be a PhysicalDtype")
    _require_representation_family(physical)
    if str(series.dtype) != physical.dtype_name:
        raise ValueError("physical dtype does not match the Series")
    observed = _non_missing_values(series, string_structure)
    if physical.family is PhysicalDtypeFamily.OBJECT and len(observed) == 0:
        raise TypeError(_APPLICABILITY_ERROR)
    return _evidence_from_values(string_structure, observed)


def _require_representation_family(physical: PhysicalDtype) -> None:
    """Reject storage that string-structure evidence cannot describe."""
    if physical.family not in (
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    ):
        raise TypeError(_APPLICABILITY_ERROR)


def _non_missing_values(
    series: pd.Series,
    string_structure: StringStructureEvidence,
) -> pd.Series:
    """Return non-missing values in row order, without changing the source."""
    basic = string_structure.basic
    observed = series.dropna()
    if len(series) != basic.n_total or len(observed) != basic.n_non_missing:
        raise ValueError(
            "representation observations do not match BasicColumnEvidence "
            "n_total and n_non_missing"
        )
    return observed


def _evidence_from_values(
    string_structure: StringStructureEvidence,
    observed: pd.Series,
) -> RepresentationEvidence:
    """Place every non-missing string in one family.

    The original string is classified once. No match list is retained.

    When the known distinct count is at most half the non-missing
    count, each exact string is classified once and weighted by its
    occurrences. That table is not retained. Otherwise each value is read.
    """
    basic = string_structure.basic
    if _repeated_enough(basic.n_unique_non_missing, basic.n_non_missing):
        return _weighted_representation(string_structure, observed)
    totals = [0] * _FAMILY_COUNT
    for value in observed:
        if not isinstance(value, str):
            raise TypeError(_APPLICABILITY_ERROR)
        family = _classify(value)
        totals[_FAMILY_INDEX[family]] += 1
    return RepresentationEvidence(
        string_structure=string_structure,
        counts=tuple(totals),
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


def _weighted_representation(
    string_structure: StringStructureEvidence,
    observed: pd.Series,
) -> RepresentationEvidence:
    """Classify each exact string once and weight its family by its count."""
    counts = _exact_string_counts(observed)
    totals = [0] * _FAMILY_COUNT
    for value, weight in counts.items():
        totals[_FAMILY_INDEX[_classify(value)]] += weight
    return RepresentationEvidence(
        string_structure=string_structure,
        counts=tuple(totals),
    )


def _classify(value: str) -> RepresentationFamily:
    """Return the one family that describes ``value``.

    Earlier families win. The tests do not rewrite ``value``. A positive
    specialized shape is not later called a label.
    """
    if value == "" or value.isspace():
        return RepresentationFamily.BLANK
    if value[0].isspace() or value[-1].isspace():
        return RepresentationFamily.PADDED
    if (
        len(value) <= 7
        and value[0] in "uUnNmM"
        and value.casefold() in _MISSING_LITERALS
    ):
        return RepresentationFamily.MISSING_LIKE

    scan = _scan(value)
    if scan.has_at and _is_email(value):
        return RepresentationFamily.EMAIL_LIKE
    if value[0] in "hHwW" and _is_url(value):
        return RepresentationFamily.URL_LIKE
    if scan.dated_hint and _is_temporal(value):
        return RepresentationFamily.TEMPORAL_LIKE
    if _is_quarter(value):
        return RepresentationFamily.QUARTER_YEAR_LIKE
    if scan.has_digit and (
        scan.has_currency_symbol
        or (scan.has_letter and _currency_code_hint(value) and _has_currency_code(value))
    ):
        return RepresentationFamily.CURRENCY_LIKE
    if (scan.has_plus or scan.has_hyphen) and _is_range(value):
        return RepresentationFamily.RANGE_LIKE
    if scan.has_slash and _is_score(value):
        return RepresentationFamily.SCORE_LIKE
    if scan.has_space and scan.has_digit and scan.has_letter and _is_unit_count(value):
        return RepresentationFamily.UNIT_COUNT_LIKE
    if len(value) in _IDENTITY_LENGTHS and _is_identity_syntax(value):
        return RepresentationFamily.IDENTITY_SYNTAX
    if scan.has_digit and _is_number_token(value):
        return RepresentationFamily.NUMERIC_LIKE
    if scan.has_letter and scan.tokens >= PROSE_MIN_TOKENS:
        return RepresentationFamily.PROSE_LIKE
    if (
        scan.has_letter
        and scan.label_chars
        and 1 <= scan.tokens <= MAX_LABEL_TOKENS
        and len(value) <= MAX_LABEL_LENGTH
    ):
        return RepresentationFamily.LABEL_LIKE
    return RepresentationFamily.OTHER


class _Scan:
    """Flags from one pass over an original string. Not retained."""

    __slots__ = (
        "has_digit",
        "has_letter",
        "has_at",
        "has_currency_symbol",
        "has_slash",
        "has_hyphen",
        "has_plus",
        "has_space",
        "dated_hint",
        "label_chars",
        "tokens",
    )

    def __init__(self) -> None:
        self.has_digit = False
        self.has_letter = False
        self.has_at = False
        self.has_currency_symbol = False
        self.has_slash = False
        self.has_hyphen = False
        self.has_plus = False
        self.has_space = False
        self.dated_hint = False
        self.label_chars = True
        self.tokens = 0


def _scan(value: str) -> _Scan:
    """Record shape flags without allocating a token list."""
    scan = _Scan()
    in_token = False
    for character in value:
        if character.isdigit():
            scan.has_digit = True
        elif character.isalpha():
            scan.has_letter = True
        if character.isalnum():
            if not in_token:
                scan.tokens += 1
                in_token = True
            continue
        in_token = False
        if character == "@":
            scan.has_at = True
            scan.label_chars = False
        elif character in _CURRENCY_CHARS:
            scan.has_currency_symbol = True
            scan.label_chars = False
        elif character == "/":
            scan.has_slash = True
            scan.label_chars = False
        elif character == "-":
            scan.has_hyphen = True
        elif character == "+":
            scan.has_plus = True
            scan.label_chars = False
        elif character == " ":
            scan.has_space = True
        elif character in _LABEL_PUNCTUATION:
            continue
        elif character.isspace():
            scan.has_space = True
            scan.label_chars = False
        else:
            scan.label_chars = False
    if scan.has_digit and (scan.has_hyphen or scan.has_slash or scan.has_space):
        scan.dated_hint = True
    else:
        scan.dated_hint = False
    return scan


def _is_email(value: str) -> bool:
    """Return whether the entire string has a single-address email shape.

    The local part and the domain are non-empty, the domain contains a
    dot, and the string contains no whitespace. The address is not
    validated and is not rewritten.
    """
    if any(character.isspace() for character in value):
        return False
    local, separator, domain = value.partition("@")
    if separator != "@" or not local or not domain or "@" in domain:
        return False
    if domain.startswith(".") or domain.endswith(".") or "." not in domain:
        return False
    return True


def _is_url(value: str) -> bool:
    """Return whether the string starts with a URL prefix and contains a dot.

    Accepted prefixes are ``http://``, ``https://``, and ``www.``. The
    comparison uses a short case-folded prefix. The remainder is not
    canonicalized. A string with whitespace does not match.
    """
    if any(character.isspace() for character in value):
        return False
    prefix = value[:8].casefold()
    if prefix.startswith("https://"):
        body = value[8:]
    elif prefix.startswith("http://"):
        body = value[7:]
    elif prefix.startswith("www."):
        body = value[4:]
    else:
        return False
    return len(body) >= 3 and "." in body


def _is_temporal(value: str) -> bool:
    """Return whether ``value`` has one explicit date or timestamp shape.

    The shapes are an ISO date, an ISO datetime, a three-part numeric
    date, and a day, month-name, year triple. A pure digit string is not
    a date. Calendar validity is not checked, and the string is not parsed
    into a datetime.
    """
    if len(value) < 6 or len(value) > 40:
        return False
    if _is_iso_date(value) or _is_iso_datetime(value):
        return True
    if _is_numeric_date(value):
        return True
    return _is_month_date(value)


def _is_iso_date(value: str) -> bool:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        return False
    return value[0:4].isdigit() and value[5:7].isdigit() and value[8:10].isdigit()


def _is_iso_datetime(value: str) -> bool:
    if len(value) < 19 or value[10] != "T":
        return False
    if not _is_iso_date(value[:10]):
        return False
    clock = value[11:19]
    if clock[2] != ":" or clock[5] != ":":
        return False
    if not (clock[0:2].isdigit() and clock[3:5].isdigit() and clock[6:8].isdigit()):
        return False
    return _iso_tail(value[19:])


def _iso_tail(rest: str) -> bool:
    if rest == "":
        return True
    if rest[:1] == ".":
        index = 1
        if index >= len(rest) or not rest[index].isdigit():
            return False
        while index < len(rest) and rest[index].isdigit():
            index += 1
        rest = rest[index:]
        if rest == "":
            return True
    if rest == "Z" or rest == "z":
        return True
    if len(rest) == 6 and rest[0] in "+-" and rest[3] == ":":
        return rest[1:3].isdigit() and rest[4:6].isdigit()
    return False


def _is_numeric_date(value: str) -> bool:
    if "/" in value:
        separator = "/"
    elif "-" in value:
        separator = "-"
    else:
        return False
    parts = value.split(separator)
    if len(parts) != 3:
        return False
    first, second, year = parts
    if not (first.isdigit() and second.isdigit() and year.isdigit()):
        return False
    if not (1 <= len(first) <= 2 and 1 <= len(second) <= 2):
        return False
    return len(year) in (2, 4)


def _is_month_date(value: str) -> bool:
    parts = value.split(" ")
    if len(parts) != 3:
        return False
    day, month, year = parts
    if not day.isdigit() or not 1 <= len(day) <= 2:
        return False
    if month.casefold() not in _MONTHS:
        return False
    return year.isdigit() and len(year) in (2, 4)


def _is_quarter(value: str) -> bool:
    """Return whether ``value`` is a quarter token and a four-digit year.

    ``Q1 2016`` and ``2016 Q1`` match. A phrase that merely contains a
    quarter token does not. The match does not convert the text.
    """
    if len(value) < 6 or len(value) > 8:
        return False
    if "Q" not in value and "q" not in value:
        return False
    parts = value.split(" ")
    if len(parts) != 2:
        return False
    left, right = parts
    return (_is_quarter_token(left) and _is_year_token(right)) or (
        _is_year_token(left) and _is_quarter_token(right)
    )


def _is_quarter_token(token: str) -> bool:
    folded = token.casefold()
    return len(folded) == 2 and folded[0] == "q" and folded[1] in "1234"


def _is_year_token(token: str) -> bool:
    return len(token) == 4 and token.isdigit()


def _currency_code_hint(value: str) -> bool:
    """Return whether ``value`` contains a letter used by USD, EUR, or GBP.

    This avoids a code parse on ordinary alphanumeric text. It is not
    itself a currency match.
    """
    for character in value:
        if character in "UEGueg":
            return True
    return False


def _has_currency_code(value: str) -> bool:
    """Return whether a currency code is a token or is glued to a number.

    ``USD 250000`` and ``USD250000`` match. A longer word that merely
    starts with a code does not. The string is not converted.
    """
    for part in value.split(" "):
        folded = part.casefold().strip(".,")
        if not folded:
            continue
        if folded in _CURRENCY_CODES:
            return True
        for code in _CURRENCY_CODES:
            if folded.startswith(code):
                rest = folded[len(code) :]
            elif folded.endswith(code):
                rest = folded[: -len(code)]
            else:
                continue
            if rest and all(
                character.isdigit() or character in ",." for character in rest
            ):
                return True
    return False


def _is_range(value: str) -> bool:
    """Return whether ``value`` is a numeric range or an open numeric bound.

    ``1-10``, ``1,000+``, and ``500+`` match. A currency marker is handled
    earlier, so a currency range is not given this family. The endpoints
    are not converted to numbers.
    """
    if value.endswith("+"):
        return _is_number_token(value[:-1].strip())
    if "-" not in value:
        return False
    left, _separator, right = value.partition("-")
    if "-" in right:
        return False
    return _is_number_token(left.strip()) and _is_number_token(right.strip())


def _is_score(value: str) -> bool:
    """Return whether ``value`` is two integers separated by one slash."""
    left, separator, right = value.partition("/")
    if separator != "/" or "/" in right or not left or not right:
        return False
    return left.isdigit() and right.isdigit()


def _is_unit_count(value: str) -> bool:
    """Return whether ``value`` is one number token, a space, and one word.

    ``127 employees`` matches. The number is not parsed.
    """
    number, separator, word = value.partition(" ")
    if separator != " " or " " in word or not word.isalpha():
        return False
    return _is_number_token(number)


def _is_number_token(token: str) -> bool:
    """Return whether ``token`` is a plain, grouped, decimal, or suffixed number.

    A single trailing ``k``, ``m``, or ``b`` is a magnitude mark. It is
    not applied as a multiplier. Commas are recognized, not removed from
    the source.
    """
    if not token:
        return False
    if token[-1] in _MAGNITUDE_SUFFIXES and len(token) > 1:
        token = token[:-1]
    if "," in token:
        token = token.replace(",", "")
    if token.count(".") > 1:
        return False
    if "." in token:
        left, right = token.split(".")
        if not left or not right:
            return False
        return left.isdigit() and right.isdigit()
    return token.isdigit()


def _is_identity_syntax(value: str) -> bool:
    """Return whether pattern evidence would count this full value.

    The tests are the UUID and fixed-width hexadecimal tests. This
    function does not increment those counts.
    """
    return matches_identifier_syntax(value)


def _is_material(count: int, population: int) -> bool:
    if count < MATERIAL_MIN_COUNT:
        return False
    return count * MATERIAL_PROPORTION_DENOMINATOR >= population


def _ratio(count: int, denominator: int) -> Optional[float]:
    if denominator == 0:
        return None
    return count / denominator


def _normalize_counts(value: Any) -> Tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise TypeError("counts must be a tuple of ints")
    if len(value) != _FAMILY_COUNT:
        raise ValueError("counts must contain one int per representation family")
    for item in value:
        if type(item) is not int:
            raise TypeError("counts must contain only ints")
        if item < 0:
            raise ValueError("representation counts must be >= 0")
    return value
