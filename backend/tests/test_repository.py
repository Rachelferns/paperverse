"""Unit tests for the SQLite Repository (storage layer)."""
import json
import pytest


@pytest.fixture
def repo(tmp_data_dir):
    """Fresh Repository backed by a temp directory."""
    # Import after env is patched so get_settings sees the tmp dir
    from paperverse.storage.repository import Repository
    return Repository()


def make_ids():
    from uuid import uuid4
    return str(uuid4()), str(uuid4())


# ---------------------------------------------------------------------------
# Paper + job lifecycle
# ---------------------------------------------------------------------------

def test_create_and_get_job(repo):
    paper_id, job_id = make_ids()
    repo.create_paper_job(paper_id, job_id, "Test Paper", "test.pdf", None)
    job = repo.get_job(job_id)
    assert job is not None
    assert job["id"] == job_id
    assert job["paper_id"] == paper_id
    assert job["status"] == "queued"
    assert job["progress"] == 0


def test_update_job_status(repo):
    paper_id, job_id = make_ids()
    repo.create_paper_job(paper_id, job_id, "Test Paper", "test.pdf", None)
    repo.update_job(job_id, "processing", "ingestion", 15)
    job = repo.get_job(job_id)
    assert job["status"] == "processing"
    assert job["stage"] == "ingestion"
    assert job["progress"] == 15


def test_update_job_to_completed_updates_paper_status(repo):
    paper_id, job_id = make_ids()
    repo.create_paper_job(paper_id, job_id, "Test Paper", "test.pdf", None)
    repo.update_job(job_id, "completed", "complete", 100)
    job = repo.get_job(job_id)
    assert job["status"] == "completed"


def test_update_job_to_failed_sets_error(repo):
    paper_id, job_id = make_ids()
    repo.create_paper_job(paper_id, job_id, "Test Paper", "test.pdf", None)
    repo.update_job(job_id, "failed", "failed", 100, "Something went wrong")
    job = repo.get_job(job_id)
    assert job["status"] == "failed"
    assert job["error"] == "Something went wrong"


def test_get_job_nonexistent_returns_none(repo):
    assert repo.get_job("00000000-0000-0000-0000-000000000000") is None


# ---------------------------------------------------------------------------
# get_recent_job
# ---------------------------------------------------------------------------

def test_get_recent_job_returns_most_recent(repo):
    p1, j1 = make_ids()
    p2, j2 = make_ids()
    repo.create_paper_job(p1, j1, "Paper One", "one.pdf", None)
    repo.create_paper_job(p2, j2, "Paper Two", "two.pdf", None)
    recent = repo.get_recent_job()
    assert recent is not None
    assert recent["paper_id"] == p2


def test_get_recent_job_empty_db_returns_none(repo):
    assert repo.get_recent_job() is None


# ---------------------------------------------------------------------------
# save_analysis + get_paper round-trip
# ---------------------------------------------------------------------------

def _sample_artifacts():
    return {
        "diagram_mermaid": "flowchart TD\n  A --> B",
        "python_code": "print('hello')",
        "flashcards": [{"question": "Q?", "answer": "A.", "tag": "test"}],
        "viva_questions": [{"question": "Why?", "answer_hint": "Because.", "key_concept": "test"}],
        "video_composition_props": {"equation_id": "Eq_1", "title": "Test", "steps": [], "fps": 30},
        "video_mp4_url": None,
    }


def _sample_equations():
    return [{
        "equation_id": "Eq_1",
        "original_latex": r"y = mx + b",
        "official_latex": r"y = mx + b",
        "section_name": "Section 1",
        "paper_section": "Section 1",
        "conceptual_summary": "A line.",
        "step_by_step_derivation": [],
        "steps": [],
        "sympy_verification_script": "",
        "verification_note": "No verification.",
        "symbol_glossary": [],
        "symbol_dependencies": [],
        "dependencies": [],
    }]


def _sample_symbols():
    return [{"symbol": "m", "definition": "slope", "dimensions": "Scalar", "kind": "Scalar", "color": "amber"}]


def test_save_and_get_paper_round_trip(repo):
    paper_id, job_id = make_ids()
    repo.create_paper_job(paper_id, job_id, "Original", "test.pdf", None)
    repo.save_analysis(
        paper_id, "Updated Title", "# markdown", "Abstract text.",
        [{"id": "section-1", "title": "Intro", "page": 1, "content": "Text.", "explanation": "Explanation."}],
        _sample_equations(), _sample_symbols(), _sample_artifacts()
    )
    result = repo.get_paper(paper_id)
    assert result is not None
    assert result["paper"]["title"] == "Updated Title"
    assert result["paper"]["summary"] == "Abstract text."
    assert len(result["paper"]["sections"]) == 1
    assert result["paper"]["sections"][0]["title"] == "Intro"
    assert len(result["equations"]) == 1
    assert result["equations"][0]["equation_id"] == "Eq_1"
    assert len(result["symbols"]) == 1
    assert result["symbols"][0]["symbol"] == "m"
    artifacts = result["artifacts"]
    assert artifacts is not None
    assert artifacts["diagram_mermaid"] == "flowchart TD\n  A --> B"
    assert artifacts["python_code"] == "print('hello')"
    assert len(artifacts["flashcards"]) == 1
    assert artifacts["flashcards"][0]["question"] == "Q?"


def test_get_paper_nonexistent_returns_none(repo):
    assert repo.get_paper("00000000-0000-0000-0000-000000000000") is None


def test_save_analysis_idempotent(repo):
    """Calling save_analysis twice should not produce duplicate rows."""
    paper_id, job_id = make_ids()
    repo.create_paper_job(paper_id, job_id, "Paper", "test.pdf", None)
    for _ in range(2):
        repo.save_analysis(
            paper_id, "Paper", "# md", "Summary.",
            [], _sample_equations(), _sample_symbols(), _sample_artifacts()
        )
    result = repo.get_paper(paper_id)
    assert len(result["equations"]) == 1  # not doubled
    assert len(result["symbols"]) == 1
