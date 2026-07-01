# 최종 원고 Outline

## 제목

온디바이스 ONNX Runtime sLLM 추론의 Decode 병목 분석과 FPGA 기반 INT8 MatVec 가속기 구조 제안

## 영문 제목

Decode Bottleneck Analysis of On-device ONNX Runtime sLLM Inference and an FPGA-based INT8 MatVec Accelerator Architecture Proposal

## 초록 초안

온디바이스 sLLM 추론에서는 모델 크기뿐 아니라 runtime graph, execution provider, quantization state, decode cache 처리 방식이 token latency를 결정한다. 본 연구는 Snapdragon 8+ Gen 1 기반 Lenovo Y700에서 ONNX Runtime 기반 sLLM 또는 대표 decode micrograph를 실행해 온디바이스 decode 병목을 측정하고, 해당 병목이 FPGA INT8 MatVec/MatMul 구조로 옮겨질 때 필요한 tiling, memory bandwidth, host/offload interface 조건을 분석한다. 또한 DE10-Lite에서 INT8 MatVec core의 RTL simulation, clean rebuild, JTAG-to-Avalon correctness, internal cycle counter 측정을 수행하여 fixed 16x4 primitive가 CPU reference와 동일한 결과를 반환하고 65 compute cycles로 완료됨을 확인한다. 본 결과는 full Gemma FPGA 실행이나 ONNX Runtime end-to-end speedup이 아니라, ONNX Runtime 병목 분석에서 도출된 projection-heavy primitive를 FPGA tiled datapath 구조 요구사항으로 연결한 분석 및 core-level validation이다.

## 핵심 기여

1. Snapdragon 8+ Gen 1 기반 Lenovo Y700에서 ONNX Runtime CPU/가능한 EP 경로와 대표 decode workload를 측정해 온디바이스 decode 병목을 분석한다.
2. ONNX graph/operator profiling 결과를 Gemma 계열 projection shape, arithmetic intensity, bandwidth, tile reuse, interface overhead와 연결하여 FPGA offload 조건을 정량화한다.
3. DE10-Lite에서 INT8 MatVec core의 correctness와 internal cycle counter를 board-level로 확인하고, 이를 full accelerator가 아니라 tiled INT8 MatVec 구조 제안의 검증 anchor로 제시한다.

## 1. 서론

- 온디바이스 sLLM 배포에서 decode token latency가 중요한 이유.
- ONNX Runtime 배포 계층에서는 모델 연산량뿐 아니라 graph optimization, EP, quantization, cache tensor handling이 병목을 바꾼다는 문제 제기.
- 본 연구의 질문:
  - Y700급 Android 장치에서 ORT decode 병목은 무엇인가?
  - optimized/quantized/MatMulInteger 경로에서도 projection-heavy primitive가 남는가?
  - FPGA로 옮기려면 compute lane보다 어떤 memory/interface 조건이 필요한가?
- 기여 3개.

## 2. 관련 연구 및 배경

- sLLM decode: prefill/decode, KV-cache, projection 반복.
- ONNX Runtime: graph optimization, CPU/NNAPI/QNN EP, quantized graph.
- LLM serving/cache: vLLM/PagedAttention, Orca 등.
- FPGA LLM accelerator: FTRANS, DFX, FlightLLM 등.
- 본 연구 위치:
  - full model mapping이 아니라 ONNX Runtime profiling에서 offload boundary를 도출하는 연구.
  - QK-only가 아니라 projection-general INT8 MatVec/MatMul 구조 요구사항 제안.

## 3. 실험 방법

### 3.1 Lenovo Y700 Android 환경

- 장치 정보, SoC, RAM, Android version, thermal/memory state.
- ADB 기반 실행 경로.

### 3.2 ONNX Runtime 실행 경로

- CPU EP baseline.
- NNAPI EP 시도 및 결과.
- QNN EP 시도 및 결과.
- 실패한 backend는 integration blocked 또는 attempted but not used로 기록.

### 3.3 모델 및 micrograph

- Gemma 3 1B full/partial ONNX 가능 여부.
- optimized ONNX.
- quantized/QDQ 또는 MatMulInteger graph.
- projection-heavy synthetic micrograph:
  - MLP-like 1152 -> 6912
  - lm_head-like tile
  - attention output projection-like

### 3.4 FPGA 검증 계층

- fixed 16x4 INT8 MatVec primitive.
- parameterized/tiled config simulation/synthesis sweep.
- evidence type 정의:
  - measured
  - board_measured
  - simulation
  - projected
  - invocation_overhead

## 4. 온디바이스 ONNX Runtime 병목 분석

- Y700 wall-clock baseline.
- EP별 성공/실패.
- optimized/quantized/MatMulInteger 결과.
- operator 또는 micrograph latency summary.
- 기존 Ryzen 결과는 비교/보조로만 배치.
- 해석:
  - projection-heavy primitive가 남는지.
  - MatMul보다 cache/shape overhead가 커질 경우 FPGA offload boundary를 어떻게 바꿔야 하는지.

## 5. FPGA 기반 INT8 MatVec 가속기 구조 제안

- profiling 결과에서 구조 요구사항으로 연결:
  - projection-general datapath
  - activation reuse
  - weight tile streaming
  - INT32 accumulation
  - output tiling/top-k 또는 host reduction
  - cache-aware host interface
- Gemma projection shape tile mapping:
  - hidden size 1152
  - MLP projection
  - lm_head tile
  - attention output projection
- 구조 그림: Host/ORT boundary, activation buffer, weight tile streamer, MAC lanes, accumulator, output tile buffer.

## 6. FPGA 구현 및 검증 결과

- RTL simulation 결과.
- DE10-Lite clean rebuild resource/timing.
- Board validation:
  - pass_count=20/fail_count=0
  - reference/result 일치
  - COMPUTE_CYCLES=65
  - compute time 1.3 us @ 50 MHz
- JTAG total latency는 correctness/debug invocation overhead로만 표기.
- parameterized/multi-lane/tiled sweep 결과:
  - 성공 config
  - 실패 config
  - resource/timing 한계
- 16x4 latency 우열 비교는 하지 않는다.

## 7. Offload interface 및 bandwidth/roofline 분석

- projection별 MAC count, weight bytes, activation bytes, output bytes.
- arithmetic intensity.
- compute time model.
- stream time model.
- DE10-Lite 한계:
  - DSP, memory bits, external bandwidth/interface 부재.
- 실용 interface 조건:
  - JTAG: correctness/debug
  - USB serial: correctness only
  - USB3/FT600-class streaming: prototype 후보
  - Ethernet/UDP: external prototype 후보
  - AXI DMA/shared memory: KR260/Zynq future path
- 결론:
  - 실제 projection-scale acceleration은 compute lane 수보다 bandwidth와 invocation path가 지배한다.

## 8. 논의 및 결론

- Y700 실험의 의미와 한계.
- QNN/NNAPI 성공/실패가 뜻하는 것.
- FPGA 구조 제안의 범위.
- DE10-Lite와 KR260/RMA 이후 확장 방향.
- 금지 claim 재확인 없이 간결한 claim boundary:
  - 본 연구는 full system acceleration이 아니라 병목 분석과 구조 조건 도출이다.
- 최종 결론:
  - 온디바이스 ORT decode 병목에서 projection-heavy primitive를 확인/검토했다.
  - FPGA 구조는 tiled INT8 MatVec/MatMul과 memory/interface co-design을 요구한다.
  - DE10-Lite는 core validation anchor이며, 실용 offload는 상위 interface와 memory system이 필요하다.

## 최종 표

1. 실험 환경
2. Lenovo Y700 ONNX Runtime baseline
3. ONNX graph/operator 또는 micrograph 병목 요약
4. FPGA tiled accelerator design space/resource summary
5. DE10-Lite board validation summary
6. Offload interface/bandwidth 해석

## 최종 그림

1. 전체 연구 흐름
2. Y700 ONNX Runtime 병목 결과
3. FPGA tiled INT8 MatVec accelerator 구조
4. Roofline 또는 measured/projected/overhead 분해
