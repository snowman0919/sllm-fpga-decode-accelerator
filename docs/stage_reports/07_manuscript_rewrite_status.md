# 07단계 원고 전면 개정 상태 보고

작성 시점: 2026-07-01

## 요약

`paper/current/manuscript.md`를 새 제목과 새 연구 정체성에 맞게 전면 재구성했다. 이후 Lenovo Y700 APK benchmark 결과를 반영하여 CPU EP/NNAPI EP latency와 QNN QNN EP 실행 경로 미확보 상태를 본문 표와 그림에 포함했다.

## 반영한 방향

- 최종 제목을 `온디바이스 ONNX Runtime sLLM 추론의 Decode 병목 분석과 FPGA 기반 INT8 MatVec 가속기 구조 제안`으로 변경했다.
- 기존 16x4 INT8 MatVec 결과를 ONNX Runtime latency와 직접 비교하는 구도를 제거했다.
- FPGA 결과는 DE10-Lite board-level correctness와 internal cycle counter 검증 기준로만 배치했다.
- JTAG total latency는 host-tool invocation overhead로 분리했고 compute latency로 해석하지 않았다.
- ONNX Runtime profiling, Android/Y700 실행 하네스, micrograph manifest, FPGA validation, roofline/interface model을 서로 다른 evidence layer로 분리했다.
- Ryzen/host CPUExecutionProvider trace는 온디바이스 결과가 아니라 기존 host profiling artifact로 낮춰 서술했다.
- long-decode shape/cache 결과는 exploratory operator-share evidence로만 사용했다.

## 현재 원고 구조

1. 서론
2. 관련 연구 및 배경
3. 실험 방법
4. ONNX Runtime 및 Micrograph 병목 분석
5. FPGA 기반 INT8 MatVec 가속기 구조 제안
6. FPGA 구현 및 검증 결과
7. Offload Interface 및 Roofline 분석
8. 논의 및 결론

## 표와 그림 상태

- 본문 표: 8개
- 본문 그림: 4개
- 그림 파일 위치: `paper_assets/figures/`
- 표 원본 CSV 위치: `paper_assets/tables/`

`y700_onnx_runtime_bottleneck.png`는 실제 Y700 INT8 MatMulInteger projection micrograph p50 latency chart로 교체했다.

## 아직 최종본이 아닌 이유

- Gemma 전체 모델 실행은 아직 확보하지 않았고, 현재 온디바이스 latency는 representative ONNX micrograph 기준이다.
- QNN은 tested AAR build에서 provider 미지원으로 QNN EP 실행 경로 미확보이다.
- HWP 직접 생성 도구가 로컬/Nix/Windows PATH에서 확인되지 않았다.
- 논문 문장은 Y700 micrograph 수치 기준으로 갱신되었지만 HWP 제출본은 아직 생성되지 않았다.

## 다음 조치

1. HWP/HWPX 변환 경로를 확정한다.
2. pandoc 기반 DOCX 중간본을 생성한다.
3. 최종 HWP 직접 생성 가능 여부를 다시 확인한다.
