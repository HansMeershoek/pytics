"""Variables summary aggregated from an existing dataset analysis.

The builder reads each column's identity, physical dtype, resolved
semantic state, and retained evidence. It does not read a DataFrame,
rescan values, reclassify storage, recollect evidence, or choose a
semantic type. The result does not keep the analysis it was built from.

Every physical column has one common summary. A specialized detail is
attached only for the semantic type resolution selected, and only when
the retained evidence for that detail is present. Numeric detail copies
numeric-structure counts and, when that column analysis retained one,
the finite-population descriptive statistics. Categorical detail copies
frequency counts. Identifier detail copies pattern counts. Those counts
may overlap and are not scores. Empty, Constant, Boolean, Datetime,
Timedelta, Text, insufficient evidence, and ambiguity have no
specialized detail.

Confidence and inference source are not copied. A candidate-derived
selection has neither, and this result does not invent them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from typing import Tuple
from typing import Union

from pytics.analysis.column import ColumnAnalysis
from pytics.analysis.dataset import DatasetAnalysis
from pytics.analysis.numeric import NumericDescriptiveAnalysis
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.physical import PhysicalDtype
from pytics.semantics.resolution import ResolutionStatus


@dataclass(frozen=True)
class NumericVariableDetail:
    """Structural facts for a column selected as Numeric.

    The counts are copied from retained numeric-structure evidence.
    ``n_non_missing`` is that evidence's denominator, copied so a ratio
    does not need the evidence object. It is not a second observation.
    The variable summary requires it to equal the universal non-missing
    count.

    Sign counts and integer-like counts partition finite values.
    Finite values and the two infinities partition non-missing values.
    ``is_non_decreasing`` and ``is_non_increasing`` are ``bool`` when
    every non-missing value is finite, and both are ``None`` when any
    non-missing value is infinite. ``None`` is not false.     No non-missing
    values and one finite value are both directions. These flags do not
    record a step size.

    ``descriptive`` is the retained finite-population profile when column
    analysis collected one. It is a separate frozen value, not the
    numeric-structure evidence and not a Series. Range and interquartile
    range stay on that value. Skewness, kurtosis, and outlier signals are
    not part of it.
    """

    n_non_missing: int
    finite_count: int
    positive_count: int
    negative_count: int
    zero_count: int
    positive_infinity_count: int
    negative_infinity_count: int
    integer_like_count: int
    non_integer_like_count: int
    is_non_decreasing: Optional[bool]
    is_non_increasing: Optional[bool]
    descriptive: Optional[NumericDescriptiveAnalysis] = None

    def __post_init__(self) -> None:
        _require_count(self.n_non_missing, "n_non_missing")
        _require_count(self.finite_count, "finite_count")
        _require_count(self.positive_count, "positive_count")
        _require_count(self.negative_count, "negative_count")
        _require_count(self.zero_count, "zero_count")
        _require_count(self.positive_infinity_count, "positive_infinity_count")
        _require_count(self.negative_infinity_count, "negative_infinity_count")
        _require_count(self.integer_like_count, "integer_like_count")
        _require_count(self.non_integer_like_count, "non_integer_like_count")
        if (
            self.finite_count
            + self.positive_infinity_count
            + self.negative_infinity_count
            != self.n_non_missing
        ):
            raise ValueError("finite and infinite counts must equal n_non_missing")
        if (
            self.positive_count + self.negative_count + self.zero_count
            != self.finite_count
        ):
            raise ValueError(
                "positive, negative, and zero counts must equal finite_count"
            )
        if self.integer_like_count + self.non_integer_like_count != self.finite_count:
            raise ValueError(
                "integer-like and non-integer-like counts must equal finite_count"
            )
        _require_monotonicity(
            self.n_non_missing,
            self.finite_count,
            self.is_non_decreasing,
            self.is_non_increasing,
        )
        _require_descriptive(self.finite_count, self.descriptive)

    @property
    def infinity_count(self) -> int:
        """Positive and negative infinities added together.

        This is not stored separately from those two counts.
        """
        return self.positive_infinity_count + self.negative_infinity_count

    @property
    def finite_ratio(self) -> Optional[float]:
        """Finite values divided by non-missing values.

        ``None`` when there is no non-missing value. Infinities are
        non-missing and are not finite.
        """
        return _ratio(self.finite_count, self.n_non_missing)

    @property
    def positive_ratio(self) -> Optional[float]:
        """Finite values greater than zero, divided by finite values.

        ``None`` when there is no finite value.
        """
        return _ratio(self.positive_count, self.finite_count)

    @property
    def negative_ratio(self) -> Optional[float]:
        """Finite values less than zero, divided by finite values.

        ``None`` when there is no finite value.
        """
        return _ratio(self.negative_count, self.finite_count)

    @property
    def zero_ratio(self) -> Optional[float]:
        """Finite zeros divided by finite values.

        ``None`` when there is no finite value.
        """
        return _ratio(self.zero_count, self.finite_count)

    @property
    def integer_like_ratio(self) -> Optional[float]:
        """Finite integer-like values divided by finite values.

        ``None`` when there is no finite value. This is not a discrete
        or binary threshold.
        """
        return _ratio(self.integer_like_count, self.finite_count)


@dataclass(frozen=True)
class CategoricalVariableDetail:
    """Frequency facts for a column selected as Categorical.

    The two counts are copied from retained frequency evidence. The
    denominators are copied from the basic evidence that frequency
    evidence was composed with. They are not a second observation. The
    variable summary requires them to equal the universal counts.

    ``most_frequent_ratio`` divides by non-missing values.
    ``singleton_ratio`` divides by distinct non-missing values. The most
    frequent value itself is not retained, and neither is the frequency
    table. Unobserved categorical levels are not counts.
    """

    n_non_missing: int
    n_unique_non_missing: int
    most_frequent_count: int
    singleton_count: int

    def __post_init__(self) -> None:
        _require_count(self.n_non_missing, "n_non_missing")
        _require_count(self.n_unique_non_missing, "n_unique_non_missing")
        _require_count(self.most_frequent_count, "most_frequent_count")
        _require_count(self.singleton_count, "singleton_count")
        if self.n_unique_non_missing > self.n_non_missing:
            raise ValueError("n_unique_non_missing cannot exceed n_non_missing")
        _require_frequency_counts(
            self.n_non_missing,
            self.n_unique_non_missing,
            self.most_frequent_count,
            self.singleton_count,
        )

    @property
    def most_frequent_ratio(self) -> Optional[float]:
        """Largest non-missing count divided by non-missing values.

        ``None`` when there is no non-missing value.
        """
        return _ratio(self.most_frequent_count, self.n_non_missing)

    @property
    def singleton_ratio(self) -> Optional[float]:
        """Share of distinct non-missing values that occur once.

        The denominator is the distinct non-missing count, not the row
        count. ``None`` when there is no distinct non-missing value.
        """
        return _ratio(self.singleton_count, self.n_unique_non_missing)


@dataclass(frozen=True)
class IdentifierVariableDetail:
    """Pattern facts for a column selected as Identifier.

    The counts are copied from retained pattern evidence.
    ``n_non_missing`` is their denominator, copied from the basic
    evidence that pattern evidence was composed with. The variable
    summary requires it to equal the universal non-missing count.

    A value may increment more than one count. A compact UUID increments
    both ``uuid_count`` and ``hex_32_count``. The counts are not scores
    and are not added together. No identifier confidence is stored.
    """

    n_non_missing: int
    uuid_count: int
    ipv4_count: int
    ipv6_count: int
    hex_32_count: int
    hex_40_count: int
    hex_64_count: int
    hex_128_count: int

    def __post_init__(self) -> None:
        _require_count(self.n_non_missing, "n_non_missing")
        for name in _PATTERN_COUNTS:
            count = getattr(self, name)
            _require_count(count, name)
            if count > self.n_non_missing:
                raise ValueError(f"{name} cannot exceed n_non_missing")

    @property
    def uuid_ratio(self) -> Optional[float]:
        """UUID syntax matches divided by non-missing values."""
        return _ratio(self.uuid_count, self.n_non_missing)

    @property
    def ipv4_ratio(self) -> Optional[float]:
        """IPv4 syntax matches divided by non-missing values."""
        return _ratio(self.ipv4_count, self.n_non_missing)

    @property
    def ipv6_ratio(self) -> Optional[float]:
        """IPv6 syntax matches divided by non-missing values."""
        return _ratio(self.ipv6_count, self.n_non_missing)

    @property
    def hex_32_ratio(self) -> Optional[float]:
        """32-character hexadecimal tokens divided by non-missing values."""
        return _ratio(self.hex_32_count, self.n_non_missing)

    @property
    def hex_40_ratio(self) -> Optional[float]:
        """40-character hexadecimal tokens divided by non-missing values."""
        return _ratio(self.hex_40_count, self.n_non_missing)

    @property
    def hex_64_ratio(self) -> Optional[float]:
        """64-character hexadecimal tokens divided by non-missing values."""
        return _ratio(self.hex_64_count, self.n_non_missing)

    @property
    def hex_128_ratio(self) -> Optional[float]:
        """128-character hexadecimal tokens divided by non-missing values."""
        return _ratio(self.hex_128_count, self.n_non_missing)


VariableDetail = Union[
    NumericVariableDetail,
    CategoricalVariableDetail,
    IdentifierVariableDetail,
]

_PATTERN_COUNTS = (
    "uuid_count",
    "ipv4_count",
    "ipv6_count",
    "hex_32_count",
    "hex_40_count",
    "hex_64_count",
    "hex_128_count",
)


@dataclass(frozen=True)
class VariableSummary:
    """Common facts for one physical column, plus optional typed detail.

    ``position`` is the column's place on the source column axis.
    ``label`` is the original label object. It is not a display string,
    and the label alone does not identify the column. ``physical`` is
    the physical dtype already classified. It is not flattened into a
    family name.

    ``resolution_status`` is the resolution state. ``selected_type`` is
    present only when that state is ``RESOLVED``. A candidate-derived
    selection is resolved while its interpretation is absent. This
    summary does not treat interpretation presence as that test, and it
    does not store confidence or inference source.

    The four counts and ``missing_ratio`` come from basic evidence.
    ``unique_ratio_non_missing`` divides distinct non-missing values by
    non-missing values, and is ``None`` when that count is zero. It is
    not an identifier threshold and not a ratio over all rows.

    ``detail`` follows ``selected_type``. It is absent when that type
    has no specialized detail in this result, and when the retained
    evidence for that detail was not collected.
    """

    position: int
    label: object
    physical: PhysicalDtype
    resolution_status: ResolutionStatus
    selected_type: Optional[SemanticType]
    n_total: int
    n_missing: int
    n_non_missing: int
    n_unique_non_missing: int
    detail: Optional[VariableDetail] = None

    def __post_init__(self) -> None:
        if type(self.position) is not int or self.position < 0:
            raise ValueError("position must be a non-negative int")
        if not isinstance(self.physical, PhysicalDtype):
            raise TypeError("physical must be a PhysicalDtype")
        if not isinstance(self.resolution_status, ResolutionStatus):
            raise TypeError("resolution_status must be a ResolutionStatus")
        _require_selected_type(self.resolution_status, self.selected_type)
        _require_count(self.n_total, "n_total")
        _require_count(self.n_missing, "n_missing")
        _require_count(self.n_non_missing, "n_non_missing")
        _require_count(self.n_unique_non_missing, "n_unique_non_missing")
        if self.n_missing > self.n_total:
            raise ValueError("n_missing cannot exceed n_total")
        if self.n_non_missing != self.n_total - self.n_missing:
            raise ValueError("n_non_missing must equal n_total - n_missing")
        if self.n_unique_non_missing > self.n_non_missing:
            raise ValueError("n_unique_non_missing cannot exceed n_non_missing")
        _require_detail(self.selected_type, self.detail)
        _require_detail_consistency(self)

    @property
    def missing_ratio(self) -> Optional[float]:
        """Missing values divided by all values.

        ``None`` when the column has no rows.
        """
        return _ratio(self.n_missing, self.n_total)

    @property
    def unique_ratio_non_missing(self) -> Optional[float]:
        """Distinct non-missing values divided by non-missing values.

        ``None`` when there is no non-missing value. The denominator is
        not the row count.
        """
        return _ratio(self.n_unique_non_missing, self.n_non_missing)


@dataclass(frozen=True)
class VariablesSummary:
    """Ordered variable summaries for one dataset analysis.

    ``variables`` has one summary per physical column, in source order.
    Duplicate labels stay distinct because position is the identity.
    The summary does not repeat dataset-overview facts.
    """

    variables: Tuple[VariableSummary, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.variables, tuple):
            raise TypeError("variables must be a tuple")
        n_total: Optional[int] = None
        for position, variable in enumerate(self.variables):
            if not isinstance(variable, VariableSummary):
                raise TypeError("variables must contain VariableSummary values")
            if variable.position != position:
                raise ValueError("variable position must match source order")
            if n_total is None:
                n_total = variable.n_total
            elif variable.n_total != n_total:
                raise ValueError("every variable must share n_total")

    @property
    def n_variables(self) -> int:
        """How many physical columns this summary contains."""
        return len(self.variables)


def build_variables_summary(analysis: DatasetAnalysis) -> VariablesSummary:
    """Summarize one dataset analysis as ordered variable facts.

    The argument must already be a ``DatasetAnalysis``. A DataFrame is
    not accepted and is not analyzed. The analysis is not modified.
    """
    if not isinstance(analysis, DatasetAnalysis):
        raise TypeError("build_variables_summary expects a DatasetAnalysis")
    return VariablesSummary(
        variables=tuple(_variable_from_column(column) for column in analysis.columns)
    )


def _variable_from_column(column: ColumnAnalysis) -> VariableSummary:
    """Copy one column's retained facts into a variable summary."""
    status = column.inferred.resolution.status
    if status is ResolutionStatus.RESOLVED:
        selected = column.inferred.selected_type
        if not isinstance(selected, SemanticType):
            raise ValueError("a resolved column has no selected semantic type")
    elif status in (
        ResolutionStatus.INSUFFICIENT_EVIDENCE,
        ResolutionStatus.AMBIGUOUS,
    ):
        if column.inferred.selected_type is not None:
            raise ValueError("an unresolved column has a selected semantic type")
        selected = None
    else:
        raise ValueError(f"unrecognized resolution status: {status!r}")
    basic = column.evidence.basic
    return VariableSummary(
        position=column.position,
        label=column.label,
        physical=column.physical,
        resolution_status=status,
        selected_type=selected,
        n_total=basic.n_total,
        n_missing=basic.n_missing,
        n_non_missing=basic.n_non_missing,
        n_unique_non_missing=basic.n_unique_non_missing,
        detail=_detail_for(column, selected),
    )


def _detail_for(
    column: ColumnAnalysis,
    selected: Optional[SemanticType],
) -> Optional[VariableDetail]:
    """Copy the specialized detail for the selected semantic type.

    Physical storage does not choose the detail. Retained evidence is
    copied into a product value. The evidence object itself is not stored.
    """
    if selected is SemanticType.NUMERIC:
        return _numeric_detail(column)
    if selected is SemanticType.CATEGORICAL:
        return _categorical_detail(column)
    if selected is SemanticType.IDENTIFIER:
        return _identifier_detail(column)
    return None


def _numeric_detail(column: ColumnAnalysis) -> Optional[NumericVariableDetail]:
    evidence = column.evidence.numeric_structure
    if evidence is None:
        return None
    return NumericVariableDetail(
        n_non_missing=evidence.basic.n_non_missing,
        finite_count=evidence.finite_count,
        positive_count=evidence.positive_count,
        negative_count=evidence.negative_count,
        zero_count=evidence.zero_count,
        positive_infinity_count=evidence.positive_infinity_count,
        negative_infinity_count=evidence.negative_infinity_count,
        integer_like_count=evidence.integer_like_count,
        non_integer_like_count=evidence.non_integer_like_count,
        is_non_decreasing=evidence.is_non_decreasing,
        is_non_increasing=evidence.is_non_increasing,
        descriptive=_copied_descriptive(column.numeric_analysis),
    )


def _copied_descriptive(
    descriptive: Optional[NumericDescriptiveAnalysis],
) -> Optional[NumericDescriptiveAnalysis]:
    """Copy retained descriptive facts without calculating them again.

    The product value is a new frozen object. It does not alias the
    analysis object, and it does not keep a Series or the source array.
    """
    if descriptive is None:
        return None
    return NumericDescriptiveAnalysis(
        finite_count=descriptive.finite_count,
        minimum=descriptive.minimum,
        maximum=descriptive.maximum,
        mean=descriptive.mean,
        median=descriptive.median,
        standard_deviation=descriptive.standard_deviation,
        q1=descriptive.q1,
        q3=descriptive.q3,
    )


def _require_descriptive(
    finite_count: int,
    descriptive: Optional[NumericDescriptiveAnalysis],
) -> None:
    if descriptive is None:
        return
    if not isinstance(descriptive, NumericDescriptiveAnalysis):
        raise TypeError("descriptive must be a NumericDescriptiveAnalysis")
    if descriptive.finite_count != finite_count:
        raise ValueError("descriptive finite_count must match numeric detail")


def _categorical_detail(
    column: ColumnAnalysis,
) -> Optional[CategoricalVariableDetail]:
    evidence = column.evidence.frequency
    if evidence is None:
        return None
    basic = evidence.basic
    return CategoricalVariableDetail(
        n_non_missing=basic.n_non_missing,
        n_unique_non_missing=basic.n_unique_non_missing,
        most_frequent_count=evidence.most_frequent_count,
        singleton_count=evidence.singleton_count,
    )


def _identifier_detail(
    column: ColumnAnalysis,
) -> Optional[IdentifierVariableDetail]:
    evidence = column.evidence.pattern
    if evidence is None:
        return None
    return IdentifierVariableDetail(
        n_non_missing=evidence.string_structure.basic.n_non_missing,
        uuid_count=evidence.uuid_count,
        ipv4_count=evidence.ipv4_count,
        ipv6_count=evidence.ipv6_count,
        hex_32_count=evidence.hex_32_count,
        hex_40_count=evidence.hex_40_count,
        hex_64_count=evidence.hex_64_count,
        hex_128_count=evidence.hex_128_count,
    )


def _require_selected_type(
    status: ResolutionStatus,
    selected_type: Optional[SemanticType],
) -> None:
    if status is ResolutionStatus.RESOLVED:
        if not isinstance(selected_type, SemanticType):
            raise ValueError("a resolved variable requires a selected semantic type")
        return
    if selected_type is not None:
        raise ValueError("an unresolved variable has no selected semantic type")


def _require_detail(
    selected_type: Optional[SemanticType],
    detail: Optional[VariableDetail],
) -> None:
    if selected_type is SemanticType.NUMERIC:
        if detail is not None and not isinstance(detail, NumericVariableDetail):
            raise TypeError("numeric detail must be a NumericVariableDetail")
        return
    if selected_type is SemanticType.CATEGORICAL:
        if detail is not None and not isinstance(detail, CategoricalVariableDetail):
            raise TypeError("categorical detail must be a CategoricalVariableDetail")
        return
    if selected_type is SemanticType.IDENTIFIER:
        if detail is not None and not isinstance(detail, IdentifierVariableDetail):
            raise TypeError("identifier detail must be an IdentifierVariableDetail")
        return
    if detail is not None:
        raise TypeError(
            "specialized detail applies only to Numeric, Categorical, and Identifier"
        )


def _require_detail_consistency(summary: VariableSummary) -> None:
    detail = summary.detail
    if isinstance(detail, NumericVariableDetail):
        if detail.n_non_missing != summary.n_non_missing:
            raise ValueError("numeric detail n_non_missing must match the variable")
        _require_numeric_uniqueness(summary, detail)
        return
    if isinstance(detail, CategoricalVariableDetail):
        if detail.n_non_missing != summary.n_non_missing:
            raise ValueError("categorical detail n_non_missing must match the variable")
        if detail.n_unique_non_missing != summary.n_unique_non_missing:
            raise ValueError(
                "categorical detail n_unique_non_missing must match the variable"
            )
        return
    if isinstance(detail, IdentifierVariableDetail):
        if detail.n_non_missing != summary.n_non_missing:
            raise ValueError("identifier detail n_non_missing must match the variable")


def _require_numeric_uniqueness(
    summary: VariableSummary,
    detail: NumericVariableDetail,
) -> None:
    """Keep monotonicity consistent with the universal distinct count.

    A finite population that is both non-decreasing and non-increasing
    has one distinct value when it has more than one observation. A
    finite population with one distinct value is both directions.
    """
    finite = detail.finite_count == detail.n_non_missing
    both = detail.is_non_decreasing is True and detail.is_non_increasing is True
    if (
        summary.n_non_missing > 1
        and summary.n_unique_non_missing == 1
        and finite
        and not both
    ):
        raise ValueError(
            "a finite constant numeric population is both "
            "non-decreasing and non-increasing"
        )
    if summary.n_non_missing > 1 and both and summary.n_unique_non_missing != 1:
        raise ValueError(
            "a series that is both non-decreasing and non-increasing "
            "has one distinct non-missing value"
        )


def _require_monotonicity(
    n_non_missing: int,
    finite_count: int,
    is_non_decreasing: Optional[bool],
    is_non_increasing: Optional[bool],
) -> None:
    flags = (is_non_decreasing, is_non_increasing)
    if finite_count != n_non_missing:
        if flags != (None, None):
            raise ValueError(
                "monotonicity is undefined when a non-missing value is infinite"
            )
        return
    if type(is_non_decreasing) is not bool or type(is_non_increasing) is not bool:
        raise TypeError("monotonicity is a bool when every non-missing value is finite")
    if n_non_missing <= 1 and flags != (True, True):
        raise ValueError(
            "zero or one finite non-missing observation is both "
            "non-decreasing and non-increasing"
        )


def _require_frequency_counts(
    n_non_missing: int,
    n_unique: int,
    most_frequent_count: int,
    singleton_count: int,
) -> None:
    if n_non_missing == 0:
        if most_frequent_count != 0 or singleton_count != 0:
            raise ValueError(
                "an empty frequency population has most_frequent_count 0 "
                "and singleton_count 0"
            )
        return
    if n_unique < 1:
        raise ValueError(
            "n_unique_non_missing must be positive when non-missing "
            "observations exist"
        )
    if most_frequent_count < 1:
        raise ValueError(
            "most_frequent_count must be >= 1 when non-missing observations exist"
        )
    if most_frequent_count > n_non_missing:
        raise ValueError("most_frequent_count cannot exceed n_non_missing")
    if singleton_count > n_unique:
        raise ValueError("singleton_count cannot exceed n_unique_non_missing")
    if n_unique == 1:
        if most_frequent_count != n_non_missing:
            raise ValueError(
                "the only distinct non-missing value occurs n_non_missing times"
            )
        expected = 1 if n_non_missing == 1 else 0
        if singleton_count != expected:
            raise ValueError(
                "singleton_count is 1 only when the single distinct value occurs once"
            )
        return
    if most_frequent_count == 1:
        if singleton_count != n_unique or n_non_missing != n_unique:
            raise ValueError(
                "when every non-missing value occurs once, singleton_count "
                "equals n_unique_non_missing"
            )
        return
    non_singletons = n_unique - singleton_count
    if non_singletons < 1:
        raise ValueError(
            "a repeated value means at least one distinct value is not a singleton"
        )
    lower = singleton_count + 2 * (non_singletons - 1) + most_frequent_count
    upper = singleton_count + non_singletons * most_frequent_count
    if not lower <= n_non_missing <= upper:
        raise ValueError(
            "frequency counts are inconsistent with n_non_missing and "
            "n_unique_non_missing"
        )


def _require_count(value: object, field: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative int")


def _ratio(count: int, denominator: int) -> Optional[float]:
    if denominator == 0:
        return None
    return count / denominator
