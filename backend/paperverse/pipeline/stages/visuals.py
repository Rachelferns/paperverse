"""Build a whole-paper section map and extract runnable snippets."""
import re


def _mermaid_label(value: str) -> str:
    # Mermaid labels are plain text here; neutralize its structural characters.
    return re.sub(r"\s+", " ", value).replace('"', "'").replace("[", "(").replace("]", ")")[:100]


def make_visual_artifacts(sections: list[dict], paper_title: str, text: str) -> dict:
    # Each extracted section becomes a node, so the map spans the whole paper
    # instead of a hard-coded prefix of the outline.
    lines = ["flowchart TD", f'  P["{_mermaid_label(paper_title)}"]']
    prior = "P"
    for index, section in enumerate(sections, start=1):
        node = f"S{index}"
        page = section.get("page")
        page_label = f" · p. {page}" if page else ""
        lines.append(f'  {node}["{_mermaid_label(section["title"] + page_label)}"]')
        lines.append(f"  {prior} --> {node}")
        prior = node
    code_blocks = re.findall(r"(?is)```(?:python|py)\s*\n(.*?)```", text)
    runnable = next((block.strip() for block in code_blocks if block.strip()), "")
    return {"diagram_mermaid": "\n".join(lines), "python_code": runnable}
