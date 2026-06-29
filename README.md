# sLLM FPGA Decode Accelerator Skeleton

This repository is a reproducible research skeleton for the topic:

- Korean: ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계
- English: Bottleneck Analysis of ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator Architecture

The manuscript keeps this title. It already captures the on-device scope and Decode accelerator direction without implying full Gemma execution or measured ONNX Runtime acceleration.

## Project Purpose

The goal is to study where bottlenecks actually appear in ONNX Runtime-based on-device small language model inference, then use those profiling results to choose decode-stage primitives that are realistic FPGA hardware candidates. This repository is intentionally minimal and focuses on export, graph inspection, runtime profiling, host-side baselines, and primitive-level FPGA validation instead of overbuilding or overclaiming a full accelerator.

## Research Framing

- The host machine is used for Gemma 3 1B ONNX export, graph inspection, ONNX Runtime profiling, and PyTorch host-side reference baselines.
- KV-cache is treated as a representative structural source of long-context decode memory pressure, not as the only assumed bottleneck.
- The actual bottleneck location must be inferred from export behavior, ONNX graph structure, runtime execution traces, memory pressure measurements, prefill/decode timing, and host-side reference baselines.
- The Terasic DE10-Lite is used only to validate small FPGA hardware blocks. The current paper-facing evidence centers on a fixed-dimension INT8 Decode MatVec primitive and bitstream configuration evidence.
- This project does not claim that the DE10-Lite runs Gemma 3 1B or a full small language model.
- This project does not implement full KV-cache storage, movement, or management on FPGA.
- This project does not claim ONNX Runtime speedup or board-level numeric output validation from programming evidence alone.
- This project does not claim that FPGA logic replaces GPU or NPU inference.
- This project does not fabricate performance numbers.

## Research Questions

- Where do practical bottlenecks arise in ONNX Runtime-based on-device sLLM inference?
- Are the bottlenecks located in model export, graph structure, runtime execution, memory pressure, prefill, or decode?
- Which decode-stage primitives exposed by that analysis are suitable for FPGA hardware implementation?

For the current paper-facing hardware work, the FPGA result is a primitive-level feasibility validation of a small INT8 Decode MatVec block. A fuller FPGA Decode accelerator architecture can later extend toward projection-general tiled MatVec/MatMul, weight streaming, output tiling, cache-aware host binding, QK/V attention primitives, and the Host/ORT offload 경계.

## Repository Layout

- `flake.nix`: primary Nix development environment
- `.envrc`: direnv entrypoint with `use flake`
- `justfile`: common commands for generation, simulation, profiling, and board-validation checks
- `docs/`: research direction, experiment plan, paper outline, Quartus notes
- `hw/spinal/`: minimal SpinalHDL project and canonical generated Verilog
- `quartus/de10_lite_qk/`: Quartus import mirror, Tcl scripts, and QSF workflow
- `onnx_profile/`: ONNX export, graph inspection, ONNX Runtime profiling, PyTorch host-side reference baseline sweeps, and KV-cache size scripts
- `fpga_test/`: exported vectors and captured board validation artifacts
- `paper_assets/`: figures and tables intended for paper assembly

## Quick Start

Enter the shell directly:

```bash
nix develop
```

Enable direnv:

```bash
direnv allow
```

Inspect the environment:

```bash
just env-info
```

## SpinalHDL Workflow

Generate canonical Verilog and refresh the Quartus import mirror:

```bash
just spinal-generate
```

Generate the dim-sweep variants and refresh the synthesis-only Quartus mirror:

```bash
just spinal-generate-sweep
```

Canonical generated files:

- `hw/spinal/generated/DotProductInt8_dim16.v`
- `hw/spinal/generated/DotProductInt8_dim32.v`
- `hw/spinal/generated/DotProductInt8_dim64.v`
- `hw/spinal/generated/DotProductInt8_dim128.v`
- `hw/spinal/generated/DotProductInt8SweepTop_dim16.v`
- `hw/spinal/generated/DotProductInt8SweepTop_dim32.v`
- `hw/spinal/generated/DotProductInt8SweepTop_dim64.v`
- `hw/spinal/generated/DotProductInt8SweepTop_dim128.v`
- `hw/spinal/generated/HexDisplay.v`
- `hw/spinal/generated/De10LiteTop.v`

Quartus import mirror:

- `quartus/de10_lite_qk/generated_verilog/DotProductInt8_dim16.v`
- `quartus/de10_lite_qk/generated_verilog/HexDisplay.v`
- `quartus/de10_lite_qk/generated_verilog/De10LiteTop.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8_dim16.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8_dim32.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8_dim64.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8_dim128.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8SweepTop_dim16.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8SweepTop_dim32.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8SweepTop_dim64.v`
- `quartus/dim_sweep/generated_verilog/DotProductInt8SweepTop_dim128.v`

Run the minimal dot-product simulation:

```bash
just spinal-sim
```

Run the deterministic dim sweep simulation and emit CSV summaries:

```bash
just spinal-sim-sweep
```

If a simulator backend is unavailable, the command will fail in the normal SBT/SpinalHDL way. Verilog generation is still supported independently.

## Python Research Utilities

Raw Hugging Face `safetensors` directories cannot be executed directly by ONNX Runtime. For Gemma 3 1B host profiling in this repository, first inspect the raw directory, then export ONNX, then inspect the exported graph to see whether past-KV cache reuse is available.

Generate deterministic INT8 vectors for FPGA tests:

```bash
just vectors
```

Inspect the raw Gemma directory before export:

```bash
nix develop -c just hf-inspect model_dir=/home/monad/develop/ai_accel/gemma3-1B
```

Review the ONNX export plan without running the heavy export:

```bash
nix develop -c just gemma-onnx-export-dry model_dir=/home/monad/develop/ai_accel/gemma3-1B
```

Run the actual export only when you want to generate ONNX artifacts:

```bash
nix develop -c just gemma-onnx-export model_dir=/home/monad/develop/ai_accel/gemma3-1B
```

Inspect the exported ONNX graph:

```bash
nix develop -c just onnx-inspect model=/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx
```

Interpretation:

- if the ONNX graph exposes `past_key_values`, `present`, or similar cache I/O, decode cache reuse profiling is possible
- if those graph I/O are absent, only prefill or whole-graph profiling should be treated as supported by that export

Generate a KV-cache size table and plot:

```bash
just kv-cache-table
```

Check ONNX Runtime profiling script behavior without a model:

```bash
just onnx-profile
```

Run ONNX Runtime profiling with an exported Gemma 3 1B ONNX model:

```bash
just onnx-profile /absolute/path/to/gemma3-1b.onnx CPUExecutionProvider 128 32 1
```

Run a context-length sweep with separate prefill/decode measurement and KV/RSS comparison:

```bash
just onnx-decode-sweep /absolute/path/to/gemma3-1b.onnx CPUExecutionProvider "128 512 1024 2048 4096" 8 0 18 1 256 2
just onnx-decode-summary
```

Run a PyTorch/Transformers host-side baseline sweep directly from the local Gemma 3 1B `safetensors` directory:

```bash
nix develop -c just torch-context-sweep model_dir=/home/monad/develop/ai_accel/gemma3-1B
just torch-context-summary
```

Interpretation limit:

- PyTorch context sweep is not ONNX Runtime profiling.
- PyTorch context sweep is a host-side reference baseline for observing Gemma 3 1B prefill/decode behavior and memory pressure outside ONNX Runtime.
- Use it as a companion baseline when interpreting ONNX export, graph inspection, and ONNX Runtime profiling results.

## Quartus Integration

Quartus is handled in a fault-tolerant way:

- If a suitable Quartus package is available in the current `nixpkgs`, the flake exposes an optional `.#quartus` shell path.
- If Quartus is managed externally, set `QUARTUS_ROOT` or expose Quartus tools on `PATH`.
- If Quartus is missing, Verilog generation, simulation, and host-side profiling still work.
- If Quartus is already installed under a common home-directory path such as `~/.intelFPGA_lite`, the repository can use it directly without `nix develop`.

Check detection directly:

```bash
./scripts/quartus.sh check
```

Optional shell with a Nix-packaged Quartus, if your local `nixpkgs` exposes one:

```bash
nix develop .#quartus
```

## Verified QSF Import

This repository does not guess DE10-Lite pin assignments. Import a verified `.qsf` from a trusted source such as Terasic System Builder, an official DE10-Lite example project, or your own validated board project.

Import it into the expected location:

```bash
./scripts/quartus.sh import-qsf /absolute/path/to/verified_de10_lite.qsf
```

The imported file is stored at:

- `quartus/de10_lite_qk/qsf/verified_de10_lite_pins.qsf`

If the verified QSF is missing, the Quartus project can still be created as a placeholder, but compile and program steps should be treated as incomplete manual work.

## Quartus Project Creation

Create the Quartus project skeleton around the mirrored Verilog:

```bash
./scripts/quartus.sh project
```

This uses:

- top-level entity `De10LiteTop`
- target device `10M50DAF484C7G`
- `quartus/de10_lite_qk/de10_lite_qk.sdc`
- `quartus/de10_lite_qk/generated_verilog/*.v`

If a verified QSF is present, the project includes it. If not, the script emits a clear warning and leaves the manual pin-assignment step open.

## Compile and Program

Compile only after importing a verified DE10-Lite QSF:

```bash
./scripts/quartus.sh compile
```

Program the board only after a `.sof` has been produced:

```bash
./scripts/quartus.sh program
```

`./scripts/quartus.sh program` attempts USB-Blaster programming only when `quartus_pgm` is available and `quartus/de10_lite_qk/output_files/de10_lite_qk.sof` exists.

If you are already inside `nix develop`, the equivalent `just quartus-check`, `just quartus-project`, `just quartus-compile`, and `just quartus-program` targets remain available as convenience wrappers.

After compile, collect paper-facing summaries directly from the Quartus output directory:

```bash
just fpga-report
just fpga-validate-summary
```

For synthesis scaling across `dim = 16, 32, 64, 128`, run the sweep flow:

```bash
just quartus-dim-sweep
just fpga-dim-sweep-report
```

This sweep is intentionally narrower than the board flow. It is a synthesis experiment for the INT8 QK dot-product primitive, not a claim about full sLLM execution or end-to-end acceleration.

## What HEX Displays Confirm

`De10LiteTop` uses a fixed internal Q vector and fixed internal K vector. It runs a deterministic INT8 dot-product and exposes the result on the 7-segment displays.

Expected low 16-bit score value after completion:

- `0xFFEA` for the current built-in test vectors

Suggested interpretation:

- `HEX0` to `HEX3`: low 16 bits of the score, expected to settle to `A`, `E`, `F`, `F`
- equivalently, the board should read `HEX3..HEX0 = F F E A`
- `HEX4`: status nibble with busy, done, sign, and rerun marker bits
- `HEX5`: rerun counter nibble
- `LEDR`: done, busy, sign, input state, and low score bits for quick debugging

This is a board-level validation loop for a small decode-stage primitive only. It is not a claim of full-model execution on the FPGA.

## What To Record After `quartus-program`

After a successful program step, record the following before writing the paper section:

- the exact `.sof` path that was programmed
- Quartus `fit.summary`, `map.summary`, and `sta.summary`
- resource utilization and timing rows generated by `just fpga-report`
- whether the board visibly settles to `HEX3..HEX0 = F F E A`
- at least one raw board photo or short video under `fpga_test/captured/`
- one selected paper-ready board image under `paper_assets/figures/`, if you intend to include a photo in the manuscript

If no real board image is available yet, keep the placeholder files:

- `fpga_test/captured/de10_lite_validation_photo.placeholder.md`
- `paper_assets/figures/de10_lite_board_photo.placeholder.md`

## Paper Interpretation Limits

When you write up the FPGA section, keep the claim boundary narrow:

- These synthesis and board-validation results apply to the deterministic INT8 QK dot-product core block now under test.
- The dim sweep applies to resource and latency scaling of that primitive only.
- They do not show that the FPGA runs Gemma 3 1B.
- They do not provide end-to-end comparison data against ONNX Runtime.
- They are best used as evidence that a decode-stage primitive can be synthesized, programmed, and observed on DE10-Lite with stable expected outputs.

## Dim Sweep Purpose

The dim sweep covers `dim = 16, 32, 64, 128` for the sequential INT8 QK dot-product block.

- `just spinal-sim-sweep` generates deterministic expected and observed results in `fpga_test/captured/dot_product_dim_sweep_sim.csv` and `paper_assets/tables/dot_product_dim_sweep_sim.csv`.
- `just quartus-dim-sweep` compiles synthesis-only Quartus projects for the same dims.
- `just fpga-dim-sweep-report` extracts `paper_assets/tables/fpga_dim_sweep_resource.csv`, `paper_assets/tables/fpga_dim_sweep_timing.csv`, and `paper_assets/tables/fpga_dim_sweep_latency.csv`.

Interpret the tables carefully:

- they characterize how the QK dot-product primitive scales in resource usage and estimated latency
- they do not represent full decode throughput
- they do not represent whole-model execution on FPGA

## Connection to Gemma 3 1B Profiling

The ONNX-centered host workflow provides:

- raw Hugging Face directory inspection
- ONNX export preflight and export
- exported ONNX graph inspection
- model session setup timing
- separate prefill timing
- separate decode timing
- context-length decode latency tables
- optional ONNX Runtime profiling JSON
- theoretical KV-cache size tables and plots
- a caveated comparison between theoretical KV-cache growth and measured process RSS growth

Those host measurements are intended to answer where the bottleneck appears: export, graph structure, runtime execution, memory pressure, prefill, decode, or some combination of them. KV-cache growth is one important structural factor in that analysis, especially for long-context decode, but it is not assumed to be the sole cause before profiling evidence is reviewed.

The PyTorch baseline scripts provide host-side reference measurements for prefill and decode without depending on ONNX export success. PyTorch context sweep is not ONNX Runtime profiling and should not be reported as ONNX Runtime data.

The FPGA result then serves as a block-level feasibility check for an INT8 QK dot-product primitive selected from decode attention, not as end-to-end model acceleration evidence.

## Useful Commands

```bash
just env-info
just spinal-generate
just spinal-sim
just vectors
just hf-inspect model_dir=/home/monad/develop/ai_accel/gemma3-1B
just gemma-onnx-export-dry model_dir=/home/monad/develop/ai_accel/gemma3-1B
just gemma-onnx-export model_dir=/home/monad/develop/ai_accel/gemma3-1B
just onnx-inspect model=/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx
just kv-cache-table
just onnx-decode-sweep /absolute/path/to/gemma3-1b.onnx
just onnx-decode-summary
just torch-context-sweep model_dir=/home/monad/develop/ai_accel/gemma3-1B
just torch-context-summary
./scripts/quartus.sh check
./scripts/quartus.sh project
./scripts/quartus.sh compile
./scripts/quartus.sh program
just quartus-check
just de10-lite-checklist
just quartus-project
just quartus-compile
just quartus-program
just fpga-report
just fpga-validate-summary
```
