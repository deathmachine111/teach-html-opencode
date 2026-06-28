# Demo results — photosynthesis module

**Input:** `examples/photosynthesis/teach-html-src/ch01.md` — 945 words, 9 paragraphs (3 triplets)

**Pipeline:**
1. `inject_diagrams(every=3)` — picks 1 mermaid, 1 image, 1 chart
2. `build.py` — compiles to single inlined HTML
3. `validate.py` — `OK: structurally valid`

**Output:** `examples/photosynthesis/photosynthesis.html` (~? KB, fully self-contained)
**Screenshot:** `examples/photosynthesis/screenshot.png`

## Diagrams injected

| Slot | Position (paragraph) | Type | What it shows |
|---|---|---|---|
| 1 | after p2 (end of triplet 1) | mermaid flowchart | light reactions → Calvin-Benson cycle |
| 2 | after p5 (end of triplet 2) | image (gen.) | chloroplast cross-section with thylakoid stacks |
| 3 | after p8 (end of triplet 3) | chart (line) | chlorophyll absorption spectrum (blue + red peaks) |

## Cost report

| Model | Prompt tokens | Completion tokens | USD | INR |
|---|---:|---:|---:|---:|
| mermaid-local (offline) | 0 | 0 | 0.0000 | 0.00 |
| google/gemini-3.1-flash-image-preview | 62 | 1,572 | 0.0686 | 5.69 |
| chart-local (offline) | 0 | 0 | 0.0000 | 0.00 |
| **TOTAL** | | | **0.0686** | **5.69** |

(USD→INR rate: 83.0; per-image cost includes ~1120 image tokens billed at preview rate.)

## Visual verification

See `screenshot.png`. Palette rendered as designed:
- Slate paper #F8FAFC canvas
- Deep green #166534 headings, sidebar, links
- Serif body, sans sidebar/labels, framed figures with italic captions
- All three diagram types rendered inline, no external deps
