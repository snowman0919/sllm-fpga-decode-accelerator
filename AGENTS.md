# Agent Notes

## Project Identity

This repository supports the research project:

- Korean title: ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계
- English title: Bottleneck Analysis of ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator Architecture

The project is a reproducible research skeleton. It combines ONNX-centered host profiling, PyTorch host-side reference baselines, and narrow FPGA primitive validation. It is not a full small-language-model accelerator implementation.

## Core Research Claim

Keep the central claim narrow and evidence-based:

ONNX Runtime-based on-device sLLM inference can encounter bottlenecks in model export, graph structure, runtime execution, memory pressure, prefill, decode, or interactions among these layers. KV-cache is a representative structural source of long-context decode memory pressure, but it must not be assumed to be the only bottleneck before profiling evidence is reviewed.

The FPGA work validates a selected decode-attention primitive, beginning with an INT8 QK dot-product block. The current hardware result is feasibility evidence for that primitive only.

## Claim Boundaries

Do not claim any of the following unless new evidence is added:

- DE10-Lite runs Gemma 3 1B or any complete sLLM.
- The current FPGA design implements full KV-cache storage, movement, or management.
- The FPGA result is an end-to-end ONNX Runtime speedup result.
- PyTorch context-sweep results are ONNX Runtime profiling results.
- Process RSS changes are direct measurements of KV-cache allocation.
- The FPGA replaces a GPU or NPU for complete inference.
- The dim sweep represents full decode throughput or whole-model acceleration.

Acceptable wording:

- "FPGA primitive validation"
- "INT8 QK dot-product feasibility"
- "host-side PyTorch reference baseline"
- "ONNX export and graph inspection"
- "ONNX Runtime profiling, where an exported model interface permits it"
- "KV-cache as one structural memory-pressure factor"

## Evidence Layers

Treat these evidence sources as related but separate:

1. ONNX-centered host analysis
   - Raw Hugging Face directory inspection
   - ONNX export preflight and export
   - ONNX graph input/output inspection
   - ONNX Runtime session setup, prefill, decode, and profiling traces
   - Cache-I/O detection, especially `past_key_values`, `present`, or similar graph interfaces

2. PyTorch host-side reference baseline
   - Direct Transformers/PyTorch execution from local `safetensors`
   - Context-length sweep
   - Prefill latency, decode latency, and process RSS snapshots
   - Reference baseline only; never report as ONNX Runtime data

3. FPGA primitive validation
   - Deterministic INT8 Q/K vector generation
   - SpinalHDL RTL simulation
   - Quartus synthesis and dim sweep
   - DE10-Lite HEX-display validation
   - Evidence for the INT8 QK dot-product primitive only

## Repository Map

- `README.md`: project overview, current scope, and command summary
- `docs/research_direction.md`: final research framing and interpretation limits
- `docs/experiment_plan.md`: staged experiment plan from host profiling to FPGA validation
- `docs/paper_outline.md`: paper structure and required narrative boundaries
- `docs/research_note.md`: compact statement of the core claim
- `논문-초안(uncompleted).md`: active Korean manuscript draft
- `onnx_profile/`: ONNX export, graph inspection, profiling, PyTorch sweep, and KV-cache utilities
- `hw/spinal/`: SpinalHDL source and simulation tests for the INT8 QK dot-product block
- `quartus/de10_lite_qk/`: DE10-Lite Quartus project, scripts, reports, and board-validation flow
- `quartus/dim_sweep/`: synthesis-only dim-sweep projects
- `fpga_test/`: test vectors, board captures, and validation summaries
- `paper_assets/`: paper-facing frozen results, tables, figures, and summaries

## Common Commands

Prefer `just` targets over ad-hoc commands when a target exists.

Environment:

```bash
nix develop
just env-info
```

SpinalHDL and FPGA primitive simulation:

```bash
just spinal-generate
just spinal-sim
just spinal-sim-sweep
just vectors
```

ONNX and host profiling:

```bash
just hf-inspect model_dir=/home/monad/develop/ai_accel/gemma3-1B
just gemma-onnx-export-dry model_dir=/home/monad/develop/ai_accel/gemma3-1B
just gemma-onnx-export model_dir=/home/monad/develop/ai_accel/gemma3-1B
just onnx-inspect model=/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx
just kv-cache-table
just onnx-decode-sweep /absolute/path/to/gemma3-1b.onnx
just onnx-decode-summary
just torch-context-sweep model_dir=/home/monad/develop/ai_accel/gemma3-1B
just torch-context-summary
just torch-sweep-analysis
```

Quartus and DE10-Lite validation:

```bash
just quartus-check
just de10-lite-checklist
just import-qsf /absolute/path/to/verified_de10_lite.qsf
just quartus-project
just quartus-compile
just quartus-program
just fpga-report
just fpga-validate-summary
just quartus-dim-sweep
just fpga-dim-sweep-report
```

Use `./scripts/quartus.sh ...` only when it is more convenient than the equivalent `just` wrapper.

## Paper-Writing Guidance

When editing the manuscript:

- Keep Korean and English titles aligned with `docs/research_direction.md`.
- Separate ONNX Runtime results, PyTorch baseline results, and FPGA primitive results in text, tables, and captions.
- Describe KV-cache as a representative structural factor for long-context decode memory pressure, not as the sole proven bottleneck.
- When ONNX export or graph inspection is incomplete, state the limitation directly instead of filling the gap with PyTorch results.
- Use PyTorch CPU/CUDA sweep data as host-side reference evidence only.
- Tie FPGA work to decode-stage primitive selection, not to full-model deployment.
- State that the future FPGA Decode accelerator architecture may extend from QK dot-product to scale, softmax or approximation, V weighted sum, and buffer/stream interfaces.

For the current Korean draft, the abstract and introduction should follow this framing:

- Problem: practical ONNX Runtime bottleneck location is unclear without export, graph, runtime, memory, prefill, and decode analysis.
- Method: ONNX export and inspection, ONNX Runtime profiling, PyTorch host-side reference baselines, and FPGA primitive validation.
- Hardware scope: INT8 QK dot-product feasibility on DE10-Lite, not full Gemma 3 1B execution.
- Contribution: an evidence-bounded workflow and a future decode-accelerator architecture sketch.

## FPGA Validation Facts

The current DE10-Lite validation target is the deterministic INT8 QK dot-product primitive.

- Expected signed score: `-22`
- Lower 16-bit two's-complement value: `0xFFEA`
- Expected board display: `HEX3..HEX0 = F F E A`

Interpret this only as confirmation that the synthesized primitive produces the expected fixed test-vector result on the board.

## Data and Artifact Rules

- Promote stable paper-facing outputs into `paper_assets/`.
- Keep raw or captured validation material under `fpga_test/captured/`.
- Preserve frozen result archives under `paper_assets/frozen_results/`.
- Do not fabricate missing profiling, board, or export data.
- If a generated result is stale or missing, rerun the relevant `just` target or mark the paper section as pending.

## Development Rules

- Commit after every meaningful change to the codebase when the user requests commit-oriented work.
- Keep commits focused and descriptive.
- Do not overwrite user changes in a dirty worktree.
- Prefer `rg` for searching.
- Prefer existing scripts, `just` targets, and repository patterns over adding new tooling.
- Keep generated files and manually edited source files conceptually separate.
- When adding tests, focus them on the changed behavior or research artifact being produced.
