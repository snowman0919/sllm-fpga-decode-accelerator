# 0단계 초기 점검 보고

## 저장소 상태

- 작업 저장소: 작업 저장소
- 시작 브랜치: `main`
- 작업 브랜치: `paper-final-y700-fpga`
- 기준 커밋: `40af455a Remove outdated documentation`
- `main` 상태: reviewer-facing 최소 구조 유지
- `examine` 브랜치: raw 실험 흔적 보존용으로 유지됨
- 현재 dirty 항목:
  - `docs/OpenRouter Chat Tue Jun 30 2026.md`: 사용자가 제공한 비평서
  - `docs/._OpenRouter Chat Tue Jun 30 2026.md`: macOS resource fork로 보이는 부수 파일
  - `docs/stage_reports/00_critique_synthesis.md`: 0단계 산출물
  - `docs/stage_reports/00_initial_audit.md`: 본 보고서

## 확인한 필수 파일

| 항목 | 상태 | 위치 |
| --- | --- | --- |
| 현재 원고 | 확인 | `paper/current/manuscript.md` |
| 비평서 Markdown | 확인 | `docs/OpenRouter Chat Tue Jun 30 2026.md` |
| HWP 원본 양식 | repo 외부에서 확인 | repo 외부 HWP 양식 파일 |
| HWPX 양식 | repo 외부에서 확인 | repo 외부 HWPX 양식 파일 |
| FPGA primary board manifest | 확인 | `logs/jtag_cycle_counter_clean_rebuild_final/BOARD_RUN_MANIFEST.md` |

## 현재 논문의 가장 큰 문제 5개

1. 최종 제목의 "온디바이스" 중심성과 달리 현 원고의 핵심 실험은 Ryzen 7 9700X 및 ORT CPUExecutionProvider 중심이다.
2. 초록부터 결론까지 반복되는 면책 문장이 기여를 약하게 보이게 한다.
3. 16x4 INT8 MatVec 결과가 correctness/cycle anchor인지, ORT micrograph latency 비교인지, projected interface estimate인지 표에서 혼동될 수 있다.
4. FPGA 구조가 아직 fixed primitive 중심으로 서술되어 parameterized tiled INT8 MatVec/MatMul accelerator proposal로 충분히 확장되지 않았다.
5. 실제 projection shape, bandwidth-bound 조건, host/offload interface 요구사항이 정량적으로 부족해 CPU/ORT 병목과 FPGA 구조 사이의 다리가 약하다.

## 비평서에서 우선 반영할 지적 10개

1. "정직하지만 방어문이 많다"는 인상을 줄이고, 기여를 결과 중심으로 재서술한다.
2. Ryzen 실험만으로 온디바이스를 주장하지 않고, Lenovo Y700 실측을 본문 중심으로 세운다.
3. float32 ONNX profiling의 한계를 보완하기 위해 optimized/quantized/MatMulInteger 경로를 추가한다.
4. QNN/NNAPI는 성공하면 결과로, 실패하면 attempted but not used 또는 integration blocked로 기록한다.
5. 16x4 microbench는 latency 우열 비교가 아니라 기능 동등성 및 internal cycle-counter 검증으로만 쓴다.
6. CPU/ORT operator share와 FPGA offload 가능성을 arithmetic intensity, memory bandwidth, interface overhead로 연결한다.
7. DE10-Lite는 projection-scale acceleration platform이 아니라 core validation과 cycle anchor platform으로 정의한다.
8. 표와 그림에서 measured, board_measured, simulation, projected, invocation overhead를 분리한다.
9. 제목과 본문 표현은 "가속기 설계"보다 "가속기 구조 제안"으로 통일한다.
10. 절대경로, 내부 CSV 약어, 긴 해시, 깨진 캡션, 오타를 제출본에서 제거한다.

## 실험 가능성 판단

### Lenovo Y700 / Android

- 사용자 조건상 ADB가 가능하고, Snapdragon 8+ Gen 1 / RAM 8GB 장치로 전제한다.
- 우선 목표는 Gemma 전체 모델 성공이 아니라 CPU EP 또는 CPU fallback 기반 ONNX Runtime 실행 경로 확보이다.
- QNN/NNAPI는 환경과 패키지 의존성이 크므로 "시도 및 실패 로그"까지 산출물로 인정하는 계획이 필요하다.
- Gemma 3 1B full ONNX가 장치에서 OOM 또는 실행 실패하면 representative projection/decode micrograph fallback으로 전환한다.

### ONNX / micrograph

- 기존 repo에는 `onnx_micrographs/`와 `onnx_profile/`가 있어 MatMulInteger 및 projection-heavy micrograph 재사용 가능성이 높다.
- 최종 논문에서는 full model 성공 여부와 micrograph fallback을 분명히 구분해야 한다.

### FPGA / DE10-Lite

- 기존 clean rebuild board evidence는 유지 가능하다.
- 추가 확장은 parameterized/multi-lane/tiled synthesis sweep을 목표로 하되, board programming은 최소 anchor 하나만 유지해도 충분하다.
- KR260은 RMA 중이므로 실제 low-latency shared-memory offload claim은 하지 않는다.

### HWP

- HWP/HWPX 양식은 repo 외부에서 발견되었다.
- 직접 HWP 생성 가능 여부는 별도 도구 확인이 필요하다. 불가능하면 DOCX/HTML 중간 산출물과 수동 변환 지점을 명확히 보고해야 한다.

## 다음 단계에서 사용자 판단이 필요할 수 있는 분기점

1. Y700에서 Gemma 전체 모델 ONNX가 OOM 또는 실행 실패할 경우, micrograph 중심 논문으로 전환할지 여부.
2. QNN SDK 또는 QNN EP 사용에 라이선스/다운로드/설치가 필요한 경우.
3. NNAPI/QNN이 CPU보다 비정상적으로 느리거나 일부 op 미지원으로 실패할 경우 표현 방식.
4. FPGA multi-lane/tiled 확장이 기존 구조를 크게 흔들 경우, 1-lane + scaling model로 제한할지 여부.
5. HWP 직접 생성 도구가 없을 경우, DOCX/HWPX 중간본과 수동 HWP 변환을 제출 경로로 인정할지 여부.
6. 10쪽 이하를 맞추기 위해 관련 연구, FPGA 구조 설명, 실험 표 중 어느 것을 축소할지 선택해야 하는 경우.

## 0단계 결론

필수 입력 파일 중 비평서와 HWP 양식 위치가 확인되었으므로 0단계 중단 조건은 해소되었다. 다음 단계에서는 제목과 연구 질문, 최종 outline을 고정하고, 동시에 Y700/ONNX Runtime 실험 경로와 FPGA parameterized 확장 가능성을 실제 파일 기준으로 점검한다.
