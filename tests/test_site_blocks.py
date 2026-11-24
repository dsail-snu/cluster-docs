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
        self.assertIn("**6시간** 동안 GPU를 쓰지 않은 잡은 자동으로 취소", site_blocks.idle_rule(on))
        self.assertIn("**1시간 전**", site_blocks.idle_rule(on))
        self.assertIn("자동으로 취소하지는 않습니다", site_blocks.idle_rule(off))

    def test_the_idle_rule_claims_no_channel_and_follows_whether_anyone_is_told(self):
        """How an idle job's owner is told is the cluster's setting (policy.idle_notify:
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
        for text in (site_blocks.service(with_(), "dashboard"), site_blocks.service(with_(), "overview")):
            self.assertNotRegex(text, r"<|https?://|도입")

    def test_the_sessions_rule_says_whether_submit_checks_it(self):
        on = dict(DATA, policy=dict(DATA["policy"], interactive_team_qos=True))
        off = dict(DATA, policy=dict(DATA["policy"], interactive_team_qos=False))
        self.assertIn("거부됩니다", site_blocks.sessions_rule(on))
        self.assertNotIn("거부", site_blocks.sessions_rule(off))

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
        self.assertEqual(site_blocks.dated_outside_news(), [], "this site's pages")

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
        self.assertIn("아직 없습니다", site_blocks.models(wrong))

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


if __name__ == "__main__":
    unittest.main()
