"""One register per surface (owner, 2026-11-27): the rule pages, docs/policy/ai-agents.md
and the snippets it includes, are written in the concise -한다 style for people and AI
agents alike, so no sentence there ends politely (-니다, -세요, -요); the guides,
notices and Slack keep the polite register. The text a rule page includes from a
generated block counts too (rule:idle:plain, rule:sessions:plain), and so does the
agent rules' export, which is built from these pages."""

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import site_blocks  # noqa: E402

spec = importlib.util.spec_from_file_location("agent_rules", ROOT / "scripts" / "agent_rules.py")
agent_rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_rules)

RULE_PAGES = ("docs/policy/ai-agents.md", "snippets/job-rules.md", "snippets/gpu-session-rules.md",
              "snippets/io-rules.md")  # fmt: skip
# A sentence end: a word, closing punctuation or markup, then a space, the line's end, a
# table cell's bar or a marker. It is polite when it ends in -세요, -요 (어요, 아요, 해요,
# 까요) or -ㅂ니다, whose syllable before 니다 carries the final ㅂ (합니다, 됩니다,
# 있습니다), unlike the plain 아니다.
END = re.compile(r"([가-힣]+)[.!?)*_]*(?=\s|$|\||<)")


def _polite(word):
    if word.endswith(("세요", "어요", "아요", "해요", "까요")):
        return True
    return len(word) > 2 and word.endswith("니다") and (ord(word[-3]) - 0xAC00) % 28 == 17
FENCE = re.compile(r"^\s*(```|~~~)")


def prose(text):
    """TEXT's lines outside code blocks, generated markers dropped (their values kept)."""
    out, fence = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fence = not fence
            continue
        if not fence:
            out.append((n, site_blocks.MARKERS.sub("", line)))
    return out


def polite(text):
    return [f"{n}: {m.group(0)}" for n, line in prose(text) for m in END.finditer(line) if _polite(m.group(1))]


class Register(unittest.TestCase):
    def test_the_rule_pages_end_no_sentence_politely(self):
        found = [f"{p}:{v}" for p in RULE_PAGES for v in polite((ROOT / p).read_text())]
        self.assertEqual(found, [], "the rule pages are -한다 (polite endings belong to the guides)")

    def test_the_agent_rules_export_ends_no_sentence_politely(self):
        self.assertEqual(polite(agent_rules.export()), [])

    def test_the_rule_pages_blocks_have_their_plain_form(self):
        data = {"policy": {"idle_hours": 2, "cancel_after_hours": 6, "cancel_warn_hours": 1, "idle_notify": ["dm"],
                           "interactive_team_qos": True}}  # fmt: skip
        for policy in (data["policy"], dict(data["policy"], cancel_after_hours=0, idle_notify=[], interactive_team_qos=False)):
            d = {"policy": policy}
            self.assertEqual(polite(site_blocks.idle_rule(d, plain=True)), [])
            self.assertEqual(polite(site_blocks.sessions_rule(d, plain=True)), [])
            self.assertNotEqual(polite(site_blocks.idle_rule(d)), [], "the guides' form stays polite")

    def test_the_pattern(self):
        self.assertTrue(polite("확인합니다."))
        self.assertTrue(polite("| 쓰세요 | x |"))
        self.assertFalse(polite("확인한다. 쓰지 않는다. 그런 규칙이 아니다."))
        self.assertTrue(polite("있습니다. 됩니다."))
        self.assertFalse(polite("```\n# 확인합니다\n```\n"), "a comment in code is no sentence")


if __name__ == "__main__":
    unittest.main()
