import pytest

from renova_core.lab import FOUNDATIONAL_PROMPTS, render_canvas


def test_render_canvas_includes_all_prompts_and_action_fields():
    canvas = render_canvas("Community cultural lab")
    for prompt in FOUNDATIONAL_PROMPTS:
        assert f"## {prompt.title} ({prompt.duration_minutes} min)" in canvas
        assert prompt.question in canvas
        assert prompt.output in canvas
    assert "## Minimum viable renovative action" in canvas
    assert "- Evidence of completion:" in canvas


@pytest.mark.parametrize("subject", ["", "   ", None])
def test_render_canvas_requires_subject(subject):
    with pytest.raises((TypeError, ValueError)):
        render_canvas(subject)
