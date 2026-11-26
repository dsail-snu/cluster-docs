"""One Korean word for each thing people read, as deepops' glossary gives it
(scripts/deepops/terms_ko.yml, exported to data/site.json terms): no tracked file uses
a refused variant. The owner asked for the glossary on 2026-11-27, after "GPU를 쓰지 않는
잡" read as a CPU-only job. The name of a job whose allocated GPUs all sat idle is also
site_blocks.IDLE_JOB, which pages write through the term:idle_job block."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import site_blocks  # noqa: E402

DATA = json.loads((ROOT / "data" / "site.json").read_text())
# A scoped entry names deepops paths; here every page is in scope of the others.
ENTRIES = [dict(e, patterns=[re.compile(p) for p in e["not"]]) for e in DATA["terms"] if not e.get("scope")]
# The files that quote the variants: the exported glossary and this test.
QUOTING = {"data/site.json", "tests/test_terms.py"}
TERM_BLOCK = re.compile(r"<!-- BEGIN GENERATED: term:idle_job -->[^\n]*?<!-- END GENERATED: term:idle_job -->")
PAGES = ("docs/", "snippets/", "slack/")


def tracked():
    """Every file git would commit: tracked, and new ones not yet added (a run before
    `git add` once passed over a new test that used a variant, 2026-11-27)."""
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout  # fmt: skip
    return [ROOT / p for p in out.split("\0") if p and (ROOT / p).is_file()]


def texts():
    for path in tracked():
        rel = path.relative_to(ROOT).as_posix()
        if rel in QUOTING:
            continue
        try:
            yield rel, path.read_text()
        except UnicodeDecodeError:
            continue


def refused(line):
    return [(m.group(0), e["use"]) for e in ENTRIES for p in e["patterns"] for m in [p.search(line)] if m]


class Terms(unittest.TestCase):
    def test_the_glossary_came_with_the_data(self):
        self.assertGreater(len(ENTRIES), 5, "data/site.json terms (deepops scripts/docs/site_facts.py)")

    def test_no_refused_variant_is_left(self):
        found = [f"{p}:{n}: {old!r} -> {use}" for p, text in texts()
                 for n, line in enumerate(text.splitlines(), 1) for old, use in refused(line)]  # fmt: skip
        self.assertEqual(found, [], "use the glossary's word (deepops scripts/deepops/terms_ko.yml)")

    def test_pages_write_the_idle_job_through_its_block(self):
        typed = [f"{p}:{n}" for p, text in texts() if p.startswith(PAGES)
                 for n, line in enumerate(text.splitlines(), 1)
                 if site_blocks.IDLE_JOB in TERM_BLOCK.sub("", line)]  # fmt: skip
        self.assertEqual(typed, [], "write <!-- BEGIN GENERATED: term:idle_job --> instead")

    def test_the_name_is_the_glossarys_and_the_rule_says_allocated(self):
        glossary = next(e["use"] for e in DATA["terms"] if e.get("id") == "idle_job")
        self.assertEqual(site_blocks.IDLE_JOB, glossary)
        data = {"policy": {"idle_hours": 2, "cancel_after_hours": 6, "cancel_warn_hours": 1, "idle_notify": ["dm"]}}
        for policy in (data["policy"], dict(data["policy"], cancel_after_hours=0)):
            rule = site_blocks.idle_rule({"policy": policy})
            self.assertEqual(refused(rule), [], rule)
            self.assertIn("할당받은 GPU를", rule)
        self.assertEqual(site_blocks.body(data, "term:idle_job"), site_blocks.IDLE_JOB + "\n")


if __name__ == "__main__":
    unittest.main()
