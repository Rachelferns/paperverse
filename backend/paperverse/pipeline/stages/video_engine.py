"""Stage 3: a step timeline for preview. This stage does not render audio or MP4."""


def make_video_props(equation: dict | None, paper_title: str = "Paper") -> dict:
    if not equation or not (equation.get("official_latex") or equation.get("steps")):
        return {
            "equation_id": "",
            "title": f"{paper_title}: no equation walkthrough",
            "theme": "dark",
            "fps": 30,
            "steps": [],
        }
    raw_steps = equation.get("steps") or [{
        "latex": equation.get("official_latex", ""),
        "explanation": equation.get("plain_explanation") or "Equation extracted from the source PDF.",
        "is_intermediate_derived": False,
    }]
    usable = [step for step in raw_steps if step.get("latex") or step.get("explanation")]
    built = []
    total = len(usable)
    for index, step in enumerate(usable):
        kind = "Checked identity" if step.get("is_intermediate_derived") else "Extracted equation"
        if index == 0:
            relation = "This is the first step of the walkthrough."
        else:
            relation = "This step follows the previous one."
        if index == total - 1:
            relation += " Nothing follows it."
        else:
            relation += " The next step continues from here."
        explanation = step.get("explanation") or "No explanation is available for this step."
        built.append({
            "durationInFrames": 120,
            "latex": step.get("latex") or equation.get("official_latex") or "",
            "narration_text": f"{kind}. {explanation} {relation}",
            "audio_url": None,
        })
    section = equation.get("section_name") or paper_title
    return {
        "equation_id": equation.get("equation_id") or "",
        "title": f"Concept walkthrough: {section}",
        "theme": "dark",
        "fps": 30,
        "steps": built,
    }
