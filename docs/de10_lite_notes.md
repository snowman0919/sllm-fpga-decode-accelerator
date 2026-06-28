# DE10-Lite Notes

- The DE10-Lite is used for core RTL block validation only.
- The target FPGA family is Intel MAX 10, specifically the 10M50DA class used on the board.
- The current stage is to build a practical DE10-Lite board-validation loop around a deterministic dot-product block and HEX display output.

## Current Boundary

The current top-level design is only intended to:

- provide a Quartus-importable wrapper
- drive HEX displays with deterministic debug information
- expose a simple rerunnable validation path for the dot-product block
- avoid external memory, UART, ONNX data feeds, and larger accelerator scope

## Pin Assignment Policy

Pin assignments must come from a verified DE10-Lite `.qsf` file.

Do not guess final pin assignments because:

- board revisions and reference projects can differ
- an incorrect `CLOCK_50`, `HEX`, `LEDR`, `SW`, or `KEY` mapping can make the validation result meaningless
- the point of this stage is a trustworthy board loop, not a speculative bring-up

Acceptable sources for the verified QSF include:

- Terasic System Builder output
- an official DE10-Lite example project
- a user-validated DE10-Lite project already known to work on this board

The current `verified_de10_lite_pins.qsf` was extracted from the official Terasic DE10-Lite SystemCD `Golden_Top` QSF. Only the pins used by `De10LiteTop` were kept. The official board clock name `MAX10_CLK1_50` was mapped to the local top-level port name `CLOCK_50`; this is a port-name adaptation from the reference QSF, not a guessed pin assignment.

## Practical Flow

1. Run `just spinal-generate`.
2. Import a verified QSF with `./scripts/quartus.sh import-qsf /path/to/verified.qsf`.
3. Create the Quartus project with `./scripts/quartus.sh project`.
4. Compile with `./scripts/quartus.sh compile`.
5. Program with `./scripts/quartus.sh program`.
6. Confirm that the HEX displays settle to the deterministic dot-product result and that the LEDR debug bits match the expected done/sign state.

## Expected Board Observation

For the current built-in vectors, the low 16-bit score should settle to `0xFFEA`, so `HEX3..HEX0` should show `F F E A` in hexadecimal order.

`HEX4`, `HEX5`, and `LEDR` are intentionally simple debug channels for run status and low score bits, not a full user interface.
