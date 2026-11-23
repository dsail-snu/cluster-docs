# 잡 레시피

복사해서 바로 쓰는 `sbatch`/`srun` 스크립트 모음입니다. `<GPU 타입>`, `<팀 QoS>` 같은
자리표시자만 본인 값으로 바꾸면 됩니다.

!!! warning "공통 원칙"
    - 잡 제출은 **본인이 직접** 합니다. ([잡 제출 규칙](../policy/index.md#잡-제출-규칙))
    - GPU 잡은 **GPU 타입과 개수만** 적습니다. 파티션, CPU, 메모리는 적지 않습니다.
      GPU 수에 맞춰 자동으로 할당됩니다. ([자동 할당과 라우팅](../reference/slurm.md#자동-할당과-라우팅))
    - CPU 전용 잡은 필요한 CPU 수를 직접 적습니다.

| 확인할 값 | 명령 |
|---|---|
| 쓸 수 있는 `<GPU 타입>` | `sq` 또는 `sinfo -o "%G"` |
| 내가 쓸 수 있는 `<팀 QoS>`와 한도 | `qos` |

목차: [단일 GPU](#단일-gpu-배치), [단일 노드 멀티 GPU](#단일-노드-멀티-gpu-ddp),
[CPU 전용](#cpu-전용-잡), [디버그 인터랙티브](#디버그-인터랙티브), [Jupyter](#원격-jupyter-노트북),
[배열 잡](#배열-잡), [의존성](#잡-의존성), [체크포인트와 재시작](#체크포인트와-재시작),
[컨테이너](#컨테이너-잡), [서버형 잡](#서버형-잡-vllm-등), [환경 준비](#실행-환경-준비)

---

## 단일 GPU 배치

가장 흔한 형태입니다.

```bash
#!/bin/bash
#SBATCH --job-name=train
#SBATCH --gres=gpu:<GPU 타입>:1
#SBATCH --time=04:00:00             # 필요한 만큼만. 짧을수록 backfill로 빨리 시작됩니다
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
# 파티션, CPU, 메모리는 생략 -> GPU 수에 맞춰 자동 할당

set -euo pipefail
echo "Node: $(hostname) | Job: $SLURM_JOB_ID | GPUs: $CUDA_VISIBLE_DEVICES"
nvidia-smi

python train.py --epochs 50
```

```bash
mkdir -p logs && sbatch train.sbatch
```

!!! tip "`--time`은 적는 편이 유리합니다"
    생략하면 QoS의 최대 실행 시간이 적용됩니다. 필요한 만큼 적으면 backfill 덕분에
    더 빨리 시작될 수 있습니다. 최대 실행 시간은 `qos`로 확인하세요.

---

## 단일 노드 멀티 GPU (DDP)

같은 노드의 GPU 여러 장을 `torchrun`으로 씁니다.

```bash
#!/bin/bash
#SBATCH --job-name=ddp
#SBATCH --gres=gpu:<GPU 타입>:4     # 한 노드의 GPU 4장
#SBATCH --nodes=1                   # 단일 노드 고정
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
nvidia-smi

torchrun --standalone --nproc_per_node=4 train_ddp.py
# 또는: python -m torch.distributed.run --standalone --nproc_per_node=4 train_ddp.py
```

- CPU와 메모리는 GPU 수에 비례해 자동으로 따라옵니다.
- 한 노드에 요청할 수 있는 GPU 수는 그 노드에 달린 GPU 수까지입니다. `sinfo -o "%N %G"`로 확인하세요.
- 노드 간 고속 인터커넥트가 없는 클러스터에서는 **단일 노드 안에서** 여러 GPU를 쓰는 것이
  표준입니다. 여러 노드에 걸친 학습이 필요하면 먼저 [관리자에게 문의](../help.md)하세요.

---

## CPU 전용 잡

GPU가 필요 없는 전처리, 분석 등입니다. **GPU 옵션을 빼면** CPU 잡으로 라우팅되어,
GPU 잡 몫으로 예약되지 않은 여유 코어에서 돕니다.

```bash
#!/bin/bash
#SBATCH --job-name=preprocess
#SBATCH --cpus-per-task=8           # 필요한 만큼
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out
# GPU 미요청 -> CPU 잡으로 자동 라우팅

set -euo pipefail
echo "Allocated CPUs: $SLURM_CPUS_PER_TASK on $(hostname)"
python preprocess.py --workers "$SLURM_CPUS_PER_TASK"
```

---

## 디버그 인터랙티브

GPU를 점유하는 인터랙티브 셸은 `<팀 QoS>`로 실행하고, 다 쓰면 즉시 빠져나오세요.
([GPU 점유 규정](../policy/index.md#디버깅))

```bash
srun --qos=<팀 QoS> --time=04:00:00 \
     --gres=gpu:<GPU 타입>:1 --pty bash -i
```

셸 안에서:

```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
exit          # 끝나면 반드시 빠져나와 GPU를 반납합니다
```

### 이미 돌고 있는 내 잡의 노드에 들어가기

```bash
squeue --me
srun --jobid=<JOBID> --overlap --pty bash -i   # 그 잡의 노드에서 셸
htop; nvidia-smi; nvtop                         # 상태 확인
```

자원을 새로 잡지 않고 기존 잡 안으로 들어가므로 GPU 점유 규칙과 무관합니다.
자세한 모니터링은 [모니터링](monitoring.md)을 보세요.

---

## 원격 Jupyter 노트북

Jupyter도 **GPU를 점유하는 세션**입니다. `<팀 QoS>`로 실행하고, 다 쓰면
즉시 종료하세요. 계산 노드에서 노트북을 띄우고 SSH 터널로 접속합니다.

```bash
#!/bin/bash
#SBATCH --job-name=jupyter
#SBATCH --qos=<팀 QoS>              # 규정: 팀 QoS
#SBATCH --time=04:00:00             # 필요한 만큼만
#SBATCH --gres=gpu:<GPU 타입>:1
#SBATCH --output=logs/jupyter-%j.out

set -euo pipefail
PORT=8888
echo "==> 내 PC에서 아래 터널을 직접 여세요:"
echo "    ssh -N -L ${PORT}:$(hostname):${PORT} -p <SSH 포트> <아이디>@<로그인 주소>"
jupyter lab --no-browser --ip=0.0.0.0 --port=${PORT}
```

제출 후 로그(`logs/jupyter-<JOBID>.out`)에 찍힌 토큰 URL과 터널 명령을 확인하고,
**본인 PC에서 직접** 터널을 연 뒤 브라우저로 `http://localhost:8888` 에 접속하세요.
`<로그인 주소>`와 `<SSH 포트>`는 [접속하기](../start/connect.md)를 참고하세요.

!!! note
    같은 노드에서 다른 사람이 같은 포트를 쓰고 있으면 Jupyter가 다른 포트로 뜹니다.
    로그에 찍힌 실제 포트로 터널을 여세요.

---

## 배열 잡

같은 스크립트를 인자만 바꿔 여러 번 돌릴 때(하이퍼파라미터 스윕 등) 씁니다.
각 태스크가 독립 잡으로 스케줄됩니다.

```bash
#!/bin/bash
#SBATCH --job-name=sweep
#SBATCH --gres=gpu:<GPU 타입>:1
#SBATCH --array=0-7%4               # 0~7번 태스크, 동시에 최대 4개만
#SBATCH --time=02:00:00             # 태스크 하나당 상한
#SBATCH --output=logs/%x-%A_%a.out  # %A=배열 잡 ID, %a=태스크 인덱스

set -euo pipefail
LRS=(0.001 0.003 0.01 0.03 0.1 0.3 1.0 3.0)
LR=${LRS[$SLURM_ARRAY_TASK_ID]}
echo "Task $SLURM_ARRAY_TASK_ID -> lr=$LR"
python train.py --lr "$LR"
```

!!! tip
    `%4`처럼 **동시 실행 수를 제한**하면 다른 사람 몫을 배려할 수 있습니다(권장).

---

## 잡 의존성

앞 잡이 끝난 뒤에 다음 잡을 시작하게 묶습니다. 전처리 -> 학습 -> 평가 같은 파이프라인에 씁니다.

```bash
PRE=$(sbatch --parsable preprocess.sbatch)
TRAIN=$(sbatch --parsable --dependency=afterok:$PRE train.sbatch)
sbatch --dependency=afterok:$TRAIN eval.sbatch
```

| 조건 | 의미 |
|---|---|
| `afterok:<JOBID>` | 앞 잡이 성공(종료 코드 0)하면 시작 |
| `afternotok:<JOBID>` | 앞 잡이 실패하면 시작 |
| `afterany:<JOBID>` | 성공, 실패와 상관없이 끝나면 시작 |
| `after:<JOBID>` | 앞 잡이 시작되면 시작 |
| `singleton` | 같은 이름의 내 잡이 한 번에 하나씩만 실행 |

- 여러 잡을 기다리려면 `afterok:<JOBID1>:<JOBID2>` 처럼 콜론으로 잇습니다.
- 앞 잡이 실패해 조건을 영영 만족할 수 없으면 뒤 잡은 `DependencyNeverSatisfied`로 대기에
  남습니다. `scancel`로 지우세요.

---

## 체크포인트와 재시작

기본 QoS 잡은 [선점](../reference/slurm.md#선점)될 수 있고, 긴 학습은 실행 시간 한도에
걸릴 수 있습니다. 두 경우 잡이 받는 신호가 다릅니다.

| 상황 | 받는 신호 | 다시 큐로 |
|---|---|---|
| 선점 | `SIGTERM`, 짧은 유예 뒤 종료 | `--requeue`면 Slurm이 자동으로 |
| 시간 만료 직전 | `--signal`로 지정한 신호 (아래는 `USR1`) | 스크립트가 직접 `scontrol requeue` |

 주기적으로 체크포인트를 저장하고, 시작할 때 마지막 체크포인트에서
이어가도록 만들어 두면 다시 큐에 들어가도 손해가 적습니다.

```bash
#!/bin/bash
#SBATCH --job-name=long-train
#SBATCH --gres=gpu:<GPU 타입>:1
#SBATCH --time=12:00:00
#SBATCH --requeue                   # 선점되거나 노드 장애 시 다시 큐로
#SBATCH --open-mode=append          # 재시작해도 로그를 이어 씀
#SBATCH --signal=B:USR1@120         # 종료 120초 전에 배치 셸로 USR1 전송
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
CKPT_DIR=<스크래치 경로>/$USER/checkpoints/$SLURM_JOB_NAME
mkdir -p "$CKPT_DIR"

# 시간 만료 직전: 학습 프로세스에 저장 신호를 보내고 스스로 다시 큐에 넣음
on_usr1() {
    echo "USR1 received, saving and requeueing"
    kill -USR1 "$PID" 2>/dev/null || true
    wait "$PID" || true
    scontrol requeue "$SLURM_JOB_ID"
}
# 선점: 학습 프로세스도 SIGTERM을 받으므로 저장이 끝나길 기다림 (재큐는 Slurm이 함)
on_term() {
    echo "TERM received (preempted), waiting for checkpoint"
    wait "$PID" || true
}
trap on_usr1 USR1
trap on_term TERM

echo "Restart count: ${SLURM_RESTART_COUNT:-0}"
python train.py --ckpt-dir "$CKPT_DIR" --resume auto &
PID=$!
wait "$PID"
```

학습 코드 쪽에서 할 일:

- 일정 스텝마다 `$CKPT_DIR`에 저장합니다. 임시 파일에 쓴 뒤 이름을 바꾸면 저장 도중
  끊겨도 마지막 체크포인트가 깨지지 않습니다.
- 시작할 때 `$CKPT_DIR`에 체크포인트가 있으면 불러와서 이어갑니다.
- `SIGUSR1`이나 `SIGTERM`을 받으면 즉시 체크포인트를 저장하고 종료합니다. 선점 유예 시간은
  짧으니 저장이 빨리 끝나야 합니다.
- 막 시작한 잡도 선점될 수 있으니 첫 체크포인트를 너무 늦게 잡지 마세요.

!!! note
    `trap`이 동작하려면 학습 프로세스를 `&`로 띄우고 `wait`해야 합니다. 그래야 배치 셸이
    신호를 받아 처리할 수 있습니다. `--signal`은 시간 만료에만 오고 선점에는 오지 않습니다.
    체크포인트 저장 위치는 [스토리지](storage.md#체크포인트-선점-대비)를 참고하세요.

---

## 컨테이너 잡

Docker/NGC 이미지를 Slurm 잡에서 바로 실행합니다. 자세한 내용은 [컨테이너](containers.md)를 보세요.

```bash
# 인터랙티브 컨테이너 셸 (GPU를 점유하므로 팀 QoS로)
srun --qos=<팀 QoS> --time=04:00:00 \
     --gres=gpu:<GPU 타입>:1 \
     --container-image=nvcr.io#nvidia/pytorch:<태그> \
     --container-mounts=$HOME:$HOME --container-workdir=$HOME \
     --pty bash
```

```bash
#!/bin/bash
#SBATCH --job-name=ctr-train
#SBATCH --gres=gpu:<GPU 타입>:2
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out

srun --container-image=nvcr.io#nvidia/pytorch:<태그> \
     --container-mounts=$HOME:$HOME,<스크래치 경로>:<스크래치 경로> \
     --container-workdir=$PWD \
     python train.py
```

---

## 서버형 잡 (vLLM 등)

!!! warning "요청을 기다리는 서버도 GPU 점유입니다"
    대기 중인 vLLM 서버는 요청이 없어도 GPU를 잡고 있습니다. 규정상 **GPU 점유 규칙**
    (`<팀 QoS>`)을 적용하고, 다 쓰면 즉시 종료하세요.

```bash
#!/bin/bash
#SBATCH --job-name=vllm
#SBATCH --qos=<팀 QoS>
#SBATCH --time=04:00:00             # 필요한 만큼만
#SBATCH --gres=gpu:<GPU 타입>:1     # 큰 모델이면 VRAM이 큰 GPU 타입으로
#SBATCH --output=logs/vllm-%j.out

set -euo pipefail
PORT=8000
echo "Serving on $(hostname):${PORT}. 내 PC에서 SSH 터널로 접속하세요."
vllm serve <모델> --port ${PORT}
```

요청을 처리한 뒤 **스스로 자원을 반납**하는 자동화 파이프라인으로 설계했다면 일반 잡으로
제출해도 됩니다.

---

## 실행 환경 준비

배치 스크립트 안에서 환경을 활성화하는 패턴입니다. 로그인 노드에서 활성화한 환경은
잡으로 전달되지 않으니 **항상 스크립트 안에서** 준비하세요.

```bash
# (A) uv 프로젝트 (권장): 활성화 없이 프로젝트 환경으로 실행
cd ~/myproject
uv run python train.py

# (B) CUDA 모듈 (module avail cuda 로 사용 가능 버전 확인)
module load cuda/<버전>
```

자세한 내용은 [소프트웨어 모듈](modules.md)을 보세요.

---

## 자주 쓰는 `#SBATCH` 옵션

| 옵션 | 의미 | 권장 |
|---|---|---|
| `--gres=gpu:<GPU 타입>:N` | GPU 타입, 개수 | GPU 잡은 **항상 명시** |
| `--job-name=` | 잡 이름 | 알아보기 쉬운 이름 |
| `--qos=` | QoS | GPU 점유 세션, 우선 실행이 필요할 때 `<팀 QoS>` |
| `--time=D-HH:MM:SS` | 최대 실행 시간 | 필요한 만큼만. 상한은 `qos`로 확인 |
| `--cpus-per-task=` | 태스크당 CPU | CPU 전용 잡만. GPU 잡은 **생략** |
| `--nodes=1` | 노드 수 | 멀티 GPU는 단일 노드 권장 |
| `--output=` / `--error=` | 로그 파일 | `logs/%x-%j.out` 패턴 |
| `--array=A-B%C` | 배열 잡(동시 C개) | 스윕에 유용 |
| `--dependency=` | 잡 의존성 | 파이프라인에 유용 |
| `--requeue`, `--signal=` | 재시작, 종료 전 신호 | 긴 잡, 선점 대비 |
| `--mem=`, `--partition=` | 메모리, 파티션 | GPU 잡은 **생략**. 메모리는 거부, 파티션은 무시 ([처리 규칙](../reference/slurm.md#자동-할당과-라우팅)) |

전체 옵션과 환경변수는 [Slurm 레퍼런스](../reference/slurm.md#자주-쓰는-옵션)를 보세요.
잡이 시작되지 않거나 실패하면 [문제 해결](troubleshooting.md)을 확인하세요.
