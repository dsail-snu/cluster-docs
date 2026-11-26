#!/usr/bin/env python3
"""Fail when the deepops hooks this site runs are older than deepops main's.

The commit and push hooks (the sensitive guard, the commit message standard) come from
deepops at the rev .pre-commit-config.yaml pins. What matters is the code they run, not
the rev: deepops main moves many times a day, mostly in files no hook runs. So CI fails
only when a file the pinned hooks run (each hook's entry script in deepops'
.pre-commit-hooks.yaml, what it imports from deepops, and that file itself) differs
between the pin and deepops main, or when the pin is not on main at all:

    uv run pre-commit autoupdate --bleeding-edge --repo https://github.com/12kimih/deepops

Usage: hooks_rev.py [--deepops DIR]   (a deepops clone instead of cloning; for tests)
Standard library only.
"""

import argparse
import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".pre-commit-config.yaml"
REPO = "https://github.com/12kimih/deepops"
HOOKS = ".pre-commit-hooks.yaml"
FIX = f"Run: uv run pre-commit autoupdate --bleeding-edge --repo {REPO}"


def pinned(text):
    """(rev, [hook id]) the config pins for REPO; a config without it is refused."""
    m = re.search(rf"^\s*-\s*repo:\s*{re.escape(REPO)}\s*\n\s*rev:\s*(\S+)\s*\n((?:\s+.*\n?)*?)(?=^\s*-\s*repo:|\Z)", text, re.M)
    if not m:
        raise SystemExit(f"{CONFIG.name}: no rev for {REPO}")
    return m.group(1).strip("'\""), re.findall(r"^\s*-\s*id:\s*(\S+)", m.group(2), re.M)


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check, timeout=300)


def show(repo, rev, path):
    """PATH's text at REV, or None when it is not there."""
    r = git(repo, "show", f"{rev}:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


def entries(hooks_text, ids):
    """{id: the entry's script path} of the hooks IDS in a .pre-commit-hooks.yaml."""
    out = {}
    for block in re.split(r"^- ", hooks_text, flags=re.M)[1:]:
        hid = re.search(r"^id:\s*(\S+)", block, re.M)
        entry = re.search(r"^\s*entry:\s*(\S+)", block, re.M)
        if hid and entry and hid.group(1) in ids:
            out[hid.group(1)] = entry.group(1)
    return out


def imported(source, path):
    """The repository files PATH's Python SOURCE imports: modules beside it (the hooks put
    their own directory on sys.path) and from the repository root."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
    here = PurePosixPath(path).parent
    out = set()
    for name in names:
        rel = PurePosixPath(*name.split("."))
        for base in (here, PurePosixPath()):
            out |= {str(base / f"{rel}.py"), str(base / rel / "__init__.py")}
    return out


def used(repo, rev, ids):
    """Every file the hooks IDS run at REV: the hooks file, each entry and what it imports."""
    hooks = show(repo, rev, HOOKS)
    if hooks is None:
        raise SystemExit(f"deepops {rev[:12]}: no {HOOKS}")
    found = entries(hooks, ids)
    missing = set(ids) - set(found)
    if missing:
        raise SystemExit(f"deepops {rev[:12]} has no hook {', '.join(sorted(missing))}")
    seen, todo = {HOOKS}, list(found.values())
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        text = show(repo, rev, path)
        if text is None:
            continue  # a candidate module that is not a file of the repository
        seen.add(path)
        if path.endswith(".py") or text.startswith("#!/usr/bin/env python"):
            todo += sorted(imported(text, path) - seen)
    return seen


def check(repo, rev, ids, main="origin/main"):
    """None when the pinned hooks run the code deepops main has, else what is wrong."""
    if git(repo, "cat-file", "-e", f"{rev}^{{commit}}", check=False).returncode:
        return f"{CONFIG.name} pins deepops {rev[:12]}, which deepops does not have. {FIX}"
    if git(repo, "merge-base", "--is-ancestor", rev, main, check=False).returncode:
        return f"{CONFIG.name} pins deepops {rev[:12]}, which is not on deepops main. {FIX}"
    changed = set(git(repo, "diff", "--name-only", rev, main).stdout.split())
    stale = sorted((used(repo, rev, ids) | used(repo, main, ids)) & changed)
    if stale:
        return (f"{CONFIG.name} pins deepops {rev[:12]}; deepops main changed what the hooks run: "
                f"{', '.join(stale)}. {FIX}")  # fmt: skip
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--deepops", help="a deepops clone (default: a fresh one of REPO)")
    args = ap.parse_args(argv)
    rev, ids = pinned(CONFIG.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        repo = args.deepops
        if not repo:
            repo = tmp
            subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", REPO, tmp],
                           check=True, timeout=300)  # fmt: skip
        problem = check(repo, rev, ids)
    if problem:
        print(problem, file=sys.stderr)
        return 1
    print(f"deepops hooks pinned at {rev[:12]}: what they run is deepops main's")
    return 0


if __name__ == "__main__":
    sys.exit(main())
