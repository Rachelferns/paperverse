"""Stage 3: produce a Remotion-compatible timeline; server MP4 rendering is optional."""


def make_video_props(equation: dict | None, paper_title: str = "Paper") -> dict:
    if not equation:
        return {"equation_id": "", "title": f"{paper_title}: mathematical derivation", "theme": "dark", "fps": 30, "steps": []}
    steps = equation.get("steps") or equation.get("step_by_step_derivation") or []
    title = equation.get("conceptual_summary", "")[:50] or equation.get("paper_section") or "Mathematical Derivation"
    return {
        "equation_id": equation.get("equation_id", ""),
        "title": title,
        "theme": "dark",
        "fps": 30,
        "steps": [
            {
                "durationInFrames": 90,
                "latex": step.get("latex") or step.get("latex_expression", ""),
                "narration_text": step.get("explanation", ""),
                "audio_url": None,
            }
            for step in steps
        ],
    }
