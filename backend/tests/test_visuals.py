import re

from paperverse.pipeline.stages.visuals import ARCHITECTURE_MARKER, ARCHITECTURE_UNAVAILABLE, make_visual_artifacts


def _labels(diagram: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"%% component: [^|]+\| ([^|]+) \|", diagram)]


TRANSFORMER = """
The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers.
The first is a multi-head self-attention mechanism, and the second is a simple, position-wise fully connected feed-forward network.
We employ a residual connection around each of the two sub-layers, followed by layer normalization.
The decoder is also composed of a stack of identical layers.
The decoder inserts a third sub-layer, which performs multi-head attention over the output of the encoder stack.
We add positional encodings to the input embeddings at the bottoms of the encoder and decoder stacks.
Scaled dot-product attention computes compatibility between queries and keys.
"""


def test_architecture_uses_method_components_not_headings():
    sections = [
        {"title": "Abstract", "page": 1, "content": "We propose a new sequence model."},
        {"title": "Introduction", "page": 1, "content": "Recurrent models are sequential."},
        {"title": "Model Architecture", "page": 3, "content": TRANSFORMER},
        {"title": "Experiments", "page": 8, "content": "We report BLEU scores."},
    ]
    result = make_visual_artifacts(sections, "Attention Is All You Need", TRANSFORMER)
    diagram = result["diagram_mermaid"]
    labels = _labels(diagram)
    assert diagram.startswith(ARCHITECTURE_MARKER)
    assert "Abstract" not in labels
    assert "Introduction" not in labels
    assert "Model Architecture" not in labels
    assert "Experiments" not in labels
    assert "Multi-head attention" in labels
    assert "Encoder" in labels
    assert "Decoder" in labels
    assert "-->" in diagram


def test_missing_method_text_is_an_empty_state():
    sections = [
        {"title": "Abstract", "page": 1, "content": "This paper surveys public datasets."},
        {"title": "Discussion", "page": 4, "content": "More comparative work is needed."},
    ]
    result = make_visual_artifacts(sections, "A Survey", "This paper surveys public datasets.")
    diagram = result["diagram_mermaid"]
    assert diagram.startswith(ARCHITECTURE_UNAVAILABLE)
    assert "flowchart" not in diagram
    assert "Abstract" not in _labels(diagram)


def test_short_transformer_text_uses_only_named_layers():
    content = (
        "The Transformer uses stacked self-attention and pointwise fully connected layers. "
        "Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V"
    )
    result = make_visual_artifacts(
        [{"title": "2. Model Architecture", "page": 1, "content": content}],
        "Attention Is All You Need",
        content,
    )
    labels = _labels(result["diagram_mermaid"])
    assert labels == ["Self-attention", "Point-wise fully connected layer"]
    assert "Encoder" not in labels
    assert "Decoder" not in labels
    assert "self_attn --> pointwise" in result["diagram_mermaid"]


def test_component_list_is_not_a_transformer_diagram():
    sections = [{
        "title": "Proposed Method",
        "page": 2,
        "content": "The proposed model consists of a feature extractor, a fusion block, and a classifier.",
    }]
    result = make_visual_artifacts(sections, "Fusion", sections[0]["content"])
    labels = _labels(result["diagram_mermaid"])
    assert labels == ["Feature extractor", "Fusion block", "Classifier"]
    assert "-->" not in result["diagram_mermaid"]
    assert "Encoder" not in labels


def test_experiment_section_does_not_supply_the_diagram():
    sections = [
        {"title": "Model", "page": 2, "content": "We trained for ten epochs on paired sentences."},
        {"title": "Experiments", "page": 5, "content": "The encoder, decoder, and multi-head attention were ablated."},
    ]
    result = make_visual_artifacts(sections, "Probe", "")
    assert result["diagram_mermaid"].startswith(ARCHITECTURE_UNAVAILABLE)


def test_python_fence_is_preserved():
    text = "Before\n```python\nprint('from the paper')\n```\nAfter"
    result = make_visual_artifacts([], "Code Paper", text)
    assert result["python_code"] == "print('from the paper')"
    assert result["diagram_mermaid"].startswith(ARCHITECTURE_UNAVAILABLE)
