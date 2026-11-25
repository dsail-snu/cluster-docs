# Slurm 기초

Slurm을 **한 번도 써 보지 않은 사람**을 위한 문서입니다. 개념부터 첫 GPU 잡 실행까지 차근차근 갑니다.

## Slurm이 뭔가요? (왜 그냥 GPU에 못 붙나요)

여러 사람이 여러 대의 GPU 노드를 나눠 씁니다. 각자 마음대로 GPU 노드에 접속해서 코드를 돌리면:

- 누가 어떤 GPU를 쓰는지 알 수 없고,
- 두 사람이 같은 GPU를 동시에 써서 메모리 부족(OOM)으로 둘 다 죽고,
- 자원이 비어도 누가 먼저 쓸지 정리가 안 됩니다.

**Slurm**은 이 문제를 해결하는 **작업 스케줄러(job scheduler)** 입니다.
"GPU 2장 주세요. 이 명령을 실행해 주세요"라고 **작업(job)을 제출(submit)** 하기만 하면 Slurm이:

1. 조건에 맞는 빈 노드를 찾고,
2. 그 자원을 나에게 **독점 배정(allocation)** 하고,
3. 명령을 실행하고,
4. 끝나면 자원을 회수합니다.

!!! tip "비유"
    Slurm은 **식당의 웨이터**입니다. 빈자리(GPU)를 직접 찾아 앉는 게 아니라, 웨이터에게 "몇 명이요" 하고 줄을 서면 자리가 나는 대로 안내해 줍니다.

## 꼭 알아야 할 용어

| 용어 | 뜻 |
|------|-----|
| **Job (잡)** | 내가 제출하는 작업 하나. 잡마다 고유 번호(JOBID)가 붙습니다. |
| **Partition (파티션)** | 노드들의 묶음(큐). 이 클러스터에서는 Slurm이 GPU 타입을 보고 알맞은 파티션을 골라 주므로 **사용자가 직접 적지 않습니다.** |
| **GRES** | "Generic RESource". GPU 같은 특수 자원. `--gres=gpu:<GPU 타입>:2` = "그 타입 GPU 2장". |
| **QoS** | "Quality of Service". 잡의 우선순위, 한도, 선점 권한을 정하는 등급. 기본 QoS는 선점될 수 있고, 팀마다 팀 QoS가 있습니다. 내 것은 **`qos`** 로 확인합니다. -> [QoS](../reference/slurm.md#qos) |
| **선점 (preemption)** | 높은 QoS 잡이 낮은 QoS 잡의 자원을 가져가는 것. 밀려난 잡은 큐로 돌아가 처음부터 다시 돕니다. -> [선점](../reference/slurm.md#선점) |
| **Allocation (할당)** | Slurm이 나에게 배정한 자원 한 묶음. 그 안에서 여러 명령(step)을 실행할 수 있습니다. |

## 가장 많이 쓰는 명령 4개

| 명령 | 한 줄 설명 |
|------|-----------|
| `srun` | **지금 바로 실행** (대화형, 즉시). 자원을 잡고 명령을 바로 돌립니다. |
| `sbatch` | **스크립트를 큐에 제출** (배치). 가장 일반적인 실전 방식. |
| `squeue` | 큐에 어떤 잡들이 있는지 보기. |
| `scancel` | 잡 취소. |

여기에 자원 현황을 보는 `sinfo`, 끝난 잡 기록을 보는 `sacct`까지 알면 일상 사용은 충분합니다.

## 실습 1: 자원 현황 보기 (`sinfo`, `squeue`)

```bash
sinfo                                    # 파티션별 노드 상태 요약
sinfo -N -l                              # 노드별 상세 (CPU, 메모리, 상태)
sinfo -o "%P %.6D %.10c %.10m %.20G %t"  # 파티션/노드 수/CPU/메모리/GRES/상태
```

상태(STATE) 약어: `idle`(비어 있음), `alloc`/`mix`(전부 또는 일부 사용 중), `down`/`drain`(점검 중).

```bash
squeue            # 전체 큐
squeue --me       # 내 잡만
```

`squeue`의 ST(state) 열: `R`(Running, 실행 중), `PD`(Pending, 대기 중), `CG`(Completing, 마무리 중).
대기 중이면 NODELIST(REASON) 열에 **왜 대기하는지** 이유가 나옵니다(예: `Resources`, `Priority`). -> [문제 해결](../guide/troubleshooting.md)

!!! tip
    자원 현황을 컬러 표로 보여 주는 `sq` 명령도 있습니다(노드별 CPU, 메모리, GPU 사용량). -> [모니터링](../guide/monitoring.md)

## 실습 2: 인터랙티브로 GPU 잡기 (`srun`)

테스트, 디버깅에 좋은 방식입니다. GPU를 받아 **바로 셸**로 들어갑니다.

```bash
# GPU 1장으로 대화형 셸. GPU 타입은 반드시 명시하고,
# GPU를 점유하는 세션이므로 팀 QoS로 실행합니다.
srun --qos=<팀 QoS> --time=01:00:00 \
     --gres=gpu:<GPU 타입>:1 --pty bash -i
```

`<팀 QoS>`는 `qos`로, `<GPU 타입>`은 `sq` 또는 `sinfo -o "%G"`로 확인합니다.

셸이 뜨면 배정된 GPU가 보입니다.

```bash
nvidia-smi                     # 배정된 GPU 확인
echo $CUDA_VISIBLE_DEVICES     # 나에게 보이는 GPU 인덱스
python -c "import torch; print(torch.cuda.get_device_name(0))"
exit                           # 끝나면 반드시 나가서 자원 반납
```

- `--pty bash -i`: 대화형 셸을 받겠다는 뜻입니다.
- **파티션, CPU, 메모리는 적지 않습니다(규정).** Slurm이 GPU 수에 맞춰 CPU와 메모리를 자동 할당합니다. 직접 적으면 파티션과 CPU는 무시되고, 메모리는 제출이 거부됩니다. -> [자동 할당과 라우팅](../reference/slurm.md#자동-할당과-라우팅)

!!! warning "인터랙티브 셸은 GPU를 계속 점유합니다"
    빠져나오기 전까지 GPU를 계속 붙잡고 있으므로 규정상 "GPU 점유"에 해당합니다.
    **팀 QoS**로 실행하고, 다 쓰면 즉시 빠져나오세요. -> [규정: 디버깅](../policy/rules.md#디버깅)

## 실습 3: 배치 잡 제출하기 (`sbatch`)

실제 학습은 보통 **배치 스크립트**로 돌립니다. 제출하면 큐에 들어가고, 차례가 되면 알아서 실행되고, 출력은 파일로 저장됩니다. 셸을 켜 두지 않아도 됩니다.

`train.sbatch` 파일:

```bash
#!/bin/bash
#SBATCH --job-name=resnet            # 잡 이름
#SBATCH --gres=gpu:<GPU 타입>:1       # GPU 타입:개수 (필수 명시)
#SBATCH --time=04:00:00              # 최대 실행 시간. 안 적으면 QoS나 파티션의 상한이 적용됩니다
#SBATCH --output=logs/%x-%j.out      # 표준출력 로그 (%x=잡 이름, %j=JOBID)
#SBATCH --error=logs/%x-%j.err       # 표준에러 로그

echo "Host: $(hostname)  |  Job: $SLURM_JOB_ID"
nvidia-smi

# 필요하면 모듈 준비, uv 프로젝트 환경으로 실행
# module load <모듈 이름>
uv run python train.py --epochs 50
```

제출하고 확인합니다.

```bash
mkdir -p logs
sbatch train.sbatch              # -> Submitted batch job <JOBID>
squeue --me                      # 상태 보기 (PD -> R -> 사라지면 완료)
tail -f logs/resnet-<JOBID>.out  # 로그 실시간 보기
```

**`#SBATCH` 줄이 핵심입니다.** `#`로 시작하지만 주석이 아니라 Slurm 지시문입니다. 스크립트 맨 위, 실제 명령보다 먼저 와야 합니다. 자주 쓰는 지시문:

| 지시문 | 의미 |
|--------|------|
| `--job-name=NAME` | 잡 이름 (`squeue`에 표시) |
| `--gres=gpu:<GPU 타입>:N` | GPU 타입과 개수. **항상 명시** |
| `--output=` / `--error=` | 로그 파일. `%x`=잡 이름, `%j`=JOBID, `%N`=노드 이름 |
| `--time=D-HH:MM:SS` | 최대 실행 시간. 필요한 만큼만 (짧을수록 빨리 시작). 상한은 `qos`로 확인 |
| `--qos=NAME` | QoS. 생략하면 기본 QoS(선점될 수 있음). 내 것은 `qos`로 확인 |
| `--array=0-9` | 배열 잡(같은 스크립트를 여러 번). -> [잡 레시피](../guide/job-recipes.md) |

복사해서 바로 쓰는 다양한 템플릿은 [잡 레시피](../guide/job-recipes.md)에 있습니다.

## 잡 취소, 상태, 기록

```bash
scancel <JOBID>              # 특정 잡 취소
scancel --me                 # 내 모든 잡 취소
scancel --me --state=PD      # 내 대기 중 잡만 취소

scontrol show job <JOBID>    # 잡 상세 (요청 자원, 배정 노드, 상태 이유 등)

# 끝난 잡의 기록(과거 이력) 보기
sacct -j <JOBID> --format=JobID,JobName,State,Elapsed,AllocTRES%40
sacct --starttime=today      # 오늘 내 잡들
```

`sacct`는 **이미 끝난 잡**도 보여 줍니다(`squeue`는 진행 중인 것만). 실패 원인, 사용 자원, 소요 시간 확인에 유용합니다.

## `srun`과 `sbatch`: 언제 무엇을 쓰나

| | `srun` (대화형) | `sbatch` (배치) |
|---|----------------|-----------------|
| 언제 | 빠른 테스트, 디버깅, 셸 작업 | 실제 학습, 오래 걸리는 작업 |
| 동작 | 자원을 잡고 **즉시 실행, 터미널 점유** | 스크립트를 큐에 넣고 **백그라운드 실행** |
| 셸을 꺼도 되나 | 아니오 (끊기면 잡도 끝날 수 있음) | 예 (제출 후 로그아웃해도 계속) |
| 출력 | 화면에 바로 | 파일(`--output`)로 |

!!! tip
    학습은 `sbatch`로 제출하고, 그 잡이 도는 노드에 들어가 보고 싶으면
    `srun --jobid=<JOBID> --overlap --pty bash -i`로 셸을 받으세요. -> [계산 노드 접속](connect.md#계산-노드에는-직접-ssh로-접속할-수-없습니다)

## 특히 기억할 점

1. **GPU 타입을 항상 명시하세요:** `--gres=gpu:<GPU 타입>:N`.
2. **GPU 잡은 파티션, CPU, 메모리를 설정하지 마세요.** Slurm은 **GPU 타입만 보고** 그 타입의 노드가 있는 파티션으로 잡을 자동으로 보냅니다.
   CPU와 메모리도 GPU 수에 맞춰 충분히 자동 할당됩니다. 더 잡으면 그 노드의 남은 GPU를 다른 사람이 쓰지 못합니다. -> [자동 할당과 라우팅](../reference/slurm.md#자동-할당과-라우팅)
3. **CPU 전용 잡**은 `--cpus-per-task`를 필요한 만큼 지정하면 됩니다. 파티션은 적지 마세요.
4. **GPU를 점유하는 세션**(인터랙티브 셸, 노트북, 대기 중인 추론 서버 등)은 팀 QoS로 실행하고, 다 쓰면 즉시 반납하세요. -> [규정: 디버깅](../policy/rules.md#디버깅)
5. **무거운 연산은 로그인 노드에서 금지.** 항상 Slurm으로 제출하세요.

## 다음 단계

- 복사해서 쓰는 스크립트 모음 -> [잡 레시피](../guide/job-recipes.md)
- 옵션, QoS, 선점, 우선순위 전부 -> [Slurm 레퍼런스](../reference/slurm.md)
- 소프트웨어 환경 -> [소프트웨어 모듈](../guide/modules.md), [컨테이너](../guide/containers.md)
