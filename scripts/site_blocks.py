#!/usr/bin/env python3
"""Fill the generated blocks in the pages from data/site.json, the facts the cluster's
code and config hold (written there by deepops scripts/docs/site_facts.py).

A page marks a block

    <!-- BEGIN GENERATED: options:sq -->
    <!-- END GENERATED: options:sq -->

and this script writes its body; a hand edit inside a block is overwritten. A single
value sits inline, both markers on its line, so it reads inside a sentence or a list item
(a marker on a line of its own would end a list item):

    유예 시간은 <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->120<!-- END GENERATED: slurm:preempt_grace_seconds -->초입니다.
 CI runs it
with --check, so a page whose block no longer matches the data fails the build.

Generators:
  options:CMD     the options of the cluster command CMD, as a table
  policy:FIELD    one policy value (stale_days, grace_days, warn_percent)
  date:NAME       one announced date (the site's schedule); in notices only (docs/news/)
  day:NAME        the same with its weekday, as the notices write it: 2026-11-25(수)
  quota:MOUNT:F   a limit of the filesystem at MOUNT: block_hard, block_warn (TB),
                  inode_hard, inode_warn (a count); quota:ratio, files per TB
  rule:idle       the idle-GPU rule as a sentence: that the owner is told from the idle
                  hours (or, with policy.idle_notify empty, only listed), and the cancel
                  with its warning, or that no cancel is active (cancel 0)
  env:table       the users' environment variables: each with its value in a login and
                  in a job (the cluster's one list, user_environment)
  env:NAME        the login value of the variable NAME, inline
  models          the shared model cache as a sentence: where it is (SHARED_HF_HUB_CACHE,
                  read by naming it; each person's own HF_HUB_CACHE stays theirs), or
                  that there is none
  chat:channels   the Slack channels people use, as a table: each name (the cluster's)
                  and its line (slack/<role>.md table:, scripts/channels.py)
  service:overview, service:dashboard
                  where the portal's overview page and the monitoring dashboard are, as the
                  cluster runs them (site.json services), or that they are not; no address
  paths:shared_data the shared data folders, as paths
  chat:ROLE       the Slack channel of ROLE (announce, help, status, admin), as code
  rule:sessions   whether srun and salloc GPU sessions must name a team QoS, checked at
                  submit (policy.interactive_team_qos), or only asked to
  quota:section   the per-person disk limits (what happens at one, the warning, a table),
                  or that there are none: it appears when the cluster sets limits
  quota:each:M    "한 사람에 5 TB까지 쓰실 수 있고, " for mount M, or nothing
  bot:section, bot:unban, bot:leave, bot:data
                  the /cluster command's requests, or whom to ask while the cluster runs
                  no bot (site.json services.bot)
  login:limits    the login nodes' per-person limits as a sentence (CPUs, memory,
                  processes), or that none is set
  bot:command     the cluster bot's slash command
  bot:subcommands the cluster bot's slash command and subcommands as a table, with their
                  Korean help
  slurm:FIELD     one Slurm value (kill_wait_seconds, preempt_grace_seconds,
                  sigkill_after_seconds)

Usage: site_blocks.py [--check]
Standard library only.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "site.json"
# A block may sit indented in a list item: its body takes the BEGIN marker's indent.
BLOCK = re.compile(r"^([ ]*)(<!-- BEGIN GENERATED: (\S+) -->\n)(.*?)([ ]*<!-- END GENERATED: \3 -->)", re.S | re.M)


def options(data, command):
    rows = ["| 옵션 | 설명 |", "|---|---|"]
    for o in data["commands"][command]["options"]:
        flags = ", ".join(f"`{f}`" + (f" `{o['metavar']}`" if o["metavar"] and f.startswith("--") else "") for f in o["flags"])
        rows.append(f"| {flags} | {o['help'].replace('|', '\\|')} |")
    return "\n".join(rows) + "\n"


def policy(data, field):
    p = data["policy"]
    if field == "warn_percent":
        return f"{round(p['warn_fraction'] * 100)}%\n"
    return f"{p[field]}\n"


def idle_rule(data):
    p = data["policy"]
    # How the owner is told (a mention in the report, a DM) is the cluster's setting
    # (policy.idle_notify) and not stated here; with none, the report only lists the job.
    if set(p["idle_notify"]) - {"mention", "dm"}:
        raise ValueError(f"policy.idle_notify {p['idle_notify']!r}: teach scripts/site_blocks.py idle_rule")
    told = "알려 드립니다" if p["idle_notify"] else "사용 현황 리포트에 표시됩니다"
    text = f"Slurm 잡으로 GPU를 할당받아 두고 **{p['idle_hours']}시간 넘게 쓰지 않으면** {told}."
    if p["cancel_after_hours"]:
        text += (f" **{p['cancel_after_hours']}시간** 동안 GPU를 쓰지 않은 잡은 자동으로 취소되며, "
                 f"취소 **{p['cancel_warn_hours']}시간 전**에 미리 알려 드립니다.")
    else:
        text += " 쓰지 않는 잡을 자동으로 취소하지는 않습니다."
    return text + "\n"


WEEKDAYS = "월화수목금토일"


def day(iso):
    """A date with its Korean weekday: 2026-11-25 -> 2026-11-25(수)."""
    return f"{iso}({WEEKDAYS[date.fromisoformat(iso).weekday()]})"


def count(n):
    """A file count as Korean writes it: 30000000 -> 3,000만."""
    return f"{n // 10000:,}만" if n % 10000 == 0 and n >= 10000 else f"{n:,}"


PORTAL_ADDRESS = "포털 주소는 계정을 받을 때 함께 알려 드립니다."


def service(data, name):
    """A sentence on a service as the cluster runs it (site.json services): the portal's
    overview page, or the monitoring dashboard. Never an address: that is private."""
    svc = data["services"]
    if name == "overview":
        if svc["portal"] and svc["overview"]:
            return (f"한눈에 보는 개요는 **웹 포털에 로그인한 뒤** 상단 메뉴의 **{svc['overview']}** 페이지에서 "
                    f"보실 수 있습니다. {PORTAL_ADDRESS}\n")
        return "한눈에 보는 개요는 `sq`의 첫 줄에 있습니다.\n"
    if name == "dashboard":
        if svc["dashboard"] and svc["portal"] and svc["menu"]:
            return (f"대시보드는 웹 포털에 클러스터 계정으로 로그인한 뒤 상단 메뉴의 **{svc['menu'][0]}**에서 "
                    f"여실 수 있습니다. {PORTAL_ADDRESS}\n")
        if svc["dashboard"]:
            return "대시보드 주소는 관리자에게 문의해 주세요.\n"
        return "웹 대시보드는 운영하지 않습니다. `sq`와 `gpu-usage`로 확인해 주세요.\n"
    raise SystemExit(f"unknown generated block: service:{name}")


def shared_data(data):
    """The shared data folders, each as a path (site.json paths)."""
    root = data["paths"]["shared"]
    return ", ".join(f"`{root}/{d}`" for d in data["paths"]["shared_data"]) + "\n"


def sessions_rule(data):
    if data["policy"]["interactive_team_qos"]:
        return ("`srun`, `salloc`으로 여는 GPU 세션은 팀 QoS(`--qos=<팀 QoS>`)로만 시작할 수 있습니다. "
                "팀 QoS 없이 제출하면 `qos`로 내 QoS를 확인하라는 안내와 함께 거부됩니다.\n")
    return "`srun`, `salloc`으로 여는 GPU 세션은 팀 QoS(`--qos=<팀 QoS>`)로 실행해 주세요.\n"


def login_limits(data):
    """The login nodes' per-person limits as a sentence (site.json login), or that none is set."""
    limits = data.get("login") or {}
    parts = [f"{label} {fmt(limits[key])}" for key, label, fmt in (
        ("cpus", "CPU", lambda n: f"{n}개"),
        ("memory_gib", "메모리", lambda n: f"{n} GB"),
        ("tasks", "프로세스", lambda n: f"{count(n)}개"),
    ) if key in limits]  # fmt: skip
    if not parts:
        return "로그인 노드에는 사람별 자원 한도가 따로 걸려 있지 않습니다.\n"
    return f"로그인 노드에는 한 사람당 {', '.join(parts)}까지 쓰실 수 있도록 제한이 걸려 있습니다.\n"


def table(header, rows):
    return "\n".join([f"| {header[0]} | {header[1]} |", "|---|---|", *(f"| {a} | {b} |" for a, b in rows)]) + "\n"


def bot_subcommands(data):
    """The cluster bot's subcommands as a table, each with its Korean help (site.json bot)."""
    bot = data["bot"]
    return table(("명령", "하는 일"), [(f"`{bot['command']} {s['name']}`", s["help"]) for s in bot["subcommands"]])


def _tb(tib):
    return f"{tib:g} TB"


def quota_section(data):
    """The per-person disk limits as the cluster sets them (site.json quota): what happens
    at a limit, the warning, a table, the files per TB; or that there are none yet."""
    q, p = data["quota"], data["policy"]
    if not q:
        return "사람마다 정해진 용량과 파일 수 상한은 없습니다. 사용량은 매일 세어 Slack 디스크 리포트로 알려 드립니다.\n"
    spaces = "과 ".join(f"`{m}`" for m in q) if len(q) == 2 else ", ".join(f"`{m}`" for m in q)
    held = " 새 잡 제출도 보류되니" if p.get("submit_holds_disk") else "니"
    rows = [(f"`{m}`", f"{_tb(v['block_hard_tib'])} | {count(v['inode_hard'])}개") for m, v in q.items()]
    first = next(iter(q.values()))
    return (
        f"사람마다 {spaces}에 아래 용량과 파일 수 상한이 있습니다. 상한에 이르면 그 공간에 더 쓸 수 없고{held}, "
        f"그 전에 정리해 주시면 감사하겠습니다. 상한의 {round(p['warn_fraction'] * 100)}%에 이르면 Slack으로 미리 알려 드립니다.\n\n"
        + "| 공간 | 용량 상한 | 파일 수 상한 |\n|---|---|---|\n"
        + "".join(f"| {a} | {b} |\n" for a, b in rows)
        + f"\n- 파일 수 한도는 용량에 비례합니다(1 TB당 {count(round(first['inode_hard'] / first['block_hard_tib']))}개). "
        "작은 파일 수천만 개는 파일 서버의 모든 사용자를 느리게 하니 묶음 포맷(tar, WebDataset, HDF5, Arrow 등)을 써 주세요.\n"
    )


def quota_each(data, mount):
    """One filesystem's per-person limit as the start of a sentence, or nothing."""
    q = data["quota"].get(mount)
    return f"한 사람에 {_tb(q['block_hard_tib'])}까지 쓰실 수 있고, \n" if q else "\n"


def bot(data, name):
    """The /cluster command as the cluster runs it (site.json services.bot): its
    requests, or whom to ask while there is no bot."""
    b = data["bot"]
    on = data["services"]["bot"]
    subs = {s["name"] for s in b["subcommands"]}

    def cmd(sub):
        if sub not in subs:
            raise SystemExit(f"bot:{name}: the bot has no {sub} (site.json bot.subcommands)")
        return f"`{b['command']} {sub}`"

    if name == "section":
        if not on:
            return "\n"
        return ("## 봇으로 하는 신청\n\n계정, 차단 해제, 공동작업 폴더, 공유 데이터는 Slack에서 클러스터 봇에게 신청하실 수 있습니다.\n"
                "아무 채널에서나 아래 명령을 입력해 주세요.\n\n" + bot_subcommands(data)
                + "\n관리자가 승인하면 봇이 DM으로 알려 드립니다. 봇의 홈 탭에서 내 신청과 공동작업 폴더를 보실 수 있습니다.\n")  # fmt: skip
    if name == "unban":
        return f"{cmd('unban')}으로 해제를 신청해 주세요.\n" if on else "관리자에게 해제를 요청해 주세요.\n"
    if name == "leave":
        return (f"졸업 등으로 계정을 정리하실 때는 {cmd('leave')}로 신청해 주세요.\n" if on
                else "졸업 등으로 계정을 정리하실 때는 관리자에게 알려 주세요.\n")  # fmt: skip
    if name == "data":
        return (f"필요한 데이터를 받아 두는 신청은 {cmd('data')}로 하실 수 있습니다.\n" if on
                else "필요한 데이터는 관리자에게 요청해 주세요.\n")  # fmt: skip
    raise SystemExit(f"unknown generated block: bot:{name}")


def quota(data, arg):
    if arg == "ratio":
        q = next(iter(data["quota"].values()))
        return count(round(q["inode_hard"] / q["block_hard_tib"])) + "\n"
    mount, _, field = arg.rpartition(":")
    q = data["quota"][mount]
    if field.startswith("block"):
        return f"{q[field + '_tib']:g} TB\n"
    return count(q[field]) + "\n"


def env(data):
    return {e["name"]: e for e in data.get("environment", [])}


def env_table(data):
    rows = ["| 변수 | 로그인 | 잡 안 |", "|---|---|---|"]
    for e in data.get("environment", []):
        login = f"`{e['login']}`" if e["login"] else "없음"
        job = f"`{e['job']}`" if e["job"] else "같음"
        rows.append(f"| `{e['name']}` | {login} | {job} |")
    return "\n".join(rows) + "\n"


def models(data):
    hub = env(data).get("SHARED_HF_HUB_CACHE")
    if not hub:
        return "공용 모델 캐시는 아직 없습니다. 모델은 각자 `HF_HOME` 아래에 내려받습니다.\n"
    return (f"공용 모델 캐시는 `{hub['login']}`에 있고, 모든 로그인과 잡에서 `SHARED_HF_HUB_CACHE`가 그곳을 가리킵니다. "
            "**읽기 전용**이라 여기에는 내려받을 수 없으니, 각자의 `HF_HUB_CACHE`로 바꾸지 말고 읽을 때 "
            "이 경로를 직접 주세요: `from_pretrained(<모델>, cache_dir=os.environ[\"SHARED_HF_HUB_CACHE\"], "
            "local_files_only=True)`, 또는 `HF_HUB_OFFLINE=1 hf download <모델> --cache-dir \"$SHARED_HF_HUB_CACHE\"`가 "
            "출력하는 스냅샷 경로. 그 밖의 모델은 평소처럼 각자의 캐시(`HF_HOME` 아래)에 내려받고, 여럿이 쓸 모델은 "
            "관리자에게 요청하세요.\n")


def body(data, name):
    kind, _, arg = name.partition(":")
    if name == "quota:section":
        return quota_section(data)
    if name.startswith("quota:each:"):
        return quota_each(data, name.removeprefix("quota:each:"))
    if kind == "options":
        return options(data, arg)
    if kind == "policy":
        return policy(data, arg)
    if kind == "quota":
        return quota(data, arg)
    if name == "rule:idle":
        return idle_rule(data)
    if kind == "date":
        return f"{data['dates'][arg]}\n"
    if kind == "day":
        return f"{day(data['dates'][arg])}\n"
    if kind == "slurm":
        return f"{data['slurm'][arg]}\n"
    if name == "env:table":
        return env_table(data)
    if kind == "env":
        return f"`{env(data)[arg]['login']}`\n"
    if name == "models":
        return models(data)
    if kind == "service":
        return service(data, arg)
    if name == "paths:shared_data":
        return shared_data(data)
    if kind == "chat" and arg in data["chat"]["channels"]:
        return f"`{data['chat']['channels'][arg]}`\n"
    if name == "rule:sessions":
        return sessions_rule(data)
    if name == "login:limits":
        return login_limits(data)
    if kind == "bot" and arg in ("section", "unban", "leave", "data"):
        return bot(data, arg)
    if name == "bot:command":
        return f"{data['bot']['command']}\n"
    if name == "bot:subcommands":
        return bot_subcommands(data)
    if name == "chat:channels":
        import channels  # the guides' sources; it reads this module too

        return channels.help_table(data)
    raise SystemExit(f"unknown generated block: {name}")


INLINE = re.compile(r"(<!-- BEGIN GENERATED: (\S+) -->)([^\n]*?)(<!-- END GENERATED: \2 -->)")


def fill(text, data):
    def one(m):
        indent = m.group(1)
        lines = body(data, m.group(3)).splitlines(keepends=True)
        return indent + m.group(2) + "".join(indent + line if line.strip() else line for line in lines) + m.group(5)

    text = BLOCK.sub(one, text)
    return INLINE.sub(lambda m: m.group(1) + body(data, m.group(2)).strip() + m.group(4), text)


# A date says when a change takes effect: that belongs to a notice. A guide, the policy
# or a reference states the rule as it is, so a date block anywhere else is refused.
DATED = re.compile(r"<!-- BEGIN GENERATED: (?:date|day):\S+ -->")
NEWS = "docs/news/"


def dated_outside_news(root=ROOT):
    """The pages outside the notices that carry a date block."""
    pages = sorted((root / "docs").rglob("*.md")) + sorted((root / "snippets").rglob("*.md"))
    return [p.relative_to(root) for p in pages
            if not p.relative_to(root).as_posix().startswith(NEWS) and DATED.search(p.read_text())]  # fmt: skip


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = argv == ["--check"]
    data = json.loads(DATA.read_text())
    dated = dated_outside_news()
    for page in dated:
        print(f"{page}: a date block outside {NEWS}: a date belongs in a notice; state the rule as it is", file=sys.stderr)
    if dated:
        return 1
    stale = []
    for page in sorted((ROOT / "docs").rglob("*.md")) + sorted((ROOT / "snippets").rglob("*.md")):
        text = page.read_text()
        new = fill(text, data)
        if new != text:
            stale.append(page.relative_to(ROOT))
            if not check:
                page.write_text(new)
    if check and stale:
        for page in stale:
            print(f"{page}: a generated block differs from data/site.json; run scripts/site_blocks.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
