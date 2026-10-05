"""Top-level profile and compare delegate to the 2.0 result constructors."""

from __future__ import annotations

import inspect
import subprocess
import sys

import pandas as pd

import pytics
from pytics.results import ComparisonResult
from pytics.results import ProfileResult
from pytics.results import comparison_result
from pytics.results import profile_result

_EXPORT_STACK = (
    "plotly",
    "jinja2",
    "xhtml2pdf",
    "reportlab",
    "kaleido",
    "matplotlib",
    "IPython",
)


def _absent(names: tuple[str, ...]) -> str:
    return (
        f"banned = {names!r}\n"
        "loaded = [\n"
        "    name for name in banned\n"
        "    if name in sys.modules\n"
        "    or any(module.startswith(name + '.') for module in sys.modules)\n"
        "]\n"
        "assert loaded == [], loaded\n"
    )


def test_public_names_delegate_without_legacy_parameters() -> None:
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "profile_result")
    assert not hasattr(pytics, "comparison_result")
    assert not hasattr(pytics, "profiler")
    profile_parameters = inspect.signature(pytics.profile).parameters
    compare_parameters = inspect.signature(pytics.compare).parameters
    assert list(profile_parameters) == ["frame", "target"]
    assert list(compare_parameters) == ["reference", "comparison", "target"]
    for name in ("target",):
        assert profile_parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert compare_parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    for retired in ("output_file", "output_format", "theme", "title", "n_bins"):
        assert retired not in profile_parameters
        assert retired not in compare_parameters


def test_profile_and_compare_match_the_result_helpers() -> None:
    frame = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 5.0]})
    other = pd.DataFrame({"x": [1.0, 2.0, 3.0, 6.0], "y": [1.0, 2.0, 3.0, 5.0]})
    profile = pytics.profile(frame)
    again = pytics.profile(frame)
    assert isinstance(profile, ProfileResult)
    assert profile == again
    assert profile == profile_result(frame)
    targeted = pytics.profile(frame, target="y")
    assert targeted == profile_result(frame, target="y")
    assert targeted != profile
    comparison = pytics.compare(frame, other)
    assert isinstance(comparison, ComparisonResult)
    assert comparison == pytics.compare(frame, other)
    assert comparison == comparison_result(frame, other)
    assert pytics.compare(frame, other, target="y") == comparison_result(
        frame, other, target="y"
    )
    html = profile._repr_html_()
    assert html == again._repr_html_()
    assert "Data Profile" in html


def test_import_pytics_stays_lightweight_and_omits_the_export_stack() -> None:
    script = (
        "import sys\n"
        "import pytics\n"
        + _absent(_EXPORT_STACK)
        + "for name in ('pytics.results', 'pytics.analysis', 'pytics.profiler',\n"
        "              'pytics.presentation', 'scipy', 'sklearn', 'pandas'):\n"
        "    assert name not in sys.modules, name\n"
        "    assert not any(module.startswith(name + '.') for module in sys.modules)\n"
    )
    subprocess.check_call([sys.executable, "-c", script])


def test_calling_profile_loads_analysis_and_not_the_export_stack() -> None:
    script = (
        "import sys\n"
        "import pandas as pd\n"
        "import pytics\n"
        "assert 'pytics.results' not in sys.modules\n"
        "result = pytics.profile(pd.DataFrame({'x': [1.0, 2.0, 3.0]}))\n"
        "assert type(result).__name__ == 'ProfileResult'\n"
        "assert 'pytics.results' in sys.modules\n"
        "assert 'scipy' in sys.modules\n"
        + _absent(_EXPORT_STACK)
    )
    subprocess.check_call([sys.executable, "-c", script])


def test_result_import_does_not_load_the_retired_export_stack() -> None:
    script = (
        "import sys\n"
        "from pytics.results import profile_result, comparison_result\n"
        "assert callable(profile_result) and callable(comparison_result)\n"
        + _absent(_EXPORT_STACK)
        + "assert 'pytics.presentation' not in sys.modules\n"
        "assert 'pytics.profiler' not in sys.modules\n"
    )
    subprocess.check_call([sys.executable, "-c", script])
