"""Relationship analysis entry points.

The implementation lives in ``pytics.analysis.relationships``. This
module re-exports the records and collectors that dataset analysis and
the current tests import. Those names are an internal compatibility
surface. They are not the public ``profile`` or ``compare`` result, and
they are not a method registry.
"""

from pytics.analysis.relationships.collector import _labels_match
from pytics.analysis.relationships.collector import _require_relationship_attachment
from pytics.analysis.relationships.collector import build_relationships_summary
from pytics.analysis.relationships.collector import collect_relationship_analysis
from pytics.analysis.relationships.collector import relationship_analysis_for_columns
from pytics.analysis.relationships.models import AssociationMethod
from pytics.analysis.relationships.models import BooleanAssociationEstimate
from pytics.analysis.relationships.models import BooleanAssociationMethod
from pytics.analysis.relationships.models import BooleanBooleanPopulation
from pytics.analysis.relationships.models import BooleanBooleanRelationship
from pytics.analysis.relationships.models import BooleanContingencyTable
from pytics.analysis.relationships.models import BooleanDirectionalEstimate
from pytics.analysis.relationships.models import BooleanDirectionalMethod
from pytics.analysis.relationships.models import BooleanGroupContrast
from pytics.analysis.relationships.models import BooleanGroupSummary
from pytics.analysis.relationships.models import BooleanIndependenceMethod
from pytics.analysis.relationships.models import BooleanIndependenceTest
from pytics.analysis.relationships.models import BooleanLevel
from pytics.analysis.relationships.models import ConditionalOutcomeProbability
from pytics.analysis.relationships.models import AssociationResult
from pytics.analysis.relationships.models import CategoricalGroupSummary
from pytics.analysis.relationships.models import CategoryGroupOrder
from pytics.analysis.relationships.models import CorrelationEstimate
from pytics.analysis.relationships.models import CorrelationInterval
from pytics.analysis.relationships.models import CorrelationIntervalMethod
from pytics.analysis.relationships.models import EffectDirection
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import GroupEffectEstimate
from pytics.analysis.relationships.models import GroupEffectMethod
from pytics.analysis.relationships.models import MeanDifferenceEstimate
from pytics.analysis.relationships.models import MeanDifferenceInterval
from pytics.analysis.relationships.models import MeanDifferenceIntervalMethod
from pytics.analysis.relationships.models import MeanDifferenceTest
from pytics.analysis.relationships.models import MeanDifferenceTestMethod
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import NumericBooleanPopulation
from pytics.analysis.relationships.models import NumericBooleanRelationship
from pytics.analysis.relationships.models import NumericCategoricalPopulation
from pytics.analysis.relationships.models import NumericCategoricalRelationship
from pytics.analysis.relationships.models import NumericComputation
from pytics.analysis.relationships.models import NumericNumericRelationship
from pytics.analysis.relationships.models import OmnibusAnovaResult
from pytics.analysis.relationships.models import OmnibusTestMethod
from pytics.analysis.relationships.models import PairPopulation
from pytics.analysis.relationships.models import RelationshipAnalysis
from pytics.analysis.relationships.models import RelationshipFamily
from pytics.analysis.relationships.models import RelationshipRecord
from pytics.analysis.relationships.models import RelationshipsSummary
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import StandardizedDifferenceMethod
from pytics.analysis.relationships.models import StandardizedMeanDifference
from pytics.analysis.relationships.models import UnavailabilityReason
from pytics.analysis.relationships.models import UnimplementedFamilyCount
from pytics.analysis.relationships.models import UnimplementedRelationshipFamily
from pytics.analysis.relationships.numeric_numeric import _association_methods
from pytics.analysis.relationships.numeric_numeric import _bound_endpoint
from pytics.analysis.relationships.numeric_numeric import _fisher_z_bounds
from pytics.analysis.relationships.numeric_numeric import _has_variation
from pytics.analysis.relationships.numeric_numeric import _pearson_interval
from pytics.analysis.relationships.numeric_numeric import _pearson_result
from pytics.analysis.relationships.numeric_numeric import _read_integer_column
from pytics.analysis.relationships.numeric_numeric import _read_numeric_column
from pytics.analysis.relationships.numeric_numeric import _spearman_result
from pytics.analysis.relationships.numeric_numeric import _to_float64
from pytics.analysis.relationships.numeric_numeric import norm
from pytics.analysis.relationships.numeric_numeric import pearsonr
from pytics.analysis.relationships.numeric_numeric import spearmanr
