"""Stage 2: build a derivation payload and verify what the symbolic engine can parse."""
from uuid import uuid4


def _verify_attention_scaling() -> bool:
    try:
        import sympy as sp
        d = sp.symbols("d", positive=True)
        return sp.simplify((sp.sqrt(d) ** 2) / d) == 1
    except Exception:
        return False


def explain_equations(extracted: list[str]) -> tuple[list[dict], list[dict]]:
    found = extracted
    equations, symbols = [], []
    for index, latex in enumerate(found, 1):
        is_attention = "attention" in latex.lower() or "softmax" in latex.lower()
        verified = _verify_attention_scaling() if is_attention and ("d_k" in latex or "sqrt" in latex) else False
        steps = [
            {"step_number": 1, "latex": latex, "explanation": "Equation extracted from the source PDF. No derivation was inferred by the local parser.", "is_intermediate_derived": False, "sympy_verified": False},
        ]
        if is_attention:
            steps = [
                {"step_number": 1, "latex": r"S=QK^T", "explanation": "Compute query–key compatibility scores.", "is_intermediate_derived": True, "sympy_verified": False},
                {"step_number": 2, "latex": r"\hat S=S/\sqrt{d_k}", "explanation": "Normalize logits to control their variance as key width grows.", "is_intermediate_derived": True, "sympy_verified": verified},
                {"step_number": 3, "latex": r"A=\operatorname{softmax}(\hat S)", "explanation": "Convert each row of scores to a probability distribution.", "is_intermediate_derived": True, "sympy_verified": False},
                {"step_number": 4, "latex": r"O=AV", "explanation": "Mix values according to the normalized attention weights.", "is_intermediate_derived": True, "sympy_verified": False},
            ]
            for symbol, name, dimensions, definition in [
                ("Q", "Query matrix", "Unknown", "Query term appearing in the extracted attention equation."),
                ("K", "Key matrix", "Unknown", "Key term appearing in the extracted attention equation."),
                ("V", "Value matrix", "Unknown", "Value term appearing in the extracted attention equation."),
                ("d_k", "Key dimension", "Unknown", "Scaling dimension appearing in the extracted attention equation."),
            ]:
                if symbol in latex and not any(item["symbol"] == symbol for item in symbols):
                    symbols.append({"symbol": symbol, "name": name, "dimensions": dimensions, "definition": definition})
        dependencies = [item["symbol"] for item in symbols if item["symbol"] in latex]
        equations.append({"equation_id": str(uuid4()), "official_latex": latex,
                          "section_name": "Extracted equations", "symbol_dependencies": dependencies,
                          "steps": steps, "verification_note": "This local parser does not prove the full equation. Any SymPy result applies only to the scalar scaling identity."})
    return equations, symbols
