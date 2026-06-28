"""teach-html-opencode end-to-end demo.

Reads examples/photosynthesis/teach-html-src/ch01.md, injects diagrams
(mermaid + image + chart), builds the HTML, validates it, and prints
a per-model token cost report in USD and INR.

Run from the project root:
    python3 examples/photosynthesis/build_demo.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
SKILL = PROJECT / "skill"
SRC = ROOT / "teach-html-src"
OUT_HTML = ROOT / "photosynthesis.html"
sys.path.insert(0, str(SKILL / "scripts"))

from inject_diagrams import inject_diagrams, mermaid_ensure_local  # noqa: E402

# USD -> INR rate (as of session; pinned for the report)
USD_INR = 83.0


def openrouter_chat(prompt: str, model: str, key: str) -> dict:
    """Minimal openrouter chat call. Returns parsed JSON."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
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
        return json.loads(resp.read())


# ---------- demo LLM spec picker ------------------------------------------
# Hand-curated specs for the 3 slots. Cycles through all 3 diagram types
# so the demo exercises every renderer.

DEMO_SPECS = [
    {  # after paragraph 2 — process flowchart
        "type": "mermaid",
        "content": (
            "flowchart LR\n"
            "  H2O[Water] --> PSII[Photosystem II]\n"
            "  PSII --> ETC[Electron transport chain]\n"
            "  ETC --> PSI[Photosystem I]\n"
            "  PSI --> NADPH[NADPH]\n"
            "  PSII --> O2[O2]\n"
            "  NADPH --> CB[Calvin-Benson cycle]\n"
            "  CO2[CO2] --> CB\n"
            "  CB --> Sugar[Glucose]"
        ),
        "alt": "Two-stage photosynthesis: light reactions split water and produce ATP/NADPH, which power the Calvin-Benson cycle to fix CO2 into sugar.",
    },
    {  # after paragraph 5 — image of chloroplast
        "type": "image",
        "content": (
            "cross-section of a plant chloroplast showing outer membrane, inner "
            "membrane, stroma, and a stack of thylakoid membranes called a granum, "
            "flat 2D editorial illustration, no text, no labels, no letters, no "
            "watermark, no background detail, white background, 1:1"
        ),
        "alt": "Chloroplast cross-section with thylakoid stacks (grana) embedded in the stroma, enclosed by inner and outer membranes.",
    },
    {  # after paragraph 8 — absorption spectrum chart
        "type": "chart",
        "content": json.dumps({
            "kind": "line",
            "title": "Chlorophyll absorption spectrum (relative)",
            "labels": ["400", "430", "460", "490", "520", "550", "580", "610", "640", "670", "700"],
            "values": [0.45, 0.92, 0.70, 0.18, 0.10, 0.20, 0.18, 0.20, 0.45, 0.85, 0.30],
        }),
        "alt": "Line chart showing chlorophyll absorption peaks in the blue (~430 nm) and red (~660 nm) regions, with a green trough in between.",
    },
]


def demo_llm_fn(prompt: str, slot_index: int = 0) -> dict:
    """Cycle through DEMO_SPECS regardless of prompt. Real LLM would read
    the prose and pick. We just demonstrate the wiring."""
    return DEMO_SPECS[slot_index % len(DEMO_SPECS)]


def main() -> int:
    # 0. ensure mermaid bundle
    mermaid_ensure_local()
    print(f"[1/5] mermaid bundle ready")

    # 1. read source
    src_md = (SRC / "ch01.md").read_text()
    print(f"[2/5] source chapter: {len(src_md.split())} words")

    # 2. inject diagrams — wrap the demo llm_fn with slot-index state
    state = {"i": 0}
    def llm(prompt: str) -> dict:
        s = DEMO_SPECS[state["i"] % len(DEMO_SPECS)]
        state["i"] += 1
        return s

    cost_log = []
    api_key = os.environ.get("OPENROUTER_API_KEY") or _extract_key()
    try:
        augmented, summary = inject_diagrams(
            src_md, every=3, llm_fn=llm, api_key=api_key, cost_log=cost_log,
        )
    except Exception as e:
        print(f"  WARN: image slot failed ({e}); continuing with mermaid+chart only")
        # remove the image spec, retry
        for s in DEMO_SPECS:
            if s["type"] == "image":
                s["type"] = "chart"
                s["content"] = json.dumps({
                    "kind": "bar",
                    "title": "Photosystem distribution (relative)",
                    "labels": ["PSII grana", "PSI stroma", "ATP synthase", "RuBisCO"],
                    "values": [70, 50, 30, 100],
                })
                s["alt"] = "Relative abundance of key photosynthetic proteins."
        state["i"] = 0
        augmented, summary = inject_diagrams(
            src_md, every=3, llm_fn=llm, api_key=None, cost_log=cost_log,
        )

    (SRC / "ch01.md").write_text(augmented)
    print(f"[3/5] injected {summary['slots']} diagrams: {summary['by_type']}")

    # 3. build html
    out_html = str(OUT_HTML)
    import subprocess
    res = subprocess.run(
        ["python3", str(SKILL / "scripts" / "build.py"),
         str(SRC), str(SKILL / "templates"), out_html],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print("BUILD FAILED:", res.stderr)
        return 1
    print(f"[4/5] built: {out_html}")

    # 4. validate
    res = subprocess.run(
        ["python3", str(SKILL / "scripts" / "validate.py"), out_html],
        capture_output=True, text=True,
    )
    print(f"[5/5] validate: {res.stdout.strip()}")

    # 5. cost report
    print_cost_report(cost_log, summary)

    return 0


def print_cost_report(cost_log: list, summary: dict) -> None:
    print()
    print("=" * 60)
    print("COST REPORT")
    print("=" * 60)
    by_model: dict = summary.get("usage_by_model", {})
    if not by_model:
        print("  (no API calls — mermaid + chart only)")
        return
    print(f"{'model':<48} {'prompt':>8} {'completion':>12} {'USD':>8} {'INR':>10}")
    print("-" * 90)
    for model, u in by_model.items():
        usd = float(u.get("cost") or 0.0)
        inr = usd * USD_INR
        print(f"{model:<48} {u.get('prompt_tokens', 0):>8} {u.get('completion_tokens', 0):>12} "
              f"{usd:>8.4f} {inr:>10.2f}")
    total_usd = sum(float(u.get("cost") or 0.0) for u in by_model.values())
    print("-" * 90)
    print(f"{'TOTAL':<48} {'':>8} {'':>12} {total_usd:>8.4f} {total_usd * USD_INR:>10.2f}")


def _extract_key() -> str | None:
    p = Path.home() / ".hermes" / ".env"
    if not p.exists():
        return None
    for line in p.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


if __name__ == "__main__":
    sys.exit(main())
