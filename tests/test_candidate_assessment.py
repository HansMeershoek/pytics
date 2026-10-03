"""TSK-011: candidate assessment is not a selected interpretation."""

from __future__ import annotations

import dataclasses

import pytest

import pytics
import pytics.semantics as semantics_package
from pytics.semantics.candidate import CandidateAssessment
from pytics.semantics.candidate import CandidateDisposition
from pytics.semantics.interpretation import SemanticEvidence
from pytics.semantics.interpretation import SemanticInterpretation
from pytics.semantics.interpretation import SemanticType

_SUPPORT = SemanticEvidence("All 4 non-missing values match the UUID syntax.")
_HEX = SemanticEvidence(
    "All 4 non-missing values are 64-character ASCII hexadecimal tokens."
)
_OTHER = SemanticEvidence("All 4 non-missing values contain a space.")


def test_candidate_disposition_has_three_explicit_values():
    assert [item.name for item in CandidateDisposition] == [
        "SUPPORTED",
        "NOT_SUPPORTED",
        "CONTRADICTED",
    ]
    assert CandidateDisposition.SUPPORTED.value == "supported"
    assert CandidateDisposition.NOT_SUPPORTED.value == "not_supported"
    assert CandidateDisposition.CONTRADICTED.value == "contradicted"


def test_candidate_assessment_is_frozen_and_has_no_resolution_fields():
    assessment = CandidateAssessment(
        semantic_type=SemanticType.IDENTIFIER,
        disposition=CandidateDisposition.SUPPORTED,
        supporting_evidence=(_SUPPORT,),
    )

    assert assessment.__dataclass_params__.frozen is True
    assert [field.name for field in dataclasses.fields(assessment)] == [
        "semantic_type",
        "disposition",
        "supporting_evidence",
        "contradicting_evidence",
    ]
    banned = (
        "score",
        "points",
        "weight",
        "probability",
        "confidence",
        "confidence_percentage",
        "threshold_score",
        "winner",
        "rank",
        "priority",
    )
    names = {field.name for field in dataclasses.fields(assessment)}
    for name in banned:
        assert name not in names
        assert not hasattr(assessment, name)
    with pytest.raises(dataclasses.FrozenInstanceError):
        assessment.disposition = CandidateDisposition.NOT_SUPPORTED  # type: ignore[misc]
    assert not isinstance(assessment, SemanticInterpretation)


def test_semantic_type_and_disposition_are_required():
    with pytest.raises(TypeError, match="semantic_type"):
        CandidateAssessment(
            semantic_type="identifier",  # type: ignore[arg-type]
            disposition=CandidateDisposition.NOT_SUPPORTED,
        )
    with pytest.raises(TypeError, match="disposition"):
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition="not_supported",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "field",
    ["supporting_evidence", "contradicting_evidence"],
)
@pytest.mark.parametrize(
    "value",
    [
        "All 4 non-missing values match the UUID syntax.",
        b"text",
        {"statement": "x"},
        _SUPPORT,
        None,
        3,
    ],
)
def test_evidence_sequences_reject_non_sequences(field: str, value: object):
    kwargs = {
        "semantic_type": SemanticType.TEXT,
        "disposition": CandidateDisposition.NOT_SUPPORTED,
        field: value,
    }
    with pytest.raises(TypeError, match=field):
        CandidateAssessment(**kwargs)  # type: ignore[arg-type]


def test_evidence_entries_must_be_statements():
    with pytest.raises(TypeError, match="supporting_evidence"):
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.NOT_SUPPORTED,
            supporting_evidence=("All 4 non-missing values match the UUID syntax.",),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="contradicting_evidence"):
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.NOT_SUPPORTED,
            contradicting_evidence=(_SUPPORT, "not evidence"),  # type: ignore[arg-type]
        )


def test_evidence_sequences_are_stored_as_independent_tuples():
    supporting = [_SUPPORT]
    contradicting = [_OTHER]
    assessment = CandidateAssessment(
        semantic_type=SemanticType.IDENTIFIER,
        disposition=CandidateDisposition.SUPPORTED,
        supporting_evidence=supporting,
        contradicting_evidence=contradicting,
    )

    supporting.append(_HEX)
    contradicting.append(_HEX)

    assert isinstance(assessment.supporting_evidence, tuple)
    assert isinstance(assessment.contradicting_evidence, tuple)
    assert assessment.supporting_evidence == (_SUPPORT,)
    assert assessment.contradicting_evidence == (_OTHER,)


def test_supported_requires_supporting_evidence():
    with pytest.raises(ValueError, match="SUPPORTED requires supporting evidence"):
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.SUPPORTED,
        )
    with pytest.raises(ValueError, match="SUPPORTED requires supporting evidence"):
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.SUPPORTED,
            contradicting_evidence=(_OTHER,),
        )


def test_contradicted_requires_contradicting_evidence():
    with pytest.raises(
        ValueError, match="CONTRADICTED requires contradicting evidence"
    ):
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.CONTRADICTED,
        )
    with pytest.raises(
        ValueError, match="CONTRADICTED requires contradicting evidence"
    ):
        CandidateAssessment(
            semantic_type=SemanticType.IDENTIFIER,
            disposition=CandidateDisposition.CONTRADICTED,
            supporting_evidence=(_SUPPORT,),
        )


def test_not_supported_may_carry_no_evidence():
    assessment = CandidateAssessment(
        semantic_type=SemanticType.CATEGORICAL,
        disposition=CandidateDisposition.NOT_SUPPORTED,
    )

    assert assessment.supporting_evidence == ()
    assert assessment.contradicting_evidence == ()
    assert assessment.disposition is CandidateDisposition.NOT_SUPPORTED


def test_not_supported_keeps_its_disposition_when_statements_are_present():
    assessment = CandidateAssessment(
        semantic_type=SemanticType.TEXT,
        disposition=CandidateDisposition.NOT_SUPPORTED,
        supporting_evidence=(_SUPPORT,),
        contradicting_evidence=(_OTHER,),
    )

    assert assessment.disposition is CandidateDisposition.NOT_SUPPORTED
    assert assessment.supporting_evidence == (_SUPPORT,)
    assert assessment.contradicting_evidence == (_OTHER,)


@pytest.mark.parametrize(
    "disposition",
    [CandidateDisposition.SUPPORTED, CandidateDisposition.CONTRADICTED],
)
def test_support_and_contradiction_can_coexist(disposition: CandidateDisposition):
    assessment = CandidateAssessment(
        semantic_type=SemanticType.NUMERIC,
        disposition=disposition,
        supporting_evidence=(_SUPPORT,),
        contradicting_evidence=(_OTHER,),
    )

    assert assessment.semantic_type is SemanticType.NUMERIC
    assert assessment.disposition is disposition
    assert assessment.supporting_evidence == (_SUPPORT,)
    assert assessment.contradicting_evidence == (_OTHER,)


def test_candidate_assessment_is_not_on_the_public_api():
    assert pytics.__all__ == ["profile", "compare"]
    assert not hasattr(pytics, "CandidateAssessment")
    assert not hasattr(pytics, "CandidateDisposition")
    assert not hasattr(semantics_package, "CandidateAssessment")
    assert not hasattr(semantics_package, "CandidateDisposition")
