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

## 봇으로 하는 신청

계정, 차단 해제, 공동작업 폴더, 공유 데이터는 Slack에서 클러스터 봇에게 신청하실 수 있습니다.
아무 채널에서나 아래 명령을 입력해 주세요.

<!-- BEGIN GENERATED: bot:subcommands -->
| 명령 | 하는 일 |
|---|---|
| `/cluster join` | 클러스터 계정 신청 |
| `/cluster leave` | 계정 정리 신청 (졸업 등) |
| `/cluster unban` | 로그인 실패로 차단된 IP 주소의 해제 신청 |
| `/cluster project` | 공동작업 폴더 만들기 (홈 탭에서 관리) |
| `/cluster data` | 공유 데이터(데이터셋, 모델, 컨테이너 이미지) 받아 두기 신청 |
| `/cluster help` | 이 안내 |
<!-- END GENERATED: bot:subcommands -->

관리자가 승인하면 봇이 DM으로 알려 드립니다. 봇의 홈 탭에서 내 신청과 공동작업 폴더를 보실 수 있습니다.

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
