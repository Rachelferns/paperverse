from pathlib import Path
from uuid import uuid4
from paperverse.pipeline import orchestrator
from paperverse.storage.repository import Repository


def test_partial_stage_failure_keeps_ingestion(tmp_data_dir, monkeypatch):
    repo = Repository()
    monkeypatch.setattr(orchestrator, "repository", repo)
    paper_id, job_id = str(uuid4()), str(uuid4())
    repo.create_paper_job(paper_id, job_id, "Queued", "paper.pdf", None)

    monkeypatch.setattr(orchestrator, "ingest_pdf", lambda _path: {
        "title": "Kept Title",
        "markdown": "md",
        "summary": "A summary that is long enough to study.",
        "headings": ["Intro"],
        "sections": [{"title": "Intro", "page": 1, "content": "Hello", "explanation": "Hello"}],
        "text": "Hello",
        "equations": [{"official_latex": "a=b", "page": 1, "section_name": "Intro", "source_text": "a=b"}],
    })
    monkeypatch.setattr(orchestrator, "explain_equations", lambda _eqs: (
        [{"equation_id": "e1", "official_latex": "a=b", "section_name": "Intro", "page": 1,
          "symbol_dependencies": [], "steps": [{"step_number": 1, "latex": "a=b", "explanation": "src",
                                                "is_intermediate_derived": False, "sympy_verified": False}],
          "verification_note": "not verified", "source_text": "a=b", "equation_number": None}],
        [],
    ))
    monkeypatch.setattr(orchestrator, "make_video_props", lambda *_args, **_kw: {
        "equation_id": "e1", "title": "Intro", "theme": "dark", "fps": 30, "steps": []
    })

    def fail_visuals(*_args, **_kwargs):
        raise RuntimeError("diagram exploded")

    monkeypatch.setattr(orchestrator, "make_visual_artifacts", fail_visuals)
    monkeypatch.setattr(orchestrator, "make_study_cards", lambda *_args, **_kw: {
        "flashcards": [{"question": "Q", "answer": "A", "tag": "t"}],
        "viva_questions": [{"question": "V", "answer_hint": "H", "key_concept": "C"}],
    })

    orchestrator.analyze(paper_id, job_id, Path("unused.pdf"))
    job = repo.get_job(job_id)
    paper = repo.get_paper(paper_id)
    assert job["status"] == "partially_completed"
    assert "diagram exploded" in job["error"]
    assert paper["paper"]["title"] == "Kept Title"
    assert paper["paper"]["markdown_content"] == "md"
    assert paper["equations"]
