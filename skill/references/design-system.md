# teach-html Design System — Editorial / Academic

The visual language for every module. Clean, typographic, restrained. Print-friendly. No gradients, no heavy shadows, no decoration that competes with content.

## Principles

1. **Content first.** The reader is here to learn. Chrome recedes; prose dominates.
2. **Typographic hierarchy does the work.** Scale, weight, and whitespace — not color or boxes — signal structure.
3. **Restraint.** One accent color. Warm paper background. Serif body, sans for navigation/metadata.
4. **Print-friendly.** `@media print` hides the TOC and removes width constraints. Every module should be printable as a handout.

## Tokens (in `module.css` `:root`)

| Token | Value | Use |
|---|---|---|
| `--ink` | `#1a1a1a` | body text |
| `--paper` | `#fdfcf8` | page background (warm off-white) |
| `--rule` | `#e2ddd0` | borders, dividers |
| `--muted` | `#6b6358` | secondary text, captions |
| `--accent` | `#7a4b2a` | headings H3, links, active TOC, byline (deep walnut) |
| `--accent-soft` | `#f3ece1` | TOC bg, blockquotes, table headers |
| `--serif` | Iowan / Palatino / Georgia | body, headings |
| `--sans` | system-ui / Segoe / Roboto | nav, metadata, refs, code-inline labels |
| `--mono` | SF Mono / Menlo / Consolas | code |
| `--maxw` | `72ch` | content measure (readable line length) |
| `--side` | `240px` | TOC sidebar width |

## Layout

- **Grid:** `240px sidebar | 1fr content`. Sidebar sticky, full-height, independently scrollable.
- **Content:** centered, max 72ch, generous padding (3.5rem top, 2.5rem sides).
- **Masthead:** title (2.4rem), italic subtitle, uppercase tracked byline. Separated by a 2px ink rule.
- **Mobile (`<760px`):** single column, TOC collapses above content.

## Typography Scale

| Element | Size | Notes |
|---|---|---|
| doc-title (H1 masthead) | 2.4rem | letter-spacing -.01em |
| chapter H1 | 1.85rem | border-bottom rule |
| H2 | 1.4rem | |
| H3 | 1.15rem | accent color |
| body | 17px / 1.65 | serif |
| nav/refs | 0.85rem | sans |
| code | 0.9em | mono, subtle bg |

## Components

- **Blockquote:** left 3px accent border, accent-soft bg, italic, muted. For key points, warnings, clinical pearls.
- **Code block:** dark (#1e1e1e) pre, light text, rounded, horizontal scroll.
- **Table:** full-width, hairline borders, accent-soft header row, sans font.
- **Image:** max-width 100%, hairline border, centered.
- **TOC active state:** accent color, left border accent, semi-bold, tinted bg.

## What NOT to Do

- No gradients. No drop shadows on text. No rounded "card" chrome around prose.
- No more than one accent hue. No neon. No pure black or pure white.
- No auto-playing animation. No parallax. The only motion is smooth-scroll on TOC clicks.
- No web fonts loaded from CDNs — the module is self-contained. System font stacks only.
