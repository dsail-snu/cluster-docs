# 모니터링과 상태 확인

지금 클러스터가 얼마나 바쁜지, 내 잡이 GPU를 잘 쓰고 있는지 확인하는 방법입니다.

이 사이트에는 노드, GPU 타입, 파티션, QoS 같은 클러스터 구성을 적지 않습니다. 구성은 늘 현재 값을 보여 주는 `sq`, `qos`,
`sinfo`로 확인하세요. <!-- BEGIN GENERATED: service:overview -->한눈에 보는 개요는 **웹 포털에 로그인한 뒤** 상단 메뉴의 **클러스터** 페이지에서 보실 수 있습니다. 포털 주소는 계정을 받을 때 함께 알려 드립니다.<!-- END GENERATED: service:overview -->

## 자원 현황 한눈에 보기: `sq`

`sq`는 모든 노드에 설치된 클러스터 현황 명령입니다. 큐를 상태별 색으로 보여 주고, 표 여러 개를 출력합니다.
사람별 점유, 팀별 몫, 그리고 GPU 타입별, 노드별 CPU, 메모리, GPU 사용량입니다.
표에는 잡이 실제로 요청할 수 있는 자원만 셉니다. 그래서 표의 숫자가 바로 지금 요청할 수 있는 양입니다.

```bash
sq          # 내 잡 + 사람별 점유(USERS) + 팀별 몫(TEAMS) + 자원 표
sq --help   # 전체 옵션 (항상 최신)
```

- 자원 표의 각 칸은 `사용/전체`입니다.
- 노드 상태(`STATE`)는 `sinfo`가 보여 주는 그대로입니다: `idle`(비어 있음), `mix`(일부 사용),
  `alloc`(꽉 참), `drain`/`drng`(관리자가 새 잡을 막음, `drng`는 돌던 잡이 끝나기를 기다리는 중), `down`(쓸 수 없음).
  새 잡을 받지 못하는 노드는 빨간색으로 보입니다.
- 상태 뒤의 기호는 노드에 붙은 표시입니다. 자주 보이는 것은 `*`(노드가 응답하지 않음, 새 잡이 들어가지 않음),
  `-`(대기 중인 잡을 위해 비워 두는 중), `~`(전원이 꺼져 있음)입니다. 전체 목록은 `sq --help`에 있습니다.
- 대기 중인 잡에는 Slurm의 대기 사유 코드(`(Priority)`, `(Resources)` 등)가 그대로 나오고, 비슷한 사유끼리 같은 색으로 묶입니다.
  사유별 대처는 [문제 해결](troubleshooting.md#잡이-안-돌-때-pending)에 있습니다.

사용자 표(USERS)는 사람마다 다음을 보여 줍니다. 팀(`TEAM`), 실행 중인 잡 수(`RUN`), 대기 중인 잡 수(`PEND`, 배열 잡은 대기 중인 태스크마다 하나로 셉니다),
그리고 쓰고 있는 노드, CPU, 메모리, GPU입니다. GPU는 타입마다 두 칸으로 나뉩니다. `HIGH`는 높은 우선순위 QoS(팀 몫)로 쓰는 GPU 수이고,
`LOW`는 낮은 QoS(선점될 수 있음)로 쓰는 GPU 수입니다.

그 아래 팀 표(TEAMS)에는 팀마다 한 줄이 있습니다. 팀(`TEAM`), 그 팀의 높은 우선순위 QoS(`QOS`), 그리고 GPU 타입마다
팀 몫을 지금 얼마나 쓰고 있는지(막대, 사용/한도)가 나옵니다. 팀 몫은 팀원 모두가 함께 씁니다. 몫이 다 찼다면 사용자 표에서
같은 팀이면서 `HIGH` GPU를 쓰고 있는 분을 찾아, GPU를 비워 주실 수 있는지 여쭤 보세요.

## 내가 쓸 수 있는 몫: `qos`

`sq`가 "클러스터에 자원이 얼마나 남았나"를 보여 준다면, `qos`는 **"내가 그중 얼마를 쓸 수 있나"** 를 보여 줍니다.
클러스터가 한가해 보이는데 내 잡이 `(QOSGrpGRES)` 같은 사유로 대기 중이라면 이쪽을 보세요.

```bash
qos         # 사용자에게 주어진 QoS(내 것 표시)와 우선순위, 선점 관계, 팀 몫 사용량
qos --help  # 전체 옵션 (항상 최신)
```

QoS가 무엇인지는 [Slurm 레퍼런스](../reference/slurm.md#qos)에 있습니다.

!!! tip "자세한 옵션"
    자세한 옵션과 표 읽는 법은 `sq --help`, `qos --help`를 보세요. 도움말은 명령에서 바로 만들어지므로 항상 최신입니다.
    옵션 목록은 [Slurm 레퍼런스](../reference/slurm.md#클러스터-명령의-옵션)에도 있습니다.

## Slurm 기본 명령

### 노드와 자원

```bash
sinfo                               # 파티션별 요약
sinfo -N -l                         # 노드별 상세 (CPU, 메모리, 상태)
sinfo -o "%G"                       # GPU 타입 확인
scontrol show node <노드 이름>       # 특정 노드의 할당, 여유 자원
```

### 큐

```bash
squeue                  # 전체
squeue --me             # 내 잡
squeue --me --start     # 대기 잡의 예상 시작 시각 (추정)
```

### 우선순위

```bash
sprio -l                # 대기 잡의 우선순위 구성
sprio -j <JOBID> -l     # 특정 잡의 우선순위 분해
```

우선순위가 어떻게 정해지는지는 [Slurm 레퍼런스](../reference/slurm.md#우선순위)를 보세요.

### 끝난 잡 분석

```bash
sacct -j <JOBID> --format=JobID,JobName,State,Elapsed,AllocTRES%40,MaxRSS,ExitCode
sacct -S today -X --format=JobID,JobName,State,Elapsed
```

- `MaxRSS`로 실제 메모리 사용량을 보고 다음 잡의 요청량을 조정하세요.
- `State`, `ExitCode`로 실패 원인을 추적합니다. -> [문제 해결](troubleshooting.md)

## 내 잡이 도는 노드

- `sq`: 내 잡의 **NODE(REASON)** 열에 나옵니다. 도는 잡은 그 노드가, 기다리는 잡은 기다리는 이유가 보입니다.
- `scontrol show job <JOBID>`: `NodeList`에 노드가, `AllocTRES`에 받은 GPU 수가 나옵니다.
- `gpu-usage <JOBID>`: 잡이 돈 노드와 GPU 수, 그 GPU가 실제로 한 일을 보여 줍니다.
- [웹 대시보드](#웹-대시보드)에서는 잡이 도는 노드와 GPU를 찾아 그 노드의 상태를 볼 수 있습니다.

## 내 잡이 GPU를 잘 쓰는지

노드에 들어가지 않고 보려면 `gpu-usage <JOBID>`를 씁니다. 실시간으로 보려면 잡이 도는 노드에 들어갑니다.

```bash
srun --jobid=<JOBID> --overlap --pty bash -i

# 그 안에서
nvidia-smi              # GPU 사용률, 메모리 (반복: watch -n1 nvidia-smi)
nvidia-smi dmon         # 시간축 GPU 모니터
htop                    # CPU, 메모리
```

- **GPU 사용률이 낮게 머물면** 데이터 로딩 병목일 수 있습니다. 데이터로더 워커 수를 늘리고,
  데이터를 `/scratch`에 두고, 묶음 포맷을 쓰세요. -> [스토리지](storage.md)
- **GPU 메모리가 거의 차지 않으면** 배치 크기를 키워 자원을 효율적으로 쓰세요.

## 웹 대시보드

클러스터와 내 잡의 상태를 브라우저에서 늘 볼 수 있습니다. 잡을 내기 전에 지금 얼마나 바쁜지 가늠하거나,
내 잡이 도는 노드의 GPU와 CPU, 메모리를 확인할 때 쓰세요.

<!-- BEGIN GENERATED: service:dashboard -->대시보드는 웹 포털에 클러스터 계정으로 로그인한 뒤 상단 메뉴의 **Grafana**에서 여실 수 있습니다. 포털 주소는 계정을 받을 때 함께 알려 드립니다.<!-- END GENERATED: service:dashboard -->

<!-- BEGIN GENERATED: service:dashboards -->
- **GPU / Nodes**: GPU 노드 한 대의 GPU(사용률, 메모리, 온도, 전력)와 CPU, 메모리, 디스크, 네트워크. 위쪽의 **hostname**에서 노드를 고릅니다.
- **Node Exporter / Hosts**: 모든 호스트의 자세한 수치(CPU, 메모리, 디스크, 네트워크). 위쪽의 **nodename**에서 호스트를 고릅니다.
- **Slurm / Scheduler**: 클러스터 전체의 노드 상태, 쓰고 있는 CPU와 GPU, 도는 잡과 기다리는 잡.
- **Storage / NFS and disks**: 공유 스토리지(NFS)와 디스크를 누가 얼마나 읽고 쓰는지: 노드별, 잡별(**Top jobs by I/O**).
- **Storage / per person**: 한 사람의 파일시스템별 사용량과 파일 수(경고 수준과 한도), 정리하면 좋을 폴더, 내 잡과 로그인의 I/O를 시간에 따라 봅니다. `disk-usage`가 보여 주는 값입니다. 위쪽의 **user**에서 사람을 고릅니다.
- **Slurm / GPU allocation**: 지금 GPU마다 누가 어떤 잡으로 쓰는지(**Allocations now**), 잡별 GPU 사용률과 메모리, 사람별, 팀별 할당. 내 잡이 도는 노드와 GPU를 여기서 찾습니다.
<!-- END GENERATED: service:dashboards -->

## Slack 알림

- **GPU 사용량 보고**: <!-- BEGIN GENERATED: reports:usage -->매시간<!-- END GENERATED: reports:usage --> 클러스터 GPU 사용 현황이 Slack <!-- BEGIN GENERATED: chat:status -->`#infra-status`<!-- END GENERATED: chat:status -->에 올라옵니다.
- **<!-- BEGIN GENERATED: term:idle_job -->할당받은 GPU를 쓰지 않는 잡<!-- END GENERATED: term:idle_job --> 알림**: <!-- BEGIN GENERATED: rule:idle -->Slurm 잡이 할당받은 GPU를 **2시간 넘게 쓰지 않으면** 알려 드립니다. 할당받은 GPU를 **6시간** 동안 쓰지 않은 잡은 자동으로 취소되며, 취소 **1시간 전**에 미리 알려 드립니다.<!-- END GENERATED: rule:idle -->
  알림을 받으셨다면 잡이 GPU를 제대로 쓰는지 확인해 주시고, 쓰지 않는다면 취소해 주세요.
  -> [디버깅 규정](../policy/rules.md#디버깅)
- **잡 알림**: <!-- BEGIN GENERATED: service:job_notices -->잡에 `--mail-type=END,FAIL`(또는 `BEGIN`, `ALL` 등)을 적으면 그 일이 생길 때 잡의 주인에게 Slack DM으로 알려 드립니다. 메일은 보내지 않으니 `--mail-user`는 적지 않으셔도 되고, 적어도 받는 사람은 잡의 주인입니다. 짧은 사이에 생긴 알림은 한 메시지로 모아 드립니다. 받지 않으려면 봇의 홈 탭에서 끄실 수 있습니다.<!-- END GENERATED: service:job_notices -->

## 더 읽기

- 잡이 안 돌 때 -> [자주 묻는 질문과 문제 해결](troubleshooting.md)
- Slurm 개념 -> [Slurm 기초](../start/slurm-basics.md)
