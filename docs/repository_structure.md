# Repository Structure

This `main` branch is reviewer-facing. It keeps source, final paper artifacts,
compact evidence summaries, and regeneration scripts. Full raw experiment
traces, agent working notes, duplicate drafts, and generated release copies are
preserved on the `examine` branch.

## Core Paths

| path | keep on main | role |
| --- | --- | --- |
| `README.md` | yes | short project orientation and key evidence summary |
| `paper/current/` | yes | canonical current manuscript |
| `paper_assets/tables/` | yes | final paper-facing CSV evidence tables |
| `paper_assets/figures/` | yes | final paper-facing figures |
| `docs/claim_boundary.md` | yes | allowed and disallowed research claims |
| `docs/linux_windows_fpga_eval_workflow.md` | yes | Linux/Nix vs Windows board-run workflow |
| `docs/windows_board_runbook.md` | yes | Pocket4/DE10-Lite compile, program, and JTAG runbook |
| `docs/fpga_jtag_benchmark_report.md` | yes | board-measured JTAG/cycle-counter interpretation |
| `docs/ort_vs_fpga_comparison_interpretation.md` | yes | measured/projected comparison boundary |
| `docs/quartus_clean_rebuild_notes.md` | yes | clean rebuild fix and board validation notes |
| `docs/quartus_resource_timing_summary.md` | yes | generated Quartus resource/timing summary |
| `hw/spinal/` | yes | SpinalHDL source and tests |
| `quartus/de10_lite_jtag_matvec/` | yes | primary DE10-Lite JTAG-to-Avalon rebuild source and `.sof` |
| `windows/` | yes | Windows runners for board and host baselines |
| `scripts/` | yes | artifact generation and verification scripts |
| `logs/` | compact only | manifests for primary and historical board runs |

## Branch Policy

- `main`: readable source and reviewer-facing evidence.
- `examine`: complete experimental trace, raw logs, duplicate drafts, generated
  dist package copies, and agent working context.

Files removed from `main` are retained on `examine`.

## Evidence Policy

The primary board evidence is the clean-rebuilt `.sof`:

```text
40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84
```

Main keeps compact evidence in:

- `logs/jtag_cycle_counter_clean_rebuild_final/BOARD_RUN_MANIFEST.md`
- `logs/remote_board_eval/BOARD_RUN_MANIFEST.md`
- `paper_assets/tables/fpga_jtag_cycle_counter_summary.csv`
- `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`
- `paper_assets/tables/ort_vs_fpga_measured_and_projected_comparison.csv`

Raw generated Tcl files, stdout/stderr captures, CSV dumps for historical runs,
and zip archives are available on `examine` rather than `main`.

## Dist Policy

`dist/ai_accel_paper/` is a generated release package. It is not tracked on
`main`. Rebuild it locally with:

```bash
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
```

The generated package contains its own manifest and checksums. Release uploads
or tag artifacts should be created from the generated package, not hand-edited.
