# JTAG Register MatVec Offload

This path invokes the fixed INT8 `DecodeMatVecInt8` primitive through the DE10-Lite USB-Blaster JTAG connection. It is the preferred board-validation route when no external USB-UART adapter is desired.

## Why JTAG-to-Avalon Master

Two JTAG-based host paths are common:

- JTAG UART terminal: useful for character streams and simple console I/O
- JTAG-to-Avalon Master: useful for host-driven memory-mapped register reads/writes

This experiment uses JTAG-to-Avalon Master because the MatVec primitive naturally maps to a small register bank: write activation and weight registers, assert `start`, poll `done`, then read result registers. That shape is clearer and more reproducible than encoding binary payloads through a terminal stream.

## Claim Boundary

The JTAG path is only a host-to-FPGA invocation, correctness, and overhead validation route. It is not a performance-optimized bus, not a full Gemma 3 1B FPGA execution path, and not end-to-end ONNX Runtime speedup evidence. If no real JTAG execution log exists, no paper result table should include JTAG latency numbers. If a passing result exists but its numeric latency breakdown is not archived, the result may be reported as correctness/invocation evidence only.

The current paper-facing JTAG report is `docs/fpga_jtag_benchmark_report.md`. Its measured content is the deterministic result vector `[-271, 239, 287, 797]` with `correctness_pass=True`, a 20/0 pass/fail board run, JTAG total invocation latency, and `COMPUTE_CYCLES=65` from the FPGA internal cycle counter. JTAG total latency is archived as invocation overhead only; the FPGA compute latency evidence is the internal cycle-counter value.

The existing USB-UART path remains as an alternative path for setups with an external 3.3 V USB-UART adapter.

## Register Map

All registers are 32-bit words. Host addresses are byte offsets from the Avalon-MM slave base address.

| offset | name | access | description |
| ---: | --- | --- | --- |
| `0x0000` | `CONTROL` | W | bit 0 `start`, bit 1 `reset_core`, bit 2 `clear_done` |
| `0x0004` | `STATUS` | R | bit 0 `busy`, bit 1 `done`, bit 2 `error` |
| `0x0008` | `CONFIG` | R | `[15:0] input_dim`, `[31:16] output_dim` |
| `0x0010` | `SEQ` | R/W | host sequence/debug value |
| `0x0040` | `COMPUTE_CYCLES` | R | FPGA clock cycles latched from accepted start pulse to MatVec `done` |
| `0x0044` | `CORE_TOTAL_CYCLES` | R | FPGA clock cycles from host start register write observation to `done` latch |
| `0x0048` | `LAST_RUN_ID` | R | `SEQ` value captured when the most recent start was accepted |
| `0x004c` | `DEBUG_STATUS` | R | bit 0 `busy`, bit 1 `done_latched`, bit 2 `error`, bit 3 `compute_timing_active`, bit 4 `core_timing_active`, bit 5 `start_pulse`, bit 6 `matvec_done` |
| `0x0100` | `ACTIVATION[0..15]` | R/W | signed int8 in low 8 bits |
| `0x0200` | `WEIGHT[0..63]` | R/W | row-major `weight[out][in]`, signed int8 in low 8 bits |
| `0x0300` | `RESULT[0..3]` | R | signed int32 accumulator result |

Signed handling:

- Host writes activation and weight values into bits `[7:0]`.
- FPGA interprets those bits as `SInt(8 bits)`.
- Results are read as 32-bit two's-complement signed integers.
- Cycle counters assume the board `CLOCK_50` domain for the default conversion: `compute_time_us = compute_cycles / 50_000_000 * 1e6`.
- If Quartus timing extraction reports a usable Fmax, paper tables may also include `compute_time_at_fmax_us`; keep it separate from the 50 MHz board-clock measurement.

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
- `--clock-hz 50000000`: board-clock frequency used for cycle-to-time conversion
- `--sof PATH`: bitstream path used for SHA-256 provenance in logs

## Logs

The runner writes:

- `fpga_jtag_matvec.csv`
- `fpga_jtag_matvec_success.csv`
- `fpga_jtag_matvec_failure.csv`
- `fpga_jtag_summary.json`
- `fpga_jtag_summary.md`
- `jtag_stdout.txt`
- `jtag_stderr.txt`
- `generated_*.tcl` when `--keep-tcl` is used

If Quartus tools, USB-Blaster, JTAG master service, register access, or polling fails, the runner writes a skipped/failed summary and does not fabricate a passing result. Paper-facing JTAG and cycle-counter tables are updated only from real passing hardware runs, with pass and fail counts preserved.
