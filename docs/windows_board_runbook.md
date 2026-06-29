# Windows Pocket4 Board Runbook

This runbook is for the Windows Pocket4 laptop attached to the DE10-Lite board.
It intentionally avoids Nix commands.

## Environment

Expected tools:

- `quartus_sh.exe`
- `quartus_pgm.exe`
- `jtagconfig.exe`
- `system-console.exe`
- `py -3`

Known System Console path:

```text
C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe
```

Expected JTAG chain:

```text
USB-Blaster [USB-0]
10M50DA/DC
```

## Clean Compile

The Quartus project name and revision are `de10_lite_jtag_matvec`. The actual
Verilog top-level entity is `De10LiteJtagMatVecTop`. These are intentionally
different.

From the repository root:

```powershell
cd quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
```

The QSF must contain:

```text
set_global_assignment -name TOP_LEVEL_ENTITY De10LiteJtagMatVecTop
```

The QSF uses project-relative source paths so the project can rebuild from a
Windows checkout without Linux absolute paths.

## Program FPGA

Use the newly compiled `.sof` when available:

```powershell
cd ..\..
quartus_pgm.exe -m jtag -c "USB-Blaster [USB-0]" -o "p;quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof"
```

If using PowerShell and semicolon quoting causes trouble, pass arguments as an
array:

```powershell
& quartus_pgm.exe @('-m','jtag','-c','USB-Blaster [USB-0]','-o','p;quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof')
```

Programming success requires both:

```text
Configuration succeeded -- 1 device(s) configured
Successfully performed operation(s)
```

## JTAG Service Check

Create a small Tcl script:

```tcl
puts "SERVICES_BEGIN"
puts [get_service_paths master]
puts "SERVICES_END"
```

Run it:

```powershell
& "C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe" --script=jtag_service_check.tcl
```

A valid run must show a master service path between `SERVICES_BEGIN` and
`SERVICES_END`.

## Board Benchmark

Run the measured board benchmark:

```powershell
py -3 windows\run_fpga_jtag_matvec.py --runs 20 --cable "USB-Blaster [USB-0]" --quartus-bin "C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe" --keep-tcl --log-dir logs\jtag_cycle_counter_real_final
```

Success criteria:

- `pass_count = 20`
- `fail_count = 0`
- `reference = -271 239 287 797`
- `result = -271 239 287 797`
- `compute_cycles_mean = 65`
- `compute_time_us_50mhz_mean = 1.3`
- `debug_status` is present in run rows

JTAG total latency is not FPGA compute latency. It is host-tool invocation
overhead from System Console, JTAG service access, register writes, polling, and
register reads.

## Windows Baselines

Optional host baselines on the board-control laptop:

```powershell
py -3 scripts\verify_dist_package.py
py -3 windows\run_cpu_matvec_baseline.py --runs 1000 --log-dir logs\cpu_baseline_board_env
py -3 windows\run_ort_matvec_integer_baseline.py --runs 1000 --log-dir logs\ort_integer_baseline_board_env
```

The current Windows board-host ONNX Runtime MatMulInteger baseline is:

```text
mean/p50/p95 = 0.013012 / 0.011 / 0.0173 ms
```

Use this only as a fixed micrograph baseline for the same 16x4 INT8 MatVec
primitive, not as full Gemma ONNX Runtime profiling.
