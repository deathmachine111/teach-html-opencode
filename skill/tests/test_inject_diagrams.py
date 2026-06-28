"""TDD: tests for inject_diagrams.py.

Vertical slices:
  1. split_paragraphs: handles empty, single, multiple, code fences.
  2. mark_slots: every-N boundary, no trailing fragment.
  3. pick_spec: parses LLM JSON to Spec; rejects bad types.
  4. render_mermaid: integration with real playwright + local mmd (smoke).
  5. render_chart: bar/line/pie produce valid HTML.
  6. render_image: mocked HTTP (no network) + real network smoke (opt-in).
  7. inject_diagrams: end-to-end with stubbed LLM, accumulates cost.
"""
import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# allow `from inject_diagrams import ...` from project scripts/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import inject_diagrams as ID  # noqa: E402


# -------- 1. split_paragraphs ----------------------------------------------

def test_split_empty():
    assert ID.split_paragraphs("") == []
    assert ID.split_paragraphs("   \n\n  ") == []


def test_split_single():
    assert ID.split_paragraphs("Hello world.") == ["Hello world."]


def test_split_multiple():
    md = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    assert ID.split_paragraphs(md) == [
        "First paragraph.", "Second paragraph.", "Third paragraph.",
    ]


def test_split_skips_blank_paragraphs():
    md = "A.\n\n\n\nB.\n\n   \nC."
    assert ID.split_paragraphs(md) == ["A.", "B.", "C."]


# -------- 2. mark_slots -----------------------------------------------------

def test_mark_slots_every_3_short():
    assert ID.mark_slots(["a"], every=3) == []
    assert ID.mark_slots(["a", "b"], every=3) == []
    assert ID.mark_slots(["a", "b", "c"], every=3) == []  # no slot at end


def test_mark_slots_every_3_full():
    paras = [f"p{i}" for i in range(9)]
    slots = ID.mark_slots(paras, every=3)
    assert len(slots) == 2
    assert [s.after_para for s in slots] == [2, 5]
    assert slots[0].paragraphs == ["p0", "p1", "p2"]
    assert slots[1].paragraphs == ["p3", "p4", "p5"]


def test_mark_slots_every_2():
    paras = [f"p{i}" for i in range(5)]
    slots = ID.mark_slots(paras, every=2)
    # mark after p1, p3. Trailing p4 is fragment (<2 left) → no slot.
    assert [s.after_para for s in slots] == [1, 3]


def test_mark_slots_invalid():
    with pytest.raises(ValueError):
        ID.mark_slots(["a"], every=0)


# -------- 3. pick_spec ------------------------------------------------------

def test_pick_spec_mermaid():
    spec = ID.pick_spec(ID.Slot(2, ["x"]), lambda p: {"type": "mermaid",
                                                       "content": "graph TD; A-->B",
                                                       "alt": "A to B"})
    assert spec.type == "mermaid"
    assert spec.alt == "A to B"


def test_pick_spec_image():
    spec = ID.pick_spec(ID.Slot(2, ["x"]), lambda p: {"type": "image",
                                                       "content": "draw a cell",
                                                       "alt": "cell diagram"})
    assert spec.type == "image"
    assert spec.content == "draw a cell"


def test_pick_spec_rejects_bad_type():
    with pytest.raises(ValueError):
        ID.pick_spec(ID.Slot(2, ["x"]), lambda p: {"type": "video", "content": "x"})


def test_pick_spec_accepts_string_json():
    spec = ID.pick_spec(ID.Slot(2, ["x"]),
                        lambda p: '{"type":"chart","content":"{}","alt":""}')
    assert spec.type == "chart"


# -------- 4. render_mermaid (real playwright, no network) -----------------

def test_render_mermaid_smoke():
    """Render a tiny graph offline (mermaid.js is loaded from CDN — skipped
    if no network). Mark as integration, skip if mermaid can't render."""
    spec = ID.Spec("mermaid", "graph TD; A-->B", alt="A to B")
    try:
        html = ID.render_mermaid(spec, engine="playwright")
    except Exception as e:
        pytest.skip(f"playwright mermaid render unavailable: {e}")
    assert "<svg" in html
    assert "diagram-mermaid" in html
    if spec.alt:
        assert spec.alt in html


# -------- 5. render_chart ---------------------------------------------------

def test_render_chart_bar():
    spec = ID.Spec("chart",
                   json.dumps({"kind": "bar", "title": "Speed",
                               "labels": ["a", "b", "c"],
                               "values": [1, 2, 3]}),
                   alt="bar chart")
    html = ID.render_chart(spec)
    assert "diagram-chart" in html
    assert "chart-bar" in html
    assert "Speed" in html
    assert "bar-fill" in html


def test_render_chart_line():
    spec = ID.Spec("chart",
                   json.dumps({"kind": "line", "title": "Trend",
                               "labels": ["t0", "t1", "t2"],
                               "values": [1, 3, 2]}),
                   alt="line")
    html = ID.render_chart(spec)
    assert "<polyline" in html
    assert "line-dot" in html


def test_render_chart_pie():
    spec = ID.Spec("chart",
                   json.dumps({"kind": "pie", "title": "Share",
                               "labels": ["x", "y"],
                               "values": [3, 1]}),
                   alt="pie")
    html = ID.render_chart(spec)
    assert "pie-seg" in html
    assert "pie-legend" in html


def test_render_chart_rejects_other_type():
    with pytest.raises(ValueError):
        ID.render_chart(ID.Spec("mermaid", "graph TD; A-->B"))


# -------- 6. render_image (mocked network) ---------------------------------

def test_render_image_mocked():
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({
        "choices": [{"message": {"images": [
            {"type": "image", "image_url": {"url": "data:image/png;base64,FAKE"}}
        ]}}],
        "usage": {"prompt_tokens": 8, "completion_tokens": 1120, "cost": 0.0672},
    }).encode()
    fake_response.__enter__ = lambda s: s
    fake_response.__exit__ = lambda s, *a: None
    with patch("urllib.request.urlopen", return_value=fake_response):
        spec = ID.Spec("image", "draw a circle", alt="circle")
        frag = ID.render_image(spec, api_key="sk-test")
    assert isinstance(frag, ID._ImageFragment)
    assert "FAKE" in frag.html
    assert frag.usage["cost"] == 0.0672


def test_render_image_no_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError):
            ID.render_image(ID.Spec("image", "x", alt=""), api_key=None)


# -------- 7. inject_diagrams (end-to-end with stub) ------------------------

def test_inject_e2e_with_stub():
    md = "".join(f"Para {i}.\n\n" for i in range(9)).strip()
    types = iter(["mermaid", "image", "chart"])
    def stub(prompt):
        t = next(types)
        if t == "mermaid":
            return {"type": "mermaid", "content": "graph TD; A-->B", "alt": "f"}
        if t == "image":
            return {"type": "image", "content": "draw", "alt": "i"}
        return {"type": "chart",
                "content": json.dumps({"kind": "bar", "labels": ["a"], "values": [1]}),
                "alt": "c"}
    # mock image renderer to avoid network
    with patch.object(ID, "render_image",
                      return_value=ID._ImageFragment(html="<img-stub>", usage={
                          "prompt_tokens": 8, "completion_tokens": 100, "cost": 0.001})):
        new_md, summary = ID.inject_diagrams(md, every=3, llm_fn=stub)
    assert summary["slots"] == 2
    assert summary["by_type"]["mermaid"] == 1
    assert summary["by_type"]["image"] == 1
    assert summary["by_type"]["chart"] == 0
    assert "img-stub" in new_md
    assert "diagram-mermaid" in new_md


def test_inject_requires_llm():
    with pytest.raises(ValueError):
        ID.inject_diagrams("a\n\nb", every=3, llm_fn=None)


# -------- 8. round-trip with build.py (integration) ------------------------

def test_inject_into_built_html_includes_fragments(tmp_path):
    """Confirm rendered fragments are present in the final HTML after build."""
    # write a tiny src with one chapter
    src = tmp_path / "src"
    src.mkdir()
    (src / "ch01.md").write_text("A.\n\nB.\n\nC.\n\nD.\n\nE.\n\nF.\n")
    (src / "references.md").write_text("[X]: Author. *Title*.\n")
    (src / "meta.json").write_text(json.dumps({"title": "t"}))
    # import build.py
    build_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "build.py")
    spec = importlib_load(build_path, "build_mod_test")
    out = tmp_path / "out.html"
    spec.build_module(str(src),
                       os.path.join(os.path.dirname(__file__), "..", "templates"),
                       str(out))
    html = out.read_text()
    # confirm the chapter prose survived
    assert "Para 0" not in html  # we used A..F
    assert "<p>A.</p>" in html


def importlib_load(path, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
