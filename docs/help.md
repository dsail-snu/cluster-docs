# 도움 받기

## 문의 안내

<!-- BEGIN GENERATED: chat:channels -->
| Slack 채널 | 용도 |
|---|---|
| `#infra-help` | 질문, 문제 신고, 요청 |
| `#infra-announce` | 공지: 규정 변경, 점검, 소프트웨어 업데이트 |
| `#infra-status` | 클러스터 상태: GPU 사용 현황, 주간 GPU 사용, 디스크 사용량 |
<!-- END GENERATED: chat:channels -->

먼저 [자주 묻는 질문과 문제 해결](guide/troubleshooting.md)에 같은 증상이 있는지 확인하세요.

<!-- BEGIN GENERATED: bot:section -->
## Slack 명령 (/cluster)

계정, 차단 해제, 공동작업 폴더, 공유 데이터는 Slack에서 클러스터 봇에게 신청하실 수 있습니다.
아무 채널에서나 아래 명령을 입력해 주세요.

| 명령 | 역할 |
|---|---|
| `/cluster join` | 클러스터 계정 신청 |
| `/cluster leave` | 계정 정리 신청 (졸업 등) |
| `/cluster unban` | 로그인 실패로 차단된 IP 주소의 차단 해제 신청 |
| `/cluster project` | 공동작업 폴더 만들기 (홈 탭에서 관리) |
| `/cluster data` | 공유 데이터(데이터셋, 모델, 컨테이너 이미지) 신청 |
| `/cluster usage` | 규칙마다 내 현황 (로그인 노드의 usage 명령과 같은 숫자, 로그인 노드 한도만 빼고) |
| `/cluster help` | 이 안내 |

관리자가 승인하면 봇이 DM으로 알려 드립니다. 봇의 홈 탭에서 내 신청과 공동작업 폴더를 보실 수 있습니다.
<!-- END GENERATED: bot:section -->

## 문의할 때 함께 적을 것

- **잡 ID** (`JOBID`)
- **언제** 일어났는지 (시각)
- **정확한 오류 메시지** (요약하지 말고 그대로 복사)
- **무엇을 시도했는지** (실행한 명령, 바꿔 본 것)

```bash
scontrol show job <JOBID>      # 실행 중이거나 막 끝난 잡
sacct -j <JOBID>               # 끝난 잡
```

## 급한 장애

클러스터 전체가 멈추는 등 급한 장애는 <!-- BEGIN GENERATED: chat:help -->`#infra-help`<!-- END GENERATED: chat:help -->에 글을 올리고 관리자를 멘션해 주세요.

- 문의는 개인 메시지(DM)로 보내지 마세요. 모두가 볼 수 있는 채널에 올려야 같은 문제를 겪는 사람도 도움을 받습니다.
- 처리 순서는 관리자가 정합니다.
