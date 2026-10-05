"""TSK-045: representation evidence and short-label categorical support.

Fixtures use neutral values. Column names are identity only. No case
folds, strips, or parses the source.
"""

from __future__ import annotations

import inspect
import uuid

import pandas as pd
import pytest

from pytics.analysis.column import ColumnEvidence
from pytics.analysis.column import analyze_series
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.core_candidates import assess_categorical_candidate
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.representation_evidence import MATERIAL_MIN_COUNT
from pytics.semantics.representation_evidence import MATERIAL_PROPORTION_DENOMINATOR
from pytics.semantics.representation_evidence import MAX_LABEL_LENGTH
from pytics.semantics.representation_evidence import MAX_LABEL_TOKENS
from pytics.semantics.representation_evidence import PROSE_MIN_TOKENS
from pytics.semantics.representation_evidence import RepresentationEvidence
from pytics.semantics.representation_evidence import RepresentationFamily
from pytics.semantics.representation_evidence import RepresentationMixture
from pytics.semantics.representation_evidence import collect_representation_evidence
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.string_structure_evidence import collect_string_structure_evidence
from pytics.semantics.string_vocabulary import repeated_ordinary_label_support
from pytics.semantics import representation_evidence as representation_module

_ORDINARY = "A reused vocabulary of short labels supports a Categorical reading."
_LETTER = (
    "A reused vocabulary of unpunctuated letter-bearing labels "
    "supports a Categorical reading."
)
_COMPACT_A = uuid.UUID(int=1).hex
_COMPACT_B = uuid.UUID(int=2).hex
_UUID_A = str(uuid.UUID(int=1))
_UUID_B = str(uuid.UUID(int=2))


def _family(value: str) -> RepresentationFamily:
    series = pd.Series([value], dtype=object)
    evidence = _collect(series)
    present = evidence.positive_families()
    assert len(present) == 1
    return present[0]


def _collect(series: pd.Series):
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    return collect_representation_evidence(series, structure, physical)


def _categorical_statement(series: pd.Series) -> str | None:
    analysis = analyze_series(series)
    for candidate in analysis.inferred.resolution.candidates:
        if candidate.semantic_type is not SemanticType.CATEGORICAL:
            continue
        if candidate.disposition is not CandidateDisposition.SUPPORTED:
            return None
        return candidate.supporting_evidence[0].statement
    return None


def test_representation_constants_stay_explicit():
    assert MAX_LABEL_TOKENS == 4
    assert MAX_LABEL_LENGTH == 40
    assert PROSE_MIN_TOKENS == 6
    assert MATERIAL_MIN_COUNT == 2
    assert MATERIAL_PROPORTION_DENOMINATOR == 20


def test_module_does_not_parse_or_rewrite_source_values():
    source = inspect.getsource(representation_module)
    assert "to_datetime" not in source
    assert "to_numeric" not in source
    assert "import pandas" in source


@pytest.mark.parametrize(
    ("value", "family"),
    [
        ("2021-02-16", RepresentationFamily.TEMPORAL_LIKE),
        ("16/03/2020", RepresentationFamily.TEMPORAL_LIKE),
        ("16-03-2020", RepresentationFamily.TEMPORAL_LIKE),
        ("22 Oct 23", RepresentationFamily.TEMPORAL_LIKE),
        ("1 September 2024", RepresentationFamily.TEMPORAL_LIKE),
        ("2024-01-01T10:30:00", RepresentationFamily.TEMPORAL_LIKE),
        ("2024-01-01T10:30:00Z", RepresentationFamily.TEMPORAL_LIKE),
        ("2024-01-01T10:30:00.123", RepresentationFamily.TEMPORAL_LIKE),
        ("2024-01-01T10:30:00.123Z", RepresentationFamily.TEMPORAL_LIKE),
        ("2024-01-01T10:30:00+00:00", RepresentationFamily.TEMPORAL_LIKE),
        ("Q1 2016", RepresentationFamily.QUARTER_YEAR_LIKE),
        ("q3 2024", RepresentationFamily.QUARTER_YEAR_LIKE),
        ("2016 Q1", RepresentationFamily.QUARTER_YEAR_LIKE),
        ("45390", RepresentationFamily.NUMERIC_LIKE),
        ("5000000", RepresentationFamily.NUMERIC_LIKE),
        ("17k", RepresentationFamily.NUMERIC_LIKE),
        ("3k", RepresentationFamily.NUMERIC_LIKE),
        ("2.5", RepresentationFamily.NUMERIC_LIKE),
        ("12,000", RepresentationFamily.NUMERIC_LIKE),
        ("€2.5m", RepresentationFamily.CURRENCY_LIKE),
        ("USD 250000", RepresentationFamily.CURRENCY_LIKE),
        ("USD250000", RepresentationFamily.CURRENCY_LIKE),
        ("12,000,000 USD", RepresentationFamily.CURRENCY_LIKE),
        ("$1M-$5M", RepresentationFamily.CURRENCY_LIKE),
        ("1-10", RepresentationFamily.RANGE_LIKE),
        ("51-200", RepresentationFamily.RANGE_LIKE),
        ("500+", RepresentationFamily.RANGE_LIKE),
        ("1,000+", RepresentationFamily.RANGE_LIKE),
        ("127 employees", RepresentationFamily.UNIT_COUNT_LIKE),
        ("3 deals", RepresentationFamily.UNIT_COUNT_LIKE),
        ("1 stars", RepresentationFamily.UNIT_COUNT_LIKE),
        ("67/100", RepresentationFamily.SCORE_LIKE),
        ("unknown", RepresentationFamily.MISSING_LIKE),
        ("N/A", RepresentationFamily.MISSING_LIKE),
        ("na", RepresentationFamily.MISSING_LIKE),
        ("none", RepresentationFamily.MISSING_LIKE),
        ("NULL", RepresentationFamily.MISSING_LIKE),
        ("missing", RepresentationFamily.MISSING_LIKE),
        ("New York", RepresentationFamily.LABEL_LIKE),
        ("South Korea", RepresentationFamily.LABEL_LIKE),
        ("São Paulo", RepresentationFamily.LABEL_LIKE),
        ("Closed Won", RepresentationFamily.LABEL_LIKE),
        ("R&D", RepresentationFamily.LABEL_LIKE),
        ("B2B", RepresentationFamily.LABEL_LIKE),
        ("HubSpot (US)", RepresentationFamily.LABEL_LIKE),
        ("O'Brien", RepresentationFamily.LABEL_LIKE),
        (" US ", RepresentationFamily.PADDED),
        (" unknown ", RepresentationFamily.PADDED),
        (" 2021-02-16", RepresentationFamily.PADDED),
        ("", RepresentationFamily.BLANK),
        ("   ", RepresentationFamily.BLANK),
        ("ada@example.com", RepresentationFamily.EMAIL_LIKE),
        ("https://example.com/a", RepresentationFamily.URL_LIKE),
        ("www.example.com", RepresentationFamily.URL_LIKE),
        (
            "The river is wide and the road is long today.",
            RepresentationFamily.PROSE_LIKE,
        ),
        ("one two three four five six", RepresentationFamily.PROSE_LIKE),
        ("one two three four five", RepresentationFamily.OTHER),
        ("hello!", RepresentationFamily.OTHER),
        ("a@b", RepresentationFamily.OTHER),
        ("http://localhost", RepresentationFamily.OTHER),
        ("europe 1", RepresentationFamily.LABEL_LIKE),
        ("last contacted Q4", RepresentationFamily.LABEL_LIKE),
        ("a @b.co", RepresentationFamily.OTHER),
        ("@example.com", RepresentationFamily.OTHER),
        ("a@b@c.com", RepresentationFamily.OTHER),
        ("user@.example.com", RepresentationFamily.OTHER),
        ("North\tSide", RepresentationFamily.OTHER),
        ("16-03-2020T10:30:00", RepresentationFamily.OTHER),
        ("2024-01-01T10-30:00", RepresentationFamily.OTHER),
        ("2024-01-01Taa:30:00", RepresentationFamily.OTHER),
        ("2024-01-01T10:30:00.Z", RepresentationFamily.PROSE_LIKE),
        ("2024-01-01T10:30:00+0a:00", RepresentationFamily.PROSE_LIKE),
        ("2024-01-01T10:30:00UTC", RepresentationFamily.OTHER),
        ("2024-01-01T10:30:00z", RepresentationFamily.TEMPORAL_LIKE),
        ("ab/cd/2020", RepresentationFamily.OTHER),
        ("11/2/3", RepresentationFamily.OTHER),
        ("100/2/2020", RepresentationFamily.OTHER),
        ("22 Foo 23", RepresentationFamily.LABEL_LIKE),
        ("Q12016", RepresentationFamily.LABEL_LIKE),
        ("USD  250000", RepresentationFamily.CURRENCY_LIKE),
        ("12  USD", RepresentationFamily.CURRENCY_LIKE),
        ("250000USD", RepresentationFamily.CURRENCY_LIKE),
        ("1+10", RepresentationFamily.OTHER),
        ("1-", RepresentationFamily.OTHER),
        (".5", RepresentationFamily.OTHER),
        ("5.", RepresentationFamily.OTHER),
    ],
)
def test_one_original_string_has_one_family(value: str, family: RepresentationFamily):
    assert _family(value) is family


def test_identity_syntax_is_one_family_and_not_a_second_pattern_count():
    assert _family(_UUID_A) is RepresentationFamily.IDENTITY_SYNTAX
    assert _family(_COMPACT_A) is RepresentationFamily.IDENTITY_SYNTAX
    wide = "ab" * 20
    assert len(wide) == 40
    assert _family(wide) is RepresentationFamily.IDENTITY_SYNTAX
    evidence = _collect(pd.Series([_UUID_A, _COMPACT_A], dtype=object))
    assert evidence.count(RepresentationFamily.IDENTITY_SYNTAX) == 2
    assert "uuid_count" not in evidence.__dict__


def test_counts_partition_the_non_missing_population():
    series = pd.Series(
        ["New York", "", "  ", "2021-02-16", "unknown", None],
        dtype=object,
    )
    evidence = _collect(series)
    population = evidence.string_structure.basic.n_non_missing
    assert population == 5
    assert sum(evidence.counts) == population
    assert evidence.count(RepresentationFamily.BLANK) == (
        evidence.string_structure.empty_string_count
        + evidence.string_structure.whitespace_only_count
    )
    assert evidence.ratio(RepresentationFamily.LABEL_LIKE) == 1 / 5
    assert evidence.ratio(RepresentationFamily.EMAIL_LIKE) == 0.0
    assert evidence.positive_families() == (
        RepresentationFamily.BLANK,
        RepresentationFamily.MISSING_LIKE,
        RepresentationFamily.TEMPORAL_LIKE,
        RepresentationFamily.LABEL_LIKE,
    )


def test_all_missing_string_column_has_undefined_ratios():
    series = pd.Series([pd.NA, pd.NA], dtype="string")
    evidence = _collect(series)
    assert sum(evidence.counts) == 0
    assert evidence.ratio(RepresentationFamily.LABEL_LIKE) is None
    assert evidence.mixture is RepresentationMixture.NONE


def test_mixture_distinguishes_absence_observation_and_conflict():
    absent = analyze_series(pd.Series(["???", "!!!", "???"], dtype=object))
    observed = analyze_series(
        pd.Series(["2021-02-16", "16/03/2020", "22 Oct 23"], dtype=object)
    )
    conflicting = analyze_series(
        pd.Series(["2021-02-16", "16/03/2020", "45390", "45391"], dtype=object)
    )
    stray = analyze_series(
        pd.Series(["2021-02-16"] * 20 + ["45390"], dtype=object)
    )
    for analysis in (absent, observed, conflicting, stray):
        assert analysis.inferred.selected_type is None
        assert analysis.inferred.resolution.status is (
            ResolutionStatus.INSUFFICIENT_EVIDENCE
        )
        assert analysis.inferred.resolution.reason == "No candidate is supported."
    assert absent.evidence.representation.mixture is RepresentationMixture.NONE
    assert observed.evidence.representation.mixture is RepresentationMixture.OBSERVED
    assert observed.evidence.representation.ratio(
        RepresentationFamily.TEMPORAL_LIKE
    ) == 1.0
    assert conflicting.evidence.representation.mixture is (
        RepresentationMixture.CONFLICTING
    )
    assert stray.evidence.representation.mixture is RepresentationMixture.OBSERVED
    assert stray.evidence.representation.count(RepresentationFamily.NUMERIC_LIKE) == 1


def test_currency_and_ranges_stay_one_numeric_signal_without_conversion():
    series = pd.Series(
        ["€2.5m", "$1M-$5M", "5000000", "1-10", "17k", "USD 250000"],
        dtype=object,
    )
    original = series.copy(deep=True)
    analysis = analyze_series(series)
    pd.testing.assert_series_equal(series, original)
    assert analysis.inferred.selected_type is None
    assert analysis.evidence.basic.n_missing == 0
    evidence = analysis.evidence.representation
    assert evidence.mixture is RepresentationMixture.OBSERVED
    assert evidence.count(RepresentationFamily.CURRENCY_LIKE) == 3
    assert evidence.count(RepresentationFamily.RANGE_LIKE) == 1
    assert evidence.count(RepresentationFamily.NUMERIC_LIKE) == 2
    assert analysis.numeric_analysis is None


def test_missing_like_literals_do_not_become_missing():
    series = pd.Series(["unknown", "n/a", "NA", "none", "NULL"], dtype=object)
    original = series.copy(deep=True)
    analysis = analyze_series(series)
    pd.testing.assert_series_equal(series, original)
    assert series.dtype == original.dtype
    assert analysis.evidence.basic.n_missing == 0
    assert analysis.evidence.basic.n_non_missing == 5
    assert (
        analysis.evidence.representation.count(RepresentationFamily.MISSING_LIKE) == 5
    )
    assert analysis.inferred.selected_type is None


def test_clean_letter_labels_keep_the_unpunctuated_rule():
    series = pd.Series(["red", "blue", "red", "green"], dtype=object)
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert _categorical_statement(series) == _LETTER
    assert (
        analysis.evidence.representation.count(RepresentationFamily.LABEL_LIKE) == 4
    )


@pytest.mark.parametrize("dtype", ["string", object])
def test_multiword_and_punctuated_labels_resolve_categorical(dtype):
    series = pd.Series(
        ["New York", "South Korea", "New York", "R&D", "B2B", "R&D"],
        dtype=dtype,
    )
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.inferred.interpretation is None
    assert _categorical_statement(series) == _ORDINARY
    assert [level.value for level in analysis.categorical_analysis.levels] == [
        "New York",
        "South Korea",
        "R&D",
        "B2B",
    ]


def test_case_variants_stay_distinct_categorical_levels():
    series = pd.Series(
        ["United States", "UNITED STATES", "united states", "United States"],
        dtype=object,
    )
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert [level.value for level in analysis.categorical_analysis.levels] == [
        "United States",
        "UNITED STATES",
        "united states",
    ]


def test_imbalanced_labels_with_missing_values_stay_categorical():
    series = pd.Series(
        ["New York"] * 8 + ["Paris", None, pd.NA],
        dtype=object,
    )
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.evidence.basic.n_missing == 2
    assert [level.value for level in analysis.categorical_analysis.levels] == [
        "New York",
        "Paris",
    ]


def test_moderate_cardinality_multiword_labels_resolve_categorical():
    names = [f"Area {index:02d}" for index in range(20)]
    values = [names[index % 20] for index in range(100)]
    analysis = analyze_series(pd.Series(values, dtype=object))
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert analysis.evidence.basic.n_unique_non_missing == 20


def test_repeated_prose_is_not_categorical():
    sentence = "The river is wide and the road is long today."
    other = "Another short note about the same city and its harbor."
    series = pd.Series([sentence, other] * 50, dtype=object)
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is None
    evidence = analysis.evidence.representation
    assert evidence.count(RepresentationFamily.PROSE_LIKE) == 100
    assert evidence.count(RepresentationFamily.LABEL_LIKE) == 0
    assert evidence.mixture is RepresentationMixture.OBSERVED
    text = next(
        candidate
        for candidate in analysis.inferred.resolution.candidates
        if candidate.semantic_type is SemanticType.TEXT
    )
    assert text.disposition is CandidateDisposition.NOT_SUPPORTED


def test_near_unique_and_unique_strings_stay_unresolved():
    unique = pd.Series([f"label {index}" for index in range(30)], dtype=object)
    near = pd.Series(
        [f"label {index}" for index in range(80)] + ["label 0"] * 20,
        dtype=object,
    )
    for series in (unique, near):
        analysis = analyze_series(series)
        assert analysis.inferred.selected_type is None
        assert analysis.evidence.representation.mixture is (
            RepresentationMixture.OBSERVED
        )
        assert (
            analysis.evidence.representation.count(RepresentationFamily.LABEL_LIKE)
            == analysis.evidence.basic.n_non_missing
        )


def test_emails_urls_and_uuids_do_not_become_categorical():
    emails = pd.Series(
        ["ada@example.com", "grace@example.com", "ada@example.com"],
        dtype=object,
    )
    urls = pd.Series(
        ["https://example.com/a", "https://example.com/b", "https://example.com/a"],
        dtype="string",
    )
    email_analysis = analyze_series(emails)
    url_analysis = analyze_series(urls)
    assert email_analysis.inferred.selected_type is None
    assert url_analysis.inferred.selected_type is None
    assert (
        email_analysis.evidence.representation.count(RepresentationFamily.EMAIL_LIKE)
        == 3
    )
    assert (
        url_analysis.evidence.representation.count(RepresentationFamily.URL_LIKE) == 3
    )
    compact = analyze_series(pd.Series([_COMPACT_A, _COMPACT_B, _COMPACT_A]))
    assert compact.inferred.selected_type is SemanticType.IDENTIFIER
    assert (
        compact.evidence.representation.count(RepresentationFamily.IDENTITY_SYNTAX)
        == 3
    )
    hyphenated = analyze_series(
        pd.Series([_UUID_A, _UUID_B, _UUID_A], dtype=object)
    )
    assert hyphenated.inferred.selected_type is SemanticType.IDENTIFIER


def test_ipv4_strings_stay_on_pattern_evidence():
    series = pd.Series(["192.0.2.1", "198.51.100.2", "192.0.2.1"], dtype=object)
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is None
    assert analysis.evidence.pattern.ipv4_count == 3
    assert analysis.evidence.representation.mixture is RepresentationMixture.NONE


def test_padding_and_missing_literals_do_not_conflict_with_labels():
    places = pd.Series(
        ["United States", "Germany", " France ", "United States", "Germany"],
        dtype=object,
    )
    stages = pd.Series(
        ["lead", "customer", "unknown", "lead", "customer", "unknown"],
        dtype=object,
    )
    original_places = places.copy(deep=True)
    original_stages = stages.copy(deep=True)
    place_analysis = analyze_series(places)
    stage_analysis = analyze_series(stages)
    pd.testing.assert_series_equal(places, original_places)
    pd.testing.assert_series_equal(stages, original_stages)
    assert place_analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert stage_analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert place_analysis.evidence.basic.n_missing == 0
    assert stage_analysis.evidence.basic.n_missing == 0
    assert [level.value for level in place_analysis.categorical_analysis.levels] == [
        "United States",
        "Germany",
        " France ",
    ]
    assert [level.value for level in stage_analysis.categorical_analysis.levels] == [
        "lead",
        "customer",
        "unknown",
    ]
    assert (
        place_analysis.evidence.representation.count(RepresentationFamily.PADDED) == 1
    )
    assert place_analysis.evidence.representation.mixture is (
        RepresentationMixture.OBSERVED
    )
    assert (
        stage_analysis.evidence.representation.count(RepresentationFamily.MISSING_LIKE)
        == 2
    )
    assert stage_analysis.evidence.representation.mixture is (
        RepresentationMixture.OBSERVED
    )


def test_padding_does_not_make_a_non_label_column_categorical():
    series = pd.Series(
        [" 2021-02-16 ", " 2020-01-01 ", "US", " 2021-02-16 ", " 2020-01-01 "],
        dtype=object,
    )
    original = series.copy(deep=True)
    analysis = analyze_series(series)
    pd.testing.assert_series_equal(series, original)
    assert analysis.inferred.selected_type is None
    assert analysis.evidence.representation.count(RepresentationFamily.PADDED) == 4
    assert analysis.evidence.representation.count(RepresentationFamily.LABEL_LIKE) == 1
    assert analysis.evidence.representation.mixture is RepresentationMixture.OBSERVED


def test_one_other_core_family_blocks_categorical_without_conflict():
    series = pd.Series(
        ["United States", "Germany", "United States", "2024-01-01"],
        dtype=object,
    )
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is None
    assert analysis.evidence.representation.count(RepresentationFamily.TEMPORAL_LIKE) == 1
    assert analysis.evidence.representation.mixture is RepresentationMixture.OBSERVED


def test_empty_strings_block_categorical_and_stay_literal():
    blank = pd.Series(["US", "", "US"], dtype=object)
    original_blank = blank.copy(deep=True)
    blank_analysis = analyze_series(blank)
    pd.testing.assert_series_equal(blank, original_blank)
    assert blank_analysis.inferred.selected_type is None
    assert (
        blank_analysis.evidence.representation.count(RepresentationFamily.BLANK) == 1
    )


def test_long_unpunctuated_token_stays_categorical_by_the_letter_rule():
    token = "x" * 80
    series = pd.Series([token, "short", token], dtype="string")
    analysis = analyze_series(series)
    assert analysis.inferred.selected_type is SemanticType.CATEGORICAL
    assert _categorical_statement(series) == _LETTER
    evidence = analysis.evidence.representation
    assert evidence.count(RepresentationFamily.OTHER) == 2
    assert evidence.count(RepresentationFamily.LABEL_LIKE) == 1
    assert evidence.count(RepresentationFamily.PROSE_LIKE) == 0


def test_numeric_storage_has_no_representation_evidence():
    analysis = analyze_series(pd.Series([2007, 2008, 2009, 2007]))
    assert analysis.inferred.selected_type is SemanticType.NUMERIC
    assert analysis.evidence.representation is None
    assert analysis.evidence.string_structure is None


def test_column_name_and_series_name_are_not_evidence():
    dates = pd.Series(
        ["2021-02-16", "16/03/2020", "2021-02-16"],
        dtype=object,
        name="category",
    )
    places = pd.Series(
        ["New York", "Paris", "New York"],
        dtype=object,
        name="created_date",
    )
    by_label = analyze_series(places, label="revenue")
    assert analyze_series(dates).inferred.selected_type is None
    assert by_label.inferred.selected_type is SemanticType.CATEGORICAL
    assert by_label.label == "revenue"


def test_ordinary_support_withholds_when_the_bundle_does_not_apply():
    series = pd.Series(["New York", "Paris", "New York"], dtype=object)
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    other = collect_string_structure_evidence(series, basic, physical)
    representation = collect_representation_evidence(series, structure, physical)
    other_pattern = collect_pattern_evidence(series, other, physical)
    assert repeated_ordinary_label_support(basic, structure, None, representation) == ()
    assert (
        repeated_ordinary_label_support(
            basic,
            other,
            other_pattern,
            representation,
        )
        == ()
    )
    uuid_series = pd.Series([_UUID_A, _UUID_B, _UUID_A], dtype=object)
    uuid_basic = collect_basic_column_evidence(uuid_series)
    uuid_physical = classify_physical_dtype(uuid_series)
    uuid_structure = collect_string_structure_evidence(
        uuid_series,
        uuid_basic,
        uuid_physical,
    )
    uuid_pattern = collect_pattern_evidence(uuid_series, uuid_structure, uuid_physical)
    uuid_counts = [0] * len(RepresentationFamily)
    uuid_counts[list(RepresentationFamily).index(RepresentationFamily.LABEL_LIKE)] = (
        uuid_basic.n_non_missing
    )
    claimed_uuid = RepresentationEvidence(uuid_structure, tuple(uuid_counts))
    assert (
        repeated_ordinary_label_support(
            uuid_basic,
            uuid_structure,
            uuid_pattern,
            claimed_uuid,
        )
        == ()
    )
    unique = pd.Series(["New York", "Paris", "Chicago"], dtype=object)
    unique_basic = collect_basic_column_evidence(unique)
    unique_physical = classify_physical_dtype(unique)
    unique_structure = collect_string_structure_evidence(
        unique,
        unique_basic,
        unique_physical,
    )
    unique_pattern = collect_pattern_evidence(unique, unique_structure, unique_physical)
    unique_representation = collect_representation_evidence(
        unique,
        unique_structure,
        unique_physical,
    )
    assert (
        repeated_ordinary_label_support(
            unique_basic,
            unique_structure,
            unique_pattern,
            unique_representation,
        )
        == ()
    )


def test_ordinary_rule_does_not_run_without_representation_evidence():
    series = pd.Series(["New York", "Paris", "New York"], dtype=object)
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    pattern = collect_pattern_evidence(series, structure, physical)
    without = assess_categorical_candidate(
        basic,
        physical,
        string_structure=structure,
        pattern=pattern,
    )
    assert without.disposition is CandidateDisposition.NOT_SUPPORTED
    representation = collect_representation_evidence(series, structure, physical)
    with_evidence = assess_categorical_candidate(
        basic,
        physical,
        string_structure=structure,
        pattern=pattern,
        representation=representation,
    )
    assert with_evidence.disposition is CandidateDisposition.SUPPORTED
    assert with_evidence.supporting_evidence[0].statement == _ORDINARY


def test_representation_from_another_structure_is_rejected():
    series = pd.Series(["New York", "Paris"], dtype=object)
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    other = collect_string_structure_evidence(series, basic, physical)
    pattern = collect_pattern_evidence(series, other, physical)
    representation = collect_representation_evidence(series, structure, physical)
    assert other == structure
    assert other is not structure
    with pytest.raises(ValueError, match="representation evidence was not collected"):
        assess_categorical_candidate(
            basic,
            physical,
            string_structure=other,
            pattern=pattern,
            representation=representation,
        )
    with pytest.raises(TypeError, match="representation must be"):
        assess_categorical_candidate(
            basic,
            physical,
            string_structure=structure,
            pattern=collect_pattern_evidence(series, structure, physical),
            representation="counts",
        )


def test_analysis_is_deterministic_and_does_not_mutate():
    series = pd.Series(
        ["New York", "  US ", None, "€2.5m", "unknown", "New York"],
        dtype=object,
    )
    original = series.copy(deep=True)
    dtype = series.dtype
    first = analyze_series(series)
    second = analyze_series(series)
    pd.testing.assert_series_equal(series, original)
    assert series.dtype == dtype
    assert first.inferred == second.inferred
    assert first.evidence.representation == second.evidence.representation
    assert first.evidence.basic.n_missing == 1


def test_retained_evidence_does_not_store_raw_values():
    secret = "token-" + ("x" * 80) + "-secret"
    series = pd.Series(
        [secret, "The river is wide and the road is long today.", secret],
        dtype=object,
    )
    evidence = analyze_series(series).evidence.representation
    assert secret not in repr(evidence)
    assert all(type(count) is int for count in evidence.counts)
    assert len(evidence.positive_families()) <= len(RepresentationFamily)


def test_collector_rejects_ineligible_populations():
    with pytest.raises(TypeError, match="pandas Series"):
        collect_representation_evidence(object(), object(), object())
    texts = pd.Series(["aa", "bb"], dtype="string")
    text_basic = collect_basic_column_evidence(texts)
    text_physical = classify_physical_dtype(texts)
    structure = collect_string_structure_evidence(texts, text_basic, text_physical)
    with pytest.raises(TypeError, match="string_structure"):
        collect_representation_evidence(texts, "counts", text_physical)
    with pytest.raises(TypeError, match="physical must be"):
        collect_representation_evidence(texts, structure, "counts")
    numbers = pd.Series([1, 2, 3])
    basic = collect_basic_column_evidence(numbers)
    physical = classify_physical_dtype(numbers)
    with pytest.raises(TypeError, match="representation evidence applies"):
        collect_representation_evidence(numbers, structure, physical)
    mismatched = PhysicalDtype(PhysicalDtypeFamily.STRING, "not-the-dtype")
    with pytest.raises(ValueError, match="physical dtype does not match"):
        collect_representation_evidence(texts, structure, mismatched)
    mixed = pd.Series(["aa", 1], dtype=object)
    mixed_physical = classify_physical_dtype(mixed)
    with pytest.raises(TypeError, match="representation evidence applies"):
        collect_representation_evidence(mixed, structure, mixed_physical)
    empty_string = pd.Series([pd.NA, pd.NA], dtype="string")
    empty_basic = collect_basic_column_evidence(empty_string)
    empty_string_physical = classify_physical_dtype(empty_string)
    empty_structure = collect_string_structure_evidence(
        empty_string,
        empty_basic,
        empty_string_physical,
    )
    empty_object = pd.Series([None, None], dtype=object)
    empty_physical = classify_physical_dtype(empty_object)
    with pytest.raises(TypeError, match="representation evidence applies"):
        collect_representation_evidence(
            empty_object,
            empty_structure,
            empty_physical,
        )
    short = pd.Series(["aa"], dtype="string")
    with pytest.raises(ValueError, match="n_total"):
        collect_representation_evidence(short, structure, text_physical)
    assert basic.n_total == 3


def test_evidence_rejects_invalid_counts():
    series = pd.Series(["aa", "bb"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    width = len(RepresentationFamily)
    with pytest.raises(TypeError, match="tuple"):
        RepresentationEvidence(structure, [0] * width)
    with pytest.raises(ValueError, match="one int per"):
        RepresentationEvidence(structure, tuple([0] * (width - 1)))
    bool_counts = tuple(False for _ in range(width))
    with pytest.raises(TypeError, match="only ints"):
        RepresentationEvidence(structure, bool_counts)
    negative = [0] * width
    negative[0] = -1
    with pytest.raises(ValueError, match=">= 0"):
        RepresentationEvidence(structure, tuple(negative))
    over = [0] * width
    over[list(RepresentationFamily).index(RepresentationFamily.LABEL_LIKE)] = 3
    with pytest.raises(ValueError, match="sum to n_non_missing"):
        RepresentationEvidence(structure, tuple(over))
    blank = [0] * width
    blank[list(RepresentationFamily).index(RepresentationFamily.BLANK)] = 1
    blank[list(RepresentationFamily).index(RepresentationFamily.LABEL_LIKE)] = 1
    with pytest.raises(ValueError, match="blank representation"):
        RepresentationEvidence(structure, tuple(blank))
    with pytest.raises(TypeError, match="string_structure"):
        RepresentationEvidence("counts", tuple([0] * width))
    evidence = _collect(series)
    with pytest.raises(TypeError, match="family"):
        evidence.count("label_like")


def test_column_evidence_requires_the_same_string_structure():
    series = pd.Series(["aa", "bb"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    other = collect_string_structure_evidence(series, basic, physical)
    representation = collect_representation_evidence(series, structure, physical)
    with pytest.raises(TypeError, match="representation"):
        ColumnEvidence(basic=basic, representation="counts")
    with pytest.raises(ValueError, match="requires string-structure"):
        ColumnEvidence(basic=basic, representation=representation)
    with pytest.raises(ValueError, match="representation.string_structure"):
        ColumnEvidence(
            basic=basic,
            string_structure=other,
            representation=representation,
        )
    retained = ColumnEvidence(
        basic=basic,
        string_structure=structure,
        representation=representation,
    )
    assert retained.representation is representation
