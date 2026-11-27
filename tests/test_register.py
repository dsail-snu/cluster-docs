"""One register per surface (owner, 2026-11-27): the agent rules (snippets/agent-prompt.md)
and the rule snippets it includes, which the people's pages include too, are written in
the concise -한다 style, so no sentence there ends politely (-니다, -세요, -요); the
pages people read (docs/policy/ai-agents.md among them), notices and Slack keep the
polite register. The text a rule snippet includes from a generated block counts too
(rule:idle:plain, rule:sessions:plain), and so does the agent rules' export."""

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

RULE_PAGES = ("snippets/agent-prompt.md", "snippets/job-rules.md", "snippets/gpu-session-rules.md",
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
# The -한다 voice (2026-11-27): a sentence there with no named subject reads as what the
# reader (a person or an agent) does, so an act only the cluster does (applying a rule,
# watching GPUs, enforcing at submit) either names its actor ("클러스터가", "시스템이") or
# is passive ("적용된다"). "이 규칙은 ... 적용한다" read as the reader applying the rule.
CLUSTER_ACTS = re.compile(r"(?:적용|감시|강제)한다$")
ACTOR = re.compile(r"[가-힣]+[이가]\s")
SENTENCE = re.compile(r"[^.!?]+[.!?]?")


def prose(text):
    """TEXT's lines outside code blocks, generated markers dropped (their values kept)."""
    lines = text.splitlines()
    return [(n, site_blocks.MARKERS.sub("", line)) for n, (line, code) in enumerate(zip(lines, site_blocks.in_code(lines)), 1)
            if not code]  # fmt: skip


def polite(text):
    return [f"{n}: {m.group(0)}" for n, line in prose(text) for m in END.finditer(line) if _polite(m.group(1))]


def actorless(text):
    """The sentences of TEXT doing the cluster's act with no actor named."""
    out = []
    for n, line in prose(text):
        for sentence in SENTENCE.findall(re.sub(r"^\s*(?:[-*>]|\d+\.)\s+", "", line)):
            bare = re.sub(r"[*_`]", "", sentence).strip().rstrip(".!?")
            if CLUSTER_ACTS.search(bare) and not ACTOR.search(bare + " "):
                out.append(f"{n}: {sentence.strip()}")
    return out


class Register(unittest.TestCase):
    def test_the_rule_pages_end_no_sentence_politely(self):
        found = [f"{p}:{v}" for p in RULE_PAGES for v in polite((ROOT / p).read_text())]
        self.assertEqual(found, [], "the rule pages are -한다 (polite endings belong to the guides)")

    def test_the_agent_rules_export_ends_no_sentence_politely(self):
        self.assertEqual(polite(agent_rules.export()), [])

    def test_the_clusters_acts_name_their_actor(self):
        found = [f"{p}:{v}" for p in RULE_PAGES for v in actorless((ROOT / p).read_text())]
        found += [f"AGENTS.md:{v}" for v in actorless(agent_rules.export())]
        self.assertEqual(found, [], "name the actor (클러스터가) or say it passively (적용된다)")

    def test_the_voice_pattern(self):
        self.assertTrue(actorless("이 규칙은 **공유 자원에 영향을 주는 행동**에만 적용한다."))
        self.assertTrue(actorless("- 자동 승인 모드에서도 그대로 적용한다."))
        self.assertTrue(actorless("GPU 사용률은 상시 감시한다."))
        self.assertFalse(actorless("이 규칙은 제출할 때 시스템이 강제로 적용한다."))
        self.assertFalse(actorless("클러스터가 GPU 사용률을 상시 감시한다. 이 규칙은 그대로 적용된다."))
        self.assertFalse(actorless("실패 횟수는 서버마다 따로 센다."), "the reader's own act")

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
