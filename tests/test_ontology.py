import pytest

from renova_core.ontology import (
    Concept,
    OntologyGraph,
    Relation,
    default_graph,
    normalize_text,
)


def test_normalize_text_handles_diacritics_symbols_and_spacing():
    assert normalize_text("  ¿Qué es ℛenovación? ") == "que es renovacion"


def test_search_matches_direct_queries_and_concepts_inside_prompts():
    graph = default_graph()
    assert graph.search("") == []
    assert graph.search("renew")[0].identifier == "renova"
    identifiers = {concept.identifier for concept in graph.search("What is habitat and care?")}
    assert {"habitat", "care"} <= identifiers


def test_neighbors_and_json_serialization():
    graph = default_graph()
    assert graph.neighbors("renova")
    payload = graph.to_json_dict()
    assert len(payload["nodes"]) == len(graph.concepts)
    assert len(payload["edges"]) == len(graph.relations)
    assert {"id", "label", "definition", "domain"} == set(payload["nodes"][0])
    with pytest.raises(KeyError):
        graph.neighbors("missing")


def test_graph_rejects_duplicate_concept_identifiers():
    concept = Concept("same", "One", "Definition", "test")
    duplicate = Concept("same", "Two", "Definition", "test")
    with pytest.raises(ValueError, match="unique"):
        OntologyGraph([concept, duplicate], [])


def test_graph_rejects_relations_to_missing_concepts():
    concept = Concept("known", "Known", "Definition", "test")
    with pytest.raises(ValueError, match="unknown concepts"):
        OntologyGraph([concept], [Relation("known", "missing", "points_to")])
