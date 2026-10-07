"""Stage 3: produce a Remotion-compatible timeline; server MP4 rendering is optional."""


def make_video_props(equation: dict | None, paper_title: str = "Paper") -> dict:
    if not equation:
        return {"equation_id": "", "title": f"{paper_title}: no extracted equation", "theme": "dark", "fps": 30, "steps": []}
    steps = equation.get("steps", [])
    return {"equation_id": equation["equation_id"], "title": "Scaled dot-product attention",
            "theme": "dark", "fps": 30,
            "steps": [{"durationInFrames": 90, "latex": step["latex"],
                       "narration_text": step["explanation"], "audio_url": None} for step in steps]}
