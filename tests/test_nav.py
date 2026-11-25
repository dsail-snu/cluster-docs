"""The navigation: every section is a page people can open, as every top-level entry is."""

import posixpath
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import site_blocks  # noqa: E402


class Sections(unittest.TestCase):
    def test_each_section_opens_on_its_own_index_page_and_holds_one_directory(self):
        # navigation.indexes makes a section clickable only when its first page is the
        # directory's index.md; one without it reads as a heading nobody clicks.
        nav = tomllib.loads((ROOT / "zensical.toml").read_text())["project"]["nav"]
        for entry in nav:
            for title, target in entry.items():
                if isinstance(target, str):
                    continue
                dirs = {posixpath.dirname(p) for p in target}
                self.assertEqual(len(dirs), 1, f"{title}: its pages live in one directory")
                self.assertEqual(target[0], f"{dirs.pop()}/index.md", f"{title}: its first page is its index.md")

    def test_a_section_block_lists_the_section_relative_to_the_page(self):
        text = site_blocks.section("start", "index.md")
        self.assertIn("](start/connect.md)", text)
        self.assertIn("](connect.md)", site_blocks.section("start", "start/index.md"))
        self.assertNotIn("index.md)", site_blocks.section("start", "start/index.md"))
        with self.assertRaises(SystemExit):
            site_blocks.section("nowhere", "index.md")


if __name__ == "__main__":
    unittest.main()
