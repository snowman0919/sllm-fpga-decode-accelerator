# 5단계 FPGA INT8 MatVec 구조 확장 중간 보고

## 변경 요약

기존 `DecodeMatVecInt8`는 `tileDim == 1`만 허용하는 fixed sequential core였다. 이번 단계에서는 보드 경로의 16x4/1-lane demo를 유지하면서, simulation용 core에서 `tileDim > 1`을 사용할 수 있도록 확장했다.

수정 파일:

- `hw/spinal/src/main/scala/qk/DecodeMatVecInt8.scala`
- `hw/spinal/src/test/scala/qk/DecodeMatVecInt8Sim.scala`
- `scripts/build_final_analysis_tables.py`
- `paper_assets/tables/fpga_tiled_config_sweep.csv`

## 구현 내용

- `DecodeMatVecInt8Config.tileDim` 제한을 완화했다.
  - `tileDim > 0`
  - `tileDim <= inputDim`
  - `inputDim % tileDim == 0`
- `tileDim`개의 INT8 product를 한 cycle에 합산해 accumulator에 더하는 input-lane 병렬 구조를 추가했다.
- `tileDim=1`인 기존 demo definition name은 `DecodeMatVecInt8_i16_o4`로 유지했다.
- `tileDim>1`인 core는 `DecodeMatVecInt8_i{input}_o{output}_t{tile}` 이름을 사용한다.

## 검증 결과

실행한 검증:

```bash
nix develop -c bash -lc 'cd hw/spinal && sbt "testOnly qk.DecodeMatVecInt8Sim"'
nix develop -c just fpga-jtag-regbank-sim
nix develop -c just fpga-jtag-verilog
```

결과:

| config | evidence_type | 결과 |
| --- | --- | --- |
| inputDim=16, outputDim=4, tileDim=1 | simulation | pass, 기존 expected/result 일치, cycles=65 |
| inputDim=64, outputDim=16, tileDim=4 | simulation | pass, software reference 일치 |
| DecodeMatVecRegBank 16x4 board-facing path | simulation | pass, compute_cycles=65 |
| generated Verilog mirror | generated artifact | pass |
| Windows Pocket4 Quartus clean compile | synthesis/timing | pass, 0 errors, 45 warnings |
| Windows Pocket4 DE10-Lite rerun | board_measured | pass_count=20, fail_count=0, compute_cycles=65 |

## Windows Quartus clean compile

새 Verilog mirror를 `db`, `incremental_db`, `output_files` 없이 Windows Pocket4 임시 경로에 복사한 뒤 Quartus 25.1std Lite에서 clean compile을 수행했다. 이후 생성된 `.sof`를 DE10-Lite에 programming하고 동일 JTAG-to-Avalon validation runner를 20회 실행했다.

결과:

- compile status: pass
- Quartus: 25.1std.0 Build 1129 10/21/2025 SC Lite Edition
- target device: MAX 10 `10M50DAF484C7G`
- logic elements: 2,560 / 49,760
- DSP 9-bit elements: 1 / 288
- memory bits: 512 / 1,677,312
- worst setup slack: 2.353 ns
- worst hold slack: 0.094 ns
- Fmax: 56.670 MHz
- `.sof` SHA-256: `d3e07b8b14a19bede927d7af7e72d17f48741bb0cd03fc4c3c666172d9abb989`
- board rerun: pass_count=20, fail_count=0
- board rerun compute cycles: 65.0 / 65.0 / 65.0 mean/p50/p95
- board rerun compute time: 1.3 us @ 50 MHz
- board rerun JTAG total latency: 7756.114875 / 7755.08985 / 7775.94519 ms mean/p50/p95

이 `.sof`는 새 clean compile 및 rerun artifact이다. 기존 2026-06-30 board run의 primary clean rebuild `.sof` SHA-256 `40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84`와 다르므로, 두 run은 별도 evidence로 기록한다.

로컬 보존 위치:

- `logs/quartus_clean_compile_final/`
- `logs/jtag_cycle_counter_clean_rebuild_final/`
- `logs/jtag_cycle_counter_clean_rebuild_final_20260701_cmd/`
- `paper_assets/tables/quartus_resource_timing_summary_final.csv`
- `docs/stage_reports/05_quartus_clean_compile_summary.md`

## 최종 표 반영

`paper_assets/tables/fpga_tiled_config_sweep.csv`를 생성했다.

현재 표의 evidence boundary:

- `poc_board_validation`: board_measured, 기존 16x4 clean rebuild 및 board run 근거
- `small_tiled_sim`: simulation only, 64x16 tileDim=4
- 설계 공간 예시는 본문 중심 결과에서 제외하고, 필요 시 보조 artifact로만 둔다.

## 중요한 경계

이번 변경은 full tiled accelerator 구현이 아니다. 특히 다음은 아직 구현/측정하지 않았다.

- output tile buffer
- runtime/host offload protocol
- multi-lane board synthesis/timing sweep
- DE10-Lite board programming for tileDim>1

따라서 최종 논문에서는 tileDim=4 결과를 "simulation으로 확인한 parameterization step"으로만 사용한다. board-measured 수치로 사용할 수 있는 것은 여전히 16x4, tileDim=1, COMPUTE_CYCLES=65 검증 기준뿐이다.

## 다음 작업

1. tileDim>1 standalone synthesis sweep은 아직 수행하지 않았다.
2. `small_tiled_sim`은 simulation evidence로만 두고, projection-scale은 roofline/interface model로 분리한다.
3. 최종 원고의 FPGA 장은 "구현 결과"와 "구조 제안"을 표로 분리한다.
