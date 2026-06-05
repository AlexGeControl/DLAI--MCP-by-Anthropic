---
lesson: {INDEX}
slug: {SLUG}
title: {TITLE}
type: {TYPE}
duration_min: {DURATION}
video_id: {VIDEO_ID}
transcript: raw/transcripts/{TRANSCRIPT_FILE}
{ASSIGNMENT_LINE}
status: notes-baseline

# --- knowledge-graph metadata (Obsidian reads these; keep wikilinks valid) ---
concepts: {CONCEPTS_LIST}            # canonical slugs from _concepts/ (atomic notes)
prerequisites: {PREREQS}             # [[NN-lesson]] or [[concept]]
leads_to: {LEADS_TO}
related: {RELATED}
tags: [{TAGS}]
---

# Lesson {INDEX} — {TITLE}

> **One-line:** {ONE_LINE_SUMMARY}

## Concept map
```mermaid
graph TD
{MERMAID_BODY}
```

## Why this lesson exists
{MOTIVATION — 2-4 sentences, link to neighbouring lessons/concepts}

## Key ideas
{For each key concept: a short heading, a 1-3 sentence definition, a minimal code
or diagram anchor, and [[links]] to the concept atom and related lessons.}

## Mechanics / walkthrough
{The concrete steps or code path the lesson demonstrates, distilled — not transcript
dump. Reference real files in raw/assignments/ where relevant.}

> [!warning] Staleness
> {Any flags from reports/modernization.md that touch this lesson's APIs. Omit the
> callout if nothing here has rotted.}

## Connections
- ⬅ {what this builds on}
- ➡ {what consumes/extends this}
- 📖 {vocabulary / deeper refs}

> [!tip] Phone takeaway
> {1-2 sentences capturing the single idea to remember — written to stand alone on
> a small screen.}
