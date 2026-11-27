!!! info "GPU 점유의 뜻"
    인터랙티브 터미널, Jupyter Notebook, **요청을 기다리는 추론 서버**처럼 **GPU를 언제 쓸지 사용자가 직접 정하는 모든 상황**을 말한다.
    단, **데이터 처리가 끝나면 스스로 자원을 반납하는 자동화 잡**은 여기에 해당하지 않는다.

<!-- BEGIN GENERATED: rule:sessions:plain -->`srun`, `salloc`으로 여는 GPU 세션은 팀 QoS(`--qos=<팀 QoS>`)로만 시작할 수 있다. 팀 QoS 없이 제출하면 `qos`로 내 QoS를 확인하라는 안내와 함께 거부된다.<!-- END GENERATED: rule:sessions:plain -->

```bash
# GPU를 점유하는 인터랙티브 셸 (팀 QoS는 본인 것으로. `qos` 로 확인)
srun --qos=<팀 QoS> --time=04:00:00 --gres=gpu:<GPU 타입>:1 --pty bash -i
```

클러스터가 GPU 사용률을 상시 감시한다.
<!-- BEGIN GENERATED: rule:idle:plain -->
Slurm 잡이 할당받은 GPU를 **2시간 넘게 쓰지 않으면** 알린다. 할당받은 GPU를 **6시간** 동안 쓰지 않은 잡은 자동으로 취소되고, 취소 **1시간 전**에 미리 알린다.
<!-- END GENERATED: rule:idle:plain -->
여기서 할당받은 GPU를 쓰지 않는다는 것은 그 잡이 할당받은 GPU가 **모두** 그 시간 내내 쉬었다는 뜻이다.
그중 한 장이라도 쓰이면 클러스터는 시간을 처음부터 다시 센다.
