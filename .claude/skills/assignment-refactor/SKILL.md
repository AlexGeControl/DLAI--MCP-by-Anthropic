---
name: assignment-refactor
description: >
  Convert a course's notebook-style demo code into a CMU/Stanford-style Python
  project: a properly decomposed package (submodules, type hints, pyproject), a
  reference solution, and a student scaffold (stubs + docstring contracts) graded
  by a pytest suite — modernized per the staleness report. Use when the user wants
  the programming assignments turned into a real, well-engineered project instead of
  a monolithic notebook. Final step of the pipeline.
allowed-tools: Bash, Read, Write, Edit
version: 0.2.0-baseline   # 0.2: emits a runnable Makefile harness + smoke test; fixes starter README packaging
---

# assignment-refactor

Turns "watch me build it in a notebook" into "build it yourself, graded" — the way
CMU/Stanford assignments are shaped: a real package with the functionality
**decomposed into well-defined submodules**, a hidden reference solution, a student
**starter** with hollowed bodies + docstring contracts, and a **pytest** suite as the
autograder. Applies the modernization plan from
[staleness-eval](../staleness-eval/SKILL.md) (run it first).

## Output layout
```
solutions/<assignment-name>/
  README.md                 # handout: goals, background, tasks + the "Run & Explore" section
  pyproject.toml            # modernized deps, [dev] extra, ruff + mypy + pytest config
  Makefile                  # the dev harness (setup/test/smoke/serve/inspect/chatbot)
  scripts/smoke_server.py   # fast "does the server wire up?" check (no transport)
  src/<pkg>/                # the package, decomposed into submodules
    __init__.py
    <module>.py             # one responsibility each
  tests/                    # pytest suite = the autograder (public + edge cases)
  starter/                  # student-facing copy: same tree, bodies -> NotImplementedError
    README.md               # REQUIRED — pyproject's `readme=` must resolve here too
  MODERNIZATION.md          # what changed vs the course original and why (from the report)
```

## Procedure
1. **Find the through-line.** Courses usually build ONE evolving artifact across
   lessons (here: an arXiv research MCP server + an MCP chatbot client). Identify it
   from `raw/assignments/` and `manifest.json`; pick the most complete version of
   each file as the basis.
2. **Design the decomposition.** Break the monolith into single-responsibility
   modules with clean interfaces (e.g. `tools/`, `server.py`, `client.py`,
   `config.py`). Write down the module boundaries before coding.
3. **Write the reference solution**, modernized: apply every item in
   `reports/modernization.md` (new transports, current model ids, async clients,
   drop dead/harmful deps), add type hints, docstrings, and a runnable entrypoint.
4. **Write the pytest autograder.** Test behavior against the contract, not
   implementation detail. Include pure-logic unit tests that need no network/API key
   (mock arXiv / the LLM), plus clearly-marked integration tests gated behind a key.
5. **Derive the starter** from the solution: keep signatures, docstrings, imports, and
   tests; replace bodies with `raise NotImplementedError(...)` and `# TODO:` guidance.
   The starter must *import and collect tests cleanly* and fail them — never error on
   import.
6. **Write README.md** (the handout) and **MODERNIZATION.md** (deltas vs original).
   Append the **Run & Explore** section from `templates/run-and-explore.md`.
7. **Emit the runnable harness** (so operations are an artifact, not tribal knowledge):
   copy `templates/Makefile` to the assignment root and `templates/smoke_server.py`
   to `scripts/`, substituting `PKG` with the package import name. Add a `[dev]` extra
   to `pyproject.toml` (`pytest`, lint/type tools) so `make setup` installs them.
   **Place a `README.md` in BOTH the assignment root AND `starter/`** — `pyproject.toml`
   declares `readme = "README.md"`, so an editable install (`uv pip install -e .`) from
   either dir fails with *"Readme file does not exist"* if its own README is missing.
8. **Verify**: `make setup` installs cleanly; `make smoke` lists the registered
   primitives; `make test` is green on the solution; the starter collects the same
   tests and they fail at the stubs (not at import).

## Runnable harness (bundled templates)
Every generated assignment ships a `Makefile` + `scripts/smoke_server.py` (from
`templates/`) so "how to run it" lives in the artifact, not in chat history. The
operations the harness encodes — and the pitfalls baked in so they don't recur:
- `make setup` installs with **`uv pip install -e . --python .venv/bin/python`** —
  always target the venv explicitly; bare `uv pip install` can resolve to the wrong
  environment, leaving deps unimported.
- `make smoke` runs the server *without* a transport (lists tools/resources/prompts
  and returns) — distinct from `make serve`/`inspect`, which **block** (long-running).
- `make inspect` wraps the stdio server in the MCP Inspector and prints a tokenized
  `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=...` URL — that token is required.
- When scripting installs in Bash, **don't pipe through `| tail`** before checking
  success — the pipe's exit code masks a failed build (use `$PIPESTATUS`/a logfile).

## Principles
- Behavior-based tests; a student who implements the contract passes regardless of
  internal style.
- Offline-gradeable core: never require a paid API call to pass the unit tests — mock
  external services so the autograder is deterministic and free.
- Pedagogical scaffolding: each TODO names *what* and *why*, with a docstring contract
  and a pointer to the relevant lesson note ([[NN-lesson]]).
- Faithful to the course's intent, modern in its mechanics. Note every deviation in
  MODERNIZATION.md.
- Baseline scope: get the core through-line (server + client) clean and graded; mark
  stretch pieces (remote/Docker deployment) as extensions rather than blocking on them.
