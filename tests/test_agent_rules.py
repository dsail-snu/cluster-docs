"""Tests for scripts/agent_rules.py and scripts/siteurls.py."""
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import siteurls  # noqa: E402

spec = importlib.util.spec_from_file_location("agent_rules", SCRIPTS / "agent_rules.py")
agent_rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_rules)

BASE = "https://x.example/docs/"


class SiteUrlTests(unittest.TestCase):
    def test_page_url(self):
        cases = {
            ("policy/ai-agents.md", "index.md#디버깅"): BASE + "policy/#디버깅",
            ("policy/ai-agents.md", "../reference/slurm.md#qos"): BASE + "reference/slurm/#qos",
            ("news/posts/x.md", "../../start/connect.md"): BASE + "start/connect/",
            ("news/posts/x.md", "../../start/connect.md#a-b"): BASE + "start/connect/#a-b",
            ("index.md", "help.md"): BASE + "help/",
            ("help.md", "index.md"): BASE,
            ("help.md", "https://slurm.schedmd.com/"): "https://slurm.schedmd.com/",
            ("help.md", "#here"): "#here",
        }
        for (page, target), expected in cases.items():
            self.assertEqual(siteurls.page_url(BASE, page, target), expected, (page, target))


class ExportTests(unittest.TestCase):
    def test_real_page_is_self_contained(self):
        text = agent_rules.export()
        self.assertTrue(text.startswith(agent_rules.MARKER))
        self.assertNotIn("--8<--", text)
        self.assertNotIn("!!! ", text)
        self.assertIsNone(re.search(r"\]\((?!https?://)[^)]*\)", text), "relative link left")
        # Rules pulled in from the shared snippets are present.
        self.assertIn("1, 2, 4, 8", text)
        self.assertIn("--job-name=debug", text)

    def test_includes_and_admonitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/policy").mkdir(parents=True)
            (root / "snippets").mkdir()
            (root / "zensical.toml").write_text(f'[project]\nsite_url = "{BASE}"\n')
            (root / "snippets/a.md").write_text("- rule [ref](../reference/slurm.md#q)\n")
            (root / "docs/policy/ai-agents.md").write_text(
                '# T\n\nbefore\n\n--8<-- "a.md"\n\nafter\n\n!!! note "Title"\n    body line\n\nend\n')
            out = agent_rules.export(root, "abc123")
            self.assertIn("(abc123)", out)
            self.assertIn("before\n\n- rule [ref](https://x.example/docs/reference/slurm/#q)\n\nafter", out)
            self.assertIn("> **Title**\n> body line\n\nend", out)
            (root / "docs/policy/ai-agents.md").write_text('--8<-- "missing.md"\n')
            with self.assertRaises(FileNotFoundError):
                agent_rules.export(root)


if __name__ == "__main__":
    unittest.main()
