# 모니터링과 상태 확인

지금 클러스터가 얼마나 바쁜지, 내 잡이 GPU를 잘 쓰고 있는지 확인하는 방법입니다.

노드, GPU 타입, 파티션, QoS 같은 클러스터의 구성은 이 사이트에 적지 않습니다. 언제나 지금 값인 `sq`, `qos`,
`sinfo`로 보고, 한눈에 보는 개요는 **웹 포털에 로그인한 뒤** 상단 메뉴의 클러스터 페이지에서 봅니다.
포털 주소와 접속 정보는 계정을 받을 때 안내됩니다.

## 자원 현황 한눈에 보기: `sq`

`sq`는 모든 노드에 설치된 클러스터 현황 명령입니다. 큐를 상태별 색으로 보여 주고,
사용자별 점유와 GPU 타입별, 노드별 CPU, 메모리, GPU 사용량 표를 출력합니다.
잡이 실제로 요청할 수 있는 자원만 집계하므로 표의 숫자가 곧 지금 요청 가능한 양입니다.

```bash
sq          # 큐 + 사용자별 점유 + 자원 표
sq -a       # 잡 목록에 모든 사람의 잡까지 (--all). 내 잡만은 -m (--me)
sq --help   # 전체 옵션 (항상 최신)
```

- 자원 표의 각 칸은 `사용/전체`입니다.
- 노드 상태는 `sinfo`와 같은 단어로 보입니다: `idle`(비어 있음), `mix`(일부 사용),
  `alloc`(꽉 참), `drain`(관리자가 새 잡을 막음), `down`(쓸 수 없음).
- 대기 중인 잡은 Slurm의 사유 코드(`(Priority)`, `(Resources)` 등)를 그대로 보여 주고, 색으로 계열을 구분합니다.
  사유별 대처는 [문제 해결](troubleshooting.md#잡이-안-돌-때-pending)에 있습니다.

사용자 표(USERS)는 사람마다 팀과, GPU 타입별로 `hi / lo`(높은 우선순위 QoS와 낮은 QoS로 쥔 GPU 수)와
`PEND`(대기 중인 잡이 요청한 GPU 수)를 보여 줍니다. 그 아래 HIGH QOS QUOTAS는 팀마다 높은 우선순위 QoS의
GPU 타입별 몫(막대, 사용/한도)과 그것을 쥔 사람을 많이 쥔 순서로 보여 줍니다. 몫은 팀 전체의 것이니,
자리가 없으면 쥔 사람에게 GPU를 비워 달라고 하세요.

## 내가 쓸 수 있는 몫: `qos`

`sq`가 "클러스터에 자원이 얼마나 남았나"를 보여 준다면, `qos`는 **"내가 그중 얼마를 쓸 수 있나"** 를 보여 줍니다.
클러스터가 한가해 보이는데 내 잡이 `(QOSGrpGRES)` 같은 사유로 대기 중이라면 이쪽을 보세요.

```bash
qos         # 제출할 수 있는 QoS와 우선순위, 선점 관계, 팀 몫 사용량
qos -m      # 내 것만 (--me). 전체는 -a (--all), sq와 같은 뜻
```

QoS가 무엇인지는 [Slurm 레퍼런스](../reference/slurm.md#qos)에 있습니다.

!!! tip "자세한 옵션"
    자세한 옵션은 `sq --help`, `qos --help`를 보세요. 도움말은 명령에서 바로 만들어지므로 항상 최신입니다.

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

## 내 잡이 GPU를 잘 쓰는지

잡이 도는 노드에 들어가 실시간으로 봅니다.

```bash
srun --jobid=<JOBID> --overlap --pty bash -i

# 그 안에서
nvidia-smi              # GPU 사용률, 메모리 (반복: watch -n1 nvidia-smi)
nvidia-smi dmon         # 시간축 GPU 모니터
nvtop                   # GPU용 htop (설치되어 있으면)
htop                    # CPU, 메모리
```

- **GPU 사용률이 낮게 머물면** 데이터 로딩 병목일 수 있습니다. 데이터로더 워커 수를 늘리고,
  데이터를 `<스크래치 경로>`에 두고, 묶음 포맷을 쓰세요. -> [스토리지](storage.md)
- **GPU 메모리가 거의 차지 않으면** 배치 크기를 키워 자원을 효율적으로 쓰세요.

## 웹 대시보드

GPU 노드의 상태(GPU 사용률, 메모리, 온도, 전력, CPU, 메모리, 네트워크 등)를 브라우저에서 상시
볼 수 있습니다. 잡을 내기 전에 지금 얼마나 바쁜지 가늠하기 좋습니다.

대시보드는 클러스터 웹 포털 `<포털 주소>`에서 클러스터 계정으로 로그인한 뒤 엽니다.

!!! note "포털 도입 중"
    웹 포털은 도입 중입니다. 그전까지는 관리자가 대시보드 접속 방법을 공지합니다.

## Slack 알림

- **GPU 사용량 보고**: 매시간 클러스터 GPU 사용 현황이 Slack `#infra-status`에 올라옵니다.
- **유휴 GPU 알림**: <!-- BEGIN GENERATED: rule:idle -->Slurm 잡으로 GPU를 할당받아 두고 **2시간 넘게 쓰지 않으면** 알려 드립니다. **6시간** 동안 GPU를 쓰지 않은 잡은 자동으로 취소되며, 취소 **1시간 전**에 미리 알려 드립니다.<!-- END GENERATED: rule:idle -->
  알림을 받으셨다면 잡이 GPU를 제대로 쓰는지 확인해 주시고, 쓰지 않는다면 취소해 주세요.
  -> [디버깅 규정](../policy/index.md#디버깅)

## 더 읽기

- 잡이 안 돌 때 -> [자주 묻는 질문과 문제 해결](troubleshooting.md)
- Slurm 개념 -> [Slurm 기초](../start/slurm-basics.md)
