"""Diagram auto-injection for teach-html chapters.

Strategy: walk chapter, every N paragraphs mark a slot; LLM picks type+spec;
render to inline HTML/SVG/data URI; splice into the chapter content.

Public API:
    split_paragraphs(md: str) -> list[str]
    mark_slots(paragraphs, every=3) -> list[Slot]
    pick_spec(slot, llm_fn) -> Spec
    render_mermaid(spec) -> str (inline SVG via playwright)
    render_image(spec, *, api_key) -> str (<img data:>)
    render_chart(spec) -> str (inline HTML/CSS primitive)
    inject_diagrams(md, *, every=3, llm_fn, api_key=None) -> str

Kept stdlib + already-installed (markdown, bs4, requests optional, playwright).
Network calls (image) gated on api_key so tests can run offline.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Callable, Optional

# -------- data --------------------------------------------------------------

@dataclass
class Slot:
    """Insertion target: the N paragraphs of prose that justify one diagram."""
    after_para: int          # paragraph index the diagram should follow
    paragraphs: list[str]    # the supporting paragraphs (== 1 triplet if every=3)


@dataclass
class Spec:
    type: str                # 'mermaid' | 'image' | 'chart'
    content: str             # mermaid syntax / image prompt / chart data
    alt: str = ""            # accessibility text


# -------- paragraph ops -----------------------------------------------------

_PARA_SPLIT = re.compile(r"\n\s*\n")


def split_paragraphs(md: str) -> list[str]:
    """Split markdown into top-level paragraphs (blank-line separated).

    Headings count as paragraphs. Code fences stay attached to their containing
    paragraph if they precede/follow inline. Lists as single paragraphs.
    """
    md = md.strip()
    if not md:
        return []
    return [p.strip() for p in _PARA_SPLIT.split(md) if p.strip()]


def mark_slots(paragraphs: list[str], every: int = 3) -> list[Slot]:
    """Mark slot after every `every` paragraphs (1-indexed boundary).

    Only marks a slot if the trailing group has at least `every` paragraphs.
    A trailing group of 1-2 paragraphs yields no slot (would fragment the
    chapter with a diagram right at the end).
    """
    if every < 1:
        raise ValueError("every must be >= 1")
    slots = []
    n = len(paragraphs)
    for boundary in range(every, n + 1, every):
        if n - boundary < 1 or n - boundary >= every:
            # still mark full triplets
            pass
        if boundary == n:
            # Don't insert a diagram at the very end of the chapter
            continue
        slots.append(Slot(
            after_para=boundary - 1,
            paragraphs=paragraphs[boundary - every:boundary],
        ))
    return slots


# -------- LLM pick (testable) -----------------------------------------------

def pick_spec(slot: Slot, llm_fn: Callable[[str], dict]) -> Spec:
    """Call the LLM with the slot text; parse its JSON choice into a Spec.

    `llm_fn(prompt: str) -> dict` is the seam for tests (pass a stub).
    Expected JSON: {"type": "mermaid|image|chart", "content": "...", "alt": "..."}
    """
    prompt = _build_pick_prompt(slot)
    raw = llm_fn(prompt)
    if isinstance(raw, str):
        raw = json.loads(raw)
    t = raw.get("type", "").strip().lower()
    if t not in ("mermaid", "image", "chart"):
        raise ValueError(f"llm returned invalid type: {t!r}")
    return Spec(
        type=t,
        content=raw["content"],
        alt=raw.get("alt", "").strip(),
    )


def _build_pick_prompt(slot: Slot) -> str:
    body = "\n\n".join(slot.paragraphs)
    return textwrap.dedent(f"""\
        You design diagrams that augment prose. Choose ONE type and write the spec.

        Types:
        - "mermaid": write valid Mermaid syntax (flowchart, sequence, mindmap, timeline, etc.)
        - "image":   a 1-sentence prompt for an editorial-medical illustration.
                     LABELS ARE ENCOURAGED: name parts, add callouts, use arrows
                     with text, label axes. This is a journal-figure, not a stock photo.
                     Single concept, consistent flat 2D style — see suffix below.
        - "chart":   JSON {{"kind": "bar|line|pie", "title": "...", "labels": [...], "values": [...]}}

        IMAGE STYLE RULES (apply to every image spec):
        - One concept per image, named in the prompt (e.g. "a mitochondrion with labeled cristae", not "a cell scene")
        - ENCOURAGED: callouts, named parts, arrows with text, axis labels, legend entries
        - AVOID: photorealism, complex backgrounds, multiple competing subjects
        - Append the fixed suffix: "{_IMAGE_STYLE_SUFFIX}"
        - Subject first, then any specific labels, then the style suffix

        Reply with ONLY valid JSON: {{"type": "...", "content": "...", "alt": "..."}}

        Prose to augment:
        ---
        {body}
        ---
        """)


# -------- renderers ---------------------------------------------------------

def render_mermaid(spec: Spec, *, engine: str = "auto") -> str:
    """Render mermaid spec to inline SVG.

    engine="auto" picks playwright if installed, else mmdc CLI.
    Returns a <figure> wrapper with the SVG and alt text.
    """
    if spec.type != "mermaid":
        raise ValueError(f"render_mermaid called with type={spec.type}")
    if engine == "playwright" or engine == "auto":
        try:
            return _render_mermaid_playwright(spec)
        except Exception as e:
            if engine == "playwright":
                raise
            # auto → fall back to mmdc
            return _render_mermaid_mmdc(spec)
    return _render_mermaid_mmdc(spec)


def _render_mermaid_playwright(spec: Spec) -> str:
    """Render mermaid via playwright + locally-bundled mermaid.js (offline-safe).

    If the local bundle is missing, raise so the caller can fall back to mmdc.
    The local bundle is downloaded once via `mermaid_ensure_local()`.
    """
    from playwright.sync_api import sync_playwright  # type: ignore
    js_path = mermaid_js_path()
    if not js_path:
        raise FileNotFoundError(
            "mermaid.js not found at ~/.cache/teach-html/mermaid.min.js "
            "— run mermaid_ensure_local() first"
        )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content("<!doctype html><html><body><div id='out'></div></body></html>",
                             wait_until="domcontentloaded")
            # add_script_tag(path=...) is a sync file:// load — mermaid is
            # available on the page immediately after this returns
            page.add_script_tag(path=js_path)
            # Initialize and render; check at each step
            page.evaluate("mermaid.initialize({startOnLoad:false, theme:'neutral', securityLevel:'strict'})")
            svg = page.evaluate(
                "async (src) => { const r = await mermaid.render('g', src); return r.svg; }",
                spec.content,
            )
        finally:
            browser.close()
    alt_attr = f' role="img" aria-label="{_esc(spec.alt)}"' if spec.alt else ""
    return f'<figure class="diagram diagram-mermaid"{alt_attr}>{svg}</figure>'


def _render_mermaid_mmdc(spec: Spec) -> str:
    """Fallback: mmdc CLI (uses puppeteer)."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as f:
        f.write(spec.content)
        mmd_path = f.name
    svg_path = mmd_path + ".svg"
    puppeteer = os.path.expanduser("~/.cache/ms-playwright/chromium-1217/chrome-linux/chrome")
    cmd = ["npx", "--no-install", "mmdc", "-i", mmd_path, "-o", svg_path, "-q"]
    if os.path.exists(puppeteer):
        cmd += ["-p", f'{{"executablePath": "{puppeteer}"}}']
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        svg = open(svg_path, encoding="utf-8").read()
    finally:
        for p in (mmd_path, svg_path):
            if os.path.exists(p):
                os.unlink(p)
    alt_attr = f' role="img" aria-label="{_esc(spec.alt)}"' if spec.alt else ""
    return f'<figure class="diagram diagram-mermaid"{alt_attr}>{svg}</figure>'


def render_image(spec: Spec, *, api_key: Optional[str] = None,
                 model: str = "google/gemini-3.1-flash-image-preview",
                 low_res: int = 512) -> str:
    """Render image spec via openrouter. Returns <img data:...>.

    `low_res` is the target image dimension; model gets image_size hint.
    Tracks token cost on the returned object via .cost attribute (post-render).
    """
    if spec.type != "image":
        raise ValueError(f"render_image called with type={spec.type}")
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY required for image diagrams")
    import urllib.request
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": spec.content}],
        "modalities": ["image", "text"],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read())
    imgs = payload.get("choices", [{}])[0].get("message", {}).get("images") or []
    if not imgs:
        raise RuntimeError("gemini returned no image")
    url = imgs[0]["image_url"]["url"]
    usage = payload.get("usage", {})
    # stamp cost onto a wrapper so orchestrator can accumulate
    return _ImageFragment(html=_img_tag(url, spec.alt), usage=usage)


@dataclass
class _ImageFragment:
    html: str
    usage: dict = field(default_factory=dict)


def _img_tag(data_uri: str, alt: str) -> str:
    return f'<figure class="diagram diagram-image"><img src="{data_uri}" alt="{_esc(alt)}" loading="lazy"></figure>'


def render_chart(spec: Spec) -> str:
    """Render chart spec (JSON in spec.content) to inline HTML/CSS.

    Supported kinds: bar (horizontal), line, pie. No JS deps.
    """
    if spec.type != "chart":
        raise ValueError(f"render_chart called with type={spec.type}")
    data = json.loads(spec.content) if isinstance(spec.content, str) else spec.content
    kind = data.get("kind", "bar")
    title = data.get("title", "")
    labels = data.get("labels", [])
    values = [float(v) for v in data.get("values", [])]
    if kind == "bar":
        body = _chart_bar(labels, values)
    elif kind == "line":
        body = _chart_line(labels, values)
    elif kind == "pie":
        body = _chart_pie(labels, values)
    else:
        raise ValueError(f"unknown chart kind: {kind}")
    cap = f'<figcaption>{_esc(title)}</figcaption>' if title else ''
    return f'<figure class="diagram diagram-chart diagram-chart-{kind}">{body}{cap}</figure>'


def _chart_bar(labels, values) -> str:
    if not values:
        return ''
    mx = max(values) or 1.0
    rows = "".join(
        f'<div class="bar-row"><span class="bar-label">{_esc(l)}</span>'
        f'<span class="bar-track"><span class="bar-fill" style="width:{(v/mx)*100:.1f}%"></span></span>'
        f'<span class="bar-value">{v:g}</span></div>'
        for l, v in zip(labels, values)
    )
    return f'<div class="chart chart-bar">{rows}</div>'


def _chart_line(labels, values) -> str:
    if not values or len(values) < 2:
        return ''
    w, h = 600, 200
    pad = 24
    x0, y0 = pad, h - pad
    x1, y1 = w - pad, pad
    minv, maxv = min(values), max(values)
    rng = (maxv - minv) or 1.0
    pts = []
    for i, v in enumerate(values):
        x = x0 + (x1 - x0) * (i / (len(values) - 1))
        y = y0 - (y0 - y1) * ((v - minv) / rng)
        pts.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(pts)
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" class="line-dot"></circle>'
        for (x, y), l in zip(
            [(float(p.split(',')[0]), float(p.split(',')[1])) for p in pts], labels
        )
    )
    labels_svg = "".join(
        f'<text x="{x0 + (x1-x0)*(i/(len(values)-1)):.1f}" y="{h-6}" '
        f'class="line-label">{_esc(l)}</text>'
        for i, l in enumerate(labels)
    )
    return (
        f'<svg class="chart chart-line" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{polyline}" class="line-path"/>'
        f'{dots}{labels_svg}</svg>'
    )


def _chart_pie(labels, values) -> str:
    if not values:
        return ''
    total = sum(values) or 1.0
    # simple SVG pie (12 o'clock start, clockwise)
    import math
    cx, cy, r = 80, 80, 70
    segs = []
    a0 = -math.pi / 2
    for v in values:
        a1 = a0 + 2 * math.pi * (v / total)
        large = 1 if (a1 - a0) > math.pi else 0
        x0 = cx + r * math.cos(a0); y0 = cy + r * math.sin(a0)
        x1 = cx + r * math.cos(a1); y1 = cy + r * math.sin(a1)
        segs.append(
            f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} '
            f'A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" '
            f'class="pie-seg" data-pct="{100*v/total:.1f}"/>'
        )
        a0 = a1
    legend = "".join(
        f'<li><span class="pie-sw" style="background:var(--c{i%8})"></span>{_esc(l)} ({v:g})</li>'
        for i, (l, v) in enumerate(zip(labels, values))
    )
    return (
        f'<div class="chart chart-pie-wrap">'
        f'<svg viewBox="0 0 160 160" class="chart chart-pie">{"".join(segs)}</svg>'
        f'<ul class="pie-legend">{legend}</ul></div>'
    )


# -------- inject orchestrator ------------------------------------------------

def inject_diagrams(
    md: str,
    *,
    every: int = 2,
    llm_fn: Optional[Callable[[str], dict]] = None,
    api_key: Optional[str] = None,
    cost_log: Optional[list] = None,
) -> tuple[str, dict]:
    """Slot diagrams into markdown. Returns (new_md, cost_summary).

    Default `every=2` (v1.1) yields ~one diagram per two paragraphs — a
    visual-leaning, editorial-medical density. v0/v1 used 3; override here
    for text-heavy chapters.

    `llm_fn` is required (or pass a stub). For real use, wrap
    `openrouter_chat(model=...)` and pass it in.
    `cost_log` is appended with {model, type, usage} entries when set.
    """
    if llm_fn is None:
        raise ValueError("llm_fn is required")
    paragraphs = split_paragraphs(md)
    slots = mark_slots(paragraphs, every=every)
    rendered: list[tuple[int, str]] = []  # (after_para, html_fragment)
    summary = {"slots": 0, "by_type": {"mermaid": 0, "image": 0, "chart": 0},
               "usage_by_model": {}}
    for slot in slots:
        spec = pick_spec(slot, llm_fn)
        summary["slots"] += 1
        summary["by_type"][spec.type] += 1
        if spec.type == "mermaid":
            frag = render_mermaid(spec)
            usage = {"model": "mermaid-local", "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}
        elif spec.type == "image":
            frag = render_image(spec, api_key=api_key)
            usage = {"model": "google/gemini-3.1-flash-image-preview",
                     **(frag.usage if isinstance(frag, _ImageFragment) else {})}
            frag = frag.html if isinstance(frag, _ImageFragment) else frag
        else:  # chart
            frag = render_chart(spec)
            usage = {"model": "chart-local", "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}
        # accumulate cost
        for k in ("prompt_tokens", "completion_tokens", "cost"):
            summary["usage_by_model"].setdefault(usage["model"], {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0})
            summary["usage_by_model"][usage["model"]][k] += usage.get(k, 0)
        if cost_log is not None:
            cost_log.append(usage)
        rendered.append((slot.after_para, frag))
    new_md = _splice(paragraphs, rendered)
    return new_md, summary


def _splice(paragraphs: list[str], rendered: list[tuple[int, str]]) -> str:
    """Reassemble paragraphs with diagram fragments inserted after their slot."""
    by_pos = dict(rendered)
    out = []
    for i, p in enumerate(paragraphs):
        out.append(p)
        if i in by_pos:
            out.append("\n\n" + by_pos[i] + "\n\n")
    return "\n\n".join(out)


# -------- helpers -----------------------------------------------------------

def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


# Fixed style suffix appended to every image-generation prompt. Keeps all
# diagrams visually consistent (flat 2D editorial line art, white background,
# consistent strokes) while ENCOURAGING labels for journal-figure style.
# v1.1: dropped the strict "no text, no labels, no letters" rule — labels
# and callouts are now first-class citizens. See docs/IMAGE_PROMPTING.md.
_IMAGE_STYLE_SUFFIX = (
    "flat 2D editorial medical illustration, labeled diagram with named "
    "parts and callouts, clean line art, white background, no watermark, 1:1"
)


# Mermaid.js is loaded from a locally-cached file at render time. Download once:
#     curl -fsSL https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js \
#         -o ~/.cache/teach-html/mermaid.min.js
# The bundle is 3.3 MB; we keep it off the network for reproducibility + offline use.


def mermaid_js_path() -> str:
    """Return path to a local mermaid.js if cached on disk, else empty string."""
    p = os.path.expanduser("~/.cache/teach-html/mermaid.min.js")
    return p if os.path.exists(p) else ""


def mermaid_ensure_local() -> str:
    """Download mermaid.js to the local cache if not present. Returns the path."""
    import urllib.request
    dest = os.path.expanduser("~/.cache/teach-html/mermaid.min.js")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not os.path.exists(dest):
        urllib.request.urlretrieve(
            "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js", dest
        )
    return dest


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("chapter_md")
    p.add_argument("--every", type=int, default=2)
    p.add_argument("--out", default="-")
    args = p.parse_args()
    md = open(args.chapter_md).read()
    out, _ = inject_diagrams(md, every=args.every, llm_fn=lambda x: {"type": "chart", "content": '{"kind":"bar","title":"stub","labels":["a","b"],"values":[1,2]}', "alt": "stub"})
    if args.out == "-":
        sys.stdout.write(out)
    else:
        open(args.out, "w").write(out)
