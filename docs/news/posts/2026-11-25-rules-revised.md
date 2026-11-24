---
date: 2026-11-25
slug: rules-revised
categories: [policy]
---

# 사용 규정이 바뀝니다

- **<!-- BEGIN GENERATED: date:notice_day -->2026-11-25<!-- END GENERATED: date:notice_day -->부터** GPU를 점유하는 세션(인터랙티브 셸, 노트북, 대기 중인 서버)은 **팀 QoS**로 실행하고, 다 쓰면 바로 반납합니다.
- **<!-- BEGIN GENERATED: date:notice_day -->2026-11-25<!-- END GENERATED: date:notice_day -->부터** <!-- BEGIN GENERATED: rule:idle -->GPU를 할당받은 채 **2시간 넘게 쓰지 않으면** 매시간 사용 현황 리포트마다 Slack으로 알림이 갑니다. **6시간** 동안 쓰지 않은 잡은 자동으로 취소되고, 취소 **1시간 전**에 미리 알려 줍니다.<!-- END GENERATED: rule:idle -->
- **<!-- BEGIN GENERATED: date:scratch_cleanup_from -->2026-11-25<!-- END GENERATED: date:scratch_cleanup_from -->부터** `<스크래치 경로>/<아이디>`에서 <!-- BEGIN GENERATED: policy:stale_days -->60<!-- END GENERATED: policy:stale_days -->일 동안 쓰지 않은 파일은 DM 알림 <!-- BEGIN GENERATED: policy:grace_days -->14<!-- END GENERATED: policy:grace_days -->일 뒤 정리됩니다. `scratch-space`로 확인하세요.
- **<!-- BEGIN GENERATED: date:docker_admin_only_from -->2026-11-25<!-- END GENERATED: date:docker_admin_only_from -->부터** `docker`는 관리자 전용입니다. Enroot, Pyxis, Podman을 쓰세요.
- **<!-- BEGIN GENERATED: date:notice_day -->2026-11-25<!-- END GENERATED: date:notice_day -->부터** AI 에이전트의 SSH와 전송 접속은 모두 합쳐 최대 3번, 30초 이상 간격입니다.
- **<!-- BEGIN GENERATED: date:limits_from -->2026-12-09<!-- END GENERATED: date:limits_from -->부터** 사람마다 `/home` <!-- BEGIN GENERATED: quota:/home:block_hard -->10 TB<!-- END GENERATED: quota:/home:block_hard -->와 파일 <!-- BEGIN GENERATED: quota:/home:inode_hard -->3,000만<!-- END GENERATED: quota:/home:inode_hard -->개, `<스크래치 경로>` <!-- BEGIN GENERATED: quota:/scratch:block_hard -->5 TB<!-- END GENERATED: quota:/scratch:block_hard -->와 파일 <!-- BEGIN GENERATED: quota:/scratch:inode_hard -->1,500만<!-- END GENERATED: quota:/scratch:inode_hard -->개가 상한입니다. 경고는 <!-- BEGIN GENERATED: policy:warn_percent -->90%<!-- END GENERATED: policy:warn_percent -->에서 옵니다.
- **<!-- BEGIN GENERATED: date:submit_holds_from -->2026-12-09<!-- END GENERATED: date:submit_holds_from -->부터** 상한을 넘은 사람은 새 잡을 제출할 수 없습니다.
- **<!-- BEGIN GENERATED: date:home_data_move -->2026-12-09<!-- END GENERATED: date:home_data_move -->부터** 공용 데이터 폴더(`/home/data`)의 내용은 각 폴더 주인의 홈으로 옮겨집니다. 그 전에 필요한 것을 챙기세요.

<!-- more -->

자세한 규칙은 [사용 규정](../../policy/index.md), [AI 에이전트 규칙](../../policy/ai-agents.md),
[스토리지와 데이터](../../guide/storage.md#용량-한도와-정리), [컨테이너](../../guide/containers.md)에 있습니다.
위 항목 밖에 바뀐 것:

- 잡 이름을 `debug`로 짓는 규칙은 없어졌습니다.
- 이미 시스템이 막고 있던 두 가지를 규정에 적었습니다. CPU 전용 잡은 GPU 노드를 통째로 차지할 수 없고,
  한 잡에는 GPU 타입 하나만 요청할 수 있습니다.
- AI 에이전트 규칙은 공유 자원에 영향을 주는 행동에만 적용됩니다. 확인 없이 진행하는 모드도 쓸 수 있고,
  오래 돌려도 됩니다. 짧은 시간에 요청을 몰아서 보내지 말고, 남겨진 프로세스는 정리하세요.
- I/O ([스토리지](../../guide/storage.md#공유-스토리지를-느리게-만들지-않는-법)): `/home`은 오래 보관하는 데이터(묶음 파일),
  `/scratch`는 지금 실험의 작업본, 잡의 `/tmp`는 한 잡 동안 쓰는 파일입니다. 작은 파일은 묶어서 순서대로 읽고,
  Python 환경은 한 번 묶어 잡의 `/tmp`에 풀어 씁니다. 큰 트리의 `du`, `find`, 로그인 노드의 큰 `rsync`, `tar`는
  하지 말고, 사용량은 제공되는 보기로 확인하세요.
- 패키지 캐시와 공용 모델 캐시는 클러스터가 환경 변수로 정해 둡니다
  ([환경 변수](../../guide/storage.md#환경-변수), [공용 모델](../../guide/storage.md#공용-모델)).
- 권장: Python 환경은 [uv](../../guide/modules.md#python-환경-uv), 컨테이너는 [Enroot, Pyxis, Podman](../../guide/containers.md).
