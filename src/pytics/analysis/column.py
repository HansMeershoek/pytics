"""One column analysis, including the evidence that semantic inference uses.

``analyze_series`` is the only column collection path. It classifies the
physical dtype once, collects basic evidence once, and keeps every evidence
object that this path actually produces. ``None`` means that family was not
collected. It does not mean the underlying count was zero.

Frequency evidence is collected for a non-structural physical categorical
column, and for a string or object column whose selected semantic type is
Categorical. It is not an assessor input. The unpunctuated label rule
reads basic counts, string structure, and pattern evidence. The short-label
rule also reads representation evidence. String-content evidence is not
collected. Structural precedence still returns before candidate collection.

Numeric descriptive statistics are not evidence. After resolution, a column
whose selected semantic type is Numeric is described from its finite
non-missing values. Constant, Empty, and every other selected type do not
take that pass.

Boolean descriptive counts are the same kind of fact. After resolution, a
column whose selected semantic type is Boolean is counted as ``True`` and
``False``. Constant, Empty, and every other selected type do not take that
pass. ``{0, 1}`` stays Numeric and is not counted as Boolean.

Categorical descriptive counts are the same kind of fact. After resolution,
a column whose selected semantic type is Categorical receives its observed
level distribution. That collection does not depend on target selection.
Constant, Empty, and every other selected type do not take that pass.
Frequency evidence remains the aggregate observation. It is not the level
table.

Each result is retained on the column analysis, not on the evidence bundle
and not on the inferred semantic result. The two results stay separate
fields. This path does not register analyses by semantic type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Tuple

import pandas as pd

from pytics.analysis.boolean import BooleanDescriptiveAnalysis
from pytics.analysis.boolean import collect_boolean_descriptive_analysis
from pytics.analysis.categorical import CategoricalDescriptiveAnalysis
from pytics.analysis.categorical import collect_categorical_descriptive_analysis
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.analysis.numeric import collect_numeric_descriptive_analysis
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.column_evidence import AnalyticalInapplicability
from pytics.semantics.column_evidence import BasicColumnEvidence
from pytics.semantics.column_evidence import collect_basic_column_evidence
from pytics.semantics.core_candidates import assess_categorical_candidate
from pytics.semantics.core_candidates import assess_numeric_candidate
from pytics.semantics.core_candidates import assess_text_candidate
from pytics.semantics.frequency_evidence import FrequencyEvidence
from pytics.semantics.frequency_evidence import collect_frequency_evidence
from pytics.semantics.identifier_candidate import assess_identifier_candidate
from pytics.semantics.inferred import InferredSemanticResult
from pytics.semantics.inferred import build_inferred_semantic_result
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.numeric_structure_evidence import NumericStructureEvidence
from pytics.semantics.numeric_structure_evidence import (
    collect_numeric_structure_evidence,
)
from pytics.semantics.pattern_evidence import PatternEvidence
from pytics.semantics.pattern_evidence import collect_pattern_evidence
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.physical import PhysicalDtypeFamily
from pytics.semantics.physical import classify_physical_dtype
from pytics.semantics.representation_evidence import RepresentationEvidence
from pytics.semantics.representation_evidence import collect_representation_evidence
from pytics.semantics.physical_timedelta import interpret_precedence_from_evidence
from pytics.semantics.resolution import ResolutionStatus
from pytics.semantics.resolution import SemanticResolution
from pytics.semantics.resolution import resolve_semantics
from pytics.semantics.string_structure_evidence import StringStructureEvidence
from pytics.semantics.string_structure_evidence import (
    collect_string_structure_evidence,
)

# These families are the collector contracts already implemented. The
# analysis uses them only to avoid calling a collector that would reject
# the dtype. It does not reinterpret the families.
_NUMERIC_FAMILIES = frozenset(
    {
        PhysicalDtypeFamily.INTEGER,
        PhysicalDtypeFamily.FLOATING,
    }
)
_STRING_FAMILIES = frozenset(
    {
        PhysicalDtypeFamily.STRING,
        PhysicalDtypeFamily.OBJECT,
    }
)
@dataclass(frozen=True)
class ColumnEvidence:
    """Evidence retained for one column.

    ``basic`` is always present. The other families are present only when
    this observation path collected them. A missing family is ``None``.
    A collected family keeps the object the collector returned, including
    its composition with ``basic`` or with string structure. ``frequency``
    is that object for a non-structural physical categorical column.
    """

    basic: BasicColumnEvidence
    numeric_structure: Optional[NumericStructureEvidence] = None
    string_structure: Optional[StringStructureEvidence] = None
    pattern: Optional[PatternEvidence] = None
    representation: Optional[RepresentationEvidence] = None
    frequency: Optional[FrequencyEvidence] = None

    def __post_init__(self) -> None:
        _require(self.basic, BasicColumnEvidence, "basic")
        if self.numeric_structure is not None:
            _require(
                self.numeric_structure,
                NumericStructureEvidence,
                "numeric_structure",
            )
            if self.numeric_structure.basic is not self.basic:
                raise ValueError(
                    "numeric_structure.basic must be this evidence's basic"
                )
        if self.string_structure is not None:
            _require(
                self.string_structure,
                StringStructureEvidence,
                "string_structure",
            )
            if self.string_structure.basic is not self.basic:
                raise ValueError("string_structure.basic must be this evidence's basic")
        if self.pattern is not None:
            _require(self.pattern, PatternEvidence, "pattern")
            if self.string_structure is None:
                raise ValueError("pattern evidence requires string-structure evidence")
            if self.pattern.string_structure is not self.string_structure:
                raise ValueError(
                    "pattern.string_structure must be this evidence's "
                    "string_structure"
                )
        if self.representation is not None:
            _require(self.representation, RepresentationEvidence, "representation")
            if self.string_structure is None:
                raise ValueError(
                    "representation evidence requires string-structure evidence"
                )
            if self.representation.string_structure is not self.string_structure:
                raise ValueError(
                    "representation.string_structure must be this evidence's "
                    "string_structure"
                )
        if self.numeric_structure is not None and self.string_structure is not None:
            raise ValueError(
                "numeric-structure evidence and string-structure evidence "
                "do not apply to the same column"
            )
        if self.frequency is not None:
            _require(self.frequency, FrequencyEvidence, "frequency")
            if self.frequency.basic is not self.basic:
                raise ValueError("frequency.basic must be this evidence's basic")


@dataclass(frozen=True)
class ColumnAnalysis:
    """Internal analysis of one physical column.

    ``position`` is the column's place in the source column axis.
    ``label`` is the original column label. It is not a display string,
    and it is not semantic evidence. ``physical``, ``evidence``, and
    ``inferred`` are the facts this path already produced. The Series
    itself is not stored.

    ``numeric_analysis`` is the descriptive profile collected after
    resolution when the selected semantic type is Numeric. It is absent
    for every other outcome, including a physically numeric column that
    resolved as Constant or Empty.

    ``boolean_analysis`` is the true/false profile collected after
    resolution when the selected semantic type is Boolean. It is absent
    for every other outcome, including a physical Boolean column that
    resolved as Constant or Empty, and including numeric ``{0, 1}``.

    ``categorical_analysis`` is the observed level distribution collected
    after resolution when the selected semantic type is Categorical. It
    is absent for every other outcome, including a physical categorical
    column that resolved as Constant or Empty. Target selection does not
    decide whether it is collected.

    None of these profiles is stored on ``evidence``.
    """

    position: int
    label: object
    physical: PhysicalDtype
    evidence: ColumnEvidence
    inferred: InferredSemanticResult
    numeric_analysis: Optional[NumericDescriptiveAnalysis] = None
    boolean_analysis: Optional[BooleanDescriptiveAnalysis] = None
    categorical_analysis: Optional[CategoricalDescriptiveAnalysis] = None

    def __post_init__(self) -> None:
        if type(self.position) is not int or self.position < 0:
            raise ValueError("position must be a non-negative int")
        _require(self.physical, PhysicalDtype, "physical")
        _require(self.evidence, ColumnEvidence, "evidence")
        _require(self.inferred, InferredSemanticResult, "inferred")
        if self.inferred.physical is not self.physical:
            raise ValueError("inferred.physical must be this column's physical")
        _require_numeric_analysis(self)
        _require_boolean_analysis(self)
        _require_categorical_analysis(self)


def analyze_series(
    series: pd.Series,
    *,
    position: int = 0,
    label: object = None,
) -> ColumnAnalysis:
    """Analyze one Series and retain the evidence used to infer it.

    ``position`` and ``label`` are stored as column identity. They are not
    read by physical classification, evidence collection, candidate
    assessment, or resolution. The Series name and index are not read.
    The Series is not copied and is not modified.

    Semantic evidence is collected, then the semantic type is resolved.
    Only after that resolution does this function collect a type-specific
    description. A selected Numeric column receives numeric descriptive
    statistics. A selected Boolean column receives true/false counts.
    A selected Categorical column receives its observed level distribution.
    A column that resolves as Constant, Empty, or any other type is not
    given any of those results. Physical storage alone does not choose
    the pass. Target selection does not choose it either.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("analyze_series expects a pandas Series")
    if type(position) is not int or position < 0:
        raise ValueError("position must be a non-negative int")
    physical = classify_physical_dtype(series)
    basic = collect_basic_column_evidence(series)
    if basic.n_unique_non_missing is None:
        return _column_without_distinct_count(
            series_position=position,
            label=label,
            physical=physical,
            basic=basic,
        )
    structural = interpret_precedence_from_evidence(basic, physical)
    if structural is not None:
        resolution = resolve_semantics(structural_interpretation=structural)
        numeric_structure = None
        string_structure = None
        pattern = None
        representation = None
        frequency = None
    else:
        (
            numeric_structure,
            string_structure,
            pattern,
            representation,
        ) = _evidence_for_candidates(
            series,
            basic,
            physical,
        )
        frequency = _frequency_for_physical_categorical(series, basic, physical)
        candidates = _assess_candidates(
            basic,
            physical,
            numeric_structure,
            string_structure,
            pattern,
            representation,
        )
        resolution = resolve_semantics(candidates=candidates)
    inferred = build_inferred_semantic_result(physical, resolution)
    if inferred.selected_type is SemanticType.CATEGORICAL and frequency is None:
        frequency = collect_frequency_evidence(series, basic)
    numeric_analysis = _descriptive_after_resolution(series, inferred)
    boolean_analysis = _boolean_descriptive_after_resolution(series, inferred)
    categorical_analysis = _categorical_descriptive_after_resolution(series, inferred)
    evidence = ColumnEvidence(
        basic=basic,
        numeric_structure=numeric_structure,
        string_structure=string_structure,
        pattern=pattern,
        representation=representation,
        frequency=frequency,
    )
    return ColumnAnalysis(
        position=position,
        label=label,
        physical=physical,
        evidence=evidence,
        inferred=inferred,
        numeric_analysis=numeric_analysis,
        boolean_analysis=boolean_analysis,
        categorical_analysis=categorical_analysis,
    )


def _column_without_distinct_count(
    *,
    series_position: int,
    label: object,
    physical: PhysicalDtype,
    basic: BasicColumnEvidence,
) -> ColumnAnalysis:
    """Keep identity and safe counts when exact distinctness is unavailable.

    No semantic candidate is assessed. The resolution is insufficient
    evidence because the distinct count those rules need was not observed.
    Downstream eligibility follows that state.
    """
    resolution = SemanticResolution(
        status=ResolutionStatus.INSUFFICIENT_EVIDENCE,
        reason="Exact distinct values are unavailable.",
        candidates=(),
    )
    return ColumnAnalysis(
        position=series_position,
        label=label,
        physical=physical,
        evidence=ColumnEvidence(basic=basic),
        inferred=build_inferred_semantic_result(physical, resolution),
    )


def _descriptive_after_resolution(
    series: pd.Series,
    inferred: InferredSemanticResult,
) -> Optional[NumericDescriptiveAnalysis]:
    """Collect Numeric descriptive statistics only after a Numeric selection.

    Physical integer or floating storage is not enough. Constant and Empty
    numeric columns have already resolved, and this function does not
    describe them. Unresolved and ambiguous columns are not described.
    """
    if inferred.selected_type is not SemanticType.NUMERIC:
        return None
    return collect_numeric_descriptive_analysis(series)


def _boolean_descriptive_after_resolution(
    series: pd.Series,
    inferred: InferredSemanticResult,
) -> Optional[BooleanDescriptiveAnalysis]:
    """Collect Boolean true/false counts only after a Boolean selection.

    Physical boolean storage is not enough. Constant and Empty boolean
    columns have already resolved, and this function does not count them.
    Numeric ``{0, 1}``, two-valued strings, and categorical boolean values
    are not counted. Unresolved and ambiguous columns are not counted.
    """
    if inferred.selected_type is not SemanticType.BOOLEAN:
        return None
    return collect_boolean_descriptive_analysis(series)


def _categorical_descriptive_after_resolution(
    series: pd.Series,
    inferred: InferredSemanticResult,
) -> Optional[CategoricalDescriptiveAnalysis]:
    """Collect the observed level distribution only after a Categorical selection.

    Physical categorical storage is not enough. Constant and Empty
    categorical columns have already resolved, and this function does not
    describe them. A string or object column is described only after it
    has been selected as Categorical. Numeric, Boolean, and unresolved
    columns are not described. Whether the column is later named as a
    target is not an argument.
    """
    if inferred.selected_type is not SemanticType.CATEGORICAL:
        return None
    return collect_categorical_descriptive_analysis(series)


def _require_numeric_analysis(analysis: ColumnAnalysis) -> None:
    """Keep descriptive statistics on a selected Numeric column only."""
    descriptive = analysis.numeric_analysis
    if descriptive is None:
        return
    _require(descriptive, NumericDescriptiveAnalysis, "numeric_analysis")
    if analysis.inferred.selected_type is not SemanticType.NUMERIC:
        raise ValueError(
            "numeric descriptive analysis applies only when the selected "
            "semantic type is Numeric"
        )
    structure = analysis.evidence.numeric_structure
    if structure is not None and structure.finite_count != descriptive.finite_count:
        raise ValueError(
            "numeric descriptive finite_count must match numeric-structure "
            "finite_count"
        )


def _require_boolean_analysis(analysis: ColumnAnalysis) -> None:
    """Keep true/false counts on a selected Boolean column only."""
    described = analysis.boolean_analysis
    if described is None:
        return
    _require(described, BooleanDescriptiveAnalysis, "boolean_analysis")
    if analysis.inferred.selected_type is not SemanticType.BOOLEAN:
        raise ValueError(
            "boolean descriptive analysis applies only when the selected "
            "semantic type is Boolean"
        )
    if described.n_non_missing != analysis.evidence.basic.n_non_missing:
        raise ValueError("boolean true and false counts must equal n_non_missing")


def _require_categorical_analysis(analysis: ColumnAnalysis) -> None:
    """Keep the observed distribution on a selected Categorical column only."""
    described = analysis.categorical_analysis
    if described is None:
        return
    _require(described, CategoricalDescriptiveAnalysis, "categorical_analysis")
    if analysis.inferred.selected_type is not SemanticType.CATEGORICAL:
        raise ValueError(
            "categorical descriptive analysis applies only when the selected "
            "semantic type is Categorical"
        )
    basic = analysis.evidence.basic
    if described.n_non_missing != basic.n_non_missing:
        raise ValueError(
            "categorical descriptive n_non_missing must match basic evidence"
        )
    if described.n_observed != basic.n_unique_non_missing:
        raise ValueError(
            "categorical descriptive n_observed must match n_unique_non_missing"
        )
    frequency = analysis.evidence.frequency
    if frequency is None:
        raise ValueError(
            "categorical descriptive analysis requires the retained frequency evidence"
        )
    if described.most_frequent_count != frequency.most_frequent_count:
        raise ValueError(
            "categorical most_frequent_count must match frequency evidence"
        )
    if described.singleton_count != frequency.singleton_count:
        raise ValueError("categorical singleton_count must match frequency evidence")
    if described.ordered is not analysis.physical.categorical_ordered:
        raise ValueError(
            "categorical ordered flag must match the physical categorical dtype"
        )


def _evidence_for_candidates(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Tuple[
    Optional[NumericStructureEvidence],
    Optional[StringStructureEvidence],
    Optional[PatternEvidence],
    Optional[RepresentationEvidence],
]:
    """Collect the evidence the current assessors can consume.

    Numeric-structure evidence is collected only for integer and floating
    storage. String structure, pattern evidence, and representation
    evidence are collected only when the string-structure collector accepts
    the population. String-content evidence is not collected. Frequency
    evidence is collected separately, and only for physical categorical
    storage. Other families are assessed from the basic evidence and the
    physical dtype alone.
    """
    if physical.family in _NUMERIC_FAMILIES:
        numeric = collect_numeric_structure_evidence(series, basic, physical)
        return numeric, None, None, None
    if physical.family in _STRING_FAMILIES:
        structure, pattern, representation = _string_evidence(series, basic, physical)
        return None, structure, pattern, representation
    return None, None, None, None


def _frequency_for_physical_categorical(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Optional[FrequencyEvidence]:
    """Collect frequency evidence for physical categorical storage only.

    Empty and Constant columns do not reach this helper. Numeric, string,
    object, Boolean, datetime, timedelta, and the other families are not
    scanned. The collector contract is unchanged, including its retention
    bound and its removal of unobserved categorical levels.
    """
    if physical.family is not PhysicalDtypeFamily.CATEGORICAL:
        return None
    return collect_frequency_evidence(series, basic)


def _string_evidence(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Tuple[
    Optional[StringStructureEvidence],
    Optional[PatternEvidence],
    Optional[RepresentationEvidence],
]:
    """Collect string structure, then pattern and representation evidence.

    An ineligible population collects none of them. Pattern evidence and
    representation evidence share the string-structure object. Neither is
    rebuilt from a second string-structure pass.
    """
    structure = _collect_applicable_string_structure(series, basic, physical)
    if structure is None:
        return None, None, None
    pattern = collect_pattern_evidence(series, structure, physical)
    representation = collect_representation_evidence(series, structure, physical)
    return structure, pattern, representation


def _collect_applicable_string_structure(
    series: pd.Series,
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
) -> Optional[StringStructureEvidence]:
    """Return string structure, or None when the collector rejects it.

    ``AnalyticalInapplicability`` means this population is not string
    evidence. Mixed object values and ``bytes`` are that case. They are
    not coerced, and they are not an inference failure. Any other error,
    including an unexpected ``TypeError``, still propagates.
    """
    try:
        return collect_string_structure_evidence(series, basic, physical)
    except AnalyticalInapplicability:
        return None


def _assess_candidates(
    basic: BasicColumnEvidence,
    physical: PhysicalDtype,
    numeric_structure: Optional[NumericStructureEvidence],
    string_structure: Optional[StringStructureEvidence],
    pattern: Optional[PatternEvidence],
    representation: Optional[RepresentationEvidence],
) -> Tuple[CandidateAssessment, ...]:
    """Assess every current candidate from one evidence bundle.

    The assessors do not receive the Series. Omitted evidence stays
    ``None``. A zero-filled stand-in is not created for a family that
    does not apply. Frequency evidence stays on the column record and is
    not an assessor argument.
    """
    return (
        assess_identifier_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
        ),
        assess_numeric_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
        ),
        assess_categorical_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
            representation=representation,
        ),
        assess_text_candidate(
            basic,
            physical,
            numeric_structure=numeric_structure,
            string_structure=string_structure,
            pattern=pattern,
        ),
    )


def _require(value: Any, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        raise TypeError(f"{field} must be a {expected.__name__}")
