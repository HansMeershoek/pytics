"""Internal relationship analysis.

``models`` holds records that more than one family can share.
``numeric_numeric`` calculates the one implemented family.
``collector`` chooses pairs and projects the product summary.
Importing this package is not a frozen public API.
"""

from pytics.analysis.relationships.collector import build_relationships_summary
from pytics.analysis.relationships.collector import collect_relationship_analysis
from pytics.analysis.relationships.collector import relationship_analysis_for_columns
from pytics.analysis.relationships.models import AssociationMethod
from pytics.analysis.relationships.models import AssociationResult
from pytics.analysis.relationships.models import CorrelationEstimate
from pytics.analysis.relationships.models import CorrelationInterval
from pytics.analysis.relationships.models import CorrelationIntervalMethod
from pytics.analysis.relationships.models import EffectDirection
from pytics.analysis.relationships.models import FrequentistEvidence
from pytics.analysis.relationships.models import MultipleTestingAdjustment
from pytics.analysis.relationships.models import NumericComputation
from pytics.analysis.relationships.models import NumericNumericRelationship
from pytics.analysis.relationships.models import PairPopulation
from pytics.analysis.relationships.models import RelationshipAnalysis
from pytics.analysis.relationships.models import RelationshipFamily
from pytics.analysis.relationships.models import RelationshipsSummary
from pytics.analysis.relationships.models import ResultAvailability
from pytics.analysis.relationships.models import UnavailabilityReason
from pytics.analysis.relationships.models import UnimplementedFamilyCount
from pytics.analysis.relationships.models import UnimplementedRelationshipFamily
