"""Stage 5: retrieval prompts taken from extracted paper text. No LLM is called."""
import re

_PLACEHOLDER = "The local parser found no abstract"


def _short_answer(value: str, limit: int = 420) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if not value:
        return ""
    if len(value) <= limit:
        return value
    clipped = value[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{clipped}…"


def _pick_section(sections: list[dict], keywords: tuple[str, ...]) -> dict | None:
    for section in sections:
        title = (section.get("title") or "").lower()
        if any(keyword in title for keyword in keywords):
            return section
    return None


def _card(question: str, answer: str, tag: str, section: dict | None, origin: str, explanation: str, page=None, section_name: str = "") -> dict:
    source_section = section_name or (section or {}).get("title") or ""
    source_page = page if page is not None else (section or {}).get("page")
    return {
        "question": question,
        "answer": answer,
        "tag": tag,
        "origin": origin,
        "explanation": explanation,
        "source_section": source_section,
        "source_page": "" if source_page in (None, "") else str(source_page),
    }


def make_study_cards(
    paper_title: str,
    summary: str,
    headings: list[str],
    sections: list[dict] | None = None,
    equations: list[dict] | None = None,
) -> dict:
    sections = sections or []
    equations = equations or []
    flashcards: list[dict] = []
    summary = (summary or "").strip()
    abstract = _pick_section(sections, ("abstract",))
    if summary and not summary.startswith(_PLACEHOLDER) and len(summary) > 40:
        flashcards.append(_card(
            f"What does {paper_title} claim in its opening text?",
            _short_answer(summary),
            "abstract",
            abstract,
            "extracted",
            "Shortened from the extracted abstract or opening text. This is not a separate critique of the paper.",
            section_name=(abstract or {}).get("title") or "Opening text",
        ))
    method = _pick_section(sections, ("method", "approach", "model", "architecture"))
    if method and (method.get("explanation") or method.get("content")):
        flashcards.append(_card(
            f"What does the section “{method['title']}” describe?",
            _short_answer(method.get("explanation") or method.get("content") or ""),
            "method",
            method,
            "extracted",
            "Shortened from the extracted section. It is not an independent explanation written beyond that text.",
        ))
    results = _pick_section(sections, ("result", "experiment", "evaluation"))
    if results and (results.get("explanation") or results.get("content")):
        flashcards.append(_card(
            f"What does “{results['title']}” report?",
            _short_answer(results.get("explanation") or results.get("content") or ""),
            "results",
            results,
            "extracted",
            "Shortened from the extracted section.",
        ))
    if equations:
        first = equations[0]
        reading = first.get("plain_explanation") or "The equation was extracted, but a plain-language explanation is not available."
        flashcards.append(_card(
            f"What does the extracted equation in {first.get('section_name') or 'the paper'} express?",
            _short_answer(reading),
            "equations",
            None,
            "generated",
            "The question was built from an extracted equation. The answer is this pipeline's reading of that equation, not a new derivation.",
            page=first.get("page"),
            section_name=first.get("section_name") or "",
        ))
    if not flashcards and headings:
        flashcards.append(_card(
            f"Which sections were extracted from {paper_title}?",
            _short_answer(", ".join(headings[:8])),
            "outline",
            sections[0] if sections else None,
            "extracted",
            "The answer lists extracted headings only. Body text was not available for a more specific question.",
        ))

    viva = []
    for section in (item for item in (method, results, abstract) if item and (item.get("explanation") or item.get("content"))):
        viva.append({
            "question": f"Which details in “{section['title']}” would you use to restate that section?",
            "answer_hint": _short_answer(section.get("explanation") or section.get("content") or "", 320),
            "key_concept": section["title"],
            "source_section": section["title"],
            "source_page": "" if section.get("page") in (None, "") else str(section.get("page")),
            "origin": "extracted",
        })
    return {"flashcards": flashcards[:6], "viva_questions": viva[:4]}
