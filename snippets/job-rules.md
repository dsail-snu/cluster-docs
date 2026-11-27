- **팀 QoS는 본인 소속 팀 것**을 쓴다. 본인 것은 `qos`로 확인한다.
- **GPU를 요청할 때는 GPU 타입을 명시**한다: `--gres=gpu:<GPU 타입>:4`처럼. 타입 이름은 `sq` 또는 `sinfo -o "%G"`로 확인한다.
- **GPU 잡은 파티션, CPU 수, 메모리를 지정하지 않는다.** 파티션은 GPU 타입으로, CPU와 메모리는 GPU 수에 비례해 **자동으로 정해진다**.

    파티션과 CPU 수는 적더라도 무시되고, 메모리를 적으면 제출이 거부된다. 처리 규칙 전체는
    [Slurm 레퍼런스: 자동 할당과 라우팅](../reference/slurm.md#자동-할당과-라우팅)에 있다.

- **노드당 GPU 수는 <!-- BEGIN GENERATED: policy:gpus_per_node -->1, 2, 4, 8<!-- END GENERATED: policy:gpus_per_node --> 중에서** 요청한다.
  여러 노드에 걸친 잡은 노드마다 같은 수를 받는다.
    - `--gpus=N`처럼 노드 수 없이 총 개수만 적으면 N 자체가 <!-- BEGIN GENERATED: policy:gpus_per_node -->1, 2, 4, 8<!-- END GENERATED: policy:gpus_per_node --> 중 하나여야 한다.
    - `-N`(노드 수)과 함께 적으면 총 개수 N을 노드 수로 나눈 값이 <!-- BEGIN GENERATED: policy:gpus_per_node -->1, 2, 4, 8<!-- END GENERATED: policy:gpus_per_node --> 중 하나여야 한다. 예: `-N 2 --gpus=8`이면 노드마다 4장.
    - GPU가 8장보다 적은 노드도 있다. 노드별 GPU 수는 `sq`로 확인한다.
- **CPU 전용 잡은 CPU 수를 필요한 만큼 자유롭게 지정**해도 된다. 파티션은 적지 않는다. 다만 CPU 전용 잡으로 **GPU 노드를 통째로 차지할 수는 없다**.
  `--exclusive`나 `--mem=0`을 적으면 제출이 거부된다.
- **한 잡에는 GPU 타입 하나만** 요청한다. 여러 타입을 섞으면 제출이 거부된다. 타입마다 따로 제출한다.
- **`--qos`를 생략하면 기본 QoS로 제출된다.** 기본 QoS 잡은 남는 자원을 쓸 수 있는 대신, 팀 QoS 잡이 그 자원을 가져갈 수 있다(**선점**, preemption). 선점된 잡은 큐로 돌아가 **처음부터** 다시 실행된다. 긴 잡은 반드시 체크포인트를 남긴다. -> [선점 설명](../reference/slurm.md#선점)
