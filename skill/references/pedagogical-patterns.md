# teach-html Pedagogical Patterns

How author agents should structure explanatory prose. The goal: a reader who has NOT seen the source understands the chapter fully.

## Chapter Shape

A chapter is one coherent topic, 1500-3000 words:

1. **Frame** (1-2 paragraphs) — what this chapter answers and why it matters. Hook the reader with a question, contrast, or clinical scenario.
2. **Build** (the body, multiple H2 sections) — develop the concept. Lead with intuition, formalize, then apply.
3. **Consolidate** (closing) — a compact summary, a worked example, or a transition to the next chapter. Not a generic "in conclusion."

## Scaffolding Moves

Use these where the material is hard:

- **Intuition first.** Before a formal definition, give an analogy or a concrete instance. Then state the formal rule. Example: *before* defining volume of distribution, describe pouring dye into a bathtub of unknown size.
- **Worked example.** After stating a principle, walk through one concrete case end-to-end with numbers. Show the arithmetic.
- **Contrast pairs.** Juxtapose similar-but-different concepts in a table (e.g., first-order vs zero-order kinetics).
- **Clinical vignette.** A 2-3 sentence patient scenario that the principle explains. Used sparingly — once or twice per chapter.
- **Callout blockquotes.** For definitions, warnings, and clinical pearls. Format: `> **Key point:** ...` or `> **Warning:** ...`.

## Citation Discipline

- Every factual claim, statistic, definition, quotation, and non-obvious assertion carries `[@Key]`.
- Trivial/common knowledge (e.g., "the heart has four chambers") does not need a citation.
- Prefer primary sources over textbooks where the source allows. If citing a textbook for a primary fact, note it.
- Multiple sources for one claim: `[@Key1; @Key2]`.
- Page-specific: `[@Key, p. 45]`.

## Prose Quality (anti AI-ism)

- Vary sentence length. Some short. Some longer, carrying more of the argument's weight.
- No filler openers: "It is important to note that", "It should be mentioned that", "Interestingly,".
- No hollow closers: "In conclusion", "To summarize", "Thus we can see that".
- Precise verbs over adverb-verb pairs ("halves" not "reduces by half"; "doubles" not "increases twofold").
- One idea per paragraph. 3-6 sentences typical.

## Visual Elements (when to use)

- **Table:** comparisons, taxonomies, dose-response grids. Not for prose.
- **List:** enumerations, steps, criteria. Not for narrative.
- **Blockquote:** definitions, warnings, pearls. Not for ordinary paragraphs.
- **Code block:** formulas as pseudocode, dosing calculations, decision logic.
- **Image:** diagrams, schematics, figures from the source (re-referenced, captioned). Every image needs a caption explaining what to notice.

## Depth Calibration

Match density to the audience the user named:
- **Foundational:** more analogies, more worked examples, define every term on first use, glossary-style callouts.
- **Intermediate:** assume core vocabulary, focus on mechanism and application, fewer analogies.
- **Advanced:** assume fluency, focus on nuance, evidence quality, and edge cases. Cite primary literature heavily.
