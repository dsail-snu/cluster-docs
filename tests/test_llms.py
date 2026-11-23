"""Tests for scripts/llms.py: the site map and the full text for AI agents."""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("llms", SCRIPTS / "llms.py")
llms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llms)


class LlmsTests(unittest.TestCase):
    def test_the_map_lists_every_page_of_the_navigation(self):
        text = llms.llms()
        pages, project = llms.nav()
        self.assertTrue(text.startswith(f"# {project['site_name']}\n"))
        for _, page in pages:
            url = llms.page_url(llms.site_url(), "index.md", page)
            self.assertIn(f"]({url})", text, page)

    def test_the_full_text_is_self_contained(self):
        text = llms.llms_full()
        self.assertNotIn("--8<--", text)
        self.assertNotIn("!!! ", text)
        self.assertIsNone(re.search(r"\]\((?!https?://|#)[^)]*\)", text), "relative link left")
        self.assertIn("1, 2, 4, 8", text, "snippets included")


if __name__ == "__main__":
    unittest.main()
