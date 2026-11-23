---
date: 2026-11-25
slug: rules-revised
categories: [policy]
---

# 사용 규정과 AI 에이전트 규칙을 정리했습니다

모니터링이 자세해진 만큼, 사람이 눈으로 확인하려고 두었던 규칙을 덜어 내고 실제로 공유 자원에 영향을 주는
행동만 규칙으로 남겼습니다. 새 스토리지 한도는 **<!-- BEGIN GENERATED: date:limits_from -->2026-12-09<!-- END GENERATED: date:limits_from -->부터**, 일반 사용자의 Docker 사용 중단은
**<!-- BEGIN GENERATED: date:docker_admin_only_from -->2026-11-25<!-- END GENERATED: date:docker_admin_only_from -->부터** 적용됩니다.

<!-- more -->

**잡과 GPU**

- 잡 이름을 `debug`로 짓는 규칙은 없어졌습니다. GPU를 점유하는 세션(인터랙티브 셸, 노트북, 대기 중인 서버)은
  **팀 QoS**로 실행하고, 다 쓰면 바로 반납하세요.
- **<!-- BEGIN GENERATED: date:notice_day -->2026-11-25<!-- END GENERATED: date:notice_day -->부터** <!-- BEGIN GENERATED: rule:idle -->GPU를 할당받은 채 **2시간 넘게 쓰지 않으면** 매시간 사용 현황 리포트마다 Slack으로 알림이 갑니다. **6시간** 동안 쓰지 않은 잡은 자동으로 취소되고, 취소 **1시간 전**에 미리 알려 줍니다.<!-- END GENERATED: rule:idle -->
- 이미 시스템이 막고 있던 두 가지를 규정에 적었습니다. CPU 전용 잡은 GPU 노드를 통째로 차지할 수 없고,
  한 잡에는 GPU 타입 하나만 요청할 수 있습니다.

**AI 에이전트** ([AI 에이전트 규칙](../../policy/ai-agents.md))

- 규칙은 공유 자원에 영향을 주는 행동에만 적용됩니다. 확인 없이 진행하는 모드도 쓸 수 있습니다.
- SSH와 전송 접속은 **모두 합쳐 최대 3번, 30초 이상 간격**. 실패하면 멈추고 보고합니다.
- 반복 조회 간격 규칙 대신, 짧은 시간에 요청을 몰아서 보내지 않는 원칙 하나로 바꿨습니다.
- 에이전트를 오래 돌려도 됩니다. 대신 남겨진 프로세스와 누수를 정리하세요.

**스토리지** ([스토리지와 데이터](../../guide/storage.md#용량-한도와-정리))

- **<!-- BEGIN GENERATED: date:limits_from -->2026-12-09<!-- END GENERATED: date:limits_from -->부터** 사람마다 `/home` 10 TB와 파일 3,000만 개, `<스크래치 경로>` 5 TB와 파일 1,500만 개가 상한입니다.
  경고는 상한의 <!-- BEGIN GENERATED: policy:warn_percent -->90%<!-- END GENERATED: policy:warn_percent -->에서 옵니다. 같은 날부터 상한을 넘은 사람은 새 잡을 제출할 수 없고, 공용 데이터 폴더(`/home/data`)의
  내용은 각 폴더 주인의 홈으로 옮겨집니다. 그 전에 필요한 것을 챙기세요.
- **<!-- BEGIN GENERATED: date:scratch_cleanup_from -->2026-11-25<!-- END GENERATED: date:scratch_cleanup_from -->부터** `<스크래치 경로>/<아이디>`는 빠른 NVMe 작업 공간이며 백업이 아닙니다. <!-- BEGIN GENERATED: policy:stale_days -->60<!-- END GENERATED: policy:stale_days -->일 동안 쓰지 않은 파일은 DM 알림 <!-- BEGIN GENERATED: policy:grace_days -->14<!-- END GENERATED: policy:grace_days -->일 뒤
  정리됩니다. 지워질 파일은 `scratch-space`로 확인하세요.

**I/O** ([AI 에이전트 규칙](../../policy/ai-agents.md#로그인-노드와-공유-스토리지), [스토리지](../../guide/storage.md#공유-스토리지를-느리게-만들지-않는-법))

- 큰 트리의 `du`, `find`, 큰 디렉터리의 `rsync`, `tar`, 데이터셋 전처리 같은 무거운 I/O는 모두를 느리게 합니다.
  큰 데이터와 무거운 I/O는 `/scratch`에 두고, `du` 대신 제공되는 사용량 보기를 쓰세요.

**컨테이너** ([컨테이너](../../guide/containers.md))

- **<!-- BEGIN GENERATED: date:docker_admin_only_from -->2026-11-25<!-- END GENERATED: date:docker_admin_only_from -->부터** `docker` 그룹은 관리자 전용입니다. 일반 사용자는 Enroot, Pyxis, Podman을 씁니다.

**권장**

- Python 환경은 [uv](../../guide/modules.md#python-환경-uv), 컨테이너는 [Enroot, Pyxis, Podman](../../guide/containers.md)을 씁니다.
