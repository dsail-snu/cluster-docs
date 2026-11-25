# GPU 클러스터 사용 가이드

여러 사람이 한정된 GPU를 나눠 쓰는 GPU 클러스터를 처음 쓰는 사람도 따라 할 수 있도록 만든 안내 문서입니다.
이 클러스터는 [Slurm](https://slurm.schedmd.com/)으로 GPU, CPU 자원을 공유합니다.
핵심은 **"내가 직접 GPU 서버에 SSH로 붙어서 코드를 돌린다"가 아니라 "Slurm에게 작업을 제출하면 Slurm이 빈 GPU를 배정해 준다"** 는 것입니다.

!!! warning "반드시 먼저 읽으세요"
    [클러스터 사용 규정](policy/rules.md)을 가장 먼저 읽어 주세요. 규정을 몰라서 생긴 불이익은 도움받기 어렵습니다.

## 클러스터를 한 문장으로

**로그인 노드에 SSH로 접속 -> 코드와 데이터를 준비 -> Slurm에게 작업을 제출 -> Slurm이 빈 계산 노드에 배정해서 실행.**

```text
  나 --SSH-->  로그인 노드
                 - 코드 편집, 가벼운 작업, 잡 제출 (sbatch / srun)
                 - GPU 없음. 무거운 연산 금지 (사용자별 자원 한도)
                      |
                      |  sbatch / srun (작업 제출)
                      v
               [ Slurm 스케줄러 ]  --배정-->  계산 노드
                                              - 실제 GPU 연산이 도는 곳

  공유 스토리지: 홈 디렉터리(개인), 공용 소프트웨어, 스크래치(대용량 작업공간)
```

| 구분 | 하는 일 | 접속 방법 |
|------|---------|-----------|
| **로그인 노드** | 접속해서 코드를 짜고 잡을 제출하는 곳. GPU 없음 | SSH로 직접 접속 |
| **계산 노드** | 실제 GPU, CPU 연산이 도는 곳 | **직접 SSH 불가.** Slurm을 통해서만 사용 |
| **웹 포털** | 브라우저에서 파일, 잡, 터미널, 모니터링 대시보드 | 브라우저 -> [웹 포털](start/connect.md#웹-포털) |

스토리지 구성과 어디에 무엇을 둘지는 [스토리지와 데이터](guide/storage.md)를 보세요.

## 처음이라면

아래 순서대로 읽으면 됩니다.

<!-- BEGIN GENERATED: section:start -->
- [접속하기](start/connect.md): 클러스터 계정을 처음 받았을 때 해야 할 것들입니다.
- [첫 GPU 잡 돌리기](start/first-job.md): 5분 만에 첫 GPU 잡을 실행해 봅니다.
- [Slurm 기초](start/slurm-basics.md): Slurm을 한 번도 써 보지 않은 사람을 위한 문서입니다.
<!-- END GENERATED: section:start -->

더 깊이 들어가려면 [잡 레시피](guide/job-recipes.md)와 [Slurm 레퍼런스](reference/slurm.md)로 넘어가세요.

## 꼭 기억할 4가지

1. **GPU 타입을 항상 명시하세요:** `--gres=gpu:<GPU 타입>:<개수>`. `<GPU 타입>`은 `sq` 또는 `sinfo -o "%G"`로 확인합니다.
2. **GPU 잡은 파티션, CPU 수, 메모리를 설정하지 마세요.** GPU 수에 비례해 충분히 자동 할당됩니다. 그보다 많이 잡으면 그 노드의 남은 GPU를 다른 사람이 쓰지 못합니다. (CPU 전용 잡은 CPU 수를 필요한 만큼 지정해도 됩니다.) -> [자동 할당과 라우팅](reference/slurm.md#자동-할당과-라우팅)
3. **무거운 작업은 로그인 노드에서 돌리지 마세요.** 반드시 `srun` 또는 `sbatch`로 계산 노드에 제출하세요.
4. **GPU를 붙잡는 인터랙티브 작업**(셸, 노트북, 대기 중인 서버)은 팀 QoS로 실행하고, 다 쓰면 즉시 반납하세요. -> [규정: 디버깅](policy/rules.md#디버깅)

## 도움이 필요하면

- 규정: [클러스터 사용 규정 (필독)](policy/rules.md)
- 막혔을 때: [문제 해결](guide/troubleshooting.md)
- 질문과 문의: [도움 받기](help.md)

## 외부 참고 자료

- Slurm 공식 문서: <https://slurm.schedmd.com/documentation.html>
- Slurm 명령어 요약표: <https://slurm.schedmd.com/pdfs/summary.pdf>
