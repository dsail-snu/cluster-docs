# 도움 받기

## 어디에 물어볼까

<!-- BEGIN GENERATED: chat:channels -->
| Slack 채널 | 용도 |
|---|---|
| `#infra-help` | 질문, 문제 신고, 요청을 편하게 남겨 주세요 |
| `#infra-announce` | 공지 (읽기 전용) |
| `#infra-status` | 클러스터 상태: GPU 사용 현황, 오래 쉬는 잡 알림, 디스크 사용량 |
<!-- END GENERATED: chat:channels -->

먼저 [자주 묻는 질문과 문제 해결](guide/troubleshooting.md)에 같은 증상이 있는지 확인하세요.

## 문의할 때 함께 적을 것

- **잡 ID** (`JOBID`)
- **언제** 일어났는지 (시각)
- **정확한 에러 메시지** (요약하지 말고 그대로 복사)
- **무엇을 시도했는지** (실행한 명령, 바꿔 본 것)

```bash
scontrol show job <JOBID>      # 실행 중이거나 막 끝난 잡
sacct -j <JOBID>               # 끝난 잡
```

## 급한 장애

클러스터 전체가 멈추는 등 급한 장애는 `#infra-help`에 글을 올리고 관리자를 멘션하세요.

- 아무에게나 개인 메시지(DM)를 보내지 마세요. 모두가 볼 수 있는 채널에 올려야 같은 문제를 겪는 사람도 도움을 받습니다.
- 처리 순서는 관리자가 정합니다.
