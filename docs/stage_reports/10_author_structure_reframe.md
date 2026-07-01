# 10단계 추가 보고: FPGA 구조 제안 재정렬

## 변경 이유

사용자 판단에 따라 `final_manuscript_intermediate.md` 기반 원고에서 Codex가 임의로 확정한 datapath, memory controller, SRAM stacking 구조처럼 읽힐 수 있는 문장을 축소했다. FPGA 구조 절은 구현 결과가 아니라 병목 분석에서 도출한 요구사항과 저자 후속 구조 제안으로 재정렬했다.

## 반영 내용

- 논문 제목은 유지했다.
- Y700 ONNX Runtime micrograph 결과를 온디바이스 병목 근거로 유지했다.
- DE10-Lite 16x4 INT8 MatVec의 1.3 us는 64 MAC PoC core의 internal cycle-counter 기능 검증 기준로 명시했다.
- 1.3 us를 projection-scale 가속 결과로 해석하지 않도록 본문을 수정했다.
- JTAG total latency는 System Console host-tool invocation overhead이며 internal compute time과 별개라고 정리했다.
- 기존 원고에서 구현되지 않은 세부 구성요소를 확정 구조처럼 나열하던 문장을 제거했다.
- planned/projected medium/projection-tile configuration sweep은 본문 중심 표에서 제거했다.
- 사용자 구조 아이디어는 `저자 후속 구조 제안`으로 분리했다.

## 저자 후속 구조 제안으로 남긴 항목

- 1.58bit 계열 변환 기반 가산기 accelerator
- projection-heavy MatVec/MatMul 병목 offload FPGA NPU
- activation, partial sum, hot tile, cache metadata, output tile buffer 재사용을 위한 SRAM-like scratchpad FPGA
- DDR2/LPDDR2 다채널 weight memory
- 연산용 FPGA와 scratchpad FPGA 사이 custom connector

## 남은 검토 지점

5장에는 HWP 변환 전 사용자가 직접 검토할 수 있도록 `제출 전 검토 표시` 표시를 남겼다. 이 표시는 최종 제출 직전 유지 여부를 사용자가 결정해야 한다.
