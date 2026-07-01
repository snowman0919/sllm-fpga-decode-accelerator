# 1단계 논문 정체성 재정의 계획

## 최종 제목

온디바이스 ONNX Runtime sLLM 추론의 Decode 병목 분석과 FPGA 기반 INT8 MatVec 가속기 구조 제안

영문 제목 후보:

Decode Bottleneck Analysis of On-device ONNX Runtime sLLM Inference and an FPGA-based INT8 MatVec Accelerator Architecture Proposal

## 정체성

최종 논문은 "FPGA의 ONNX Runtime 대비 전체 실행 우위"는 성능 논문이 아니다. 핵심 정체성은 다음과 같다.

> Snapdragon 8+ Gen 1급 Android 장치와 ONNX Runtime 실행 계층에서 decode 병목을 실측하고, 이 병목 중 projection-heavy INT8 MatVec/MatMul primitive를 후속 FPGA 구조 요구사항으로 정리한다. DE10-Lite 결과는 full accelerator가 아니라 INT8 MatVec core의 correctness와 cycle-level board validation이다.

따라서 본문 중심어는 "가속기 설계"가 아니라 "가속기 구조 제안"으로 통일한다. 기존 fixed 16x4 결과는 설계 전체의 성능 증거가 아니라, 최소 연산 코어가 FPGA toolchain과 실제 보드에서 동작함을 보이는 검증 기준로 사용한다.

## 연구 질문

1. Snapdragon 8+ Gen 1급 온디바이스 환경에서 ONNX Runtime sLLM/대표 decode graph의 병목은 무엇인가?
2. optimized ONNX, quantized ONNX 또는 MatMulInteger 경로에서도 projection-heavy primitive가 남는가?
3. 해당 primitive를 후속 FPGA INT8 MatVec/MatMul 구조로 옮기려면 어떤 memory/interface 조건이 필요한가?
4. DE10-Lite에서 검증 가능한 범위와 실제 실용 offload interface 사이에는 어떤 간극이 있는가?

## 최종 기여문 초안

기여문은 3개로 압축한다.

1. Snapdragon 8+ Gen 1 기반 Lenovo Y700에서 ONNX Runtime CPU/가능한 EP 경로와 대표 decode micrograph를 실행하여, 온디바이스 decode 병목과 최적화/양자화 경로의 남는 연산 부담을 측정한다.
2. ONNX graph/operator profiling 결과를 실제 Gemma 계열 projection shape, arithmetic intensity, weight streaming, activation reuse, output tile 요구사항으로 연결하여 FPGA offload 조건을 정량화한다.
3. DE10-Lite에서 INT8 MatVec core의 RTL simulation, clean rebuild, JTAG-to-Avalon correctness, internal cycle counter 측정을 확보하고, 이를 full system acceleration이 아닌 tiled INT8 MatVec accelerator 구조 제안의 하드웨어 검증 기준로 제시한다.

Y700 실험이 Gemma 전체 모델 실행에 실패할 경우 1번 기여문은 다음처럼 낮춘다.

> Snapdragon 8+ Gen 1 기반 Lenovo Y700에서 ONNX Runtime CPU 경로와 대표 decode micrograph를 실행하여, full model 실행 가능성과 별개로 deployment boundary에서 남는 projection-heavy primitive의 비용을 측정한다.

## 유지할 내용

- 증거 계층 분리: graph evidence, ORT profiling, host reference, FPGA simulation/board validation.
- MatMul category breakdown에서 `mlp_projection + lm_head`를 QK-only 설계의 반례로 쓰는 논리.
- DE10-Lite clean rebuild board evidence:
  - pass_count=20, fail_count=0
  - reference/result 일치
  - COMPUTE_CYCLES=65
  - 1.3 us @ 50 MHz
  - JTAG total latency는 invocation overhead

## 축소할 내용

- 초록/서론의 반복 면책.
- 긴 관련 연구 설명. 0.7~1쪽 내에서 배경과 본 연구 위치 중심으로 축소한다.
- Ryzen profiling 중심 서사. 최종 원고에서는 Y700 실험과 대표 micrograph를 우선하고, 기존 Ryzen 결과는 보조/과거 baseline으로 낮춘다.
- 표 13/14의 latency 직접 비교. "무엇을 측정했는가" 기준의 evidence table로 재구성한다.
- SHA-256, 절대경로, 내부 CSV 출처 약어는 본문에서 제거하고 로그/부록/manifest로 이동한다.

## 삭제 또는 재구성할 내용

- "FPGA internal 1.3 us vs ORT MatMulInteger 13.012 us"를 우열로 읽히게 하는 문장.
- "optimized FPGA interface 0.005 ms"를 주요 결과처럼 보이게 하는 그림/표.
- long-decode runs=1/warmup=0 latency를 benchmark처럼 보이게 하는 `decode/token mean` 중심 표기.
- `attention_qk_score = 0%`를 발견처럼 보이게 하는 설명. classifier 한계로 짧게 처리한다.

## 표현 규칙

허용:

- 구조 제안
- 요구사항 도출
- primitive-level validation
- board-level correctness
- internal cycle counter
- measured / board_measured / simulation / projected / invocation overhead 분리

금지:

- Gemma 전체 모델의 FPGA 실행
- ONNX Runtime 전체 그래프 실행의 속도 향상 주장
- sLLM 전체 추론 가속
- FPGA의 ONNX Runtime 대비 전체 실행 우위
- Snapdragon Y700과 DE10-Lite가 실제 low-latency offload path로 연결되어 성능을 개선했다
- projected estimate를 measured result처럼 쓰는 표현

## 표와 그림 재구성 방향

최종 표:

1. 실험 환경
2. Lenovo Y700 ONNX Runtime baseline
3. ONNX graph/operator 또는 micrograph 병목 요약
4. FPGA tiled accelerator design space/resource summary
5. DE10-Lite board validation summary
6. Offload interface/bandwidth 해석

최종 그림:

1. 전체 연구 흐름
2. Y700 ONNX Runtime 병목 결과
3. FPGA tiled INT8 MatVec accelerator 구조
4. 측정/추정/오버헤드 분해 또는 roofline 해석

## 다음 단계 영향

- 2~4단계 결과에 따라 원고 중심이 달라진다. Y700 full model 성공 시 full model/partial graph 결과를 우선한다. 실패 시 실패를 숨기지 않고 representative micrograph 중심으로 병목-offload boundary를 설명한다.
- 5단계 FPGA 확장이 multi-lane까지 성공하면 구조 제안의 무게가 커진다. 실패하면 DE10-Lite 한계와 1-lane scaling model을 정직하게 제시한다.
- HWP 변환 전에는 본문에서 표 폭, 긴 path/hash, 내부 artifact ID를 제거해야 한다.
