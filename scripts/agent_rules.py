#!/usr/bin/env python3
"""Export the agent rules (snippets/agent-prompt.md) as one self-contained Markdown file.

The prompt is the only text of the agent rules, for agents (the AGENTS.md convention: a
README for people, AGENTS.md for agents); docs/policy/ai-agents.md is the people's page,
which says why and how and shows this same export in a code block (site_blocks
agents:prompt). The rule snippets (job, GPU session, I/O) are one text, included both
here and in the people's pages. Agents cannot follow site links or render snippet
includes, so this resolves `--8<--` includes from snippets/, turns admonitions into
plain quotes and makes every link absolute, as written for the people's page (PAGE). CI
publishes the result on the site (agents/AGENTS.md); the cluster installs it into each
agent's system-wide instruction channel. Standard library only.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_blocks  # noqa: E402
from siteurls import ROOT, absolute_links, site_url  # noqa: E402

PAGE = "policy/ai-agents.md"  # the people's page: where the prompt is shown, its links' base
PROMPT = "snippets/agent-prompt.md"
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
    """The files the export is made of: the prompt and every snippet it includes."""
    used = []
    include((root / PROMPT).read_text(), root, used)
    return [root / PROMPT, *dict.fromkeys(used)]


def revision(root=ROOT):
    """The last commit that changed the export's sources, not HEAD: a commit elsewhere in
    the repository leaves the published bytes, and so the cluster's pinned hash, alone."""
    paths = [str(p.relative_to(root)) for p in sources(root)]
    return subprocess.run(["git", "log", "-1", "--format=%h", "--", *paths], cwd=root,
                          capture_output=True, text=True).stdout.strip()


def published(text, root, page, absolute=True):
    """A page's text as an export hands it out: snippets included, generated blocks as
    their values (site_blocks.plain), admonitions as quotes, links absolute. The one
    reading for every export (this file and llms-full.txt). ABSOLUTE false keeps the links
    as written, for a page in the repository: the site's address is a site fact the
    sensitive guard keeps out of committed text."""
    text = plain_admonitions(site_blocks.plain(include(text, root)))
    return absolute_links(text, site_url(root), page) if absolute else text


def prompt(root=ROOT, absolute=True):
    """The agent rules as agents get them: the prompt, published from the people's page
    (PAGE), whose code block shows it with its links as written (ABSOLUTE false)."""
    return published((root / PROMPT).read_text(), root, PAGE, absolute)


def export(root=ROOT, revision=""):
    source = site_url(root) + PAGE.removesuffix(".md") + "/"
    stamp = f" ({revision})" if revision else ""
    return f"{MARKER}\n<!-- Generated from {source}{stamp}. Edit {PROMPT}, not this file. -->\n\n{prompt(root)}"


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
