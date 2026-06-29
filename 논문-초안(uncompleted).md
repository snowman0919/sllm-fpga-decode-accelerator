## ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계
**Bottleneck Analysis of ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator Architecture**
## 저자
[최윤혁](https://orcid.org/0009-0006-3537-0249)
한국디지털미디어고등학교
yunhyuk choi
korea digital media high school

## 초록
온디바이스 환경에서 소형 언어모델은 클라우드 의존성을 줄이고 개인정보 보호와 저지연 응답을 제공할 수 있다. 그러나 0.xB~1B급 sLLM이라도 ONNX Runtime 기반 추론에서는 모델 내보내기, 그래프 구조, 런타임 실행, 메모리 압력, prefill/decode 단계의 상호작용에 따라 병목 위치가 달라질 수 있다. 본 연구는 Gemma 3 1B의 ONNX export 및 graph inspection, ONNX Runtime CPUExecutionProvider profiling, PyTorch 호스트 측 reference baseline, FPGA primitive-level validation을 결합하여 병목을 증거 기반으로 분석한다. 본 연구의 ONNX Runtime profiling에서는 MatMul이 traced phase time의 67.5%를 차지했고, decode 단계에서는 MatMul 비중이 81.1%로 나타났다. MatMul 내부 category 분석에서는 `mlp_projection`과 `lm_head`가 전체 MatMul 시간의 88.90%를 차지하여, 병목을 KV-cache 또는 QK dot-product 하나로 축소하기 어렵다는 점을 확인하였다. 이에 따라 FPGA 설계 방향은 MatMul-free 모델이나 QK 전용 가속기가 아니라, MLP projection과 `lm_head`를 포함하는 decode-stage dense tiled MatVec/MatMul 구조로 설정하였다. FPGA 결과는 DE10-Lite에서 small fixed-dimension INT8 Decode MatVec primitive bitstream을 configuration한 primitive-level 검증으로 한정하며, full Gemma 3 1B 실행이나 end-to-end ONNX Runtime speedup을 주장하지 않는다.
**키워드:** 

ONNX Runtime, 온디바이스 추론, 소형 언어모델, prefill, decode, MatMul, MatVec, FPGA, DE10-Lite, primitive validation

## Abstract
On-device small language models can reduce cloud dependency while improving privacy and response latency. However, in ONNX Runtime-based inference, bottlenecks may arise from model export, graph structure, runtime execution, memory pressure, prefill, decode, or interactions among these factors. This study combines Gemma 3 1B ONNX export and graph inspection, ONNX Runtime CPUExecutionProvider profiling, PyTorch host-side reference baselines, and primitive-level FPGA validation. The latest ONNX Runtime profiling shows that MatMul accounts for 67.5% of traced phase time and 81.1% of decode traced time. Within MatMul time, `mlp_projection` and `lm_head` account for 88.90%, indicating that the bottleneck should not be reduced to KV-cache or QK dot-product alone. The resulting FPGA direction is not a MatMul-free model or a QK-only accelerator, but a decode-stage dense tiled MatVec/MatMul structure targeting projection-heavy workloads such as MLP projection and `lm_head`. The FPGA evidence is limited to small fixed-dimension INT8 Decode MatVec primitive bitstream configuration on DE10-Lite. It does not claim full Gemma 3 1B execution or end-to-end ONNX Runtime speedup.
**keyword:** 

ONNX Runtime, on-device inference, small language model, prefill, decode, MatMul, MatVec, FPGA, DE10-Lite, primitive validation

## 목차
1. 서론
   1.1 온디바이스 sLLM의 필요성
   1.2 ONNX Runtime 기반 추론의 장점과 한계
   1.3 기존 AI 하드웨어 가속 연구와의 차별점
   1.4 연구 목표와 기여

2. 본론
   2.1 ONNX 기반 sLLM 추론 구조
   2.2 Prefill과 Decode 단계의 차이
   2.3 ONNX export와 graph inspection
   2.4 ONNX Runtime profiling 방법
   2.5 KV-cache와 long-context memory pressure
   2.6 CPU/CUDA PyTorch host-side reference baseline
   2.7 ONNX Runtime MatMul hotspot 분석
   2.8 FPGA 가속 대상 primitive 선정
   2.9 INT8 Decode MatVec primitive 검증
   2.10 FPGA 기반 Decode 가속기 구조
   2.11 실험 결과 분석

3. 결론
   3.1 연구 결과 요약
   3.2 FPGA 이종 가속 구조의 가능성
   3.3 연구의 한계
   3.4 후속 연구 방향

## 서론
### 온디바이스 sLLM의 필요성
최근 언어모델은 클라우드 기반 대규모 추론뿐 아니라 모바일, 임베디드 보드, 개인용 PC와 같은 온디바이스 환경으로 확장되고 있다. 온디바이스 sLLM은 네트워크 지연을 줄이고, 민감한 입력 데이터를 외부 서버로 전송하지 않으며, 제한된 환경에서도 AI 기능을 제공할 수 있다는 장점이 있다. 그러나 온디바이스 환경은 메모리 용량, 메모리 대역폭, 전력, 연산 자원이 모두 제한되므로 1B급 소형 언어모델에서도 실제 추론 병목은 단순하지 않다.

### ONNX Runtime 기반 추론의 장점과 한계

ONNX Runtime은 다양한 하드웨어 backend와 graph optimization을 지원하기 때문에 모델 배포 연구에서 중요한 실행 계층이다. 하지만 Hugging Face 모델을 ONNX로 export하는 과정, export된 graph의 input/output 구조, cache I/O 제공 여부, runtime provider 선택, prefill과 decode의 실행 형태에 따라 병목 위치가 달라질 수 있다. 따라서 sLLM의 온디바이스 병목을 논의하려면 PyTorch 실행 결과만으로 결론을 내리기보다 ONNX export, graph inspection, ONNX Runtime profiling을 분리해서 확인해야 한다.

### 기존 AI 하드웨어 가속 연구와의 차별점

본 연구는 FPGA가 전체 언어모델을 대체 실행한다고 주장하지 않는다. 특히 DE10-Lite와 같은 교육용 FPGA 보드는 Gemma 3 1B 전체를 실행하기 위한 메모리와 시스템 구성을 갖춘 플랫폼이 아니다. 본 연구에서 FPGA는 ONNX Runtime profiling으로 도출된 병목 후보를 바탕으로, 작은 하드웨어 primitive의 합성 및 configuration 가능성을 확인하는 검증 계층이다. 따라서 FPGA 결과는 full accelerator 성능 비교가 아니라 primitive feasibility evidence로 해석한다.

### 연구 목표와 기여

본 연구의 목표는 ONNX Runtime 기반 온디바이스 sLLM 추론에서 병목이 어디에 나타나는지 확인하고, 그 결과를 바탕으로 과장 없는 FPGA Decode 가속기 구조의 1차 방향을 제시하는 것이다. 주요 기여는 다음과 같다.

1. ONNX export, graph inspection, runtime profiling, PyTorch 호스트 측 reference baseline을 구분한 재현 가능한 분석 흐름을 제시한다.
2. ONNX Runtime CPUExecutionProvider profiling에서 MatMul 중심 dense linear algebra가 주요 hotspot임을 보이고, 특히 `mlp_projection + lm_head`가 MatMul 시간의 88.90%를 차지함을 정리한다.
3. KV-cache를 long-context decode memory pressure의 대표적 구조 요인으로 다루되, 유일한 병목으로 단정하지 않는다.
4. QK 단일 primitive가 아니라 MLP projection과 `lm_head`를 포함하는 decode-stage tiled MatVec/MatMul 구조를 FPGA 설계 방향으로 제안한다.
5. DE10-Lite에서 small fixed-dimension INT8 Decode MatVec primitive bitstream을 configuration한 board programming evidence를 기록한다.

## 본론

### ONNX 기반 sLLM 추론 구조

본 연구의 host-side 분석은 Gemma 3 1B의 ONNX export와 ONNX Runtime 실행을 중심으로 구성된다. Raw Hugging Face `safetensors` directory는 ONNX Runtime에서 직접 실행할 수 없으므로, 먼저 export preflight와 export 과정을 분리하고, export된 ONNX graph의 input/output 및 operator 구성을 검사한다. 이때 cache-style graph interface가 존재하는지 확인하는 것이 중요하다. 본 연구에서 사용하는 주요 graph inspection 수치와 출처는 표 1과 같이 분리하여 기록한다.

표 1. ONNX graph inspection 요약

| 항목 | 값 | 출처 |
| --- | ---: | --- |
| ONNX graph node 수 | 7837 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| ONNX MatMul node 수 | 237 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| cache input 수 | 52 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| cache output 수 | 52 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| decode cache reuse ready | True | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |

표 1의 결과는 ONNX graph가 cache-style interface를 제공한다는 점을 보여준다. 그러나 cache I/O의 존재는 KV-cache가 단일 주병목이라는 결론으로 직접 이어지지 않는다. Graph-level 구조는 runtime profiling 결과와 함께 해석해야 한다.

### Prefill과 Decode 단계의 차이

Autoregressive language model inference는 prompt 전체를 처리하는 prefill과, 이후 token을 하나씩 생성하는 decode로 나눌 수 있다. Prefill은 sequence length 전체에 대한 계산이 크고, decode는 token 단위 반복과 cache 참조가 중요하다. 따라서 같은 모델이라도 prefill에서는 sequence-length-sensitive operator와 dense projection이 함께 커지고, decode에서는 token 단위 dense projection, cache I/O, shape manipulation이 반복된다.

### ONNX Export와 Graph Inspection

ONNX graph inspection은 profiling 결과 해석의 전제 조건이다. Graph에는 `past_key_values`와 `present` 계열 cache I/O가 노출되어 있어, KV-cache를 decode profiling의 구성 요소로 다룰 수 있다. 다만 이 절의 결과는 graph interface의 존재를 확인하는 데 한정되며, 병목 원인은 이후의 runtime profiling 결과와 결합하여 판단한다.

### ONNX Runtime Profiling 방법

ONNX Runtime profiling은 CPUExecutionProvider에서 context length 128, 512, 1024, 2048과 decode steps 1, 2, 4, 8을 대상으로 수행하였다. 결과는 `paper_assets/tables/ort_context_sweep_latency.csv`, `paper_assets/tables/ort_operator_share_by_context.csv`, `paper_assets/tables/ort_matmul_category_by_context.csv` 등에 정리되어 있다. PyTorch sweep은 host-side reference baseline으로만 사용하며, ONNX Runtime profiling 결과로 대체하지 않는다.

표 2. ONNX Runtime profiling 설정 및 산출물

| 항목 | 설정 또는 산출물 | 출처 |
| --- | --- | --- |
| Runtime provider | ONNX Runtime `CPUExecutionProvider` | `docs/onnx_runtime_sweep_report.md` |
| Context length | 128, 512, 1024, 2048 | `paper_assets/tables/ort_context_sweep_latency.csv` |
| Decode steps | 1, 2, 4, 8 | `paper_assets/tables/ort_context_sweep_latency.csv` |
| Operator share table | operator별 traced node time 비중 | `paper_assets/tables/ort_operator_share_by_context.csv` |
| MatMul category table | MatMul node category별 누적 시간 | `paper_assets/tables/ort_matmul_category_by_context.csv` |

### KV-cache와 Long-context Memory Pressure

KV-cache는 long-context decode에서 중요한 구조적 요인이다. Context가 길어질수록 past/present tensor의 shape, cache update, concat, expand, gather, reshape와 같은 tensor operation 및 memory movement가 증가할 수 있다. 다만 현재 ONNX Runtime profiling에서 관측된 1차 runtime hotspot은 KV-cache 단일 요소가 아니라 MatMul 중심 dense linear algebra다. 따라서 본 연구는 KV-cache를 long-context memory pressure의 대표 요인으로 다루되, 유일한 병목으로 주장하지 않는다.

### CPU/CUDA PyTorch Host-side Reference Baseline

PyTorch 호스트 측 sweep은 local `safetensors` 모델을 직접 실행하여 prefill/decode latency와 process RSS 변화를 관찰하는 reference baseline이다. 이 값은 ONNX Runtime 결과와 동일한 evidence layer가 아니며, ONNX graph 구조나 ORT provider 실행 특성을 직접 설명하지 않는다. 논문에서는 PyTorch 결과를 보조 baseline으로 사용하고, ONNX Runtime profiling과 분리하여 표기한다.

### ONNX Runtime MatMul Hotspot 분석

#### 결과

ONNX Runtime CPUExecutionProvider profiling에서 MatMul은 traced prefill + decode phase node time의 가장 큰 비중을 차지하였다. 주요 수치는 표 3과 같다.

표 3. ONNX Runtime MatMul phase 비중

| 측정 범위 | MatMul 비중 | 출처 |
| --- | ---: | --- |
| prefill + decode traced phase time | 67.5% | `docs/current_bottleneck_implications.md`, `docs/fpga_decode_accel_model_summary.md` |
| prefill traced phase time | 53.4% | `docs/current_bottleneck_implications.md`, `docs/fpga_decode_accel_model_summary.md` |
| decode traced phase time | 81.1% | `docs/current_bottleneck_implications.md`, `docs/fpga_decode_accel_model_summary.md` |

MatMul 내부를 node name/path 기반으로 분류한 결과는 표 4와 같다.

표 4. MatMul category별 누적 시간과 비중

| MatMul category | 전체 MatMul 시간 비중 | 누적 시간 | 출처 |
| --- | ---: | ---: | --- |
| `mlp_projection` | 61.09% | 23163.290 ms | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `lm_head` | 27.81% | 10546.540 ms | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `attention_qkv_projection` | 4.91% | 1861.004 ms | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `attention_output_projection` | 3.54% | 1343.254 ms | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `attention_v_weighted_sum` | 2.64% | 1001.248 ms | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `mlp_projection + lm_head` | 88.90% | 33709.830 ms | `paper_assets/tables/ort_matmul_category_by_context.csv`, `docs/ort_matmul_hotspot_analysis.md` |

#### 해석

표 3은 현재 ONNX Runtime profiling에서 MatMul 중심 dense linear algebra가 주요 runtime hotspot임을 보여준다. 특히 decode 단계에서 MatMul 비중이 81.1%로 나타났기 때문에, token 단위 반복 실행에서 dense projection workload가 중요한 설계 대상임을 알 수 있다.

표 4는 MatMul 내부에서도 MLP projection과 vocabulary projection인 `lm_head`가 대부분을 차지함을 보여준다. 따라서 FPGA 설계 방향은 QK dot-product 하나로 축소하기보다, 반복적인 dense projection workload를 처리하는 tiled MatVec/MatMul datapath로 확장하는 것이 더 타당하다.

`attention_qk_score`가 MatMul category에서 0.00%로 나타난 것은 QK 연산이 존재하지 않는다는 뜻이 아니다. 현재 분류는 node name/path와 output shape로 보수적으로 확정할 수 있는 MatMul만 분류했기 때문에, ORT optimization이나 fused kernel로 표현된 경우에는 별도 category로 잡히지 않을 수 있다. 따라서 안전한 해석은 “현재 MatMul hotspot으로 확인되는 큰 덩어리는 QK score가 아니라 MLP/lm_head 쪽”이라는 것이다.

### FPGA 가속 대상 Primitive 선정

초기 FPGA primitive로 INT8 QK dot-product를 검증하는 접근은 decode attention의 한 구성 요소를 확인한다는 점에서 의미가 있다. 그러나 최신 ORT profiling 결과는 전체 병목을 QK 단일 연산으로 설명하기 어렵다는 것을 보여준다. 이에 따라 본 연구의 1차 최적화 방향은 MLP projection, `lm_head`, attention QKV projection, attention output projection에 공통으로 나타나는 dense MatVec/MatMul 구조로 조정한다.

성능/대역폭 모델은 `paper_assets/tables/fpga_decode_accel_candidate_ops.csv`, `paper_assets/tables/fpga_decode_accel_roofline_estimate.csv`, `paper_assets/tables/fpga_decode_accel_priority.csv`에 정리하였다. 해당 모델은 실제 FPGA speedup을 예측하거나 보장하지 않는다. 이는 profiling-derived design estimate이며, 특히 `lm_head`는 large vocabulary projection 때문에 tiled weight streaming과 output handling이 필수적이라는 설계 함의를 제공한다.

### INT8 Decode MatVec Primitive 검증

FPGA primitive 확장은 기존 QK dot-product를 제거하지 않고, 별도의 INT8 Decode MatVec primitive를 추가하는 방식으로 수행하였다. SpinalHDL 구현은 `inputDim=16`, `outputDim=4`, sequential `tileDim=1` mode, INT8 activation vector, INT8 weight tile matrix, INT32 accumulation을 사용한다. Simulation은 deterministic activation/weight vector를 입력으로 하며, software reference와 RTL simulation output을 비교한다.

#### 결과

Simulation 결과는 `paper_assets/tables/decode_matvec_int8_sim.csv`와 `fpga_test/captured/decode_matvec_int8_sim.csv`에 저장하였다. 기대 output과 관측 output은 표 5와 같이 일치하였다.

표 5. INT8 Decode MatVec RTL simulation 결과

| output index | expected | observed | pass | cycles | 출처 |
| ---: | ---: | ---: | --- | ---: | --- |
| 0 | -271 | -271 | true | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |
| 1 | 239 | 239 | true | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |
| 2 | 287 | 287 | true | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |
| 3 | 797 | 797 | true | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |

#### 해석

표 5는 small fixed-dimension INT8 Decode MatVec primitive가 RTL simulation에서 deterministic software reference와 일치함을 보여준다. 이 결과는 primitive-level functional validation이며, full decode throughput, whole-model acceleration, 또는 ONNX Runtime speedup을 의미하지 않는다.

### Quartus 합성과 DE10-Lite Programming Evidence

DE10-Lite용 demo top은 `DecodeMatVecDemoTop`으로 구성하였다. `SW[2:1]`은 output index를 선택하고, `HEX3..HEX0`은 선택된 accumulator의 lower 16-bit를 표시하도록 설계하였다.

#### 결과

Quartus compile resource 결과는 표 6과 같다.

표 6. Decode MatVec demo Quartus resource 요약

| 항목 | 사용량 | 전체 | 비중 | 출처 |
| --- | ---: | ---: | ---: | --- |
| Total logic elements | 239 | 49,760 | <1% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Dedicated logic registers | 115 | 49,760 | <1% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Embedded Multiplier 9-bit elements | 1 | 288 | <1% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Total memory bits | 0 | 1,677,312 | 0% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |

Timing 및 board programming 결과는 표 7과 같다.

표 7. Decode MatVec demo timing 및 board programming 요약

| 항목 | 값 | 출처 |
| --- | --- | --- |
| Slow 1200mV 85C setup slack | 7.316 ns | `paper_assets/tables/decode_matvec_fpga_timing.csv` |
| Slow 1200mV 85C hold slack | 0.347 ns | `paper_assets/tables/decode_matvec_fpga_timing.csv` |
| Programming tool | Quartus Prime Programmer 25.1std.0 | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Programming cable | USB-Blaster [USB-0] | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Programming file | `de10_lite_decode_matvec.sof` | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Target device | `10M50DAF484` | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Programming status | configuration succeeded, 0 errors, 0 warnings | `paper_assets/tables/decode_matvec_board_validation.csv` |

#### 해석

표 6은 small Decode MatVec demo가 DE10-Lite resource budget 내에서 합성 가능한 규모임을 보여준다. 표 7은 50 MHz `CLOCK_50` 기준 timing summary와 Windows Programmer configuration 성공을 기록한다.

이 evidence는 DE10-Lite가 small fixed-dimension INT8 Decode MatVec primitive bitstream으로 성공적으로 configuration되었다는 의미에 한정된다. 이는 Gemma 3 1B 전체 실행, full sLLM inference, full KV-cache management, 또는 ONNX Runtime end-to-end speedup을 의미하지 않는다. 또한 screenshot은 bitstream programming 성공을 보여주지만, accumulator의 board numeric output은 별도의 `HEX3..HEX0` 또는 `LEDR` 관측으로 기록해야 한다.

### FPGA 기반 Decode 가속기 구조

Profiling 결과를 반영한 FPGA Decode 가속기 구조는 다음 구성 요소를 포함한다.

1. Host/ORT interface: ORT graph profiling과 operator selection 결과를 바탕으로 hardware offload 후보를 전달한다.
2. Activation buffer: decode token activation vector 또는 작은 prefill tile을 저장한다.
3. Weight tile streamer: MLP projection, attention projection, `lm_head` weight tile을 INT8 stream 형태로 공급한다.
4. INT8 tiled MatVec engine: input tile과 output tile을 순차 또는 병렬 구조로 처리하고 INT32 accumulator로 누산한다.
5. Scale/requant unit: future integrated path에서 INT32 accumulator를 downstream low-precision format으로 변환한다.
6. Optional element-wise/fusion unit: bias, activation, residual, approximation 등을 profiling evidence가 있을 때만 통합한다.
7. Optional cache-aware interface: KV-cache layout, stream/buffer interface, past/present update를 다루되, 현재 primitive가 KV-cache를 구현한다고 주장하지 않는다.

이 구조는 현재 FPGA 구현이 완성되었다는 의미가 아니라, ONNX Runtime bottleneck evidence에 기반한 future accelerator architecture sketch이다.

### 실험 결과 분석

#### 결과 요약

현재 결과를 종합하면 ONNX Runtime 기반 Gemma 3 1B 실행에서 MatMul 중심 dense linear algebra가 가장 큰 traced runtime hotspot으로 나타났다. Decode 단계의 MatMul share는 81.1%였으며, MatMul 내부에서는 MLP projection과 `lm_head`가 대부분을 차지했다. FPGA 측면에서는 INT8 Decode MatVec primitive가 RTL simulation에서 software reference와 일치했고, Quartus compile 및 Windows Programmer log를 통해 DE10-Lite bitstream configuration이 가능함을 확인하였다.

#### 해석

이 결과는 ONNX Runtime profiling을 통해 dense projection 중심 bottleneck을 확인하고, 그에 대응하는 작은 INT8 Decode MatVec primitive를 FPGA toolchain과 board programming 수준에서 검증했다는 범위에서 해석해야 한다. KV-cache는 cache I/O와 long-context memory pressure 측면에서 중요한 구조적 요인이지만, 현 결과만으로 유일한 병목이라고 단정할 수 없다. 또한 FPGA 결과는 primitive-level validation이며, full Gemma 3 1B 실행이나 end-to-end ONNX Runtime acceleration evidence가 아니다.

## 결론

### 연구 결과 요약

본 연구는 ONNX Runtime 기반 온디바이스 sLLM 추론의 병목을 export, graph inspection, runtime profiling, host-side baseline, FPGA primitive validation으로 구분하여 분석하였다. 최신 ORT profiling에서는 MatMul이 traced phase time의 67.5%, decode traced time의 81.1%를 차지했으며, MatMul 내부에서는 `mlp_projection + lm_head`가 88.90%를 차지하였다. 이 결과는 병목을 KV-cache 단일 요소 또는 QK dot-product 단일 primitive로 축소하는 해석이 부적절함을 보여준다.

### FPGA 이종 가속 구조의 가능성

FPGA는 전체 sLLM 실행 장치가 아니라, profiling으로 도출된 연산 primitive를 검증하는 하드웨어 계층으로 사용되었다. INT8 Decode MatVec primitive는 simulation에서 software reference와 일치했고, DE10-Lite bitstream은 Windows Quartus Programmer에서 성공적으로 configuration되었다. 이 결과는 향후 FPGA Decode accelerator가 dense projection workload를 tiled MatVec/MatMul 방식으로 다루는 방향을 검토할 수 있다는 초기 feasibility evidence로 해석할 수 있다.

### 연구의 한계

본 연구의 한계는 evidence layer별로 구분하여 해석해야 한다.

첫째, ONNX Runtime profiling 결과는 `CPUExecutionProvider` 기반의 제한된 context length 및 decode step sweep에서 얻은 host-side runtime evidence이다. 따라서 이 결과는 현재 실험 조건에서의 병목 분석으로 해석해야 하며, 다른 execution provider, 다른 quantization 설정, 다른 graph optimization 수준, 또는 다른 hardware target에서 동일한 비중이 유지된다고 일반화할 수 없다.

둘째, MatMul category 분석은 ONNX graph node name/path와 profile event를 기반으로 한 보수적 분류이다. Graph optimization 또는 fused kernel 때문에 attention QK score가 다른 형태로 나타날 수 있으며, `attention_qk_score` category의 0.00%는 QK 연산 부재를 의미하지 않는다. 이 값은 현재 분류 규칙으로 확정 가능한 profile event가 없었다는 뜻으로 제한해서 해석해야 한다.

셋째, PyTorch host-side sweep은 ONNX Runtime profiling 결과가 아니라 reference baseline이다. PyTorch 실행에서 관측된 latency 또는 process RSS 변화는 ONNX Runtime graph execution, ORT memory planner, cache I/O behavior를 직접 대체하는 증거로 사용하지 않는다.

넷째, FPGA 결과는 primitive-level validation이다. 본 연구는 FPGA가 Gemma 3 1B를 실행했다거나 ONNX Runtime 대비 speedup을 달성했다고 주장하지 않는다. 현재 FPGA 구현은 full KV-cache storage, movement, management를 포함하지 않으며, `lm_head` 전체 vocabulary projection이나 full transformer block을 구현하지 않는다.

다섯째, DE10-Lite board programming screenshot은 `de10_lite_decode_matvec.sof` bitstream configuration 성공을 의미한다. 이 증거는 Windows Quartus Programmer가 target device를 성공적으로 configuration했음을 보여주지만, accumulator numeric output의 board-level 관측은 별도의 `HEX3..HEX0` 또는 `LEDR` evidence로 기록되어야 한다. 따라서 board programming success만으로 MatVec board-output validation 또는 end-to-end inference correctness를 주장하지 않는다.

마지막으로, 성능/대역폭 모델은 design estimate이다. `paper_assets/tables/fpga_decode_accel_roofline_estimate.csv`의 compute-bound 또는 bandwidth-bound 판단은 architecture exploration을 위한 추정이며, 실제 FPGA speedup, ONNX Runtime custom operator 성능, 또는 system-level latency reduction을 측정한 결과가 아니다.

### 후속 연구 방향

후속 연구에서는 ORT graph rewrite 또는 custom operator interface를 통해 dense projection offload boundary를 구체화하고, `lm_head`의 large vocabulary projection을 위한 weight streaming, tiling, top-k 또는 output reduction 전략을 검토해야 한다. 또한 cache-aware interface, static shape specialization, operator fusion, scale/requant stage, V weighted sum 및 softmax approximation을 포함하는 더 넓은 decode accelerator architecture를 단계적으로 검증할 필요가 있다.
