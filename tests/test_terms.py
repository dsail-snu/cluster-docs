"""One Korean word for each thing people read, as deepops' glossary gives it
(scripts/deepops/terms_ko.yml, exported to data/site.json terms): no tracked file uses
a refused variant. The owner asked for the glossary on 2026-11-27, after "GPU를 쓰지 않는
잡" read as a CPU-only job. The name of a job whose allocated GPUs all sat idle is also
site_blocks.IDLE_JOB, which pages write through the term:idle_job block.

Titles are nouns, sentences stay descriptive (owner, 2026-11-27): an entry's title form
(as 중단 노드 beside 쓸 수 없는 노드) in every title, its sentence form everywhere
else, the title idioms (title_not) refused in titles, and no title ending a sentence
outside the exempt files (site.json titles). A title here is a Markdown heading, a
bold-only line or a list item's bold lead, a table header row, or a Slack guide's title,
table or bookmark (slack/*.md front matter), as deepops' scripts/deepops/terms.py reads
them; code blocks hold none."""

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
ENTRIES = [dict(e, patterns=[re.compile(p) for p in e["not"]], title_patterns=[re.compile(p) for p in e.get("title_not", [])])
           for e in DATA["terms"] if not e.get("scope")]  # fmt: skip
FORMED = [e for e in ENTRIES if e.get("title") and e.get("use") and e["title"] != e["use"]]
ENDINGS = re.compile(DATA["titles"]["endings"])
EXEMPT = tuple(x["path"] for x in DATA["titles"]["exempt"])
# The files that quote the variants: the exported glossary and this test.
QUOTING = {"data/site.json", "tests/test_terms.py"}
# A generated block's value comes from the data (term:idle_job, a rules table), not a hand.
GENERATED = re.compile(r"<!-- BEGIN GENERATED: (\S+) -->.*?<!-- END GENERATED: \1 -->", re.S)
# The commands the cluster retired, each to what took its place (site.json
# commands_retired), and the one pattern that finds a mention (commands_retired_pattern,
# group 1 the old name), as deepops' own check applies them. Notices keep theirs: they
# say what was true when they were posted.
RETIRED = DATA["commands_retired"]
RETIRED_AT = re.compile(DATA["commands_retired_pattern"])
NOTICES = "docs/news/posts/"
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


def titles(rel, lines):
    """[(line number, title)] of the title positions of a Markdown file."""
    out, code = [], site_blocks.in_code(lines)
    front = lines[:1] == ["---"]
    end = lines.index("---", 1) if front and "---" in lines[1:] else -1
    for i, line in enumerate(lines):
        if 0 < i < end:
            m = re.match(r"(title|table|bookmark):\s*(.*)", line)
            if m:
                out.append((i + 1, m.group(2).split("|")[1].strip() if m.group(1) == "bookmark" else m.group(2)))
            continue
        if code[i]:
            continue
        m = (re.match(r"\s*#{1,6}\s+(.*)", line) or re.match(r"\s*(?:[-*]\s+)?\*\*([^*]+)\*\*\s*:?\s*$", line)
             or re.match(r"\s*[-*]\s+\*\*([^*]+)\*\*\s*:", line))  # fmt: skip
        if m:
            out.append((i + 1, m.group(1)))
        elif line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            out += [(i + 1, c.strip()) for c in line.strip().strip("|").split("|")]
    return out


def bare(title):
    """TITLE as read: no markers, code, links, heading attributes, closing parenthetical
    or punctuation."""
    text = site_blocks.MARKERS.sub("", title)
    text = re.sub(r"`[^`]*`|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", text)
    text = re.sub(r"\s*\{[^}]*\}\s*$", "", text.strip())
    text = re.sub(r"\s*\([^()]*\)\s*$", "", text)
    return text.rstrip(".:!? ").strip()


def title_problems(rel, text):
    lines, out = text.split("\n"), []
    found = titles(rel, lines)
    by_line = {}
    for n, t in found:
        by_line.setdefault(n, []).append(t)
        shown = bare(t)
        out += [f"{rel}:{n}: title {t!r} -> {e['title']}" for e in FORMED if e["use"] in shown]
        out += [f"{rel}:{n}: title {t!r} -> {e['title']}" for e in ENTRIES for p in e["title_patterns"] if p.search(shown)]
        if re.search("[\uac00-\ud7a3]", shown) and ENDINGS.search(shown) and not rel.startswith(EXEMPT):
            out.append(f"{rel}:{n}: title {t!r} ends a sentence -> a noun")
    for n, line in enumerate(lines, 1):
        rest = site_blocks.MARKERS.sub("", line)
        for t in by_line.get(n, []):
            rest = rest.replace(bare(t), "")
        out += [f"{rel}:{n}: {e['title']!r} outside a title -> {e['use']}" for e in FORMED if e["title"] in rest]
    return out


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
                 for n, line in enumerate(GENERATED.sub("", text).splitlines(), 1)
                 if site_blocks.IDLE_JOB in line]  # fmt: skip
        self.assertEqual(typed, [], "write <!-- BEGIN GENERATED: term:idle_job --> instead")

    def test_no_page_names_a_retired_command(self):
        found = [f"{p}:{n}: {m.group(1)!r} -> {RETIRED[m.group(1)]}" for p, text in texts()
                 if p.startswith((*PAGES, "scripts/")) and not p.startswith(NOTICES)
                 for n, line in enumerate(text.splitlines(), 1) for m in RETIRED_AT.finditer(line)]  # fmt: skip
        self.assertEqual(found, [], "name the command that took its place (site.json commands_retired)")

    def test_the_retired_pattern_finds_a_mention_and_passes_look_alikes(self):
        self.assertTrue(RETIRED, "data/site.json commands_retired (deepops scripts/docs/site_facts.py)")
        old = next(iter(RETIRED))
        for line in (f"`{old}`", f"{old} --top 5", f"<!-- BEGIN GENERATED: command:{old} -->"):
            self.assertEqual([m.group(1) for m in RETIRED_AT.finditer(line)], [old], line)
        for line in (f"{old}.py", f"#{old}", f"x-{old}", f"{old}-report", f"/{old}"):
            self.assertFalse(RETIRED_AT.search(line), line)

    def test_titles_are_nouns_and_sentences_stay_descriptive(self):
        found = [v for p, text in texts() if p.endswith(".md") for v in title_problems(p, text)]
        self.assertEqual(found, [], "titles are nouns (deepops scripts/deepops/terms_ko.yml, titles)")

    def test_the_title_rules_catch_what_they_should(self):
        self.assertTrue(title_problems("a.md", "## 쓸 수 없는 노드\n"))
        self.assertTrue(title_problems("a.md", "중단 노드는 잡을 받지 않습니다.\n"))
        self.assertTrue(title_problems("a.md", "# 사용 규정이 바뀝니다\n"))
        self.assertTrue(title_problems("a.md", "| 명령 | 하는 일 |\n|---|---|\n"))
        self.assertFalse(title_problems("a.md", "## 중단 노드 { #old }\n\n쓸 수 없는 노드는 잡을 받지 않습니다.\n"))
        self.assertFalse(title_problems("a.md", "```bash\n# 확인합니다\n```\n"))
        self.assertFalse(title_problems(EXEMPT[0], "### 밖에서 접속이 안 돼요\n"))

    def test_the_name_is_the_glossarys_and_the_rule_says_allocated(self):
        glossary = next(e for e in DATA["terms"] if e.get("id") == "idle_job")
        self.assertEqual(site_blocks.IDLE_JOB, glossary["use"], "a noun in titles and sentences alike")
        data = {"policy": {"idle_hours": 2, "cancel_after_hours": 6, "cancel_warn_hours": 1, "idle_notify": ["dm"]}}
        for policy in (data["policy"], dict(data["policy"], cancel_after_hours=0)):
            rule = site_blocks.idle_rule({"policy": policy})
            self.assertEqual(refused(rule), [], rule)
            self.assertIn("할당받은 GPU를", rule)
        self.assertEqual(site_blocks.body(data, "term:idle_job"), site_blocks.IDLE_JOB + "\n")


if __name__ == "__main__":
    unittest.main()
