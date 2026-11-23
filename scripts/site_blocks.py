#!/usr/bin/env python3
"""Fill the generated blocks in the pages from data/site.json, the facts the cluster's
code and config hold (written there by deepops scripts/docs/site_facts.py).

A page marks a block

    <!-- BEGIN GENERATED: options:sq -->
    <!-- END GENERATED: options:sq -->

and this script writes its body; a hand edit inside a block is overwritten. CI runs it
with --check, so a page whose block no longer matches the data fails the build.

Generators:
  options:CMD     the options of the cluster command CMD, as a table
  policy:FIELD    one policy value (stale_days, grace_days, warn_percent)

Usage: site_blocks.py [--check]
Standard library only.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site.json"
BLOCK = re.compile(r"(<!-- BEGIN GENERATED: (\S+) -->\n)(.*?)(<!-- END GENERATED: \2 -->)", re.S)


def options(data, command):
    rows = ["| 옵션 | 설명 |", "|---|---|"]
    for o in data["commands"][command]["options"]:
        flags = ", ".join(f"`{f}`" + (f" `{o['metavar']}`" if o["metavar"] and f.startswith("--") else "") for f in o["flags"])
        rows.append(f"| {flags} | {o['help'].replace('|', '\\|')} |")
    return "\n".join(rows) + "\n"


def policy(data, field):
    p = data["policy"]
    if field == "warn_percent":
        return f"{round(p['warn_fraction'] * 100)}%\n"
    return f"{p[field]}\n"


def body(data, name):
    kind, _, arg = name.partition(":")
    if kind == "options":
        return options(data, arg)
    if kind == "policy":
        return policy(data, arg)
    raise SystemExit(f"unknown generated block: {name}")


def fill(text, data):
    return BLOCK.sub(lambda m: m.group(1) + body(data, m.group(2)) + m.group(4), text)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = argv == ["--check"]
    data = json.loads(DATA.read_text())
    stale = []
    for page in sorted((ROOT / "docs").rglob("*.md")) + sorted((ROOT / "snippets").rglob("*.md")):
        text = page.read_text()
        new = fill(text, data)
        if new != text:
            stale.append(page.relative_to(ROOT))
            if not check:
                page.write_text(new)
    if check and stale:
        for page in stale:
            print(f"{page}: a generated block differs from data/site.json; run scripts/site_blocks.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
