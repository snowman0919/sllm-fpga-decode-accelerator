# 6단계 Offload Interface 및 Roofline 중간 보고

## 생성한 산출물

- `paper_assets/tables/projection_tile_roofline.csv`
- `paper_assets/tables/offload_interface_model.csv`
- `paper_assets/tables/fpga_board_validation_summary.csv`
- `paper_assets/tables/experiment_environment.csv`
- 생성 스크립트: `scripts/build_final_analysis_tables.py`

## 모델 config 근거

로컬 Gemma 3 1B config에서 다음 값을 사용했다.

| 항목 | 값 |
| --- | ---: |
| hidden_size | 1152 |
| intermediate_size | 6912 |
| vocab_size | 262144 |
| num_attention_heads | 4 |
| head_dim | 256 |
| attention aggregate width | 1024 |

## Roofline 해석

새 `projection_tile_roofline.csv`는 실제 측정값이 아니라 projection-scale 구조 모델이다. 각 행은 다음을 분리한다.

- `evidence_type=projected`
- input/output dimension
- MAC 수
- INT8 weight bytes
- activation bytes
- INT32 output bytes
- arithmetic intensity
- assumed lanes: 1, 16, 64
- assumed bandwidth case:
  - JTAG: 성능 경로가 아니므로 not applicable
  - USB2-like 40 MB/s
  - USB3 streaming 320 MB/s
  - AXI DMA 1000 MB/s

이 표의 핵심은 "FPGA core cycle이 작다"는 주장이 아니라, projection-scale workload에서는 weight streaming과 output tiling이 compute lane 수만큼 중요하다는 점이다.

예를 들어 full `lm_head` shape 1152 -> 262144는 per-token MAC 수가 301,989,888이고 INT8 weight만 약 302 MB이다. 16 lanes, 50 MHz 가정에서는 compute estimate가 약 377 ms이며, USB3 320 MB/s stream estimate는 약 947 ms이다. 따라서 DE10-Lite/JTAG 경로는 물론이고 외부 streaming prototype에서도 weight movement가 지배적인 조건이 쉽게 발생한다.

## DE10-Lite 한계

기존 board evidence를 재정리한 `fpga_board_validation_summary.csv`는 다음을 보여준다.

| 항목 | 값 |
| --- | ---: |
| input_dim/output_dim | 16 / 4 |
| MACs | 64 |
| pass/fail | 20 / 0 |
| compute cycles | 65 |
| compute time | 1.3 us @ 50 MHz |
| logic elements | 2,560 / 49,760 |
| DSP 9-bit elements | 1 / 288 |
| memory bits | 512 / 1,677,312 |
| Fmax | 56.670 MHz |

이 결과는 core correctness 및 cycle-level validation이다. 실제 projection-scale acceleration을 의미하지 않는다. 특히 검증된 core는 1-lane sequential MAC 성격이고, roofline의 16/64-lane 행은 구조 모델이다. 최종 원고에서는 이 둘을 같은 measured 성능으로 병치하지 않는다.

## Interface 모델

`offload_interface_model.csv`는 interface별 claim boundary를 분리한다.

- USB-Blaster JTAG/System Console: measured invocation overhead, correctness/debug only
- UART/USB serial: projected, correctness only
- USB3/FT600-class streaming: projected prototype 후보
- Ethernet/UDP streaming: projected prototype 후보
- AXI DMA/shared memory on KR260/Zynq-class SoC: future path
- Snapdragon QNN/NNAPI EP: Y700에서 실제 시도해야 하는 on-device accelerator baseline

## 논문에 반영할 핵심 문장

최종 원고에서는 다음 해석을 사용한다.

> DE10-Lite의 16x4 INT8 MatVec 결과는 연산 코어의 기능 정합성과 cycle counter 검증 기준이다. 실제 projection-scale offload는 weight movement, output tile 처리, invocation overhead가 지배할 수 있으므로, compute lane 수만으로 acceleration을 주장할 수 없다. 따라서 최종 원고는 구현되지 않은 datapath를 확정하지 않고, activation/partial-sum reuse, weight residency, low-overhead interface를 후속 구조 요구사항으로만 정리한다.

## 남은 작업

1. Y700 장치 연결 후 실제 ONNX Runtime CPU/NNAPI/QNN 또는 fallback micrograph 로그 확보.
2. FPGA multi-lane/tiled RTL 또는 synthesis sweep 가능성 판단.
3. 최종 원고에서 기존 표 13/14 latency 비교를 evidence type 중심 표로 교체.
