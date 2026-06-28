# DE10-Lite Quartus Validation Flow

This directory contains the Quartus-side skeleton for validating a small deterministic INT8 dot-product block on the Terasic DE10-Lite. It imports SpinalHDL-generated Verilog, expects a verified board QSF, and uses HEX/LEDR outputs as simple board-visible validation channels.

This flow validates an INT8 QK dot-product primitive only. It does not claim full Gemma 3 1B or full sLLM execution on the board, does not implement full KV-cache management, and does not establish end-to-end ONNX Runtime comparison data.

## Quartus Detection

If Quartus is installed externally, you can use it directly without entering the Nix shell:

```bash
export QUARTUS_ROOT=/opt/intelFPGA_lite/22.1std
./scripts/quartus.sh check
```

The shell adds Quartus, SOPC Builder, ModelSim ASE, and common Questa directories to `PATH` when those directories exist. If `QUARTUS_ROOT` is unset, it probes common install roots such as `/opt/intelFPGA_lite`, `/opt/altera_lite`, `$HOME/intelFPGA_lite`, `$HOME/.intelFPGA_lite`, `$HOME/altera_lite`, and `$HOME/.altera_lite`, including one version directory below each root.

Check detection with:

```bash
./scripts/quartus.sh check
```

Manual checks:

```bash
command -v quartus_sh
quartus_sh --version
quartus_pgm -l
```

`quartus_pgm -l` is the basic USB-Blaster visibility check after the board is connected.

## Canonical HDL Inputs

Generate Verilog first:

```bash
just spinal-generate
```

Canonical source files:

- `hw/spinal/generated/DotProductInt8_dim16.v`
- `hw/spinal/generated/HexDisplay.v`
- `hw/spinal/generated/De10LiteTop.v`

Quartus import mirror:

- `quartus/de10_lite_qk/generated_verilog/DotProductInt8_dim16.v`
- `quartus/de10_lite_qk/generated_verilog/HexDisplay.v`
- `quartus/de10_lite_qk/generated_verilog/De10LiteTop.v`

## Verified QSF Import

This repository does not guess board pin assignments. Import a verified DE10-Lite `.qsf` from Terasic System Builder, an official DE10-Lite example project, or a user-validated board project.

Import command:

```bash
./scripts/quartus.sh import-qsf /absolute/path/to/verified_de10_lite.qsf
```

Imported destination:

- `quartus/de10_lite_qk/qsf/verified_de10_lite_pins.qsf`

Current repository status: this file has been created from the official Terasic DE10-Lite SystemCD `Demonstrations/Golden_Top/DE10_LITE_Golden_Top.qsf`, filtered down to only `CLOCK_50`, `SW[9:0]`, `KEY[1:0]`, `LEDR[9:0]`, and `HEX0..HEX5[6:0]`. The source QSF name `MAX10_CLK1_50` is mapped to this project's `CLOCK_50` port; decimal-point pins `HEX[7]` and unused peripherals are intentionally excluded.

If this file is missing, project creation can still create a placeholder project, but compile and programming remain blocked for board safety.

## Project Creation

Create the Quartus project:

```bash
./scripts/quartus.sh project
```

The command refreshes the generated Verilog mirror if needed, runs `scripts/create_project.tcl`, warns if the verified QSF is missing, and checks that `de10_lite_qk.qpf` and `de10_lite_qk.qsf` were created.

The Tcl flow sets:

- project name: `de10_lite_qk`
- top-level entity: `De10LiteTop`
- target device: `10M50DAF484C7G`
- SDC file: `de10_lite_qk.sdc`

## Compile and Program

Compile only after importing a verified QSF:

```bash
./scripts/quartus.sh compile
```

After compile produces `output_files/de10_lite_qk.sof`, program with:

```bash
./scripts/quartus.sh program
```

Programming requires `quartus_pgm`, the `.sof` file, and a visible USB-Blaster cable.

If `quartus_pgm -l` shows a more specific cable label such as `USB-Blaster variant [1-6]`, the programming script resolves that exact name automatically. If you have multiple matching cables attached, set `QUARTUS_CABLE` to one exact `quartus_pgm -l` entry before running `./scripts/quartus.sh program`.

If you are already inside `nix develop`, the corresponding `just quartus-check`, `just quartus-project`, `just quartus-compile`, and `just quartus-program` targets remain available.

## QSF Status

Possible without verified QSF:

- `just quartus-check`
- `just spinal-generate`
- `just quartus-project`, if Quartus is installed

Not claimed without verified QSF:

- board-correct pin assignment
- real DE10-Lite compile success
- `.sof` programming success
- HEX display validation

## Expected Board Observation

`De10LiteTop` runs a fixed internal dot-product. After a successful board compile and program, the low 16-bit score should settle to `0xFFEA`, so `HEX3..HEX0` should show `F F E A` in hexadecimal order.
