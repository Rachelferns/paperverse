PaperVerse — Project Plan

1. Vision

PaperVerse is an interactive academic study kit and mathematical explanation platform that transforms research papers into understandable, verifiable, and interactive learning experiences.

The goal is to go beyond static summaries by helping users understand mathematical derivations, explore paper architectures, execute educational code, watch animated mathematical explanations, and actively recall concepts.

Core principle: Every feature must serve the goal of understanding academic papers. Generated content must be traceable to its source, and mathematical verification must never be falsely claimed.

2. Development Principles

This is an existing, in-progress project. Inspect the current implementation before making changes.

Preserve working functionality and existing architectural decisions unless a change explicitly requires otherwise.

Treat this plan as the product direction. Do not silently omit requirements.

Build incrementally. Do not attempt to implement the entire platform in one change.

Prefer working, tested functionality over placeholders and superficial UI.

Validate generated outputs, handle failures gracefully, and expose uncertainty.

Do not mark a feature complete until its acceptance criteria have been verified.

Keep secrets in environment variables and never commit credentials.

Use sandboxing and resource limits for executable code.

Flag significant architectural conflicts or expensive dependencies before introducing them.

3. Intended Architecture

Frontend

Next.js 14, React, and TypeScript.

Tailwind CSS and shadcn/ui.

A resizable three-pane workspace:

Left: table of contents and mathematical symbol glossary.

Center: PDF viewer, extracted content, equations, and derivations.

Right: diagrams, executable code, generated videos, and study artifacts.

KaTeX for mathematical rendering.

React Flow and Mermaid.js for architecture diagrams and methodology visualization.

Remotion Player for interactive mathematical videos.

Pyodide for supported Python execution inside the browser.

Backend and Orchestration

FastAPI for versioned REST endpoints and streaming updates.

Celery and Redis for asynchronous ingestion and rendering jobs.

Pydantic for request validation and structured AI outputs.

Modular Python packages separating ingestion, mathematics, rendering, diagrams, and pedagogy.

Data and Storage

Supabase PostgreSQL for relational application data.

Qdrant or an existing suitable vector database for semantic retrieval.

S3-compatible object storage for generated videos, audio, and Anki decks.

Maintain document, equation, symbol, derivation, and artifact relationships.

Inspect the existing repository before selecting, replacing, or installing dependencies. Avoid running duplicate infrastructure when an adequate implementation already exists.

4. Five-Stage Processing Pipeline

Stage 1 — PDF Ingestion and Structuring

Objective: Convert an uploaded academic paper into structured, searchable content.

Requirements:

Upload and validate PDF files.

Extract text, headings, page numbers, equations, figures, captions, and references where supported.

Use a suitable layout-aware parser such as Marker or Nougat.

Convert extracted content into structured Markdown while preserving LaTeX.

Chunk content hierarchically by document section.

Index chunks in the vector database with metadata such as paper ID, section, page number, and equation IDs.

Preserve links between extracted content and its original location.

Acceptance criteria:

Valid PDFs can be ingested asynchronously.

Invalid files and extraction failures produce useful errors.

Extracted content retains page and section references wherever available.

Processing status and partial failures are visible.

Reprocessing does not silently create duplicate records.

Stage 2 — Mathematical Explanation and Verification

Objective: Explain equations and derivations step by step.

Requirements:

Detect display and inline equations using text extraction, regular expressions, and vision-based fallback where necessary.

Assign stable equation IDs.

Extract mathematical symbols and contextual definitions.

Record dimensions, notation, and first occurrence where available.

Build a directed dependency graph linking equations and symbols.

Generate intermediate derivation steps with explanations of the mathematical rules used.

Use SymPy to verify supported symbolic transformations.

Use an LLM as a fallback for unsupported tensor notation or equations that cannot be parsed symbolically.

Acceptance criteria:

Every displayed equation retains its original LaTeX and source location where available.

Original equations and AI-derived intermediate steps are distinguishable.

Each step records whether symbolic verification succeeded.

Failed or unsupported verification is explicitly reported as unverified.

No LLM-generated derivation is automatically labeled mathematically verified.

Symbol dependencies can be explored interactively.

Stage 3 — Mathematical Video and Motion Engine

Objective: Turn mathematical derivations into synchronized visual explanations.

Requirements:

Convert derivation steps into validated, structured video-composition data.

Define equation IDs, step ordering, LaTeX, narration, durations, FPS, and visual themes.

Provide interactive browser previews using Remotion Player.

Support audio narration synchronized with mathematical steps.

Render downloadable MP4 videos through background jobs.

Use Remotion rendering or a suitable supported rendering infrastructure.

Provide a Manim-based alternative for suitable geometry and transformation visualizations.

Track rendering states, errors, and output locations.

Acceptance criteria:

Valid composition data can be previewed without a production render.

Step navigation and timing work correctly.

Rendering jobs expose meaningful status and errors.

Completed renders can be retrieved through authorized URLs.

Failed renders can be retried safely.

Unsupported derivations do not prevent other study artifacts from being generated.

Stage 4 — Visual Diagrams and Code Execution

Objective: Make paper methodologies and algorithms explorable.

Requirements:

Generate Mermaid flowcharts or sequence diagrams from relevant paper sections.

Validate diagram syntax before displaying diagrams.

Generate runnable Python, NumPy, or PyTorch educational examples.

Provide syntax highlighting and clear execution feedback.

Run supported code inside Pyodide in the browser.

Enforce execution time, memory, and capability limits where possible.

Explain dependencies and limitations when a generated example cannot run in the browser.

Acceptance criteria:

Valid diagrams render interactively.

Invalid diagrams return actionable errors.

Supported code runs in an isolated browser environment.

Execution errors are displayed without breaking the application.

Generated code is associated with the paper section or methodology it explains.

Stage 5 — Pedagogy and Active Recall

Objective: Convert understanding into reusable study material.

Requirements:

Generate flashcards with concise questions, answers, and topic tags.

Export Anki-compatible .apkg decks using genanki.

Generate viva questions with answer hints and key concepts.

Generate multiple-choice questions with answer keys and explanations.

Validate generated outputs using explicit schemas.

Associate artifacts with their source paper and relevant concepts.

Allow users to download or revisit generated materials.

Acceptance criteria:

Flashcards and quizzes follow validated data structures.

Anki exports are downloadable and importable into Anki.

Viva questions cover relevant paper concepts.

Invalid model outputs are rejected or retried safely.

Artifact generation failures do not corrupt existing paper data.

5. Core Data Models

Maintain equivalent validated backend models and frontend TypeScript interfaces.

MathSymbol

symbol

name

dimensions

definition

first_introduced_sec

EquationStep

step_number

latex

explanation

is_intermediate_derived

sympy_verified

DerivationBlock

equation_id

official_latex

symbol_dependencies

steps

VideoCompositionProps

equation_id

title

steps: duration, LaTeX, narration, and optional audio URL

theme: dark, cyber, or minimal

fps

StudyKitArtifacts

diagram_mermaid

python_code

video_composition_props

video_mp4_url

flashcards

viva_questions

Use consistent identifiers and validation rules across API responses, database records, background jobs, and frontend components.

6. API Requirements

Implement and document versioned endpoints as appropriate:

POST /api/v1/papers/upload — upload and enqueue paper ingestion.

Paper retrieval endpoints — retrieve paper metadata and extracted content.

GET /api/v1/jobs/{job_id} — inspect job status and progress.

Server-Sent Events endpoint — stream extraction or processing updates.

GET /api/v1/papers/{id}/download-anki — retrieve an authorized Anki deck.

Add endpoints for equations, symbols, derivations, diagrams, code examples, and generated videos as needed by the existing application.

Requirements:

Validate inputs and outputs.

Return consistent error responses.

Use background jobs for expensive processing.

Enforce upload limits, authorization where applicable, and ownership checks.

Document request and response schemas.

Avoid breaking existing API contracts.

7. Database Requirements

Use the following logical entities, adapting existing migrations and models where necessary:

papers: paper metadata, extracted Markdown, timestamps, and processing status.

equations: paper relationship, original LaTeX, section, and derivation payload.

symbol_glossary: paper relationship, symbol, definition, and dimensions.

generated_videos: equation relationship, composition properties, video URL, and rendering status.

artifacts: paper relationship, diagrams, executable code, flashcards, and quizzes.

Use UUID identifiers where appropriate, foreign keys, timestamps, indexes, and JSONB for suitable structured payloads.

Do not assume the initial SQL schema is production-ready. Add appropriate constraints, indexes, migration handling, access controls, and storage policies.

8. Processing Reliability and Error Handling

Represent ingestion, derivation, and rendering states explicitly.

Distinguish queued, processing, completed, partially completed, and failed jobs where applicable.

Capture useful errors without exposing secrets or internal credentials.

Support retries for transient failures.

Make background jobs idempotent where possible.

Preserve successful partial results when another independent stage fails.

Apply timeouts and resource limits to expensive operations.

Keep model-generated outputs separate from verified source data.

Track model and parser failures for debugging.

Avoid duplicate records during retries.

9. Security and Data Integrity

Validate file type, size, and content before processing uploads.

Treat paper text, extracted instructions, and generated code as untrusted.

Never allow uploaded documents to override application instructions or security policies.

Never execute arbitrary generated Python on the backend without appropriate isolation.

Restrict browser code execution capabilities and resource usage.

Keep database credentials, API keys, and storage secrets outside source control.

Enforce authorization and ownership checks on private papers and artifacts.

Validate storage URLs and restrict access to generated files.

Avoid logging confidential paper contents or secrets unnecessarily.

10. Testing and Verification

Add tests incrementally as each feature is implemented.

Unit tests

PDF extraction and Markdown normalization.

Equation and symbol parsing.

Supported SymPy transformations.

Verification failure and fallback behavior.

API schema validation.

Mermaid validation.

Video composition validation.

Flashcard and quiz generation schemas.

Integration tests

Upload through extraction and database persistence.

Equation extraction through derivation generation.

Background queue status and retry behavior.

Vector indexing and retrieval.

Video rendering and artifact storage.

Anki deck generation and download.

End-to-end tests

Upload a paper and inspect extracted content.

Navigate between equations and symbol definitions.

View a derivation and distinguish verified from unverified steps.

Preview a mathematical video.

View a methodology diagram and run a supported code example.

Generate and download study materials.

Use representative papers containing ordinary equations, matrices, tensor notation, long derivations, and extraction edge cases.

11. Implementation Roadmap

Work in small, independently verifiable increments.

Phase 0 — Existing Codebase Audit

Map the current repository and architecture.

Identify working, incomplete, missing, and unverified functionality.

Review existing tests, dependencies, API contracts, and database migrations.

Compare current implementation against this plan.

Identify the highest-priority gap.

Do not rewrite working code during the audit.

Phase 1 — Core Paper Workflow

Stabilize upload and paper persistence.

Implement structured extraction and processing status.

Establish reliable paper retrieval.

Build the basic paper workspace and extraction error states.

Phase 2 — Mathematical Understanding

Implement equation extraction and symbol glossary.

Build the dependency graph.

Generate derivation steps and verification status.

Render interactive mathematical explanations.

Phase 3 — Diagrams and Executable Examples

Generate methodology diagrams.

Validate diagrams and structured code payloads.

Integrate browser-based Python execution with safeguards.

Phase 4 — Animated Explanations

Define the video composition contract.

Implement interactive previews.

Add background rendering, narration, storage, and retries.

Introduce Manim fallback only where justified.

Phase 5 — Active Recall

Generate flashcards, viva questions, and MCQs.

Implement Anki export.

Connect artifacts to their source content.

Phase 6 — Integration and Hardening

Test end-to-end workflows.

Improve error recovery, authorization, observability, and performance.

Resolve architectural inconsistencies.

Document deployment, configuration, and operational requirements.

These phases are a planning sequence, not a requirement to discard the existing implementation and restart from Phase 1. Reorder work according to the audit findings.

12. Definition of Done

A change is complete only when:

It meets its documented acceptance criteria.

It integrates with the existing architecture.

Relevant automated tests and validation checks have been executed.

Failure cases and edge cases have been considered.

Security and data integrity implications have been addressed.

Existing functionality remains intact, or intentional changes are documented.

Relevant specifications and documentation are updated.

Actual limitations, failed tests, and unverified behavior are reported honestly.

13. Immediate Next Action

Perform a read-only audit of the current PaperVerse repository against this plan.

Produce:

A repository and architecture summary.

A feature-by-feature implementation status matrix.

A list of existing functionality that must be preserved.

Missing requirements and significant technical risks.

The recommended next incremental change with acceptance criteria.

Do not implement all planned stages at once. Do not modify application code until the audit and proposed next step have been reviewed.


