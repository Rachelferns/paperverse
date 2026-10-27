import json

from paperverse.pipeline.stages.video_engine import make_video_props


def test_walkthrough_does_not_claim_an_mp4():
    props = make_video_props({
        "equation_id": "e1",
        "section_name": "Loss",
        "official_latex": r"y = Wx + b",
        "steps": [{
            "latex": r"y = Wx + b",
            "explanation": "Equation as extracted from selectable PDF text.",
            "is_intermediate_derived": False,
            "sympy_verified": False,
        }],
    }, "Widget Paper")
    payload = json.dumps(props).lower()
    assert "mp4" not in payload
    assert props["steps"][0]["audio_url"] is None
    assert "concept walkthrough" in props["title"].lower()
    assert "first step" in props["steps"][0]["narration_text"].lower()
    assert "nothing follows" in props["steps"][0]["narration_text"].lower()


def test_missing_equation_has_no_storyboard_steps():
    props = make_video_props(None, "Empty")
    assert props["steps"] == []
    assert "no equation walkthrough" in props["title"].lower()
