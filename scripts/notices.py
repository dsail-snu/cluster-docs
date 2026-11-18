#!/usr/bin/env python3
"""Notices: one Markdown file per notice in docs/news/posts. Standard library only.

  check [BASE]            validate every notice; with BASE (a git revision), also
                          require a new or changed notice when docs/policy/ changed
  announce BASE HEAD      post the notices added between two revisions to Slack
                          (incoming webhook in $SLACK_WEBHOOK_URL; --dry-run prints)

The notice format lives here and in CONTRIBUTING.md only; the site generator reads the
same files, so the site, its feed and Slack always show the same notice.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from siteurls import absolute_links, site_url  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
POSTS = "docs/news/posts"
# Paths whose changes change the rules: the policy pages and the rule blocks they include.
POLICY = ("docs/policy/", "snippets/")
CATEGORIES = {
    "policy": (":scroll:", "규정"),
    "update": (":arrows_counterclockwise:", "업데이트"),
    "maintenance": (":wrench:", "점검"),
    "notice": (":mega:", "공지"),
}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass
class Notice:
    path: str
    date: date
    slug: str
    categories: list
    title: str
    summary: str

    def url(self, site):
        return f"{site}news/{self.date:%Y/%m/%d}/{self.slug}/"


def parse(path, text):
    """A notice from its file; raises ValueError naming what is wrong."""
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not match:
        raise ValueError("front matter (--- ... ---) missing")
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.split(" #")[0].strip()
    body = match.group(2)
    try:
        day = date.fromisoformat(meta.get("date", ""))
    except ValueError:
        raise ValueError("date must be YYYY-MM-DD") from None
    slug = meta.get("slug", "")
    if not SLUG.fullmatch(slug):
        raise ValueError("slug must be lowercase ASCII words joined by '-'")
    categories = [c.strip() for c in meta.get("categories", "").strip("[]").split(",") if c.strip()]
    unknown = set(categories) - set(CATEGORIES)
    if not categories or unknown:
        raise ValueError(f"categories must be some of {sorted(CATEGORIES)}")
    title = re.search(r"^# (.+)$", body, re.M)
    if not title:
        raise ValueError("a '# title' line is required")
    if "<!-- more -->" not in body:
        raise ValueError("'<!-- more -->' must end the summary")
    summary = body[title.end():body.index("<!-- more -->")].strip()
    if not summary:
        raise ValueError("a summary is required before '<!-- more -->'")
    expected = f"{day:%Y-%m-%d}-{slug}.md"
    if Path(path).name != expected:
        raise ValueError(f"file name must be {expected}")
    return Notice(path, day, slug, categories, title.group(1).strip(), summary)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def changed(base, head="HEAD", status="AMR"):
    out = git("diff", "--name-only", f"--diff-filter={status}", base, head)
    return [p for p in out.splitlines() if p]


def all_notices():
    notices, errors = [], []
    for path in sorted((ROOT / POSTS).glob("*.md")):
        rel = str(path.relative_to(ROOT))
        try:
            notices.append(parse(rel, path.read_text()))
        except ValueError as err:
            errors.append(f"{rel}: {err}")
    return notices, errors


def check(base):
    _, errors = all_notices()
    if base:
        files = changed(base)
        # A rule-neutral edit (rewording, restructuring) says so with a "No-Notice: <why>" trailer.
        waived = re.search(r"^No-Notice: \S", git("log", "--format=%B", f"{base}..HEAD"), re.M)
        if (any(p.startswith(POLICY) for p in files) and not waived
                and not any(p.startswith(POSTS + "/") for p in files)):
            errors.append(f"{' or '.join(POLICY)} changed without a notice in {POSTS}/ (see CONTRIBUTING.md)")
    for err in errors:
        print(err, file=sys.stderr)
    return 1 if errors else 0


BLOCK_START = re.compile(r"^(?:[-*+] |\d+[.)] |> |#{1,6} |\|)")


def unwrap(markdown):
    """Join the lines of each paragraph, as a Markdown renderer does.

    Sources are wrapped for editing, but Slack shows every newline, so a sentence
    would break mid-line. New lines start only at a list item, quote, heading, table
    row, a hard break (trailing backslash or two spaces) and around fenced code.
    """
    out, fenced = [], False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        joinable = (out and out[-1].strip() and line.strip() and not fenced
                    and not BLOCK_START.match(line.lstrip()) and not out[-1].lstrip().startswith("```")
                    and not out[-1].endswith(("\\", "  ")))
        if joinable:
            out[-1] = out[-1] + " " + line.strip()
        else:
            out.append(line)
    # Drop the hard-break markers (trailing backslash or spaces) outside code fences.
    result, fenced = [], False
    for line in out:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        result.append(line if fenced or line.lstrip().startswith("```") else re.sub(r"(\\| +)$", "", line))
    return "\n".join(result)


def mrkdwn(markdown, base, page):
    """Notice Markdown to Slack mrkdwn: paragraphs unwrapped, bold, links absolute."""
    text = absolute_links(unwrap(markdown), base, page, fmt="<{url}|{text}>")
    return re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)


def blocks(notice, base):
    icon = CATEGORIES[notice.categories[0]][0]
    labels = ", ".join(CATEGORIES[c][1] for c in notice.categories)
    page = notice.path.removeprefix("docs/")
    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"{icon} {notice.title}"[:150], "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn(notice.summary, base, page)[:2900]}},
        {"type": "actions", "elements": [{"type": "button", "text": {"type": "plain_text", "text": "자세히 보기"},
                                          "url": notice.url(base)}]},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"{labels}  |  {notice.date:%Y-%m-%d}"}]},
    ]


def announce(base, head, dry_run):
    site = site_url(ROOT)
    added = [p for p in changed(base, head, status="A") if p.startswith(POSTS + "/") and p.endswith(".md")]
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "")
    if added and not webhook and not dry_run:
        print("SLACK_WEBHOOK_URL is not set", file=sys.stderr)
        return 1
    for rel in added:
        notice = parse(rel, git("show", f"{head}:{rel}"))
        payload = {"text": notice.title, "blocks": blocks(notice, site)}
        if dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=1))
            continue
        req = urllib.request.Request(webhook, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                print(f"{rel}: Slack answered {resp.status}", file=sys.stderr)
                return 1
        print(f"announced {rel}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("base", nargs="?")
    a = sub.add_parser("announce")
    a.add_argument("base")
    a.add_argument("head")
    a.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.cmd == "check":
        return check(args.base)
    return announce(args.base, args.head, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
