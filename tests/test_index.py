from renova_core.index import DimensionScore, RenovaAssessment, calculate_irg, classify_irg, strengths_and_risks


def test_calculate_irg_uses_default_weights():
    assessment = RenovaAssessment(
        subject="demo",
        dimensions={
            "habitat": DimensionScore("habitat", 80),
            "repair": DimensionScore("repair", 60),
            "horizon": DimensionScore("horizon", 70),
            "sensitivity": DimensionScore("sensitivity", 90),
            "equilibrium": DimensionScore("equilibrium", 50),
        },
    )
    assert calculate_irg(assessment) == 71.0
    assert classify_irg(71.0) == "renovacion activa"


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
    assert buckets["strengths"] == ["habitat"]
    assert buckets["watchlist"] == ["horizon"]
    assert buckets["risks"] == ["repair"]
