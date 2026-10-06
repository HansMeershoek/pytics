"""TSK-050: weighted string evidence matches the row-wise counts.

The occurrence table is not an oracle implementation. The same collectors
run twice, once with a distinct count that keeps the per-value walk and
once with a distinct count that classifies each exact string once.
"""

from __future__ import annotations

import ipaddress

import pandas as pd
import pytest

import pytics.semantics.pattern_evidence as pattern_module
from pytics.analysis.column import analyze_series
from pytics.semantics.column_evidence import AnalyticalInapplicability
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.representation_evidence import collect_representation_evidence
from pytics.semantics.string_structure_evidence import collect_string_structure_evidence

_MIX = (
    "north",
    "  padded",
    "2020-01-15",
    "12345",
    "user@example.com",
    "https://example.com/a",
    "192.168.0.1",
    "550e8400-e29b-41d4-a716-446655440000",
    "the quick brown fox jumps over",
)
_UUID = "550e8400-e29b-41d4-a716-446655440000"


def _cycle(
    values: tuple[str, ...] | list[str], rows: int, dtype: object = object
) -> pd.Series:
    return pd.Series(
        [values[index % len(values)] for index in range(rows)], dtype=dtype
    )


def _facts(structure, pattern, representation) -> tuple:
    return (
        structure.empty_string_count,
        structure.whitespace_only_count,
        structure.contains_whitespace_count,
        structure.contains_alpha_count,
        structure.contains_digit_count,
        structure.contains_other_count,
        structure.min_length,
        structure.max_length,
        pattern.uuid_count,
        pattern.ipv4_count,
        pattern.ipv6_count,
        pattern.hex_32_count,
        pattern.hex_40_count,
        pattern.hex_64_count,
        pattern.hex_128_count,
        representation.counts,
        representation.positive_families(),
        representation.mixture,
    )


def _with_unique(series: pd.Series, n_unique: int) -> BasicColumnEvidence:
    basic = collect_basic_column_evidence(series)
    return BasicColumnEvidence(
        n_total=basic.n_total,
        n_missing=basic.n_missing,
        n_non_missing=basic.n_non_missing,
        n_unique_non_missing=n_unique,
    )


def _collect(series: pd.Series, n_unique: int):
    physical = classify_physical_dtype(series)
    basic = _with_unique(series, n_unique)
    structure = collect_string_structure_evidence(series, basic, physical)
    pattern = collect_pattern_evidence(series, structure, physical)
    representation = collect_representation_evidence(series, structure, physical)
    assert structure.basic is basic
    assert pattern.string_structure is structure
    assert representation.string_structure is structure
    return structure, pattern, representation


def _assert_paths_agree(series: pd.Series) -> None:
    population = int(collect_basic_column_evidence(series).n_non_missing)
    assert population > 0
    row = _collect(series, population)
    weighted = _collect(series, 0)
    assert _facts(*row) == _facts(*weighted)


def _assert_analysis_matches_real_path(series: pd.Series) -> None:
    again = analyze_series(series)
    once = analyze_series(series)
    assert once == again
    evidence = once.evidence
    if evidence.string_structure is None:
        return
    population = evidence.basic.n_non_missing
    unique = evidence.basic.n_unique_non_missing
    assert unique is not None
    forced = population if unique * 2 <= population else 0
    structure, pattern, representation = _collect(series, forced)
    assert _facts(
        evidence.string_structure, evidence.pattern, evidence.representation
    ) == (_facts(structure, pattern, representation))


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(_cycle(("alpha", "beta", "gamma", "delta"), 40), id="labels"),
        pytest.param(
            pd.Series([f"v{index:05d}" for index in range(30)], dtype=object),
            id="all-distinct",
        ),
        pytest.param(
            _cycle(("2020-01-15", "16/03/2020", "22 Oct 23"), 24), id="temporal"
        ),
        pytest.param(
            _cycle(("user@example.com", "other@example.org"), 20),
            id="emails",
        ),
        pytest.param(
            _cycle(("https://example.com/a", "www.example.org"), 20),
            id="urls",
        ),
        pytest.param(_cycle(("192.168.0.1", "10.0.0.2"), 20), id="ipv4"),
        pytest.param(_cycle((_UUID, "2001:db8::1"), 16), id="uuid-and-ipv6"),
        pytest.param(_cycle(("ab" * 16,), 4, dtype="string"), id="compact-hex"),
        pytest.param(_cycle(("  padded", "padded  ", "alpha"), 18), id="padded"),
        pytest.param(_cycle(("", "   ", "x"), 15), id="blanks"),
        pytest.param(_cycle(("NA", "n/a", "none", "unknown"), 16), id="missing-like"),
        pytest.param(
            _cycle(
                ("the quick brown fox jumps over", "one two three four five six"), 12
            ),
            id="prose",
        ),
        pytest.param(_cycle(_MIX, 36), id="nine-shapes"),
        pytest.param(_cycle(("alpha", "beta"), 20, dtype="string"), id="pandas-string"),
        pytest.param(
            pd.Series(
                [
                    "".join(("x", "alpha" if index % 2 == 0 else "beta"))[1:]
                    for index in range(20)
                ],
                dtype=object,
            ),
            id="distinct-objects",
        ),
        pytest.param(
            pd.Series(
                ["alpha", None, "beta", "alpha", pd.NA, "beta"] * 4, dtype=object
            ),
            id="missing-mixed",
        ),
        pytest.param(pd.Series(["only"], dtype=object), id="one-row"),
        pytest.param(pd.Series(["alpha"] * 12, dtype=object), id="all-equal"),
    ],
)
def test_weighted_counts_match_the_row_walk(series: pd.Series) -> None:
    _assert_paths_agree(series)
    _assert_analysis_matches_real_path(series)


def test_equal_strings_with_different_identities_share_one_analysis() -> None:
    labels = ("alpha", "beta", "gamma", "delta")
    shared = _cycle(labels, 40)
    fresh = pd.Series(
        ["".join(("z", labels[index % 4]))[1:] for index in range(40)],
        dtype=object,
    )

    assert len({id(value) for value in fresh}) == 40
    assert analyze_series(shared).evidence.string_structure == (
        analyze_series(fresh).evidence.string_structure
    )
    assert (
        analyze_series(shared).evidence.pattern
        == analyze_series(fresh).evidence.pattern
    )
    assert analyze_series(shared).evidence.representation == (
        analyze_series(fresh).evidence.representation
    )
    assert analyze_series(shared).inferred == analyze_series(fresh).inferred


def test_grouped_and_shuffled_labels_keep_first_appearance_order() -> None:
    grouped = pd.Series(["alpha"] * 8 + ["beta"] * 8 + ["gamma"] * 8, dtype=object)
    shuffled = pd.Series(
        ["gamma", "alpha", "beta"] + ["alpha"] * 7 + ["beta"] * 7 + ["gamma"] * 7,
        dtype=object,
    )
    grouped_analysis = analyze_series(grouped)
    shuffled_analysis = analyze_series(shuffled)

    assert grouped_analysis.evidence.string_structure == (
        shuffled_analysis.evidence.string_structure
    )
    assert grouped_analysis.evidence.pattern == shuffled_analysis.evidence.pattern
    assert grouped_analysis.evidence.representation == (
        shuffled_analysis.evidence.representation
    )
    assert grouped_analysis.inferred == shuffled_analysis.inferred
    assert tuple(
        level.value for level in grouped_analysis.categorical_analysis.levels
    ) == ("alpha", "beta", "gamma")
    assert tuple(
        level.value for level in shuffled_analysis.categorical_analysis.levels
    ) == ("gamma", "alpha", "beta")


def test_empty_and_all_missing_columns_keep_their_current_results() -> None:
    empty_string = pd.Series([], dtype="string")
    empty_object = pd.Series([], dtype=object)
    missing_object = pd.Series([None, None], dtype=object)

    assert analyze_series(empty_string).evidence.string_structure is None
    physical = classify_physical_dtype(empty_string)
    basic = collect_basic_column_evidence(empty_string)
    structure = collect_string_structure_evidence(empty_string, basic, physical)
    assert structure.empty_string_count == 0
    assert structure.min_length is None
    assert structure.max_length is None
    for series in (empty_object, missing_object):
        analysis = analyze_series(series)
        assert analysis.evidence.string_structure is None
        series_physical = classify_physical_dtype(series)
        series_basic = collect_basic_column_evidence(series)
        with pytest.raises(AnalyticalInapplicability):
            collect_string_structure_evidence(series, series_basic, series_physical)


def test_direct_ineligible_calls_keep_their_exception_type() -> None:
    mixed = pd.Series(["a", 1, "a", "a"], dtype=object)
    blobs = pd.Series([b"ab", b"ab", b"cd", b"ab"], dtype=object)
    lists = pd.Series([[1], [1], [2], [1]], dtype=object)
    for series in (mixed, blobs, lists):
        physical = classify_physical_dtype(series)
        basic = collect_basic_column_evidence(series)
        with pytest.raises(AnalyticalInapplicability):
            collect_string_structure_evidence(series, basic, physical)
        forced = BasicColumnEvidence(
            n_total=basic.n_total,
            n_missing=basic.n_missing,
            n_non_missing=basic.n_non_missing,
            n_unique_non_missing=0,
        )
        with pytest.raises(AnalyticalInapplicability):
            collect_string_structure_evidence(series, forced, physical)


def test_pattern_rejects_a_repetitive_non_string_with_type_error() -> None:
    strings = pd.Series(["a", "b", "a", "a"], dtype=object)
    mixed = pd.Series(["a", 1, "a", "a"], dtype=object)
    physical = classify_physical_dtype(strings)
    basic = collect_basic_column_evidence(strings)
    structure = collect_string_structure_evidence(strings, basic, physical)

    with pytest.raises(TypeError, match="string-structure evidence"):
        collect_pattern_evidence(mixed, structure, physical)
    with pytest.raises(TypeError, match="string-structure evidence"):
        collect_representation_evidence(mixed, structure, physical)


def test_repetitive_collection_does_not_recompute_basic_or_frequency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    series = pd.Series(["alpha", "beta", "alpha", "beta", "alpha"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)

    def _forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("basic or frequency evidence was recomputed")

    monkeypatch.setattr(pd.Series, "nunique", _forbidden)
    monkeypatch.setattr(pd.Series, "value_counts", _forbidden)
    monkeypatch.setattr(
        "pytics.semantics.column_evidence.collect_basic_column_evidence",
        _forbidden,
    )
    structure = collect_string_structure_evidence(series, basic, physical)
    pattern = collect_pattern_evidence(series, structure, physical)
    representation = collect_representation_evidence(series, structure, physical)

    assert structure.basic is basic
    assert pattern.string_structure is structure
    assert representation.string_structure is structure
    assert structure.contains_alpha_count == 5


@pytest.mark.parametrize(
    "value, ipv4, ipv6",
    [
        ("192.168.0.1", True, False),
        ("255.255.255.255", True, False),
        ("192.168.001.1", False, False),
        ("1.2.3", False, False),
        ("1.2.3.4.5", False, False),
        ("192.168.0.1/24", False, False),
        ("::1", False, True),
        ("2001:db8::1", False, True),
        ("fe80::1%eth0", False, True),
        ("fe80::1%" + ("z" * 80), False, True),
        (":", False, False),
        ("12:30", False, False),
        ("2020-01-15T00:00:00", False, False),
        ("https://example.com/a", False, False),
        ("north", False, False),
        ("1.2.3.4", True, False),
        ("not.an.ip.address", False, False),
    ],
)
def test_ip_guards_match_ipaddress(value: str, ipv4: bool, ipv6: bool) -> None:
    assert pattern_module._is_ipv4_syntax(value) is ipv4
    assert pattern_module._is_ipv6_syntax(value) is ipv6
    assert ipv4 is _address_accepted(ipaddress.IPv4Address, value)
    assert ipv6 is _address_accepted(ipaddress.IPv6Address, value)


def test_ordinary_labels_are_not_submitted_to_ipaddress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _forbidden(_value: object) -> None:
        raise AssertionError("ipaddress was called")

    monkeypatch.setattr(pattern_module.ipaddress, "IPv4Address", _forbidden)
    monkeypatch.setattr(pattern_module.ipaddress, "IPv6Address", _forbidden)
    series = _cycle(("north", "south"), 8, dtype="string")
    analysis = analyze_series(series)

    assert analysis.evidence.pattern.ipv4_count == 0
    assert analysis.evidence.pattern.ipv6_count == 0


def test_unknown_distinct_count_keeps_the_per_value_walk() -> None:
    series = pd.Series(["ab", "ab", "cd", "cd"], dtype=object)
    physical = classify_physical_dtype(series)
    unknown = BasicColumnEvidence(
        n_total=4,
        n_missing=0,
        n_non_missing=4,
        n_unique_non_missing=None,
    )
    structure = collect_string_structure_evidence(series, unknown, physical)
    pattern = collect_pattern_evidence(series, structure, physical)
    representation = collect_representation_evidence(series, structure, physical)
    weighted = _collect(series, 0)

    assert structure.basic is unknown
    assert _facts(structure, pattern, representation) == _facts(*weighted)


def test_repeated_hex_widths_are_weighted() -> None:
    tokens = ("a" * 40, "b" * 64, "c" * 128)
    series = _cycle(tokens, 12, dtype="string")
    _assert_paths_agree(series)
    pattern = analyze_series(series).evidence.pattern

    assert pattern.hex_40_count == 4
    assert pattern.hex_64_count == 4
    assert pattern.hex_128_count == 4
    assert pattern.uuid_count == 0


def test_a_plausible_address_still_reaches_ipaddress() -> None:
    series = _cycle(("192.168.0.1", "2001:db8::1"), 8, dtype="string")
    pattern = analyze_series(series).evidence.pattern

    assert pattern.ipv4_count == 4
    assert pattern.ipv6_count == 4


def _address_accepted(constructor: type, value: str) -> bool:
    try:
        constructor(value)
    except ValueError:
        return False
    return True
