---
name: courseware-compile
description: >
  Compile a DeepLearning.AI course into a canonical on-disk layout (transcripts +
  raw coding assignments + manifest.json) by authenticating with the user's local
  Chrome session. Use when the user wants to extract, fetch, download, or "compile"
  a DLAI course they're enrolled in for note-taking or assignment work. Folds auth
  into the platform adapter; strictly local and read-only.
allowed-tools: Bash, Read, Write, Edit
---

# courseware-compile (DeepLearning.AI adapter)

Extracts a DLAI course into the **canonical layout** that all downstream skills
(notes, staleness-eval, assignment-refactor) consume. This is the platform-specific
layer — auth + fetch folded into one adapter. New platforms get a sibling adapter
emitting the same layout; downstream skills never change.

## Canonical output layout
```
<course-dir>/
  manifest.json                 # lessons, ids, program_id crosswalk, provenance
  raw/transcripts/NN-slug.md    # full prose + timestamped transcript per video lesson
  raw/assignments/<verbatim sandbox tree>   # notebooks (.ipynb) + project source + images
```

## How to run

1. **Confirm Chrome is logged in.** The user must already be signed into
   learn.deeplearning.ai in their local Chrome profile. Cookies are decrypted
   locally (gnome-keyring, `Chrome Safe Storage`). The session is **read-only and
   never leaves the machine** except to deeplearning.ai itself.

2. **Compile** from the course slug or any lesson URL:
   ```bash
   python .claude/skills/courseware-compile/compile.py \
       https://learn.deeplearning.ai/courses/<slug>/lesson/.../... \
       --out <course-dir>
   ```
   Selective runs: `--what transcripts` | `--what assignments` | `--manifest-only`.

3. **Verify**: check `manifest.json` lesson count, that `raw/transcripts/` has one
   file per video lesson, and that `raw/assignments/` contains the notebooks.

## Key facts about the DLAI platform (encoded in `dlai_adapter.py`)
- **Auth**: Chrome v11 cookies → AES key from keyring item exactly `Chrome Safe
  Storage` (not `...Control`); PBKDF2-SHA1(salt=`saltysalt`, iters=1, 16B); AES-128-CBC,
  IV=16 spaces. Copy the Cookies DB before reading (Chrome locks the live file).
- **Data**: Next.js + tRPC at `/api/trpc/<proc>?batch=1&input=<urlencoded {"0":{"json":...}}>`.
  - `course.getCourseBySlug {courseSlug}` → courseId + `lessons` (keyed by slug; each
    has index, type, videoId, and **`programId`** for notebook lessons).
  - `course.getLessonVideoSubtitle {videoId}` → timestamped captions.
  - `course.getProgramLab {programAssignmentId=programId, courseId, userId}` → boots a
    per-user Jupyter sandbox (422 "launching"/"not ready"; poll ~8s, ready <1 min),
    returns a notebook URL with `?token=`.
  - Files via the sandbox's **Jupyter contents API**:
    `https://<host>/api/contents/<path>?token=<tok>&content=1`, recursed.
- **One sandbox holds the whole course** — boot once (any notebook lesson's programId),
  crawl everything. Sandboxes time out, so mirror in a single pass.
- Sandbox lab-folder numbers can be offset from lesson numbers (e.g. Lesson 5 = `L4`).
  `manifest.json` records each lesson's `program_id`; the sandbox tree is verbatim.

## Boundaries
- Read-only. Never write to the sandbox, never modify the user's course state.
- Faithful extraction only — no transformation here. Notes/refactor are separate skills.
- If the user isn't logged in (auth fails / empty cookies), tell them to sign into
  the course in Chrome first; do not attempt other credential sources.
