"""Compare two dataset analyses.

The question is what changed between a reference dataset and a comparison
dataset, how large a distributional change is, and what evidence supports
it. A difference is not degradation, and this result does not score
either one. It does not say that the comparison dataset is worse,
invalid, or the result of a particular event. Each side's
``DatasetAnalysis`` stays the single-dataset truth.

Modules, in dependency order:

``values``
    Directional count, proportion, and number records shared by every
    layer. ``comparison - reference`` where defined, ``None`` otherwise.
``alignment``
    Column identity across frames: match key plus occurrence.
``schema``
    Physical dtype and inferred semantic state on each side.
``overview``
    Dataset-level counts copied from the two analyses.
``descriptive``
    Missingness counts and typed Numeric, Categorical, and Boolean
    descriptive change. Owns comparison eligibility.
``distribution_models`` and ``distribution``
    Univariate distribution drift records and their calculation. The
    only part of this package that reads source values, and only for
    Numeric columns.
``models``
    ``ColumnComparison``, ``ComparisonCoverage``, and
    ``DatasetComparison``, with the checks that tie them together.
``collector``
    The two entry points and the order of the pass.

Rows are not paired. The DataFrame index is not an entity key. Duplicate
groups are not matched across datasets. Relationship drift, target
drift, anomaly-count comparison, and missingness-pattern drift are not
this result. There is no score, severity, threshold, or significance
flag.

Nothing here is ``pytics.compare``. The legacy public function is unchanged.
"""

from pytics.analysis.compare.alignment import ColumnAlignment
from pytics.analysis.compare.alignment import ColumnMatchStatus
from pytics.analysis.compare.collector import compare_dataframes
from pytics.analysis.compare.collector import compare_dataset_analyses
from pytics.analysis.compare.descriptive import BooleanDescriptiveComparison
from pytics.analysis.compare.descriptive import CategoricalDescriptiveComparison
from pytics.analysis.compare.descriptive import ColumnMissingnessComparison
from pytics.analysis.compare.descriptive import ComparedCategoryLevel
from pytics.analysis.compare.descriptive import DescriptiveComparisonReason
from pytics.analysis.compare.descriptive import DescriptiveComparisonStatus
from pytics.analysis.compare.descriptive import NumericDescriptiveComparison
from pytics.analysis.compare.distribution_models import BooleanDistributionDrift
from pytics.analysis.compare.distribution_models import CategoricalDistributionDrift
from pytics.analysis.compare.distribution_models import DistributionDrift
from pytics.analysis.compare.distribution_models import DistributionDriftStatus
from pytics.analysis.compare.distribution_models import DriftEffect
from pytics.analysis.compare.distribution_models import DriftEffectMethod
from pytics.analysis.compare.distribution_models import DriftPopulation
from pytics.analysis.compare.distribution_models import DriftPopulationRule
from pytics.analysis.compare.distribution_models import DriftTest
from pytics.analysis.compare.distribution_models import DriftTestMethod
from pytics.analysis.compare.distribution_models import DriftUnavailabilityReason
from pytics.analysis.compare.distribution_models import KolmogorovSmirnovLocation
from pytics.analysis.compare.distribution_models import NumericDistributionDrift
from pytics.analysis.compare.distribution_models import PValueComputation
from pytics.analysis.compare.models import DEFERRED_COMPARISON_FAMILIES
from pytics.analysis.compare.models import ColumnComparison
from pytics.analysis.compare.models import ComparisonCoverage
from pytics.analysis.compare.models import DatasetComparison
from pytics.analysis.compare.models import DeferredComparisonFamily
from pytics.analysis.compare.overview import DatasetOverviewComparison
from pytics.analysis.compare.overview import SemanticTypeCountComparison
from pytics.analysis.compare.schema import PhysicalDtypeComparison
from pytics.analysis.compare.schema import PhysicalDtypeSnapshot
from pytics.analysis.compare.schema import SemanticComparison
from pytics.analysis.compare.schema import SemanticSnapshot
from pytics.analysis.compare.values import CountComparison
from pytics.analysis.compare.values import MetricNumber
from pytics.analysis.compare.values import NumericDifference
from pytics.analysis.compare.values import OptionalCountComparison
from pytics.analysis.compare.values import ProportionDifference
from pytics.analysis.compare.values import directional_difference
