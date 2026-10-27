from paperverse.pipeline.stages.ingestion import extract_equations, unicode_to_latex


def test_extracts_numbered_display_equation_without_latex_delimiters():
    pages = [{"page_number": 2, "text": "Some context.\nAttention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V\n(1)\nMore text.\n"}]
    sections = [{"title": "Model Architecture", "page": 2, "content": pages[0]["text"]}]
    found = extract_equations(pages, sections, pages[0]["text"])
    latexes = [item["official_latex"] for item in found]
    assert any("Attention" in latex and "=" in latex for latex in latexes)
    hit = next(item for item in found if "Attention" in item["official_latex"])
    assert hit["page"] == 2
    assert hit["section_name"] == "Model Architecture"
    assert hit.get("equation_number") == "1"


def test_extracts_latex_delimiters():
    pages = [{"page_number": 1, "text": r"Intro $$E = mc^2$$ body"}]
    found = extract_equations(pages, [], pages[0]["text"])
    assert any("E = mc^2" in item["official_latex"] for item in found)


def test_does_not_treat_ordinary_prose_as_an_equation():
    pages = [{"page_number": 1, "text": "We show that the method is accurate = better than chance in practice.\n"}]
    found = extract_equations(pages, [], pages[0]["text"])
    assert found == []


def test_unicode_sqrt_becomes_latex():
    assert r"\sqrt{d_k}" in unicode_to_latex("softmax(QK^T / √d_k) V")
