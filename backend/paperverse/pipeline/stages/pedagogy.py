"""Stage 5: deterministic retrieval prompts from extracted paper text and outline."""
import re


def _short_answer(value: str, limit: int = 150) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    first_sentence = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", value, maxsplit=1)[0]
    answer = first_sentence or value
    if len(answer) > limit:
        answer = answer[:limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return answer


def make_study_cards(paper_title: str, summary: str, headings: list[str]) -> dict:
    summary = summary or "The local parser found no abstract text. Review the extracted source PDF for the paper's claims."
    section = next((heading for heading in headings if any(word in heading.lower() for word in ("method", "approach", "experiment", "result"))), "the paper's main sections")
    return {
        "flashcards": [
            {"question": "What is the paper’s central claim?", "answer": _short_answer(summary), "tag": "local-extraction"},
            {"question": "Where should you look for the method or evidence?", "answer": _short_answer(section, 120), "tag": "paper-structure"},
        ],
        "viva_questions": [
            {"question": f"What evidence in {section} supports the paper's main claim?", "answer_hint": "Refer to the extracted paper sections and results; no model-generated answer is configured.", "key_concept": section},
        ],
        "generation_note": "Recall prompts use extracted text and section headings. No LLM provider is configured.",
    }
