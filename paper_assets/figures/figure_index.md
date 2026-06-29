# Figure Index

| 그림 번호 | 파일 | 삽입 위치 | 캡션 | 출처 | 해석 제한 |
| --- | --- | --- | --- | --- | --- |
| 그림 1 | `paper_assets/figures/research_flow.png` | II. 본론 2.1 전체 실험 흐름 | ONNX export, graph inspection, ONNX Runtime profiling, MatMul category analysis, FPGA primitive validation, future accelerator 구조 제안을 구분한 전체 연구 흐름 | `docs/current_bottleneck_implications.md` | workflow diagram only |
| 그림 2 | `paper_assets/figures/ort_matmul_phase_share.png` | II. 본론 3.2 ONNX Runtime profiling 결과 | ONNX Runtime traced phase time에서 MatMul이 차지하는 비중 | `docs/current_bottleneck_implications.md` | visualizes existing ORT profiling interpretation only |
| 그림 3 | `paper_assets/figures/ort_long_decode_matmul_share.png` | II. 본론 3.3 Long-decode ONNX Runtime sweep 결과 | Decode step 증가에 따른 ONNX Runtime CPUExecutionProvider traced decode node time 중 MatMul 비중 | `paper_assets/tables/ort_long_decode_operator_share.csv` | host-side ORT CPU profile only |
| 그림 4 | `paper_assets/figures/ort_long_decode_shape_ops_share.png` | II. 본론 3.3 Long-decode ONNX Runtime sweep 결과 | Decode step 증가에 따른 `Expand`, `Concat`, `Unsqueeze` 합산 비중 | `paper_assets/tables/ort_long_decode_operator_share.csv` | shape/cache pressure indicator only |
| 그림 5 | `paper_assets/figures/ort_matmul_category_breakdown.png` | II. 본론 3.4 MatMul category 분석 결과 | MatMul category 누적 시간을 전체 MatMul 시간 비중으로 시각화한 결과 | `paper_assets/tables/ort_matmul_category_by_context.csv` | visualizes existing category aggregation only |
| 그림 6 | `paper_assets/figures/fpga_decode_accelerator_architecture.png` | II. 본론 5. FPGA 기반 Decode 가속기 구조 | ONNX Runtime 병목 분석 결과를 반영한 FPGA Decode tiled MatVec/MatMul accelerator 구조 | `docs/current_bottleneck_implications.md`; `docs/fpga_decode_accelerator_optimization_plan.md` | future architecture sketch; primitive validation only |

## HWP/PDF 변환 시 주의사항

- 원본 PNG 파일을 `paper_assets/figures/`에서 직접 삽입한다.
- 그림 번호와 캡션은 본문과 figure index를 기준으로 맞춘다.
- Quartus/board screenshot이 추가될 경우 별도 figure_no를 부여한다.
- screenshot은 bitstream configuration evidence로만 설명한다.
- board numeric output photo가 없으면 numeric board-output validation을 주장하지 않는다.
