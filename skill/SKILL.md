---
name: teach-html
description: Build extensively-detailed, single-file HTML pedagogical modules from textbook excerpts, research papers, or pasted source. Pipeline = ingest sources to markdown → outliner designs chapter architecture → author writes each chapter section-by-section with citations → coder compiles to one self-contained inlined HTML (CSS/JS/images embedded) → structural validation. Model-routed: outline=glm-5.2, author+citations=deepseek-v4-flash, HTML/CSS/JS=minimax-m3. Use when the user wants to turn a PDF/DOCX/MD/paper/textbook chapter into a polished, shareable, citation-tracked HTML learning module. Triggers: "make an HTML module", "turn this into a teachable HTML", "build a course module from this", "/teach-html".
---

# /teach-html — Pedagogical HTML Module Builder

Turn source material (PDF / DOCX / MD / paper / textbook excerpt / paste) into a single self-contained, citation-tracked, editorial-quality HTML learning module.

**Strategy B (md→build):** authors write markdown chapters; a deterministic build script compiles them into one inlined HTML. Cheapest (md tokens), debuggable (readable source), shareable (single file, no hosting), reproducible.

## Paths

- Scripts: `~/.config/opencode/skills/teach-html/scripts/` (`ingest.py`, `build.py`, `validate.py`, `citations.py`)
- Templates: `~/.config/opencode/skills/teach-html/templates/` (`module.css`, `module.js`)
- References: `~/.config/opencode/skills/teach-html/references/` (`design-system.md`, `pedagogical-patterns.md`)
- Agents: `teach-html-outliner`, `teach-html-author`, `teach-html-coder` (in `~/.config/opencode/agents/`)
- **Work directory:** create `<project>/teach-html-src/` per invocation. All `ch*.md`, `references.md`, `meta.json`, and image files live there.

## Model Routing

| Stage | Agent | Model |
|---|---|---|
| Outline + architecture | `teach-html-outliner` | `opencode-go/glm-5.2` |
| Chapter prose + citations | `teach-html-author` | `opencode-go/deepseek-v4-flash` |
| HTML/CSS/JS build + tooling | `teach-html-coder` | `opencode-go/minimax-m3` |

Invoke agents via the `task` tool with the matching `subagent_type`. Verification (structural) is a deterministic script run by you directly — no agent needed.

---

## Workflow

### Stage 0 — Ingest

Collect every source the user provided. For each file:

```bash
python3 ~/.config/opencode/skills/teach-html/scripts/ingest.py <source> <teach-html-src>/<name>.md
```

- PDF → `ingest.py` cascades through markitdown (uvx/pipx) → pypdf. If all fail, ask the user to paste the text.
- DOCX → python-docx extraction (headings, paragraphs, tables → md).
- MD/TXT → copied as-is.
- **URL** → you fetch with `webfetch`/`ctx_fetch_and_index`, save the markdown to the src dir.
- **Paste** → write the pasted text directly to `<name>.md`.

Confirm all sources are markdown in `teach-html-src/` before proceeding.

### Stage 1 — Outline + Architecture

Spawn `teach-html-outliner` (task tool). Give it:
- The list of ingested source files (paths)
- The user's learning objectives and audience level
- Instruction: write `meta.json`, `outline.md`, and seed `references.md` to `teach-html-src/`.

It returns the chapter plan. Review: are the chapters sensibly sized (1500-3000 words each)? Are citation keys real? Adjust if needed.

### Stage 2 — Author Each Chapter

For each `chNN.md` in the outline, spawn `teach-html-author` (task tool). Give it:
- The chapter's outline section
- The source excerpt(s) it maps to
- The current `references.md`

**Parallelize:** chapters are independent — spawn multiple author tasks concurrently when the outline has 3+ chapters and sources don't overlap heavily. Each writes its own `chNN.md`. After each returns, check it appended any new citation keys to `references.md` and merge (authors append-only; reconcile duplicates).

### Stage 3 — Citation Reconciliation

```bash
python3 ~/.config/opencode/skills/teach-html/scripts/citations.py teach-html-src/
```

This reports `undefined` (cited but no entry) and `uncited` (defined but never used). Fix undefined by adding entries to `references.md` (spawn author in "complete references" mode if bibliographic data is needed). Uncited entries are harmless but you may prune them.

### Stage 4 — Build

Spawn `teach-html-coder` (task tool). It runs `build.py` → produces `<project>/<module-name>.html`, then runs `validate.py`. If structural errors appear, it fixes the source (md or templates) and rebuilds until clean.

You can also build directly if no custom work is needed:

```bash
python3 ~/.config/opencode/skills/teach-html/scripts/build.py \
  teach-html-src/ \
  ~/.config/opencode/skills/teach-html/templates \
  <project>/<module-name>.html
python3 ~/.config/opencode/skills/teach-html/scripts/validate.py <project>/<module-name>.html
```

### Stage 5 — Verify + Deliver

1. **Structural validation** — `validate.py` must report `OK: structurally valid`.
2. **Spot-check** — open the HTML (or use `webapp-testing` / browser skill) and confirm: TOC scrollspy works, headings anchor, images render, bibliography lists only cited works, no broken layout.
3. **Deliver** — report the path to the single `.html` file. Remind the user it is fully self-contained (email it, host it, or open locally — no dependencies).

---

## Conventions

- **Chapter files:** `ch01.md`, `ch02.md`, ... zero-padded, `ch` prefix. One H1 each. The build script picks these up by regex `ch\d`.
- **Citations:** pandoc-style `[@Key]`, `[@Key, p. 12]`, `[@Key1; @Key2]`. References in `references.md` as `[Key]: entry`.
- **Images:** `![caption](file.png)` — file lives in `teach-html-src/`, inlined as data URI at build time.
- **Bibliography:** auto-generated, cited-works-only, sorted by key. Appears as the final `<section id="references">`.
- **Single output:** one `.html`, CSS/JS/images inlined. No external links survive the build.

## When to Deviate

- **Very large source (book-length):** split into multiple modules, each its own `teach-html-src/` + build. Don't force one giant HTML.
- **Interactive quizzes/diagrams needed:** instruct the coder agent to add vanilla-JS components to `module.js` + matching CSS. Keep dependency-free.
- **User wants multi-file output (not single):** build normally, then the user can extract — but the default is single-file for shareability.
