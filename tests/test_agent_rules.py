"""Tests for scripts/agent_rules.py and scripts/siteurls.py."""
import importlib.util
import re
import subprocess
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
        self.assertIn("--qos=<팀 QoS>", text)
        self.assertNotIn("--job-name=debug", text)

    def test_the_agents_get_the_prompt_and_people_the_page(self):
        """The prompt is the only text of the agent rules; the people's page says why and
        how and does not restate them (owner, 2026-11-27: README for people, AGENTS.md for
        agents). What only people need stays off the export."""
        text = agent_rules.export()
        for gone in ("지침 파일이나 메모리로", "8은 1, 2, 4로 나누어떨어지므로", "그래야 빈 GPU가",
                     "(사람과 AI 에이전트 모두)", "제출 전에 한 번 읽어"):  # fmt: skip
            self.assertNotIn(gone, text)
        for kept in ("--exclusive", "sbatch --wait", "--qos=<팀 QoS>", "--pty bash -i", "## 권장 사항\n", "uv",
                     "IP가 차단된 사고", "`--json`으로 읽는다"):  # fmt: skip
            self.assertIn(kept, text)
        self.assertNotIn("<!--", text.split("\n", 2)[2], "no marker reaches the agents")

    def test_the_page_shows_the_export_byte_for_byte(self):
        """What the owner approves on the site is what agents get, but for the links, which
        the export makes absolute (the site's address stays out of the repository)."""
        page = (agent_rules.ROOT / "docs" / agent_rules.PAGE).read_text()
        m = re.search(r"<!-- BEGIN GENERATED: agents:prompt -->\n(`{3,})markdown\n(.*?)\n\1\n<!-- END", page, re.S)
        self.assertTrue(m, "the people's page shows the prompt (agents:prompt)")
        shown = siteurls.absolute_links(m.group(2) + "\n", siteurls.site_url(), agent_rules.PAGE)
        self.assertEqual(shown, agent_rules.prompt())
        self.assertNotIn(siteurls.site_url(), page, "no address committed")
        self.assertTrue(agent_rules.export().endswith("\n\n" + agent_rules.prompt()))
        self.assertNotIn("--8<--", page, "the page includes no rule snippet: it does not restate them")

    def test_includes_and_admonitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/policy").mkdir(parents=True)
            (root / "snippets").mkdir()
            (root / "zensical.toml").write_text(f'[project]\nsite_url = "{BASE}"\n')
            (root / "snippets/a.md").write_text("- rule [ref](../reference/slurm.md#q)\n")
            (root / "snippets/agent-prompt.md").write_text(
                '# T\n\nbefore\n\n--8<-- "a.md"\n\nafter\n\n!!! note "Title"\n    body line\n\nend\n')
            out = agent_rules.export(root, "abc123")
            self.assertIn("(abc123)", out)
            self.assertIn("before\n\n- rule [ref](https://x.example/docs/reference/slurm/#q)\n\nafter", out)
            self.assertIn("> **Title**\n> body line\n\nend", out)
            (root / "snippets/agent-prompt.md").write_text('--8<-- "missing.md"\n')
            with self.assertRaises(FileNotFoundError):
                agent_rules.export(root)


class RevisionTests(unittest.TestCase):
    def test_the_stamp_is_the_last_commit_of_the_sources_not_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/policy").mkdir(parents=True)
            (root / "snippets").mkdir()
            (root / "snippets/a.md").write_text("- rule\n")
            (root / "snippets/agent-prompt.md").write_text('# T\n\n--8<-- "a.md"\n')
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
            subprocess.run([*git, "init", "-q"], check=True)
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-qm", "rules"], check=True)
            rules = subprocess.run([*git, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
            self.assertEqual([p.name for p in agent_rules.sources(root)], ["agent-prompt.md", "a.md"])
            (root / "other.md").write_text("x\n")
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-qm", "other page"], check=True)
            self.assertEqual(agent_rules.revision(root), rules, "another page's commit leaves the stamp")
            (root / "snippets/a.md").write_text("- rule 2\n")
            subprocess.run([*git, "commit", "-qam", "snippet"], check=True)
            self.assertNotEqual(agent_rules.revision(root), rules, "a snippet's commit moves it")


if __name__ == "__main__":
    unittest.main()
