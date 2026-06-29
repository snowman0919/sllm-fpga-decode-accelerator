# Release Artifacts

The reviewer-facing `main` branch does not track generated `dist/` contents.
This avoids duplicating source files, paper tables, figures, Quartus reports,
and Windows runners in two places.

## Build

```bash
python scripts/build_ort_fpga_comparison.py
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
```

The installer template for the generated package is:

```text
scripts/dist_install.py
```

The generated package appears at:

```text
dist/ai_accel_paper/
```

## Contents

The package is a convenience bundle for local/Windows smoke checks. It includes
selected scripts, Windows runners, ONNX micrographs, paper-facing tables,
figures, and Quartus JTAG MatVec artifacts.

The package does not create new evidence by itself. Its manifest only verifies
that the copied files match the generated checksums.

## Claim Boundary

Release artifacts must preserve the same evidence labels as the repository:

- `measured` for host baselines and JTAG invocation overhead.
- `board_measured` for FPGA internal cycle-counter evidence from a passing board run.
- `simulation` for RTL simulation evidence.
- `projected` for optimized-interface estimates.

The package must not describe JTAG latency as FPGA compute latency, and it must
not claim full Gemma FPGA execution, full ONNX Runtime acceleration, or
end-to-end speedup.
