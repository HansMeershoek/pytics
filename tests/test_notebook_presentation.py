"""TSK-043: notebook landing view of the public result."""

from __future__ import annotations

import ast
import subprocess
import sys
import uuid
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pytics.analysis.column_label import ColumnLabelKind
from pytics.analysis.column_label import RetainedColumnLabel
from pytics.analysis.compare.alignment import ColumnAlignment
from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.collector import compare_dataset_analyses
from pytics.analysis.dataset import analyze_dataframe
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.target import TargetStatus
from pytics.analysis.target_diagnostic import DiagnosticStatus
from pytics.analysis.target_diagnostic import PredictiveTask
from pytics.presentation.notebook.comparison import render_comparison
from pytics.presentation.notebook.profile import render_profile
from pytics.presentation.notebook.style import NOTEBOOK_CSS
from pytics.presentation.notebook.text import DIAGNOSTIC_STATUS_LABEL
from pytics.presentation.notebook.text import TARGET_STATUS_LABEL
from pytics.presentation.notebook.text import _occurrence_attribute
from pytics.presentation.notebook.text import english_list
from pytics.presentation.notebook.text import format_percent
from pytics.presentation.notebook.text import missing_text
from pytics.presentation.notebook.text import more_findings
from pytics.presentation.notebook.text import paired_label
from pytics.presentation.notebook.text import present_counts
from pytics.presentation.notebook.text import retained_display
from pytics.presentation.notebook.text import retained_text
from pytics.presentation.notebook.text import task_name
from pytics.presentation.notebook.text import type_name
from pytics.results import comparison_result
from pytics.results import profile_result
from pytics.results.comparison import ComparisonResult
from pytics.semantics.interpretation import SemanticType

_ROOT = Path(__file__).resolve().parents[1]
_SECRET = "SECRET_LEVEL_<img src=x onerror=alert(1)>"
_OUTLIER = 987654321.25
_BANNED = (
    "degraded",
    "problematic",
    "dangerous",
    "must fix",
    "broken",
    "bad row",
    "invalid value",
    "worse",
    "better",
)


def _html(result: object) -> str:
    html = result._repr_html_()  # type: ignore[attr-defined]
    assert isinstance(html, str)
    return html


def _assert_shell(html: str) -> None:
    assert html.startswith('<div class="pytics-report ')
    assert "<script" not in html.lower()
    assert "plotly" not in html.lower()
    assert "cdn" not in html.lower()
    assert "href=" not in html.lower()
    assert "http://" not in html
    assert "https://" not in html
    assert 'class="pytics-report' in html
    assert "</style>" in html


def _subjects(html: str) -> list[str]:
    marker = 'pytics-finding-subject">'
    found = []
    start = 0
    while True:
        index = html.find(marker, start)
        if index < 0:
            return found
        index += len(marker)
        end = html.find("</span>", index)
        found.append(html[index:end])
        start = end


def _codes(html: str) -> list[str]:
    marker = 'data-finding-code="'
    found = []
    start = 0
    while True:
        index = html.find(marker, start)
        if index < 0:
            return found
        index += len(marker)
        end = html.find('"', index)
        found.append(html[index:end])
        start = end


def _labeled(labels: list[object], rows: list[list[object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame.columns = pd.Index(labels, dtype=object)
    return frame


def _constants(labels: list[object]) -> pd.DataFrame:
    width = len(labels)
    rows = [[1] * width + [float(row)] for row in range(4)]
    return _labeled([*labels, "varying"], rows)


def _categories(values: list[str]) -> pd.Series:
    return pd.Series(pd.Categorical(values))


def test_text_formatters_cover_counts_lists_and_label_kinds() -> None:
    assert format_percent(0, 10) == "0%"
    assert format_percent(10, 10) == "100%"
    assert format_percent(1, 1_000_000) == "<0.01%"
    assert format_percent(284, 10_000) == "2.84%"
    assert format_percent(15, 100) == "15%"
    assert format_percent(1, 8) == "12.5%"
    assert format_percent(1, 3) == "33.3%"
    with pytest.raises(ValueError):
        format_percent(1, 0)
    assert missing_text(0, 0) == "0"
    assert missing_text(0, 24) == "0 of 24"
    assert missing_text(12, 400) == "12 of 400 (3%)"
    assert english_list(()) == ""
    assert english_list(("empty columns",)) == "empty columns"
    assert english_list(("a", "b")) == "a and b"
    assert english_list(("a", "b", "c")) == "a, b, and c"
    assert more_findings(1) == "1 more finding follows in the same order."
    assert more_findings(2) == "2 more findings follow in the same order."
    assert present_counts((("Ambiguous", 0), ("Source values not supplied", 2))) == (
        "Source values not supplied 2"
    )
    assert present_counts((("Wasserstein distances unavailable", 0),)) == ""
    assert type_name(None) == "unresolved"
    assert type_name(SemanticType.NUMERIC) == "Numeric"
    assert task_name(None) == "not collected"
    assert task_name(PredictiveTask.REGRESSION) == "Regression"
    assert _occurrence_attribute(None) == ()
    assert _occurrence_attribute(2) == (("data-occurrence", "2"),)


def test_retained_label_text_covers_each_kind_and_disambiguates() -> None:
    samples = [
        (ColumnLabelKind.NONE, None, "None"),
        (ColumnLabelKind.BOOL, True, "True"),
        (ColumnLabelKind.BOOL, False, "False"),
        (ColumnLabelKind.INT, 1, "1"),
        (ColumnLabelKind.FLOAT, 1.0, "1.0"),
        (ColumnLabelKind.FLOAT_NAN, None, "NaN"),
        (ColumnLabelKind.PANDAS_NA, None, "NA"),
        (ColumnLabelKind.PANDAS_NAT, None, "NaT"),
        (ColumnLabelKind.STRING, "age", "age"),
        (ColumnLabelKind.BYTES, b"ab", "b'ab'"),
        (ColumnLabelKind.DATE, date(2020, 1, 2), "2020-01-02"),
        (ColumnLabelKind.TIME, time(3, 4), "03:04:00"),
        (ColumnLabelKind.DATETIME, datetime(2020, 1, 2, 3, 4), "2020-01-02 03:04:00"),
        (ColumnLabelKind.TIMEDELTA, timedelta(days=1), "1 day, 0:00:00"),
        (ColumnLabelKind.UNSUPPORTED, None, "Unsupported label"),
    ]
    for kind, value, expected in samples:
        assert retained_text(RetainedColumnLabel(kind=kind, value=value)) == expected
    nested = RetainedColumnLabel(
        kind=ColumnLabelKind.TUPLE,
        value=(
            RetainedColumnLabel(ColumnLabelKind.STRING, "age"),
            RetainedColumnLabel(ColumnLabelKind.INT, 1),
            RetainedColumnLabel(ColumnLabelKind.BOOL, True),
        ),
    )
    assert retained_text(nested) == "(age, 1, True)"
    age = RetainedColumnLabel(ColumnLabelKind.STRING, "age")
    assert retained_display(age, 1) == "age"
    assert retained_display(age, 2) == "age [2]"
    unsupported = RetainedColumnLabel(ColumnLabelKind.UNSUPPORTED, None)
    assert retained_display(unsupported, None, 4) == "Unsupported label · position 4"
    assert retained_display(unsupported, None, None) == "Unsupported label"
    nan = RetainedColumnLabel(ColumnLabelKind.FLOAT_NAN, None)
    assert retained_display(nan, 2) == "NaN [2]"
    same = ColumnAlignment(
        status=ColumnMatchStatus.MATCHED,
        reference_label=age,
        comparison_label=RetainedColumnLabel(ColumnLabelKind.STRING, "age"),
        occurrence=1,
        reference_position=0,
        comparison_position=0,
    )
    assert paired_label(same) == "age"
    differing = ColumnAlignment(
        status=ColumnMatchStatus.MATCHED,
        reference_label=RetainedColumnLabel(ColumnLabelKind.INT, 1),
        comparison_label=RetainedColumnLabel(ColumnLabelKind.FLOAT, 1.0),
        occurrence=3,
        reference_position=1,
        comparison_position=1,
    )
    assert paired_label(differing) == "1 [3] · 1.0 [3]"
    reference_only = ColumnAlignment(
        status=ColumnMatchStatus.REFERENCE_ONLY,
        reference_label=age,
        comparison_label=None,
        occurrence=1,
        reference_position=0,
        comparison_position=None,
    )
    assert paired_label(reference_only) == "age"


def test_renderer_rejects_the_wrong_object() -> None:
    with pytest.raises(TypeError):
        render_profile(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        render_comparison(object())  # type: ignore[arg-type]


def test_css_rules_stay_under_the_report_namespace() -> None:
    assert "@import" not in NOTEBOOK_CSS
    assert "http://" not in NOTEBOOK_CSS
    assert "https://" not in NOTEBOOK_CSS
    assert "<script" not in NOTEBOOK_CSS
    assert "\nbody" not in NOTEBOOK_CSS
    assert " body" not in NOTEBOOK_CSS
    for token in ("#ff0000", "#f00", " red", "#dc2626", "#b91c1c", "#ef4444"):
        assert token not in NOTEBOOK_CSS.lower()
    selectors = []
    for block in NOTEBOOK_CSS.split("}"):
        if "{" not in block:
            continue
        selectors.append(block.split("{")[0])
    assert selectors
    for selector in selectors:
        for piece in selector.split(","):
            assert piece.strip().startswith(".pytics-report")


def test_presentation_is_not_on_the_import_path_of_pytics() -> None:
    init = (_ROOT / "src" / "pytics" / "__init__.py").read_text(encoding="utf-8")
    assert "presentation" not in init
    import pytics

    assert "presentation" not in pytics.__all__
    banned = (
        "plotly",
        "jinja",
        "IPython",
        "analyze_dataframe",
        "compare_dataframes",
        "collect_profile_findings",
        "collect_compare_findings",
    )
    root = _ROOT / "src" / "pytics" / "presentation"
    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        for name in banned:
            assert name not in imported
            assert name not in source


def test_results_import_does_not_load_the_presentation_package() -> None:
    script = (
        "import sys; "
        "from pytics.results import profile_result; "
        "assert 'pytics.presentation' not in sys.modules; "
        "assert 'pytics.presentation.notebook' not in sys.modules"
    )
    subprocess.check_call([sys.executable, "-c", script])


def test_profile_hook_is_deterministic_and_does_not_mutate(monkeypatch) -> None:
    frame = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 5.0]})
    result = profile_result(frame)
    twin = profile_result(frame)
    records = result.findings.records
    assert result == twin
    assert repr(result) == (
        "ProfileResult(rows=4, columns=2, findings=0, target=not_requested)"
    )
    assert str(result) == repr(result)

    def _boom(*_args, **_kwargs):
        raise AssertionError("rendering analyzed again")

    monkeypatch.setattr("pytics.analysis.dataset.analyze_dataframe", _boom)
    first = _html(result)
    second = _html(result)
    assert first == second
    assert result.findings.records is records
    assert result == twin
    _assert_shell(first)
    assert "Data Profile" in first
    assert "4" in first
    assert "No findings." in first
    assert "Target: not requested." in first
    assert "<h2>Target</h2>" not in first
    assert "spearman" not in first.lower()
    assert "x" not in _subjects(first)


def test_ipython_formatter_uses_the_notebook_hook() -> None:
    pytest.importorskip("IPython")
    from IPython.core.formatters import HTMLFormatter

    profile = profile_result(pd.DataFrame({"x": [1.0, 2.0, 3.0]}))
    comparison = comparison_result(
        pd.DataFrame({"x": [1.0, 2.0, 3.0]}),
        pd.DataFrame({"x": [1.0, 2.0, 4.0]}),
    )
    formatter = HTMLFormatter()
    profile_html = formatter(profile)
    comparison_html = formatter(comparison)
    assert profile_html is not None and "Data Profile" in profile_html
    assert comparison_html is not None and "Dataset Comparison" in comparison_html


def test_zero_column_one_column_and_non_numeric_profiles() -> None:
    repeated = profile_result(pd.DataFrame(index=[0, 1, 2]))
    repeated_html = _html(repeated)
    _assert_shell(repeated_html)
    assert "Exact duplicate rows" in repeated_html
    assert "No selected semantic type" in repeated_html
    assert "No column" in repeated_html
    assert "of 0" not in repeated_html
    assert "<h2>Target</h2>" not in repeated_html
    empty = profile_result(pd.DataFrame(index=[0]))
    empty_html = _html(empty)
    assert "No findings." in empty_html
    assert "No selected semantic type" in empty_html
    one = profile_result(pd.DataFrame({"x": [1.0, 2.0, 3.0]}))
    one_html = _html(one)
    assert "0 calculated · 0 unimplemented · 0 ineligible" in one_html
    strings = profile_result(
        pd.DataFrame(
            {"city": pd.Series(["Amsterdam", "Berlin", "Amsterdam"], dtype="string")}
        )
    )
    strings_html = _html(strings)
    assert "No eligible numeric column" in strings_html
    assert "Insufficient evidence" in strings_html


def test_empty_constant_and_duplicate_findings_keep_canonical_order() -> None:
    labels = ["a", "b"] * 6
    frame = pd.DataFrame(
        {
            "y": _categories(labels),
            "copy": _categories(labels),
            "constant": [1] * 12,
            "x": [1.0, 2.0] * 6,
        }
    )
    result = profile_result(frame, target="y")
    html = _html(result)
    codes = _codes(html)
    assert codes == [finding.code.value for finding in result.findings]
    assert codes[0] == FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE.value
    assert FindingCode.CONSTANT_COLUMN.value in codes
    assert FindingCode.DUPLICATE_ROWS.value in codes
    assert html.index("Exact copy of the target") < html.index("Constant column")
    assert html.index("Constant column") < html.index("Exact duplicate rows")
    assert "Warning" in html
    assert "Notable" in html
    assert "Info" in html
    assert "bad" not in html.lower()
    assert "leak" not in html.lower()


def test_landing_findings_stop_after_five_without_reordering() -> None:
    labels = [f"col-{name}" for name in ("a", "b", "c", "d", "e", "f")]
    result = profile_result(_constants(labels))
    html = _html(result)
    shown = result.findings.records[:5]
    assert _codes(html) == [finding.code.value for finding in shown]
    assert "col-f" not in html
    assert "1 more finding follows in the same order." in html
    assert len(result.findings) == 6


def test_duplicate_nan_bool_and_numeric_labels_stay_distinct() -> None:
    result = profile_result(_constants([True, 1, 1, 1.0]))
    assert _subjects(_html(result)) == ["True", "1", "1 [2]", "1.0 [3]"]
    nan = profile_result(_constants([float("nan"), float("nan")]))
    assert _subjects(_html(nan)) == ["NaN", "NaN [2]"]


def test_user_controlled_labels_are_escaped_and_sensitive_values_stay_off() -> None:
    script = '<script>alert("x")</script>'
    ampersand = 'a&b"c'
    long_label = "测量\n" + ("长" * 40) + " 🌡️ <b>x</b>"
    rows = [
        [1, 1, 1, 1.0, _SECRET],
        [1, 1, 1, 2.0, "a"],
        [1, 1, 1, 3.0, "b"],
        [1, 1, 1, _OUTLIER, "a"],
    ]
    frame = _labeled([script, ampersand, long_label, "amount", "city"], rows)
    frame["city"] = pd.Categorical(frame["city"])
    html = _html(profile_result(frame))
    _assert_shell(html)
    assert script not in html
    assert escape(script, quote=True) in html
    assert escape(ampersand, quote=True) in html
    assert "🌡️" in html
    assert "测量" in html
    assert "<b>" not in html
    assert "&lt;b&gt;" in html
    assert _SECRET not in html
    assert "987654321" not in html
    assert "onerror" not in html


def test_clean_profile_is_a_compact_reading() -> None:
    frame = pd.DataFrame(
        {
            "amount": [10.0, 12.5, 9.0, 11.0, 13.5],
            "region": ["north", "south", "east", "north", "west"],
            "flag": [True, False, True, False, True],
            "when": pd.date_range("2024-01-01", periods=5, freq="D"),
        }
    )
    result = profile_result(frame)
    html = _html(result)
    _assert_shell(html)
    assert "No findings." in html
    assert "Numeric" in html
    assert "Categorical" in html or "Boolean" in html
    assert "Rows" in html and "Columns" in html and "Cells" in html
    assert "Evaluated:" in html
    assert "No finding rule in this version" in html
    assert (
        "Variables, relationships, findings, and coverage are on this result." in html
    )
    for word in _BANNED:
        assert word not in html.lower()


def test_messy_profile_keeps_findings_and_hides_raw_evidence() -> None:
    identifier = [str(uuid.UUID(int=index)) for index in range(7)]
    identifier.append(identifier[0])
    frame = pd.DataFrame(
        {
            "record": identifier,
            "amount": [1.0, 2.0, None, _OUTLIER, 5.0, 6.0, 7.0, 1.0],
            "blank": [None] * 8,
            "status": ["open"] * 8,
            "outcome": pd.Categorical(["a", "b", "a", "b", "a", "b", "a", "a"]),
            "city": pd.Categorical([_SECRET, "a", "b", "a", "b", "a", "b", _SECRET]),
        }
    )
    result = profile_result(frame, target="outcome")
    html = _html(result)
    _assert_shell(html)
    assert result.target.status is TargetStatus.SUPPORTED
    assert "<h2>Target</h2>" in html
    assert TARGET_STATUS_LABEL[result.target.status] in html
    assert result.target.diagnostic_status is not None
    assert DIAGNOSTIC_STATUS_LABEL[result.target.diagnostic_status] in html
    assert "Empty column" in html
    assert "Constant column" in html
    assert "Missing cells" in html
    assert _SECRET not in html
    assert "987654321" not in html
    assert SemanticType.EMPTY in {
        variable.selected_type for variable in result.variables
    }
    if SemanticType.IDENTIFIER in {
        variable.selected_type for variable in result.variables
    }:
        assert "Identifier" in html
    for word in _BANNED:
        assert word not in html.lower()


def test_requested_targets_distinguish_unsupported_and_unresolved() -> None:
    unsupported = profile_result(
        pd.DataFrame(
            {
                "when": pd.to_datetime(
                    ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
                ),
                "x": [1.0, 2.0, 3.0, 4.0],
            }
        ),
        target="when",
    )
    unsupported_html = _html(unsupported)
    assert unsupported.target.status is TargetStatus.UNSUPPORTED
    assert "<h2>Target</h2>" in unsupported_html
    assert "Unsupported" in unsupported_html
    assert "Not collected" in unsupported_html
    assert "not requested" not in unsupported_html.lower()
    unresolved = profile_result(
        pd.DataFrame(
            {
                "city": pd.Series(["Amsterdam", "Berlin", "Amsterdam"], dtype="string"),
                "x": [1.0, 2.0, 3.0],
            }
        ),
        target="city",
    )
    unresolved_html = _html(unresolved)
    assert unresolved.target.status is TargetStatus.UNRESOLVED
    assert "Unresolved" in unresolved_html
    assert "Selected type" not in unresolved_html
    supported = profile_result(
        pd.DataFrame(
            {
                "y": pd.Series(pd.Categorical(["a", "b"] * 20)),
                "x": [float(index) for index in range(40)],
            }
        ),
        target="y",
    )
    supported_html = _html(supported)
    assert supported.target.status is TargetStatus.SUPPORTED
    assert supported.target.diagnostic_status is DiagnosticStatus.AVAILABLE
    assert "Supported" in supported_html
    assert "Available" in supported_html
    assert "Binary classification" in supported_html
    assert "permutation" not in supported_html.lower()


def test_small_profile_does_not_list_variables_or_relationships() -> None:
    frame = pd.DataFrame(
        {f"col{index}": [float(index), float(index + 1)] for index in range(4)}
    )
    html = _html(profile_result(frame))
    for index in range(4):
        assert f"col{index}" not in html
    assert "spearman" not in html.lower()
    assert "p-value" not in html.lower()


def test_comparison_limits_findings_and_empty_frames() -> None:
    reference = pd.DataFrame({f"only{index}": [1.0, 2.0, 3.0] for index in range(6)})
    current = pd.DataFrame({"added": [1.0, 2.0, 4.0]})
    html = _html(comparison_result(reference, current))
    assert "more findings follow in the same order." in html
    assert html.count('data-finding-index="') == 5
    bare = comparison_result(pd.DataFrame(index=[0]), pd.DataFrame(index=[0]))
    bare_html = _html(bare)
    assert "No selected semantic type on either side." in bare_html
    assert "No findings." in bare_html


def test_comparison_without_a_target_uses_neutral_sides() -> None:
    reference = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 4.0]})
    current = pd.DataFrame({"x": [1.0, 2.0, 3.0, 8.0], "y": [4.0, 3.0, 2.0, 1.0]})
    result = comparison_result(reference, current)
    html = _html(result)
    _assert_shell(html)
    assert "Dataset Comparison" in html
    assert ">Reference<" in html
    assert ">Comparison<" in html
    assert "Target: not requested." in html
    assert "<h2>Target</h2>" not in html
    assert "Before" not in html
    assert "After" not in html
    assert "Old" not in html
    assert "New" not in html
    assert repr(result) == (
        "ComparisonResult(rows=4/4, columns=2, findings=0, " "target=not_requested)"
    )
    assert str(result) == repr(result)
    records = result.findings.records
    assert html == _html(result)
    assert result.findings.records is records
    for word in _BANNED:
        assert word not in html.lower()
    assert "spearman" not in html.lower()
    assert "wasserstein" not in html.lower()


def test_comparison_schema_distribution_and_relationship_counts() -> None:
    reference = pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            "kind": ["a", "b", "a", "b", "a", "b", "a", "b"],
            "only_ref": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        }
    )
    current = pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 8.0, 9.0, 10.0, 11.0],
            "y": [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
            "kind": [1, 0, 1, 0, 1, 0, 1, 0],
            "only_cur": [1, 1, 1, 1, 1, 1, 1, 1],
        }
    )
    result = comparison_result(reference, current)
    html = _html(result)
    codes = _codes(html)
    assert codes == [finding.code.value for finding in result.findings][: len(codes)]
    assert FindingCode.COLUMN_REFERENCE_ONLY.value in codes
    assert FindingCode.COLUMN_COMPARISON_ONLY.value in codes
    assert FindingCode.SEMANTIC_TYPE_CHANGED.value in codes
    assert "only_ref" in html
    assert "only_cur" in html
    assert "Reference " in html
    assert "relationship transitions" in html
    assert "reference only" in html
    assert "comparison only" in html
    assert "family transition" in html or "same family" in html
    assert "degraded" not in html.lower()
    assert html.count("<tr") < 40


def test_comparison_target_states() -> None:
    reference = pd.DataFrame(
        {"y": _categories(["a", "b"] * 12), "x": np.linspace(0.0, 1.0, 24)}
    )
    comparison = pd.DataFrame(
        {"y": _categories(["a", "b", "c"] * 8), "x": np.linspace(0.0, 1.0, 24)}
    )
    task = comparison_result(reference, comparison, target="y")
    task_html = _html(task)
    assert FindingCode.TARGET_TASK_CHANGED.value in _codes(task_html)
    assert "Diagnostic task changed" in task_html
    assert "Binary classification" in task_html
    assert "Multiclass classification" in task_html
    assert "<h2>Target</h2>" in task_html
    vocabulary = comparison_result(
        pd.DataFrame(
            {"y": _categories(["a", "b"] * 12), "x": np.linspace(0.0, 1.0, 24)}
        ),
        pd.DataFrame(
            {"y": _categories(["a", "c"] * 12), "x": np.linspace(0.0, 1.0, 24)}
        ),
        target="y",
    )
    vocabulary_html = _html(vocabulary)
    assert FindingCode.TARGET_CLASS_VOCABULARY_CHANGED.value in _codes(vocabulary_html)
    assert "a" not in _subjects(vocabulary_html)
    assert _SECRET not in vocabulary_html
    values = [index % 3 == 0 for index in range(24)]
    broken = list(values)
    broken[0] = not broken[0]
    changed = comparison_result(
        pd.DataFrame({"y": values, "copy": values, "x": np.linspace(0.0, 1.0, 24)}),
        pd.DataFrame({"y": values, "copy": broken, "x": np.linspace(1.0, 2.0, 24)}),
        target="y",
    )
    changed_html = _html(changed)
    assert FindingCode.TARGET_EXACT_DUPLICATE_EVIDENCE_CHANGED.value in _codes(
        changed_html
    )
    assert "Exact-copy evidence changed" in changed_html
    missing = comparison_result(reference, comparison, target="missing-target")
    missing_html = _html(missing)
    assert "Not in either dataset" in missing_html
    assert "error" not in missing_html.lower()
    reference_only = comparison_result(reference, comparison[["x"]], target="y")
    reference_html = _html(reference_only)
    assert "Reference only" in reference_html
    assert FindingCode.COLUMN_REFERENCE_ONLY.value in _codes(reference_html)
    comparison_only = comparison_result(reference[["x"]], comparison, target="y")
    assert "Comparison only" in _html(comparison_only)


def test_distribution_source_not_supplied_is_labeled() -> None:
    reference = analyze_dataframe(pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0]}))
    current = analyze_dataframe(pd.DataFrame({"x": [1.0, 2.0, 4.0, 8.0]}))
    result = ComparisonResult.from_comparison(
        compare_dataset_analyses(reference, current)
    )
    html = _html(result)
    assert "Source values not supplied" in html
    assert "Not collected" in html


def test_wide_profile_landing_is_bounded() -> None:
    frame = pd.DataFrame(
        np.arange(30 * 100, dtype=float).reshape(30, 100) + np.arange(100, dtype=float),
        columns=[f"c{index:03d}" for index in range(100)],
    )
    result = profile_result(frame)
    html = _html(result)
    _assert_shell(html)
    assert result.relationships.analysis.n_analyzed_pairs > 1000
    assert f"{result.relationships.analysis.n_analyzed_pairs:,}" in html
    for index in range(100):
        assert f"c{index:03d}" not in html
    assert "spearman" not in html.lower()
    assert html.count("<tr") < 40
    assert len(html.encode("utf-8")) < 64 * 1024


def test_wide_comparison_landing_is_bounded() -> None:
    values = np.arange(30 * 100, dtype=float).reshape(30, 100) + np.arange(100)
    columns = [f"c{index:03d}" for index in range(100)]
    reference = pd.DataFrame(values, columns=columns)
    current = pd.DataFrame(values + 1.0, columns=columns)
    result = comparison_result(reference, current)
    html = _html(result)
    _assert_shell(html)
    assert result.relationships.coverage.n_aligned_pairs > 1000
    assert f"{result.relationships.coverage.n_aligned_pairs:,}" in html
    for index in range(100):
        assert f"c{index:03d}" not in html
    assert "spearman" not in html.lower()
    assert html.count("<tr") < 40
    assert len(html.encode("utf-8")) < 64 * 1024
    assert "degraded" not in html.lower()
