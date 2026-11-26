"""scripts/hooks_rev.py: CI fails while the deepops hooks are pinned behind deepops main,
so the guard and message checks here never run old code unnoticed (2026-11-27)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hooks_rev  # noqa: E402

CONFIG = f"repos:\n  - repo: x\n    rev: v1\n  - repo: {hooks_rev.REPO}\n    rev: abc123\n    hooks: []\n"


class HooksRev(unittest.TestCase):
    def test_the_pin_of_the_deepops_repo(self):
        self.assertEqual(hooks_rev.pinned(CONFIG), "abc123")
        self.assertEqual(hooks_rev.pinned(CONFIG.replace("abc123", "'abc123'")), "abc123")
        with self.assertRaises(SystemExit):
            hooks_rev.pinned("repos: []\n")

    def test_behind_main_fails_with_the_fix_and_at_main_passes(self):
        self.assertIsNone(hooks_rev.check(CONFIG, "abc123"))
        problem = hooks_rev.check(CONFIG, "def456")
        self.assertIn("pre-commit autoupdate --bleeding-edge", problem)
        self.assertIn("def456", problem)

    def test_this_sites_config_has_a_deepops_pin(self):
        self.assertRegex(hooks_rev.pinned(hooks_rev.CONFIG.read_text()), r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
