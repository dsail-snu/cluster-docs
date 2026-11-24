"""A sentence whose truth depends on the cluster's state is generated, never typed, so no
page can go stale: no stand-in for a value the cluster knows, no "coming soon" claim, and
the shared paths a page writes out (in commands too) are the cluster's (data/site.json)."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import site_blocks  # noqa: E402

DATA = json.loads((ROOT / "data" / "site.json").read_text())

# The stand-ins a page may write: what the reader fills in, and what each person is told
# privately with their account (start/connect.md). Anything else the cluster knows is a
# generated value: a stand-in for it (a portal address, a scratch path) goes stale.
READER = {
    "JOBID", "JOBID1", "JOBID2", "GPU 타입", "팀 QoS", "아이디", "개수", "장수", "초", "값", "경로", "이름",
    "모듈 이름", "버전", "이미지", "태그", "모델", ".sqsh 경로", "명령", "노드 이름", "시작 날짜", "주소",
    "레지스트리", "레지스트리 주소", "사용자명", "토큰", "Docker Hub 사용자명", "Docker Hub 액세스 토큰",
    "NGC API 키",
}  # fmt: skip
PRIVATE = {"로그인 주소", "SSH 포트"}
STANDIN = re.compile(r"<([^<>\n]{1,40})>")
# Words that make a sentence true only for a while: a service "being introduced", a change
# "planned", a state "for now". A dated change says its date instead ("**2026-12-09부터**").
TIME_BOUND = re.compile(r"도입 중|도입될|예정입니다|예정이|준비 중|지금은|현재는|아직 (?:없|지원|안 )|곧 (?:도입|적용|시작|바뀝|열립)")
# Wording that shows what administrators may and others may not (owner 2026-11-25): a page
# says what people use. Who approves a request, or whom to ask, stays.
PRIVILEGE = re.compile(r"관리자 전용|관리자만|일반 사용자는|권한이 없|admin-only", re.I)
# A shared path as the pages write it, in commands too, and where the cluster's value is.
PATHS = {"/scratch": "scratch", "/sw": "software", "/home/shared": "shared"}


def pages(news=True):
    for path in sorted((ROOT / "docs").rglob("*.md")) + sorted((ROOT / "snippets").rglob("*.md")) + sorted(
        (ROOT / "slack").glob("*.md")
    ):
        if news or "/news/posts/" not in path.as_posix():
            yield path


def prose(text):
    """TEXT without its generated blocks and HTML comments."""
    text = site_blocks.BLOCK.sub("", text)
    text = site_blocks.INLINE.sub("", text)
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def standins(text):
    found = set()
    for m in STANDIN.findall(prose(text)):
        if re.search(r"[가-힣]|^[A-Z][A-Z0-9 ]*$|^\.", m) and not re.match(r"(https?:|/)", m):
            found.add(m)
    return found


class SiteState(unittest.TestCase):
    def test_no_stand_in_for_a_value_the_cluster_knows(self):
        unknown = sorted(f"{p.relative_to(ROOT)}: <{s}>" for p in pages() for s in standins(p.read_text())
                         if s not in READER | PRIVATE)  # fmt: skip
        self.assertEqual(unknown, [], "generate it from data/site.json, or add a reader's value to READER")

    def test_a_portal_address_stand_in_is_refused(self):
        self.assertEqual(standins("대시보드는 `<포털 주소>`에서 엽니다."), {"포털 주소"})
        self.assertNotIn("포털 주소", READER | PRIVATE)

    def test_no_time_bound_claim_outside_the_notices(self):
        found = [f"{p.relative_to(ROOT)}: {m.group(0)}" for p in pages(news=False)
                 for m in TIME_BOUND.finditer(prose(p.read_text()))]  # fmt: skip
        self.assertEqual(found, [], "state the date, or generate the sentence from data/site.json")

    def test_the_old_portal_note_would_fail(self):
        self.assertTrue(TIME_BOUND.search("웹 포털은 도입 중입니다. 그전까지는 관리자가 공지합니다."))

    def test_no_wording_of_admin_privilege(self):
        found = [f"{p.relative_to(ROOT)}: {m.group(0)}" for p in pages(news=False)
                 for m in PRIVILEGE.finditer(prose(p.read_text()))]  # fmt: skip
        self.assertEqual(found, [], "say what people use (Enroot, Pyxis, Podman), not what administrators have")
        self.assertTrue(PRIVILEGE.search("`docker` 그룹은 관리자 전용이 되어, 일반 사용자는 Docker를 쓸 수 없습니다."))

    def test_the_shared_paths_written_out_are_the_clusters(self):
        for written, key in PATHS.items():
            used = [p for p in pages() if re.search(rf"(?<![\w/.]){re.escape(written)}(?![\w-])", prose(p.read_text()))]
            if used:
                self.assertEqual(DATA["paths"][key], written,
                                 f"{written} is written in {used[0].relative_to(ROOT)}; the cluster's is {DATA['paths'][key]}")


if __name__ == "__main__":
    unittest.main()
