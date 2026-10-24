from pathlib import Path
from paperverse.pipeline.stages.ingestion import ingest_pdf
from paperverse.pipeline.stages.math_engine import explain_equations
from paperverse.pipeline.stages.video_engine import make_video_props
from paperverse.pipeline.stages.visuals import make_visual_artifacts
from paperverse.pipeline.stages.pedagogy import make_study_cards
from paperverse.storage.repository import repository


def analyze(paper_id: str, job_id: str, file_path: Path) -> None:
    stages = [("ingestion", 15), ("math_explainer", 40), ("video_timeline", 60),
              ("visual_sandbox", 78), ("active_recall", 92)]
    try:
        repository.update_job(job_id, "processing", stages[0][0], stages[0][1])
        document = ingest_pdf(file_path)
        repository.update_job(job_id, "processing", stages[1][0], stages[1][1])
        equations, symbols = explain_equations(document["equations"], document["markdown"])
        repository.update_job(job_id, "processing", stages[2][0], stages[2][1])
        video_props = make_video_props(equations[0] if equations else None, document["title"])
        repository.update_job(job_id, "processing", stages[3][0], stages[3][1])
        visual = make_visual_artifacts(document["sections"], document["title"], document["text"])
        repository.update_job(job_id, "processing", stages[4][0], stages[4][1])
        recall = make_study_cards(document["title"], document["summary"], document["headings"])
        artifacts = {**visual, **recall, "video_composition_props": video_props, "video_mp4_url": None}
        repository.save_analysis(paper_id, document["title"], document["markdown"], document["summary"],
                                 document["sections"], equations, symbols, artifacts)
        repository.update_job(job_id, "completed", "complete", 100)
    except Exception as exc:
        repository.update_job(job_id, "failed", "failed", 100, str(exc))
