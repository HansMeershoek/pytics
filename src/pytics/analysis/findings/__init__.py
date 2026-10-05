"""Findings: retained analytical facts selected for attention.

A finding names one condition that a canonical analysis already holds,
the subject it is about, a severity from an explicit policy, and typed
evidence. It is not a statistic, a verdict, or a recommendation, and it
has no prose. The engine reads a finished ``DatasetAnalysis`` or
``DatasetComparison``. It does not read a DataFrame or a p-value.

Modules, in dependency order:

``models``
    Codes, scopes, severities, subjects, evidence, identity, and
    suppression, with the checks that tie a code to its evidence.
``result``
    The policy type, coverage, and the ordered findings result.
``policy``
    The v0.1 severity and order table, and assembly of a result.
``profile``
    Rules over one dataset analysis.
``compare``
    Rules over one dataset comparison.

Nothing here is exported from top-level ``pytics``. The names are not a
public schema.
"""

from pytics.analysis.findings.compare import collect_compare_findings
from pytics.analysis.findings.models import DEFERRED_FINDING_FAMILIES
from pytics.analysis.findings.models import ColumnSubject
from pytics.analysis.findings.models import ComparedTargetPredictorSubject
from pytics.analysis.findings.models import DeferredFindingFamily
from pytics.analysis.findings.models import DuplicateRowsEvidence
from pytics.analysis.findings.models import Finding
from pytics.analysis.findings.models import FindingCode
from pytics.analysis.findings.models import FindingIdentity
from pytics.analysis.findings.models import FindingScope
from pytics.analysis.findings.models import FindingSeverity
from pytics.analysis.findings.models import FindingsSource
from pytics.analysis.findings.models import SemanticTransitionEvidence
from pytics.analysis.findings.models import SuppressedFinding
from pytics.analysis.findings.models import SuppressionRule
from pytics.analysis.findings.models import TargetPredictorSubject
from pytics.analysis.findings.policy import FINDINGS_POLICY
from pytics.analysis.findings.profile import collect_profile_findings
from pytics.analysis.findings.result import FindingRule
from pytics.analysis.findings.result import FindingsAnalysis
from pytics.analysis.findings.result import FindingsCoverage
from pytics.analysis.findings.result import FindingsPolicy
