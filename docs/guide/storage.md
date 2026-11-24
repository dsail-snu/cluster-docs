# 스토리지와 데이터

어디에 무엇을 두어야 하는지, 공유 스토리지를 느리게 만들지 않으려면 무엇을 조심해야 하는지 정리합니다.

## 세 가지 공유 공간

모든 노드에서 똑같이 보이는 공유 디렉터리가 셋 있습니다. `/home` 외의 실제 경로는
로그인 배너에 표시됩니다.

| 공간 | 용도 | 권장 사용 |
|------|------|-----------|
| `/home` | 개인 홈, 크고 오래 보관하는 공간 | 코드, 결과, **묶음 파일로 보관하는** 데이터셋. 큰 파일을 순서대로 읽는 데 강하고 작은 파일 무작위 접근에 약합니다 |
| `/sw` | 공용 소프트웨어 (모듈, CUDA 등) | 읽기 전용. 필요한 소프트웨어는 [요청](../help.md)해 주세요 |
| `/scratch` | 빠른 NVMe 작업 공간 (임시) | **지금 실험이 많이 읽고 쓰는 작업본** (작은 파일, 무작위 접근, 체크포인트) |

잡마다 노드 로컬 `/tmp`도 따로 있습니다. 잡이 끝나면 지워지므로, 풀어 놓은 실행 환경이나 압축을 푼 데이터셋처럼
한 잡 동안만 쓰는 파일을 둡니다.

여러 사람이 함께 쓰는 데이터셋, 모델, 컨테이너 이미지는 <!-- BEGIN GENERATED: paths:shared_data -->`/home/shared/datasets`, `/home/shared/models`, `/home/shared/containers`<!-- END GENERATED: paths:shared_data -->에 있습니다(읽기 전용).
<!-- BEGIN GENERATED: bot:data -->필요한 데이터를 받아 두는 신청은 `/cluster data`로 하실 수 있습니다.<!-- END GENERATED: bot:data -->

```bash
df -h /home /scratch          # 공간 전체의 용량과 마운트 확인
```

## 환경 변수

클러스터는 모든 로그인과 잡에 아래 환경 변수를 정해 둡니다. 직접 설정한 값이 있으면 그 값이 이깁니다.
잡 안에서 값이 다른 것은 작은 파일이 많은 캐시를 잡의 `/tmp`(노드 로컬, 잡이 끝나면 지워짐)에 두기 위해서입니다.

<!-- BEGIN GENERATED: env:table -->
| 변수 | 로그인 | 잡 안 |
|---|---|---|
| `HF_HOME` | `~/.cache/huggingface` | 같음 |
| `PIP_CACHE_DIR` | `~/.cache/pip` | `/tmp/pip-cache` |
| `SHARED_HF_HUB_CACHE` | `/home/shared/models/hub` | 같음 |
| `UV_CACHE_DIR` | `~/.cache/uv` | `/tmp/uv-cache` |
<!-- END GENERATED: env:table -->

`HF_HOME`은 로그인 토큰이 들어 있는 각자의 디렉터리입니다. 공유 위치로 옮기지 마세요.

## 공용 모델

<!-- BEGIN GENERATED: models -->
공용 모델 캐시는 `/home/shared/models/hub`에 있고, 모든 로그인과 잡에서 `SHARED_HF_HUB_CACHE`가 그곳을 가리킵니다. **읽기 전용**이라 여기에는 내려받을 수 없으니, 각자의 `HF_HUB_CACHE`로 바꾸지 말고 읽을 때 이 경로를 직접 주세요: `from_pretrained(<모델>, cache_dir=os.environ["SHARED_HF_HUB_CACHE"], local_files_only=True)`, 또는 `HF_HUB_OFFLINE=1 hf download <모델> --cache-dir "$SHARED_HF_HUB_CACHE"`가 출력하는 스냅샷 경로. 그 밖의 모델은 평소처럼 각자의 캐시(`HF_HOME` 아래)에 내려받고, 여럿이 쓸 모델은 관리자에게 요청하세요.
<!-- END GENERATED: models -->

## 어디에 무엇을 둘까

| 무엇 | 어디에 |
|------|--------|
| 코드, 스크립트, `~/.bashrc` (작은 파일, 자주 편집) | `/home` |
| 보관하는 데이터셋 (묶음 파일), 남길 결과와 최종 체크포인트 | `/home` |
| 진행 중인 실험의 작업본, 학습 중 체크포인트 | `/scratch` |
| 풀어 놓은 실행 환경, 압축을 푼 데이터셋, 임시 파일 | 잡의 `/tmp` |
| 공용 라이브러리, CUDA 모듈 | `/sw` (읽기만) |
| 컨테이너 작업본 캐시 | 노드 로컬 (잡이 끝나면 정리될 수 있음) |
| 보관할 컨테이너 이미지(`.sqsh`) | `/home` 또는 `/scratch` |

- `/home`에서 작은 파일 수백만 개를 직접 읽거나 거기에 큰 데이터를 풀면 홈 서버가 느려져 **모든 사용자가 영향**을
  받습니다. 묶음 파일로 두고, 풀 때는 잡의 `/tmp`나 `/scratch`에 푸세요.
- 컨테이너 캐시는 노드 로컬이라 잡이 끝나면 사라질 수 있습니다. 보관하려면 `.sqsh` 파일을
  공유 공간으로 옮기세요. -> [컨테이너](containers.md)

## 공유 스토리지를 느리게 만들지 않는 법

--8<-- "io-rules.md"

## 체크포인트 (선점 대비)

기본 QoS로 제출한 잡은 우선순위가 높은 잡에 **선점**되어 다시 큐로 돌아갈 수 있습니다.
다시 시작된 잡은 **처음부터** 돌기 때문에:

- **주기적으로 체크포인트를 저장**하고 (예: epoch마다 `/scratch/$USER/` 아래에),
- 시작할 때 **체크포인트가 있으면 이어서 학습**하도록 코드를 작성하세요.

선점이 결정되면 잡에 `SIGTERM`이 가고, 짧은 유예 시간 뒤 종료됩니다. 그 시간을 쓰려면 `SIGTERM`을 잡으세요.

```bash
trap 'touch /scratch/$USER/ckpt.request' TERM
```

`--signal=B:USR1@<초>`는 **시간 제한**에만 걸리고 선점에는 오지 않습니다. 둘 다 대비하려면
`trap '...' USR1 TERM` 처럼 두 신호를 모두 잡으세요. 막 시작한 잡도 선점될 수 있으니 첫 체크포인트를
너무 늦게 잡지 마세요. -> [선점](../reference/slurm.md#선점)

## 데이터 옮기기

!!! warning "AI 에이전트로 전송할 때"
    접속 재시도 횟수와 간격 등 [AI 에이전트 규칙](../policy/ai-agents.md)을 먼저 숙지시키세요.

내 PC와 클러스터 사이 (`<로그인 주소>`, `<SSH 포트>`는 계정 발급 때 관리자가 알려 줍니다):

```bash
# 업로드 (rsync 권장: 끊겨도 이어받고, 바뀐 것만 보냄)
rsync -avP -e "ssh -p <SSH 포트>" ./dataset/ <아이디>@<로그인 주소>:/scratch/<아이디>/dataset/

# 다운로드
rsync -avP -e "ssh -p <SSH 포트>" <아이디>@<로그인 주소>:/scratch/<아이디>/results/ ./results/

# scp 한 번 전송
scp -P <SSH 포트> file.tar.gz <아이디>@<로그인 주소>:/scratch/<아이디>/
```

- 대용량은 `rsync -avP`가 안전합니다 (이어받기, 검증, 진행률).
- 외부에서 데이터셋을 받을 때는 가능하면 **계산 노드의 인터랙티브 잡 안에서** 받아
  `/scratch`에 두세요. 로그인 노드와 홈 서버 부담이 줄어듭니다.

## 용량 한도와 정리

<!-- BEGIN GENERATED: quota:section -->
사람마다 정해진 용량과 파일 수 상한은 없습니다. 사용량은 매일 세어 Slack 디스크 리포트로 알려 드립니다.
<!-- END GENERATED: quota:section -->

- 내 사용량은 `du` 대신 제공되는 보기로 확인하세요: 매일 아침 Slack 디스크 리포트(상위 사용자, 정리하면 좋을 폴더),
  `/scratch`는 `scratch-space`.

### `/scratch`: 빠른 작업 공간

- 사람마다 `/scratch/<아이디>`가 있습니다. 높은 대역폭이 필요한 실험 데이터를 두는 **빠른 NVMe** 공간입니다.
  작업 중인 파일은 `/scratch`, 오래 둘 파일은 `/home`에 두세요. `/scratch` 바로 아래에는 새 폴더를 만들 수 없으니
  `/scratch/<아이디>` 안을 이용해 주세요.
- **<!-- BEGIN GENERATED: policy:stale_days -->60<!-- END GENERATED: policy:stale_days -->일 동안 읽거나 쓰지 않은 파일은 자동으로 정리됩니다.** 정리 대상이 되면 Slack DM으로 알려 주고,
  **<!-- BEGIN GENERATED: policy:grace_days -->14<!-- END GENERATED: policy:grace_days -->일 뒤** 그때까지도 쓰지 않은 파일을 지웁니다. 그 사이에 쓴 파일은 남습니다.
- 지워질 파일과 날짜는 `scratch-space` 명령으로 언제든 확인할 수 있습니다. 같은 목록이
  `/scratch/<아이디>/.purge-list`에도 매일 갱신됩니다.
- 정리를 피할 목적으로 접근 시각만 일괄 갱신하는 것(예: 전체 `touch`)은 금지합니다.
- **다 쓴 중간 산출물과 오래된 체크포인트는 정리**해 주세요. 모두의 공용 작업 공간입니다.

## 더 읽기

- 컨테이너 캐시 주의 -> [컨테이너](containers.md)
- 선점과 QoS -> [Slurm 레퍼런스](../reference/slurm.md#qos)
