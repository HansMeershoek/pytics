"""Exact token and character observations for one string-valued column.

A token is a maximal contiguous run of Unicode alphanumeric characters,
using ``str.isalnum``. Punctuation and whitespace separate tokens.
``"hello-world"`` is two tokens. ``"abc123"`` is one. Case is preserved,
and accents are not rewritten. The observations describe that structure.
They do not decide Text, Categorical, Identifier, or any other role.

The population is the non-missing strings already accepted by
``StringStructureEvidence``. This module does not decide that eligibility
again and does not recollect string structure, basic counts, or
whole-value frequencies. Missing values stay missing. ``""`` and
whitespace-only strings stay observed strings with no tokens.

Whole-value repetition stays on frequency evidence. Token repetition is
a separate count. No token, string, or vocabulary is retained.

Collection is exact, full-column, and unsampled. It runs only when
requested. The Empty, Constant, and physical-type precedence chain does
not collect it, and collecting string structure does not collect it either.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import cast

import pandas as pd

from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.string_structure_evidence import StringStructureEvidence

_APPLICABILITY_ERROR = (
    "string content evidence applies only to non-missing Python strings "
    "from a population already accepted by string-structure evidence"
)

_COUNT_FIELDS = (
    "total_token_count",
    "strings_with_zero_tokens_count",
    "strings_with_one_token_count",
    "strings_with_multiple_tokens_count",
    "total_character_count",
    "n_distinct_tokens",
    "singleton_token_count",
    "most_frequent_token_count",
)


@dataclass(frozen=True)
class StringContentEvidence:
    """Immutable token and character facts for one string Series.

    ``string_structure`` is the string-structure evidence these facts were
    collected with. Basic counts, length bounds, and character-class counts
    stay on that object. They are not copied. Whole-value frequency counts
    are not copied either.

    The eight counts are stored. A count is never ``None``. Ratios and
    means are read from those counts. An undefined ratio or mean is
    ``None``.

    No raw string and no token is retained. A ratio is an observed
    proportion, not a semantic conclusion.
    """

    string_structure: StringStructureEvidence
    total_token_count: int
    strings_with_zero_tokens_count: int
    strings_with_one_token_count: int
    strings_with_multiple_tokens_count: int
    total_character_count: int
    n_distinct_tokens: int
    singleton_token_count: int
    most_frequent_token_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.string_structure, StringStructureEvidence):
            raise TypeError("string_structure must be StringStructureEvidence")
        for field in _COUNT_FIELDS:
            _require_count(getattr(self, field), field)
        _require_string_partition(self)
        _require_token_occurrences(self)
        _require_character_count(self)
        _require_blank_strings_have_no_token(self)
        _require_token_vocabulary(self)

    @property
    def zero_token_ratio(self) -> Optional[float]:
        """Strings with no token, divided by non-missing strings.

        The denominator is ``string_structure.basic.n_non_missing``.
        ``None`` when that count is zero. This is not a Text rule.
        """
        return _ratio(
            self.strings_with_zero_tokens_count,
            self.string_structure.basic.n_non_missing,
        )

    @property
    def one_token_ratio(self) -> Optional[float]:
        """Strings with one token, divided by non-missing strings.

        The denominator is ``n_non_missing``. ``None`` when that count is
        zero. This is not a Categorical rule.
        """
        return _ratio(
            self.strings_with_one_token_count,
            self.string_structure.basic.n_non_missing,
        )

    @property
    def multiple_token_ratio(self) -> Optional[float]:
        """Strings with two or more tokens, divided by non-missing strings.

        The denominator is ``n_non_missing``. ``None`` when that count is
        zero. This is not a Text rule.
        """
        return _ratio(
            self.strings_with_multiple_tokens_count,
            self.string_structure.basic.n_non_missing,
        )

    @property
    def mean_tokens_per_non_missing(self) -> Optional[float]:
        """Token occurrences divided by non-missing strings.

        The denominator is ``n_non_missing``. ``None`` when that count is
        zero. A column of punctuation has mean ``0.0``, not ``None``.
        """
        return _ratio(self.total_token_count, self.string_structure.basic.n_non_missing)

    @property
    def mean_characters_per_non_missing(self) -> Optional[float]:
        """Character occurrences divided by non-missing strings.

        The denominator is ``n_non_missing``. ``None`` when that count is
        zero. Length is ``len`` of the original string, the same definition
        as string-structure evidence. This is not a Text cutoff.
        """
        return _ratio(
            self.total_character_count,
            self.string_structure.basic.n_non_missing,
        )

    @property
    def token_singleton_ratio(self) -> Optional[float]:
        """Distinct tokens that occur once, divided by distinct tokens.

        The denominator is ``n_distinct_tokens``. It is not
        ``total_token_count`` and not ``n_non_missing``. ``None`` when
        there is no distinct token, including a non-empty column whose
        strings contain no alphanumeric run.
        """
        return _ratio(self.singleton_token_count, self.n_distinct_tokens)

    @property
    def most_frequent_token_ratio(self) -> Optional[float]:
        """Occurrences of the most frequent token, over all token occurrences.

        The denominator is ``total_token_count``. It is not
        ``n_distinct_tokens`` and not ``n_non_missing``. ``None`` when
        there is no token occurrence.
        """
        return _ratio(self.most_frequent_token_count, self.total_token_count)


def collect_string_content_evidence(
    series: pd.Series,
    string_structure: StringStructureEvidence,
    physical: PhysicalDtype,
) -> StringContentEvidence:
    """Collect exact token facts from evidence already in hand.

    ``string_structure`` supplies the string population's basic evidence.
    This function does not collect string structure, basic counts, or
    whole-value frequencies, and it does not classify the physical dtype
    again. ``physical`` must already describe this Series. The Series is
    not modified, stripped, case-folded, or Unicode-normalized.

    One drop of pandas-missing values produces the non-missing population.
    Each remaining value must be a Python ``str``, including subclasses.
    ``bytes`` are not strings and are not decoded. An ineligible population
    raises ``TypeError``. Counts that disagree with the composed basic
    evidence raise ``ValueError``.

    A temporary mapping counts token occurrences so the distinct-token,
    singleton-token, and most-frequent-token totals can be exact. That
    mapping is not part of the returned value.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("collect_string_content_evidence expects a pandas Series")
    if not isinstance(string_structure, StringStructureEvidence):
        raise TypeError("string_structure must be StringStructureEvidence")
    if not isinstance(physical, PhysicalDtype):
        raise TypeError("physical must be a PhysicalDtype")
    _require_content_family(physical)
    if str(series.dtype) != physical.dtype_name:
        raise ValueError("physical dtype does not match the Series")
    observed = _non_missing_values(series, string_structure)
    if physical.family is PhysicalDtypeFamily.OBJECT and len(observed) == 0:
        # No non-missing value means string-structure evidence cannot
        # describe this object column. Do not treat that absence as a
        # string population.
        raise TypeError(_APPLICABILITY_ERROR)
    return _evidence_from_values(string_structure, observed)


def _require_content_family(physical: PhysicalDtype) -> None:
    """Reject storage that string-structure evidence cannot describe.

    This is a consistency guard for the supplied physical dtype. It does
    not classify the Series and does not recompute string structure.
    Categorical labels are not inspected.
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
            "string content observations do not match BasicColumnEvidence "
            "n_total and n_non_missing"
        )
    return observed


def _evidence_from_values(
    string_structure: StringStructureEvidence,
    observed: pd.Series,
) -> StringContentEvidence:
    """Derive every stored fact from one pass over non-missing strings.

    Each value must already be a Python ``str``. The original string is
    not stripped, case-folded, or Unicode-normalized. Token identity is
    the original alphanumeric run, so ``"Apple"`` and ``"apple"`` stay
    distinct. The occurrence mapping exists only for this pass.
    """
    occurrences: dict[str, int] = {}
    total_token_count = 0
    strings_with_zero_tokens_count = 0
    strings_with_one_token_count = 0
    strings_with_multiple_tokens_count = 0
    total_character_count = 0
    for value in observed:
        if not isinstance(value, str):
            raise TypeError(_APPLICABILITY_ERROR)
        total_character_count += len(value)
        token_count = _record_tokens(value, occurrences)
        total_token_count += token_count
        if token_count == 0:
            strings_with_zero_tokens_count += 1
        elif token_count == 1:
            strings_with_one_token_count += 1
        else:
            strings_with_multiple_tokens_count += 1
    singleton_token_count = 0
    most_frequent_token_count = 0
    for count in occurrences.values():
        if count == 1:
            singleton_token_count += 1
        if count > most_frequent_token_count:
            most_frequent_token_count = count
    return StringContentEvidence(
        string_structure=string_structure,
        total_token_count=total_token_count,
        strings_with_zero_tokens_count=strings_with_zero_tokens_count,
        strings_with_one_token_count=strings_with_one_token_count,
        strings_with_multiple_tokens_count=strings_with_multiple_tokens_count,
        total_character_count=total_character_count,
        n_distinct_tokens=len(occurrences),
        singleton_token_count=singleton_token_count,
        most_frequent_token_count=most_frequent_token_count,
    )


def _record_tokens(value: str, occurrences: dict[str, int]) -> int:
    """Count maximal alphanumeric runs in one original string.

    ``str.isalnum`` is Python's Unicode alphanumeric test. A character
    that is not alphanumeric ends the current run. Underscore, hyphen,
    period, whitespace, and emoji are separators under that test. The
    recorded token is the original slice. Nothing is case-folded.
    """
    count = 0
    start: Optional[int] = None
    for index, character in enumerate(value):
        if character.isalnum():
            if start is None:
                start = index
            continue
        if start is not None:
            _increment(occurrences, value[start:index])
            count += 1
            start = None
    if start is not None:
        _increment(occurrences, value[start:])
        count += 1
    return count


def _increment(occurrences: dict[str, int], token: str) -> None:
    occurrences[token] = occurrences.get(token, 0) + 1


def _ratio(count: int, denominator: int) -> Optional[float]:
    """Divide by ``denominator``, or return ``None`` when it is 0.

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


def _require_string_partition(evidence: StringContentEvidence) -> None:
    """The three token-count classes partition the non-missing strings."""
    classified = (
        evidence.strings_with_zero_tokens_count
        + evidence.strings_with_one_token_count
        + evidence.strings_with_multiple_tokens_count
    )
    if classified != evidence.string_structure.basic.n_non_missing:
        raise ValueError(
            "zero-token, one-token, and multiple-token strings must "
            "partition n_non_missing"
        )


def _require_token_occurrences(evidence: StringContentEvidence) -> None:
    """Keep token occurrences possible for the string partition.

    A one-token string contributes one token. A multiple-token string
    contributes at least two. Strings with no token contribute none, so
    a positive token total requires at least one of those other strings.
    """
    minimum = (
        evidence.strings_with_one_token_count
        + 2 * evidence.strings_with_multiple_tokens_count
    )
    if evidence.total_token_count < minimum:
        raise ValueError(
            "token occurrences are below the one-token and multiple-token strings"
        )
    token_bearing = (
        evidence.strings_with_one_token_count
        + evidence.strings_with_multiple_tokens_count
    )
    if token_bearing == 0 and evidence.total_token_count != 0:
        raise ValueError("token occurrences require a string that contains a token")


def _require_character_count(evidence: StringContentEvidence) -> None:
    """Keep the character total inside the population and the length bounds.

    Each token occupies at least one character. ``min_length`` and
    ``max_length`` stay on the composed string-structure evidence. When
    there is no non-missing string, both the character total and those
    bounds are empty rather than zero-as-observed.
    """
    non_missing = evidence.string_structure.basic.n_non_missing
    if non_missing == 0:
        if evidence.total_character_count != 0:
            raise ValueError("total_character_count is 0 when n_non_missing is 0")
        return
    if evidence.total_character_count < evidence.total_token_count:
        raise ValueError("total_character_count is below the token occurrences")
    # The composed evidence defines both bounds whenever n_non_missing > 0.
    minimum_length = cast(int, evidence.string_structure.min_length)
    maximum_length = cast(int, evidence.string_structure.max_length)
    lower = minimum_length * non_missing
    upper = maximum_length * non_missing
    if evidence.total_character_count < lower or evidence.total_character_count > upper:
        raise ValueError("total_character_count is outside min_length and max_length")


def _require_blank_strings_have_no_token(evidence: StringContentEvidence) -> None:
    """Empty and whitespace-only strings have no alphanumeric run.

    Other zero-token strings, such as punctuation or emoji, may also be
    present. The inequality is one direction only.
    """
    blank = (
        evidence.string_structure.empty_string_count
        + evidence.string_structure.whitespace_only_count
    )
    if evidence.strings_with_zero_tokens_count < blank:
        raise ValueError(
            "empty and whitespace-only strings contain no alphanumeric token"
        )


def _require_token_vocabulary(evidence: StringContentEvidence) -> None:
    """Keep distinct, singleton, and most-frequent token counts possible.

    The population is token occurrences, not strings. A singleton is a
    distinct token that occurs once. The denominator of that idea is
    ``n_distinct_tokens``.
    """
    total = evidence.total_token_count
    distinct = evidence.n_distinct_tokens
    singleton = evidence.singleton_token_count
    most_frequent = evidence.most_frequent_token_count
    if total == 0:
        if distinct != 0 or singleton != 0 or most_frequent != 0:
            raise ValueError(
                "a column with no tokens has no distinct, singleton, "
                "or most-frequent token"
            )
        return
    if distinct < 1:
        raise ValueError("n_distinct_tokens must be positive when tokens exist")
    if distinct > total:
        raise ValueError("n_distinct_tokens cannot exceed total_token_count")
    if most_frequent < 1:
        raise ValueError("most_frequent_token_count must be >= 1 when tokens exist")
    if most_frequent > total:
        raise ValueError("most_frequent_token_count cannot exceed total_token_count")
    if singleton > distinct:
        raise ValueError("singleton_token_count cannot exceed n_distinct_tokens")
    if distinct == 1:
        _require_single_token_counts(total, most_frequent, singleton)
        return
    if most_frequent == 1:
        if singleton != distinct or total != distinct:
            raise ValueError(
                "when every token occurs once, singleton_token_count "
                "equals n_distinct_tokens and total_token_count"
            )
        return
    non_singletons = distinct - singleton
    if non_singletons < 1:
        raise ValueError(
            "a repeated token means at least one distinct token is not a singleton"
        )
    lower = singleton + 2 * (non_singletons - 1) + most_frequent
    upper = singleton + non_singletons * most_frequent
    if not lower <= total <= upper:
        raise ValueError(
            "token counts are inconsistent with total_token_count and "
            "n_distinct_tokens"
        )


def _require_single_token_counts(
    total: int,
    most_frequent: int,
    singleton: int,
) -> None:
    if most_frequent != total:
        raise ValueError("the only distinct token occurs total_token_count times")
    expected_singletons = 1 if total == 1 else 0
    if singleton != expected_singletons:
        raise ValueError(
            "singleton_token_count is 1 only when the single distinct token "
            "occurs once"
        )
