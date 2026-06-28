# teach-html-opencode — Planning

## Goal
Build a redesigned version of teach-html as a standalone opencode skill with editorial-medical aesthetic, short chapters, and build-time diagram auto-injection.

## Phases

### P0 — v0 baseline
- Copy current teach-html skill (with citation linkify + agent fixes already applied) as v0.
- Push to github.com/deathmachine111/teach-html-opencode.

### P1 — Aesthetic overhaul
- Rewrite `module.css` for Nature-style: bg #F8FAFC, accent #166534, serif headings, Inter body.
- Update `module.js` to match.

### P2 — Diagram auto-injector (TDD)
- `scripts/inject_diagrams.py`:
  - Walk chapter, mark slot every 3 paragraphs.
  - Per slot: LLM picks type + writes spec.
  - Render: mermaid→SVG (playwright), image→gemini-flash (openrouter), chart→HTML/CSS.
  - Inject into HTML during build.

### P3 — Exa research
- Image prompt engineering for educational diagrams.

### P4 — Agent updates
- Author: 900-word chapters, triplet structure.
- Outliner: estimate diagram slots, seed image anchors.

### P5 — Demo + cost report
- Photosynthesis chapter end-to-end.
- Screenshot.
- INR cost report per model × per generation.

## Status
- P0: done
- P1: done
- P2: done
- P3: done
- P4: done
- P5: done

## v1.1 update (post-interview)
- P2 now defaults to every=2 paragraphs (was 3) — visual-leaning density.
- Image style suffix changed: labels and callouts now ENCOURAGED (was: "no text, no labels"). Journal-figure style.
- New agents teach-html-opencode-{outliner,author} (replaced teach-html-*).
- Author style: tables and bullet lists first, prose connects and explains.
- 58/58 tests green. End-to-end demo: 2 image API calls = 11.27 INR total.
