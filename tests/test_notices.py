"""Tests for scripts/notices.py."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("notices", Path(__file__).resolve().parents[1] / "scripts/notices.py")
notices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notices)

GOOD = """---
date: 2026-11-19
slug: docs-site
categories: [notice, policy]
---

# 제목

요약 **강조**와 [규정](../../policy/index.md#디버깅), [연결](../../start/connect.md).

<!-- more -->

본문.
"""


class ParseTests(unittest.TestCase):
    def test_good(self):
        n = notices.parse("docs/news/posts/2026-11-19-docs-site.md", GOOD)
        self.assertEqual((n.slug, n.categories, n.title), ("docs-site", ["notice", "policy"], "제목"))
        self.assertEqual(n.url("https://x.example/docs/"), "https://x.example/docs/news/2026/11/19/docs-site/")

    def test_a_generated_value_reads_as_the_value(self):
        text = GOOD.replace("요약", "요약 <!-- BEGIN GENERATED: date:x -->2030-01-02<!-- END GENERATED: date:x -->부터", 1)
        summary = notices.parse("docs/news/posts/2026-11-19-docs-site.md", text).summary
        self.assertNotIn("GENERATED", summary)
        self.assertIn("2030-01-02부터", summary)

    def test_errors(self):
        cases = {
            "front matter": "# 제목\n",
            "date": GOOD.replace("2026-11-19\n", "yesterday\n"),
            "slug": GOOD.replace("slug: docs-site", "slug: 문서"),
            "categories": GOOD.replace("[notice, policy]", "[news]"),
            "title": GOOD.replace("# 제목", "제목"),
            "more": GOOD.replace("<!-- more -->", ""),
            "summary": GOOD.replace("요약 **강조**와 [규정](../../policy/index.md#디버깅), [연결](../../start/connect.md).", ""),
            "file name": GOOD,
        }
        for what, text in cases.items():
            path = "docs/news/posts/2026-11-19-other.md" if what == "file name" else "docs/news/posts/2026-11-19-docs-site.md"
            with self.assertRaises(ValueError, msg=what):
                notices.parse(path, text)

    def test_unwrap_joins_paragraph_lines_only(self):
        src = ("긴 문장이\n다음 줄로 이어집니다.\n\n- 항목 하나가\n  두 줄입니다\n- 항목 둘\n"
               "강제 줄바꿈\\\n다음\n```\ncode a\ncode b\n```\n끝")
        self.assertEqual(notices.unwrap(src),
                         "긴 문장이 다음 줄로 이어집니다.\n\n- 항목 하나가 두 줄입니다\n- 항목 둘 강제 줄바꿈\n"
                         "다음\n```\ncode a\ncode b\n```\n끝")

    def test_slack_blocks(self):
        n = notices.parse("docs/news/posts/2026-11-19-docs-site.md", GOOD)
        b = notices.blocks(n, "https://x.example/docs/")
        self.assertEqual(b[0]["text"]["text"], ":mega: 제목")
        self.assertEqual(b[1]["text"]["text"],
                         "요약 *강조*와 <https://x.example/docs/policy/#디버깅|규정>, "
                         "<https://x.example/docs/start/connect/|연결>.")
        wrapped = GOOD.replace("요약 **강조**와", "요약\n**강조**와")
        b = notices.blocks(notices.parse("docs/news/posts/2026-11-19-docs-site.md", wrapped), "https://x.example/docs/")
        self.assertNotIn("\n", b[1]["text"]["text"])
        self.assertEqual(b[2]["elements"][0]["url"], "https://x.example/docs/news/2026/11/19/docs-site/")
        self.assertIn("공지, 규정", b[3]["elements"][0]["text"])


class GitTests(unittest.TestCase):
    """check and announce against a throwaway repository."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        (self.root / "zensical.toml").write_text('[project]\nsite_url = "https://x.example/docs/"\n')
        (self.root / "docs/policy").mkdir(parents=True)
        (self.root / "docs/news/posts").mkdir(parents=True)
        (self.root / "docs/policy/index.md").write_text("# 규정\n")
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD").strip()
        notices.ROOT = self.root

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True).stdout

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def test_policy_change_needs_notice(self):
        (self.root / "docs/policy/index.md").write_text("# 규정\n\n바뀜\n")
        self.commit("policy")
        self.assertEqual(notices.check(self.base), 1)
        (self.root / "docs/news/posts/2026-11-19-docs-site.md").write_text(GOOD)
        self.commit("notice")
        self.assertEqual(notices.check(self.base), 0)

    def test_snippet_change_needs_notice(self):
        (self.root / "snippets").mkdir()
        (self.root / "snippets/rules.md").write_text("- rule\n")
        self.commit("rule block")
        self.assertEqual(notices.check(self.base), 1)

    def test_rule_neutral_edit_can_waive_the_notice(self):
        (self.root / "docs/policy/index.md").write_text("# 규정\n\n문장만 다듬음\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "docs: reword\n\nNo-Notice: wording only, no rule changed")
        self.assertEqual(notices.check(self.base), 0)

    def test_announce_dry_run_lists_added_notices_only(self):
        (self.root / "docs/news/posts/2026-11-19-docs-site.md").write_text(GOOD)
        self.commit("notice")
        head = self.git("rev-parse", "HEAD").strip()
        self.assertEqual(notices.announce(self.base, head, dry_run=True), 0)
        (self.root / "docs/news/posts/2026-11-19-docs-site.md").write_text(GOOD + "\n수정\n")
        self.commit("edit")
        self.assertEqual(notices.changed(head, "HEAD", status="A"), [])


if __name__ == "__main__":
    unittest.main()
