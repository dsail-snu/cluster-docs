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
  quota:MOUNT:F   a limit of the filesystem at MOUNT: block_hard, block_warn (TB),
                  inode_hard, inode_warn (a count); quota:ratio, files per TB
  rule:idle       the idle-GPU rule as a sentence: notices from the idle hours, and the
                  cancel with its warning, or that no cancel is active (cancel 0)
  env:table       the users' environment variables: each with its value in a login and
                  in a job (the cluster's one list, user_environment)
  env:NAME        the login value of the variable NAME, inline
  models          the shared model cache as a sentence: where it is (SHARED_HF_HUB_CACHE,
                  read by naming it; each person's own HF_HUB_CACHE stays theirs), or
                  that there is none
  chat:channels   the Slack channels people use, as a table: each name (the cluster's)
                  and its line (slack/<role>.md table:, scripts/channels.py)
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


def count(n):
    """A file count as Korean writes it: 30000000 -> 3,000만."""
    return f"{n // 10000:,}만" if n % 10000 == 0 and n >= 10000 else f"{n:,}"


def quota(data, arg):
    if arg == "ratio":
        q = next(iter(data["quota"].values()))
        return count(round(q["inode_hard"] / q["block_hard_tib"])) + "\n"
    mount, _, field = arg.rpartition(":")
    q = data["quota"][mount]
    if field.startswith("block"):
        return f"{q[field + '_tib']:g} TB\n"
    return count(q[field]) + "\n"


def env(data):
    return {e["name"]: e for e in data.get("environment", [])}


def env_table(data):
    rows = ["| 변수 | 로그인 | 잡 안 |", "|---|---|---|"]
    for e in data.get("environment", []):
        login = f"`{e['login']}`" if e["login"] else "없음"
        job = f"`{e['job']}`" if e["job"] else "같음"
        rows.append(f"| `{e['name']}` | {login} | {job} |")
    return "\n".join(rows) + "\n"


def models(data):
    hub = env(data).get("SHARED_HF_HUB_CACHE")
    if not hub:
        return "공용 모델 캐시는 아직 없습니다. 모델은 각자 `HF_HOME` 아래에 내려받습니다.\n"
    return (f"공용 모델 캐시는 `{hub['login']}`에 있고, 모든 로그인과 잡에서 `SHARED_HF_HUB_CACHE`가 그곳을 가리킵니다. "
            "**읽기 전용**이라 여기에는 내려받을 수 없으니, 각자의 `HF_HUB_CACHE`로 바꾸지 말고 읽을 때 "
            "이 경로를 직접 주세요: `from_pretrained(<모델>, cache_dir=os.environ[\"SHARED_HF_HUB_CACHE\"], "
            "local_files_only=True)`, 또는 `HF_HUB_OFFLINE=1 hf download <모델> --cache-dir \"$SHARED_HF_HUB_CACHE\"`가 "
            "출력하는 스냅샷 경로. 그 밖의 모델은 평소처럼 각자의 캐시(`HF_HOME` 아래)에 내려받고, 여럿이 쓸 모델은 "
            "관리자에게 요청하세요.\n")


def body(data, name):
    kind, _, arg = name.partition(":")
    if kind == "options":
        return options(data, arg)
    if kind == "policy":
        return policy(data, arg)
    if kind == "quota":
        return quota(data, arg)
    if name == "rule:idle":
        return idle_rule(data)
    if kind == "date":
        return f"{data['dates'][arg]}\n"
    if kind == "slurm":
        return f"{data['slurm'][arg]}\n"
    if name == "env:table":
        return env_table(data)
    if kind == "env":
        return f"`{env(data)[arg]['login']}`\n"
    if name == "models":
        return models(data)
    if name == "chat:channels":
        import channels  # the guides' sources; it reads this module too

        return channels.help_table(data)
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
