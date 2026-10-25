"""Unit tests for Stage 2: Math Engine."""
import pytest


# ---------------------------------------------------------------------------
# SymPy runner
# ---------------------------------------------------------------------------

def test_sympy_runner_passes_valid_script():
    from paperverse.pipeline.stages.math_engine import run_sympy_script
    # Use the same assertion style as production scripts: compare via sympy.simplify
    # The restricted builtins allow int, so == 1 works for a confirmed identity.
    script = (
        "import sympy as sp\n"
        "d_k = sp.symbols('d_k', positive=True)\n"
        "variance_ratio = (sp.sqrt(d_k)**2) / d_k\n"
        "assert sp.simplify(variance_ratio) == 1\n"
    )
    assert run_sympy_script(script) is True


def test_sympy_runner_fails_invalid_assertion():
    from paperverse.pipeline.stages.math_engine import run_sympy_script
    script = (
        "import sympy as sp\n"
        "assert 1 == 2\n"
    )
    assert run_sympy_script(script) is False


def test_sympy_runner_returns_false_for_empty_script():
    from paperverse.pipeline.stages.math_engine import run_sympy_script
    assert run_sympy_script("") is False


def test_sympy_runner_returns_false_for_no_automated_comment():
    from paperverse.pipeline.stages.math_engine import run_sympy_script
    assert run_sympy_script("# No automated check") is False


# ---------------------------------------------------------------------------
# JSON response cleaning
# ---------------------------------------------------------------------------

def test_clean_json_response_plain_array():
    from paperverse.pipeline.stages.math_engine import _clean_json_response
    raw = '[{"equation_id": "Eq_1", "original_latex": "x=1"}]'
    result = _clean_json_response(raw)
    assert result is not None
    assert len(result) == 1
    assert result[0]["equation_id"] == "Eq_1"


def test_clean_json_response_fenced_json():
    from paperverse.pipeline.stages.math_engine import _clean_json_response
    raw = '```json\n[{"equation_id": "Eq_2"}]\n```'
    result = _clean_json_response(raw)
    assert result is not None
    assert result[0]["equation_id"] == "Eq_2"


def test_clean_json_response_single_object():
    from paperverse.pipeline.stages.math_engine import _clean_json_response
    raw = '{"equation_id": "Eq_3", "original_latex": "y=2"}'
    result = _clean_json_response(raw)
    assert result is not None
    assert isinstance(result, list)
    assert result[0]["equation_id"] == "Eq_3"


def test_clean_json_response_invalid_returns_none():
    from paperverse.pipeline.stages.math_engine import _clean_json_response
    assert _clean_json_response("not json at all") is None


# ---------------------------------------------------------------------------
# Rule-based pipeline
# ---------------------------------------------------------------------------

def test_rule_based_attention_paper():
    from paperverse.pipeline.stages.math_engine import _rule_based_pipeline
    results = _rule_based_pipeline("This paper describes the attention mechanism and transformer.", [])
    eq_ids = [r["equation_id"] for r in results]
    assert "Eq_Attention" in eq_ids


def test_rule_based_loss_paper():
    from paperverse.pipeline.stages.math_engine import _rule_based_pipeline
    results = _rule_based_pipeline("We minimize a cross-entropy loss and regression objective.", [])
    eq_ids = [r["equation_id"] for r in results]
    assert "Eq_Loss" in eq_ids


def test_rule_based_always_returns_at_least_one():
    from paperverse.pipeline.stages.math_engine import _rule_based_pipeline
    results = _rule_based_pipeline("Completely unrelated paper about gardening.", [])
    assert len(results) >= 1


def test_rule_based_includes_extracted_equations():
    from paperverse.pipeline.stages.math_engine import _rule_based_pipeline
    extracted = [r"y = mx + b"]
    results = _rule_based_pipeline("Linear regression", extracted)
    latexes = [r["original_latex"] for r in results]
    assert r"y = mx + b" in latexes


# ---------------------------------------------------------------------------
# Public explain_equations
# ---------------------------------------------------------------------------

def test_explain_equations_returns_tuple_of_lists():
    from paperverse.pipeline.stages.math_engine import explain_equations
    equations, symbols = explain_equations([], "simple paper context")
    assert isinstance(equations, list)
    assert isinstance(symbols, list)


def test_explain_equations_normalizes_steps():
    from paperverse.pipeline.stages.math_engine import explain_equations
    equations, _ = explain_equations([], "attention transformer softmax")
    for eq in equations:
        for step in eq.get("step_by_step_derivation", []):
            assert "step_number" in step
            assert "latex" in step
            assert "explanation" in step
            assert isinstance(step["sympy_verified"], bool)


def test_explain_equations_verification_note_set():
    from paperverse.pipeline.stages.math_engine import explain_equations
    equations, _ = explain_equations([], "attention transformer")
    for eq in equations:
        assert "verification_note" in eq
        assert isinstance(eq["verification_note"], str)
        assert len(eq["verification_note"]) > 0


def test_explain_equations_sympy_verified_flag_honest():
    """sympy_verified must be True only when the script actually passed."""
    from paperverse.pipeline.stages.math_engine import explain_equations, run_sympy_script
    equations, _ = explain_equations([], "attention transformer softmax")
    for eq in equations:
        script = eq.get("sympy_verification_script", "")
        expected = run_sympy_script(script)
        for step in eq.get("step_by_step_derivation", []):
            assert step["sympy_verified"] == expected
