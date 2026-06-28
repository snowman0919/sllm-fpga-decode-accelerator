# sLLM FPGA Decode Accelerator Skeleton

This repository is a reproducible research skeleton for the topic:

- Korean: ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 KV-cache 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계
- English: Analysis of KV-cache Bottlenecks in ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator

## Project Purpose

The immediate goal is to set up a clean Ubuntu + Nix + direnv + SpinalHDL + Quartus-compatible foundation for research and experimentation. This repository is intentionally minimal and focuses on a practical board-validation loop instead of overbuilding a full accelerator.

## Research Framing

- The host machine is used for Gemma 3 1B ONNX Runtime profiling and KV-cache bottleneck analysis.
- The Terasic DE10-Lite is used only to validate small FPGA hardware blocks that represent part of decode-stage attention work, such as an INT8 QK dot-product block or later a streaming score unit.
- This project does not claim that the DE10-Lite runs Gemma 3 1B or a full small language model.
- This project does not claim that FPGA logic replaces GPU or NPU inference.
- This project does not fabricate performance numbers.

## Repository Layout

- `flake.nix`: primary Nix development environment
- `.envrc`: direnv entrypoint with `use flake`
- `justfile`: common commands for generation, simulation, profiling, and board-validation checks
- `docs/`: research notes, experiment plan, paper outline, Quartus notes
- `hw/spinal/`: minimal SpinalHDL project and canonical generated Verilog
- `quartus/de10_lite_qk/`: Quartus import mirror, Tcl scripts, and QSF workflow
- `onnx_profile/`: ONNX Runtime profiling and KV-cache analysis scripts
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

Canonical generated files:

- `hw/spinal/generated/DotProductInt8_dim16.v`
- `hw/spinal/generated/HexDisplay.v`
- `hw/spinal/generated/De10LiteTop.v`

Quartus import mirror:

- `quartus/de10_lite_qk/generated_verilog/DotProductInt8_dim16.v`
- `quartus/de10_lite_qk/generated_verilog/HexDisplay.v`
- `quartus/de10_lite_qk/generated_verilog/De10LiteTop.v`

Run the minimal dot-product simulation:

```bash
just spinal-sim
```

If a simulator backend is unavailable, the command will fail in the normal SBT/SpinalHDL way. Verilog generation is still supported independently.

## Python Research Utilities

Generate deterministic INT8 vectors for FPGA tests:

```bash
just vectors
```

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
- They do not show that the FPGA runs Gemma 3 1B.
- They do not show that the FPGA is faster than ONNX Runtime.
- They are best used as evidence that a decode-stage primitive can be synthesized, programmed, and observed on DE10-Lite with stable expected outputs.

## Connection to Gemma 3 1B Profiling

The host-side ONNX Runtime scripts provide:

- model session setup timing
- separate prefill timing
- separate decode timing
- context-length decode latency tables
- optional ONNX Runtime profiling JSON
- theoretical KV-cache size tables and plots
- a comparison between theoretical KV-cache growth and measured process RSS growth

Those host measurements are intended to answer a narrow question: whether decode-stage cost and memory pressure increase enough with context length to justify isolating selected primitives such as the INT8 QK dot-product block for FPGA validation.

The FPGA result then serves as a block-level feasibility check for that primitive, not as end-to-end model acceleration evidence.

## Useful Commands

```bash
just env-info
just spinal-generate
just spinal-sim
just vectors
just kv-cache-table
just onnx-decode-sweep /absolute/path/to/gemma3-1b.onnx
just onnx-decode-summary
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
