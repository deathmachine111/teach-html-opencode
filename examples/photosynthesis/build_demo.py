"""teach-html-opencode end-to-end demo (v1.1).

Reads examples/photosynthesis/teach-html-src/ch01.md, injects diagrams
(mermaid + image + chart, every 2 paragraphs = 6 slots), builds the HTML,
validates it, and prints a per-model token cost report in USD and INR.

v1.1 changes:
  - diagram density: every 2 paragraphs (was every 3)
  - images: labeled journal figures with named parts and callouts
  - 6 diagram slots, mixed types (mermaid / image / chart)
  - ch01.md rewritten in tables+bullets-first style

Run from the project root:
    python3 examples/photosynthesis/build_demo.py
"""
from __future__ import annotations

import json
import os
import subprocess
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

USD_INR = 83.0


# ---------- 6 hand-curated specs (v1.1) ------------------------------------
# Cycled through the 6 doublet slots. Mix of all 3 render types.
# Image specs use the v1.1 style suffix: labeled journal figures with
# named parts and callouts (no more "no text, no labels").

DEMO_SPECS = [
    {
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
    {
        "type": "image",
        "content": (
            "labeled cross-section diagram of a plant chloroplast with named parts: "
            "outer membrane, inner membrane, stroma, thylakoid stack (granum), "
            "stroma lamellae, thylakoid lumen, with arrows pointing to each label, "
            "flat 2D editorial medical illustration, clean line art, white background, "
            "no watermark, 1:1"
        ),
        "alt": "Labeled cross-section of a plant chloroplast with thylakoid stacks (grana) embedded in the stroma, enclosed by inner and outer membranes.",
    },
    {
        "type": "mermaid",
        "content": (
            "flowchart LR\n"
            "  CO2[CO2] --> Fix[1. Carbon fixation]\n"
            "  Fix -->|3-PGA| Red[2. Reduction]\n"
            "  Red -->|G3P| Reg[3. Regeneration]\n"
            "  Reg -->|RuBP| Fix\n"
            "  Red -->|G3P| Out[Glucose + biomass]\n"
            "  ATP[ATP] --> Red\n"
            "  ATP --> Reg\n"
            "  NADPH[NADPH] --> Red"
        ),
        "alt": "Three-stage Calvin-Benson cycle: CO2 fixation by RuBisCO produces 3-PGA, which is reduced to G3P using ATP and NADPH; some G3P exits as sugar while the rest regenerates RuBP using more ATP.",
    },
    {
        "type": "chart",
        "content": json.dumps({
            "kind": "line",
            "title": "Chlorophyll absorption spectrum (relative)",
            "labels": ["400", "430", "460", "490", "520", "550", "580", "610", "640", "670", "700"],
            "values": [0.45, 0.92, 0.70, 0.18, 0.10, 0.20, 0.18, 0.20, 0.45, 0.85, 0.30],
        }),
        "alt": "Line chart showing chlorophyll absorption peaks in the blue (~430 nm) and red (~660 nm) regions, with a green trough in between.",
    },
    {
        "type": "image",
        "content": (
            "side-by-side labeled comparison of C3 and C4 leaf cross-sections: "
            "C3 leaf labeled with mesophyll cells, palisade, spongy mesophyll, "
            "vascular bundle; C4 leaf labeled with mesophyll cells, bundle-sheath "
            "cells around the vascular bundle, Kranz anatomy highlighted, "
            "flat 2D editorial medical illustration, clean line art, "
            "white background, no watermark, 1:1"
        ),
        "alt": "Labeled comparison of C3 and C4 leaf cross-sections. C4 has prominent bundle-sheath cells surrounding the vascular bundle (Kranz anatomy), which C3 lacks.",
    },
    {
        "type": "chart",
        "content": json.dumps({
            "kind": "bar",
            "title": "Radiation use efficiency (g biomass per MJ PAR)",
            "labels": ["C3 (wheat)", "C4 (maize)", "CAM (agave)"],
            "values": [1.2, 1.7, 2.5],
        }),
        "alt": "Bar chart comparing radiation use efficiency: C3 wheat ~1.2, C4 maize ~1.7, CAM agave ~2.5 grams of biomass per megajoule of photosynthetically active radiation.",
    },
]


def demo_llm_fn(prompt: str, slot_index: int = 0) -> dict:
    return DEMO_SPECS[slot_index % len(DEMO_SPECS)]


def main() -> int:
    mermaid_ensure_local()
    print("[1/5] mermaid bundle ready")

    src_path = SRC / "ch01.md"
    src_md = src_path.read_text()
    print(f"[2/5] source chapter: {len(src_md.split())} words")

    cost_log: list = []
    api_key = os.environ.get("OPENROUTER_API_KEY") or _extract_key()

    state = {"i": 0}
    def llm(prompt: str) -> dict:
        s = DEMO_SPECS[state["i"] % len(DEMO_SPECS)]
        state["i"] += 1
        return s

    augmented, summary = inject_diagrams(
        src_md, every=2, llm_fn=llm, api_key=api_key, cost_log=cost_log,
    )
    aug_path = SRC / "ch01.augmented.md"
    aug_path.write_text(augmented)
    print(f"[3/5] injected {summary['slots']} diagrams: {summary['by_type']} -> {aug_path.name}")

    out_html = str(OUT_HTML)
    # Build the HTML from a build dir containing the AUGMENTED chapter
    # (so the <figure> blocks survive) plus meta.json + references.md
    # copied from the clean source dir.
    import shutil
    build_dir = SRC / "_build"
    build_dir.mkdir(exist_ok=True)
    shutil.copy(aug_path, build_dir / "ch01.md")
    for sidecar in ("meta.json", "references.md"):
        src_side = SRC / sidecar
        if src_side.exists():
            shutil.copy(src_side, build_dir / sidecar)
    res = subprocess.run(
        ["python3", str(SKILL / "scripts" / "build.py"),
         str(build_dir), str(SKILL / "templates"), out_html],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print("BUILD FAILED:", res.stderr)
        return 1
    print(f"[4/5] built: {out_html}")

    res = subprocess.run(
        ["python3", str(SKILL / "scripts" / "validate.py"), out_html],
        capture_output=True, text=True,
    )
    print(f"[5/5] validate: {res.stdout.strip()}")

    print_cost_report(cost_log, summary)
    return 0


def print_cost_report(cost_log: list, summary: dict) -> None:
    print()
    print("=" * 60)
    print("COST REPORT (v1.1 demo)")
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
