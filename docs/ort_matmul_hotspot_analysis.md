# ORT MatMul Hotspot Category Analysis

## 입력과 방법

- ONNX model: `/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx`
- ORT sweep raw runs: `onnx_profile/results_onnx_sweep/raw/ort_sweep_raw_runs.json`
- ONNX graph inspection: `onnx_profile/results_onnx/raw/onnx_graph_inspection.json`
- 분석 profile 수: 60 / 60
- ONNX graph node 수: 7837
- ONNX MatMul node 수: 237

ORT profile JSON의 `Node` event 중 `op_name == "MatMul"`인 항목을 읽고, profile event의 normalized node name을 우선 ONNX graph node name에 매칭했다. `node_index`는 ORT 최적화 이후 원본 ONNX graph index와 어긋날 수 있으므로 graph metadata 보조 fallback으로만 사용하고, category 분류에는 profile/graph node name path를 사용했다. 분류는 node name/path가 명확한 경우에만 적용했다.

분류 규칙은 다음과 같다.

- `q_proj`, `k_proj`, `v_proj`: `attention_qkv_projection`
- attention 내부 bare `MatMul`이고 profile output이 attention score 형태의 4D tensor인 경우: `attention_qk_score`
- attention 내부 `MatMul_1`이고 profile output이 4D tensor인 경우: `attention_v_weighted_sum`
- `o_proj`: `attention_output_projection`
- `mlp/*_proj`: `mlp_projection`
- `lm_head`: `lm_head`
- 위 규칙으로 확정할 수 없는 MatMul: `unknown`

## MatMul Category 비중

아래 비중은 전체 MatMul 시간 중 category별 비중이다. 단위 `total_us` 열은 표에서는 ms로 표시한다.

| category | call_count | total_ms | share |
| --- | --- | --- | --- |
| mlp_projection | 14976 | 23163.290 | 61.09% |
| lm_head | 192 | 10546.540 | 27.81% |
| attention_qkv_projection | 14976 | 1861.004 | 4.91% |
| attention_output_projection | 4992 | 1343.254 | 3.54% |
| attention_v_weighted_sum | 4992 | 1001.248 | 2.64% |
| unknown | 384 | 2.787 | 0.01% |
| attention_qk_score | 0 | 0.000 | 0.00% |

## Prefill/Decode 차이

phase별 MatMul category 비중은 다음과 같다.

| phase | category | call_count | total_ms | share |
| --- | --- | --- | --- | --- |
| decode | mlp_projection | 14040 | 15016.566 | 64.71% |
| decode | lm_head | 180 | 6079.624 | 26.20% |
| decode | attention_qkv_projection | 14040 | 1212.377 | 5.22% |
| decode | attention_output_projection | 4680 | 746.767 | 3.22% |
| decode | attention_v_weighted_sum | 4680 | 149.655 | 0.64% |
| decode | unknown | 360 | 2.344 | 0.01% |
| decode | attention_qk_score | 0 | 0.000 | 0.00% |
| prefill | mlp_projection | 936 | 8146.724 | 55.38% |
| prefill | lm_head | 12 | 4466.916 | 30.36% |
| prefill | attention_v_weighted_sum | 312 | 851.593 | 5.79% |
| prefill | attention_qkv_projection | 936 | 648.627 | 4.41% |
| prefill | attention_output_projection | 312 | 596.487 | 4.05% |
| prefill | unknown | 24 | 0.443 | 0.00% |
| prefill | attention_qk_score | 0 | 0.000 | 0.00% |

세부 context/decode-step별 값은 `paper_assets/tables/ort_matmul_category_by_context.csv`에 저장했다. `paper_assets/figures/ort_matmul_category_share.png`는 같은 값을 stacked share로 시각화한다.

## Top MatMul Nodes

아래 표는 context/phase/decode-step을 모두 합쳐 시간이 큰 MatMul node 상위 20개다. 단위 `total_us` 열은 표에서는 ms로 표시한다.

| category | phase | ctx | steps | node | calls | total_ms | matmul_share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lm_head | prefill | 2048 | 0 | /lm_head/MatMul | 3 | 2644.152 | 31.25% |
| lm_head | prefill | 1024 | 0 | /lm_head/MatMul | 3 | 1127.542 | 29.17% |
| lm_head | decode | 1024 | 8 | /lm_head/MatMul | 24 | 823.545 | 22.29% |
| lm_head | decode | 512 | 8 | /lm_head/MatMul | 24 | 810.926 | 27.40% |
| lm_head | decode | 128 | 8 | /lm_head/MatMul | 24 | 805.637 | 28.22% |
| lm_head | decode | 2048 | 8 | /lm_head/MatMul | 24 | 798.101 | 27.38% |
| lm_head | prefill | 512 | 0 | /lm_head/MatMul | 3 | 532.474 | 29.21% |
| lm_head | decode | 1024 | 4 | /lm_head/MatMul | 12 | 412.897 | 27.95% |
| lm_head | decode | 128 | 4 | /lm_head/MatMul | 12 | 403.880 | 26.09% |
| lm_head | decode | 512 | 4 | /lm_head/MatMul | 12 | 399.463 | 26.41% |
| lm_head | decode | 2048 | 4 | /lm_head/MatMul | 12 | 396.964 | 27.00% |
| lm_head | decode | 2048 | 2 | /lm_head/MatMul | 6 | 211.859 | 26.11% |
| lm_head | decode | 1024 | 2 | /lm_head/MatMul | 6 | 206.039 | 23.65% |
| lm_head | decode | 128 | 2 | /lm_head/MatMul | 6 | 204.977 | 28.19% |
| lm_head | decode | 512 | 2 | /lm_head/MatMul | 6 | 199.824 | 25.91% |
| lm_head | prefill | 128 | 0 | /lm_head/MatMul | 3 | 162.748 | 28.95% |
| lm_head | decode | 1024 | 1 | /lm_head/MatMul | 3 | 103.878 | 24.50% |
| lm_head | decode | 2048 | 1 | /lm_head/MatMul | 3 | 103.213 | 25.40% |
| lm_head | decode | 128 | 1 | /lm_head/MatMul | 3 | 99.347 | 26.87% |
| lm_head | decode | 512 | 1 | /lm_head/MatMul | 3 | 99.074 | 25.18% |

## QK Dot-Product 확인 가능 여부

- `attention_qk_score`로 분류된 MatMul 비중: 0.00%
- 이 값은 node name/path가 attention 내부 bare `MatMul`로 남아 있고 profile output이 4D attention score 형태로 확인되는 항목에 한정한 보수적 분류다.
- `MatMul`이 곧 QK라고 가정하지 않았으며, `rotary_emb/MatMul`처럼 이름/path가 QK score를 확정하지 못하는 항목은 `unknown`으로 남겼다.
- unknown 비중: 0.01%

## FPGA Decode Accelerator 설계 판단

- 전체 MatMul 시간의 주된 비중은 QK dot-product보다 MLP/linear projection 계열에 더 가깝다. 따라서 FPGA Decode Accelerator의 1차 확장 대상은 QK 단일 블록만이 아니라 decode 단계의 일반 MatVec/MatMul 데이터패스와 weight streaming 구조까지 포함해 검토해야 한다.
- attention/MLP/lm_head projection으로 분류된 일반 MatVec/MatMul 계열 합계는 전체 MatMul 시간의 97.35%이다.
- unknown 비중이 0.01% 남아 있으므로, 이 부분은 노드명과 graph path만으로는 설계 대상 연산을 확정하지 않는다.

현 시점의 하드웨어 해석은 기존 DE10-Lite INT8 QK dot-product primitive의 타당성을 넘어서지 않는다. 이 분석은 다음 설계 단계에서 QK score, V weighted sum, attention/MLP projection, 그리고 stream/buffer interface 중 무엇을 우선 검토할지 정하기 위한 host-side ORT 근거로만 사용한다.

## 한계

- 분류는 node name/path 기반이다. node name이 불충분하거나 graph 최적화로 의미가 사라진 경우 category를 확정하지 않는다.
- ORT CPUExecutionProvider profile의 시간은 host-side 실행 특성을 반영한다. FPGA primitive의 cycle 또는 end-to-end speedup으로 직접 환산하지 않는다.
- MatMul 내부 shape와 인접 연산은 보조 정보로 CSV에 남겼지만, 이름/path가 불충분한 경우 억지로 category를 추정하지 않았다.
