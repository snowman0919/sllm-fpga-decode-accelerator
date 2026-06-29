# Paper Tables

This directory stores CSV tables that can be imported into the paper draft.

Expected generated files after `just fpga-report`:

- `fpga_resource_summary.csv`
- `fpga_timing_summary.csv`
- `fpga_validation_summary.csv`
- `dot_product_dim_sweep_sim.csv`
- `fpga_dim_sweep_resource.csv`
- `fpga_dim_sweep_timing.csv`
- `fpga_dim_sweep_latency.csv`

These tables summarize either the DE10-Lite validation build or the dim-sweep synthesis experiments for the INT8 QK dot-product primitive. They are paper support artifacts, not proof of full-model execution or FPGA-vs-ONNX-Runtime superiority.
