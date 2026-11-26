# 컨테이너

Docker/NGC 이미지를 **Slurm 잡 안에서** 실행하는 방법입니다.

| 도구 | 역할 |
|---|---|
| Enroot | root 권한 없이 동작하는 컨테이너 런타임 |
| Pyxis | Enroot를 `srun`/`sbatch`에 붙여 주는 Slurm 플러그인 |
| Podman | root 권한 없이 이미지를 만들고 실행하는 도구 (잡 안에서 이미지를 빌드할 때) |

Slurm 잡에서 컨테이너를 돌릴 때는 **Enroot와 Pyxis**를, 이미지를 직접 만들 때는 **Podman**을 이용해 주세요.

!!! question "왜 Docker가 아닌가요?"
    여러 사람이 함께 쓰는 클러스터에서는 root 권한 없이 안전하게 컨테이너를 돌려야 합니다.
    Enroot는 root 권한 없이 사용자 네임스페이스(user namespace)로 동작하고, Pyxis는 Enroot를 Slurm 잡에
    연결해 줍니다.

설치된 버전이 궁금하면 계산 노드에서 확인하세요.

```bash
enroot version
srun --help | grep container      # Pyxis 옵션이 보이면 사용 가능
```

---

## 가장 쉬운 방법: `--container-image`

`srun`/`sbatch`에 `--container-image`를 붙이면 Slurm이 이미지를 받아 컨테이너 안에서
명령을 실행합니다.

### 인터랙티브

```bash
# GPU를 점유하는 세션이므로 팀 QoS로 실행합니다
srun --qos=<팀 QoS> --time=04:00:00 \
     --gres=gpu:<GPU 타입>:1 \
     --container-image=nvcr.io#nvidia/pytorch:<태그> \
     --container-mounts=$HOME:$HOME,/scratch:/scratch \
     --container-workdir=$HOME \
     --pty bash
```

- `<태그>`는 [NGC 카탈로그](https://catalog.ngc.nvidia.com/)에서 확인하세요.
- 셸 안에서 `nvidia-smi`, `python -c "import torch; print(torch.__version__)"` 로 확인합니다.
- GPU를 점유하는 세션의 규칙은 [디버깅 규정](../policy/rules.md#디버깅)을 보세요.

### 배치

```bash
#!/bin/bash
#SBATCH --job-name=ctr-train
#SBATCH --gres=gpu:<GPU 타입>:2
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out

srun --container-image=nvcr.io#nvidia/pytorch:<태그> \
     --container-mounts=$HOME:$HOME,/scratch:/scratch \
     --container-workdir=$PWD \
     python train.py
```

### 이미지 주소 형식

Enroot 표기는 `<레지스트리>#<이미지>:<태그>` 입니다. 레지스트리와 이미지 사이가 `/`가 아니라
`#`인 점에 주의하세요.

| 출처 | 예시 |
|---|---|
| NGC | `nvcr.io#nvidia/pytorch:<태그>` |
| Docker Hub | `pytorch/pytorch:<태그>` 또는 `docker.io#pytorch/pytorch:<태그>` |
| 저장해 둔 파일 | `$HOME/images/pytorch.sqsh` (절대 경로. `--container-image=~/...`의 `~`는 셸이 홈 경로로 바꾸지 않습니다) |

### 자주 쓰는 Pyxis 옵션

| 옵션 | 설명 |
|---|---|
| `--container-image=` | 이미지 주소 또는 `.sqsh` 파일 경로 |
| `--container-mounts=SRC:DST[,SRC2:DST2]` | 호스트 경로를 컨테이너에 마운트. `:ro`를 붙이면 읽기 전용 |
| `--container-workdir=` | 컨테이너 안 작업 디렉터리 |
| `--container-name=NAME` | 컨테이너에 이름을 붙여 같은 잡의 다음 step에서 **재사용** |
| `--container-save=PATH.sqsh` | 컨테이너 상태를 squashfs 파일로 저장 |
| `--container-mount-home` / `--no-container-mount-home` | 홈 자동 마운트 켜기, 끄기 |
| `--container-entrypoint` / `--no-container-entrypoint` | 이미지의 ENTRYPOINT 실행 여부 |
| `--container-writable` / `--container-readonly` | 컨테이너 파일시스템 쓰기 가능 여부 |

!!! note "기본 동작은 클러스터마다 다릅니다"
    홈 자동 마운트, ENTRYPOINT 실행 여부 같은 기본값은 클러스터 설정에 따라 다릅니다.
    원하는 동작이 있으면 위 옵션으로 명시하는 편이 안전합니다.

---

## 마운트

컨테이너 안에서는 마운트한 경로만 보입니다. 데이터나 코드가 있는 경로를 꼭 마운트하세요.

```bash
--container-mounts=$HOME:$HOME                                  # 홈
--container-mounts=/scratch:/scratch                            # 스크래치
--container-mounts=$HOME/data:/data:ro                          # 읽기 전용, 다른 경로로
--container-mounts=$HOME:$HOME,$HOME/data:/data:ro              # 여러 개는 쉼표로
```

어떤 데이터를 어디에 두면 좋은지는 [스토리지](storage.md)를 보세요.

---

## 이미지 저장해 두고 재사용하기

잡마다 이미지를 새로 받으면 시작이 느립니다. 한 번 `.sqsh` 파일로 만들어 공유 스토리지에
두고 재사용하세요.

### 방법 1: Enroot CLI로 import

**계산 노드에서**(인터랙티브 잡 안에서) 수행합니다. 이미지를 받는 데는 GPU가 필요 없으니 CPU 전용 잡으로 받으세요.

```bash
# 1) CPU 전용 인터랙티브 셸 확보 (GPU를 잡지 않습니다)
srun --cpus-per-task=4 --time=01:00:00 --pty bash -i

# 2) 이미지 import -> .sqsh 파일 생성
mkdir -p ~/images && cd ~/images
enroot import -o pytorch.sqsh docker://nvcr.io#nvidia/pytorch:<태그>

# 3) (선택) Enroot로 직접 실행
enroot create --name myctr pytorch.sqsh
enroot start --rw --mount $HOME:$HOME myctr python train.py
```

이후에는 Pyxis에서 그 파일을 바로 씁니다.

```bash
srun --gres=gpu:<GPU 타입>:1 --container-image=$HOME/images/pytorch.sqsh python train.py
```

### 방법 2: 패키지를 설치한 뒤 `--container-save`

베이스 이미지에 패키지를 더 설치한 상태를 저장할 때 씁니다. 패키지 설치에는 GPU가 필요 없으니 CPU 전용 잡으로 합니다.

```bash
srun --cpus-per-task=4 --time=01:00:00 \
     --container-image=nvcr.io#nvidia/pytorch:<태그> \
     --container-save=$HOME/images/my-pytorch.sqsh \
     --pty bash
# 셸 안에서 pip install 등을 마치고 exit 하면 파일로 저장됩니다
```

### 노드 로컬 캐시

Enroot는 런타임, 캐시, 데이터(이미지를 풀어 놓는 곳) 경로를 공유 스토리지(NFS)가 아니라 **각 노드의 로컬 디스크**에
사람마다 따로 둡니다. 이미지를 풀 때는 작은 파일을 많이 읽고 쓰므로, 공유 스토리지에 두면 모두가 느려지기 때문입니다.

- 노드 로컬 데이터는 노드마다 따로 있고 잡이 끝나면 지워질 수 있습니다. 보관용으로 쓰지 마세요.
- 보관하고 싶은 이미지는 **`.sqsh` 파일로 만들어 `/home`이나 `/scratch`에** 두세요.
- 같은 이미지를 여러 잡에서 쓴다면 `--container-image=<.sqsh 경로>` 가 가장 효율적입니다.

---

## 비공개 레지스트리 (인증)

NGC의 일부 이미지나 비공개 레지스트리는 로그인이 필요합니다. Enroot는
`~/.config/enroot/.credentials` 파일(netrc 형식)에서 인증 정보를 읽습니다.

```bash
mkdir -p ~/.config/enroot
touch ~/.config/enroot/.credentials
chmod 600 ~/.config/enroot/.credentials     # 본인만 읽을 수 있게
```

파일 내용 예시 (자리표시자를 본인 값으로 바꾸세요):

```text
# NGC: login 은 글자 그대로 $oauthtoken 입니다
machine nvcr.io login $oauthtoken password <NGC API 키>

# Docker Hub: 비밀번호 대신 액세스 토큰을 권장합니다
machine auth.docker.io login <Docker Hub 사용자명> password <Docker Hub 액세스 토큰>

# 그 밖의 레지스트리
machine <레지스트리 주소> login <사용자명> password <토큰>
```

!!! danger "인증 정보 관리"
    - 파일 권한은 반드시 `600`으로 둡니다.
    - API 키와 토큰을 스크립트, 노트북, Git 저장소, Slack에 붙여 넣지 마세요.
    - 키가 노출되었다면 즉시 해당 레지스트리에서 폐기하고 새로 발급하세요.

`/home`은 모든 노드가 공유하므로, 이 파일을 로그인 노드에서 한 번만 만들면 계산 노드의
잡에서도 그대로 쓰입니다.

---

## 자주 막히는 부분

| 증상 | 원인과 해결 |
|---|---|
| 컨테이너 안에서 GPU가 안 보임 | `--gres=gpu:<GPU 타입>:N`으로 GPU를 요청했는지 확인. 할당된 GPU만 보입니다 |
| 홈이 안 보임 | `--container-mounts=$HOME:$HOME` 또는 `--container-mount-home` 추가 |
| 스크래치 데이터가 안 보임 | `--container-mounts=/scratch:/scratch` 추가 |
| 이미지 받기가 느림 | 한 번 `.sqsh`로 저장한 뒤 재사용 |
| 내 명령 대신 다른 것이 실행됨 | 이미지 ENTRYPOINT 때문일 수 있습니다. `--no-container-entrypoint` 추가 |
| 인증 오류(401, unauthorized) | `~/.credentials` 가 아니라 `~/.config/enroot/.credentials` 인지, `machine` 주소와 권한(`600`)이 맞는지 확인 |
| 권한 오류(`Permission denied`)가 계속됨 | [문제 해결](troubleshooting.md)을 보고, 그래도 안 되면 [관리자 문의](../help.md) |

---

## 더 읽기

- Enroot 공식 문서: <https://github.com/NVIDIA/enroot>
- Pyxis 공식 문서: <https://github.com/NVIDIA/pyxis>
- 잡 레시피의 컨테이너 예제 -> [잡 레시피](job-recipes.md#컨테이너-잡)
