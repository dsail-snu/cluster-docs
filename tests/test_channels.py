"""scripts/channels.py: the Slack channels' guides from slack/<role>.md, every fact from
data/site.json, every link to a page that exists, within Slack's limits."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import channels  # noqa: E402

DATA = json.loads((ROOT / "data/site.json").read_text())
GUIDE = """---
purpose: Notices only
topic: Ask in [[#help]]
title: About
table: notices
bookmark: :books: | Docs | index.md
---
# News

Ask [[admins]] with [[/cluster]]; see [storage](guide/storage.md).
"""


class Guides(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "slack").mkdir()
        (self.root / "docs/guide").mkdir(parents=True)
        (self.root / "docs/index.md").write_text("# x\n")
        (self.root / "docs/guide/storage.md").write_text("# x\n")
        (self.root / "zensical.toml").write_text('[project]\nsite_url = "https://x.example/docs/"\n')
        self.data = dict(DATA, chat={"channels": {"announce": "#news", "help": "#ask"}, "admin_group": "@ops"})

    def tearDown(self):
        self.tmp.cleanup()

    def guide(self, text=GUIDE, role="announce"):
        (self.root / "slack" / f"{role}.md").write_text(text)
        return channels.document(self.data, self.root)["channels"][role]

    def test_facts_filled_links_absolute_and_channels_left_for_the_bot(self):
        g = self.guide()
        self.assertEqual(g["topic"], "Ask in [[#help]]")
        self.assertIn("Ask @ops with " + DATA["bot"]["command"], g["canvas"]["markdown"])
        self.assertIn("[storage](https://x.example/docs/guide/storage/)", g["canvas"]["markdown"])
        self.assertEqual(g["bookmarks"], [{"title": "Docs", "url": "https://x.example/docs/", "emoji": ":books:"}])

    def test_a_link_to_a_missing_page_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no page docs/guide/gone.md"):
            self.guide(GUIDE.replace("guide/storage.md", "guide/gone.md"))

    def test_an_unknown_placeholder_or_channel_is_refused(self):
        with self.assertRaisesRegex(ValueError, "unknown placeholder"):
            self.guide(GUIDE.replace("[[admins]]", "[[nobody]]"))
        with self.assertRaisesRegex(ValueError, "no such channel role"):
            self.guide(GUIDE.replace("[[#help]]", "[[#lobby]]"))

    def test_a_topic_over_slacks_limit_counts_the_channel_names(self):
        long = "x" * 245 + " [[#help]]"  # 245 + 1 + "#ask" = 250: fits
        self.guide(GUIDE.replace("Ask in [[#help]]", long))
        with self.assertRaisesRegex(ValueError, "251 characters"):
            self.guide(GUIDE.replace("Ask in [[#help]]", "y" + long))

    def test_a_malformed_source_is_refused(self):
        with self.assertRaisesRegex(ValueError, "bookmark is"):
            self.guide(GUIDE.replace(":books: | Docs | index.md", "Docs | index.md"))
        (self.root / "slack/announce.md").unlink()
        with self.assertRaisesRegex(ValueError, "named after one of"):
            self.guide(GUIDE, role="lobby")

    def test_an_english_channel_refuses_korean_typed_or_filled(self):
        """The administrators' channel is English (owner, 2026-11-28); its guide was Korean."""
        english = GUIDE.replace("[[admins]]", "[[admins]] or [[term:idle_job]]")
        with self.assertRaisesRegex(ValueError, "admin: the channel is English"):
            self.guide(english, role="admin")
        with self.assertRaisesRegex(ValueError, "the channel is English"):
            self.guide(GUIDE.replace("title: About", "title: 안내"), role="admin")
        self.data["chat"] = dict(self.data["chat"], admin_group="")
        self.assertIn("Ask the administrators with", self.guide(role="admin")["canvas"]["markdown"])
        self.assertIn("관리자", self.guide(GUIDE.replace("Ask", "묻기"))["canvas"]["markdown"])

    def test_schedules_as_korean_reads_them(self):
        self.assertEqual(channels.when("hourly"), "매시간")
        self.assertEqual(channels.when("Mon *-*-* 09:00:00"), "월요일 09:00")
        self.assertEqual(channels.when("*-*-* 09:30"), "매일 09:30")
        with self.assertRaisesRegex(ValueError, "teach"):
            channels.when("*:0/5")


class TheRealGuides(unittest.TestCase):
    def test_every_channel_has_its_guide_and_it_builds(self):
        doc = channels.document(DATA)["channels"]
        self.assertEqual(set(doc), set(channels.ROLES))
        for role, g in doc.items():
            self.assertNotRegex(json.dumps(g, ensure_ascii=False), r"\[\[(?!#)", role)

    def test_the_help_pages_table_names_the_clusters_channels(self):
        table = channels.help_table(DATA)
        self.assertIn(f"`{DATA['chat']['channels']['help']}`", table)
        self.assertNotIn(DATA["chat"]["channels"]["admin"], table, "the admin channel is not listed")
        self.assertNotIn("[[", table, "a guide's table line is filled like its other fields")

    def test_the_status_channel_lists_its_reports_from_the_data(self):
        """slack/status.md listed its report kinds by hand, one of them under an old name."""
        names = channels.fill("[[reports:names]]", DATA)
        self.assertEqual(names, ", ".join(short for short, _ in channels.REPORTS.values()))
        status = channels.document(DATA)["channels"]["status"]
        self.assertIn(names, json.dumps(status, ensure_ascii=False))
        self.assertIn(channels.site_blocks.IDLE_JOB, json.dumps(status, ensure_ascii=False))

    def test_the_reports_are_a_list_by_their_cards_titles(self):
        """The status canvas held the reports as a table under an old weekly name (주간
        요약); lists are bullets, each report by its card's title (deepops cluster_tools)."""
        listed = channels.fill("[[reports]]", DATA).splitlines()
        self.assertEqual([line.split("**")[1] for line in listed], [t for t, _ in channels.REPORTS.values()])
        self.assertTrue(all(line.startswith("- **") for line in listed), listed)
        self.assertIn("주간 GPU 사용", [t for t, _ in channels.REPORTS.values()])

    def test_each_guide_is_in_its_channels_language(self):
        for role, g in channels.document(DATA)["channels"].items():
            text = json.dumps(g, ensure_ascii=False)
            if role in channels.ENGLISH:
                self.assertNotRegex(text, channels.HANGUL, role)
            else:
                self.assertRegex(text, channels.HANGUL, role)


if __name__ == "__main__":
    unittest.main()
