from uuid import uuid4
from paperverse.storage.repository import Repository


def _ids():
    return str(uuid4()), str(uuid4())


def test_save_analysis_replaces_equations_and_symbols(tmp_data_dir):
    repo = Repository()
    paper_id, job_id = _ids()
    repo.create_paper_job(paper_id, job_id, "Paper", "paper.pdf", None)
    artifacts = {
        "diagram_mermaid": "flowchart TD\n  A[A]",
        "python_code": "",
        "flashcards": [{"question": "Q", "answer": "A", "tag": "t"}],
        "viva_questions": [{"question": "V", "answer_hint": "H", "key_concept": "C"}],
        "video_composition_props": {"equation_id": "", "title": "t", "steps": []},
    }
    eq = {"equation_id": "eq-1", "official_latex": "a=b", "section_name": "Intro", "steps": []}
    repo.save_analysis(paper_id, "Paper", "md", "sum", [], [eq],
                       [{"symbol": "a", "definition": "def", "dimensions": "R"}], artifacts)
    repo.save_analysis(paper_id, "Paper", "md", "sum", [], [eq],
                       [{"symbol": "a", "definition": "def", "dimensions": "R"}], artifacts)
    paper = repo.get_paper(paper_id)
    assert len(paper["equations"]) == 1
    assert len(paper["symbols"]) == 1


def test_partially_completed_updates_paper_status(tmp_data_dir):
    repo = Repository()
    paper_id, job_id = _ids()
    repo.create_paper_job(paper_id, job_id, "Paper", "paper.pdf", None)
    repo.update_job(job_id, "partially_completed", "complete", 100, "visual_sandbox: boom")
    job = repo.get_job(job_id)
    assert job["status"] == "partially_completed"
    assert "boom" in job["error"]
