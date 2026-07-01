# 최종 자기평가

작성 시점: 2026-07-01

이 문서는 2026-07-01 working draft 기준의 자기평가이다. Lenovo Y700 Android APK micrograph 실측과 DE10-Lite board rerun은 확보되었고, DOCX/HWPX/PDF 중간본도 생성했다. 다만 HWP 직접 저장 도구가 없어 최종 `.hwp` 제출본은 아직 생성하지 못했다.

## 1. 제목-주장-증거 일치성

- 평가: 부분 해결
- 제목은 온디바이스 ONNX Runtime decode 병목과 FPGA INT8 MatVec 구조 제안을 정확히 가리킨다.
- Y700 APK 기반 CPU/NNAPI micrograph latency가 반영되어 온디바이스 근거가 강화되었다.
- 단, Gemma 전체 모델 실행이 아니라 representative ONNX micrograph 기준이다.

## 2. 온디바이스 실험 타당성

- 평가: 부분 해결
- `ssh win` 경유 ADB device info와 Android APK benchmark를 통해 CPU/NNAPI latency를 확보했다.
- QNN은 tested AAR build에서 provider 미지원으로 integration blocked이다.
- Gemma 전체 모델 latency는 아직 확보하지 않았다.

## 3. ONNX Runtime 최적화/quantization 반영

- 평가: 부분 해결
- MatMulInteger micrograph와 projection-heavy INT8 micrograph는 생성했다.
- full model optimized/quantized ONNX 실행은 아직 확보하지 못했다.
- 원고는 micrograph evidence와 full model execution을 분리했다.

## 4. CPU/NNAPI/QNN/MatMulInteger baseline 신뢰성

- 평가: 부분 해결
- 기존 CPUExecutionProvider profiling artifact는 보조 병목 분석에 사용했다.
- Y700 CPU/NNAPI MatMulInteger baseline은 확보했다.
- QNN baseline은 provider 미지원으로 integration blocked이다.

## 5. FPGA 구조 확장성

- 평가: 부분 해결
- 16x4 sequential primitive에서 `tileDim` parameter를 허용하고 64x16, tileDim=4 simulation을 추가했다.
- board-measured 결과는 새 clean compile bitstream 기준으로 재확인했지만, 여전히 16x4에 한정된다.
- 구조 제안은 tiled MatVec/MatMul accelerator로 확장했지만, full memory/interface 구현은 아직 없다.

## 6. 16x4 microbenchmark 오해 제거

- 평가: 해결
- 원고에서 16x4 FPGA cycle과 ORT MatMulInteger latency를 성능 우열처럼 직접 비교하지 않았다.
- 16x4 결과는 correctness 및 cycle anchor로만 배치했다.

## 7. Evidence type 구분

- 평가: 해결
- measured, simulation, projected, invocation overhead, integration blocked 상태를 표와 본문에서 분리했다.

## 8. DE10-Lite bandwidth 한계

- 평가: 부분 해결
- roofline/interface 표로 bandwidth-bound 조건을 설명했다.
- 실제 external streaming 측정은 아직 없다.

## 9. Snapdragon과 FPGA 연결 경계

- 평가: 해결
- Snapdragon Y700과 DE10-Lite가 실제 low-latency path로 연결되어 성능을 개선했다는 주장을 하지 않았다.
- Android host와 external FPGA 사이에는 USB3-class streaming 또는 shared-memory/DMA path가 필요하다고 제한했다.

## 10. 표/그림 가독성

- 평가: 부분 해결
- 표와 그림은 핵심 evidence layer 중심으로 줄였다.
- 그림 일부는 영어 라벨이 남아 있다. 학술지 양식에서 한글화를 요구하면 추가 편집이 필요하다.

## 11. 분량

- 평가: 해결
- Markdown 기준 222 lines로, 원고 자체는 압축했다.
- LibreOffice PDF 검토본은 14쪽으로 생성되었으므로, HWP 10쪽 이하 목표는 아직 증명되지 않았다.
- 실제 HWP 조판 후 페이지 수 확인과 추가 압축 판단이 필요하다.

## 12. 참고문헌

- 평가: 부분 해결
- 주요 ONNX Runtime, KV-cache, FPGA accelerator, quantization 관련 참고문헌은 유지했다.
- ONNX Runtime QNN/NNAPI 세부 문서는 최종 원고 전 공식 문서 기준으로 재검토하는 것이 좋다.

## 13. HWP 양식 적합성

- 평가: 부분 해결
- repo 안에서 사용할 수 있는 HWP 원본 양식 또는 HWP 직접 저장 도구를 확인하지 못했다.
- 상위 `../paper/`의 학술지 HWPX 양식을 이용해 `paper/final/final_manuscript.hwpx`를 생성했고, pandoc 기반 DOCX 중간본도 생성했다.
- Nix LibreOffice로 `docx -> hwp`를 시도했지만 export filter가 없어 실패했고, `hwpx` 입력도 열리지 않았다.
- `ssh win` Windows 환경에서도 Hancom 실행 파일, registry 항목, COM 자동화 ProgID가 확인되지 않았다.
- 검토용 PDF `paper/final/final_manuscript.pdf`는 생성했지만, 이는 HWP 제출본을 대체하지 않는다.
- Hancom Office에서 HWPX 또는 DOCX를 열어 `.hwp`로 저장하는 수동 변환 절차가 필요하다.

## 14. 제출 리스크

- 평가: 중간-높음
- 가장 큰 리스크는 HWP 최종본 미생성과 10쪽 이하 조판 미확인이다.
- 연구 방향, Markdown 원고, DOCX/HWPX/PDF 중간본, 주요 표/그림, Y700/FPGA 로그는 정리되었지만, `.hwp` 파일이 필수이면 제출 완료 조건은 아직 충족하지 못했다.
