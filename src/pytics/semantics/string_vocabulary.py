"""Categorical support for a reused label vocabulary on string storage.

Physical categorical storage is a separate rule. This module does not
replace it, and it does not read a Series, a column name, or a numeric
code. It reads basic counts, string-structure counts, and pattern counts
that were already collected.

Support requires four independent facts at once. Repetition shows that
the values are reused. A vocabulary bound keeps a near-key from passing
as a small label set. Character classes require every non-missing string
to be an unpunctuated, letter-bearing label. Full-population UUID or
fixed-width hexadecimal syntax is identity syntax, so it is not this
vocabulary. Missing any one fact withholds support. That is not a
contradiction, and it does not assign High, Medium, or Low confidence.

The vocabulary bound is ``max(12, n_non_missing // 4)``. Twelve is a
closed enumerable set, used only while the sample is too small for an
average of four observations per label. Once the sample is larger, one
distinct label per four observations is the reuse density. Neither number
is a category list, and neither number is used alone.

Low-cardinality numeric storage is not this rule. Multi-word labels,
punctuation, pure digit strings, and mixed representations stay
unsupported here. Text is not selected by withholding Categorical.
"""

from __future__ import annotations

from typing import Optional
from typing import Tuple
from typing import cast

from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.pattern_evidence import PatternEvidence
from pytics.semantics.string_structure_evidence import StringStructureEvidence

# A familiar closed set (the months). It is a floor for a short extract,
# not a cap once the proportional term is larger.
SMALL_VOCABULARY_FLOOR = 12

# Large samples must reuse labels densely enough that the average label
# is observed at least this many times. A near-key of accidental pairs
# does not clear it.
MIN_AVERAGE_REUSE = 4

# Same widths the Identifier candidate treats as full-population syntax.
_IDENTIFIER_HEX_WIDTHS = (32, 40, 64, 128)

_SUPPORT_STATEMENT = (
    "A reused vocabulary of unpunctuated letter-bearing labels "
    "supports a Categorical reading."
)


def vocabulary_limit(n_non_missing: int) -> int:
    """Return the distinct-label bound for one non-missing population.

    The proportional term is ``n_non_missing // 4``. The floor of 12
    applies only when that term is not already larger.
    """
    proportional = n_non_missing // MIN_AVERAGE_REUSE
    if proportional > SMALL_VOCABULARY_FLOOR:
        return proportional
    return SMALL_VOCABULARY_FLOOR


def repeated_alphabetic_label_support(
    basic: BasicColumnEvidence,
    string_structure: Optional[StringStructureEvidence],
    pattern: Optional[PatternEvidence],
) -> Tuple[SemanticEvidence, ...]:
    """Return Categorical support for a reused alphabetic label vocabulary.

    An empty tuple means this rule does not support Categorical. It does
    not contradict Categorical, and it does not select a reading.
    """
    if not _bundle_applies(basic, string_structure, pattern):
        return ()
    structure = cast(StringStructureEvidence, string_structure)
    observed = cast(PatternEvidence, pattern)
    population = basic.n_non_missing
    if _identifier_syntax_covers_population(observed, population):
        return ()
    if not _unpunctuated_letter_bearing(structure, population):
        return ()
    if not _reused_vocabulary(basic):
        return ()
    return (SemanticEvidence(_SUPPORT_STATEMENT),)


def _bundle_applies(
    basic: BasicColumnEvidence,
    string_structure: Optional[StringStructureEvidence],
    pattern: Optional[PatternEvidence],
) -> bool:
    """True when string structure and pattern describe this basic evidence.

    Pattern evidence is required so identity syntax can be excluded.
    A missing pattern is missing evidence, not support.
    """
    if string_structure is None or pattern is None:
        return False
    if string_structure.basic is not basic:
        return False
    if pattern.string_structure is not string_structure:
        return False
    return basic.n_non_missing > 0


def _identifier_syntax_covers_population(
    pattern: PatternEvidence,
    population: int,
) -> bool:
    """True when UUID or one hex width matches every non-missing value.

    This is the same full-population fact the Identifier candidate uses.
    A partial pattern does not block a label vocabulary by itself.
    """
    if pattern.uuid_count == population:
        return True
    for width in _IDENTIFIER_HEX_WIDTHS:
        if getattr(pattern, f"hex_{width}_count") == population:
            return True
    return False


def _unpunctuated_letter_bearing(
    structure: StringStructureEvidence,
    population: int,
) -> bool:
    """True when every non-missing string is an unpunctuated letter label.

    Whitespace, empty strings, and other characters (punctuation, symbols,
    separators) are not this shape. A string that does not contain a
    letter is not this shape, so a pure digit string is not a label here.
    A letter may still sit beside digits, as in a short code.
    """
    if structure.empty_string_count != 0:
        return False
    if structure.contains_whitespace_count != 0:
        return False
    if structure.contains_other_count != 0:
        return False
    return structure.contains_alpha_count == population


def _reused_vocabulary(basic: BasicColumnEvidence) -> bool:
    """True when distinct labels are reused inside the vocabulary bound.

    ``n_unique_non_missing < n_non_missing`` is the repetition fact: at
    least one observed value occurs more than once. The bound is not used
    without that fact, so an all-unique column cannot pass through the
    small-sample floor.
    """
    n_unique = basic.n_unique_non_missing
    n_non_missing = basic.n_non_missing
    if n_unique >= n_non_missing:
        return False
    return n_unique <= vocabulary_limit(n_non_missing)
