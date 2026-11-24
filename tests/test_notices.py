"""Tests for scripts/notices.py."""
import importlib.util
import json
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

- **2026-11-19부터** 요약 **강조**와 [규정](../../policy/index.md#디버깅), [연결](../../start/connect.md).

<!-- more -->

본문.
"""


class ParseTests(unittest.TestCase):
    def test_good(self):
        n = notices.parse("docs/news/posts/2026-11-19-docs-site.md", GOOD)
        self.assertEqual((n.slug, n.categories, n.title), ("docs-site", ["notice", "policy"], "제목"))
        self.assertEqual(n.url("https://x.example/docs/"), "https://x.example/docs/news/2026/11/19/docs-site/")

    def test_a_generated_value_reads_as_the_value(self):
        text = GOOD.replace("**2026-11-19부터**", "**<!-- BEGIN GENERATED: date:x -->2030-01-02<!-- END GENERATED: date:x -->부터**", 1)
        summary = notices.parse("docs/news/posts/2026-11-19-docs-site.md", text).summary
        self.assertNotIn("GENERATED", summary)
        self.assertIn("**2030-01-02부터**", summary)

    def test_the_lead_is_a_short_title_and_dated_bullets_only(self):
        """What Slack shows is what people must newly know: no framing sentence, no
        undated item; a bullet's further lines are indented."""
        path = "docs/news/posts/2026-11-19-docs-site.md"
        two = GOOD.replace("<!-- more -->", "  이어지는 줄.\n- **2026-12-09부터** 둘째.\n\n<!-- more -->")
        self.assertIn("둘째", notices.parse(path, two).summary)
        grouped = GOOD.replace("- **2026-11-19부터** 요약", "- **2026-11-19부터**\n  - 요약")
        self.assertIn("  - 요약", notices.parse(path, grouped).summary)
        refused = {
            "framing": GOOD.replace("- **2026-11-19부터**", "바뀐 것을 알려 드립니다.\n\n- **2026-11-19부터**"),
            "undated": GOOD.replace("- **2026-11-19부터** ", "- "),
            "paragraph": GOOD.replace("- **2026-11-19부터** ", ""),
            "unbolded date": GOOD.replace("**2026-11-19부터**", "2026-11-19부터"),
            "long title": GOOD.replace("# 제목", "# " + "가" * (notices.TITLE_MAX + 1)),
        }
        for what, text in refused.items():
            with self.assertRaises(ValueError, msg=what):
                notices.parse(path, text)

    def test_a_link_to_another_notice_reads_as_its_page(self):
        """A notice file is served at news/YYYY/MM/DD/slug/, not at its path."""
        text = notices.absolute("- **2026-11-25부터** [지난 공지](2026-11-19-gpu-count-rule.md)", "https://x.example/docs/",
                                "news/posts/2026-11-25-rules-revised.md")  # fmt: skip
        self.assertIn("[지난 공지](https://x.example/docs/news/2026/11/19/gpu-count-rule/)", text)

    def test_a_lead_longer_than_slack_shows_is_refused_not_cut(self):
        n = notices.parse("docs/news/posts/2026-11-19-docs-site.md", GOOD)
        n.summary = "- **2026-11-19부터** " + "가" * notices.SECTION_MAX
        with self.assertRaisesRegex(ValueError, "longer than Slack shows"):
            notices.blocks(n, "https://x.example/docs/", "#help")

    def test_errors(self):
        cases = {
            "front matter": "# 제목\n",
            "date": GOOD.replace("2026-11-19\n", "yesterday\n"),
            "slug": GOOD.replace("slug: docs-site", "slug: 문서"),
            "categories": GOOD.replace("[notice, policy]", "[news]"),
            "title": GOOD.replace("# 제목", "제목"),
            "more": GOOD.replace("<!-- more -->", ""),
            "summary": GOOD.replace("- **2026-11-19부터** 요약 **강조**와 [규정](../../policy/index.md#디버깅), [연결](../../start/connect.md).", ""),
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
        b = notices.blocks(n, "https://x.example/docs/", "#help")
        self.assertEqual(b[0]["text"]["text"], ":mega: 제목")
        [items, invite] = b[1]["elements"]
        self.assertEqual((b[1]["type"], items["type"], items["style"], items["indent"]),
                         ("rich_text", "rich_text_list", "bullet", 0))
        self.assertEqual(items["elements"][0]["elements"], [
            {"type": "text", "text": "2026-11-19부터", "style": {"bold": True}},
            {"type": "text", "text": " 요약 "},
            {"type": "text", "text": "강조", "style": {"bold": True}},
            {"type": "text", "text": "와 "},
            {"type": "link", "url": "https://x.example/docs/policy/#디버깅", "text": "규정"},
            {"type": "text", "text": ", "},
            {"type": "link", "url": "https://x.example/docs/start/connect/", "text": "연결"},
            {"type": "text", "text": "."},
        ])
        self.assertEqual(invite, {"type": "rich_text_section", "elements": [
            {"type": "text", "text": "\n"}, {"type": "text", "text": "궁금한 점은 #help 채널에 편하게 남겨 주세요."}]})
        wrapped = GOOD.replace("요약 **강조**와", "요약\n  **강조**와")
        b = notices.blocks(notices.parse("docs/news/posts/2026-11-19-docs-site.md", wrapped), "https://x.example/docs/", "#help")
        self.assertEqual(len(b[1]["elements"][0]["elements"]), 1, "a wrapped item stays one item")
        self.assertEqual(b[2]["elements"][0]["url"], "https://x.example/docs/news/2026/11/19/docs-site/")
        self.assertIn("공지, 규정", b[3]["elements"][0]["text"])

    def test_the_lead_is_rich_text_with_no_markdown_left(self):
        """Slack's mrkdwn has no lists, and its *bold* closes only before a space or
        punctuation: "**팀 QoS**로" showed its stars. The lead is rich text, nested items
        a list one indent deeper, styles as styles."""
        lead = "- **2026-11-25(수)부터**\n  - **팀 QoS**로 실행해 주세요. `scratch-space`로 확인\n  - 둘째\n- **2026-12-09(수)부터** 셋째"
        block = notices.rich_text(lead)
        self.assertEqual([(e["type"], e.get("indent")) for e in block["elements"]],
                         [("rich_text_list", 0), ("rich_text_list", 1), ("rich_text_list", 0)])
        self.assertEqual(len(block["elements"][1]["elements"]), 2)
        first = block["elements"][1]["elements"][0]["elements"]
        self.assertEqual(first[0], {"type": "text", "text": "팀 QoS", "style": {"bold": True}})
        self.assertEqual(first[1]["text"], "로 실행해 주세요. ")
        self.assertEqual(first[2], {"type": "text", "text": "scratch-space", "style": {"code": True}})
        texts = [e.get("text", "") for el in block["elements"] for sec in el["elements"] for e in sec["elements"]]
        for t in texts:
            self.assertNotRegex(t, r"^\s*- |\*|`", t)


class GitTests(unittest.TestCase):
    """check and export against a throwaway repository."""
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
        (self.root / "data").mkdir()
        (self.root / "data/site.json").write_text('{"chat": {"channels": {"help": "#help"}}}')
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

    def test_export_writes_each_notice_as_its_slack_message(self):
        """The cluster bot posts what this file holds (deepops cluster_bot.notices): one
        entry per notice, its page as the id, its date, the Slack text and blocks."""
        (self.root / "docs/news/posts/2026-11-19-docs-site.md").write_text(GOOD)
        out = self.root / "site/notices.json"
        self.assertEqual(notices.export(out), 0)
        doc = json.loads(out.read_text())
        [n] = doc["notices"]
        self.assertEqual(n["id"], "https://x.example/docs/news/2026/11/19/docs-site/")
        self.assertEqual(n["date"], "2026-11-19")
        self.assertTrue(n["text"])
        self.assertEqual(n["blocks"][0]["type"], "header")
        self.assertEqual(n["blocks"][1]["type"], "rich_text")
        self.assertIn("#help 채널에 편하게 남겨 주세요.", json.dumps(n["blocks"][1], ensure_ascii=False))
        self.assertNotIn('"mrkdwn"', json.dumps(n["blocks"][:2]))

    def test_export_refuses_a_broken_notice(self):
        (self.root / "docs/news/posts/broken.md").write_text("no front matter\n")
        self.assertEqual(notices.export(self.root / "site/notices.json"), 1)
        self.assertFalse((self.root / "site/notices.json").exists())

    def test_no_slack_credential_is_read(self):
        source = Path(notices.__file__).read_text()
        self.assertNotIn("WEBHOOK", source)
        self.assertNotIn("urlopen", source)

if __name__ == "__main__":
    unittest.main()
