import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from paperverse.config import get_settings


class Repository:
    """Small SQLite repository for local development; production can use Supabase."""
    def __init__(self) -> None:
        self.path = get_settings().data_dir / "paperverse.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self.initialize()

    def connect(self):
        db = sqlite3.connect(self.path, check_same_thread=False)
        db.row_factory = sqlite3.Row
        return db

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS papers (
              id TEXT PRIMARY KEY, title TEXT NOT NULL, arxiv_id TEXT,
              source_filename TEXT NOT NULL, markdown_content TEXT DEFAULT '', summary TEXT DEFAULT '', sections_json TEXT DEFAULT '[]',
              created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued'
            );
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
              status TEXT NOT NULL, stage TEXT, progress INTEGER NOT NULL DEFAULT 0,
              error TEXT, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS equations (
              id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
              official_latex TEXT NOT NULL, section_name TEXT, derivation_payload TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS symbol_glossary (
              id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
              symbol TEXT NOT NULL, definition TEXT NOT NULL, dimensions TEXT
            );
            CREATE TABLE IF NOT EXISTS artifacts (
              id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
              mermaid_diagram TEXT, executable_python TEXT, flashcards_json TEXT, viva_quiz_json TEXT,
              video_props_json TEXT
            );
            """)
            paper_columns = {row[1] for row in db.execute("PRAGMA table_info(papers)")}
            if "summary" not in paper_columns:
                db.execute("ALTER TABLE papers ADD COLUMN summary TEXT DEFAULT ''")
            if "sections_json" not in paper_columns:
                db.execute("ALTER TABLE papers ADD COLUMN sections_json TEXT DEFAULT '[]'")

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_paper_job(self, paper_id: str, job_id: str, title: str, filename: str, arxiv_id: str | None) -> None:
        with self.lock, self.connect() as db:
            db.execute("INSERT INTO papers (id,title,arxiv_id,source_filename,created_at) VALUES (?,?,?,?,?)",
                       (paper_id, title, arxiv_id, filename, self.now()))
            db.execute("INSERT INTO jobs (id,paper_id,status,updated_at) VALUES (?,?,?,?)",
                       (job_id, paper_id, "queued", self.now()))

    def update_job(self, job_id: str, status: str, stage: str | None, progress: int, error: str | None = None) -> None:
        with self.lock, self.connect() as db:
            db.execute("UPDATE jobs SET status=?,stage=?,progress=?,error=?,updated_at=? WHERE id=?",
                       (status, stage, progress, error, self.now(), job_id))
            if status in ("completed", "partially_completed", "failed"):
                db.execute("UPDATE papers SET status=? WHERE id=(SELECT paper_id FROM jobs WHERE id=?)", (status, job_id))

    def save_analysis(self, paper_id: str, title: str, markdown: str, summary: str, sections: list[dict], equations: list[dict], symbols: list[dict], artifacts: dict) -> None:
        with self.lock, self.connect() as db:
            db.execute("UPDATE papers SET title=?,markdown_content=?,summary=?,sections_json=? WHERE id=?",
                       (title, markdown, summary, json.dumps(sections), paper_id))
            db.execute("DELETE FROM equations WHERE paper_id=?", (paper_id,))
            db.execute("DELETE FROM symbol_glossary WHERE paper_id=?", (paper_id,))
            for equation in equations:
                db.execute("INSERT OR REPLACE INTO equations VALUES (?,?,?,?,?,?)",
                           (equation["equation_id"], paper_id, equation["official_latex"], equation.get("section_name"),
                            json.dumps(equation), self.now()))
            for index, symbol in enumerate(symbols):
                db.execute("INSERT INTO symbol_glossary VALUES (?,?,?,?,?)",
                           (f"{paper_id}-{index}", paper_id, symbol["symbol"], symbol["definition"], symbol.get("dimensions")))
            db.execute("INSERT OR REPLACE INTO artifacts VALUES (?,?,?,?,?,?,?)",
                       (f"{paper_id}-artifacts", paper_id, artifacts["diagram_mermaid"], artifacts["python_code"],
                        json.dumps(artifacts["flashcards"]), json.dumps(artifacts["viva_questions"]),
                        json.dumps(artifacts["video_composition_props"])))

    def get_job(self, job_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row: return None
        return dict(row)

    def get_recent_job(self) -> dict | None:
        with self.connect() as db:
            row = db.execute("""SELECT jobs.* FROM jobs JOIN papers ON papers.id=jobs.paper_id
                               ORDER BY papers.created_at DESC LIMIT 1""").fetchone()
        return dict(row) if row else None

    def get_paper(self, paper_id: str) -> dict | None:
        with self.connect() as db:
            paper = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
            if not paper: return None
            equations = db.execute("SELECT derivation_payload FROM equations WHERE paper_id=?", (paper_id,)).fetchall()
            symbols = db.execute("SELECT symbol,definition,dimensions FROM symbol_glossary WHERE paper_id=?", (paper_id,)).fetchall()
            artifacts = db.execute("SELECT * FROM artifacts WHERE paper_id=?", (paper_id,)).fetchone()
        paper_data = dict(paper)
        paper_data["sections"] = json.loads(paper_data.pop("sections_json", "[]") or "[]")
        return {"paper": paper_data, "equations": [json.loads(r[0]) for r in equations],
                "symbols": [dict(r) for r in symbols], "artifacts": self._decode_artifacts(artifacts)}

    @staticmethod
    def _decode_artifacts(row):
        if not row: return None
        data = dict(row)
        return {"diagram_mermaid": data["mermaid_diagram"], "python_code": data["executable_python"],
                "flashcards": json.loads(data["flashcards_json"] or "[]"),
                "viva_questions": json.loads(data["viva_quiz_json"] or "[]"),
                "video_composition_props": json.loads(data["video_props_json"] or "{}")}


repository = Repository()
