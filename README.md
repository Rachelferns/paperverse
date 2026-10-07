# PaperVerse

PaperVerse is a local-first academic paper study workbench. The included frontend is React + Vite; the API is a modular FastAPI service. Uploads and analysis data stay on the local machine by default.

## Start the app

In one terminal:

```bash
npm install
npm run dev
```

In a second terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn paperverse.main:app --app-dir . --reload --port 8001
```

Open `http://localhost:5173`. Set `VITE_API_BASE` if the API uses a different URL. The frontend default is `http://localhost:8001/api/v1`.

For Redis/Celery mode, set `PAPERVERSE_QUEUE_MODE=celery` and `PAPERVERSE_REDIS_URL`, then run a worker with `celery -A paperverse.queue.celery_app worker --loglevel=INFO`. See [backend/README.md](backend/README.md) for pipeline details and current provider boundaries.

## What runs locally today

- PDF text extraction and section/equation discovery with PyMuPDF.
- Structured equation-step payloads, a narrow SymPy scaling identity check, and a clear verification note for unsupported tensor proofs.
- Mermaid diagrams, Python snippets, flashcards, viva prompts, and Remotion composition props.
- SQLite storage, background processing, job polling, and SSE progress events.
- In-browser Remotion preview, Mermaid rendering, and Pyodide + NumPy execution.
- Anki package generation after analysis completes.

Hosted model reasoning, OCR for scanned pages, vector indexing, Supabase persistence, audio narration, and server-side MP4 rendering need provider implementations and credentials; the local pipeline reports unsupported steps instead of claiming these integrations ran.
