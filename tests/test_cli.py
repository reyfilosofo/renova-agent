import json
import subprocess
import sys

import pytest

from renova_core.cli import load_assessment, main
from renova_core.index import calculate_irg


def write_json(tmp_path, payload, filename="assessment.json"):
    path = tmp_path / filename
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def minimal_payload():
    return {
        "subject": "Custom assessment",
        "dimensions": {
            "habitat": {"value": 100, "evidence": "Observed"},
            "repair": {"value": 0},
        },
        "weights": {"habitat": 0, "repair": 1},
        "notes": "Explicit weights",
    }


def test_load_assessment_honors_custom_weights(tmp_path):
    assessment = load_assessment(write_json(tmp_path, minimal_payload()))
    assert calculate_irg(assessment) == 0.0
    assert assessment.notes == "Explicit weights"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: [], "root"),
        (lambda payload: {**payload, "subject": None}, "subject"),
        (lambda payload: {**payload, "notes": None}, "notes"),
        (lambda payload: {**payload, "dimensions": []}, "dimensions"),
        (
            lambda payload: {**payload, "dimensions": {"habitat": []}},
            "must be an object",
        ),
        (
            lambda payload: {**payload, "dimensions": {"habitat": {}}},
            "missing field 'value'",
        ),
        (
            lambda payload: {
                **payload,
                "dimensions": {"habitat": {"value": True}},
                "weights": {"habitat": 1},
            },
            "must be numeric",
        ),
        (
            lambda payload: {
                **payload,
                "dimensions": {"habitat": {"value": 50, "evidence": None}},
                "weights": {"habitat": 1},
            },
            "Evidence",
        ),
        (lambda payload: {**payload, "weights": []}, "weights"),
        (
            lambda payload: {**payload, "weights": {"habitat": "heavy"}},
            "must be numeric",
        ),
    ],
)
def test_load_assessment_rejects_invalid_schema(tmp_path, mutation, message):
    with pytest.raises(ValueError, match=message):
        load_assessment(write_json(tmp_path, mutation(minimal_payload())))


def test_main_runs_every_subcommand(tmp_path, capsys):
    path = write_json(tmp_path, minimal_payload())

    assert main(["index", str(path)]) == 0
    assert "IRG: **0.0/100**" in capsys.readouterr().out

    assert main(["agent", "What is Renova?"]) == 0
    assert "philosophy of renewal" in capsys.readouterr().out

    assert main(["ontology"]) == 0
    ontology = json.loads(capsys.readouterr().out)
    assert ontology["nodes"] and ontology["edges"]

    assert main(["canvas", "Community lab"]) == 0
    assert "Renova Lab Canvas: Community lab" in capsys.readouterr().out


def test_main_returns_code_two_and_concise_error_for_bad_file(tmp_path, capsys):
    missing = tmp_path / "missing.json"
    assert main(["index", str(missing)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("renova: error:")


def test_main_returns_code_two_for_invalid_json(tmp_path, capsys):
    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")
    assert main(["index", str(path)]) == 2
    assert "renova: error:" in capsys.readouterr().err


def test_python_module_entrypoint_executes_documented_cli():
    result = subprocess.run(
        [sys.executable, "-m", "renova_core.cli", "ontology"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["nodes"]
    assert result.stderr == ""
