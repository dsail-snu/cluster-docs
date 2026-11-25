# 자주 묻는 질문과 문제 해결

자주 막히는 상황과 해결법입니다. 증상으로 찾아보세요.

## 접속과 보안

### 접속이 갑자기 안 되고 비밀번호도 안 먹어요

비밀번호를 여러 번 틀리면 접속한 IP가 자동으로 차단됩니다.

- **해결**: <!-- BEGIN GENERATED: bot:unban -->`/cluster unban`으로 해제를 신청해 주세요.<!-- END GENERATED: bot:unban --> -> [도움 받기](../help.md)
- **예방**: SSH 키를 등록해서 비밀번호 없이 접속하세요. -> [접속하기](../start/connect.md), [접속 보안](../policy/rules.md#접속-보안)

### 밖에서 접속이 안 돼요

외부 접속에 쓰는 주소와 포트는 계정 발급 때 관리자가 알려 줍니다.

```bash
ssh -p <SSH 포트> <아이디>@<로그인 주소>
```

자세한 방법은 [접속하기](../start/connect.md)를 보세요.

### 계산 노드에 `ssh`했더니 거부돼요

계산 노드는 **내 잡이 실행 중일 때만** 들어갈 수 있습니다. 내 잡이 도는 노드에 들어가려면:

```bash
srun --jobid=<JOBID> --overlap --pty bash -i
```

### 로그인 노드가 느리거나 내 프로세스가 죽어요

<!-- BEGIN GENERATED: login:limits -->로그인 노드에는 한 사람당 CPU 8개, 메모리 64 GB, 프로세스 4,096개까지 쓰실 수 있도록 제한이 걸려 있습니다.<!-- END GENERATED: login:limits --> 무거운 작업이 이 한도에 걸린 것이니,
**연산은 Slurm으로 계산 노드에 제출**하세요. -> [첫 잡 실행하기](../start/first-job.md)

## 잡이 안 돌 때 (Pending)

`squeue --me`의 `NODELIST(REASON)` 열이나 `sq`에 대기 사유가 나옵니다.

| 사유 | 뜻 | 대처 |
|------|-----|------|
| `Resources` | 요청한 만큼의 자원이 아직 비지 않음 | 기다리기. GPU 수나 `--time`을 줄이면 빈틈(backfill)에 먼저 들어갈 수 있음 |
| `Priority` | 우선순위가 더 높은 잡이 앞에 있음 | 기다리기. `<팀 QoS>` 사용 검토 |
| `QOSGrpGRES`, `QOSMaxGRESPerUser`, `AssocGrp*` 등 | QoS나 계정 한도(동시 GPU 수, 잡 수 등)에 도달 | 내 잡이나 팀 잡이 끝나면 시작됨. `qos`로 한도와 사용량 확인 |
| `QOSMax*PerJob` 등 | 잡 하나의 요청이 한도를 넘음 | 요청을 고치기 전에는 시작되지 않음. 잡을 취소하고 요청을 줄여 다시 제출 |
| `ReqNodeNotAvail`, `Reserved` | 점검이나 예약으로 노드를 쓸 수 없음 | 점검이 끝날 때까지 기다리기. 공지 확인 |
| `Dependency` | 선행 잡(`--dependency`)을 기다리는 중 | 선행 잡 상태 확인 |
| `DependencyNeverSatisfied` | 선행 잡이 조건을 만족하지 못하고 끝남 | 잡을 취소하고 다시 제출 |
| `BeginTime` | `--begin`으로 정한 시각을 기다리는 중 | 정상. 그 시각에 시작됨 |
| `JobHeldUser` | 본인이 잡을 보류함 (`scontrol hold`) | `scontrol release <JOBID>` |
| `JobHeldAdmin` | 관리자가 잡을 보류함 | 관리자에게 문의 |
| `PartitionTimeLimit`, `BadConstraints` | 요청이 노드나 시간 조건에 맞지 않음 | `--time`, GPU 타입, 개수 점검 |

진단:

```bash
squeue --me --start                                      # 예상 시작 시각 (추정)
scontrol show job <JOBID> | grep -iE 'Reason|JobState|TRES'
sprio -j <JOBID> -l                                      # 우선순위 분해
qos                                                      # 내 QoS 한도와 팀 사용량
```

QoS와 우선순위의 배경은 [Slurm 레퍼런스](../reference/slurm.md#qos)를 보세요.

## 제출이 거부될 때

### `Requested node configuration is not available`

노드 하나가 가진 것보다 많은 자원을 요청했습니다. 예: 노드 하나에 달린 GPU보다 많은 GPU를 한 노드에 요청.
노드별 GPU 수는 `sq` 또는 `sinfo -N -o "%N %G"`로 확인하세요.

### `Invalid qos specification`, `Invalid account`

쓸 수 없는 QoS나 계정을 지정했습니다. `qos`로 내가 쓸 수 있는 QoS를 확인하세요.
우선순위가 높은 QoS는 **본인 팀 것**(`<팀 QoS>`)만 쓸 수 있습니다.

### `Invalid generic resource (gres) specification`

GPU 타입 문자열을 확인하세요. 유효한 값은 `sinfo -o "%G"` 또는 `sq`로 볼 수 있습니다.

```bash
--gres=gpu:<GPU 타입>:<개수>
```

## 실행 중 문제

### 코드나 컨테이너에서 GPU가 안 보여요 (`torch.cuda.is_available()` 가 `False`)

- 잡에 `--gres=gpu:<GPU 타입>:<개수>`를 줬는지 확인하세요. 안 주면 GPU가 0개입니다.
- 잡 안에서 `echo $CUDA_VISIBLE_DEVICES`, `nvidia-smi`로 배정된 GPU를 확인하세요.
- 로그인 노드에서는 GPU가 보이지 않는 것이 정상입니다. 잡 안에서 확인하세요.
- pip 휠의 CUDA 버전과 드라이버가 맞는지 확인하세요. 애매하면 CUDA가 들어 있는 컨테이너를 쓰세요. -> [컨테이너](containers.md)

### 잡이 메모리 부족으로 죽어요 (OOM, `oom-kill`)

잡은 할당받은 메모리까지만 쓸 수 있습니다.

- 배치 크기나 데이터로더 워커 수를 줄이세요.
- 실제 사용량 확인: 끝난 잡은 `sacct -j <JOBID> --format=JobID,MaxRSS,State`,
  실행 중인 잡은 `sstat -j <JOBID> --format=MaxRSS`.
- GPU 잡의 메모리는 GPU 수에 따라 자동으로 정해지고, `--mem`을 적으면 제출이 거부됩니다. 그래도 모자라면 관리자에게 문의하세요.
  -> [자동 할당](../reference/slurm.md#자동-할당과-라우팅)

### 잡이 갑자기 다시 큐로 돌아갔어요 (REQUEUE)

우선순위가 더 높은 잡에 **선점**됐습니다. 기본 QoS로 제출한 잡은 `<팀 QoS>` 잡에 밀릴 수 있습니다.

```bash
sacct -D -j <JOBID> --format=JobID,State,Reason,Elapsed   # PREEMPTED 이면 선점 (-D: 다시 큐에 들어가기 전 기록까지)
qos                                                     # 무엇이 내 QoS를 선점하는지
```

- 선점되면 `SIGTERM`이 가고 짧은 유예 시간 뒤 종료됩니다. `trap '...' TERM`으로 그 사이에 체크포인트를 남기세요.
  `--signal`로 정한 신호는 시간 제한이 다가올 때만 오고, 선점될 때는 오지 않습니다. -> [선점](../reference/slurm.md#선점), [체크포인트](storage.md#체크포인트-선점-대비)
- 인터랙티브 잡(`srun --pty`)은 다시 큐로 돌아가지 않고 **그냥 취소**됩니다.

### `module: command not found`, 또는 원하는 CUDA 버전이 없어요

`module avail cuda`로 올라와 있는 버전을 확인하세요. 원하는 버전이 없으면 CUDA가 들어 있는 컨테이너를 쓰거나
관리자에게 요청하세요. -> [모듈](modules.md)

### Ray가 `/tmp/ray` 권한 오류로 시작하지 않아요

Ray는 기본으로 노드의 `/tmp/ray`에 소켓과 로그를 둡니다. 같은 노드에서 다른 사람의 Ray가 이 디렉터리를 먼저
만들었으면, 내 Ray는 `Permission denied`로 시작하지 못합니다. 내 Ray 둘이 한 노드에서 돌면 서로의 세션이 섞입니다.
잡마다 따로 쓰도록 스크립트 안에서 경로를 지정하세요.

```bash
export RAY_TMPDIR=/tmp/ray-$SLURM_JOB_ID      # ray.init(), ray start 가 이 아래(<경로>/ray)를 씁니다
# 또는: ray start --head --temp-dir=/tmp/ray-$SLURM_JOB_ID
```

- `/tmp` 아래의 짧은 경로를 쓰세요. Ray의 소켓 경로에는 길이 제한(107바이트)이 있어 `/home` 아래의 긴 경로는 실패할 수 있습니다.
  공유 스토리지에 두면 느리기도 합니다.
- 잡이 끝나면 내 `/tmp` 파일은 정리됩니다. 로그를 남기려면 잡 안에서 필요한 것만 홈으로 복사하세요.
  -> [자원 격리](../reference/slurm.md#자원-격리)

### `/home` 파일 접근이 느려요

누군가 공유 스토리지에 큰 부하를 주고 있을 수 있습니다. 본인도 데이터가 크거나 작은 파일이 많은 I/O(읽기와 쓰기)는
`/scratch`에서 하세요. -> [스토리지](storage.md#공유-스토리지를-느리게-만들지-않는-법)

## 자원

### 파티션, CPU, 메모리를 꼭 지정해야 하나요?

GPU 잡은 **GPU 타입과 개수만** 지정하면 됩니다. 맞는 파티션으로 자동으로 보내지고 CPU, 메모리도
GPU 수에 맞춰 배정됩니다. GPU 잡에 메모리를 적으면 제출이 거부됩니다. CPU 전용 잡은 CPU 수만 필요한 만큼 주세요.
-> [자동 할당과 라우팅](../reference/slurm.md#자동-할당과-라우팅)

### 어떤 GPU 타입을 써야 하나요?

`sq`로 클러스터에 있는 GPU 타입과 남은 양을 보고 고르세요. 큰 모델처럼 GPU 메모리가 많이 필요하면
메모리가 큰 타입을, 그렇지 않으면 여유 있는 타입을 쓰는 것이 좋습니다. GPU 타입마다 공정 분배(fairshare) 점수에
세는 가중치가 다를 수 있습니다. -> [Fairshare와 과금](../reference/slurm.md#fairshare와-과금)

### 내가 자원을 얼마나 썼는지 보고 싶어요

```bash
sshare -U                                                            # 내 fairshare
sreport cluster AccountUtilizationByUser start=<시작 날짜> -t hours   # 기간별 사용량
```

## 규정에서 자주 헷갈리는 것

### Jupyter, 인터랙티브 셸, 띄워 둔 추론 서버도 규제 대상인가요?

네. GPU를 언제 쓸지 사용자가 직접 정한다면 모두 **GPU 점유 세션**이고, 그 규칙을 따릅니다.
`<팀 QoS>`로 제출하고, 다 쓰면 바로 종료하세요. -> [GPU 점유 규정](../policy/rules.md#디버깅)

### AI 에이전트로 잡 제출이나 SSH를 해도 되나요?

쓸 수 있습니다. 다만 그 에이전트에 [AI 에이전트 규칙](../policy/ai-agents.md)(접속 재시도 제한, 제출 전 현황 확인,
잡 제출 규칙 등)을 반드시 넣어야 합니다.
에이전트가 한 일의 책임은 그 에이전트를 실행한 사용자에게 있습니다.

## 그래도 안 되면

1. `scontrol show job <JOBID>`, `sacct -j <JOBID>` 출력을 확인하고,
2. 무엇을 시도했는지와 함께 문의하세요. -> [도움 받기](../help.md)

막연히 "안 돼요"보다 **잡 ID, 에러 메시지, 실행한 명령**을 함께 알려 주면 훨씬 빨리 해결됩니다.
