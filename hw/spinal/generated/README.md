# Generated Verilog

This directory is the canonical output location for Verilog generated from the SpinalHDL sources.

Expected files after `just spinal-generate`:

- `DotProductInt8_dim16.v`
- `HexDisplay.v`
- `De10LiteTop.v`

These files are then mirrored into `quartus/de10_lite_qk/generated_verilog/` for Quartus import.

Simulation workspaces may also be placed under this directory to keep generated artifacts contained.
