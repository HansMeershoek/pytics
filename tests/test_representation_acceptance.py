"""TSK-045 acceptance fixtures.

The frames are synthetic. Column names are neutral on purpose. They are
not used as evidence.
"""

from __future__ import annotations

import pandas as pd

from pytics.analysis.dataset import analyze_dataframe
from pytics.presentation.notebook.profile import render_profile
from pytics.results.profile import profile_result
from pytics.semantics.interpretation import SemanticType
from pytics.semantics.representation_evidence import RepresentationFamily
from pytics.semantics.representation_evidence import RepresentationMixture
from pytics.semantics.resolution import ResolutionStatus


def _mixed_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "c01": [
                "New York",
                "South Korea",
                "New York",
                "São Paulo",
                "South Korea",
                "São Paulo",
            ],
            "c02": [
                "The river is wide and the road is long today.",
                "Another short note about the same city and its harbor.",
            ]
            * 3,
            "c03": [
                "2021-02-16",
                "16/03/2020",
                "22 Oct 23",
                "45390",
                "45391",
                "44000",
            ],
            "c04": ["€2.5m", "$1M-$5M", "5000000", "1-10", "unknown", "unknown"],
            "c05": [f"row-{index:04d}" for index in range(6)],
            "c06": [f"https://example.com/{index}" for index in range(6)],
            "c07": [f"user{index}@example.com" for index in range(6)],
            "c08": ["67/100", "80/100", "1 stars", "needs review", "warm", "A"],
            "c09": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
            "c10": ["red", "blue", "red", "green", "blue", "red"],
        }
    )


def test_mixed_fixture_keeps_source_and_separates_evidence_from_type():
    frame = _mixed_frame()
    original = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    pd.testing.assert_frame_equal(frame, original)
    selected = [column.inferred.selected_type for column in analysis.columns]
    assert selected == [
        SemanticType.CATEGORICAL,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        SemanticType.NUMERIC,
        SemanticType.CATEGORICAL,
    ]
    prose = analysis.columns[1].evidence.representation
    dates = analysis.columns[2].evidence.representation
    money = analysis.columns[3].evidence.representation
    keys = analysis.columns[4].evidence.representation
    urls = analysis.columns[5].evidence.representation
    emails = analysis.columns[6].evidence.representation
    scores = analysis.columns[7].evidence.representation
    assert prose.count(RepresentationFamily.PROSE_LIKE) == 6
    assert prose.mixture is RepresentationMixture.OBSERVED
    assert dates.count(RepresentationFamily.TEMPORAL_LIKE) == 3
    assert dates.count(RepresentationFamily.NUMERIC_LIKE) == 3
    assert dates.mixture is RepresentationMixture.CONFLICTING
    assert money.count(RepresentationFamily.MISSING_LIKE) == 2
    assert money.count(RepresentationFamily.CURRENCY_LIKE) == 2
    assert money.mixture is RepresentationMixture.OBSERVED
    assert analysis.columns[3].inferred.selected_type is None
    assert analysis.columns[3].evidence.basic.n_missing == 0
    assert list(frame["c04"]) == [
        "€2.5m",
        "$1M-$5M",
        "5000000",
        "1-10",
        "unknown",
        "unknown",
    ]
    assert keys.mixture is RepresentationMixture.OBSERVED
    assert urls.count(RepresentationFamily.URL_LIKE) == 6
    assert emails.count(RepresentationFamily.EMAIL_LIKE) == 6
    assert analysis.columns[5].inferred.selected_type is not SemanticType.IDENTIFIER
    assert analysis.columns[6].inferred.selected_type is not SemanticType.IDENTIFIER
    assert scores.mixture is RepresentationMixture.CONFLICTING
    for column in analysis.columns:
        if column.inferred.selected_type is None:
            assert column.inferred.resolution.status is (
                ResolutionStatus.INSUFFICIENT_EVIDENCE
            )
            assert column.inferred.resolution.reason == "No candidate is supported."
    summary = analysis.relationship_analysis
    assert summary.n_supported_pairs == 3
    assert summary.n_unimplemented_family_pairs == 0
    assert summary.n_ineligible_pairs == 42
    again = analyze_dataframe(frame)
    assert [column.inferred for column in again.columns] == [
        column.inferred for column in analysis.columns
    ]
    assert [column.evidence.representation for column in again.columns] == [
        column.evidence.representation for column in analysis.columns
    ]


def test_public_result_retains_representation_for_a_later_renderer():
    result = profile_result(_mixed_frame())
    dates = result.variables[2]
    junk = result.variables[1]
    assert dates.resolution_status is ResolutionStatus.INSUFFICIENT_EVIDENCE
    assert dates.selected_type is None
    assert dates.record.evidence.representation.mixture is (
        RepresentationMixture.CONFLICTING
    )
    assert junk.record.evidence.representation.mixture is (
        RepresentationMixture.OBSERVED
    )
    html = render_profile(result)
    assert "Insufficient evidence" in html
    assert "45390" not in html


def test_penguins_shaped_table_stays_categorical_and_numeric():
    n = 344
    groups = ["alpha", "beta", "gamma"]
    sites = ["north", "south", "east"]
    flags = ["male", "female"]
    frame = pd.DataFrame(
        {
            "p0": [groups[index % 3] for index in range(n)],
            "p1": [sites[index % 3] for index in range(n)],
            "p2": [32.1 + (index % 17) * 0.1 for index in range(n)],
            "p3": [15.0 + (index % 9) * 0.1 for index in range(n)],
            "p4": [180 + (index % 40) for index in range(n)],
            "p5": [3000 + (index % 50) * 25 for index in range(n)],
            "p6": [flags[index % 2] for index in range(n)],
            "p7": [2007 + (index % 3) for index in range(n)],
        }
    )
    original = frame.copy(deep=True)
    analysis = analyze_dataframe(frame)
    pd.testing.assert_frame_equal(frame, original)
    selected = [column.inferred.selected_type for column in analysis.columns]
    assert selected == [
        SemanticType.CATEGORICAL,
        SemanticType.CATEGORICAL,
        SemanticType.NUMERIC,
        SemanticType.NUMERIC,
        SemanticType.NUMERIC,
        SemanticType.NUMERIC,
        SemanticType.CATEGORICAL,
        SemanticType.NUMERIC,
    ]
    summary = analysis.relationship_analysis
    assert summary.n_supported_pairs == 28
    assert summary.n_ineligible_pairs == 0
    assert summary.n_unimplemented_family_pairs == 0
