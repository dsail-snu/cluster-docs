#!/usr/bin/env python3
"""Check every internal link and #anchor in the built site (site/). Standard library only.

The generator reports missing pages but not missing anchors; a renamed heading would
silently break links such as policy/#디버깅. Run after `zensical build`.
"""
import sys
import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BASE = "http://site.invalid/"
# Absolute links (e.g. on 404.html) carry the site_url path prefix.
PREFIX = urlparse(tomllib.loads((ROOT / "zensical.toml").read_text())["project"]["site_url"]).path


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def page_file(url_path):
    if url_path.startswith(PREFIX):
        url_path = "/" + url_path[len(PREFIX):]
    path = SITE / unquote(url_path).lstrip("/")
    return path / "index.html" if url_path.endswith("/") or path.is_dir() else path


def main():
    pages = {}
    for html in SITE.rglob("*.html"):
        parser = Page()
        parser.feed(html.read_text(errors="replace"))
        pages[html] = parser
    errors = []
    for html, parser in pages.items():
        here = BASE + str(html.relative_to(SITE))
        for href in parser.links:
            url = urlparse(urljoin(here, href))
            if f"{url.scheme}://{url.netloc}/" != BASE:
                continue
            target = page_file(url.path)
            if target not in pages:
                if not target.exists():
                    errors.append(f"{html.relative_to(SITE)}: missing page {href}")
                continue
            if url.fragment and unquote(url.fragment) not in pages[target].ids:
                errors.append(f"{html.relative_to(SITE)}: missing anchor {href}")
    for err in sorted(set(errors)):
        print(err, file=sys.stderr)
    print(f"{len(pages)} pages checked, {len(set(errors))} broken links")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
