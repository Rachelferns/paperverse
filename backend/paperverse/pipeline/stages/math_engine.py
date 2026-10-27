"""Stage 2: explain extracted equations without claiming unchecked derivations."""
import re
from uuid import uuid4

from paperverse.schemas import DerivationBlock, EquationStep, MathSymbol

_GREEK = "alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|phi|omega|tau|pi"
_FUNCTION_NAMES = re.compile(
    r"\b(?:softmax|attention|clip|max|min|exp|log|sin|cos|tan|relu|gelu|sigmoid)\b",
    re.I,
)
_KNOWN = (
    ("Q", re.compile(r"\bquer(?:y|ies)\b", re.I), "Query", "What each position uses to look up relevant information."),
    ("K", re.compile(r"\bkeys\b|\bkey vectors?\b|\bkey matrix\b", re.I), "Key", "What each position is matched against."),
    ("V", re.compile(r"\bvalues\b|\bvalue vectors?\b|\bvalue matrix\b", re.I), "Value", "Information combined by the attention weights."),
    ("d_k", re.compile(r"key dimension|dimension of the key", re.I), "Key dimension", "Width of the key vectors. Scores are divided by its square root."),
    ("d_{k}", re.compile(r"key dimension|dimension of the key", re.I), "Key dimension", "Width of the key vectors. Scores are divided by its square root."),
)

ATTENTION_EXPLANATION = (
    "Queries (Q) are compared with keys (K) by a dot product. "
    "The scores are divided by the square root of the key dimension so their magnitude stays stable as that dimension grows. "
    "Softmax turns the scaled scores into weights, and those weights combine the values (V)."
)
ATTENTION_INTUITION = (
    "Reading of this formula: dot products grow with the key dimension, so dividing by its square root keeps softmax from saturating. "
    "The resulting weights blend the values instead of collapsing onto one position."
)


def _as_extracted(item: str | dict) -> dict:
    if isinstance(item, str):
        return {"official_latex": item, "source_text": item, "section_name": "Extracted equations", "page": None, "context": ""}
    return item


def _symbols_from_latex(latex: str) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    cleaned = _FUNCTION_NAMES.sub(" ", latex)
    cleaned = re.sub(r"\^[A-Za-z]", " ", cleaned)
    tokens: list[str] = []
    tokens.extend("\\" + match.group(1) for match in re.finditer(rf"\\({_GREEK})\b", latex))
    tokens.extend(match.group(0) for match in re.finditer(r"\b[A-Za-z](?:_[A-Za-z0-9]+|_\{[^}]+\})", cleaned))
    tokens.extend(match.group(1) for match in re.finditer(r"\b([A-Z])\b", cleaned))
    for token in tokens:
        token = token.strip()
        if not token or len(token) > 24:
            continue
        key = token.casefold()
        if key in seen:
            continue
        seen.add(key)
        symbols.append(token)
        if len(symbols) >= 12:
            break
    return symbols


def _lookup_definition(symbol: str, context: str) -> tuple[str, str] | None:
    if not context:
        return None
    for token, pattern, name, detail in _KNOWN:
        if token.casefold() == symbol.casefold() and pattern.search(context):
            return name, detail
    readable = symbol.replace("\\", "")
    match = re.search(rf"(?i)\b{re.escape(readable)}\b\s+is\s+([^.]{{8,160}})", context)
    if match:
        return readable, match.group(1).strip()
    return None


def _annotate_symbol(symbol: str, section: str, page: int | None, context: str) -> dict:
    found = _lookup_definition(symbol, context)
    where = section + (f", page {page}" if page else "")
    if found:
        name, detail = found
        model = MathSymbol(
            symbol=symbol,
            name=name,
            dimensions="defined",
            definition=f"Defined from nearby text in {where}: {name}. {detail}",
            first_introduced_sec=section,
            status="defined",
        )
    else:
        model = MathSymbol(
            symbol=symbol,
            name=symbol,
            dimensions="occurrence",
            definition=f"Occurrence in {where}. A definition was not extracted from the surrounding text.",
            first_introduced_sec=section,
            status="occurrence",
        )
    return model.model_dump()


def _attention_reading(symbols: list[dict]) -> str:
    defined = {item["symbol"] for item in symbols if item.get("status") == "defined"}
    if {"Q", "K", "V"} <= defined:
        return ATTENTION_EXPLANATION
    return (
        ATTENTION_EXPLANATION
        + " These are the standard roles of this formula. A symbol is marked defined only when the surrounding text states that role."
    )


def _is_scaled_attention(latex: str) -> bool:
    compact = re.sub(r"\s+", "", latex).lower()
    has_softmax = "softmax" in compact
    has_qk = "qk" in compact
    has_scale = "sqrt" in compact or "√" in latex or "d_k" in compact or "d_{k}" in compact
    return has_softmax and has_qk and has_scale


def _scaling_identity_checked() -> bool:
    try:
        import sympy as sp
    except ImportError:
        return False
    dimension = sp.symbols("d_k", positive=True)
    identity = sp.simplify(dimension / (sp.sqrt(dimension) ** 2) - 1)
    return identity == 0


def explain_equations(extracted: list[str] | list[dict]) -> tuple[list[dict], list[dict]]:
    equations: list[dict] = []
    symbols: list[dict] = []
    for item in extracted:
        payload = _as_extracted(item)
        latex = (payload.get("official_latex") or payload.get("source_text") or "").strip()
        if not latex:
            continue
        section = payload.get("section_name") or "Extracted equations"
        page = payload.get("page")
        context = payload.get("context") or ""
        local = [_annotate_symbol(token, section, page, context) for token in _symbols_from_latex(latex)]
        attention = _is_scaled_attention(latex)
        steps = [EquationStep(
            step_number=1,
            latex=latex,
            explanation=ATTENTION_EXPLANATION if attention else "Equation as extracted from selectable PDF text.",
            is_intermediate_derived=False,
            sympy_verified=False,
        )]
        verification_status = "extracted_only"
        if attention and _scaling_identity_checked():
            steps.append(EquationStep(
                step_number=2,
                latex=r"\frac{d_{k}}{\left(\sqrt{d_{k}}\right)^{2}} = 1",
                explanation=(
                    "SymPy checked the algebraic identity d_k / (sqrt(d_k))^2 = 1. "
                    "This supports the scaling term only. It is not a verification of the full attention equation, "
                    "and it is not an intermediate line extracted from the paper."
                ),
                is_intermediate_derived=True,
                sympy_verified=True,
            ))
            verification_status = "partially_checked"
            note = (
                "Extracted from the paper. The full attention equation was not symbolically verified. "
                "SymPy checked only the scaling identity d_k / (sqrt(d_k))^2 = 1."
            )
            plain = _attention_reading(local)
            intuition = ATTENTION_INTUITION
        elif attention:
            note = "Extracted from the paper. The full attention equation was not symbolically verified. Derivation checks are unavailable."
            plain = _attention_reading(local)
            intuition = ATTENTION_INTUITION
        else:
            note = "Source equation extracted; derivation not available. Not symbolically verified."
            plain = "Source equation extracted. A plain-English reading is not available for this expression."
            intuition = ""
        if attention:
            steps[0].explanation = plain
        block = DerivationBlock(
            equation_id=str(uuid4()),
            official_latex=latex,
            symbol_dependencies=[item["symbol"] for item in local],
            steps=steps,
            section_name=section,
            page=page,
            source_text=payload.get("source_text") or latex,
            verification_note=note,
            equation_number=str(payload["equation_number"]) if payload.get("equation_number") is not None else None,
            plain_explanation=plain,
            intuition=intuition,
            verification_status=verification_status,
            explained_symbols=local,
        )
        equations.append(block.model_dump())
        for annotated in local:
            existing = next((item for item in symbols if item["symbol"] == annotated["symbol"]), None)
            if existing is None:
                symbols.append(annotated)
            elif existing.get("status") != "defined" and annotated.get("status") == "defined":
                symbols[symbols.index(existing)] = annotated
    return equations, symbols
