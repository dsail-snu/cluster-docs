#!/usr/bin/env python3
"""Fail when the deepops hooks this site runs are behind deepops main.

The commit and push hooks (the sensitive guard, the commit message standard) come from
deepops at the rev .pre-commit-config.yaml pins. A pin left behind runs old guard code
on every commit here, so CI compares it with deepops main and fails until it is moved:

    uv run pre-commit autoupdate --bleeding-edge --repo https://github.com/12kimih/deepops

Usage: hooks_rev.py [--remote-sha SHA]   (SHA instead of asking the remote; for tests)
Standard library only.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".pre-commit-config.yaml"
REPO = "https://github.com/12kimih/deepops"


def pinned(text):
    """The rev the config pins for REPO; a config without it is refused."""
    m = re.search(rf"^\s*-\s*repo:\s*{re.escape(REPO)}\s*\n\s*rev:\s*(\S+)", text, re.M)
    if not m:
        raise SystemExit(f"{CONFIG.name}: no rev for {REPO}")
    return m.group(1).strip("'\"")


def main_sha():
    out = subprocess.run(["git", "ls-remote", REPO, "refs/heads/main"], capture_output=True, text=True,
                         check=True, timeout=60).stdout.split()  # fmt: skip
    if not out:
        raise SystemExit(f"{REPO}: no main branch")
    return out[0]


def check(text, remote):
    """None when the pin is deepops main, else what to do."""
    rev = pinned(text)
    if rev == remote:
        return None
    return (f"{CONFIG.name} pins deepops {rev[:12]}, deepops main is {remote[:12]}: the hooks run old code. "
            f"Run: uv run pre-commit autoupdate --bleeding-edge --repo {REPO}")  # fmt: skip


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    remote = argv[1] if argv[:1] == ["--remote-sha"] and len(argv) == 2 else main_sha()
    problem = check(CONFIG.read_text(), remote)
    if problem:
        print(problem, file=sys.stderr)
        return 1
    print(f"deepops hooks at main ({remote[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
