# 최종 표

최종 논문 표는 다음 원칙으로 생성한다.

1. 파일명은 `c01.csv` 같은 내부 번호가 아니라 의미 있는 이름을 사용한다.
2. 각 행에는 가능한 경우 `evidence_type`을 둔다.
3. measured, board_measured, simulation, projected, invocation_overhead를 같은 성능 순위로 비교하지 않는다.
4. Y700 실험 실패 또는 backend integration 실패도 숨기지 않고 `status`와 `notes`로 기록한다.

예정 표:

- `experiment_environment.csv`
- `y700_onnx_runtime_baseline.csv`
- `y700_operator_or_micrograph_summary.csv`
- `model_artifact_manifest.csv`
- `fpga_tiled_config_sweep.csv`
- `fpga_resource_timing_sweep.csv`
- `fpga_board_validation_summary.csv`
- `projection_tile_roofline.csv`
- `offload_interface_model.csv`
