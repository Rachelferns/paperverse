import asyncio
import json
import re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from paperverse.config import get_settings
from paperverse.pipeline.orchestrator import analyze
from paperverse.queue import celery_app
from paperverse.storage.repository import repository

router = APIRouter(prefix="/api/v1")
settings = get_settings()


def _schedule(paper_id: str, job_id: str, target: Path, background: BackgroundTasks) -> None:
    if celery_app:
        from paperverse.queue import analyze_pdf_task
        analyze_pdf_task.delay(paper_id, job_id, str(target))
    else:
        background.add_task(analyze, paper_id, job_id, target)


@router.post("/papers/upload", status_code=202)
async def upload_paper(background: BackgroundTasks, file: UploadFile = File(...)):
    if file.content_type not in ("application/pdf", "application/octet-stream") and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(415, "Upload a PDF file.")
    paper_id, job_id = str(uuid4()), str(uuid4())
    filename = Path(file.filename or "paper.pdf").name
    paper_dir = settings.data_dir / "uploads"
    paper_dir.mkdir(parents=True, exist_ok=True)
    target = paper_dir / f"{paper_id}.pdf"
    size = 0
    with target.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                target.unlink(missing_ok=True)
                raise HTTPException(413, "PDF exceeds the configured upload limit.")
            out.write(chunk)
    if size == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(400, "The uploaded file is empty.")
    header = target.read_bytes()[:5]
    if not header.startswith(b"%PDF"):
        target.unlink(missing_ok=True)
        raise HTTPException(415, "Upload a valid PDF file.")
    arxiv_match = re.search(r"(?:arxiv\.org/(?:abs|pdf)/)?(\d{4}\.\d{4,5})", filename)
    title = Path(filename).stem.replace("_", " ")
    repository.create_paper_job(paper_id, job_id, title, filename, arxiv_match.group(1) if arxiv_match else None)
    _schedule(paper_id, job_id, target, background)
    return {"paper_id": paper_id, "job_id": job_id, "status": "queued"}


@router.post("/papers/arxiv", status_code=202)
async def import_arxiv(payload: dict, background: BackgroundTasks):
    source = str(payload.get("url", "")).strip()
    match = re.search(r"(?:arxiv\.org/(?:abs|pdf)/)?(\d{4}\.\d{4,5}(?:v\d+)?)", source)
    if not match:
        raise HTTPException(422, "Paste a valid arXiv URL or paper ID.")
    arxiv_id = match.group(1)
    request = Request(f"https://export.arxiv.org/pdf/{arxiv_id}", headers={"User-Agent": "PaperVerse/0.1 contact: local-app"})
    try:
        pdf_bytes = await asyncio.to_thread(lambda: urlopen(request, timeout=20).read(settings.max_upload_bytes + 1))
    except (URLError, HTTPError, TimeoutError) as exc:
        raise HTTPException(502, f"Could not retrieve the arXiv PDF: {exc}") from exc
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(502, "arXiv did not return a PDF for that identifier.")
    if len(pdf_bytes) > settings.max_upload_bytes:
        raise HTTPException(413, "PDF exceeds the configured upload limit.")
    paper_id, job_id = str(uuid4()), str(uuid4())
    paper_dir = settings.data_dir / "uploads"
    paper_dir.mkdir(parents=True, exist_ok=True)
    target = paper_dir / f"{paper_id}.pdf"
    target.write_bytes(pdf_bytes)
    repository.create_paper_job(paper_id, job_id, f"arXiv:{arxiv_id}", f"{arxiv_id}.pdf", arxiv_id)
    _schedule(paper_id, job_id, target, background)
    return {"paper_id": paper_id, "job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    return job


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str):
    if not repository.get_job(job_id):
        raise HTTPException(404, "Job not found.")
    async def stream():
        last = None
        while True:
            current = repository.get_job(job_id)
            if not current: break
            payload = json.dumps(current)
            if payload != last:
                yield f"event: job\ndata: {payload}\n\n"
                last = payload
            if current["status"] in ("completed", "partially_completed", "failed"): break
            await asyncio.sleep(0.8)
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/papers/recent")
def get_recent_paper():
    job = repository.get_recent_job()
    if not job:
        return {"job": None, "paper": None}
    result = repository.get_paper(job["paper_id"])
    return {"job": job, **(result or {})}


@router.get("/papers/{paper_id}")
def get_paper(paper_id: str):
    paper = repository.get_paper(paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found.")
    return paper


@router.get("/papers/{paper_id}/download-anki")
def download_anki(paper_id: str):
    paper = repository.get_paper(paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found.")
    try:
        import genanki
    except ImportError:
        raise HTTPException(501, "Anki export is unavailable; install backend dependencies.")
    model = getattr(genanki, "BASIC_MODEL", None) or getattr(genanki, "Basic", None)
    if model is None:
        raise HTTPException(501, "This genanki version does not expose a Basic note model.")
    deck = genanki.Deck(abs(hash(paper_id)) % (2**31), paper["paper"]["title"])
    for item in (paper["artifacts"] or {}).get("flashcards", []):
        deck.add_note(genanki.Note(model=model, fields=[item["question"], item["answer"]], tags=[item.get("tag", "paperverse")]))
    out = settings.data_dir / f"{paper_id}.apkg"
    genanki.Package(deck).write_to_file(str(out))
    from fastapi.responses import FileResponse
    return FileResponse(out, media_type="application/octet-stream", filename=f"{paper_id}.apkg")
