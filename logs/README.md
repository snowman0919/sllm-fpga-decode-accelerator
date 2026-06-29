# Board Log Policy

`main` keeps compact board-run manifests only:

- `logs/jtag_cycle_counter_clean_rebuild_final/BOARD_RUN_MANIFEST.md`
- `logs/remote_board_eval/BOARD_RUN_MANIFEST.md`

The primary measured values are also frozen in `paper_assets/tables/`.

Raw generated Tcl files, stdout/stderr captures, expanded CSV dumps, and zip
archives are preserved on the `examine` branch. They are intentionally omitted
from `main` to keep the reviewer-facing branch readable.
