"""One name for a job whose allocated GPUs all sat idle. "A job not using GPUs" alone
reads as a CPU-only job (owner, 2026-11-27), so the name says the GPUs were allocated
(site_blocks.IDLE_JOB, deepops' usage report's name), pages write it through the
term:idle_job block, and no tracked file keeps an old phrasing."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import site_blocks  # noqa: E402

OLD = re.compile(
    "|".join(
        (
            r"(?<!할당받은 )GPU를 (?:\S+ ){0,2}쓰지 않",  # 'GPU를 쓰지 않는 잡', '6시간 동안 GPU를 쓰지 않은 잡'
            r"GPU를 할당받아 두고",
            r"유휴 (?:GPU|잡)",
            r"쉬(?:는|던) 잡",  # '오래 쉬는 잡 알림'
            r"(?i:\bidle[- ](?:GPU )?(?:jobs?|rule)\b)",
        )
    )
)
TERM_BLOCK = re.compile(r"<!-- BEGIN GENERATED: term:idle_job -->[^\n]*?<!-- END GENERATED: term:idle_job -->")
PAGES = ("docs/", "snippets/", "slack/")


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.split("\0") if p and (ROOT / p).is_file()]


def texts():
    for path in tracked():
        if path.resolve() == Path(__file__).resolve():
            continue
        try:
            yield path.relative_to(ROOT).as_posix(), path.read_text()
        except UnicodeDecodeError:
            continue


class Terms(unittest.TestCase):
    def test_no_old_phrasing_is_left(self):
        found = [f"{p}:{n}: {line.strip()}" for p, text in texts()
                 for n, line in enumerate(text.splitlines(), 1) if OLD.search(line)]  # fmt: skip
        self.assertEqual(found, [], "say 할당받은 GPU (English: a job leaving its GPUs idle)")

    def test_pages_write_the_name_through_its_block(self):
        typed = [f"{p}:{n}" for p, text in texts() if p.startswith(PAGES)
                 for n, line in enumerate(text.splitlines(), 1)
                 if site_blocks.IDLE_JOB in TERM_BLOCK.sub("", line)]  # fmt: skip
        self.assertEqual(typed, [], "write <!-- BEGIN GENERATED: term:idle_job --> instead")

    def test_the_rule_and_the_name_say_allocated(self):
        self.assertEqual(site_blocks.IDLE_JOB, "할당받은 GPU를 쓰지 않는 잡")
        data = {"policy": {"idle_hours": 2, "cancel_after_hours": 6, "cancel_warn_hours": 1, "idle_notify": ["dm"]}}
        for policy in (data["policy"], dict(data["policy"], cancel_after_hours=0)):
            rule = site_blocks.idle_rule({"policy": policy})
            self.assertIsNone(OLD.search(rule), rule)
            self.assertIn("할당받은 GPU를", rule)
        self.assertEqual(site_blocks.body(data, "term:idle_job"), site_blocks.IDLE_JOB + "\n")

    def test_the_pattern_catches_the_old_and_passes_the_new(self):
        for old in ("GPU를 쓰지 않는 잡", "**6시간** 동안 GPU를 쓰지 않은 잡", "유휴 GPU 알림", "유휴 잡 취소", "오래 쉬는 잡 알림",
                    "Slurm 잡으로 GPU를 할당받아 두고", "the idle-GPU rule", "idle jobs"):  # fmt: skip
            self.assertRegex(old, OLD)
        for new in ("할당받은 GPU를 쓰지 않는 잡", "할당받은 GPU를 **6시간** 동안 쓰지 않은 잡", "idle_hours", "`idle*`"):
            self.assertNotRegex(new, OLD)


if __name__ == "__main__":
    unittest.main()
