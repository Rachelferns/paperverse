from paperverse.pipeline.stages.math_engine import explain_equations


def test_does_not_invent_attention_for_unrelated_text():
    equations, _symbols = explain_equations([])
    assert equations == []


def test_preserves_official_latex_and_does_not_claim_verification():
    extracted = [{
        "official_latex": r"L = \alpha L_{cls} + \beta L_{reg}",
        "source_text": "L = alpha L_cls + beta L_reg",
        "section_name": "Loss",
        "page": 3,
    }]
    equations, symbols = explain_equations(extracted)
    assert len(equations) == 1
    block = equations[0]
    assert block["official_latex"] == r"L = \alpha L_{cls} + \beta L_{reg}"
    assert block["page"] == 3
    assert block["section_name"] == "Loss"
    assert block["steps"][0]["is_intermediate_derived"] is False
    assert block["steps"][0]["sympy_verified"] is False
    assert "not symbolically verified" in block["verification_note"].lower()
    names = {item["symbol"] for item in symbols}
    assert "L_{cls}" in names or "L_cls" in names or "L" in names
    assert not any(len(item["symbol"]) == 1 and item["symbol"].islower() for item in symbols)
    assert all(item["dimensions"] != "Unknown" for item in symbols)
    assert all(item["status"] == "occurrence" for item in symbols)
    assert "definition was not extracted" in symbols[0]["definition"].lower()
    assert all(step["sympy_verified"] is False for step in block["steps"])
    assert block["verification_status"] == "extracted_only"


def test_attention_equation_explains_roles_without_verifying_the_full_formula():
    extracted = [{
        "official_latex": r"\mathrm{Attention}(Q, K, V) = \mathrm{softmax}(QK^{T} / \sqrt{d_k}) V",
        "source_text": "Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V",
        "section_name": "Attention",
        "page": 4,
        "equation_number": "1",
        "context": "An attention function maps a query and a set of key-value pairs to an output. We call the queries Q, the keys K, and the values V. Scores are scaled by the key dimension.",
    }]
    equations, symbols = explain_equations(extracted)
    block = equations[0]
    assert block["equation_number"] == "1"
    assert block["page"] == 4
    assert "softmax" in block["plain_explanation"].lower()
    assert "dot product" in block["plain_explanation"].lower()
    assert block["steps"][0]["sympy_verified"] is False
    assert block["steps"][0]["is_intermediate_derived"] is False
    checked = [step for step in block["steps"] if step["sympy_verified"]]
    assert len(checked) == 1
    assert checked[0]["is_intermediate_derived"] is True
    assert block["verification_status"] == "partially_checked"
    assert "not symbolically verified" in block["verification_note"].lower()
    by_symbol = {item["symbol"]: item for item in symbols}
    assert by_symbol["Q"]["status"] == "defined"
    assert by_symbol["K"]["status"] == "defined"
    assert by_symbol["V"]["status"] == "defined"
