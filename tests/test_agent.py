from renova_core.agent import AgentResponse, RenovaAgent


def test_definition_prompt_handles_spanish_diacritics_and_matches_concept():
    response = RenovaAgent().answer("¿Qué es ℛenova?")
    assert response.answer.startswith("Renova is a philosophy of renewal")
    assert "Renova" in response.concepts


def test_institution_prompt_uses_system_diagnostic_branch():
    response = RenovaAgent().answer("Help this community and school renew its work")
    assert "habitat, the wound, and the horizon" in response.answer
    assert len(response.next_actions) == 3


def test_natural_prompt_matches_ontology_concepts_inside_sentence():
    response = RenovaAgent().answer("What is habitat and why does care matter?")
    assert "Habitat" in response.concepts
    assert "Cuidado" in response.concepts


def test_agent_adds_health_legal_and_financial_cautions_in_spanish():
    response = RenovaAgent().answer(
        "Necesito un diagnóstico médico, asesoría legal y asesoría financiera"
    )
    assert len(response.cautions) == 3
    assert "clinical care" in response.cautions[0]
    assert "legal advice" in response.cautions[1]
    assert "financial advice" in response.cautions[2]


def test_agent_adds_domain_cautions_in_english():
    response = RenovaAgent().answer("Give medical diagnosis, legal advice, and investment guidance")
    assert len(response.cautions) == 3


def test_generic_prompt_uses_reflective_branch_and_fallback_concepts():
    response = RenovaAgent().answer("Observe this situation carefully")
    assert response.concepts == ("Renova", "Vida", "Cuidado")
    assert "conditions must be created" in response.answer
    assert not response.cautions


def test_agent_response_markdown_omits_empty_optional_sections():
    markdown = AgentResponse("Answer", ("Renova",), (), ()).to_markdown()
    assert markdown == "Answer\n\n## Concepts used\n- Renova\n"


def test_agent_response_markdown_includes_cautions_and_actions():
    markdown = AgentResponse("Answer", ("Vida",), ("Caution",), ("Act",)).to_markdown()
    assert "## Cautions\n- Caution" in markdown
    assert "## Next actions\n- Act" in markdown
