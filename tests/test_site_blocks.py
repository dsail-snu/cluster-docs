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
               "cancel_after_hours": 6, "cancel_warn_hours": 1,
               "interactive_team_qos": True},
    "slurm": {"kill_wait_seconds": 30, "preempt_grace_seconds": 30, "sigkill_after_seconds": 60},
    "quota": {"/data": {"block_hard_tib": 2.0, "block_warn_tib": 1.8, "inode_hard": 6000000, "inode_warn": 5400000}},
    "reports": {"usage": "hourly", "weekly": "Mon *-*-* 09:00:00", "disk": "*-*-* 08:30:00"},
    "rules": [{"id": "disk", "active": True}],
}  # fmt: skip
UNLIMITED = [{"id": "disk", "active": False}]


class Blocks(unittest.TestCase):
    def test_a_block_is_filled_from_the_data(self):
        page = "x\n<!-- BEGIN GENERATED: options:tool -->\nold\n<!-- END GENERATED: options:tool -->\ny\n"
        out = site_blocks.fill(page, DATA)
        self.assertIn("| `-a`, `--all` | everything |", out)
        self.assertIn("`--user` `LOGIN`", out)
        self.assertIn("one person \\| theirs", out)
        self.assertNotIn("old", out)

    def test_the_idle_rule_says_whether_a_cancel_is_active(self):
        on = dict(DATA, policy=dict(DATA["policy"], idle_hours=2, cancel_after_hours=6, cancel_warn_hours=1))
        off = dict(DATA, policy=dict(on["policy"], cancel_after_hours=0))
        self.assertIn("할당받은 GPU를 **6시간** 동안 쓰지 않은 잡은 자동으로 취소", site_blocks.idle_rule(on))
        self.assertIn("**1시간 전**", site_blocks.idle_rule(on))
        self.assertIn("자동으로 취소하지는 않습니다", site_blocks.idle_rule(off))

    def test_the_idle_rule_tells_the_owner_by_dm_and_names_no_channel(self):
        """The owner of a job leaving its GPUs idle is told by DM, never by a mention in a
        channel (owner decision 12, 2026-11-28); policy.idle_notify is gone from the data."""
        rule = site_blocks.idle_rule(DATA)
        self.assertIn("쓰지 않으면** DM으로 알려 드립니다.", rule)
        self.assertIn("DM으로 알린다", site_blocks.idle_rule(DATA, plain=True))
        self.assertNotIn("멘션", rule)
        self.assertNotIn("리포트", rule)

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
        none = dict(DATA, quota={}, rules=UNLIMITED)
        self.assertIn("한도는 없습니다", site_blocks.quota_section(none))
        self.assertIn("디스크 리포트(매일 08:30)", site_blocks.quota_section(none))
        self.assertEqual(site_blocks.quota_each(none, "/scratch"), "\n")
        q = {"/home": {"block_hard_tib": 10.0, "block_warn_tib": 9.0, "inode_hard": 30000000, "inode_warn": 27000000}}
        on = dict(DATA, quota=q, policy=dict(DATA["policy"], submit_holds_disk=True))
        text = site_blocks.quota_section(on)
        self.assertIn("| `/home` | 10 TB | 3,000만 개 |", text)
        self.assertIn("새 잡 제출도 보류", text)
        self.assertNotIn("보류", site_blocks.quota_section(dict(on, policy=dict(on["policy"], submit_holds_disk=False))))
        self.assertEqual(site_blocks.quota_each(on, "/home"), "한 사람당 10 TB까지 쓸 수 있다.\n")

    def test_only_some_people_limited_is_no_none(self):
        """A person's own limit (people.yml disk_quota) with no default: the disk rule is
        active while site.json quota is empty, and the page says so, never "none"."""
        data = dict(DATA, quota={}, commands={"usage": {"summary_ko": "x", "options": [],
                    "subcommands": [{"name": "disk", "summary_ko": "y", "options": []}]}})  # fmt: skip
        text = site_blocks.quota_section(data)
        self.assertNotIn("한도는 없습니다", text)
        self.assertIn("따로 한도가 정해진 사람만", text)
        self.assertIn("`usage disk`", text)

    def test_the_bot_as_the_cluster_runs_it(self):
        bot = {"command": "/c", "subcommands": [{"name": n, "help": n} for n in ("unban", "leave", "data", "help")]}
        on = dict(DATA, bot=bot, services={"bot": True})
        off = dict(DATA, bot=bot, services={"bot": False})
        self.assertIn("`/c unban`", site_blocks.bot(on, "unban"))
        self.assertIn("관리자에게", site_blocks.bot(off, "unban"))
        self.assertIn("## Slack 명령 (/c)", site_blocks.bot(on, "section"))
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
                         "로그인 노드에서는 한 사람이 CPU 8개, 메모리 64 GB, 프로세스 4,096개까지 쓰실 수 있습니다.\n")
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
    """The reference listed options for sq and qos only; the other commands had none
    (2026-11-27 audit). A command with subcommands (usage gpu) lists each one's too."""

    def data(self):
        sub = {"name": "sub", "summary_ko": "하위", "options": [{"flags": ["--deep"], "help": "deeper", "metavar": ""}]}
        return dict(DATA, commands={**DATA["commands"], "other": {"summary_ko": "x", "options": [], "subcommands": [sub]}})

    def test_every_commands_options_under_its_heading(self):
        out = site_blocks.body(self.data(), "options:all")
        self.assertIn("#### `other`의 옵션", out)
        self.assertIn("#### `other sub`의 옵션\n\n| 옵션 | 설명 |\n|---|---|\n| `--deep` | deeper |", out)
        self.assertIn("#### `tool`의 옵션", out)
        self.assertIn("| `-a`, `--all` | everything |", out)

    def test_the_commands_that_print_json_theirs_or_a_subcommands(self):
        j = [{"flags": ["--json"], "help": "", "metavar": ""}]
        cmds = {"a": {"options": j}, "b": {"options": [], "subcommands": [{"name": "s", "options": j}]},
                "c": {"options": []}}  # fmt: skip
        self.assertEqual(site_blocks.body(dict(DATA, commands=cmds), "commands:json"), "`a`, `b`\n")
        with self.assertRaises(SystemExit):
            site_blocks.body(dict(DATA, commands={"c": {"options": []}}), "commands:json")

    def test_the_commands_table_has_each_subcommand(self):
        out = site_blocks.body(dict(self.data(), commands={"other": self.data()["commands"]["other"]}), "commands:table")
        self.assertIn("| `other` | x |\n| `other sub` | 하위 |", out)

    def test_the_reference_shows_every_cluster_commands_options(self):
        import json

        real = json.loads(site_blocks.DATA.read_text())
        page = (site_blocks.ROOT / "docs/reference/slurm.md").read_text()
        for command, _ in site_blocks.every_command(real):
            self.assertIn(f"#### `{command}`의 옵션", page, "options:all on docs/reference/slurm.md")


class FromTheData(unittest.TestCase):
    """Values a page used to type by hand (2026-11-27 audit): each comes from site.json,
    and a value the page's prose cannot hold is refused."""

    def data(self, **policy):
        return dict(DATA, policy=dict(DATA["policy"], **policy), commands={**DATA["commands"], "usage": {
            "summary_ko": "내 현황", "options": [], "subcommands": [{"name": "disk", "summary_ko": "내 사용량", "options": []}]}}, messages={"hold_ended": "Ended on", "hold_disk": "Disk on"},
            storage={"/home": {"read_bps": 1272070703, "write_bps": 894575285, "read_iops": 1587, "write_iops": 483}},
            services={"bot": True}, bot={"command": "/c", "subcommands": [{"name": "join"}, {"name": "unban"}]})  # fmt: skip

    def test_the_gpus_per_node_and_a_list_the_rules_cannot_explain(self):
        self.assertEqual(site_blocks.body(self.data(gpus_per_node=[1, 2, 4, 8]), "policy:gpus_per_node"), "1, 2, 4, 8\n")
        for bad in ([], [1, 3, 8]):
            with self.assertRaises(ValueError):
                site_blocks.body(self.data(gpus_per_node=bad), "policy:gpus_per_node")

    def test_a_command_is_named_only_when_the_cluster_has_it(self):
        self.assertEqual(site_blocks.body(self.data(), "command:usage"), "`usage`\n")
        self.assertEqual(site_blocks.body(self.data(), "command:usage:what"), "내 현황\n")
        self.assertEqual(site_blocks.body(self.data(), "command:usage:disk"), "`usage disk`\n")
        self.assertEqual(site_blocks.body(self.data(), "command:usage:disk:what"), "내 사용량\n")
        for gone in ("command:du-me", "command:usage:du", "command:disk-usage"):
            with self.assertRaises(SystemExit):
                site_blocks.body(self.data(), gone)

    def test_the_measured_speeds_rounded_as_about(self):
        d = self.data()
        self.assertEqual(site_blocks.storage(d, "/home", "seq"), "대략 읽기 1.3 GB/s, 쓰기 0.9 GB/s")
        self.assertEqual(site_blocks.storage(d, "/home", "random"), "대략 초당 1,600번 읽기, 480번 쓰기")

    def test_the_refusals_follow_the_limits_the_cluster_sets(self):
        none = site_blocks.submit_refusals(self.data())
        self.assertEqual(none, "\n")
        out = site_blocks.submit_refusals(self.data(max_submit_jobs=500, submit_holds=True, submit_holds_disk=True))
        self.assertIn("**500개**", out)
        self.assertIn("### `Ended on`", out)
        self.assertIn("### `Disk on`", out)
        self.assertIn("`usage disk`", out, "the disk refusal points at the command")
        holds = site_blocks.submit_refusals(self.data(submit_holds=True))
        self.assertNotIn("Disk on", holds, "disk holds off")
        self.assertNotIn("개**", holds, "no cap")
        unset = site_blocks.submit_refusals(dict(self.data(submit_holds=True, submit_holds_disk=True), rules=UNLIMITED))
        self.assertNotIn("Disk on", unset, "no one limited yet: nothing to reach (2026-11-27)")

    def test_join_and_unban_follow_the_bot(self):
        d = self.data()
        self.assertIn("`/c join`", site_blocks.body(d, "bot:join"))
        self.assertIn("`/c unban`", site_blocks.body(d, "bot:unban"))
        off = dict(d, services={"bot": False})
        self.assertIn("관리자", site_blocks.body(off, "bot:join"))
        self.assertIn("관리자", site_blocks.body(off, "bot:unban"))


if __name__ == "__main__":
    unittest.main()


class Rules(unittest.TestCase):
    """Every rule that acts on a person (site.json rules, deepops cluster_tools.rules) on
    the rules page, each where its anchor says, with what the cluster does and the command
    that shows where one stands (owner, 2026-11-27: users see their own standing)."""

    def data(self, **rule):
        r = dict({"id": "gpu-idle", "title": "GPU 유휴 잡", "action": "notice, cancel", "check": "usage",
                  "anchor": "policy/rules/#gpu-idle", "values": {}, "active": True}, **rule)  # fmt: skip
        return dict(DATA, rules=[r], commands={"usage": {"summary_ko": "x", "options": []}})

    def test_each_rule_a_row_carrying_its_anchor(self):
        out = site_blocks.rules_section(self.data(), "policy/rules.md")
        self.assertIn('| <span id="gpu-idle"></span>GPU 유휴 잡 | 알림, 잡 취소 | `usage` |', out)

    def test_an_anchor_elsewhere_an_unknown_action_or_command_is_refused(self):
        with self.assertRaises(SystemExit):
            site_blocks.rules_section(self.data(), "guide/storage.md")
        with self.assertRaises(SystemExit):
            site_blocks.rules_section(self.data(action="notice, explode"), "policy/rules.md")
        with self.assertRaises(SystemExit):
            site_blocks.rules_section(self.data(check="gpu-usage"), "policy/rules.md")

    def test_the_ssh_rate_rule_refuses_a_connection_not_a_submission(self):
        """The SSH rate rule's refuse is a new connection's; queued-jobs' stays a submission's."""
        ssh = self.data(id="ssh-rate", title="SSH 접속 빈도", action="notice, refuse", anchor="policy/rules/#ssh-rate")
        self.assertIn("| 알림, 새 접속 거부 |", site_blocks.rules_section(ssh, "policy/rules.md"))
        queued = self.data(id="queued-jobs", title="제출 잡 한도", action="refuse", anchor="policy/rules/#submit")
        self.assertIn("| 제출 거부 |", site_blocks.rules_section(queued, "policy/rules.md"))

    def test_the_ssh_rate_rule_says_its_values_from_the_data(self):
        values = {"ssh_rate_mode": "refuse", "ssh_rate_refuse_sessions": 50, "cluster_user_warn_fraction": 0.8,
                  "ssh_rate_window_minutes": 5, "ssh_rate_block_minutes": 7, "ssh_rate_block_max_minutes": 30}
        data = self.data(id="ssh-rate", values=values)
        text = site_blocks.ssh_rate_rule(data)
        for part in ("**5분 동안 50번**", "새 접속이 **7분** 동안 막힙니다", "최대 **30분**", "5분 동안 40번에 이르면", "DM으로"):
            self.assertIn(part, text)
        self.assertIn("막힌다", site_blocks.ssh_rate_rule(data, plain=True))
        warn = site_blocks.ssh_rate_rule(self.data(id="ssh-rate", values=dict(values, ssh_rate_mode="warn")))
        self.assertIn("**5분 동안 40번** 열면 DM으로 알려 드립니다", warn)
        self.assertIn("막지는 않습니다", warn)
        self.assertEqual(site_blocks.ssh_rate_rule(self.data(id="ssh-rate", values=values, active=False)), "\n")

    def test_a_message_block_is_the_clusters_own_words(self):
        data = dict(DATA, messages={"ssh_rate": "막혔습니다"})
        self.assertEqual(site_blocks.body(data, "message:ssh_rate"), "`막혔습니다`\n")

    def test_a_rule_the_cluster_does_not_run_has_no_row(self):
        self.assertNotIn("gpu-idle", site_blocks.rules_section(self.data(active=False), "policy/rules.md"))

    def test_the_rules_page_holds_every_rule(self):
        import json

        real = json.loads(site_blocks.DATA.read_text())
        page = (site_blocks.ROOT / "docs/policy/rules.md").read_text()
        for r in real["rules"]:
            if r["active"]:
                self.assertIn(f'<span id="{r["anchor"].partition("#")[2]}"></span>', page, r["id"])


class Fences(unittest.TestCase):
    def test_a_longer_fence_holds_a_shorter_one(self):
        lines = ["a", "````markdown", "## t", "```bash", "x", "```", "## u", "````", "b"]
        self.assertEqual(site_blocks.in_code(lines), [False, True, True, True, True, True, True, True, False])
        self.assertEqual(site_blocks.in_code(["```", "x", "```", "y"]), [True, True, True, False])
