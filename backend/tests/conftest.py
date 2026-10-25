"""Shared pytest fixtures and helpers for the PaperVerse test suite."""
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Point PAPERVERSE_DATA_DIR at a temp directory for each test."""
    monkeypatch.setenv("PAPERVERSE_DATA_DIR", str(tmp_path))
    # Reset the lru_cache so Settings picks up the new env var
    from paperverse import config as cfg
    cfg.get_settings.cache_clear()
    yield tmp_path
    cfg.get_settings.cache_clear()


@pytest.fixture
def minimal_pdf(tmp_path) -> Path:
    """Return a tiny but valid selectable-text PDF."""
    try:
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            "Test Paper Title\n\nAbstract\nThis is the abstract.\n\n"
            "1. Introduction\nSome introduction text.\n\n"
            "2. Methods\nAttention(Q, K, V) = softmax(QK^T / sqrt(d_k))V",
            fontsize=11,
        )
        out = tmp_path / "test.pdf"
        doc.save(str(out))
        doc.close()
        return out
    except ImportError:
        pytest.skip("PyMuPDF not installed")
