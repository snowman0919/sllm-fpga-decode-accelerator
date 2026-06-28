# Experiment Plan

Research title:

- Korean: ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계
- English: Bottleneck Analysis of ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator Architecture

Primary questions:

- Where do practical bottlenecks arise in ONNX Runtime-based on-device sLLM inference?
- Are they caused by model export, graph structure, runtime execution, memory pressure, prefill, decode, or interactions between these factors?
- Which decode-stage primitives are realistic FPGA hardware targets after profiling evidence is reviewed?

## Stage 1. HF/Safetensors Directory Inspection

- Inspect the raw Gemma 3 1B Hugging Face directory.
- Confirm `config.json`, tokenizer assets, and `*.safetensors` weights exist.
- Extract model metadata needed for later ONNX export, graph interpretation, profiling setup, and KV-cache size calculations.

## Stage 2. ONNX Export

- Preflight the export plan with a dry-run.
- Export the raw Gemma directory to ONNX only when the user explicitly runs the heavy export command.
- Keep the flow on Python-package-based ONNX Runtime tooling instead of building the local `onnxruntime` source tree first.

## Stage 3. ONNX Graph Inspection

- Inspect exported ONNX graph inputs and outputs.
- Check whether past-KV or other cache-related graph I/O exist.
- Decide whether decode cache reuse profiling is supported by the export.
- Identify graph operators and graph boundaries that may affect prefill/decode measurement.

## Stage 4. Gemma 3 1B ONNX Runtime Profiling

- Measure session initialization overhead.
- Measure prefill and decode-stage execution separately where the model interface permits it.
- Export ONNX Runtime profiling traces when enabled.
- Use runtime traces to distinguish export/graph limitations from actual execution bottlenecks.

## Stage 5. PyTorch Host-side Reference Baseline

- Run a PyTorch/Transformers host-side context sweep directly from the local Gemma 3 1B `safetensors` directory.
- Measure model load time, prefill latency, manual decode-loop latency with `past_key_values` reuse, and RSS snapshots.
- Treat this flow as a companion host-side reference baseline even when ONNX export succeeds, not as a replacement for ONNX Runtime profiling.
- PyTorch context sweep is not ONNX Runtime profiling and should not be reported as ONNX Runtime data.

## Stage 6. Context-Length Sweep

- Sweep multiple prompt lengths.
- Generate a decode latency table by context length.
- Compare theoretical KV-cache growth against measured process RSS growth with clear caveats. RSS changes are process-level memory observations, not direct KV-cache byte measurements.

## Stage 7. KV-cache Theoretical Size Calculation

- Sweep representative sequence lengths.
- Produce CSV tables and a simple plot.
- Use the results to explain long-context decode memory pressure as one structural factor, not as the sole assumed bottleneck.

## Stage 8. INT8 QK Dot-Product Baseline Generation

- Generate deterministic INT8 Q and K vectors on the host.
- Compute expected dot-product scores in software.
- Reuse those vectors in RTL simulation and board validation.

## Stage 9. SpinalHDL RTL Generation

- Implement a minimal parameterized INT8 QK dot-product block.
- Generate Verilog reproducibly from Scala sources.

## Stage 10. RTL Simulation

- Run deterministic unit simulation.
- Compare RTL output against the software-computed score.

## Stage 11. Quartus Synthesis

- Import generated Verilog into a DE10-Lite-oriented Quartus project.
- Synthesize only the validation design.

## Stage 12. Dim Sweep Synthesis Scaling

- Generate `dim = 16, 32, 64, 128` variants of the INT8 QK dot-product primitive.
- Run deterministic simulation for each dim and save expected versus observed scores.
- Compile synthesis-only Quartus projects for each dim to compare resource and timing scaling.
- Generate a latency estimate table using the sequential MAC cycle count and the 50 MHz board clock as a reference.
- Keep the interpretation narrow: the dim sweep is not a full sLLM acceleration result, only a primitive-level scaling study.

## Stage 13. DE10-Lite HEX Display Validation

- Display small debug values or low score digits on the 7-segment HEX outputs.
- Confirm basic top-level clocking and observable hardware behavior.
- After `quartus-program`, record the exact `.sof` path, Quartus summary reports, and whether the board settles to `HEX3..HEX0 = F F E A`.
- Treat `HEX3..HEX0 = F F E A` as the low 16 bits of the deterministic signed score `-22`, which is `0xFFEA` in two's complement.
- Save raw photos or videos first under `fpga_test/captured/`.

## Stage 14. FPGA QK Dot-Product Connection

- Use the ONNX export, graph inspection, and runtime profiling results to justify why a decode-stage primitive is worth isolating.
- Use the PyTorch host-side reference baseline when ONNX Runtime decode profiling is unavailable or incomplete.
- Connect that host-side motivation to the FPGA validation of the current INT8 QK dot-product block.
- Use the dim-sweep tables to discuss how primitive cost changes with vector length.
- Keep the interpretation narrow: block-level feasibility only, not full-model deployment and not end-to-end ONNX Runtime comparison data.
- Describe the future architecture as an FPGA Decode accelerator path that can extend from QK dot-product to scale, softmax or approximation, V weighted sum, and buffer/stream interfaces.

## Stage 15. Paper Figure and Table Extraction

- Promote stable plots and tables into `paper_assets/`.
- Run `just hf-inspect ...` to populate `paper_assets/tables/hf_model_dir_summary.csv`.
- Run `just fpga-report` to generate `paper_assets/tables/fpga_resource_summary.csv`, `paper_assets/tables/fpga_timing_summary.csv`, and `paper_assets/tables/fpga_validation_summary.csv`.
- Run `just spinal-sim-sweep` to generate `paper_assets/tables/dot_product_dim_sweep_sim.csv`.
- Run `just fpga-dim-sweep-report` to generate `paper_assets/tables/fpga_dim_sweep_resource.csv`, `paper_assets/tables/fpga_dim_sweep_timing.csv`, and `paper_assets/tables/fpga_dim_sweep_latency.csv`.
- Run `just onnx-decode-sweep ...` to generate `paper_assets/tables/decode_latency_by_context.csv` and `paper_assets/tables/kv_memory_comparison.csv`.
- Run `just torch-context-sweep ...` to generate `paper_assets/tables/torch_decode_latency_by_context.csv`, `paper_assets/tables/torch_memory_by_context.csv`, `paper_assets/figures/torch_decode_latency_by_context.png`, and `paper_assets/figures/torch_memory_by_context.png`.
- Copy one selected board image into `paper_assets/figures/` only if a real hardware photo is available; otherwise keep the placeholder.
- Use host and FPGA validation outputs to build the final report narrative.
- Connect the two sides carefully: host profiling motivates why decode-stage primitives matter, while FPGA validation shows that the current INT8 QK dot-product block can be synthesized and observed on hardware.
- Interpret the FPGA results narrowly as synthesis and board-validation evidence for the INT8 QK dot-product block, including dim-sweep scaling behavior, not as full Gemma 3 1B execution and not as end-to-end ONNX Runtime comparison data.
