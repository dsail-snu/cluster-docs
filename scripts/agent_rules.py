#!/usr/bin/env python3
"""Export docs/policy/ai-agents.md as one self-contained Markdown file for AI agents.

The page is the single source of the agent rules. Agents cannot follow site links or
render snippet includes, so this resolves `--8<--` includes from snippets/, turns
admonitions into plain quotes and makes every link absolute. CI publishes the result
on the site (agents/AGENTS.md); the cluster installs it into each agent's system-wide
instruction channel. Standard library only.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from siteurls import ROOT, absolute_links, site_url  # noqa: E402

PAGE = "policy/ai-agents.md"
SNIPPET = re.compile(r'^--8<-- "([^"]+)"[ \t]*$', re.M)
ADMONITION = re.compile(r'^!!! \w+(?: "([^"]*)")?\n((?:    .*\n|\n(?=    ))+)', re.M)
MARKER = "<!-- cluster-agent-rules -->"


def include(text, root, used=None):
    def repl(m):
        path = root / "snippets" / m.group(1)
        if not path.is_file():
            raise FileNotFoundError(f"snippet {m.group(1)} not found")
        if used is not None:
            used.append(path)
        return include(path.read_text().rstrip("\n"), root, used)
    return SNIPPET.sub(repl, text)


def plain_admonitions(text):
    def repl(m):
        body = re.sub(r"^    ", "", m.group(2).rstrip("\n"), flags=re.M)
        title = f"**{m.group(1)}**\n" if m.group(1) else ""
        return "\n".join("> " + line if line else ">" for line in (title + body).split("\n")) + "\n"
    return ADMONITION.sub(repl, text)


def sources(root=ROOT):
    """The files the export is made of: the page and every snippet it includes."""
    used = []
    include((root / "docs" / PAGE).read_text(), root, used)
    return [root / "docs" / PAGE, *dict.fromkeys(used)]


def revision(root=ROOT):
    """The last commit that changed the export's sources, not HEAD: a commit elsewhere in
    the repository leaves the published bytes, and so the cluster's pinned hash, alone."""
    paths = [str(p.relative_to(root)) for p in sources(root)]
    return subprocess.run(["git", "log", "-1", "--format=%h", "--", *paths], cwd=root,
                          capture_output=True, text=True).stdout.strip()


def export(root=ROOT, revision=""):
    base = site_url(root)
    text = (root / "docs" / PAGE).read_text()
    text = absolute_links(plain_admonitions(include(text, root)), base, PAGE)
    source = base + PAGE.removesuffix(".md") + "/"
    stamp = f" ({revision})" if revision else ""
    return f"{MARKER}\n<!-- Generated from {source}{stamp}. Edit the page, not this file. -->\n\n{text}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="-", help="output file (default: stdout)")
    args = ap.parse_args()
    text = export(revision=revision())
    if args.out == "-":
        sys.stdout.write(text)
    else:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
