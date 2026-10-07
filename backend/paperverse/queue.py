"""Optional Redis/Celery adapter; local development uses FastAPI BackgroundTasks."""
from paperverse.config import get_settings

settings = get_settings()
celery_app = None
if settings.queue_mode == "celery":
    from celery import Celery
    celery_app = Celery("paperverse", broker=settings.redis_url, backend=settings.redis_url)
    celery_app.conf.update(task_track_started=True, result_expires=3600)

    @celery_app.task(name="paperverse.analyze_pdf")
    def analyze_pdf_task(paper_id: str, job_id: str, file_path: str):
        from paperverse.pipeline.orchestrator import analyze
        analyze(paper_id, job_id, __import__("pathlib").Path(file_path))
