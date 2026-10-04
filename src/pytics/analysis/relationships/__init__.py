"""Internal relationship analysis.

``models`` holds shared records and the heterogeneous dataset
container. ``numeric_numeric`` calculates Numeric × Numeric.
``numeric_categorical`` calculates Numeric × Categorical.
``collector`` chooses pairs and projects the product summary.
Importing this package is not a frozen public API.
"""

from pytics.analysis.relationships.collector import build_relationships_summary
from pytics.analysis.relationships.collector import collect_relationship_analysis
from pytics.analysis.relationships.collector import relationship_analysis_for_columns
from pytics.analysis.relationships.models import AssociationMethod
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
from pytics.analysis.relationships.models import MultipleTestingAdjustment
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
from pytics.analysis.relationships.models import UnavailabilityReason
from pytics.analysis.relationships.models import UnimplementedFamilyCount
from pytics.analysis.relationships.models import UnimplementedRelationshipFamily
