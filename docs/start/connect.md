# 접속하기

클러스터 계정을 처음 받았을 때 해야 할 것들입니다. 순서대로 따라 하세요.
<!-- BEGIN GENERATED: bot:join -->아직 계정이 없다면 Slack에서 `/cluster join`으로 신청해 주세요.<!-- END GENERATED: bot:join -->

!!! warning "AI 에이전트를 쓴다면"
    AI 에이전트로 접속하거나 전송하려면 그 에이전트에 [AI 에이전트 규칙](../policy/ai-agents.md)을 반드시 넣어야 합니다.

## 접속 정보

계정을 발급할 때 관리자가 아래 정보를 알려 줍니다. 이 문서에서는 자리표시자로 씁니다.

| 항목 | 자리표시자 | 설명 |
|------|-----------|------|
| 로그인 노드 주소 | `<로그인 주소>` | SSH로 접속할 대상 |
| SSH 포트 | `<SSH 포트>` | 접속 위치(내부망, 외부망)에 따라 다를 수 있습니다 |
| 계정 이름 | `<아이디>` | 클러스터 사용자 이름 |

접속하면 **로그인 노드**에 있게 됩니다. 여기서 코드를 편집하고 Slurm에 잡을 제출합니다.
GPU 연산은 로그인 노드가 아니라 **계산 노드**에서 Slurm을 통해 실행됩니다.

## SSH 키 등록 (가장 먼저, 필수)

!!! warning "왜 필수인가요"
    로그인 노드에는 방화벽과 무차별 대입(brute-force) 차단이 항상 켜져 있습니다.
    **비밀번호를 여러 번 틀리면 접속한 IP가 차단됩니다.** 비밀번호 로그인을 반복하면 차단되기 쉬우니,
    반드시 SSH 키로 비밀번호 없이 접속하세요.

### 1. 내 PC에서 SSH 키 만들기

이미 키가 있으면 건너뛰세요.

```bash
# 본인 PC(노트북, 데스크톱)의 터미널에서 실행
ssh-keygen -t ed25519 -C "you@example.com"
# 엔터 몇 번이면 ~/.ssh/id_ed25519 (개인키)와 id_ed25519.pub (공개키)가 생깁니다
```

### 2. 공개키를 클러스터에 등록

```bash
ssh-copy-id -p <SSH 포트> <아이디>@<로그인 주소>
```

`ssh-copy-id`가 없거나 안 되면, 공개키(`~/.ssh/id_ed25519.pub`) 내용을 클러스터의 `~/.ssh/authorized_keys`에 직접 추가하면 됩니다.

### 3. 접속

```bash
ssh -p <SSH 포트> <아이디>@<로그인 주소>
```

### 4. `~/.ssh/config`로 편하게 (강력 추천)

내 PC의 `~/.ssh/config`에 아래를 넣어 두면 `ssh cluster` 한 줄로 접속됩니다.

```sshconfig
Host cluster
    HostName <로그인 주소>
    User <아이디>
    Port <SSH 포트>
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 10m
```

`Control`로 시작하는 세 줄은 한 번 연 접속을 다시 쓰고, 마지막 창을 닫은 뒤에도 10분 동안 열어 둡니다. 창을 여러 개 열거나 `scp`를 할 때도 새로 로그인하지 않으니
빨라지고, 로그인 노드와 네트워크의 부담도 줄어듭니다.

```bash
ssh cluster
```

!!! tip "IP가 차단되었다면"
    <!-- BEGIN GENERATED: bot:unban -->`/cluster unban`으로 해제를 신청해 주세요.<!-- END GENERATED: bot:unban --> 풀린 뒤에는 꼭 SSH 키를 등록해 주세요. -> [도움 받기](../help.md)

## VSCode로 접속하기

- **VSCode Remote-SSH**는 위의 `~/.ssh/config`를 그대로 인식합니다. VSCode에서 `Remote-SSH: Connect to Host...` -> `cluster`를 선택하세요.
- **VSCode Tunnel은 사용하지 마세요.** 로그인 노드의 CPU를 많이 잡아먹습니다. 반드시 **Remote-SSH**를 쓰세요.

## 웹 포털

SSH 말고도 브라우저로 클러스터를 쓰실 수 있습니다.

<!-- BEGIN GENERATED: service:portal -->
웹 포털에 클러스터 계정으로 로그인하면 상단 메뉴에서 다음을 쓰실 수 있습니다. 포털 주소는 계정을 받을 때 함께 알려 드립니다.

- **Files**: 브라우저에서 `/home` 아래의 파일을 보고, 올리고, 내려받습니다.
- **Jobs**: 내 잡을 보고(Active Jobs), 잡 스크립트를 만들어 제출합니다(Job Composer).
- **Clusters**: 브라우저에서 로그인 노드의 터미널을 엽니다.
- **클러스터**: 노드와 파티션의 구성을 한눈에 봅니다.
- **Grafana**: 모니터링 대시보드입니다.
<!-- END GENERATED: service:portal -->

대시보드마다 무엇을 보여 주는지는 [모니터링](../guide/monitoring.md#웹-대시보드)에 정리해 두었습니다.

## 로그인 노드 사용 규칙 (중요)

로그인 노드는 **모두가 공유하는 현관**입니다. 여기서 무거운 연산(학습, 대용량 전처리 등)을 돌리면 다른 사람의 접속과 편집까지 느려집니다.
그래서 <!-- BEGIN GENERATED: login:limits -->로그인 노드에서는 한 사람이 CPU 8개, 메모리 64 GB, 프로세스 4,096개까지 쓰실 수 있습니다.<!-- END GENERATED: login:limits -->

VSCode 접속, 코드 편집, 가벼운 디버깅은 이 한도 안에서 충분히 할 수 있습니다.
학습, 추론 같은 **실제 연산은 반드시 `srun` 또는 `sbatch`로 계산 노드에 제출**하세요. -> [Slurm 기초](slurm-basics.md)

| 해도 됨 | 하면 안 됨 |
|---------|-----------|
| 코드 편집, git, 가벼운 스크립트 | GPU 학습, 추론을 로그인 노드에서 직접 실행 |
| `sbatch`, `srun`으로 잡 제출 | 대용량 데이터 압축, 복사를 로그인 노드에서 장시간 실행 |
| 가벼운 빌드, 결과 확인 | `nohup python train.py &` 같은 백그라운드 연산 |

## 계산 노드 접속: 내 잡이 실행 중인 노드만 { #계산-노드에는-내-잡이-도는-노드에만-접속할-수-있습니다 }

계산 노드에는 **그 노드에서 내 잡이 실행 중인 동안에만** SSH로 접속할 수 있습니다. 내 잡이 없는 노드에 `ssh`로 접속하면
막힙니다. 접속한 셸은 그 잡에 속해서 그 잡이 받은 CPU, 메모리, GPU만 쓰고, 잡이 끝나면 함께 끝납니다.

내 잡이 실행 중인 노드에 들어가 상태를 보려면, 그 잡의 ID로 셸을 받는 방법을 권합니다. 노드 이름을 몰라도 되고, 여러 노드에
걸친 잡에서도 쓸 수 있습니다. 노드 이름을 알면(`sq`의 NODE 열) `ssh <노드 이름>`으로 접속해도 됩니다.

```bash
squeue --me                                      # 내 잡의 JOBID 확인
srun --jobid=<JOBID> --overlap --pty bash -i     # 그 잡이 실행 중인 노드에서 셸 받기
# 여기서 nvidia-smi, htop, py-spy 등으로 디버깅
```

!!! danger
    시스템 감시를 우회해 자원을 점유하거나 할당받지 않은 자원을 쓰는 행위(예: 잡이 끝난 뒤에도 노드에 프로세스를 남기려는
    시도)는 **무관용 원칙**으로 조치됩니다. -> [규정: 디버깅](../policy/rules.md#디버깅)

## 첫 접속 후 점검 체크리스트

접속했다면 아래를 한 번 실행해 보세요. 계정과 클러스터가 정상인지 확인하는 용도입니다.

```bash
whoami; hostname              # 로그인 노드에 내 계정으로 들어왔는지
id                            # 소속 그룹(팀) 확인. 팀 QoS와 관련
sinfo                         # 노드 상태가 보이면 Slurm 정상
squeue                        # 현재 큐
qos                           # 내가 쓸 수 있는 QoS, 선점 관계, 팀 몫
module avail 2>&1 | head      # 사용 가능한 소프트웨어 모듈
usage                         # 경고, 한도, 취소가 있는 규칙마다 내 현황
```

- `qos`에서 `▌`로 표시된 것이 내가 쓸 수 있는 QoS입니다. 기본 QoS와 함께 **본인 팀 QoS**가 보이는지 확인하세요. 보이지 않으면 관리자에게 문의하세요. -> [QoS 설명](../reference/slurm.md#qos)
- 모듈과 CUDA 환경 설정 -> [소프트웨어 모듈](../guide/modules.md)
- 공유 공간(`/home`, `/scratch`, `/sw`)과 그 쓰임 -> [스토리지와 데이터](../guide/storage.md)

## 다음 단계

- 바로 GPU 잡을 돌려 보고 싶다면 -> [첫 GPU 잡 돌리기](first-job.md)
- Slurm을 처음 쓴다면 -> [Slurm 기초](slurm-basics.md)
- 규칙부터 확인하고 싶다면 -> [클러스터 사용 규정](../policy/rules.md)
