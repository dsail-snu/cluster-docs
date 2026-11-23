#!/usr/bin/env python3
"""Fill the generated blocks in the pages from data/site.json, the facts the cluster's
code and config hold (written there by deepops scripts/docs/site_facts.py).

A page marks a block

    <!-- BEGIN GENERATED: options:sq -->
    <!-- END GENERATED: options:sq -->

and this script writes its body; a hand edit inside a block is overwritten. A single
value sits inline, both markers on its line, so it reads inside a sentence or a list item
(a marker on a line of its own would end a list item):

    유예 시간은 <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->120<!-- END GENERATED: slurm:preempt_grace_seconds -->초입니다.
 CI runs it
with --check, so a page whose block no longer matches the data fails the build.

Generators:
  options:CMD     the options of the cluster command CMD, as a table
  policy:FIELD    one policy value (stale_days, grace_days, warn_percent)
  date:NAME       one announced date (the site's schedule)
  rule:idle       the idle-GPU rule as a sentence: notices from the idle hours, and the
                  cancel with its warning, or that no cancel is active (cancel 0)
  slurm:FIELD     one Slurm value (kill_wait_seconds, preempt_grace_seconds,
                  sigkill_after_seconds)

Usage: site_blocks.py [--check]
Standard library only.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site.json"
# A block may sit indented in a list item: its body takes the BEGIN marker's indent.
BLOCK = re.compile(r"^([ ]*)(<!-- BEGIN GENERATED: (\S+) -->\n)(.*?)([ ]*<!-- END GENERATED: \3 -->)", re.S | re.M)


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


def idle_rule(data):
    p = data["policy"]
    text = (f"GPU를 할당받은 채 **{p['idle_hours']}시간 넘게 쓰지 않으면** 매시간 사용 현황 리포트마다 "
            "Slack으로 알림이 갑니다.")
    if p["cancel_after_hours"]:
        text += (f" **{p['cancel_after_hours']}시간** 동안 쓰지 않은 잡은 자동으로 취소되고, "
                 f"취소 **{p['cancel_warn_hours']}시간 전**에 미리 알려 줍니다.")
    else:
        text += " 쓰지 않는 잡의 자동 취소는 켜져 있지 않습니다."
    return text + "\n"


def body(data, name):
    kind, _, arg = name.partition(":")
    if kind == "options":
        return options(data, arg)
    if kind == "policy":
        return policy(data, arg)
    if name == "rule:idle":
        return idle_rule(data)
    if kind == "date":
        return f"{data['dates'][arg]}\n"
    if kind == "slurm":
        return f"{data['slurm'][arg]}\n"
    raise SystemExit(f"unknown generated block: {name}")


INLINE = re.compile(r"(<!-- BEGIN GENERATED: (\S+) -->)([^\n]*?)(<!-- END GENERATED: \2 -->)")


def fill(text, data):
    def one(m):
        indent = m.group(1)
        lines = body(data, m.group(3)).splitlines(keepends=True)
        return indent + m.group(2) + "".join(indent + line if line.strip() else line for line in lines) + m.group(5)

    text = BLOCK.sub(one, text)
    return INLINE.sub(lambda m: m.group(1) + body(data, m.group(2)).strip() + m.group(4), text)


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
