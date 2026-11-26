# Slurm 레퍼런스

[Slurm 기초](../start/slurm-basics.md)를 넘어, 클러스터가 잡을 **어떻게 배정하고, 줄 세우고, 선점하는지** 정리한 참고 문서입니다.
구체적인 값(QoS 이름, 한도, 가중치)은 클러스터마다 다르고 바뀔 수 있으므로, 문서 대신 아래 명령으로 **직접 확인**하세요.

## 명령어 전체

| 명령 | 용도 |
|---|---|
| `sbatch` | 배치 스크립트 제출 |
| `srun` | 즉시 실행, 잡 스텝 실행, 인터랙티브 |
| `salloc` | 자원만 먼저 할당받기 (셸은 로그인 노드에 유지) |
| `squeue` | 대기, 실행 중인 잡 조회 |
| `scancel` | 잡 취소 |
| `sinfo` | 노드, 파티션 상태 |
| `scontrol` | 잡, 노드, 파티션 상세 조회와 수정 (`show job`, `show node`) |
| `sacct` | **끝난 잡을 포함한** 이력 조회 |
| `sstat` | 실행 중인 잡의 실시간 자원 사용량 |
| `sprio` | 대기 중인 잡의 우선순위 분해 |
| `sshare` | Fairshare 점수 조회 |
| `sacctmgr` | 계정, 사용자, QoS, association 조회 |
| `sreport` | 기간별 사용량 리포트 (GPU 시간 등) |

클러스터가 따로 배포하는 명령도 있습니다.

<!-- BEGIN GENERATED: commands:table -->
| 명령 | 보여 주는 것 |
|---|---|
| `disk-usage` | 내 파일시스템별 사용량과 파일 수, 경고 수준과 한도, 정리하면 좋을 폴더, 최근 I/O |
| `gpu-usage` | 잡의 GPU가 실제로 한 일: 사용률, SM 활동, 메모리, 전력 (실행 중이거나 끝난 잡) |
| `qos` | 내가 잡을 낼 수 있는 QoS |
| `scratch-space` | 스크래치 공간에서 정리될 예정인 내 파일과 그 시점 |
| `sq` | 큐, 누가 무엇을 쓰는지, 파티션별 남은 자원 |
<!-- END GENERATED: commands:table -->

옵션은 각 명령의 `--help` 가 항상 최신입니다.

### 클러스터 명령의 옵션

클러스터 명령마다의 옵션입니다. 명령의 정의에서 만들어지므로 `--help`와 같습니다.

<!-- BEGIN GENERATED: options:all -->
#### `disk-usage`의 옵션

| 옵션 | 설명 |
|---|---|
| `-u`, `--user` `NAME` | someone else's figures instead of yours |
| `--hours` `N` | the I/O window, in hours (default 24) |
| `--top` `N` | rows per table of folders and I/O (default 10) |
| `--json` | the figures as JSON, for scripts |
| `--theme` `FLAVOUR` | catppuccin flavour: mocha (default), macchiato, frappe, latte. $CLUSTER_THEME sets it for every cluster command |
| `--themes` | list the flavours with a swatch |
| `--color` `WHEN`, `--colour` `WHEN` | always, never or auto (default; $NO_COLOR is honoured) |
| `--no-color`, `--no-colour` | the same as --color never |
| `--ascii` | ASCII glyphs for terminals without UTF-8 |
| `--wide` | every column at full width, whatever the terminal fits |

#### `gpu-usage`의 옵션

| 옵션 | 설명 |
|---|---|
| `--source` `WHERE` | auto (default: Slurm's figures where the job has them, else Prometheus'), slurm or prometheus |
| `--json` | the figures as JSON, for scripts |
| `--theme` `FLAVOUR` | catppuccin flavour: mocha (default), macchiato, frappe, latte. $CLUSTER_THEME sets it for every cluster command |
| `--themes` | list the flavours with a swatch |
| `--color` `WHEN`, `--colour` `WHEN` | always, never or auto (default; $NO_COLOR is honoured) |
| `--no-color`, `--no-colour` | the same as --color never |
| `--ascii` | ASCII glyphs for terminals without UTF-8 |
| `--wide` | every column at full width, whatever the terminal fits |

#### `qos`의 옵션

| 옵션 | 설명 |
|---|---|
| `-m`, `--me` | only the QoS you may submit against |
| `-a`, `--all` | include QoS held by no user (Slurm's built-in normal) |
| `-u`, `--user` `NAME` | answer for someone else instead of you |
| `--usage` | the live usage figures (--no-usage skips the job list) |
| `--json` | the model as JSON, for scripts (ignores $QOS_OPTIONS) |
| `--theme` `FLAVOUR` | catppuccin flavour: mocha (default), macchiato, frappe, latte. $CLUSTER_THEME sets it for every cluster command |
| `--themes` | list the flavours with a swatch |
| `--color` `WHEN`, `--colour` `WHEN` | always, never or auto (default; $NO_COLOR is honoured) |
| `--no-color`, `--no-colour` | the same as --color never |
| `--ascii` | ASCII glyphs for terminals without UTF-8 |
| `--wide` | every column at full width, whatever the terminal fits |

#### `scratch-space`의 옵션

| 옵션 | 설명 |
|---|---|
| `--root` `DIR` | the scratch space (default: the cluster's, scratch_root in cluster.json) |
| `--theme` `FLAVOUR` | catppuccin flavour: mocha (default), macchiato, frappe, latte. $CLUSTER_THEME sets it for every cluster command |
| `--themes` | list the flavours with a swatch |
| `--color` `WHEN`, `--colour` `WHEN` | always, never or auto (default; $NO_COLOR is honoured) |
| `--no-color`, `--no-colour` | the same as --color never |
| `--ascii` | ASCII glyphs for terminals without UTF-8 |
| `--wide` | every column at full width, whatever the terminal fits |

#### `sq`의 옵션

| 옵션 | 설명 |
|---|---|
| `-m`, `--me` | only your jobs |
| `-u`, `--user` `USER` | only these users (comma list; * and ? match) |
| `-p`, `--partition` `PART` | only these partitions |
| `-w`, `--nodelist` `NODES` | only these nodes (a hostlist like gpu[1-3,8], or globs) |
| `-t`, `--states` `STATES`, `--state` `STATES` | only these job states (R,PD or running,pending; all includes finished) |
| `-j`, `--jobs` `IDS` | only these job IDs |
| `-A`, `--account` `ACCOUNTS` | only these accounts |
| `-q`, `--qos` `QOS` | only these QoS |
| `-n`, `--name` `NAMES` | only these job names |
| `--queue` `WHICH` | the job list: mine (default; a job filter shows what it selects), all, or none |
| `-a`, `--all` | everyone's jobs in the job list (--queue all) |
| `--no-queue` | no job list (--queue none) |
| `-U`, `--users` | who holds what (each GPU type under a high QoS and a low one), each user's share of the GPUs, and each team's high QoS quota in use |
| `-W`, `--why` | why jobs wait: reason families, then Slurm's codes |
| `--resources` | the CPU / memory / GPU table |
| `-d`, `--detail` | full node states and reasons, and who is behind each pending reason |
| `--group` | pending jobs above running ones (--no-group: job ID order) |
| `--split` | break each pool into the partitions it is split across |
| `-P`, `--partitions` | pool totals only |
| `-N`, `--nodes`, `--show-nodes` | a flat node list, as in sinfo -N |
| `--gres` `NAME` | the generic resource to count (default: the one most nodes have) |
| `-i`, `--interval` `SEC`, `--iterate` `SEC` | redraw every SEC seconds (at least 2); while Slurm fails or does not answer, the wait doubles, up to 60s or SEC if longer |
| `--json` | the model as JSON, for scripts (ignores $SQ_OPTIONS) |
| `--theme` `FLAVOUR` | catppuccin flavour: mocha (default), macchiato, frappe, latte. $CLUSTER_THEME sets it for every cluster command |
| `--themes` | list the flavours with a swatch |
| `--color` `WHEN`, `--colour` `WHEN` | always, never or auto (default; $NO_COLOR is honoured) |
| `--no-color`, `--no-colour` | the same as --color never |
| `--ascii` | ASCII glyphs for terminals without UTF-8 |
| `--wide` | every column at full width, whatever the terminal fits |
<!-- END GENERATED: options:all -->

## QoS

QoS(Quality of Service)는 잡의 **우선순위, 한도, 선점 권한**을 정하는 등급입니다.

### 등급

| 등급 | 누가 쓰나 | 특징 |
|---|---|---|
| **기본 QoS** | 모든 사용자 | `--qos` 를 생략하면 이것으로 제출됩니다. 남는 자원을 쓰는 대신 **선점될 수 있습니다**. 실행 시간 한도가 있습니다 |
| **팀 QoS** | 팀마다 하나 | 우선순위가 높고, **팀 몫의 GPU 안에서** 기본 QoS 잡을 밀어내고 먼저 돕니다 |

이 밖에 운영자의 긴급 대응용 QoS가 있을 수 있습니다. 정확한 이름, 몫, 한도는 바뀔 수 있어 문서에 적지 않습니다. **`qos` 로 확인하세요.**

```bash
qos                  # 제출 가능한 QoS 전체. 내 것 표시, 선점 관계와 팀 몫 포함
qos --help           # 전체 옵션 (항상 최신)
```

`qos` 는 내가 속한 계정을 모두 합쳐 보여 줍니다. 여러 계정에 속해 있어도 한 번에 확인할 수 있습니다. 원본 데이터를 직접 보려면:

```bash
sacctmgr show assoc user=$USER format=Account,User,QOS%50,DefaultQOS
sacctmgr show qos format=Name,Priority,Preempt%40,GrpTRES%40,MaxWall
```

- 팀 QoS는 **반드시 본인 소속 팀 것**을 쓰세요. -> [규정](../policy/rules.md#잡-제출-규칙)
- GPU를 점유하는 세션은 **팀 QoS**로 실행하고, 다 쓰면 즉시 반납합니다. -> [규정: 디버깅](../policy/rules.md#디버깅)

```bash
sbatch --qos=<팀 QoS> job.sbatch    # --qos 생략 시 기본 QoS
```

### 팀 몫: `QOSGrpGRES` 로 대기하는 이유

팀 QoS에는 **팀 전체가 동시에 쓸 수 있는 GPU 수** 상한(`GrpTRES`)이 있습니다. 이 한도는 사람마다 따로 걸리지 않고, **그 QoS로 도는 모든 잡의 GPU를 합친 수**에 걸립니다.

그래서 클러스터에 GPU가 남아 있어도 내 잡이 `(QOSGrpGRES)` 사유로 대기할 수 있습니다. 팀 몫을 이미 팀원들이 쓰고 있다는 뜻입니다. `qos` 의 사용량 막대가 바로 이 숫자입니다.

선택지는 둘입니다.

1. 팀원의 잡이 끝나기를 기다립니다.
2. 기본 QoS로 제출해 남는 자원으로 지금 시작합니다. 대신 선점 대상이 됩니다.

!!! note "GPU 타입을 꼭 적어야 하는 이유"
    QoS의 GPU 한도는 GPU 타입마다 걸려 있고, Slurm은 **잡이 요청한 자원**을 보고 한도를 검사합니다.
    타입 없이 `--gres=gpu:4` 로 요청하면 타입별 한도 검사가 제대로 되지 않을 수 있습니다. 그래서 항상 `--gres=gpu:<GPU 타입>:N` 으로 적습니다.

## 우선순위

대기 중인 잡의 순서는 여러 요소를 합친 **우선순위 점수**(multifactor)로 정해집니다. 주요 요소는 둘입니다.

| 요소 | 의미 |
|---|---|
| **QoS** | 가장 큰 비중. 팀 QoS 잡이 기본 QoS 잡보다 앞섭니다 |
| **Fairshare** | 최근에 적게 쓴 사람을 우대. 많이 쓸수록 점수가 내려가고, 시간이 지나면 서서히 회복됩니다 |

요소별 가중치와 회복 속도(반감기)는 클러스터 설정입니다. 확인하려면:

```bash
scontrol show config | grep -i '^Priority'
```

### Backfill

스케줄러는 **Backfill** 방식입니다. 앞에 선 잡이 자원을 기다리는 동안, 스케줄러는 지금 빈 자원에 들어가는 작은 잡이나 짧은 잡을 먼저 실행합니다. 단, 앞 잡의 시작이 늦어지지 않을 때만 그렇게 합니다.
**`--time` 을 현실적으로 짧게 적으면 backfill로 더 빨리 시작**될 수 있습니다.

### 내 위치 확인

```bash
sprio -j <JOBID> -l      # 대기 중인 잡 하나의 우선순위 분해
sprio -l                 # 대기 중인 잡 전체
```

### Fairshare와 과금

여기서 "과금"은 돈이 아니라 **Fairshare 계산에 쓰는 사용량 점수**입니다. 자원마다 얼마나 무겁게 셀지(예: GPU 타입별 가중치)는 파티션 설정 `TRESBillingWeights` 가 정합니다.

```bash
sshare -U                 # 내 fairshare 점수
sshare -a                 # 전체 계정 트리
scontrol show partition | grep -i billing    # 과금 가중치

# 기간별 GPU 사용 시간 리포트
sreport cluster AccountUtilizationByUser start=<YYYY-MM-DD> -t hours
```

## 선점

### 누가 누구를 선점하나

- **팀 QoS는 기본 QoS를 선점**합니다.
- 같은 등급끼리는 서로 선점하지 않습니다.
- 운영자 긴급 QoS가 있다면 그것이 나머지를 선점할 수 있습니다.

Slurm은 "이 QoS가 무엇을 선점하는지"만 기록하고, "무엇에 선점당하는지"는 보여 주지 않습니다. **`qos` 는 두 방향(`PREEMPTS`, `PREEMPTED BY`)을 모두 정리해 보여 줍니다.** 실제 관계는 항상 `qos` 로 확인하세요.

### 선점되면 일어나는 일

1. 잡의 모든 프로세스에 곧바로 **SIGTERM** 이 옵니다. 최소 실행 시간을 보장하지 않으므로 막 시작한 잡도 선점될 수 있습니다.
2. 유예 시간(`GraceTime`) 동안 잡은 계속 돌 수 있습니다. 이 클러스터에서는 <!-- BEGIN GENERATED: slurm:preempt_grace_seconds -->120<!-- END GENERATED: slurm:preempt_grace_seconds -->초입니다.
3. 유예가 끝나면 Slurm이 잡을 끝내고, 그래도 남은 프로세스는 `KillWait` 뒤 **SIGKILL** 로 종료됩니다. 선점부터 SIGKILL까지 최대 <!-- BEGIN GENERATED: slurm:sigkill_after_seconds -->240<!-- END GENERATED: slurm:sigkill_after_seconds -->초입니다.
4. 배치 잡은 **requeue** 됩니다. 큐로 돌아가 다시 실행되고, 체크포인트가 있으면 거기서 이어 갑니다.

유예 시간 안에 체크포인트를 저장하세요: `SIGTERM` 을 잡거나(아래), `sbatch --signal` 로 미리 신호를 받습니다. 다시 시작한 잡은 그 체크포인트에서 이어 돌면 됩니다.

### 유예 시간을 쓰려면 SIGTERM을 잡으세요

```bash
trap 'touch /scratch/$USER/ckpt.request' TERM
```

!!! warning "`--signal` 은 선점에는 오지 않습니다"
    `--signal=B:USR1@120` 같은 옵션은 잡의 **시간 제한**을 기준으로 발동합니다. 선점된 잡은 시간 제한에 도달하지 않으므로 이 시그널을 받지 못합니다.
    (클러스터가 `PreemptParameters=send_user_signal` 을 켜 둔 경우는 예외입니다.)
    시간 제한에는 `--signal` 로, 선점에는 `TERM` 트랩으로 대비합니다. 둘 다 대비하려면 `trap <명령> USR1 TERM` 을 쓰세요.

트랩은 마지막 순간을 쓰는 수단일 뿐입니다. **체크포인트를 주기적으로 남기고, 재시작하면 이어서 돌도록** 짜는 것이 근본 대책입니다. -> [스토리지 가이드](../guide/storage.md), [잡 레시피](../guide/job-recipes.md)

### 인터랙티브 잡은 되살아나지 않습니다

`srun --pty`, `salloc` 은 requeue할 수 없으므로 선점되면 **그냥 취소**됩니다. 잃으면 곤란한 작업은 배치 잡으로 돌리세요.

!!! tip "갑자기 `PD` 로 돌아간 잡"
    실행 중이던 잡이 갑자기 `PD`(pending)로 돌아갔다면 선점됐을 수 있습니다.
    `sacct -D -j <JOBID> --format=JobID,State,Reason,Elapsed` 로 확인하면 `PREEMPTED` 뒤에 같은 JobID로 새 시도가 붙어 있습니다.
    `-D`(`--duplicates`)가 없으면 `sacct`는 가장 최근 시도만 보여 줍니다.

## 자동 할당과 라우팅

잡을 제출하면 클러스터가 규칙에 따라 **GPU 잡이 갈 곳과 받을 CPU, 메모리 양**을 정해 줍니다. 사용자는 **GPU 타입과 개수만** 적으면 됩니다.

### 라우팅: GPU 타입만 적으면 됩니다

| 제출 내용 | 처리 |
|---|---|
| `--gres=gpu:<GPU 타입>:N` (또는 `--gpus=<GPU 타입>:N`) | 그 GPU 타입의 **풀**(그 타입 GPU가 있는 노드 전체)로 제출. Slurm이 가장 먼저 시작할 수 있는 노드를 고릅니다 |
| GPU를 요청했는데 **타입 미지정** | 기본 타입으로 보정되고 안내 메시지가 나옵니다. 규정상 **항상 타입을 적으세요** |
| GPU 잡이 `--partition` 을 직접 지정 | **무시**하고 그 GPU 타입의 풀로 보냅니다 |
| `srun`, `salloc` 으로 여는 **GPU 세션** | <!-- BEGIN GENERATED: rule:sessions -->`srun`, `salloc`으로 여는 GPU 세션은 팀 QoS(`--qos=<팀 QoS>`)로만 시작할 수 있습니다. 팀 QoS 없이 제출하면 `qos`로 내 QoS를 확인하라는 안내와 함께 거부됩니다.<!-- END GENERATED: rule:sessions --> |
| **GPU 미요청 (CPU 전용 잡)** | CPU 잡이 쓸 수 있는 노드 전체로 제출. GPU 잡 몫의 코어는 따로 보호됩니다 |

- 한 GPU 타입이 여러 파티션에 나뉘어 있어도 하나의 풀처럼 동작합니다. 한쪽 파티션이 꽉 차면 잡은 다른 쪽의 빈 노드로 갑니다.
- 특정 노드가 꼭 필요하면 파티션 대신 `-w <노드 이름>` 으로 노드를 지정합니다.
- 같은 보정이 `--gpus`, `--gpus-per-node`, `--gpus-per-task` 와 제출 후의 `scontrol update` 에도 적용됩니다.

GPU 타입 이름은 `sq` 또는 `sinfo -o "%G"` 로 확인합니다.

### 자동 할당: CPU와 메모리는 GPU 수를 따라갑니다

GPU 잡의 **CPU와 메모리는 요청한 GPU 수에 비례해** 자동으로 정해집니다 (`DefCpuPerGPU`, `DefMemPerCPU`). 노드마다 GPU 한 장에 딸린 CPU와 메모리가 넉넉하게 정해져 있습니다.
GPU 잡은 이 값을 바꿀 수 없습니다. 더 많이 잡으면 그 노드에 남은 GPU가 CPU나 메모리가 모자라 놀게 되기 때문입니다.

GPU 한 장당 몫은 노드 크기에 따라 다를 수 있습니다. 실제로 받은 양은 이렇게 확인합니다.

```bash
scontrol show job <JOBID> | grep -i tres
```

| GPU 잡에 적은 옵션 | 처리 |
|---|---|
| `--cpus-per-task`(`-c`), `--cpus-per-gpu`, `--mincpus`, `--exclusive` | **무시**하고 기본값 적용 + 안내 메시지 |
| `--mem`, `--mem-per-cpu`, `--mem-per-gpu` | **거부**. 해당 줄을 지우고 다시 제출 |
| `-n`/`--ntasks`, `--ntasks-per-node` | `-n`은 잡 전체의 GPU 수 이하, `--ntasks-per-node`는 노드당 GPU 수 이하만 허용 (GPU당 태스크 1개). 넘으면 거부. 여러 노드면 `-N` 으로 노드 수를 적습니다 |
| `--ntasks-per-gpu` | 1만 허용 |
| 노드당 GPU 수 (`--gres`, `--gpus`, `-N`과 함께) | **<!-- BEGIN GENERATED: policy:gpus_per_node -->1, 2, 4, 8<!-- END GENERATED: policy:gpus_per_node -->**만 허용. 다른 수는 거부되고, 메시지에 허용되는 수가 나옵니다 |

!!! info "메모리만 거부하는 이유"
    제출 규칙은 사용자가 적은 메모리 값을 지워 "지정 안 함"으로 되돌릴 수 없습니다. 되돌리면 `--mem=0`, 즉 노드 메모리 전부가 되기 때문입니다. 그래서 값을 지우는 대신 제출을 거부합니다.

제출한 뒤 `scontrol update` 로 바꿀 때도 같은 규칙이 적용됩니다. GPU 잡의 파티션은 다시 그 타입의 풀 전체로 넓혀집니다. CPU를 바꾸면 무시되고, 메모리나 태스크 수를 바꾸면 거부됩니다. CPU 잡에 나중에 GPU를 더할 수도 없으니, GPU가 필요하면 잡을 새로 제출하세요.

**CPU 전용 잡**은 이 규칙과 무관하게 CPU와 메모리를 자유롭게 지정합니다. 파티션은 적지 않습니다.

### 자원 격리

잡마다 CPU, GPU, 메모리가 cgroup으로 격리됩니다.

- 다른 잡의 GPU는 **보이지 않습니다**. `nvidia-smi` 에는 내게 배정된 GPU만 나옵니다.
- 메모리 한도를 넘으면 그 잡만 OOM으로 종료됩니다. 노드 전체는 안전합니다.
- 한 자원(GPU, 코어)을 두 잡이 공유하지 않습니다.
- 한 노드에서 내 마지막 잡이 끝나면 그 노드에 남은 내 프로세스와 임시 파일(`/tmp`, `/dev/shm`)이 정리됩니다.

## 사용량 조회

```bash
# 끝난 잡 상세 (실패 원인 추적에 유용)
sacct -j <JOBID> --format=JobID,JobName,QOS,State,ExitCode,Elapsed,AllocTRES%50,MaxRSS,Reason

# 기간 지정
sacct -S <YYYY-MM-DD> -E now -X --format=JobID,JobName,State,Elapsed,AllocTRES%40

# 실행 중인 잡의 실시간 사용량 (메모리, CPU)
sstat -j <JOBID> --format=JobID,MaxRSS,AveCPU,NTasks

# 내 association과 한도
sacctmgr show assoc user=$USER format=Account,User,QOS%40,GrpTRES,MaxJobs,MaxSubmit

# QoS 목록과 한도
sacctmgr show qos format=Name,Priority,Flags,MaxWall,MaxTRESPU%30,GrpTRES%30
```

## 자주 쓰는 옵션

```text
# 자원
--gres=gpu:<GPU 타입>:N          GPU 타입과 개수 (항상 명시)
--gpus=<GPU 타입>:N              대안 표기
--gpus-per-node=<GPU 타입>:N     대안 표기
--cpus-per-task=N                태스크당 CPU (CPU 전용 잡만. GPU 잡은 무시 -> 자동)
--cpus-per-gpu=N                 GPU당 CPU (GPU 잡은 무시 -> 자동)
--mem=NG                         메모리 (CPU 전용 잡만. GPU 잡은 거부 -> 자동)
--nodes=1                        노드 수
--ntasks=N / --ntasks-per-node=N 태스크 분배 (GPU 잡은 GPU 수 이하)

# 메타, 스케줄
--job-name=NAME                  잡 이름
--qos=<팀 QoS>                   QoS (생략하면 기본 QoS)
--time=D-HH:MM:SS                최대 실행 시간 (짧게 적을수록 backfill에 유리)
--dependency=afterok:JOBID       선행 잡이 성공한 뒤 시작
--array=A-B%C                    배열 잡 (동시 C개)
--signal=B:USR1@120              시간 제한 전에 시그널 받기 (선점에는 오지 않음 -> TERM 트랩)

# 입출력, 실행
--output=PATTERN --error=PATTERN %x 잡 이름, %j 잡 ID, %N 노드, %a 배열 인덱스
--chdir=DIR                      작업 디렉터리
--export=ALL|NONE|VAR=<값>         환경 변수 전달
--mail-type=END,FAIL             잡 알림 (Slack DM, 아래)

# 컨테이너
--container-image=  --container-mounts=  --container-workdir=
```

잡 알림: <!-- BEGIN GENERATED: service:job_notices -->잡에 `--mail-type=END,FAIL`(또는 `BEGIN`, `ALL` 등)을 적으면 그 일이 생길 때 잡의 주인에게 Slack DM으로 알려 드립니다. 메일은 보내지 않으니 `--mail-user`는 적지 않으셔도 되고, 적어도 받는 사람은 잡의 주인입니다. 짧은 사이에 생긴 알림은 한 메시지로 모아 드립니다. 받지 않으려면 봇의 홈 탭에서 끄실 수 있습니다.<!-- END GENERATED: service:job_notices -->

`--time` 이 파티션 상한보다 길면 제출은 되지만 `PartitionTimeLimit` 사유로 시작하지 못하고 계속 대기합니다. 상한은 `qos` 와 `scontrol show partition` 으로 확인하세요.
컨테이너 옵션은 [컨테이너 가이드](../guide/containers.md)를 보세요.

전체 옵션은 `man sbatch`, `man srun`, 또는 [Slurm 공식 문서](https://slurm.schedmd.com/sbatch.html)를 참고하세요.

## 환경 변수

잡 안에서 쓸 수 있는 주요 변수입니다.

| 변수 | 의미 |
|---|---|
| `SLURM_JOB_ID` | 잡 ID |
| `SLURM_JOB_NODELIST` | 배정된 노드 목록 |
| `SLURM_JOB_NUM_NODES` | 노드 수 |
| `SLURM_NTASKS` / `SLURM_NPROCS` | 태스크 수 |
| `SLURM_CPUS_PER_TASK` | 태스크당 CPU |
| `SLURM_GPUS` / `SLURM_GPUS_ON_NODE` | 할당된 GPU 수 |
| `CUDA_VISIBLE_DEVICES` | 내게 보이는 GPU 인덱스 (cgroup으로 격리됨) |
| `SLURM_ARRAY_TASK_ID` / `SLURM_ARRAY_JOB_ID` | 배열 잡 인덱스, ID |
| `SLURM_PROCID` / `SLURM_LOCALID` | 분산 실행 시 전역, 로컬 랭크 |
| `SLURM_SUBMIT_DIR` | 제출한 디렉터리 |

## 더 읽기

- 컨테이너 -> [컨테이너 가이드](../guide/containers.md)
- 모듈, CUDA -> [소프트웨어 모듈](../guide/modules.md)
- 문제 해결 -> [트러블슈팅](../guide/troubleshooting.md)
