import json

import pytest

from renova_core.corpus import load_glossary, load_json, search_glossary


def write_json(tmp_path, payload):
    path = tmp_path / "glossary.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_json_and_glossary(tmp_path):
    payload = {
        "terms": [
            {"term": "Renovación", "definition": "Reapertura disciplinada de la vida."},
            {"term": "Cuidado", "definition": "Atención práctica a la vida frágil."},
        ]
    }
    path = write_json(tmp_path, payload)
    assert load_json(path) == payload
    glossary = load_glossary(path)
    assert glossary["Renovación"].startswith("Reapertura")
    assert search_glossary(glossary, "renovacion") == {
        "Renovación": "Reapertura disciplinada de la vida."
    }
    assert "Cuidado" in search_glossary(glossary, "fragil")
    assert search_glossary(glossary, "  ") == {}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "terms"),
        ({}, "terms"),
        ({"terms": ["bad"]}, "entry 0"),
        ({"terms": [{"term": "", "definition": "value"}]}, "invalid term"),
        ({"terms": [{"term": "Renova", "definition": ""}]}, "invalid definition"),
        (
            {
                "terms": [
                    {"term": "Renovación", "definition": "one"},
                    {"term": "renovacion", "definition": "two"},
                ]
            },
            "Duplicate",
        ),
    ],
)
def test_load_glossary_validates_schema_and_duplicates(tmp_path, payload, message):
    with pytest.raises(ValueError, match=message):
        load_glossary(write_json(tmp_path, payload))
