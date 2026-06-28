---
name: teach-html-opencode
description: Build single-file HTML pedagogical modules from textbook excerpts, research papers, or pasted source, with auto-injected diagrams every 3 paragraphs. Pipeline = ingest sources to markdown → outliner designs chapter architecture → author writes each chapter section-by-section with citations → diagram injector (build-time LLM picks type: mermaid / generated image / chart) → coder compiles to one self-contained inlined HTML (CSS/JS/images embedded) → structural validation. Aesthetic: Nature-style editorial-medical (slate #F8FAFC + deep green #166534). Target ~900 words/chapter. Model-routed: outline=glm-5.2, author+citations=deepseek-v4-flash, HTML/CSS/JS=minimax-m3. Use when the user wants to turn a PDF/DOCX/MD/paper/textbook chapter into a polished, shareable, citation-tracked HTML learning module with diagrams. Triggers: "make an HTML module", "turn this into a teachable HTML", "build a course module from this", "/teach-html-opencode".
---

# /teach-html-opencode — Pedagogical HTML Module Builder

Turn source material (PDF / DOCX / MD / paper / textbook excerpt / paste) into a single self-contained, citation-tracked, editorial-quality HTML learning module with **auto-injected diagrams** every ~3 paragraphs.

**Strategy B (md→build):** authors write markdown chapters; a deterministic build script compiles them into one inlined HTML. Cheapest (md tokens), debuggable (readable source), shareable (single file, no hosting), reproducible.

## Design Aesthetic

- **Palette:** slate paper `#F8FAFC` canvas, deep green `#166534` accent, slate-900 ink, green-50 sidebar.
- **Type:** serif body (Iowan / Source Serif / Palatino), sans for labels (Inter / system), mono for code (JetBrains Mono / SF Mono).
- **Feel:** Nature / NEJM / Lancet — clean scientific restraint, hairline rules, italic captions, light-green tinted blockquotes, framed figures with captions underneath.
- **Reading width:** 72ch. Sidebar 260px TOC with sticky scrollspy.
- **Figures:** all diagrams (mermaid / image / chart) wrapped in `<figure class="diagram">` with a captioned `<figcaption>`. Mermaid baked to SVG at build time; image gen via gemini-3.1-flash-image-preview; charts as inline CSS/SVG primitives (no JS).

## Paths

- Scripts: `skill/scripts/` (`ingest.py`, `build.py`, `validate.py`, `citations.py`, `inject_diagrams.py`)
- Templates: `skill/templates/` (`module.css`, `module.js`)
- Agents: `teach-html-opencode-outliner`, `teach-html-opencode-author`, `teach-html-opencode-coder` (in `~/.config/opencode/agents/`)
- **Work directory:** create `<project>/teach-html-src/` per invocation. All `ch*.md`, `references.md`, `meta.json`, and image files live there.
- **Mermaid bundle:** `~/.cache/teach-html/mermaid.min.js` (downloaded once via `inject_diagrams.mermaid_ensure_local()` — required for mermaid rendering).

## Model Routing

| Stage | Agent | Model |
|---|---|---|
| Outline + architecture | `teach-html-opencode-outliner` | `opencode-go/glm-5.2` |
| Chapter prose + citations | `teach-html-opencode-author` | `opencode-go/deepseek-v4-flash` |
| HTML/CSS/JS build + tooling | `teach-html-opencode-coder` | `opencode-go/minimax-m3` |
| Diagram spec picker (build-time) | embedded in `inject_diagrams.pick_spec` | user-supplied `llm_fn` |
| Image generation (build-time) | `render_image` | `google/gemini-3.1-flash-image-preview` via openrouter |

Invoke agents via the `task` tool with the matching `subagent_type`. Verification (structural) is a deterministic script run by you directly — no agent needed.

---

## Workflow

### Stage 0 — Ingest

Collect every source the user provided. For each file:

```bash
python3 skill/scripts/ingest.py <source> teach-html-src/<name>.md
```

- PDF → `ingest.py` cascades through markitdown (uvx/pipx) → pypdf. If all fail, ask the user to paste the text.
- DOCX → python-docx extraction (headings, paragraphs, tables → md).
- MD/TXT → copied as-is.
- **URL** → you fetch with `webfetch`/`ctx_fetch_and_index`, save the markdown to the src dir.
- **Paste** → write the pasted text directly to `<name>.md`.

Confirm all sources are markdown in `teach-html-src/` before proceeding.

### Stage 1 — Outline + Architecture

Spawn `teach-html-opencode-outliner` (task tool). Give it:
- The list of ingested source files (paths)
- The user's learning objectives and audience level
- Instruction: write `meta.json`, `outline.md`, and seed `references.md` to `teach-html-src/`.

It returns the chapter plan. Review: are the chapters sensibly sized (target **~900 words each**)? Are citation keys real? Adjust if needed.

### Stage 2 — Author Each Chapter

For each `chNN.md` in the outline, spawn `teach-html-opencode-author` (task tool). Give it:
- The chapter's outline section
- The source excerpt(s) it maps to
- The current `references.md`

**Chapter triplet structure:** each chapter is written as 3-paragraph triplets. The diagram injector will mark a slot after every 3 paragraphs and ask the LLM to pick the right diagram type. Authors should write prose that **justifies** a diagram at each triplet boundary (a concept map, an illustration, or a small data chart).

**Parallelize:** chapters are independent — spawn multiple author tasks concurrently when the outline has 3+ chapters and sources don't overlap heavily. Each writes its own `chNN.md`. After each returns, check it appended any new citation keys to `references.md` and merge (authors append-only; reconcile duplicates).

### Stage 3 — Citation Reconciliation

```bash
python3 skill/scripts/citations.py teach-html-src/
```

This reports `undefined` (cited but no entry) and `uncited` (defined but never used). Fix undefined by adding entries to `references.md` (spawn author in "complete references" mode if bibliographic data is needed). Uncited entries are harmless but you may prune them.

### Stage 4 — Inject Diagrams (build-time)

Before HTML build, augment each chapter with auto-generated diagrams:

```python
from inject_diagrams import inject_diagrams

with open("teach-html-src/ch01.md") as f:
    md = f.read()

def llm_fn(prompt: str) -> dict:
    # wrap openrouter call or pass a stub for testing
    ...

augmented, summary = inject_diagrams(
    md,
    every=3,                  # one diagram per triplet
    llm_fn=llm_fn,            # chooses {mermaid|image|chart} per slot
    api_key=os.environ["OPENROUTER_API_KEY"],
    cost_log=[],              # accumulate usage per model
)
open("teach-html-src/ch01.md", "w").write(augmented)
```

- `every=3` controls slot density. Set lower (e.g. 2) for visual-heavy chapters, higher (e.g. 4) for text-heavy ones.
- `summary["usage_by_model"]` returns `{model: {prompt_tokens, completion_tokens, cost_usd}}`. For INR cost, multiply USD by ~83.
- Mermaid rendering requires `~/.cache/teach-html/mermaid.min.js`. Run `inject_diagrams.mermaid_ensure_local()` once to download it.
- Image rendering needs `OPENROUTER_API_KEY` in env.
- Charts (bar/line/pie) are pure HTML/SVG/CSS — no API call, no cost.

### Stage 5 — Build

Spawn `teach-html-opencode-coder` (task tool). It runs the inject_diagrams → build.py → validate.py pipeline, fixes any structural errors, and produces `<project>/<module-name>.html` plus a `cost_log` of per-model token usage.

You can also build directly if no custom work is needed:

```bash
python3 skill/scripts/build.py \
  teach-html-src/ \
  skill/templates \
  <project>/<module-name>.html
python3 skill/scripts/validate.py <project>/<module-name>.html
```

### Stage 6 — Verify + Deliver

1. **Structural validation** — `validate.py` must report `OK: structurally valid`.
2. **Test suite** — `python3 -m pytest skill/tests/` must pass (47 tests: split/mark/pick/render/inject + build + validate + citations).
3. **Cost report** — sum `cost_log` entries per model, convert USD→INR, print as a table.
4. **Spot-check** — open the HTML (or use `webapp-testing` / browser skill) and confirm: TOC scrollspy works, headings anchor, images render, bibliography lists only cited works, no broken layout.
5. **Deliver** — report the path to the single `.html` file. Remind the user it is fully self-contained (email it, host it, or open locally — no dependencies).

---

## Conventions

- **Chapter files:** `ch01.md`, `ch02.md`, ... zero-padded, `ch` prefix. One H1 each. The build script picks these up by regex `ch\d`.
- **Chapter length:** target ~900 words. Structure as 3-paragraph triplets so the diagram injector has predictable slots.
- **Citations:** pandoc-style `[@Key]`, `[@Key, p. 12]`, `[@Key1; @Key2]`. References in `references.md` as `[Key]: entry`.
- **Diagrams (post-inject):** the injector inserts `<figure class="diagram">` blocks after every 3 paragraphs. Authors do not write diagrams by hand.
- **Images:** `![caption](file.png)` — file lives in `teach-html-src/`, inlined as data URI at build time. (For generated diagrams, the image is a data URI returned by the image model and already inlined.)
- **Bibliography:** auto-generated, cited-works-only, sorted by key. Appears as the final `<section id="references">`.
- **Single output:** one `.html`, CSS/JS/images inlined. No external links survive the build.

## When to Deviate

- **Very large source (book-length):** split into multiple modules, each its own `teach-html-src/` + build. Don't force one giant HTML.
- **Interactive quizzes/diagrams needed:** instruct the coder agent to add vanilla-JS components to `module.js` + matching CSS. Keep dependency-free.
- **User wants multi-file output (not single):** build normally, then the user can extract — but the default is single-file for shareability.
- **No API key for image gen:** set `llm_fn` to never return `"image"` type. The injector will only emit mermaid + chart diagrams.
