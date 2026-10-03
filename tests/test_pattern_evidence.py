"""TSK-010: full-value pattern observations over string-structure evidence."""

from __future__ import annotations

import dataclasses
import inspect
import math
from dataclasses import fields
from typing import Optional

import numpy as np
import pandas as pd
import pytest

import pytics
import pytics.semantics as semantics_package
import pytics.semantics.empty_constant as empty_constant_module
import pytics.semantics.pattern_evidence as pattern_module
import pytics.semantics.physical_boolean as physical_boolean_module
import pytics.semantics.physical_datetime as physical_datetime_module
import pytics.semantics.physical_timedelta as physical_timedelta_module
import pytics.semantics.string_structure_evidence as string_module
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.interpretation import Confidence
from pytics.semantics.interpretation import InferenceSource
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.pattern_evidence import PatternEvidence
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.physical_timedelta import interpret_series_precedence
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import (
    collect_string_structure_evidence,
)

_COUNT_FIELDS = (
    "uuid_count",
    "ipv4_count",
    "ipv6_count",
    "hex_32_count",
    "hex_40_count",
    "hex_64_count",
    "hex_128_count",
)

_CANONICAL_UUID = "550e8400-e29b-41d4-a716-446655440000"
_COMPACT_UUID = "550e8400e29b41d4a716446655440000"
_APPLICABILITY = "string-structure evidence"


class _Token(str):
    """A ``str`` subclass used to pin the ``isinstance`` contract."""


def _collect(series: pd.Series) -> PatternEvidence:
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)
    evidence = collect_pattern_evidence(series, structure, physical)
    assert evidence.string_structure is structure
    assert evidence.string_structure.basic is basic
    _assert_invariants(evidence)
    return evidence


def _basic(
    n_non_missing: int, n_unique: int, n_missing: int = 0
) -> BasicColumnEvidence:
    return BasicColumnEvidence(
        n_total=n_non_missing + n_missing,
        n_missing=n_missing,
        n_non_missing=n_non_missing,
        n_unique_non_missing=n_unique,
    )


def _structure(
    n_non_missing: int,
    n_unique: Optional[int] = None,
    n_missing: int = 0,
) -> StringStructureEvidence:
    if n_unique is None:
        n_unique = n_non_missing
    if n_non_missing == 0:
        minimum: Optional[int] = None
        maximum: Optional[int] = None
    else:
        minimum = 1
        maximum = 1
    return StringStructureEvidence(
        basic=_basic(n_non_missing, n_unique, n_missing),
        empty_string_count=0,
        whitespace_only_count=0,
        contains_whitespace_count=0,
        contains_alpha_count=0,
        contains_digit_count=0,
        contains_other_count=0,
        min_length=minimum,
        max_length=maximum,
    )


def _pattern(**overrides: object) -> PatternEvidence:
    values: dict[str, object] = {
        "string_structure": _structure(0),
        "uuid_count": 0,
        "ipv4_count": 0,
        "ipv6_count": 0,
        "hex_32_count": 0,
        "hex_40_count": 0,
        "hex_64_count": 0,
        "hex_128_count": 0,
    }
    values.update(overrides)
    return PatternEvidence(**values)  # type: ignore[arg-type]


def _hex_token(width: int, case: str = "lower") -> str:
    token = ("0123456789abcdef" * ((width // 16) + 1))[:width]
    if case == "upper":
        return token.upper()
    if case == "mixed":
        return "".join(
            character.upper() if index % 2 else character
            for index, character in enumerate(token)
        )
    return token


def _assert_ratio(value: Optional[float], expected: Optional[float]) -> None:
    if expected is None:
        assert value is None
        return
    assert type(value) is float
    assert value == expected
    assert not math.isnan(value)
    assert not math.isinf(value)


def _assert_invariants(evidence: PatternEvidence) -> None:
    denominator = evidence.string_structure.basic.n_non_missing
    for name in _COUNT_FIELDS:
        value = getattr(evidence, name)
        assert type(value) is int
        assert 0 <= value <= denominator
        _assert_ratio(
            getattr(evidence, name.removesuffix("_count") + "_ratio"),
            None if denominator == 0 else value / denominator,
        )


def _assert_only(evidence: PatternEvidence, **expected: int) -> None:
    for name in _COUNT_FIELDS:
        assert getattr(evidence, name) == expected.get(name, 0)


def test_pattern_evidence_stores_pattern_counts_only():
    evidence = _collect(pd.Series([_CANONICAL_UUID, "plain"], dtype="string"))
    names = {field.name for field in fields(evidence)}

    assert names == {
        "string_structure",
        "uuid_count",
        "ipv4_count",
        "ipv6_count",
        "hex_32_count",
        "hex_40_count",
        "hex_64_count",
        "hex_128_count",
    }
    assert "uuid_ratio" not in names
    assert evidence.uuid_count == 1
    _assert_ratio(evidence.uuid_ratio, 0.5)
    for absent in (
        "n_total",
        "n_missing",
        "n_non_missing",
        "n_unique_non_missing",
        "basic",
        "matched_values",
        "sample_matches",
        "first_match",
        "ip_count",
        "md5_count",
        "sha1_count",
        "sha256_count",
        "sha512_count",
        "dominant_pattern",
        "pattern_confidence",
        "semantic_type",
        "confidence",
    ):
        assert absent not in names
        assert not hasattr(evidence, absent)
    assert not isinstance(evidence, StringStructureEvidence)
    assert not isinstance(evidence, BasicColumnEvidence)
    assert not issubclass(PatternEvidence, StringStructureEvidence)
    assert not issubclass(PatternEvidence, BasicColumnEvidence)
    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.uuid_count = 0  # type: ignore[misc]


def test_overlapping_stored_counts_are_not_mutually_exclusive():
    evidence = _pattern(
        string_structure=_structure(1),
        uuid_count=1,
        hex_32_count=1,
    )

    assert evidence.uuid_count + evidence.hex_32_count == 2
    _assert_ratio(evidence.uuid_ratio, 1.0)
    _assert_ratio(evidence.hex_32_ratio, 1.0)


@pytest.mark.parametrize("field", _COUNT_FIELDS)
def test_non_integer_pattern_count_is_rejected(field: str):
    with pytest.raises(TypeError, match=field):
        _pattern(**{field: True})


@pytest.mark.parametrize("field", _COUNT_FIELDS)
def test_negative_pattern_count_is_rejected(field: str):
    with pytest.raises(ValueError, match=field):
        _pattern(**{field: -1})


@pytest.mark.parametrize("field", _COUNT_FIELDS)
def test_pattern_count_cannot_exceed_the_non_missing_population(field: str):
    with pytest.raises(ValueError, match="cannot exceed n_non_missing"):
        _pattern(string_structure=_structure(1), **{field: 2})


def test_pattern_evidence_requires_string_structure_evidence():
    with pytest.raises(TypeError, match="StringStructureEvidence"):
        _pattern(string_structure="structure")


@pytest.mark.parametrize("dtype", ["string", "str"])
def test_native_string_dtype_counts_full_values(dtype: str):
    series = pd.Series(["192.168.1.1", "192.168.1.1", "plain"], dtype=dtype)
    evidence = _collect(series)

    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.STRING
    _assert_only(evidence, ipv4_count=2)
    _assert_ratio(evidence.ipv4_ratio, 2 / 3)
    assert interpret_series_precedence(series) is None


def test_object_series_of_python_strings_can_carry_pattern_evidence():
    series = pd.Series(["192.168.1.1", None, "plain"], dtype=object)
    evidence = _collect(series)

    assert classify_physical_dtype(series).family is PhysicalDtypeFamily.OBJECT
    assert evidence.string_structure.basic.n_total == 3
    assert evidence.string_structure.basic.n_non_missing == 2
    _assert_only(evidence, ipv4_count=1)
    _assert_ratio(evidence.ipv4_ratio, 0.5)
    assert interpret_series_precedence(series) is None


def test_str_subclass_remains_eligible_for_pattern_evidence():
    series = pd.Series([_Token("127.0.0.1"), _Token("plain")], dtype=object)
    assert type(series.iloc[0]) is _Token
    evidence = _collect(series)

    _assert_only(evidence, ipv4_count=1)
    _assert_ratio(evidence.ipv4_ratio, 0.5)


@pytest.mark.parametrize(
    "series",
    [
        pytest.param(pd.Series([pd.NA, pd.NA], dtype="string"), id="all-missing"),
        pytest.param(pd.Series([], dtype="string"), id="zero-length"),
    ],
)
def test_empty_physical_string_population_has_undefined_ratios(series: pd.Series):
    evidence = _collect(series)

    _assert_only(evidence)
    for name in _COUNT_FIELDS:
        assert getattr(evidence, name.removesuffix("_count") + "_ratio") is None
    reading = interpret_series_precedence(series)
    assert reading is not None
    assert reading.semantic_type is SemanticType.EMPTY


def test_constant_pattern_column_keeps_constant_precedence():
    series = pd.Series(["192.168.1.1", "192.168.1.1", "192.168.1.1"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    _assert_only(evidence, ipv4_count=3)
    _assert_ratio(evidence.ipv4_ratio, 1.0)
    assert reading is not None
    assert reading.semantic_type is SemanticType.CONSTANT
    assert reading.source is InferenceSource.INFERRED
    assert reading.confidence is Confidence.HIGH


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(_CANONICAL_UUID, id="lower"),
        pytest.param(_CANONICAL_UUID.upper(), id="upper"),
        pytest.param("550E8400-e29b-41D4-a716-446655440000", id="mixed"),
    ],
)
def test_canonical_uuid_matches_and_is_not_a_hex_token(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence, uuid_count=1)
    _assert_ratio(evidence.uuid_ratio, 1.0)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(_COMPACT_UUID, id="lower"),
        pytest.param(_COMPACT_UUID.upper(), id="upper"),
        pytest.param("550E8400e29b41D4a716446655440000", id="mixed"),
    ],
)
def test_compact_uuid_matches_hex_32_as_well(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence, uuid_count=1, hex_32_count=1)
    _assert_ratio(evidence.uuid_ratio, 1.0)
    _assert_ratio(evidence.hex_32_ratio, 1.0)


def test_uuid_version_and_variant_are_not_required():
    nil = "00000000-0000-0000-0000-000000000000"
    unusual = "550e8400-e29b-f1d4-0716-446655440000"
    evidence = _collect(pd.Series([nil, unusual], dtype="string"))

    _assert_only(evidence, uuid_count=2)
    _assert_ratio(evidence.uuid_ratio, 1.0)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("550e8400-e29b-41d4-a716-44665544000", id="short"),
        pytest.param("550e8400-e29b-41d4-a716-4466554400000", id="long"),
        pytest.param("550e8400e29b-41d4-a716-446655440000", id="misplaced-hyphens"),
        pytest.param("550e8400e-29b-41d4-a716-446655440000", id="hyphen-positions"),
        pytest.param("550e8400-e29b-41d4-a716-44665544000g", id="non-hex"),
        pytest.param("{" + _CANONICAL_UUID + "}", id="braces"),
        pytest.param("urn:uuid:" + _CANONICAL_UUID, id="urn"),
        pytest.param(" " + _CANONICAL_UUID, id="leading-space"),
        pytest.param(_CANONICAL_UUID + " ", id="trailing-space"),
        pytest.param("prefix-" + _CANONICAL_UUID, id="embedded"),
        pytest.param(_CANONICAL_UUID + "-suffix", id="trailing-text"),
    ],
)
def test_malformed_uuid_shapes_do_not_match(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence)
    _assert_ratio(evidence.uuid_ratio, 0.0)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("{" + _CANONICAL_UUID + "}", id="braces"),
        pytest.param("urn:uuid:" + _CANONICAL_UUID, id="urn"),
        pytest.param("550e8400e29b-41d4-a716-446655440000", id="misplaced-hyphens"),
    ],
)
def test_permissive_uuid_parser_cannot_widen_the_shape(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
):
    def _forbidden(text: str) -> None:
        raise AssertionError(f"uuid.UUID was consulted for {text!r}")

    monkeypatch.setattr(pattern_module.uuid, "UUID", _forbidden)
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence)


def test_uuid_parser_rejection_does_not_count(monkeypatch: pytest.MonkeyPatch):
    def _reject(text: str) -> None:
        raise ValueError(text)

    monkeypatch.setattr(pattern_module.uuid, "UUID", _reject)
    evidence = _collect(pd.Series([_CANONICAL_UUID], dtype="string"))

    _assert_only(evidence)
    _assert_ratio(evidence.uuid_ratio, 0.0)


@pytest.mark.parametrize(
    "value",
    [
        "0.0.0.0",
        "127.0.0.1",
        "192.168.1.1",
        "255.255.255.255",
    ],
)
def test_valid_ipv4_addresses_match(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence, ipv4_count=1)
    _assert_ratio(evidence.ipv4_ratio, 1.0)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("256.1.1.1", id="out-of-range"),
        pytest.param("192.168.1", id="shortened"),
        pytest.param("192.168.1.1.5", id="extra-component"),
        pytest.param("192.168.001.001", id="leading-zeros"),
        pytest.param("192.168.1.1/24", id="cidr"),
        pytest.param(" 192.168.1.1", id="leading-space"),
        pytest.param("192.168.1.1 ", id="trailing-space"),
        pytest.param("IP=192.168.1.1", id="embedded"),
        pytest.param("192.168.1.1/32", id="host-cidr"),
    ],
)
def test_invalid_ipv4_text_does_not_match(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence)
    _assert_ratio(evidence.ipv4_ratio, 0.0)


@pytest.mark.parametrize(
    "value",
    [
        "::1",
        "2001:db8::1",
        "fe80::1",
        "2001:0db8:0000:0000:0000:0000:0000:0001",
        "2001:DB8::1",
        "FE80::1",
    ],
)
def test_valid_ipv6_addresses_match(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence, ipv6_count=1)
    _assert_ratio(evidence.ipv6_ratio, 1.0)
    _assert_ratio(evidence.ipv4_ratio, 0.0)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("1:2:3:4:5:6:7:8:9", id="too-many-groups"),
        pytest.param("2001:db8::gggg", id="non-hex"),
        pytest.param("2001::db8::1", id="malformed-compression"),
        pytest.param("::1/128", id="cidr"),
        pytest.param("2001:db8::/32", id="network-cidr"),
        pytest.param(" ::1", id="leading-space"),
        pytest.param("::1 ", id="trailing-space"),
        pytest.param("ip=::1", id="embedded"),
        pytest.param("prefix-2001:db8::1", id="prefix"),
    ],
)
def test_invalid_ipv6_text_does_not_match(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence)
    _assert_ratio(evidence.ipv6_ratio, 0.0)


def test_ipv4_mapped_ipv6_is_not_also_ipv4():
    evidence = _collect(pd.Series(["::ffff:192.0.2.1"], dtype="string"))

    _assert_only(evidence, ipv6_count=1)


def test_one_address_is_not_counted_in_both_ip_families():
    ipv4 = _collect(pd.Series(["192.168.1.1"], dtype="string"))
    ipv6 = _collect(pd.Series(["2001:db8::1"], dtype="string"))

    _assert_only(ipv4, ipv4_count=1)
    _assert_only(ipv6, ipv6_count=1)


@pytest.mark.parametrize("width", [32, 40, 64, 128])
@pytest.mark.parametrize("case", ["lower", "upper", "mixed"])
def test_fixed_width_hex_tokens_match_only_that_width(width: int, case: str):
    field = f"hex_{width}_count"
    evidence = _collect(pd.Series([_hex_token(width, case)], dtype="string"))

    assert getattr(evidence, field) == 1
    if width == 32:
        _assert_only(evidence, hex_32_count=1, uuid_count=1)
    else:
        _assert_only(evidence, **{field: 1})
        assert evidence.uuid_count == 0


@pytest.mark.parametrize("width", [32, 40, 64, 128])
def test_wrong_hex_lengths_do_not_match(width: int):
    short = _hex_token(width)[:-1]
    long = _hex_token(width) + "a"
    evidence = _collect(pd.Series([short, long], dtype="string"))

    _assert_only(evidence)
    _assert_ratio(evidence.hex_32_ratio, 0.0)


@pytest.mark.parametrize("width", [32, 40, 64, 128])
def test_non_hex_character_does_not_match_a_token_width(width: int):
    token = _hex_token(width)[:-1] + "g"
    evidence = _collect(pd.Series([token], dtype="string"))

    _assert_only(evidence)


@pytest.mark.parametrize("width", [32, 40, 64, 128])
def test_hex_prefix_is_not_stripped(width: int):
    token = "0x" + _hex_token(width)[: width - 2]
    evidence = _collect(pd.Series([token], dtype="string"))

    assert len(token) == width
    _assert_only(evidence)


@pytest.mark.parametrize("width", [32, 40, 64, 128])
@pytest.mark.parametrize("separator", ["-", ":", "_"])
def test_hex_separators_are_not_removed(width: int, separator: str):
    body = _hex_token(width)
    token = body[: width // 2] + separator + body[(width // 2) + 1 :]
    evidence = _collect(pd.Series([token], dtype="string"))

    assert len(token) == width
    _assert_only(evidence)


@pytest.mark.parametrize("width", [32, 40, 64, 128])
def test_hex_whitespace_is_not_stripped(width: int):
    token = " " + _hex_token(width)[: width - 1]
    evidence = _collect(pd.Series([token], dtype="string"))

    assert len(token) == width
    _assert_only(evidence)


def test_unicode_digits_are_not_ascii_hexadecimal_tokens():
    token = "\uff10" * 32
    series = pd.Series([token], dtype="string")
    evidence = _collect(series)

    assert evidence.string_structure.contains_digit_count == 1
    _assert_only(evidence)
    _assert_ratio(evidence.hex_32_ratio, 0.0)
    _assert_ratio(evidence.uuid_ratio, 0.0)


def test_digit_only_width_32_is_hex_and_compact_uuid():
    evidence = _collect(pd.Series(["1" * 32], dtype="string"))

    _assert_only(evidence, uuid_count=1, hex_32_count=1)


def test_pattern_counts_overlap_without_a_winner():
    canonical = _CANONICAL_UUID
    compact = _COMPACT_UUID
    evidence = _collect(pd.Series([compact, canonical, "192.168.1.1"], dtype="string"))

    assert evidence.uuid_count == 2
    assert evidence.hex_32_count == 1
    assert evidence.ipv4_count == 1
    assert (
        evidence.uuid_count + evidence.hex_32_count + evidence.ipv4_count
        > evidence.string_structure.basic.n_non_missing
    )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty"),
        pytest.param(" ", id="space"),
        pytest.param("\t", id="tab"),
        pytest.param(" \t\n", id="mixed-whitespace"),
        pytest.param("NA", id="missing-like-na"),
        pytest.param("N/A", id="missing-like-n-a"),
        pytest.param("null", id="missing-like-null"),
        pytest.param("None", id="missing-like-none"),
        pytest.param("?", id="missing-like-question"),
        pytest.param("12345", id="short-numeric"),
        pytest.param("3.1415", id="decimal-numeric"),
        pytest.param("user@example.com", id="email"),
        pytest.param("https://example.com/a", id="url"),
        pytest.param("/usr/local/bin", id="posix-path"),
        pytest.param("C:\\temp\\file", id="windows-path"),
        pytest.param("00:11:22:33:44:55", id="mac"),
        pytest.param("00-11-22-33-44-55", id="mac-hyphen"),
        pytest.param("+1-202-555-0100", id="phone"),
        pytest.param("10001", id="postal"),
        pytest.param("4111111111111111", id="card-like"),
        pytest.param('{"a": 1}', id="json"),
        pytest.param("YWJjZA==", id="base64"),
        pytest.param("example.com", id="hostname"),
        pytest.param("2020-01-02", id="date"),
        pytest.param("2020-01-02T03:04:05", id="datetime"),
        pytest.param("03:04:05", id="time"),
    ],
)
def test_out_of_scope_strings_match_no_pattern(value: str):
    evidence = _collect(pd.Series([value], dtype="string"))

    _assert_only(evidence)


def test_date_looking_strings_are_not_parsed(monkeypatch: pytest.MonkeyPatch):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("a datetime parser was called")

    monkeypatch.setattr(pd, "to_datetime", _forbidden)
    evidence = _collect(
        pd.Series(["2020-01-02", "2020-01-02T03:04:05"], dtype="string")
    )

    _assert_only(evidence)
    assert (
        interpret_series_precedence(
            pd.Series(["2020-01-02", "2020-01-03"], dtype="string")
        )
        is None
    )


def test_pattern_free_strings_are_not_text_or_categorical():
    series = pd.Series(["hello", "world", "hello"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    _assert_only(evidence)
    assert reading is None


def test_uuid_column_is_not_identifier():
    series = pd.Series(
        [
            "550e8400-e29b-41d4-a716-446655440000",
            "550e8400-e29b-41d4-a716-446655440001",
        ],
        dtype="string",
    )
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    _assert_only(evidence, uuid_count=2)
    _assert_ratio(evidence.uuid_ratio, 1.0)
    assert reading is None


def test_ip_column_is_not_identifier():
    series = pd.Series(["192.168.1.1", "10.0.0.1"], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    _assert_only(evidence, ipv4_count=2)
    _assert_ratio(evidence.ipv4_ratio, 1.0)
    assert reading is None


def test_hex_column_is_not_identifier():
    series = pd.Series([_hex_token(64), _hex_token(64, "upper")], dtype="string")
    evidence = _collect(series)
    reading = interpret_series_precedence(series)

    _assert_only(evidence, hex_64_count=2)
    _assert_ratio(evidence.hex_64_ratio, 1.0)
    assert reading is None


def test_supplied_string_structure_and_basic_evidence_are_reused(
    monkeypatch: pytest.MonkeyPatch,
):
    series = pd.Series([_CANONICAL_UUID, pd.NA, "192.168.1.1"], dtype="string")
    basic = collect_basic_column_evidence(series)
    physical = classify_physical_dtype(series)
    structure = collect_string_structure_evidence(series, basic, physical)

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("evidence was recomputed during pattern collection")

    monkeypatch.setattr(pd.Series, "nunique", _forbidden)
    monkeypatch.setattr(pd.Series, "value_counts", _forbidden)
    monkeypatch.setattr(pd.Series, "astype", _forbidden)
    monkeypatch.setattr(pd, "to_numeric", _forbidden)
    monkeypatch.setattr(pd, "to_datetime", _forbidden)
    monkeypatch.setattr(
        "pytics.semantics.column_evidence.collect_basic_column_evidence",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.string_structure_evidence.collect_string_structure_evidence",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.physical.classify_physical_dtype",
        _forbidden,
    )
    monkeypatch.setattr(
        "pytics.semantics.frequency_evidence.collect_frequency_evidence",
        _forbidden,
    )

    evidence = collect_pattern_evidence(series, structure, physical)

    assert evidence.string_structure is structure
    assert evidence.string_structure.basic is basic
    _assert_only(evidence, uuid_count=1, ipv4_count=1)
    assert not hasattr(pattern_module, "collect_basic_column_evidence")
    assert not hasattr(pattern_module, "collect_string_structure_evidence")
    assert not hasattr(pattern_module, "collect_frequency_evidence")
    assert not hasattr(pattern_module, "classify_physical_dtype")
    parameters = list(inspect.signature(collect_pattern_evidence).parameters)
    assert parameters == ["series", "string_structure", "physical"]


def test_every_non_missing_row_is_counted():
    rows: list[Optional[str]] = ["plain"] * 40
    rows[0] = "127.0.0.1"
    rows[20] = None
    rows[-1] = "255.255.255.255"
    series = pd.Series(rows, dtype="string")
    evidence = _collect(series)

    assert evidence.string_structure.basic.n_total == 40
    assert evidence.string_structure.basic.n_missing == 1
    assert evidence.string_structure.basic.n_non_missing == 39
    _assert_only(evidence, ipv4_count=2)
    _assert_ratio(evidence.ipv4_ratio, 2 / 39)


def test_precedence_does_not_collect_pattern_evidence(
    monkeypatch: pytest.MonkeyPatch,
):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("pattern evidence was collected during precedence")

    monkeypatch.setattr(pattern_module, "collect_pattern_evidence", _forbidden)
    for module in (
        empty_constant_module,
        physical_boolean_module,
        physical_datetime_module,
        physical_timedelta_module,
        string_module,
    ):
        source = inspect.getsource(module)
        assert "PatternEvidence" not in source
        assert "collect_pattern_evidence" not in source

    empty = interpret_series_precedence(pd.Series([pd.NA, pd.NA], dtype="string"))
    constant = interpret_series_precedence(pd.Series(["aa", "aa"], dtype="string"))
    boolean = interpret_series_precedence(
        pd.Series([True, False, pd.NA], dtype="boolean")
    )
    native = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02"]))
    )
    aware = interpret_series_precedence(
        pd.Series(pd.to_datetime(["2026-01-01T12:00:00Z", "2026-01-02T12:00:00Z"]))
    )
    duration = interpret_series_precedence(
        pd.Series(pd.to_timedelta(["1 day", "2 days"]))
    )
    ordinary_strings = interpret_series_precedence(
        pd.Series(["a", "b"], dtype="string")
    )
    ordinary_numbers = interpret_series_precedence(pd.Series([1, 2, 3]))

    assert empty is not None
    assert empty.semantic_type is SemanticType.EMPTY
    assert constant is not None
    assert constant.semantic_type is SemanticType.CONSTANT
    assert boolean is not None
    assert boolean.semantic_type is SemanticType.BOOLEAN
    assert boolean.source is InferenceSource.PHYSICAL_DTYPE
    assert native is not None
    assert native.semantic_type is SemanticType.DATETIME
    assert aware is not None
    assert aware.physical.family is PhysicalDtypeFamily.DATETIME_TZ_AWARE
    assert duration is not None
    assert duration.semantic_type is SemanticType.TIMEDELTA
    assert ordinary_strings is None
    assert ordinary_numbers is None


def test_string_structure_collection_does_not_collect_pattern_evidence(
    monkeypatch: pytest.MonkeyPatch,
):
    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("pattern evidence was collected with string structure")

    monkeypatch.setattr(pattern_module, "collect_pattern_evidence", _forbidden)
    series = pd.Series([_CANONICAL_UUID, "plain"], dtype="string")
    structure = collect_string_structure_evidence(
        series,
        collect_basic_column_evidence(series),
        classify_physical_dtype(series),
    )

    assert isinstance(structure, StringStructureEvidence)
    assert structure.contains_digit_count == 1
    assert not hasattr(structure, "uuid_count")


def test_collection_does_not_mutate_the_series():
    series = pd.Series(
        [_CANONICAL_UUID, None, " 192.168.1.1 "],
        dtype=object,
        name="label",
        index=pd.Index([3, 1, 4], name="row"),
    )
    before = series.copy(deep=True)

    _collect(series)

    pd.testing.assert_series_equal(series, before)
    assert series.name == "label"
    assert series.index.name == "row"


def test_pattern_evidence_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "PatternEvidence")
    assert not hasattr(pytics, "collect_pattern_evidence")
    assert not hasattr(semantics_package, "PatternEvidence")
    assert not hasattr(semantics_package, "collect_pattern_evidence")


def test_mismatched_basic_evidence_is_rejected():
    series = pd.Series(["a", "b", "c"], dtype="string")
    physical = classify_physical_dtype(series)
    structure = _structure(2)

    with pytest.raises(ValueError, match="do not match BasicColumnEvidence"):
        collect_pattern_evidence(series, structure, physical)


def test_mismatched_physical_dtype_is_rejected():
    series = pd.Series(["a", "b"], dtype="string")
    physical = PhysicalDtype(family=PhysicalDtypeFamily.STRING, dtype_name="object")
    structure = collect_string_structure_evidence(
        series,
        collect_basic_column_evidence(series),
        classify_physical_dtype(series),
    )

    with pytest.raises(ValueError, match="does not match the Series"):
        collect_pattern_evidence(series, structure, physical)


def test_forged_non_string_family_is_rejected():
    series = pd.Series(["192.168.1.1"], dtype="string")
    physical = PhysicalDtype(
        family=PhysicalDtypeFamily.INTEGER,
        dtype_name=str(series.dtype),
    )

    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_pattern_evidence(series, _structure(1), physical)


def test_all_missing_object_population_is_rejected():
    series = pd.Series([None, None], dtype=object)
    physical = classify_physical_dtype(series)

    assert physical.family is PhysicalDtypeFamily.OBJECT
    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_pattern_evidence(series, _structure(0, n_missing=2), physical)


def test_numpy_byte_strings_are_not_decoded():
    series = pd.Series(np.array([b"ab", b"cd"]))
    physical = classify_physical_dtype(series)

    assert physical.family is PhysicalDtypeFamily.STRING
    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_pattern_evidence(
            series,
            _structure(2),
            physical,
        )


def test_mixed_object_values_are_not_stringified():
    series = pd.Series(["192.168.1.1", 1], dtype=object)
    physical = classify_physical_dtype(series)

    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_pattern_evidence(series, _structure(2), physical)


def test_categorical_labels_are_not_a_pattern_population():
    series = pd.Series(["192.168.1.1", "10.0.0.1"], dtype="category")
    physical = classify_physical_dtype(series)

    assert physical.family is PhysicalDtypeFamily.CATEGORICAL
    with pytest.raises(TypeError, match=_APPLICABILITY):
        collect_pattern_evidence(series, _structure(2), physical)


def test_wrong_input_types_are_rejected():
    series = pd.Series(["a", "b"], dtype="string")
    structure = collect_string_structure_evidence(
        series,
        collect_basic_column_evidence(series),
        classify_physical_dtype(series),
    )
    physical = classify_physical_dtype(series)

    with pytest.raises(TypeError, match="pandas Series"):
        collect_pattern_evidence(["a", "b"], structure, physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="StringStructureEvidence"):
        collect_pattern_evidence(series, "structure", physical)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="PhysicalDtype"):
        collect_pattern_evidence(series, structure, "physical")  # type: ignore[arg-type]


def test_zero_numerator_ratio_is_zero_not_none():
    evidence = _collect(pd.Series(["plain"], dtype="string"))

    _assert_ratio(evidence.uuid_ratio, 0.0)
    _assert_ratio(evidence.ipv4_ratio, 0.0)
    _assert_ratio(evidence.ipv6_ratio, 0.0)
    _assert_ratio(evidence.hex_32_ratio, 0.0)
    _assert_ratio(evidence.hex_40_ratio, 0.0)
    _assert_ratio(evidence.hex_64_ratio, 0.0)
    _assert_ratio(evidence.hex_128_ratio, 0.0)
