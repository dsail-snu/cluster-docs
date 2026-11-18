"""Facts about the published site shared by the scripts: its URL and how a Markdown
link written in a docs/ page maps to a published URL."""
import os
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def site_url(root=ROOT):
    return tomllib.loads((root / "zensical.toml").read_text())["project"]["site_url"].rstrip("/") + "/"


def page_url(base, page, target):
    """Absolute URL of `target` as linked from docs page `page` (path under docs/)."""
    if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
        return target
    path, _, anchor = target.partition("#")
    resolved = os.path.normpath(Path(page).parent / path).replace(os.sep, "/")
    resolved = re.sub(r"(^|/)index\.md$", r"\1", resolved)
    resolved = re.sub(r"\.md$", "/", resolved)
    url = base + ("" if resolved in (".", "") else resolved)
    return url + (f"#{anchor}" if anchor else "")


def absolute_links(markdown, base, page, fmt="[{text}]({url})"):
    """Rewrite every relative Markdown link to an absolute site URL, in `fmt`."""
    return LINK.sub(lambda m: fmt.format(text=m.group(1), url=page_url(base, page, m.group(2))), markdown)
