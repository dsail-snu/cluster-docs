"""scripts/hooks_rev.py: CI fails while the deepops hooks pinned here run older code than
deepops main's, and only then: a pin compared by rev made CI red after every deepops
push, mostly in files no hook runs (2026-11-27), so the docs could not be published."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hooks_rev  # noqa: E402

CONFIG = (f"repos:\n  - repo: x\n    rev: v1\n    hooks:\n      - id: other\n"
          f"  - repo: {hooks_rev.REPO}\n    rev: abc123\n    hooks:\n      - id: guard\n      - id: message\n"
          f"  - repo: local\n    hooks:\n      - id: mine\n")  # fmt: skip
HOOKS = ("- id: guard\n  entry: scripts/guard.py staged\n  language: script\n"
         "- id: message\n  entry: scripts/message.py message\n  language: script\n"
         "- id: unused\n  entry: scripts/unused.py\n  language: script\n")  # fmt: skip


class Pinned(unittest.TestCase):
    def test_the_rev_and_the_hooks_of_the_deepops_repo(self):
        self.assertEqual(hooks_rev.pinned(CONFIG), ("abc123", ["guard", "message"]))
        with self.assertRaises(SystemExit):
            hooks_rev.pinned("repos: []\n")

    def test_this_sites_config_has_a_deepops_pin(self):
        rev, ids = hooks_rev.pinned(hooks_rev.CONFIG.read_text())
        self.assertRegex(rev, r"^[0-9a-f]{40}$")
        self.assertIn("sensitive-guard", ids)


class Check(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.write(".pre-commit-hooks.yaml", HOOKS)
        self.write("scripts/guard.py", "import sys\nsys.path.insert(0, '.')\nimport cli\nfrom push_range import x\n")
        self.write("scripts/cli.py", "import os\n")
        self.write("scripts/push_range.py", "x = 1\n")
        self.write("scripts/message.py", "import cli\n")
        self.write("scripts/unused.py", "")
        self.write("roles/a.yml", "a: 1\n")
        self.pin = self.commit("base")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def write(self, path, text):
        (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / path).write_text(text)

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD").strip()

    def check(self):
        return hooks_rev.check(self.repo, self.pin, ["guard", "message"], main="main")

    def test_the_files_the_hooks_run(self):
        self.assertEqual(hooks_rev.used(self.repo, self.pin, ["guard", "message"]),
                         {".pre-commit-hooks.yaml", "scripts/guard.py", "scripts/message.py",
                          "scripts/cli.py", "scripts/push_range.py"})  # fmt: skip

    def test_main_moving_in_files_no_hook_runs_passes(self):
        self.write("roles/a.yml", "a: 2\n")
        self.write("scripts/unused.py", "changed = True\n")
        self.commit("elsewhere")
        self.assertIsNone(self.check())

    def test_a_change_in_what_a_hook_runs_fails(self):
        for path in ("scripts/guard.py", "scripts/push_range.py", ".pre-commit-hooks.yaml"):
            with self.subTest(path=path):
                self.write(path, (self.repo / path).read_text() + "# changed\n")
                self.commit(path)
                self.assertIn(path, self.check() or "")
                self.pin = self.git("rev-parse", "HEAD").strip()

    def test_a_module_a_hook_newly_imports_counts(self):
        self.write("scripts/new.py", "y = 1\n")
        self.write("scripts/guard.py", "import cli\nimport new\n")
        self.commit("new import")
        self.assertIn("scripts/new.py", self.check() or "")

    def test_a_pin_not_on_main_fails(self):
        self.git("checkout", "-q", "-b", "side")
        self.write("roles/a.yml", "a: 3\n")
        self.pin = self.commit("side")
        self.git("checkout", "-q", "main")
        self.assertIn("not on deepops main", self.check() or "")

    def test_a_pin_deepops_does_not_have_fails(self):
        self.pin = "0" * 40
        self.assertIn("does not have", self.check() or "")


if __name__ == "__main__":
    unittest.main()
