from pathlib import Path
from paperverse.pipeline.stages.ingestion import ingest_pdf
from paperverse.pipeline.stages.math_engine import explain_equations
from paperverse.pipeline.stages.video_engine import make_video_props
from paperverse.pipeline.stages.visuals import make_visual_artifacts, unavailable_architecture
from paperverse.pipeline.stages.pedagogy import make_study_cards
from paperverse.schemas import StudyKitArtifacts, VideoCompositionProps
from paperverse.storage.repository import repository


def _equations_with_context(document: dict) -> list:
    sections = document.get("sections") or []
    prepared = []
    for item in document.get("equations") or []:
        equation = dict(item) if isinstance(item, dict) else {"official_latex": item}
        if not equation.get("context"):
            section = next((candidate for candidate in sections if candidate.get("title") == equation.get("section_name")), None)
            equation["context"] = (section or {}).get("content") or ""
        prepared.append(equation)
    return prepared


def _empty_artifacts(title: str) -> dict:
    return StudyKitArtifacts(
        diagram_mermaid=unavailable_architecture(
            f"No method architecture was inferred for {title}. Document headings are not used as a diagram."
        ),
        python_code="",
        video_composition_props=VideoCompositionProps(
            equation_id="", title=f"{title}: no extracted equation", steps=[],
        ),
        video_mp4_url=None,
        flashcards=[],
        viva_questions=[],
    ).model_dump()


def analyze(paper_id: str, job_id: str, file_path: Path) -> None:
    stage_errors: list[str] = []
    try:
        repository.update_job(job_id, "processing", "ingestion", 15)
        document = ingest_pdf(file_path)
    except Exception as exc:
        repository.update_job(job_id, "failed", "failed", 100, str(exc))
        return

    equations, symbols = [], []
    artifacts = _empty_artifacts(document["title"])

    try:
        repository.update_job(job_id, "processing", "math_explainer", 40)
        equations, symbols = explain_equations(_equations_with_context(document))
    except Exception as exc:
        stage_errors.append(f"math_explainer: {exc}")

    try:
        repository.update_job(job_id, "processing", "video_timeline", 60)
        artifacts["video_composition_props"] = make_video_props(
            equations[0] if equations else None, document["title"]
        )
    except Exception as exc:
        stage_errors.append(f"video_timeline: {exc}")

    try:
        repository.update_job(job_id, "processing", "visual_sandbox", 78)
        visual = make_visual_artifacts(document["sections"], document["title"], document["text"])
        artifacts["diagram_mermaid"] = visual["diagram_mermaid"]
        artifacts["python_code"] = visual["python_code"]
    except Exception as exc:
        stage_errors.append(f"visual_sandbox: {exc}")

    try:
        repository.update_job(job_id, "processing", "active_recall", 92)
        recall = make_study_cards(
            document["title"], document["summary"], document["headings"],
            sections=document["sections"], equations=equations,
        )
        artifacts["flashcards"] = recall["flashcards"]
        artifacts["viva_questions"] = recall["viva_questions"]
    except Exception as exc:
        stage_errors.append(f"active_recall: {exc}")

    try:
        artifacts = StudyKitArtifacts.model_validate(artifacts).model_dump()
        repository.save_analysis(
            paper_id, document["title"], document["markdown"], document["summary"],
            document["sections"], equations, symbols, artifacts,
        )
    except Exception as exc:
        repository.update_job(job_id, "failed", "failed", 100, f"Could not save analysis: {exc}")
        return

    if stage_errors:
        repository.update_job(job_id, "partially_completed", "complete", 100, " | ".join(stage_errors))
    else:
        repository.update_job(job_id, "completed", "complete", 100)
