# Public Release Hygiene

This repository separates source artifacts, generated evaluation outputs, and the distributable test package.

## Canonical Paper Path

The canonical current manuscript is:

```text
paper/current/ONNX_Runtime_온디바이스_sLLM_FPGA_Decode_가속기_논문양식본.md
```

Top-level paper draft mirrors are retained for compatibility with earlier review passes, but new edits should target the canonical path above first.

## Source Repository vs Dist Package

| location | role |
| --- | --- |
| `windows/`, `onnx_micrographs/`, `scripts/`, `docs/`, `hw/`, `quartus/` | source and reproducibility inputs |
| `paper_assets/` | paper-facing frozen or regenerated tables and figures |
| `dist/ai_accel_paper/` | self-contained local/FTP test package with a manifest and checksums |

The dist package is rebuilt from source with:

```bash
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
```

The package manifest is a checksum contract for the copied package contents. If any file in `dist/ai_accel_paper/` changes after manifest generation, `scripts/verify_dist_package.py` must fail.

## Generated Files

`__pycache__` directories and `.pyc` files are release noise and should be removed before packaging. Quartus database directories and transient project outputs are excluded from the dist package; selected source Verilog, scripts, summary reports, and `.sof` artifacts are retained only where needed for reproducible board validation.

## Existing Archives

`paper/asset.zip` is retained as a paper asset archive unless it is superseded by a documented replacement. It is not used as evidence for a new measurement by itself.

## Claim Boundary

The public package is an evaluation and validation package. It does not claim full Gemma execution on FPGA, full ONNX Runtime acceleration, or measured end-to-end speedup. Hardware rows remain correctness, invocation, simulation, measured board-cycle, or projected estimate evidence according to their source.
