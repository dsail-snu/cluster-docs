"""scripts/site_blocks.py: generated blocks come from data/site.json, and --check fails
on a page whose block no longer matches."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import site_blocks  # noqa: E402

DATA = {
    "commands": {"tool": {"summary": "s", "usage": "tool", "options": [
        {"flags": ["-a", "--all"], "metavar": "", "help": "everything"},
        {"flags": ["-u", "--user"], "metavar": "LOGIN", "help": "one person | theirs"}]}},
    "policy": {"stale_days": 60, "grace_days": 14, "warn_fraction": 0.9},
    "slurm": {"kill_wait_seconds": 30, "preempt_grace_seconds": 30, "sigkill_after_seconds": 60},
}  # fmt: skip


class Blocks(unittest.TestCase):
    def test_a_block_is_filled_from_the_data(self):
        page = "x\n<!-- BEGIN GENERATED: options:tool -->\nold\n<!-- END GENERATED: options:tool -->\ny\n"
        out = site_blocks.fill(page, DATA)
        self.assertIn("| `-a`, `--all` | everything |", out)
        self.assertIn("`--user` `LOGIN`", out)
        self.assertIn("one person \\| theirs", out)
        self.assertNotIn("old", out)

    def test_policy_values(self):
        page = "<!-- BEGIN GENERATED: policy:warn_percent -->\n<!-- END GENERATED: policy:warn_percent -->"
        self.assertIn("90%", site_blocks.fill(page, DATA))

    def test_an_inline_value_stays_on_its_line(self):
        page = "- 유예 <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->9<!-- END GENERATED: slurm:preempt_grace_seconds -->초\n"
        self.assertEqual(
            site_blocks.fill(page, DATA),
            "- 유예 <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->30<!-- END GENERATED: slurm:preempt_grace_seconds -->초\n",
        )

    def test_a_block_in_a_list_item_keeps_its_indent(self):
        page = "- item\n  <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->\n  <!-- END GENERATED: slurm:preempt_grace_seconds -->\n"
        self.assertEqual(
            site_blocks.fill(page, DATA),
            "- item\n  <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->\n  30\n  <!-- END GENERATED: slurm:preempt_grace_seconds -->\n",
        )

    def test_the_site_pages_match_the_data(self):
        self.assertEqual(site_blocks.main(["--check"]), 0, "run scripts/site_blocks.py")


if __name__ == "__main__":
    unittest.main()
