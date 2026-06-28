# teach-html-opencode

Pedagogical HTML module builder for **opencode** — turn source material (PDF / DOCX / MD / paste) into a single self-contained, citation-tracked, editorial-quality HTML learning module with **build-time auto-injected diagrams** every 3 paragraphs.

## Why

- **Editorial-medical aesthetic** (Nature-style: slate paper + deep green accent) — calm, formal, authoritative.
- **Short chapters (~900 words)** — atomic ideas, low reading cost.
- **Build-time diagram injection** — every 3 paragraphs, a diagram augments the prose. Mix of:
  - **Mermaid** → inline SVG (rendered at build via Playwright/mmdc).
  - **Generated images** → gemini-3.1-flash-image via OpenRouter (low res, schematic).
  - **HTML/CSS charts** → from inline data, zero JS deps.
- **Citation linkification** — `[@Key]` → clickable `<a href="#ref-Key">`.
- **Single-file output** — fully inlined, shareable, offline.

## Quick start

```bash
# 1. Install deps
pip install --user markdown beautifulsoup4 python-docx playwright
python3 -m playwright install chromium

# 2. (one-time) Set openrouter key for image generation
export OPENROUTER_API_KEY=sk-or-v1-...

# 3. Use
/teach-html @path/to/source.pdf
```

## Layout

```
skill/
  SKILL.md             # orchestrator instructions
  scripts/             # build.py, citations.py, validate.py, ingest.py, inject_diagrams.py
  templates/           # module.css, module.js
  references/          # design-system.md, pedagogical-patterns.md
  tests/               # pytest + fixtures
  examples/            # sample-src/ for testing
planning/              # GSD planning artifacts
docs/                  # additional documentation
```

## License

MIT
