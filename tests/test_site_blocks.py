"""scripts/site_blocks.py: generated blocks come from data/site.json, and --check fails
on a page whose block no longer matches."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import site_blocks  # noqa: E402

DATA = {
    "commands": {"tool": {"summary": "s", "usage": "tool", "options": [
        {"flags": ["-a", "--all"], "metavar": "", "help": "everything"},
        {"flags": ["-u", "--user"], "metavar": "LOGIN", "help": "one person | theirs"}]}},
    "policy": {"stale_days": 60, "grace_days": 14, "warn_fraction": 0.9, "idle_hours": 2,
               "cancel_after_hours": 6, "cancel_warn_hours": 1, "idle_notify": ["mention"],
               "interactive_team_qos": True},
    "slurm": {"kill_wait_seconds": 30, "preempt_grace_seconds": 30, "sigkill_after_seconds": 60},
    "quota": {"/data": {"block_hard_tib": 2.0, "block_warn_tib": 1.8, "inode_hard": 6000000, "inode_warn": 5400000}},
    "reports": {"usage": "hourly", "weekly": "Mon *-*-* 09:00:00", "disk": "*-*-* 08:30:00"},
}  # fmt: skip


class Blocks(unittest.TestCase):
    def test_a_block_is_filled_from_the_data(self):
        page = "x\n<!-- BEGIN GENERATED: options:tool -->\nold\n<!-- END GENERATED: options:tool -->\ny\n"
        out = site_blocks.fill(page, DATA)
        self.assertIn("| `-a`, `--all` | everything |", out)
        self.assertIn("`--user` `LOGIN`", out)
        self.assertIn("one person \\| theirs", out)
        self.assertNotIn("old", out)

    def test_the_idle_rule_says_whether_a_cancel_is_active(self):
        on = dict(DATA, policy=dict(DATA["policy"], idle_hours=2, cancel_after_hours=6, cancel_warn_hours=1,
                                    idle_notify=["mention"]))  # fmt: skip
        off = dict(DATA, policy=dict(on["policy"], cancel_after_hours=0))
        self.assertIn("할당받은 GPU를 **6시간** 동안 쓰지 않은 잡은 자동으로 취소", site_blocks.idle_rule(on))
        self.assertIn("**1시간 전**", site_blocks.idle_rule(on))
        self.assertIn("자동으로 취소하지는 않습니다", site_blocks.idle_rule(off))

    def test_the_idle_rule_claims_no_channel_and_follows_whether_anyone_is_told(self):
        """How the owner of a job leaving its GPUs idle is told is the cluster's setting (policy.idle_notify:
        a mention in the hourly report, or a DM); the rule never names one, and with none
        set it says the report only lists the job."""
        def told(how):
            return site_blocks.idle_rule(dict(DATA, policy=dict(DATA["policy"], idle_notify=how)))
        for how in (["mention"], ["dm"], ["mention", "dm"]):
            self.assertIn("쓰지 않으면** 알려 드립니다.", told(how))
            self.assertNotIn("DM", told(how))
            self.assertNotIn("멘션", told(how))
        self.assertIn("리포트에 표시됩니다", told([]))
        with self.assertRaisesRegex(ValueError, "idle_rule"):
            told(["email"])

    def test_the_services_as_the_cluster_runs_them_and_never_an_address(self):
        def with_(**svc):
            base = {"portal": True, "overview": "클러스터", "menu": ["Grafana"], "dashboard": True}
            return dict(DATA, services={**base, **svc})
        self.assertIn("상단 메뉴의 **Grafana**", site_blocks.service(with_(), "dashboard"))
        self.assertIn("**클러스터** 페이지", site_blocks.service(with_(), "overview"))
        self.assertIn("관리자에게 문의", site_blocks.service(with_(portal=False), "dashboard"))
        self.assertIn("운영하지 않습니다", site_blocks.service(with_(dashboard=False), "dashboard"))
        self.assertIn("`sq`", site_blocks.service(with_(portal=False, overview=""), "overview"))
        self.assertIn("홈 탭", site_blocks.service(with_(job_notices=True, bot=True), "job_notices"))
        self.assertNotIn("홈 탭", site_blocks.service(with_(job_notices=True, bot=False), "job_notices"))
        self.assertIn("보내지 않습니다", site_blocks.service(with_(job_notices=False), "job_notices"))
        for text in (site_blocks.service(with_(), "dashboard"), site_blocks.service(with_(), "overview")):
            self.assertNotRegex(text, r"<|https?://|도입")

    def test_the_portal_lists_what_its_menu_gives(self):
        svc = {"portal": True, "overview": "클러스터", "menu": ["Grafana"], "dashboard": True,
               "portal_groups": ["apps", "files", "jobs", "clusters"], "portal_files": ["/home"]}
        text = site_blocks.portal(dict(DATA, services=svc))
        self.assertIn("`/home` 아래", text)
        self.assertIn("**Grafana**", text)
        self.assertNotIn("apps", text.lower(), "a group the role gives no app is not shown")
        self.assertNotRegex(text, r"https?://")
        self.assertIn("운영하지 않습니다", site_blocks.portal(dict(DATA, services={**svc, "portal": False})))

    def test_every_dashboard_the_cluster_ships_has_its_line(self):
        site = __import__("json").loads((Path(__file__).resolve().parents[1] / "data" / "site.json").read_text())
        for board in site["services"]["dashboards"]:
            self.assertIn(board["uid"], site_blocks.DASHBOARDS, f"say what {board['title']} shows")
        svc = {"dashboard": False, "dashboards": site["services"]["dashboards"]}
        self.assertIn("운영하지 않습니다", site_blocks.dashboards(dict(DATA, services=svc)))

    def test_the_sessions_rule_says_whether_submit_checks_it(self):
        on = dict(DATA, policy=dict(DATA["policy"], interactive_team_qos=True))
        off = dict(DATA, policy=dict(DATA["policy"], interactive_team_qos=False))
        self.assertIn("거부됩니다", site_blocks.sessions_rule(on))
        self.assertNotIn("거부", site_blocks.sessions_rule(off))

    def test_the_limits_appear_when_the_cluster_sets_them(self):
        none = dict(DATA, quota={})
        self.assertIn("상한은 없습니다", site_blocks.quota_section(none))
        self.assertIn("디스크 리포트(매일 08:30)", site_blocks.quota_section(none))
        self.assertEqual(site_blocks.quota_each(none, "/scratch"), "\n")
        q = {"/home": {"block_hard_tib": 10.0, "block_warn_tib": 9.0, "inode_hard": 30000000, "inode_warn": 27000000}}
        on = dict(DATA, quota=q, policy=dict(DATA["policy"], submit_holds_disk=True))
        text = site_blocks.quota_section(on)
        self.assertIn("| `/home` | 10 TB | 3,000만개 |", text)
        self.assertIn("새 잡 제출도 보류", text)
        self.assertNotIn("보류", site_blocks.quota_section(dict(on, policy=dict(on["policy"], submit_holds_disk=False))))
        self.assertEqual(site_blocks.quota_each(on, "/home"), "한 사람에 10 TB까지 쓰실 수 있고, \n")

    def test_the_bot_as_the_cluster_runs_it(self):
        bot = {"command": "/c", "subcommands": [{"name": n, "help": n} for n in ("unban", "leave", "data", "help")]}
        on = dict(DATA, bot=bot, services={"bot": True})
        off = dict(DATA, bot=bot, services={"bot": False})
        self.assertIn("`/c unban`", site_blocks.bot(on, "unban"))
        self.assertIn("관리자에게", site_blocks.bot(off, "unban"))
        self.assertIn("## 봇으로 하는 신청", site_blocks.bot(on, "section"))
        self.assertEqual(site_blocks.bot(off, "section"), "\n")
        for name in ("unban", "leave", "data"):
            self.assertNotIn("/c", site_blocks.bot(off, name))
        with self.assertRaises(SystemExit):
            site_blocks.bot(dict(on, bot={"command": "/c", "subcommands": []}), "unban")

    def test_the_cpu_knobs_as_the_cluster_sets_them(self):
        knobs = [{"name": "OMP_NUM_THREADS", "kind": "threads", "value": "{n}"},
                 {"name": "MAKEFLAGS", "kind": "build", "value": "-j{n}"},
                 {"name": "NVCC_THREADS", "kind": "build", "value": "1"}]
        text = site_blocks.threads_section(dict(DATA, threads={"variables": knobs}))
        self.assertIn("## CPU 스레드 수와 빌드 병렬 수", text)
        self.assertIn("| `OMP_NUM_THREADS` | 계산 스레드 | CPU 수 |", text)
        self.assertIn("| `MAKEFLAGS` | 빌드 병렬 수 | `-j` + CPU 수 |", text)
        self.assertIn("| `NVCC_THREADS` | 빌드 병렬 수 | `1` |", text)
        self.assertEqual(site_blocks.threads_section(dict(DATA, threads={"variables": []})), "\n")
        with self.assertRaises(SystemExit):
            site_blocks.threads_section(dict(DATA, threads={"variables": [dict(knobs[0], kind="io")]}))

    def test_a_date_block_outside_the_notices_is_refused(self):
        """A guide states the rule as it is; when it changes is a notice's (owner 2026-11-25)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/news/posts").mkdir(parents=True)
            (root / "docs/guide").mkdir()
            (root / "snippets").mkdir()
            block = "<!-- BEGIN GENERATED: day:x --><!-- END GENERATED: day:x -->부터"
            (root / "docs/news/posts/2030-01-01-a.md").write_text(block)
            (root / "docs/guide/a.md").write_text("상한이 있습니다.")
            self.assertEqual(site_blocks.dated_outside_news(root), [])
            (root / "docs/guide/a.md").write_text(block.replace("day:", "date:"))
            self.assertEqual(site_blocks.dated_outside_news(root), [Path("docs/guide/a.md")])
            # A date typed by hand is refused the same way, in a guide, a snippet or a Slack guide.
            (root / "docs/guide/a.md").write_text("상한이 있습니다.")
            (root / "slack").mkdir()
            for page, text in (("snippets/b.md", "2030-01-05부터 적용"), ("slack/c.md", "12월 9일부터")):
                (root / page).write_text(text)
                self.assertEqual(site_blocks.dated_outside_news(root), [Path(page)])
                (root / page).write_text("상한이 있습니다.")
        self.assertEqual(site_blocks.dated_outside_news(), [], "this site's pages")

    def test_a_report_says_when_it_runs_in_the_channels_words(self):
        page = "<!-- BEGIN GENERATED: reports:usage --><!-- END GENERATED: reports:usage -->, " \
               "<!-- BEGIN GENERATED: reports:weekly --><!-- END GENERATED: reports:weekly -->"  # fmt: skip
        self.assertIn("매시간<", site_blocks.fill(page, DATA))
        self.assertIn("월요일 09:00<", site_blocks.fill(page, DATA))
        with self.assertRaises(KeyError):
            site_blocks.body(DATA, "reports:nightly")

    def test_a_day_is_written_with_its_weekday(self):
        self.assertEqual(site_blocks.day("2026-11-25"), "2026-11-25(수)")
        self.assertEqual(site_blocks.day("2026-12-06"), "2026-12-06(일)")

    def test_the_login_limits_as_a_sentence(self):
        data = dict(DATA, login={"cpus": 8, "memory_gib": 64, "tasks": 4096})
        self.assertEqual(site_blocks.login_limits(data),
                         "로그인 노드에는 한 사람당 CPU 8개, 메모리 64 GB, 프로세스 4,096개까지 쓰실 수 있도록 제한이 걸려 있습니다.\n")
        self.assertIn("걸려 있지 않습니다", site_blocks.login_limits(dict(DATA, login={})))

    def test_the_shared_model_cache_is_read_by_name_never_as_hf_hub_cache(self):
        """The shared cache is writer-owned: a page telling people their HF_HUB_CACHE
        points there sends every download of an uncached file into a refusal."""
        shared = dict(DATA, environment=[{"name": "SHARED_HF_HUB_CACHE", "login": "/srv/hub", "job": ""}])
        text = site_blocks.models(shared)
        self.assertIn("`/srv/hub`", text)
        self.assertIn("`SHARED_HF_HUB_CACHE`가 그곳을 가리킵니다", text)
        self.assertNotIn("`HF_HUB_CACHE`가 그곳을", text)
        wrong = dict(DATA, environment=[{"name": "HF_HUB_CACHE", "login": "/srv/hub", "job": ""}])
        self.assertIn("캐시는 없습니다", site_blocks.models(wrong))

    def test_quota_limits_in_tb_and_korean_counts(self):
        page = "<!-- BEGIN GENERATED: quota:/data:block_hard --><!-- END GENERATED: quota:/data:block_hard -->, " \
               "<!-- BEGIN GENERATED: quota:/data:inode_hard --><!-- END GENERATED: quota:/data:inode_hard -->, " \
               "<!-- BEGIN GENERATED: quota:ratio --><!-- END GENERATED: quota:ratio -->"  # fmt: skip
        out = site_blocks.fill(page, DATA)
        self.assertIn("-->2 TB<!--", out)
        self.assertIn("-->600만<!--", out)
        self.assertIn("-->300만<!--", out)

    def test_policy_values(self):
        page = "<!-- BEGIN GENERATED: policy:warn_percent -->\n<!-- END GENERATED: policy:warn_percent -->"
        self.assertIn("90%", site_blocks.fill(page, DATA))

    def test_an_inline_value_stays_on_its_line(self):
        page = "- 유예 <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->9<!-- END GENERATED: slurm:preempt_grace_seconds -->초\n"
        self.assertEqual(
            site_blocks.fill(page, DATA),
            "- 유예 <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->30<!-- END GENERATED: slurm:preempt_grace_seconds -->초\n",
        )

    def test_a_block_in_a_list_item_keeps_its_indent(self):
        page = "- item\n  <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->\n  <!-- END GENERATED: slurm:preempt_grace_seconds -->\n"
        self.assertEqual(
            site_blocks.fill(page, DATA),
            "- item\n  <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->\n  30\n  <!-- END GENERATED: slurm:preempt_grace_seconds -->\n",
        )

    def test_the_site_pages_match_the_data(self):
        self.assertEqual(site_blocks.main(["--check"]), 0, "run scripts/site_blocks.py")


class EveryCommand(unittest.TestCase):
    """The reference listed options for sq and qos only; disk-usage, gpu-usage and
    scratch-space had none (2026-11-27 audit)."""

    def test_every_commands_options_under_its_heading(self):
        data = dict(DATA, commands={**DATA["commands"], "other": {"summary_ko": "x", "options": []}})
        out = site_blocks.body(data, "options:all")
        self.assertIn("#### `other`의 옵션", out)
        self.assertIn("#### `tool`의 옵션", out)
        self.assertIn("| `-a`, `--all` | everything |", out)

    def test_the_reference_shows_every_cluster_commands_options(self):
        import json

        real = json.loads(site_blocks.DATA.read_text())
        page = (site_blocks.ROOT / "docs/reference/slurm.md").read_text()
        for command in real["commands"]:
            self.assertIn(f"#### `{command}`의 옵션", page, "options:all on docs/reference/slurm.md")


if __name__ == "__main__":
    unittest.main()
