# Reproducibility Artifacts

이 문서는 논문 양식본 본문에서 제거한 artifact inventory와 reproducibility command를 별도로 정리한다. 본 문서 작성 과정에서는 새 실험, 재컴파일, 보드 프로그래밍을 수행하지 않았다.

## 주요 문서

```text
AGENTS.md
README.md
docs/paper_outline.md
docs/current_bottleneck_implications.md
docs/onnx_runtime_sweep_report.md
docs/ort_matmul_hotspot_analysis.md
docs/fpga_decode_accelerator_optimization_plan.md
docs/fpga_decode_accel_model_summary.md
fpga_test/captured/decode_matvec_board_validation.md
```

## 주요 CSV

```text
paper_assets/tables/onnx_export_status.csv
paper_assets/tables/onnx_graph_io_summary.csv
paper_assets/tables/model_summary.csv
paper_assets/tables/ort_context_sweep_latency.csv
paper_assets/tables/ort_operator_share_by_context.csv
paper_assets/tables/ort_prefill_decode_comparison.csv
paper_assets/tables/ort_matmul_category_by_context.csv
paper_assets/tables/ort_matmul_top_nodes.csv
paper_assets/tables/fpga_decode_accel_candidate_ops.csv
paper_assets/tables/fpga_decode_accel_roofline_estimate.csv
paper_assets/tables/fpga_decode_accel_priority.csv
paper_assets/tables/decode_matvec_int8_sim.csv
paper_assets/tables/decode_matvec_fpga_resource.csv
paper_assets/tables/decode_matvec_fpga_timing.csv
paper_assets/tables/decode_matvec_board_validation.csv
```

## Raw ORT Profile 및 Inspection Artifact

```text
onnx_profile/results_onnx/raw/onnx_graph_inspection.json
onnx_profile/results_onnx/raw/model_inspection.json
onnx_profile/results_onnx_sweep/raw/ort_sweep_raw_runs.json
onnx_profile/results_onnx_sweep/raw/ort_sweep_status.json
```

## FPGA Captured 및 Quartus Output

```text
fpga_test/captured/decode_matvec_int8_sim.csv
fpga_test/captured/decode_matvec_board_validation.md
quartus/de10_lite_decode_matvec/output_files/de10_lite_decode_matvec.sof
quartus/de10_lite_decode_matvec/output_files/de10_lite_decode_matvec.fit.summary
quartus/de10_lite_decode_matvec/output_files/de10_lite_decode_matvec.sta.summary
```

## Reproducibility Commands

다음 명령은 repository에 기록된 기존 흐름을 재현하기 위한 command inventory이다.

```bash
nix develop -c just hf-inspect model_dir=/home/monad/develop/ai_accel/gemma3-1B
nix develop -c just gemma-onnx-export model_dir=/home/monad/develop/ai_accel/gemma3-1B
nix develop -c just onnx-inspect model=/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx
nix develop -c just ort-sweep
nix develop -c just ort-sweep-report
nix develop -c just ort-matmul-analysis
nix develop -c just torch-context-sweep model_dir=/home/monad/develop/ai_accel/gemma3-1B
nix develop -c just decode-accel-model
nix develop -c just decode-matvec-sim
nix develop -c just spinal-generate
nix develop -c just decode-matvec-quartus
```

Windows board programming command:

```powershell
quartus_pgm.exe -m jtag -c "USB-Blaster" -o "p;.\de10_lite_decode_matvec.sof"
```

## Claim Boundary Checklist

| 항목 | 처리 |
| --- | --- |
| full Gemma FPGA execution | not claimed |
| end-to-end ORT speedup | not claimed |
| KV-cache-only bottleneck | not claimed |
| board numeric output validation | not claimed by board programming evidence alone |
| PyTorch baseline as ORT profiling | not claimed |
| roofline/model estimate as measured result | not claimed |
| MatMul-free model as implementation direction | not claimed |
| QK-only accelerator as complete solution | not claimed |
