from typing import Any, Literal
from pydantic import BaseModel, Field


class MathSymbol(BaseModel):
    symbol: str
    name: str
    dimensions: str = ""
    definition: str
    first_introduced_sec: str = ""
    status: Literal["defined", "occurrence"] = "occurrence"


class EquationStep(BaseModel):
    step_number: int
    latex: str
    explanation: str
    is_intermediate_derived: bool = False
    sympy_verified: bool = False


class DerivationBlock(BaseModel):
    equation_id: str
    official_latex: str
    symbol_dependencies: list[str] = Field(default_factory=list)
    steps: list[EquationStep] = Field(default_factory=list)
    section_name: str = "Extracted equations"
    page: int | None = None
    source_text: str = ""
    verification_note: str = ""
    equation_number: str | None = None
    plain_explanation: str = ""
    intuition: str = ""
    verification_status: Literal["extracted_only", "partially_checked"] = "extracted_only"
    explained_symbols: list[dict[str, Any]] = Field(default_factory=list)


class VideoStep(BaseModel):
    durationInFrames: int
    latex: str
    narration_text: str
    audio_url: str | None = None


class VideoCompositionProps(BaseModel):
    equation_id: str
    title: str
    steps: list[VideoStep]
    theme: Literal["dark", "cyber", "minimal"] = "dark"
    fps: int = 30


class StudyKitArtifacts(BaseModel):
    diagram_mermaid: str
    python_code: str
    video_composition_props: VideoCompositionProps
    video_mp4_url: str | None = None
    flashcards: list[dict[str, str]] = Field(default_factory=list)
    viva_questions: list[dict[str, str]] = Field(default_factory=list)


class JobStatus(BaseModel):
    job_id: str
    paper_id: str
    status: Literal["queued", "processing", "completed", "partially_completed", "failed"]
    stage: str | None = None
    progress: int = 0
    error: str | None = None
