# JTAG Register MatVec Offload

This path invokes the fixed INT8 `DecodeMatVecInt8` primitive through the DE10-Lite USB-Blaster JTAG connection. It is the preferred board-validation route when no external USB-UART adapter is desired.

## Why JTAG-to-Avalon Master

Two JTAG-based host paths are common:

- JTAG UART terminal: useful for character streams and simple console I/O
- JTAG-to-Avalon Master: useful for host-driven memory-mapped register reads/writes

This experiment uses JTAG-to-Avalon Master because the MatVec primitive naturally maps to a small register bank: write activation and weight registers, assert `start`, poll `done`, then read result registers. That shape is clearer and more reproducible than encoding binary payloads through a terminal stream.

## Claim Boundary

The JTAG path is only a host-to-FPGA invocation, correctness, and overhead validation route. It is not a performance-optimized bus, not a full Gemma 3 1B FPGA execution path, and not end-to-end ONNX Runtime speedup evidence. If no real JTAG execution log exists, no paper result table should include JTAG latency numbers.

The existing USB-UART path remains as an alternative path for setups with an external 3.3 V USB-UART adapter.

## Register Map

All registers are 32-bit words. Host addresses are byte offsets from the Avalon-MM slave base address.

| offset | name | access | description |
| ---: | --- | --- | --- |
| `0x0000` | `CONTROL` | W | bit 0 `start`, bit 1 `reset_core`, bit 2 `clear_done` |
| `0x0004` | `STATUS` | R | bit 0 `busy`, bit 1 `done`, bit 2 `error` |
| `0x0008` | `CONFIG` | R | `[15:0] input_dim`, `[31:16] output_dim` |
| `0x0010` | `SEQ` | R/W | host sequence/debug value |
| `0x0100` | `ACTIVATION[0..15]` | R/W | signed int8 in low 8 bits |
| `0x0200` | `WEIGHT[0..63]` | R/W | row-major `weight[out][in]`, signed int8 in low 8 bits |
| `0x0300` | `RESULT[0..3]` | R | signed int32 accumulator result |

Signed handling:

- Host writes activation and weight values into bits `[7:0]`.
- FPGA interprets those bits as `SInt(8 bits)`.
- Results are read as 32-bit two's-complement signed integers.

## FPGA Components

- `hw/spinal/src/main/scala/qk/DecodeMatVecRegBank.scala`
- `hw/spinal/src/main/scala/qk/JtagDecodeMatVecRegTop.scala`

Generate Verilog:

```bash
nix develop -c just fpga-jtag-verilog
```

Mirrored Quartus sources are written to:

```text
quartus/de10_lite_jtag_matvec/generated_verilog/
```

## Quartus Setup

The scaffold lives in:

```text
quartus/de10_lite_jtag_matvec/
```

The current Tcl project scaffold can include the generated register top, but a board-ready system still requires Platform Designer integration with the JTAG-to-Avalon Master IP. Follow:

```text
quartus/de10_lite_jtag_matvec/platform_designer/create_jtag_matvec_system.tcl
```

Manual setup summary:

1. Create a Platform Designer system.
2. Add JTAG-to-Avalon Master IP.
3. Connect its master interface to the MatVec register-bank Avalon-MM slave or a wrapper exposing the same signals.
4. Connect the system to the 50 MHz clock and reset.
5. Generate HDL, include it in Quartus, compile, and program via USB-Blaster.

Do not report a compile or benchmark result unless Quartus actually generates, compiles, programs, and the host runner reads passing result registers.

## Windows Runner

Run CPU/ORT baselines plus optional JTAG:

```powershell
python windows\run_fpga_jtag_matvec.py --runs 10 --cable "USB-Blaster [USB-0]"
```

Installer example:

```powershell
curl.exe -fsSL https://ftp.kotori9.dev/ai_accel_paper/install.py | py -3 - --base-url https://ftp.kotori9.dev/ai_accel_paper/ --run-cpu --run-ort --run-jtag --cable "USB-Blaster [USB-0]"
```

Useful options:

- `--quartus-bin PATH`: directory containing `system-console` or `quartus_stp`
- `--base-address 0x00000000`: Avalon slave base address
- `--keep-tcl`: save generated Tcl scripts in the log directory

## Logs

The runner writes:

- `fpga_jtag_matvec.csv`
- `fpga_jtag_summary.json`
- `fpga_jtag_summary.md`

If Quartus tools, USB-Blaster, JTAG master service, register access, or polling fails, the runner writes a skipped/failed summary and does not update `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`.
