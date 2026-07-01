# 비평서 대응표

작성 시점: 2026-07-01

| 비평 항목 | 기존 문제 | 수정 조치 | 반영 위치 | 남은 한계 | 자체 평가 |
| --- | --- | --- | --- | --- | --- |
| 정직하지만 방어문이 많아 기여가 약해 보임 | 하지 않은 것의 나열이 길었음 | 기여를 Y700 micrograph 병목 분석, 구조 요구사항, primitive validation으로 재정의 | `paper/current/manuscript.md` 초록, 1장 | Gemma 전체 모델 실행은 아님 | 부분 해결 |
| CPU/ORT profiling과 FPGA primitive 연결 약함 | 16x4 결과와 ORT 병목 사이 정량 bridge 부족 | projection roofline/interface model 추가 | 7장, `projection_tile_roofline.csv` | 실제 offload 측정 없음 | 부분 해결 |
| 16x4 비교가 overhead와 compute latency를 섞음 | ORT micrograph latency와 FPGA core cycle이 직접 비교됨 | 직접 우열 비교 제거, evidence type 분리 | 3장, 6장 | 없음 | 해결 |
| Ryzen 실험만으로 온디바이스 주장 어려움 | host 결과가 중심이었음 | Y700 Android APK benchmark를 추가하고 host 결과를 기존 artifact로 격하 | 3장, 4장 | full graph latency는 아님 | 부분 해결 |
| Snapdragon급 실제 온디바이스 실험 필요 | 실제 Android latency 없음 | Y700 CPU/NNAPI projection micrograph latency 확보 | `android/y700_ort_benchmark/`, `logs/y700_onnx_runtime/` | representative micrograph 기준 | 부분 해결 |
| float32 profiling만으로 배포 병목 대표 어려움 | FP32 graph 중심 | MatMulInteger 및 INT8 projection micrograph 추가 | `onnx_micrographs/`, 표 3 | full quantized model 없음 | 부분 해결 |
| optimized ONNX/quantized/QNN/NNAPI 조사 필요 | provider 경로 구분 부족 | CPU/NNAPI 실행, QNN integration blocked 기록 | `paper_assets/tables/y700_onnx_runtime_baseline.csv` | QNN SDK build 미확보 | 부분 해결 |
| FPGA가 toy primitive에 머무름 | 16x4 smoke test 중심 | tiled MatVec/MatMul 구조 제안, `tileDim=4` simulation 추가 | 5장, 6장, SpinalHDL 변경 | board-measured 확장은 없음 | 부분 해결 |
| DE10-Lite 한계와 bandwidth-bound 조건 부족 | compute cycle만 강조 | interface model과 weight streaming roofline 추가 | 7장 | actual streaming 미측정 | 부분 해결 |
| measured/projected/simulation 혼동 | 표가 다른 evidence를 섞음 | 표 1과 각 결과 표에 evidence type 명시 | 3장, 5-7장 | 없음 | 해결 |
| 10쪽 이하 압축 필요 | 이전 원고가 장황함 | 214-line compact draft로 재작성 | 전체 원고 | HWP 조판 미확인 | 부분 해결 |
| HWP 최종본 필요 | Markdown 중심 | pandoc DOCX/HTML 중간본과 HWPX 양식 기반 중간본 생성, HWP 변환 차단 사유와 수동 변환 절차 기록 | `paper/final/`, `08_hwp_conversion_blocker.md` | 직접 HWP 저장 도구 미확보 | 부분 해결 |
