# 소프트웨어 모듈 (Lmod)

여러 버전의 소프트웨어(특히 CUDA)를 **명령 한 줄로 바꿔 쓰는** 방법입니다. 클러스터는
**Lmod**(환경 모듈)를 쓰며, 공용 소프트웨어는 `<공용 소프트웨어 경로>`에 설치되어 모든
노드에서 똑같이 보입니다.

---

## 환경 모듈이란

`module load`로 특정 소프트웨어와 버전을 **현재 셸 환경에 추가**하고, `module unload`로
뺍니다. 시스템 전체를 건드리지 않고 내 세션의 `PATH`, 라이브러리 경로만 바꿉니다.

```bash
module avail                 # 사용 가능한 모듈 전체
module avail cuda            # cuda 관련만
module load cuda             # 기본 버전 로드 ((D) 표시)
module load cuda/<버전>      # 특정 버전 로드
module list                  # 현재 로드된 모듈
module unload cuda           # 빼기
module purge                 # 전부 초기화
module spider cuda           # 검색 (다른 모듈에 딸린 것까지)
module show cuda/<버전>      # 이 모듈이 어떤 환경변수를 바꾸는지
```

| 명령 | 언제 쓰나 |
|---|---|
| `module avail` | 무엇이 설치되어 있는지 볼 때 |
| `module load` / `unload` | 쓰거나 뺄 때 |
| `module list` | 지금 무엇이 로드되어 있는지 볼 때 |
| `module purge` | 환경이 꼬였을 때 처음부터 다시 |
| `module spider` | `avail`에 안 보이는 모듈을 찾을 때 |

!!! note
    모듈은 **셸 세션 단위**입니다. 배치 잡에서 쓰려면 **스크립트 안에서** `module load`를
    호출하세요. ([배치 잡에서 환경 활성화](#배치-잡에서-환경-활성화))

---

## CUDA 버전 고르기

CUDA는 두 부분으로 나뉩니다.

| 구성 | 어디서 오나 | 확인 |
|---|---|---|
| NVIDIA 드라이버 | 시스템에 설치됨 | `nvidia-smi` (계산 노드의 잡 안에서) |
| CUDA 툴킷 (`nvcc` 등) | Lmod 모듈 또는 컨테이너 | `module avail cuda` |

```bash
module avail cuda            # 설치된 CUDA 모듈 목록
module load cuda/<버전>      # 목록에서 골라 로드
nvcc --version               # 로드된 버전 확인
```

- 모듈 이름은 **주.부 버전**입니다: `cuda/12.4`, `cuda/13.0`. 한 부 버전에는 그 최신 패치 하나만 설치됩니다.
- 패치까지 적은 이름(`cuda/12.4.0`, `cuda/12.4.1`)도 같은 `cuda/12.4`를 로드합니다. 새 패치로 바뀌어도
  패치를 적어 둔 잡 스크립트가 그대로 동작합니다. 실제 패치는 `nvcc --version`으로 확인하세요.
- 버전을 적지 않으면 기본 버전(`(D)` 표시, 설치된 가장 최신 부 버전)이 로드됩니다. 기본 버전은 새 CUDA가
  설치되면 바뀌니, 재현이 중요한 잡은 버전을 적으세요.
- 설치된 버전 목록은 클러스터마다, 시기마다 다릅니다. 항상 `module avail cuda`로 확인하세요.
- 드라이버가 툴킷보다 같거나 더 최신이면 여러 CUDA 버전을 골라 쓸 수 있습니다.
- 원하는 버전이 없으면 관리자에게 요청하거나, CUDA가 들어 있는 [컨테이너](containers.md)를 쓰세요.

!!! tip "로그인 노드에서 `nvidia-smi`가 안 될 때"
    로그인 노드나 SSH 세션에서는 GPU가 보이지 않을 수 있습니다. GPU는 잡 안에서 확인하세요.
    ([첫 잡 제출](../start/first-job.md))

---

## Python 환경 (uv)

Python 환경은 **[uv](https://docs.astral.sh/uv/)를 권장합니다.** 프로젝트마다 환경이 디렉터리 안에 생기고,
`uv.lock`으로 누가 어디서 실행해도 같은 패키지 버전을 씁니다. 설치가 빠르고, 내려받은 패키지는
한 곳에 캐시해 다시 받지 않습니다. 대부분의 딥러닝 작업은 **uv 환경 + CUDA가 포함된 pip 휠**이나
**[컨테이너](containers.md)**로 충분합니다.

```bash
# uv 설치 (최초 1회, 홈의 ~/.local/bin 에 설치됩니다. 설치 방법은 uv 공식 문서 참고)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 새 프로젝트
uv init myproject && cd myproject
uv python install 3.12        # 필요한 Python 버전도 uv가 받아 둡니다
uv add torch                  # CUDA 버전에 맞는 정확한 지정은 pytorch.org 와 uv 문서의 PyTorch 안내 참고
uv run python train.py        # 프로젝트 환경으로 실행 (활성화가 필요 없습니다)
```

### 팁

| 상황 | 방법 |
|---|---|
| PyTorch, TensorFlow만 쓴다 | pip 휠에 CUDA 런타임이 들어 있어 보통 `module load cuda`가 필요 없습니다 (드라이버만 맞으면 됨) |
| 직접 CUDA 코드를 컴파일한다 (custom 커널 등) | `module load cuda/<버전>`으로 `nvcc`를 맞춥니다 |
| 홈 용량이 부족하다 | `uv cache prune` 으로 쓰지 않는 캐시를 정리. 용량 확인은 [스토리지](storage.md) |
| 환경을 다른 곳에서 재현하고 싶다 | `pyproject.toml`과 `uv.lock`을 함께 두면 `uv sync`로 똑같이 만듭니다 |
| 이미 conda 환경이 있다 | 그대로 써도 됩니다. 새 프로젝트부터 uv로 옮기는 것을 권장합니다 |

---

## 배치 잡에서 환경 활성화

```bash
#!/bin/bash
#SBATCH --job-name=train
#SBATCH --gres=gpu:<GPU 타입>:1
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail

# (선택) CUDA 모듈
# module load cuda/<버전>

# 프로젝트 디렉터리에서 uv 환경으로 실행
cd ~/myproject
uv run python train.py
```

!!! warning
    로그인 노드에서 `module load`나 환경 활성화를 해 둔 상태에 기대지 마세요.
    **항상 스크립트 안에서** 환경을 준비해야 어디서 실행해도 같은 결과가 나옵니다.

더 많은 예제는 [잡 레시피](job-recipes.md#실행-환경-준비)를 보세요.

---

## 공용 소프트웨어 경로

`<공용 소프트웨어 경로>`는 로그인 배너에 표시됩니다. 보통 이런 것들이 들어 있습니다.

| 내용 | 쓰는 법 |
|---|---|
| Lmod 모듈 파일 | `module avail`이 자동으로 찾음 |
| 관리자가 설치한 공용 소프트웨어 | `module load <이름>` |
| CUDA 툴킷 | `module load cuda/<버전>` |

- 공유 스토리지에 있고 사용자는 읽기만 합니다. 모든 노드에서 똑같이 보입니다.
- 여러 사람이 쓸 소프트웨어가 필요하면 [관리자에게 요청](../help.md)하세요. 설치되면 모두가
  `module load`로 씁니다.
- 나만 쓸 소프트웨어는 홈에 설치하고, 원하면 개인 모듈 파일을 만들어 `module use ~/modulefiles`로
  추가할 수 있습니다.

---

## 더 읽기

- Lmod 사용자 가이드: <https://lmod.readthedocs.io/>
- 환경을 통째로 가져오기 -> [컨테이너](containers.md)
- 잡에서 환경 준비 예제 -> [잡 레시피](job-recipes.md#실행-환경-준비)
