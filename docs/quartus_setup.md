# Quartus Setup

Quartus may be managed externally if Nix integration is not practical for your local environment. The default development shell remains usable for SpinalHDL, simulation, and Python work even when Quartus is not installed.

If Quartus is already installed under a common home-directory location such as `~/.intelFPGA_lite/25.1std`, you can use the repository's direct wrapper without entering `nix develop`:

```bash
./scripts/quartus.sh check
```

## QUARTUS_ROOT

If Quartus is installed outside Nix, point `QUARTUS_ROOT` at the installation root that contains `quartus/bin/quartus_sh`:

```bash
export QUARTUS_ROOT=/opt/intelFPGA_lite/22.1std
./scripts/quartus.sh check
```

The shell hook adds these directories when they exist:

- `$QUARTUS_ROOT/quartus/bin`
- `$QUARTUS_ROOT/quartus/bin64`
- `$QUARTUS_ROOT/quartus/sopc_builder/bin`
- `$QUARTUS_ROOT/modelsim_ase/bin`
- `$QUARTUS_ROOT/questa_fse/bin`
- `$QUARTUS_ROOT/questa_fe/bin`
- `$QUARTUS_ROOT/questa_ase/bin`

If `QUARTUS_ROOT` is unset, the shell probes common roots and one version directory below each root:

- `/opt/intelFPGA_lite`
- `/opt/altera_lite`
- `$HOME/intelFPGA_lite`
- `$HOME/.intelFPGA_lite`
- `$HOME/altera_lite`
- `$HOME/.altera_lite`

## Tool Checks

Use the direct project command:

```bash
./scripts/quartus.sh check
```

It reports `QUARTUS_ROOT`, the resolved paths for `quartus_sh`, `quartus_map`, `quartus_fit`, `quartus_asm`, and `quartus_pgm`, and whether `quartus_sh --version` runs.

If you are already working inside the Nix shell, `just quartus-check` remains equivalent.

You can also check manually:

```bash
command -v quartus_sh
quartus_sh --version
```

For USB-Blaster visibility after connecting the board:

```bash
quartus_pgm -l
```

If this fails, resolve host USB permissions or cable visibility outside this repository. The project does not run sudo-based installation steps.

## Verified QSF Requirement

A verified DE10-Lite QSF is required for trustworthy board compilation because the repository does not guess pin assignments. Use a QSF from Terasic System Builder, an official DE10-Lite example, or a user-validated board project.

Import it with:

```bash
./scripts/quartus.sh import-qsf /absolute/path/to/verified_de10_lite.qsf
```

The destination is:

- `quartus/de10_lite_qk/qsf/verified_de10_lite_pins.qsf`

## Project Flow

1. Generate Verilog with `just spinal-generate`.
2. Import a verified DE10-Lite QSF with `./scripts/quartus.sh import-qsf /path/to/verified.qsf`.
3. Create the Quartus project with `./scripts/quartus.sh project`.
4. Compile with `./scripts/quartus.sh compile`.
5. Program with `./scripts/quartus.sh program`.

## Without a Verified QSF

Available without a QSF:

- Nix shell entry
- Quartus tool detection
- SpinalHDL Verilog generation
- Quartus project creation as a placeholder, if Quartus itself is installed

Blocked without a QSF:

- trustworthy compile for the real DE10-Lite board
- `.sof` generation intended for the board
- board programming and HEX validation

## Reproducibility Note

Quartus is proprietary, so reproducibility is maintained by keeping HDL generation deterministic in `hw/spinal/generated/`, mirroring only the canonical Verilog into `quartus/de10_lite_qk/generated_verilog/`, and isolating Quartus scripts and imported board files under `quartus/de10_lite_qk/`.
