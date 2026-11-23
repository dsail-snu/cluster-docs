#!/usr/bin/env python3
"""Write llms.txt and llms-full.txt (https://llmstxt.org/) for the site, for AI agents.

llms.txt is the site's map: every page of the navigation, in its order and sections,
with its absolute URL and its first sentence. llms-full.txt is every page in full, in
the same order, self-contained as the agent rules export makes them (snippets
included, admonitions as quotes, links absolute). CI writes both into the built site's
root. Standard library only.
"""
import argparse
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_rules import include, plain_admonitions  # noqa: E402
from siteurls import ROOT, absolute_links, page_url, site_url  # noqa: E402


def nav(root=ROOT):
    """[(section, page)] in the navigation's order; top-level pages have section ""."""
    project = tomllib.loads((root / "zensical.toml").read_text())["project"]
    out = []
    for entry in project["nav"]:
        for title, target in entry.items():
            if isinstance(target, str):
                out.append(("", target))
            else:
                out.extend((title, page) for page in target)
    return out, project


def page_text(root, page):
    text = (root / project_docs(root) / page).read_text()
    return absolute_links(plain_admonitions(include(text, root)), site_url(root), page)


def project_docs(root):
    return tomllib.loads((root / "zensical.toml").read_text())["project"].get("docs_dir", "docs")


def summary(text):
    """The page's title (its first heading) and its first plain sentence."""
    title = next((m.group(1) for m in re.finditer(r"^# (.+)$", text, re.M)), "")
    for block in re.split(r"\n\s*\n", text):
        line = " ".join(block.split())
        if line and not re.match(r"^(#|>|!!!|\||```|-|\d+\.|<|--8<--)", line):
            sentence = re.split(r"(?<=[.!?다요])\s", line, maxsplit=1)[0]
            return title, re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", sentence).replace("**", "")
    return title, ""


def llms(root=ROOT):
    pages, project = nav(root)
    base = site_url(root)
    lines = [f"# {project['site_name']}", "", f"> {project.get('site_description', '')}", ""]
    section = None
    for sec, page in pages:
        if sec != section:
            lines += ["", f"## {sec or project['site_name']}", ""]
            section = sec
        title, first = summary((root / project_docs(root) / page).read_text())
        lines.append(f"- [{title}]({page_url(base, 'index.md', page)}): {first}".rstrip(": "))
    return "\n".join(lines).replace("\n\n\n", "\n\n") + "\n"


def llms_full(root=ROOT):
    pages, project = nav(root)
    base = site_url(root)
    parts = [f"# {project['site_name']}\n\n> {project.get('site_description', '')}\n"]
    for _, page in pages:
        parts.append(f"<!-- {page_url(base, 'index.md', page)} -->\n\n{page_text(root, page).rstrip()}\n")
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="site", help="directory to write both files into (default: site)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "llms.txt").write_text(llms())
    (out / "llms-full.txt").write_text(llms_full())
    return 0


if __name__ == "__main__":
    sys.exit(main())
