"""site_blocks.plain: an export of the pages (the agent rules, llms-full.txt, the Slack
notices) drops the generated blocks' markers and nothing else. Its pattern took the line
end after every END marker, so an inline value at the end of a line glued the next line
onto it: a list item of the agent rules, the idle rule's next item in a notice posted to
Slack, and the blank line after each block (2026-11-27)."""

import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import llms  # noqa: E402
import site_blocks  # noqa: E402

spec = importlib.util.spec_from_file_location("agent_rules", ROOT / "scripts" / "agent_rules.py")
agent_rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_rules)

# A list item joined onto the text before it: words, two spaces or more, then "- ".
GLUED = re.compile(r"\S {2,}- \S")


def expected(text):
    """TEXT's lines, a line holding only a marker gone, every other line without markers."""
    lines = [line for line in text.split("\n") if not site_blocks.MARKER_LINE.match(line + "\n")]
    return site_blocks.MARKERS.sub("", "\n".join(lines))


class Plain(unittest.TestCase):
    def test_an_inline_value_at_a_line_end_keeps_the_line_end(self):
        page = "- a <!-- BEGIN GENERATED: x -->v<!-- END GENERATED: x -->\n- b\n"
        self.assertEqual(site_blocks.plain(page), "- a v\n- b\n")

    def test_a_block_goes_with_its_marker_lines_and_the_blank_line_after_stays(self):
        page = "a\n  <!-- BEGIN GENERATED: x -->\n  v\n  <!-- END GENERATED: x -->\n\nb\n"
        self.assertEqual(site_blocks.plain(page), "a\n  v\n\nb\n")

    def test_every_page_keeps_every_line(self):
        out = subprocess.run(["git", "ls-files", "-z", "docs", "snippets", "slack"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout  # fmt: skip
        pages = [p for p in out.split("\0") if p.endswith(".md")]
        self.assertGreater(len(pages), 20)
        for page in pages:
            text = (ROOT / page).read_text()
            self.assertEqual(site_blocks.plain(text), expected(text), page)

    def test_the_exports_join_no_list_item_onto_a_line(self):
        for name, text in (("agents/AGENTS.md", agent_rules.export()), ("llms-full.txt", llms.llms_full())):
            glued = [line for line in text.splitlines() if GLUED.search(line) and "|" not in line]
            self.assertEqual(glued, [], name)


if __name__ == "__main__":
    unittest.main()
