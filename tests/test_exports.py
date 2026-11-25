"""Every export of the pages reads them as a reader would: no generated-block markers
(scripts/site_blocks.py's syntax) reach the agent rules, llms-full.txt or a notice."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import agent_rules  # noqa: E402
import llms  # noqa: E402
import notices  # noqa: E402
import site_blocks  # noqa: E402

MARK = "GENERATED:"


class Exports(unittest.TestCase):
    def test_plain_keeps_the_value_and_drops_the_markers(self):
        text = "a <!-- BEGIN GENERATED: x -->60<!-- END GENERATED: x --> b\n<!-- BEGIN GENERATED: y -->\nrow\n<!-- END GENERATED: y -->\n"
        self.assertEqual(site_blocks.plain(text), "a 60 b\nrow\n")

    def test_no_export_carries_a_marker(self):
        self.assertNotIn(MARK, agent_rules.export())
        self.assertNotIn(MARK, llms.llms_full())
        self.assertNotIn(MARK, llms.llms())
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "notices.json"
            notices.export(out)
            self.assertNotIn(MARK, json.dumps(json.loads(out.read_text()), ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
