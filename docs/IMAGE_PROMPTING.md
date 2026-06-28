# Image Prompt Engineering for Educational & Scientific Diagrams

Sourced guidance for generating clean, single-concept, schematic visuals from text-to-image models (DALL·E 3, Gemini/Nano Banana, FLUX, Midjourney, Stable Diffusion).

---

## TL;DR — the 5-bullet checklist

1. **Name the style, not the topic.** Open every prompt with `[style: scientific diagram | vector line art | Nature journal style | schematic | editorial illustration]` before the subject.
2. **One concept per image.** State the single learning outcome in one sentence; forbid everything else.
3. **Specify "no text, no labels"** for the AI to draw, then overlay labels yourself in HTML/CSS/SVG. This eliminates ~90% of hallucinated text and misspellings.
4. **Anchor geometry, not adjectives.** Use "centered", "single object", "white background", "bold outlines ≥2pt", "no shadow". Skip "beautiful", "professional", "stunning".
5. **Cap prompt at 80–250 words, 3–5 visual concepts.** Beyond 300 the model starts truncating and contradicting itself.

---

## 1. Style anchors — phrase → when to use

| Phrase (use at the prompt's start) | When to use |
|---|---|
| `flat vector illustration, white background, no shading` | Icons, learning tiles, UI-adjacent visuals |
| `editorial illustration, single hero object, soft palette` | Chapter-opener art, lesson intros |
| `scientific diagram in Nature journal style, clean line art, no photorealism` | Mechanism / pathway / process figures |
| `schematic, line drawing, black outlines on white, no fill texture` | Circuit, block-diagram, flow explainers |
| `iconographic, minimal geometric shapes, bold outlines` | Concept-icon grids (4-up tiles) |
| `cutaway / cross-section diagram, labelled regions` | Anatomy, layered structures |
| `isometric technical drawing` | Workflows, pipelines, architecture |
| `anatomical illustration, single subject, neutral background, educational` | Body-part, organ, system figures |

**Rule:** one style anchor + one subject + one composition cue. Combining "photorealistic" with "scientific diagram" is a known failure pattern (Cureus 2024; ScholarViz "style soup").

---

## 2. Single-concept clarity

The strongest principle across sources: **describe one drawable outcome**, not a topic.

**Phillip Alcock's 4-stage framework (2026):** (1) *Concept* — one sentence, not a heading; (2) *Learning goal* — something a student can point to in 30 seconds; (3) *Visual zones* — split the canvas into 2–4 zones, one idea per zone; (4) *Prompt* — only after the above three.

For an HTML module: **one figure = one `<figure>` = one caption naming the only thing the student should remember.** If the caption needs a colon and a list, the figure is doing two jobs.

**Banned phrases** (force multi-concept output):
- "comprehensive overview of…" → panoramas
- "and its relationship to X, Y, Z" → all three get drawn
- "step-by-step detailed process" → pick the single step

**Composition cues:** `single object, centered, large subject filling 60% of frame, plenty of white space, no background scenery, no people`

---

## 3. Low-resolution / small-format constraints

For 200–400px inline figures (typical in HTML modules), over-detailing causes blur.

| Phrase | Effect |
|---|---|
| `simple, low detail, iconographic` | Cuts shading/texture, keeps outlines |
| `flat 2D, no perspective, no 3D shading` | Kills photorealistic drift |
| `vector, bold outlines, 2pt stroke, no gradient` | Stable at small sizes |
| `no text, no letters, no words, no labels, no numbers, no watermark` | The most important phrase for education — kills hallucinated text |
| `isolated on plain white background, no border, no frame` | Stops the model adding chrome |
| `square 1:1 aspect, fill the frame` | Consistent tile sizing |
| `simple geometric shapes, primary colors only` | Locks palette at 3–4 hues |

For programmatic generation (HTML shell with 20+ figures): pass these as a fixed *style suffix* appended to every prompt, never rewritten.

---

## 4. Failure modes & fixes

Sources: Cureus 2024 (anatomy errors across DALL·E 3, SDXL, Stable Cascade); ScholarViz; arXiv 2409.12784.

| Failure mode | Fix |
|---|---|
| **Photorealism drift** | `flat 2D, no photorealism, no realistic lighting` |
| **Hallucinated text/labels** | `no text, no letters, no labels, no watermark` — overlay real labels in HTML |
| **Anatomical errors** (hands: 60%+ error rate) | `single figure, five fingers, symmetric` — **always verify; AI cannot guarantee accuracy** |
| **Busy scene** | `single subject, centered, no background objects, negative space` |
| **Cultural / gender bias** (DALL·E 3 "twinning") | Specify demographic explicitly or use neutral silhouettes |
| **Style soup** | `single consistent style, unified illustration` |
| **Decorative clutter** | `no shadow, no glow, no vignette, no lens flare, no bokeh` |
| **Truncation past ~300 words** | Cap at 250 words; 3–5 visual concepts max |
| **"Faux figure"** (lists as art) | Skip AI — use a `<ul>` |

**Negative-prompt suffix:**
`negative: photorealism, 3D, shadow, gradient, text, letters, labels, watermark, scenery, people, hands, fingers, complex detail, multiple objects`

---

## 5. Medical / scientific illustration conventions

Per the **Nature scientific illustration guide** and ScholarViz journal comparison:

| Convention | Prompt phrasing |
|---|---|
| **Hierarchy** (importance = saturation) | `key element saturated, background muted, neutral palette` |
| **Clarity** | `clearly defined shapes, no overlapping, generous spacing` |
| **Accessibility** | `Okabe-Ito palette, no red-green, grayscale-safe` |
| **Nature style** | `clean white background, 2pt black outlines, flat fills, no shading, sans-serif labels` |
| **Cell Press** | `square 1:1, high contrast, minimal text, bold color blocks` |
| **Lancet / NEJM** | `editorial illustration, soft palette, single human or anatomical region, narrative` |
| **eLife / PLOS** | `panel labelled a/b/c, white background, vector-quality, multi-panel consistent` |

**Note:** Nature/Cell/Elsevier generally **prohibit** AI figures for submission (ScholarViz 2026). For *educational* HTML modules the anchors still produce on-brand figures — these are aids, not submitted data.

---

## 6. Recommended prompt template

```
{Style anchor} of {Single subject}, {Composition cue},
{One key element in saturated color}, {1-2 supporting elements in muted tones},
no text, no labels, no letters, no numbers, no watermark,
flat 2D, no perspective, no shadow, no gradient, no photorealism,
bold black outlines, white background, 1:1 square,
single object, centered, filling 60% of frame.
Negative: photorealism, 3D, shadow, gradient, text, labels, watermark, scenery, people, hands, complex detail.
```

**Worked example (classical conditioning):**

> Flat 2D editorial illustration of a single dog, side view, neutral background. A bell in saturated red above the dog's head; the dog in muted gray; a small bone in soft yellow. No text, no labels, no watermark. No perspective, no shadow, no gradient, no photorealism. Bold black outlines 2pt, white background, 1:1. Single subject, centered, 60% of frame. Negative: photorealism, scenery, people, hands, multiple dogs.

HTML caption: `<figcaption>The bell (CS) predicts food (US) — the dog learns the association.</figcaption>` with any labels overlaid via positioned `<span>`s.

---

## 7. Iteration loop (3 attempts is the sweet spot)

1. Broad composition + style anchor.
2. Change exactly one variable (subject / color / pose).
3. Final color/layout tweak.
4. After 3 failures: switch to manual SVG / Figma / draw.io. AI is for ideation, not polish.

---

## Sources

1. Nature — *Scientific illustration for commissioned content* — https://www.nature.com/documents/Nature_scientific_illustration_author_guide.pdf
2. Nature — *Research figure guide* — https://research-figure-guide.nature.com/
3. Sci-Draw AI — *8 AI Prompt Rules for Publication-Ready Scientific Figures* — https://sci-draw.com/blog/ai-prompt-guide
4. ScholarViz — *Scientific Figure Prompt Templates & Best Practices* — https://scholarviz.com/blog/scientific-figure-prompt-template-library
5. Phillip Alcock — *How to Create AI Educational Infographics That Actually Teach* — https://phillipalcock.substack.com/p/how-to-create-ai-educational-infographics
6. Muhr et al. (Cureus, 2024) — *Evaluating Text-to-Image Generated Photorealistic Images of Human Anatomy* — https://doi.org/10.7759/cureus.74193
7. Midlibrary — *Schematic / Technical / Cross-section / Wireframe styles* — https://midlibrary.io/styles/schematic-diagram
8. Free AI Prompt Maker — *Master DALL·E 3 Diagrams* — https://freeaipromptmaker.com/blog/2026-06-09-master-dall-e-3-diagrams-schematics
9. Lim, Choi, Shim (AAAI 2025) — *Evaluating Image Hallucination in Text-to-Image Generation* — https://arxiv.org/html/2409.12784v3
10. Google Cloud — *Omit content using a negative prompt (Imagen on Vertex AI)* — https://cloud.google.com/vertex-ai/generative-ai/docs/image/omit-content-using-a-negative-prompt
