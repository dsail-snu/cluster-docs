# 첫 GPU 잡 돌리기

5분 만에 첫 GPU 잡을 실행해 봅니다.

!!! note "시작 전에"
    SSH 키 등록과 로그인까지 끝난 상태여야 합니다. 아직이면 [접속하기](connect.md)를 먼저 보세요.
    AI 에이전트에게 제출을 맡긴다면 [AI 에이전트 규칙](../policy/index.md#ai-에이전트-규칙)을 먼저 숙지시키세요.

## 1. 자원 현황과 내 권한 보기

```bash
sq      # 큐, 사용자별 점유, 노드별 CPU/메모리/GPU 사용량 (내 잡은 ▌ 표시)
qos     # 내가 쓸 수 있는 QoS, 선점 관계, 우리 팀 몫이 얼마나 찼는지
```

아래 예시에 넣을 두 값을 여기서 확인합니다.

| 자리표시자 | 뜻 | 확인 방법 |
|-----------|-----|-----------|
| `<GPU 타입>` | 요청할 GPU 종류 | `sq` 또는 `sinfo -o "%G"` (예: `gpu:<GPU 타입>:<장수>` 형태로 보입니다) |
| `<팀 QoS>` | 본인 팀에 배정된 QoS | `qos` (`▌`로 표시된 것) |

## 2. 배치 잡으로 제출하기 (기본 방식)

`train.sbatch` 파일을 만듭니다.

```bash
#!/bin/bash
#SBATCH --job-name=my-first-job
#SBATCH --gres=gpu:<GPU 타입>:1     # GPU 타입을 반드시 명시
#SBATCH --time=01:00:00            # 넉넉하되 현실적으로. 짧을수록 빨리 시작됩니다
#SBATCH --output=%x-%j.out         # 로그 파일 (%x=잡 이름, %j=잡 ID)

nvidia-smi
python train.py
```

제출하고 확인합니다.

```bash
sbatch train.sbatch            # 제출 -> "Submitted batch job <JOBID>"
squeue --me                    # 내 잡 상태 보기
cat my-first-job-<JOBID>.out   # 로그 확인
scancel <JOBID>                # 취소
```

`--qos`를 적지 않았으므로 이 잡은 **기본 QoS**로 돕니다. 남는 자원으로 바로 시작할 수 있지만,
팀 QoS 잡에 **선점**되면 큐로 돌아가 처음부터 다시 돌 수 있습니다. 오래 걸리는 잡은 체크포인트를 남기세요. -> [선점](../reference/slurm.md#선점)

## 3. GPU를 붙잡고 대화형으로 만지기 (디버그 잡)

인터랙티브 셸은 빠져나올 때까지 GPU를 점유하므로 **규정상 디버그 잡**입니다.
**팀 QoS, 잡 이름 `debug`, 짧은 `--time`** 이 필수입니다. -> [규정: 디버깅](../policy/index.md#디버깅)

```bash
srun --qos=<팀 QoS> --job-name=debug --time=01:00:00 \
     --gres=gpu:<GPU 타입>:1 --pty bash -i

nvidia-smi
exit   # 끝나면 반드시 빠져나와 자원 반납
```

## 다음 단계

이게 전부입니다. 더 깊이 들어가려면 아래 순서로 읽으세요.

1. [Slurm 기초](slurm-basics.md): 개념, 용어, 자주 쓰는 명령
2. [잡 레시피](../guide/job-recipes.md): 복사해서 쓰는 배치 스크립트 모음
3. [컨테이너](../guide/containers.md): Docker 이미지를 Slurm 잡에서 실행
