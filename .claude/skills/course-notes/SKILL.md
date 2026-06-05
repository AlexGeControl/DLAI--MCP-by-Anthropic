---
name: course-notes
description: >
  Turn compiled course transcripts (plus assignment code and the staleness report)
  into an Obsidian knowledge-graph vault: one cross-linked note per lesson, atomic
  concept notes, and a map-of-content index. Optimized for learning the ideas on a
  phone and finalizing via Obsidian sync. Use when the user wants study notes /
  knowledge-graph notes for a compiled course. Second step of the pipeline.
allowed-tools: Bash, Read, Write, Edit
version: 0.1.0-baseline
---

# course-notes (Obsidian knowledge graph)

Builds a vault under `<course-dir>/notes/` from `raw/transcripts/`, grounded by
`raw/assignments/` and annotated with `reports/modernization.md` (run
[staleness-eval](../staleness-eval/SKILL.md) first). Designed for **mobile-first
reading**: self-contained, link-rich, every note ends with a one-glance takeaway.

## Vault structure
```
notes/
  00-map-of-content.md     # MOC: course overview + ordered lesson links + concept index
  _concepts/<slug>.md      # atomic concept notes (definitions reused across lessons)
  NN-<lesson-slug>.md      # one per lesson (template: templates/lesson-note.md)
  _attachments/            # images copied from raw/assignments when a note embeds one
```

## Conventions (so the graph actually connects)
- **Frontmatter graph metadata** — `concepts`, `prerequisites`, `leads_to`, `related`,
  all as `[[wikilinks]]`. Obsidian's graph view uses these + inline links.
- **Atomic concept notes** — each cross-cutting idea (e.g. `[[stdio-transport]]`,
  `[[fastmcp]]`) gets ONE note in `_concepts/`; lessons link to it instead of
  redefining. This is what makes the graph dense and reusable.
- **Mermaid concept map** per lesson (Obsidian renders mermaid natively, incl. mobile).
- **Callouts**: `> [!warning] Staleness` for rotted APIs (from the report);
  `> [!tip] Phone takeaway` as the closing one-liner.
- **Code**: short, real snippets anchored to files in `raw/assignments/`; link, don't dump.
- **Images**: copy referenced images into `_attachments/` and embed with `![[name.png]]`.

## Procedure
1. **Build the concept spine FIRST** — read all transcripts, list the canonical
   concept slugs and which lessons touch each. This fixes the vocabulary so parallel
   note-writing stays consistent (no `[[Tool]]` vs `[[tools]]` drift).
2. **Write atomic concept notes** in `_concepts/` for the cross-cutting ones.
3. **Write one lesson note per lesson** from the template, distilling the transcript
   (ideas, not a transcript dump) and grounding code claims in `raw/assignments/`.
   Pull staleness callouts from the modernization report where APIs are affected.
4. **Write `00-map-of-content.md`** — course one-paragraph, the ordered lesson list as
   links, the concept index, and a top-level mermaid of the lesson dependency flow.
5. **Verify links** — every `[[wikilink]]` resolves to a file that exists (or is an
   intentional concept stub). List any dangling links.

## Principles
- Distill, don't transcribe. A note should be readable in ~2 min on a phone.
- One idea per concept note; lessons compose them.
- Keep it valid Obsidian markdown — frontmatter, `[[links]]`, `![[embeds]]`, callouts,
  mermaid. No HTML that mobile won't render.
- Match the established template/voice (see the Lesson-5 exemplar if present).
