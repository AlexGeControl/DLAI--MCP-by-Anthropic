#!/usr/bin/env python3
"""
Deterministic dependency/runtime scanner for a compiled course.

Walks <course>/raw/assignments, extracts declared dependency specifiers
(pyproject.toml, requirements.txt), locked versions (uv.lock), Python runtime
requirements, third-party imports actually used in .py and .ipynb files, and
version-sensitive call-site signals (e.g. transport=, model=). Emits JSON to
stdout (or --out). The model layer then adds web-checked "current version" +
breaking-change judgment to produce reports/modernization.md.

Usage:
    python scan_deps.py <course-dir> [--out reports/dependency-scan.json]
"""
import os, re, sys, json, argparse, tomllib
from collections import defaultdict

STDLIB_HINT = {  # common stdlib modules we should NOT report as third-party deps
    "os", "sys", "json", "re", "typing", "asyncio", "contextlib", "pathlib",
    "datetime", "time", "math", "collections", "itertools", "functools",
    "dataclasses", "enum", "io", "subprocess", "logging", "argparse", "base64",
    "hashlib", "sqlite3", "tempfile", "shutil", "urllib", "glob", "warnings",
}

SIGNAL_PATTERNS = {
    "transport": re.compile(r"transport\s*=\s*['\"]([a-z-]+)['\"]"),
    "model": re.compile(r"model\s*=\s*['\"]([\w.-]+)['\"]"),
    "fastmcp_decorator": re.compile(r"@mcp\.(tool|resource|prompt)\b"),
}


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except Exception:
        return ""


def notebook_sources(path):
    try:
        nb = json.loads(read(path))
    except Exception:
        return ""
    return "\n".join(
        "".join(c.get("source", [])) for c in nb.get("cells", []) if c.get("cell_type") == "code"
    )


def scan_imports(code):
    mods = set()
    for m in re.finditer(r"^\s*(?:from|import)\s+([a-zA-Z0-9_]+)", code, re.M):
        mod = m.group(1)
        if mod not in STDLIB_HINT:
            mods.add(mod)
    return mods


def collect_signals(code, signals):
    for sig, pat in SIGNAL_PATTERNS.items():
        for hit in pat.findall(code):
            signals[sig].add(hit)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course")
    ap.add_argument("--out")
    args = ap.parse_args()
    root = os.path.join(os.path.abspath(args.course), "raw", "assignments")

    declared, locked, runtimes = {}, {}, set()
    imports, signals = set(), defaultdict(set)
    files_seen = {"pyproject.toml": 0, "requirements.txt": 0, "uv.lock": 0, "py": 0, "ipynb": 0}

    for dirpath, _, files in os.walk(root):
        for fn in files:
            fp = os.path.join(dirpath, fn)
            if fn == "pyproject.toml":
                files_seen["pyproject.toml"] += 1
                try:
                    data = tomllib.loads(read(fp))
                    proj = data.get("project", {})
                    if proj.get("requires-python"):
                        runtimes.add("python " + proj["requires-python"])
                    for dep in proj.get("dependencies", []):
                        m = re.match(r"([A-Za-z0-9_.-]+)\s*(.*)", dep)
                        if m:
                            declared[m.group(1).lower()] = m.group(2).strip() or "*"
                except Exception:
                    pass
            elif fn == "requirements.txt":
                files_seen["requirements.txt"] += 1
                for line in read(fp).splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        m = re.match(r"([A-Za-z0-9_.-]+)\s*(.*)", line)
                        if m:
                            declared.setdefault(m.group(1).lower(), m.group(2).strip() or "*")
            elif fn == "uv.lock":
                files_seen["uv.lock"] += 1
                txt = read(fp)
                for m in re.finditer(r'name = "([^"]+)"\s*\nversion = "([^"]+)"', txt):
                    locked[m.group(1).lower()] = m.group(2)
            elif fn.endswith(".py"):
                files_seen["py"] += 1
                code = read(fp)
                imports |= scan_imports(code)
                collect_signals(code, signals)
            elif fn.endswith(".ipynb"):
                files_seen["ipynb"] += 1
                code = notebook_sources(fp)
                imports |= scan_imports(code)
                collect_signals(code, signals)

    third_party_imports = sorted(imports - set(STDLIB_HINT))
    declared_unused = sorted(d for d in declared if d.replace("-", "_") not in
                             {i.lower() for i in imports} and d not in {i.lower() for i in imports})

    report = {
        "scanned_root": root,
        "files_seen": files_seen,
        "python_runtime": sorted(runtimes),
        "declared_dependencies": declared,
        "locked_versions": locked,
        "third_party_imports": third_party_imports,
        "declared_but_never_imported": declared_unused,
        "version_sensitive_signals": {k: sorted(v) for k, v in signals.items()},
    }
    out = json.dumps(report, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        open(args.out, "w").write(out)
        print(f"wrote {args.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
