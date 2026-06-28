# Experiment Plan

## Stage 1. Gemma 3 1B ONNX Runtime Profiling

- Prepare or locate an ONNX-exported Gemma 3 1B model on the host machine.
- Measure session initialization overhead.
- Measure prefill and decode-stage execution separately where the model interface permits it.
- Sweep multiple prompt lengths and generate a decode latency table by context length.
- Export ONNX Runtime profiling traces when enabled.

## Stage 2. KV-cache Theoretical Size Calculation

- Sweep representative sequence lengths.
- Produce CSV tables and a simple plot.
- Compare theoretical KV-cache growth against measured ONNX Runtime process RSS growth with clear caveats.
- Use the results to motivate decode-stage memory pressure discussion.

## Stage 3. INT8 QK Dot-Product Baseline Generation

- Generate deterministic INT8 Q and K vectors on the host.
- Compute expected dot-product scores in software.
- Reuse those vectors in RTL simulation and board validation.

## Stage 4. SpinalHDL RTL Generation

- Implement a minimal parameterized INT8 QK dot-product block.
- Generate Verilog reproducibly from Scala sources.

## Stage 5. RTL Simulation

- Run deterministic unit simulation.
- Compare RTL output against the software-computed score.

## Stage 6. Quartus Synthesis

- Import generated Verilog into a DE10-Lite-oriented Quartus project.
- Synthesize only the validation design.

## Stage 7. DE10-Lite HEX Display Validation

- Display small debug values or low score digits on the 7-segment HEX outputs.
- Confirm basic top-level clocking and observable hardware behavior.
- After `quartus-program`, record the exact `.sof` path, Quartus summary reports, and whether the board settles to `HEX3..HEX0 = F F E A`.
- Treat `HEX3..HEX0 = F F E A` as the low 16 bits of the deterministic signed score `-22`, which is `0xFFEA` in two's complement.
- Save raw photos or videos first under `fpga_test/captured/`.

## Stage 8. Paper Figure and Table Extraction

- Promote stable plots and tables into `paper_assets/`.
- Run `just fpga-report` to generate `paper_assets/tables/fpga_resource_summary.csv`, `paper_assets/tables/fpga_timing_summary.csv`, and `paper_assets/tables/fpga_validation_summary.csv`.
- Run `just onnx-decode-sweep ...` to generate `paper_assets/tables/decode_latency_by_context.csv` and `paper_assets/tables/kv_memory_comparison.csv`.
- Copy one selected board image into `paper_assets/figures/` only if a real hardware photo is available; otherwise keep the placeholder.
- Use host and FPGA validation outputs to build the final report narrative.
- Connect the two sides carefully: host profiling motivates why decode-stage primitives matter, while FPGA validation shows that the current INT8 QK dot-product block can be synthesized and observed on hardware.
- Interpret the FPGA results narrowly as synthesis and board-validation evidence for the INT8 QK dot-product block, not as full Gemma 3 1B execution and not as proof of end-to-end speedup over ONNX Runtime.
