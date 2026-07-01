# 0단계 비평서 종합

## 입력 파일

- 비평서: `docs/OpenRouter Chat Tue Jun 30 2026.md`
- 현재 원고: `paper/current/manuscript.md`
- 현재 기준 브랜치: `paper-final-y700-fpga`

## 총평

비평서의 공통 진단은 명확하다. 기존 원고는 측정값을 정직하게 구분하려는 태도는 좋지만, 방어문이 너무 많고 핵심 기여가 작아 보인다. 특히 Ryzen CPU 기반 ONNX Runtime profiling과 DE10-Lite 16x4 INT8 MatVec primitive 사이의 정량적 연결이 약해, "CPU에서 비싸다"와 "FPGA로 옮길 가치가 있다" 사이의 논리적 다리가 부족하다는 지적이 반복된다.

최종 개정의 방향은 가속 성능을 키워 주장하는 것이 아니라, 제목과 주장을 "온디바이스 ORT decode 병목 분석" 및 "FPGA 기반 INT8 tiled MatVec 구조 제안"으로 정렬하는 것이다. 이를 위해 Snapdragon 8+ Gen 1급 Lenovo Y700 실측, optimized/quantized ONNX 또는 MatMulInteger 경로, projection tile roofline, offload interface 모델, DE10-Lite의 기능 검증과 한계 분리를 본문 중심으로 재배치해야 한다.

## 반드시 해결해야 할 핵심 지적 10개

| 우선순위 | 비평서 지적 | 최종 개정 대응 |
| ---: | --- | --- |
| 1 | "온디바이스" 주장 근거가 Ryzen 7 9700X 중심이라 약하다. | Lenovo Y700 Snapdragon 8+ Gen 1 실험을 본문 핵심 근거로 올리고, Ryzen 결과는 historical/desktop reference로 축소한다. |
| 2 | float32 ONNX profiling은 실제 배포형 온디바이스 병목을 대표하기 어렵다. | optimized ONNX, quantized/QDQ 또는 MatMulInteger micrograph, 가능하면 NNAPI/QNN 시도 결과를 분리 보고한다. |
| 3 | CPU/ORT profiling과 FPGA primitive 사이의 정량적 연결이 약하다. | projection shape, arithmetic intensity, bandwidth, compute lane, interface overhead를 roofline/offload 모델로 연결한다. |
| 4 | 16x4 microbench latency 비교는 framework dispatch overhead와 FPGA compute latency를 섞는다. | 16x4 결과는 correctness와 board cycle-counter anchor로만 두고, latency 우열 비교 표는 폐기 또는 측정 성격별로 재구성한다. |
| 5 | 방어문이 너무 많아 논문이 스스로 기여를 깎는다. | 금지 claim은 유지하되, 본문 반복 면책을 줄이고 한계는 방법/논의/결론의 지정 위치로 압축한다. |
| 6 | FPGA 파트가 toy primitive에 머물러 "구조 설계" 제목을 지탱하지 못한다. | 제목과 본문을 "구조 제안"으로 정렬하고, parameterized tiled INT8 MatVec/MatMul datapath, tile mapping, resource/timing sweep을 추가한다. |
| 7 | bandwidth-bound 조건을 정직하게 수식화하지 않았다. | Gemma projection shape별 weight bytes, activation reuse, output bytes, required bandwidth, compute/stream time을 표로 제시한다. |
| 8 | JTAG total latency를 반복 변명하는 방식이 오히려 약점처럼 보인다. | JTAG은 correctness/debug path로 한 번 정의하고, 표에서는 invocation overhead와 internal cycle counter를 명확히 분리한다. |
| 9 | measured, projected, simulation, correctness, invocation overhead가 한 표/그림에서 섞인다. | 모든 표에 evidence type을 명시하고, projected estimate는 measured result와 같은 latency 비교열에 놓지 않는다. |
| 10 | 표/그림과 용어에 오타, 내부 artifact ID, 절대경로, AI식 깨진 캡션이 남아 있다. | 제출본에서 절대경로, 긴 SHA 본문 노출, `c01`류 내부 출처, 깨진 영어 캡션, MatMul 및 prefill 관련 오타를 제거한다. |

## 현재 원고의 가장 큰 문제 5개

1. 제목은 "가속기 구조 설계"에 가깝지만 실제 검증은 fixed 16x4 primitive에 머물러 기대 수준이 맞지 않는다.
2. "온디바이스" 근거가 Y700이 아니라 Ryzen/CPUExecutionProvider 중심이어서 최종 제목과 충돌한다.
3. 초록과 본문에 면책 문장이 반복되어 연구 기여보다 하지 않은 일이 먼저 보인다.
4. 표 13/14류의 primitive latency 비교가 ORT dispatch overhead, FPGA internal compute, JTAG invocation, projected interface estimate를 한 비교 서사로 묶어 오해를 만든다.
5. 실제 projection shape와 DE10-Lite/미래 FPGA interface 사이의 대역폭 모델이 부족해, FPGA 구조 제안의 조건이 불명확하다.

## 유지할 요소

- ONNX export, graph inspection, runtime profiling, FPGA board validation을 증거 계층으로 구분한 기본 태도.
- DE10-Lite clean rebuild `.sof` SHA-256, pass_count=20/fail_count=0, reference/result 일치, COMPUTE_CYCLES=65라는 board-level anchor.
- JTAG total latency를 compute latency로 해석하지 않는 claim boundary.
- MatMul category에서 `mlp_projection`과 `lm_head`를 중심으로 projection-heavy decode primitive를 분석한 방향.

## 축소하거나 삭제할 요소

- Ryzen 결과를 "온디바이스"의 주 근거로 쓰는 표현.
- long-decode runs=1/warmup=0 데이터를 latency benchmark처럼 보이게 하는 표기.
- 16x4 primitive의 compute latency와 ORT MatMulInteger dispatch latency를 직접 우열 비교하는 문장.
- 긴 SHA-256, 내부 CSV 약어, 절대경로의 본문 노출.
- "full sLLM 실행이 아니다"류 반복 면책. 필요한 위치에 한 번씩만 둔다.

## 최종 개정 기준

최종 원고는 다음 문장으로 요약될 수 있어야 한다.

> 본 연구는 Snapdragon 8+ Gen 1급 Lenovo Y700에서 ONNX Runtime 기반 sLLM 또는 대표 decode micrograph의 병목을 실측하고, 남는 projection-heavy INT8 MatVec/MatMul primitive를 어떤 FPGA tiled datapath와 offload interface 조건에서 다룰 수 있는지 분석한다. DE10-Lite 결과는 full system acceleration이 아니라 INT8 MatVec core의 correctness와 cycle-level board anchor이다.

이 기준을 벗어나 전체 실행 가속, Gemma 전체 모델의 FPGA 실행, FPGA의 ORT 대비 우위라는 식의 claim으로 읽히는 표현은 삭제한다.
