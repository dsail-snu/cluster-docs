---
purpose: 클러스터 상태를 자동으로 알리는 채널: GPU 사용 현황, 쓰지 않는 GPU, 스토리지. 사람은 글을 쓰지 않습니다.
topic: [[reports:inline]] | 질문은 [[#help]]
title: 상태 채널 읽는 법
table: 클러스터 상태: GPU 사용 현황, 오래 노는 잡 알림, 디스크 사용량
bookmark: :bar_chart: | 모니터링 안내 | guide/monitoring.md
---
# 클러스터 상태

이 채널의 글은 모두 자동으로 올라옵니다.

[[reports]]

## 쓰지 않는 GPU

[[rule:idle]]

내 잡의 GPU가 실제로 무엇을 했는지는 로그인 노드에서 `gpu-usage <JOBID>`로 봅니다.

## 더 자세히

- [모니터링](guide/monitoring.md): 대시보드와 각 수치의 뜻
- 리포트에 대한 질문은 [[#help]]에
