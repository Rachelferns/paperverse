from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from paperverse.api import router

app = FastAPI(title="PaperVerse API", version="0.1.0", description="Local-first paper ingestion and study kit pipeline")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "paperverse-api"}
