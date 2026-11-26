#!/usr/bin/env python3
"""The Slack channels' guides: one source per channel in slack/<ROLE>.md, written to the
site as channels.json, which the cluster's bot keeps each channel in step with
(deepops roles/cluster_bot, cluster_bot.channels: purpose, topic, canvas, bookmarks).

    slack/<ROLE>.md   ROLE is the channel's purpose (announce, help, status, admin); the
                      channel's name is the cluster's (data/site.json chat.channels)
      ---
      purpose: one line (at most 250 characters, Slack's limit)
      topic: one line (the same)
      title: the canvas's title
      table: the channel's line in the help page's table (left out: not listed)
      bookmark: :emoji: | title | link     (one line each, in order)
      ---
      the canvas, in Markdown

A link is a docs page (guide/storage.md) or a site file; the export makes it absolute.
Placeholders, filled from data/site.json so no fact is typed twice:
  [[admins]]          the administrators' group handle
  [[/cluster]]        the bot's slash command
  [[bot.subcommands]] its subcommands as a table, with their Korean help
  [[commands]]        the cluster commands as a table, with their Korean summaries
  [[rule:idle]]       the rule on jobs leaving their GPUs idle (scripts/site_blocks.py)
  [[reports]]         the status channel's reports as a table: when, what
  [[reports:inline]]  the same on one line
  [[#ROLE]]           that channel: left for the bot, which writes a mention in the
                      canvas and the channel's name in a purpose or topic

Usage: channels.py export OUT | check
Standard library only.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_blocks  # noqa: E402
from siteurls import LINK, ROOT, page_url, site_url  # noqa: E402

SOURCES = "slack"
ROLES = ("help", "announce", "status", "admin")  # the help page's table order
LIMIT = 250
PLACEHOLDER = re.compile(r"\[\[([^\]]+)\]\]")
FIELDS = ("purpose", "topic", "title")
DAYS = {"Mon": "월요일", "Tue": "화요일", "Wed": "수요일", "Thu": "목요일", "Fri": "금요일", "Sat": "토요일",
        "Sun": "일요일"}  # fmt: skip
CALENDAR = re.compile(r"(?:(Mon|Tue|Wed|Thu|Fri|Sat|Sun) +)?\*-\*-\* +(\d{2}):(\d{2})(?::00)?")
REPORTS = {  # what each of the status channel's reports holds (site.json reports)
    "usage": ("GPU 사용 현황", "누가 어떤 GPU를 쓰는지, 남은 GPU"),
    "weekly": ("주간 요약", "지난 한 주 사람별 GPU 사용 시간과 쓰지 않고 잡아 둔 시간"),
    "disk": ("디스크 사용량", "사람별, 공간별 디스크 사용량과 경고 수준을 넘은 사람"),
}


def when(schedule):
    """A systemd OnCalendar value as Korean reads it: hourly -> 매시간, "Mon *-*-* 09:00:00"
    -> 월요일 09:00. Another form is refused, so the generator learns it before a page
    says it wrong."""
    named = {"hourly": "매시간", "daily": "매일 00:00", "weekly": "월요일 00:00"}
    if schedule in named:
        return named[schedule]
    m = CALENDAR.fullmatch(schedule.strip())
    if not m:
        raise ValueError(f"schedule {schedule!r}: teach scripts/channels.py when() this form")
    return f"{DAYS[m.group(1)] if m.group(1) else '매일'} {m.group(2)}:{m.group(3)}"


def parse(path):
    """{role, purpose, topic, title, table, bookmarks [{emoji, title, link}], markdown}."""
    text = path.read_text()
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not match:
        raise ValueError(f"{path.name}: front matter (--- ... ---) missing")
    out = {"role": path.stem, "table": "", "bookmarks": [], "markdown": match.group(2).strip() + "\n"}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not sep:
            raise ValueError(f"{path.name}: {line!r} is not key: value")
        if key == "bookmark":
            parts = [p.strip() for p in value.split("|")]
            if len(parts) != 3 or not re.fullmatch(r":[a-z0-9_+-]+:", parts[0]):
                raise ValueError(f"{path.name}: bookmark is ':emoji: | title | link', not {value!r}")
            out["bookmarks"].append(dict(zip(("emoji", "title", "link"), parts)))
        elif key in (*FIELDS, "table"):
            out[key] = value
        else:
            raise ValueError(f"{path.name}: unknown key {key!r}")
    missing = [f for f in FIELDS if not out.get(f)]
    if missing or out["role"] not in ROLES:
        raise ValueError(f"{path.name}: needs {', '.join(FIELDS)}; the file is named after one of {ROLES}")
    return out


def sources(root=ROOT):
    return {g["role"]: g for g in map(parse, sorted((root / SOURCES).glob("*.md")))}


def _table(header, rows):
    return site_blocks.table(header, rows).rstrip("\n")


def fill(text, data):
    """TEXT with every placeholder but [[#ROLE]] filled from DATA; an unknown one raises."""
    chat, bot = data["chat"], data["bot"]

    def one(m):
        name = m.group(1)
        if name.startswith("#"):
            if name[1:] not in ROLES:
                raise ValueError(f"[[{name}]]: no such channel role")
            return m.group(0)
        if name == "admins":
            return chat["admin_group"] or "관리자"
        if name == "/cluster":
            return bot["command"]
        if name == "bot.subcommands":
            return site_blocks.bot_subcommands(data).rstrip("\n")
        if name == "commands":
            return site_blocks.commands_table(data).rstrip("\n")
        if name == "rule:idle":
            return site_blocks.idle_rule(data).strip()
        if name == "reports":
            return _table(("언제", "무엇"), [(when(data["reports"][k]), f"{short}: {what}")
                                             for k, (short, what) in REPORTS.items()])  # fmt: skip
        if name == "reports:inline":
            return " | ".join(f"{when(data['reports'][k])} {short}" for k, (short, _) in REPORTS.items())
        raise ValueError(f"[[{name}]]: unknown placeholder")

    return PLACEHOLDER.sub(one, text)


def _link(target, root, base):
    """TARGET absolute; a docs page that does not exist raises."""
    if re.match(r"[a-z][a-z0-9+.-]*:", target):
        return target
    path = target.partition("#")[0]
    if path.endswith(".md") and not (root / "docs" / path).is_file():
        raise ValueError(f"link {target}: no page docs/{path}")
    return page_url(base, "index.md", target)


def channel(guide, data, root=ROOT):
    base = site_url(root)
    names = data["chat"]["channels"]
    shown = {f: fill(guide[f], data) for f in ("purpose", "topic")}
    for field, value in shown.items():  # as Slack will hold it: each [[#ROLE]] a name
        as_set = re.sub(r"\[\[#([a-z]+)\]\]", lambda m: names[m.group(1)], value)
        if len(as_set) > LIMIT:
            raise ValueError(f"{guide['role']}: the {field} is {len(as_set)} characters; Slack keeps {LIMIT}")
    markdown = LINK.sub(lambda m: f"[{m.group(1)}]({_link(m.group(2), root, base)})", fill(guide["markdown"], data))
    return {
        **shown,
        "canvas": {"title": guide["title"], "markdown": markdown},
        "bookmarks": [{"title": b["title"], "url": _link(b["link"], root, base), "emoji": b["emoji"]}
                      for b in guide["bookmarks"]],  # fmt: skip
    }


def document(data, root=ROOT):
    return {"channels": {role: channel(g, data, root) for role, g in sources(root).items()}}


def help_table(data, root=ROOT):
    """The help page's table: each listed channel's name and line, in ROLES order."""
    guides, names = sources(root), data["chat"]["channels"]
    rows = [(f"`{names[r]}`", guides[r]["table"]) for r in ROLES if r in guides and guides[r]["table"]]
    return _table(("Slack 채널", "용도"), rows) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    data = json.loads(site_blocks.DATA.read_text())
    try:
        doc = document(data)
    except (ValueError, KeyError) as err:
        print(f"slack/: {err}", file=sys.stderr)
        return 1
    if argv[:1] == ["export"] and len(argv) == 2:
        out = Path(argv[1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        return 0
    if argv == ["check"]:
        return 0
    print(__doc__.split("\n\n")[-2], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
