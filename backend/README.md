# PaperVerse API

Local-first FastAPI backend. It accepts PDF uploads and arXiv IDs/URLs, extracts selectable text, builds a structured study kit, persists papers/jobs/derivations in SQLite, and streams job changes over SSE. Redis/Celery is available as an opt-in queue adapter; the default local queue needs no Redis service.

## Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn paperverse.main:app --reload --port 8000
```

Set `PAPERVERSE_QUEUE_MODE=celery` and run `celery -A paperverse.queue.celery_app worker --loglevel=INFO` to use Redis/Celery. Set `PAPERVERSE_DATA_DIR` to move local uploads and SQLite data.

The local stages are deterministic adapters, not hosted LLM calls. PDF text extraction uses PyMuPDF; scanned-page OCR, vector embeddings/Qdrant, Supabase credentials, audio generation, and MP4 rendering need separately configured providers. SymPy's badge is limited to the scalar identity check described in each derivation payload and must not be interpreted as full tensor proof.
