# Figure Index

| 그림 번호 | 파일 | 삽입 위치 | 캡션 | 출처 | 해석 제한 |
| --- | --- | --- | --- | --- | --- |
| 그림 1 | `assets/f01.png` | II. 본론 2.1 전체 실험 흐름 | ONNX export, graph inspection, ONNX Runtime profiling, MatMul category analysis, FPGA primitive validation, future accelerator 구조 제안을 구분한 전체 연구 흐름 | `docs/01_실험_근거와_주장_범위.md` | workflow diagram only |
| 그림 2 | `assets/f02.png` | II. 본론 3.2 ONNX Runtime profiling 결과 | ONNX Runtime traced phase time에서 MatMul이 차지하는 비중 | `assets/c08.csv` | visualizes existing ORT profiling interpretation only |
| 그림 3 | `assets/f03.png` | II. 본론 3.3 Long-decode ONNX Runtime sweep 결과 | Decode step 증가에 따른 ONNX Runtime CPUExecutionProvider traced decode node time 중 MatMul 비중 | `assets/c07.csv` | host-side ORT CPU profile only |
| 그림 4 | `assets/f04.png` | II. 본론 3.3 Long-decode ONNX Runtime sweep 결과 | Decode step 증가에 따른 `Expand`, `Concat`, `Unsqueeze` 합산 비중 | `assets/c07.csv` | shape/cache pressure indicator only |
| 그림 5 | `assets/f05.png` | II. 본론 3.4 MatMul category 분석 결과 | MatMul category 누적 시간을 전체 MatMul 시간 비중으로 시각화한 결과 | `assets/c09.csv` | visualizes existing category aggregation only |
| 그림 6 | `assets/f06.png` | II. 본론 5. FPGA 기반 Decode 가속기 구조 | ONNX Runtime 병목 분석 결과를 반영한 FPGA Decode tiled MatVec/MatMul accelerator 구조 | `docs/01_실험_근거와_주장_범위.md`; `assets/c16.csv` | future architecture sketch; primitive validation only |
| 그림 7 | `assets/f07.png` | II. 본론 5. FPGA 기반 Decode 가속기 구조 | Measured baseline과 projected optimized FPGA estimate를 같은 축에 놓되 직접 speedup claim이 아님을 명시한 해석 그림 | `assets/c14.csv` | measured and projected rows are mixed; not a direct speedup claim |
| 그림 8 | `assets/f08.png` | II. 본론 6. 실험 결과 | CPU/ONNX Runtime measured baseline과 FPGA projected interface estimate를 구분하고 JTAG/cycle-counter 경계를 명시한 latency decomposition | `assets/c14.csv` | measured/pending/projected rows are separated; not an end-to-end speedup claim |

## HWP/PDF 변환 시 주의사항

- 원본 PNG 파일을 `assets/`에서 직접 삽입한다.
- 그림 번호와 캡션은 본문과 figure index를 기준으로 맞춘다.
- Quartus/board screenshot이 추가될 경우 별도 figure_no를 부여한다.
- screenshot은 bitstream configuration evidence로만 설명한다.
- board numeric output photo가 없으면 numeric board-output validation을 주장하지 않는다.
