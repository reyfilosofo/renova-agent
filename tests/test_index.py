import math

import pytest

from renova_core.index import (
    DEFAULT_WEIGHTS,
    DimensionScore,
    RenovaAssessment,
    assessment_report,
    calculate_irg,
    classify_irg,
    dimension_average,
    recommendation_for_dimension,
    strengths_and_risks,
)


def standard_assessment() -> RenovaAssessment:
    return RenovaAssessment(
        subject="demo",
        dimensions={
            "habitat": DimensionScore("habitat", 80, "habitat evidence"),
            "repair": DimensionScore("repair", 60, "repair evidence"),
            "horizon": DimensionScore("horizon", 70, "horizon evidence"),
            "sensitivity": DimensionScore("sensitivity", 90, "sensitivity evidence"),
            "equilibrium": DimensionScore("equilibrium", 50, "equilibrium evidence"),
        },
        notes="Reviewed with participants.",
    )


def test_calculate_irg_uses_default_weights():
    assessment = standard_assessment()
    assert assessment.normalized_weights() == DEFAULT_WEIGHTS
    assert calculate_irg(assessment) == 71.0
    assert classify_irg(71.0) == "renovacion activa"


@pytest.mark.parametrize("value", [-1, 101, math.inf, -math.inf, math.nan])
def test_dimension_score_rejects_out_of_range_or_non_finite_values(value):
    with pytest.raises(ValueError):
        DimensionScore("habitat", value)


@pytest.mark.parametrize("value", [True, "50", None])
def test_dimension_score_rejects_non_numeric_values(value):
    with pytest.raises(TypeError):
        DimensionScore("habitat", value)


def test_dimension_score_validates_name_and_evidence():
    with pytest.raises(ValueError, match="name"):
        DimensionScore("", 50)
    with pytest.raises(TypeError, match="Evidence"):
        DimensionScore("habitat", 50, evidence=None)


def test_assessment_validates_structure():
    with pytest.raises(ValueError, match="subject"):
        RenovaAssessment("", {"habitat": DimensionScore("habitat", 50)})
    with pytest.raises(ValueError, match="at least one"):
        RenovaAssessment("demo", {})
    with pytest.raises(TypeError, match="notes"):
        RenovaAssessment(
            "demo",
            {"habitat": DimensionScore("habitat", 50)},
            weights={"habitat": 1},
            notes=None,
        )
    with pytest.raises(ValueError, match="does not match"):
        RenovaAssessment(
            "demo",
            {"habitat": DimensionScore("repair", 50)},
            weights={"habitat": 1},
        )
    with pytest.raises(TypeError, match="DimensionScore"):
        RenovaAssessment("demo", {"habitat": 50}, weights={"habitat": 1})
    with pytest.raises(TypeError, match="dimensions must be a mapping"):
        RenovaAssessment("demo", [DimensionScore("habitat", 50)], weights={"habitat": 1})
    with pytest.raises(TypeError, match="weights must be a mapping"):
        RenovaAssessment(
            "demo",
            {"habitat": DimensionScore("habitat", 50)},
            weights=[("habitat", 1)],
        )


def test_partial_assessment_requires_explicit_exact_weights():
    implicit = RenovaAssessment("partial", {"habitat": DimensionScore("habitat", 100)})
    with pytest.raises(ValueError, match="Partial assessments"):
        calculate_irg(implicit)

    explicit = RenovaAssessment(
        "partial",
        {"habitat": DimensionScore("habitat", 100)},
        weights={"habitat": 1},
    )
    assert calculate_irg(explicit) == 100.0
    assert "custom assessment (1 dimensions)" in assessment_report(explicit)


def test_full_assessment_with_custom_weights_is_labeled_custom():
    standard = standard_assessment()
    custom = RenovaAssessment(
        standard.subject,
        standard.dimensions,
        weights={name: 1 for name in standard.dimensions},
    )
    assert "custom assessment (5 dimensions)" in assessment_report(custom)


def test_weights_must_match_dimensions():
    dimension = {"habitat": DimensionScore("habitat", 50)}
    with pytest.raises(ValueError, match="Missing weights"):
        RenovaAssessment("demo", dimension, weights={}).normalized_weights()
    with pytest.raises(ValueError, match="unknown dimensions"):
        RenovaAssessment(
            "demo", dimension, weights={"habitat": 1, "repair": 1}
        ).normalized_weights()


@pytest.mark.parametrize("weight", [-1, math.inf, -math.inf, math.nan])
def test_weights_reject_negative_or_non_finite_values(weight):
    assessment = RenovaAssessment(
        "demo",
        {"habitat": DimensionScore("habitat", 100)},
        weights={"habitat": weight},
    )
    with pytest.raises(ValueError, match="finite and non-negative"):
        calculate_irg(assessment)


@pytest.mark.parametrize("weight", [True, "1", None])
def test_weights_reject_non_numeric_values(weight):
    assessment = RenovaAssessment(
        "demo",
        {"habitat": DimensionScore("habitat", 100)},
        weights={"habitat": weight},
    )
    with pytest.raises(TypeError, match="must be numeric"):
        calculate_irg(assessment)


def test_weights_require_a_positive_value_and_keep_irg_bounded():
    dimensions = {
        "a": DimensionScore("a", 0),
        "b": DimensionScore("b", 100),
    }
    with pytest.raises(ValueError, match="positive"):
        calculate_irg(RenovaAssessment("demo", dimensions, weights={"a": 0, "b": 0}))

    score = calculate_irg(RenovaAssessment("demo", dimensions, weights={"a": 1, "b": 3}))
    assert score == 75.0
    assert 0 <= score <= 100


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, "renovacion excelente"),
        (85, "renovacion excelente"),
        (70, "renovacion activa"),
        (55, "renovacion vulnerable"),
        (40, "renovacion critica"),
        (0, "renovacion bloqueada"),
    ],
)
def test_classify_irg_thresholds(score, expected):
    assert classify_irg(score) == expected


@pytest.mark.parametrize("score", [-1, 101, math.nan, math.inf])
def test_classify_irg_rejects_invalid_range(score):
    with pytest.raises(ValueError):
        classify_irg(score)


def test_classify_irg_rejects_non_numeric_value():
    with pytest.raises(TypeError):
        classify_irg("70")


def test_dimension_average_validates_items():
    assert dimension_average([0, 50, 100]) == 50.0
    with pytest.raises(ValueError, match="At least one"):
        dimension_average([])
    with pytest.raises(ValueError, match="between 0 and 100"):
        dimension_average([101])
    with pytest.raises(TypeError, match="numeric"):
        dimension_average([True])


def test_strengths_and_risks():
    assessment = RenovaAssessment(
        subject="demo",
        dimensions={
            "habitat": DimensionScore("habitat", 80),
            "repair": DimensionScore("repair", 45),
            "horizon": DimensionScore("horizon", 60),
        },
        weights={"habitat": 1, "repair": 1, "horizon": 1},
    )
    buckets = strengths_and_risks(assessment)
    assert buckets == {
        "strengths": ["habitat"],
        "watchlist": ["horizon"],
        "risks": ["repair"],
    }


@pytest.mark.parametrize("name", ["habitat", "repair", "horizon", "sensitivity", "equilibrium"])
def test_recommendations_cover_low_and_healthy_scores(name):
    assert recommendation_for_dimension(name, 20)
    assert recommendation_for_dimension(name, 80)


def test_unknown_dimension_has_generic_recommendation():
    assert recommendation_for_dimension("other", 50) == (
        "Define one concrete action for this dimension."
    )


def test_assessment_report_contains_evidence_buckets_actions_and_notes():
    report = assessment_report(standard_assessment())
    assert "# Renova Assessment: demo" in report
    assert "IRG: **71.0/100**" in report
    assert "habitat evidence" in report
    assert "Strengths: habitat, sensitivity" in report
    assert "## Recommended next actions" in report
    assert "Reviewed with participants." in report
    assert report.endswith("\n")
