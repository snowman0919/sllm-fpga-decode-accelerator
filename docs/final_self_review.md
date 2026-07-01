# 최종 자기평가

작성 시점: 2026-07-02

## 1. 제목과 증거의 일치

- 평가: 부분 해결
- 제목의 "가속기 구조 제안"은 구현 완료가 아니라 병목 분석에서 도출한 구조 요구사항과 후속 설계 방향으로 제한했다.
- Y700 micrograph, 기존 ORT profiling, DE10-Lite PoC 검증을 분리해 배치했다.
- 남은 한계: Gemma 전체 graph latency가 아니라 representative projection micrograph 기준이다.

## 2. 온디바이스 근거의 강도

- 평가: 부분 해결
- Lenovo Y700 Android APK로 CPU EP와 NNAPI EP의 projection micrograph latency를 확보했다.
- 이 결과는 full decode share를 직접 측정한 것이 아니라, 온디바이스 projection 연산의 절대 latency와 provider granularity를 보여주는 근거로 해석했다.

## 3. QNN/NPU 경로 처리

- 평가: 부분 해결
- `ssh win` 접속은 성공했지만 지정 경로 `C:\Users\dbsgu\dev\qinst`가 확인되지 않아 QNN SDK 구조를 파악하지 못했다.
- 원고 표현은 "본 실험 환경에서는 QNN EP 실행 경로를 확보하지 못했다"로 정리했다.
- 남은 한계: Snapdragon NPU backend 성능 평가는 후속 과제이다.

## 4. 기존 ORT profiling과 Y700 실험의 연결

- 평가: 부분 해결
- ORT profiling은 decode trace의 operator share를, Y700 micrograph는 Android provider별 absolute latency를 보여주는 서로 다른 evidence layer로 정리했다.
- "같은 결론"처럼 full decode share를 암시할 수 있는 표현은 제거했다.
- `attention_qk_score` 0%는 QK 연산이 없다는 뜻이 아니라 ONNX Runtime graph optimization/fused operator 내부로 흡수되었거나 event classifier가 MatMul event로 분류하지 못한 결과로 제한했다.
- Micrograph는 full graph 대체 주장이 아니라 Android full export, dynamic KV-cache shape, graph copy 비용과 dense projection dispatch/compute 비용을 분리하기 위한 실험 설계로 설명했다.

## 5. DE10-Lite PoC 해석 범위

- 평가: 해결
- 16x4 INT8 MatVec 결과는 기능 정합성과 cycle-level validation으로만 제시했다.
- 1.3 us는 64 MAC PoC core의 internal compute time이며, projection-scale acceleration 결과가 아니라고 정리했다.
- JTAG total latency는 host-tool invocation overhead로 분리했다.

## 6. 1.58bit/DDR2/SRAM 구조 제안의 위치

- 평가: 부분 해결
- 1.58bit 변환, SRAM-like scratchpad FPGA, DDR2/LPDDR2 다채널 memory는 모두 후속 특기자 산출물 후보로 낮췄다.
- INT8 MatVec PoC와 1.58bit 가산기 accelerator 사이의 직접 구현 연결을 주장하지 않는다.
- 남은 한계: 후속 구조 방향 자체는 아직 구현 검증이 없다.

## 7. Roofline/interface 모델

- 평가: 부분 해결
- `T_compute = MACs / (lanes x f_clk)`, `T_stream = W_bytes / B_interface`, `B_required = W_bytes / T_target` 수식을 본문에 추가했다.
- USB3 320 MB/s는 실측값이 아니라 외부 streaming prototype을 상정한 model case로 명시했다.
- 남은 한계: 실제 external streaming 측정은 없다.

## 8. 방어문과 제출본 문체

- 평가: 부분 해결
- `제출 전 검토 표시`, `QNN EP 실행 경로 미확보`, `PoC`, `검증 기준` 같은 제출본에 부적절한 표현을 원고에서 제거했다.
- 부정문을 줄이고, 측정한 것과 후속 과제를 중심으로 다시 썼다.

## 9. 표/그림과 분량

- 평가: 부분 해결
- 표는 evidence layer, Y700 result, ORT bottleneck, hardware requirements, DE10-Lite PoC, roofline, follow-up direction 중심으로 유지했다.
- 그림 경로는 repo 기준 `paper_assets/...`로 바꿨고, HWPX 변환 스크립트가 이를 처리하도록 수정했다.
- LibreOffice PDF는 이전 기준 14쪽이었으며, 최신 변환 후에도 10쪽 이하 여부는 Hancom/HWP 조판에서 재확인이 필요하다.

## 10. HWP 양식 적합성

- 평가: 부분 해결
- Markdown, DOCX, HWPX, HTML, PDF 중간본은 생성 가능하다.
- 현재 환경에는 legacy `.hwp` 직접 저장 도구가 없어 `paper/final/final_manuscript.hwp`는 아직 만들 수 없다.
- `paper/final/README_conversion.md`에 Hancom Office 수동 변환 절차를 남긴다.

## 11. 제출 리스크

- 평가: 중간
- 가장 큰 리스크는 QNN/NPU backend 미측정, legacy HWP 직접 생성 불가, HWP 조판 페이지 수 미확인이다.
- 논문 성격은 선행 병목 분석 + 온디바이스 micrograph + DE10-Lite PoC + 후속 구조 요구사항으로 정리되어, 구현 논문으로 과장되는 위험은 이전보다 낮다.
- 7월 2일 비평 원문은 `docs/OpenRouter Chat Thu Jul 02 2026.md`로 보존했다. 해당 원문은 review transcript라 금지 표현을 포함하지만, 제출 원고와 대응 문서에서는 해당 표현을 제거하거나 학술적 표현으로 바꾸었다.
