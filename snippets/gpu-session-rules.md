!!! info "GPU를 점유한다는 것"
    인터랙티브 터미널, Jupyter Notebook, **요청을 기다리는 추론 서버**처럼 **GPU를 언제 쓸지 사용자가 직접 정하는 모든 상황**을 말합니다.
    단, **데이터 처리가 끝나면 스스로 자원을 반납하는 자동화 잡**은 여기에 들지 않습니다.

**GPU를 점유하는 세션의 규칙**

| # | 규칙 | 예시 |
|---|---|---|
| 1 | **본인 소속 팀 QoS**로 실행 | `--qos=<팀 QoS>` (`qos` 로 확인) |
| 2 | 다 쓰면 **즉시 반납** | 셸에서 `exit`, 또는 `scancel <JOBID>` |

<!-- BEGIN GENERATED: rule:sessions -->`srun`, `salloc`으로 여는 GPU 세션은 팀 QoS(`--qos=<팀 QoS>`)로만 시작할 수 있습니다. 팀 QoS 없이 제출하면 `qos`로 내 QoS를 확인하라는 안내와 함께 거부됩니다.<!-- END GENERATED: rule:sessions -->

```bash
# GPU를 점유하는 인터랙티브 셸 (팀 QoS는 본인 것으로. `qos` 로 확인)
srun --qos=<팀 QoS> --time=04:00:00 --gres=gpu:<GPU 타입>:1 --pty bash -i
```

GPU 사용률은 상시 감시됩니다.
<!-- BEGIN GENERATED: rule:idle -->
Slurm 잡으로 GPU를 할당받아 두고 **2시간 넘게 쓰지 않으면** 알려 드립니다. **6시간** 동안 GPU를 쓰지 않은 잡은 자동으로 취소되며, 취소 **1시간 전**에 미리 알려 드립니다.
<!-- END GENERATED: rule:idle -->
