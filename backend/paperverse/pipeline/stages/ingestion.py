"""Extract full-paper text and section boundaries from a selectable-text PDF."""
import re
import statistics
from pathlib import Path


def _clean_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().strip(".•")


def _section_explanation(content: str, title: str) -> str:
    body = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", content)
    body = re.sub(r"\s+", " ", body).strip()
    if body.casefold().startswith(title.casefold()):
        body = body[len(title):].lstrip(" .:—–-")
    body = re.sub(r"\[[0-9,; –-]+\]", "", body)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", body)
    explanation = " ".join(sentence.strip() for sentence in sentences[:2] if sentence.strip())
    if not explanation:
        explanation = body
    if len(explanation) > 360:
        explanation = explanation[:357].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return explanation or "The parser found this section heading but no readable body text."


def _sections_from_pdf(document, pages: list[dict], full_text: str) -> list[dict]:
    """Prefer the PDF outline, then use typographic headings across every page."""
    candidates: list[tuple[int, str]] = []
    toc = document.get_toc(simple=True) or []
    if toc:
        for _level, title, page_no in toc:
            if 1 <= page_no <= len(pages) and _clean_heading(title):
                candidates.append((page_no, _clean_heading(title)))

    if not candidates:
        font_sizes: list[float] = []
        page_lines: list[tuple[int, str, float, bool]] = []
        for page_no, page in enumerate(document, start=1):
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    text = _clean_heading("".join(span.get("text", "") for span in spans))
                    if not text:
                        continue
                    sizes = [float(span.get("size", 0)) for span in spans]
                    font_sizes.extend(sizes)
                    bold = any(int(span.get("flags", 0)) & 16 for span in spans)
                    page_lines.append((page_no, text, max(sizes, default=0), bold))
        body_size = statistics.median(font_sizes) if font_sizes else 10.0
        seen: set[tuple[int, str]] = set()
        references_page = None
        references_offset = None
        for page_no, page in enumerate(pages, start=1):
            reference_match = re.search(r"(?im)^\s*references\s*$", page["text"])
            if reference_match:
                references_page = page_no
                references_offset = reference_match.start()
                candidates.append((page_no, "References"))
                break
        for page_no, text, size, bold in page_lines:
            numbered = bool(re.match(r"^(?:\d+(?:\.\d+)*\.?\s+|[A-Z]\.\s+|[IVX]{1,5}\.\s+)[A-Z]", text))
            short_heading = len(text) <= 115 and not re.search(r"[.!?]$", text)
            title_case = sum(char.isupper() for char in text) >= 2
            typographic = size >= body_size * 1.16 or (bold and size >= body_size * 1.04)
            abstract_start = re.search(r"(?i)\babstract\b", pages[0]["text"])
            if page_no == 1 and abstract_start and text.casefold() != "abstract" and page_lines:
                page_text = pages[0]["text"]
                candidate_position = page_text.casefold().find(text.casefold())
                if 0 <= candidate_position < abstract_start.start():
                    continue
            if references_page is not None and page_no >= references_page:
                page_text = pages[page_no - 1]["text"]
                candidate_position = page_text.find(text)
                if page_no > references_page or (candidate_position >= 0 and candidate_position >= references_offset):
                    continue
            if short_heading and (numbered or (typographic and title_case)):
                key = (page_no, text.casefold())
                if key not in seen:
                    candidates.append((page_no, text))
                    seen.add(key)

        abstract = re.search(r"(?im)^\s*abstract\b", pages[0]["text"])
        if abstract:
            candidates.insert(0, (1, "Abstract"))

    # Resolve candidates to exact positions in the original text. This keeps
    # section bodies complete and makes outline selection deterministic.
    page_offsets: dict[int, int] = {}
    offset = 0
    for page in pages:
        page_offsets[page["page_number"]] = offset
        offset += len(page["text"]) + 2
    located: list[tuple[int, str, int]] = []
    for page_no, title in candidates:
        page_text = pages[page_no - 1]["text"]
        page_start = page_offsets[page_no]
        page_end = page_start + len(page_text)
        escaped = re.escape(title).replace(r"\ ", r"\s+")
        match = re.search(escaped, full_text[page_start:page_end], re.I)
        if not match:
            # PDF bookmarks may have slightly different whitespace/punctuation.
            normalized = re.sub(r"[^a-z0-9]+", "", title.casefold())
            for line in page_text.splitlines():
                if re.sub(r"[^a-z0-9]+", "", line.casefold()) == normalized:
                    match = re.search(re.escape(line.strip()), full_text[page_start:page_end], re.I)
                    if match:
                        break
        if match:
            start = page_start + match.start()
            located.append((start, title, page_no))

    # De-duplicate nearby headings and keep the page's original order.
    located.sort(key=lambda item: item[0])
    unique: list[tuple[int, str, int]] = []
    for item in located:
        if unique and (item[0] == unique[-1][0] or item[1].casefold() == unique[-1][1].casefold()):
            continue
        unique.append(item)
    if not unique:
        return [{"id": "full-paper", "title": "Full paper", "page": 1, "content": full_text,
                 "explanation": _section_explanation(full_text, "Full paper")}]

    sections = []
    for index, (start, title, page_no) in enumerate(unique):
        end = unique[index + 1][0] if index + 1 < len(unique) else len(full_text)
        content = full_text[start:end].strip()
        sections.append({"id": f"section-{index + 1}", "title": title, "page": page_no, "content": content,
                         "explanation": _section_explanation(content, title)})
    return sections


def ingest_pdf(path: Path) -> dict:
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PDF extraction requires PyMuPDF. Install backend dependencies.") from exc
    with pymupdf.open(path) as pdf:
        pages = [{"page_number": number, "text": page.get_text("text")} for number, page in enumerate(pdf, start=1)]
        toc_title = next((_clean_heading(item[1]) for item in pdf.get_toc(simple=True) or [] if item[0] == 1), "")
        sections = _sections_from_pdf(pdf, pages, "\n\n".join(page["text"] for page in pages).strip())
    text = "\n\n".join(page["text"] for page in pages).strip()
    if not text:
        raise ValueError("No selectable text was found. OCR is not configured for scanned PDFs yet.")

    title = toc_title or path.stem.replace("_", " ")
    if not toc_title:
        before_abstract = re.split(r"(?i)abstract\s*[—–:-]", text, maxsplit=1)[0]
        title_lines = []
        for line in (item.strip() for item in before_abstract.splitlines()):
            if not line:
                continue
            if re.search(r"\b(department|university|institute|email|@|india)\b", line, re.I):
                break
            if re.search(r"\b(and|et al\.)\b", line) and re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+", line):
                break
            if len(line) > 105:
                break
            title_lines.append(line)
            if len(title_lines) >= 3:
                break
        if title_lines:
            title = re.sub(r"\s+", " ", " ".join(title_lines)).strip()

    llm_markdown = ""
    try:
        import pymupdf4llm
        llm_markdown = pymupdf4llm.to_markdown(str(path))
    except Exception:
        pass

    abstract_match = re.search(r"(?is)abstract\s*[—–:-]?\s*(.+?)(?=index terms|keywords|\n\s*(?:\d+(?:\.\d+)*|[IVX]+|[A-Z])\.\s+[A-Z])", text)
    summary = re.sub(r"\s+", " ", abstract_match.group(1)).strip() if abstract_match else ""
    if not summary:
        paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
        summary = next((p for p in paragraphs if len(p) > 180), "")

    markdown = llm_markdown if len(llm_markdown) > 50 else "\n\n".join(f"<!-- page:{page['page_number']} -->\n{page['text']}" for page in pages)

    # Search for LaTeX / display math equations in both markdown and raw text
    seen_eqs = set()
    latex = []

    def _add_eq(eq_str: str):
        cleaned = re.sub(r"\s+", " ", eq_str).strip()
        if len(cleaned) >= 4 and cleaned not in seen_eqs:
            seen_eqs.add(cleaned)
            latex.append(cleaned)

    # 1. Standard LaTeX delimiters
    for match in re.finditer(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", markdown, flags=re.S):
        _add_eq(match.group(1) or match.group(2))
    for match in re.finditer(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", text, flags=re.S):
        _add_eq(match.group(1) or match.group(2))

    # 2. Inline math containing equality or key mathematical operators
    for match in re.finditer(r"\$([^\$\n]{5,180})\$", markdown):
        val = match.group(1).strip()
        if any(op in val for op in ("=", r"\sum", r"\prod", r"\frac", r"\sqrt", "softmax", r"\mathbb", r"\mathcal", r"\alpha", r"\beta", r"\gamma", r"\lambda")):
            _add_eq(val)

    # 3. Text lines with display equation patterns, e.g. "Attention(Q, K, V) = ... (1)"
    for line in (text + "\n" + markdown).splitlines():
        line = line.strip()
        if re.search(r"(?:Attention|Loss|softmax|\\mathcal\{L\}|argmin|argmax)|=", line, re.I):
            m = re.match(r"^([A-Za-z\\][A-Za-z0-9_\(\)\{\}\\\^\+\-\*\/\s,=]{4,100}\s*=\s*[^;\n]{3,120})(?:\s*\(([0-9]+)\))?$", line)
            if m:
                _add_eq(m.group(1))

    return {"markdown": markdown, "text": text, "title": title, "summary": summary[:1800], "pages": pages,
            "headings": [section["title"] for section in sections], "sections": sections, "equations": latex}
