"""Public result contract for Pytics 2.0.

``profile_result`` and ``comparison_result`` return read-only views of
the canonical analysis. They do not replace :func:`pytics.profile` or
:func:`pytics.compare`. Those two functions are still the legacy 1.1.5
renderers.

A notebook display of these results delegates to
:mod:`pytics.presentation.notebook`. That layer is not exported from
:mod:`pytics`. Markdown, PDF, and JSON are not produced here. A
serializer should read this package and should not import collectors
from :mod:`pytics.analysis` to obtain a finished profile or comparison.
"""

from pytics.results.common import AmbiguousColumnLabel
from pytics.results.common import FindingsView
from pytics.results.common import ResultKind
from pytics.results.common import ResultMetadata
from pytics.results.common import TargetRequest
from pytics.results.comparison import ComparisonColumnIndex
from pytics.results.comparison import ComparisonCoverageView
from pytics.results.comparison import ComparisonRelationshipIndex
from pytics.results.comparison import ComparisonResult
from pytics.results.comparison import ComparisonTargetView
from pytics.results.comparison import comparison_result
from pytics.results.profile import ProfileCoverage
from pytics.results.profile import ProfileResult
from pytics.results.profile import RelationshipIndex
from pytics.results.profile import TargetView
from pytics.results.profile import Variable
from pytics.results.profile import VariableIndex
from pytics.results.profile import profile_result

__all__ = [
    "AmbiguousColumnLabel",
    "ComparisonColumnIndex",
    "ComparisonCoverageView",
    "ComparisonRelationshipIndex",
    "ComparisonResult",
    "ComparisonTargetView",
    "FindingsView",
    "ProfileCoverage",
    "ProfileResult",
    "RelationshipIndex",
    "ResultKind",
    "ResultMetadata",
    "TargetRequest",
    "TargetView",
    "Variable",
    "VariableIndex",
    "comparison_result",
    "profile_result",
]
