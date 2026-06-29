# Windows Test Guide

The Windows scripts are intended for CPU baselines, ONNX Runtime micrograph baselines, and optional DE10-Lite UART validation. FPGA tests skip gracefully when no COM port is provided.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r windows\requirements.txt
```

## CPU Primitive Baseline

```powershell
python windows\run_cpu_matvec_baseline.py --runs 10
```

Outputs are written under `logs\<timestamp>\` and the paper-facing summary row is updated in `paper_assets\tables\fpga_uart_primitive_benchmark.csv`.

## ONNX Runtime Micrograph Baseline

```powershell
python windows\run_ort_matvec_baseline.py --runs 10
```

This runs a small `float32` MatMul graph with `CPUExecutionProvider`. The dtype difference from the INT8 FPGA primitive is recorded in the output table.

## FPGA JTAG Register Primitive

The preferred board-validation path uses the DE10-Lite USB-Blaster with JTAG-to-Avalon Master and a MatVec register bank. It does not require an external USB-UART adapter.

```powershell
python windows\run_fpga_jtag_matvec.py --runs 10 --cable "USB-Blaster [USB-0]" --keep-tcl
```

If Quartus tools, USB-Blaster, or the JTAG-to-Avalon master service is unavailable, the script writes `fpga_jtag_summary.json`/`.md` and does not update paper result tables.

## FPGA UART Primitive Alternative

List available serial ports:

```powershell
python windows\run_fpga_uart_matvec.py --list-ports
```

```powershell
python windows\run_fpga_uart_matvec.py --port COM5 --baud 115200 --runs 10 --dump-request-hex --dump-response-hex
```

The expected FPGA bitstream implements the fixed `input_dim=16`, `output_dim=4` UART MatVec command. If the board is not connected or the port cannot be opened, the script writes a skipped summary and exits without fabricating a result row.

## ORT-Equivalent UART Harness

```powershell
python windows\run_ort_fpga_custom_op.py --port COM5 --baud 115200 --runs 10
```

This is a graph-level equivalent harness, not a native ONNX Runtime custom-op DLL. Tables mark `custom_op=false` until a DLL path exists and is verified.
