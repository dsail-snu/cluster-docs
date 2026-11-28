공유 스토리지는 모두가 함께 쓴다. 한 사람의 I/O가 모든 사람의 잡을 느리게 할 수 있으므로, 데이터를 알맞은 곳에 두고 I/O를 줄인다.

**1. 성격에 맞는 데이터 위치**

| 공간 | 성격 | 용도 |
|---|---|---|
| `/home` | 용량이 크고 오래 보관하는 공간. HDD RAID라서 큰 파일을 처음부터 순서대로 읽고 쓰면 빠르다. 작은 파일을 여기저기 읽고 쓰면 매우 느리다 | 코드, 결과, **묶음 파일로 보관하는** 데이터셋 |
| `/scratch` | 진행 중인 실험이 자주 읽고 쓰는 작업본을 두는 NVMe RAID. 작은 파일, 무작위 접근, 체크포인트에 강하다. <!-- BEGIN GENERATED: quota:each:/scratch -->한 사람당 5 TB까지 쓸 수 있다.<!-- END GENERATED: quota:each:/scratch --> <!-- BEGIN GENERATED: policy:stale_days -->60<!-- END GENERATED: policy:stale_days -->일 동안 아무도 읽거나 쓰지 않은 파일은 정리된다 | 진행 중인 실험의 작업본 (임시) |
| 잡의 `/tmp` | 잡이 실행 중인 노드의 로컬 디스크에 잡마다 따로 생기고, 잡이 끝나면 지워진다 | 풀어 놓은 실행 환경, 압축을 푼 데이터셋, 한 잡의 임시 파일 |

**2. I/O 줄이기**

- 작은 파일 수만 개는 **묶음**(tar, WebDataset 샤드, LMDB, HDF5, Parquet)으로 만들어 순서대로 읽는다.
  압축이 필요하면 gzip 대신 zstd(`tar -I "zstd -T$(nproc)"`)를 쓴다. 압축하고 푸는 속도가 훨씬 빠르다.
- Python 환경은 미리 파일 하나로 묶어 `/home`에 두고, 잡이 시작할 때 그 잡의 `/tmp`에 푼다.
  묶는 방법은 lockfile로 만든 uv 가상환경을 묶거나 conda-pack을 쓰는 것이다. 컨테이너 이미지(Enroot, Podman)도 파일 하나라서 효과가 같다.
  ([잡 레시피](../guide/job-recipes.md#실행-환경-묶어서-쓰기))
- 잡 안에서는 클러스터가 패키지 캐시(`UV_CACHE_DIR`, `PIP_CACHE_DIR`)를 그 잡의 `/tmp`로 정해 둔다. 공유 스토리지로 바꾸지 않는다.
  필요한 모델이 공용 모델 캐시(`SHARED_HF_HUB_CACHE`)에 있으면 각자 내려받지 않고 그 캐시에서 읽는다.
  ([환경 변수](../guide/storage.md#환경-변수))
- 체크포인트는 **크게, 드물게** `/scratch`에 쓰고, 남길 최종본은 `/home`으로 옮긴다. 학습 스텝마다 작은 로그를 공유 스토리지에 쓰지 않는다.

**3. 무거운 파일 작업 삼가기**

- 큰 디렉터리 트리 전체에 `du`나 `find`를 실행하지 않는다. 큰 `rsync`나 `tar`도 로그인 노드에서 하지 않는다.
  내 사용량은 <!-- BEGIN GENERATED: command:usage:disk -->`usage disk`<!-- END GENERATED: command:usage:disk -->로(파일시스템별 사용량과 한도, 정리 후보 폴더), 전체는 디스크 리포트로 확인한다.
- 무거운 파일 작업이 꼭 필요하면 Slurm 잡(CPU 전용, 낮은 우선순위)으로 실행한다. 다만 잡도 같은 파일 서버를 쓰므로 부담은
  그대로 남는다.
