"""Infer a method diagram from methodology prose.

Section headings are a document outline. They are never emitted as architecture nodes.
A diagram is returned only when the methodology text names components. Arrows are added
only for sequences the same text actually states.
"""
import re

ARCHITECTURE_MARKER = "%% paperverse-architecture: inferred"
ARCHITECTURE_UNAVAILABLE = "PAPERVERSE_ARCHITECTURE_UNAVAILABLE"

_SKIP_TITLE = re.compile(
    r"\b(abstract|introduction|background|related|experiment|result|discussion|conclusion|reference|acknowledg|limitation|appendix)\b",
    re.I,
)
_METHOD_TITLE = re.compile(r"\b(methods?|approach|model|architect|framework|proposed|system)\b", re.I)
_COMPONENT_TITLE = re.compile(r"\b(encoder|decoder|attention|embedding|layer|module|block|network)\b", re.I)
_STRUCTURAL = re.compile(
    r"consist|compos|compris|stack|sub-layer|sublayer|employ|insert|followed by|add |comput|perform|maps |produce|layer has|first is|second is",
    re.I,
)
_LIST_INTRO = re.compile(
    r"(?:consists of|composed of|comprises|made up of)\s+([^.]{8,280})",
    re.I,
)

# Phrases have to appear in methodology prose. Matching a phrase never invents it.
_CATALOG = (
    {"id": "embed", "pattern": r"input embeddings?", "label": "Input embeddings", "detail": "Token representations entering the model."},
    {"id": "pos", "pattern": r"positional encodings?", "label": "Positional encoding", "detail": "Order information added to the embeddings."},
    {"id": "encoder", "pattern": r"\bencoder\b", "label": "Encoder", "detail": "Maps an input sequence into continuous representations."},
    {"id": "mha", "pattern": r"multi-head (?:self-)?attention", "label": "Multi-head attention", "detail": "Several attention operations run in parallel."},
    {"id": "self_attn", "pattern": r"self-attention|self attention", "label": "Self-attention", "detail": "Attention over positions in the same sequence."},
    {"id": "sdpa", "pattern": r"scaled dot-product attention", "label": "Scaled dot-product attention", "detail": "Compares queries with keys, scales the scores, applies softmax, and mixes values."},
    {"id": "ffn", "pattern": r"feed-forward(?: network)?|position-wise fully connected", "label": "Feed-forward network", "detail": "Position-wise transformation inside a layer."},
    {"id": "pointwise", "pattern": r"point-?wise fully connected", "label": "Point-wise fully connected layer", "detail": "A fully connected transformation applied at each position."},
    {"id": "residual", "pattern": r"residual connections?", "label": "Residual connection", "detail": "Adds a sub-layer input to its output."},
    {"id": "norm", "pattern": r"layer normali[sz]ation", "label": "Layer normalization", "detail": "Normalizes a residual sub-layer output."},
    {"id": "decoder", "pattern": r"\bdecoder\b", "label": "Decoder", "detail": "Produces an output sequence, attending to the encoder when the text says so."},
)


def unavailable_architecture(reason: str) -> str:
    return f"{ARCHITECTURE_UNAVAILABLE}\n{re.sub(r'\\s+', ' ', reason).strip()}"


def _mermaid_label(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).replace('"', "'").replace("[", "(").replace("]", ")")
    return re.sub(r"[{}|]", "", cleaned)[:80]


def _method_sections(sections: list[dict]) -> list[dict]:
    chosen = []
    for section in sections:
        title = section.get("title") or ""
        if _SKIP_TITLE.search(title) and not _METHOD_TITLE.search(title):
            continue
        if _METHOD_TITLE.search(title) or _COMPONENT_TITLE.search(title):
            if (section.get("content") or section.get("explanation") or "").strip():
                chosen.append(section)
    return chosen


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _supported_components(text: str) -> list[dict]:
    found = []
    for item in _CATALOG:
        pattern = re.compile(item["pattern"], re.I)
        for sentence in _sentences(text):
            if pattern.search(sentence) and _STRUCTURAL.search(sentence):
                found.append(item)
                break
    present = {item["id"] for item in found}
    if "mha" in present:
        found = [item for item in found if item["id"] != "self_attn"]
    if "ffn" in present:
        found = [item for item in found if item["id"] != "pointwise"]
    return found


def _edges(text: str, present: set[str]) -> list[dict]:
    rules = (
        ("embed", "pos", "The text says positional encodings are added to the input embeddings.", r"positional encodings?.{0,80}input embeddings|add positional encodings"),
        ("pos", "encoder", "The text places positional encodings at the encoder.", r"positional encodings?.{0,140}encoder"),
        ("mha", "ffn", "The text orders multi-head attention before the feed-forward sub-layer.", r"first is a multi-head.{0,160}second is"),
        ("self_attn", "pointwise", "The text lists stacked self-attention and then point-wise fully connected layers.", r"stacked self-attention and point-?wise fully connected"),
        ("residual", "norm", "The text says a residual connection is followed by layer normalization.", r"residual connection.{0,120}followed by layer normali"),
        ("encoder", "decoder", "The text says the decoder attends over the encoder output.", r"attention over the output of the encoder"),
        ("mha", "sdpa", "Scaled dot-product attention is the scoring function named with multi-head attention.", r"scaled dot-product attention"),
    )
    edges = []
    seen = set()
    for src, dst, reason, pattern in rules:
        if src in present and dst in present and re.search(pattern, text, re.I):
            key = (src, dst)
            if key not in seen:
                seen.add(key)
                edges.append({"src": src, "dst": dst, "reason": reason})
    return edges


def _list_components(text: str, titles: set[str]) -> tuple[list[dict], bool]:
    match = _LIST_INTRO.search(text)
    if not match:
        return [], False
    chunk = re.sub(r"\([^)]*\)", "", match.group(1))
    parts = re.split(r",| and ", chunk)
    nodes = []
    for part in parts:
        phrase = re.sub(r"^(a|an|the|our)\s+", "", part.strip(), flags=re.I)
        phrase = re.sub(r"\s+", " ", phrase).strip(" .;:")
        if not (3 <= len(phrase) <= 60):
            continue
        if phrase.casefold() in titles:
            continue
        if re.search(r"\b(stack of|identical layers|following|below)\b", phrase, re.I):
            continue
        nodes.append(phrase)
    unique = []
    seen = set()
    for phrase in nodes:
        key = phrase.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(phrase)
    sentence = match.group(0)
    ordered = bool(re.search(r"\bthen\b|followed by|pipeline", sentence, re.I))
    return unique[:8], ordered


def _render(components: list[dict], links: list[dict], note: str) -> str:
    lines = [ARCHITECTURE_MARKER, f"%% note: {_mermaid_label(note)}", "flowchart TD"]
    for component in components:
        lines.append(f"%% component: {component['id']} | {component['label']} | {component['detail']}")
        lines.append(f'  {component["id"]}["{_mermaid_label(component["label"])}"]')
    for link in links:
        lines.append(f"%% link: {link['src']} | {link['dst']} | {_mermaid_label(link['reason'])}")
        lines.append(f"  {link['src']} --> {link['dst']}")
    return "\n".join(lines)


def _python_code(text: str) -> str:
    blocks = re.findall(r"(?is)```(?:python|py)\s*\n(.*?)```", text or "")
    return next((block.strip() for block in blocks if block.strip()), "")


def make_visual_artifacts(sections: list[dict], paper_title: str, text: str) -> dict:
    """Return a method diagram, or an explicit unavailable marker. Never a heading outline."""
    code = _python_code(text)
    method_sections = _method_sections(sections)
    if not method_sections:
        reason = (
            "No methodology, model, or architecture section was found in the extracted outline. "
            "Document headings stay in the outline and were not drawn as a system diagram."
        )
        return {"diagram_mermaid": unavailable_architecture(reason), "python_code": code}

    method_text = "\n".join((section.get("content") or "") for section in method_sections)
    titles = ", ".join(section.get("title") or "Untitled section" for section in method_sections[:4])
    title_keys = {(section.get("title") or "").casefold() for section in sections}
    title_keys.add((paper_title or "").casefold())
    components = _supported_components(method_text)
    links: list[dict] = []
    if len(components) >= 2:
        links = _edges(method_text, {item["id"] for item in components})
        if links:
            note = (
                f"Inferred interpretation of components named in {titles}. "
                "Arrows are limited to sequences stated in that text. This is not a figure copied from the paper."
            )
        else:
            note = (
                f"Components named in {titles}. The extracted text does not state a directed information flow, "
                "so the diagram has no arrows."
            )
    else:
        phrases, ordered = _list_components(method_text, title_keys)
        if len(phrases) >= 2:
            components = [
                {"id": f"n{index}", "label": _mermaid_label(phrase[:1].upper() + phrase[1:]), "detail": "Named together in the methodology text."}
                for index, phrase in enumerate(phrases, start=1)
            ]
            if ordered:
                links = [
                    {"src": components[index - 1]["id"], "dst": components[index]["id"], "reason": "The source lists these parts in this order."}
                    for index in range(1, len(components))
                ]
                note = f"Inferred from a component list in {titles}. Arrows follow that stated order."
            else:
                note = f"Components listed together in {titles}. The text does not state a directed flow, so there are no arrows."
        else:
            reason = (
                f"Methodology text was found ({titles}), but it does not name a connected set of components. "
                "No architecture diagram was inferred."
            )
            return {"diagram_mermaid": unavailable_architecture(reason), "python_code": code}

    if re.search(r"Figure\s+\d+", method_text):
        note += " Figure captions were not turned into extra nodes."
    return {"diagram_mermaid": _render(components, links, note), "python_code": code}
