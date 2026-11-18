!!! info "GPU를 점유한다는 것"
    인터랙티브 터미널, Jupyter Notebook, **요청을 기다리는 추론 서버** 등 **사용자가 GPU 사용 시점을 임의로 제어할 수 있는 모든 상황**을 말합니다.
    단, **데이터 처리가 끝나면 스스로 자원을 반납하도록 만든 자동화 잡**은 해당하지 않습니다.

**디버깅용 GPU 점유 잡의 필수 규칙**

| # | 규칙 | 예시 |
|---|---|---|
| 1 | **본인 소속 팀 QoS**로 제출 | `--qos=<팀 QoS>` (`qos` 로 확인) |
| 2 | **잡 이름을 `debug`** 로 | `--job-name=debug` |
| 3 | 다 쓰면 **즉시 반납** | 셸에서 `exit`, 또는 `scancel <JOBID>` |

```bash
# 디버깅용 인터랙티브 GPU 셸 (팀 QoS는 본인 것으로. `qos` 로 확인)
srun --qos=<팀 QoS> --job-name=debug --time=04:00:00 \
     --gres=gpu:<GPU 타입>:1 --pty bash -i
```
