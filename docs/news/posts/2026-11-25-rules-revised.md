---
date: 2026-11-25
slug: rules-revised
categories: [policy]
---

# 사용 규정 변경 안내

- **<!-- BEGIN GENERATED: day:notice_day -->2026-11-25(수)<!-- END GENERATED: day:notice_day -->부터**
  - `/scratch/<아이디>` 개인 작업 공간은 빠른 NVMe 공간이라, 읽기와 쓰기(I/O)가 많은 실험의 파일을 두시면 좋습니다.
    <!-- BEGIN GENERATED: policy:stale_days -->60<!-- END GENERATED: policy:stale_days -->일 동안 아무도 읽거나 쓰지 않은 파일은 DM으로 먼저 알려 드린 뒤 <!-- BEGIN GENERATED: policy:grace_days -->14<!-- END GENERATED: policy:grace_days -->일 후 정리합니다. 정리될 파일은 `scratch-space`로 확인하실 수 있습니다.
  - <!-- BEGIN GENERATED: rule:idle -->Slurm 잡으로 GPU를 할당받아 두고 **2시간 넘게 쓰지 않으면** 알려 드립니다. **6시간** 동안 GPU를 쓰지 않은 잡은 자동으로 취소되며, 취소 **1시간 전**에 미리 알려 드립니다.<!-- END GENERATED: rule:idle -->
  - 디버깅을 위해 GPU를 잡아 두는 세션(셸, 노트북, 서버)은 **팀 QoS**로 실행해 주시고, 다 쓰시면 바로 반납해 주세요.
  - <!-- BEGIN GENERATED: login:limits -->로그인 노드에는 한 사람당 CPU 8개, 메모리 64 GB, 프로세스 4,096개까지 쓰실 수 있도록 제한이 걸려 있습니다.<!-- END GENERATED: login:limits --> 무거운 작업은 Slurm 잡으로 실행해 주세요.
  - 공유 스토리지를 많이 읽고 쓰는 잡이 있으면 DM으로 알려 드립니다. I/O를 줄이는 방법은
    [스토리지 안내](../../guide/storage.md#공유-스토리지를-느리게-만들지-않는-법)에 정리해 두었습니다.
  - 공용 모델 캐시(`$SHARED_HF_HUB_CACHE`)를 쓰실 수 있습니다. 사용법은 [스토리지 안내](../../guide/storage.md#공용-모델)를 참고해 주세요.
  - 컨테이너는 Enroot, Pyxis, Podman을 이용해 주세요.
  - [AI 에이전트 규칙](../../policy/ai-agents.md)을 새로 정리했습니다. AI 에이전트를 쓰려면 그 에이전트에
    규칙 파일(사이트의 `agents/AGENTS.md`)을 반드시 넣어야 합니다.
- **<!-- BEGIN GENERATED: day:limits_from -->2026-12-09(수)<!-- END GENERATED: day:limits_from -->부터**
  - 한 사람이 `/home` 10 TB(파일 3,000만 개), `/scratch` 5 TB(파일 1,500만 개)까지 쓰실 수 있고, <!-- BEGIN GENERATED: policy:warn_percent -->90%<!-- END GENERATED: policy:warn_percent -->에 이르면 미리 알려 드립니다.
  - 한도에 이르면 새 잡 제출이 보류되니, 그 전에 정리해 주시면 감사하겠습니다.
  - `/home/data`의 내용은 각 폴더 주인의 홈으로 옮겨 드릴 예정입니다. 필요한 파일은 미리 백업해 두시기 바랍니다.

<!-- more -->

자세한 내용은 [사용 규정](../../policy/rules.md), [AI 에이전트 규칙](../../policy/ai-agents.md),
[스토리지와 데이터](../../guide/storage.md#용량-한도와-정리), [컨테이너](../../guide/containers.md)에서 보실 수 있습니다.
함께 바뀐 것도 알려 드립니다.

- GPU를 쓰는 잡의 이름을 따로 정하지 않으셔도 됩니다.
- 이미 시스템이 지키고 있던 두 가지를 규정에 적었습니다. CPU만 쓰는 잡은 GPU 노드를 통째로 쓸 수 없고,
  한 잡에는 GPU 타입 하나만 요청하실 수 있습니다.
- AI 에이전트 규칙은 공유 자원에 영향을 주는 행동에 적용됩니다. 짧은 시간에 요청을 몰아서 보내지 않기,
  끝난 뒤 남은 프로세스 정리하기 등이 들어 있습니다.
- 데이터는 성격에 맞게 두시면 모두가 빨라집니다 ([스토리지](../../guide/storage.md#공유-스토리지를-느리게-만들지-않는-법)).
  `/home`에는 오래 보관할 데이터(묶음 파일), `/scratch`에는 지금 실험의 작업본, 잡의 `/tmp`에는 한 잡 동안 쓰는 파일을 두어 주세요.
  작은 파일은 묶어서 순서대로 읽고, Python 환경은 한 번 묶어 잡의 `/tmp`에 풀어 쓰시길 권해 드립니다.
  큰 디렉터리 트리 전체에 `du`, `find`를 돌리거나 로그인 노드에서 큰 `rsync`, `tar`를 하는 일은 피해 주세요. 사용량은 클러스터가 제공하는 보기로 확인해 주세요.
- 패키지 캐시와 공용 모델 캐시는 클러스터가 환경 변수로 정해 두었습니다
  ([환경 변수](../../guide/storage.md#환경-변수), [공용 모델](../../guide/storage.md#공용-모델)).
- Python 환경은 [uv](../../guide/modules.md#python-환경-uv)를 권해 드립니다.
