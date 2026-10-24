from typing import Literal
from pydantic import BaseModel, Field


class MathSymbol(BaseModel):
    symbol: str
    name: str
    dimensions: str = "Unknown"
    definition: str
    first_introduced_sec: str = ""


class EquationStep(BaseModel):
    step_number: str
    latex: str = ""
    latex_expression: str = ""
    explanation: str = ""
    axiom_or_rule_applied: str = ""
    is_intermediate_derived: bool = False
    sympy_verified: bool = False


class DerivationBlock(BaseModel):
    equation_id: str
    original_latex: str = ""
    official_latex: str = ""
    paper_section: str = ""
    conceptual_summary: str = ""
    symbol_glossary: list[dict] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    step_by_step_derivation: list[dict] = Field(default_factory=list)
    sympy_verification_script: str = ""
    notational_notes_or_typos: str = ""
    symbol_dependencies: list[str] = Field(default_factory=list)
    steps: list[EquationStep] = Field(default_factory=list)
    verification_note: str = ""


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
    status: Literal["queued", "processing", "completed", "failed"]
    stage: str | None = None
    progress: int = 0
    error: str | None = None
