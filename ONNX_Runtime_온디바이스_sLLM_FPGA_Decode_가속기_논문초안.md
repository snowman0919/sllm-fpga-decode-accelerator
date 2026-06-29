# ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계

**Bottleneck Analysis of ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator Architecture**

## 저자 정보

최윤혁  
ORCID: [0009-0006-3537-0249](https://orcid.org/0009-0006-3537-0249)  
한국디지털미디어고등학교  

Yunhyuk Choi  
Korea Digital Media High School

## 국문 초록

온디바이스 환경에서 소형 언어모델은 클라우드 의존성을 줄이고 개인정보 보호와 저지연 응답을 제공할 수 있다.
그러나 0.xB~1B급 sLLM이라도 ONNX Runtime 기반 추론에서는 모델 내보내기, 그래프 구조, 런타임 실행, 메모리 압력, prefill/decode 단계의 상호작용에 따라 병목 위치가 달라질 수 있다.
본 연구는 Gemma 3 1B의 ONNX export 및 graph inspection, ONNX Runtime CPUExecutionProvider profiling, PyTorch 호스트 측 reference baseline, FPGA primitive-level validation을 결합하여 병목을 증거 기반으로 분석하였다.
ONNX Runtime profiling 결과, MatMul은 prefill과 decode를 합산한 traced phase time의 67.5%를 차지했으며, decode 단계에서는 81.1%, prefill 단계에서는 53.4%로 나타났다.
또한 MatMul category 분석에서 `mlp_projection`과 `lm_head`는 전체 MatMul 시간의 88.90%를 차지하였다.
이 결과는 병목을 KV-cache 또는 QK dot-product 하나로 축소하기 어렵다는 점을 보여준다.
이에 따라 본 연구는 FPGA 설계 방향을 MatMul-free 모델 구현이나 QK 전용 가속기가 아니라, MLP projection과 `lm_head`를 포함하는 decode-stage dense tiled MatVec/MatMul 구조로 설정하였다.
하드웨어 결과는 DE10-Lite에서 small fixed-dimension INT8 Decode MatVec primitive bitstream을 configuration한 primitive-level 검증으로 제한하며, full sLLM 실행 또는 end-to-end ONNX Runtime 성능 개선으로 해석하지 않는다.

**국문 키워드:** ONNX Runtime, 온디바이스 추론, 소형 언어모델, prefill, decode, MatMul, MatVec, FPGA, DE10-Lite, primitive validation

## English Abstract

On-device small language models can reduce cloud dependency while improving privacy and response latency. However, even 0.xB- to 1B-class sLLMs may exhibit bottlenecks at different layers of an ONNX Runtime deployment, including model export, graph structure, runtime execution, memory pressure, prefill, decode, and interactions among these factors. This study combines Gemma 3 1B ONNX export and graph inspection, ONNX Runtime CPUExecutionProvider profiling, PyTorch host-side reference baselines, and primitive-level FPGA validation. In the ONNX Runtime profile, MatMul accounts for 67.5% of traced prefill-plus-decode phase time, 81.1% of decode traced time, and 53.4% of prefill traced time. Within MatMul time, `mlp_projection` and `lm_head` together account for 88.90%. These results indicate that the observed bottleneck should not be reduced to KV-cache or QK dot-product alone. Accordingly, the FPGA direction in this work is not a MatMul-free model implementation or a QK-only accelerator, but a decode-stage dense tiled MatVec/MatMul architecture for projection-heavy workloads such as MLP projection and `lm_head`. The hardware evidence is limited to primitive-level validation through configuration of a small fixed-dimension INT8 Decode MatVec bitstream on DE10-Lite. It is not interpreted as full sLLM execution or end-to-end ONNX Runtime acceleration.

**English Keywords:** ONNX Runtime, on-device inference, small language model, prefill, decode, MatMul, MatVec, FPGA, DE10-Lite, primitive validation

## 1. 서론

### 1.1 연구 배경

최근 언어모델은 클라우드 기반 대규모 추론뿐 아니라 모바일, 임베디드 보드, 개인용 PC와 같은 온디바이스 환경으로 확장되고 있다. 온디바이스 sLLM은 네트워크 지연을 줄이고, 민감한 입력 데이터를 외부 서버로 전송하지 않으며, 제한된 환경에서도 AI 기능을 제공할 수 있다는 장점이 있다. 그러나 온디바이스 환경은 메모리 용량, 메모리 대역폭, 전력, 연산 자원이 모두 제한되므로 1B급 소형 언어모델에서도 실제 추론 병목은 단순하지 않다.

본 연구는 ONNX Runtime 기반 온디바이스 sLLM 추론을 연구 대상으로 삼는다. ONNX Runtime은 다양한 execution provider와 graph optimization을 제공하므로 배포 계층의 공통 기반으로 사용할 수 있다. 동시에 Hugging Face 모델을 ONNX로 export하는 과정, export된 graph의 input/output 구조, cache I/O 제공 여부, runtime provider 선택에 따라 병목이 다르게 나타날 수 있다.

### 1.2 온디바이스 sLLM 추론의 병목 문제

Autoregressive language model inference는 prompt 전체를 처리하는 prefill과 token을 순차적으로 생성하는 decode로 나뉜다. Prefill은 긴 sequence를 한 번에 처리하므로 sequence-length-sensitive 연산과 dense projection이 함께 커진다. Decode는 token 단위 반복과 cache 참조가 중요하며, interactive generation에서는 token당 latency가 사용자 경험에 직접적인 영향을 준다.

일반적으로 long-context decode에서는 KV-cache가 중요한 구조적 요인으로 작동한다. 그러나 cache I/O가 존재한다는 사실만으로 전체 병목을 KV-cache만으로 설명할 수는 없다. 실제 병목은 ONNX graph 구조, provider 실행 방식, operator별 traced time, tensor shape manipulation, memory movement를 함께 검토해야 한다.

### 1.3 ONNX Runtime 기반 분석의 필요성

PyTorch 또는 Transformers 기반 실행은 모델 동작을 이해하는 데 유용하지만, ONNX Runtime 배포 계층의 graph execution 특성을 직접 대체하지 않는다. Raw Hugging Face `safetensors` directory는 ONNX Runtime에서 직접 실행되지 않으므로 export, graph inspection, profiling을 단계적으로 분리해야 한다. 특히 `past_key_values`와 `present` 계열 cache interface가 graph에 노출되는지 확인해야 decode cache reuse profiling이 가능하다.

따라서 본 연구는 ONNX export와 graph inspection을 먼저 수행하고, 그 결과를 기반으로 ONNX Runtime CPUExecutionProvider profiling을 수행하였다. PyTorch sweep은 host-side reference baseline으로만 사용하며, ONNX Runtime 결과와 동일한 evidence layer로 취급하지 않는다.

### 1.4 연구 목표와 기여

본 연구의 목표는 ONNX Runtime 기반 온디바이스 sLLM 추론에서 병목이 어디에 나타나는지 확인하고, 그 결과를 바탕으로 과장 없는 FPGA Decode 가속기 구조의 1차 방향을 제시하는 것이다. 주요 기여는 다음과 같다.

1. ONNX export, graph inspection, runtime profiling, PyTorch 호스트 측 reference baseline, FPGA primitive validation을 구분한 재현 가능한 분석 흐름을 제시한다.
2. ONNX Runtime CPUExecutionProvider profiling에서 MatMul 중심 dense linear algebra가 주요 hotspot임을 보이고, `mlp_projection + lm_head`가 MatMul 시간의 88.90%를 차지함을 정리한다.
3. KV-cache를 long-context decode memory pressure의 대표적 구조 요인으로 다루되, 유일한 병목으로 단정하지 않는다.
4. QK 단일 primitive가 아니라 MLP projection과 `lm_head`를 포함하는 decode-stage tiled MatVec/MatMul 구조를 FPGA 설계 방향으로 제안한다.
5. DE10-Lite에서 small fixed-dimension INT8 Decode MatVec primitive bitstream을 configuration한 board programming evidence를 기록한다.

## 2. 배경 및 관련 연구

### 2.1 Prefill과 Decode

Transformer 기반 causal language model의 추론은 prefill과 decode로 구분된다. Prefill은 입력 prompt 전체에 대해 attention, MLP, normalization, output projection을 수행한다. 이 단계에서는 sequence length에 비례하거나 그 이상으로 증가하는 연산이 나타나며, 긴 context일수록 tensor operation과 memory movement도 함께 커진다.

Decode는 이전 token의 cache를 참조하면서 다음 token을 하나씩 생성한다. Batch와 token dimension은 작아질 수 있지만, layer마다 MLP projection, attention projection, `lm_head` projection이 반복된다. 따라서 decode 병목은 attention score 계산뿐 아니라 반복적인 dense projection과 cache 관련 data movement의 결합으로 해석해야 한다.

### 2.2 KV-cache와 Long-context Memory Pressure

KV-cache는 autoregressive decode에서 이전 token의 key/value tensor를 재사용하기 위한 구조이다. Cache reuse는 매 token마다 과거 sequence를 다시 계산하지 않도록 하지만, context가 길어질수록 cache tensor의 크기, stream, update, concat, shape manipulation이 runtime과 memory pressure를 증가시킬 수 있다.

본 연구에서는 ONNX graph가 52개의 cache input과 52개의 cache output을 노출하며 decode cache reuse가 가능한 interface를 제공함을 확인하였다. 그러나 본 연구는 cache I/O의 존재를 병목의 단일 원인으로 해석하지 않는다. KV-cache는 long-context decode를 설명하는 구조적 요인 중 하나이며, 실제 runtime hotspot은 profiling 결과로 확인해야 한다.

### 2.3 ONNX Runtime과 Graph-based Deployment

ONNX Runtime은 ONNX graph를 다양한 provider에서 실행하기 위한 runtime이다. 이 계층에서는 graph optimization, execution provider, memory planner, operator implementation에 따라 성능 특성이 달라진다. 그러므로 모델 파일의 이론적 연산량만으로 온디바이스 병목을 판단하기 어렵다.

본 연구는 ONNX export 상태, graph input/output, operator histogram, cache interface를 먼저 확인하고, 이후 runtime profiling trace를 분석하였다. 이러한 절차는 PyTorch reference baseline과 ONNX Runtime profiling을 혼동하지 않기 위한 전제이다.

### 2.4 MatMul 중심 LLM 연산 병목

LLM의 attention projection, MLP projection, vocabulary projection은 대부분 dense linear algebra로 표현된다. 본 연구의 ONNX Runtime profiling에서도 MatMul은 prefill과 decode를 합산한 traced phase time의 67.5%를 차지하였다. 특히 decode 단계에서 MatMul 비중은 81.1%로 나타나, token 단위 반복 실행에서 dense projection workload가 중요한 설계 대상임을 보였다.

MatMul 내부를 node name/path 기반으로 분류하면 `mlp_projection`과 `lm_head`가 MatMul 시간의 88.90%를 차지하였다. 이는 attention QK score 하나만을 중심으로 가속기를 설계하는 접근이 현재 profiling evidence와 충분히 맞지 않을 수 있음을 의미한다.

### 2.5 저정밀 및 MatMul-efficient 연구와 본 연구의 차이

BitNet b1.58은 LLM weight를 ternary 값으로 제한하여 저정밀 모델과 전용 하드웨어 가능성을 논의한 관련 연구이다. Scalable MatMul-free Language Modeling은 MatMul 연산을 제거하거나 대체하는 모델 구조를 제안한 관련 연구이다. 이러한 연구는 LLM 효율화 방향을 보여주지만, 본 연구의 구현 방향과는 다르다.

본 연구는 MatMul-free 모델을 새로 학습하거나 Gemma 3 1B의 모델 구조를 MatMul-free 구조로 변경하지 않는다. 또한 BitNet b1.58과 같은 ternary training recipe를 적용하지 않는다. 본 연구는 기존 ONNX Runtime profiling에서 관측된 dense projection 병목을 보존한 채, 그 workload를 저정밀 tiled MatVec/MatMul primitive와 future accelerator architecture로 연결하는 데 초점을 둔다.

## 3. 연구 방법

### 3.1 전체 실험 흐름

본 연구의 실험 흐름은 여섯 evidence layer로 구성된다. 첫째, local Hugging Face Gemma 3 1B model directory를 inspection하여 모델 구성과 cache 관련 기본 정보를 확인하였다. 둘째, ONNX export를 수행하고 export 성공 여부와 산출 파일을 기록하였다. 셋째, export된 ONNX graph의 input/output, cache I/O, operator 구성을 inspection하였다. 넷째, ONNX Runtime CPUExecutionProvider에서 prefill/decode profiling을 수행하였다. 다섯째, PyTorch host-side reference baseline을 별도로 기록하였다. 여섯째, FPGA primitive validation으로 INT8 Decode MatVec primitive의 simulation, Quartus compile, DE10-Lite bitstream configuration evidence를 기록하였다.

이 흐름은 full accelerator 구현을 주장하기 위한 절차가 아니라, ONNX-centered 병목 분석과 primitive-level hardware validation을 구분하기 위한 연구 절차이다.

### 3.2 ONNX Export 및 Graph Inspection

ONNX export는 Gemma 3 1B local model directory에서 수행되었으며, export 결과는 `/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx`로 기록되었다. Graph inspection에서는 graph node 수, MatMul node 수, cache input/output 수, decode cache reuse 가능 여부를 확인하였다. Cache-style interface는 `past_key_values`와 `present` 계열 입출력으로 나타났다.

Graph inspection은 runtime 병목 자체를 증명하지 않는다. 이 단계의 역할은 ONNX Runtime profiling이 어떤 graph interface 위에서 수행되는지를 명확히 하는 것이다.

### 3.3 ORT Profiling Setup

ONNX Runtime profiling은 `CPUExecutionProvider`를 사용하였다. Context length는 128, 512, 1024, 2048로 설정하고, decode steps는 1, 2, 4, 8로 설정하였다. 각 조합은 runs 3, warmup 1 조건으로 수행된 기존 artifact를 사용하였다. 본 논문에서는 새 profiling을 실행하지 않고, `paper_assets/tables/ort_context_sweep_latency.csv`, `paper_assets/tables/ort_operator_share_by_context.csv`, `paper_assets/tables/ort_prefill_decode_comparison.csv`에 저장된 결과를 사용하였다.

본 논문에서 `traced phase time`은 ORT profiling trace에 기록된 해당 prefill 또는 decode phase의 node event duration 합계를 의미하며, wall-clock latency 전체나 profiling되지 않은 host-side overhead를 포함하지 않는다.

### 3.4 MatMul Category Classification 방법

MatMul category 분석은 ORT profile JSON의 `Node` event 중 `op_name == "MatMul"`인 항목을 대상으로 수행되었다. Profile event의 normalized node name을 ONNX graph node name에 우선 매칭하고, graph metadata는 보조 fallback으로만 사용하였다. Category는 node name/path가 명확한 경우에만 부여하였다.

분류 규칙은 다음과 같다. `q_proj`, `k_proj`, `v_proj`는 `attention_qkv_projection`으로 분류하였다. `o_proj`는 `attention_output_projection`으로, `mlp/*_proj`는 `mlp_projection`으로, `lm_head`는 `lm_head`로 분류하였다. Attention 내부 MatMul 중 output shape가 attention score 또는 V weighted sum 형태로 확인되는 경우 각각 `attention_qk_score`, `attention_v_weighted_sum`으로 분류하였다. 확정할 수 없는 항목은 `unknown`으로 남겼다.

### 3.5 FPGA Decode MatVec Primitive 설계 방법

FPGA primitive는 기존 INT8 QK dot-product 검증 흐름을 확장하여, projection workload에 더 가까운 small fixed-dimension INT8 Decode MatVec 구조로 구성하였다. SpinalHDL 구현은 `inputDim=16`, `outputDim=4`, sequential mode, INT8 activation vector, INT8 weight tile matrix, INT32 accumulation을 사용한다. Simulation은 deterministic activation/weight vector를 입력으로 하며, software reference와 RTL output을 비교한다.

DE10-Lite demo top은 선택된 output accumulator의 lower 16-bit를 `HEX3..HEX0`에 표시할 수 있도록 구성하였다. 이 design은 full model integration이 아니라 primitive-level synthesis 및 configuration evidence를 얻기 위한 작은 고정 차원 demo이다.

### 3.6 Evidence Layer 구분

본 연구는 다음 evidence layer를 엄격히 구분한다.

ONNX graph evidence는 export된 model interface와 cache I/O 존재 여부를 설명한다. ORT runtime profiling evidence는 CPUExecutionProvider에서 관측된 prefill/decode runtime hotspot을 설명한다. PyTorch reference evidence는 local `safetensors` 모델의 host-side reference behavior를 보여주지만, ORT profiling 결과로 대체하지 않는다. FPGA primitive evidence는 small INT8 Decode MatVec primitive의 simulation, compile, bitstream configuration을 보여주며, full accelerator 성능을 의미하지 않는다.

## 4. 실험 결과

### 4.1 결과

표 1은 ONNX graph inspection의 핵심 수치를 정리한다.

**표 1. ONNX graph inspection 요약**

| 항목 | 값 | 출처 |
| --- | ---: | --- |
| ONNX graph node 수 | 7837 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| ONNX MatMul node 수 | 237 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| cache input 수 | 52 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| cache output 수 | 52 | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |
| decode cache reuse ready | True | `onnx_profile/results_onnx/raw/onnx_graph_inspection.json` |

표 2는 ONNX Runtime profiling 설정과 산출물을 정리한다.

**표 2. ONNX Runtime profiling 설정 및 산출물**

| 항목 | 설정 또는 산출물 | 출처 |
| --- | --- | --- |
| Runtime provider | ONNX Runtime `CPUExecutionProvider` | `docs/onnx_runtime_sweep_report.md` |
| Context length | 128, 512, 1024, 2048 | `paper_assets/tables/ort_context_sweep_latency.csv` |
| Decode steps | 1, 2, 4, 8 | `paper_assets/tables/ort_context_sweep_latency.csv` |
| Runs / warmup | 3 / 1 | `docs/onnx_runtime_sweep_report.md` |
| Operator share table | operator별 traced node time 비중 | `paper_assets/tables/ort_operator_share_by_context.csv` |
| MatMul category table | MatMul node category별 누적 시간 | `paper_assets/tables/ort_matmul_category_by_context.csv` |

표 3은 MatMul이 traced phase time에서 차지한 비중을 요약한다.

**표 3. ONNX Runtime MatMul phase 비중**

| 측정 범위 | MatMul time | traced phase time | MatMul 비중 | 출처 |
| --- | ---: | ---: | ---: | --- |
| prefill + decode traced phase time | 37.918 s | 56.168 s | 67.5% | `docs/current_bottleneck_implications.md` |
| prefill traced phase time | 14.711 s | 27.539 s | 53.4% | `docs/current_bottleneck_implications.md` |
| decode traced phase time | 23.207 s | 28.629 s | 81.1% | `docs/current_bottleneck_implications.md` |

표 4는 MatMul 내부 category별 누적 시간과 비중을 정리한다.

**표 4. MatMul category별 누적 시간과 비중**

| MatMul category | call count | 누적 시간 | 전체 MatMul 시간 비중 | 출처 |
| --- | ---: | ---: | ---: | --- |
| `mlp_projection` | 14976 | 23163.290 ms | 61.09% | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `lm_head` | 192 | 10546.540 ms | 27.81% | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `attention_qkv_projection` | 14976 | 1861.004 ms | 4.91% | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `attention_output_projection` | 4992 | 1343.254 ms | 3.54% | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `attention_v_weighted_sum` | 4992 | 1001.248 ms | 2.64% | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `unknown` | 384 | 2.787 ms | 0.01% | `paper_assets/tables/ort_matmul_category_by_context.csv` |
| `attention_qk_score` | 0 | 0.000 ms | 0.00% | `docs/ort_matmul_hotspot_analysis.md` |
| `mlp_projection + lm_head` | 15168 | 33709.830 ms | 88.90% | `docs/ort_matmul_hotspot_analysis.md` |

표 5는 INT8 Decode MatVec RTL simulation 결과를 보여준다.

**표 5. INT8 Decode MatVec RTL simulation 결과**

| output index | expected | observed | pass | input dimension | output dimension | cycles | 출처 |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 0 | -271 | -271 | true | 16 | 4 | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |
| 1 | 239 | 239 | true | 16 | 4 | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |
| 2 | 287 | 287 | true | 16 | 4 | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |
| 3 | 797 | 797 | true | 16 | 4 | 65 | `paper_assets/tables/decode_matvec_int8_sim.csv` |

표 6은 Decode MatVec demo의 Quartus resource 결과를 정리한다.

**표 6. Decode MatVec demo Quartus resource 요약**

| 항목 | 사용량 | 전체 | 비중 | 출처 |
| --- | ---: | ---: | ---: | --- |
| Total logic elements | 239 | 49,760 | <1% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Total combinational functions | 222 | 49,760 | <1% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Dedicated logic registers | 115 | 49,760 | <1% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Total pins | 65 | 360 | 18% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Total memory bits | 0 | 1,677,312 | 0% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |
| Embedded Multiplier 9-bit elements | 1 | 288 | <1% | `paper_assets/tables/decode_matvec_fpga_resource.csv` |

표 7은 timing 및 board programming 결과를 함께 요약한다.

**표 7. Decode MatVec demo timing 및 board programming 요약**

| 항목 | 값 | 출처 |
| --- | --- | --- |
| Slow 1200mV 85C setup slack | 7.316 ns | `paper_assets/tables/decode_matvec_fpga_timing.csv` |
| Slow 1200mV 85C hold slack | 0.347 ns | `paper_assets/tables/decode_matvec_fpga_timing.csv` |
| Slow 1200mV 85C minimum pulse width slack | 9.637 ns | `paper_assets/tables/decode_matvec_fpga_timing.csv` |
| Programming tool | Quartus Prime Programmer 25.1std.0 Build 1129 10/21/2025 SC Lite Edition | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Programming cable | USB-Blaster [USB-0] | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Programming file | `de10_lite_decode_matvec.sof` | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Target device | `10M50DAF484` | `paper_assets/tables/decode_matvec_board_validation.csv` |
| Programming status | configuration succeeded, 0 errors, 0 warnings | `paper_assets/tables/decode_matvec_board_validation.csv` |

### 4.2 해석

표 1은 ONNX graph가 cache-style interface를 제공한다는 점을 보여준다. 그러나 cache input/output의 존재는 병목 원인을 직접 증명하지 않는다. 표 2는 profiling 설정이 CPUExecutionProvider에 한정되어 있음을 명확히 한다.

표 3은 현재 ONNX Runtime profiling에서 MatMul 중심 dense linear algebra가 가장 큰 traced runtime hotspot임을 보여준다. Decode 단계에서 MatMul 비중이 81.1%로 높게 나타났기 때문에, token 단위 반복 실행에서 dense projection workload가 중요한 설계 대상이 된다.

표 4는 MatMul 내부에서도 `mlp_projection`과 `lm_head`가 대부분을 차지함을 보여준다. 따라서 FPGA 설계 방향은 QK dot-product 하나로 축소하기보다, 반복적인 dense projection workload를 처리하는 tiled MatVec/MatMul datapath로 확장하는 것이 타당하다. 단, `attention_qk_score`가 0.00%로 나타난 것은 QK 연산이 존재하지 않는다는 뜻이 아니라, 현재 node name/path 기반 분류 규칙으로 확정 가능한 event가 없었다는 뜻으로 제한해서 해석해야 한다.

표 5는 small fixed-dimension INT8 Decode MatVec primitive가 RTL simulation에서 deterministic software reference와 일치함을 보여준다. 표 6은 이 demo가 DE10-Lite resource budget 내에서 합성 가능한 규모임을 보여준다. 표 7은 timing summary와 Windows Quartus Programmer configuration 성공을 기록한다. 이 evidence는 bitstream configuration 성공에 한정되며, accumulator numeric output의 board-level 관측과는 분리된다.

## 5. 논의

### 5.1 병목은 KV-cache만으로 설명되지 않음

ONNX graph는 cache input 52개와 cache output 52개를 제공하므로 KV-cache는 decode profiling에서 중요한 구조적 요소이다. 그러나 현재 runtime profiling에서 가장 큰 traced hotspot은 MatMul이다. 따라서 KV-cache는 long-context memory pressure를 설명하는 대표적 구조 요인이지만, 현재 결과를 모두 설명하는 유일한 원인으로 해석하지 않는다.

### 5.2 Decode에서 MatMul이 지배적인 이유

Decode에서는 token 단위 실행이 반복되며, 각 layer에서 attention projection, MLP projection, output projection이 계속 수행된다. Batch와 token dimension이 작더라도 hidden dimension과 projection dimension은 유지되므로 dense linear algebra의 누적 시간이 크다. 본 연구의 결과에서 decode MatMul 비중이 81.1%로 나타난 것은 이러한 구조와 일치한다.

### 5.3 MLP Projection과 lm_head가 FPGA 설계 방향에 주는 의미

`mlp_projection`은 layer마다 `gate_proj`, `up_proj`, `down_proj` 형태로 반복되며, `lm_head`는 vocabulary projection 때문에 output dimension이 매우 크다. 두 category가 MatMul 시간의 88.90%를 차지한다는 점은 FPGA 설계가 attention QK score만이 아니라 projection-heavy workload를 다루어야 함을 시사한다. 특히 `lm_head`는 weight streaming, tiling, output reduction 또는 top-k 처리 전략과 함께 검토되어야 한다.

### 5.4 QK-only Accelerator가 충분하지 않은 이유

QK dot-product는 decode attention datapath의 핵심 primitive 중 하나이다. 그러나 현재 ONNX Runtime profile에서 큰 비중으로 확인된 MatMul category는 MLP projection과 `lm_head`이다. 따라서 QK-only accelerator는 attention primitive 검증으로는 의미가 있지만, 현재 관측된 projection-heavy bottleneck을 포괄하기에는 충분하지 않다. 본 연구는 QK primitive를 배제하지 않고, tiled MatVec/MatMul datapath의 한 응용 영역으로 포함한다.

### 5.5 Tiled MatVec/MatMul 구조의 타당성

Decode-stage workload는 작은 token dimension과 큰 hidden/output dimension을 갖는 projection을 반복한다. 이 구조는 activation buffer, weight tile streamer, INT8 tiled MatVec engine, INT32 accumulator, scale/requant unit으로 구성된 streaming datapath와 자연스럽게 연결된다. 이러한 구조는 MLP projection, attention projection, `lm_head`에 공통으로 적용 가능한 형태이며, DE10-Lite demo에서는 작은 고정 차원의 primitive로만 검증되었다.

### 5.6 DE10-Lite Primitive Validation의 의미와 한계

DE10-Lite 결과는 small INT8 Decode MatVec primitive의 simulation, compile, bitstream configuration 가능성을 보여준다. 이는 FPGA toolchain과 board programming flow가 primitive 수준에서 작동했음을 의미한다. 그러나 이 결과는 complete model execution, full transformer block implementation, ORT custom operator integration, board numeric output validation을 포함하지 않는다. 따라서 하드웨어 결과는 future architecture sketch의 feasibility evidence로 제한해서 해석한다.

## 6. FPGA Decode 가속기 구조 제안

본 장의 구조는 future accelerator architecture sketch이며, 현재 구현된 full accelerator가 아니다. 제안 구조는 ONNX Runtime profiling에서 확인된 projection-heavy bottleneck을 기준으로 한다.

1. **Host/ORT interface**: ONNX Runtime graph profiling과 operator selection 결과를 바탕으로 offload 후보를 전달한다. Shape, quantization, cache binding 정보는 host side에서 명시적으로 관리한다.
2. **Activation buffer**: Decode token activation vector 또는 작은 prefill tile을 저장하고 MatVec engine에 공급한다.
3. **Weight tile streamer**: MLP projection, attention projection, `lm_head`의 INT8 weight tile을 순차적으로 공급한다. Large vocabulary projection을 갖는 `lm_head`는 bandwidth-sensitive workload로 다룬다.
4. **INT8 tiled MatVec engine**: `inputDim`, `outputDim`, tile dimension에 따라 dot product를 반복 수행한다. MLP projection, `lm_head`, attention QKV projection, attention output projection에 공통으로 적용 가능한 datapath를 목표로 한다.
5. **INT32 accumulator**: INT8 곱셈 결과를 INT32로 누산하여 deterministic primitive validation과 후속 requantization을 지원한다.
6. **Scale/requant unit**: Future integrated path에서 accumulator를 downstream low-precision format으로 변환한다.
7. **Optional element-wise/fusion unit**: Bias, activation, residual, approximation, fusion stage는 profiling과 graph rewrite evidence가 확보될 때 선택적으로 통합한다.
8. **Optional cache-aware interface**: KV-cache layout, past/present update, stream/buffer interface를 다루기 위한 확장 지점이다. 현재 primitive가 full KV-cache management를 구현했다는 의미는 아니다.

이 구조는 MatMul-free 모델을 구현하는 방향이 아니라, 기존 ONNX Runtime profile에서 확인된 dense linear algebra workload를 저정밀 tiled streaming 구조로 다루는 방향이다.

## 7. 한계

첫째, ONNX Runtime profiling 결과는 `CPUExecutionProvider` 기반의 제한된 context length 및 decode step sweep에서 얻은 host-side runtime evidence이다. 다른 execution provider, quantization 설정, graph optimization 수준, hardware target에서 동일한 비중이 유지된다고 일반화할 수 없다.

둘째, context sweep은 synthetic prompt와 제한된 run count에 기반한다. 따라서 latency variance, prompt content, batch size, provider scheduling, memory planner behavior에 대한 추가 검증이 필요하다. 본 논문에서는 기존 artifact의 수치만 사용하고 새 sweep을 수행하지 않았다.

셋째, MatMul category 분석은 node name/path와 profile event를 기반으로 한 보수적 분류이다. Graph optimization 또는 fused kernel 때문에 QK score가 다른 형태로 나타날 수 있으며, `attention_qk_score` category의 0.00%는 QK 연산 부재를 의미하지 않는다.

넷째, PyTorch host-side sweep은 ONNX Runtime profiling 결과가 아니라 reference baseline이다. PyTorch 실행에서 관측된 latency 또는 process RSS 변화는 ONNX Runtime graph execution, ORT memory planner, cache I/O behavior를 직접 대체하는 증거로 사용하지 않는다.

다섯째, FPGA 결과는 primitive-level validation이다. 현재 구현은 full KV-cache storage, movement, management를 포함하지 않으며, `lm_head` 전체 vocabulary projection이나 full transformer block을 구현하지 않는다.

여섯째, DE10-Lite board programming screenshot은 `de10_lite_decode_matvec.sof` bitstream configuration 성공을 의미한다. 이 증거는 target device configuration을 보여주지만, accumulator numeric output의 board-level 관측은 별도의 `HEX3..HEX0` 또는 `LEDR` evidence로 기록되어야 한다. 따라서 board programming success만으로 MatVec board-output validation 또는 inference correctness를 주장하지 않는다.

마지막으로, 성능/대역폭 모델은 design estimate이다. `paper_assets/tables/fpga_decode_accel_roofline_estimate.csv`의 compute-bound 또는 bandwidth-bound 판단은 architecture exploration을 위한 추정이며, 실제 custom operator 성능 또는 system-level latency reduction을 측정한 결과가 아니다.

## 8. 결론

본 연구는 ONNX Runtime 기반 온디바이스 sLLM 추론의 병목을 export, graph inspection, runtime profiling, host-side reference baseline, FPGA primitive validation으로 구분하여 분석하였다. ONNX Runtime CPUExecutionProvider profiling에서는 MatMul이 prefill과 decode를 합산한 traced phase time의 67.5%를 차지했고, decode 단계에서는 81.1%, prefill 단계에서는 53.4%를 차지하였다. MatMul 내부에서는 `mlp_projection + lm_head`가 88.90%를 차지하였다.

이 결과는 병목을 KV-cache 또는 QK dot-product 하나로 축소하는 해석이 부적절함을 보여준다. KV-cache는 long-context decode memory pressure의 중요한 구조적 요인이지만, 현재 profiling evidence에서 가장 큰 runtime hotspot은 dense projection 중심 MatMul workload이다.

FPGA 측면에서는 INT8 Decode MatVec primitive가 RTL simulation에서 software reference와 일치했고, Quartus resource/timing artifact와 Windows Programmer log를 통해 small fixed-dimension bitstream configuration이 가능함을 확인하였다. 이 evidence는 primitive-level validation으로 제한된다. 향후 연구에서는 Host/ORT interface, activation buffer, weight tile streamer, INT8 tiled MatVec engine, INT32 accumulator, scale/requant unit, optional fusion unit, optional cache-aware interface를 포함하는 decode accelerator architecture를 단계적으로 검증해야 한다. 본 연구의 의의는 ONNX Runtime 병목 분석과 FPGA primitive 검증을 하나의 제한된 증거 연결 구조로 정리하여, 후속 하드웨어 설계가 측정된 병목에서 출발하도록 한 데 있다.

## 참고문헌

[1] Shuming Ma, Hongyu Wang, Lingxiao Ma, Lei Wang, Wenhui Wang, Shaohan Huang, Li Dong, Ruiping Wang, Jilong Xue, and Furu Wei. "The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits." arXiv preprint arXiv:2402.17764, 2024.

[2] Rui-Jie Zhu, Yu Zhang, Steven Abreu, Ethan Sifferman, Tyler Sheaves, Yiqiao Wang, Dustin Richmond, Sumit Bam Shrestha, Peng Zhou, and Jason K. Eshraghian. "Scalable MatMul-free Language Modeling." arXiv preprint arXiv:2406.02528, 2024.

## 부록 A. Artifact Inventory

주요 문서:

```text
AGENTS.md
README.md
docs/paper_outline.md
docs/current_bottleneck_implications.md
docs/onnx_runtime_sweep_report.md
docs/ort_matmul_hotspot_analysis.md
docs/fpga_decode_accelerator_optimization_plan.md
docs/fpga_decode_accel_model_summary.md
fpga_test/captured/decode_matvec_board_validation.md
```

주요 CSV:

```text
paper_assets/tables/onnx_export_status.csv
paper_assets/tables/onnx_graph_io_summary.csv
paper_assets/tables/model_summary.csv
paper_assets/tables/ort_context_sweep_latency.csv
paper_assets/tables/ort_operator_share_by_context.csv
paper_assets/tables/ort_prefill_decode_comparison.csv
paper_assets/tables/ort_matmul_category_by_context.csv
paper_assets/tables/ort_matmul_top_nodes.csv
paper_assets/tables/fpga_decode_accel_candidate_ops.csv
paper_assets/tables/fpga_decode_accel_roofline_estimate.csv
paper_assets/tables/fpga_decode_accel_priority.csv
paper_assets/tables/decode_matvec_int8_sim.csv
paper_assets/tables/decode_matvec_fpga_resource.csv
paper_assets/tables/decode_matvec_fpga_timing.csv
paper_assets/tables/decode_matvec_board_validation.csv
```

Raw ORT profile 및 inspection artifact:

```text
onnx_profile/results_onnx/raw/onnx_graph_inspection.json
onnx_profile/results_onnx/raw/model_inspection.json
onnx_profile/results_onnx_sweep/raw/ort_sweep_raw_runs.json
onnx_profile/results_onnx_sweep/raw/ort_sweep_status.json
```

FPGA captured 및 Quartus output:

```text
fpga_test/captured/decode_matvec_int8_sim.csv
fpga_test/captured/decode_matvec_board_validation.md
quartus/de10_lite_decode_matvec/output_files/de10_lite_decode_matvec.sof
quartus/de10_lite_decode_matvec/output_files/de10_lite_decode_matvec.fit.summary
quartus/de10_lite_decode_matvec/output_files/de10_lite_decode_matvec.sta.summary
```

## 부록 B. Reproducibility Commands

다음 명령은 repository에 기록된 기존 흐름을 재현하기 위한 command inventory이다. 본 초안 작성 과정에서는 새 실험, 재컴파일, 보드 프로그래밍을 수행하지 않았다.

```bash
nix develop -c just hf-inspect model_dir=/home/monad/develop/ai_accel/gemma3-1B
nix develop -c just gemma-onnx-export model_dir=/home/monad/develop/ai_accel/gemma3-1B
nix develop -c just onnx-inspect model=/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx
nix develop -c just ort-sweep
nix develop -c just ort-sweep-report
nix develop -c just ort-matmul-analysis
nix develop -c just torch-context-sweep model_dir=/home/monad/develop/ai_accel/gemma3-1B
nix develop -c just decode-accel-model
nix develop -c just decode-matvec-sim
nix develop -c just spinal-generate
nix develop -c just decode-matvec-quartus
```

Windows board programming command:

```powershell
quartus_pgm.exe -m jtag -c "USB-Blaster" -o "p;.\de10_lite_decode_matvec.sof"
```

## 부록 C. Claim Boundary Checklist

| 항목 | 본 초안의 처리 |
| --- | --- |
| full Gemma FPGA execution | not claimed |
| end-to-end ORT speedup | not claimed |
| KV-cache-only bottleneck | not claimed |
| board numeric output validation | not yet claimed |
| PyTorch baseline as ORT profiling | not claimed |
| roofline/model estimate as measured result | not claimed |
| MatMul-free model as implementation direction | not claimed |
| QK-only accelerator as complete solution | not claimed |
