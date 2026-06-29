# sLLM FPGA Decode Accelerator

Reproducible research repository for:

**ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계**

This repository connects ONNX Runtime bottleneck analysis with a narrow FPGA
primitive validation. It does not contain a full small-language-model
accelerator implementation.

## What This Repository Contains

- ONNX export, graph inspection, and ONNX Runtime CPUExecutionProvider profiling artifacts.
- PyTorch host-side reference baselines kept separate from ONNX Runtime evidence.
- A SpinalHDL fixed 16x4 INT8 Decode MatVec primitive and JTAG register-bank wrapper.
- A DE10-Lite Quartus project for JTAG-to-Avalon board validation.
- Board-measured internal cycle-counter evidence from a real Windows Pocket4 + DE10-Lite run.
- Paper manuscript, paper-facing tables/figures, and reproducibility scripts.

## Key Result

Primary board evidence uses the Windows clean-rebuilt bitstream:

```text
quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof
SHA-256: 40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84
```

Fixed primitive result:

| metric | value |
| --- | ---: |
| primitive | 16x4 INT8 Decode MatVec |
| board run | pass_count=20, fail_count=0 |
| reference/result | `-271 239 287 797` / `-271 239 287 797` |
| FPGA internal compute | 65 cycles = 1.3 us at 50 MHz |
| ONNX Runtime MatMulInteger baseline | 13.012 us mean, 11.0 us p50, 17.3 us p95 |
| JTAG total invocation | 7720.85016 ms mean, 7720.45115 ms p50, 7748.84833 ms p95 |

The JTAG total invocation latency is System Console/JTAG host-tool overhead. It
is not FPGA compute latency.

## Claim Boundary

Allowed interpretation:

- The FPGA result is fixed 16x4 INT8 Decode MatVec primitive validation.
- `COMPUTE_CYCLES` is board-measured internal primitive compute evidence.
- The ONNX Runtime comparison is a primitive micrograph comparison only.
- Optimized FPGA interface rows are projected design estimates only.

Not claimed:

- No full Gemma FPGA execution.
- No full ONNX Runtime model acceleration.
- No end-to-end ONNX Runtime speedup.
- No sLLM inference speedup.
- No claim that JTAG latency is accelerator compute latency.

See [docs/claim_boundary.md](docs/claim_boundary.md).

## Repository Layout

| path | role |
| --- | --- |
| `paper/current/` | canonical current manuscript |
| `paper_assets/tables/` | paper-facing CSV evidence tables |
| `paper_assets/figures/` | paper-facing figures |
| `docs/` | reviewer-facing runbooks, evidence interpretation, and claim boundaries |
| `hw/spinal/` | SpinalHDL source and simulation tests |
| `quartus/de10_lite_jtag_matvec/` | DE10-Lite JTAG-to-Avalon Quartus project and primary `.sof` |
| `windows/` | Windows board and baseline runners |
| `scripts/` | artifact generation and verification scripts |
| `logs/` | compact board-run manifests only; raw logs are preserved on the `examine` branch |

See [docs/repository_structure.md](docs/repository_structure.md).

## Reproduction Workflow

Linux/Nix is used for development and generated paper artifacts. Windows
Pocket4 is used only for Quartus compile, programming, and real DE10-Lite board
runs.

### Linux/Nix

```bash
nix develop -c just fpga-jtag-verilog
nix develop -c just fpga-jtag-regbank-sim
python scripts/build_ort_fpga_comparison.py
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
```

### Windows Pocket4 / DE10-Lite

```powershell
cd quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
cd ..\..
quartus_pgm.exe -m jtag -c "USB-Blaster [USB-0]" -o "p;quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof"
py -3 windows\run_fpga_jtag_matvec.py --runs 20 --cable "USB-Blaster [USB-0]" --quartus-bin "C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe" --keep-tcl --log-dir logs\jtag_cycle_counter_clean_rebuild_final
```

Runbooks:

- [docs/linux_windows_fpga_eval_workflow.md](docs/linux_windows_fpga_eval_workflow.md)
- [docs/windows_board_runbook.md](docs/windows_board_runbook.md)
- [docs/quartus_clean_rebuild_notes.md](docs/quartus_clean_rebuild_notes.md)

## Paper

Canonical manuscript:

```text
paper/current/ONNX_Runtime_온디바이스_sLLM_FPGA_Decode_가속기_논문양식본.md
```

Top-level draft copies and raw experiment traces are preserved on the
`examine` branch, not on reviewer-facing `main`.

## Evidence Pointers

- Primary board manifest: [logs/jtag_cycle_counter_clean_rebuild_final/BOARD_RUN_MANIFEST.md](logs/jtag_cycle_counter_clean_rebuild_final/BOARD_RUN_MANIFEST.md)
- Historical board manifest: [logs/remote_board_eval/BOARD_RUN_MANIFEST.md](logs/remote_board_eval/BOARD_RUN_MANIFEST.md)
- JTAG benchmark report: [docs/fpga_jtag_benchmark_report.md](docs/fpga_jtag_benchmark_report.md)
- ORT vs FPGA interpretation: [docs/ort_vs_fpga_comparison_interpretation.md](docs/ort_vs_fpga_comparison_interpretation.md)
- Primary tables:
  - `paper_assets/tables/fpga_jtag_cycle_counter_summary.csv`
  - `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`
  - `paper_assets/tables/onnx_runtime_integer_micrograph_baseline.csv`
  - `paper_assets/tables/ort_vs_fpga_measured_and_projected_comparison.csv`
