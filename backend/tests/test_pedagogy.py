import json

from paperverse.pipeline.stages.pedagogy import make_study_cards


def test_cards_follow_the_selected_paper_and_name_a_source():
    cards = make_study_cards(
        "Widget Routing",
        "We show that routing widgets to the nearest cache reduces lookup error on the public benchmark.",
        ["Abstract", "Method"],
        sections=[
            {"title": "Abstract", "page": 1, "explanation": "Routing widgets to the nearest cache reduces lookup error.", "content": "Routing widgets."},
            {"title": "Method", "page": 3, "explanation": "The method builds a cache key from the widget type and the query city.", "content": "The method builds a cache key."},
        ],
        equations=[],
    )
    payload = json.dumps(cards).lower()
    assert "attention is all you need" not in payload
    assert "self-attention" not in payload
    assert cards["flashcards"]
    assert any(card["source_section"] == "Method" and card["source_page"] == "3" for card in cards["flashcards"])
    assert all(card["answer"] for card in cards["flashcards"])
    assert all(card["origin"] in {"extracted", "generated"} for card in cards["flashcards"])


def test_insufficient_text_produces_no_cards():
    cards = make_study_cards("Untitled", "", [], sections=[], equations=[])
    assert cards["flashcards"] == []
    assert cards["viva_questions"] == []
