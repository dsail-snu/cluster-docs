"""A value the cluster's data owns (data/site.json) appears only as a generated value:
typed anywhere else in a page or snippet, it would go stale when the cluster changes."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import site_blocks  # noqa: E402

DATA = json.loads((ROOT / "data" / "site.json").read_text())


def typed_forms(data):
    """The ways a page would type each owned value: dates as written, periods with their unit."""
    p, s = data["policy"], data.get("slurm", {})
    forms = set(data.get("dates", {}).values())
    forms |= {f"{p['stale_days']}일", f"{p['grace_days']}일", f"{round(p['warn_fraction'] * 100)}%"}
    forms |= {f"{p['idle_hours']}시간"}
    if p.get("cancel_after_hours"):
        forms |= {f"{p['cancel_after_hours']}시간"}
    forms |= {f"{v}초" for k, v in s.items() if k.endswith("_seconds")}
    for q in data.get("quota", {}).values():
        forms |= {f"{q['block_hard_tib']:g} TB", f"{q['block_warn_tib']:g} TB"}
        forms |= {site_blocks.count(q["inode_hard"]), site_blocks.count(q["inode_warn"])}
    return forms


def outside_blocks(text):
    text = site_blocks.BLOCK.sub("", text)
    return site_blocks.INLINE.sub("", text)


class TypedValues(unittest.TestCase):
    def test_no_owned_value_is_typed_outside_a_generated_block(self):
        forms = typed_forms(DATA)
        pages = sorted((ROOT / "docs").rglob("*.md")) + sorted((ROOT / "snippets").rglob("*.md"))
        found = []
        for page in pages:
            if "/news/posts/" in page.as_posix() and page.name < "2026-11-25":
                continue  # an earlier notice is dated history
            text = re.sub(r"(?s)^---\n.*?\n---\n", "", page.read_text())  # front matter (a post's date)
            for form in forms:
                if re.search(rf"(?<![\d.]){re.escape(form)}", outside_blocks(text)):
                    found.append(f"{page.relative_to(ROOT)}: {form}")
        self.assertEqual(found, [], "render it with a generated block (scripts/site_blocks.py)")


if __name__ == "__main__":
    unittest.main()
