# ai_accel_paper Test Package

This package contains the Windows CPU/ONNX Runtime baselines, optional FPGA UART
validation runner, ONNX micrograph artifacts, claim-boundary notes, and
paper-facing tables prepared from the repository.

Run locally:

```powershell
python install.py --local . --run-cpu --run-ort
```

List serial ports:

```powershell
python install.py --local . --list-ports
```

Run optional FPGA UART validation:

```powershell
python install.py --local . --run-fpga --port COM5 --baud 115200
```

The FPGA UART path is a low-speed validation/control path. It is not a full
Gemma ONNX execution path and does not imply end-to-end speedup.
