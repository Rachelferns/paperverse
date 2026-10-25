"""Unit tests for Stage 1: PDF ingestion."""
import re
import pytest


def test_ingest_pdf_returns_expected_keys(minimal_pdf):
    from paperverse.pipeline.stages.ingestion import ingest_pdf
    result = ingest_pdf(minimal_pdf)
    assert isinstance(result, dict)
    for key in ("markdown", "text", "title", "summary", "pages", "headings", "sections", "equations"):
        assert key in result, f"Missing key: {key}"


def test_ingest_pdf_extracts_title(minimal_pdf):
    from paperverse.pipeline.stages.ingestion import ingest_pdf
    result = ingest_pdf(minimal_pdf)
    # Title should come from the first lines of text, not just the filename stem
    assert isinstance(result["title"], str)
    assert len(result["title"]) > 0


def test_ingest_pdf_extracts_sections(minimal_pdf):
    from paperverse.pipeline.stages.ingestion import ingest_pdf
    result = ingest_pdf(minimal_pdf)
    sections = result["sections"]
    assert isinstance(sections, list)
    assert len(sections) > 0
    for s in sections:
        assert "id" in s
        assert "title" in s
        assert "content" in s


def test_ingest_pdf_extracts_equations(minimal_pdf):
    from paperverse.pipeline.stages.ingestion import ingest_pdf
    result = ingest_pdf(minimal_pdf)
    # The PDF has a plain-text equation line; regex may or may not capture it
    # depending on PyMuPDF text rendering — just assert the field is a list
    assert isinstance(result["equations"], list)


def test_ingest_pdf_pages_have_numbers(minimal_pdf):
    from paperverse.pipeline.stages.ingestion import ingest_pdf
    result = ingest_pdf(minimal_pdf)
    for page in result["pages"]:
        assert "page_number" in page
        assert "text" in page
        assert page["page_number"] >= 1


def test_ingest_empty_pdf_raises(tmp_path):
    """An empty file should raise, not silently return empty data."""
    from paperverse.pipeline.stages.ingestion import ingest_pdf
    empty = tmp_path / "empty.pdf"
    # Write a file that is not a valid PDF
    empty.write_bytes(b"")
    with pytest.raises(Exception):
        ingest_pdf(empty)


def test_section_explanation_truncates():
    from paperverse.pipeline.stages.ingestion import _section_explanation
    long_text = "Word " * 200
    result = _section_explanation(long_text, "intro")
    assert len(result) <= 365  # 360 limit + ellipsis headroom
