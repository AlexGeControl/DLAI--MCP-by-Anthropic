---
name: staleness-eval
description: >
  Audit a compiled course's coding assignments for framework/dependency staleness
  and produce a modernization report. Use when the user wants to know whether a
  course's programming assignments are built on legacy/outdated frameworks and how
  to modernize them, before drafting notes or refactoring. Reads the canonical
  raw/assignments layout; first step of the pipeline.
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
version: 0.1.0-baseline
---

# staleness-eval

**The pain point this solves:** online-course content is often excellent, but its
programming assignments freeze on the framework versions current at release and are
never updated. Before you build notes or refactor, you need to know *what has rotted*
and *how it changed* — otherwise you teach yourself a dead API.

This is the **first** skill in the pipeline (`staleness-eval → course-notes →
assignment-refactor`). Its report feeds the other two: notes get "⚠️ this changed"
callouts; refactor gets an explicit modernization target.

## Procedure

1. **Mechanical scan** — deterministic, no judgment:
   ```bash
   python .claude/skills/staleness-eval/scan_deps.py <course-dir> \
       --out <course-dir>/reports/dependency-scan.json
   ```
   Extracts declared specifiers, locked versions (uv.lock), Python runtime, the
   third-party imports actually used, **declared-but-never-imported** deps (dead
   weight), and version-sensitive call-site signals (`transport=`, `model=`,
   `@mcp.*` decorators).

2. **Establish the release baseline** — from the scan, note the versions the course
   assumed and infer its rough vintage.

3. **Check current state** — for each significant dependency, WebSearch/WebFetch the
   latest version (PyPI/GitHub) and any **breaking changes / deprecations** between
   baseline and now. Pay special attention to:
   - transport / protocol changes (e.g. MCP SSE → Streamable HTTP),
   - model identifiers that have been retired,
   - packages that were deprecated or renamed (e.g. `PyPI:typing` backport,
     `PyPI:PyPDF2` → `pypdf`),
   - sync→async client migrations and hacks they imply (e.g. `nest_asyncio`).

4. **Classify** each item: `current` · `minor-drift` · `major-drift` ·
   `deprecated/removed` · `dead-dependency`. Rank by learner impact (does following
   the assignment as-written break or teach a wrong pattern?).

5. **Write** `<course-dir>/reports/modernization.md`:
   - Verdict (one line: modernize? how urgently?) + course vintage.
   - Severity-ranked table: dep · baseline · current · status · impact.
   - Per-item migration notes (old pattern → new pattern, with code).
   - A prioritized "modernization plan" the refactor skill can execute.
   - Cite sources for current versions.

## Principles
- Distinguish **cosmetic drift** (version bumped, API stable) from **teaching hazards**
  (the assignment teaches a now-wrong pattern). Only the latter is urgent.
- Flag dead/declared-but-unused and harmful deps — they confuse learners and CI.
- Be concrete: every "deprecated" claim gets a replacement + a code-level migration.
- Don't refactor here — only diagnose and prescribe. Execution is assignment-refactor.
