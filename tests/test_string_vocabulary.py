"""TSK-044: reused alphabetic labels can support Categorical.

The cases are constructed. They do not name a published dataset and they
do not branch on a column name. Boundaries use the vocabulary constants
so a silent change of either constant fails here.
"""

from __future__ import annotations

import uuid

import pandas as pd
import pytest

from pytics.analysis.column import analyze_series
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.relationship import CategoricalCategoricalRelationship
from pytics.analysis.relationship import NumericCategoricalRelationship
from pytics.analysis.relationship import build_relationships_summary
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.core_candidates import assess_categorical_candidate
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.string_structure_evidence import collect_string_structure_evidence
from pytics.semantics.string_vocabulary import repeated_alphabetic_label_support
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.string_vocabulary import MIN_AVERAGE_REUSE
from pytics.semantics.string_vocabulary import SMALL_VOCABULARY_FLOOR

_LABEL_STATEMENT = (
    "A reused vocabulary of unpunctuated letter-bearing labels "
    "supports a Categorical reading."
)
_COMPACT_A = uuid.UUID(int=1).hex
_COMPACT_B = uuid.UUID(int=2).hex
_UUID_A = str(uuid.UUID(int=1))
_UUID_B = str(uuid.UUID(int=2))


def _labels(n_unique: int, n_rows: int, *, dtype: str | type = "string") -> pd.Series:
    """Build letter-bearing labels with as even a reuse as the lengths allow."""
    names = [f"L{index:02d}" for index in range(n_unique)]
    values = [names[index % n_unique] for index in range(n_rows)]
    return pd.Series(values, dtype=dtype)


def _selected(series: pd.Series) -> InferredSemanticResult:
    return analyze_series(series).inferred


def _categorical_statement(series: pd.Series) -> str | None:
    analysis = analyze_series(series)
    for candidate in analysis.inferred.resolution.candidates:
        if candidate.semantic_type is not SemanticType.CATEGORICAL:
            continue
        if candidate.disposition is not CandidateDisposition.SUPPORTED:
            return None
        return candidate.supporting_evidence[0].statement
    return None


def test_vocabulary_constants_stay_explicit():
    assert SMALL_VOCABULARY_FLOOR == 12
    assert MIN_AVERAGE_REUSE == 4


@pytest.mark.parametrize("dtype", ["string", object])
def test_clean_low_cardinality_labels_resolve_categorical(dtype):
    series = pd.Series(["red", "blue", "red", "green", "blue"], dtype=dtype)
    result = _selected(series)
    assert result.selected_type is SemanticType.CATEGORICAL
    assert result.interpretation is None
    assert result.resolution.status is ResolutionStatus.RESOLVED
    assert result.resolution.reason == (
        "Exactly one candidate is supported: Categorical."
    )
    assert _categorical_statement(series) == _LABEL_STATEMENT
    assert result.physical.family is (
        PhysicalDtypeFamily.STRING if dtype == "string" else PhysicalDtypeFamily.OBJECT
    )


def test_categorical_labels_with_missingness_stay_categorical():
    series = pd.Series(["US", "DE", None, "US", pd.NA, "FR", "DE"], dtype=object)
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.evidence.basic.n_missing == 2
    described = analysis.categorical_analysis
    assert described is not None
    assert described.ordered is None
    assert described.n_non_missing == 5
    assert [level.value for level in described.levels] == ["US", "DE", "FR"]
    assert analysis.evidence.frequency is not None
    assert described.most_frequent_count == (
        analysis.evidence.frequency.most_frequent_count
    )


def test_two_letter_labels_are_categorical_not_boolean():
    series = pd.Series(["male", "female", "male", "female"], dtype=object)
    result = _selected(series)
    assert result.selected_type is SemanticType.CATEGORICAL
    assert result.selected_type is not SemanticType.BOOLEAN
    assert result.interpretation is None
    yes_no = _selected(pd.Series(["yes", "no", "yes"], dtype="string"))
    assert yes_no.selected_type is SemanticType.CATEGORICAL
    active = _selected(pd.Series(["active", "inactive", "active"], dtype="string"))
    assert active.selected_type is SemanticType.CATEGORICAL


def test_case_variants_stay_distinct_labels():
    analysis = analyze_series(pd.Series(["US", "us", "US", "us"], dtype=object))
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert [level.value for level in analysis.categorical_analysis.levels] == [
        "US",
        "us",
    ]


def test_imbalanced_labels_stay_categorical():
    series = pd.Series(["lead"] * 40 + ["customer"], dtype="string")
    assert _selected(series).selected_type is SemanticType.CATEGORICAL


def test_moderate_vocabulary_is_categorical_and_the_next_label_is_not():
    assert SMALL_VOCABULARY_FLOOR == 12
    supported = _labels(20, 80)
    assert supported.nunique(dropna=True) == 20
    assert _selected(supported).selected_type is SemanticType.CATEGORICAL
    blocked = _labels(21, 80)
    assert _selected(blocked).selected_type is None
    assert _selected(blocked).resolution.status is (
        ResolutionStatus.INSUFFICIENT_EVIDENCE
    )


@pytest.mark.parametrize(
    ("n_unique", "n_rows", "expected"),
    [
        (12, 48, SemanticType.CATEGORICAL),
        (13, 48, None),
        (13, 52, SemanticType.CATEGORICAL),
        (14, 52, None),
        (3, 4, SemanticType.CATEGORICAL),
        (4, 4, None),
        (12, 13, SemanticType.CATEGORICAL),
        (13, 13, None),
    ],
)
def test_vocabulary_bound_boundaries(n_unique: int, n_rows: int, expected):
    result = _selected(_labels(n_unique, n_rows))
    assert result.selected_type is expected


def test_unique_and_near_unique_letter_strings_stay_unresolved():
    unique = pd.Series([f"name{index:03d}" for index in range(30)], dtype=object)
    assert _selected(unique).selected_type is None
    near = _labels(99, 100)
    assert near.nunique(dropna=True) == 99
    result = _selected(near)
    assert result.selected_type is None
    assert result.resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE


def test_alphanumeric_codes_can_be_categorical_and_pure_digits_cannot():
    codes = pd.Series(["Q1", "Q2", "Q3", "Q1", "Q2"], dtype="string")
    assert _selected(codes).selected_type is SemanticType.CATEGORICAL
    digits = pd.Series(["1", "2", "3", "1", "2"], dtype="string")
    digit_result = _selected(digits)
    assert digit_result.selected_type is None
    mixed = pd.Series(["A", "B", "3", "A"], dtype="string")
    assert _selected(mixed).selected_type is None


def test_full_population_hex_width_is_identifier_not_categorical():
    token_a = "ab" * 20
    token_b = "cd" * 20
    result = _selected(pd.Series([token_a, token_b, token_a], dtype="string"))
    assert len(token_a) == 40
    assert result.selected_type is SemanticType.IDENTIFIER


def test_label_support_withholds_when_the_bundle_does_not_apply():
    series = pd.Series(["red", "blue", "red"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    pattern = collect_pattern_evidence(series, structure, physical)
    assert repeated_alphabetic_label_support(basic, None, pattern) == ()
    assert repeated_alphabetic_label_support(basic, structure, None) == ()
    other = BasicColumnEvidence(
        n_total=basic.n_total,
        n_missing=basic.n_missing,
        n_non_missing=basic.n_non_missing,
        n_unique_non_missing=basic.n_unique_non_missing,
    )
    assert repeated_alphabetic_label_support(other, structure, pattern) == ()
    other_series = pd.Series(["aa", "bb", "aa"], dtype="string")
    other_basic = collect_basic_column_evidence(other_series)
    other_physical = classify_physical_dtype(other_series)
    other_structure = collect_string_structure_evidence(
        other_series,
        other_basic,
        other_physical,
    )
    other_pattern = collect_pattern_evidence(
        other_series,
        other_structure,
        other_physical,
    )
    assert repeated_alphabetic_label_support(basic, structure, other_pattern) == ()
    empty = pd.Series([], dtype="string")
    empty_basic = collect_basic_column_evidence(empty)
    empty_physical = classify_physical_dtype(empty)
    empty_structure = collect_string_structure_evidence(
        empty,
        empty_basic,
        empty_physical,
    )
    empty_pattern = collect_pattern_evidence(empty, empty_structure, empty_physical)
    assert (
        repeated_alphabetic_label_support(
            empty_basic,
            empty_structure,
            empty_pattern,
        )
        == ()
    )


def test_high_cardinality_identifier_like_strings_are_not_categorical():
    emails = pd.Series(
        ["ada@example.com", "grace@example.com", "ada@example.com"],
        dtype=object,
    )
    urls = pd.Series(
        ["https://example.com/a", "https://example.com/b", "https://example.com/a"],
        dtype="string",
    )
    assert _selected(emails).selected_type is None
    assert _selected(urls).selected_type is None
    compact = pd.Series([_COMPACT_A, _COMPACT_B, _COMPACT_A], dtype="string")
    compact_result = _selected(compact)
    assert compact_result.selected_type is SemanticType.IDENTIFIER
    hyphenated = pd.Series([_UUID_A, _UUID_B, _UUID_A], dtype=object)
    assert _selected(hyphenated).selected_type is SemanticType.IDENTIFIER


def test_repeated_prose_and_multiword_labels_stay_unresolved():
    prose = pd.Series(
        [
            "The river is wide and the road is long today.",
            "Another short note about the same city.",
            "The river is wide and the road is long today.",
        ],
        dtype="string",
    )
    places = pd.Series(["New York", "Los Angeles", "New York"], dtype=object)
    padded = pd.Series(["US", " US ", "US"], dtype=object)
    blank = pd.Series(["US", "", "US"], dtype=object)
    for series in (prose, places, padded, blank):
        result = _selected(series)
        assert result.selected_type is None
        assert result.resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    analysis = analyze_series(prose)
    text = next(
        candidate
        for candidate in analysis.inferred.resolution.candidates
        if candidate.semantic_type is SemanticType.TEXT
    )
    categorical = next(
        candidate
        for candidate in analysis.inferred.resolution.candidates
        if candidate.semantic_type is SemanticType.CATEGORICAL
    )
    assert text.disposition is CandidateDisposition.NOT_SUPPORTED
    assert categorical.disposition is CandidateDisposition.NOT_SUPPORTED


def test_repeated_long_letter_token_is_still_a_label():
    token = "x" * 80
    series = pd.Series([token, "short", token], dtype="string")
    assert _selected(series).selected_type is SemanticType.CATEGORICAL


def test_mixed_representations_do_not_resolve_categorical():
    dates = pd.Series(
        ["2024-01-01", "Q1 2024", "45292", "2024-01-01", "16/03/2020"],
        dtype=object,
    )
    money = pd.Series(
        ["€2.5m", "$1M-$5M", "unknown", "5000000", "USD 250000"],
        dtype=object,
    )
    scores = pd.Series(
        ["67/100", "1 stars", "needs review", "warm", "80/100", "A"],
        dtype=object,
    )
    for series in (dates, money, scores):
        result = _selected(series)
        assert result.selected_type is None
        assert result.interpretation is None
        assert result.resolution.status is ResolutionStatus.INSUFFICIENT_EVIDENCE


def test_low_cardinality_numeric_stays_numeric():
    samples = [
        pd.Series([2007, 2008, 2009, 2007, 2008]),
        pd.Series([1, 2, 3, 1, 2, 3]),
        pd.Series([0, 1, 0, 1]),
        pd.Series([0.0, 1.0, 0.0, 1.0]),
    ]
    for series in samples:
        result = _selected(series)
        assert result.selected_type is SemanticType.NUMERIC
        categorical = next(
            candidate
            for candidate in result.resolution.candidates
            if candidate.semantic_type is SemanticType.CATEGORICAL
        )
        assert categorical.disposition is CandidateDisposition.NOT_SUPPORTED


def test_constant_and_empty_stay_structural():
    constant = _selected(pd.Series(["red", "red", None], dtype=object))
    assert constant.selected_type is SemanticType.CONSTANT
    empty = _selected(pd.Series([pd.NA, None], dtype=object))
    assert empty.selected_type is SemanticType.EMPTY
    physical = _selected(pd.Series(pd.Categorical(["New York", "Paris", "New York"])))
    assert physical.selected_type is SemanticType.CATEGORICAL
    assert physical.physical.categorical_ordered is False


def test_resolution_is_deterministic_and_does_not_mutate_the_source():
    series = pd.Series(["red", "blue", None, "red"], dtype=object)
    original = series.copy(deep=True)
    dtype = series.dtype
    first = analyze_series(series)
    second = analyze_series(series)
    assert first.inferred == second.inferred
    assert series.dtype == dtype
    pd.testing.assert_series_equal(series, original)


def test_generic_mixed_frame_activates_existing_relationships_without_mutation():
    frame = pd.DataFrame(
        {
            "group_label": pd.Series(
                ["red", "blue", "red", "green", "blue", "red"],
                dtype=object,
            ),
            "site_code": pd.Series(
                ["US", "DE", "FR", "US", "DE", "FR"],
                dtype=object,
            ),
            "status": pd.Series(
                ["active", "inactive", "active", "active", "inactive", "active"],
                dtype="string",
            ),
            "measure": [1.2, 2.4, 1.1, 3.0, 2.2, 1.5],
            "cohort_year": [2007, 2008, 2009, 2007, 2008, 2009],
            "record_key": pd.Series(
                [uuid.UUID(int=index + 1).hex for index in range(6)],
                dtype=object,
            ),
        }
    )
    original = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    pd.testing.assert_frame_equal(frame, original)
    selected = [column.inferred.selected_type for column in analysis.columns]
    assert selected == [
        SemanticType.CATEGORICAL,
        SemanticType.CATEGORICAL,
        SemanticType.CATEGORICAL,
        SemanticType.NUMERIC,
        SemanticType.NUMERIC,
        SemanticType.IDENTIFIER,
    ]
    summary = build_relationships_summary(analysis)
    assert summary.n_supported_pairs == 10
    assert summary.n_ineligible_pairs == 5
    assert summary.n_unimplemented_family_pairs == 0
    assert any(
        isinstance(item, NumericCategoricalRelationship)
        for item in summary.relationships
    )
    assert any(
        isinstance(item, CategoricalCategoricalRelationship)
        for item in summary.relationships
    )
    assert analysis.columns[0].categorical_analysis is not None
    assert analysis.columns[0].evidence.frequency is not None


def test_assessor_does_not_import_pandas_or_read_a_series():
    import inspect

    import pytics.semantics.string_vocabulary as vocabulary

    source = inspect.getsource(vocabulary)
    assert "import pandas" not in source
    assert "import numpy" not in source
    assert "pd." not in source
    assessment = assess_categorical_candidate
    assert "series" not in inspect.signature(assessment).parameters
